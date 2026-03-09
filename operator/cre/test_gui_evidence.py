from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load_gui_evidence_module():
    path = Path(__file__).resolve().parent / "project_understanding" / "tools" / "gui_evidence.py"
    spec = importlib.util.spec_from_file_location("gui_evidence_module", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["gui_evidence_module"] = module
    spec.loader.exec_module(module)
    return module


def test_detects_scriptable_vs_visible_window_contradiction(monkeypatch):
    module = _load_gui_evidence_module()

    monkeypatch.setattr(module, "get_frontmost_application_name", lambda: "Safari")
    monkeypatch.setattr(
        module,
        "_system_events_frontmost_probe",
        lambda: {
            "status": "ok",
            "stdout": "Safari",
            "stderr": "",
            "returncode": 0,
            "ok": True,
            "frontmost_app": "Safari",
        },
    )
    monkeypatch.setattr(
        module,
        "_scriptable_window_probe",
        lambda app_name: {
            "status": "ok",
            "ok": True,
            "running": True,
            "window_count": 1,
            "stdout": "1",
            "stderr": "",
            "returncode": 0,
        },
    )
    monkeypatch.setattr(
        module,
        "_system_events_window_probe",
        lambda app_name: {
            "status": "ok",
            "ok": True,
            "process_exists": True,
            "window_count": 0,
            "stdout": "0",
            "stderr": "",
            "returncode": 0,
        },
    )
    monkeypatch.setattr(module, "get_front_window_info", lambda owner_name=None: None)

    payload = module.app_gui_evidence("Safari", require_frontmost=True, capture=False)

    assert payload["ready_for_visible_task"] is False
    assert payload["evidence_level"] == "blocked"
    assert any("Quartz does not report an eligible onscreen window" in item for item in payload["contradictions"])


def test_ready_when_frontmost_ax_quartz_and_capture_all_agree(monkeypatch):
    module = _load_gui_evidence_module()

    monkeypatch.setattr(module, "get_frontmost_application_name", lambda: "Safari")
    monkeypatch.setattr(
        module,
        "_system_events_frontmost_probe",
        lambda: {
            "status": "ok",
            "stdout": "Safari",
            "stderr": "",
            "returncode": 0,
            "ok": True,
            "frontmost_app": "Safari",
        },
    )
    monkeypatch.setattr(
        module,
        "_scriptable_window_probe",
        lambda app_name: {
            "status": "ok",
            "ok": True,
            "running": True,
            "window_count": 1,
            "stdout": "1",
            "stderr": "",
            "returncode": 0,
        },
    )
    monkeypatch.setattr(
        module,
        "_system_events_window_probe",
        lambda app_name: {
            "status": "ok",
            "ok": True,
            "process_exists": True,
            "window_count": 1,
            "stdout": "1",
            "stderr": "",
            "returncode": 0,
        },
    )
    monkeypatch.setattr(
        module,
        "get_front_window_info",
        lambda owner_name=None: {
            "owner_name": "Safari",
            "window_id": 123,
            "bounds": {"x": 0, "y": 0, "width": 1200, "height": 800},
        },
    )
    monkeypatch.setattr(
        module,
        "_window_capture_probe",
        lambda app_name: {"status": "ok", "ok": True, "path": "/tmp/fake.png", "owner_name": "Safari"},
    )

    payload = module.app_gui_evidence("Safari", require_frontmost=True, capture=True)

    assert payload["ready_for_visible_task"] is True
    assert payload["evidence_level"] == "screen_captured"
    assert payload["blockers"] == []
