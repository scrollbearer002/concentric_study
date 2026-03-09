#!/usr/bin/env python3
"""Live visual control demo: visible mouse movement + click + typing.

Safe target: TextEdit (local document only, no credentials, no network actions).

This script is intentionally human-visible:
- 8-second countdown before control starts
- smooth pointer movements
- deliberate click and paced typing
- completion screenshot + JSON action log
"""

from __future__ import annotations

import json
import subprocess
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

import Quartz


ARTIFACT_DIR = Path(__file__).resolve().parent / "artifacts"


@dataclass
class ActionEvent:
    ts_iso: str
    action: str
    detail: str


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat()


def _activate_textedit() -> None:
    # Keep activation path free of AppleScript automation prompts.
    subprocess.run(["open", "-a", "TextEdit"], check=True)
    time.sleep(1.4)
    # Cmd+N (keycode 45) to open a fresh document in the active app.
    _key_press(
        keycode=45,
        flags=getattr(Quartz, "kCGEventFlagMaskCommand", 0x100000),
    )


def _main_display_bounds() -> tuple[float, float, float, float]:
    bounds = Quartz.CGDisplayBounds(Quartz.CGMainDisplayID())
    left = float(bounds.origin.x)
    top = float(bounds.origin.y)
    right = left + float(bounds.size.width)
    bottom = top + float(bounds.size.height)
    return left, top, right, bottom


def _mouse_location() -> tuple[float, float]:
    event = Quartz.CGEventCreate(None)
    point = Quartz.CGEventGetLocation(event)
    return float(point.x), float(point.y)


def _post_mouse_move(x: float, y: float) -> None:
    point = Quartz.CGPointMake(x, y)
    event = Quartz.CGEventCreateMouseEvent(
        None,
        Quartz.kCGEventMouseMoved,
        point,
        Quartz.kCGMouseButtonLeft,
    )
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, event)


def _move_mouse_smooth(x: float, y: float, duration_s: float = 1.0, steps: int = 45) -> None:
    start_x, start_y = _mouse_location()
    for i in range(1, steps + 1):
        t = i / steps
        nx = start_x + (x - start_x) * t
        ny = start_y + (y - start_y) * t
        _post_mouse_move(nx, ny)
        time.sleep(max(0.001, duration_s / steps))


def _left_click(x: float, y: float) -> None:
    point = Quartz.CGPointMake(x, y)
    down = Quartz.CGEventCreateMouseEvent(
        None, Quartz.kCGEventLeftMouseDown, point, Quartz.kCGMouseButtonLeft
    )
    up = Quartz.CGEventCreateMouseEvent(
        None, Quartz.kCGEventLeftMouseUp, point, Quartz.kCGMouseButtonLeft
    )
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, down)
    time.sleep(0.04)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, up)


def _post_unicode_char(ch: str) -> None:
    down = Quartz.CGEventCreateKeyboardEvent(None, 0, True)
    up = Quartz.CGEventCreateKeyboardEvent(None, 0, False)
    Quartz.CGEventKeyboardSetUnicodeString(down, len(ch), ch)
    Quartz.CGEventKeyboardSetUnicodeString(up, len(ch), ch)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, down)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, up)


def _key_press(keycode: int, flags: int = 0) -> None:
    down = Quartz.CGEventCreateKeyboardEvent(None, keycode, True)
    up = Quartz.CGEventCreateKeyboardEvent(None, keycode, False)
    if flags:
        Quartz.CGEventSetFlags(down, flags)
        Quartz.CGEventSetFlags(up, flags)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, down)
    time.sleep(0.04)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, up)
    time.sleep(0.12)


def _type_text(text: str, char_delay_s: float = 0.02) -> None:
    for ch in text:
        _post_unicode_char(ch)
        time.sleep(char_delay_s)


def _screenshot(path: Path) -> None:
    subprocess.run(["screencapture", "-x", str(path)], check=True)


def run_demo() -> dict:
    events: list[ActionEvent] = []

    def log(action: str, detail: str) -> None:
        events.append(ActionEvent(ts_iso=_now_iso(), action=action, detail=detail))
        print(f"[{events[-1].ts_iso}] {action}: {detail}")

    print("\n=== LIVE VISUAL CONTROL DEMO ===")
    print("Target: TextEdit")
    print("Watch your screen now. Control starts in 8 seconds...")
    for sec in range(8, 0, -1):
        print(f"  starting in {sec}...")
        time.sleep(1.0)

    log("activate_app", "TextEdit")
    _activate_textedit()
    time.sleep(0.8)

    left, top, right, bottom = _main_display_bounds()
    cx = (left + right) / 2.0
    cy = (top + bottom) / 2.0
    log("window_bounds", f"left={left}, top={top}, right={right}, bottom={bottom}")

    # Draw a visible pointer pattern, then land in the edit area.
    targets = [
        (left + 120, top + 120),
        (right - 120, top + 120),
        (right - 120, bottom - 120),
        (left + 120, bottom - 120),
        (cx, cy),
    ]
    for idx, (tx, ty) in enumerate(targets, start=1):
        log("move_mouse", f"path_point_{idx}=({tx:.1f},{ty:.1f})")
        _move_mouse_smooth(tx, ty, duration_s=0.65, steps=32)
        time.sleep(0.12)

    log("click", f"editor_center=({cx:.1f},{cy:.1f})")
    _left_click(cx, cy)
    time.sleep(0.2)

    demo_text = (
        "Concentric Study Live Control Demo\n"
        "Date: 2026-03-05\n"
        "This line was typed by native Quartz events.\n"
        "Observed actions: smooth pointer move, click, and typing.\n"
    )
    log("type_text", "typing demo payload into TextEdit")
    _type_text(demo_text, char_delay_s=0.014)

    shot_path = ARTIFACT_DIR / "live_visual_control_demo_2026-03-05.png"
    shot_path.parent.mkdir(parents=True, exist_ok=True)
    _screenshot(shot_path)
    log("screenshot", str(shot_path))

    result = {
        "run_date": "2026-03-05",
        "timezone": "America/Los_Angeles",
        "target_app": "TextEdit",
        "success": True,
        "actions": [asdict(e) for e in events],
        "screenshot_path": str(shot_path),
    }
    return result


def main() -> None:
    out_path = ARTIFACT_DIR / "live_visual_control_demo_2026-03-05.json"
    try:
        result = run_demo()
    except Exception as exc:  # pragma: no cover - runtime/OS dependent
        result = {
            "run_date": "2026-03-05",
            "timezone": "America/Los_Angeles",
            "target_app": "TextEdit",
            "success": False,
            "error": str(exc),
        }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"\nArtifact: {out_path}")
    if not result.get("success"):
        raise SystemExit(1)
    print("Live visual control demo completed.")


if __name__ == "__main__":
    main()
