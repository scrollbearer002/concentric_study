#!/usr/bin/env python3
"""Run PhD-level robot on BrowserBotics sandbox in Safari with full Live Safari stack.

Uses: mission_control evidence gate, Safari focus, bounds+inset for coordinates,
      paste from clipboard (robot code), then click Run. The robot does not appear
      until Play/Run is pressed after the code is in main.py; this script clicks
      Run automatically. Compliant with LIVE_SAFARI_STACK_CHECKLIST.md and live-safari-stack.mdc.

Usage:
  1. Optional: mission_control.py up live   (for observability)
  2. Run: ./venv/bin/python cre/run_browserbotics_safari_phd.py [--no-evidence]
  3. Script opens Safari to https://browserbotics.com/sandbox, passes evidence gate,
     pastes operator/cre/project_understanding/tools/browserbotics_phd_robot.py, clicks Run.

Research basis: See .cursor/plans/browserbotics-phd-robot-2026-03-07.md and
  browserbotics.com/docs/sandbox/overview, browserbotics.com/docs/getting-started/quickstart.
DOM/controls: BROWSERBOTICS_PHD_SITE_AND_ROBOT_BUILDER.md Part VI (sandbox refs e2=main.py, e4=Play, e9=editor);
  for screenshot confirmation, DOM-driven run (click by ref, fill e9) is preferred when available (see 05_mcp_verified_run.png).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
OPERATOR_DIR = REPO_ROOT / "operator"
if str(OPERATOR_DIR) not in sys.path:
    sys.path.insert(0, str(OPERATOR_DIR))

from Quartz import (
    CGEventCreateMouseEvent,
    CGEventPost,
    kCGEventLeftMouseDown,
    kCGEventLeftMouseUp,
    kCGHIDEventTap,
    kCGMouseButtonLeft,
)

VENV_PYTHON = OPERATOR_DIR / "venv" / "bin" / "python"
MISSION_CONTROL = (
    REPO_ROOT / "operator" / "cre" / "project_understanding" / "tools" / "mission_control.py"
)
ROBOT_CODE_PATH = (
    REPO_ROOT
    / "operator"
    / "cre"
    / "project_understanding"
    / "tools"
    / "browserbotics_phd_robot.py"
)
HUMANOID_CODE_PATH = (
    REPO_ROOT
    / "operator"
    / "cre"
    / "project_understanding"
    / "tools"
    / "browserbotics_phd_humanoid.py"
)
BROWSERBOTICS_SANDBOX_URL = "https://browserbotics.com/sandbox"
SCREENSHOTS_DIR = (
    REPO_ROOT / "operator" / "cre" / "project_understanding" / "artifacts" / "browserbotics_phd_screenshots"
)

# Content area: Safari toolbar + nav below window top. Tune if clicks miss.
SAFARI_CONTENT_INSET_TOP = 90
# Client coords (relative to viewport): main.py tab (left tab), code editor center, Run button. From sandbox layout.
# Run executes the active tab — paste and Run must be with main.py active; main.py is the left tab.
MAIN_PY_TAB_CLIENT = (90, 220)
EDITOR_CLIENT = (320, 300)
# Play (run) is the leftmost green triangle above the editor; avoid Stop (red square).
# Tuned for sandbox control bar: left-to-right order is Play, Stop, Settings, Help.
RUN_BUTTON_CLIENT = (80, 100)


def _run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, text=True, capture_output=True, check=check)


def _run_optional(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, text=True, capture_output=True, check=False)


def _get_safari_window_bounds() -> dict[str, float]:
    try:
        out = _run(["osascript", "-e", 'tell application "Safari" to get bounds of front window']).stdout.strip()
        parts = [int(p.strip()) for p in out.split(",")]
        if len(parts) != 4:
            return {"x": 0.0, "y": 31.0, "width": 1440.0, "height": 782.0}
        left, top, right, bottom = parts
        return {"x": float(left), "y": float(top), "width": float(right - left), "height": float(bottom - top)}
    except Exception:
        return {"x": 0.0, "y": 31.0, "width": 1440.0, "height": 782.0}


def _global_from_client(cx: float, cy: float, bounds: dict[str, float]) -> tuple[float, float]:
    gx = bounds["x"] + cx
    gy = bounds["y"] + SAFARI_CONTENT_INSET_TOP + cy
    return round(gx, 1), round(gy, 1)


def _click_global(gx: float, gy: float, double: bool = False) -> None:
    for _ in range(2 if double else 1):
        for event_type in (kCGEventLeftMouseDown, kCGEventLeftMouseUp):
            event = CGEventCreateMouseEvent(None, event_type, (gx, gy), kCGMouseButtonLeft)
            CGEventPost(kCGHIDEventTap, event)
            time.sleep(0.02)
        if double:
            time.sleep(0.05)


def _hide_cursor_and_activate_safari() -> None:
    _run_optional(
        [
            "osascript",
            "-e",
            'tell application "Cursor" to activate',
            "-e",
            'tell application "System Events" to keystroke "h" using command down',
            "-e",
            'tell application "Safari" to activate',
        ]
    )


def _ensure_safari_ready() -> dict[str, Any]:
    _hide_cursor_and_activate_safari()
    time.sleep(0.6)
    result = _run(
        [str(VENV_PYTHON), str(MISSION_CONTROL), "evidence", "Safari", "--require-frontmost", "--capture", "--json"]
    )
    payload = json.loads(result.stdout)
    if not payload.get("ready_for_visible_task"):
        blockers = payload.get("blockers") or ["Evidence gate failed."]
        raise RuntimeError("Safari evidence gate failed: " + " ".join(str(b) for b in blockers))
    return payload


def _open_safari_to_sandbox() -> None:
    _run_optional(["osascript", "-e", f'tell application "Safari" to open location "{BROWSERBOTICS_SANDBOX_URL}"'])
    time.sleep(1.0)
    _run_optional(["osascript", "-e", 'tell application "Safari" to activate'])
    time.sleep(5.0)  # Sandbox loads Python + physics ~5 s per docs


MINIMAL_QUICKSTART = '''import browserbotics as bb
import time
bb.addGroundPlane()
bb.createBody("box", halfExtent=[0.1, 0.1, 0.1], position=[0.15, 0.3, 0.1])
bb.createBody("sphere", radius=0.05, position=[0.15, 0.2, 0.2], color="blue")
robot = bb.loadURDF("viporX300.urdf", fixedBase=True)
for jpos in [[0,0,0,0,0,0], [0,-0.4,0.8,0,0.8,0], [0,0,0,0,0,0]]:
    for ji, jp in enumerate(jpos):
        bb.setJointMotorControl(robot, ji, targetPosition=jp)
    time.sleep(1)
'''


def _paste_robot_into_clipboard(short_run: bool = False, minimal: bool = False, humanoid: bool = False) -> None:
    if minimal:
        text = MINIMAL_QUICKSTART
    elif humanoid:
        if not HUMANOID_CODE_PATH.exists():
            raise FileNotFoundError(f"Humanoid code not found: {HUMANOID_CODE_PATH}")
        text = HUMANOID_CODE_PATH.read_text(encoding="utf-8")
    else:
        if not ROBOT_CODE_PATH.exists():
            raise FileNotFoundError(f"Robot code not found: {ROBOT_CODE_PATH}")
        text = ROBOT_CODE_PATH.read_text(encoding="utf-8")
        if short_run:
            text = text.replace("MAX_STEPS = 800", "MAX_STEPS = 150")
    proc = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE, text=True)
    proc.communicate(text)
    proc.wait(timeout=2)


def _capture_safari(step_name: str, manifest: list[dict[str, Any]]) -> None:
    """Capture Safari front window to SCREENSHOTS_DIR; append path and step to manifest."""
    from window_capture import capture_front_window

    _run_optional(["osascript", "-e", 'tell application "Safari" to activate'])
    time.sleep(0.5)
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    path = SCREENSHOTS_DIR / f"{step_name}.png"
    try:
        meta = capture_front_window(path, owner_name="Safari", fallback_to_fullscreen=False, include_cursor=True)
        manifest.append({
            "step": step_name,
            "path": str(path),
            "mode": meta.get("mode"),
            "bounds": meta.get("bounds"),
        })
    except Exception as e:
        manifest.append({"step": step_name, "path": None, "error": str(e)})


def _variance_and_checks(path: Path) -> tuple[float | None, dict[str, Any]]:
    """Compute variance and basic checks for one screenshot. Returns (variance, checks_dict)."""
    checks: dict[str, Any] = {}
    try:
        from PIL import Image
        img = Image.open(path).convert("L")
        w, h = img.size
        checks["width"], checks["height"] = w, h
        if w * h < 10_000:
            return None, checks
        pixels = list(img.getdata())
        mean_bright = sum(pixels) / len(pixels)
        checks["mean_brightness"] = round(mean_bright, 2)
        var = sum((x - mean_bright) ** 2 for x in pixels) / len(pixels)
        return var, checks
    except Exception as e:
        checks["image_error"] = str(e)
        return None, checks


def _run_verification(manifest: list[dict[str, Any]]) -> None:
    """PhD-style verification (Mitra/Huang-inspired): screenshot exists, non-empty (size + pixel).
    Part IX: multi-screenshot — if both 03 and 04 exist, pass when both have variance >= 1.0;
    otherwise 03 alone must pass. Writes verification_result.json."""
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    result_path = SCREENSHOTS_DIR / "verification_result.json"
    result: dict[str, Any] = {"passed": False, "reason": "", "checks": {}}
    path_03 = path_04 = None
    for m in manifest:
        if m.get("step") == "03_simulation_mid_run" and m.get("path"):
            path_03 = Path(m["path"])
        if m.get("step") == "04_simulation_after_run" and m.get("path"):
            path_04 = Path(m["path"])
    if not path_03 or not path_03.exists():
        result["reason"] = "no_screenshot_03"
        result_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print("Verification: FAIL (no 03_simulation_mid_run.png)")
        return
    size = path_03.stat().st_size
    result["checks"]["file_size_03"] = size
    if size < 50_000:
        result["reason"] = "screenshot_too_small"
        result_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print("Verification: FAIL (screenshot too small)")
        return
    var_03, c03 = _variance_and_checks(path_03)
    result["checks"].update({f"03_{k}": v for k, v in c03.items()})
    if var_03 is not None:
        result["checks"]["variance_03"] = round(var_03, 4)
    if var_03 is None or var_03 < 1.0:
        result["reason"] = "screenshot_blank_or_near_blank"
        result_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print("Verification: FAIL (image variance too low)")
        return
    var_04 = None
    if path_04 and path_04.exists():
        var_04, c04 = _variance_and_checks(path_04)
        result["checks"].update({f"04_{k}": v for k, v in c04.items()})
        if var_04 is not None:
            result["checks"]["variance_04"] = round(var_04, 4)
        if var_04 is not None and var_04 < 1.0:
            result["reason"] = "screenshot_04_blank_or_near_blank"
            result_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
            print("Verification: FAIL (04 variance too low)")
            return
    result["passed"] = True
    result["reason"] = "size_ok_and_non_empty"
    if var_04 is not None:
        result["reason"] = "size_ok_and_non_empty_multi_screenshot"
    result_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("Verification: PASS (PhD-verified run)")

def _keystroke(key: str, modifiers: list[str] | None = None) -> None:
    mod = modifiers or []
    # Use osascript for Cmd+A, Cmd+V
    app = "System Events"
    key_desc = key.lower()
    if "cmd" in mod:
        _run_optional(["osascript", "-e", f'tell application "{app}" to keystroke "{key_desc}" using command down'])
    else:
        _run_optional(["osascript", "-e", f'tell application "{app}" to keystroke "{key_desc}"'])
    time.sleep(0.25)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run PhD robot on BrowserBotics sandbox in Safari (full stack).")
    parser.add_argument(
        "--no-evidence",
        action="store_true",
        help="Skip evidence gate (not recommended for live tasks; use for fast reruns only).",
    )
    parser.add_argument("--no-open", action="store_true", help="Do not open Safari/sandbox URL; assume already open.")
    parser.add_argument(
        "--no-screenshots",
        action="store_true",
        help="Do not capture screenshots at each step (use for fast reruns).",
    )
    parser.add_argument(
        "--short-run",
        action="store_true",
        help="Use MAX_STEPS=150 so run finishes before capture; ensures 3D view shows robot+obstacle.",
    )
    parser.add_argument(
        "--minimal",
        action="store_true",
        help="Paste minimal quickstart (box + sphere + viporX300) to verify Play click and 3D render.",
    )
    parser.add_argument(
        "--humanoid",
        action="store_true",
        help="Paste dual-arm humanoid + mobile base script (browserbotics_phd_humanoid.py) instead of single-arm.",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="After run, run PhD-style verification on screenshot (size + variance check; see Autonomous Verification doc).",
    )
    args = parser.parse_args()

    manifest: list[dict[str, Any]] = []

    if not args.no_evidence:
        _ensure_safari_ready()
    else:
        _hide_cursor_and_activate_safari()
        time.sleep(0.5)

    if not args.no_open:
        _open_safari_to_sandbox()
        if not args.no_evidence:
            _ensure_safari_ready()
        if not args.no_screenshots:
            _capture_safari("01_sandbox_loaded", manifest)

    _paste_robot_into_clipboard(
        short_run=args.short_run,
        minimal=getattr(args, "minimal", False),
        humanoid=getattr(args, "humanoid", False),
    )
    bounds = _get_safari_window_bounds()

    # Ensure main.py is active (Run executes main.py only)
    gx_tab, gy_tab = _global_from_client(MAIN_PY_TAB_CLIENT[0], MAIN_PY_TAB_CLIENT[1], bounds)
    _click_global(gx_tab, gy_tab)
    time.sleep(0.4)

    # Click in code editor (select all then paste)
    gx_editor, gy_editor = _global_from_client(EDITOR_CLIENT[0], EDITOR_CLIENT[1], bounds)
    _click_global(gx_editor, gy_editor)
    time.sleep(0.4)
    _keystroke("a", ["cmd"])
    time.sleep(0.2)
    _keystroke("v", ["cmd"])
    time.sleep(0.6)
    if not args.no_screenshots:
        _capture_safari("02_editor_with_code", manifest)

    # Re-select main.py so Run definitely executes main.py (sandbox runs main.py on Play).
    _click_global(gx_tab, gy_tab)
    time.sleep(0.5)
    # Click Play (Run) button; ensure Safari and sandbox have focus.
    # DOM stability (MCP flow): when using DOM-driven automation, poll for Play (e4) enabled
    # before click; e4 is disabled while run is active. Safari harness uses pixel coords only.
    _run_optional(["osascript", "-e", "tell application \"Safari\" to activate"])
    time.sleep(0.3)
    gx_run, gy_run = _global_from_client(RUN_BUTTON_CLIENT[0], RUN_BUTTON_CLIENT[1], bounds)
    _click_global(gx_run, gy_run)
    if getattr(args, "minimal", False):
        print("Run clicked (minimal quickstart). Wait 10 s for run + 3D render then capture.")
        time.sleep(10)
        if not args.no_screenshots:
            _capture_safari("03_simulation_mid_run", manifest)
        if not args.no_screenshots:
            _capture_safari("04_simulation_after_run", manifest)
    elif getattr(args, "short_run", False):
        print("Run clicked (short run: MAX_STEPS=150). Wait for script to finish then capture.")
        time.sleep(8)
        if not args.no_screenshots:
            _capture_safari("03_simulation_mid_run", manifest)
        time.sleep(2)
        if not args.no_screenshots:
            _capture_safari("04_simulation_after_run", manifest)
    else:
        wait_s = 22 if getattr(args, "humanoid", False) else 12
        print(f"Run clicked. Simulation runs ~{wait_s} s. Check Safari.")
        time.sleep(wait_s)
        if not args.no_screenshots:
            _capture_safari("03_simulation_mid_run", manifest)
        time.sleep(6)
        if not args.no_screenshots:
            _capture_safari("04_simulation_after_run", manifest)

    if getattr(args, "verify", False) and not args.no_screenshots:
        _run_verification(manifest)

    if manifest:
        SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        manifest_path = SCREENSHOTS_DIR / "screenshots_manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        print("Screenshots:", [m.get("path") or m.get("error") for m in manifest])
        print("Manifest:", str(manifest_path))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
