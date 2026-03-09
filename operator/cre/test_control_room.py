from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load_control_room_module():
    path = Path(__file__).resolve().parent / "project_understanding" / "tools" / "control_room.py"
    spec = importlib.util.spec_from_file_location("control_room_module", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["control_room_module"] = module
    spec.loader.exec_module(module)
    return module


def test_build_snapshot_has_expected_sections():
    module = _load_control_room_module()
    snapshot = module.build_snapshot()

    assert "diagrams" in snapshot
    assert "master_systems" in snapshot["diagrams"]
    assert "runtime_overview" in snapshot["diagrams"]
    assert "station_focus" in snapshot["diagrams"]
    assert "latest_run" in snapshot
    assert "conformance" in snapshot
    assert "calibration" in snapshot
    assert "stations" in snapshot
    assert snapshot["stations"]
    assert "viewpoints" in snapshot
    assert "laws" in snapshot
    assert "selection" in snapshot
    assert "action_space_conformance" in snapshot
    assert "observability" in snapshot
    assert "sourcegraph" in snapshot
    assert "structurizr" in snapshot
    assert "d2" in snapshot["diagrams"]
    assert snapshot["selection"]["default_station_id"] in {station["id"] for station in snapshot["stations"]}
    assert snapshot["action_space_conformance"]["missing_handler_actions"] == []
    assert len(snapshot["viewpoints"]) >= 1
    assert len(snapshot["laws"]) >= 1
    assert snapshot["selection"]["default_station_id"] in snapshot["sourcegraph"]["station_queries"]
    assert snapshot["sourcegraph"]["repo_name"] is None or snapshot["sourcegraph"]["repo_name"]
    assert "signal" in snapshot["sourcegraph"]["local_index"]
    assert snapshot["structurizr"]["workspace_dsl"]
    assert snapshot["structurizr"]["docs"]["count"] >= 1
    assert snapshot["structurizr"]["adrs"]["count"] >= 1
    assert (module.STRUCTURIZR_WORKSPACE_DSL).exists()
    if module.STRUCTURIZR_BIN:
        assert snapshot["structurizr"]["exports"]["static_index"]
        assert snapshot["structurizr"]["exports"]["json_workspace"]
        assert snapshot["structurizr"]["export_error"] is None
    if snapshot["diagrams"]["d2"]["available"]:
        assert snapshot["diagrams"]["d2"]["master_systems"]
        assert snapshot["diagrams"]["d2"]["runtime_overview"]
        assert snapshot["selection"]["default_station_id"] in snapshot["diagrams"]["d2"]["station_focus"]
        assert (module.D2_SVG_DIR / "master_systems.svg").exists()
        assert (module.D2_SRC_DIR / "master_systems.d2").exists()


def test_latest_run_summary_shape():
    module = _load_control_room_module()
    latest = module.latest_run_summary()

    assert "run_id" in latest
    assert "task_result" in latest
    assert "trace_tail" in latest
    assert "station_activity_counts" in latest
    assert isinstance(latest["trace_tail"], list)
    if latest["trace_tail"]:
        assert "station_ids" in latest["trace_tail"][0]
        assert isinstance(latest["trace_tail"][0]["station_ids"], list)


def test_parse_action_handler_keys_finds_live_dispatch_surface():
    module = _load_control_room_module()
    keys = module.parse_action_handler_keys(Path(__file__).resolve().parents[1] / "agent_infra" / "action_handlers.py")

    assert "click" in keys
    assert "visual_assert" in keys
