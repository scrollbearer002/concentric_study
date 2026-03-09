#!/usr/bin/env python3
"""Phase 1 Tests: Structured Execution Traces — TraceWriter

Tests the TraceWriter in isolation before integrating into the agent pipeline.
Following the testing pyramid from arXiv:2509.19185 (Empirical Study of Testing
Practices in Open Source AI Agent Frameworks): test deterministic components
with unit tests first.

Test 1: Serialization round-trip — write a trace, read it back, verify fields
Test 2: Manifest generation — verify summary correctness
Test 3: Failure recording — verify failure metadata propagates to manifest
Test 4: Multi-step trace — verify ordering and completeness
Test 5: Directory structure — verify runs/, screenshots/, trace.jsonl, manifest.json
"""

import json
import os
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from trace_writer import TraceWriter, TraceStep


def _assert(condition: bool, msg: str) -> None:
    if not condition:
        raise AssertionError(f"FAIL: {msg}")
    print(f"  PASS: {msg}")


def test_serialization_roundtrip() -> None:
    """Write one step, read it back, verify every field."""
    print("\n--- Test 1: Serialization Round-Trip ---")
    with tempfile.TemporaryDirectory() as tmpdir:
        tw = TraceWriter(tmpdir, task_id="test_task", task_description="Test task")

        step = tw.begin_step(1)
        step.pre_state = {"screenshot": "pre.png", "focused_app": "Safari"}
        step.thought = "I need to clear the canvas"
        step.action = {"type": "clear_canvas", "parameters": {}}
        step.action_result = {"success": True, "output": "canvas cleared"}
        step.post_state = {"screenshot": "post.png", "state_changed": True}
        step.evaluation = {"expected": "empty canvas", "actual": "empty canvas", "match": True}
        tw.end_step(step)

        trace_path = tw.trace_path
        _assert(trace_path.exists(), "trace.jsonl file exists")

        with open(trace_path) as f:
            lines = f.readlines()
        _assert(len(lines) == 1, f"exactly 1 line in trace (got {len(lines)})")

        loaded = json.loads(lines[0])
        _assert(loaded["step"] == 1, "step index is 1")
        _assert(loaded["pre_state"]["focused_app"] == "Safari", "pre_state.focused_app round-trips")
        _assert(loaded["thought"] == "I need to clear the canvas", "thought round-trips")
        _assert(loaded["action"]["type"] == "clear_canvas", "action.type round-trips")
        _assert(loaded["action_result"]["success"] is True, "action_result.success round-trips")
        _assert(loaded["post_state"]["state_changed"] is True, "post_state.state_changed round-trips")
        _assert(loaded["evaluation"]["match"] is True, "evaluation.match round-trips")
        _assert(loaded["timestamp_start"] is not None, "timestamp_start is set")
        _assert(loaded["timestamp_end"] is not None, "timestamp_end is set")
        _assert(loaded["duration_ms"] >= 0, "duration_ms is non-negative")


def test_manifest_generation() -> None:
    """Verify manifest summary correctness after a successful run."""
    print("\n--- Test 2: Manifest Generation ---")
    with tempfile.TemporaryDirectory() as tmpdir:
        tw = TraceWriter(
            tmpdir,
            task_id="CONCENTRIC_TRIANGLES_CLEAN",
            task_description="Draw concentric triangles",
            agent_config={"model": "gemini-2.5-pro", "mode": "enterprise"},
        )

        for i in range(1, 4):
            step = tw.begin_step(i)
            step.action = {"type": f"action_{i}", "parameters": {}}
            step.action_result = {"success": True}
            tw.end_step(step)

        manifest = tw.finalize(outcome="success")

        _assert(manifest["run_id"] == tw.run_id, "run_id matches")
        _assert(manifest["task_id"] == "CONCENTRIC_TRIANGLES_CLEAN", "task_id correct")
        _assert(manifest["num_steps"] == 3, f"num_steps is 3 (got {manifest['num_steps']})")
        _assert(manifest["outcome"] == "success", "outcome is success")
        _assert(manifest["failure_step"] is None, "no failure_step on success")
        _assert(manifest["failure_category"] is None, "no failure_category on success")
        _assert(manifest["error_summary"] is None, "no error_summary on success")
        _assert(manifest["outcome_semantics"]["task_result"] == "accepted", "task_result is accepted")
        _assert(manifest["outcome_semantics"]["final_verification"]["status"] == "not_run", "final verification not_run by default")
        _assert(len(manifest["steps_summary"]) == 3, "steps_summary has 3 entries")
        _assert(manifest["total_duration_ms"] >= 0, "total_duration_ms is non-negative")
        _assert("macos" in manifest["environment"]["os"], "environment.os is macos")

        manifest_path = tw.manifest_path
        _assert(manifest_path.exists(), "manifest.json file exists")
        with open(manifest_path) as f:
            loaded = json.load(f)
        _assert(loaded["run_id"] == tw.run_id, "manifest.json round-trips correctly")


def test_failure_recording() -> None:
    """Verify failure metadata propagates to manifest."""
    print("\n--- Test 3: Failure Recording ---")
    with tempfile.TemporaryDirectory() as tmpdir:
        tw = TraceWriter(tmpdir, task_id="test_fail")

        step1 = tw.begin_step(1)
        step1.action = {"type": "clear_canvas", "parameters": {}}
        step1.action_result = {"success": True}
        tw.end_step(step1)

        step2 = tw.begin_step(2)
        step2.action = {"type": "set_stroke_color", "parameters": {"color": "red"}}
        step2.action_result = {"success": False, "error": "Color picker not found"}
        tw.end_step(step2)

        tw.record_failure(2, "grounding_error", "Color picker not found")
        manifest = tw.finalize(outcome="failure")

        _assert(manifest["outcome"] == "failure", "outcome is failure")
        _assert(manifest["failure_step"] == 2, "failure_step is 2")
        _assert(manifest["failure_category"] == "grounding_error", "failure_category correct")
        _assert(manifest["error_summary"] == "Color picker not found", "error_summary correct")
        _assert(manifest["outcome_semantics"]["task_result"] == "rejected", "task_result is rejected on failure")


def test_multistep_ordering() -> None:
    """Verify step ordering and completeness across many steps."""
    print("\n--- Test 4: Multi-Step Ordering ---")
    with tempfile.TemporaryDirectory() as tmpdir:
        tw = TraceWriter(tmpdir, task_id="test_order")
        num_steps = 12

        for i in range(1, num_steps + 1):
            step = tw.begin_step(i)
            step.action = {"type": f"action_{i}", "parameters": {}}
            step.action_result = {"success": True}
            tw.end_step(step)

        with open(tw.trace_path) as f:
            lines = f.readlines()

        _assert(len(lines) == num_steps, f"trace has {num_steps} lines (got {len(lines)})")

        for idx, line in enumerate(lines):
            loaded = json.loads(line)
            expected_step = idx + 1
            _assert(loaded["step"] == expected_step, f"line {idx} has step {expected_step}")


def test_directory_structure() -> None:
    """Verify the full directory structure is created correctly."""
    print("\n--- Test 5: Directory Structure ---")
    with tempfile.TemporaryDirectory() as tmpdir:
        tw = TraceWriter(tmpdir, task_id="test_dirs")

        runs_dir = Path(tmpdir) / "runs"
        _assert(runs_dir.exists(), "runs/ directory exists")

        run_dir = tw.run_dir
        _assert(run_dir.exists(), f"run directory {run_dir.name} exists")
        _assert(run_dir.parent == runs_dir, "run dir is inside runs/")

        screenshots_dir = tw.screenshots_dir
        _assert(screenshots_dir.exists(), "screenshots/ directory exists")
        _assert(screenshots_dir.parent == run_dir, "screenshots/ is inside run dir")

        _assert(tw.trace_path.parent == run_dir, "trace.jsonl is inside run dir")
        _assert(tw.manifest_path.parent == run_dir, "manifest.json is inside run dir")

        _assert(tw.trace_path.name == "trace.jsonl", "trace file is named trace.jsonl")
        _assert(tw.manifest_path.name == "manifest.json", "manifest file is named manifest.json")


def test_duplicate_failure_recording() -> None:
    """Verify only the first failure is recorded (no overwrite)."""
    print("\n--- Test 6: Duplicate Failure Recording ---")
    with tempfile.TemporaryDirectory() as tmpdir:
        tw = TraceWriter(tmpdir, task_id="test_dup_fail")
        tw.record_failure(3, "grounding_error", "first error")
        tw.record_failure(5, "execution_error", "second error")
        manifest = tw.finalize(outcome="failure")

        _assert(manifest["failure_step"] == 3, "first failure preserved (step 3)")
        _assert(manifest["failure_category"] == "grounding_error", "first failure category preserved")
        _assert(manifest["error_summary"] == "first error", "first error summary preserved")


def test_final_verification_failure_infers_canonical_failure_metadata() -> None:
    print("\n--- Test 7: Final Verification Failure Semantics ---")
    with tempfile.TemporaryDirectory() as tmpdir:
        tw = TraceWriter(tmpdir, task_id="test_verify_fail")

        draw_step = tw.begin_step(1)
        draw_step.action = {"type": "draw_path", "parameters": {}}
        draw_step.action_result = {"success": True}
        tw.end_step(draw_step)

        verify_step = tw.begin_step(997)
        verify_step.action = {"type": "final_verification_gate", "parameters": {}}
        verify_step.action_result = {"success": False}
        verify_step.post_state = {
            "score": 0.4,
            "verdict": "FAILED: subject not recognizable",
            "deficiencies": ["subject not recognizable"],
        }
        tw.end_step(verify_step)

        manifest = tw.finalize(outcome="failure")

        _assert(manifest["failure_step"] == 997, "final verification step inferred as canonical failure")
        _assert(manifest["failure_category"] == "verification_failed", "failure category inferred from final verification")
        _assert("subject not recognizable" in manifest["error_summary"], "verification verdict used as error summary")
        _assert(manifest["outcome_semantics"]["final_verification"]["status"] == "failed", "final verification status is failed")


def test_success_with_meta_failure_is_explicit_in_outcome_semantics() -> None:
    print("\n--- Test 8: Accepted Run With Meta Failure ---")
    with tempfile.TemporaryDirectory() as tmpdir:
        tw = TraceWriter(tmpdir, task_id="test_meta_fail")

        draw_step = tw.begin_step(1)
        draw_step.action = {"type": "draw_path", "parameters": {}}
        draw_step.action_result = {"success": True}
        tw.end_step(draw_step)

        audit_step = tw.begin_step(998)
        audit_step.action = {"type": "metacognitive_audit", "parameters": {}}
        audit_step.action_result = {"success": False}
        tw.end_step(audit_step)

        manifest = tw.finalize(outcome="success")

        semantics = manifest["outcome_semantics"]
        _assert(semantics["task_result"] == "accepted", "task_result remains accepted")
        _assert(semantics["step_outcomes"]["failed"] == 1, "one failed step counted")
        _assert(semantics["step_outcomes"]["productive_failed"] == 0, "no productive failures counted")
        _assert(semantics["step_outcomes"]["meta_failed"] == 1, "one meta failure counted")
        _assert(semantics["consistency"]["accepted_with_failed_steps"] is True, "accepted_with_failed_steps flag set")


def main() -> int:
    print("=" * 60)
    print("PHASE 1 TESTS: TraceWriter")
    print("=" * 60)

    tests = [
        test_serialization_roundtrip,
        test_manifest_generation,
        test_failure_recording,
        test_multistep_ordering,
        test_directory_structure,
        test_duplicate_failure_recording,
        test_final_verification_failure_infers_canonical_failure_metadata,
        test_success_with_meta_failure_is_explicit_in_outcome_semantics,
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
