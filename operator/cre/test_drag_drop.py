#!/usr/bin/env python3
"""
Test drag-and-drop functionality.
Demonstrates complex state machine: See -> Think -> Smooth Move -> Drag -> Verify
"""

import sys
from pathlib import Path

# Add operator to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from codex_client import CodexClient
import time

def test_drag(client: CodexClient, start_x: int, start_y: int, end_x: int, end_y: int):
    """Test smooth drag operation."""
    print(f"Dragging from ({start_x}, {start_y}) to ({end_x}, {end_y})")
    
    result = client.drag(start_x, start_y, end_x, end_y)
    print(f"Drag result: {result}")
    return result.get("status") == "ok"

if __name__ == "__main__":
    client = CodexClient()
    
    # Example: Drag from top-left to bottom-right
    # Adjust coordinates based on your screen
    print("=== Test: Drag Operation ===")
    print("This will drag from (100, 100) to (800, 600)")
    print("Make sure you have a window/app open that supports drag-and-drop")
    print("Starting in 3 seconds...")
    
    time.sleep(3)
    
    success = test_drag(client, 100, 100, 800, 600)
    
    if success:
        print("✅ Drag test complete!")
    else:
        print("❌ Drag test failed")
