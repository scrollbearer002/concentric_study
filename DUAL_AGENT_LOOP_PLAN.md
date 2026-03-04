# Dual-Agent Self-Healing Loop — Build Plan

## Research Foundation

This plan is grounded in 8 peer-reviewed papers. Each sub-step cites the paper
that justifies *why* we build it that way.

| # | Paper | Venue | Key Principle We Use |
|---|-------|-------|---------------------|
| 1 | VIGIL (Cruz, 2025) | arXiv:2512.07094 | Stage-gated supervisory pipeline; structured JSONL log ingestion; code proposals as unified diffs |
| 2 | SHML (Rauba et al., 2024) | NeurIPS 2024, arXiv:2411.00186 | Monitor → Diagnose → Adapt → Test cycle as prerequisite for self-healing |
| 3 | TraceCoder (2025) | ICSE 2026, arXiv:2602.06875 | Observe-Analyze-Repair with Historical Lesson Learning; rollback mechanism |
| 4 | COCO (2025) | arXiv:2508.13815 | Contextual Rollback Mechanism preserving execution history; Bidirectional Reflection Protocol |
| 5 | Reflexion (Shinn et al., 2023) | NeurIPS 2023, arXiv:2303.11366 | Verbal self-reflection stored in episodic memory; 91% pass@1 via reflection loop |
| 6 | ICE (Qian et al., 2024) | arXiv:2401.13996 | Investigate → Consolidate → Exploit; inter-task knowledge transfer |
| 7 | Voyager (Wang et al., 2023) | arXiv:2305.16291 | Skill library with iterative prompting; feedback loop before curriculum |
| 8 | RepairAgent (2024) | arXiv:2403.17134 | Finite state machine for escalation policy; tool selection via diagnosis |

---

## Related Work and Validation Tiers

This section summarizes what is **implemented** versus **proposed** in the current codebase and aligns each component with the validation tiers (Direct / Analogous / Novel) used in the architectural audit. For pairing-level citations and tool-by-tool evidence, see **POTENTIAL_CHANGES.md** § "PhD Evidence: Which Tool Combinations Have Proven Success Together."

**Validation tier note:** This plan mixes three evidence levels:
1. components directly implemented and exercised in the current runtime,
2. components implemented on the universal-agent path or in selected demos/tests but not universal across every entrypoint,
3. proposed design work not yet in the hot path.

Treat current runtime-health and architecture-health claims as subordinate to the
live repo tests and architecture-conformance checks.

**Implemented (in the runtime today):**

- **Bi-channel perception fusion:** a11y (macOS accessibility tree) + SoM (visual overlay) merged in `element_map.py`; no DOM channel. Validation: Direct (OSWorld, SeeAct, UGround use visual + structural; we use two channels).
- **Trace-driven outer loop:** JSONL traces + manifest, DiagnosticReader, HealingOrchestrator, SkillLibrary ingest on success, ReflectionJournal and RulesStore. Validation: Direct (VIGIL, AutoRefine, TRAIL, ReDel).
- **Beta-Binomial verification gating:** `action_trust.py` — skip VLM assertion when posterior lower bound exceeds threshold. Validation: Direct (BetaConform, Beta Reputation, Learning to Trust).
- **Model-tier inference routing:** `inference_router.py` — Flash/Pro/Local by task type, EMA-based promotion/demotion, persistence. Validation: Analogous (FrugalGPT validates cascade; we apply to VLM task types).
- **Pydantic/Gemini structured outputs:** `agent_core.py` — TargetExtraction, UIAnalysis, etc. Validation: Direct (PydanticAI, Gemini API).
- **Skill library with maturity and staleness:** candidate → proven → master; staleness window (simplified ACT-R). Validation: Direct (MemSkill, Voyager).

**Proposed (design / not yet in hot path):**

- **Tri-channel fusion:** DOM + a11y + visual in one queryable graph. Current system is bi-channel (a11y + visual). Validation: Novel (published systems use at most two channels).
- **Modality-driven FrugalGPT cascade:** Cascade by perception channel (try DOM/a11y first, escalate to VLM). Current routing is by **model tier** for a given task, not by modality. Validation: Novel application.
- **Asynchronous closed-loop observer:** Quartz actuator + Hammerspoon observer for sub-20ms feedback. Current design is synchronous observe–plan–act; Hammerspoon in legacy mode is actuator only. Validation: Analogous (DeepLabCut-Live, Syntalos); novel macOS combination.

**Compact validation table (source: POTENTIAL_CHANGES.md Summary):**

| # | Component | Evidence | Notes |
|---|-----------|----------|--------|
| 1 | Screenshot + SoM + VLM | Direct | OmniParser, ScreenAgent |
| 2 | Gemini + Pydantic | Direct | PydanticAI, Google API |
| 3 | JSONL + self-healing + skills | Direct | VIGIL, AutoRefine, TRAIL |
| 4 | Beta-Binomial + verify skip | Direct | BetaConform, Beta Reputation |
| 5 | pHash + coord cache | Analogous | GUI-KV, PHASER |
| 6 | ACT-R decay + staleness | Direct | MemSkill |
| 7 | Quartz + Hammerspoon observer | Analogous / Novel | DeepLabCut-Live; novel on macOS |
| 8 | Minimum-jerk + OS events | Analogous | BeCAPTCHA-Mouse; not yet implemented |
| 9 | DOM + a11y + visual fusion | Direct (2-channel) / Novel (3-channel) | We have 2-channel; 3-channel proposed |
| 10 | FrugalGPT → perception cascade | Analogous / Novel | We have model-tier cascade; modality cascade proposed |

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                    OUTER-LOOP ORCHESTRATOR                       │
│                  (operator/agent_infra/outer_loop.py)            │
│                                                                  │
│  ┌──────────┐    ┌──────────────┐    ┌─────────────────┐        │
│  │ Run      │───>│ Analyze      │───>│ Decide           │        │
│  │ (invoke  │    │ (Diagnostic  │    │ (Healing         │        │
│  │  test)   │    │  Reader)     │    │  Orchestrator)   │        │
│  └──────────┘    └──────────────┘    └────────┬────────┘        │
│       ▲                                       │                  │
│       │           ┌───────────────────────────┼──────────┐       │
│       │           │                           ▼          │       │
│       │     ┌─────┴─────┐  ┌──────────┐  ┌──────────┐   │       │
│       │     │ retry     │  │ adjust   │  │ escalate │   │       │
│       │     │ (re-run   │  │ params   │  │ to code  │   │       │
│       │     │  same)    │  │ (tweak)  │  │ agent    │   │       │
│       │     └─────┬─────┘  └────┬─────┘  └────┬─────┘   │       │
│       │           │             │              │         │       │
│       └───────────┴─────────────┘              │         │       │
│                                                ▼         │       │
│                                    ┌──────────────────┐  │       │
│                                    │ Write diagnosis  │  │       │
│                                    │ to escalation    │  │       │
│                                    │ file for code    │  │       │
│                                    │ agent to read    │  │       │
│                                    └──────────────────┘  │       │
│                                                          │       │
│  On success: SkillLibrary.ingest_from_trace()            │       │
│  On abort:   Write post-mortem + halt                    │       │
└──────────────────────────────────────────────────────────────────┘
```

---

## What Exists Today (No Changes Needed)

| Module | Location | Status |
|--------|----------|--------|
| `TraceWriter` | `agent_infra/trace_writer.py` | DONE — writes JSONL + manifest |
| `DiagnosticReader` | `agent_infra/diagnostic_reader.py` | DONE — progressive disclosure L1/L2/L3 |
| `HealingOrchestrator` | `agent_infra/healing_orchestrator.py` | DONE — classify + recommend action |
| `SkillLibrary` | `agent_infra/skill_library.py` | DONE — ingest, maturity gating, retrieval |
| `test_excalidraw_covt.py` | `operator/cre/` | DONE — writes traces, returns exit code |
| Cursor Rules | `.cursor/rules/concentric-study.mdc` | DONE — agent governance |
| `AGENTS.md` | project root | DONE — universal agent instructions |

---

## What We Build — 5 Sub-Steps

### Sub-Step A1: Outer-Loop Runner

**File:** `operator/agent_infra/outer_loop.py`

**What it does:** Invokes the test as a subprocess, waits for completion,
reads the exit code and trace directory. This is the "Monitor" phase of SHML.

**Research basis:** SHML (Rauba et al., 2024) — "Monitoring detects performance
decreases." VIGIL (Cruz, 2025) — "Observation Layer captures runtime behavior
as structured JSONL event logs."

**Design:**

```python
class OuterLoop:
    def __init__(self, task_id: str, test_script: str, runs_dir: str,
                 max_cycles: int = 3):
        self.task_id = task_id
        self.test_script = test_script
        self.runs_dir = runs_dir
        self.max_cycles = max_cycles
        self.healer = HealingOrchestrator(runs_dir, max_attempts=max_cycles)
        self.skill_lib = SkillLibrary(runs_dir)
        self.cycle_log: list[dict] = []

    def run_cycle(self) -> OuterLoopResult:
        """Execute one full Monitor→Diagnose→Adapt→Test cycle."""
        for cycle in range(self.max_cycles):
            # MONITOR: run the test
            run_dir = self._invoke_test()

            # DIAGNOSE: read the trace
            manifest = self._read_manifest(run_dir)

            if manifest["outcome"] == "success":
                # SUCCESS PATH: ingest skill, return
                self.skill_lib.ingest_from_trace(run_dir)
                return OuterLoopResult(outcome="success", cycles=cycle+1,
                                       run_id=manifest["run_id"])

            # FAILURE PATH: classify
            classification = self.healer.analyze_run(run_dir)

            if classification.action == "retry":
                # Log and retry (next iteration)
                continue

            if classification.action == "adjust_parameters":
                # Write parameter adjustment hint for next run
                self._write_param_adjustment(classification)
                continue

            if classification.action == "escalate_to_code_agent":
                # Generate diagnosis document for code agent
                diagnosis = self.healer.get_diagnostic_for_code_agent(run_dir)
                self._write_escalation(diagnosis, classification)
                return OuterLoopResult(outcome="escalated",
                                       cycles=cycle+1,
                                       run_id=manifest["run_id"],
                                       escalation_path=self._escalation_path)

            if classification.action == "abort":
                return OuterLoopResult(outcome="aborted", cycles=cycle+1,
                                       run_id=manifest["run_id"])

        return OuterLoopResult(outcome="max_retries_exhausted",
                               cycles=self.max_cycles)
```

**Key methods:**
- `_invoke_test()` — `subprocess.run()` with the test script, returns the
  latest run directory by checking `runs/` after completion.
- `_read_manifest(run_dir)` — loads `manifest.json`.
- `_write_escalation(diagnosis, classification)` — writes a structured
  Markdown file that a code agent can read.

**Test:** Unit test with mock subprocess that simulates success, retry, and
escalation paths.

---

### Sub-Step A2: Escalation Protocol

**File:** `operator/agent_infra/outer_loop.py` (within OuterLoop class)

**What it does:** When HealingOrchestrator says "escalate_to_code_agent",
produces a structured diagnosis document that contains everything a code
agent needs to understand and fix the problem — without reading the entire
codebase.

**Research basis:** TraceCoder (ICSE 2026) — "Causal analysis on runtime traces
to accurately identify root causes." VIGIL (Cruz, 2025) — "Code proposals as
unified diffs based on log evidence and code hotspots." RepairAgent (2024) —
"Finite state machine for escalation policy."

**Output format:** `operator/cre/runs/<run_id>/ESCALATION.md`

```markdown
# Escalation: Code Agent Repair Request

## Run Summary
- Run ID: {run_id}
- Task: {task_id}
- Failed at step: {step_index} ({action_type})
- Failure category: {category}
- Confidence: {confidence}

## Diagnosis (Progressive Disclosure)

### Level 1: Overview
{DiagnosticReader.level1_summary()}

### Level 2: Failure Window
{DiagnosticReader.level2_failure_window()}

### Level 3: Failed Step Detail
{DiagnosticReader.level3_step_detail(step_index)}

## Historical Context
- Previous attempts this cycle: {attempts}
- Previous failure categories: {history}
- Skill Library status: {skill_status}

## Suggested Investigation
{classification.details}

## Architecture-Critical Files
(from AGENTS.md — do not modify without understanding dependencies)
- operator/cre/test_excalidraw_covt.py
- operator/agent_core.py
- operator/visual_engine.py
```

**Test:** Unit test that verifies the escalation document is well-formed and
contains all required sections.

---

### Sub-Step A3: Reflection Journal

**File:** `operator/agent_infra/outer_loop.py` (ReflectionJournal class)

**What it does:** After each cycle (success or failure), records a verbal
self-reflection. On retry, the reflection is fed back as context so the
system doesn't repeat the same mistake.

**Research basis:** Reflexion (Shinn et al., NeurIPS 2023) — "Agents verbally
reflect on task failures and maintain these reflections in episodic memory."
TraceCoder (ICSE 2026) — "Historical Lesson Learning Mechanism to prevent
repeated mistakes." COCO (2025) — "Bidirectional Reflection Protocol."

**Design:**

```python
class ReflectionJournal:
    def __init__(self, journal_path: str | Path):
        self.journal_path = Path(journal_path)
        self.entries: list[dict] = []

    def record(self, run_id: str, outcome: str, cycle: int,
               classification: FailureClassification | None,
               lesson: str) -> None:
        """Store a verbal reflection after each cycle."""
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "run_id": run_id,
            "outcome": outcome,
            "cycle": cycle,
            "failure_category": classification.category if classification else None,
            "action_taken": classification.action if classification else None,
            "lesson": lesson,  # Natural language: what went wrong and why
        }
        self.entries.append(entry)
        self._persist()

    def get_lessons_for_category(self, category: str) -> list[str]:
        """Retrieve past lessons for a failure category."""
        return [e["lesson"] for e in self.entries
                if e["failure_category"] == category]

    def get_recent(self, n: int = 5) -> list[dict]:
        """Get the N most recent reflections."""
        return self.entries[-n:]
```

**Storage:** `operator/cre/reflection_journal.jsonl` — one JSON object per
line, append-only.

**Integration:** The OuterLoop reads recent reflections before each retry
and includes them in the escalation document for context.

**Test:** Unit test verifying persistence, retrieval by category, and
recency filtering.

---

### Sub-Step A4: Run Result Dataclass + CLI Entry Point

**File:** `operator/agent_infra/outer_loop.py` (OuterLoopResult + CLI)

**What it does:** Clean return type from the outer loop, plus a command-line
entry point so the loop can be invoked from terminal or by another agent.

**Research basis:** SHML (Rauba et al., 2024) — "Testing evaluates strategy
effectiveness." Magentic-One (Microsoft, 2024) — "Orchestrator tracks progress
and re-plans."

**Design:**

```python
@dataclass
class OuterLoopResult:
    outcome: str  # "success" | "escalated" | "aborted" | "max_retries_exhausted"
    cycles: int
    run_id: str | None = None
    escalation_path: str | None = None  # path to ESCALATION.md if escalated
    total_duration_ms: int | None = None
    reflections: list[dict] | None = None


def main() -> int:
    """CLI entry point: python -m agent_infra.outer_loop [task_id]"""
    import argparse
    parser = argparse.ArgumentParser(description="Dual-Agent Outer Loop")
    parser.add_argument("--task", default="CONCENTRIC_TRIANGLES_CLEAN")
    parser.add_argument("--max-cycles", type=int, default=3)
    args = parser.parse_args()

    loop = OuterLoop(
        task_id=args.task,
        test_script="operator/cre/test_excalidraw_covt.py",
        runs_dir="operator/cre/runs",
        max_cycles=args.max_cycles,
    )
    result = loop.run_cycle()

    print(f"\n{'='*60}")
    print(f"OUTER LOOP COMPLETE")
    print(f"  Outcome: {result.outcome}")
    print(f"  Cycles:  {result.cycles}")
    if result.escalation_path:
        print(f"  Escalation: {result.escalation_path}")
    print(f"{'='*60}")

    return 0 if result.outcome == "success" else 1
```

**Test:** Integration test that mocks subprocess to verify the full
Monitor → Diagnose → Adapt → Test cycle.

---

### Sub-Step A5: Integration Test — The Full Loop on Known Failure

**What it does:** Validates the entire dual-agent loop end-to-end using a
*simulated* failure trace (so we don't need a real GUI run during testing).

**Research basis:** SHML (Rauba et al., 2024) — "The Monitor → Diagnose →
Adapt → Test cycle must be validated on known failures first." Reflexion
(Shinn et al., 2023) — "Validated on single domain first, then generalized."

**Test scenarios:**

1. **Happy path:** Mock subprocess returns exit code 0. Outer loop reads
   trace, confirms success, ingests into SkillLibrary. Assert: 1 cycle,
   outcome="success".

2. **Transient failure + retry:** Mock subprocess returns exit code 1 on
   first call (with a trace whose failure_category="transient"), then
   exit code 0 on second call. Assert: 2 cycles, outcome="success",
   reflection journal has 1 failure entry.

3. **Escalation:** Mock subprocess returns exit code 1 with
   failure_category="logic". HealingOrchestrator classifies as
   "escalate_to_code_agent". Assert: outcome="escalated",
   ESCALATION.md exists and contains all required sections.

4. **Max retries exhausted:** Mock subprocess always returns exit code 1
   with failure_category="transient". Assert: 3 cycles,
   outcome="max_retries_exhausted".

5. **Reflection accumulation:** Run scenario 2. Verify the reflection
   journal contains the failure lesson and it's retrieved by category.

---

## Build Order and Testing Strategy

| Step | What | Test Before Proceeding | Research Citation |
|------|------|----------------------|-------------------|
| A1 | OuterLoop runner (invoke + monitor) | Unit test: mock subprocess success/failure | SHML Monitor phase |
| A2 | Escalation protocol (write ESCALATION.md) | Unit test: document structure validation | TraceCoder, VIGIL, RepairAgent |
| A3 | ReflectionJournal (episodic memory) | Unit test: persist, retrieve by category | Reflexion, TraceCoder HLLM, COCO BRP |
| A4 | OuterLoopResult + CLI entry point | Unit test: argparse, return codes | SHML Test phase, Magentic-One |
| A5 | Full integration test (all 5 scenarios) | Integration test: end-to-end loop | SHML full cycle, Reflexion |

Each sub-step is tested in isolation before building the next.
No sub-step depends on real GUI execution (all tests use mock subprocess).
The loop is validated against known failure patterns from run `814800d58cab`.

---

## What This Enables

Once A1–A5 are complete and all tests pass:

1. You can run `python -m agent_infra.outer_loop` and it will:
   - Execute the test
   - If it passes: ingest the skill, report success
   - If it fails transiently: retry up to 3 times
   - If it fails structurally: write an ESCALATION.md with full diagnosis
   - Record a reflection after every cycle

2. When ESCALATION.md is written, **I** (the code agent) can read it,
   understand exactly what failed and why, and write a targeted fix —
   without you needing to copy-paste terminal output.

3. The Reflection Journal prevents blind retries — each retry has context
   from previous failures, matching Reflexion's 91% improvement pattern.

4. After this is validated, we move to **Phase B: Task Generalization** —
   the loop will automatically catch whatever breaks on new tasks.

---

## Files Created/Modified

| Action | File |
|--------|------|
| CREATE | `operator/agent_infra/outer_loop.py` |
| MODIFY | `operator/agent_infra/__init__.py` (add OuterLoop, ReflectionJournal, OuterLoopResult to exports) |
| CREATE | `operator/cre/tests/test_outer_loop.py` (unit + integration tests) |
| MODIFY | `.cursor/rules/concentric-study.mdc` (add outer loop usage instructions) |
| MODIFY | `AGENTS.md` (add outer loop section) |
