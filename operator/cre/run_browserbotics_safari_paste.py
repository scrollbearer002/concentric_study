#!/usr/bin/env python3
"""Minimal Safari automation: paste BrowserBotics build from clipboard and run.

Run from operator dir with: ./venv/bin/python cre/run_browserbotics_safari_paste.py
Requires: Safari open to https://browserbotics.com/sandbox, script in clipboard (pbcopy < cre/browserbotics_phd_build.py).
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

OPERATOR_DIR = Path(__file__).resolve().parents[1]
if str(OPERATOR_DIR) not in sys.path:
    sys.path.insert(0, str(OPERATOR_DIR))

from agent_core import MacOSAgentCore


def main() -> int:
    agent = MacOSAgentCore()
    agent.enforce_app_focus("Safari")
    # Click in code editor (left panel, below toolbar)
    agent.execute_global_click(200, 250)
    time.sleep(0.5)
    # Select all
    agent.execute_keystroke("a", app_focus=None, modifiers=["cmd"])
    time.sleep(0.3)
    # Paste
    agent.execute_keystroke("v", app_focus=None, modifiers=["cmd"])
    time.sleep(0.8)
    # Click Run (green play) — adjust if layout differs
    agent.execute_global_click(110, 80)
    time.sleep(12)
    print("Done. Check Safari for simulation result.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
