#!/usr/bin/env python3
"""Generate an AI image on canva.com using macOS Quartz GUI automation.

Coordinate reference (from screenshot analysis of 2880x1800 retina display):
- Safari toolbar: y ≈ 0-80 (retina px)
- Tab bar: y ≈ 80-140
- Canva navbar: y ≈ 140-230
- Cookie banner: y ≈ 890-1100, "Accept all cookies" button at (200, 1070)
- Searchbox: y ≈ 870, x ≈ 80-750 (center ≈ 400)
- Purple Generate button: x ≈ 830-960, y ≈ 870
- "Log in" button: x ≈ 1940, y ≈ 228
"""

from __future__ import annotations

import subprocess
import time

import pytest

# macOS-only: drives real macOS UI via the native Quartz/AppKit stack.
pytest.importorskip("Quartz", reason="macOS-only GUI automation (requires pyobjc/Quartz)")

import Quartz
from AppKit import NSScreen


def _pixel_to_global(px: float, py: float) -> tuple[float, float]:
    screen = NSScreen.mainScreen()
    scale = screen.backingScaleFactor()
    frame = screen.frame()
    return (frame.origin.x + px / scale, frame.origin.y + py / scale)


def _click(px: int, py: int, label: str = "") -> None:
    gx, gy = _pixel_to_global(px, py)
    pt = Quartz.CGPointMake(gx, gy)
    down = Quartz.CGEventCreateMouseEvent(
        None, Quartz.kCGEventLeftMouseDown, pt, Quartz.kCGMouseButtonLeft)
    up = Quartz.CGEventCreateMouseEvent(
        None, Quartz.kCGEventLeftMouseUp, pt, Quartz.kCGMouseButtonLeft)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, down)
    time.sleep(0.05)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, up)
    time.sleep(0.4)
    if label:
        print(f"    -> click: {label} @ ({px}, {py})")


def _type_string(text: str, char_delay: float = 0.02) -> None:
    for ch in text:
        ev_down = Quartz.CGEventCreateKeyboardEvent(None, 0, True)
        Quartz.CGEventKeyboardSetUnicodeString(ev_down, len(ch), ch)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, ev_down)
        ev_up = Quartz.CGEventCreateKeyboardEvent(None, 0, False)
        Quartz.CGEventKeyboardSetUnicodeString(ev_up, len(ch), ch)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, ev_up)
        time.sleep(char_delay)


def _key(keycode: int, flags: int = 0) -> None:
    down = Quartz.CGEventCreateKeyboardEvent(None, keycode, True)
    up = Quartz.CGEventCreateKeyboardEvent(None, keycode, False)
    if flags:
        Quartz.CGEventSetFlags(down, flags)
        Quartz.CGEventSetFlags(up, flags)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, down)
    time.sleep(0.05)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, up)
    time.sleep(0.2)


def _scroll_down(lines: int = 3, repeats: int = 3) -> None:
    for _ in range(repeats):
        ev = Quartz.CGEventCreateScrollWheelEvent(
            None, Quartz.kCGScrollEventUnitLine, 1, -lines)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, ev)
        time.sleep(0.2)


def _ss(name: str) -> str:
    path = f"/tmp/canva_{name}.png"
    subprocess.run(["screencapture", "-x", path], check=True)
    print(f"    [screenshot] {path}")
    return path


def main():
    print("=== Canva AI Image Generator ===\n")

    prompt = (
        "A close-up, high-angle shot of two hands interlaced, "
        "struggling over a small, shattered glass sphere with "
        "profuse details and exhaustive colors to show the realism"
    )

    # Step 1: Ensure Safari is on the Canva tab
    print("[1] Activating Safari on Canva page...")
    subprocess.run(["osascript", "-e", '''
tell application "Safari"
    activate
    set tabCount to count of tabs of front window
    repeat with i from 1 to tabCount
        if URL of tab i of front window contains "canva.com" then
            set current tab of front window to tab i of front window
            exit repeat
        end if
    end repeat
end tell'''], check=True)
    time.sleep(2)
    _ss("01_activated")

    # Step 2: Accept cookies (button at bottom of page)
    print("\n[2] Accepting cookies...")
    # "Accept all cookies" button: from screenshot, it's at approximately
    # x=200, y=1070 in retina pixels
    _click(200, 1070, "Accept all cookies")
    time.sleep(2)
    _ss("02_cookies")

    # Step 3: Scroll down slightly to fully reveal the search box
    print("\n[3] Scrolling to reveal searchbox...")
    _scroll_down(lines=4, repeats=3)
    time.sleep(1)
    _ss("03_scrolled")

    # Step 4: Click the searchbox
    print("\n[4] Clicking the searchbox...")
    # The search input field is a white box in the hero area.
    # After scrolling and cookie dismiss, it should be around y=700-800 area.
    # Let's try center of page width, around where the input should be.
    # The input was at roughly x=80..750, y≈870 before scroll.
    # After scrolling ~12 lines down (4*3), it moves up by roughly 180px.
    # Estimate: x=400, y=700
    _click(400, 700, "searchbox (attempt 1)")
    time.sleep(0.5)
    _ss("04_clicked_searchbox")

    # Step 5: Clear any existing text and type prompt
    print("\n[5] Typing prompt...")
    _key(0, flags=Quartz.kCGEventFlagMaskCommand)  # Cmd+A
    time.sleep(0.1)
    _key(51)  # Backspace
    time.sleep(0.2)

    _type_string(prompt)
    time.sleep(1)
    _ss("05_typed")
    print(f"    Typed {len(prompt)} characters")

    # Step 6: Click Generate or press Enter
    print("\n[6] Generating image...")
    # The purple "Generate AI Images" button should be to the right of the searchbox.
    # After scroll, estimated at x≈900, y≈700
    _click(900, 700, "Generate button")
    time.sleep(3)
    _ss("06_after_generate")

    # If login was required, Canva shows a login modal.
    # Check the screenshot to see what happened.

    # Step 7: Wait and monitor
    print("\n[7] Waiting for results (up to 60s)...")
    for i in range(12):
        time.sleep(5)
        _ss(f"07_wait_{i:02d}")
        print(f"    Check {i+1}/12")

    _ss("08_final")
    print("\n=== DONE ===")
    print("Final: /tmp/canva_08_final.png")
    print("Check Safari for results. If login was required, log in and re-run.")


if __name__ == "__main__":
    main()
