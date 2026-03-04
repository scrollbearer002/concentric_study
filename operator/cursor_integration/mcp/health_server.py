from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path
from typing import Any, Callable

from agent_infra.host_tool_health import HostToolHealth

from cursor_integration.mcp.base import CRE_ROOT, OPERATOR_ROOT, ToolSpec, ReadOnlyMCPServer, load_json, repo_relative


def _load_cursor_environment_module() -> Any:
    module_path = CRE_ROOT / "tools" / "cursor_environment_snapshot.py"
    module_name = "cursor_environment_snapshot"
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load cursor_environment_snapshot from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class HealthServer(ReadOnlyMCPServer):
    def __init__(
        self,
        *,
        checker: HostToolHealth | None = None,
        snapshot_provider: Callable[[], dict[str, Any]] | None = None,
        latest_snapshot_path: str | Path | None = None,
    ) -> None:
        super().__init__(server_name="concentric-health")
        self._checker = checker or HostToolHealth(operator_dir=OPERATOR_ROOT, cre_dir=CRE_ROOT)
        self._snapshot_provider = snapshot_provider
        self._latest_snapshot_path = (
            Path(latest_snapshot_path)
            if latest_snapshot_path else CRE_ROOT / "artifacts" / "cursor_environment" / "latest.json"
        )
        self.register_tool(
            ToolSpec(
                name="health_summary",
                title="Health Summary",
                description="Summarize HostToolHealth readiness and selected providers.",
                input_schema={
                    "type": "object",
                    "properties": {"has_url": {"type": "boolean"}},
                },
                output_schema={"type": "object"},
                handler=self._handle_health_summary,
            )
        )
        self.register_tool(
            ToolSpec(
                name="check_tool_class",
                title="Check Tool Class",
                description="Return the current availability and selected provider for one tool class.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "class_id": {"type": "string"},
                        "has_url": {"type": "boolean"},
                    },
                    "required": ["class_id"],
                },
                output_schema={"type": "object"},
                handler=self._handle_check_tool_class,
            )
        )
        self.register_tool(
            ToolSpec(
                name="compare_environment_baselines",
                title="Compare Environment Baselines",
                description="Diff two Cursor environment snapshot JSON files.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "left_path": {"type": "string"},
                        "right_path": {"type": "string"},
                    },
                    "required": ["left_path", "right_path"],
                },
                output_schema={"type": "object"},
                handler=self._handle_compare_environment_baselines,
            )
        )
        self.register_tool(
            ToolSpec(
                name="cursor_environment_snapshot",
                title="Cursor Environment Snapshot",
                description="Return a live read-only Cursor environment snapshot and compare it to the latest saved baseline if present.",
                input_schema={"type": "object", "properties": {}},
                output_schema={"type": "object"},
                handler=self._handle_cursor_environment_snapshot,
            )
        )

    def health_summary(self, has_url: bool = False) -> dict[str, Any]:
        payload = self._checker.evaluate(has_url=has_url)
        return {
            "summary": self._checker.summary(payload),
            "selected": payload.get("selected", {}),
            "missing_required_classes": payload.get("missing_required_classes", []),
            "required_classes": payload.get("required_classes", []),
        }

    def check_tool_class(self, class_id: str, has_url: bool = False) -> dict[str, Any]:
        payload = self._checker.evaluate(has_url=has_url)
        classes = payload.get("classes", {})
        if class_id not in classes:
            raise ValueError(f"Unknown tool class: {class_id}")
        return {
            "class_id": class_id,
            "class_row": classes[class_id],
            "selected": payload.get("selected", {}).get(class_id),
            "all_required_ready": payload.get("all_required_ready"),
        }

    def compare_environment_baselines(self, left_path: str, right_path: str) -> dict[str, Any]:
        left = load_json(Path(left_path))
        right = load_json(Path(right_path))
        snapshot_module = _load_cursor_environment_module()
        diff = snapshot_module.diff_snapshots(left, right)
        return {
            "left_path": repo_relative(Path(left_path)),
            "right_path": repo_relative(Path(right_path)),
            "diff": diff,
        }

    def cursor_environment_snapshot(self) -> dict[str, Any]:
        snapshot_module = _load_cursor_environment_module()
        current = self._snapshot_provider() if self._snapshot_provider else snapshot_module.collect_snapshot()
        latest = load_json(self._latest_snapshot_path) if self._latest_snapshot_path.exists() else None
        diff = snapshot_module.diff_snapshots(latest, current) if latest else {"has_changes": False, "added": {}, "removed": {}, "changed": {}}
        return {
            "snapshot": current,
            "baseline_path": repo_relative(self._latest_snapshot_path),
            "baseline_exists": self._latest_snapshot_path.exists(),
            "diff_vs_latest": diff,
        }

    def _handle_health_summary(self, arguments: dict[str, Any]) -> dict[str, Any]:
        return self.health_summary(has_url=bool(arguments.get("has_url", False)))

    def _handle_check_tool_class(self, arguments: dict[str, Any]) -> dict[str, Any]:
        return self.check_tool_class(
            str(arguments.get("class_id", "")),
            has_url=bool(arguments.get("has_url", False)),
        )

    def _handle_compare_environment_baselines(self, arguments: dict[str, Any]) -> dict[str, Any]:
        return self.compare_environment_baselines(
            str(arguments.get("left_path", "")),
            str(arguments.get("right_path", "")),
        )

    def _handle_cursor_environment_snapshot(self, arguments: dict[str, Any]) -> dict[str, Any]:
        del arguments
        return self.cursor_environment_snapshot()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the concentric health MCP server.")
    parser.add_argument(
        "--latest-snapshot-path",
        default=str(CRE_ROOT / "artifacts" / "cursor_environment" / "latest.json"),
    )
    args = parser.parse_args()
    server = HealthServer(latest_snapshot_path=args.latest_snapshot_path)
    return server.serve_forever()


if __name__ == "__main__":
    raise SystemExit(main())
