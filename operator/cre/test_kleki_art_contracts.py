#!/usr/bin/env python3
from __future__ import annotations

from types import SimpleNamespace

import agent_infra.action_handlers as action_handlers


def test_draw_segments_prefers_shift_modifier_for_straight_lines() -> None:
    calls: list[tuple[str, object]] = []

    class FakeAgent:
        def enforce_app_focus(self, app_name: str) -> None:
            calls.append(("focus", app_name))

        def execute_draw_path_with_modifier(self, rel_segment, cx: int, cy: int, *, modifier: str = "shift") -> None:
            calls.append(("modifier", (tuple(rel_segment), cx, cy, modifier)))

        def execute_draw_path(self, rel_segment, cx: int, cy: int) -> None:
            calls.append(("plain", (tuple(rel_segment), cx, cy)))

    ctx = SimpleNamespace(use_enterprise=True, agent=FakeAgent(), cx=1440, cy=900)
    result = action_handlers._handle_draw_segments(
        ctx,
        {
            "segments": [
                [[1200, 1200], [1200, 400]],
                [[1200, 400], [1600, 400]],
            ],
            "straight": True,
        },
    )

    assert result["status"] == "ok"
    modifier_calls = [call for call in calls if call[0] == "modifier"]
    assert len(modifier_calls) == 2
    assert not [call for call in calls if call[0] == "plain"]



def test_kleki_reset_render_state_executes_canonical_sequence(monkeypatch) -> None:
    calls: list[tuple[str, dict]] = []

    monkeypatch.setattr(action_handlers, "_handle_kleki_select_tool", lambda ctx, args: calls.append(("tool", dict(args))) or {"status": "ok"})
    monkeypatch.setattr(action_handlers, "_kleki_click_site_button", lambda ctx, *keys: calls.append(("brush_shape", {"keys": keys})) or True)
    monkeypatch.setattr(action_handlers, "_handle_kleki_set_scatter", lambda ctx, args: calls.append(("scatter", dict(args))) or {"status": "ok"})
    monkeypatch.setattr(action_handlers, "_handle_kleki_set_stabilizer", lambda ctx, args: calls.append(("stabilizer", dict(args))) or {"status": "ok"})
    monkeypatch.setattr(action_handlers, "_handle_kleki_set_brush_size", lambda ctx, args: calls.append(("size", dict(args))) or {"status": "ok"})
    monkeypatch.setattr(action_handlers, "_handle_kleki_set_opacity", lambda ctx, args: calls.append(("opacity", dict(args))) or {"status": "ok"})

    ctx = SimpleNamespace(use_enterprise=True, agent=object())
    result = action_handlers._handle_kleki_reset_render_state(ctx, {})

    assert result["status"] == "ok"
    assert calls == [
        ("tool", {"tool": "brush"}),
        ("brush_shape", {"keys": ("brush_shape_round",)}),
        ("scatter", {"scatter": "0"}),
        ("stabilizer", {"stabilizer": "1"}),
        ("size", {"size": "very thin"}),
        ("opacity", {"opacity": "100%"}),
    ]



def test_kleki_select_tool_prefers_shortcut_and_site_alias() -> None:
    clicks: list[tuple[int, int]] = []
    keys: list[tuple[int | str, object]] = []

    class FakeAgent:
        def enforce_app_focus(self, app_name: str) -> None:
            assert app_name == "Safari"

        def execute_global_click(self, x: int, y: int) -> None:
            clicks.append((x, y))

        def execute_keystroke(self, key: int | str, app_focus=None) -> None:
            keys.append((key, app_focus))

    ctx = SimpleNamespace(
        use_enterprise=True,
        agent=FakeAgent(),
        site_knowledge=SimpleNamespace(
            button_map={
                "brush_tool_button": SimpleNamespace(pixel_x=2520, pixel_y=375),
            }
        ),
    )

    result = action_handlers._handle_kleki_select_tool(ctx, {"tool": "brush"})
    assert result["status"] == "ok"
    assert clicks == [(2520, 375)]
    assert keys == [("b", None)]
