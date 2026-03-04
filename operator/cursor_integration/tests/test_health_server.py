from __future__ import annotations

import json
from pathlib import Path

from cursor_integration.mcp.health_server import HealthServer


class _FakeChecker:
    def evaluate(self, *, has_url: bool = False):
        return {
            "required_classes": ["runtime_python_selected", "browser_target"] if has_url else ["runtime_python_selected"],
            "selected": {
                "runtime_python_selected": "operator_venv_python",
                "browser_target": "safari_bundle" if has_url else None,
            },
            "missing_required_classes": [] if has_url else [],
            "all_required_ready": True,
            "classes": {
                "runtime_python_selected": {
                    "required": True,
                    "available_providers": ["operator_venv_python"],
                    "selected_tool": "operator_venv_python",
                },
                "browser_target": {
                    "required": has_url,
                    "available_providers": ["safari_bundle"],
                    "selected_tool": "safari_bundle" if has_url else None,
                },
            },
        }

    def summary(self, payload):
        return {
            "selected": payload["selected"],
            "all_required_ready": payload["all_required_ready"],
        }


def test_health_server_returns_summary_and_class_checks(tmp_path: Path) -> None:
    latest = tmp_path / "latest.json"
    latest.write_text(
        json.dumps({"app": {"version": {"value": "2.6.10", "provenance": "direct"}}}),
        encoding="utf-8",
    )
    snapshot = {
        "app": {"version": {"value": "2.6.11", "provenance": "direct"}},
        "captured_at_utc": "2026-03-04T00:00:00Z",
    }
    server = HealthServer(
        checker=_FakeChecker(),
        snapshot_provider=lambda: snapshot,
        latest_snapshot_path=latest,
    )

    summary = server.health_summary(has_url=True)
    assert summary["summary"]["all_required_ready"] is True
    assert summary["selected"]["browser_target"] == "safari_bundle"

    class_row = server.check_tool_class("runtime_python_selected")
    assert class_row["class_row"]["selected_tool"] == "operator_venv_python"

    current = server.cursor_environment_snapshot()
    assert current["snapshot"]["app"]["version"]["value"] == "2.6.11"
    assert current["diff_vs_latest"]["has_changes"] is True


def test_health_server_compares_environment_baselines(tmp_path: Path) -> None:
    left = tmp_path / "left.json"
    right = tmp_path / "right.json"
    left.write_text(
        json.dumps({"app": {"version": {"value": "2.6.10", "provenance": "direct"}}}),
        encoding="utf-8",
    )
    right.write_text(
        json.dumps({"app": {"version": {"value": "2.6.11", "provenance": "direct"}}}),
        encoding="utf-8",
    )
    server = HealthServer(checker=_FakeChecker(), snapshot_provider=lambda: {}, latest_snapshot_path=right)
    diff = server.compare_environment_baselines(str(left), str(right))
    assert diff["diff"]["has_changes"] is True
    assert diff["diff"]["changed"]["app.version"]["after"] == "2.6.11"
