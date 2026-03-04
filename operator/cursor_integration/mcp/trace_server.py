from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from agent_infra.diagnostic_reader import DiagnosticReader
from agent_infra.healing_orchestrator import HealingOrchestrator

from cursor_integration.mcp.base import CRE_ROOT, ToolSpec, ReadOnlyMCPServer, load_json, repo_relative


class TraceServer(ReadOnlyMCPServer):
    def __init__(self, runs_root: str | Path | None = None) -> None:
        super().__init__(server_name="concentric-trace")
        self._runs_root = Path(runs_root) if runs_root else CRE_ROOT / "runs"
        self.register_tool(
            ToolSpec(
                name="list_recent_runs",
                title="List Recent Runs",
                description="List recent traced runs under operator/cre/runs.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer", "minimum": 1, "maximum": 50}
                    },
                },
                output_schema={"type": "object"},
                handler=self._handle_list_recent_runs,
            )
        )
        self.register_tool(
            ToolSpec(
                name="get_run_manifest",
                title="Get Run Manifest",
                description="Return the manifest.json for a traced run.",
                input_schema={
                    "type": "object",
                    "properties": {"run_id": {"type": "string"}},
                    "required": ["run_id"],
                },
                output_schema={"type": "object"},
                handler=self._handle_get_run_manifest,
            )
        )
        self.register_tool(
            ToolSpec(
                name="get_run_summary",
                title="Get Run Summary",
                description="Return a DiagnosticReader summary for a traced run.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "run_id": {"type": "string"},
                        "detail_level": {"type": "integer", "minimum": 1, "maximum": 3},
                    },
                    "required": ["run_id"],
                },
                output_schema={"type": "object"},
                handler=self._handle_get_run_summary,
            )
        )
        self.register_tool(
            ToolSpec(
                name="summarize_failure_chain",
                title="Summarize Failure Chain",
                description="Use DDG-aware healing analysis to summarize a run's failure chain.",
                input_schema={
                    "type": "object",
                    "properties": {"run_id": {"type": "string"}},
                    "required": ["run_id"],
                },
                output_schema={"type": "object"},
                handler=self._handle_summarize_failure_chain,
            )
        )
        self.register_tool(
            ToolSpec(
                name="list_run_artifacts",
                title="List Run Artifacts",
                description="List files saved under a traced run directory.",
                input_schema={
                    "type": "object",
                    "properties": {"run_id": {"type": "string"}},
                    "required": ["run_id"],
                },
                output_schema={"type": "object"},
                handler=self._handle_list_run_artifacts,
            )
        )

    def list_recent_runs(self, limit: int = 10) -> dict[str, Any]:
        if limit < 1 or limit > 50:
            raise ValueError("limit must be between 1 and 50")
        rows: list[dict[str, Any]] = []
        for run_dir in self._iter_run_dirs()[:limit]:
            manifest_path = run_dir / "manifest.json"
            manifest = load_json(manifest_path)
            rows.append(
                {
                    "run_id": manifest.get("run_id", run_dir.name),
                    "task_id": manifest.get("task_id"),
                    "outcome": manifest.get("outcome"),
                    "total_duration_ms": manifest.get("total_duration_ms"),
                    "timestamp": manifest.get("timestamp"),
                    "path": repo_relative(run_dir),
                    "has_benchmark_result": (run_dir / "benchmark_result.json").exists(),
                    "has_research_brief": (run_dir / "research_brief.json").exists(),
                }
            )
        return {"runs_root": repo_relative(self._runs_root), "runs": rows}

    def get_run_manifest(self, run_id: str) -> dict[str, Any]:
        run_dir = self._resolve_run_dir(run_id)
        manifest = load_json(run_dir / "manifest.json")
        return {
            "run_id": run_id,
            "run_dir": repo_relative(run_dir),
            "manifest": manifest,
        }

    def get_run_summary(self, run_id: str, detail_level: int = 2) -> dict[str, Any]:
        run_dir = self._resolve_run_dir(run_id)
        reader = DiagnosticReader(run_dir)
        if detail_level == 1:
            summary = reader.level1_summary()
        elif detail_level == 2:
            summary = reader.full_diagnostic()
        elif detail_level == 3:
            manifest = load_json(run_dir / "manifest.json")
            failure_step = manifest.get("failure_step")
            detail = reader.level3_step_detail(failure_step) if failure_step is not None else "No failure step recorded."
            summary = reader.full_diagnostic() + "\n\n=== FAILURE STEP DETAIL ===\n" + detail
        else:
            raise ValueError("detail_level must be 1, 2, or 3")
        return {
            "run_id": run_id,
            "run_dir": repo_relative(run_dir),
            "detail_level": detail_level,
            "summary": summary,
        }

    def summarize_failure_chain(self, run_id: str) -> dict[str, Any]:
        run_dir = self._resolve_run_dir(run_id)
        manifest = load_json(run_dir / "manifest.json")
        orchestrator = HealingOrchestrator(self._runs_root)
        classification = orchestrator.analyze_run_with_ddg(run_dir)
        if classification is None:
            return {
                "run_id": run_id,
                "run_dir": repo_relative(run_dir),
                "outcome": "success",
                "summary": "Run succeeded; no failure chain to summarize.",
            }
        return {
            "run_id": run_id,
            "run_dir": repo_relative(run_dir),
            "outcome": manifest.get("outcome"),
            "failure_step": manifest.get("failure_step"),
            "failure_category": manifest.get("failure_category"),
            "error_summary": manifest.get("error_summary"),
            "classification": classification.to_dict(),
        }

    def list_run_artifacts(self, run_id: str) -> dict[str, Any]:
        run_dir = self._resolve_run_dir(run_id)
        files: list[dict[str, Any]] = []
        for path in sorted(p for p in run_dir.rglob("*") if p.is_file()):
            files.append(
                {
                    "path": repo_relative(path),
                    "size_bytes": path.stat().st_size,
                }
            )
        return {
            "run_id": run_id,
            "run_dir": repo_relative(run_dir),
            "artifacts": files,
        }

    def _iter_run_dirs(self) -> list[Path]:
        runs = [
            path for path in self._runs_root.iterdir()
            if path.is_dir() and (path / "manifest.json").exists()
        ]
        return sorted(
            runs,
            key=lambda path: (path / "manifest.json").stat().st_mtime,
            reverse=True,
        )

    def _resolve_run_dir(self, run_id: str) -> Path:
        run_dir = self._runs_root / run_id
        if not run_dir.exists():
            raise FileNotFoundError(f"Run not found: {run_id}")
        if not (run_dir / "manifest.json").exists():
            raise FileNotFoundError(f"manifest.json missing for run: {run_id}")
        return run_dir

    def _handle_list_recent_runs(self, arguments: dict[str, Any]) -> dict[str, Any]:
        return self.list_recent_runs(limit=int(arguments.get("limit", 10)))

    def _handle_get_run_manifest(self, arguments: dict[str, Any]) -> dict[str, Any]:
        return self.get_run_manifest(str(arguments.get("run_id", "")))

    def _handle_get_run_summary(self, arguments: dict[str, Any]) -> dict[str, Any]:
        return self.get_run_summary(
            str(arguments.get("run_id", "")),
            detail_level=int(arguments.get("detail_level", 2)),
        )

    def _handle_summarize_failure_chain(self, arguments: dict[str, Any]) -> dict[str, Any]:
        return self.summarize_failure_chain(str(arguments.get("run_id", "")))

    def _handle_list_run_artifacts(self, arguments: dict[str, Any]) -> dict[str, Any]:
        return self.list_run_artifacts(str(arguments.get("run_id", "")))


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the concentric trace MCP server.")
    parser.add_argument("--runs-root", default=str(CRE_ROOT / "runs"))
    args = parser.parse_args()
    server = TraceServer(runs_root=args.runs_root)
    return server.serve_forever()


if __name__ == "__main__":
    raise SystemExit(main())
