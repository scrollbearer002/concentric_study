#!/usr/bin/env python3
"""XBitLabs Mouse Accuracy Test — first test = Path Follow.

Open in Safari, click Path Follow, Easy, then green start; move along path.
Uses same Safari/viewport/Quartz pattern as mouse_accuracy_suite.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from Quartz import (
    CGEventCreateMouseEvent,
    CGEventPost,
    kCGEventLeftMouseDown,
    kCGEventLeftMouseUp,
    kCGEventMouseMoved,
    kCGHIDEventTap,
    kCGMouseButtonLeft,
)

REPO_ROOT = Path("/Users/christianpardo/Desktop/concentric_study")
VENV_PYTHON = REPO_ROOT / "operator" / "venv" / "bin" / "python"
MISSION_CONTROL = (
    REPO_ROOT / "operator" / "cre" / "project_understanding" / "tools" / "mission_control.py"
)
ARTIFACT_DIR = (
    REPO_ROOT / "operator" / "cre" / "project_understanding" / "artifacts" / "xbitlabs"
)
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

XBITLABS_URL = "https://www.xbitlabs.com/mouse-accuracy-test/"
SAFARI_CONTENT_INSET_TOP = 90

# Viewport coords from recon. Green start is at LEFT end of path (screenshot).
PATH_FOLLOW_TAB = (350, 192)
SHAPE_TRACE_TAB = (500, 192)  # fallback; live query can use cy~23 in some layouts
EASY_BTN = (1174, 629)
# Green start point: left end of the dashed line in the canvas (not center).
GREEN_START_VIEWPORT = (361, 541)
CANVAS_CENTER = (687, 542)
CANVAS_LEFT = 281
CANVAS_RIGHT = 1093
CANVAS_TOP = 237
CANVAS_BOTTOM = 846
CANVAS_W = 812
CANVAS_H = 609


def _run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, capture_output=True, check=True)


def _run_optional(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, capture_output=True, check=False)


def _osascript(script: str) -> str:
    return _run(["osascript", "-e", script]).stdout.strip()


def _do_js(js: str) -> str:
    escaped = json.dumps(js)
    return _osascript(
        f'tell application "Safari" to do JavaScript {escaped} in current tab of front window'
    )


def _get_safari_window_bounds() -> dict[str, float]:
    out = _run(
        ["osascript", "-e", 'tell application "Safari" to get bounds of front window']
    ).stdout.strip()
    parts = [int(p.strip()) for p in out.split(",")]
    if len(parts) != 4:
        return {"x": 0.0, "y": 31.0, "width": 1440.0, "height": 782.0}
    left, top, right, bottom = parts
    return {"x": float(left), "y": float(top), "width": float(right - left), "height": float(bottom - top)}


def _global_from_client(
    cx: float,
    cy: float,
    bounds: dict[str, float] | None = None,
    viewport_origin: tuple[float, float] | None = None,
) -> tuple[float, float]:
    if viewport_origin:
        sx, sy = viewport_origin
        return round(sx + cx, 1), round(sy + cy, 1)
    if bounds:
        gx = bounds["x"] + cx
        gy = bounds["y"] + SAFARI_CONTENT_INSET_TOP + cy
        return round(gx, 1), round(gy, 1)
    return round(cx, 1), round(cy + SAFARI_CONTENT_INSET_TOP, 1)


def _smooth_move(x: float, y: float, duration: float, steps: int) -> None:
    try:
        out = _run(["/opt/homebrew/bin/cliclick", "p"]).stdout.strip()
        sx, sy = map(float, out.split(","))
    except Exception:
        sx, sy = x, y
    for i in range(1, steps + 1):
        t = i / steps
        cx = sx + (x - sx) * t
        cy = sy + (y - sy) * t
        event = CGEventCreateMouseEvent(None, kCGEventMouseMoved, (cx, cy), kCGMouseButtonLeft)
        CGEventPost(kCGHIDEventTap, event)
        time.sleep(duration / steps)


def _click_here(x: float, y: float) -> None:
    for event_type in (kCGEventLeftMouseDown, kCGEventLeftMouseUp):
        event = CGEventCreateMouseEvent(None, event_type, (x, y), kCGMouseButtonLeft)
        CGEventPost(kCGHIDEventTap, event)
        time.sleep(0.006)


def _hide_cursor_app_and_activate_safari() -> None:
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


def _safari_evidence() -> dict[str, Any]:
    return json.loads(
        _run(
            [str(VENV_PYTHON), str(MISSION_CONTROL), "evidence", "Safari", "--require-frontmost", "--capture", "--json"]
        ).stdout
    )


def _ensure_safari_ready() -> dict[str, Any]:
    _hide_cursor_app_and_activate_safari()
    time.sleep(0.6)
    evidence = _safari_evidence()
    if not evidence.get("ready_for_visible_task"):
        raise RuntimeError(
            f"Safari not ready: {evidence.get('blockers', ['unknown'])}"
        )
    return evidence


def _query_xbitlabs_state() -> dict[str, Any]:
    js = r"""
(function(){
  var body = (document.body && document.body.innerText) ? document.body.innerText : '';
  var out = { bodyPreview: body.slice(0, 600) };
  var acc = body.match(/Accuracy\s*([\d.]+)%/);
  var dev = body.match(/Deviation\s*([\d.]+)px/);
  var prog = body.match(/Progress\s*(\d+)%/);
  var timeMatch = body.match(/Time\s*([\d.]+)s/);
  var rank = body.match(/Rank\s*(\w+)/);
  var stage = body.match(/Stage\s*(\d+)\s*\/\s*(\d+)/);
  out.accuracy = acc ? parseFloat(acc[1]) : null;
  out.deviation = dev ? parseFloat(dev[1]) : null;
  out.progress = prog ? parseInt(prog[1], 10) : null;
  out.time = timeMatch ? parseFloat(timeMatch[1]) : null;
  out.rank = rank ? rank[1] : null;
  out.stage = stage ? stage[1] + '/' + stage[2] : null;
  out.stageNum = stage ? parseInt(stage[1], 10) : null;
  out.stageTotal = stage ? parseInt(stage[2], 10) : null;
  var c = document.querySelector('canvas');
  if (c) { var r = c.getBoundingClientRect(); out.canvasRect = { cx: r.x + r.width/2, cy: r.y + r.height/2, w: r.width, h: r.height, left: r.left, top: r.top }; }
  out.screenX = (typeof window.screenX !== 'undefined') ? window.screenX : (window.screenLeft || 0);
  out.screenY = (typeof window.screenY !== 'undefined') ? window.screenY : (window.screenTop || 0);
  return JSON.stringify(out);
})();
"""
    return json.loads(_do_js(js))


@dataclass
class MotionProfile:
    name: str
    move_duration: float
    move_steps: int
    settle_sleep: float


class XBitLabsPathFollowHarness:
    """First test: Path Follow. Click start, move along path, maximize accuracy."""

    def __init__(self, artifact_prefix: str = "xbitlabs_path_follow") -> None:
        self.artifact_prefix = artifact_prefix
        self.log_path = ARTIFACT_DIR / f"{artifact_prefix}_log.json"
        self.log_path.write_text("[]")

    def log(self, event: str, **payload: Any) -> None:
        try:
            data = json.loads(self.log_path.read_text())
        except Exception:
            data = []
        data.append({"ts": time.time(), "event": event, **payload})
        self.log_path.write_text(json.dumps(data, indent=2))

    def run(
        self,
        profile: MotionProfile,
        *,
        skip_evidence: bool = False,
        content_inset: float | None = None,
        path_duration: float = 4.0,
        path_steps: int = 200,
    ) -> dict[str, Any]:
        if not skip_evidence:
            _run([str(VENV_PYTHON), str(MISSION_CONTROL), "up", "live", "--json"])
            evidence = _ensure_safari_ready()
            self.log("evidence", evidence=evidence)
        else:
            _hide_cursor_app_and_activate_safari()
            time.sleep(0.8)
            self.log("evidence", skipped=True)

        _osascript(f'tell application "Safari" to set URL of current tab of front window to "{XBITLABS_URL}"')
        time.sleep(2.5)
        self.log("navigated", url=XBITLABS_URL)

        state = _query_xbitlabs_state()
        vx, vy = state.get("screenX"), state.get("screenY")
        if vx is not None and vy is not None and (vx != 0 or vy != 0):
            viewport_origin = (float(vx), float(vy))
        else:
            b = _get_safari_window_bounds()
            inset = content_inset if content_inset is not None else SAFARI_CONTENT_INSET_TOP
            viewport_origin = (b["x"], b["y"] + inset)
        self.log("viewport_origin", viewport_origin=viewport_origin)

        # 1) Click Path Follow tab (first test)
        cx, cy = PATH_FOLLOW_TAB
        gx, gy = _global_from_client(cx, cy, viewport_origin=viewport_origin)
        _smooth_move(gx, gy, profile.move_duration, max(1, profile.move_steps))
        _click_here(gx, gy)
        time.sleep(0.4)

        # 2) Click Easy
        cx, cy = EASY_BTN
        gx, gy = _global_from_client(cx, cy, viewport_origin=viewport_origin)
        _smooth_move(gx, gy, profile.move_duration, max(1, profile.move_steps))
        _click_here(gx, gy)
        time.sleep(0.3)

        # 3) Click green start (left end of path). Retry with small offsets if not started.
        for attempt, (dx, dy) in enumerate([(0, 0), (25, 0), (-25, 0), (0, 15)]):
            cx = GREEN_START_VIEWPORT[0] + dx
            cy = GREEN_START_VIEWPORT[1] + dy
            gx, gy = _global_from_client(cx, cy, viewport_origin=viewport_origin)
            _smooth_move(gx, gy, profile.move_duration, max(1, profile.move_steps))
            _click_here(gx, gy)
            time.sleep(0.7)
            state = _query_xbitlabs_state()
            if (state.get("accuracy") or 0) > 0 or (state.get("time") or 0) > 0:
                self.log("start_registered", attempt=attempt, accuracy=state.get("accuracy"), time=state.get("time"))
                break
            self.log("start_retry", attempt=attempt)

        state = _query_xbitlabs_state()
        if state.get("progress") is not None and state.get("progress") > 0:
            self.log("started_after_click", progress=state.get("progress"))
        else:
            self.log("start_click_done", state=state)

        best_accuracy = float(state.get("accuracy") or 0.0)
        best_deviation = float(state.get("deviation") or 999.0)

        # 4) Move along path (left to right). Track best accuracy during run; UI resets after round.
        margin = 60
        x_start = CANVAS_LEFT + margin
        x_end = CANVAS_RIGHT - margin
        y_mid = (CANVAS_TOP + CANVAS_BOTTOM) / 2
        points: list[tuple[float, float]] = []
        for i in range(path_steps + 1):
            t = i / path_steps
            px = x_start + (x_end - x_start) * t
            py = y_mid
            points.append((px, py))
        for i, (px, py) in enumerate(points):
            gx, gy = _global_from_client(px, py, viewport_origin=viewport_origin)
            _smooth_move(gx, gy, path_duration / path_steps, 3)
            if i % 40 == 0 and i > 0:
                s = _query_xbitlabs_state()
                acc = s.get("accuracy")
                dev = s.get("deviation")
                if acc is not None:
                    best_accuracy = max(best_accuracy, float(acc))
                if dev is not None:
                    best_deviation = min(best_deviation, float(dev))
                self.log("path_progress", step=i, progress=s.get("progress"), accuracy=acc, deviation=dev)
                if s.get("progress") is not None and s.get("progress") >= 100:
                    break

        time.sleep(0.5)
        final = _query_xbitlabs_state()
        self.log("final_state", **{k: v for k, v in final.items() if k != "bodyPreview"})
        # Use best seen during run; final state may be reset for next stage.
        accuracy = max(best_accuracy, final.get("accuracy") or 0.0)
        deviation = min(best_deviation, final.get("deviation") or 999.0)
        progress = final.get("progress") or 0
        passed = accuracy >= 50.0 or progress >= 100  # Casual 50%+ or completed
        return {
            "status": "ok" if passed else "incomplete",
            "passed": passed,
            "accuracy": accuracy,
            "deviation": deviation,
            "progress": progress,
            "rank": final.get("rank"),
            "final_state": final,
            "log": str(self.log_path),
        }

    def run_all_stages(
        self,
        profile: MotionProfile,
        *,
        skip_evidence: bool = False,
        content_inset: float | None = None,
        path_duration: float = 5.0,
        path_steps: int = 250,
        max_stages: int = 5,
    ) -> dict[str, Any]:
        """Run Path Follow for all stages (1/5 through 5/5); adapt on the go."""
        if not skip_evidence:
            _run([str(VENV_PYTHON), str(MISSION_CONTROL), "up", "live", "--json"])
            evidence = _ensure_safari_ready()
            self.log("evidence", evidence=evidence)
        else:
            _hide_cursor_app_and_activate_safari()
            time.sleep(0.8)
            self.log("evidence", skipped=True)

        _osascript(f'tell application "Safari" to set URL of current tab of front window to "{XBITLABS_URL}"')
        time.sleep(2.5)
        self.log("navigated", url=XBITLABS_URL)

        state = _query_xbitlabs_state()
        if state.get("screenX") is not None and state.get("screenY") is not None and (state.get("screenX") != 0 or state.get("screenY") != 0):
            viewport_origin = (float(state["screenX"]), float(state["screenY"]))
        else:
            b = _get_safari_window_bounds()
            inset = content_inset if content_inset is not None else SAFARI_CONTENT_INSET_TOP
            viewport_origin = (b["x"], b["y"] + inset)
        self.log("viewport_origin", viewport_origin=viewport_origin)

        # Select Path Follow + Easy once
        for label, (cx, cy) in [("Path Follow", PATH_FOLLOW_TAB), ("Easy", EASY_BTN)]:
            gx, gy = _global_from_client(cx, cy, viewport_origin=viewport_origin)
            _smooth_move(gx, gy, profile.move_duration, max(1, profile.move_steps))
            _click_here(gx, gy)
            time.sleep(0.35)
        self.log("setup_done", tab="Path Follow", difficulty="Easy")

        stage_results: list[dict[str, Any]] = []
        stages_completed = 0
        overall_best_accuracy = 0.0
        overall_best_deviation = 999.0

        for stage_num in range(1, max_stages + 1):
            state = _query_xbitlabs_state()
            cr = state.get("canvasRect") or {}
            # Green start: left side of canvas (works in full screen)
            left = cr.get("left", CANVAS_LEFT)
            cx_start = left + 80
            cy_start = cr.get("cy", (CANVAS_TOP + CANVAS_BOTTOM) / 2)
            canvas_w = cr.get("w", CANVAS_W)
            canvas_h = cr.get("h", CANVAS_H)
            x_start_vp = left + 60
            x_end_vp = left + canvas_w - 60
            y_mid_vp = cr.get("top", CANVAS_TOP) + canvas_h / 2

            self.log("stage_start", stage=stage_num, green_start=(cx_start, cy_start))

            # Click green start (retry with small offsets)
            for attempt, (dx, dy) in enumerate([(0, 0), (20, 0), (-20, 0), (0, 10)]):
                gx, gy = _global_from_client(cx_start + dx, cy_start + dy, viewport_origin=viewport_origin)
                _smooth_move(gx, gy, profile.move_duration, max(1, profile.move_steps))
                _click_here(gx, gy)
                time.sleep(0.7)
                s = _query_xbitlabs_state()
                if (s.get("accuracy") or 0) > 0 or (s.get("time") or 0) > 0:
                    self.log("start_registered", stage=stage_num, attempt=attempt)
                    break
                self.log("start_retry", stage=stage_num, attempt=attempt)

            best_accuracy = float((_query_xbitlabs_state().get("accuracy")) or 0.0)
            best_deviation = float((_query_xbitlabs_state().get("deviation")) or 999.0)

            # Move along path (left to right)
            for i in range(path_steps + 1):
                t = i / path_steps if path_steps else 0
                px = x_start_vp + (x_end_vp - x_start_vp) * t
                py = y_mid_vp
                gx, gy = _global_from_client(px, py, viewport_origin=viewport_origin)
                _smooth_move(gx, gy, path_duration / max(1, path_steps), 3)
                if i > 0 and i % 50 == 0:
                    s = _query_xbitlabs_state()
                    if s.get("accuracy") is not None:
                        best_accuracy = max(best_accuracy, float(s["accuracy"]))
                    if s.get("deviation") is not None:
                        best_deviation = min(best_deviation, float(s["deviation"]))
                    self.log("path_progress", stage=stage_num, step=i, accuracy=s.get("accuracy"), deviation=s.get("deviation"))

            time.sleep(0.6)
            final = _query_xbitlabs_state()
            acc = max(best_accuracy, final.get("accuracy") or 0.0)
            dev = min(best_deviation, final.get("deviation") or 999.0)
            overall_best_accuracy = max(overall_best_accuracy, acc)
            overall_best_deviation = min(overall_best_deviation, dev)
            stage_results.append({
                "stage": stage_num,
                "accuracy": acc,
                "deviation": dev,
                "rank": final.get("rank"),
            })
            self.log("stage_done", stage=stage_num, accuracy=acc, deviation=dev, rank=final.get("rank"))

            # Brief pause before next level (game shows next path with green start)
            if stage_num < max_stages:
                time.sleep(1.2)

        passed = overall_best_accuracy >= 50.0
        return {
            "status": "ok" if passed else "incomplete",
            "passed": passed,
            "stages_completed": len(stage_results),
            "stage_results": stage_results,
            "accuracy": overall_best_accuracy,
            "deviation": overall_best_deviation,
            "log": str(self.log_path),
        }

    def run_shape_trace(
        self,
        profile: MotionProfile,
        *,
        skip_evidence: bool = False,
        content_inset: float | None = None,
        trace_duration: float = 8.0,
        trace_steps: int = 200,
        shape: str = "circle",
    ) -> dict[str, Any]:
        """Run Shape Trace test on current Safari tab (no navigate). Click tab, Easy, start; trace shape."""
        import math
        if not skip_evidence:
            _run([str(VENV_PYTHON), str(MISSION_CONTROL), "up", "live", "--json"])
            _ensure_safari_ready()
            self.log("evidence", source="mission_control + gui_evidence")
        else:
            _hide_cursor_app_and_activate_safari()
            time.sleep(0.6)
            self.log("evidence", skipped=True)
        state = _query_xbitlabs_state()
        if state.get("screenX") is not None and state.get("screenY") is not None and (state.get("screenX") != 0 or state.get("screenY") != 0):
            viewport_origin = (float(state["screenX"]), float(state["screenY"]))
        else:
            b = _get_safari_window_bounds()
            inset = content_inset if content_inset is not None else SAFARI_CONTENT_INSET_TOP
            viewport_origin = (b["x"], b["y"] + inset)
        self.log("shape_trace_viewport", viewport_origin=viewport_origin)

        # Get Shape Trace tab position (must be tab at top, not "Trace (0)" in achievements)
        tab_js = r'(function(){ var el = Array.from(document.querySelectorAll("button, [role=tab], a, div")).find(function(e){ var t=(e.innerText||e.textContent||"").trim(); var r=e.getBoundingClientRect(); return (t=== "Shape Trace" || (t.indexOf("Shape Trace")===0 && t.length<20)) && r.width>50 && r.top<150; }); if(el){ var r=el.getBoundingClientRect(); return JSON.stringify({cx: r.x+r.width/2, cy: r.y+r.height/2}); } return "{}"; })()'
        tab_out = _do_js(tab_js)
        try:
            tab_pos = json.loads(tab_out)
            if "cx" in tab_pos and "cy" in tab_pos:
                gx, gy = _global_from_client(tab_pos["cx"], tab_pos["cy"], viewport_origin=viewport_origin)
                _smooth_move(gx, gy, profile.move_duration, max(1, profile.move_steps))
                _click_here(gx, gy)
                self.log("shape_trace_tab_clicked", viewport=(tab_pos["cx"], tab_pos["cy"]))
        except Exception as e:
            self.log("shape_trace_tab_error", err=str(e))
        time.sleep(1.0)
        # Easy
        gx, gy = _global_from_client(EASY_BTN[0], EASY_BTN[1], viewport_origin=viewport_origin)
        _smooth_move(gx, gy, profile.move_duration, max(1, profile.move_steps))
        _click_here(gx, gy)
        time.sleep(0.5)

        state = _query_xbitlabs_state()
        cr = state.get("canvasRect") or {}
        left = cr.get("left", CANVAS_LEFT)
        top = cr.get("top", CANVAS_TOP)
        cw = cr.get("w", CANVAS_W)
        ch = cr.get("h", CANVAS_H)
        # Shape Trace: green start can be shape center or left; try center first then left
        center_x = left + cw / 2
        center_y = top + ch / 2
        radius = min(cw, ch) / 2.8
        start_candidates = [(center_x, center_y), (left + 80, center_y), (center_x - 80, center_y)]

        # Click green start (try center, then left, then offset)
        for attempt, (cx_start, cy_start) in enumerate(start_candidates):
            gx, gy = _global_from_client(cx_start, cy_start, viewport_origin=viewport_origin)
            _smooth_move(gx, gy, profile.move_duration, max(1, profile.move_steps))
            _click_here(gx, gy)
            time.sleep(0.8)
            s = _query_xbitlabs_state()
            if (s.get("accuracy") or 0) > 0 or (s.get("time") or 0) > 0:
                self.log("shape_trace_started", attempt=attempt)
                break
            self.log("shape_trace_start_retry", attempt=attempt)

        best_accuracy = float((_query_xbitlabs_state().get("accuracy")) or 0.0)
        best_deviation = float((_query_xbitlabs_state().get("deviation")) or 999.0)

        # Trace circle
        for i in range(trace_steps + 1):
            t = 2 * math.pi * i / trace_steps
            px = center_x + radius * math.cos(t)
            py = center_y + radius * math.sin(t)
            gx, gy = _global_from_client(px, py, viewport_origin=viewport_origin)
            _smooth_move(gx, gy, trace_duration / max(1, trace_steps), 4)
            if i > 0 and i % 40 == 0:
                s = _query_xbitlabs_state()
                if s.get("accuracy") is not None:
                    best_accuracy = max(best_accuracy, float(s["accuracy"]))
                if s.get("deviation") is not None:
                    best_deviation = min(best_deviation, float(s["deviation"]))
                self.log("shape_trace_progress", step=i, accuracy=s.get("accuracy"), deviation=s.get("deviation"))

        time.sleep(0.5)
        final = _query_xbitlabs_state()
        acc = max(best_accuracy, final.get("accuracy") or 0.0)
        dev = min(best_deviation, final.get("deviation") or 999.0)
        passed = acc >= 50.0
        self.log("shape_trace_done", accuracy=acc, deviation=dev, rank=final.get("rank"))
        return {
            "status": "ok" if passed else "incomplete",
            "passed": passed,
            "test": "shape_trace",
            "accuracy": acc,
            "deviation": dev,
            "rank": final.get("rank"),
            "log": str(self.log_path),
        }


def _safari_fullscreen() -> None:
    _run_optional(["osascript", "-e", 'tell application "Safari" to activate'])
    time.sleep(0.3)
    _run_optional([
        "osascript", "-e",
        'tell application "System Events" to tell process "Safari" to set value of attribute "AXFullScreen" of window 1 to true',
    ])
    time.sleep(0.5)


def main() -> None:
    parser = argparse.ArgumentParser(description="XBitLabs Path Follow (first test or all 5 stages)")
    parser.add_argument("--name", default="xbitlabs_path_follow")
    parser.add_argument("--move-duration", type=float, default=0.08)
    parser.add_argument("--move-steps", type=int, default=8)
    parser.add_argument("--settle-sleep", type=float, default=0.05)
    parser.add_argument("--path-duration", type=float, default=5.0)
    parser.add_argument("--path-steps", type=int, default=250)
    parser.add_argument("--skip-evidence", action="store_true")
    parser.add_argument("--content-inset", type=float, default=None)
    parser.add_argument("--all-stages", action="store_true", help="Run all 5 Path Follow stages in sequence")
    parser.add_argument("--fullscreen", action="store_true", help="Put Safari in full screen before run")
    parser.add_argument("--test", choices=["path_follow", "shape_trace"], default=None, help="Run this test on current tab (no navigate)")
    args = parser.parse_args()

    if args.fullscreen or args.all_stages:
        _safari_fullscreen()

    profile = MotionProfile(
        name=args.name,
        move_duration=args.move_duration,
        move_steps=args.move_steps,
        settle_sleep=args.settle_sleep,
    )
    harness = XBitLabsPathFollowHarness(args.name)

    if args.test == "shape_trace":
        result = harness.run_shape_trace(
            profile,
            skip_evidence=args.skip_evidence,
            content_inset=args.content_inset,
            trace_duration=8.0,
            trace_steps=250,
        )
    elif args.all_stages:
        result = harness.run_all_stages(
            profile,
            skip_evidence=args.skip_evidence,
            content_inset=args.content_inset,
            path_duration=args.path_duration,
            path_steps=args.path_steps,
            max_stages=5,
        )
    else:
        result = harness.run(
            profile,
            skip_evidence=args.skip_evidence,
            content_inset=args.content_inset,
            path_duration=args.path_duration,
            path_steps=args.path_steps,
        )
    print(json.dumps(result, indent=2))
    if not result.get("passed"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
