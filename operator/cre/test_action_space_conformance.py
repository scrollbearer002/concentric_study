#!/usr/bin/env python3
"""Planner/executor conformance regression tests."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from action_space import UnifiedActionSpace
import agent_infra.action_handlers as action_handlers
from agent_infra.research_agent import EquationMapping, EquationSolution, ResearchAgent, evaluate_phase3_equation_gate


def test_planner_visible_actions_are_dispatchable() -> None:
    space = UnifiedActionSpace()
    report = space.conformance_report(set(action_handlers.ACTION_HANDLERS.keys()))

    assert report["missing_handler_actions"] == []


def test_planner_context_hides_non_runtime_macros() -> None:
    space = UnifiedActionSpace()

    assert "login_flow" not in space.list_planner_names()
    assert "login_flow" not in space.to_planner_context()


def test_phase3_gate_rejects_invalid_fallback_actions() -> None:
    solution = EquationSolution(
        mappings=[
            EquationMapping(
                method_step_id="step_01",
                tool_name="universal_action_space",
                action_type="draw_path",
                fallback_action_type="not_dispatchable",
            )
        ],
        solution_confidence=0.9,
    )

    gate = evaluate_phase3_equation_gate(solution, UnifiedActionSpace().list_planner_names())

    assert gate["passed"] is False
    assert gate["invalid_fallback_action_types"] == ["not_dispatchable"]
    assert "all_fallback_actions_valid" in gate["fail_reasons"]


def test_type_text_handler_types_each_character() -> None:
    typed: list[object] = []

    class FakeAgent:
        def enforce_app_focus(self, app_name: str) -> None:
            assert app_name == "Safari"

        def execute_keystroke(self, key, app_focus=None) -> None:
            typed.append(key)

    ctx = SimpleNamespace(use_enterprise=True, agent=FakeAgent())
    result = action_handlers._handle_type_text(ctx, {"text": "ab c"})

    assert result["status"] == "ok"
    assert typed == ["a", "b", 49, "c"]


def test_legacy_bmw_detail_alias_uses_modern_phases(monkeypatch) -> None:
    calls: list[str] = []

    monkeypatch.setattr(
        action_handlers,
        "_handle_bmw_form_blocking",
        lambda ctx, args: calls.append("bmw_form_blocking") or {"status": "ok", "strokes": 3},
    )
    monkeypatch.setattr(
        action_handlers,
        "_handle_bmw_mechanical",
        lambda ctx, args: calls.append("bmw_mechanical") or {"status": "ok", "strokes": 5},
    )

    result = action_handlers._handle_bmw_details(SimpleNamespace(), {})

    assert result["status"] == "ok"
    assert result["strokes"] == 8
    assert calls == ["bmw_form_blocking", "bmw_mechanical"]


def test_draw_shape_semantics_route_to_shape_specific_execution(monkeypatch) -> None:
    drag_calls: list[dict[str, int | str]] = []

    monkeypatch.setattr(
        action_handlers,
        "_handle_drag_shape",
        lambda ctx, args: drag_calls.append(dict(args)) or {"status": "ok"},
    )

    result = action_handlers._handle_draw_shape(SimpleNamespace(), {"shape_type": "circle", "size": 80})

    assert result["status"] == "ok"
    assert drag_calls == [
        {
            "tool_key": "4",
            "width": 160,
            "height": 160,
            "offset_x": 0,
            "offset_y": 0,
        }
    ]


def test_a11y_snapshot_uses_injected_provider(monkeypatch, tmp_path) -> None:
    elements = [
        SimpleNamespace(label="Email", is_interactive=True),
        SimpleNamespace(label="Password", is_interactive=True),
        SimpleNamespace(label="", is_interactive=False),
    ]

    monkeypatch.setattr(action_handlers, "_get_a11y_snapshot", lambda app_name: elements)
    ctx = SimpleNamespace(cre_dir=tmp_path, ui_analysis={})

    result = action_handlers._handle_a11y_snapshot(ctx, {"app_name": "Safari"})

    assert result["status"] == "ok"
    assert result["interactive"] == 2
    payload = json.loads((tmp_path / Path(result["path"]).name).read_text(encoding="utf-8"))
    assert payload["labels"] == ["Email", "Password"]


def test_research_agent_uses_supplied_planner_action_hints(tmp_path: Path) -> None:
    captured_prompt: list[str] = []

    def fake_vlm(prompt: str, image_paths: list[str]) -> str:
        captured_prompt.append(prompt)
        return json.dumps({"mappings": []})

    agent = ResearchAgent(
        output_dir=tmp_path,
        planner_action_names=["click", "draw_path"],
    )
    agent._solve_equation(
        "Draw a tiger wearing armor.",
        {
            "steps": [
                {"step_id": "step_01", "description": "Outline the silhouette."},
            ],
        },
        [
            {
                "tool_name": "universal_action_space",
                "description": "Semantic actions",
                "interaction_mode": "semantic_actions",
            }
        ],
        vlm_fn=fake_vlm,
    )

    assert captured_prompt
    assert "  - click" in captured_prompt[0]
    assert "  - draw_path" in captured_prompt[0]
