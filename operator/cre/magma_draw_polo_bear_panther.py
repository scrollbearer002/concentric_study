#!/usr/bin/env python3
"""Draw a stylized Polo-style polar bear in Black Panther Party-inspired clothing on Magma.

This uses direct Quartz mouse events in full-screen Safari so the cursor visibly
does the work. It opens a blank Magma canvas if Safari is not already on one.
"""

from __future__ import annotations

import math
import subprocess
import sys
import time
from pathlib import Path

import Quartz
from AppKit import NSScreen
from reference_board import build_polo_bear_panther_reference_board


ROOT = Path(__file__).resolve().parent
FINAL_SCREENSHOT = ROOT / "magma_polo_bear_panther_final.png"


def _osascript(script: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )


def _safari_activate() -> None:
    subprocess.run(["osascript", "-e", 'tell application "Safari" to activate'], check=True)
    time.sleep(0.8)


def _safari_get_url() -> str:
    result = _osascript('tell application "Safari" to get URL of current tab of front window')
    return (result.stdout or "").strip()


def _safari_set_url(url: str) -> None:
    _osascript(f'tell application "Safari" to set URL of current tab of front window to "{url}"')


def _safari_do_js(js: str) -> str:
    one_line = " ".join(js.split())
    escaped = one_line.replace("\\", "\\\\").replace('"', '\\"')
    result = _osascript(
        f'tell application "Safari" to do JavaScript "{escaped}" in current tab of front window'
    )
    return (result.stdout or "").strip()


def ensure_magma_canvas() -> str:
    _safari_activate()
    current_url = _safari_get_url()
    if "magma.com/d/" in current_url:
        return current_url

    subprocess.run(["open", "-a", "Safari", "https://www.magma.com"], check=True, timeout=5)
    time.sleep(3)
    _safari_set_url("https://magma.com/app")
    time.sleep(5)

    js_new = """
    (function() {
      const el = Array.from(document.querySelectorAll('button, a, [role=button]'))
        .find(e => e.innerText && e.innerText.trim().includes('New canvas'));
      if (el) { el.click(); return 'clicked'; }
      return 'not_found';
    })();
    """
    _safari_do_js(js_new)
    time.sleep(1.5)

    js_landscape = """
    (function() {
      const el = Array.from(document.querySelectorAll('button, a, [role=menuitem], div'))
        .find(e => e.innerText && e.innerText.trim().includes('Landscape'));
      if (el) { el.click(); return 'clicked'; }
      return 'not_found';
    })();
    """
    _safari_do_js(js_landscape)
    time.sleep(8)
    return _safari_get_url()


def pixel_to_global(px: float, py: float) -> tuple[float, float]:
    primary = NSScreen.mainScreen()
    if primary is None:
        return (px, py)
    scale = primary.backingScaleFactor()
    frame = primary.frame()
    return (frame.origin.x + px / scale, frame.origin.y + py / scale)


def draw_stroke_global(points: list[tuple[float, float]], delay: float = 0.006) -> None:
    if len(points) < 2:
        return
    pts_global = [pixel_to_global(x, y) for x, y in points]
    start = pts_global[0]
    down = Quartz.CGEventCreateMouseEvent(
        None,
        Quartz.kCGEventLeftMouseDown,
        Quartz.CGPointMake(start[0], start[1]),
        Quartz.kCGMouseButtonLeft,
    )
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, down)
    time.sleep(0.05)
    for px, py in pts_global[1:]:
        drag = Quartz.CGEventCreateMouseEvent(
            None,
            Quartz.kCGEventLeftMouseDragged,
            Quartz.CGPointMake(px, py),
            Quartz.kCGMouseButtonLeft,
        )
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, drag)
        time.sleep(delay)
    end = pts_global[-1]
    up = Quartz.CGEventCreateMouseEvent(
        None,
        Quartz.kCGEventLeftMouseUp,
        Quartz.CGPointMake(end[0], end[1]),
        Quartz.kCGMouseButtonLeft,
    )
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, up)
    time.sleep(0.12)


def smooth_curve(points: list[tuple[float, float]], n_per_seg: int = 10) -> list[tuple[float, float]]:
    if len(points) < 2:
        return points
    out = [points[0]]
    for i in range(len(points) - 1):
        ax, ay = points[i]
        bx, by = points[i + 1]
        for k in range(1, n_per_seg + 1):
            t = k / n_per_seg
            out.append((ax + t * (bx - ax), ay + t * (by - ay)))
    return out


def oval_points(cx: float, cy: float, rx: float, ry: float, n: int = 32) -> list[tuple[float, float]]:
    return [
        (cx + rx * math.cos(2 * math.pi * i / n), cy + ry * math.sin(2 * math.pi * i / n))
        for i in range(n + 1)
    ]


def arc_points(
    cx: float,
    cy: float,
    rx: float,
    ry: float,
    start_deg: float,
    end_deg: float,
    n: int = 18,
) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    for i in range(n + 1):
        t = i / n
        ang = math.radians(start_deg + (end_deg - start_deg) * t)
        points.append((cx + rx * math.cos(ang), cy + ry * math.sin(ang)))
    return points


def line(x1: float, y1: float, x2: float, y2: float) -> list[tuple[float, float]]:
    return [(x1, y1), (x2, y2)]


def build_bear_strokes() -> list[list[tuple[float, float]]]:
    cx, cy = 1120.0, 760.0
    strokes: list[list[tuple[float, float]]] = []

    # Beret and ears
    strokes.append(smooth_curve(arc_points(cx - 25, cy - 250, 110, 30, 195, 345), 4))
    strokes.append(smooth_curve([
        (cx - 120, cy - 246), (cx - 55, cy - 285), (cx + 22, cy - 276), (cx + 55, cy - 242)
    ], 8))
    strokes.append(smooth_curve(oval_points(cx - 88, cy - 215, 20, 24, 18), 4))
    strokes.append(smooth_curve(oval_points(cx + 70, cy - 208, 19, 22, 18), 4))

    # Head outline and muzzle
    head = [
        (cx - 108, cy - 182), (cx - 132, cy - 138), (cx - 132, cy - 75), (cx - 102, cy - 20),
        (cx - 55, cy + 18), (cx, cy + 28), (cx + 58, cy + 17), (cx + 105, cy - 18),
        (cx + 130, cy - 76), (cx + 128, cy - 135), (cx + 102, cy - 182), (cx + 52, cy - 208),
        (cx - 10, cy - 215), (cx - 68, cy - 208), (cx - 108, cy - 182),
    ]
    strokes.append(smooth_curve(head, 10))
    strokes.append(smooth_curve(oval_points(cx, cy - 44, 52, 38, 24), 4))
    strokes.append(smooth_curve(oval_points(cx, cy - 20, 18, 10, 16), 4))
    strokes.append(smooth_curve(line(cx, cy - 10, cx, cy + 8), 8))
    strokes.append(smooth_curve([
        (cx - 24, cy + 12), (cx - 12, cy + 24), (cx, cy + 18), (cx + 12, cy + 24), (cx + 24, cy + 12)
    ], 8))

    # Sunglasses
    strokes.append(smooth_curve(line(cx - 62, cy - 112, cx + 62, cy - 112), 8))
    strokes.append(smooth_curve(oval_points(cx - 38, cy - 110, 28, 16, 22), 4))
    strokes.append(smooth_curve(oval_points(cx + 38, cy - 110, 28, 16, 22), 4))
    strokes.append(smooth_curve(line(cx - 8, cy - 110, cx + 8, cy - 110), 8))

    # Jacket / torso
    torso = [
        (cx - 126, cy + 42), (cx - 156, cy + 126), (cx - 148, cy + 250), (cx - 118, cy + 330),
        (cx - 88, cy + 390), (cx - 30, cy + 420), (cx + 30, cy + 420), (cx + 88, cy + 390),
        (cx + 118, cy + 330), (cx + 148, cy + 250), (cx + 156, cy + 126), (cx + 126, cy + 42),
        (cx + 88, cy + 6), (cx + 38, cy - 8), (cx - 36, cy - 8), (cx - 88, cy + 8), (cx - 126, cy + 42),
    ]
    strokes.append(smooth_curve(torso, 10))
    strokes.append(smooth_curve([
        (cx - 82, cy + 28), (cx - 38, cy + 128), (cx - 10, cy + 190)
    ], 10))
    strokes.append(smooth_curve([
        (cx + 82, cy + 28), (cx + 38, cy + 128), (cx + 10, cy + 190)
    ], 10))
    strokes.append(smooth_curve(line(cx, cy + 4, cx, cy + 294), 10))
    for y in [74, 118, 162]:
        strokes.append(smooth_curve(line(cx - 12, cy + y, cx + 12, cy + y), 8))

    # Jacket pockets and belt
    strokes.append(smooth_curve([
        (cx - 108, cy + 185), (cx - 68, cy + 165), (cx - 48, cy + 188), (cx - 88, cy + 204), (cx - 108, cy + 185)
    ], 8))
    strokes.append(smooth_curve([
        (cx + 108, cy + 185), (cx + 68, cy + 165), (cx + 48, cy + 188), (cx + 88, cy + 204), (cx + 108, cy + 185)
    ], 8))
    strokes.append(smooth_curve(line(cx - 84, cy + 308, cx + 84, cy + 308), 8))
    strokes.append(smooth_curve(line(cx - 12, cy + 308, cx + 12, cy + 308), 8))

    # Arms and paws
    left_arm = [
        (cx - 124, cy + 64), (cx - 192, cy + 108), (cx - 230, cy + 172), (cx - 230, cy + 238),
        (cx - 214, cy + 288), (cx - 182, cy + 312), (cx - 154, cy + 296), (cx - 142, cy + 248),
        (cx - 148, cy + 186), (cx - 138, cy + 118), (cx - 124, cy + 64),
    ]
    right_arm = [
        (cx + 124, cy + 64), (cx + 192, cy + 108), (cx + 230, cy + 172), (cx + 230, cy + 238),
        (cx + 214, cy + 288), (cx + 182, cy + 312), (cx + 154, cy + 296), (cx + 142, cy + 248),
        (cx + 148, cy + 186), (cx + 138, cy + 118), (cx + 124, cy + 64),
    ]
    strokes.append(smooth_curve(left_arm, 10))
    strokes.append(smooth_curve(right_arm, 10))
    strokes.append(smooth_curve(oval_points(cx - 186, cy + 312, 24, 18, 18), 4))
    strokes.append(smooth_curve(oval_points(cx + 186, cy + 312, 24, 18, 18), 4))

    # Pants and boots
    strokes.append(smooth_curve([
        (cx - 70, cy + 420), (cx - 82, cy + 520), (cx - 88, cy + 640), (cx - 84, cy + 760)
    ], 10))
    strokes.append(smooth_curve([
        (cx - 12, cy + 420), (cx - 16, cy + 522), (cx - 18, cy + 640), (cx - 16, cy + 760)
    ], 10))
    strokes.append(smooth_curve([
        (cx + 12, cy + 420), (cx + 16, cy + 522), (cx + 18, cy + 640), (cx + 16, cy + 760)
    ], 10))
    strokes.append(smooth_curve([
        (cx + 70, cy + 420), (cx + 82, cy + 520), (cx + 88, cy + 640), (cx + 84, cy + 760)
    ], 10))
    strokes.append(smooth_curve([
        (cx - 108, cy + 760), (cx - 24, cy + 760), (cx - 6, cy + 786), (cx - 122, cy + 792), (cx - 108, cy + 760)
    ], 8))
    strokes.append(smooth_curve([
        (cx + 24, cy + 760), (cx + 108, cy + 760), (cx + 122, cy + 792), (cx + 6, cy + 786), (cx + 24, cy + 760)
    ], 8))

    # Clothing and fur details
    strokes.append(smooth_curve(line(cx - 46, cy - 2, cx - 22, cy + 40), 8))
    strokes.append(smooth_curve(line(cx + 46, cy - 2, cx + 22, cy + 40), 8))
    for y in [110, 136, 162, 188]:
        strokes.append(smooth_curve(line(cx - 30, cy + y, cx + 30, cy + y), 8))
    strokes.append(smooth_curve(arc_points(cx - 52, cy - 46, 18, 10, 210, 330), 4))
    strokes.append(smooth_curve(arc_points(cx + 52, cy - 46, 18, 10, 210, 330), 4))
    strokes.append(smooth_curve([
        (cx - 90, cy - 170), (cx - 72, cy - 150), (cx - 58, cy - 132)
    ], 6))
    strokes.append(smooth_curve([
        (cx + 90, cy - 170), (cx + 72, cy - 150), (cx + 58, cy - 132)
    ], 6))

    return strokes


def capture_final() -> None:
    subprocess.run(["screencapture", "-x", str(FINAL_SCREENSHOT)], check=True)


def main() -> None:
    ref_board = build_polo_bear_panther_reference_board()
    written = ref_board.save_split_artifacts(ROOT, "magma_polo_bear_panther")
    print(f"[magma] reference_board={written['reference_board']}")
    url = ensure_magma_canvas()
    print(f"[magma] canvas: {url}")
    time.sleep(3)
    strokes = build_bear_strokes()
    print(f"[draw] strokes: {len(strokes)}")
    for idx, stroke in enumerate(strokes, start=1):
        draw_stroke_global(stroke, delay=0.005 if len(stroke) > 12 else 0.007)
        if idx % 6 == 0:
            time.sleep(0.2)
    time.sleep(1.5)
    capture_final()
    print(f"[done] screenshot: {FINAL_SCREENSHOT}")


if __name__ == "__main__":
    main()
