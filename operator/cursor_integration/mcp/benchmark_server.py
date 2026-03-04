from __future__ import annotations

import argparse
from pathlib import Path
from statistics import mean
from typing import Any

from cursor_integration.mcp.base import CRE_ROOT, ToolSpec, ReadOnlyMCPServer, load_json, repo_relative


class BenchmarkServer(ReadOnlyMCPServer):
    def __init__(self, runs_root: str | Path | None = None) -> None:
        super().__init__(server_name="concentric-benchmark")
        self._runs_root = Path(runs_root) if runs_root else CRE_ROOT / "runs"
        self.register_tool(
            ToolSpec(
                name="evaluate_run",
                title="Evaluate Run",
                description="Return the precomputed benchmark result for a run when available, with a read-only fallback summary otherwise.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "run_id": {"type": "string"},
                        "benchmark_id": {"type": "string"},
                    },
                    "required": ["run_id"],
                },
                output_schema={"type": "object"},
                handler=self._handle_evaluate_run,
            )
        )
        self.register_tool(
            ToolSpec(
                name="compare_runs",
                title="Compare Runs",
                description="Compare multiple runs on benchmark and manifest metrics.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "run_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "minItems": 2,
                            "maxItems": 20,
                        }
                    },
                    "required": ["run_ids"],
                },
                output_schema={"type": "object"},
                handler=self._handle_compare_runs,
            )
        )
        self.register_tool(
            ToolSpec(
                name="latest_benchmark_summary",
                title="Latest Benchmark Summary",
                description="Summarize benchmark_result.json files found under operator/cre/runs.",
                input_schema={"type": "object", "properties": {}},
                output_schema={"type": "object"},
                handler=self._handle_latest_benchmark_summary,
            )
        )

    def evaluate_run(self, run_id: str, benchmark_id: str | None = None) -> dict[str, Any]:
        run_dir = self._resolve_run_dir(run_id)
        manifest = load_json(run_dir / "manifest.json")
        benchmark_path = run_dir / "benchmark_result.json"
        if benchmark_path.exists():
            result = load_json(benchmark_path)
            return {
                "run_id": run_id,
                "run_dir": repo_relative(run_dir),
                "benchmark_id": benchmark_id,
                "has_precomputed_result": True,
                "result": result,
            }
        return {
            "run_id": run_id,
            "run_dir": repo_relative(run_dir),
            "benchmark_id": benchmark_id,
            "has_precomputed_result": False,
            "result": {
                "task_id": manifest.get("task_id"),
                "outcome": manifest.get("outcome"),
                "total_duration_ms": manifest.get("total_duration_ms"),
                "num_steps": manifest.get("num_steps"),
                "message": "No precomputed benchmark_result.json found for this run.",
            },
        }

    def compare_runs(self, run_ids: list[str]) -> dict[str, Any]:
        if len(run_ids) < 2:
            raise ValueError("compare_runs requires at least two run_ids")
        rows = [self._comparison_row(run_id) for run_id in run_ids]
        ranked = sorted(
            rows,
            key=lambda row: (
                row.get("claims_score", -1.0),
                row.get("outcome") == "success",
                -row.get("total_duration_ms", 0),
            ),
            reverse=True,
        )
        return {
            "compared_run_ids": run_ids,
            "ranked_runs": ranked,
            "recommended_run_id": ranked[0]["run_id"] if ranked else None,
        }

    def latest_benchmark_summary(self) -> dict[str, Any]:
        paths = sorted(
            self._runs_root.glob("*/benchmark_result.json"),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        if not paths:
            return {
                "total_results": 0,
                "message": "No benchmark_result.json files found.",
            }
        rows = [load_json(path) for path in paths]
        claims_scores = [float(row.get("claims_score", 0.0)) for row in rows]
        recovery_rates = [float(row.get("recovery_rate", 0.0)) for row in rows]
        return {
            "total_results": len(rows),
            "latest_run_id": rows[0].get("run_id"),
            "latest_path": repo_relative(paths[0]),
            "mean_claims_score": mean(claims_scores),
            "mean_recovery_rate": mean(recovery_rates),
            "best_run_id": max(rows, key=lambda row: row.get("claims_score", 0.0)).get("run_id"),
        }

    def _comparison_row(self, run_id: str) -> dict[str, Any]:
        run_dir = self._resolve_run_dir(run_id)
        manifest = load_json(run_dir / "manifest.json")
        benchmark_path = run_dir / "benchmark_result.json"
        if benchmark_path.exists():
            result = load_json(benchmark_path)
            return {
                "run_id": run_id,
                "task_id": result.get("task_id", manifest.get("task_id")),
                "outcome": manifest.get("outcome"),
                "claims_score": float(result.get("claims_score", 0.0)),
                "discovery_precision": float(result.get("discovery_precision", 0.0)),
                "recovery_rate": float(result.get("recovery_rate", 0.0)),
                "plan_optimality": float(result.get("plan_optimality", 0.0)),
                "net_resilient_performance": float(result.get("net_resilient_performance", 0.0)),
                "total_duration_ms": int(result.get("total_duration_ms", manifest.get("total_duration_ms", 0))),
                "has_precomputed_result": True,
            }
        return {
            "run_id": run_id,
            "task_id": manifest.get("task_id"),
            "outcome": manifest.get("outcome"),
            "claims_score": 0.0,
            "discovery_precision": 0.0,
            "recovery_rate": 0.0,
            "plan_optimality": 0.0,
            "net_resilient_performance": 0.0,
            "total_duration_ms": int(manifest.get("total_duration_ms", 0)),
            "has_precomputed_result": False,
        }

    def _resolve_run_dir(self, run_id: str) -> Path:
        run_dir = self._runs_root / run_id
        if not run_dir.exists():
            raise FileNotFoundError(f"Run not found: {run_id}")
        if not (run_dir / "manifest.json").exists():
            raise FileNotFoundError(f"manifest.json missing for run: {run_id}")
        return run_dir

    def _handle_evaluate_run(self, arguments: dict[str, Any]) -> dict[str, Any]:
        benchmark_id = arguments.get("benchmark_id")
        return self.evaluate_run(
            str(arguments.get("run_id", "")),
            benchmark_id=str(benchmark_id) if benchmark_id is not None else None,
        )

    def _handle_compare_runs(self, arguments: dict[str, Any]) -> dict[str, Any]:
        return self.compare_runs([str(run_id) for run_id in arguments.get("run_ids", [])])

    def _handle_latest_benchmark_summary(self, arguments: dict[str, Any]) -> dict[str, Any]:
        del arguments
        return self.latest_benchmark_summary()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the concentric benchmark MCP server.")
    parser.add_argument("--runs-root", default=str(CRE_ROOT / "runs"))
    args = parser.parse_args()
    server = BenchmarkServer(runs_root=args.runs_root)
    return server.serve_forever()


if __name__ == "__main__":
    raise SystemExit(main())
