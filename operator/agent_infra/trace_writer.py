"""Structured execution trace writer for the dual-agent self-healing loop.

Produces JSONL traces and per-run manifests following the OSWorld/AgentTrek/UI-TARS
schema conventions (arXiv:2404.07972, arXiv:2412.09605, arXiv:2501.12326).

Build-order rationale (AgentTrace, arXiv:2602.10133): structured traces are the
foundation for self-healing — the diagnostic reader (Phase 2) and self-healing
orchestrator (Phase 3) both consume these traces to identify and fix failures.
"""

from __future__ import annotations

import json
import os
import time
import uuid
from pathlib import Path
from typing import Any

_META_ACTION_TYPES = {
    "a11y_passive_snapshot",
    "a11y_snapshot",
    "final_verification_gate",
    "metacognitive_audit",
    "phash_audit",
    "visual_monitor_summary",
}


class TraceStep:
    """One step in an execution trace.

    Captures the full observation-thought-action-result cycle per step,
    following the ReAct pattern used by AgentTrek and SWE-Agent.
    """

    __slots__ = (
        "step_index", "timestamp_start", "timestamp_end", "duration_ms",
        "pre_state", "thought", "action", "action_result", "post_state",
        "model_call", "evaluation",
    )

    def __init__(self, step_index: int) -> None:
        self.step_index = step_index
        self.timestamp_start: str = _iso_now()
        self.timestamp_end: str | None = None
        self.duration_ms: int = 0
        self.pre_state: dict[str, Any] = {}
        self.thought: str = ""
        self.action: dict[str, Any] = {}
        self.action_result: dict[str, Any] = {}
        self.post_state: dict[str, Any] = {}
        self.model_call: dict[str, Any] | None = None
        self.evaluation: dict[str, Any] = {}

    def finalize(self) -> None:
        self.timestamp_end = _iso_now()
        start_epoch = _iso_to_epoch(self.timestamp_start)
        end_epoch = _iso_to_epoch(self.timestamp_end)
        self.duration_ms = max(0, int((end_epoch - start_epoch) * 1000))

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "step": self.step_index,
            "timestamp_start": self.timestamp_start,
            "timestamp_end": self.timestamp_end,
            "duration_ms": self.duration_ms,
            "pre_state": self.pre_state,
            "thought": self.thought,
            "action": self.action,
            "action_result": self.action_result,
            "post_state": self.post_state,
            "evaluation": self.evaluation,
        }
        if self.model_call:
            d["model_call"] = self.model_call
        return d


class TraceWriter:
    """Writes structured JSONL traces and a per-run manifest.

    Usage:
        tw = TraceWriter(output_dir, task_id="CONCENTRIC_TRIANGLES_CLEAN")
        step = tw.begin_step(1)
        step.pre_state = {"screenshot": "path.png", "focused_app": "Safari"}
        step.action = {"type": "clear_canvas", "parameters": {}}
        step.action_result = {"success": True}
        tw.end_step(step)
        tw.finalize(outcome="success")
    """

    def __init__(
        self,
        output_dir: str | Path,
        task_id: str = "",
        task_description: str = "",
        agent_config: dict[str, Any] | None = None,
    ) -> None:
        self._output_dir = Path(output_dir)
        self._run_id = uuid.uuid4().hex[:12]
        self._run_dir = self._output_dir / "runs" / self._run_id
        self._run_dir.mkdir(parents=True, exist_ok=True)
        self._screenshots_dir = self._run_dir / "screenshots"
        self._screenshots_dir.mkdir(exist_ok=True)

        self._task_id = task_id
        self._task_description = task_description
        self._agent_config = agent_config or {}
        self._start_time = _iso_now()
        self._steps: list[dict[str, Any]] = []
        self._failure_step: int | None = None
        self._failure_category: str | None = None
        self._error_summary: str | None = None

        self._trace_path = self._run_dir / "trace.jsonl"
        self._manifest_path = self._run_dir / "manifest.json"

        self._trace_path.write_text("", encoding="utf-8")

    @property
    def run_id(self) -> str:
        return self._run_id

    @property
    def run_dir(self) -> Path:
        return self._run_dir

    @property
    def screenshots_dir(self) -> Path:
        return self._screenshots_dir

    @property
    def trace_path(self) -> Path:
        return self._trace_path

    @property
    def manifest_path(self) -> Path:
        return self._manifest_path

    def begin_step(self, step_index: int) -> TraceStep:
        return TraceStep(step_index)

    def end_step(self, step: TraceStep) -> None:
        """Finalize a step and append it to the trace JSONL file."""
        step.finalize()
        step_dict = step.to_dict()
        self._steps.append(step_dict)
        with open(self._trace_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(step_dict, default=str) + "\n")

    def record_failure(
        self,
        step_index: int,
        category: str,
        error_summary: str,
    ) -> None:
        """Mark a step as the failure point (called at most once per run)."""
        if self._failure_step is None:
            self._failure_step = step_index
            self._failure_category = category
            self._error_summary = error_summary

    def finalize(self, outcome: str = "success") -> dict[str, Any]:
        """Write the manifest and return it.

        Args:
            outcome: one of "success", "failure", "timeout", "error"
        """
        end_time = _iso_now()
        total_duration_ms = max(
            0,
            int((_iso_to_epoch(end_time) - _iso_to_epoch(self._start_time)) * 1000),
        )

        failure_step = self._failure_step
        failure_category = self._failure_category
        error_summary = self._error_summary

        step_stats = _summarize_step_outcomes(self._steps)
        verification_summary = _extract_final_verification_summary(self._steps)

        if failure_step is None and outcome != "success":
            inferred = _infer_failure_from_steps(self._steps, verification_summary)
            if inferred is not None:
                failure_step = inferred["step"]
                failure_category = inferred["category"]
                error_summary = inferred["error_summary"]

        task_result = "accepted" if outcome == "success" else "rejected"
        if verification_summary["status"] == "failed":
            acceptance_basis = "final_verification_failed"
        elif verification_summary["status"] == "passed":
            acceptance_basis = "final_verification_passed"
        elif outcome == "success":
            acceptance_basis = "execution_succeeded_without_final_verification"
        else:
            acceptance_basis = "execution_failed_before_final_verification"

        steps_summary = []
        for s in self._steps:
            result_str = _step_result_label(s)
            action_type = s.get("action", {}).get("type", "unknown")
            steps_summary.append(f"{s['step']}: {action_type} ({result_str})")

        manifest: dict[str, Any] = {
            "run_id": self._run_id,
            "task_id": self._task_id,
            "task_description": self._task_description,
            "agent_config": self._agent_config,
            "environment": {
                "os": "macos",
                "platform": _get_platform_info(),
            },
            "start_time": self._start_time,
            "end_time": end_time,
            "total_duration_ms": total_duration_ms,
            "num_steps": len(self._steps),
            "outcome": outcome,
            "failure_step": failure_step,
            "failure_category": failure_category,
            "error_summary": error_summary,
            "outcome_semantics": {
                "task_result": task_result,
                "execution_result": outcome,
                "acceptance_basis": acceptance_basis,
                "final_verification": verification_summary,
                "step_outcomes": step_stats,
                "consistency": {
                    "accepted_with_failed_steps": (
                        task_result == "accepted" and step_stats["failed"] > 0
                    ),
                    "accepted_with_productive_failures": (
                        task_result == "accepted" and step_stats["productive_failed"] > 0
                    ),
                    "rejected_without_failed_steps": (
                        task_result == "rejected" and step_stats["failed"] == 0
                    ),
                    "rejected_by_final_verification": verification_summary["status"] == "failed",
                    "failure_step_recorded": failure_step is not None,
                },
            },
            "steps_summary": steps_summary,
        }

        with open(self._manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, default=str)

        return manifest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _iso_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()) + f".{int((time.time() % 1) * 1000):03d}Z"


def _iso_to_epoch(iso_str: str) -> float:
    """Parse our ISO timestamp back to epoch seconds."""
    try:
        base = iso_str.split(".")[0].replace("Z", "")
        st = time.strptime(base, "%Y-%m-%dT%H:%M:%S")
        epoch = time.mktime(st) - time.timezone
        millis_part = iso_str.split(".")[1].replace("Z", "") if "." in iso_str else "0"
        return epoch + int(millis_part) / 1000.0
    except (ValueError, IndexError):
        return time.time()


def _get_platform_info() -> str:
    try:
        import platform
        return f"{platform.system()} {platform.release()} ({platform.machine()})"
    except Exception:
        return "unknown"


def _step_result_label(step: dict[str, Any]) -> str:
    action_result = step.get("action_result", {}) or {}
    success = action_result.get("success")
    if success is True:
        return "success"
    if success is False:
        return "failed"
    status = str(action_result.get("status", "")).strip().lower()
    if status in {"skip", "skipped"}:
        return "skipped"
    return "unknown"


def _is_meta_step(step: dict[str, Any]) -> bool:
    return str(step.get("action", {}).get("type", "")).strip() in _META_ACTION_TYPES


def _summarize_step_outcomes(steps: list[dict[str, Any]]) -> dict[str, Any]:
    summary = {
        "total": len(steps),
        "succeeded": 0,
        "failed": 0,
        "skipped": 0,
        "unknown": 0,
        "productive_total": 0,
        "meta_total": 0,
        "productive_failed": 0,
        "meta_failed": 0,
        "failed_step_indices": [],
        "productive_failed_step_indices": [],
        "meta_failed_step_indices": [],
    }
    for step in steps:
        label = _step_result_label(step)
        is_meta = _is_meta_step(step)
        if is_meta:
            summary["meta_total"] += 1
        else:
            summary["productive_total"] += 1

        if label == "success":
            summary["succeeded"] += 1
        elif label == "failed":
            summary["failed"] += 1
            summary["failed_step_indices"].append(step.get("step"))
            if is_meta:
                summary["meta_failed"] += 1
                summary["meta_failed_step_indices"].append(step.get("step"))
            else:
                summary["productive_failed"] += 1
                summary["productive_failed_step_indices"].append(step.get("step"))
        elif label == "skipped":
            summary["skipped"] += 1
        else:
            summary["unknown"] += 1
    return summary


def _extract_final_verification_summary(steps: list[dict[str, Any]]) -> dict[str, Any]:
    verification_step = None
    for step in reversed(steps):
        if step.get("action", {}).get("type") == "final_verification_gate":
            verification_step = step
            break

    if verification_step is None:
        return {
            "status": "not_run",
            "step": None,
            "passed": None,
            "score": None,
            "verdict": "",
            "deficiencies_count": 0,
        }

    post_state = verification_step.get("post_state", {}) or {}
    passed = bool(verification_step.get("action_result", {}).get("success", False))
    return {
        "status": "passed" if passed else "failed",
        "step": verification_step.get("step"),
        "passed": passed,
        "score": post_state.get("score"),
        "verdict": post_state.get("verdict", ""),
        "deficiencies_count": len(post_state.get("deficiencies", []) or []),
    }


def _infer_failure_from_steps(
    steps: list[dict[str, Any]],
    verification_summary: dict[str, Any],
) -> dict[str, Any] | None:
    if verification_summary.get("status") == "failed":
        verdict = verification_summary.get("verdict") or "Final verification failed"
        return {
            "step": verification_summary.get("step"),
            "category": "verification_failed",
            "error_summary": verdict,
        }

    for step in steps:
        if _step_result_label(step) != "failed":
            continue
        action_type = str(step.get("action", {}).get("type", "")).strip()
        action_result = step.get("action_result", {}) or {}
        error = (
            str(action_result.get("error", "")).strip()
            or str(step.get("evaluation", {}).get("actual", "")).strip()
            or f"Step {step.get('step')} failed"
        )
        category = "meta_step_failed" if _is_meta_step(step) else "step_failed"
        return {
            "step": step.get("step"),
            "category": category,
            "error_summary": f"{action_type}: {error}" if action_type else error,
        }

    return None
