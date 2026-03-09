#!/usr/bin/env python3
"""GUI evidence protocol for live, user-visible macOS tasks.

This module exists to prevent the exact failure mode we saw in live testing:
command/app-model success being mistaken for visible on-screen success.

Research basis:
- SeeAct (2024): grounding remains a major challenge for real GUI agents.
- OSWorld (2024): real computer-use agents still fail frequently on
  operational knowledge + GUI grounding.
- Chain-of-Verification (2023): require explicit verification instead of
  trusting fluent continuation.
- Apple automation / accessibility model: Apple Events and System Events may
  be blocked by TCC permissions and must be treated as hard blockers.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[4]
OPERATOR_DIR = ROOT / "operator"
if str(OPERATOR_DIR) not in sys.path:
    sys.path.insert(0, str(OPERATOR_DIR))

from window_capture import capture_front_window, get_front_window_info, get_frontmost_application_name

ARTIFACTS_DIR = ROOT / "operator" / "cre" / "project_understanding" / "artifacts" / "control_room_generated" / "gui_evidence"


@dataclass(frozen=True)
class ScriptProbe:
    status: str
    stdout: str
    stderr: str
    returncode: int | None
    detail: str | None = None


def _run_osascript(script: str, *, timeout_seconds: float = 3.0) -> ScriptProbe:
    if not shutil.which("osascript"):
        return ScriptProbe(
            status="missing_osascript",
            stdout="",
            stderr="osascript is not installed on this machine.",
            returncode=None,
        )
    try:
        result = subprocess.run(
            ["osascript", "-"],
            input=script,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired:
        return ScriptProbe(
            status="timeout",
            stdout="",
            stderr="osascript timed out; possible TCC/Automation prompt or blocked GUI script.",
            returncode=None,
        )
    stdout = (result.stdout or "").strip()
    stderr = (result.stderr or "").strip()
    if result.returncode == 0:
        return ScriptProbe(status="ok", stdout=stdout, stderr=stderr, returncode=0)
    lowered = f"{stdout}\n{stderr}".lower()
    if "-1743" in lowered or "not authorized to send apple events" in lowered or "automation" in lowered:
        status = "automation_denied"
    elif "assistive access" in lowered or "not allowed assistive access" in lowered or "accessibility" in lowered:
        status = "accessibility_denied"
    elif "isn’t running" in lowered or "isn't running" in lowered:
        status = "not_running"
    elif "can’t get process" in lowered or "can't get process" in lowered or "invalid index" in lowered:
        status = "not_visible_or_not_running"
    else:
        status = "error"
    return ScriptProbe(status=status, stdout=stdout, stderr=stderr, returncode=result.returncode, detail=(stderr or stdout or None))


def _scriptable_window_probe(app_name: str) -> dict[str, Any]:
    script = f'''
tell application "{app_name}"
    if it is running then
        return (count of windows) as text
    else
        return "__NOT_RUNNING__"
    end if
end tell
'''
    probe = _run_osascript(script)
    payload: dict[str, Any] = {
        "status": probe.status,
        "stdout": probe.stdout,
        "stderr": probe.stderr,
        "returncode": probe.returncode,
        "ok": False,
        "running": False,
        "window_count": None,
    }
    if probe.status != "ok":
        return payload
    if probe.stdout == "__NOT_RUNNING__":
        payload["status"] = "not_running"
        return payload
    try:
        payload["window_count"] = int(float(probe.stdout))
    except (TypeError, ValueError):
        payload["status"] = "parse_error"
        return payload
    payload["running"] = True
    payload["ok"] = True
    return payload


def _system_events_window_probe(app_name: str) -> dict[str, Any]:
    script = f'''
tell application "System Events"
    if exists process "{app_name}" then
        tell process "{app_name}"
            return (count of windows) as text
        end tell
    else
        return "__NO_PROCESS__"
    end if
end tell
'''
    probe = _run_osascript(script)
    payload: dict[str, Any] = {
        "status": probe.status,
        "stdout": probe.stdout,
        "stderr": probe.stderr,
        "returncode": probe.returncode,
        "ok": False,
        "process_exists": False,
        "window_count": None,
    }
    if probe.status != "ok":
        return payload
    if probe.stdout == "__NO_PROCESS__":
        payload["status"] = "no_process"
        return payload
    try:
        payload["window_count"] = int(float(probe.stdout))
    except (TypeError, ValueError):
        payload["status"] = "parse_error"
        return payload
    payload["process_exists"] = True
    payload["ok"] = True
    return payload


def _system_events_frontmost_probe() -> dict[str, Any]:
    script = '''
tell application "System Events"
    return name of first application process whose frontmost is true
end tell
'''
    probe = _run_osascript(script)
    payload: dict[str, Any] = {
        "status": probe.status,
        "stdout": probe.stdout,
        "stderr": probe.stderr,
        "returncode": probe.returncode,
        "ok": probe.status == "ok" and bool(probe.stdout),
        "frontmost_app": probe.stdout or None,
    }
    return payload


def _window_capture_probe(app_name: str) -> dict[str, Any]:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix=f"{app_name.lower()}-", suffix=".png", dir=ARTIFACTS_DIR, delete=False) as handle:
        path = Path(handle.name)
    try:
        meta = capture_front_window(path, owner_name=app_name, fallback_to_fullscreen=False, include_cursor=True)
        return {
            "status": "ok",
            "ok": True,
            "path": str(path),
            "mode": meta.get("mode"),
            "owner_name": meta.get("owner_name"),
            "window_id": meta.get("window_id"),
            "bounds": meta.get("bounds"),
        }
    except Exception as exc:
        try:
            path.unlink(missing_ok=True)
        except Exception:
            pass
        return {
            "status": "capture_failed",
            "ok": False,
            "error": str(exc),
        }


def _evidence_level(*, capture_ok: bool, visible_ok: bool, logical_ok: bool, blockers: list[str]) -> str:
    if blockers:
        return "blocked"
    if capture_ok:
        return "screen_captured"
    if visible_ok:
        return "visible"
    if logical_ok:
        return "logical_only"
    return "none"


def app_gui_evidence(
    app_name: str = "Safari",
    *,
    require_frontmost: bool = False,
    capture: bool = False,
) -> dict[str, Any]:
    """Build a closed-loop evidence report for a visible GUI task."""
    frontmost_app = get_frontmost_application_name()
    frontmost_match = bool(frontmost_app and frontmost_app.lower() == app_name.lower())
    system_events_frontmost = _system_events_frontmost_probe()
    scriptable = _scriptable_window_probe(app_name)
    system_events = _system_events_window_probe(app_name)
    quartz_window = get_front_window_info(owner_name=app_name)
    capture_result = _window_capture_probe(app_name) if capture else {"status": "skipped", "ok": False}

    contradictions: list[str] = []
    blockers: list[str] = []

    scriptable_windows = scriptable.get("window_count") if isinstance(scriptable.get("window_count"), int) else 0
    ax_windows = system_events.get("window_count") if isinstance(system_events.get("window_count"), int) else 0

    if scriptable["status"] in {"automation_denied", "timeout"}:
        blockers.append(f"{app_name} Apple Events are blocked or awaiting approval ({scriptable['status']}).")
    if system_events["status"] in {"automation_denied", "accessibility_denied", "timeout"}:
        blockers.append(f"System Events GUI scripting for {app_name} is blocked or awaiting approval ({system_events['status']}).")
    if system_events_frontmost["status"] in {"automation_denied", "accessibility_denied", "timeout"}:
        blockers.append(
            f"System Events frontmost-app probe is blocked or awaiting approval ({system_events_frontmost['status']})."
        )
    if require_frontmost and not frontmost_match:
        blockers.append(f"{app_name} is not frontmost (frontmost app: {frontmost_app or 'unknown'}).")

    if scriptable_windows > 0 and quartz_window is None:
        contradictions.append(
            f"{app_name} reports {scriptable_windows} scriptable window(s), but Quartz does not report an eligible onscreen window."
        )
    if frontmost_match and quartz_window is None:
        contradictions.append(
            f"{app_name} is frontmost according to the visible-window probe, but Quartz does not report an eligible onscreen window."
        )
    if (
        system_events_frontmost.get("ok")
        and system_events_frontmost.get("frontmost_app")
        and frontmost_app
        and system_events_frontmost["frontmost_app"].lower() != frontmost_app.lower()
    ):
        contradictions.append(
            "Quartz and System Events disagree on the frontmost application "
            f"({frontmost_app!r} vs {system_events_frontmost['frontmost_app']!r})."
        )

    if contradictions:
        blockers.extend(contradictions)

    logical_ok = bool(scriptable.get("ok") and scriptable_windows > 0)
    visible_ok = bool(
        quartz_window is not None
        and (frontmost_match or not require_frontmost)
    )
    capture_ok = bool(capture_result.get("ok"))

    return {
        "target_app": app_name,
        "require_frontmost": require_frontmost,
        "frontmost_app": frontmost_app,
        "frontmost_match": frontmost_match,
        "checks": {
            "scriptable_windows": scriptable,
            "system_events_frontmost": system_events_frontmost,
            "system_events_windows": system_events,
            "quartz_front_window": {
                "ok": quartz_window is not None,
                "info": quartz_window,
            },
            "window_capture": capture_result,
        },
        "contradictions": contradictions,
        "blockers": blockers,
        "evidence_level": _evidence_level(
            capture_ok=capture_ok,
            visible_ok=visible_ok,
            logical_ok=logical_ok,
            blockers=blockers,
        ),
        "ready_for_visible_task": bool((capture_ok or visible_ok) and not blockers),
    }


def assert_ready_for_visible_task(
    app_name: str = "Safari",
    *,
    require_frontmost: bool = False,
    capture: bool = False,
) -> dict[str, Any]:
    """Return evidence payload or raise when a visible GUI task is not safe to claim."""
    payload = app_gui_evidence(
        app_name,
        require_frontmost=require_frontmost,
        capture=capture,
    )
    if not payload["ready_for_visible_task"]:
        blockers = payload.get("blockers") or ["GUI evidence gate did not pass."]
        raise RuntimeError(
            f"Visible-task evidence gate failed for {app_name}: " + " ".join(str(item) for item in blockers)
        )
    return payload


def protocol_runtime_payload() -> dict[str, Any]:
    """Environment-level readiness for the GUI evidence protocol itself."""
    return {
        "ok": bool(shutil.which("osascript")),
        "osascript": shutil.which("osascript"),
        "frontmost_probe_available": get_frontmost_application_name() is not None,
    }


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app", default="Safari")
    parser.add_argument("--require-frontmost", action="store_true")
    parser.add_argument("--capture", action="store_true")
    args = parser.parse_args(argv)
    print(
        json.dumps(
            app_gui_evidence(
                args.app,
                require_frontmost=args.require_frontmost,
                capture=args.capture,
            ),
            indent=2,
            sort_keys=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
