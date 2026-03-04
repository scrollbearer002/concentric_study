#!/usr/bin/env python3
"""Regression tests for research-guided planning helpers."""

from agent import (
    _build_research_planner_block,
    _generate_fallback_plan,
    _normalize_research_quality_criteria,
    _plan_is_viable,
)
from agent_infra.research_agent import ResearchBrief


def test_research_planner_block_surfaces_method_plan_and_quality() -> None:
    brief = ResearchBrief(
        task_description="Draw a skyscraper",
        method_brief={
            "steps": [
                "Establish the horizon and vanishing point.",
                "Block in the front face before secondary detail.",
            ],
            "references": [
                {
                    "title": "Perspective Drawing Guide",
                    "url": "https://example.com/perspective",
                }
            ],
        },
        execution_plan=[
            {
                "description": "Lay in the major tower silhouette.",
                "tool": "brush",
            }
        ],
        quality_criteria=[
            "The tower reads clearly as a skyscraper, not an abstract shape.",
            "Shading creates at least three visible grayscale tones.",
        ],
    )

    block = _build_research_planner_block(brief)

    assert "Research-backed method steps" in block
    assert "Research-backed execution strategy" in block
    assert "Quality criteria the result must satisfy" in block
    assert "Perspective Drawing Guide" in block
    assert "three visible grayscale tones" in block


def test_research_quality_criteria_filter_respects_grayscale_goal() -> None:
    filtered = _normalize_research_quality_criteria(
        "Draw a grayscale skyscraper with shading.",
        [
            "Colors are appropriate and varied as requested",
            "Multiple grayscale tones are visible in the shading",
            "Multiple grayscale tones are visible in the shading",
        ],
    )

    assert "Colors are appropriate and varied as requested" not in filtered
    assert filtered == ["Multiple grayscale tones are visible in the shading"]


def test_observation_only_plan_is_not_viable_for_drawing_goal() -> None:
    plan = [
        {"action": "screenshot", "args": {}, "description": "Capture state"},
        {"action": "a11y_snapshot", "args": {}, "description": "Read a11y tree"},
        {"action": "assert_visual", "args": {"assertion": "Is the page loaded?"}, "description": "Verify page"},
    ]

    assert _plan_is_viable(plan, "Draw a skyscraper with exhaustive detail.") is False


def test_kleki_skyscraper_fallback_is_viable() -> None:
    plan = _generate_fallback_plan(
        "Draw a skyscraper with exhaustive facade detail and grayscale shading.",
        "https://kleki.com",
        720,
        450,
    )

    assert _plan_is_viable(plan, "Draw a skyscraper with exhaustive facade detail and grayscale shading.")
    assert any(step.get("action") == "kleki_clear_canvas" for step in plan)
    assert any(step.get("action") == "kleki_reset_render_state" for step in plan)
    assert any(step.get("action") == "draw_segments" for step in plan)
    assert any(step.get("action") == "visual_assert" for step in plan)
