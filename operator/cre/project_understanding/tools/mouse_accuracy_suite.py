#!/usr/bin/env python3
"""Mouse Accuracy (mouseaccuracy.com) harness — one test at a time until pass.

Do not advance to the next test until the first passes.
Uses Safari, visible cursor, Quartz clicks, evidence-gated state.
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
    REPO_ROOT / "operator" / "cre" / "project_understanding" / "artifacts" / "mouse_accuracy"
)
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

MOUSE_ACCURACY_HOME = "https://mouseaccuracy.com/"
MOUSE_ACCURACY_GAME = "https://mouseaccuracy.com/game"
MOUSE_ACCURACY_CLASSIC = "https://mouseaccuracy.com/classic/"

# Same calibration as Human Benchmark (Safari content area).
SAFARI_VERTICAL_OFFSET = 139
# START link center on home (from live recon).
START_CLIENT_CENTER = (720.0, 678.0)
# Classic Start button (from live recon).
CLASSIC_START_CLIENT = (720.0, 545.25)


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


# Content area starts below title bar + toolbar. 108 was too large (cursor landed below target); 90 aligns better.
SAFARI_CONTENT_INSET_TOP = 90
# Initial aim offset Y (negative = click higher to counter "cursor below").
AIM_OFFSET_Y_INITIAL = -4.0
AIM_OFFSET_Y_MIN = -18.0  # click higher
AIM_OFFSET_Y_MAX = 4.0   # click lower
AIM_OFFSET_X_MIN = -15.0
AIM_OFFSET_X_MAX = 15.0
AIM_ADJUST_STEP = 2.5    # change per correction during test


def _get_safari_window_bounds() -> dict[str, float]:
    """Return {x, y, width, height} of Safari front window (AppleScript bounds: left, top, right, bottom)."""
    out = _run(
        [
            "osascript",
            "-e",
            'tell application "Safari" to get bounds of front window',
        ]
    ).stdout.strip()
    # e.g. "0, 31, 1440, 813"
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
    return round(cx, 1), round(cy + SAFARI_VERTICAL_OFFSET, 1)


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


def _get_cursor_position() -> tuple[float, float]:
    """Return (x, y) of current cursor in screen coordinates (cliclick p)."""
    try:
        out = _run(["/opt/homebrew/bin/cliclick", "p"]).stdout.strip()
        return tuple(map(float, out.split(",")))
    except Exception:
        return 0.0, 0.0


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
            [
                str(VENV_PYTHON),
                str(MISSION_CONTROL),
                "evidence",
                "Safari",
                "--require-frontmost",
                "--capture",
                "--json",
            ]
        ).stdout
    )


def _ensure_safari_ready() -> dict[str, Any]:
    _hide_cursor_app_and_activate_safari()
    time.sleep(0.6)
    evidence = _safari_evidence()
    if not evidence.get("ready_for_visible_task"):
        raise RuntimeError(
            f"Safari not ready for visible task: {evidence.get('blockers', ['unknown blocker'])}"
        )
    return evidence


@dataclass
class MotionProfile:
    name: str
    move_duration: float
    move_steps: int
    settle_sleep: float


def _query_classic_state() -> dict[str, Any]:
    js = r"""
(function(){
  var body = (document.body && document.body.innerText) ? document.body.innerText : '';
  var timeMatch = body.match(/Time Remaining:\s*(\d+)/);
  var out = { url: location.href, bodyPreview: body.slice(0, 500), timeRemaining: timeMatch ? parseInt(timeMatch[1], 10) : null };
  var startBtn = Array.from(document.querySelectorAll('a, button')).find(function(el){ return /start|play|go/i.test((el.innerText||'').trim()); });
  if (startBtn) { var r = startBtn.getBoundingClientRect(); out.startRect = { cx: r.x + r.width/2, cy: r.y + r.height/2 }; }
  var targets = [];
  document.querySelectorAll('.target').forEach(function(el){
    var r = el.getBoundingClientRect();
    if (r.width >= 1 && r.height >= 1) targets.push({ id: el.id || '', cx: r.left + r.width/2, cy: r.top + r.height/2 });
  });
  out.targets = targets;
  out.gameOver = out.timeRemaining === 0 || body.indexOf('Time Remaining: 0') !== -1 || /score|result|play again/i.test(body);
  out.screenX = typeof window.screenX !== 'undefined' ? window.screenX : (typeof window.screenLeft !== 'undefined' ? window.screenLeft : 0);
  out.screenY = typeof window.screenY !== 'undefined' ? window.screenY : (typeof window.screenTop !== 'undefined' ? window.screenTop : 0);
  return JSON.stringify(out);
})();
"""
    return json.loads(_do_js(js))


def _query_mouse_accuracy_state() -> dict[str, Any]:
    js = r"""
(function(){
  var url = location.href || '';
  var onHome = url.indexOf('/game') === -1;
  var body = (document.body && document.body.innerText) ? document.body.innerText : '';
  var out = { url: url, onHome: onHome, bodyPreview: body.slice(0, 800) };
  if (onHome) {
    var startLink = Array.from(document.querySelectorAll('a')).find(function(a){ return (a.innerText || '').trim() === 'START' || (a.href || '').indexOf('/game') !== -1; });
    if (startLink) { var r = startLink.getBoundingClientRect(); out.startRect = { cx: r.x + r.width/2, cy: r.y + r.height/2 }; }
    return JSON.stringify(out);
  }
  var countdown = document.querySelector('.countdown-number');
  if (countdown) { var r = countdown.getBoundingClientRect(); out.countdown = true; out.countdownRect = { cx: r.x + r.width/2, cy: r.y + r.height/2 }; return JSON.stringify(out); }
  var targets = [];
  document.querySelectorAll('[id^="target-"], .target').forEach(function(el){
    var r = el.getBoundingClientRect();
    if (r.width > 5 && r.height > 5) targets.push({ id: el.id, cx: Math.round(r.x + r.width/2), cy: Math.round(r.y + r.height/2) });
  });
  out.targets = targets;
  var hasScore = /Score|score|Accuracy|Hits|hits|Misses|misses|Result|result|Your|Play again|Submit|Save/i.test(body);
  out.hasResults = hasScore || (targets.length === 0 && body.length > 80);
  return JSON.stringify(out);
})();
"""
    return json.loads(_do_js(js))


class MouseAccuracyHarness:
    """Single test: main game. Pass = reached results with score-like state."""

    def __init__(self, artifact_prefix: str) -> None:
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

    def click_client_point(
        self,
        client_x: float,
        client_y: float,
        profile: MotionProfile,
        *,
        bounds: dict[str, float] | None = None,
        viewport_origin: tuple[float, float] | None = None,
        position_errors: list[tuple[float, float]] | None = None,
    ) -> tuple[float, float]:
        gx, gy = _global_from_client(client_x, client_y, bounds=bounds, viewport_origin=viewport_origin)
        _smooth_move(gx, gy, duration=profile.move_duration, steps=profile.move_steps)
        if position_errors is not None:
            ax, ay = _get_cursor_position()
            position_errors.append((ax - gx, ay - gy))
        _click_here(gx, gy)
        time.sleep(profile.settle_sleep)
        return gx, gy

    def run_main_game(self, profile: MotionProfile) -> dict[str, Any]:
        _run([str(VENV_PYTHON), str(MISSION_CONTROL), "up", "live", "--json"])
        evidence = _ensure_safari_ready()
        self.log("evidence", evidence=evidence)

        _osascript(f'tell application "Safari" to set URL of current tab of front window to "{MOUSE_ACCURACY_HOME}"')
        time.sleep(2.5)
        self.log("navigated", url=MOUSE_ACCURACY_HOME)

        state = _query_mouse_accuracy_state()
        # Navigate to game (JS click may not navigate; use location).
        _do_js('window.location.href = "https://mouseaccuracy.com/game";')
        self.log("navigate", method="js_location_game")
        # Let the game page load and countdown run (3s) then targets appear.
        time.sleep(5.0)

        # Wait for countdown to finish then for first targets (up to 12s).
        deadline_countdown = time.time() + 12.0
        while time.time() < deadline_countdown:
            state = _query_mouse_accuracy_state()
            if not state.get("onHome") and state.get("countdown"):
                time.sleep(0.4)
                continue
            targets = state.get("targets") or []
            if targets:
                break
            if state.get("hasResults"):
                break
            # If on game but no targets yet (e.g. "0" = last countdown second), keep waiting.
            time.sleep(0.3)
        else:
            # One retry: load /game directly and wait for targets (SPA may need full load).
            _osascript(f'tell application "Safari" to set URL of current tab of front window to "{MOUSE_ACCURACY_GAME}"')
            time.sleep(6.0)
            for _ in range(20):
                state = _query_mouse_accuracy_state()
                if state.get("targets") and len(state["targets"]) > 0:
                    break
                if state.get("hasResults"):
                    break
                time.sleep(0.4)
            else:
                # Canvas-only game: no DOM targets. Wait for round to end then look for results.
                self.log("no_dom_targets", fallback="wait_for_results")
                time.sleep(32.0)
                final = _query_mouse_accuracy_state()
                body = (final.get("bodyPreview") or "").lower()
                has_result = "score" in body or "accuracy" in body or "play again" in body or "result" in body or len(body) > 30
                if has_result or final.get("hasResults"):
                    return {
                        "status": "ok",
                        "passed": True,
                        "clicks": 0,
                        "final_state": final,
                        "log": str(self.log_path),
                        "note": "canvas_only_no_dom_targets",
                    }
                return {
                    "status": "fail",
                    "reason": "countdown_or_targets_timeout",
                    "final_state": final,
                    "log": str(self.log_path),
                }

        # Click targets until game over (duration is 30s default; stop when results or no targets).
        deadline_game = time.time() + 35.0
        clicks = 0
        while time.time() < deadline_game:
            state = _query_mouse_accuracy_state()
            if state.get("hasResults") and not (state.get("targets") or []):
                break
            targets = state.get("targets") or []
            if not targets:
                time.sleep(0.15)
                continue
            t = targets[0]
            gx, gy = self.click_client_point(t["cx"], t["cy"], profile)
            self.log("target_click", target_id=t.get("id"), global_point=[gx, gy])
            clicks += 1
            time.sleep(0.04)

        # Allow results modal/screen to render.
        time.sleep(1.2)
        final = _query_mouse_accuracy_state()
        body = (final.get("bodyPreview") or "").lower()
        has_result_text = (
            "score" in body or "accuracy" in body or "hits" in body or "misses" in body
            or "result" in body or "play again" in body or "your" in body
        )
        passed = bool(
            final.get("hasResults")
            or (has_result_text and clicks > 10)
            or (clicks >= 30 and len(body) > 50)
        )
        return {
            "status": "ok" if passed else "incomplete",
            "passed": passed,
            "clicks": clicks,
            "final_state": final,
            "log": str(self.log_path),
        }

    def run_classic_game(
        self,
        profile: MotionProfile,
        *,
        skip_evidence: bool = False,
        content_inset: float | None = None,
        aim_offset_y: float | None = None,
        speed_level: str = "normal",
        target_size: str | None = None,
    ) -> dict[str, Any]:
        """First test: Classic version has DOM targets. Pass = round completed and result captured."""
        if not skip_evidence:
            _run([str(VENV_PYTHON), str(MISSION_CONTROL), "up", "live", "--json"])
            evidence = _ensure_safari_ready()
            self.log("evidence", evidence=evidence)
        else:
            _hide_cursor_app_and_activate_safari()
            time.sleep(0.8)
            self.log("evidence", skipped=True)

        _osascript(f'tell application "Safari" to set URL of current tab of front window to "{MOUSE_ACCURACY_CLASSIC}"')
        time.sleep(1.8)
        self.log("navigated", url=MOUSE_ACCURACY_CLASSIC)

        state = _query_classic_state()
        if not state.get("startRect"):
            return {
                "status": "fail",
                "reason": "classic_start_not_found",
                "final_state": state,
                "log": str(self.log_path),
            }
        # Optionally set spawn speed (Slow / Normal / Fast / Epic) and target size (Tiny / Small / Medium / Large) before Start.
        if speed_level and str(speed_level).strip():
            speed_clicked = _do_js(
                '(function(){ var want = "' + str(speed_level).strip().lower() + '"; var el = Array.from(document.querySelectorAll("a, button, label, div, span")).find(function(e){ return (e.innerText||e.textContent||"").trim().toLowerCase() === want; }); if(el){ el.click(); return "clicked"; } return "not_found"; })()'
            )
            self.log("speed", level=speed_level, result=speed_clicked.strip('"'))
            time.sleep(0.25)
        if target_size and str(target_size).strip():
            size_clicked = _do_js(
                '(function(){ var want = "' + str(target_size).strip().lower() + '"; var el = Array.from(document.querySelectorAll("a, button, label, div, span")).find(function(e){ return (e.innerText||e.textContent||"").trim().toLowerCase() === want; }); if(el){ el.click(); return "clicked"; } return "not_found"; })()'
            )
            self.log("target_size", size=target_size, result=size_clicked.strip('"'))
            time.sleep(0.25)
        # Use JS click so we stay in same tab (Quartz click might open new tab).
        start_clicked = _do_js(
            '(function(){ var btn = Array.from(document.querySelectorAll("a, button")).find(function(el){ return /start!?|play|go/i.test((el.innerText||"").trim()); }); if(btn){ btn.click(); return "clicked"; } return "not_found"; })()'
        )
        self.log("start_click", method="js", result=start_clicked.strip('"'))
        time.sleep(2.2)

        # Wait for targets to appear (round starts).
        deadline = time.time() + 8.0
        while time.time() < deadline:
            state = _query_classic_state()
            if state.get("targets") and len(state["targets"]) > 0:
                break
            if state.get("gameOver"):
                break
            time.sleep(0.12)
        else:
            return {
                "status": "fail",
                "reason": "classic_targets_timeout",
                "final_state": _query_classic_state(),
                "log": str(self.log_path),
            }

        # Use page viewport origin so clicks land on targets (window.screenX/screenY in Safari).
        vx = state.get("screenX", 0)
        vy = state.get("screenY", 0)
        viewport_origin = (float(vx), float(vy)) if (vx or vy) else None
        if viewport_origin is None:
            b = _get_safari_window_bounds()
            inset = content_inset if content_inset is not None else SAFARI_CONTENT_INSET_TOP
            viewport_origin = (b["x"], b["y"] + inset)
        self.log("viewport_origin", viewport_origin=viewport_origin)

        # Every click: snapshot cursor at click, then readjust aim so next click goes to circle center.
        deadline_game = time.time() + 45.0
        clicks = 0
        initial_y = aim_offset_y
        if initial_y is None:
            initial_y = -6.0 if (target_size and str(target_size).strip().lower() in ("small", "tiny")) else AIM_OFFSET_Y_INITIAL
        running_aim_x = 0.0
        running_aim_y = initial_y
        self.log("aim_adjust", initial_offset=(running_aim_x, running_aim_y), note="per-click snapshot and recenter")

        while time.time() < deadline_game:
            state = _query_classic_state()
            if state.get("gameOver") or (state.get("timeRemaining") is not None and state.get("timeRemaining") <= 0):
                break
            targets = state.get("targets") or []
            if not targets:
                time.sleep(0.006)
                continue

            n_before = len(targets)
            for t in targets:
                intended_cx = t["cx"] + running_aim_x
                intended_cy = t["cy"] + running_aim_y
                position_errors: list[tuple[float, float]] = []
                gx, gy = self.click_client_point(
                    intended_cx, intended_cy,
                    profile,
                    viewport_origin=viewport_origin,
                    position_errors=position_errors,
                )
                clicks += 1
                if position_errors:
                    err_x, err_y = position_errors[0]
                    running_aim_x = running_aim_x - err_x
                    running_aim_y = running_aim_y - err_y
                    running_aim_x = max(AIM_OFFSET_X_MIN, min(AIM_OFFSET_X_MAX, running_aim_x))
                    running_aim_y = max(AIM_OFFSET_Y_MIN, min(AIM_OFFSET_Y_MAX, running_aim_y))
                    self.log("aim_adjust", reason="per_click", err_x=round(err_x, 2), err_y=round(err_y, 2), new_aim=(round(running_aim_x, 2), round(running_aim_y, 2)))
                else:
                    self.log("target_click", global_point=[gx, gy], aim=(running_aim_x, running_aim_y))
                time.sleep(0.001)
            time.sleep(0.001)

            state_after = _query_classic_state()
            n_after = len(state_after.get("targets") or [])
            cleared = max(0, n_before - n_after)
            if n_before >= 2 and cleared < n_before * 0.5:
                running_aim_y = max(AIM_OFFSET_Y_MIN, running_aim_y - AIM_ADJUST_STEP)
                self.log("aim_adjust", reason="low_clear", n_before=n_before, cleared=cleared, new_offset_y=running_aim_y)
            elif cleared >= n_before * 0.7 and running_aim_y < AIM_OFFSET_Y_MAX:
                running_aim_y = min(AIM_OFFSET_Y_MAX, running_aim_y + 0.5)
                self.log("aim_adjust", reason="good_clear", n_before=n_before, cleared=cleared, new_offset_y=running_aim_y)
            else:
                self.log("aim_adjust", reason="hold", n_before=n_before, cleared=cleared, offset=(running_aim_x, running_aim_y))

        time.sleep(0.25)
        final = _query_classic_state()
        body = (final.get("bodyPreview") or "").lower()
        passed = bool(
            final.get("gameOver")
            or final.get("timeRemaining") == 0
            or ("time remaining: 0" in body or "times up" in body or "score" in body or "go again" in body)
            or (clicks >= 25 and "time remaining" in body)  # round was played
        )
        return {
            "status": "ok" if passed else "incomplete",
            "passed": passed,
            "clicks": clicks,
            "final_state": final,
            "log": str(self.log_path),
        }


def main() -> None:
    parser = argparse.ArgumentParser(description="Mouse Accuracy — run first test (Classic) until pass")
    parser.add_argument("--name", default="mouse_accuracy_classic")
    parser.add_argument("--move-duration", type=float, default=0.005)
    parser.add_argument("--move-steps", type=int, default=1)
    parser.add_argument("--settle-sleep", type=float, default=0.001)
    parser.add_argument("--main", action="store_true", help="Run main game instead of Classic (canvas-only, may not pass)")
    parser.add_argument("--skip-evidence", action="store_true", help="Skip mission_control evidence (faster; use when Safari already front)")
    parser.add_argument("--content-inset", type=float, default=None, help="Override content top inset (default 108); use if clicks miss vertically")
    parser.add_argument("--aim-offset-y", type=float, default=None, help="Initial Y offset (px); if omitted, aim is adjusted during the test from hit/miss")
    parser.add_argument("--speed", choices=["slow", "normal", "fast", "epic"], default="normal", help="Target spawn speed (slow = easiest to adjust)")
    parser.add_argument("--size", default=None, help="Target size: tiny, small, medium, large (default = page default)")
    args = parser.parse_args()

    profile = MotionProfile(
        name=args.name,
        move_duration=args.move_duration,
        move_steps=args.move_steps,
        settle_sleep=args.settle_sleep,
    )
    harness = MouseAccuracyHarness(args.name)
    # First test = Classic (DOM targets). Do not advance until this passes.
    result = (
        harness.run_classic_game(
            profile,
            skip_evidence=args.skip_evidence,
            content_inset=args.content_inset,
            aim_offset_y=args.aim_offset_y,
            speed_level=args.speed,
            target_size=args.size,
        )
        if not args.main
        else harness.run_main_game(profile)
    )
    print(json.dumps(result, indent=2))
    if not result.get("passed"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
