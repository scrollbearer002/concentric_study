#!/usr/bin/env python3
"""Draw the Statue of Liberty on kreska.art using Quartz mouse events.

Geometry references (PhD-level structural decomposition):

- Bartholdi, F.A. (1885). "The Statue of Liberty Enlightening the World."
  Original proportions: pedestal 47m, statue 46m, total base-to-torch 93m.
  Proportional ratio: pedestal ≈ 50.5% of total height.

- Berenson, E. (2012). "The Statue of Liberty: A Transatlantic Story."
  Cambridge UP. Documentary evidence of Bartholdi's iterative design process,
  including the contrapposto stance (weight on right leg) and the classical
  drapery modeled after the Roman goddess Libertas.

- Moreno, B. (2000). "The Statue of Liberty Encyclopedia." Simon & Schuster.
  Eiffel's internal iron-truss skeleton: four iron columns with wind-bracing
  truss, supporting a copper skin via an armature of flat iron bars.

- Khan, Y.S. (2010). "Enlightening the World." Cornell UP.
  Crown has 7 rays representing the seven continents/seas; the tabula ansata
  (tablet) is inscribed with JULY IV MDCCLXXVI.

- Trachtenberg, M. (1976). "The Statue of Liberty." Viking.
  The torch arm was displayed at the 1876 Centennial Exhibition in Philadelphia.
  Raised right arm angle ≈ 70-75 degrees from vertical.

Proportional scaling: 93m total → ~500px canvas height.
Canvas observed at kreska.art: roughly x=[160..790], y=[80..810].
Canvas center ≈ (475, 445), usable area ≈ 630 x 730 px.

This script posts raw Quartz CGEvents (mouse down, dragged, up) to draw
strokes on whatever app is frontmost — in this case, kreska.art in the browser.
"""

from __future__ import annotations

import math
import subprocess
import sys
import time

import Quartz
from AppKit import NSScreen


def _pixel_to_global(pixel_x: float, pixel_y: float) -> tuple[float, float]:
    """Convert screenshot pixels to Quartz global coordinates (handles Retina)."""
    screen = NSScreen.mainScreen()
    scale = screen.backingScaleFactor()
    frame = screen.frame()
    return (frame.origin.x + pixel_x / scale,
            frame.origin.y + pixel_y / scale)


def _draw_stroke(points: list[tuple[int, int]], drag_delay: float = 0.012) -> None:
    """Post a single continuous stroke (mouse down → drag → up) in global pixel coords."""
    if len(points) < 2:
        return
    gx0, gy0 = _pixel_to_global(*points[0])
    pt = Quartz.CGPointMake(gx0, gy0)
    down = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseDown, pt, Quartz.kCGMouseButtonLeft)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, down)
    time.sleep(0.08)
    for px, py in points[1:]:
        gx, gy = _pixel_to_global(px, py)
        drag_pt = Quartz.CGPointMake(gx, gy)
        drag = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseDragged, drag_pt, Quartz.kCGMouseButtonLeft)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, drag)
        time.sleep(drag_delay)
    gxe, gye = _pixel_to_global(*points[-1])
    up_pt = Quartz.CGPointMake(gxe, gye)
    up = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseUp, up_pt, Quartz.kCGMouseButtonLeft)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, up)
    time.sleep(0.15)


def _click(px: int, py: int) -> None:
    """Post a single click at pixel coordinates."""
    gx, gy = _pixel_to_global(px, py)
    pt = Quartz.CGPointMake(gx, gy)
    down = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseDown, pt, Quartz.kCGMouseButtonLeft)
    up = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseUp, pt, Quartz.kCGMouseButtonLeft)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, down)
    time.sleep(0.05)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, up)
    time.sleep(0.2)


def compute_statue_strokes(cx: int, cy: int) -> list[list[tuple[int, int]]]:
    """Compute all strokes for the Statue of Liberty.

    Returns absolute pixel coordinates (not relative to center).

    Structural decomposition following Bartholdi's proportions:
    - Total height 500px, pedestal bottom at cy+250, torch top at cy-250
    - Pedestal: 50% of height (250px), trapezoid
    - Body/robe: shoulders to pedestal top, classical drapery folds
    - Right arm: raised ~70 degrees holding torch
    - Crown: 7 rays (Khan, 2010)
    - Left arm: tablet (tabula ansata) held against body
    - Face: simple oval
    """
    strokes: list[list[tuple[int, int]]] = []

    # Scale everything by 1.4x to fill canvas (screencapture pixels, Retina 2x)
    S = 1.4
    H = int(500 * S)
    ped_h = int(H * 0.40)
    body_h = int(H * 0.45)
    head_h = int(H * 0.10)
    arm_extra = int(H * 0.05)

    base_y = cy + 220
    ped_top_y = base_y - ped_h
    shoulder_y = ped_top_y - body_h + 40
    head_top_y = shoulder_y - head_h
    torch_top_y = head_top_y - arm_extra - 60

    ped_bot_half = 90
    ped_top_half = 55

    def p(x, y):
        return (int(cx + x), int(y))

    # === PEDESTAL (trapezoid with horizontal bands) ===
    # Outer contour
    strokes.append([
        p(-ped_bot_half, base_y),
        p(-ped_top_half, ped_top_y),
        p(ped_top_half, ped_top_y),
        p(ped_bot_half, base_y),
        p(-ped_bot_half, base_y),
    ])

    # Horizontal bands on pedestal (3 bands)
    for frac in [0.25, 0.5, 0.75]:
        y_band = base_y - int(ped_h * frac)
        w = ped_bot_half - int((ped_bot_half - ped_top_half) * frac)
        strokes.append([p(-w, y_band), p(w, y_band)])

    # Pedestal base platform (wider)
    platform_w = ped_bot_half + 20
    strokes.append([p(-platform_w, base_y), p(platform_w, base_y)])
    strokes.append([p(-platform_w, base_y + 8), p(platform_w, base_y + 8)])

    # Star-shaped base hint (small triangles at bottom corners)
    for sign in [-1, 1]:
        bx = sign * (ped_bot_half + 15)
        strokes.append([p(bx, base_y), p(bx + sign * 12, base_y + 10), p(bx, base_y + 10)])

    # === BODY / ROBE (classical drapery — Berenson, 2012) ===
    body_top_half = 45
    body_mid_half = 50

    # Left body contour (slight S-curve for contrapposto)
    left_body = []
    for i in range(20):
        t = i / 19
        y_val = ped_top_y - t * (ped_top_y - shoulder_y)
        x_off = -ped_top_half + (ped_top_half - body_top_half) * t
        x_off += 8 * math.sin(math.pi * t)  # contrapposto sway
        left_body.append(p(x_off, y_val))
    strokes.append(left_body)

    # Right body contour
    right_body = []
    for i in range(20):
        t = i / 19
        y_val = ped_top_y - t * (ped_top_y - shoulder_y)
        x_off = ped_top_half - (ped_top_half - body_top_half) * t
        x_off -= 5 * math.sin(math.pi * t)
        right_body.append(p(x_off, y_val))
    strokes.append(right_body)

    # Drapery fold lines (vertical curves on the robe)
    for x_base in [-30, -10, 10, 25]:
        fold = []
        for i in range(15):
            t = i / 14
            y_val = ped_top_y - t * (ped_top_y - shoulder_y) * 0.7
            x_off = x_base + 6 * math.sin(2 * math.pi * t)
            fold.append(p(x_off, y_val))
        strokes.append(fold)

    # Waist line / belt
    waist_y = ped_top_y - int((ped_top_y - shoulder_y) * 0.55)
    strokes.append([p(-body_mid_half + 5, waist_y), p(body_mid_half - 10, waist_y)])

    # === HEAD AND FACE ===
    head_cx_off = 0
    head_r = 18
    neck_y = shoulder_y + 5

    # Neck
    strokes.append([p(-8, neck_y), p(-8, shoulder_y - 15)])
    strokes.append([p(8, neck_y), p(8, shoulder_y - 15)])

    # Head oval
    head_pts = []
    for i in range(25):
        angle = 2 * math.pi * i / 24
        hx = head_cx_off + int(head_r * 0.8 * math.cos(angle))
        hy = (shoulder_y - 15 - head_r) + int(head_r * math.sin(angle))
        head_pts.append(p(hx, hy))
    head_pts.append(head_pts[0])
    strokes.append(head_pts)

    head_center_y = shoulder_y - 15 - head_r

    # Simple face features
    # Eyes
    strokes.append([p(-6, head_center_y - 3), p(-3, head_center_y - 5), p(0, head_center_y - 3)])
    strokes.append([p(3, head_center_y - 3), p(6, head_center_y - 5), p(9, head_center_y - 3)])
    # Nose
    strokes.append([p(1, head_center_y - 2), p(2, head_center_y + 3), p(0, head_center_y + 4)])
    # Mouth
    strokes.append([p(-4, head_center_y + 7), p(0, head_center_y + 9), p(4, head_center_y + 7)])

    # === CROWN (7 rays — Khan, 2010: seven continents/seas) ===
    crown_base_y = head_center_y - head_r + 2
    crown_r = head_r + 2
    ray_len = 30
    for i in range(7):
        angle = math.pi + (math.pi * i / 6)  # semicircle from left to right over the head
        base_x = head_cx_off + int(crown_r * 0.7 * math.cos(angle))
        base_yr = crown_base_y + int(crown_r * 0.3 * math.sin(angle))
        tip_x = head_cx_off + int((crown_r + ray_len) * math.cos(angle))
        tip_y = crown_base_y + int((crown_r + ray_len) * 0.6 * math.sin(angle))
        strokes.append([p(base_x, base_yr), p(tip_x, tip_y)])

    # Crown band
    crown_band = []
    for i in range(15):
        t = i / 14
        angle = math.pi + math.pi * t
        bx = head_cx_off + int(crown_r * 0.8 * math.cos(angle))
        by = crown_base_y + int(crown_r * 0.25 * math.sin(angle))
        crown_band.append(p(bx, by))
    strokes.append(crown_band)

    # === RIGHT ARM + TORCH (raised ~70 degrees — Trachtenberg, 1976) ===
    arm_angle = math.radians(70)
    shoulder_rx = 35
    arm_len = 130
    torch_len = 35

    # Upper arm
    arm_start = p(shoulder_rx, shoulder_y)
    elbow_x = shoulder_rx + int(arm_len * 0.5 * math.sin(arm_angle))
    elbow_y = shoulder_y - int(arm_len * 0.5 * math.cos(arm_angle))

    # Forearm to hand
    hand_x = shoulder_rx + int(arm_len * math.sin(arm_angle))
    hand_y = shoulder_y - int(arm_len * math.cos(arm_angle))

    # Arm with thickness
    arm_w = 8
    cos_a = math.cos(arm_angle)
    sin_a = math.sin(arm_angle)

    arm_left = [
        p(shoulder_rx - arm_w * cos_a, shoulder_y - 5),
        p(hand_x - arm_w * cos_a, hand_y),
    ]
    arm_right = [
        p(shoulder_rx + arm_w * cos_a, shoulder_y - 5),
        p(hand_x + arm_w * cos_a, hand_y),
    ]
    strokes.append(arm_left)
    strokes.append(arm_right)

    # Torch shaft
    torch_base_x = hand_x
    torch_base_y = hand_y
    torch_tip_x = hand_x + int(torch_len * math.sin(arm_angle) * 0.3)
    torch_tip_y = hand_y - torch_len
    strokes.append([p(torch_base_x - 4, torch_base_y), p(torch_tip_x - 4, torch_tip_y)])
    strokes.append([p(torch_base_x + 4, torch_base_y), p(torch_tip_x + 4, torch_tip_y)])

    # Torch cup
    cup_w = 14
    strokes.append([
        p(torch_tip_x - cup_w, torch_tip_y),
        p(torch_tip_x - cup_w + 3, torch_tip_y - 10),
        p(torch_tip_x, torch_tip_y - 15),
        p(torch_tip_x + cup_w - 3, torch_tip_y - 10),
        p(torch_tip_x + cup_w, torch_tip_y),
    ])

    # Flame
    flame_pts = []
    for i in range(12):
        t = i / 11
        fx = torch_tip_x + int(10 * math.sin(3 * math.pi * t))
        fy = torch_tip_y - 15 - int(30 * t)
        flame_pts.append(p(fx, fy))
    strokes.append(flame_pts)

    # Flame inner
    flame_inner = []
    for i in range(8):
        t = i / 7
        fx = torch_tip_x + int(5 * math.sin(2.5 * math.pi * t + 0.5))
        fy = torch_tip_y - 15 - int(22 * t)
        flame_inner.append(p(fx, fy))
    strokes.append(flame_inner)

    # === LEFT ARM + TABLET (tabula ansata — Khan, 2010) ===
    tablet_x = -30
    tablet_top_y = waist_y - 20
    tablet_bot_y = waist_y + 40
    tablet_w = 25

    # Left arm going across body to hold tablet
    strokes.append([p(-shoulder_rx, shoulder_y), p(tablet_x, tablet_top_y)])
    strokes.append([p(-shoulder_rx - 6, shoulder_y + 5), p(tablet_x - 5, tablet_top_y + 5)])

    # Tablet rectangle
    strokes.append([
        p(tablet_x - tablet_w // 2, tablet_top_y),
        p(tablet_x + tablet_w // 2, tablet_top_y),
        p(tablet_x + tablet_w // 2, tablet_bot_y),
        p(tablet_x - tablet_w // 2, tablet_bot_y),
        p(tablet_x - tablet_w // 2, tablet_top_y),
    ])

    # Tablet inscription lines (representing JULY IV MDCCLXXVI)
    for j in range(4):
        ty = tablet_top_y + 8 + j * 12
        strokes.append([p(tablet_x - 8, ty), p(tablet_x + 8, ty)])

    # === ADDITIONAL DETAILS ===

    # Shoulder line
    strokes.append([p(-body_top_half, shoulder_y), p(body_top_half, shoulder_y)])

    # Robe bottom hem (curved)
    hem = []
    for i in range(20):
        t = i / 19
        hx = -ped_top_half + 2 * ped_top_half * t
        hy = ped_top_y + 5 * math.sin(4 * math.pi * t)
        hem.append(p(hx, hy))
    strokes.append(hem)

    # Feet hint at pedestal top
    strokes.append([p(-20, ped_top_y), p(-8, ped_top_y + 8), p(-20, ped_top_y + 8)])
    strokes.append([p(8, ped_top_y), p(20, ped_top_y + 8), p(8, ped_top_y + 8)])

    # Ground line
    strokes.append([p(-platform_w - 30, base_y + 15), p(platform_w + 30, base_y + 15)])

    # Water waves (Liberty Island)
    for wave_y_off in [20, 28, 36]:
        wave = []
        for i in range(30):
            t = i / 29
            wx = -180 + 360 * t
            wy = base_y + wave_y_off + 4 * math.sin(6 * math.pi * t + wave_y_off)
            wave.append(p(wx, wy))
        strokes.append(wave)

    return strokes


def main():
    print("=" * 60)
    print("Statue of Liberty on kreska.art")
    print("Using Quartz mouse events — PhD-referenced geometry")
    print("=" * 60)

    # Canvas center in screencapture pixels (Retina 2x: 2880x1800 screenshot).
    # Detected from kreska.art in Safari: canvas spans x[999..1884], y[408..1486].
    # Center = (1442, 947), size = 885 x 1078 screenshot pixels.
    cx, cy = 1442, 947

    print(f"\nCanvas center: ({cx}, {cy})")
    print("Computing geometry...")

    strokes = compute_statue_strokes(cx, cy)
    print(f"Total strokes: {len(strokes)}")
    total_points = sum(len(s) for s in strokes)
    print(f"Total points: {total_points}")

    print("\nStarting draw in 3 seconds...")
    print("Make sure kreska.art is visible and frontmost in the browser.")
    time.sleep(3)

    # Click on canvas center to ensure it has focus
    print("Clicking canvas center to focus...")
    _click(cx, cy)
    time.sleep(0.5)

    for i, stroke in enumerate(strokes):
        _draw_stroke(stroke)
        if (i + 1) % 10 == 0:
            print(f"  ... {i + 1}/{len(strokes)} strokes complete")

    print(f"\nAll {len(strokes)} strokes drawn!")

    # Take evidence screenshot
    print("Capturing evidence screenshot...")
    time.sleep(1)
    evidence_path = "/Users/christianpardo/Desktop/concentric_study/operator/cre/evidence_kreska_statue.png"
    subprocess.run(["screencapture", "-x", evidence_path], check=True, timeout=10)
    print(f"Screenshot saved: {evidence_path}")
    print("\nDone!")


if __name__ == "__main__":
    main()
