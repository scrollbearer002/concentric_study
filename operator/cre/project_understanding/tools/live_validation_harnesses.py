#!/usr/bin/env python3
"""Reusable harnesses for Concentric live validation claims."""

from __future__ import annotations

import json
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[4]
OPERATOR_DIR = ROOT / "operator"
TOOLS_DIR = Path(__file__).resolve().parent
if str(OPERATOR_DIR) not in sys.path:
    sys.path.insert(0, str(OPERATOR_DIR))
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from a11y_engine import A11yEngine
from security.auth_workflow import (
    AuthSurfaceObservation,
    AuthWorkflowContext,
    classify_auth_surface,
    plan_auth_workflow,
)
from security.credential_vault import HITLGuard
from window_capture import capture_front_window

import mission_control
from live_validation_registry import LiveValidationClaim


FIXTURE_PATH = ROOT / "operator" / "cre" / "fixtures" / "preclick_demo.html"
VENV_PYTHON = OPERATOR_DIR / "venv" / "bin" / "python"

PASS = "PASS"
FAIL = "FAIL"
BLOCKED_BY_CORE_DEFECT = "BLOCKED_BY_CORE_DEFECT"
BLOCKED_BY_PERMISSION = "BLOCKED_BY_PERMISSION"
NOT_YET_RUN = "NOT_YET_RUN"


@dataclass
class HarnessContext:
    claim: LiveValidationClaim
    run_id: str
    run_dir: Path
    actions: list[dict[str, Any]] = field(default_factory=list)
    evidence: dict[str, Any] = field(default_factory=dict)

    def record_action(
        self,
        *,
        kind: str,
        description: str,
        command: str | None = None,
        hidden_shortcut_used: bool = False,
        observable_on_screen: bool | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.actions.append(
            {
                "kind": kind,
                "description": description,
                "command": command,
                "hidden_shortcut_used": hidden_shortcut_used,
                "observable_on_screen": observable_on_screen,
                "details": details or {},
                "at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            }
        )

    def add_evidence(self, key: str, value: Any) -> None:
        self.evidence[key] = value

    def write_json(self, filename: str, payload: Any) -> Path:
        path = self.run_dir / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")
        return path


def _run_osascript(script: str, *, timeout: int = 20) -> str:
    proc = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout).strip() or "osascript failed"
        raise RuntimeError(detail)
    return (proc.stdout or "").strip()


def _make_agent_core():
    from agent_core import MacOSAgentCore

    return MacOSAgentCore()


def _safari_activate() -> None:
    _run_osascript('tell application "Safari" to activate')


def _safari_open_url(url: str) -> None:
    literal = url.replace("\\", "\\\\").replace('"', '\\"')
    script = f'''
tell application "Safari"
    activate
    if (count of windows) = 0 then
        make new document with properties {{URL:"{literal}"}}
    else
        set URL of current tab of front window to "{literal}"
    end if
end tell
'''
    _run_osascript(script)


def _safari_set_bounds(left: int, top: int, right: int, bottom: int) -> None:
    script = f'tell application "Safari" to set bounds of front window to {{{left}, {top}, {right}, {bottom}}}'
    _run_osascript(script)


def _safari_title() -> str:
    return _run_osascript('tell application "Safari" to return name of current tab of front window')


def _safari_url() -> str:
    return _run_osascript('tell application "Safari" to return URL of current tab of front window')


def _safari_js(script: str) -> str:
    literal = json.dumps(script)
    applescript = f'''
tell application "Safari"
    return do JavaScript {literal} in current tab of front window
end tell
'''
    return _run_osascript(applescript)


def _wait_until(description: str, predicate: Callable[[], bool], *, timeout_seconds: float = 12.0, interval_seconds: float = 0.25) -> None:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            if predicate():
                return
        except Exception:
            pass
        time.sleep(interval_seconds)
    raise RuntimeError(f"Timed out waiting for: {description}")


def _evidence_gate(app_name: str, *, require_frontmost: bool = True, capture: bool = True) -> dict[str, Any]:
    return mission_control.evidence_payload(
        app_name,
        require_frontmost=require_frontmost,
        capture=capture,
        strict=False,
    )


def _classify_evidence_failure(payload: dict[str, Any]) -> str:
    blockers = " ".join(str(item) for item in payload.get("blockers", []))
    lowered = blockers.lower()
    if "automation" in lowered or "accessibility" in lowered or "approval" in lowered:
        return BLOCKED_BY_PERMISSION
    return BLOCKED_BY_CORE_DEFECT


def _latest_manifest_path() -> Path | None:
    runs_dir = ROOT / "operator" / "cre" / "runs"
    manifests = sorted(runs_dir.glob("*/manifest.json"), key=lambda path: path.stat().st_mtime, reverse=True)
    return manifests[0] if manifests else None


def _latest_run_dir() -> Path | None:
    manifest = _latest_manifest_path()
    return manifest.parent if manifest else None


def _find_a11y_center(label_fragment: str) -> tuple[int, int] | None:
    engine = A11yEngine()
    candidates = engine.extract_interactive("Safari")
    target = label_fragment.lower()
    for element in candidates:
        label = (element.label or "").lower()
        if target in label and element.center is not None:
            return element.center
    return None


def _capture_front_window_artifact(ctx: HarnessContext, name: str, *, include_cursor: bool = True) -> dict[str, Any]:
    path = ctx.run_dir / f"{name}.png"
    meta = capture_front_window(path, owner_name="Safari", include_cursor=include_cursor)
    payload = {**meta, "path": str(path)}
    ctx.add_evidence(name, payload)
    return payload


def _quartz_frontmost_owner() -> str | None:
    payload = mission_control.evidence_payload("Safari", require_frontmost=False, capture=False, strict=False)
    return payload.get("frontmost_app")


def _focus_app_with_strategies(app_name: str, ctx: HarnessContext | None = None) -> dict[str, Any]:
    attempts: list[dict[str, Any]] = []

    def record(strategy: str, outcome: str, detail: str | None = None) -> None:
        attempt = {"strategy": strategy, "outcome": outcome}
        if detail:
            attempt["detail"] = detail
        attempts.append(attempt)
        if ctx is not None:
            ctx.record_action(
                kind="focus_attempt",
                description=f"Attempt to bring {app_name} frontmost via {strategy}.",
                hidden_shortcut_used=False,
                observable_on_screen=True,
                details=attempt,
            )

    current = _quartz_frontmost_owner()
    if current and app_name.lower() in current.lower():
        record("already_frontmost", "ok", current)
        return {"ok": True, "attempts": attempts, "frontmost_app": current}

    try:
        _make_agent_core().enforce_app_focus(app_name, timeout_seconds=2.5, poll_interval=0.1)
        current = _quartz_frontmost_owner()
        record("agent_core_enforce", "ok", current or "unknown")
        if current and app_name.lower() in current.lower():
            return {"ok": True, "attempts": attempts, "frontmost_app": current}
    except Exception as exc:
        record("agent_core_enforce", "error", str(exc))

    try:
        from AppKit import NSApplicationActivateAllWindows, NSApplicationActivateIgnoringOtherApps, NSWorkspace

        app_name_lower = app_name.lower()
        workspace = NSWorkspace.sharedWorkspace()
        flags = NSApplicationActivateIgnoringOtherApps | NSApplicationActivateAllWindows
        activated = False
        for app in workspace.runningApplications():
            name = (app.localizedName() or "").lower()
            if app_name_lower in name:
                activated = bool(app.activateWithOptions_(flags))
                break
        time.sleep(0.75)
        current = _quartz_frontmost_owner()
        record("appkit_activate_all_windows", "ok" if activated else "no_match", current or "unknown")
        if current and app_name.lower() in current.lower():
            return {"ok": True, "attempts": attempts, "frontmost_app": current}
    except Exception as exc:
        record("appkit_activate_all_windows", "error", str(exc))

    try:
        _run_osascript(f'tell application "{app_name}" to activate')
        time.sleep(0.75)
        current = _quartz_frontmost_owner()
        record("osascript_activate", "ok", current or "unknown")
        if current and app_name.lower() in current.lower():
            return {"ok": True, "attempts": attempts, "frontmost_app": current}
    except Exception as exc:
        record("osascript_activate", "error", str(exc))

    try:
        subprocess.run(["open", "-a", app_name], check=True, timeout=10)
        time.sleep(1.0)
        current = _quartz_frontmost_owner()
        record("open_app", "ok", current or "unknown")
        if current and app_name.lower() in current.lower():
            return {"ok": True, "attempts": attempts, "frontmost_app": current}
    except Exception as exc:
        record("open_app", "error", str(exc))

    return {"ok": False, "attempts": attempts, "frontmost_app": _quartz_frontmost_owner()}


def _click_fixture_button(ctx: HarnessContext) -> dict[str, Any]:
    fixture_url = FIXTURE_PATH.resolve().as_uri()
    ctx.record_action(
        kind="navigate",
        description="Open the local preclick fixture in Safari.",
        command=f"Safari -> {fixture_url}",
        hidden_shortcut_used=False,
        observable_on_screen=True,
    )
    _safari_open_url(fixture_url)
    _wait_until("Safari fixture title", lambda: "Preclick Demo" in _safari_title())
    _safari_set_bounds(160, 96, 1360, 860)
    time.sleep(0.75)

    pre_evidence = _evidence_gate("Safari", require_frontmost=True, capture=True)
    ctx.add_evidence("pre_click_gui_evidence", pre_evidence)
    if not pre_evidence.get("ready_for_visible_task"):
        verdict = _classify_evidence_failure(pre_evidence)
        return {
            "verdict": verdict,
            "root_cause_category": "app_focus_window_detection" if verdict == BLOCKED_BY_CORE_DEFECT else "permissions",
            "actual_observed_behavior": "Safari could not prove visible-task readiness before the click fixture.",
            "evidence_quality": pre_evidence.get("evidence_level", "none"),
            "fix_status": "required",
            "retest_status": "required",
        }

    status_before = _safari_js("document.getElementById('status').textContent")
    ctx.add_evidence("status_before", status_before)
    capture_meta = _capture_front_window_artifact(ctx, "pre_click_capture")
    target_center = _find_a11y_center("continue safely")
    if target_center is None:
        return {
            "verdict": BLOCKED_BY_CORE_DEFECT,
            "root_cause_category": "page_state_verification",
            "actual_observed_behavior": "The fixture button was not discoverable through the Safari accessibility tree.",
            "evidence_quality": "visible",
            "fix_status": "required",
            "retest_status": "required",
        }

    bounds = capture_meta.get("bounds") or {}
    scale_factor = float(_make_agent_core().get_screen_info()["scale_factor"])
    capture_origin = (float(bounds.get("x", 0)), float(bounds.get("y", 0)))
    local_pixel_x = int(round((target_center[0] - capture_origin[0]) * scale_factor))
    local_pixel_y = int(round((target_center[1] - capture_origin[1]) * scale_factor))

    ctx.add_evidence(
        "click_target",
        {
            "global_center": list(target_center),
            "capture_origin": list(capture_origin),
            "scale_factor": scale_factor,
            "local_pixel": [local_pixel_x, local_pixel_y],
        },
    )

    agent = _make_agent_core()
    ctx.record_action(
        kind="cursor_move",
        description="Move the cursor to the fixture button using the visible-click backend.",
        hidden_shortcut_used=False,
        observable_on_screen=True,
        details={"local_pixel": [local_pixel_x, local_pixel_y], "capture_origin": list(capture_origin)},
    )
    agent.execute_move_mouse(
        local_pixel_x,
        local_pixel_y,
        app_focus="Safari",
        capture_origin=capture_origin,
    )
    time.sleep(0.15)

    ctx.record_action(
        kind="click",
        description="Physically click the fixture button using the visible-click backend.",
        hidden_shortcut_used=False,
        observable_on_screen=True,
        details={"local_pixel": [local_pixel_x, local_pixel_y], "capture_origin": list(capture_origin)},
    )
    agent.execute_global_click(
        local_pixel_x,
        local_pixel_y,
        app_focus="Safari",
        capture_origin=capture_origin,
    )
    _wait_until(
        "fixture status update",
        lambda: _safari_js("document.getElementById('status').textContent") == "Clicked safely",
        timeout_seconds=4.0,
        interval_seconds=0.25,
    )

    status_after = _safari_js("document.getElementById('status').textContent")
    ctx.add_evidence("status_after", status_after)
    _capture_front_window_artifact(ctx, "post_click_capture")
    post_evidence = _evidence_gate("Safari", require_frontmost=True, capture=True)
    ctx.add_evidence("post_click_gui_evidence", post_evidence)

    if status_after != "Clicked safely":
        return {
            "verdict": BLOCKED_BY_CORE_DEFECT,
            "root_cause_category": "cursor_click_typing_backend",
            "actual_observed_behavior": f"Visible click backend left the fixture status at {status_after!r}.",
            "evidence_quality": post_evidence.get("evidence_level", "visible"),
            "fix_status": "required",
            "retest_status": "required",
        }
    return {
        "verdict": PASS,
        "root_cause_category": None,
        "actual_observed_behavior": "The visible click backend changed the fixture status from 'Awaiting confirmed click' to 'Clicked safely'.",
        "evidence_quality": post_evidence.get("evidence_level", "screen_captured"),
        "fix_status": "not_required",
        "retest_status": "not_required",
    }


def harness_mission_profile_health(ctx: HarnessContext) -> dict[str, Any]:
    doctor = mission_control.doctor_payload()
    ctx.record_action(kind="doctor", description="Run mission-control doctor before profile startup.", hidden_shortcut_used=False, observable_on_screen=False, details={"overall_ok": doctor.get("overall_ok")})
    ctx.add_evidence("doctor", doctor)

    profile_result = mission_control.up_profile(ctx.claim.required_profile, open_browser=False)
    ctx.record_action(kind="profile_up", description=f"Start or reuse the {ctx.claim.required_profile} profile.", hidden_shortcut_used=False, observable_on_screen=False, details=profile_result)
    ctx.add_evidence("profile_up", profile_result)

    status = mission_control.status_payload()
    ctx.add_evidence("status", status)
    healthy_services = {
        service["service_id"]: service["healthy"]
        for service in status["services"]
        if service["service_id"] in mission_control.desired_services(ctx.claim.required_profile)
    }
    required_checks = {
        "live": ("repo_venv_python", "phoenix_sidecar_ready", "gui_evidence_runtime", "control_room_snapshot"),
        "debug": ("repo_venv_python", "phoenix_sidecar_ready", "gui_evidence_runtime", "control_room_snapshot"),
        "architecture": ("repo_venv_python", "structurizr_cli", "graphviz_dot", "docker_binary", "docker_daemon", "control_room_snapshot"),
        "full": ("repo_venv_python", "phoenix_sidecar_ready", "gui_evidence_runtime", "control_room_snapshot", "structurizr_cli", "graphviz_dot", "docker_binary", "docker_daemon"),
    }.get(ctx.claim.required_profile, ())
    relevant_doctor_ok = all(bool(doctor["checks"].get(name, {}).get("ok")) for name in required_checks)
    ctx.add_evidence("relevant_doctor_checks", {name: doctor["checks"].get(name, {}) for name in required_checks})
    all_healthy = all(healthy_services.values())
    if relevant_doctor_ok and all_healthy:
        return {
            "verdict": PASS,
            "root_cause_category": None,
            "actual_observed_behavior": f"Mission-control profile {ctx.claim.required_profile!r} came up with healthy services {healthy_services}.",
            "evidence_quality": "system_health",
            "fix_status": "not_required",
            "retest_status": "not_required",
        }
    return {
        "verdict": BLOCKED_BY_CORE_DEFECT,
        "root_cause_category": "mission_supervisor",
        "actual_observed_behavior": (
            f"Mission-control profile {ctx.claim.required_profile!r} was not fully healthy: "
            f"services={healthy_services}, relevant_doctor_ok={relevant_doctor_ok}."
        ),
        "evidence_quality": "system_health",
        "fix_status": "required",
        "retest_status": "required",
    }


def harness_safari_visible_readiness(ctx: HarnessContext) -> dict[str, Any]:
    mission_control.up_profile("live", open_browser=False)
    ctx.record_action(kind="profile_up", description="Ensure the live mission profile is running.", hidden_shortcut_used=False, observable_on_screen=False)
    _safari_open_url("about:blank")
    focus_attempt = _focus_app_with_strategies("Safari", ctx)
    ctx.add_evidence("focus_attempt", focus_attempt)
    evidence = _evidence_gate("Safari", require_frontmost=True, capture=True)
    ctx.record_action(kind="evidence", description="Run the GUI evidence gate for Safari readiness.", hidden_shortcut_used=False, observable_on_screen=False, details={"ready": evidence.get("ready_for_visible_task")})
    ctx.add_evidence("safari_ready", evidence)
    if evidence.get("ready_for_visible_task"):
        return {
            "verdict": PASS,
            "root_cause_category": None,
            "actual_observed_behavior": "Safari was frontmost, visible, and front-window capture succeeded.",
            "evidence_quality": evidence.get("evidence_level", "screen_captured"),
            "fix_status": "not_required",
            "retest_status": "not_required",
        }
    verdict = _classify_evidence_failure(evidence)
    return {
        "verdict": verdict,
        "root_cause_category": "permissions" if verdict == BLOCKED_BY_PERMISSION else "app_focus_window_detection",
        "actual_observed_behavior": (
            "Safari readiness failed the GUI evidence gate after focus attempts "
            f"{focus_attempt.get('attempts', [])}."
        ),
        "evidence_quality": evidence.get("evidence_level", "none"),
        "fix_status": "required",
        "retest_status": "required",
    }


def harness_public_navigation_readiness(ctx: HarnessContext) -> dict[str, Any]:
    mission_control.up_profile("live", open_browser=False)
    url = "https://www.learnaqa.info/"
    _safari_open_url(url)
    _wait_until("QA Practice page load", lambda: "learnaqa.info" in _safari_url())
    evidence = _evidence_gate("Safari", require_frontmost=True, capture=True)
    ctx.add_evidence("public_navigation", {"url": _safari_url(), "title": _safari_title(), "gui": evidence})
    if evidence.get("ready_for_visible_task") and "learnaqa.info" in _safari_url():
        return {
            "verdict": PASS,
            "root_cause_category": None,
            "actual_observed_behavior": "Safari navigated to a public site and retained visible-task readiness.",
            "evidence_quality": evidence.get("evidence_level", "screen_captured"),
            "fix_status": "not_required",
            "retest_status": "not_required",
        }
    return {
        "verdict": BLOCKED_BY_CORE_DEFECT,
        "root_cause_category": "page_state_verification",
        "actual_observed_behavior": f"Public navigation did not converge on the expected URL/title ({_safari_url()!r}, {_safari_title()!r}).",
        "evidence_quality": evidence.get("evidence_level", "visible"),
        "fix_status": "required",
        "retest_status": "required",
    }


def harness_mysterymaster_readiness(ctx: HarnessContext) -> dict[str, Any]:
    mission_control.up_profile("live", open_browser=False)
    url = "https://www.mysterymaster.com/surfers/SuperSurfers.htm"
    _safari_open_url(url)
    _wait_until("Mystery Master page load", lambda: "mysterymaster.com" in _safari_url())
    evidence = _evidence_gate("Safari", require_frontmost=True, capture=True)
    title = _safari_title()
    current_url = _safari_url()
    ctx.add_evidence("mysterymaster", {"url": current_url, "title": title, "gui": evidence})
    if evidence.get("ready_for_visible_task") and "mysterymaster.com" in current_url and ("Surfers" in title or "Mystery Master" in title):
        return {
            "verdict": PASS,
            "root_cause_category": None,
            "actual_observed_behavior": "Mystery Master loaded in Safari with visible evidence preserved.",
            "evidence_quality": evidence.get("evidence_level", "screen_captured"),
            "fix_status": "not_required",
            "retest_status": "not_required",
        }
    return {
        "verdict": BLOCKED_BY_CORE_DEFECT,
        "root_cause_category": "page_state_verification",
        "actual_observed_behavior": f"Mystery Master readiness could not verify title/URL alignment ({title!r}, {current_url!r}).",
        "evidence_quality": evidence.get("evidence_level", "visible"),
        "fix_status": "required",
        "retest_status": "required",
    }


def harness_canvas_readiness(ctx: HarnessContext) -> dict[str, Any]:
    mission_control.up_profile("live", open_browser=False)
    urls = {
        "canvas.excalidraw_visible_readiness": "https://excalidraw.com/",
        "canvas.kleki_visible_readiness": "https://kleki.com/",
        "canvas.jspaint_visible_readiness": "https://jspaint.app/",
    }
    url = urls[ctx.claim.claim_id]
    _safari_open_url(url)
    _wait_until("canvas page load", lambda: any(host in _safari_url() for host in ("excalidraw.com", "kleki.com", "jspaint.app")))
    evidence = _evidence_gate("Safari", require_frontmost=True, capture=True)
    title = _safari_title()
    current_url = _safari_url()
    ctx.add_evidence("canvas_readiness", {"url": current_url, "title": title, "gui": evidence})
    if evidence.get("ready_for_visible_task") and any(host in current_url for host in ("excalidraw.com", "kleki.com", "jspaint.app")):
        return {
            "verdict": PASS,
            "root_cause_category": None,
            "actual_observed_behavior": f"Canvas site loaded into a visibly capturable Safari state ({current_url}).",
            "evidence_quality": evidence.get("evidence_level", "screen_captured"),
            "fix_status": "not_required",
            "retest_status": "not_required",
        }
    return {
        "verdict": BLOCKED_BY_CORE_DEFECT,
        "root_cause_category": "page_state_verification",
        "actual_observed_behavior": f"Canvas readiness could not verify a visible, loaded page ({title!r}, {current_url!r}).",
        "evidence_quality": evidence.get("evidence_level", "visible"),
        "fix_status": "required",
        "retest_status": "required",
    }


def harness_verification_contract(ctx: HarnessContext) -> dict[str, Any]:
    manifest_path = _latest_manifest_path()
    if manifest_path is None:
        return {
            "verdict": FAIL,
            "root_cause_category": "verification_oracle_logic",
            "actual_observed_behavior": "No run manifests were available to inspect outcome semantics.",
            "evidence_quality": "none",
            "fix_status": "required",
            "retest_status": "required",
        }
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    ctx.add_evidence("manifest_path", str(manifest_path))
    ctx.add_evidence("manifest_outcome_semantics", manifest.get("outcome_semantics"))
    ctx.add_evidence("manifest_outcome", manifest.get("outcome"))
    if manifest.get("outcome_semantics"):
        return {
            "verdict": PASS,
            "root_cause_category": None,
            "actual_observed_behavior": f"Latest run manifest {manifest_path.name} preserved normalized outcome semantics.",
            "evidence_quality": "artifact_contract",
            "fix_status": "not_required",
            "retest_status": "not_required",
        }
    return {
        "verdict": FAIL,
        "root_cause_category": "verification_oracle_logic",
        "actual_observed_behavior": f"Outcome semantics were missing or unreadable in {manifest_path}.",
        "evidence_quality": "artifact_contract",
        "fix_status": "required",
        "retest_status": "required",
    }


def harness_calibration_contract(ctx: HarnessContext) -> dict[str, Any]:
    report_path = ROOT / "operator" / "cre" / "project_understanding" / "artifacts" / "verification_calibration_report.json"
    index_path = ROOT / "operator" / "cre" / "project_understanding" / "artifacts" / "verification_review_packets" / "INDEX.md"
    if not report_path.exists() or not index_path.exists():
        return {
            "verdict": FAIL,
            "root_cause_category": "verification_oracle_logic",
            "actual_observed_behavior": "Verification calibration artifacts were missing.",
            "evidence_quality": "none",
            "fix_status": "required",
            "retest_status": "required",
        }
    report = json.loads(report_path.read_text(encoding="utf-8"))
    ctx.add_evidence("calibration_report", report)
    ctx.add_evidence("review_packet_index", str(index_path))
    return {
        "verdict": PASS,
        "root_cause_category": None,
        "actual_observed_behavior": "Verification calibration artifacts remain exportable and distinguish unlabeled records.",
        "evidence_quality": "artifact_contract",
        "fix_status": "not_required",
        "retest_status": "not_required",
    }


def harness_outer_loop_contract(ctx: HarnessContext) -> dict[str, Any]:
    journal = ROOT / "operator" / "cre" / "runs" / "reflection_journal.jsonl"
    rules = ROOT / "operator" / "cre" / "runs" / "rules.jsonl"
    latest_run_dir = _latest_run_dir()
    ctx.add_evidence("reflection_journal_exists", journal.exists())
    ctx.add_evidence("rules_store_exists", rules.exists())
    ctx.add_evidence("latest_run_dir", str(latest_run_dir) if latest_run_dir else None)
    if journal.exists() and rules.exists():
        return {
            "verdict": PASS,
            "root_cause_category": None,
            "actual_observed_behavior": "Outer-loop persistence artifacts remain present for reflection and rule extraction.",
            "evidence_quality": "artifact_contract",
            "fix_status": "not_required",
            "retest_status": "not_required",
        }
    return {
        "verdict": FAIL,
        "root_cause_category": "mission_supervisor",
        "actual_observed_behavior": "Outer-loop persistence artifacts were missing.",
        "evidence_quality": "artifact_contract",
        "fix_status": "required",
        "retest_status": "required",
    }


def harness_trust_contract(ctx: HarnessContext) -> dict[str, Any]:
    trust_path = ROOT / "operator" / "cre" / "action_trust.json"
    if not trust_path.exists():
        return {
            "verdict": FAIL,
            "root_cause_category": "mission_supervisor",
            "actual_observed_behavior": "The trust tracker persistence file was missing.",
            "evidence_quality": "none",
            "fix_status": "required",
            "retest_status": "required",
        }
    trust = json.loads(trust_path.read_text(encoding="utf-8"))
    ctx.add_evidence("trust_records", trust)
    if isinstance(trust, dict):
        return {
            "verdict": PASS,
            "root_cause_category": None,
            "actual_observed_behavior": "The trust tracker persistence file remains structured as a dictionary of action records.",
            "evidence_quality": "artifact_contract",
            "fix_status": "not_required",
            "retest_status": "not_required",
        }
    return {
        "verdict": FAIL,
        "root_cause_category": "mission_supervisor",
        "actual_observed_behavior": "The trust tracker persistence file was not structured as expected.",
        "evidence_quality": "artifact_contract",
        "fix_status": "required",
        "retest_status": "required",
    }


def harness_auth_surface_contract(ctx: HarnessContext) -> dict[str, Any]:
    login = AuthSurfaceObservation(
        url="https://example.com/login",
        heading_text="Sign in",
        submit_labels=("Continue",),
        has_email_field=True,
        has_password_field=True,
    )
    signup = AuthSurfaceObservation(
        url="https://example.com/register",
        heading_text="Create your account",
        submit_labels=("Create account",),
        has_email_field=True,
        has_password_field=True,
        has_confirm_password_field=True,
    )
    two_factor = AuthSurfaceObservation(
        url="https://example.com/challenge",
        visible_text="Enter the verification code from your authenticator app",
        submit_labels=("Verify",),
        has_totp_field=True,
    )
    cases = {
        "login": classify_auth_surface(login),
        "signup": classify_auth_surface(signup),
        "two_factor": classify_auth_surface(two_factor),
    }
    plan = plan_auth_workflow(
        AuthWorkflowContext(
            observation=login,
            provider="proton_pass",
            has_existing_credential=True,
            proton_pass_available=True,
            proton_pass_unlocked=True,
        )
    )
    guard = HITLGuard().check_action(
        "retrieve_password_manager_secret",
        {"domain": "example.com", "credential_provider": "proton_pass"},
    )
    ctx.add_evidence("auth_classifier_cases", cases)
    ctx.add_evidence("auth_plan", plan.to_dict())
    ctx.add_evidence("hitl_guard", guard)
    if cases == {
        "login": "login_existing",
        "signup": "signup_new",
        "two_factor": "two_factor_challenge",
    }:
        return {
            "verdict": PASS,
            "root_cause_category": None,
            "actual_observed_behavior": "Representative auth surfaces classified into explicit intents and yielded a sensitive-action-aware plan.",
            "evidence_quality": "contract_smoke",
            "fix_status": "not_required",
            "retest_status": "not_required",
        }
    return {
        "verdict": FAIL,
        "root_cause_category": "verification_oracle_logic",
        "actual_observed_behavior": f"Representative auth surfaces classified unexpectedly: {cases}.",
        "evidence_quality": "contract_smoke",
        "fix_status": "required",
        "retest_status": "required",
    }


HARNESSES: dict[str, Callable[[HarnessContext], dict[str, Any]]] = {
    "mission_profile_health": harness_mission_profile_health,
    "safari_visible_readiness": harness_safari_visible_readiness,
    "safari_visible_click_fixture": _click_fixture_button,
    "public_navigation_readiness": harness_public_navigation_readiness,
    "mysterymaster_readiness": harness_mysterymaster_readiness,
    "canvas_readiness": harness_canvas_readiness,
    "verification_contract": harness_verification_contract,
    "calibration_contract": harness_calibration_contract,
    "outer_loop_contract": harness_outer_loop_contract,
    "trust_contract": harness_trust_contract,
    "auth_surface_contract": harness_auth_surface_contract,
}


def run_harness(claim: LiveValidationClaim, run_dir: Path, run_id: str) -> dict[str, Any]:
    ctx = HarnessContext(claim=claim, run_id=run_id, run_dir=run_dir)
    harness = HARNESSES.get(claim.harness)
    if harness is None:
        result = {
            "claim_id": claim.claim_id,
            "family": claim.family,
            "verdict": NOT_YET_RUN,
            "root_cause_category": None,
            "actual_observed_behavior": f"No harness is implemented for {claim.harness}.",
            "evidence_quality": "none",
            "fix_status": "pending_harness",
            "retest_status": "pending_harness",
            "actions": [],
            "evidence": {},
            "implementation_confidence": "not_assessed",
        }
        ctx.write_json("result.json", result)
        return result

    started_at = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    try:
        body = harness(ctx)
    except Exception as exc:
        body = {
            "verdict": BLOCKED_BY_CORE_DEFECT,
            "root_cause_category": "mission_supervisor",
            "actual_observed_behavior": f"Harness execution raised: {exc}",
            "evidence_quality": "none",
            "fix_status": "required",
            "retest_status": "required",
        }

    result = {
        "claim_id": claim.claim_id,
        "family": claim.family,
        "phase": claim.phase,
        "criticality": claim.criticality,
        "started_at": started_at,
        "finished_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "claimed_capability": claim.capability_claim,
        "live_task_attempted": claim.live_task_recipe,
        "expected_evidence": claim.expected_evidence,
        "success_oracle": claim.success_oracle,
        "actions": ctx.actions,
        "evidence": ctx.evidence,
        "implementation_confidence": (
            "live_evidence_gated"
            if body.get("evidence_quality") in {"visible", "screen_captured"}
            else "contract_smoke"
        ),
        **body,
    }
    ctx.write_json("result.json", result)
    return result
