#!/usr/bin/env python3
"""Draw a realistic 1991 BMW M3 E30 (side profile) on Magma canvas using Quartz.

Realism category / PhD arts: detailed contour, flared wheel arches, Hofmeister kink,
spoiler, round headlight. Coordinates in screenshot pixels (2880x1800); canvas
center as in magma_draw_realism_hand.py. Run after magma_open_canvas.py when
Safari is on a Magma canvas tab.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import Quartz
from AppKit import NSScreen


def pixel_to_global(px: float, py: float) -> tuple[float, float]:
    primary = NSScreen.mainScreen()
    if primary is None:
        return (px, py)
    scale = primary.backingScaleFactor()
    frame = primary.frame()
    lx = px / scale
    ly = py / scale
    return (frame.origin.x + lx, frame.origin.y + ly)


def draw_stroke_global(points: list[tuple[float, float]], delay: float = 0.006) -> None:
    if len(points) < 2:
        return
    pts_global = [pixel_to_global(x, y) for x, y in points]
    p0 = pts_global[0]
    down = Quartz.CGEventCreateMouseEvent(
        None, Quartz.kCGEventLeftMouseDown,
        Quartz.CGPointMake(p0[0], p0[1]), Quartz.kCGMouseButtonLeft
    )
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, down)
    time.sleep(0.05)
    for p in pts_global[1:]:
        drag = Quartz.CGEventCreateMouseEvent(
            None, Quartz.kCGEventLeftMouseDragged,
            Quartz.CGPointMake(p[0], p[1]), Quartz.kCGMouseButtonLeft
        )
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, drag)
        time.sleep(delay)
    plast = pts_global[-1]
    up = Quartz.CGEventCreateMouseEvent(
        None, Quartz.kCGEventLeftMouseUp,
        Quartz.CGPointMake(plast[0], plast[1]), Quartz.kCGMouseButtonLeft
    )
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, up)
    time.sleep(0.12)


def smooth_curve(pts: list[tuple[float, float]], n_per_seg: int = 10) -> list[tuple[float, float]]:
    if len(pts) < 2:
        return pts
    out = [pts[0]]
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        for k in range(1, n_per_seg + 1):
            t = k / n_per_seg
            out.append((a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])))
    return out


def circle_pts(cx: float, cy: float, r: float, n: int = 24) -> list[tuple[float, float]]:
    import math
    return [
        (cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n))
        for i in range(n + 1)
    ]


def main() -> None:
    import subprocess
    subprocess.run(["osascript", "-e", 'tell application "Safari" to activate'], check=True)
    time.sleep(0.8)

    # Canvas center (screenshot pixels), same as magma_draw_realism_hand
    cx, cy = 1120, 750
    # E30 side profile: car facing right, ~540px long, ~160px tall; left edge at cx - 270
    L = cx - 270
    R = cx + 270
    T = cy - 80
    B = cy + 80
    # Wheel centers (side view)
    wrad = 52
    w1x, w1y = cx - 100, cy + 58
    w2x, w2y = cx + 100, cy + 58

    # --- 1) Upper body silhouette (hood, windshield, roof, C-pillar, trunk, spoiler) ---
    upper = [
        (L + 20, cy - 25),       # front bumper / nose
        (L + 55, cy - 35),       # hood start
        (L + 140, cy - 42),      # hood
        (L + 200, cy - 55),      # base windshield
        (L + 210, T + 15),       # windshield top
        (L + 280, T + 8),        # roof
        (L + 380, T + 18),       # C-pillar start (Hofmeister)
        (L + 400, cy - 45),     # C-pillar kink
        (L + 430, cy - 35),      # rear window base
        (L + 480, cy - 38),      # trunk
        (L + 520, cy - 55),      # spoiler
        (R - 15, cy - 40),       # rear bumper
        (R - 25, cy + 15),       # bumper down
        (R - 30, cy + 42),       # meet sill
        (L + 25, cy + 45),       # front sill
        (L + 20, cy - 25),       # back to nose
    ]
    draw_stroke_global(smooth_curve(upper, 12), delay=0.005)
    time.sleep(0.2)

    # --- 2) Lower sill / rocker ---
    sill = [
        (L + 25, cy + 45),
        (L + 200, cy + 52),
        (L + 400, cy + 50),
        (R - 30, cy + 42),
    ]
    draw_stroke_global(smooth_curve(sill, 8), delay=0.006)
    time.sleep(0.15)

    # --- 3) Front wheel arch (flared) + wheel ---
    arch1 = [
        (w1x - 75, cy + 58),
        (w1x - 55, cy + 25),
        (w1x - 25, cy + 8),
        (w1x + 25, cy + 8),
        (w1x + 55, cy + 25),
        (w1x + 75, cy + 58),
    ]
    draw_stroke_global(smooth_curve(arch1, 10), delay=0.006)
    time.sleep(0.12)
    draw_stroke_global(smooth_curve(circle_pts(w1x, w1y, wrad), 8), delay=0.004)
    time.sleep(0.15)

    # --- 4) Rear wheel arch (flared) + wheel ---
    arch2 = [
        (w2x - 75, cy + 58),
        (w2x - 55, cy + 25),
        (w2x - 25, cy + 8),
        (w2x + 25, cy + 8),
        (w2x + 55, cy + 25),
        (w2x + 75, cy + 58),
    ]
    draw_stroke_global(smooth_curve(arch2, 10), delay=0.006)
    time.sleep(0.12)
    draw_stroke_global(smooth_curve(circle_pts(w2x, w2y, wrad), 8), delay=0.004)
    time.sleep(0.15)

    # --- 5) Windshield line (realism: A-pillar) ---
    screen1 = [(L + 198, cy - 52), (L + 212, T + 12)]
    draw_stroke_global(smooth_curve(screen1, 6), delay=0.006)
    time.sleep(0.1)

    # --- 6) Side window + Hofmeister kink ---
    window = [
        (L + 282, T + 10),
        (L + 378, T + 20),
        (L + 398, cy - 42),
        (L + 428, cy - 32),
    ]
    draw_stroke_global(smooth_curve(window, 8), delay=0.006)
    time.sleep(0.12)

    # --- 7) Round headlight ---
    draw_stroke_global(smooth_curve(circle_pts(L + 35, cy - 28, 18), 6), delay=0.004)
    time.sleep(0.1)

    # --- 8) Kidney grille hint (short vertical lines) ---
    grille = [
        [(L + 62, cy - 48), (L + 62, cy - 18)],
        [(L + 78, cy - 48), (L + 78, cy - 18)],
    ]
    for seg in grille:
        draw_stroke_global(seg, delay=0.008)
        time.sleep(0.08)

    print("Magma realism BMW M3 E30 drawn: body, arches, wheels, windshield, window, headlight, grille.")


if __name__ == "__main__":
    main()
