#!/usr/bin/env python3
"""
Study file: CONCENTRIC_TRIANGLES_CLEAN logic only.
Hot-path functions, no dead code. Explains Quartz events and Gemini oracles.
"""

import json
import os
import time
from pathlib import Path

# Dry Run: observe logic without posting Quartz events. Set CONCENTRIC_DRY_RUN=1
DRY_RUN = os.environ.get("CONCENTRIC_DRY_RUN", "0").lower() in ("1", "true", "yes")


def _dry_run_guard(action: str, **kwargs) -> bool:
    """If DRY_RUN, log what would happen and return True (skip actual execution)."""
    if DRY_RUN:
        print(f"[DRY_RUN] {action} {kwargs}")
        return True
    return False


# =============================================================================
# PILLAR 1: GEOMETRY ENGINE
# =============================================================================

def get_screenshot_center(screenshot_path: str) -> tuple[int, int]:
    """
    True middle from screenshot dimensions. No VLM.
    center_x = width // 2, center_y = height // 2
    """
    from PIL import Image
    with Image.open(screenshot_path) as im:
        w, h = im.size
    return (w // 2, h // 2)


def triangle_vertices(size: int) -> list[tuple[int, int]]:
    """
    Equilateral-like triangle vertices (relative to center).
    Math: top vertex at (0, -size); base from (-size, size) to (size, size).
    """
    return [(0, -size), (-size, size), (size, size)]


# =============================================================================
# PILLAR 2: BRIDGE (MacOSAgentCore hot-path subset)
# =============================================================================

# Requires: pyobjc-framework-Cocoa, pyobjc-framework-Quartz
try:
    import Quartz
    from AppKit import NSScreen
except ImportError:
    Quartz = None

def _pixel_to_global_quartz(px: float, py: float) -> tuple[float, float]:
    """Convert image pixel (top-left origin) to Quartz global (bottom-left)."""
    primary = NSScreen.mainScreen()
    if primary is None:
        scale = 2.0
    else:
        scale = primary.backingScaleFactor()
    # Quartz uses bottom-left origin; screen height flips Y
    screen_height = primary.frame().size.height * scale if primary else 900 * scale
    gx = px
    gy = screen_height - py
    return (gx, gy)


def execute_clear_canvas(app_focus: str = "Safari"):
    """Cmd+Backspace. Quartz: keycode 51 + kCGEventFlagMaskCommand."""
    if _dry_run_guard("execute_clear_canvas", app_focus=app_focus):
        return
    if Quartz is None:
        return
    keycode = 51  # kVK_Delete (Backspace)
    flags = getattr(Quartz, "kCGEventFlagMaskCommand", 0x100000)
    event_down = Quartz.CGEventCreateKeyboardEvent(None, keycode, True)
    event_up = Quartz.CGEventCreateKeyboardEvent(None, keycode, False)
    Quartz.CGEventSetFlags(event_down, flags)
    Quartz.CGEventSetFlags(event_up, flags)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, event_down)
    time.sleep(0.05)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, event_up)


def execute_keystroke(key: int | str, app_focus: str = "Safari"):
    """Single key. key=36 -> Enter; key='p' -> pen."""
    if _dry_run_guard("execute_keystroke", key=key, app_focus=app_focus):
        return
    if Quartz is None:
        return
    KEYCODE = {"p": 35, "S": 1}
    keycode = int(key) if isinstance(key, int) else KEYCODE.get(str(key), 35)
    event_down = Quartz.CGEventCreateKeyboardEvent(None, keycode, True)
    event_up = Quartz.CGEventCreateKeyboardEvent(None, keycode, False)
    Quartz.CGEventSetFlags(event_down, 0)
    Quartz.CGEventSetFlags(event_up, 0)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, event_down)
    time.sleep(0.05)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, event_up)


def execute_global_click(px: int, py: int):
    """Click at image pixel (px, py)."""
    # Try to compute coordinates for dry run log, but don't fail if Quartz unavailable
    gx, gy = None, None
    try:
        gx, gy = _pixel_to_global_quartz(float(px), float(py))
    except (NameError, AttributeError):
        pass  # Quartz/AppKit not available - skip coordinate computation
    
    if _dry_run_guard("execute_global_click", px=px, py=py, gx=gx, gy=gy):
        return
    if Quartz is None:
        return
    if gx is None or gy is None:
        gx, gy = _pixel_to_global_quartz(float(px), float(py))
    pos = Quartz.CGPointMake(gx, gy)
    down = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseDown, pos, Quartz.kCGMouseButtonLeft)
    up = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseUp, pos, Quartz.kCGMouseButtonLeft)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, down)
    time.sleep(0.05)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, up)


def execute_move_mouse(px: int, py: int):
    """Move cursor to image pixel (px, py)."""
    # Try to compute coordinates for dry run log, but don't fail if Quartz unavailable
    gx, gy = None, None
    try:
        gx, gy = _pixel_to_global_quartz(float(px), float(py))
    except (NameError, AttributeError):
        pass  # Quartz/AppKit not available - skip coordinate computation
    
    if _dry_run_guard("execute_move_mouse", px=px, py=py, gx=gx, gy=gy):
        return
    if Quartz is None:
        return
    if gx is None or gy is None:
        gx, gy = _pixel_to_global_quartz(float(px), float(py))
    pos = Quartz.CGPointMake(gx, gy)
    ev = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventMouseMoved, pos, Quartz.kCGMouseButtonLeft)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, ev)


def execute_draw_path_segments(
    path_coordinates: list[tuple[int, int]],
    center_x: int,
    center_y: int,
    drag_delay: float = 0.02,
):
    """
    Draw polygon by releasing mouse at every corner.
    Each segment: mouse_down at A -> drag to B -> mouse_up at B.
    """
    if _dry_run_guard(
        "execute_draw_path_segments",
        n_points=len(path_coordinates),
        center=(center_x, center_y),
        drag_delay=drag_delay,
    ):
        return
    if Quartz is None or len(path_coordinates) < 2:
        return
    global_points = []
    for px, py in path_coordinates:
        gx, gy = _pixel_to_global_quartz(float(center_x + px), float(center_y + py))
        global_points.append((gx, gy))
    n = len(global_points)
    for i in range(n):
        j = (i + 1) % n
        ax, ay = global_points[i]
        bx, by = global_points[j]
        # mouse_down at A
        down = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseDown, Quartz.CGPointMake(ax, ay), Quartz.kCGMouseButtonLeft)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, down)
        time.sleep(0.15)
        # drag to B
        drag = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseDragged, Quartz.CGPointMake(bx, by), Quartz.kCGMouseButtonLeft)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, drag)
        time.sleep(drag_delay)
        # mouse_up at B
        up = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseUp, Quartz.CGPointMake(bx, by), Quartz.kCGMouseButtonLeft)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, up)
        time.sleep(0.1)


# =============================================================================
# PILLAR 3: ORACLE (Gemini 2.5 Pro visual assertions)
# =============================================================================

def assert_visual_state(image_path: str, question: str) -> bool:
    """
    Ask VLM YES/NO about screenshot. Returns True iff YES.
    Uses google.genai + Gemini 2.5 Pro + JSON schema.
    """
    from google import genai
    from google.genai import types
    from pydantic import BaseModel, Field
    class VisualAssertionResult(BaseModel):
        answer: str = Field(description="Exactly one of: YES or NO.")
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY") or os.environ.get("OPENAI_API_KEY"))
    uploaded = client.files.upload(file=image_path)
    response = client.models.generate_content(
        model="gemini-2.5-pro",
        contents=[uploaded, f"{question}\nReply with exactly one word: YES or NO."],
        config=types.GenerateContentConfig(temperature=0.0, response_mime_type="application/json", response_schema=VisualAssertionResult),
    )
    parsed = json.loads(response.text)
    if (parsed.get("answer") or "").strip().upper() != "YES":
        raise RuntimeError(f"Visual Assertion Failed: {question}")
    return True


# =============================================================================
# 12-STEP FLOW (with comments linking to Quartz / Oracle)
# =============================================================================

def run_concentric_triangles_study(evidence_dir: str | None = None):
    """
    Minimal 12-step flow. Each step maps to either Quartz events or an Oracle.
    """
    sizes = [220, 160, 100, 50]
    cre_dir = Path(__file__).parent
    current_state_path = str(cre_dir / "current_state.png")
    cx, cy = get_screenshot_center(current_state_path)

    # Step 1: Quartz - Cmd+Backspace
    execute_clear_canvas()
    # Step 2: Quartz - Enter (keycode 36)
    execute_keystroke(36)
    time.sleep(1.0)
    # Step 3: pause
    time.sleep(0.5)
    # Step 4: Oracle - "Is canvas empty?"
    # (Would call assert_visual_state(assert_path, "Is the Excalidraw canvas empty...")
    # Step 5: pause
    time.sleep(0.5)
    # Step 6: Re-capture, get center
    cx, cy = get_screenshot_center(current_state_path)
    execute_move_mouse(cx, cy)
    time.sleep(0.5)
    # Step 7: pause
    time.sleep(0.5)
    # Step 8: Quartz - 'p' (pen), then Oracle - "Is pen selected?"
    execute_keystroke("p")
    # Step 9: Quartz - 'S' (stroke picker)
    execute_keystroke("S")
    time.sleep(0.3)
    # Step 10: SoM + VLM target extraction + Quartz click (black swatch)
    # (Omitted here - needs visual_engine + visually_extract_target + execute_global_click)
    time.sleep(0.5)
    # Step 11: pause
    time.sleep(0.5)
    # Step 12: Quartz - 4x execute_draw_path_segments, then Oracle - "Four triangles?"
    for size in sizes:
        vertices = triangle_vertices(size)
        execute_draw_path_segments(vertices, cx, cy, drag_delay=0.02)
        time.sleep(0.6)


if __name__ == "__main__":
    if DRY_RUN:
        print("DRY_RUN=1: Logic only, no Quartz events.")
        print("=" * 60)
        # Test coordinate conversion
        print("\n[TEST] Coordinate conversion (center of 2880x1800 screenshot):")
        try:
            gx, gy = _pixel_to_global_quartz(1440.0, 900.0)
            print(f"  Input: (1440, 900) image pixels")
            print(f"  Output: ({gx:.1f}, {gy:.1f}) Quartz global")
        except Exception as e:
            print(f"  Error: {e} (Quartz/AppKit may not be available)")
        
        # Test triangle vertices
        print("\n[TEST] Triangle vertices (size=220, center=(1440, 900)):")
        vertices = triangle_vertices(220)
        print(f"  Relative vertices: {vertices}")
        for vx, vy in vertices:
            px, py = 1440 + vx, 900 + vy
            try:
                gx, gy = _pixel_to_global_quartz(float(px), float(py))
                print(f"    Image ({px}, {py}) → Quartz ({gx:.1f}, {gy:.1f})")
            except Exception as e:
                print(f"    Image ({px}, {py}) → Error: {e}")
        
        # Test screenshot center (if file exists)
        print("\n[TEST] Screenshot center detection:")
        cre_dir = Path(__file__).parent
        current_state_path = cre_dir / "current_state.png"
        if current_state_path.exists():
            try:
                cx, cy = get_screenshot_center(str(current_state_path))
                print(f"  Found current_state.png: center = ({cx}, {cy})")
            except Exception as e:
                print(f"  Error reading screenshot: {e}")
        else:
            print(f"  current_state.png not found at {current_state_path}")
        
        print("\n[TEST] Dry run execution (would execute 12 steps):")
        print("  (Skipping actual execution - use CONCENTRIC_TRIANGLES_CLEAN=1 for real run)")
        print("=" * 60)
    else:
        print("Study file. Run the full test with CONCENTRIC_TRIANGLES_CLEAN=1 for real execution.")
    print("Use CONCENTRIC_DRY_RUN=1 to observe logic without taking over mouse/keyboard.")
