#!/usr/bin/env python3
"""Live Cursor-window demo: visible move + click + typing in Cursor.

This runs on local macOS using native Quartz HID events only.
No AppleScript automation permission is required.
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


def _display_bounds() -> tuple[float, float, float, float]:
    b = Quartz.CGDisplayBounds(Quartz.CGMainDisplayID())
    left = float(b.origin.x)
    top = float(b.origin.y)
    right = left + float(b.size.width)
    bottom = top + float(b.size.height)
    return left, top, right, bottom


def _mouse_location() -> tuple[float, float]:
    event = Quartz.CGEventCreate(None)
    p = Quartz.CGEventGetLocation(event)
    return float(p.x), float(p.y)


def _post_mouse_move(x: float, y: float) -> None:
    point = Quartz.CGPointMake(x, y)
    event = Quartz.CGEventCreateMouseEvent(
        None, Quartz.kCGEventMouseMoved, point, Quartz.kCGMouseButtonLeft
    )
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, event)


def _move_mouse_smooth(x: float, y: float, duration_s: float = 0.8, steps: int = 34) -> None:
    sx, sy = _mouse_location()
    for i in range(1, steps + 1):
        t = i / steps
        nx = sx + (x - sx) * t
        ny = sy + (y - sy) * t
        _post_mouse_move(nx, ny)
        time.sleep(max(0.001, duration_s / steps))


def _left_click(x: float, y: float) -> None:
    p = Quartz.CGPointMake(x, y)
    down = Quartz.CGEventCreateMouseEvent(
        None, Quartz.kCGEventLeftMouseDown, p, Quartz.kCGMouseButtonLeft
    )
    up = Quartz.CGEventCreateMouseEvent(
        None, Quartz.kCGEventLeftMouseUp, p, Quartz.kCGMouseButtonLeft
    )
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, down)
    time.sleep(0.04)
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


def _type_text(text: str, char_delay_s: float = 0.012) -> None:
    for ch in text:
        down = Quartz.CGEventCreateKeyboardEvent(None, 0, True)
        up = Quartz.CGEventCreateKeyboardEvent(None, 0, False)
        Quartz.CGEventKeyboardSetUnicodeString(down, len(ch), ch)
        Quartz.CGEventKeyboardSetUnicodeString(up, len(ch), ch)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, down)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, up)
        time.sleep(char_delay_s)


def _screenshot(path: Path) -> None:
    subprocess.run(["screencapture", "-x", str(path)], check=True)


def run_demo() -> dict:
    events: list[ActionEvent] = []

    def log(action: str, detail: str) -> None:
        events.append(ActionEvent(ts_iso=_now_iso(), action=action, detail=detail))
        print(f"[{events[-1].ts_iso}] {action}: {detail}")

    print("\n=== LIVE CURSOR WINDOW DEMO ===")
    print("Target: Cursor")
    print("Watch your screen now. Control starts in 8 seconds...")
    for sec in range(8, 0, -1):
        print(f"  starting in {sec}...")
        time.sleep(1.0)

    log("activate_app", "Cursor")
    subprocess.run(["open", "-a", "Cursor"], check=True)
    time.sleep(1.8)

    # Cmd+N to open a fresh unsaved editor tab.
    cmd_flag = getattr(Quartz, "kCGEventFlagMaskCommand", 0x100000)
    log("key_press", "Cmd+N")
    _key_press(45, flags=cmd_flag)  # keycode 45 = N
    time.sleep(0.6)

    left, top, right, bottom = _display_bounds()
    log("window_bounds", f"left={left}, top={top}, right={right}, bottom={bottom}")

    # Aim at likely editor region in a full-screen Cursor layout.
    p1 = (left + (right - left) * 0.30, top + (bottom - top) * 0.22)
    p2 = (left + (right - left) * 0.74, top + (bottom - top) * 0.22)
    p3 = (left + (right - left) * 0.74, top + (bottom - top) * 0.62)
    p4 = (left + (right - left) * 0.30, top + (bottom - top) * 0.62)
    target = (left + (right - left) * 0.54, top + (bottom - top) * 0.40)

    for i, (tx, ty) in enumerate((p1, p2, p3, p4, target), start=1):
        log("move_mouse", f"path_point_{i}=({tx:.1f},{ty:.1f})")
        _move_mouse_smooth(tx, ty, duration_s=0.72, steps=36)
        time.sleep(0.1)

    log("click", f"editor_target=({target[0]:.1f},{target[1]:.1f})")
    _left_click(*target)
    time.sleep(0.2)

    payload = (
        "# Live Cursor Control Demo\n"
        "Date: 2026-03-05\n"
        "Typed by native Quartz events after visible pointer motion and click.\n"
        "No AppleScript automation prompt path used in this run.\n"
    )
    log("type_text", "typing payload in Cursor editor")
    _type_text(payload)

    shot = ARTIFACT_DIR / "live_cursor_window_demo_2026-03-05.png"
    shot.parent.mkdir(parents=True, exist_ok=True)
    _screenshot(shot)
    log("screenshot", str(shot))

    return {
        "run_date": "2026-03-05",
        "timezone": "America/Los_Angeles",
        "target_app": "Cursor",
        "success": True,
        "actions": [asdict(x) for x in events],
        "screenshot_path": str(shot),
    }


def main() -> None:
    out = ARTIFACT_DIR / "live_cursor_window_demo_2026-03-05.json"
    try:
        result = run_demo()
    except Exception as exc:  # pragma: no cover
        result = {
            "run_date": "2026-03-05",
            "timezone": "America/Los_Angeles",
            "target_app": "Cursor",
            "success": False,
            "error": str(exc),
        }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"\nArtifact: {out}")
    if not result.get("success"):
        raise SystemExit(1)
    print("Live Cursor window demo completed.")


if __name__ == "__main__":
    main()

