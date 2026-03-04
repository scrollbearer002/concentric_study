"""Trajectory summarizer with folding and token-budget enforcement.

Implements the Summarizer role from OpAgent (arXiv:2602.13559, 2026) and
trajectory folding from MemoBrain (arXiv:2601.08079, 2026).  Completed
sub-tasks are collapsed into single-line entries so the VLM receives a
compact "Context So Far" prefix that stays under a configurable token
budget (default 500 tokens, ~375 words).

Context-Folding (arXiv:2510.11967, 2025) shows that 62.0% accuracy on
BrowseComp-Plus is achievable within a 32K-token window when prior
trajectory segments are aggressively folded.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


_APPROX_CHARS_PER_TOKEN = 4

_FOLD_PROMPT = (
    "Compress the following execution summary into a single dense paragraph "
    "under {budget} tokens (~{chars} characters).  Preserve: (1) which steps "
    "succeeded, (2) which failed and why, (3) current UI state, (4) what remains.  "
    "Do NOT include step numbers or timestamps.\n\n{text}"
)


class Summarizer:
    """Incrementally summarises a running execution trace.

    Usage::

        s = Summarizer()
        s.ingest_step(step_dict)        # call after each step completes
        context = s.get_context()       # inject into the next VLM prompt
    """

    def __init__(
        self,
        token_budget: int = 500,
        vlm_compress: Any | None = None,
    ) -> None:
        self._budget = token_budget
        self._char_budget = token_budget * _APPROX_CHARS_PER_TOKEN
        self._vlm_compress = vlm_compress
        self._entries: list[str] = []
        self._folded_prefix: str = ""

    def ingest_step(self, step: dict[str, Any]) -> None:
        idx = step.get("step", "?")
        action = step.get("action", {})
        action_type = action.get("type", action.get("description", "unknown"))
        params = action.get("parameters", {})
        result = step.get("action_result", {})
        ok = result.get("success", False)
        status = "OK" if ok else "FAIL"
        detail = ""
        if not ok:
            detail = f" — {result.get('error', '')}"[:80]

        param_summary = ""
        if params:
            parts = [f"{k}={v}" for k, v in list(params.items())[:3]]
            param_summary = f"({', '.join(parts)})"

        line = f"[{idx}] {action_type}{param_summary}: {status}{detail}"
        self._entries.append(line)

    def ingest_from_trace_file(self, trace_path: str | Path) -> None:
        p = Path(trace_path)
        if not p.exists():
            return
        for raw in p.read_text(encoding="utf-8").splitlines():
            raw = raw.strip()
            if not raw:
                continue
            try:
                self.ingest_step(json.loads(raw))
            except json.JSONDecodeError:
                continue

    def get_context(self) -> str:
        if not self._entries and not self._folded_prefix:
            return ""
        body = "\n".join(self._entries)
        full = f"{self._folded_prefix}\n{body}".strip() if self._folded_prefix else body

        if len(full) <= self._char_budget:
            return full

        if self._vlm_compress is not None:
            return self._compress_with_vlm(full)

        return self._compress_heuristic(full)

    def _compress_heuristic(self, text: str) -> str:
        """Fold the oldest half of entries into a one-line summary."""
        if len(self._entries) <= 2:
            return text[: self._char_budget]

        mid = len(self._entries) // 2
        old_entries = self._entries[:mid]
        ok_count = sum(1 for e in old_entries if ": OK" in e)
        fail_count = len(old_entries) - ok_count
        fold_line = f"[Steps 1–{mid}] {ok_count} passed, {fail_count} failed."
        self._folded_prefix = (
            f"{self._folded_prefix}\n{fold_line}".strip()
            if self._folded_prefix
            else fold_line
        )
        self._entries = self._entries[mid:]
        return self.get_context()

    def _compress_with_vlm(self, text: str) -> str:
        """Use the injected VLM callable to abstractively compress."""
        prompt = _FOLD_PROMPT.format(
            budget=self._budget,
            chars=self._char_budget,
            text=text,
        )
        try:
            result = self._vlm_compress(prompt)
            if isinstance(result, str) and len(result) <= self._char_budget:
                self._folded_prefix = result
                self._entries.clear()
                return result
        except Exception:
            pass
        return self._compress_heuristic(text)

    def reset(self) -> None:
        self._entries.clear()
        self._folded_prefix = ""
