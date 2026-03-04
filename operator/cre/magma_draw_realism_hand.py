#!/usr/bin/env python3
"""Draw a realism-style hand on Magma canvas using Quartz.
Single hand, detailed contour and finger segments. Coordinates in screenshot pixels (2880x1800)."""
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

def draw_stroke_global(points: list[tuple[float, float]], delay: float = 0.008) -> None:
    if len(points) < 2:
        return
    pts_global = [pixel_to_global(x, y) for x, y in points]
    p0 = pts_global[0]
    down = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseDown, Quartz.CGPointMake(p0[0], p0[1]), Quartz.kCGMouseButtonLeft)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, down)
    time.sleep(0.05)
    for p in pts_global[1:]:
        drag = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseDragged, Quartz.CGPointMake(p[0], p[1]), Quartz.kCGMouseButtonLeft)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, drag)
        time.sleep(delay)
    plast = pts_global[-1]
    up = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseUp, Quartz.CGPointMake(plast[0], plast[1]), Quartz.kCGMouseButtonLeft)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, up)
    time.sleep(0.12)

def smooth_curve(pts: list[tuple[float, float]], n_per_seg: int = 12) -> list[tuple[float, float]]:
    """Interpolate points along polyline for smoother stroke."""
    if len(pts) < 2:
        return pts
    out = [pts[0]]
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        for k in range(1, n_per_seg + 1):
            t = k / n_per_seg
            x = a[0] + t * (b[0] - a[0])
            y = a[1] + t * (b[1] - a[1])
            out.append((x, y))
    return out

def main():
    import subprocess
    subprocess.run(["osascript", "-e", 'tell application "Safari" to activate'], check=True)
    time.sleep(0.7)

    # Canvas center (screenshot pixels)
    cx, cy = 1120, 750
    # Hand scale and offset: palm ~220px wide, fingers up
    s = 1.35
    ox, oy = cx - 20, cy - 80

    # --- 1) Palm / heel contour (realism: rounded heel, thenar, hypothenar) ---
    palm = [
        (ox - 42*s, oy + 120*s),   # wrist left
        (ox - 55*s, oy + 85*s),
        (ox - 50*s, oy + 45*s),
        (ox - 38*s, oy + 15*s),    # base of little finger
        (ox - 25*s, oy - 25*s),    # between ring/middle
        (ox - 8*s,  oy - 50*s),    # between middle/index
        (ox + 18*s, oy - 55*s),    # base index
        (ox + 45*s, oy - 45*s),    # base thumb
        (ox + 65*s, oy - 15*s),    # thumb side
        (ox + 70*s, oy + 35*s),    # heel of palm
        (ox + 55*s, oy + 75*s),
        (ox + 35*s, oy + 105*s),
        (ox - 10*s, oy + 118*s),
        (ox - 42*s, oy + 120*s),
    ]
    draw_stroke_global(smooth_curve(palm, 10), delay=0.006)
    time.sleep(0.25)

    # --- 2) Thumb (2 segments, realistic angle) ---
    thumb = [
        (ox + 45*s, oy - 45*s),
        (ox + 58*s, oy - 65*s),
        (ox + 72*s, oy - 58*s),
        (ox + 78*s, oy - 38*s),
        (ox + 75*s, oy - 18*s),
    ]
    draw_stroke_global(smooth_curve(thumb, 10), delay=0.006)
    time.sleep(0.15)

    # --- 3) Index finger (3 segments, slight curve) ---
    index = [
        (ox + 18*s, oy - 55*s),
        (ox + 22*s, oy - 85*s),
        (ox + 25*s, oy - 115*s),
        (ox + 28*s, oy - 145*s),
        (ox + 30*s, oy - 172*s),
        (ox + 28*s, oy - 195*s),
    ]
    draw_stroke_global(smooth_curve(index, 10), delay=0.006)
    time.sleep(0.12)

    # --- 4) Middle finger ---
    middle = [
        (ox - 8*s, oy - 50*s),
        (ox - 10*s, oy - 82*s),
        (ox - 12*s, oy - 118*s),
        (ox - 10*s, oy - 155*s),
        (ox - 6*s,  oy - 192*s),
        (ox - 2*s,  oy - 218*s),
    ]
    draw_stroke_global(smooth_curve(middle, 10), delay=0.006)
    time.sleep(0.12)

    # --- 5) Ring finger ---
    ring = [
        (ox - 25*s, oy - 25*s),
        (ox - 32*s, oy - 58*s),
        (ox - 38*s, oy - 95*s),
        (ox - 40*s, oy - 132*s),
        (ox - 38*s, oy - 168*s),
        (ox - 34*s, oy - 198*s),
    ]
    draw_stroke_global(smooth_curve(ring, 10), delay=0.006)
    time.sleep(0.12)

    # --- 6) Little finger ---
    little = [
        (ox - 38*s, oy + 15*s),
        (ox - 48*s, oy - 18*s),
        (ox - 55*s, oy - 52*s),
        (ox - 58*s, oy - 88*s),
        (ox - 56*s, oy - 120*s),
    ]
    draw_stroke_global(smooth_curve(little, 10), delay=0.006)
    time.sleep(0.15)

    # --- 7) Inner palm crease (lifeline style, adds realism) ---
    crease = [
        (ox + 35*s, oy + 50*s),
        (ox + 10*s, oy + 25*s),
        (ox - 15*s, oy + 5*s),
        (ox - 35*s, oy + 20*s),
    ]
    draw_stroke_global(smooth_curve(crease, 8), delay=0.007)
    time.sleep(0.12)

    # --- 8) Knuckle hints (short arcs at finger bases) ---
    for base, dx in [((ox + 18*s, oy - 55*s), 8), ((ox - 8*s, oy - 50*s), 10), ((ox - 25*s, oy - 25*s), 8)]:
        knuckle = [
            (base[0] - dx*s, base[1]),
            (base[0], base[1] - dx*s*0.6),
            (base[0] + dx*s, base[1]),
        ]
        draw_stroke_global(smooth_curve(knuckle, 8), delay=0.006)
        time.sleep(0.08)

    print("Magma realism hand drawn: palm, thumb, four fingers, crease, knuckles.")

if __name__ == "__main__":
    main()
