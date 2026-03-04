from __future__ import annotations

import json
from pathlib import Path

from cursor_integration.mcp.research_server import ResearchServer


def _write_research_brief(root: Path, run_id: str, task_description: str) -> None:
    run_dir = root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "task_description": task_description,
        "reference_images": [],
        "method_brief": {
            "subject_family": "browser",
            "task_family": "research",
            "steps": [
                {
                    "step_id": "method-1",
                    "description": "Inspect the target UI.",
                    "objective": "Get the current state.",
                }
            ],
            "pitfalls": ["Do not assume the UI state."],
            "references": [
                {
                    "title": "Guide",
                    "url": "https://example.com/guide",
                    "source_tier": "primary",
                    "published_or_retrieved_date": "2026-03-04",
                    "relevance_note": "Shows the workflow.",
                }
            ],
            "acceptance_clues": ["UI evidence captured."],
            "method_confidence": 0.8,
            "coverage_gaps": [],
        },
        "tool_inventory": [
            {
                "tool_name": "integrated_browser",
                "interaction_mode": "click",
                "description": "Inspect the page with screenshots and DOM.",
            }
        ],
        "equation_solution": {
            "mappings": [
                {
                    "method_step_id": "method-1",
                    "tool_name": "integrated_browser",
                    "action_type": "screenshot",
                    "why_this_mapping": "The browser captures the current UI state.",
                    "verification_hint": "Check the screenshot and DOM.",
                }
            ],
            "uncovered_method_steps": [],
            "tool_gaps": [],
            "execution_plan": [
                {
                    "description": "Capture the current browser state.",
                    "tool": "integrated_browser",
                    "action": "screenshot",
                }
            ],
            "quality_criteria": ["Evidence is grounded in the current UI."],
            "solution_confidence": 0.8,
        },
        "execution_plan": [
            {
                "description": "Capture the current browser state.",
                "tool": "integrated_browser",
                "action": "screenshot",
            }
        ],
        "quality_criteria": ["Evidence is grounded in the current UI."],
        "research_duration_ms": 1200,
        "timestamp": "2026-03-04T00:00:00Z",
    }
    (run_dir / "research_brief.json").write_text(json.dumps(payload), encoding="utf-8")


def test_research_server_finds_briefs_and_maps_tools(tmp_path: Path) -> None:
    _write_research_brief(tmp_path, "run-alpha", "Use the browser to inspect a visual workflow.")
    _write_research_brief(tmp_path, "run-beta", "Research how to debug a browser automation regression.")
    server = ResearchServer(runs_root=tmp_path)

    brief = server.get_research_brief(run_id="run-alpha")
    assert brief["run_id"] == "run-alpha"
    assert "Execution Plan" in brief["plan_summary"]

    search = server.search_research_notes("browser regression", limit=3)
    assert search["matches"]
    assert search["matches"][0]["run_id"] == "run-beta"

    mapping = server.method_tool_map("debug browser workflow regression")
    assert mapping["matched_run_id"] == "run-beta"
    assert mapping["mappings"][0]["tool_name"] == "integrated_browser"
