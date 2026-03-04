#!/usr/bin/env python3
"""Draw a tiger in Ralph Lauren-inspired Iron Man fashion on JSPaint using visible cursor strokes."""

from __future__ import annotations

import json
import math
import subprocess
import time
from pathlib import Path

import Quartz

from art_geometry import normalize_strokes_to_canvas
from reference_board import build_generic_reference_board

ROOT = Path(__file__).resolve().parent
FINAL_SCREENSHOT = ROOT / "jspaint_tiger_rl_ironman_final.png"

BLACK = "rgb(0,0,0)"
RED = "rgb(255,0,0)"
GOLD = "rgb(255,255,0)"
ORANGE = "rgb(255,128,64)"
BROWN = "rgb(128,64,0)"


def _osascript(script: str) -> str:
    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True,
        timeout=25,
        check=False,
    )
    return (result.stdout or "").strip()


def _safari_activate_and_open() -> None:
    subprocess.run(["open", "-a", "Safari", "https://jspaint.app/"], check=True, timeout=5)
    subprocess.run(["osascript", "-e", 'tell application "Safari" to activate'], check=True)
    time.sleep(3)


def _maximize_safari() -> None:
    script = '''
    tell application "Safari" to activate
    tell application "System Events"
      tell process "Safari"
        try
          click menu item "Fill" of menu "Window" of menu bar 1
        end try
      end tell
    end tell
    '''
    _osascript(script)
    time.sleep(0.8)


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


def _palette_info() -> dict[str, tuple[float, float]]:
    js = """
    (function(){
      return JSON.stringify(
        Array.from(document.querySelectorAll('.swatch.color-button')).map((el) => {
          const r = el.getBoundingClientRect();
          return {
            color: el.getAttribute('data-color'),
            cx: r.left + r.width / 2,
            cy: r.top + r.height / 2
          };
        })
      );
    })();
    """
    one_line = " ".join(js.split())
    escaped = one_line.replace("\\", "\\\\").replace('"', '\\"')
    out = _osascript(
        f'tell application "Safari" to do JavaScript "{escaped}" in current tab of front window'
    )
    if not out:
        raise RuntimeError("Safari palette probe returned empty output")
    payload = json.loads(out)
    return {entry["color"]: (float(entry["cx"]), float(entry["cy"])) for entry in payload}


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


def _global_point(local_x: float, local_y: float, global_origin: tuple[float, float]) -> tuple[float, float]:
    return (global_origin[0] + local_x, global_origin[1] + local_y)


def _click_global(global_pt: tuple[float, float]) -> None:
    x, y = global_pt
    down = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseDown, Quartz.CGPointMake(x, y), Quartz.kCGMouseButtonLeft)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, down)
    time.sleep(0.03)
    up = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseUp, Quartz.CGPointMake(x, y), Quartz.kCGMouseButtonLeft)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, up)
    time.sleep(0.15)


def _select_color(color: str, global_origin: tuple[float, float], palette_info: dict[str, tuple[float, float]]) -> None:
    if color not in palette_info:
        raise KeyError(f"Palette color unavailable: {color}")
    _click_global(_global_point(*palette_info[color], global_origin))


def _draw_stroke(points: list[tuple[float, float]], global_canvas_origin: tuple[float, float], delay: float = 0.004) -> None:
    if len(points) < 2:
        return
    gpoints = [_global_point(x, y, global_canvas_origin) for x, y in points]
    x0, y0 = gpoints[0]
    down = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseDown, Quartz.CGPointMake(x0, y0), Quartz.kCGMouseButtonLeft)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, down)
    time.sleep(0.045)
    for gx, gy in gpoints[1:]:
        drag = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseDragged, Quartz.CGPointMake(gx, gy), Quartz.kCGMouseButtonLeft)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, drag)
        time.sleep(delay)
    xe, ye = gpoints[-1]
    up = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseUp, Quartz.CGPointMake(xe, ye), Quartz.kCGMouseButtonLeft)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, up)
    time.sleep(0.08)


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


def _oval(cx: float, cy: float, rx: float, ry: float, n: int = 30) -> list[tuple[float, float]]:
    return [
        (cx + rx * math.cos(2 * math.pi * i / n), cy + ry * math.sin(2 * math.pi * i / n))
        for i in range(n + 1)
    ]


def _line(x1: float, y1: float, x2: float, y2: float) -> list[tuple[float, float]]:
    return [(x1, y1), (x2, y2)]


def _arc(cx: float, cy: float, rx: float, ry: float, start_deg: float, end_deg: float, n: int = 20) -> list[tuple[float, float]]:
    pts = []
    for i in range(n + 1):
        t = i / n
        ang = math.radians(start_deg + (end_deg - start_deg) * t)
        pts.append((cx + rx * math.cos(ang), cy + ry * math.sin(ang)))
    return pts


def _scanline_fill(points: list[tuple[float, float]], step: float = 10.0) -> list[list[tuple[float, float]]]:
    ys = [p[1] for p in points]
    min_y = min(ys)
    max_y = max(ys)
    strokes: list[list[tuple[float, float]]] = []
    y = min_y
    while y <= max_y:
        intersections: list[float] = []
        for i in range(len(points)):
            x1, y1 = points[i]
            x2, y2 = points[(i + 1) % len(points)]
            if y1 == y2:
                continue
            if (y1 <= y < y2) or (y2 <= y < y1):
                t = (y - y1) / (y2 - y1)
                intersections.append(x1 + t * (x2 - x1))
        intersections.sort()
        for i in range(0, len(intersections) - 1, 2):
            strokes.append([(intersections[i], y), (intersections[i + 1], y)])
        y += step
    return strokes


def _ellipse_fill(cx: float, cy: float, rx: float, ry: float, step: float = 10.0) -> list[list[tuple[float, float]]]:
    strokes: list[list[tuple[float, float]]] = []
    y = cy - ry
    while y <= cy + ry:
        rel = (y - cy) / ry
        inside = max(0.0, 1.0 - rel * rel)
        x_extent = rx * math.sqrt(inside)
        strokes.append([(cx - x_extent, y), (cx + x_extent, y)])
        y += step
    return strokes


def _build_groups() -> list[tuple[str, list[list[tuple[float, float]]]]]:
    cx = 500.0
    head_cy = 175.0
    body_top = 310.0
    groups: list[tuple[str, list[list[tuple[float, float]]]]] = []

    orange_strokes: list[list[tuple[float, float]]] = []
    red_strokes: list[list[tuple[float, float]]] = []
    gold_strokes: list[list[tuple[float, float]]] = []
    brown_strokes: list[list[tuple[float, float]]] = []
    black_strokes: list[list[tuple[float, float]]] = []

    # Filled regions
    orange_strokes += _ellipse_fill(cx, head_cy, 118, 108, 11)
    orange_strokes += _ellipse_fill(cx - 74, head_cy - 83, 34, 40, 9)
    orange_strokes += _ellipse_fill(cx + 74, head_cy - 83, 34, 40, 9)
    orange_strokes += _scanline_fill([(680, 670), (740, 640), (790, 670), (820, 720), (760, 745), (690, 726)], 10)

    red_torso = [(320, body_top), (680, body_top), (735, 515), (655, 760), (345, 760), (265, 515)]
    red_left_arm = [(315, 335), (170, 420), (130, 585), (225, 670), (340, 620)]
    red_right_arm = [(685, 335), (830, 420), (870, 585), (775, 670), (660, 620)]
    red_left_leg = [(410, 760), (355, 970), (455, 970), (490, 760)]
    red_right_leg = [(590, 760), (545, 970), (645, 970), (610, 760)]
    red_boot_l = [(335, 970), (470, 970), (492, 1010), (320, 1010)]
    red_boot_r = [(530, 970), (665, 970), (680, 1010), (508, 1010)]
    for poly in (red_torso, red_left_arm, red_right_arm, red_left_leg, red_right_leg, red_boot_l, red_boot_r):
        red_strokes += _scanline_fill(poly, 11)

    gold_shoulder_l = [(312, 318), (220, 372), (282, 430), (365, 370)]
    gold_shoulder_r = [(688, 318), (780, 372), (718, 430), (635, 370)]
    gold_mask = [(440, 118), (470, 104), (530, 104), (560, 118), (545, 160), (455, 160)]
    gold_reactor = _ellipse_fill(cx, 500, 40, 40, 8)
    gold_badge = _ellipse_fill(585, 395, 26, 24, 7)
    gold_cuffs_l = [(190, 598), (265, 620), (250, 665), (175, 648)]
    gold_cuffs_r = [(735, 620), (810, 598), (825, 648), (750, 665)]
    for poly in (gold_shoulder_l, gold_shoulder_r, gold_mask, gold_cuffs_l, gold_cuffs_r):
        gold_strokes += _scanline_fill(poly, 9)
    gold_strokes += gold_reactor
    gold_strokes += gold_badge

    # Optional darker accents
    brown_strokes += _scanline_fill([(460, 214), (540, 214), (530, 260), (470, 260)], 8)

    # Outlines and detail
    black_strokes.append(_smooth(_oval(cx, head_cy, 118, 108), 5))
    black_strokes.append(_smooth(_oval(cx - 74, head_cy - 83, 34, 40), 5))
    black_strokes.append(_smooth(_oval(cx + 74, head_cy - 83, 34, 40), 5))
    black_strokes.append(_smooth(_oval(cx - 34, 170, 22, 14), 4))
    black_strokes.append(_smooth(_oval(cx + 34, 170, 22, 14), 4))
    black_strokes.append(_smooth(_line(cx - 12, 170, cx + 12, 170), 6))
    black_strokes.append(_smooth(_oval(cx, 232, 64, 44), 5))
    black_strokes.append(_smooth(_line(cx, 234, cx, 260), 6))
    black_strokes.append(_smooth([(cx - 22, 270), (cx - 10, 280), (cx, 276), (cx + 10, 280), (cx + 22, 270)], 6))
    for dx in (-54, -24, 0, 24, 54):
        black_strokes.append(_smooth(_line(cx + dx, 108, cx + dx * 0.85, 148), 6))
    # tiger stripes
    stripe_sets = [
        [(420, 160), (380, 190), (405, 212)],
        [(580, 160), (620, 190), (595, 212)],
        [(447, 205), (415, 232), (438, 252)],
        [(553, 205), (585, 232), (562, 252)],
        [(476, 118), (454, 148), (474, 172)],
        [(524, 118), (546, 148), (526, 172)],
    ]
    for stripe in stripe_sets:
        black_strokes.append(_smooth(stripe, 8))
    # whiskers
    for yoff in (228, 242, 255):
        black_strokes.append(_smooth(_line(430, yoff, 370, yoff - 10), 5))
        black_strokes.append(_smooth(_line(570, yoff, 630, yoff - 10), 5))

    for poly in (red_torso, red_left_arm, red_right_arm, red_left_leg, red_right_leg, red_boot_l, red_boot_r,
                 gold_shoulder_l, gold_shoulder_r, gold_mask, gold_cuffs_l, gold_cuffs_r):
        black_strokes.append(_smooth(poly + [poly[0]], 7))
    black_strokes.append(_smooth(_oval(cx, 500, 40, 40), 5))
    black_strokes.append(_smooth(_oval(585, 395, 26, 24), 5))
    black_strokes.append(_smooth(_line(500, 335, 500, 748), 10))
    for y in (400, 455, 510, 565):
        black_strokes.append(_smooth(_line(486, y, 514, y), 6))
    black_strokes.append(_smooth([(392, 365), (455, 470), (500, 610)], 10))
    black_strokes.append(_smooth([(608, 365), (545, 470), (500, 610)], 10))
    black_strokes.append(_smooth([(362, 405), (430, 382), (445, 430), (376, 452), (362, 405)], 8))
    black_strokes.append(_smooth([(638, 405), (570, 382), (555, 430), (624, 452), (638, 405)], 8))
    black_strokes.append(_smooth(_line(575, 396, 597, 396), 5))
    black_strokes.append(_smooth(_line(586, 384, 586, 408), 5))
    black_strokes.append(_smooth([(680, 670), (740, 640), (790, 670), (820, 720), (760, 745), (690, 726), (680, 670)], 8))
    for y in (685, 702, 720):
        black_strokes.append(_smooth(_line(710, y, 780, y - 6), 5))

    groups.append((ORANGE, orange_strokes))
    groups.append((RED, red_strokes))
    groups.append((GOLD, gold_strokes))
    groups.append((BROWN, brown_strokes))
    groups.append((BLACK, black_strokes))
    return groups


def main() -> None:
    board = build_generic_reference_board(
        request="Draw a tiger wearing Ralph Lauren everything inspired by Iron Man from Marvel comics.",
        primary_subject="tiger",
        anatomy_anchor="tiger anatomy",
        identity_anchor="Ralph Lauren Polo visual identity",
        style_anchor="Iron Man armor from Marvel comics",
        must_have_parts=[
            "full tiger figure",
            "recognizable tiger face and stripes",
            "Ralph Lauren style cue or badge",
            "red and gold Iron Man inspired armor tailoring",
            "full body inside canvas",
        ],
        must_avoid=[
            "canvas clipping",
            "generic cat drift",
            "non-tiger facial structure",
            "missing red/gold Iron Man palette",
        ],
        style_notes=[
            "Use tiger anatomy first, fashion/armor second.",
            "Keep the silhouette readable from a distance.",
            "Use red-gold armor fashion cues, not a literal Iron Man copy.",
        ],
        pose="heroic front-facing standing pose with broad shoulders and grounded boots",
        camera_angle="straight-on poster composition",
        passes=["base color masses", "armor fills", "outline and stripes", "detail verification"],
    )
    written = board.save_split_artifacts(ROOT, "jspaint_tiger_rl_ironman")
    print(f"[jspaint-tiger] reference_board={written['reference_board']}")

    _safari_activate_and_open()
    _maximize_safari()
    time.sleep(1.0)
    safari_bounds = _safari_bounds()
    canvas_info = _canvas_js_info()
    palette_info = _palette_info()
    _clear_visible_canvas()
    time.sleep(0.3)

    x1, y1, x2, y2 = safari_bounds
    ax_w = x2 - x1
    ax_h = y2 - y1
    chrome_left_pt = max(0.0, (ax_w - canvas_info["innerWidth"]) / 2.0)
    chrome_top_pt = max(0.0, ax_h - canvas_info["innerHeight"])
    global_canvas_origin = (
        x1 + chrome_left_pt + canvas_info["left"],
        y1 + chrome_top_pt + canvas_info["top"],
    )
    global_window_origin = (x1 + chrome_left_pt, y1 + chrome_top_pt)
    canvas_w_pt = float(canvas_info["cssWidth"])
    canvas_h_pt = float(canvas_info["cssHeight"])

    print(f"[jspaint-tiger] url={canvas_info['url']}")
    print(f"[jspaint-tiger] bounds={safari_bounds}")
    print(f"[jspaint-tiger] canvas_origin_pt=({global_canvas_origin[0]:.1f}, {global_canvas_origin[1]:.1f})")
    print(f"[jspaint-tiger] canvas_size_pt=({canvas_w_pt:.1f}, {canvas_h_pt:.1f})")

    groups = _build_groups()
    # normalize each color group's strokes together to keep the composition aligned
    all_strokes = [stroke for _, strokes in groups for stroke in strokes]
    normalized_all = normalize_strokes_to_canvas(
        all_strokes,
        canvas_w_pt,
        canvas_h_pt,
        margin_ratio_x=0.12,
        margin_ratio_top=0.05,
        margin_ratio_bottom=0.05,
    )
    cursor = 0
    normalized_groups: list[tuple[str, list[list[tuple[float, float]]]]] = []
    for color, strokes in groups:
        group_norm = normalized_all[cursor: cursor + len(strokes)]
        normalized_groups.append((color, group_norm))
        cursor += len(strokes)

    for color, strokes in normalized_groups:
        _select_color(color, global_window_origin, palette_info)
        for idx, stroke in enumerate(strokes, start=1):
            _draw_stroke(stroke, global_canvas_origin, delay=0.0038 if len(stroke) > 12 else 0.0048)
            if idx % 14 == 0:
                time.sleep(0.12)
        time.sleep(0.18)

    time.sleep(1.2)
    subprocess.run(["screencapture", "-x", str(FINAL_SCREENSHOT)], check=True)
    print(f"[done] {FINAL_SCREENSHOT}")


if __name__ == "__main__":
    main()
