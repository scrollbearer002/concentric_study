from __future__ import annotations

from pathlib import Path

from agent_infra.host_tool_health import CheckResult, HostToolHealth


def _fake_result(name: str, passed: bool) -> CheckResult:
    return CheckResult(
        name=name,
        check_type="fake",
        passed=passed,
        detail=name,
    )


def test_host_health_keeps_browser_target_optional_without_url(monkeypatch) -> None:
    checker = HostToolHealth(
        operator_dir=Path(__file__).resolve().parents[1],
        cre_dir=Path(__file__).resolve().parent,
    )

    def fake_run_check(check: dict[str, str]) -> CheckResult:
        name = check["name"]
        mapping = {
            "venv_": True,
            "native_": True,
            "osascript_": True,
            "system_events_": True,
            "screencapture_": True,
            "safari_": False,
            "security_": False,
            "window_capture_": True,
            "macapptree_": False,
            "pyax_": False,
            "sentence_": False,
            "openai_": False,
        }
        for prefix, passed in mapping.items():
            if name.startswith(prefix):
                return _fake_result(name, passed)
        return _fake_result(name, False)

    monkeypatch.setattr(checker, "_run_check", fake_run_check)
    payload = checker.evaluate(has_url=False)
    assert payload["all_required_ready"] is True
    assert payload["missing_required_classes"] == []
    assert payload["selected"]["runtime_python_selected"] == "operator_venv_python"
    assert payload["selected"]["screen_capture"] == "screencapture_cli"
    assert payload["classes"]["browser_target"]["required"] is False


def test_host_health_requires_browser_target_when_url_is_present(monkeypatch) -> None:
    checker = HostToolHealth(
        operator_dir=Path(__file__).resolve().parents[1],
        cre_dir=Path(__file__).resolve().parent,
    )

    available_tools = {
        "operator_venv_python",
        "pyobjc_native_stack",
        "osascript_system_events",
        "screencapture_cli",
    }

    def fake_run_check(check: dict[str, str]) -> CheckResult:
        name = check["name"]
        mapping = {
            "venv": "operator_venv_python",
            "native": "pyobjc_native_stack",
            "osascript": "osascript_system_events",
            "system": "osascript_system_events",
            "screencapture": "screencapture_cli",
            "safari": "safari_bundle",
        }
        tool_id = next((value for prefix, value in mapping.items() if name.startswith(prefix)), "")
        return _fake_result(name, tool_id in available_tools)

    monkeypatch.setattr(checker, "_run_check", fake_run_check)
    payload = checker.evaluate(has_url=True)
    assert payload["all_required_ready"] is False
    assert payload["missing_required_classes"] == ["browser_target"]
