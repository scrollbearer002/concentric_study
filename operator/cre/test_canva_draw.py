#!/usr/bin/env python3
"""Draw 'two hands interlaced struggling over a shattered glass sphere'
on Canva Draw (canva.com/draw/) using Quartz mouse events.

Integrates:
- VisualMonitor: background screenshots every 5s during execution
- VerificationGate: mandatory post-execution screenshot + judge

All coordinates are in Quartz POINTS (not retina pixels).
Safari window: top=31, chrome=52pt, viewport starts at y=83.
Canvas usable area: x=160..1400, y=180..600 (Quartz points).
Canvas center: (720, 400).
"""

from __future__ import annotations

import math
import subprocess
import sys
import time

import pytest

# macOS-only: drives real macOS UI via the native Quartz stack.
pytest.importorskip("Quartz", reason="macOS-only GUI automation (requires pyobjc/Quartz)")

import Quartz

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))


TASK_DESCRIPTION = (
    "Draw two hands interlaced struggling over a shattered glass sphere "
    "with exhaustive detail and profuse colors"
)


def _draw_stroke(points: list[tuple[float, float]], drag_delay: float = 0.008) -> None:
    if len(points) < 2:
        return
    pt = Quartz.CGPointMake(points[0][0], points[0][1])
    down = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseDown, pt, Quartz.kCGMouseButtonLeft)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, down)
    time.sleep(0.06)
    for px, py in points[1:]:
        drag_pt = Quartz.CGPointMake(px, py)
        drag = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseDragged, drag_pt, Quartz.kCGMouseButtonLeft)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, drag)
        time.sleep(drag_delay)
    up_pt = Quartz.CGPointMake(points[-1][0], points[-1][1])
    up = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseUp, up_pt, Quartz.kCGMouseButtonLeft)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, up)
    time.sleep(0.12)


def _click_quartz(x: float, y: float, label: str = "") -> None:
    pt = Quartz.CGPointMake(x, y)
    down = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseDown, pt, Quartz.kCGMouseButtonLeft)
    up = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseUp, pt, Quartz.kCGMouseButtonLeft)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, down)
    time.sleep(0.05)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, up)
    time.sleep(0.4)
    if label:
        print(f"  click: {label}")


def _ss(name: str) -> str:
    path = f"/tmp/canva_draw_{name}.png"
    subprocess.run(["screencapture", "-x", path], check=True)
    return path


def _ensure_safari_focus():
    subprocess.run(["osascript", "-e", 'tell application "Safari" to activate'], check=True)
    time.sleep(0.5)


def _select_pen_color(color_index: int) -> None:
    """Select a pen color from the Draw sub-panel.

    Pen preview buttons (CSS positions, Quartz = CSS + 83 for y):
    0: blue line   at CSS(156, 263) -> Quartz(156, 346)
    1: red line    at CSS(180, 306) -> Quartz(180, 389)
    2: pink rect   at CSS(156, 349) -> Quartz(156, 432)
    3: red circle  at CSS(156, 392) -> Quartz(156, 475)
    """
    pen_positions = [
        (156, 346),
        (180, 389),
        (156, 432),
        (156, 475),
    ]
    if 0 <= color_index < len(pen_positions):
        x, y = pen_positions[color_index]
        _click_quartz(x, y, f"pen color {color_index}")


def compute_hands_and_sphere(cx: float, cy: float, scale: float = 0.65) -> list[list[tuple[float, float]]]:
    """Compute strokes for two interlaced hands and a shattered glass sphere.
    All coordinates in Quartz global points.
    """
    strokes: list[list[tuple[float, float]]] = []
    s = scale

    # === LEFT HAND ===
    palm_l = []
    for i in range(25):
        t = i / 24
        x = cx - 350*s + t * 200*s
        y = cy + 30*s * math.sin(math.pi * t) - 10*s
        palm_l.append((x, y))
    strokes.append(palm_l)

    palm_lb = []
    for i in range(25):
        t = i / 24
        x = cx - 350*s + t * 200*s
        y = cy + 60*s - 20*s * math.sin(math.pi * t)
        palm_lb.append((x, y))
    strokes.append(palm_lb)

    strokes.append([(cx - 380*s, cy - 20*s), (cx - 350*s, cy - 10*s)])
    strokes.append([(cx - 380*s, cy + 70*s), (cx - 350*s, cy + 60*s)])

    for fi, y_off in enumerate([-40, -15, 10, 35]):
        finger = []
        for i in range(20):
            t = i / 19
            x = cx - 150*s + t * 130*s
            y = cy + y_off*s + 15*s * math.sin(math.pi * t * 1.5)
            y += t * t * 20*s
            finger.append((x, y))
        strokes.append(finger)

    thumb_l = []
    for i in range(15):
        t = i / 14
        x = cx - 200*s + t * 80*s
        y = cy + 70*s - t * 50*s - 10*s * math.sin(math.pi * t)
        thumb_l.append((x, y))
    strokes.append(thumb_l)

    # === RIGHT HAND ===
    palm_r = []
    for i in range(25):
        t = i / 24
        x = cx + 350*s - t * 200*s
        y = cy + 30*s * math.sin(math.pi * t) + 5*s
        palm_r.append((x, y))
    strokes.append(palm_r)

    palm_rb = []
    for i in range(25):
        t = i / 24
        x = cx + 350*s - t * 200*s
        y = cy + 65*s - 20*s * math.sin(math.pi * t)
        palm_rb.append((x, y))
    strokes.append(palm_rb)

    strokes.append([(cx + 380*s, cy - 15*s), (cx + 350*s, cy - 5*s)])
    strokes.append([(cx + 380*s, cy + 75*s), (cx + 350*s, cy + 65*s)])

    for fi, y_off in enumerate([-28, -3, 22, 47]):
        finger = []
        for i in range(20):
            t = i / 19
            x = cx + 150*s - t * 130*s
            y = cy + y_off*s - 15*s * math.sin(math.pi * t * 1.5)
            y -= t * t * 20*s
            finger.append((x, y))
        strokes.append(finger)

    thumb_r = []
    for i in range(15):
        t = i / 14
        x = cx + 200*s - t * 80*s
        y = cy + 75*s - t * 55*s - 10*s * math.sin(math.pi * t)
        thumb_r.append((x, y))
    strokes.append(thumb_r)

    # === KNUCKLE DETAILS ===
    for side in [-1, 1]:
        for k in range(4):
            kx = cx + side * (170*s + k * 5*s)
            ky = cy - 30*s + k * 25*s
            arc = []
            for i in range(8):
                t = i / 7
                arc.append((kx + 8*s * math.cos(math.pi * t),
                            ky + 5*s * math.sin(math.pi * t)))
            strokes.append(arc)

    # === GLASS SPHERE ===
    sphere_r = 55 * s
    circle = []
    for i in range(40):
        angle = 2 * math.pi * i / 39
        circle.append((cx + sphere_r * math.cos(angle),
                        cy + sphere_r * math.sin(angle)))
    strokes.append(circle)

    inner = []
    for i in range(30):
        angle = 2 * math.pi * i / 29
        r = sphere_r * 0.75
        inner.append((cx + r * math.cos(angle),
                       cy + r * math.sin(angle)))
    strokes.append(inner)

    highlight = []
    for i in range(12):
        angle = math.pi * 0.8 + (math.pi * 0.5) * i / 11
        r = sphere_r * 0.85
        highlight.append((cx + r * math.cos(angle),
                           cy + r * math.sin(angle)))
    strokes.append(highlight)

    # === SHATTER CRACKS ===
    num_cracks = 8
    for c in range(num_cracks):
        angle = 2 * math.pi * c / num_cracks + 0.2
        crack = [(cx, cy)]
        length = sphere_r + 15*s + (c % 3) * 10*s
        for i in range(1, 8):
            t = i / 7
            wobble = 5*s * math.sin(t * math.pi * 3 + c)
            crack.append((
                cx + length * t * math.cos(angle) + wobble * math.sin(angle),
                cy + length * t * math.sin(angle) - wobble * math.cos(angle)
            ))
        strokes.append(crack)

    for sh in range(12):
        angle = 2 * math.pi * sh / 12
        r1 = sphere_r + 10*s
        r2 = sphere_r + 25*s
        a1 = angle - 0.12
        a2 = angle + 0.12
        shard = [
            (cx + r1 * math.cos(angle), cy + r1 * math.sin(angle)),
            (cx + r2 * math.cos(a1), cy + r2 * math.sin(a1)),
            (cx + r2 * math.cos(a2), cy + r2 * math.sin(a2)),
            (cx + r1 * math.cos(angle), cy + r1 * math.sin(angle)),
        ]
        strokes.append(shard)

    # === FINGER TENDONS ===
    for side in [-1, 1]:
        for t_line in range(3):
            tendon = []
            base_x = cx + side * 250*s
            for i in range(15):
                t = i / 14
                x = base_x + side * t * 50*s
                y = cy - 10*s + t_line * 25*s + 3*s * math.sin(t * math.pi * 4)
                tendon.append((x, y))
            strokes.append(tendon)

    return strokes


def main():
    print("=" * 60)
    print("CANVA DRAW: Hands & Shattered Glass Sphere")
    print("With VisualMonitor + VerificationGate")
    print("=" * 60)

    _ensure_safari_focus()
    _ss("00_start")

    # Start VisualMonitor
    monitor = None
    try:
        from agent_infra import VisualMonitor
        monitor = VisualMonitor(
            interval_seconds=5,
            buffer_size=30,
            output_dir="/tmp/canva_monitor",
        )
        monitor.start()
        print("[Monitor] Started (5s interval)")
    except ImportError:
        print("[Monitor] Not available")

    cx, cy = 720.0, 400.0

    print(f"\n[1] Computing strokes at center ({cx}, {cy})...")
    strokes = compute_hands_and_sphere(cx, cy)
    print(f"    {len(strokes)} strokes ready")

    print(f"\n[2] Drawing {len(strokes)} strokes...")
    for i, stroke in enumerate(strokes):
        _draw_stroke(stroke)
        if (i + 1) % 10 == 0:
            print(f"    Stroke {i+1}/{len(strokes)}")

    print("\n[3] Drawing complete. Taking screenshot...")
    _ensure_safari_focus()
    time.sleep(0.5)
    _ss("02_after_draw")

    if monitor:
        monitor.stop()
        print(f"[Monitor] Stopped. {monitor.get_status()['total_captures']} snapshots")

    # === MANDATORY VERIFICATION GATE ===
    print("\n" + "=" * 60)
    print("MANDATORY VERIFICATION GATE")
    print("=" * 60)

    from agent_infra import VerificationGate
    gate = VerificationGate(
        task_description=TASK_DESCRIPTION,
        output_dir="/tmp/canva_verification",
    )
    result = gate.verify(iteration=1)

    if result.passed:
        print("\n>>> TASK COMPLETE — Verification gate PASSED <<<")
    else:
        print(f"\n>>> TASK NOT COMPLETE — {len(result.deficiencies)} deficiencies <<<")
        print("The following issues must be fixed before declaring done:")
        for d in result.deficiencies:
            print(f"  - {d}")
        print("\nThis output does NOT meet the requested standard.")

    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(main())
