#!/usr/bin/env python3
"""Phase 2 Tests: DiagnosticReader — progressive disclosure trace consumer.

Tests:
1. Level 1 summary — manifest-only compact output
2. Level 2 failure window — correct step window extraction
3. Level 3 step detail — full step retrieval
4. Full diagnostic — combined output with recommendation
5. Token budget — Level 1 under 500 tokens, Level 2 under 5000 tokens
6. Success case — no failure steps, compact overview
7. Analysis helpers — failure step data, success rate
"""

import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from trace_writer import TraceWriter
from diagnostic_reader import DiagnosticReader


def _assert(condition: bool, msg: str) -> None:
    if not condition:
        raise AssertionError(f"FAIL: {msg}")
    print(f"  PASS: {msg}")


def _create_test_trace(tmpdir: str, num_steps: int = 10, fail_at: int | None = 7) -> TraceWriter:
    """Create a realistic test trace with an optional failure point."""
    tw = TraceWriter(
        tmpdir,
        task_id="CONCENTRIC_TRIANGLES_CLEAN",
        task_description="Clear canvas and draw 4 nested concentric triangles",
        agent_config={"mode": "enterprise", "model": "gemini-2.5-pro"},
    )

    action_types = [
        "clear_canvas", "keystroke", "set_stroke_color",
        "draw_concentric_triangles", "keystroke", "refresh_canvas_center",
        "set_stroke_color", "draw_path", "click", "verify_success",
    ]

    for i in range(1, num_steps + 1):
        step = tw.begin_step(i)
        atype = action_types[(i - 1) % len(action_types)]
        step.thought = f"Executing step {i}: {atype}"
        step.action = {"type": atype, "parameters": {"step": i}}
        step.pre_state = {"focused_app": "Safari", "canvas_center": {"x": 720, "y": 450}}

        if fail_at and i == fail_at:
            step.action_result = {"success": False, "error": "Visual assertion failed: element not found"}
            step.post_state = {"screenshot": f"screenshots/step_{i}_post.png", "state_changed": False}
            step.evaluation = {"expected": "stroke color changed", "actual": "element not found", "match": False}
            tw.end_step(step)
            tw.record_failure(i, "grounding_error", "Visual assertion failed: element not found")
        else:
            step.action_result = {"success": True, "output": "ok"}
            step.post_state = {"screenshot": f"screenshots/step_{i}_post.png", "state_changed": True}
            step.evaluation = {"expected": "action effect", "actual": "verified", "match": True}
            tw.end_step(step)

    outcome = "failure" if fail_at else "success"
    tw.finalize(outcome=outcome)
    return tw


def test_level1_summary() -> None:
    """Level 1 summary is compact and contains essential info."""
    print("\n--- Test 1: Level 1 Summary ---")
    with tempfile.TemporaryDirectory() as tmpdir:
        tw = _create_test_trace(tmpdir, num_steps=10, fail_at=7)
        reader = DiagnosticReader(tw.run_dir)
        summary = reader.level1_summary()

        _assert("RUN SUMMARY" in summary, "contains RUN SUMMARY header")
        _assert("CONCENTRIC_TRIANGLES_CLEAN" in summary, "contains task_id")
        _assert("FAILURE" in summary, "contains FAILURE marker")
        _assert("step 7" in summary, "identifies step 7 as failure")
        _assert("grounding_error" in summary, "contains failure category")
        _assert("Steps overview" in summary, "contains steps overview")

        token_est = reader.estimate_token_count(summary)
        _assert(token_est < 500, f"Level 1 under 500 tokens (est: {token_est})")


def test_level2_failure_window() -> None:
    """Level 2 extracts the correct window around the failure."""
    print("\n--- Test 2: Level 2 Failure Window ---")
    with tempfile.TemporaryDirectory() as tmpdir:
        tw = _create_test_trace(tmpdir, num_steps=10, fail_at=7)
        reader = DiagnosticReader(tw.run_dir)
        window = reader.level2_failure_window(window=2)

        _assert("FAILURE WINDOW" in window, "contains FAILURE WINDOW header")
        _assert(">>> FAILED >>>" in window, "failure step is marked")
        _assert("Step 5" in window, "includes step 5 (failure-2)")
        _assert("Step 6" in window, "includes step 6 (failure-1)")
        _assert("Step 7" in window, "includes step 7 (failure)")
        _assert("Step 8" in window, "includes step 8 (failure+1)")
        _assert("Step 9" in window, "includes step 9 (failure+2)")
        _assert("Step 4" not in window or "Step 4" in window.split("FAILURE WINDOW")[0], "step 4 not in window body")

        token_est = reader.estimate_token_count(window)
        _assert(token_est < 5000, f"Level 2 under 5000 tokens (est: {token_est})")


def test_level3_step_detail() -> None:
    """Level 3 returns full JSON for a specific step."""
    print("\n--- Test 3: Level 3 Step Detail ---")
    with tempfile.TemporaryDirectory() as tmpdir:
        tw = _create_test_trace(tmpdir, num_steps=10, fail_at=7)
        reader = DiagnosticReader(tw.run_dir)
        detail = reader.level3_step_detail(7)

        parsed = json.loads(detail)
        _assert(parsed["step"] == 7, "step 7 returned")
        _assert(parsed["action"]["type"] == "set_stroke_color", "correct action type")
        _assert(parsed["action_result"]["success"] is False, "failure captured")
        _assert("element not found" in parsed["action_result"]["error"], "error message present")

        missing = reader.level3_step_detail(99)
        _assert("not found" in missing, "missing step handled gracefully")


def test_full_diagnostic() -> None:
    """Full diagnostic combines Level 1 + Level 2 + recommendation."""
    print("\n--- Test 4: Full Diagnostic ---")
    with tempfile.TemporaryDirectory() as tmpdir:
        tw = _create_test_trace(tmpdir, num_steps=10, fail_at=7)
        reader = DiagnosticReader(tw.run_dir)
        full = reader.full_diagnostic()

        _assert("RUN SUMMARY" in full, "contains Level 1")
        _assert("FAILURE WINDOW" in full, "contains Level 2")
        _assert("RECOMMENDATION" in full, "contains recommendation")
        _assert("grounding" in full.lower(), "recommendation is relevant to grounding")


def test_success_case() -> None:
    """Successful run produces compact output without failure window."""
    print("\n--- Test 5: Success Case ---")
    with tempfile.TemporaryDirectory() as tmpdir:
        tw = _create_test_trace(tmpdir, num_steps=5, fail_at=None)
        reader = DiagnosticReader(tw.run_dir)
        summary = reader.level1_summary()

        _assert("SUCCESS" in summary, "outcome shows SUCCESS")
        _assert("FAILURE" not in summary, "no failure info in success case")

        full = reader.full_diagnostic()
        _assert("FAILURE WINDOW" not in full, "no failure window in success case")
        _assert("RECOMMENDATION" not in full, "no recommendation in success case")


def test_analysis_helpers() -> None:
    """Test get_failure_step_data, get_all_failed_steps, get_success_rate."""
    print("\n--- Test 6: Analysis Helpers ---")
    with tempfile.TemporaryDirectory() as tmpdir:
        tw = _create_test_trace(tmpdir, num_steps=10, fail_at=7)
        reader = DiagnosticReader(tw.run_dir)

        failure_data = reader.get_failure_step_data()
        _assert(failure_data is not None, "failure step data found")
        _assert(failure_data["step"] == 7, "failure step is 7")

        failed_steps = reader.get_all_failed_steps()
        _assert(len(failed_steps) == 1, f"exactly 1 failed step (got {len(failed_steps)})")
        _assert(failed_steps[0]["step"] == 7, "failed step is step 7")

        rate = reader.get_success_rate()
        _assert(abs(rate - 0.9) < 0.01, f"success rate is 90% (got {rate:.1%})")

    with tempfile.TemporaryDirectory() as tmpdir:
        tw = _create_test_trace(tmpdir, num_steps=5, fail_at=None)
        reader = DiagnosticReader(tw.run_dir)

        _assert(reader.get_failure_step_data() is None, "no failure in success case")
        _assert(len(reader.get_all_failed_steps()) == 0, "no failed steps in success case")
        _assert(reader.get_success_rate() == 1.0, "100% success rate")


def test_token_budgets() -> None:
    """Verify token budgets for Level 1 and Level 2 at scale."""
    print("\n--- Test 7: Token Budgets at Scale ---")
    with tempfile.TemporaryDirectory() as tmpdir:
        tw = _create_test_trace(tmpdir, num_steps=50, fail_at=35)
        reader = DiagnosticReader(tw.run_dir)

        l1 = reader.level1_summary()
        l1_tokens = reader.estimate_token_count(l1)
        _assert(l1_tokens < 2000, f"Level 1 under 2000 tokens even with 50 steps (est: {l1_tokens})")

        l2 = reader.level2_failure_window(window=2)
        l2_tokens = reader.estimate_token_count(l2)
        _assert(l2_tokens < 5000, f"Level 2 under 5000 tokens (est: {l2_tokens})")

        full = reader.full_diagnostic()
        full_tokens = reader.estimate_token_count(full)
        _assert(full_tokens < 10000, f"Full diagnostic under 10000 tokens (est: {full_tokens})")


def main() -> int:
    print("=" * 60)
    print("PHASE 2 TESTS: DiagnosticReader")
    print("=" * 60)

    tests = [
        test_level1_summary,
        test_level2_failure_window,
        test_level3_step_detail,
        test_full_diagnostic,
        test_success_case,
        test_analysis_helpers,
        test_token_budgets,
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
