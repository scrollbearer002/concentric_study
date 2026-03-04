"""Diagnostic reader for structured execution traces.

Implements progressive disclosure (RCI, arXiv:2303.17491): the diagnosing agent
starts with a compact summary and can drill into specific steps on demand.

Addresses the "Lost in the Middle" problem (arXiv:2307.03172) by placing the
most diagnostic information (error messages, failure steps) at the beginning
and end of the output, not buried in the middle of a long trace.

Build-order rationale: Phase 2 depends on Phase 1 (TraceWriter) and is required
by Phase 3 (Self-Healing Loop) which consumes diagnostic output.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class DiagnosticReader:
    """Reads a structured trace run directory and produces diagnostic output
    at three levels of detail for consumption by the code agent.

    Level 1: Manifest summary (~200-500 tokens)
    Level 2: Failure window — steps around the failure point (~2,000-5,000 tokens)
    Level 3: Full step detail for a specific step (variable)
    """

    def __init__(self, run_dir: str | Path) -> None:
        self._run_dir = Path(run_dir)
        self._manifest_path = self._run_dir / "manifest.json"
        self._trace_path = self._run_dir / "trace.jsonl"
        self._manifest: dict[str, Any] | None = None
        self._steps: list[dict[str, Any]] | None = None

    def _load_manifest(self) -> dict[str, Any]:
        if self._manifest is None:
            with open(self._manifest_path, encoding="utf-8") as f:
                self._manifest = json.load(f)
        return self._manifest

    def _load_steps(self) -> list[dict[str, Any]]:
        if self._steps is None:
            self._steps = []
            with open(self._trace_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        self._steps.append(json.loads(line))
        return self._steps

    # ------------------------------------------------------------------
    # Level 1: Manifest Summary
    # ------------------------------------------------------------------

    def level1_summary(self) -> str:
        """Compact diagnostic summary from the manifest only.

        Designed to be under 500 tokens. The diagnosing agent reads this first
        to decide whether to drill deeper.
        """
        m = self._load_manifest()
        lines = [
            f"=== RUN SUMMARY: {m['run_id']} ===",
            f"Task: {m['task_id']} — {m['task_description']}",
            f"Outcome: {m['outcome'].upper()}",
            f"Steps: {m['num_steps']} | Duration: {m['total_duration_ms']}ms",
            f"Agent: {json.dumps(m.get('agent_config', {}))}",
        ]

        if m["outcome"] != "success":
            lines.append(f"FAILURE at step {m['failure_step']}: {m['failure_category']}")
            lines.append(f"Error: {m['error_summary']}")

        lines.append("")
        lines.append("Steps overview:")
        for s in m.get("steps_summary", []):
            lines.append(f"  {s}")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Level 2: Failure Window
    # ------------------------------------------------------------------

    def level2_failure_window(self, window: int = 2) -> str:
        """Expanded view of steps around the failure point.

        Shows [failure - window, failure + window] steps with full detail.
        Designed to be 2,000-5,000 tokens. Returns the full trace summary
        if no failure was recorded.
        """
        m = self._load_manifest()
        steps = self._load_steps()

        if not steps:
            return "No steps recorded in trace."

        failure_step = m.get("failure_step")
        if failure_step is None:
            return self._format_all_steps_compact(steps)

        failure_idx = None
        for i, s in enumerate(steps):
            if s["step"] == failure_step:
                failure_idx = i
                break

        if failure_idx is None:
            return self._format_all_steps_compact(steps)

        start = max(0, failure_idx - window)
        end = min(len(steps), failure_idx + window + 1)
        window_steps = steps[start:end]

        lines = [
            f"=== FAILURE WINDOW: steps {steps[start]['step']}-{steps[end-1]['step']} ===",
            f"(Failure at step {failure_step}: {m.get('error_summary', 'unknown')})",
            "",
        ]

        for s in window_steps:
            is_failure = s["step"] == failure_step
            marker = ">>> FAILED >>>" if is_failure else ""
            lines.append(f"--- Step {s['step']} {marker} ---")
            lines.append(f"  Thought: {s.get('thought', 'N/A')}")
            lines.append(f"  Action: {json.dumps(s.get('action', {}))}")
            lines.append(f"  Result: {json.dumps(s.get('action_result', {}))}")
            if s.get("evaluation"):
                ev = s["evaluation"]
                lines.append(f"  Expected: {ev.get('expected', 'N/A')}")
                lines.append(f"  Actual: {ev.get('actual', 'N/A')}")
                lines.append(f"  Match: {ev.get('match', 'N/A')}")
            if s.get("pre_state"):
                lines.append(f"  Pre-state: {json.dumps(s['pre_state'])}")
            if s.get("post_state"):
                lines.append(f"  Post-state: {json.dumps(s['post_state'])}")
            if s.get("model_call"):
                mc = s["model_call"]
                lines.append(f"  Model: {mc.get('model', 'N/A')} | Tokens: {mc.get('input_tokens', '?')}/{mc.get('output_tokens', '?')} | Latency: {mc.get('latency_ms', '?')}ms")
            lines.append(f"  Duration: {s.get('duration_ms', 0)}ms")
            lines.append("")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Level 3: Full Step Detail
    # ------------------------------------------------------------------

    def level3_step_detail(self, step_index: int) -> str:
        """Full detail for a single step. Used when Level 2 is insufficient."""
        steps = self._load_steps()

        for s in steps:
            if s["step"] == step_index:
                return json.dumps(s, indent=2, default=str)

        return f"Step {step_index} not found in trace."

    # ------------------------------------------------------------------
    # Convenience: Full Diagnostic Report
    # ------------------------------------------------------------------

    def full_diagnostic(self, window: int = 2) -> str:
        """Combined Level 1 + Level 2 output for a complete diagnostic.

        Following the "Lost in the Middle" paper's recommendation: diagnostic
        summary at the top, detailed failure window in the middle, and a
        concise action recommendation at the bottom.
        """
        m = self._load_manifest()
        parts = [self.level1_summary()]

        if m["outcome"] != "success":
            parts.append("")
            parts.append(self.level2_failure_window(window=window))
            parts.append("")
            parts.append(self._action_recommendation(m))

        return "\n".join(parts)

    # ------------------------------------------------------------------
    # Analysis Helpers
    # ------------------------------------------------------------------

    def get_failure_step_data(self) -> dict[str, Any] | None:
        """Return the raw step dict for the failure step, or None."""
        m = self._load_manifest()
        failure_step = m.get("failure_step")
        if failure_step is None:
            return None
        steps = self._load_steps()
        for s in steps:
            if s["step"] == failure_step:
                return s
        return None

    def get_all_failed_steps(self) -> list[dict[str, Any]]:
        """Return all steps where action_result.success is False."""
        steps = self._load_steps()
        return [s for s in steps if not s.get("action_result", {}).get("success", True)]

    def get_success_rate(self) -> float:
        """Return the fraction of steps that succeeded."""
        steps = self._load_steps()
        if not steps:
            return 0.0
        succeeded = sum(1 for s in steps if s.get("action_result", {}).get("success", False))
        return succeeded / len(steps)

    def estimate_token_count(self, text: str) -> int:
        """Rough token estimate (~4 chars per token for English/JSON)."""
        return len(text) // 4

    # ------------------------------------------------------------------
    # Internal Helpers
    # ------------------------------------------------------------------

    def _format_all_steps_compact(self, steps: list[dict[str, Any]]) -> str:
        lines = ["=== ALL STEPS (compact) ===", ""]
        for s in steps:
            result_str = "OK" if s.get("action_result", {}).get("success") else "FAILED"
            action_type = s.get("action", {}).get("type", "unknown")
            lines.append(f"  Step {s['step']}: {action_type} -> {result_str} ({s.get('duration_ms', 0)}ms)")
        return "\n".join(lines)

    def _action_recommendation(self, manifest: dict[str, Any]) -> str:
        """Generate a concise action recommendation based on failure metadata."""
        category = manifest.get("failure_category", "unknown")
        error = manifest.get("error_summary", "unknown error")

        recommendations = {
            "grounding_error": "RECOMMENDATION: Visual grounding failed. Check if UI layout changed. Consider AX API fallback or iterative grounding refinement.",
            "action_failed": "RECOMMENDATION: Action execution failed after retries. Review the action handler code and check if the target element is accessible.",
            "non_recoverable_error": "RECOMMENDATION: Non-recoverable error. Check for environment issues (app crash, network failure, permission denied).",
            "launch_failure": "RECOMMENDATION: Application launch failed. Verify Safari is installed and Excalidraw URL is accessible.",
            "timeout": "RECOMMENDATION: Operation timed out. Check if the application is responsive and increase timeout if needed.",
        }

        rec = recommendations.get(category, f"RECOMMENDATION: Investigate failure category '{category}': {error}")
        return rec
