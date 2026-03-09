#!/usr/bin/env python3
"""Regression tests for Phase 3 tool inventory + equation solving."""

from __future__ import annotations

import json
from pathlib import Path

from action_space import UnifiedActionSpace
from agent_infra.research_agent import (
    EquationMapping,
    EquationSolution,
    MethodBrief,
    MethodReference,
    MethodStep,
    ResearchAgent,
    ResearchBrief,
    ToolInventoryEntry,
    evaluate_phase3_equation_gate,
)
from agent_infra.site_knowledge import SiteKnowledge, ToolAffordance


def _drawing_method_brief() -> MethodBrief:
    return MethodBrief(
        subject_family="animal",
        task_family="drawing",
        steps=[
            MethodStep(
                step_id="step_01",
                description="Establish the animal silhouette.",
                objective="Block in the major outer shape before details.",
                required_visual_outcome="The silhouette clearly reads as the requested animal.",
            ),
            MethodStep(
                step_id="step_02",
                description="Add internal anatomy and clothing structure.",
                objective="Place the internal landmarks before detail work.",
                required_visual_outcome="The major internal structure aligns with the silhouette.",
                depends_on_step_ids=["step_01"],
            ),
            MethodStep(
                step_id="step_03",
                description="Finish with detail, color, and verification passes.",
                objective="Add identity cues and finish the drawing.",
                required_visual_outcome="The result contains the requested identity and finish cues.",
                depends_on_step_ids=["step_01", "step_02"],
            ),
        ],
        pitfalls=[
            "Do not let the figure drift generic.",
            "Do not add detail before the main silhouette is correct.",
        ],
        references=[
            MethodReference(
                title="Animal reference",
                url="https://example.com/animal",
                source_tier="primary",
            ),
            MethodReference(
                title="Costume reference",
                url="https://example.com/costume",
                source_tier="secondary",
            ),
            MethodReference(
                title="Style reference",
                url="https://example.com/style",
                source_tier="secondary",
            ),
        ],
        acceptance_clues=[
            "The silhouette should be legible at a glance.",
            "Requested style cues must be visibly present.",
        ],
        method_confidence=0.82,
    )


def test_research_brief_round_trip_preserves_phase3_types(tmp_path: Path) -> None:
    brief = ResearchBrief(
        task_description="Draw a tiger in armor",
        method_brief=_drawing_method_brief(),
        tool_inventory=[
            ToolInventoryEntry(
                tool_name="browser_surface",
                interaction_mode="pointer+keyboard",
                source="hardcoded",
                confidence=0.7,
            )
        ],
        equation_solution=EquationSolution(
            mappings=[
                EquationMapping(
                    method_step_id="step_01",
                    tool_name="browser_surface",
                    action_type="draw_segments",
                    fallback_action_type="draw_path",
                )
            ],
            execution_plan=[{"step_index": 1, "action": "draw_segments"}],
            quality_criteria=["Requested structure is visible."],
            solution_confidence=0.76,
        ),
        execution_plan=[{"step_index": 1, "action": "draw_segments"}],
        quality_criteria=["Requested structure is visible."],
    )
    path = tmp_path / "research_brief.json"
    brief.save(path)

    loaded = ResearchBrief.load(path)

    assert isinstance(loaded.tool_inventory[0], ToolInventoryEntry)
    assert isinstance(loaded.equation_solution, EquationSolution)
    assert loaded.equation_solution.mappings[0].action_type == "draw_segments"


def test_study_tools_builds_typed_inventory_from_site_knowledge(tmp_path: Path) -> None:
    knowledge = SiteKnowledge(tmp_path / "site_knowledge.json")
    knowledge.site_name = "Example"
    knowledge.site_url = "https://example.com"
    knowledge.add_tool(
        ToolAffordance(
            tool_name="brush",
            shortcut="B",
            interaction_mode="draw",
            description="Primary brush tool",
            preconditions=["canvas visible"],
            postconditions=["active brush selected"],
            known_failures=["wrong layer selected"],
            success_count=2,
        )
    )

    agent = ResearchAgent(output_dir=tmp_path)
    inventory = agent._study_tools("https://example.com", knowledge, screenshot_fn=lambda _: None)

    assert inventory
    assert all(isinstance(entry, ToolInventoryEntry) for entry in inventory)
    assert any(entry.tool_name == "brush" for entry in inventory)
    assert any(entry.tool_name == "browser_surface" for entry in inventory)
    assert any(entry.tool_name == "universal_action_space" for entry in inventory)


def test_solve_equation_produces_covered_action_mappings(tmp_path: Path) -> None:
    agent = ResearchAgent(output_dir=tmp_path)
    solution = agent._solve_equation(
        "Draw a tiger wearing armor.",
        _drawing_method_brief(),
        [
            ToolInventoryEntry(
                tool_name="browser_surface",
                interaction_mode="pointer+keyboard",
                source="hardcoded",
                confidence=0.7,
            ),
            ToolInventoryEntry(
                tool_name="universal_action_space",
                interaction_mode="semantic_actions",
                source="hardcoded",
                confidence=0.9,
            ),
        ],
        vlm_fn=None,
    )

    gate = evaluate_phase3_equation_gate(solution, UnifiedActionSpace().list_planner_names())

    assert isinstance(solution, EquationSolution)
    assert len(solution.mappings) == 3
    assert gate["passed"] is True
    assert not solution.uncovered_method_steps
    assert all(mapping.fallback_action_type for mapping in solution.mappings)


def test_phase3_gate_rejects_invalid_actions() -> None:
    solution = EquationSolution(
        mappings=[
            EquationMapping(
                method_step_id="step_01",
                tool_name="browser_surface",
                action_type="not_a_real_action",
                fallback_action_type="draw_path",
            )
        ],
        solution_confidence=0.9,
    )

    gate = evaluate_phase3_equation_gate(solution, UnifiedActionSpace().list_planner_names())

    assert gate["passed"] is False
    assert "all_action_mappings_valid" in gate["fail_reasons"]


def test_research_agent_writes_phase3_artifacts(tmp_path: Path) -> None:
    knowledge = SiteKnowledge(tmp_path / "site_knowledge.json")
    knowledge.add_tool(
        ToolAffordance(
            tool_name="brush",
            shortcut="B",
            interaction_mode="draw",
            description="Primary brush tool",
        )
    )
    agent = ResearchAgent(output_dir=tmp_path)

    def fake_search(query: str, max_results: int = 5):
        lowered = query.lower()
        if "how to" in lowered or "technique" in lowered:
            return [
                {"title": "Method A", "url": "https://docs.example.com/method-a", "snippet": "Silhouette first."},
                {"title": "Method B", "url": "https://example.com/method-b", "snippet": "Add structure second."},
                {"title": "Method C", "url": "https://example.com/method-c", "snippet": "Finish with detail."},
            ]
        return [
            {"title": "Reference A", "url": "https://example.com/ref-a", "snippet": "Reference one."},
            {"title": "Reference B", "url": "https://example.com/ref-b", "snippet": "Reference two."},
        ]

    def fake_vlm(prompt: str, image_paths: list[str]) -> str:
        if "Break this down into an executable method" in prompt:
            return json.dumps(
                {
                    "steps": [
                        {
                            "step_id": "step_01",
                            "description": "Establish the silhouette.",
                            "objective": "Block in the outer shape.",
                            "required_visual_outcome": "The silhouette is visible.",
                        },
                        {
                            "step_id": "step_02",
                            "description": "Add structure.",
                            "objective": "Place internal landmarks.",
                            "required_visual_outcome": "Internal structure is visible.",
                            "depends_on_step_ids": ["step_01"],
                        },
                        {
                            "step_id": "step_03",
                            "description": "Finish with detail.",
                            "objective": "Add identity cues.",
                            "required_visual_outcome": "Requested detail cues are visible.",
                            "depends_on_step_ids": ["step_01", "step_02"],
                        },
                    ],
                    "pitfalls": ["Do not crop the subject.", "Do not add detail too early."],
                    "acceptance_clues": ["The silhouette reads clearly.", "Identity details are visible."],
                }
            )
        if "Solve the equation by mapping each method step" in prompt:
            return json.dumps(
                {
                    "mappings": [
                        {
                            "method_step_id": "step_01",
                            "tool_name": "universal_action_space",
                            "action_type": "draw_segments",
                            "action_parameters_hint": {"segments": "outline"},
                            "why_this_mapping": "Use structure-first guides.",
                            "fallback_tool_name": "universal_action_space",
                            "fallback_action_type": "draw_path",
                            "verification_hint": "Silhouette is visible.",
                        },
                        {
                            "method_step_id": "step_02",
                            "tool_name": "universal_action_space",
                            "action_type": "draw_segments",
                            "action_parameters_hint": {"segments": "structure"},
                            "why_this_mapping": "Add internal structure with guides.",
                            "fallback_tool_name": "universal_action_space",
                            "fallback_action_type": "draw_path",
                            "verification_hint": "Internal structure is visible.",
                        },
                        {
                            "method_step_id": "step_03",
                            "tool_name": "universal_action_space",
                            "action_type": "draw_path",
                            "action_parameters_hint": {"vertices": "detail strokes"},
                            "why_this_mapping": "Finish with freehand detail work.",
                            "fallback_tool_name": "universal_action_space",
                            "fallback_action_type": "draw_shape",
                            "verification_hint": "Identity details are visible.",
                        },
                    ],
                    "execution_plan": [
                        {
                            "step_index": 1,
                            "step_id": "step_01",
                            "description": "Establish the silhouette.",
                            "tool": "universal_action_space",
                            "action": "draw_segments",
                            "args_hint": {"segments": "outline"},
                            "verification_hint": "Silhouette is visible.",
                            "is_major": True,
                        }
                    ],
                    "quality_criteria": [
                        "The silhouette reads clearly.",
                        "Identity details are visible.",
                    ],
                }
            )
        return json.dumps({"plan": [], "quality_criteria": []})

    brief = agent.research(
        task="Draw a tiger wearing armor.",
        site_url="https://example.com/canvas",
        search_fn=fake_search,
        vlm_fn=fake_vlm,
        site_knowledge=knowledge,
    )

    assert brief.tool_inventory
    assert isinstance(brief.equation_solution, EquationSolution)
    assert (tmp_path / "tool_inventory.json").exists()
    assert (tmp_path / "equation_solution.json").exists()
    assert (tmp_path / "execution_plan.json").exists()
