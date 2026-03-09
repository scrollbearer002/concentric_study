#!/usr/bin/env python3
"""Post a daily macOS reminder for the deferred verification-packet walkthrough."""

from __future__ import annotations

import argparse
import json
import subprocess
import time
from pathlib import Path

TITLE = "Concentric Study"
SUBTITLE = "Deferred follow-up"
BODY = (
    "Review one real VerificationGate packet and walk through how a human "
    "would label it."
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path.home() / "Library/Application Support/ConcentricStudy/verification_packet_walkthrough_reminder",
    )
    return parser.parse_args()


def display_notification(title: str, subtitle: str, body: str) -> None:
    script = (
        f'display notification "{body}" with title "{title}" subtitle "{subtitle}"'
    )
    subprocess.run(["osascript", "-e", script], check=True, capture_output=True, text=True)


def write_log(output_root: Path) -> None:
    output_root.mkdir(parents=True, exist_ok=True)
    payload = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "title": TITLE,
        "subtitle": SUBTITLE,
        "body": BODY,
    }
    latest_path = output_root / "latest_reminder.json"
    latest_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    log_path = output_root / "reminder_log.jsonl"
    with open(log_path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")


def main() -> int:
    args = parse_args()
    display_notification(TITLE, SUBTITLE, BODY)
    write_log(args.output_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
