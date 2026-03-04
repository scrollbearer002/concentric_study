#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
CRE_DIR = ROOT / "cre"
FIXTURE = CRE_DIR / "fixtures" / "preclick_demo.html"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import agent_infra.action_handlers as action_handlers
from agent_core import MacOSAgentCore
from visual_engine import VisualGroundingEngine


def _open_in_safari(url: str) -> None:
    script = f'''
    tell application "Safari"
      activate
      if (count of windows) = 0 then
        make new document with properties {{URL:"{url}"}}
      else
        set URL of current tab of front window to "{url}"
      end if
    end tell
    '''
    subprocess.run(["osascript", "-e", script], check=True, timeout=15)


def _js(expr: str) -> str:
    script = f'''
    tell application "Safari"
      return do JavaScript "{expr}" in current tab of front window
    end tell
    '''
    proc = subprocess.run(["osascript", "-e", script], check=True, capture_output=True, text=True, timeout=15)
    return (proc.stdout or "").strip()


def main() -> None:
    fixture_url = FIXTURE.resolve().as_uri()
    _open_in_safari(fixture_url)
    time.sleep(2.0)

    status_before = _js("document.getElementById('status').textContent")

    screenshot_path = CRE_DIR / "preclick_smoke_display.png"
    som_path = CRE_DIR / "preclick_smoke_som.png"
    subprocess.run(["screencapture", "-x", str(screenshot_path)], check=True, timeout=10)

    agent = MacOSAgentCore()
    engine = VisualGroundingEngine(grid_size=12, output_dir=str(CRE_DIR))
    coords_map, generated_path = engine.generate_som_overlay(str(screenshot_path), output_filename=som_path.name)
    target_id = agent.visually_extract_target(
        "Find the large blue button labeled 'Continue Safely'. Output only the integer box ID.",
        generated_path,
    )
    pixel_x, pixel_y = coords_map[str(target_id)]

    ctx = SimpleNamespace(
        use_enterprise=True,
        agent=agent,
        cre_dir=CRE_DIR,
        url=fixture_url,
    )

    click_result = action_handlers._handle_click(
        ctx,
        {
            "x": pixel_x,
            "y": pixel_y,
            "label": "Continue Safely",
            "expected_effect": "Change the status text from 'Awaiting confirmed click' to 'Clicked safely'.",
            "confirm_before_click": True,
        },
    )
    time.sleep(1.0)

    status_after = _js("document.getElementById('status').textContent")
    result = {
        "fixture_url": fixture_url,
        "status_before": status_before,
        "target_id": target_id,
        "target_pixel": [pixel_x, pixel_y],
        "click_result": click_result,
        "status_after": status_after,
        "screenshot_path": str(screenshot_path),
        "som_path": str(som_path),
    }
    out_path = CRE_DIR / "preclick_smoke_result.json"
    out_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
