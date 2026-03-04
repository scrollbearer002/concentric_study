#!/usr/bin/env python3
"""Draw a smaller, more detailed tiger in Ralph Lauren-inspired Iron Man fashion on JSPaint using visible cursor strokes."""

from __future__ import annotations

import json
import math
import subprocess
import time
from pathlib import Path

import Quartz

from art_geometry import strokes_bbox
from reference_board import build_generic_reference_board

ROOT = Path(__file__).resolve().parent
FINAL_SCREENSHOT = ROOT / "jspaint_tiger_rl_ironman_v2_final.png"

BLACK = "rgb(0,0,0)"
RED = "rgb(255,0,0)"
GOLD = "rgb(255,255,0)"
ORANGE = "rgb(255,128,64)"
BROWN = "rgb(128,64,0)"
SILVER = "rgb(192,192,192)"
CYAN = "rgb(0,255,255)"
WHITE = "rgb(255,255,255)"


def _osascript(script: str) -> str:
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=25, check=False)
    return (result.stdout or "").strip()


def _do_js(js: str) -> str:
    one_line = " ".join(js.split())
    escaped = one_line.replace("\\", "\\\\").replace('"', '\\"')
    return _osascript(f'tell application "Safari" to do JavaScript "{escaped}" in current tab of front window')


def _safari_open() -> None:
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


def _canvas_info() -> dict[str, float]:
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
    out = _do_js(js)
    if not out:
        raise RuntimeError("missing canvas info")
    return json.loads(out)


def _palette_info() -> dict[str, tuple[float, float]]:
    js = """
    (function(){
      return JSON.stringify(Array.from(document.querySelectorAll('.swatch.color-button')).map((el)=>{
        const r = el.getBoundingClientRect();
        return {color: el.getAttribute('data-color'), cx: r.left + r.width/2, cy: r.top + r.height/2};
      }));
    })();
    """
    payload = json.loads(_do_js(js))
    return {entry['color']: (float(entry['cx']), float(entry['cy'])) for entry in payload}


def _tool_info() -> dict[str, tuple[float, float]]:
    js = """
    (function(){
      return JSON.stringify(Array.from(document.querySelectorAll('.tool')).map((el)=>{
        const r = el.getBoundingClientRect();
        return {title: el.title, cx: r.left + r.width/2, cy: r.top + r.height/2};
      }));
    })();
    """
    payload = json.loads(_do_js(js))
    return {entry['title']: (float(entry['cx']), float(entry['cy'])) for entry in payload}


def _clear_canvas() -> None:
    _do_js("""
    (function(){
      const c = document.querySelectorAll('canvas')[0];
      if (!c) return 'no_canvas';
      const ctx = c.getContext('2d');
      ctx.fillStyle = 'white';
      ctx.fillRect(0,0,c.width,c.height);
      return 'ok';
    })();
    """)


def _global_point(local_x: float, local_y: float, global_origin: tuple[float, float]) -> tuple[float, float]:
    return global_origin[0] + local_x, global_origin[1] + local_y


def _click(pt: tuple[float, float]) -> None:
    x, y = pt
    down = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseDown, Quartz.CGPointMake(x, y), Quartz.kCGMouseButtonLeft)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, down)
    time.sleep(0.03)
    up = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseUp, Quartz.CGPointMake(x, y), Quartz.kCGMouseButtonLeft)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, up)
    time.sleep(0.10)


def _choose_tool(title: str, global_window_origin: tuple[float, float], tool_info: dict[str, tuple[float, float]]) -> None:
    if title not in tool_info:
        raise KeyError(f"tool not found: {title}")
    _click(_global_point(*tool_info[title], global_window_origin))


def _choose_color(color: str, global_window_origin: tuple[float, float], palette_info: dict[str, tuple[float, float]]) -> None:
    if color not in palette_info:
        raise KeyError(f"color not found: {color}")
    _click(_global_point(*palette_info[color], global_window_origin))


def _draw_stroke(points: list[tuple[float, float]], global_canvas_origin: tuple[float, float], delay: float = 0.004) -> None:
    if len(points) < 2:
        return
    gpoints = [_global_point(x, y, global_canvas_origin) for x, y in points]
    x0, y0 = gpoints[0]
    down = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseDown, Quartz.CGPointMake(x0, y0), Quartz.kCGMouseButtonLeft)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, down)
    time.sleep(0.04)
    for gx, gy in gpoints[1:]:
        drag = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseDragged, Quartz.CGPointMake(gx, gy), Quartz.kCGMouseButtonLeft)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, drag)
        time.sleep(delay)
    xe, ye = gpoints[-1]
    up = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseUp, Quartz.CGPointMake(xe, ye), Quartz.kCGMouseButtonLeft)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, up)
    time.sleep(0.05)


def _smooth(points: list[tuple[float, float]], n_per_seg: int = 8) -> list[tuple[float, float]]:
    if len(points) < 2:
        return points
    out = [points[0]]
    for i in range(len(points)-1):
        ax, ay = points[i]
        bx, by = points[i+1]
        for k in range(1, n_per_seg + 1):
            t = k / n_per_seg
            out.append((ax + (bx-ax)*t, ay + (by-ay)*t))
    return out


def _oval(cx: float, cy: float, rx: float, ry: float, n: int = 30) -> list[tuple[float, float]]:
    return [(cx + rx*math.cos(2*math.pi*i/n), cy + ry*math.sin(2*math.pi*i/n)) for i in range(n+1)]


def _line(x1: float, y1: float, x2: float, y2: float) -> list[tuple[float, float]]:
    return [(x1, y1), (x2, y2)]


def _arc(cx: float, cy: float, rx: float, ry: float, start_deg: float, end_deg: float, n: int = 20) -> list[tuple[float, float]]:
    pts = []
    for i in range(n + 1):
        t = i / n
        ang = math.radians(start_deg + (end_deg - start_deg) * t)
        pts.append((cx + rx * math.cos(ang), cy + ry * math.sin(ang)))
    return pts


def _transform_groups(groups: list[tuple[str, list[dict[str, object]]]], canvas_w: float, canvas_h: float) -> list[tuple[str, list[dict[str, object]]]]:
    all_strokes: list[list[tuple[float, float]]] = []
    for _, items in groups:
        for item in items:
            all_strokes.append(item['points'])  # type: ignore[arg-type]
    min_x, min_y, max_x, max_y = strokes_bbox(all_strokes)
    bbox_w = max_x - min_x
    bbox_h = max_y - min_y
    left_margin = canvas_w * 0.20
    right_margin = canvas_w * 0.20
    top_margin = canvas_h * 0.05
    bottom_margin = canvas_h * 0.09
    usable_w = canvas_w - left_margin - right_margin
    usable_h = canvas_h - top_margin - bottom_margin
    scale = min(usable_w / bbox_w, usable_h / bbox_h)
    target_min_x = left_margin + (usable_w - bbox_w * scale) / 2.0
    target_min_y = top_margin + (usable_h - bbox_h * scale) / 2.0

    def tx(p: tuple[float, float]) -> tuple[float, float]:
        return (target_min_x + (p[0] - min_x) * scale, target_min_y + (p[1] - min_y) * scale)

    transformed: list[tuple[str, list[dict[str, object]]]] = []
    for color, items in groups:
        out_items: list[dict[str, object]] = []
        for item in items:
            points = [tx(p) for p in item['points']]  # type: ignore[index]
            out: dict[str, object] = {'points': points, 'kind': item['kind']}  # type: ignore[index]
            if 'fill_point' in item:
                out['fill_point'] = tx(item['fill_point'])  # type: ignore[index]
            out_items.append(out)
        transformed.append((color, out_items))
    return transformed


def _build_groups() -> list[tuple[str, list[dict[str, object]]]]:
    cx = 500.0
    head_y = 220.0
    body_y = 430.0
    groups: list[tuple[str, list[dict[str, object]]]] = []

    orange: list[dict[str, object]] = []
    red: list[dict[str, object]] = []
    gold: list[dict[str, object]] = []
    silver: list[dict[str, object]] = []
    black: list[dict[str, object]] = []
    cyan: list[dict[str, object]] = []

    head = _smooth(_oval(cx, head_y, 120, 106), 4)
    left_ear = _smooth(_oval(cx - 70, head_y - 88, 30, 38), 4)
    right_ear = _smooth(_oval(cx + 70, head_y - 88, 30, 38), 4)
    muzzle = _smooth(_oval(cx, head_y + 48, 58, 38), 4)
    torso = _smooth([(350, body_y), (650, body_y), (715, 575), (655, 790), (345, 790), (285, 575), (350, body_y)], 8)
    left_arm = _smooth([(345, 468), (210, 525), (185, 685), (270, 752), (350, 680), (345, 468)], 8)
    right_arm = _smooth([(655, 468), (790, 525), (815, 685), (730, 752), (650, 680), (655, 468)], 8)
    left_leg = _smooth([(420, 790), (380, 1020), (470, 1020), (500, 790), (420, 790)], 8)
    right_leg = _smooth([(580, 790), (530, 1020), (620, 1020), (580, 790)], 8)
    left_boot = _smooth([(355, 1020), (485, 1020), (505, 1055), (340, 1055), (355, 1020)], 8)
    right_boot = _smooth([(515, 1020), (645, 1020), (660, 1055), (495, 1055), (515, 1020)], 8)
    left_shoulder = _smooth([(346, 430), (260, 470), (315, 532), (392, 482), (346, 430)], 8)
    right_shoulder = _smooth([(654, 430), (740, 470), (685, 532), (608, 482), (654, 430)], 8)
    tail = _smooth([(678, 760), (745, 722), (798, 748), (824, 804), (782, 832), (712, 812), (678, 760)], 8)
    faceplate = _smooth([(445, 158), (470, 130), (530, 130), (555, 158), (542, 205), (458, 205), (445, 158)], 8)
    badge = _smooth(_oval(590, 505, 24, 22), 4)
    reactor = _smooth(_oval(500, 555, 36, 36), 4)

    orange += [
        {'kind': 'closed', 'points': head, 'fill_point': (500, 220)},
        {'kind': 'closed', 'points': left_ear, 'fill_point': (430, 132)},
        {'kind': 'closed', 'points': right_ear, 'fill_point': (570, 132)},
        {'kind': 'closed', 'points': tail, 'fill_point': (770, 790)},
    ]
    silver += [
        {'kind': 'closed', 'points': muzzle, 'fill_point': (500, 268)},
    ]
    red += [
        {'kind': 'closed', 'points': torso, 'fill_point': (500, 590)},
        {'kind': 'closed', 'points': left_arm, 'fill_point': (255, 610)},
        {'kind': 'closed', 'points': right_arm, 'fill_point': (745, 610)},
        {'kind': 'closed', 'points': left_leg, 'fill_point': (430, 930)},
        {'kind': 'closed', 'points': right_leg, 'fill_point': (570, 930)},
        {'kind': 'closed', 'points': left_boot, 'fill_point': (430, 1040)},
        {'kind': 'closed', 'points': right_boot, 'fill_point': (575, 1040)},
    ]
    gold += [
        {'kind': 'closed', 'points': left_shoulder, 'fill_point': (325, 478)},
        {'kind': 'closed', 'points': right_shoulder, 'fill_point': (675, 478)},
        {'kind': 'closed', 'points': faceplate, 'fill_point': (500, 165)},
        {'kind': 'closed', 'points': badge, 'fill_point': (590, 505)},
    ]
    cyan += [
        {'kind': 'closed', 'points': reactor, 'fill_point': (500, 555)},
    ]

    # outlines and details
    black += [
        {'kind': 'stroke', 'points': head},
        {'kind': 'stroke', 'points': left_ear},
        {'kind': 'stroke', 'points': right_ear},
        {'kind': 'stroke', 'points': muzzle},
        {'kind': 'stroke', 'points': _smooth(_arc(cx - 35, head_y + 6, 18, 10, 200, 340), 4)},
        {'kind': 'stroke', 'points': _smooth(_arc(cx + 35, head_y + 6, 18, 10, 200, 340), 4)},
        {'kind': 'stroke', 'points': _smooth(_line(488, 266, 500, 286), 5)},
        {'kind': 'stroke', 'points': _smooth(_line(500, 286, 512, 266), 5)},
        {'kind': 'stroke', 'points': _smooth(_line(500, 286, 500, 307), 5)},
        {'kind': 'stroke', 'points': _smooth(_line(500, 307, 474, 319), 5)},
        {'kind': 'stroke', 'points': _smooth(_line(500, 307, 526, 319), 5)},
        {'kind': 'stroke', 'points': _smooth(_line(462, 289, 402, 278), 5)},
        {'kind': 'stroke', 'points': _smooth(_line(462, 303, 398, 304), 5)},
        {'kind': 'stroke', 'points': _smooth(_line(538, 289, 598, 278), 5)},
        {'kind': 'stroke', 'points': _smooth(_line(538, 303, 602, 304), 5)},
        {'kind': 'stroke', 'points': _smooth(_line(500, 132, 500, 90), 5)},
        {'kind': 'stroke', 'points': _smooth(_line(470, 150, 450, 102), 5)},
        {'kind': 'stroke', 'points': _smooth(_line(530, 150, 550, 102), 5)},
        {'kind': 'stroke', 'points': _smooth([(430, 155), (395, 192), (420, 212)], 8)},
        {'kind': 'stroke', 'points': _smooth([(570, 155), (605, 192), (580, 212)], 8)},
        {'kind': 'stroke', 'points': _smooth([(452, 205), (428, 236), (450, 258)], 8)},
        {'kind': 'stroke', 'points': _smooth([(548, 205), (572, 236), (550, 258)], 8)},
        {'kind': 'stroke', 'points': _smooth([(478, 134), (470, 166), (484, 184)], 8)},
        {'kind': 'stroke', 'points': _smooth([(522, 134), (530, 166), (516, 184)], 8)},
        {'kind': 'stroke', 'points': torso},
        {'kind': 'stroke', 'points': left_arm},
        {'kind': 'stroke', 'points': right_arm},
        {'kind': 'stroke', 'points': left_leg},
        {'kind': 'stroke', 'points': right_leg},
        {'kind': 'stroke', 'points': left_boot},
        {'kind': 'stroke', 'points': right_boot},
        {'kind': 'stroke', 'points': left_shoulder},
        {'kind': 'stroke', 'points': right_shoulder},
        {'kind': 'stroke', 'points': tail},
        {'kind': 'stroke', 'points': faceplate},
        {'kind': 'stroke', 'points': badge},
        {'kind': 'stroke', 'points': reactor},
        {'kind': 'stroke', 'points': _smooth(_line(500, 430, 500, 790), 8)},
        {'kind': 'stroke', 'points': _smooth([(370, 445), (448, 585), (492, 740)], 9)},
        {'kind': 'stroke', 'points': _smooth([(630, 445), (552, 585), (508, 740)], 9)},
        {'kind': 'stroke', 'points': _smooth([(380, 540), (445, 518), (455, 570), (390, 590), (380, 540)], 8)},
        {'kind': 'stroke', 'points': _smooth([(620, 540), (555, 518), (545, 570), (610, 590), (620, 540)], 8)},
        {'kind': 'stroke', 'points': _smooth(_line(590, 494, 608, 494), 4)},
        {'kind': 'stroke', 'points': _smooth(_line(599, 486, 599, 514), 4)},
        {'kind': 'stroke', 'points': _smooth(_line(484, 555, 516, 555), 4)},
        {'kind': 'stroke', 'points': _smooth(_line(500, 539, 500, 571), 4)},
    ]

    groups.append((ORANGE, orange))
    groups.append((SILVER, silver))
    groups.append((RED, red))
    groups.append((GOLD, gold))
    groups.append((CYAN, cyan))
    groups.append((BLACK, black))
    return groups


def main() -> None:
    board = build_generic_reference_board(
        request="Draw a Tiger Wearing Ralph Lauren everything inspired by Iron Man from Marvel comics.",
        primary_subject="tiger",
        anatomy_anchor="tiger anatomy",
        identity_anchor="Ralph Lauren Polo visual identity",
        style_anchor="Iron Man armor from Marvel comics",
        must_have_parts=[
            "full tiger figure",
            "recognizable tiger face and stripes",
            "Ralph Lauren cue",
            "red and gold armor tailoring",
            "smaller figure centered on canvas",
        ],
        must_avoid=[
            "canvas clipping",
            "generic cat drift",
            "scanline fill artifacts",
            "missing armor color contrast",
        ],
        style_notes=[
            "Use tiger anatomy first, armor fashion second.",
            "Keep the figure comfortably inside the canvas with generous margins.",
            "Use JSPaint fill tool for solid color masses, then add outline/detail.",
        ],
        pose="heroic smaller full-body standing pose with centered composition",
        camera_angle="straight-on character poster view",
        passes=["outline", "fill masses", "detail/stripes", "verification"],
    )
    written = board.save_split_artifacts(ROOT, "jspaint_tiger_rl_ironman_v2")
    print(f"[jspaint-tiger-v2] reference_board={written['reference_board']}")

    _safari_open()
    _maximize_safari()
    time.sleep(1.0)
    safari_bounds = _safari_bounds()
    canvas_info = _canvas_info()
    palette_info = _palette_info()
    tool_info = _tool_info()
    _clear_canvas()
    time.sleep(0.2)

    x1, y1, x2, y2 = safari_bounds
    ax_w = x2 - x1
    ax_h = y2 - y1
    chrome_left = max(0.0, (ax_w - canvas_info['innerWidth']) / 2.0)
    chrome_top = max(0.0, ax_h - canvas_info['innerHeight'])
    global_canvas_origin = (x1 + chrome_left + canvas_info['left'], y1 + chrome_top + canvas_info['top'])
    global_window_origin = (x1 + chrome_left, y1 + chrome_top)
    canvas_w = float(canvas_info['cssWidth'])
    canvas_h = float(canvas_info['cssHeight'])

    print(f"[jspaint-tiger-v2] url={canvas_info['url']}")
    print(f"[jspaint-tiger-v2] bounds={safari_bounds}")
    print(f"[jspaint-tiger-v2] canvas_origin_pt=({global_canvas_origin[0]:.1f}, {global_canvas_origin[1]:.1f})")
    print(f"[jspaint-tiger-v2] canvas_size_pt=({canvas_w:.1f}, {canvas_h:.1f})")

    groups = _transform_groups(_build_groups(), canvas_w, canvas_h)

    _choose_color(BLACK, global_window_origin, palette_info)
    _choose_tool('Pencil', global_window_origin, tool_info)
    for color, items in groups:
        if color != BLACK:
            for item in items:
                _draw_stroke(item['points'], global_canvas_origin, delay=0.0038)
        time.sleep(0.05)

    _choose_tool('Fill With Color', global_window_origin, tool_info)
    for color, items in groups:
        if color == BLACK:
            continue
        _choose_color(color, global_window_origin, palette_info)
        for item in items:
            fill_pt = item.get('fill_point')
            if fill_pt:
                _click(_global_point(fill_pt[0], fill_pt[1], global_canvas_origin))
                time.sleep(0.06)
        time.sleep(0.10)

    _choose_color(BLACK, global_window_origin, palette_info)
    _choose_tool('Pencil', global_window_origin, tool_info)
    for color, items in groups:
        if color == BLACK:
            for idx, item in enumerate(items, start=1):
                _draw_stroke(item['points'], global_canvas_origin, delay=0.0038 if len(item['points']) > 20 else 0.0045)
                if idx % 8 == 0:
                    time.sleep(0.08)

    time.sleep(1.1)
    subprocess.run(["screencapture", "-x", str(FINAL_SCREENSHOT)], check=True)
    print(f"[done] {FINAL_SCREENSHOT}")


if __name__ == '__main__':
    main()
