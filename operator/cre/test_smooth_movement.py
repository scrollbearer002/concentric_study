#!/usr/bin/env python3
"""
Test smooth mouse movement with Bezier curves.
Demonstrates human-like movement vs. teleporting.
"""

import sys
from pathlib import Path

# Add operator to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from codex_client import CodexClient
import time

def test_smooth_circle(client: CodexClient, center_x: int, center_y: int, radius: int = 100):
    """Draw a smooth circle using Bezier curve movement."""
    print(f"Drawing circle at ({center_x}, {center_y}) with radius {radius}")
    
    steps = 40
    import math
    
    for i in range(steps + 1):
        angle = (i / steps) * 2 * math.pi
        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)
        
        client.move_mouse(int(x), int(y))
        time.sleep(0.02)  # 20ms per step = smooth movement
    
    print("Circle complete!")

def test_smooth_figure_eight(client: CodexClient, center_x: int, center_y: int, radius: int = 80):
    """Draw a figure-eight using smooth Bezier curves."""
    print(f"Drawing figure-eight at ({center_x}, {center_y})")
    
    steps_per_loop = 30
    
    # First loop (top)
    for i in range(steps_per_loop):
        t = i / steps_per_loop
        angle = t * 2 * math.pi
        # Figure-eight parametric equations
        x = center_x + radius * math.sin(angle)
        y = center_y - 50 + radius * math.sin(angle) * math.cos(angle)
        client.move_mouse(int(x), int(y))
        time.sleep(0.02)
    
    # Second loop (bottom, overlapping)
    for i in range(steps_per_loop):
        t = i / steps_per_loop
        angle = t * 2 * math.pi
        x = center_x + radius * math.sin(angle)
        y = center_y + 50 - radius * math.sin(angle) * math.cos(angle)
        client.move_mouse(int(x), int(y))
        time.sleep(0.02)
    
    print("Figure-eight complete!")

if __name__ == "__main__":
    client = CodexClient()
    
    # Get current mouse position as starting point
    try:
        pos = client.get_mouse_position()
        center_x = pos.get("x", 720)
        center_y = pos.get("y", 450)
        print(f"Starting from mouse position: ({center_x}, {center_y})")
    except Exception as e:
        print(f"Could not get mouse position: {e}")
        center_x, center_y = 720, 450  # Default center
        print(f"Using default center: ({center_x}, {center_y})")
    
    print("\n=== Test 1: Smooth Circle ===")
    test_smooth_circle(client, center_x, center_y, radius=100)
    
    time.sleep(1)
    
    print("\n=== Test 2: Smooth Figure-Eight ===")
    test_smooth_figure_eight(client, center_x, center_y, radius=80)
    
    print("\n✅ Smooth movement tests complete!")
    print("Open a drawing app (Freeform, web canvas) and run this script to see smooth curves.")
