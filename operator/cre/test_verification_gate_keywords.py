#!/usr/bin/env python3
"""VerificationGate regression tests for architectural drawing prompts."""

from agent_infra.verification_gate import VerificationGate


def test_verification_gate_decomposes_skyscraper_constraints() -> None:
    gate = VerificationGate(
        task_description=(
            "Draw a tall modern skyscraper in one-point perspective with exhaustive "
            "facade detail and profuse grayscale shading. Use clear line work and a "
            "finished architectural look."
        ),
        output_dir="/tmp/test_verification_gate_keywords",
    )

    descriptions = [constraint.description for constraint in gate.constraints]

    assert any("skyscraper" in description.lower() for description in descriptions)
    assert any("perspective" in description.lower() for description in descriptions)
    assert any("facade" in description.lower() for description in descriptions)
    assert any("shading" in description.lower() or "tonal" in description.lower() for description in descriptions)
    assert any("grayscale" in description.lower() for description in descriptions)
    assert any("vertical edges stay vertical" in description.lower() for description in descriptions)
    assert any("vanishing point" in description.lower() for description in descriptions)
    assert any("scatter-noise" in description.lower() for description in descriptions)


def test_verification_gate_does_not_require_multiple_colors_for_grayscale_task() -> None:
    gate = VerificationGate(
        task_description="Draw a grayscale skyscraper with shading and facade detail.",
        output_dir="/tmp/test_verification_gate_keywords_gray",
    )

    descriptions = [constraint.description for constraint in gate.constraints]
    assert "Multiple distinct colors used (not monochrome)" not in descriptions


def test_verification_gate_adds_extra_research_criteria() -> None:
    gate = VerificationGate(
        task_description="Draw a grayscale skyscraper with shading and facade detail.",
        output_dir="/tmp/test_verification_gate_keywords_extra",
        extra_criteria=[
            "The facade grid remains legible across the full height of the tower.",
            "The facade grid remains legible across the full height of the tower.",
        ],
    )

    descriptions = [constraint.description for constraint in gate.constraints]
    assert descriptions.count("The facade grid remains legible across the full height of the tower.") == 1
