#!/usr/bin/env python3
"""
Test the dry run flow - shows what would execute without posting Quartz events.
"""

import os
import sys
from pathlib import Path

# Set dry run mode
os.environ["CONCENTRIC_DRY_RUN"] = "1"

# Import after setting env var
sys.path.insert(0, str(Path(__file__).parent))
from study_concentric_logic import (
    DRY_RUN,
    get_screenshot_center,
    triangle_vertices,
    execute_clear_canvas,
    execute_keystroke,
    execute_move_mouse,
    execute_draw_path_segments,
    _pixel_to_global_quartz,
)

def test_dry_run_flow():
    """Simulate the 12-step flow in dry run mode."""
    print("=" * 60)
    print("DRY RUN FLOW TEST - 12 Steps (No Quartz Events)")
    print("=" * 60)
    
    assert DRY_RUN, "DRY_RUN should be True"
    print(f"✅ DRY_RUN mode: {DRY_RUN}\n")
    
    # Simulate screenshot center (would come from actual screenshot)
    center_x, center_y = 1440, 900
    print(f"[Step 6] Screenshot center: ({center_x}, {center_y})")
    
    # Step 1: Clear canvas
    print("\n[Step 1] execute_clear_canvas()")
    execute_clear_canvas()
    
    # Step 2: Enter
    print("\n[Step 2] execute_keystroke(36) - Enter")
    execute_keystroke(36)
    
    # Step 8: Pen tool
    print("\n[Step 8] execute_keystroke('p') - Pen tool")
    execute_keystroke("p")
    
    # Step 9: Stroke picker
    print("\n[Step 9] execute_keystroke('S') - Stroke picker")
    execute_keystroke("S")
    
    # Step 6: Move mouse to center
    print("\n[Step 6] execute_move_mouse(cx, cy)")
    execute_move_mouse(center_x, center_y)
    
    # Step 12: Draw triangles
    print("\n[Step 12] Drawing 4 concentric triangles:")
    sizes = [220, 160, 100, 50]
    for i, size in enumerate(sizes, 1):
        vertices = triangle_vertices(size)
        print(f"\n  Triangle {i}/4 (size={size}):")
        print(f"    Vertices: {vertices}")
        execute_draw_path_segments(vertices, center_x, center_y, drag_delay=0.02)
    
    print("\n" + "=" * 60)
    print("✅ DRY RUN FLOW COMPLETE")
    print("=" * 60)
    print("\nNote: All Quartz events were logged but NOT posted.")
    print("      Mouse/keyboard remain untouched.")


if __name__ == "__main__":
    try:
        test_dry_run_flow()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
