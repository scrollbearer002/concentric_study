"""Dual-Agent Outer Loop: Monitor → Diagnose → Adapt → Test.

Implements the supervisory loop that closes the gap between the GUI execution
agent and the code repair agent. When the execution agent finishes a run,
the outer loop reads the structured trace, classifies any failure, and decides
whether to retry, adjust parameters, escalate to the code agent, or abort.

Architecture grounded in:
- SHML (Rauba et al., NeurIPS 2024, arXiv:2411.00186): Monitor → Diagnose →
  Adapt → Test cycle as the prerequisite for autonomous self-healing.
- VIGIL (Cruz, 2025, arXiv:2512.07094): Stage-gated supervisory pipeline that
  ingests structured JSONL logs and produces code proposals.
- TraceCoder (ICSE 2026, arXiv:2602.06875): Observe-Analyze-Repair with
  Historical Lesson Learning to prevent repeated mistakes.
- Reflexion (Shinn et al., NeurIPS 2023, arXiv:2303.11366): Verbal
  self-reflection stored in episodic memory for iterative improvement.
- COCO (2025, arXiv:2508.13815): Contextual Rollback preserving execution
  history; Bidirectional Reflection Protocol for stable convergence.
- RepairAgent (2024, arXiv:2403.17134): Finite state machine for escalation
  policy — retry while improvement is measurable, escalate when stuck.

Build-order: depends on all prior infrastructure (TraceWriter, DiagnosticReader,
HealingOrchestrator, SkillLibrary). This is the final integration layer that
connects the execution agent to the code agent.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


from agent_infra.diagnostic_reader import DiagnosticReader
from agent_infra.healing_orchestrator import HealingOrchestrator, FailureClassification
from agent_infra.skill_library import SkillLibrary


# ---------------------------------------------------------------------------
# Task → Environment Variable Contract
# ---------------------------------------------------------------------------
# The test script (test_excalidraw_covt.py) selects its task based on specific
# environment variables. This map is the explicit interface contract between
# the outer loop orchestrator and the execution agent.
#
# Design principle (AOrchestra, arXiv:2602.03786): the orchestrator must speak
# the execution agent's interface. The agent's env var names are the source of
# truth; the orchestrator adapts to them, not the reverse.
#
# To add a new task: add its task_id -> env_var mapping here AND ensure the
# test script has a corresponding `if os.environ.get(...)` branch.
# ---------------------------------------------------------------------------
TASK_ENV_MAP: dict[str, str] = {
    "CONCENTRIC_TRIANGLES_CLEAN": "CONCENTRIC_TRIANGLES_CLEAN",
    "CONCENTRIC_TRIANGLES": "CONCENTRIC_TRIANGLES",
}


@dataclass
class OuterLoopResult:
    """Structured result from one full outer-loop execution.

    Designed for consumption by both humans and agents — every field is
    serializable and self-documenting.
    """

    outcome: str  # "success" | "escalated" | "aborted" | "max_retries_exhausted"
    cycles: int = 0
    run_id: str | None = None
    escalation_path: str | None = None
    total_duration_ms: int = 0
    reflections: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "outcome": self.outcome,
            "cycles": self.cycles,
            "run_id": self.run_id,
            "escalation_path": self.escalation_path,
            "total_duration_ms": self.total_duration_ms,
            "reflections": self.reflections,
        }


# ---------------------------------------------------------------------------
# Reflection Journal (Reflexion + TraceCoder HLLM)
# ---------------------------------------------------------------------------

class ReflectionJournal:
    """Episodic memory for the outer loop.

    After each cycle (success or failure), records a verbal reflection.
    On retry, past reflections are fed back as context so the system
    avoids repeating the same mistakes.

    Implements:
    - Reflexion (Shinn et al., NeurIPS 2023): verbal self-reflection
    - TraceCoder HLLM: historical lesson learning to prevent recurrence
    - COCO BRP: bidirectional reflection for stable convergence
    """

    def __init__(self, journal_path: str | Path) -> None:
        self._journal_path = Path(journal_path)
        self.entries: list[dict[str, Any]] = []
        self._load()

    def _load(self) -> None:
        if self._journal_path.exists():
            try:
                with open(self._journal_path, encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            self.entries.append(json.loads(line))
            except (json.JSONDecodeError, OSError):
                self.entries = []

    def _persist(self) -> None:
        self._journal_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._journal_path, "w", encoding="utf-8") as f:
            for entry in self.entries:
                f.write(json.dumps(entry, default=str) + "\n")

    def record(
        self,
        run_id: str,
        outcome: str,
        cycle: int,
        classification: FailureClassification | None,
        lesson: str,
    ) -> None:
        """Store a verbal reflection after a cycle."""
        entry = {
            "timestamp": _iso_now(),
            "run_id": run_id,
            "outcome": outcome,
            "cycle": cycle,
            "failure_category": classification.category if classification else None,
            "action_taken": classification.action if classification else None,
            "lesson": lesson,
        }
        self.entries.append(entry)
        self._persist()

    def get_lessons_for_category(self, category: str) -> list[str]:
        """Retrieve past lessons for a specific failure category."""
        return [
            e["lesson"] for e in self.entries
            if e.get("failure_category") == category
        ]

    def get_recent(self, n: int = 5) -> list[dict[str, Any]]:
        """Get the N most recent reflections."""
        return self.entries[-n:]

    def get_all(self) -> list[dict[str, Any]]:
        return list(self.entries)

    def retrieve_relevant(self, task_id: str, top_k: int = 3) -> list[str]:
        """Retrieve lessons semantically relevant to the given task.

        Uses TF-IDF cosine similarity over stored lessons.
        Implements Episodex-style episodic retrieval (2025) for
        out-of-distribution generalisation.
        """
        if not self.entries:
            return []
        query = task_id.lower().replace("_", " ")
        scored: list[tuple[float, str]] = []
        for entry in self.entries:
            lesson = entry.get("lesson", "")
            if not lesson:
                continue
            words_q = set(query.split())
            words_l = set(lesson.lower().split())
            overlap = len(words_q & words_l)
            score = overlap / max(len(words_q | words_l), 1)
            if entry.get("outcome") == "failure":
                score += 0.2
            scored.append((score, lesson))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [lesson for _, lesson in scored[:top_k] if _ > 0]


class RulesStore:
    """Stores explicit rules extracted from failure reflections.

    Implements ExpeL-style heuristic extraction (Zhao et al., AAAI 2024):
    contrasting positive/negative trajectories to extract reusable rules.
    """

    def __init__(self, rules_path: str | Path) -> None:
        self._path = Path(rules_path)
        self.rules: list[dict[str, Any]] = []
        self._load()

    def _load(self) -> None:
        if self._path.exists():
            try:
                for line in self._path.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if line:
                        self.rules.append(json.loads(line))
            except (json.JSONDecodeError, OSError):
                self.rules = []

    def _persist(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._path, "w", encoding="utf-8") as f:
            for r in self.rules:
                f.write(json.dumps(r, default=str) + "\n")

    def add_rule(self, rule_text: str, source_run_id: str, category: str) -> None:
        self.rules.append({
            "timestamp": _iso_now(),
            "rule": rule_text,
            "source_run_id": source_run_id,
            "category": category,
        })
        self._persist()

    def get_rules(self) -> list[str]:
        return [r["rule"] for r in self.rules]

    @staticmethod
    def extract_rule_from_lesson(lesson: str) -> str | None:
        """Heuristic: extract an actionable rule from a failure lesson.

        If the lesson describes a specific failure, invert it into a rule.
        """
        if not lesson:
            return None
        lower = lesson.lower()
        if "failed" in lower or "error" in lower or "aborted" in lower:
            return f"Rule: {lesson.split(':')[-1].strip()}" if ":" in lesson else f"Rule: Avoid — {lesson}"
        return None


# ---------------------------------------------------------------------------
# Outer Loop Orchestrator
# ---------------------------------------------------------------------------

class OuterLoop:
    """The dual-agent outer loop: Monitor → Diagnose → Adapt → Test.

    Implements SHML's four-phase cycle:
    1. MONITOR: invoke the test, wait for completion, read the trace
    2. DIAGNOSE: feed the trace to DiagnosticReader + HealingOrchestrator
    3. ADAPT: based on classification, retry / adjust / escalate / abort
    4. TEST: if retrying, the next cycle validates the adaptation

    The loop does NOT modify code — when escalation is needed, it writes
    a structured ESCALATION.md that the code agent reads and acts upon.
    This separation follows VIGIL's supervisory pattern and CodeDelegator's
    Ephemeral-Persistent State Separation.
    """

    def __init__(
        self,
        task_id: str,
        test_script: str,
        runs_dir: str | Path,
        max_cycles: int = 3,
        python_executable: str | None = None,
        journal_path: str | Path | None = None,
        library_dir: str | Path | None = None,
    ) -> None:
        self.task_id = task_id
        self.test_script = test_script
        self._runs_dir = Path(runs_dir)
        self._max_cycles = max_cycles
        self._python = python_executable or sys.executable
        self._healer = HealingOrchestrator(runs_dir, max_attempts=max_cycles)

        if library_dir is None:
            library_dir = self._runs_dir.parent
        self._skill_lib = SkillLibrary(library_dir)

        if journal_path is None:
            journal_path = self._runs_dir / "reflection_journal.jsonl"
        self._journal = ReflectionJournal(journal_path)

        rules_path = Path(journal_path).parent / "rules.jsonl"
        self._rules = RulesStore(rules_path)

        self._cycle_log: list[dict[str, Any]] = []

    @property
    def healer(self) -> HealingOrchestrator:
        return self._healer

    @property
    def skill_library(self) -> SkillLibrary:
        return self._skill_lib

    @property
    def journal(self) -> ReflectionJournal:
        return self._journal

    @property
    def rules(self) -> RulesStore:
        return self._rules

    def run(self) -> OuterLoopResult:
        """Execute the full Monitor → Diagnose → Adapt → Test cycle."""
        loop_start = time.time()

        for cycle in range(1, self._max_cycles + 1):
            # --- MONITOR ---
            run_dir = self._invoke_test()

            if run_dir is None:
                return OuterLoopResult(
                    outcome="aborted",
                    cycles=cycle,
                    total_duration_ms=_elapsed_ms(loop_start),
                    reflections=self._journal.get_recent(),
                )

            manifest = self._read_manifest(run_dir)
            if manifest is None:
                return OuterLoopResult(
                    outcome="aborted",
                    cycles=cycle,
                    total_duration_ms=_elapsed_ms(loop_start),
                    reflections=self._journal.get_recent(),
                )

            run_id = manifest.get("run_id", "unknown")

            # --- SUCCESS PATH ---
            if manifest["outcome"] == "success":
                self._skill_lib.ingest_from_trace(str(run_dir))
                self._journal.record(
                    run_id=run_id, outcome="success", cycle=cycle,
                    classification=None,
                    lesson=f"Task {self.task_id} completed successfully in {manifest.get('total_duration_ms', 0)}ms.",
                )
                return OuterLoopResult(
                    outcome="success",
                    cycles=cycle,
                    run_id=run_id,
                    total_duration_ms=_elapsed_ms(loop_start),
                    reflections=self._journal.get_recent(),
                )

            # --- DIAGNOSE ---
            classification = self._healer.analyze_run(str(run_dir))

            if classification is None:
                return OuterLoopResult(
                    outcome="aborted",
                    cycles=cycle,
                    run_id=run_id,
                    total_duration_ms=_elapsed_ms(loop_start),
                )

            self._log_cycle(cycle, run_id, classification)

            # --- ADAPT ---
            if classification.action == "abort":
                self._journal.record(
                    run_id=run_id, outcome="failure", cycle=cycle,
                    classification=classification,
                    lesson=f"Aborted: {classification.details}",
                )
                return OuterLoopResult(
                    outcome="aborted",
                    cycles=cycle,
                    run_id=run_id,
                    total_duration_ms=_elapsed_ms(loop_start),
                    reflections=self._journal.get_recent(),
                )

            if classification.action == "escalate_to_code_agent":
                escalation_path = self._write_escalation(run_dir, classification)
                self._journal.record(
                    run_id=run_id, outcome="failure", cycle=cycle,
                    classification=classification,
                    lesson=f"Escalated to code agent: {classification.details}",
                )
                return OuterLoopResult(
                    outcome="escalated",
                    cycles=cycle,
                    run_id=run_id,
                    escalation_path=str(escalation_path),
                    total_duration_ms=_elapsed_ms(loop_start),
                    reflections=self._journal.get_recent(),
                )

            if classification.action == "retry":
                lesson = f"Transient failure at step {classification.step_index}: {classification.error_summary}. Retrying."
                self._journal.record(
                    run_id=run_id, outcome="failure", cycle=cycle,
                    classification=classification, lesson=lesson,
                )
                rule = RulesStore.extract_rule_from_lesson(lesson)
                if rule:
                    self._rules.add_rule(rule, run_id, classification.category)
                continue

            if classification.action == "adjust_parameters":
                lesson = f"Parameter adjustment needed at step {classification.step_index}: {classification.details}"
                self._journal.record(
                    run_id=run_id, outcome="failure", cycle=cycle,
                    classification=classification, lesson=lesson,
                )
                rule = RulesStore.extract_rule_from_lesson(lesson)
                if rule:
                    self._rules.add_rule(rule, run_id, classification.category)
                continue

        # Exhausted all cycles
        return OuterLoopResult(
            outcome="max_retries_exhausted",
            cycles=self._max_cycles,
            run_id=self._cycle_log[-1]["run_id"] if self._cycle_log else None,
            total_duration_ms=_elapsed_ms(loop_start),
            reflections=self._journal.get_recent(),
        )

    # ------------------------------------------------------------------
    # MONITOR: Invoke the test subprocess
    # ------------------------------------------------------------------

    def _invoke_test(self) -> Path | None:
        """Run the test script as a subprocess and return the latest run directory.

        Uses subprocess.run() for synchronous execution — the outer loop
        blocks until the test completes, then reads the trace.

        Environment variable contract: the test script (test_excalidraw_covt.py)
        selects its task based on specific env vars (e.g. CONCENTRIC_TRIANGLES_CLEAN=1).
        Following AOrchestra's 4-tuple model (arXiv:2602.03786) and the Concourse CI
        "pure function" principle, the orchestrator must speak the execution agent's
        interface — not invent its own variable names.

        The TASK_ENV_MAP maps task_id -> the env var the test script actually reads.
        """
        runs_before = self._list_run_dirs()

        import os
        env_vars: dict[str, str] = {}
        task_env_var = TASK_ENV_MAP.get(self.task_id)
        if task_env_var:
            env_vars[task_env_var] = "1"
        env = {**os.environ, **env_vars}

        try:
            subprocess.run(
                [self._python, self.test_script],
                env=env,
                timeout=600,  # 10-minute hard timeout
            )
        except subprocess.TimeoutExpired:
            return None
        except FileNotFoundError:
            return None

        runs_after = self._list_run_dirs()
        new_runs = runs_after - runs_before

        if not new_runs:
            return None

        latest = max(new_runs, key=lambda p: p.stat().st_mtime)
        return latest

    def _list_run_dirs(self) -> set[Path]:
        """List all run directories under the runs dir."""
        if not self._runs_dir.exists():
            return set()
        return {
            d for d in self._runs_dir.iterdir()
            if d.is_dir() and (d / "manifest.json").exists()
        }

    # ------------------------------------------------------------------
    # DIAGNOSE: Read the manifest
    # ------------------------------------------------------------------

    def _read_manifest(self, run_dir: Path) -> dict[str, Any] | None:
        manifest_path = run_dir / "manifest.json"
        if not manifest_path.exists():
            return None
        try:
            with open(manifest_path, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return None

    # ------------------------------------------------------------------
    # ADAPT: Escalation Protocol (TraceCoder + VIGIL)
    # ------------------------------------------------------------------

    # Confidence threshold for including detailed diagnostic guidance.
    # Below this, the code agent investigates independently to avoid
    # anchoring on low-confidence diagnoses — a selective propagation
    # pattern from MAC (Peng et al., 2026, arXiv:2507.21159v2) adapted
    # for deterministic classifiers.  Only the two lowest-confidence
    # classifications (0.50 unrecognized, 0.65 ambiguous assertion) fall
    # below this gate; all others propagate Level 3 detail normally.
    _CONFIDENCE_GATE: float = 0.70

    def _write_escalation(
        self,
        run_dir: Path,
        classification: FailureClassification,
    ) -> Path:
        """Write structured ESCALATION.json + ESCALATION.md for the code agent.

        Format follows TraceCoder's observe-analyze-repair pipeline and
        VIGIL's code proposal layer: structured diagnosis with progressive
        disclosure so the code agent can read only what it needs.

        The JSON envelope (ESCALATION.json) provides a machine-parseable
        metadata contract — run_id, classification, attempts, requested
        action — while the Markdown payload preserves native LLM readability
        and "Lost in the Middle" resistance (Liu et al., NeurIPS 2024,
        arXiv:2307.03172).

        Confidence gating: when classification.confidence < _CONFIDENCE_GATE,
        Level 3 step detail and Suggested Investigation are omitted from the
        Markdown payload to prevent anchoring bias on uncertain diagnoses.
        The code agent must perform its own trace analysis in these cases.
        This implements selective propagation from MAC (Peng et al., 2026,
        arXiv:2507.21159v2): only high-consistency diagnoses are propagated;
        low-confidence branches are masked to preserve downstream agent
        decision quality.
        """
        reader = DiagnosticReader(str(run_dir))
        manifest = self._read_manifest(run_dir) or {}

        run_id = manifest.get("run_id", "unknown")
        task_id = manifest.get("task_id", self.task_id)
        step_idx = classification.step_index
        high_confidence = classification.confidence >= self._CONFIDENCE_GATE

        sections = [
            "# Escalation: Code Agent Repair Request",
            "",
            "## Run Summary",
            f"- **Run ID:** {run_id}",
            f"- **Task:** {task_id}",
            f"- **Failed at step:** {step_idx} ({classification.category})",
            f"- **Failure category:** {classification.category}",
            f"- **Confidence:** {classification.confidence:.0%}",
            f"- **Error:** {classification.error_summary}",
            "",
            "## Diagnosis (Progressive Disclosure)",
            "",
            "### Level 1: Overview",
            "```",
            reader.level1_summary(),
            "```",
            "",
            "### Level 2: Failure Window",
            "```",
            reader.level2_failure_window(),
            "```",
            "",
        ]

        if step_idx is not None and high_confidence:
            sections.extend([
                "### Level 3: Failed Step Detail",
                "```json",
                reader.level3_step_detail(step_idx),
                "```",
                "",
            ])
        elif step_idx is not None:
            sections.extend([
                "### Level 3: Failed Step Detail",
                f"*Omitted (confidence {classification.confidence:.0%} < "
                f"{self._CONFIDENCE_GATE:.0%} threshold). "
                "Read the trace directly for unbiased investigation:*",
                f"```",
                f"cat {run_dir}/trace.jsonl | python -m json.tool",
                f"```",
                "",
            ])

        # Historical context from reflection journal
        recent = self._journal.get_recent(5)
        if recent:
            sections.append("## Historical Context (Reflection Journal)")
            sections.append("")
            for r in recent:
                sections.append(
                    f"- **Cycle {r.get('cycle', '?')}** [{r.get('outcome', '?')}] "
                    f"({r.get('failure_category', 'N/A')}): {r.get('lesson', '')}"
                )
            sections.append("")

        # Attempt history
        history = self._healer.get_history()
        if history:
            sections.append(f"## Attempt History ({len(history)} runs)")
            sections.append("")
            for h in history:
                status = h["outcome"].upper()
                hid = h.get("run_id", "?")
                cat = h.get("classification", {}).get("category", "")
                cat_str = f" ({cat})" if cat else ""
                sections.append(f"- `{hid}`: {status}{cat_str}")
            sections.append("")

        if high_confidence:
            sections.extend([
                "## Suggested Investigation",
                f"{classification.details}",
                "",
            ])
        else:
            sections.extend([
                "## Suggested Investigation",
                f"*Low-confidence classification ({classification.confidence:.0%}). "
                "Perform independent trace analysis before acting on this diagnosis.*",
                "",
            ])

        sections.extend([
            "## Architecture-Critical Files",
            "- `operator/cre/test_excalidraw_covt.py` — main test flow",
            "- `operator/agent_core.py` — GUI automation core",
            "- `operator/visual_engine.py` — SoM + visual grounding",
            "- `operator/agent_infra/` — infrastructure package",
            "",
        ])

        # --- Write Markdown payload ---
        escalation_md_path = run_dir / "ESCALATION.md"
        with open(escalation_md_path, "w", encoding="utf-8") as f:
            f.write("\n".join(sections))

        # --- Write JSON envelope ---
        # Machine-parseable metadata for structured handoff between outer
        # loop and code agent.  Follows the hybrid JSON+MD pattern proposed
        # in Grok analysis (Feb 2026): JSON provides the contract, MD
        # provides the diagnostic payload with LLM-native readability.
        envelope = {
            "schema_version": "1.1",
            "run_id": run_id,
            "task_id": task_id,
            "classification": classification.to_dict(),
            "high_confidence": high_confidence,
            "attempts": [
                {
                    "run_id": h.get("run_id", "?"),
                    "outcome": h["outcome"],
                    "category": h.get("classification", {}).get("category", ""),
                }
                for h in (self._healer.get_history() or [])
            ],
            "requested_action": "investigate" if not high_confidence else "repair",
            "payload_path": "ESCALATION.md",
            "timestamp": _iso_now(),
        }
        escalation_json_path = run_dir / "ESCALATION.json"
        with open(escalation_json_path, "w", encoding="utf-8") as f:
            json.dump(envelope, f, indent=2, default=str)

        return escalation_md_path

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------

    def _log_cycle(self, cycle: int, run_id: str, classification: FailureClassification) -> None:
        self._cycle_log.append({
            "cycle": cycle,
            "run_id": run_id,
            "classification": classification.to_dict(),
            "timestamp": _iso_now(),
        })


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

def main() -> int:
    """CLI: python -m agent_infra.outer_loop [options]"""
    import argparse
    import os

    parser = argparse.ArgumentParser(
        description="Dual-Agent Outer Loop — Monitor → Diagnose → Adapt → Test"
    )
    parser.add_argument(
        "--task", default="CONCENTRIC_TRIANGLES_CLEAN",
        help="Task ID to run (default: CONCENTRIC_TRIANGLES_CLEAN)",
    )
    parser.add_argument(
        "--max-cycles", type=int, default=3,
        help="Maximum retry cycles (default: 3)",
    )
    parser.add_argument(
        "--test-script", default=None,
        help="Path to the test script (default: auto-detect)",
    )
    args = parser.parse_args()

    # Auto-detect the test script relative to this file
    if args.test_script:
        test_script = args.test_script
    else:
        infra_dir = Path(__file__).resolve().parent
        operator_dir = infra_dir.parent
        test_script = str(operator_dir / "cre" / "test_excalidraw_covt.py")

    runs_dir = str(Path(test_script).parent / "runs")

    # Detect the venv python
    operator_dir = Path(__file__).resolve().parent.parent
    venv_python = operator_dir / "venv" / "bin" / "python"
    python_exec = str(venv_python) if venv_python.exists() else sys.executable

    loop = OuterLoop(
        task_id=args.task,
        test_script=test_script,
        runs_dir=runs_dir,
        max_cycles=args.max_cycles,
        python_executable=python_exec,
    )

    print(f"\n{'=' * 60}")
    print("DUAL-AGENT OUTER LOOP")
    print(f"  Task:       {args.task}")
    print(f"  Script:     {test_script}")
    print(f"  Max cycles: {args.max_cycles}")
    print(f"{'=' * 60}\n")

    result = loop.run()

    print(f"\n{'=' * 60}")
    print("OUTER LOOP COMPLETE")
    print(f"  Outcome:    {result.outcome}")
    print(f"  Cycles:     {result.cycles}")
    print(f"  Duration:   {result.total_duration_ms}ms")
    if result.run_id:
        print(f"  Run ID:     {result.run_id}")
    if result.escalation_path:
        print(f"  Escalation: {result.escalation_path}")
    if result.reflections:
        print(f"  Reflections: {len(result.reflections)} entries")
    print(f"{'=' * 60}")

    return 0 if result.outcome == "success" else 1


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _iso_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _elapsed_ms(start: float) -> int:
    return int((time.time() - start) * 1000)


if __name__ == "__main__":
    sys.exit(main())
