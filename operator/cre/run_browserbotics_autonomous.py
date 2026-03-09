#!/usr/bin/env python3
"""Fully autonomous BrowserBotics run with self-verifying loop (PhD-inspired).

State machine (formal web automation, Leotta-style model):
  LOADED -> EDIT (e2, fill e9) -> RUNNING (e4 Play) -> VERIFY -> PASS | RETRY
Invariants (safety; never violate):
  - Never click Stop (e5) when disabled (e5 is only enabled while run is active).
  - Only click Play (e4) when sandbox is loaded and main.py content is set.
  - Verification uses P1 safety (DOM refs valid), P2 execution (run completed), P3 verification (screenshot check).

Research basis: S. Mitra (2020) runtime verification and barrier certificates for sim autonomy;
  F. Pecora et al. ICRA 2018 automated testing of robotic systems; M. Leotta (2015) model-based web UI testing;
  X. Huang (2019) visual verification in sim (lightweight pixel/variance check here).

Usage:
  ./venv/bin/python cre/run_browserbotics_autonomous.py [--humanoid] [--max-retries 2] [--runs N]
Runs the Safari harness with --humanoid and --verify. With --runs N, chains N runs and verifies
each; pass only if all runs pass. Retries on verification failure (script refresh = re-paste + Run).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
OPERATOR_DIR = REPO_ROOT / "operator"
if str(OPERATOR_DIR) not in sys.path:
    sys.path.insert(0, str(OPERATOR_DIR))

HARNESS = OPERATOR_DIR / "cre" / "run_browserbotics_safari_phd.py"
SCREENSHOTS_DIR = (
    REPO_ROOT / "operator" / "cre" / "project_understanding" / "artifacts" / "browserbotics_phd_screenshots"
)
VENV_PYTHON = OPERATOR_DIR / "venv" / "bin" / "python"


def _run_one_and_verify(humanoid: bool) -> bool:
    """Run harness once; return True iff run succeeded and verification passed."""
    cmd = [str(VENV_PYTHON), str(HARNESS), "--verify"]
    if humanoid:
        cmd.append("--humanoid")
    proc = subprocess.run(cmd, cwd=str(OPERATOR_DIR), text=True)
    if proc.returncode != 0:
        return False
    result_path = SCREENSHOTS_DIR / "verification_result.json"
    if not result_path.exists():
        return False
    data = json.loads(result_path.read_text(encoding="utf-8"))
    return bool(data.get("passed"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Autonomous BrowserBotics run with self-verifying loop.")
    parser.add_argument("--humanoid", action="store_true", help="Use dual-arm humanoid + mobile base script.")
    parser.add_argument("--max-retries", type=int, default=2, help="Max retries on verification failure.")
    parser.add_argument("--runs", type=int, default=1, help="Chain N runs; pass only if all pass (multi-screenshot verify).")
    args = parser.parse_args()

    n_required = max(1, args.runs)
    for run_idx in range(n_required):
        attempt = 0
        while attempt <= args.max_retries:
            attempt += 1
            print(f"Run {run_idx + 1}/{n_required} attempt {attempt}/{args.max_retries + 1} ...")
            if _run_one_and_verify(args.humanoid):
                print("PhD-verified run: PASS.")
                break
            print("Verification failed or harness error. Retry ...")
        else:
            print("Max retries exhausted for this run.")
            return 1
    print("All runs passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
