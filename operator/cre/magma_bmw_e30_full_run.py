#!/usr/bin/env python3
"""Run full Magma flow: open Safari to canvas, then draw a realistic 1991 BMW M3 E30.

Realism category / PhD arts on www.magma.com. Steps:
  1) Open Safari to www.magma.com, navigate to My artworks, New canvas → Landscape.
  2) Wait for canvas to load.
  3) Draw E30 M3 side profile (contour, wheels, headlight, grille) via Quartz.

Usage (from operator/):
  ./venv/bin/python cre/magma_bmw_e30_full_run.py

Prerequisites: Safari available; Magma.com loads (network). Display 2880x1800 preferred.
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

CRE_DIR = Path(__file__).resolve().parent
OPERATOR_DIR = CRE_DIR.parent
VENV_PYTHON = str(OPERATOR_DIR / "venv" / "bin" / "python")


def main() -> int:
    print("=== Magma: Realistic 1991 BMW M3 E30 (realism / PhD arts) ===\n")

    print("[Phase 1] Opening Magma and creating canvas...")
    r = subprocess.run(
        [VENV_PYTHON, str(CRE_DIR / "magma_open_canvas.py")],
        cwd=str(OPERATOR_DIR),
        timeout=90,
    )
    if r.returncode != 0:
        print("Open canvas step failed. Check Safari and network.")
        return 1

    print("\n[Phase 2] Waiting for canvas to be ready (12s)...")
    time.sleep(12)

    print("\n[Phase 3] Drawing BMW M3 E30 (realism contour)...")
    r2 = subprocess.run(
        [VENV_PYTHON, str(CRE_DIR / "magma_draw_bmw_e30.py")],
        cwd=str(OPERATOR_DIR),
        timeout=60,
    )
    if r2.returncode != 0:
        print("Drawing step failed.")
        return 1

    print("\nDone. Check Safari Magma tab for the E30 drawing.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
