#!/usr/bin/env python3
"""Phase 3 Tests: HealingOrchestrator — self-healing loop.

Tests:
1. Successful run — no classification returned
2. Transient failure — classified as retry
3. Grounding failure — classified as adjust_parameters
4. Environment failure — classified as abort
5. Logic failure (repeated) — escalate after 2+ repeats
6. Should_retry logic — max attempts, abort, repeated errors
7. Diagnostic for code agent — combined output format
8. Attempt history tracking
9. Real trace from Phase 1 — analyze the actual successful run
"""

import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from trace_writer import TraceWriter
from healing_orchestrator import HealingOrchestrator, FailureClassification


def _assert(condition: bool, msg: str) -> None:
    if not condition:
        raise AssertionError(f"FAIL: {msg}")
    print(f"  PASS: {msg}")


def _create_trace(
    tmpdir: str,
    task_id: str = "TEST",
    outcome: str = "success",
    fail_at: int | None = None,
    failure_category: str = "action_failed",
    error_summary: str = "test error",
    num_steps: int = 5,
) -> Path:
    """Create a test trace and return its run_dir."""
    tw = TraceWriter(tmpdir, task_id=task_id)
    for i in range(1, num_steps + 1):
        step = tw.begin_step(i)
        step.action = {"type": f"action_{i}", "parameters": {}}
        if fail_at and i == fail_at:
            step.action_result = {"success": False, "error": error_summary}
            step.evaluation = {"match": False}
            tw.end_step(step)
            tw.record_failure(i, failure_category, error_summary)
        else:
            step.action_result = {"success": True, "output": "ok"}
            step.evaluation = {"match": True}
            tw.end_step(step)
    tw.finalize(outcome=outcome)
    return tw.run_dir


def test_successful_run() -> None:
    """Successful run returns None classification."""
    print("\n--- Test 1: Successful Run ---")
    with tempfile.TemporaryDirectory() as tmpdir:
        run_dir = _create_trace(tmpdir, outcome="success")
        orch = HealingOrchestrator(tmpdir)
        result = orch.analyze_run(run_dir)
        _assert(result is None, "no classification for success")
        _assert(len(orch.get_history()) == 1, "history has 1 entry")
        _assert(orch.get_history()[0]["outcome"] == "success", "history records success")


def test_transient_failure() -> None:
    """Popup/dialog failures classified as transient -> retry."""
    print("\n--- Test 2: Transient Failure ---")
    with tempfile.TemporaryDirectory() as tmpdir:
        run_dir = _create_trace(
            tmpdir, outcome="failure", fail_at=3,
            failure_category="action_failed",
            error_summary="Dialog popup appeared blocking canvas",
        )
        orch = HealingOrchestrator(tmpdir)
        result = orch.analyze_run(run_dir)
        _assert(result is not None, "classification returned")
        _assert(result.category == "transient", f"category is transient (got {result.category})")
        _assert(result.action == "retry", f"action is retry (got {result.action})")
        _assert(result.confidence >= 0.80, f"confidence >= 80% (got {result.confidence:.0%})")


def test_grounding_failure() -> None:
    """Element not found failures classified as grounding -> adjust."""
    print("\n--- Test 3: Grounding Failure ---")
    with tempfile.TemporaryDirectory() as tmpdir:
        run_dir = _create_trace(
            tmpdir, outcome="failure", fail_at=5,
            failure_category="grounding_error",
            error_summary="Visual assertion failed: target element not found in screenshot",
        )
        orch = HealingOrchestrator(tmpdir)
        result = orch.analyze_run(run_dir)
        _assert(result is not None, "classification returned")
        _assert(result.category == "grounding", f"category is grounding (got {result.category})")
        _assert(result.action == "adjust_parameters", f"action is adjust (got {result.action})")
        _assert(result.step_index == 5, f"step index is 5 (got {result.step_index})")


def test_environment_failure() -> None:
    """Launch failure classified as environment -> abort."""
    print("\n--- Test 4: Environment Failure ---")
    with tempfile.TemporaryDirectory() as tmpdir:
        run_dir = _create_trace(
            tmpdir, outcome="failure", fail_at=1,
            failure_category="launch_failure",
            error_summary="Safari failed to open",
        )
        orch = HealingOrchestrator(tmpdir)
        result = orch.analyze_run(run_dir)
        _assert(result is not None, "classification returned")
        _assert(result.category == "environment", f"category is environment (got {result.category})")
        _assert(result.action == "abort", f"action is abort (got {result.action})")


def test_repeated_failure_escalation() -> None:
    """Same error 3+ times escalates to code agent."""
    print("\n--- Test 5: Repeated Failure Escalation ---")
    with tempfile.TemporaryDirectory() as tmpdir:
        orch = HealingOrchestrator(tmpdir, max_attempts=5)

        for i in range(3):
            run_dir = _create_trace(
                tmpdir, outcome="failure", fail_at=2,
                failure_category="action_failed",
                error_summary="Mysterious recurring error XYZ",
            )
            result = orch.analyze_run(run_dir)

        _assert(result.category == "logic", f"3rd repeat classified as logic (got {result.category})")
        _assert(result.action == "escalate_to_code_agent", f"action is escalate (got {result.action})")
        _assert("repeated" in result.details.lower(), "details mention repetition")


def test_should_retry_logic() -> None:
    """Should_retry respects max attempts, abort, and repeated errors."""
    print("\n--- Test 6: Should_retry Logic ---")

    with tempfile.TemporaryDirectory() as tmpdir:
        orch = HealingOrchestrator(tmpdir, max_attempts=2)
        _assert(orch.should_retry() is True, "can retry before any failures")

        run_dir = _create_trace(
            tmpdir, outcome="failure", fail_at=1,
            error_summary="Dialog popup appeared",
        )
        orch.analyze_run(run_dir)
        _assert(orch.should_retry() is True, "can retry after 1 failure (max 2)")

        run_dir2 = _create_trace(
            tmpdir, outcome="failure", fail_at=1,
            error_summary="Another dialog popup",
        )
        orch.analyze_run(run_dir2)
        _assert(orch.should_retry() is False, "cannot retry after 2 failures (max 2)")

    with tempfile.TemporaryDirectory() as tmpdir:
        orch = HealingOrchestrator(tmpdir, max_attempts=5)
        run_dir = _create_trace(
            tmpdir, outcome="failure", fail_at=1,
            failure_category="launch_failure",
            error_summary="Safari crash",
        )
        orch.analyze_run(run_dir)
        _assert(orch.should_retry() is False, "cannot retry after abort classification")

    with tempfile.TemporaryDirectory() as tmpdir:
        orch = HealingOrchestrator(tmpdir, max_attempts=10)
        for i in range(3):
            run_dir = _create_trace(
                tmpdir, outcome="failure", fail_at=1,
                error_summary="Same exact error message",
            )
            orch.analyze_run(run_dir)
        _assert(orch.should_retry() is False, "cannot retry after 3 identical errors")


def test_diagnostic_for_code_agent() -> None:
    """Diagnostic output contains all required sections."""
    print("\n--- Test 7: Diagnostic for Code Agent ---")
    with tempfile.TemporaryDirectory() as tmpdir:
        run_dir = _create_trace(
            tmpdir, outcome="failure", fail_at=3,
            failure_category="grounding_error",
            error_summary="Element not found on screen",
        )
        orch = HealingOrchestrator(tmpdir)
        diagnostic = orch.get_diagnostic_for_code_agent(run_dir)

        _assert("RUN SUMMARY" in diagnostic, "contains Level 1 summary")
        _assert("FAILURE CLASSIFICATION" in diagnostic, "contains classification")
        _assert("grounding" in diagnostic, "classification category present")
        _assert("ATTEMPT HISTORY" in diagnostic, "contains attempt history")
        _assert("retry attempt(s) remaining" in diagnostic, "shows remaining retries")
        _assert("RECOMMENDATION" in diagnostic, "contains recommendation")


def test_attempt_history_tracking() -> None:
    """History correctly tracks mixed success/failure runs."""
    print("\n--- Test 8: Attempt History ---")
    with tempfile.TemporaryDirectory() as tmpdir:
        orch = HealingOrchestrator(tmpdir, max_attempts=5)

        run1 = _create_trace(tmpdir, outcome="failure", fail_at=2, error_summary="popup dialog")
        orch.analyze_run(run1)

        run2 = _create_trace(tmpdir, outcome="failure", fail_at=4, error_summary="element not found")
        orch.analyze_run(run2)

        run3 = _create_trace(tmpdir, outcome="success")
        orch.analyze_run(run3)

        history = orch.get_history()
        _assert(len(history) == 3, f"3 entries in history (got {len(history)})")
        _assert(history[0]["outcome"] == "failure", "first run is failure")
        _assert(history[1]["outcome"] == "failure", "second run is failure")
        _assert(history[2]["outcome"] == "success", "third run is success")
        _assert(orch.get_attempt_count() == 2, "2 failed attempts counted")


def test_real_trace_analysis() -> None:
    """Analyze the actual successful trace from the live test run."""
    print("\n--- Test 9: Real Trace Analysis ---")
    real_run_dir = Path(__file__).parent / "runs" / "64f991f80d39"
    if not real_run_dir.exists():
        print("  SKIP: Real trace not found (run CONCENTRIC_TRIANGLES_CLEAN first)")
        return

    orch = HealingOrchestrator(real_run_dir.parent)
    result = orch.analyze_run(real_run_dir)
    _assert(result is None, "real successful run returns no classification")

    diagnostic = orch.get_diagnostic_for_code_agent(real_run_dir)
    _assert("SUCCESS" in diagnostic, "diagnostic shows SUCCESS")
    _assert("CONCENTRIC_TRIANGLES_CLEAN" in diagnostic, "task ID present")


def main() -> int:
    print("=" * 60)
    print("PHASE 3 TESTS: HealingOrchestrator")
    print("=" * 60)

    tests = [
        test_successful_run,
        test_transient_failure,
        test_grounding_failure,
        test_environment_failure,
        test_repeated_failure_escalation,
        test_should_retry_logic,
        test_diagnostic_for_code_agent,
        test_attempt_history_tracking,
        test_real_trace_analysis,
    ]

    passed = 0
    failed = 0
    for test_fn in tests:
        try:
            test_fn()
            passed += 1
        except AssertionError as e:
            print(f"  {e}")
            failed += 1
        except Exception as e:
            print(f"  ERROR: {test_fn.__name__} raised {type(e).__name__}: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed, {passed + failed} total")
    print("=" * 60)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
