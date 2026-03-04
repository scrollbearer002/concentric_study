#!/usr/bin/env python3
"""Kleki live-reliability regression tests.

These tests lock in the fixes for the observed live Kleki failure mode:
generic panel clicks, Excalidraw-specific verification on Kleki, and
non-corrective retries after an invisible-stroke diagnosis.
"""

from __future__ import annotations

from types import SimpleNamespace

import agent
from action_space import UnifiedActionSpace
import agent_infra.action_handlers as action_handlers
import agent_infra.action_contracts as action_contracts


def test_kleki_plan_normalization_rewrites_generic_panel_clicks() -> None:
    plan = [
        {"action": "clear_canvas", "args": {}, "description": "Clear canvas"},
        {"action": "key", "args": {"key": "b"}, "description": "Select brush"},
        {"action": "click", "args": {"label": "hex_color_input"}, "description": "Select black color"},
        {"action": "click", "args": {"label": "Size 4"}, "description": "Set brush size to 4"},
    ]

    normalized = agent._normalize_plan_for_site(
        plan,
        "https://kleki.com",
        "Draw a skyscraper with profuse shading",
    )

    assert normalized[0]["action"] == "kleki_clear_canvas"
    assert normalized[1]["action"] == "kleki_reset_render_state"
    assert normalized[2]["action"] == "kleki_select_tool"
    assert normalized[2]["args"]["tool"] == "brush"
    assert normalized[3]["action"] == "kleki_set_color"
    assert normalized[3]["args"]["color"] == "black"
    assert "Kleki" in normalized[3]["visual_assert"]
    assert normalized[4]["action"] == "kleki_set_brush_size"
    assert normalized[4]["args"]["size"] == "thin"


def test_kleki_plan_normalization_rewrites_facade_grid_to_segments() -> None:
    plan = [
        {
            "action": "draw_path",
            "args": {
                "vertices": [
                    [1050, 1500], [1450, 1500],
                    [1050, 1410], [1450, 1410],
                    [1050, 1330], [1450, 1330],
                ]
            },
            "description": "Draw horizontal lines for the facade grid",
        }
    ]

    normalized = agent._normalize_plan_for_site(
        plan,
        "https://kleki.com",
        "Draw a skyscraper with profuse shading",
    )

    assert normalized[1]["action"] == "draw_segments"
    segments = normalized[1]["args"]["segments"]
    assert segments == [
        [[1050, 1500], [1450, 1500]],
        [[1050, 1410], [1450, 1410]],
        [[1050, 1330], [1450, 1330]],
    ]
    assert normalized[1]["args"]["straight"] is True


def test_kleki_plan_normalization_rewrites_structural_two_point_line_to_draw_segments() -> None:
    plan = [
        {
            "action": "draw_path",
            "args": {"vertices": [[850, 1550], [1250, 400]]},
            "description": "Draw the left vertical edge of the skyscraper",
        }
    ]

    normalized = agent._normalize_plan_for_site(
        plan,
        "https://kleki.com",
        "Draw a skyscraper with profuse shading",
    )

    assert normalized[1]["action"] == "draw_segments"
    assert normalized[1]["args"]["segments"] == [[[850, 1550], [1250, 400]]]
    assert normalized[1]["args"]["straight"] is True


def test_kleki_plan_normalization_rewrites_fill_quad_to_scanlines() -> None:
    plan = [
        {
            "action": "draw_path",
            "args": {
                "vertices": [[750, 1600], [1150, 200], [1350, 200], [1750, 1600]],
            },
            "description": "Fill the central facade with a light gray base tone",
        }
    ]

    normalized = agent._normalize_plan_for_site(
        plan,
        "https://kleki.com",
        "Draw a skyscraper with profuse shading",
    )

    segments = normalized[1]["args"]["segments"]
    assert len(segments) > 10
    assert segments[0][0][1] == segments[0][1][1]
    assert segments[-1][0][1] == segments[-1][1][1]


def test_kleki_plan_normalization_rewrites_open_fill_polyline_to_segments() -> None:
    plan = [
        {
            "action": "draw_path",
            "args": {
                "vertices": [
                    [905, 1445], [1495, 1445],
                    [905, 1200], [1495, 1200],
                    [905, 950], [1495, 950],
                    [905, 700], [1495, 700],
                    [905, 450], [1495, 450],
                    [905, 355],
                ]
            },
            "description": "Apply a base layer of light gray shading to the front face",
        }
    ]

    normalized = agent._normalize_plan_for_site(
        plan,
        "https://kleki.com",
        "Draw a skyscraper with profuse shading",
    )

    segments = normalized[1]["args"]["segments"]
    assert segments == [
        [[905, 1445], [1495, 1445]],
        [[905, 1200], [1495, 1200]],
        [[905, 950], [1495, 950]],
        [[905, 700], [1495, 700]],
        [[905, 450], [1495, 450]],
    ]


def test_action_space_exposes_kleki_specific_controls() -> None:
    space = UnifiedActionSpace()
    assert space.get("kleki_clear_canvas") is not None
    assert space.get("kleki_set_color") is not None
    assert space.get("kleki_set_brush_size") is not None
    assert space.get("kleki_set_opacity") is not None
    assert space.get("kleki_set_scatter") is not None
    assert space.get("kleki_set_stabilizer") is not None
    assert space.get("kleki_select_tool") is not None
    assert space.get("kleki_reset_render_state") is not None
    assert space.get("draw_segments") is not None
    assert action_handlers.ACTION_HANDLERS.get("visual_assert") is not None


def test_kleki_effect_checks_are_site_aware() -> None:
    ctx = SimpleNamespace(url="https://kleki.com")
    draw_prompt = action_contracts.get_action_effect_check(ctx, "draw_path", {})
    assert draw_prompt is not None
    assert "Kleki" in draw_prompt
    assert "Excalidraw" not in draw_prompt

    color_prompt = action_contracts.get_action_effect_check(ctx, "kleki_set_color", {"color": "black"})
    assert color_prompt is not None
    assert "lower-left grayscale region" in color_prompt

    size_prompt = action_contracts.get_action_effect_check(ctx, "kleki_set_brush_size", {"size": "very thin"})
    assert size_prompt is not None
    assert "Size field show 1" in size_prompt

    opacity_prompt = action_contracts.get_action_effect_check(ctx, "kleki_set_opacity", {"opacity": "medium"})
    assert opacity_prompt is not None
    assert "medium value" in opacity_prompt

    scatter_prompt = action_contracts.get_action_effect_check(ctx, "kleki_set_scatter", {"scatter": "0"})
    assert scatter_prompt is not None
    assert "Scatter field show 0" in scatter_prompt

    stabilizer_prompt = action_contracts.get_action_effect_check(ctx, "kleki_set_stabilizer", {"stabilizer": "1"})
    assert stabilizer_prompt is not None
    assert "near 1" in stabilizer_prompt

    tool_prompt = action_contracts.get_action_effect_check(ctx, "kleki_select_tool", {"tool": "shape"})
    assert tool_prompt is not None
    assert "straight-line-capable" in tool_prompt


def test_invisible_kleki_draw_diagnosis_triggers_contrast_repair() -> None:
    diagnosis = {
        "description": "The selected brush color is white, which is the same as the canvas background color.",
        "missing_precondition": "A contrasting drawing color is not selected.",
    }
    assert action_contracts.needs_contrast_repair(diagnosis)


def test_kleki_grayscale_anchor_uses_site_knowledge_coordinates() -> None:
    clicks: list[tuple[int, int]] = []

    class FakeAgent:
        def execute_global_click(self, x: int, y: int) -> None:
            clicks.append((x, y))

    ctx = SimpleNamespace(
        agent=FakeAgent(),
        site_knowledge=SimpleNamespace(
            button_map={
                "color_picker_box": SimpleNamespace(pixel_x=2520, pixel_y=675),
            }
        ),
    )

    used = action_handlers._kleki_try_grayscale_click_from_site_knowledge(ctx, "black")
    assert used
    assert clicks == [(2360, 860)]


def test_kleki_brush_size_slider_uses_site_knowledge_coordinates() -> None:
    clicks: list[tuple[int, int]] = []

    class FakeAgent:
        def execute_global_click(self, x: int, y: int) -> None:
            clicks.append((x, y))

    ctx = SimpleNamespace(
        agent=FakeAgent(),
        site_knowledge=SimpleNamespace(
            button_map={
                "brush_size_slider": SimpleNamespace(pixel_x=2520, pixel_y=1125),
            }
        ),
    )

    used = action_handlers._kleki_try_brush_size_from_site_knowledge(ctx, "very thin")
    assert used
    assert clicks == [(2280, 1125)]


def test_kleki_opacity_slider_uses_site_knowledge_coordinates() -> None:
    clicks: list[tuple[int, int]] = []
    keys: list[int | str] = []
    command_select: list[str] = []

    class FakeAgent:
        def execute_global_click(self, x: int, y: int) -> None:
            clicks.append((x, y))

        def execute_keystroke(self, key: int | str, app_focus=None) -> None:
            keys.append(key)

    ctx = SimpleNamespace(
        agent=FakeAgent(),
        site_knowledge=SimpleNamespace(
            button_map={
                "brush_opacity_slider": SimpleNamespace(pixel_x=2520, pixel_y=1275),
            }
        ),
    )

    original = action_handlers._send_command_select_all
    action_handlers._send_command_select_all = lambda: command_select.append("cmd+a")
    try:
        used = action_handlers._kleki_try_opacity_from_site_knowledge(ctx, "medium")
    finally:
        action_handlers._send_command_select_all = original

    assert used
    assert clicks == [(2520, 1275)]
    assert command_select == ["cmd+a"]
    assert keys == [51, 51, "5", "5", 36]


def test_kleki_scatter_slider_uses_site_knowledge_coordinates() -> None:
    clicks: list[tuple[int, int]] = []

    class FakeAgent:
        def execute_global_click(self, x: int, y: int) -> None:
            clicks.append((x, y))

    ctx = SimpleNamespace(
        agent=FakeAgent(),
        site_knowledge=SimpleNamespace(
            button_map={
                "brush_scatter_slider": SimpleNamespace(pixel_x=2520, pixel_y=1350),
            }
        ),
    )

    used = action_handlers._kleki_try_scatter_from_site_knowledge(ctx, "0")
    assert used
    assert clicks == [(2280, 1350)]


def test_kleki_stabilizer_control_uses_site_knowledge_coordinates() -> None:
    clicks: list[tuple[int, int]] = []
    keys: list[int | str] = []

    class FakeAgent:
        def execute_global_click(self, x: int, y: int) -> None:
            clicks.append((x, y))

        def execute_keystroke(self, key: int | str, app_focus=None) -> None:
            keys.append(key)

    ctx = SimpleNamespace(
        agent=FakeAgent(),
        site_knowledge=SimpleNamespace(
            button_map={
                "brush_stabilizer_control": SimpleNamespace(pixel_x=2760, pixel_y=975),
            }
        ),
    )

    used = action_handlers._kleki_try_stabilizer_from_site_knowledge(ctx, "1")
    assert used
    assert clicks == [(2760, 975)]
    assert keys == [51, 51, "1", 36]


def test_contract_registry_resolves_kleki_color_contract() -> None:
    ctx = SimpleNamespace(url="https://kleki.com")
    contract = action_contracts.resolve_action_contract(
        ctx,
        "kleki_set_color",
        {"color": "black"},
    )
    assert contract is not None
    assert contract.name == "kleki_color_selection"

    brush_contract = action_contracts.resolve_action_contract(
        ctx,
        "kleki_set_brush_size",
        {"size": "thin"},
    )
    assert brush_contract is not None
    assert brush_contract.name == "kleki_brush_size"

    scatter_contract = action_contracts.resolve_action_contract(
        ctx,
        "kleki_set_scatter",
        {"scatter": "0"},
    )
    assert scatter_contract is not None
    assert scatter_contract.name == "kleki_scatter"


def test_contract_repair_dispatches_site_specific_handler(monkeypatch) -> None:
    calls: list[dict] = []

    def fake_handler(ctx, args):
        calls.append(args)
        return {"status": "ok"}

    monkeypatch.setitem(action_contracts.ACTION_HANDLERS, "kleki_set_color", fake_handler)
    ctx = SimpleNamespace(url="https://kleki.com")
    diagnosis = {
        "description": "The selected brush color is white, which is the same as the canvas background color.",
        "missing_precondition": "A contrasting drawing color is not selected.",
    }
    used = action_contracts.apply_action_contract_repair(
        ctx,
        {"action": "kleki_set_color", "args": {"color": "black"}},
        diagnosis,
        attempt=0,
    )
    assert used
    assert calls == [{"color": "black"}]


def test_render_state_contract_repair_reruns_reset_handler(monkeypatch) -> None:
    calls: list[dict] = []

    def fake_handler(ctx, args):
        calls.append(dict(args))
        return {"status": "ok"}

    monkeypatch.setitem(action_contracts.ACTION_HANDLERS, "kleki_reset_render_state", fake_handler)
    ctx = SimpleNamespace(url="https://kleki.com")
    diagnosis = {
        "description": "The brush settings are incorrect. The brush size is set to 4 and the scatter is set to 27.",
        "missing_precondition": "Controlled architectural linework is not configured.",
    }
    used = action_contracts.apply_action_contract_repair(
        ctx,
        {"action": "kleki_reset_render_state", "args": {"size": "very thin", "scatter": "0", "opacity": "100%", "stabilizer": "1", "tool": "brush"}},
        diagnosis,
        attempt=0,
    )
    assert used
    assert calls == [{"size": "very thin", "scatter": "0", "opacity": "100%", "stabilizer": "1", "tool": "brush"}]


def test_kleki_clear_canvas_uses_window_scoped_focus_and_documented_shortcut(monkeypatch) -> None:
    clicks: list[tuple[int, int]] = []
    keys: list[int | str] = []

    class FakeAgent:
        def enforce_app_focus(self, app_name: str) -> None:
            assert app_name == "Safari"

        def execute_global_click(self, x: int, y: int) -> None:
            clicks.append((x, y))

        def execute_keystroke(self, key: int | str) -> None:
            keys.append(key)

    monkeypatch.setattr(
        action_handlers,
        "get_front_window_info",
        lambda owner_name=None: {
            "owner_name": "Safari",
            "window_id": 123,
            "bounds": {"x": 100, "y": 40, "width": 1200, "height": 800},
        },
    )

    ctx = SimpleNamespace(use_enterprise=True, agent=FakeAgent(), cx=1440, cy=900)
    result = action_handlers._handle_kleki_clear_canvas(ctx, {})

    assert result["status"] == "ok"
    assert result["shortcut"] == "delete_backspace"
    assert clicks == [(532, 456)]
    assert keys == [53, 51, 51]
