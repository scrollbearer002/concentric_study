#!/usr/bin/env python3
"""Dynamic execution architecture regression tests.

These tests keep the runtime-architecture recovery reproducible over the live
run corpus. They follow the same evidence-first posture as the rest of the
project-understanding suite: the generator must rebuild from real manifests and
traces, and the resulting view must remain internally consistent.
"""

from __future__ import annotations

import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent / "project_understanding" / "tools"
sys.path.insert(0, str(TOOLS_DIR))

from build_dynamic_execution_architecture import (  # type: ignore
    OUTPUT_CSV,
    OUTPUT_JSON,
    OUTPUT_MMD,
    RUNS_DIR,
    build_outputs,
)


def _count_complete_runs() -> int:
    count = 0
    for run_dir in RUNS_DIR.iterdir():
        if not run_dir.is_dir():
            continue
        if (run_dir / "manifest.json").exists() and (run_dir / "trace.jsonl").exists():
            count += 1
    return count


def test_dynamic_execution_artifacts_build_and_match_live_run_count() -> None:
    payload = build_outputs()
    assert payload["analyzed_run_dirs"] == _count_complete_runs()
    assert sum(payload["outcome_counts"].values()) == payload["analyzed_run_dirs"]
    assert OUTPUT_JSON.exists()
    assert OUTPUT_CSV.exists()
    assert OUTPUT_MMD.exists()



def test_dynamic_execution_detects_primary_runtime_families() -> None:
    payload = build_outputs()
    families = payload["execution_family_counts"]
    assert "enterprise" in families
    assert "universal" in families
    assert payload["verification_signals"]["explicit_verify_success_steps"] > 0
    assert payload["verification_signals"]["assertion_backed_sleep_steps"] > 0



def test_dynamic_execution_reports_trace_semantic_mismatches() -> None:
    payload = build_outputs()
    mismatch_reasons = {entry["reason"] for entry in payload["trace_semantics_mismatches"]}
    assert mismatch_reasons
    assert "success_with_failed_steps" in mismatch_reasons or "terminal_failure_without_failed_trace_step" in mismatch_reasons
