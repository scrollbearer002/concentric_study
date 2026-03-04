#!/usr/bin/env python3
"""Tests for the Dual-Agent Outer Loop (Phase A).

Tests cover all 5 scenarios from the build plan:
1. Happy path — success on first try
2. Transient failure + retry → success on second try
3. Escalation — logic failure triggers ESCALATION.md
4. Max retries exhausted — persistent transient failure
5. Reflection accumulation — journal records lessons correctly

Also tests individual components:
6. ReflectionJournal persistence and retrieval
7. OuterLoopResult serialization
8. Escalation document structure
9. Real trace analysis through the outer loop (if available)

All tests use mock subprocess — no real GUI execution needed.
"""

import json
import os
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

from trace_writer import TraceWriter
from agent_infra.outer_loop import OuterLoop, OuterLoopResult, ReflectionJournal
from agent_infra.healing_orchestrator import FailureClassification


def _assert(condition: bool, msg: str) -> None:
    if not condition:
        raise AssertionError(f"FAIL: {msg}")
    print(f"  PASS: {msg}")


def _create_trace(
    output_dir: str,
    task_id: str = "TEST_TASK",
    outcome: str = "success",
    fail_at: int | None = None,
    failure_category: str = "action_failed",
    error_summary: str = "test error",
    num_steps: int = 5,
) -> Path:
    """Create a test trace and return its run_dir.

    TraceWriter creates output_dir/runs/<run_id>/, so `output_dir` should
    be the *parent* of the runs/ directory.
    """
    tw = TraceWriter(output_dir, task_id=task_id)
    for i in range(1, num_steps + 1):
        step = tw.begin_step(i)
        step.thought = f"Step {i} thought"
        step.action = {"type": f"action_{i}", "parameters": {}}
        step.pre_state = {"focused_app": "Safari"}
        if fail_at and i == fail_at:
            step.action_result = {"success": False, "error": error_summary}
            step.evaluation = {"expected": "action effect", "actual": error_summary, "match": False}
            tw.end_step(step)
            tw.record_failure(i, failure_category, error_summary)
        else:
            step.action_result = {"success": True, "output": "ok"}
            step.evaluation = {"expected": "action effect", "actual": "verified", "match": True}
            tw.end_step(step)
    tw.finalize(outcome=outcome)
    return tw.run_dir


class _MockSubprocess:
    """Helper to mock subprocess.run() with pre-built trace directories.

    TraceWriter creates <output_dir>/runs/<run_id>/, so we pass the *parent*
    of runs_dir to _create_trace so traces land in runs_dir/<run_id>/.
    """

    def __init__(self, runs_parent_dir: str):
        self._runs_parent_dir = runs_parent_dir
        self._call_count = 0
        self._trace_configs: list[dict] = []

    def add_run(self, **kwargs) -> "_MockSubprocess":
        """Queue a trace to be created on the next subprocess.run() call."""
        self._trace_configs.append(kwargs)
        return self

    def mock_run(self, *args, **kwargs) -> MagicMock:
        """Drop-in replacement for subprocess.run that creates a trace."""
        if self._call_count >= len(self._trace_configs):
            raise RuntimeError("MockSubprocess: no more queued runs")
        config = self._trace_configs[self._call_count]
        self._call_count += 1
        _create_trace(self._runs_parent_dir, **config)
        result = MagicMock()
        result.returncode = 0 if config.get("outcome", "success") == "success" else 1
        return result


# ===================================================================
# Test 1: Happy Path — Success on First Try
# ===================================================================

def test_happy_path() -> None:
    """Outer loop succeeds on first try, ingests skill, records reflection."""
    print("\n--- Test 1: Happy Path ---")
    with tempfile.TemporaryDirectory() as tmpdir:
        runs_dir = os.path.join(tmpdir, "runs")

        mock = _MockSubprocess(tmpdir)
        mock.add_run(outcome="success", task_id="TEST_TASK")

        loop = OuterLoop(
            task_id="TEST_TASK",
            test_script="/fake/test.py",
            runs_dir=runs_dir,
            max_cycles=3,
        )

        with patch("agent_infra.outer_loop.subprocess.run", side_effect=mock.mock_run):
            result = loop.run()

        _assert(result.outcome == "success", f"outcome is success (got {result.outcome})")
        _assert(result.cycles == 1, f"completed in 1 cycle (got {result.cycles})")
        _assert(result.run_id is not None, "run_id is set")
        _assert(result.escalation_path is None, "no escalation")

        skill = loop.skill_library.retrieve_exact("TEST_TASK")
        _assert(skill is not None, "skill ingested into library")

        reflections = loop.journal.get_all()
        _assert(len(reflections) == 1, f"1 reflection recorded (got {len(reflections)})")
        _assert(reflections[0]["outcome"] == "success", "reflection shows success")


# ===================================================================
# Test 2: Transient Failure + Retry → Success
# ===================================================================

def test_transient_retry_then_success() -> None:
    """First run fails transiently, second run succeeds."""
    print("\n--- Test 2: Transient Failure + Retry ---")
    with tempfile.TemporaryDirectory() as tmpdir:
        runs_dir = os.path.join(tmpdir, "runs")

        mock = _MockSubprocess(tmpdir)
        mock.add_run(
            outcome="failure", task_id="TEST_TASK",
            fail_at=3, failure_category="action_failed",
            error_summary="Dialog popup appeared blocking canvas",
        )
        mock.add_run(outcome="success", task_id="TEST_TASK")

        loop = OuterLoop(
            task_id="TEST_TASK",
            test_script="/fake/test.py",
            runs_dir=runs_dir,
            max_cycles=3,
        )

        with patch("agent_infra.outer_loop.subprocess.run", side_effect=mock.mock_run):
            result = loop.run()

        _assert(result.outcome == "success", f"outcome is success (got {result.outcome})")
        _assert(result.cycles == 2, f"completed in 2 cycles (got {result.cycles})")

        reflections = loop.journal.get_all()
        _assert(len(reflections) == 2, f"2 reflections recorded (got {len(reflections)})")
        _assert(reflections[0]["outcome"] == "failure", "first reflection is failure")
        _assert(reflections[0]["failure_category"] == "transient", "first failure classified as transient")
        _assert(reflections[1]["outcome"] == "success", "second reflection is success")


# ===================================================================
# Test 3: Escalation — Logic Failure
# ===================================================================

def test_escalation() -> None:
    """Logic failure triggers escalation with ESCALATION.md."""
    print("\n--- Test 3: Escalation ---")
    with tempfile.TemporaryDirectory() as tmpdir:
        runs_dir = os.path.join(tmpdir, "runs")

        mock = _MockSubprocess(tmpdir)
        mock.add_run(
            outcome="failure", task_id="TEST_TASK",
            fail_at=4, failure_category="non_recoverable_error",
            error_summary="Handler returned invalid state for draw_path action",
        )

        loop = OuterLoop(
            task_id="TEST_TASK",
            test_script="/fake/test.py",
            runs_dir=runs_dir,
            max_cycles=3,
        )

        with patch("agent_infra.outer_loop.subprocess.run", side_effect=mock.mock_run):
            result = loop.run()

        _assert(result.outcome == "escalated", f"outcome is escalated (got {result.outcome})")
        _assert(result.cycles == 1, f"escalated after 1 cycle (got {result.cycles})")
        _assert(result.escalation_path is not None, "escalation path is set")

        escalation = Path(result.escalation_path)
        _assert(escalation.exists(), "ESCALATION.md was written")

        content = escalation.read_text()
        _assert("# Escalation: Code Agent Repair Request" in content, "has title")
        _assert("Run Summary" in content, "has run summary section")
        _assert("Level 1: Overview" in content, "has L1 diagnosis")
        _assert("Level 2: Failure Window" in content, "has L2 diagnosis")
        _assert("Suggested Investigation" in content, "has investigation section")
        _assert("Architecture-Critical Files" in content, "has architecture files")

        reflections = loop.journal.get_all()
        _assert(len(reflections) == 1, f"1 reflection (got {len(reflections)})")
        _assert("escalat" in reflections[0]["lesson"].lower(), "lesson mentions escalation")


# ===================================================================
# Test 4: Max Retries Exhausted
# ===================================================================

def test_max_retries_exhausted() -> None:
    """Persistent transient failure exhausts all cycles."""
    print("\n--- Test 4: Max Retries Exhausted ---")
    with tempfile.TemporaryDirectory() as tmpdir:
        runs_dir = os.path.join(tmpdir, "runs")

        mock = _MockSubprocess(tmpdir)
        for i in range(3):
            mock.add_run(
                outcome="failure", task_id="TEST_TASK",
                fail_at=2, failure_category="action_failed",
                error_summary=f"Dialog popup appeared attempt {i+1}",
            )

        loop = OuterLoop(
            task_id="TEST_TASK",
            test_script="/fake/test.py",
            runs_dir=runs_dir,
            max_cycles=3,
        )

        with patch("agent_infra.outer_loop.subprocess.run", side_effect=mock.mock_run):
            result = loop.run()

        _assert(result.outcome == "max_retries_exhausted", f"outcome is max_retries (got {result.outcome})")
        _assert(result.cycles == 3, f"used all 3 cycles (got {result.cycles})")

        reflections = loop.journal.get_all()
        _assert(len(reflections) == 3, f"3 reflections (got {len(reflections)})")
        _assert(all(r["outcome"] == "failure" for r in reflections), "all reflections are failures")


# ===================================================================
# Test 5: Reflection Accumulation
# ===================================================================

def test_reflection_accumulation() -> None:
    """Reflections accumulate across cycles and are retrievable by category."""
    print("\n--- Test 5: Reflection Accumulation ---")
    with tempfile.TemporaryDirectory() as tmpdir:
        runs_dir = os.path.join(tmpdir, "runs")

        mock = _MockSubprocess(tmpdir)
        mock.add_run(
            outcome="failure", task_id="TEST_TASK",
            fail_at=3, failure_category="action_failed",
            error_summary="Dialog popup appeared blocking canvas",
        )
        mock.add_run(outcome="success", task_id="TEST_TASK")

        loop = OuterLoop(
            task_id="TEST_TASK",
            test_script="/fake/test.py",
            runs_dir=runs_dir,
            max_cycles=3,
        )

        with patch("agent_infra.outer_loop.subprocess.run", side_effect=mock.mock_run):
            result = loop.run()

        _assert(result.outcome == "success", "final outcome is success")

        transient_lessons = loop.journal.get_lessons_for_category("transient")
        _assert(len(transient_lessons) == 1, f"1 transient lesson (got {len(transient_lessons)})")
        _assert("popup" in transient_lessons[0].lower() or "retry" in transient_lessons[0].lower(),
                "transient lesson references the failure")

        recent = loop.journal.get_recent(10)
        _assert(len(recent) == 2, f"2 total reflections (got {len(recent)})")


# ===================================================================
# Test 6: ReflectionJournal Persistence
# ===================================================================

def test_journal_persistence() -> None:
    """Journal persists to JSONL and reloads correctly."""
    print("\n--- Test 6: Journal Persistence ---")
    with tempfile.TemporaryDirectory() as tmpdir:
        journal_path = os.path.join(tmpdir, "journal.jsonl")

        journal1 = ReflectionJournal(journal_path)
        classification = FailureClassification(
            category="transient", confidence=0.85, action="retry",
            details="popup", step_index=3, error_summary="popup",
        )
        journal1.record("run-abc", "failure", 1, classification, "Popup blocked step 3")
        journal1.record("run-def", "success", 2, None, "Succeeded on retry")

        _assert(len(journal1.entries) == 2, "2 entries in memory")

        journal2 = ReflectionJournal(journal_path)
        _assert(len(journal2.entries) == 2, "2 entries after reload")
        _assert(journal2.entries[0]["run_id"] == "run-abc", "first entry preserved")
        _assert(journal2.entries[1]["run_id"] == "run-def", "second entry preserved")

        lessons = journal2.get_lessons_for_category("transient")
        _assert(len(lessons) == 1, f"1 transient lesson (got {len(lessons)})")
        _assert("Popup" in lessons[0], "lesson content preserved")


# ===================================================================
# Test 7: OuterLoopResult Serialization
# ===================================================================

def test_result_serialization() -> None:
    """OuterLoopResult serializes to dict cleanly."""
    print("\n--- Test 7: OuterLoopResult Serialization ---")
    result = OuterLoopResult(
        outcome="escalated",
        cycles=2,
        run_id="abc123",
        escalation_path="/tmp/runs/abc123/ESCALATION.md",
        total_duration_ms=45000,
        reflections=[{"lesson": "test"}],
    )
    d = result.to_dict()
    _assert(d["outcome"] == "escalated", "outcome serialized")
    _assert(d["cycles"] == 2, "cycles serialized")
    _assert(d["run_id"] == "abc123", "run_id serialized")
    _assert(d["escalation_path"] is not None, "escalation_path serialized")
    _assert(len(d["reflections"]) == 1, "reflections serialized")


# ===================================================================
# Test 8: Abort on Environment Failure
# ===================================================================

def test_abort_on_environment_failure() -> None:
    """Environment failure (launch_failure) aborts immediately."""
    print("\n--- Test 8: Abort on Environment Failure ---")
    with tempfile.TemporaryDirectory() as tmpdir:
        runs_dir = os.path.join(tmpdir, "runs")

        mock = _MockSubprocess(tmpdir)
        mock.add_run(
            outcome="failure", task_id="TEST_TASK",
            fail_at=1, failure_category="launch_failure",
            error_summary="Safari failed to open",
        )

        loop = OuterLoop(
            task_id="TEST_TASK",
            test_script="/fake/test.py",
            runs_dir=runs_dir,
            max_cycles=3,
        )

        with patch("agent_infra.outer_loop.subprocess.run", side_effect=mock.mock_run):
            result = loop.run()

        _assert(result.outcome == "aborted", f"outcome is aborted (got {result.outcome})")
        _assert(result.cycles == 1, f"aborted after 1 cycle (got {result.cycles})")

        reflections = loop.journal.get_all()
        _assert(len(reflections) == 1, "1 reflection recorded")
        _assert("abort" in reflections[0]["lesson"].lower(), "lesson mentions abort")


# ===================================================================
# Test 9: Escalation Document Structure (Deep Validation)
# ===================================================================

def test_escalation_document_detail() -> None:
    """ESCALATION.md contains all required sections with real data."""
    print("\n--- Test 9: Escalation Document Detail ---")
    with tempfile.TemporaryDirectory() as tmpdir:
        runs_dir = os.path.join(tmpdir, "runs")

        mock = _MockSubprocess(tmpdir)
        mock.add_run(
            outcome="failure", task_id="TEST_TASK",
            fail_at=3, failure_category="action_failed",
            error_summary="Visual assertion failed: expected drawing not found",
            num_steps=5,
        )
        mock.add_run(
            outcome="failure", task_id="TEST_TASK",
            fail_at=3, failure_category="action_failed",
            error_summary="Visual assertion failed: expected drawing not found",
            num_steps=5,
        )
        mock.add_run(
            outcome="failure", task_id="TEST_TASK",
            fail_at=3, failure_category="action_failed",
            error_summary="Visual assertion failed: expected drawing not found",
            num_steps=5,
        )

        loop = OuterLoop(
            task_id="TEST_TASK",
            test_script="/fake/test.py",
            runs_dir=runs_dir,
            max_cycles=3,
        )

        with patch("agent_infra.outer_loop.subprocess.run", side_effect=mock.mock_run):
            result = loop.run()

        if result.escalation_path:
            content = Path(result.escalation_path).read_text()
            _assert("Level 3: Failed Step Detail" in content, "L3 detail present")
            _assert("action_3" in content, "failed action type in detail")
            _assert("TEST_TASK" in content, "task ID in document")
            _assert("Attempt History" in content, "attempt history section present")
        else:
            _assert(
                result.outcome == "max_retries_exhausted",
                f"expected escalation or max_retries (got {result.outcome})",
            )
            print("  INFO: repeated errors exhausted retries without explicit escalation")


# ===================================================================
# Test 10: Real Trace Through Outer Loop (if available)
# ===================================================================

def test_real_trace_through_loop() -> None:
    """Analyze an actual run directory through the outer loop components."""
    print("\n--- Test 10: Real Trace Components ---")
    real_runs_dir = Path(__file__).parent / "runs"
    if not real_runs_dir.exists():
        print("  SKIP: No real runs directory found")
        return

    real_runs = [d for d in real_runs_dir.iterdir() if d.is_dir() and (d / "manifest.json").exists()]
    if not real_runs:
        print("  SKIP: No real run traces found")
        return

    cre_dir = Path(__file__).parent
    loop = OuterLoop(
        task_id="CONCENTRIC_TRIANGLES_CLEAN",
        test_script="/unused",
        runs_dir=str(real_runs_dir),
        library_dir=str(cre_dir),
    )

    latest = max(real_runs, key=lambda p: p.stat().st_mtime)
    manifest = loop._read_manifest(latest)
    _assert(manifest is not None, f"real manifest readable ({latest.name})")
    _assert("run_id" in manifest, "manifest has run_id")
    _assert("outcome" in manifest, "manifest has outcome")

    skill = loop.skill_library.retrieve_exact("CONCENTRIC_TRIANGLES_CLEAN")
    _assert(skill is not None, "skill library has CONCENTRIC_TRIANGLES_CLEAN")
    _assert(skill.maturity.tier == "master", f"skill is at master tier (got {skill.maturity.tier})")

    print(f"  INFO: Latest run {latest.name}: {manifest['outcome']} in {manifest.get('total_duration_ms', 0)}ms")


# ===================================================================
# Main
# ===================================================================

def main() -> int:
    print("=" * 60)
    print("PHASE A TESTS: Dual-Agent Outer Loop")
    print("=" * 60)

    tests = [
        test_happy_path,
        test_transient_retry_then_success,
        test_escalation,
        test_max_retries_exhausted,
        test_reflection_accumulation,
        test_journal_persistence,
        test_result_serialization,
        test_abort_on_environment_failure,
        test_escalation_document_detail,
        test_real_trace_through_loop,
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
            import traceback
            traceback.print_exc()
            failed += 1

    print(f"\n{'=' * 60}")
    print(f"RESULTS: {passed} passed, {failed} failed, {passed + failed} total")
    print(f"{'=' * 60}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
