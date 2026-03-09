from __future__ import annotations

from cre.run_qa_practice_safari_probe import (
    build_probe_summary,
    count_successful_site_actions,
    dom_expectation_satisfied,
    url_matches_target,
)


def test_url_matches_target_handles_trailing_slashes() -> None:
    assert url_matches_target("https://www.learnaqa.info/drag-and-drop", "https://www.learnaqa.info/drag-and-drop/")
    assert url_matches_target("https://www.learnaqa.info/iframe-windows/", "https://www.learnaqa.info/iframe-windows")
    assert not url_matches_target("https://www.learnaqa.info/shadow-dom", "https://www.learnaqa.info/dashboard")


def test_dom_expectation_satisfied_respects_site_specific_signals() -> None:
    assert dom_expectation_satisfied(
        "drag-and-drop",
        {"href": "https://www.learnaqa.info/drag-and-drop/", "body_preview": "drag the card to the target", "draggable": 0},
    )
    assert dom_expectation_satisfied(
        "iframe-windows",
        {"href": "https://www.learnaqa.info/iframe-windows", "body_preview": "", "iframes": 2},
    )
    assert dom_expectation_satisfied(
        "shadow-dom",
        {"href": "https://www.learnaqa.info/shadow-dom", "body_preview": "", "shadow_hosts": 1},
    )
    assert not dom_expectation_satisfied(
        "dashboard",
        {"href": "https://www.learnaqa.info/", "body_preview": "home page", "shadow_hosts": 0},
    )


def test_count_successful_site_actions_counts_distinct_sites() -> None:
    steps = [
        {"action": {"type": "navigate_site", "parameters": {"site_slug": "home"}}, "action_result": {"success": True}},
        {"action": {"type": "navigate_site", "parameters": {"site_slug": "home"}}, "action_result": {"success": True}},
        {"action": {"type": "navigate_site", "parameters": {"site_slug": "dashboard"}}, "action_result": {"success": True}},
        {"action": {"type": "navigate_site", "parameters": {"site_slug": "shadow-dom"}}, "action_result": {"success": False}},
    ]
    assert count_successful_site_actions(steps, "navigate_site") == 2


def test_build_probe_summary_rolls_up_site_pass_counts() -> None:
    summary = build_probe_summary(
        [
            {"slug": "home", "all_steps_passed": True},
            {"slug": "dashboard", "all_steps_passed": False},
        ],
        {"all_required_ready": True, "selected": {"browser_target": "safari"}},
        {"running": False, "total_captures": 7},
    )
    assert summary["site_count"] == 2
    assert summary["sites_passed"] == 1
    assert summary["sites_failed"] == 1
    assert not summary["all_sites_passed"]
