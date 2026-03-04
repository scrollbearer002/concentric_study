from __future__ import annotations

import json
from pathlib import Path

from cursor_integration.mcp.benchmark_server import BenchmarkServer


def _write_run(root: Path, run_id: str, claims_score: float, duration_ms: int) -> None:
    run_dir = root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "manifest.json").write_text(
        json.dumps(
            {
                "run_id": run_id,
                "task_id": "BENCHMARK_TASK",
                "outcome": "success",
                "total_duration_ms": duration_ms,
                "num_steps": 4,
            }
        ),
        encoding="utf-8",
    )
    (run_dir / "benchmark_result.json").write_text(
        json.dumps(
            {
                "task_id": "BENCHMARK_TASK",
                "run_id": run_id,
                "claims_score": claims_score,
                "discovery_precision": 0.8,
                "recovery_rate": 0.5,
                "plan_optimality": 1.0,
                "net_resilient_performance": claims_score,
                "total_duration_ms": duration_ms,
            }
        ),
        encoding="utf-8",
    )


def test_benchmark_server_reads_and_compares_results(tmp_path: Path) -> None:
    _write_run(tmp_path, "run-one", 0.4, 1000)
    _write_run(tmp_path, "run-two", 0.9, 900)
    server = BenchmarkServer(runs_root=tmp_path)

    single = server.evaluate_run("run-one")
    assert single["has_precomputed_result"] is True
    assert single["result"]["claims_score"] == 0.4

    comparison = server.compare_runs(["run-one", "run-two"])
    assert comparison["recommended_run_id"] == "run-two"
    assert comparison["ranked_runs"][0]["claims_score"] == 0.9

    latest = server.latest_benchmark_summary()
    assert latest["total_results"] == 2
    assert latest["best_run_id"] == "run-two"
