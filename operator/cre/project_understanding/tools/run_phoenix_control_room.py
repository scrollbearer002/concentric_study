#!/usr/bin/env python3
"""Launch local Phoenix plus the Concentric control room with OTel enabled."""

from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
import time
import webbrowser
from pathlib import Path
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[4]
OPERATOR_DIR = ROOT / "operator"
VENV_BIN = OPERATOR_DIR / "venv" / "bin"
PYTHON_BIN = VENV_BIN / "python"
CONTROL_ROOM = ROOT / "operator" / "cre" / "project_understanding" / "tools" / "control_room.py"
SIDECAR_DIR = ROOT / "operator" / "cre" / "local_ops" / "phoenix_sidecar"
SIDECAR_VENV = SIDECAR_DIR / "venv"
SIDECAR_BIN = SIDECAR_VENV / "bin"
PHOENIX_BIN = SIDECAR_BIN / "phoenix"
SIDECAR_REQS = ROOT / "operator" / "cre" / "project_understanding" / "tools" / "requirements-phoenix-sidecar.txt"


def wait_for_http(url: str, timeout_seconds: float = 20.0) -> bool:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            with urlopen(url, timeout=2.0):
                return True
        except Exception:
            time.sleep(0.5)
    return False


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--open-browser", action="store_true")
    parser.add_argument("--project-name", default="concentric-control-room")
    parser.add_argument("--phoenix-ui-url", default="http://127.0.0.1:6006/")
    parser.add_argument("--python39", default="/usr/bin/python3", help="Python interpreter used for the Phoenix sidecar venv bootstrap.")
    return parser.parse_args(argv)


def ensure_sidecar(args: argparse.Namespace) -> int:
    SIDECAR_DIR.mkdir(parents=True, exist_ok=True)
    if not SIDECAR_VENV.exists():
        subprocess.run([args.python39, "-m", "venv", str(SIDECAR_VENV)], check=True, cwd=str(ROOT))

    pip_bin = SIDECAR_BIN / "pip"
    if not PHOENIX_BIN.exists():
        subprocess.run([str(pip_bin), "install", "-r", str(SIDECAR_REQS)], check=True, cwd=str(ROOT))
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if not PYTHON_BIN.exists():
        print(f"Repo venv python not found at {PYTHON_BIN}", file=sys.stderr)
        return 1
    try:
        ensure_sidecar(args)
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        print(f"Failed to prepare Phoenix sidecar: {exc}", file=sys.stderr)
        print("This machine needs a compatible Python (for example python3.9) to bootstrap the Phoenix sidecar.", file=sys.stderr)
        return 1

    phoenix_proc = subprocess.Popen([str(PHOENIX_BIN), "serve"], cwd=str(SIDECAR_DIR))
    try:
        if not wait_for_http(args.phoenix_ui_url):
            print("Phoenix UI did not become ready in time.", file=sys.stderr)
            return 1

        env = os.environ.copy()
        env["CONCENTRIC_OTEL_ENABLE"] = "1"
        env["PHOENIX_PROJECT_NAME"] = args.project_name
        env["PHOENIX_COLLECTOR_ENDPOINT"] = "http://127.0.0.1:6006/v1/traces"

        control_room_proc = subprocess.Popen(
            [str(PYTHON_BIN), str(CONTROL_ROOM), "--host", args.host, "--port", str(args.port)],
            cwd=str(ROOT),
            env=env,
        )
        try:
            if args.open_browser:
                webbrowser.open(args.phoenix_ui_url)
                webbrowser.open(f"http://{args.host}:{args.port}/")
            print(f"Phoenix sidecar: {SIDECAR_VENV}")
            print(f"Phoenix UI: {args.phoenix_ui_url}")
            print(f"Control room: http://{args.host}:{args.port}/")
            print("Press Ctrl-C to stop both.")
            while True:
                if phoenix_proc.poll() is not None or control_room_proc.poll() is not None:
                    return control_room_proc.returncode or phoenix_proc.returncode or 0
                time.sleep(0.5)
        finally:
            if control_room_proc.poll() is None:
                control_room_proc.send_signal(signal.SIGINT)
                control_room_proc.wait(timeout=5)
    except KeyboardInterrupt:
        return 0
    finally:
        if phoenix_proc.poll() is None:
            phoenix_proc.send_signal(signal.SIGINT)
            phoenix_proc.wait(timeout=5)


if __name__ == "__main__":
    raise SystemExit(main())
