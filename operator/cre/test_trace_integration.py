#!/usr/bin/env python3
"""Phase 1 Integration Test: Verify TraceWriter integrates correctly with _Ctx.

This test creates a mock _Ctx with a real TraceWriter, simulates the trace
step creation that _execute_action_with_recovery performs, and verifies
the trace output matches expectations.

Does NOT require Safari, Gemini API, or any GUI — fully offline.
"""

import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

from trace_writer import TraceWriter


def _assert(condition: bool, msg: str) -> None:
    if not condition:
        raise AssertionError(f"FAIL: {msg}")
    print(f"  PASS: {msg}")


def test_ctx_trace_writer_integration() -> None:
    """Simulate the flow that _execute_action_with_recovery uses."""
    print("\n--- Integration Test 1: _Ctx + TraceWriter Flow ---")

    with tempfile.TemporaryDirectory() as tmpdir:
        tw = TraceWriter(
            tmpdir,
            task_id="CONCENTRIC_TRIANGLES_CLEAN",
            task_description="Draw concentric triangles",
            agent_config={"mode": "enterprise", "model": "gemini-2.5-pro"},
        )

        actions = [
            {"action": "clear_canvas", "args": {}, "description": "Clear the canvas", "visual_assert": "Is the canvas empty? YES or NO."},
            {"action": "keystroke", "args": {"key": "p"}, "description": "Select pencil tool"},
            {"action": "set_stroke_color", "args": {"color": "#e03131"}, "description": "Set stroke to red"},
            {"action": "draw_concentric_triangles", "args": {"count": 4}, "description": "Draw 4 nested triangles"},
            {"action": "verify_success", "args": {}, "description": "Verify final result"},
        ]

        for i, action_item in enumerate(actions, 1):
            action_type = action_item["action"]
            description = action_item.get("description", action_type)

            step = tw.begin_step(i)
            step.thought = description
            step.action = {"type": action_type, "parameters": action_item["args"]}
            step.pre_state = {"focused_app": "Safari", "canvas_center": {"x": 720, "y": 450}}

            if i == 3:
                step.action_result = {"success": False, "error": "Color picker not found"}
                step.evaluation = {"expected": "color set", "actual": "Color picker not found", "match": False}
                tw.end_step(step)
                tw.record_failure(i, "grounding_error", "Color picker not found")
            else:
                step.action_result = {"success": True, "output": "ok"}
                step.evaluation = {"expected": "action effect", "actual": "verified", "match": True}
                tw.end_step(step)

        manifest = tw.finalize(outcome="failure")

        with open(tw.trace_path) as f:
            lines = f.readlines()

        _assert(len(lines) == 5, f"5 trace lines written (got {len(lines)})")

        step3 = json.loads(lines[2])
        _assert(step3["action"]["type"] == "set_stroke_color", "step 3 is set_stroke_color")
        _assert(step3["action_result"]["success"] is False, "step 3 marked as failed")
        _assert("Color picker" in step3["action_result"]["error"], "step 3 error message captured")

        _assert(manifest["outcome"] == "failure", "manifest outcome is failure")
        _assert(manifest["failure_step"] == 3, "failure at step 3")
        _assert(manifest["failure_category"] == "grounding_error", "failure category is grounding_error")
        _assert(manifest["num_steps"] == 5, "all 5 steps recorded despite failure at step 3")

        steps_summary = manifest["steps_summary"]
        _assert("clear_canvas (success)" in steps_summary[0], "step 1 summary correct")
        _assert("set_stroke_color (failed)" in steps_summary[2], "step 3 summary shows failed")


def test_successful_run_trace() -> None:
    """Simulate a fully successful run and verify the trace."""
    print("\n--- Integration Test 2: Successful Run Trace ---")

    with tempfile.TemporaryDirectory() as tmpdir:
        tw = TraceWriter(
            tmpdir,
            task_id="CONCENTRIC_TRIANGLES_CLEAN",
            task_description="Draw concentric triangles",
        )

        for i in range(1, 13):
            step = tw.begin_step(i)
            step.action = {"type": f"action_{i}", "parameters": {}}
            step.action_result = {"success": True, "output": "ok"}
            step.evaluation = {"match": True}
            tw.end_step(step)

        manifest = tw.finalize(outcome="success")

        _assert(manifest["outcome"] == "success", "outcome is success")
        _assert(manifest["failure_step"] is None, "no failure step")
        _assert(manifest["num_steps"] == 12, "12 steps recorded")

        with open(tw.trace_path) as f:
            lines = f.readlines()
        _assert(len(lines) == 12, "12 lines in trace.jsonl")

        all_steps = [json.loads(line) for line in lines]
        _assert(all(s["action_result"]["success"] for s in all_steps), "all steps succeeded")
        _assert(all(s["duration_ms"] >= 0 for s in all_steps), "all durations non-negative")
        _assert(all(s["timestamp_start"] is not None for s in all_steps), "all timestamps present")


def test_trace_readable_by_code_agent() -> None:
    """Verify that a trace file can be read and summarized (Phase 2 prerequisite)."""
    print("\n--- Integration Test 3: Trace Readability for Code Agent ---")

    with tempfile.TemporaryDirectory() as tmpdir:
        tw = TraceWriter(tmpdir, task_id="readability_test")

        step = tw.begin_step(1)
        step.thought = "Clear the canvas before drawing"
        step.action = {"type": "clear_canvas", "parameters": {}}
        step.action_result = {"success": True}
        step.evaluation = {"expected": "empty canvas", "actual": "empty canvas", "match": True}
        tw.end_step(step)

        step2 = tw.begin_step(2)
        step2.thought = "Set stroke color to red"
        step2.action = {"type": "set_stroke_color", "parameters": {"color": "#e03131"}}
        step2.action_result = {"success": False, "error": "Element not found"}
        step2.evaluation = {"expected": "red stroke", "actual": "Element not found", "match": False}
        tw.end_step(step2)
        tw.record_failure(2, "grounding_error", "Element not found")

        manifest = tw.finalize(outcome="failure")

        # Simulate what the code agent (Phase 2 DiagnosticReader) would do:
        with open(tw.manifest_path) as f:
            loaded_manifest = json.load(f)

        _assert(loaded_manifest["outcome"] == "failure", "manifest says failure")
        _assert(loaded_manifest["failure_step"] == 2, "manifest says step 2 failed")

        with open(tw.trace_path) as f:
            trace_lines = f.readlines()

        failure_step_data = json.loads(trace_lines[1])
        _assert(failure_step_data["step"] == 2, "can locate failure step in trace")
        _assert(failure_step_data["thought"] == "Set stroke color to red", "thought field is readable")
        _assert(failure_step_data["action"]["type"] == "set_stroke_color", "action type is readable")
        _assert("Element not found" in failure_step_data["action_result"]["error"], "error is readable")

        total_tokens = sum(len(json.dumps(json.loads(line))) for line in trace_lines)
        _assert(total_tokens < 10000, f"trace is under 10k chars for LLM consumption (got {total_tokens})")


def main() -> int:
    print("=" * 60)
    print("PHASE 1 INTEGRATION TESTS: TraceWriter + Agent Pipeline")
    print("=" * 60)

    tests = [
        test_ctx_trace_writer_integration,
        test_successful_run_trace,
        test_trace_readable_by_code_agent,
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
