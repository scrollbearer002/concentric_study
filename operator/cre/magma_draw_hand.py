#!/usr/bin/env python3
"""Draw a minimal hand-holding-pencil sketch on Magma canvas using Quartz.
Coordinates in screenshot pixels (2880x1800); converted to global for Quartz."""
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

def draw_stroke_global(points: list[tuple[float, float]], delay: float = 0.012) -> None:
    if len(points) < 2:
        return
    pts_global = [pixel_to_global(x, y) for x, y in points]
    p0 = pts_global[0]
    down = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseDown, Quartz.CGPointMake(p0[0], p0[1]), Quartz.kCGMouseButtonLeft)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, down)
    time.sleep(0.06)
    for p in pts_global[1:]:
        drag = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseDragged, Quartz.CGPointMake(p[0], p[1]), Quartz.kCGMouseButtonLeft)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, drag)
        time.sleep(delay)
    plast = pts_global[-1]
    up = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseUp, Quartz.CGPointMake(plast[0], plast[1]), Quartz.kCGMouseButtonLeft)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, up)
    time.sleep(0.15)

def main():
    import subprocess
    subprocess.run(["osascript", "-e", 'tell application "Safari" to activate'], check=True)
    time.sleep(0.6)

    # Canvas area (screenshot pixels): roughly 400-1850 x 150-1350
    cx, cy = 1120, 750

    # 1) Paper: rectangle
    w, h = 380, 280
    paper = [
        (cx - w//2, cy - h//2),
        (cx + w//2, cy - h//2),
        (cx + w//2, cy + h//2),
        (cx - w//2, cy + h//2),
        (cx - w//2, cy - h//2),
    ]
    draw_stroke_global(paper, delay=0.015)
    time.sleep(0.3)

    # 2) Pencil: diagonal line (hand holds it)
    pencil = [(cx - 80, cy + 20), (cx + 120, cy - 80)]
    draw_stroke_global(pencil, delay=0.01)
    time.sleep(0.2)

    # 3) Simplified hand: palm + fingers outline (few strokes)
    hand = [
        (cx - 100, cy + 30),
        (cx - 60, cy - 20),
        (cx, cy - 50),
        (cx + 50, cy - 30),
        (cx + 70, cy + 10),
        (cx + 40, cy + 60),
        (cx - 20, cy + 80),
        (cx - 100, cy + 30),
    ]
    draw_stroke_global(hand, delay=0.018)
    time.sleep(0.2)

    # 4) Short line on "paper" as if pencil is drawing
    line_on_paper = [(cx - 40, cy + 10), (cx + 60, cy + 5)]
    draw_stroke_global(line_on_paper, delay=0.01)
    print("Magma sketch drawn: paper, pencil, hand outline, line on paper.")

if __name__ == "__main__":
    main()
