from __future__ import annotations

import json

from agent_infra.research_agent import (
    MethodBrief,
    MethodReference,
    MethodStep,
    ResearchAgent,
    ResearchBrief,
    evaluate_phase2_method_gate,
)


def test_method_brief_round_trip_in_research_brief(tmp_path) -> None:
    brief = ResearchBrief(
        task_description="Draw a tiger in ornate armor.",
        method_brief=MethodBrief(
            subject_family="animal",
            task_family="drawing",
            steps=[
                MethodStep(
                    step_id="step_01",
                    description="Block in the tiger silhouette.",
                    objective="Establish the major masses.",
                    required_visual_outcome="The tiger reads clearly at a glance.",
                ),
                MethodStep(
                    step_id="step_02",
                    description="Add armor segmentation and key details.",
                    objective="Place the costume structure over the body plan.",
                    required_visual_outcome="The armor aligns with the tiger anatomy.",
                    depends_on_step_ids=["step_01"],
                ),
                MethodStep(
                    step_id="step_03",
                    description="Finish with final color and polish.",
                    objective="Make the subject recognizable and complete.",
                    required_visual_outcome="The result shows the requested subject/style cues.",
                    depends_on_step_ids=["step_01", "step_02"],
                ),
            ],
            pitfalls=["Do not crop the subject.", "Do not genericize the anatomy."],
            references=[
                MethodReference(
                    title="Tiger anatomy",
                    url="https://example.com/tiger",
                    source_tier="primary",
                    published_or_retrieved_date="2026-03-03",
                ),
                MethodReference(
                    title="Armor silhouettes",
                    url="https://example.com/armor",
                    source_tier="secondary",
                    published_or_retrieved_date="2026-03-03",
                ),
                MethodReference(
                    title="Color blocking guide",
                    url="https://example.com/color",
                    source_tier="secondary",
                    published_or_retrieved_date="2026-03-03",
                ),
            ],
            acceptance_clues=["Silhouette reads as tiger.", "Armor details remain aligned."],
            method_confidence=0.85,
        ),
    )

    path = tmp_path / "research_brief.json"
    brief.save(path)
    loaded = ResearchBrief.load(path)

    assert isinstance(loaded.method_brief, MethodBrief)
    assert loaded.method_brief.task_family == "drawing"
    assert len(loaded.method_brief.steps) == 3
    assert loaded.method_brief.steps[1].depends_on_step_ids == ["step_01"]
    assert loaded.method_brief.references[0].source_tier == "primary"


def test_study_method_builds_structured_method_brief() -> None:
    agent = ResearchAgent(output_dir="operator/cre/runs/test_phase2_structured")

    def fake_search(query: str) -> list[dict[str, str]]:
        return [
            {
                "title": f"{query} official guide",
                "url": "https://developer.example.com/guide",
                "snippet": "Avoid proportion mistakes and establish the silhouette first.",
            },
            {
                "title": f"{query} tutorial",
                "url": "https://example.com/tutorial",
                "snippet": "Use a major-shape pass before details.",
            },
            {
                "title": f"{query} notes",
                "url": "https://example.com/notes",
                "snippet": "Common mistake: missing clothing seams.",
            },
        ]

    def fake_vlm(prompt: str, image_paths: list[str]) -> str:
        assert "Break this down into an executable method" in prompt
        payload = {
            "steps": [
                {
                    "step_id": "step_01",
                    "description": "Establish the tiger silhouette and armor footprint.",
                    "objective": "Lock in the major masses before details.",
                    "required_visual_outcome": "The tiger and armor silhouette are legible.",
                    "common_failure_modes": ["cropped subject"],
                    "depends_on_step_ids": [],
                },
                {
                    "step_id": "step_02",
                    "description": "Add internal anatomy and suit segmentation.",
                    "objective": "Align armor structure with the tiger body.",
                    "required_visual_outcome": "Armor panels align with the anatomy.",
                    "common_failure_modes": ["floating armor detail"],
                    "depends_on_step_ids": ["step_01"],
                },
                {
                    "step_id": "step_03",
                    "description": "Finish with color, face detail, and final identity cues.",
                    "objective": "Make the result clearly tiger + Iron Man-inspired.",
                    "required_visual_outcome": "The subject reads clearly as the requested character concept.",
                    "common_failure_modes": ["generic styling"],
                    "depends_on_step_ids": ["step_01", "step_02"],
                },
            ],
            "pitfalls": [
                "Do not genericize the tiger anatomy.",
                "Do not add detail before the silhouette is stable.",
            ],
            "acceptance_clues": [
                "The silhouette reads clearly as a tiger.",
                "The armor styling is visible and coherent.",
            ],
        }
        return json.dumps(payload)

    method = agent._study_method(
        "Draw a tiger wearing ornate red-and-gold armor.",
        search_fn=fake_search,
        vlm_fn=fake_vlm,
    )

    assert isinstance(method, MethodBrief)
    assert method.task_family == "drawing"
    assert method.subject_family == "animal"
    assert len(method.steps) == 3
    assert all(isinstance(step, MethodStep) for step in method.steps)
    assert len(method.references) >= 3
    assert any(ref.source_tier == "primary" for ref in method.references)
    assert len(method.pitfalls) >= 2
    assert len(method.acceptance_clues) >= 2
    assert method.method_confidence > 0.0


def test_phase2_gate_passes_and_fails_with_explicit_reasons() -> None:
    passing = MethodBrief(
        subject_family="animal",
        task_family="drawing",
        steps=[
            MethodStep("step_01", "A"),
            MethodStep("step_02", "B"),
            MethodStep("step_03", "C"),
        ],
        pitfalls=["p1", "p2"],
        references=[
            MethodReference("r1", "https://developer.example.com/1", "primary"),
            MethodReference("r2", "https://example.com/2", "secondary"),
            MethodReference("r3", "https://example.com/3", "secondary"),
        ],
        acceptance_clues=["c1", "c2"],
        coverage_gaps=["No repo-local source available."],
        method_confidence=0.8,
    )
    passing_gate = evaluate_phase2_method_gate(passing)
    assert passing_gate["passed"] is True
    assert passing_gate["fail_reasons"] == []

    gap_tolerated = MethodBrief(
        subject_family="general",
        task_family="mixed",
        steps=[
            MethodStep("step_01", "A"),
            MethodStep("step_02", "B"),
            MethodStep("step_03", "C"),
        ],
        pitfalls=["p1", "p2"],
        references=[
            MethodReference("r1", "https://example.com/1", "secondary"),
            MethodReference("r2", "https://example.com/2", "secondary"),
            MethodReference("r3", "https://example.com/3", "secondary"),
        ],
        acceptance_clues=["c1", "c2"],
        coverage_gaps=[
            "Fewer than three method references were recovered.",
            "No primary/repo-local high-confidence method source was recovered.",
        ],
        method_confidence=0.7,
    )
    gap_gate = evaluate_phase2_method_gate(gap_tolerated)
    assert gap_gate["passed"] is True
    assert gap_gate["references_gap_explicit"] is True
    assert gap_gate["primary_gap_explicit"] is True

    failing = MethodBrief(
        subject_family="general",
        task_family="mixed",
        steps=[MethodStep("step_01", "Only one step")],
        pitfalls=["Only one pitfall"],
        references=[],
        acceptance_clues=["Only one clue"],
        method_confidence=0.1,
    )
    failing_gate = evaluate_phase2_method_gate(failing)
    assert failing_gate["passed"] is False
    assert "references_min_met" in failing_gate["fail_reasons"]
    assert "method_steps_min_met" in failing_gate["fail_reasons"]
    assert "pitfalls_min_met" in failing_gate["fail_reasons"]
    assert "acceptance_clues_min_met" in failing_gate["fail_reasons"]


def test_research_writes_method_brief_artifact(tmp_path) -> None:
    agent = ResearchAgent(output_dir=tmp_path)

    def fake_search(query: str) -> list[dict[str, str]]:
        return [
            {
                "title": f"{query} official guide",
                "url": "https://developer.example.com/guide",
                "snippet": "Avoid proportion mistakes and establish the silhouette first.",
            },
            {
                "title": f"{query} tutorial",
                "url": "https://example.com/tutorial",
                "snippet": "Use a major-shape pass before details.",
            },
            {
                "title": f"{query} notes",
                "url": "https://example.com/notes",
                "snippet": "Common mistake: missing clothing seams.",
            },
        ]

    def fake_vlm(prompt: str, image_paths: list[str]) -> str:
        if "Break this down into an executable method" in prompt:
            return json.dumps(
                {
                    "steps": [
                        {"step_id": "step_01", "description": "Block silhouette."},
                        {"step_id": "step_02", "description": "Add structure.", "depends_on_step_ids": ["step_01"]},
                        {"step_id": "step_03", "description": "Finish details.", "depends_on_step_ids": ["step_01", "step_02"]},
                    ],
                    "pitfalls": ["Avoid clipping.", "Avoid generic details."],
                    "acceptance_clues": ["Silhouette reads clearly.", "Requested details are present."],
                }
            )
        if "Output JSON:" in prompt:
            return json.dumps(
                {
                    "plan": [
                        {"step": "Block silhouette", "tool": "brush", "how": "Use a broad brush pass."},
                        {"step": "Add structure", "tool": "line", "how": "Add internal subdivisions."},
                        {"step": "Finish details", "tool": "detail_brush", "how": "Add facial/detail accents."},
                    ],
                    "quality_criteria": [
                        "The subject reads clearly as requested.",
                        "The result has visible secondary detail.",
                    ],
                }
            )
        raise AssertionError(f"Unexpected prompt: {prompt}")

    brief = agent.research(
        task="Draw a tiger wearing ornate armor.",
        site_url="https://jspaint.app/",
        search_fn=fake_search,
        vlm_fn=fake_vlm,
    )

    assert isinstance(brief.method_brief, MethodBrief)
    assert (tmp_path / "research_brief.json").exists()
    assert (tmp_path / "method_brief.json").exists()
    payload = json.loads((tmp_path / "method_brief.json").read_text(encoding="utf-8"))
    assert payload["task_family"] == "drawing"
    assert len(payload["steps"]) >= 3
