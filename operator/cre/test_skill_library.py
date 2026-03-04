"""Tests for the Skill Library (Phase 5).

Validates:
1. Ingestion from real and synthetic traces
2. Maturity gating (candidate -> proven -> master)
3. Poisoning prevention (failed traces rejected)
4. Exact-match and semantic retrieval
5. Persistence (save/load cycle)
6. Provenance integrity (hash verification)
7. Failure demotion (master -> proven on failure)
8. Best-plan update (faster run replaces slower)
9. Real trace ingestion from actual runs
"""

import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from skill_library import SkillLibrary, SkillRecord, SkillMaturity, _cosine_similarity, _compute_tfidf, _tokenize


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _create_synthetic_run(tmp_dir: Path, run_id: str, task_id: str, outcome: str = "success",
                          duration_ms: int = 120000, num_steps: int = 12) -> Path:
    """Create a synthetic run directory with manifest + trace."""
    run_dir = tmp_dir / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "run_id": run_id,
        "task_id": task_id,
        "task_description": f"Execute task {task_id}",
        "agent_config": {"mode": "enterprise", "model": "gemini-2.5-pro"},
        "environment": {"os": "macos", "platform": "Darwin 25.3.0 (arm64)"},
        "start_time": "2026-02-22T00:00:00.000Z",
        "end_time": "2026-02-22T00:02:00.000Z",
        "total_duration_ms": duration_ms,
        "num_steps": num_steps,
        "outcome": outcome,
        "failure_step": None if outcome == "success" else 5,
        "failure_category": None if outcome == "success" else "action_failed",
        "error_summary": None if outcome == "success" else "Test failure",
        "steps_summary": [f"{i}: action_{i} (success)" for i in range(1, num_steps + 1)],
    }

    trace_lines = []
    for i in range(1, num_steps + 1):
        step = {
            "step": i,
            "timestamp_start": f"2026-02-22T00:00:{i:02d}.000Z",
            "timestamp_end": f"2026-02-22T00:00:{i + 10:02d}.000Z",
            "duration_ms": 10000,
            "pre_state": {"focused_app": "Safari"},
            "thought": f"Perform action {i}",
            "action": {"type": f"action_{i}", "parameters": {"step": i}},
            "action_result": {"success": True, "output": "ok"},
            "post_state": {},
            "evaluation": {"expected": "effect", "actual": "verified", "match": True},
        }
        trace_lines.append(json.dumps(step))

    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    (run_dir / "trace.jsonl").write_text("\n".join(trace_lines) + "\n")

    return run_dir


# ---------------------------------------------------------------------------
# Test 1: Basic ingestion and storage
# ---------------------------------------------------------------------------

def test_ingest_successful_trace():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        run_dir = _create_synthetic_run(tmp_path, "aaa111", "TASK_A")

        lib = SkillLibrary(tmp_path / "library")
        record = lib.ingest_from_trace(run_dir)

        assert record is not None
        assert record.task_id == "TASK_A"
        assert record.maturity.tier == "candidate"
        assert record.maturity.success_count == 1
        assert len(record.action_plan) == 12
        assert record.provenance["run_id"] == "aaa111"
        assert lib.get_skill_count() == 1


# ---------------------------------------------------------------------------
# Test 2: Poisoning prevention — failed traces rejected
# ---------------------------------------------------------------------------

def test_reject_failed_trace():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        run_dir = _create_synthetic_run(tmp_path, "bad111", "TASK_BAD", outcome="failure")

        lib = SkillLibrary(tmp_path / "library")
        record = lib.ingest_from_trace(run_dir)

        assert record is None
        assert lib.get_skill_count() == 0


# ---------------------------------------------------------------------------
# Test 3: Maturity gating — candidate -> proven -> master
# ---------------------------------------------------------------------------

def test_maturity_progression():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        lib = SkillLibrary(tmp_path / "library")

        for i in range(5):
            run_dir = _create_synthetic_run(tmp_path, f"run_{i:03d}", "TASK_PROG")
            record = lib.ingest_from_trace(run_dir)

        assert record is not None
        assert record.maturity.success_count == 5
        assert record.maturity.tier == "master"
        assert len(record.maturity.evidence_run_ids) == 5

        # Verify tier transitions happened correctly
        m = SkillMaturity()
        assert m.tier == "candidate"
        m.record_success("r2")  # count=2
        assert m.tier == "candidate"
        m.record_success("r3")  # count=3 -> proven threshold
        assert m.tier == "proven"
        m.record_success("r4")  # count=4
        assert m.tier == "proven"
        m.record_success("r5")  # count=5 -> master threshold
        assert m.tier == "master"


# ---------------------------------------------------------------------------
# Test 4: Proven retrieval gate — candidate skills not returned
# ---------------------------------------------------------------------------

def test_proven_retrieval_gate():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        lib = SkillLibrary(tmp_path / "library")

        run_dir = _create_synthetic_run(tmp_path, "single_001", "TASK_SINGLE")
        lib.ingest_from_trace(run_dir)

        assert lib.retrieve_exact("TASK_SINGLE") is not None
        assert lib.retrieve_proven("TASK_SINGLE") is None  # candidate, not proven

        for i in range(2, 4):
            run_dir = _create_synthetic_run(tmp_path, f"single_{i:03d}", "TASK_SINGLE")
            lib.ingest_from_trace(run_dir)

        assert lib.retrieve_proven("TASK_SINGLE") is not None  # now proven


# ---------------------------------------------------------------------------
# Test 5: Persistence — save/load cycle
# ---------------------------------------------------------------------------

def test_persistence():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        lib_dir = tmp_path / "library"

        lib1 = SkillLibrary(lib_dir)
        for i in range(3):
            run_dir = _create_synthetic_run(tmp_path, f"persist_{i}", "TASK_PERSIST")
            lib1.ingest_from_trace(run_dir)

        assert lib1.get_skill_count() == 1
        skill1 = lib1.retrieve_exact("TASK_PERSIST")
        assert skill1.maturity.tier == "proven"

        # Load from disk in new instance
        lib2 = SkillLibrary(lib_dir)
        assert lib2.get_skill_count() == 1
        skill2 = lib2.retrieve_exact("TASK_PERSIST")
        assert skill2.maturity.tier == "proven"
        assert skill2.maturity.success_count == 3
        assert skill2.task_description == skill1.task_description


# ---------------------------------------------------------------------------
# Test 6: Provenance integrity
# ---------------------------------------------------------------------------

def test_provenance_hashes():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        run_dir = _create_synthetic_run(tmp_path, "prov_001", "TASK_PROV")

        lib = SkillLibrary(tmp_path / "library")
        record = lib.ingest_from_trace(run_dir)

        assert record.provenance["manifest_hash"]
        assert record.provenance["trace_hash"]
        assert len(record.provenance["manifest_hash"]) == 16
        assert len(record.provenance["trace_hash"]) == 16
        assert record.provenance["run_id"] == "prov_001"
        assert record.provenance["agent_config"]["mode"] == "enterprise"


# ---------------------------------------------------------------------------
# Test 7: Failure demotion — master demoted to proven
# ---------------------------------------------------------------------------

def test_failure_demotion():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        lib = SkillLibrary(tmp_path / "library")

        for i in range(5):
            run_dir = _create_synthetic_run(tmp_path, f"dem_{i:03d}", "TASK_DEMOTE")
            lib.ingest_from_trace(run_dir)

        skill = lib.retrieve_exact("TASK_DEMOTE")
        assert skill.maturity.tier == "master"

        new_tier = lib.record_failure("TASK_DEMOTE", "dem_fail")
        assert new_tier == "proven"

        skill = lib.retrieve_exact("TASK_DEMOTE")
        assert skill.maturity.tier == "proven"
        assert skill.maturity.failure_count == 1


# ---------------------------------------------------------------------------
# Test 8: Best-plan update (faster run replaces slower)
# ---------------------------------------------------------------------------

def test_best_plan_update():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        lib = SkillLibrary(tmp_path / "library")

        slow_dir = _create_synthetic_run(tmp_path, "slow_001", "TASK_SPEED", duration_ms=200000)
        lib.ingest_from_trace(slow_dir)

        skill = lib.retrieve_exact("TASK_SPEED")
        assert skill.performance["total_duration_ms"] == 200000

        fast_dir = _create_synthetic_run(tmp_path, "fast_001", "TASK_SPEED", duration_ms=100000)
        lib.ingest_from_trace(fast_dir)

        skill = lib.retrieve_exact("TASK_SPEED")
        assert skill.performance["total_duration_ms"] == 100000


# ---------------------------------------------------------------------------
# Test 9: Semantic similarity retrieval
# ---------------------------------------------------------------------------

def test_semantic_retrieval():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        lib = SkillLibrary(tmp_path / "library")

        tasks = [
            ("DRAW_TRIANGLES", "Draw four nested concentric triangles on the canvas"),
            ("DRAW_CIRCLES", "Draw three concentric circles on the canvas"),
            ("CLEAR_CANVAS", "Clear the Excalidraw canvas completely"),
        ]

        for i, (task_id, desc) in enumerate(tasks):
            run_dir = tmp_path / "runs" / f"sem_{i}"
            run_dir.mkdir(parents=True, exist_ok=True)

            manifest = {
                "run_id": f"sem_{i}",
                "task_id": task_id,
                "task_description": desc,
                "agent_config": {},
                "start_time": "2026-01-01T00:00:00.000Z",
                "end_time": "2026-01-01T00:01:00.000Z",
                "total_duration_ms": 60000,
                "num_steps": 5,
                "outcome": "success",
                "failure_step": None,
                "failure_category": None,
                "error_summary": None,
                "steps_summary": [],
            }
            trace = [{"step": 1, "action": {"type": "test"}, "thought": "test", "duration_ms": 100}]

            (run_dir / "manifest.json").write_text(json.dumps(manifest))
            (run_dir / "trace.jsonl").write_text(json.dumps(trace[0]) + "\n")
            lib.ingest_from_trace(run_dir)

        results = lib.retrieve_by_similarity("Draw nested triangles on canvas")
        assert len(results) > 0
        assert results[0][0].task_id == "DRAW_TRIANGLES"
        assert results[0][1] > results[-1][1]


# ---------------------------------------------------------------------------
# Test 10: TF-IDF and cosine similarity correctness
# ---------------------------------------------------------------------------

def test_tfidf_cosine():
    tokens = _tokenize("Hello, World! This is a test-123.")
    assert "hello" in tokens
    assert "world" in tokens
    assert "123" in tokens

    corpus = ["the cat sat on the mat", "the dog sat on the log", "the bird flew over the tree"]
    tfidf = _compute_tfidf(corpus)
    assert len(tfidf) == 3

    sim_01 = _cosine_similarity(tfidf[0], tfidf[1])
    sim_02 = _cosine_similarity(tfidf[0], tfidf[2])
    assert sim_01 > sim_02  # cat/dog more similar than cat/bird

    sim_self = _cosine_similarity(tfidf[0], tfidf[0])
    assert abs(sim_self - 1.0) < 0.001  # self-similarity = 1.0


# ---------------------------------------------------------------------------
# Test 11: Real trace ingestion (if runs exist)
# ---------------------------------------------------------------------------

def test_real_trace_ingestion():
    """Test ingestion of actual traces from live runs."""
    runs_dir = Path(__file__).resolve().parent / "runs"
    if not runs_dir.exists():
        pytest.skip("No real runs directory found")

    run_dirs = sorted(runs_dir.iterdir())
    success_dirs = []
    for rd in run_dirs:
        manifest_path = rd / "manifest.json"
        if manifest_path.exists():
            with open(manifest_path) as f:
                m = json.load(f)
            if m.get("outcome") == "success":
                success_dirs.append(rd)

    if not success_dirs:
        pytest.skip("No successful runs found")

    with tempfile.TemporaryDirectory() as tmp:
        lib = SkillLibrary(Path(tmp) / "library")

        for rd in success_dirs:
            record = lib.ingest_from_trace(rd)
            assert record is not None

        summary = lib.get_summary()
        assert "SKILL LIBRARY" in summary
        assert lib.get_skill_count() >= 1

        first_skill = lib.get_all_skills()[0]
        assert first_skill.provenance["manifest_hash"]
        assert first_skill.provenance["trace_hash"]
        assert first_skill.action_plan
        assert first_skill.maturity.success_count >= 1


# ---------------------------------------------------------------------------
# Test 12: Library summary output
# ---------------------------------------------------------------------------

def test_library_summary():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        lib = SkillLibrary(tmp_path / "library")

        assert "empty" in lib.get_summary()

        run_dir = _create_synthetic_run(tmp_path, "sum_001", "TASK_SUMMARY")
        lib.ingest_from_trace(run_dir)

        summary = lib.get_summary()
        assert "SKILL LIBRARY (1 skills)" in summary
        assert "CANDIDATE" in summary
        assert "TASK_SUMMARY" in summary
