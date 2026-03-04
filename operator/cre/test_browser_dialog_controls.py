from __future__ import annotations

from types import SimpleNamespace

from action_space import UnifiedActionSpace
import agent_infra.action_contracts as action_contracts
import agent_infra.action_handlers as action_handlers
import agent_infra.recovery as recovery


def test_beforeunload_choice_normalization() -> None:
    assert action_handlers._normalize_beforeunload_choice("stay on page") == ("stay", "Stay on Page")
    assert action_handlers._normalize_beforeunload_choice("stay_on_page") == ("stay", "Stay on Page")
    assert action_handlers._normalize_beforeunload_choice("leave page") == ("leave", "Leave Page")
    assert action_handlers._normalize_beforeunload_choice("leave_page") == ("leave", "Leave Page")


def test_beforeunload_geometry_estimate_uses_window_midpoint() -> None:
    bounds = {"x": 100, "y": 50, "width": 1200, "height": 900}
    stay_x, stay_y = action_handlers._estimate_beforeunload_button_point(bounds, "stay")
    leave_x, leave_y = action_handlers._estimate_beforeunload_button_point(bounds, "leave")

    assert stay_y == leave_y
    assert stay_x < leave_x
    assert stay_y == 401


def test_browser_beforeunload_dialog_prefers_vlm_location(monkeypatch) -> None:
    clicks: list[tuple[int, int]] = []

    class FakeAgent:
        def enforce_app_focus(self, app_name: str) -> None:
            assert app_name == "Safari"

        def execute_global_click(self, x: int, y: int) -> None:
            clicks.append((x, y))

    monkeypatch.setattr(
        action_handlers,
        "_try_beforeunload_choice_via_vlm",
        lambda ctx, choice, label: (901, 477),
    )

    ctx = SimpleNamespace(
        use_enterprise=True,
        agent=FakeAgent(),
        cx=1440,
        cy=900,
        vision_engine=object(),
    )
    result = action_handlers._handle_browser_beforeunload_dialog(ctx, {"choice": "stay"})

    assert result["status"] == "ok"
    assert result["strategy"] == "vlm"
    assert clicks == [(901, 477)]


def test_browser_beforeunload_dialog_falls_back_to_geometry(monkeypatch) -> None:
    clicks: list[tuple[int, int]] = []

    class FakeAgent:
        def enforce_app_focus(self, app_name: str) -> None:
            assert app_name == "Safari"

        def execute_global_click(self, x: int, y: int) -> None:
            clicks.append((x, y))

    monkeypatch.setattr(action_handlers, "_try_beforeunload_choice_via_vlm", lambda ctx, choice, label: None)
    monkeypatch.setattr(
        action_handlers,
        "get_front_window_info",
        lambda owner_name=None: {
            "owner_name": "Safari",
            "window_id": 123,
            "bounds": {"x": 100, "y": 50, "width": 1200, "height": 900},
        },
    )

    ctx = SimpleNamespace(
        use_enterprise=True,
        agent=FakeAgent(),
        cx=1440,
        cy=900,
        vision_engine=object(),
    )
    result = action_handlers._handle_browser_beforeunload_dialog(ctx, {"choice": "leave"})

    assert result["status"] == "ok"
    assert result["strategy"] == "geometry"
    assert clicks == [(772, 401)]


def test_beforeunload_dialog_detection_supports_contract_repairs() -> None:
    diagnosis = {
        "description": "A browser confirmation dialog asks 'Are you sure you want to leave this page?' with Stay on Page and Leave Page buttons.",
        "missing_precondition": "none",
    }
    assert action_contracts.needs_beforeunload_dialog_repair(diagnosis) is True


def test_recovery_executes_explicit_stay_on_page_action() -> None:
    calls: list[dict[str, str]] = []

    class FakeAgent:
        def execute_keystroke(self, key: int) -> None:
            raise AssertionError("should not fall back to raw keystroke")

        def execute_global_click(self, x: int, y: int) -> None:
            raise AssertionError("recovery should route through explicit dialog handler")

    original_handler = recovery.ACTION_HANDLERS.get("browser_beforeunload_dialog")
    original_exec_log = recovery._exec_log_line
    original_checkpoint = recovery._capture_visual_monitor_checkpoint
    recovery.ACTION_HANDLERS["browser_beforeunload_dialog"] = lambda ctx, args: calls.append(dict(args)) or {"status": "ok"}
    recovery._exec_log_line = lambda *args, **kwargs: None
    recovery._capture_visual_monitor_checkpoint = lambda *args, **kwargs: None

    try:
        ctx = SimpleNamespace(use_enterprise=True, agent=FakeAgent(), cx=1440, cy=900)
        recovery._execute_recovery(ctx, {"recovery_action": "stay_on_page", "description": "beforeunload dialog"})
    finally:
        recovery._exec_log_line = original_exec_log
        recovery._capture_visual_monitor_checkpoint = original_checkpoint
        if original_handler is None:
            recovery.ACTION_HANDLERS.pop("browser_beforeunload_dialog", None)
        else:
            recovery.ACTION_HANDLERS["browser_beforeunload_dialog"] = original_handler

    assert calls == [{"choice": "stay"}]


def test_action_space_exposes_browser_beforeunload_dialog() -> None:
    space = UnifiedActionSpace()
    spec = space.get("browser_beforeunload_dialog")
    assert spec is not None
    assert spec.handler_key == "browser_beforeunload_dialog"
