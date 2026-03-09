#!/usr/bin/env python3
"""Live Safari probe across five QA Practice pages.

This is a bounded capability probe for the current macOS/Safari stack. It
does not try to solve end-to-end tasks on each page. Instead, it exercises the
repo's core evidence surfaces on each page and leaves a normal traced run:

- HostToolHealth
- VisualMonitor
- Safari navigation / ready-state checks
- window_capture.capture_front_window
- A11yEngine
- VisualGroundingEngine
- TraceWriter / DiagnosticReader
- BenchmarkEvaluator

Usage:
    cd operator
    ./venv/bin/python cre/run_qa_practice_safari_probe.py
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from AppKit import NSApplicationActivateIgnoringOtherApps, NSWorkspace
except Exception:  # pragma: no cover - environment-specific
    NSApplicationActivateIgnoringOtherApps = None
    NSWorkspace = None

from a11y_engine import A11yElement, A11yEngine
from agent_infra.benchmark_evaluator import BenchmarkEvaluator, TaskClaim
from agent_infra.diagnostic_reader import DiagnosticReader
from agent_infra.host_tool_health import HostToolHealth
from agent_infra.trace_writer import TraceWriter
from agent_infra.visual_monitor import VisualMonitor
from visual_engine import VisualGroundingEngine
from window_capture import capture_front_window, get_frontmost_application_name


@dataclass(frozen=True)
class SiteTarget:
    name: str
    slug: str
    url: str


SITE_TARGETS: list[SiteTarget] = [
    SiteTarget("QA Practice Home", "home", "https://www.learnaqa.info/"),
    SiteTarget("QA Practice Dashboard", "dashboard", "https://www.learnaqa.info/dashboard"),
    SiteTarget("QA Practice Drag and Drop", "drag-and-drop", "https://www.learnaqa.info/drag-and-drop/"),
    SiteTarget("QA Practice iFrame Windows", "iframe-windows", "https://www.learnaqa.info/iframe-windows"),
    SiteTarget("QA Practice Shadow DOM", "shadow-dom", "https://www.learnaqa.info/shadow-dom/"),
]


def normalize_url_for_match(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path.rstrip("/")
    return f"{parsed.scheme}://{parsed.netloc}{path}"


def url_matches_target(current_url: str, target_url: str) -> bool:
    current = normalize_url_for_match(current_url)
    target = normalize_url_for_match(target_url)
    return current == target or current.startswith(f"{target}/")


def count_successful_site_actions(steps: list[dict[str, Any]], action_type: str) -> int:
    return len(
        {
            step.get("action", {}).get("parameters", {}).get("site_slug")
            for step in steps
            if step.get("action", {}).get("type") == action_type
            and step.get("action_result", {}).get("success")
            and step.get("action", {}).get("parameters", {}).get("site_slug")
        }
    )


def dom_expectation_satisfied(site_slug: str, probe: dict[str, Any]) -> bool:
    href = str(probe.get("href", ""))
    preview = str(probe.get("body_preview", ""))
    if site_slug == "home":
        return bool(probe.get("title")) and "learnaqa.info" in href
    if site_slug == "dashboard":
        return "dashboard" in href or "dashboard" in preview
    if site_slug == "drag-and-drop":
        return "drag" in preview or int(probe.get("draggable", 0)) > 0
    if site_slug == "iframe-windows":
        return int(probe.get("iframes", 0)) > 0 or "iframe" in preview or "window" in preview
    if site_slug == "shadow-dom":
        return int(probe.get("shadow_hosts", 0)) > 0 or "shadow" in preview
    return False


def summarize_a11y(elements: list[A11yElement], backend: str) -> dict[str, Any]:
    interactive = [element for element in elements if element.is_interactive]
    labels = [element.label for element in interactive if element.label][:15]
    roles = sorted({element.role for element in elements if element.role})
    return {
        "backend": backend,
        "total_elements": len(elements),
        "interactive_elements": len(interactive),
        "sample_labels": labels,
        "roles": roles[:20],
    }


def build_probe_summary(
    site_results: list[dict[str, Any]],
    health_payload: dict[str, Any],
    monitor_status: dict[str, Any],
) -> dict[str, Any]:
    passed_sites = sum(1 for site in site_results if site.get("all_steps_passed"))
    return {
        "site_count": len(site_results),
        "sites_passed": passed_sites,
        "sites_failed": len(site_results) - passed_sites,
        "all_sites_passed": passed_sites == len(site_results),
        "health_all_required_ready": bool(health_payload.get("all_required_ready")),
        "selected_health_tools": health_payload.get("selected", {}),
        "monitor_status": monitor_status,
        "site_results": site_results,
    }


def _save_json(path: Path, payload: dict[str, Any] | list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


def _run_osascript(script: str, *, timeout: int = 15) -> str:
    proc = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if proc.returncode != 0:
        stderr = proc.stderr.strip() or proc.stdout.strip() or "osascript failed"
        raise RuntimeError(stderr)
    return proc.stdout.strip()


def _safari_activate() -> None:
    _run_osascript('tell application "Safari" to activate')


def _ensure_safari_frontmost(timeout_seconds: float = 5.0) -> bool:
    if NSWorkspace is not None and NSApplicationActivateIgnoringOtherApps is not None:
        workspace = NSWorkspace.sharedWorkspace()
        for app in workspace.runningApplications():
            try:
                name = app.localizedName() or ""
                if "safari" in name.lower():
                    if app.activateWithOptions_(NSApplicationActivateIgnoringOtherApps):
                        break
            except Exception:
                continue

    _safari_activate()
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if get_frontmost_application_name() == "Safari":
            return True
        time.sleep(0.1)
    return get_frontmost_application_name() == "Safari"


def _safari_open_url(url: str) -> None:
    escaped_url = url.replace("\\", "\\\\").replace('"', '\\"')
    script = f'''
tell application "Safari"
    activate
    if (count of windows) = 0 then
        make new document with properties {{URL:"{escaped_url}"}}
    else
        set URL of current tab of front window to "{escaped_url}"
    end if
end tell
'''
    _run_osascript(script)


def _safari_current_tab_name() -> str:
    return _run_osascript('tell application "Safari" to return name of current tab of front window')


def _safari_current_tab_url() -> str:
    return _run_osascript('tell application "Safari" to return URL of current tab of front window')


def _safari_do_javascript(script: str) -> str:
    script_literal = json.dumps(script)
    applescript = f'''
tell application "Safari"
    return do JavaScript {script_literal} in current tab of front window
end tell
'''
    return _run_osascript(applescript)


def _wait_for_page_ready(site: SiteTarget, timeout_seconds: float = 20.0) -> dict[str, Any]:
    deadline = time.time() + timeout_seconds
    last_observation: dict[str, Any] = {}
    time.sleep(2.0)
    while time.time() < deadline:
        try:
            current_url = _safari_current_tab_url()
            current_title = _safari_current_tab_name()
            ready_state = _safari_do_javascript("document.readyState")
            last_observation = {
                "current_url": current_url,
                "current_title": current_title,
                "ready_state": ready_state,
            }
            if url_matches_target(current_url, site.url) and ready_state in {"interactive", "complete"}:
                last_observation["success"] = True
                return last_observation
        except Exception as exc:
            last_observation = {"success": False, "error": str(exc)}
        time.sleep(0.5)
    last_observation["success"] = False
    return last_observation


def _dom_probe() -> dict[str, Any]:
    script = """
(() => {
  const text = document.body && document.body.innerText ? document.body.innerText : "";
  const shadowHosts = Array.from(document.querySelectorAll("*")).filter((el) => el.shadowRoot).length;
  return JSON.stringify({
    title: document.title || "",
    href: location.href,
    ready_state: document.readyState,
    buttons: document.querySelectorAll("button").length,
    inputs: document.querySelectorAll("input, textarea, select").length,
    links: document.querySelectorAll("a").length,
    iframes: document.querySelectorAll("iframe").length,
    draggable: document.querySelectorAll('[draggable="true"]').length,
    shadow_hosts: shadowHosts,
    body_preview: text.slice(0, 600).toLowerCase()
  });
})()
"""
    raw = _safari_do_javascript(script)
    return json.loads(raw)


def _record_step(
    writer: TraceWriter,
    step_index: int,
    *,
    action_type: str,
    parameters: dict[str, Any],
    success: bool,
    post_state: dict[str, Any],
    thought: str = "",
) -> None:
    step = writer.begin_step(step_index)
    step.thought = thought
    step.pre_state = {"frontmost_app": get_frontmost_application_name()}
    step.action = {"type": action_type, "parameters": parameters}
    step.action_result = {"success": success, "status": "ok" if success else "error"}
    step.post_state = post_state
    writer.end_step(step)


def _register_probe_claims(evaluator: BenchmarkEvaluator, task_id: str) -> None:
    evaluator.register_custom_check(
        "check_navigated_all_sites",
        lambda manifest, steps: count_successful_site_actions(steps, "navigate_site") == len(SITE_TARGETS),
    )
    evaluator.register_custom_check(
        "check_captured_all_sites",
        lambda manifest, steps: count_successful_site_actions(steps, "capture_window") == len(SITE_TARGETS),
    )
    evaluator.register_custom_check(
        "check_a11y_all_sites",
        lambda manifest, steps: count_successful_site_actions(steps, "a11y_snapshot") == len(SITE_TARGETS),
    )
    evaluator.register_custom_check(
        "check_dom_probe_all_sites",
        lambda manifest, steps: count_successful_site_actions(steps, "dom_probe") == len(SITE_TARGETS),
    )
    evaluator.register_custom_check(
        "check_som_all_sites",
        lambda manifest, steps: count_successful_site_actions(steps, "som_overlay") == len(SITE_TARGETS),
    )
    evaluator.register_claims(
        task_id,
        [
            TaskClaim("Run completed successfully", "check_success"),
            TaskClaim("All recorded steps passed", "check_all_steps_passed"),
            TaskClaim("Navigated all five target sites", "check_navigated_all_sites"),
            TaskClaim("Captured all five target sites", "check_captured_all_sites"),
            TaskClaim("Extracted a11y from all five target sites", "check_a11y_all_sites"),
            TaskClaim("Completed DOM probe on all five target sites", "check_dom_probe_all_sites"),
            TaskClaim("Generated SoM overlay for all five target sites", "check_som_all_sites"),
        ],
    )
    evaluator.register_optimal_steps(task_id, 1 + (len(SITE_TARGETS) * 5))


def run_probe() -> int:
    cre_dir = Path(__file__).resolve().parent
    task_id = "QA_PRACTICE_SAFARI_5_SITE_PROBE"
    writer = TraceWriter(
        output_dir=cre_dir,
        task_id=task_id,
        task_description="Probe five QA Practice pages in Safari with the current core tooling stack.",
        agent_config={
            "probe": "qa_practice_safari_5_site",
            "browser": "Safari",
            "sites": [site.url for site in SITE_TARGETS],
        },
    )
    run_dir = writer.run_dir
    dom_dir = run_dir / "dom"
    a11y_dir = run_dir / "a11y"
    som_dir = run_dir / "som"
    monitor_dir = run_dir / "visual_monitor"
    diagnostics_path = run_dir / "diagnostic.txt"
    summary_path = run_dir / "site_probe_summary.json"
    benchmark_path = run_dir / "benchmark_result.json"
    health_path = run_dir / "health_payload.json"
    monitor_timeline_path = run_dir / "visual_monitor_timeline.json"

    dom_dir.mkdir(parents=True, exist_ok=True)
    a11y_dir.mkdir(parents=True, exist_ok=True)
    som_dir.mkdir(parents=True, exist_ok=True)

    print(f"[probe] Run dir: {run_dir}")

    checker = HostToolHealth()
    health_payload = checker.evaluate(has_url=True)
    _save_json(health_path, health_payload)

    step_index = 0
    first_failure_recorded = False
    had_failure = False

    def mark_failure(current_step_index: int, category: str, summary: str) -> None:
        nonlocal first_failure_recorded, had_failure
        had_failure = True
        if not first_failure_recorded:
            writer.record_failure(current_step_index, category, summary)
            first_failure_recorded = True

    _record_step(
        writer,
        step_index,
        action_type="host_tool_health",
        parameters={"has_url": True},
        success=bool(health_payload.get("all_required_ready")),
        post_state=checker.summary(health_payload),
        thought="Confirm the live macOS/Safari substrate is ready before touching the browser.",
    )
    if not health_payload.get("all_required_ready"):
        mark_failure(step_index, "environment_not_ready", "HostToolHealth reported missing required classes.")
        writer.finalize(outcome="failure")
        diagnostics_path.write_text(DiagnosticReader(run_dir).full_diagnostic(), encoding="utf-8")
        return 1
    step_index += 1

    monitor = VisualMonitor(
        interval_seconds=2.0,
        buffer_size=40,
        output_dir=monitor_dir,
        capture_frontmost_window=True,
    )
    monitor.start()

    a11y = A11yEngine()
    visual = VisualGroundingEngine(output_dir=str(som_dir))
    site_results: list[dict[str, Any]] = []

    try:
        for site in SITE_TARGETS:
            print(f"[probe] {site.name}: {site.url}")
            site_result: dict[str, Any] = {"name": site.name, "slug": site.slug, "url": site.url}
            site_params = {"site_slug": site.slug, "site_name": site.name, "url": site.url}

            try:
                focus_ok = _ensure_safari_frontmost()
                _safari_open_url(site.url)
                ready = _wait_for_page_ready(site)
                nav_success = bool(ready.get("success"))
                ready["success"] = nav_success
                site_result["navigation"] = ready
                _record_step(
                    writer,
                    step_index,
                    action_type="navigate_site",
                    parameters=site_params,
                    success=nav_success,
                    post_state={"focus_ok": focus_ok, **ready},
                    thought="Open the next QA Practice surface and wait for a usable ready-state.",
                )
                if not nav_success:
                    mark_failure(step_index, "navigation_failure", f"Navigation failed for {site.url}")
                step_index += 1
            except Exception as exc:
                site_result["navigation"] = {"success": False, "error": str(exc)}
                _record_step(
                    writer,
                    step_index,
                    action_type="navigate_site",
                    parameters=site_params,
                    success=False,
                    post_state=site_result["navigation"],
                    thought="Open the next QA Practice surface and wait for a usable ready-state.",
                )
                mark_failure(step_index, "navigation_failure", f"Navigation exception for {site.url}: {exc}")
                step_index += 1

            screenshot_path = writer.screenshots_dir / f"{site.slug}.png"
            try:
                capture_meta = capture_front_window(screenshot_path, owner_name="Safari")
                capture_meta["success"] = True
                site_result["capture"] = capture_meta
                _record_step(
                    writer,
                    step_index,
                    action_type="capture_window",
                    parameters={**site_params, "output_path": str(screenshot_path)},
                    success=True,
                    post_state=capture_meta,
                    thought="Capture the live Safari surface before any downstream interpretation.",
                )
                step_index += 1
            except Exception as exc:
                site_result["capture"] = {"success": False, "error": str(exc), "path": str(screenshot_path)}
                _record_step(
                    writer,
                    step_index,
                    action_type="capture_window",
                    parameters={**site_params, "output_path": str(screenshot_path)},
                    success=False,
                    post_state=site_result["capture"],
                    thought="Capture the live Safari surface before any downstream interpretation.",
                )
                mark_failure(step_index, "capture_failure", f"Window capture failed for {site.slug}: {exc}")
                step_index += 1

            try:
                elements = a11y.extract("Safari")
                a11y_summary = summarize_a11y(elements, a11y.backend)
                a11y_success = a11y_summary["total_elements"] > 0
                a11y_summary["success"] = a11y_success
                _save_json(a11y_dir / f"{site.slug}.json", a11y_summary)
                site_result["a11y"] = a11y_summary
                _record_step(
                    writer,
                    step_index,
                    action_type="a11y_snapshot",
                    parameters=site_params,
                    success=a11y_success,
                    post_state=a11y_summary,
                    thought="Extract the accessibility view of Safari so the probe measures hybrid perception, not only pixels.",
                )
                if not a11y_success:
                    mark_failure(step_index, "a11y_failure", f"A11y extraction returned no elements for {site.slug}.")
                step_index += 1
            except Exception as exc:
                site_result["a11y"] = {"backend": a11y.backend, "success": False, "error": str(exc)}
                _record_step(
                    writer,
                    step_index,
                    action_type="a11y_snapshot",
                    parameters=site_params,
                    success=False,
                    post_state=site_result["a11y"],
                    thought="Extract the accessibility view of Safari so the probe measures hybrid perception, not only pixels.",
                )
                mark_failure(step_index, "a11y_failure", f"A11y extraction failed for {site.slug}: {exc}")
                step_index += 1

            try:
                dom_probe = _dom_probe()
                dom_probe["expectation_satisfied"] = dom_expectation_satisfied(site.slug, dom_probe)
                dom_probe["success"] = bool(dom_probe["expectation_satisfied"])
                _save_json(dom_dir / f"{site.slug}.json", dom_probe)
                site_result["dom_probe"] = dom_probe
                _record_step(
                    writer,
                    step_index,
                    action_type="dom_probe",
                    parameters=site_params,
                    success=bool(dom_probe["expectation_satisfied"]),
                    post_state=dom_probe,
                    thought="Probe the page DOM so the run distinguishes navigation success from site-specific surface detection.",
                )
                if not dom_probe["expectation_satisfied"]:
                    mark_failure(step_index, "dom_probe_failure", f"DOM expectation failed for {site.slug}.")
                step_index += 1
            except Exception as exc:
                site_result["dom_probe"] = {"success": False, "error": str(exc)}
                _record_step(
                    writer,
                    step_index,
                    action_type="dom_probe",
                    parameters=site_params,
                    success=False,
                    post_state=site_result["dom_probe"],
                    thought="Probe the page DOM so the run distinguishes navigation success from site-specific surface detection.",
                )
                mark_failure(step_index, "dom_probe_failure", f"DOM probe failed for {site.slug}: {exc}")
                step_index += 1

            try:
                coordinate_map, overlay_path = visual.generate_som_overlay(
                    str(screenshot_path),
                    output_filename=f"{site.slug}_som.png",
                )
                som_state = {
                    "overlay_path": overlay_path,
                    "coordinate_count": len(coordinate_map),
                    "first_coordinates": dict(list(coordinate_map.items())[:5]),
                }
                som_state["success"] = len(coordinate_map) > 0
                site_result["som"] = som_state
                _record_step(
                    writer,
                    step_index,
                    action_type="som_overlay",
                    parameters=site_params,
                    success=len(coordinate_map) > 0,
                    post_state=som_state,
                    thought="Generate a SoM grid on the captured page so the probe exercises the current visual-grounding layer.",
                )
                if len(coordinate_map) == 0:
                    mark_failure(step_index, "som_failure", f"SoM overlay produced no coordinates for {site.slug}.")
                step_index += 1
            except Exception as exc:
                site_result["som"] = {"success": False, "error": str(exc)}
                _record_step(
                    writer,
                    step_index,
                    action_type="som_overlay",
                    parameters=site_params,
                    success=False,
                    post_state=site_result["som"],
                    thought="Generate a SoM grid on the captured page so the probe exercises the current visual-grounding layer.",
                )
                mark_failure(step_index, "som_failure", f"SoM overlay failed for {site.slug}: {exc}")
                step_index += 1

            site_result["all_steps_passed"] = all(
                bool(site_result.get(key, {}).get("success"))
                for key in ("navigation", "capture", "a11y", "dom_probe", "som")
            )
            site_results.append(site_result)
    finally:
        monitor.stop()

    monitor_status = monitor.get_status()
    _save_json(
        monitor_timeline_path,
        [snapshot.to_dict() for snapshot in monitor.timeline(last_n=monitor.snapshot_count)],
    )
    _save_json(summary_path, build_probe_summary(site_results, health_payload, monitor_status))

    manifest = writer.finalize(outcome="failure" if had_failure else "success")
    evaluator = BenchmarkEvaluator()
    _register_probe_claims(evaluator, task_id)
    result = evaluator.evaluate_run(run_dir)
    result.save(benchmark_path)

    diagnostic = DiagnosticReader(run_dir).full_diagnostic()
    diagnostics_path.write_text(diagnostic, encoding="utf-8")

    print(f"[probe] Outcome: {manifest['outcome']}")
    print(f"[probe] Benchmark claims score: {result.claims_score:.0%}")
    print(f"[probe] Summary: {summary_path}")
    print(f"[probe] Diagnostic: {diagnostics_path}")
    return 1 if had_failure else 0


def main() -> int:
    return run_probe()


if __name__ == "__main__":
    raise SystemExit(main())
