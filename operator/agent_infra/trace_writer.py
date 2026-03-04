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

        steps_summary = []
        for s in self._steps:
            result_str = "success" if s.get("action_result", {}).get("success") else "failed"
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
            "failure_step": self._failure_step,
            "failure_category": self._failure_category,
            "error_summary": self._error_summary,
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
