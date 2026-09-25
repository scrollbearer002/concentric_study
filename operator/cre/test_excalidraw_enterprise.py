#!/usr/bin/env python3
"""
Enterprise Excalidraw test: NSWorkspace focus → screencapture → SoM → Gemini File API → Quartz click.

Uses only agent_core.py and visual_engine.py (no Hammerspoon kernel).
Flow per plan: Initialize MacOSAgentCore and VisualGroundingEngine → Enforce Safari focus →
Capture screenshot (screencapture -x) → Generate SoM overlay and coordinate map →
Upload to Gemini File API and extract target box ID → Lookup coordinates from map →
Execute global click using Quartz.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

# macOS-only: agent_core imports the native Quartz/AppKit stack at import time.
pytest.importorskip("Quartz", reason="macOS-only GUI automation (requires pyobjc/Quartz)")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent_core import MacOSAgentCore
from visual_engine import VisualGroundingEngine


def main() -> int:
    print("\n" + "=" * 60)
    print("ENTERPRISE GUI AGENT - Excalidraw Test")
    print("Focus → Screenshot → SoM → File API → Quartz Click")
    print("=" * 60)

    if not os.environ.get("GEMINI_API_KEY") and not os.environ.get("OPENAI_API_KEY"):
        print("\nGEMINI_API_KEY or OPENAI_API_KEY not set.")
        print("  export GEMINI_API_KEY='your-key'")
        return 1

    cre_dir = Path(__file__).resolve().parent
    current_state_path = str(cre_dir / "current_state.png")
    som_filename = "som_overlay.png"

    agent = MacOSAgentCore()
    vision_engine = VisualGroundingEngine(grid_size=12, output_dir=str(cre_dir))

    try:
        print("\n[1] Enforcing Safari focus (NSWorkspace)...")
        agent.enforce_app_focus("Safari")

        print("\n[2] Capturing uncompressed Retina screenshot (screencapture -x)...")
        subprocess.run(["screencapture", "-x", current_state_path], check=True, timeout=10)

        print("\n[3] Generating Set-of-Mark overlay and coordinate map...")
        coords_map, som_path = vision_engine.generate_som_overlay(
            current_state_path, output_filename=som_filename
        )
        print(f"    {len(coords_map)} target zones mapped.")

        print("\n[4] Gemini File API: extracting target box ID (Excalidraw color picker)...")
        prompt = "Find the Excalidraw color picker tool. Output only the integer box ID."
        target_id = agent.visually_extract_target(prompt, som_path)

        print("\n[5] Lookup coordinates from map and execute Quartz global click...")
        if str(target_id) not in coords_map:
            print(f"    Target ID {target_id} not in coordinate map. Aborting.")
            return 1
        target_x, target_y = coords_map[str(target_id)]
        agent.execute_global_click(target_x, target_y)

        print("\n[6] Execution loop complete.")
        return 0

    except Exception as e:
        print(f"\n[PIPELINE HALTED] {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
