#!/usr/bin/env python3
"""Launch the generated Structurizr atlas through a local Docker-backed viewer."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import time
import webbrowser
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import control_room  # type: ignore


CONTAINER_NAME = "concentric-structurizr-atlas"


def ensure_bundle() -> None:
    snapshot = control_room.CACHE.get_or_build()
    structurizr = snapshot.get("structurizr", {})
    workspace_dsl = structurizr.get("workspace_dsl")
    if not workspace_dsl:
        raise RuntimeError("Structurizr workspace bundle was not generated.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Launch the generated Structurizr atlas with Docker.")
    parser.add_argument("--port", type=int, default=8782)
    parser.add_argument("--open-browser", action="store_true")
    args = parser.parse_args()

    if not control_room.DOCKER_BIN:
        raise RuntimeError("Docker is not installed on this machine.")

    ensure_bundle()
    atlas_dir = control_room.STRUCTURIZR_DIR
    if not atlas_dir.exists():
        raise RuntimeError(f"Structurizr atlas directory does not exist: {atlas_dir}")

    subprocess.run(
        [control_room.DOCKER_BIN, "rm", "-f", CONTAINER_NAME],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )

    run_cmd = [
        control_room.DOCKER_BIN,
        "run",
        "--rm",
        "--name",
        CONTAINER_NAME,
        "-p",
        f"{args.port}:8080",
        "-v",
        f"{atlas_dir}:/usr/local/structurizr",
        "structurizr/lite",
    ]

    if args.open_browser:
        time.sleep(1.0)
        webbrowser.open(f"http://127.0.0.1:{args.port}/")

    subprocess.run(run_cmd, check=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
