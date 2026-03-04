#!/usr/bin/env python3
from __future__ import annotations

import math
import subprocess
import time
from pathlib import Path

import Quartz
from AppKit import NSScreen
from reference_board import build_generic_reference_board

ROOT = Path(__file__).resolve().parent
FINAL_SCREENSHOT = ROOT / "magma_tiger_rl_ironman_final.png"


def _osascript(script: str) -> subprocess.CompletedProcess:
    return subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=20, check=False)


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


def _maximize() -> None:
    _osascript(
        'tell application "Safari" to activate\n'
        'tell application "System Events"\n'
        'tell process "Safari"\n'
        'set frontmost to true\n'
        'keystroke "f" using {control down, command down}\n'
        'end tell\n'
        'end tell'
    )
    time.sleep(1.6)


def ensure_magma_canvas() -> str:
    _safari_activate()
    current_url = _safari_get_url()
    if "magma.com/d/" in current_url:
        _maximize()
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
    _maximize()
    return _safari_get_url()


def pixel_to_global(px: float, py: float) -> tuple[float, float]:
    primary = NSScreen.mainScreen()
    if primary is None:
        return (px, py)
    scale = primary.backingScaleFactor()
    frame = primary.frame()
    return (frame.origin.x + px / scale, frame.origin.y + py / scale)


def draw_stroke_global(points: list[tuple[float, float]], delay: float = 0.004) -> None:
    if len(points) < 2:
        return
    pts_global = [pixel_to_global(x, y) for x, y in points]
    start = pts_global[0]
    down = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseDown, Quartz.CGPointMake(start[0], start[1]), Quartz.kCGMouseButtonLeft)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, down)
    time.sleep(0.04)
    for px, py in pts_global[1:]:
        drag = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseDragged, Quartz.CGPointMake(px, py), Quartz.kCGMouseButtonLeft)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, drag)
        time.sleep(delay)
    end = pts_global[-1]
    up = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseUp, Quartz.CGPointMake(end[0], end[1]), Quartz.kCGMouseButtonLeft)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, up)
    time.sleep(0.08)


def smooth_curve(points: list[tuple[float, float]], n_per_seg: int = 12) -> list[tuple[float, float]]:
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


def oval_points(cx: float, cy: float, rx: float, ry: float, n: int = 40) -> list[tuple[float, float]]:
    return [(cx + rx * math.cos(2 * math.pi * i / n), cy + ry * math.sin(2 * math.pi * i / n)) for i in range(n + 1)]


def arc_points(cx: float, cy: float, rx: float, ry: float, start_deg: float, end_deg: float, n: int = 20) -> list[tuple[float, float]]:
    points = []
    for i in range(n + 1):
        t = i / n
        ang = math.radians(start_deg + (end_deg - start_deg) * t)
        points.append((cx + rx * math.cos(ang), cy + ry * math.sin(ang)))
    return points


def line(x1: float, y1: float, x2: float, y2: float) -> list[tuple[float, float]]:
    return [(x1, y1), (x2, y2)]


def build_tiger_strokes() -> list[list[tuple[float, float]]]:
    cx, cy = 1120.0, 720.0
    s: list[list[tuple[float, float]]] = []

    # Head silhouette and ears
    s.append(smooth_curve(oval_points(cx, cy - 175, 145, 150, 48), 4))
    s.append(smooth_curve(oval_points(cx - 90, cy - 300, 48, 62, 28), 4))
    s.append(smooth_curve(oval_points(cx + 90, cy - 300, 48, 62, 28), 4))
    s.append(smooth_curve(oval_points(cx - 90, cy - 300, 24, 32, 20), 4))
    s.append(smooth_curve(oval_points(cx + 90, cy - 300, 24, 32, 20), 4))

    # Face planes
    s.append(smooth_curve(oval_points(cx, cy - 118, 78, 56, 32), 4))
    s.append(smooth_curve(oval_points(cx - 42, cy - 190, 20, 14, 18), 4))
    s.append(smooth_curve(oval_points(cx + 42, cy - 190, 20, 14, 18), 4))
    s.append(smooth_curve([(cx, cy - 150), (cx - 18, cy - 124), (cx, cy - 110), (cx + 18, cy - 124), (cx, cy - 150)], 8))
    s.append(smooth_curve(line(cx, cy - 110, cx, cy - 78), 8))
    s.append(smooth_curve([(cx - 48, cy - 62), (cx - 22, cy - 42), (cx, cy - 38), (cx + 22, cy - 42), (cx + 48, cy - 62)], 8))

    # Whiskers
    for off in (-42, -18, 18, 42):
        s.append(smooth_curve(line(cx - 120, cy - 98 + off * 0.15, cx - 36, cy - 90 + off * 0.06), 6))
        s.append(smooth_curve(line(cx + 36, cy - 90 + off * 0.06, cx + 120, cy - 98 + off * 0.15), 6))

    # Tiger stripes on head
    stripe_specs = [(-86, -220, -56, -150), (-42, -245, -20, -162), (-10, -256, 0, -168), (10, -256, 0, -168), (42, -245, 20, -162), (86, -220, 56, -150)]
    for x1, y1, x2, y2 in stripe_specs:
        s.append(smooth_curve(line(cx + x1, cy + y1, cx + x2, cy + y2), 8))
    s.append(smooth_curve([(cx - 78, cy - 134), (cx - 102, cy - 112), (cx - 82, cy - 94)], 8))
    s.append(smooth_curve([(cx + 78, cy - 134), (cx + 102, cy - 112), (cx + 82, cy - 94)], 8))

    # Neck / shoulders / torso armor-fashion silhouette
    torso = [
        (cx - 170, cy - 8), (cx - 220, cy + 54), (cx - 246, cy + 138), (cx - 246, cy + 254),
        (cx - 214, cy + 370), (cx - 156, cy + 458), (cx - 98, cy + 518), (cx - 42, cy + 552),
        (cx + 42, cy + 552), (cx + 98, cy + 518), (cx + 156, cy + 458), (cx + 214, cy + 370),
        (cx + 246, cy + 254), (cx + 246, cy + 138), (cx + 220, cy + 54), (cx + 170, cy - 8),
        (cx + 96, cy - 48), (cx + 32, cy - 58), (cx - 32, cy - 58), (cx - 96, cy - 48), (cx - 170, cy - 8)
    ]
    s.append(smooth_curve(torso, 10))
    # Jacket lapels / shirt opening
    s.append(smooth_curve([(cx - 84, cy - 34), (cx - 24, cy + 118), (cx - 6, cy + 278)], 10))
    s.append(smooth_curve([(cx + 84, cy - 34), (cx + 24, cy + 118), (cx + 6, cy + 278)], 10))
    s.append(smooth_curve(line(cx, cy - 26, cx, cy + 396), 10))
    for yy in (68, 144, 220):
        s.append(smooth_curve(line(cx - 12, cy + yy, cx + 12, cy + yy), 8))

    # Iron Man inspired chest/pauldrons
    s.append(smooth_curve(oval_points(cx, cy + 102, 62, 62, 30), 4))  # arc reactor housing
    s.append(smooth_curve(oval_points(cx, cy + 102, 26, 26, 22), 4))
    s.append(smooth_curve([(cx - 138, cy + 10), (cx - 196, cy + 44), (cx - 216, cy + 106), (cx - 180, cy + 126), (cx - 124, cy + 76)], 8))
    s.append(smooth_curve([(cx + 138, cy + 10), (cx + 196, cy + 44), (cx + 216, cy + 106), (cx + 180, cy + 126), (cx + 124, cy + 76)], 8))
    s.append(smooth_curve(line(cx - 112, cy + 18, cx - 44, cy + 74), 8))
    s.append(smooth_curve(line(cx + 112, cy + 18, cx + 44, cy + 74), 8))

    # Ralph Lauren details
    s.append(smooth_curve(oval_points(cx + 92, cy + 40, 24, 24, 18), 4))  # RL medallion
    s.append(smooth_curve(line(cx + 82, cy + 54, cx + 96, cy + 18), 8))
    s.append(smooth_curve(line(cx + 96, cy + 18, cx + 108, cy + 34), 8))
    s.append(smooth_curve(line(cx + 84, cy + 40, cx + 106, cy + 40), 8))
    s.append(smooth_curve(oval_points(cx - 86, cy + 54, 18, 18, 16), 4))  # button/pin

    # Arms / gauntlets
    left_arm = [
        (cx - 170, cy + 50), (cx - 304, cy + 124), (cx - 378, cy + 232), (cx - 382, cy + 330),
        (cx - 348, cy + 430), (cx - 284, cy + 490), (cx - 214, cy + 470), (cx - 184, cy + 392),
        (cx - 194, cy + 302), (cx - 186, cy + 206), (cx - 170, cy + 50)
    ]
    right_arm = [
        (cx + 170, cy + 50), (cx + 304, cy + 124), (cx + 378, cy + 232), (cx + 382, cy + 330),
        (cx + 348, cy + 430), (cx + 284, cy + 490), (cx + 214, cy + 470), (cx + 184, cy + 392),
        (cx + 194, cy + 302), (cx + 186, cy + 206), (cx + 170, cy + 50)
    ]
    s.append(smooth_curve(left_arm, 10))
    s.append(smooth_curve(right_arm, 10))
    s.append(smooth_curve(line(cx - 270, cy + 404, cx - 198, cy + 376), 8))
    s.append(smooth_curve(line(cx + 270, cy + 404, cx + 198, cy + 376), 8))
    s.append(smooth_curve(oval_points(cx - 296, cy + 492, 28, 22, 20), 4))
    s.append(smooth_curve(oval_points(cx + 296, cy + 492, 28, 22, 20), 4))

    # Legs / boots / tail
    left_leg = [(cx - 86, cy + 552), (cx - 120, cy + 684), (cx - 130, cy + 842), (cx - 126, cy + 980)]
    right_leg = [(cx + 86, cy + 552), (cx + 120, cy + 684), (cx + 130, cy + 842), (cx + 126, cy + 980)]
    s.append(smooth_curve(left_leg, 10))
    s.append(smooth_curve(right_leg, 10))
    s.append(smooth_curve([(cx - 166, cy + 982), (cx - 54, cy + 982), (cx - 42, cy + 1032), (cx - 176, cy + 1032), (cx - 166, cy + 982)], 8))
    s.append(smooth_curve([(cx + 54, cy + 982), (cx + 166, cy + 982), (cx + 176, cy + 1032), (cx + 42, cy + 1032), (cx + 54, cy + 982)], 8))
    s.append(smooth_curve([(cx + 122, cy + 610), (cx + 212, cy + 660), (cx + 252, cy + 742), (cx + 236, cy + 820), (cx + 180, cy + 870)], 8))

    # Extra tiger body stripes and face detail
    body_stripes = [(-122, 140, -86, 178), (-158, 222, -100, 246), (-146, 308, -90, 332), (122, 140, 86, 178), (158, 222, 100, 246), (146, 308, 90, 332)]
    for x1, y1, x2, y2 in body_stripes:
        s.append(smooth_curve(line(cx + x1, cy + y1, cx + x2, cy + y2), 8))
    s.append(smooth_curve(line(cx - 66, cy - 182, cx - 28, cy - 172), 8))
    s.append(smooth_curve(line(cx + 28, cy - 172, cx + 66, cy - 182), 8))
    s.append(smooth_curve(line(cx - 18, cy - 184, cx - 4, cy - 172), 8))
    s.append(smooth_curve(line(cx + 4, cy - 172, cx + 18, cy - 184), 8))
    return s


def main() -> int:
    request = "Draw a tiger wearing Ralph Lauren-inspired fashion with Iron Man from Marvel comic design cues."
    board = build_generic_reference_board(
        request=request,
        primary_subject="tiger",
        anatomy_anchor="real tiger anatomy",
        style_anchor="Ralph Lauren fashion styling",
        identity_anchor="Iron Man Marvel comic armor cues",
        must_have_parts=[
            "tiger face with stripes and muzzle",
            "Ralph Lauren-inspired badge or fashion cue",
            "Iron Man-style chest reactor and armor seams",
            "full body visible on canvas",
        ],
        must_avoid=[
            "clipped figure",
            "generic bear silhouette",
            "unstyled plain black clothing",
        ],
    )
    board.save_split_artifacts(ROOT, "magma_tiger_rl_ironman")

    url = ensure_magma_canvas()
    print(f"[magma-tiger] url={url}")
    strokes = build_tiger_strokes()
    for idx, stroke in enumerate(strokes, 1):
        draw_stroke_global(stroke)
        if idx % 10 == 0:
            time.sleep(0.15)
    subprocess.run(["screencapture", "-x", str(FINAL_SCREENSHOT)], check=True)
    print(f"[done] {FINAL_SCREENSHOT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
