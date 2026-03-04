#!/usr/bin/env python3
"""Draw a stylized Polo-style polar bear in Black Panther Party-inspired clothing on JSPaint.

Uses live Safari geometry calibration from the actual front window screenshot so
Quartz strokes land on the real canvas instead of guessed coordinates.
"""

from __future__ import annotations

import json
import math
import subprocess
import time
from pathlib import Path

import Quartz
from art_geometry import normalize_strokes_to_canvas
from reference_board import build_polo_bear_panther_reference_board


ROOT = Path(__file__).resolve().parent
FINAL_SCREENSHOT = ROOT / "jspaint_polo_bear_panther_final.png"


def _osascript(script: str) -> str:
    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    return (result.stdout or "").strip()


def _safari_activate_and_open() -> None:
    subprocess.run(["open", "-a", "Safari", "https://jspaint.app/"], check=True, timeout=5)
    subprocess.run(["osascript", "-e", 'tell application "Safari" to activate'], check=True)
    time.sleep(3)


def _safari_bounds() -> tuple[int, int, int, int]:
    out = _osascript('tell application "Safari" to get bounds of front window')
    parts = [int(p.strip()) for p in out.split(",")]
    if len(parts) != 4:
        raise RuntimeError(f"Could not parse Safari bounds: {out!r}")
    return tuple(parts)  # type: ignore[return-value]


def _canvas_js_info() -> dict[str, float]:
    js = """
    (function(){
      const c = document.querySelectorAll('canvas')[0];
      if (!c) return '';
      const r = c.getBoundingClientRect();
      return JSON.stringify({
        url: location.href,
        title: document.title,
        width: c.width,
        height: c.height,
        left: r.left,
        top: r.top,
        right: r.right,
        bottom: r.bottom,
        cssWidth: r.width,
        cssHeight: r.height,
        screenX: window.screenX,
        screenY: window.screenY,
        outerWidth: window.outerWidth,
        outerHeight: window.outerHeight,
        innerWidth: window.innerWidth,
        innerHeight: window.innerHeight,
        dpr: window.devicePixelRatio || 1
      });
    })();
    """
    one_line = " ".join(js.split())
    escaped = one_line.replace("\\", "\\\\").replace('"', '\\"')
    out = _osascript(
        f'tell application "Safari" to do JavaScript "{escaped}" in current tab of front window'
    )
    if not out:
        raise RuntimeError("Safari canvas probe returned empty output")
    return json.loads(out)


def _clear_visible_canvas() -> None:
    js = """
    (function(){
      const c = document.querySelectorAll('canvas')[0];
      if (!c) return 'no_canvas';
      const ctx = c.getContext('2d');
      ctx.fillStyle = 'white';
      ctx.fillRect(0, 0, c.width, c.height);
      return 'ok';
    })();
    """
    one_line = " ".join(js.split())
    escaped = one_line.replace("\\", "\\\\").replace('"', '\\"')
    _osascript(f'tell application "Safari" to do JavaScript "{escaped}" in current tab of front window')

def _global_point(
    local_x: float,
    local_y: float,
    global_canvas_origin: tuple[float, float],
) -> tuple[float, float]:
    canvas_left, canvas_top = global_canvas_origin
    return (
        canvas_left + local_x,
        canvas_top + local_y,
    )


def _draw_stroke(
    points: list[tuple[float, float]],
    global_canvas_origin: tuple[float, float],
    delay: float = 0.006,
) -> None:
    if len(points) < 2:
        return
    gpoints = [_global_point(x, y, global_canvas_origin) for x, y in points]
    x0, y0 = gpoints[0]
    down = Quartz.CGEventCreateMouseEvent(
        None, Quartz.kCGEventLeftMouseDown, Quartz.CGPointMake(x0, y0), Quartz.kCGMouseButtonLeft
    )
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, down)
    time.sleep(0.05)
    for gx, gy in gpoints[1:]:
        drag = Quartz.CGEventCreateMouseEvent(
            None, Quartz.kCGEventLeftMouseDragged, Quartz.CGPointMake(gx, gy), Quartz.kCGMouseButtonLeft
        )
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, drag)
        time.sleep(delay)
    xe, ye = gpoints[-1]
    up = Quartz.CGEventCreateMouseEvent(
        None, Quartz.kCGEventLeftMouseUp, Quartz.CGPointMake(xe, ye), Quartz.kCGMouseButtonLeft
    )
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, up)
    time.sleep(0.11)


def _smooth(points: list[tuple[float, float]], n_per_seg: int = 10) -> list[tuple[float, float]]:
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


def _oval(cx: float, cy: float, rx: float, ry: float, n: int = 24) -> list[tuple[float, float]]:
    return [
        (cx + rx * math.cos(2 * math.pi * i / n), cy + ry * math.sin(2 * math.pi * i / n))
        for i in range(n + 1)
    ]


def _arc(cx: float, cy: float, rx: float, ry: float, start_deg: float, end_deg: float, n: int = 18) -> list[tuple[float, float]]:
    pts = []
    for i in range(n + 1):
        t = i / n
        ang = math.radians(start_deg + (end_deg - start_deg) * t)
        pts.append((cx + rx * math.cos(ang), cy + ry * math.sin(ang)))
    return pts


def _line(x1: float, y1: float, x2: float, y2: float) -> list[tuple[float, float]]:
    return [(x1, y1), (x2, y2)]


def _build_strokes(canvas_w: float, canvas_h: float) -> list[list[tuple[float, float]]]:
    cx = canvas_w * 0.50
    cy = canvas_h * 0.53
    strokes: list[list[tuple[float, float]]] = []

    # Beret and ears
    strokes.append(_smooth(_arc(cx - 18, cy - 120, 78, 22, 195, 348), 5))
    strokes.append(_smooth([(cx - 88, cy - 118), (cx - 40, cy - 150), (cx + 18, cy - 148), (cx + 42, cy - 118)], 8))
    strokes.append(_smooth(_oval(cx - 62, cy - 99, 15, 17, 18), 4))
    strokes.append(_smooth(_oval(cx + 52, cy - 96, 14, 16, 18), 4))

    # Head outline and muzzle
    head = [
        (cx - 76, cy - 78), (cx - 92, cy - 42), (cx - 92, cy + 8), (cx - 74, cy + 48),
        (cx - 42, cy + 74), (cx, cy + 82), (cx + 42, cy + 74), (cx + 74, cy + 48),
        (cx + 92, cy + 8), (cx + 92, cy - 42), (cx + 76, cy - 78), (cx + 38, cy - 98),
        (cx - 8, cy - 104), (cx - 46, cy - 98), (cx - 76, cy - 78),
    ]
    strokes.append(_smooth(head, 10))
    strokes.append(_smooth(_oval(cx, cy + 10, 38, 28, 20), 4))
    strokes.append(_smooth(_oval(cx, cy + 28, 12, 8, 14), 4))
    strokes.append(_smooth(_line(cx, cy + 34, cx, cy + 50), 8))
    strokes.append(_smooth([(cx - 18, cy + 54), (cx - 8, cy + 62), (cx, cy + 58), (cx + 8, cy + 62), (cx + 18, cy + 54)], 8))

    # Sunglasses and brows
    strokes.append(_smooth(_line(cx - 44, cy - 22, cx + 44, cy - 22), 8))
    strokes.append(_smooth(_oval(cx - 28, cy - 22, 20, 12, 18), 4))
    strokes.append(_smooth(_oval(cx + 28, cy - 22, 20, 12, 18), 4))
    strokes.append(_smooth(_line(cx - 6, cy - 22, cx + 6, cy - 22), 8))
    strokes.append(_smooth(_arc(cx - 28, cy - 36, 16, 6, 205, 335), 4))
    strokes.append(_smooth(_arc(cx + 28, cy - 36, 16, 6, 205, 335), 4))

    # Torso jacket
    torso = [
        (cx - 88, cy + 92), (cx - 108, cy + 150), (cx - 102, cy + 232), (cx - 78, cy + 284),
        (cx - 38, cy + 322), (cx - 2, cy + 330), (cx + 36, cy + 322), (cx + 78, cy + 284),
        (cx + 102, cy + 232), (cx + 108, cy + 150), (cx + 88, cy + 92), (cx + 54, cy + 66),
        (cx + 18, cy + 56), (cx - 18, cy + 56), (cx - 54, cy + 66), (cx - 88, cy + 92),
    ]
    strokes.append(_smooth(torso, 10))
    strokes.append(_smooth([(cx - 58, cy + 70), (cx - 26, cy + 138), (cx - 6, cy + 182)], 10))
    strokes.append(_smooth([(cx + 58, cy + 70), (cx + 26, cy + 138), (cx + 6, cy + 182)], 10))
    strokes.append(_smooth(_line(cx, cy + 58, cx, cy + 250), 10))
    for dy in (104, 132, 160):
        strokes.append(_smooth(_line(cx - 8, cy + dy, cx + 8, cy + dy), 8))

    # Shirt panel and pocket seams
    for dy in (102, 120, 138, 156):
        strokes.append(_smooth(_line(cx - 18, cy + dy, cx + 18, cy + dy), 8))
    strokes.append(_smooth([(cx - 72, cy + 168), (cx - 42, cy + 154), (cx - 30, cy + 176), (cx - 60, cy + 188), (cx - 72, cy + 168)], 8))
    strokes.append(_smooth([(cx + 72, cy + 168), (cx + 42, cy + 154), (cx + 30, cy + 176), (cx + 60, cy + 188), (cx + 72, cy + 168)], 8))

    # Arms and paws
    left_arm = [
        (cx - 86, cy + 102), (cx - 132, cy + 140), (cx - 156, cy + 188), (cx - 154, cy + 236),
        (cx - 138, cy + 272), (cx - 110, cy + 286), (cx - 92, cy + 272), (cx - 90, cy + 232),
        (cx - 98, cy + 188), (cx - 92, cy + 140), (cx - 86, cy + 102),
    ]
    right_arm = [
        (cx + 86, cy + 102), (cx + 132, cy + 140), (cx + 156, cy + 188), (cx + 154, cy + 236),
        (cx + 138, cy + 272), (cx + 110, cy + 286), (cx + 92, cy + 272), (cx + 90, cy + 232),
        (cx + 98, cy + 188), (cx + 92, cy + 140), (cx + 86, cy + 102),
    ]
    strokes.append(_smooth(left_arm, 10))
    strokes.append(_smooth(right_arm, 10))
    strokes.append(_smooth(_oval(cx - 118, cy + 286, 18, 13, 16), 4))
    strokes.append(_smooth(_oval(cx + 118, cy + 286, 18, 13, 16), 4))

    # Lower body and boots
    strokes.append(_smooth([(cx - 42, cy + 330), (cx - 48, cy + 392), (cx - 50, cy + 462)], 10))
    strokes.append(_smooth([(cx - 8, cy + 330), (cx - 10, cy + 392), (cx - 10, cy + 462)], 10))
    strokes.append(_smooth([(cx + 8, cy + 330), (cx + 10, cy + 392), (cx + 10, cy + 462)], 10))
    strokes.append(_smooth([(cx + 42, cy + 330), (cx + 48, cy + 392), (cx + 50, cy + 462)], 10))
    strokes.append(_smooth([(cx - 66, cy + 462), (cx - 4, cy + 462), (cx + 4, cy + 478), (cx - 74, cy + 480), (cx - 66, cy + 462)], 8))
    strokes.append(_smooth([(cx + 4, cy + 462), (cx + 66, cy + 462), (cx + 74, cy + 480), (cx - 4, cy + 478), (cx + 4, cy + 462)], 8))

    # Fur and clothing detail
    for dx in (-60, -44, -28, 28, 44, 60):
        strokes.append(_smooth(_line(cx + dx, cy - 88, cx + dx * 0.82, cy - 66), 6))
    for dy in (0, 18, 34):
        strokes.append(_smooth(_line(cx - 22, cy + dy, cx + 22, cy + dy), 8))
    strokes.append(_smooth(_line(cx - 34, cy + 254, cx + 34, cy + 254), 8))
    strokes.append(_smooth(_line(cx - 24, cy + 254, cx - 24, cy + 286), 8))
    strokes.append(_smooth(_line(cx + 24, cy + 254, cx + 24, cy + 286), 8))

    return strokes


def main() -> None:
    ref_board = build_polo_bear_panther_reference_board()
    written = ref_board.save_split_artifacts(ROOT, "jspaint_polo_bear_panther")
    print(f"[jspaint] reference_board={written['reference_board']}")
    _safari_activate_and_open()
    time.sleep(1.0)
    safari_bounds = _safari_bounds()
    canvas_info = _canvas_js_info()
    _clear_visible_canvas()
    time.sleep(0.2)
    x1, y1, x2, y2 = safari_bounds
    ax_w = x2 - x1
    ax_h = y2 - y1
    chrome_left_pt = max(0.0, (ax_w - canvas_info["innerWidth"]) / 2.0)
    chrome_top_pt = max(0.0, ax_h - canvas_info["innerHeight"])
    global_canvas_origin = (
        x1 + chrome_left_pt + canvas_info["left"],
        y1 + chrome_top_pt + canvas_info["top"],
    )
    canvas_w_pt = canvas_info["cssWidth"]
    canvas_h_pt = canvas_info["cssHeight"]

    print(f"[jspaint] url={canvas_info['url']}")
    print(f"[jspaint] bounds={safari_bounds}")
    print(f"[jspaint] window_metrics=(outer={canvas_info['outerWidth']}x{canvas_info['outerHeight']}, inner={canvas_info['innerWidth']}x{canvas_info['innerHeight']}, dpr={canvas_info['dpr']})")
    print(f"[jspaint] chrome_offsets_pt=(left={chrome_left_pt:.1f}, top={chrome_top_pt:.1f})")
    print(f"[jspaint] canvas_origin_pt=({global_canvas_origin[0]:.1f}, {global_canvas_origin[1]:.1f})")
    print(f"[jspaint] canvas_size_pt=({canvas_w_pt:.1f}, {canvas_h_pt:.1f})")

    strokes = _build_strokes(canvas_w_pt, canvas_h_pt)
    strokes = normalize_strokes_to_canvas(
        strokes,
        canvas_w_pt,
        canvas_h_pt,
        margin_ratio_x=0.10,
        margin_ratio_top=0.08,
        margin_ratio_bottom=0.06,
    )
    for idx, stroke in enumerate(strokes, start=1):
        _draw_stroke(stroke, global_canvas_origin, delay=0.005 if len(stroke) > 12 else 0.007)
        if idx % 6 == 0:
            time.sleep(0.2)

    time.sleep(1.2)
    subprocess.run(["screencapture", "-x", str(FINAL_SCREENSHOT)], check=True)
    print(f"[done] {FINAL_SCREENSHOT}")


if __name__ == "__main__":
    main()
