from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace


def _load_mission_control_module():
    path = Path(__file__).resolve().parent / "project_understanding" / "tools" / "mission_control.py"
    spec = importlib.util.spec_from_file_location("mission_control_module", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["mission_control_module"] = module
    spec.loader.exec_module(module)
    return module


def test_profiles_resolve_expected_services():
    module = _load_mission_control_module()

    assert module.desired_services("live") == ["phoenix", "control_room"]
    assert module.desired_services("architecture") == ["control_room", "structurizr"]
    assert module.desired_services("full") == ["phoenix", "control_room", "structurizr"]


def test_state_round_trip(tmp_path):
    module = _load_mission_control_module()
    module.MISSION_DIR = tmp_path / "mission_control"
    module.LOGS_DIR = module.MISSION_DIR / "logs"
    module.STATE_FILE = module.MISSION_DIR / "state.json"

    state = {"services": {"phoenix": {"pid": 1234, "managed": True}}}
    module.save_state(state)
    loaded = module.load_state()

    assert loaded["services"]["phoenix"]["pid"] == 1234
    assert loaded["updated_at"]


def test_doctor_payload_shape(monkeypatch, tmp_path):
    module = _load_mission_control_module()

    fake_python = tmp_path / "python"
    fake_python.write_text("", encoding="utf-8")
    fake_phoenix = tmp_path / "phoenix"
    fake_phoenix.write_text("", encoding="utf-8")
    module.VENV_PYTHON = fake_python

    fake_control_room = SimpleNamespace(
        sourcegraph_repo_name=lambda: "github.com/cpardo91/concentric_study",
        sourcegraph_base_url=lambda: "https://sourcegraph.com",
        CACHE=SimpleNamespace(get_or_build=lambda: {"status": "Conformance Passing", "observability": {"available": True}}),
    )
    fake_phoenix_launcher = SimpleNamespace(PHOENIX_BIN=fake_phoenix, PYTHON_BIN=fake_python)
    monkeypatch.setattr(module, "import_control_room", lambda: fake_control_room)
    monkeypatch.setattr(module, "import_phoenix_launcher", lambda: fake_phoenix_launcher)
    monkeypatch.setattr(module, "gui_evidence_runtime_payload", lambda: {"ok": True, "python": str(fake_python), "script": "/tmp/gui_evidence.py"})
    monkeypatch.setattr(module, "docker_daemon_running", lambda: True)

    def fake_which(name: str):
        mapping = {
            "d2": "/opt/homebrew/bin/d2",
            "structurizr-cli": "/opt/homebrew/bin/structurizr-cli",
            "dot": "/opt/homebrew/bin/dot",
            "docker": "/Applications/Docker.app/Contents/Resources/bin/docker",
        }
        return mapping.get(name)

    monkeypatch.setattr(module.shutil, "which", fake_which)

    payload = module.doctor_payload()

    assert payload["overall_ok"] is True
    assert payload["checks"]["repo_venv_python"]["ok"] is True
    assert payload["checks"]["control_room_snapshot"]["ok"] is True
    assert payload["checks"]["sourcegraph_repo"]["repo_name"] == "github.com/cpardo91/concentric_study"
    assert payload["checks"]["gui_evidence_runtime"]["ok"] is True


def test_evidence_payload_shape(monkeypatch):
    module = _load_mission_control_module()

    class FakeCompleted:
        returncode = 0
        stdout = json.dumps(
            {
                "target_app": "Safari",
                "require_frontmost": True,
                "ready_for_visible_task": False,
                "blockers": ["Safari is not frontmost."],
                "evidence_level": "blocked",
            }
        )
        stderr = ""

    monkeypatch.setattr(module, "VENV_PYTHON", Path(sys.executable))
    monkeypatch.setattr(module.subprocess, "run", lambda *args, **kwargs: FakeCompleted())

    payload = module.evidence_payload("Safari", require_frontmost=True, capture=False, strict=False)

    assert payload["target_app"] == "Safari"
    assert payload["ready_for_visible_task"] is False
    assert payload["evidence_level"] == "blocked"
