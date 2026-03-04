from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import agent_infra.action_handlers as action_handlers


class _FakeConfirmationResult:
    def __init__(self, **payload):
        self._payload = payload

    def model_dump(self) -> dict:
        return dict(self._payload)


def test_confirm_click_target_uses_cursor_visible_capture(monkeypatch, tmp_path: Path) -> None:
    captures: list[tuple[str, dict]] = []
    logs: list[tuple[str, dict]] = []

    class FakeAgent:
        def __init__(self) -> None:
            self.moves: list[tuple[int, int]] = []

        def enforce_app_focus(self, app_name: str) -> None:
            assert app_name == "Safari"

        def execute_move_mouse(self, x: int, y: int) -> None:
            self.moves.append((x, y))

        def confirm_click_target(self, image_path: str, **kwargs):
            assert image_path.endswith("_preclick_confirm.png")
            return _FakeConfirmationResult(
                approved=True,
                target_under_cursor=True,
                blockers_present=False,
                expected_effect_likely=True,
                confidence=5,
                rationale="Target looks correct.",
                suggested_action="Proceed.",
            )

    def fake_capture(path, **kwargs):
        captures.append((str(path), dict(kwargs)))
        Path(path).write_bytes(b"png")
        return {"mode": "window", "path": str(path)}

    monkeypatch.setattr(action_handlers, "capture_front_window", fake_capture)
    monkeypatch.setattr(action_handlers, "_exec_log_line", lambda event, detail=None, data=None: logs.append((event, data or {})))

    ctx = SimpleNamespace(
        use_enterprise=True,
        agent=FakeAgent(),
        url="https://example.com",
        cre_dir=tmp_path,
    )

    result = action_handlers._confirm_click_target(
        ctx,
        pixel_x=220,
        pixel_y=160,
        label="Continue",
        expected_effect="Continue to the next step.",
        source="direct_coords",
    )

    assert result["approved"] is True
    assert captures[0][1]["include_cursor"] is True
    assert captures[0][1]["owner_name"] == "Safari"
    assert ctx.agent.moves == [(220, 160)]
    assert logs[0][0] == "preclick_confirmation"


def test_handle_click_blocks_when_preclick_confirmation_fails(monkeypatch, tmp_path: Path) -> None:
    clicks: list[tuple[int, int]] = []

    class FakeAgent:
        def enforce_app_focus(self, app_name: str) -> None:
            assert app_name == "Safari"

        def execute_global_click(self, x: int, y: int) -> None:
            clicks.append((x, y))

    monkeypatch.setattr(
        action_handlers,
        "_confirm_click_target",
        lambda ctx, **kwargs: {
            "approved": False,
            "confidence": 1,
            "blockers_present": True,
            "target_under_cursor": False,
            "expected_effect_likely": False,
            "rationale": "A blocking dialog may be present.",
            "suggested_action": "Re-check the page.",
        },
    )

    ctx = SimpleNamespace(
        use_enterprise=True,
        agent=FakeAgent(),
        cre_dir=tmp_path,
    )

    result = action_handlers._handle_click(
        ctx,
        {
            "x": 300,
            "y": 240,
            "label": "Continue",
            "confirm_before_click": True,
            "expected_effect": "Proceed to the next page.",
        },
    )

    assert result["status"] == "blocked"
    assert result["reason"] == "preclick_confirmation_failed"
    assert clicks == []


def test_handle_click_executes_when_preclick_confirmation_passes(monkeypatch, tmp_path: Path) -> None:
    clicks: list[tuple[int, int]] = []

    class FakeAgent:
        def execute_global_click(self, x: int, y: int) -> None:
            clicks.append((x, y))

    monkeypatch.setattr(
        action_handlers,
        "_confirm_click_target",
        lambda ctx, **kwargs: {
            "approved": True,
            "confidence": 5,
            "blockers_present": False,
            "target_under_cursor": True,
            "expected_effect_likely": True,
            "rationale": "Looks safe.",
            "suggested_action": "Proceed.",
        },
    )

    ctx = SimpleNamespace(
        use_enterprise=True,
        agent=FakeAgent(),
        cre_dir=tmp_path,
    )

    result = action_handlers._handle_click(
        ctx,
        {
            "x": 410,
            "y": 280,
            "confirm_before_click": True,
            "expected_effect": "Open the selected item.",
        },
    )

    assert result["status"] == "ok"
    assert clicks == [(410, 280)]
