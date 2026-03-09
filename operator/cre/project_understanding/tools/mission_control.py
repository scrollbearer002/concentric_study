#!/usr/bin/env python3
"""Profile-based mission supervisor for the Concentric local control stack."""

from __future__ import annotations

import argparse
import json
import os
import signal
import shutil
import socket
import subprocess
import sys
import time
import webbrowser
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[4]
OPERATOR_DIR = ROOT / "operator"
TOOLS_DIR = Path(__file__).resolve().parent
VENV_PYTHON = OPERATOR_DIR / "venv" / "bin" / "python"
CONTROL_ROOM_PATH = TOOLS_DIR / "control_room.py"
RUN_PHOENIX_PATH = TOOLS_DIR / "run_phoenix_control_room.py"
RUN_STRUCTURIZR_PATH = TOOLS_DIR / "run_structurizr_atlas.py"
GUI_EVIDENCE_PATH = TOOLS_DIR / "gui_evidence.py"
GENERATED_DIR = ROOT / "operator" / "cre" / "project_understanding" / "artifacts" / "control_room_generated"
MISSION_DIR = GENERATED_DIR / "mission_control"
STATE_FILE = MISSION_DIR / "state.json"
LOGS_DIR = MISSION_DIR / "logs"

PHOENIX_HOST = "127.0.0.1"
PHOENIX_PORT = 6006
CONTROL_ROOM_HOST = "127.0.0.1"
CONTROL_ROOM_PORT = 8765
STRUCTURIZR_HOST = "127.0.0.1"
STRUCTURIZR_PORT = 8782
PHOENIX_PROJECT_NAME = "concentric-control-room"

DEFAULT_PROFILES: dict[str, list[str]] = {
    "live": ["phoenix", "control_room"],
    "debug": ["phoenix", "control_room"],
    "architecture": ["control_room", "structurizr"],
    "full": ["phoenix", "control_room", "structurizr"],
}


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def ensure_dirs() -> None:
    MISSION_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)


def load_state() -> dict[str, Any]:
    if not STATE_FILE.exists():
        return {"updated_at": None, "services": {}}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"updated_at": None, "services": {}}


def save_state(state: dict[str, Any]) -> None:
    ensure_dirs()
    state["updated_at"] = now_iso()
    STATE_FILE.write_text(json.dumps(state, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def process_alive(pid: int | None) -> bool:
    if not pid:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def port_open(host: str, port: int, timeout: float = 0.5) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        return sock.connect_ex((host, port)) == 0


def port_listener_pids(port: int) -> list[int]:
    lsof_bin = shutil.which("lsof")
    if not lsof_bin:
        return []
    result = subprocess.run(
        [lsof_bin, "-nP", f"-iTCP:{port}", "-sTCP:LISTEN", "-t"],
        capture_output=True,
        text=True,
        timeout=5,
    )
    if result.returncode != 0:
        return []
    pids: list[int] = []
    for line in (result.stdout or "").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            pids.append(int(line))
        except ValueError:
            continue
    return pids


def command_line_for_pid(pid: int) -> str:
    try:
        result = subprocess.run(
            ["ps", "-p", str(pid), "-o", "command="],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except Exception:
        return ""
    if result.returncode != 0:
        return ""
    return (result.stdout or "").strip()


def terminate_pid(pid: int, *, grace_seconds: float = 5.0) -> bool:
    if not process_alive(pid):
        return True
    try:
        os.kill(pid, signal.SIGINT)
    except OSError:
        return False
    if wait_for(lambda: not process_alive(pid), timeout_seconds=grace_seconds, interval_seconds=0.2):
        return True
    try:
        os.kill(pid, signal.SIGTERM)
    except OSError:
        return False
    return wait_for(lambda: not process_alive(pid), timeout_seconds=grace_seconds, interval_seconds=0.2)


def reclaim_port_if_known_service(port: int, command_markers: tuple[str, ...]) -> bool:
    reclaimed = False
    for pid in port_listener_pids(port):
        command = command_line_for_pid(pid)
        if command and any(marker in command for marker in command_markers):
            terminate_pid(pid)
            reclaimed = True
    return reclaimed


def fetch_text(url: str, timeout: float = 2.0) -> str | None:
    try:
        with urlopen(url, timeout=timeout) as response:
            return response.read().decode("utf-8", errors="replace")
    except (HTTPError, URLError, TimeoutError):
        return None
    except Exception:
        return None


def fetch_json(url: str, timeout: float = 2.0) -> dict[str, Any] | None:
    payload = fetch_text(url, timeout=timeout)
    if not payload:
        return None
    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        return None


def wait_for(check, timeout_seconds: float = 20.0, interval_seconds: float = 0.5) -> bool:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if check():
            return True
        time.sleep(interval_seconds)
    return False


def open_urls(urls: list[str]) -> None:
    for url in urls:
        webbrowser.open(url)


def import_control_room():
    if str(TOOLS_DIR) not in sys.path:
        sys.path.insert(0, str(TOOLS_DIR))
    import control_room  # type: ignore

    return control_room


def import_phoenix_launcher():
    if str(TOOLS_DIR) not in sys.path:
        sys.path.insert(0, str(TOOLS_DIR))
    import run_phoenix_control_room  # type: ignore

    return run_phoenix_control_room


def control_room_status() -> dict[str, Any]:
    url = f"http://{CONTROL_ROOM_HOST}:{CONTROL_ROOM_PORT}/api/state"
    payload = fetch_json(url)
    healthy = payload is not None
    observability = payload.get("observability", {}) if payload else {}
    return {
        "service_id": "control_room",
        "healthy": healthy,
        "host": CONTROL_ROOM_HOST,
        "port": CONTROL_ROOM_PORT,
        "url": f"http://{CONTROL_ROOM_HOST}:{CONTROL_ROOM_PORT}/",
        "api_url": url,
        "observability_enabled": bool(observability.get("enabled")),
        "observability_project": observability.get("project_name"),
        "status": payload.get("status") if payload else None,
    }


def phoenix_status() -> dict[str, Any]:
    url = f"http://{PHOENIX_HOST}:{PHOENIX_PORT}/"
    body = fetch_text(url)
    return {
        "service_id": "phoenix",
        "healthy": body is not None,
        "host": PHOENIX_HOST,
        "port": PHOENIX_PORT,
        "url": url,
    }


def structurizr_status() -> dict[str, Any]:
    root_url = f"http://{STRUCTURIZR_HOST}:{STRUCTURIZR_PORT}/"
    body = fetch_text(root_url)
    return {
        "service_id": "structurizr",
        "healthy": body is not None,
        "host": STRUCTURIZR_HOST,
        "port": STRUCTURIZR_PORT,
        "url": root_url,
    }


@dataclass(frozen=True)
class ServiceSpec:
    service_id: str
    display_name: str
    profile_ids: tuple[str, ...]
    url: str
    port: int
    start_fn: Any
    status_fn: Any


def start_detached(command: list[str], *, env: dict[str, str] | None, log_path: Path, cwd: Path) -> int:
    ensure_dirs()
    with log_path.open("ab") as log_handle:
        proc = subprocess.Popen(
            command,
            cwd=str(cwd),
            env=env,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    return proc.pid


def start_phoenix() -> dict[str, Any]:
    launcher = import_phoenix_launcher()
    args = SimpleNamespace(python39="/usr/bin/python3")
    launcher.ensure_sidecar(args)
    log_path = LOGS_DIR / "phoenix.log"
    pid = start_detached(
        [str(launcher.PHOENIX_BIN), "serve"],
        env=os.environ.copy(),
        log_path=log_path,
        cwd=launcher.SIDECAR_DIR,
    )
    healthy = wait_for(lambda: phoenix_status()["healthy"], timeout_seconds=25.0)
    return {
        "pid": pid,
        "log_path": str(log_path),
        "healthy": healthy,
        "url": f"http://{PHOENIX_HOST}:{PHOENIX_PORT}/",
    }


def start_control_room(*, with_observability: bool) -> dict[str, Any]:
    if not VENV_PYTHON.exists():
        raise RuntimeError(f"Repo venv python not found at {VENV_PYTHON}")
    env = os.environ.copy()
    if with_observability:
        env["CONCENTRIC_OTEL_ENABLE"] = "1"
        env["PHOENIX_PROJECT_NAME"] = PHOENIX_PROJECT_NAME
        env["PHOENIX_COLLECTOR_ENDPOINT"] = f"http://{PHOENIX_HOST}:{PHOENIX_PORT}/v1/traces"
    log_path = LOGS_DIR / "control_room.log"
    pid = start_detached(
        [
            str(VENV_PYTHON),
            str(CONTROL_ROOM_PATH),
            "--host",
            CONTROL_ROOM_HOST,
            "--port",
            str(CONTROL_ROOM_PORT),
        ],
        env=env,
        log_path=log_path,
        cwd=ROOT,
    )
    healthy = wait_for(
        lambda: (
            control_room_status()["healthy"]
            and (not with_observability or control_room_status()["observability_enabled"])
        ),
        timeout_seconds=35.0,
    )
    return {
        "pid": pid,
        "log_path": str(log_path),
        "healthy": healthy,
        "url": f"http://{CONTROL_ROOM_HOST}:{CONTROL_ROOM_PORT}/",
        "observability_enabled": with_observability,
    }


def start_structurizr() -> dict[str, Any]:
    if not VENV_PYTHON.exists():
        raise RuntimeError(f"Repo venv python not found at {VENV_PYTHON}")
    if not shutil.which("docker"):
        raise RuntimeError("Docker is not installed on this machine.")
    control_room = import_control_room()
    control_room.CACHE.get_or_build()
    log_path = LOGS_DIR / "structurizr.log"
    pid = start_detached(
        [str(VENV_PYTHON), str(RUN_STRUCTURIZR_PATH), "--port", str(STRUCTURIZR_PORT)],
        env=os.environ.copy(),
        log_path=log_path,
        cwd=ROOT,
    )
    healthy = wait_for(lambda: structurizr_status()["healthy"], timeout_seconds=60.0)
    return {
        "pid": pid,
        "log_path": str(log_path),
        "healthy": healthy,
        "url": f"http://{STRUCTURIZR_HOST}:{STRUCTURIZR_PORT}/",
    }


def service_specs() -> dict[str, ServiceSpec]:
    return {
        "phoenix": ServiceSpec(
            service_id="phoenix",
            display_name="Phoenix",
            profile_ids=("live", "debug", "full"),
            url=f"http://{PHOENIX_HOST}:{PHOENIX_PORT}/",
            port=PHOENIX_PORT,
            start_fn=start_phoenix,
            status_fn=phoenix_status,
        ),
        "control_room": ServiceSpec(
            service_id="control_room",
            display_name="Concentric Control Room",
            profile_ids=("live", "debug", "architecture", "full"),
            url=f"http://{CONTROL_ROOM_HOST}:{CONTROL_ROOM_PORT}/",
            port=CONTROL_ROOM_PORT,
            start_fn=None,
            status_fn=control_room_status,
        ),
        "structurizr": ServiceSpec(
            service_id="structurizr",
            display_name="Structurizr Atlas",
            profile_ids=("architecture", "full"),
            url=f"http://{STRUCTURIZR_HOST}:{STRUCTURIZR_PORT}/",
            port=STRUCTURIZR_PORT,
            start_fn=start_structurizr,
            status_fn=structurizr_status,
        ),
    }


def desired_services(profile: str) -> list[str]:
    if profile not in DEFAULT_PROFILES:
        raise ValueError(f"Unknown profile: {profile}")
    return DEFAULT_PROFILES[profile]


def record_service_state(
    state: dict[str, Any],
    *,
    service_id: str,
    profile: str,
    runtime: dict[str, Any],
) -> None:
    state.setdefault("services", {})[service_id] = {
        "pid": runtime.get("pid"),
        "profile": profile,
        "started_at": now_iso(),
        "log_path": runtime.get("log_path"),
        "url": runtime.get("url"),
        "port": service_specs()[service_id].port,
        "managed": True,
        "metadata": {
            key: value
            for key, value in runtime.items()
            if key not in {"pid", "log_path", "healthy", "url"}
        },
    }


def clear_service_state(state: dict[str, Any], service_id: str) -> None:
    state.setdefault("services", {}).pop(service_id, None)


def satisfy_control_room(profile: str, state: dict[str, Any]) -> dict[str, Any]:
    current = control_room_status()
    requires_obs = profile in {"live", "debug", "full"}
    if current["healthy"] and (not requires_obs or current["observability_enabled"]):
        return {"reused": True, "healthy": True, "url": current["url"]}

    existing = state.get("services", {}).get("control_room")
    if current["healthy"] and requires_obs and not current["observability_enabled"]:
        reclaimed = False
        if existing and process_alive(existing.get("pid")):
            terminate_pid(existing["pid"])
            reclaimed = True
        else:
            reclaimed = reclaim_port_if_known_service(CONTROL_ROOM_PORT, ("control_room.py",))
        if not reclaimed:
            raise RuntimeError(
                "A control room is already running on the default port without Phoenix/OpenTelemetry enabled. "
                "Stop it first or run `mission_control down --all` if it is managed by this supervisor."
            )
        wait_for(lambda: not port_open(CONTROL_ROOM_HOST, CONTROL_ROOM_PORT), timeout_seconds=10.0)
    if port_open(CONTROL_ROOM_HOST, CONTROL_ROOM_PORT) and not current["healthy"]:
        reclaimed = False
        if existing and process_alive(existing.get("pid")):
            terminate_pid(existing["pid"])
            reclaimed = True
        else:
            reclaimed = reclaim_port_if_known_service(CONTROL_ROOM_PORT, ("control_room.py",))
        if not reclaimed:
            raise RuntimeError(f"Port {CONTROL_ROOM_PORT} is occupied by a non-healthy control-room process.")
        wait_for(lambda: not port_open(CONTROL_ROOM_HOST, CONTROL_ROOM_PORT), timeout_seconds=10.0)
    if existing and process_alive(existing.get("pid")):
        terminate_pid(existing["pid"])
        wait_for(lambda: not port_open(CONTROL_ROOM_HOST, CONTROL_ROOM_PORT), timeout_seconds=10.0)
    runtime = start_control_room(with_observability=requires_obs)
    record_service_state(state, service_id="control_room", profile=profile, runtime=runtime)
    return {"reused": False, **runtime}


def satisfy_service(service_id: str, profile: str, state: dict[str, Any]) -> dict[str, Any]:
    specs = service_specs()
    spec = specs[service_id]
    if service_id == "control_room":
        return satisfy_control_room(profile, state)

    current = spec.status_fn()
    if current["healthy"]:
        return {"reused": True, "healthy": True, "url": current["url"]}
    if port_open("127.0.0.1", spec.port) and not current["healthy"]:
        raise RuntimeError(f"Port {spec.port} is occupied but {service_id} is not healthy.")
    runtime = spec.start_fn()
    record_service_state(state, service_id=service_id, profile=profile, runtime=runtime)
    return {"reused": False, **runtime}


def up_profile(profile: str, *, open_browser: bool) -> dict[str, Any]:
    ensure_dirs()
    state = load_state()
    results: dict[str, Any] = {"profile": profile, "services": {}, "opened_urls": []}
    for service_id in desired_services(profile):
        result = satisfy_service(service_id, profile, state)
        results["services"][service_id] = result
    save_state(state)
    if open_browser:
        urls = [result["url"] for result in results["services"].values() if result.get("healthy") and result.get("url")]
        open_urls(urls)
        results["opened_urls"] = urls
    return results


def stop_service(service_id: str, state: dict[str, Any]) -> dict[str, Any]:
    specs = service_specs()
    record = state.get("services", {}).get(service_id)
    stopped = False
    if service_id == "structurizr" and shutil.which("docker"):
        subprocess.run([shutil.which("docker"), "rm", "-f", "concentric-structurizr-atlas"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        stopped = True
    if record and process_alive(record.get("pid")):
        try:
            os.kill(record["pid"], signal.SIGINT)
            stopped = True
        except OSError:
            pass
    clear_service_state(state, service_id)
    return {"service_id": service_id, "stopped": stopped, "healthy_after": specs[service_id].status_fn()["healthy"]}


def down_profile(profile: str | None = None, *, all_services: bool = False) -> dict[str, Any]:
    state = load_state()
    target_ids = list(service_specs().keys()) if all_services or profile is None else desired_services(profile)
    results = [stop_service(service_id, state) for service_id in target_ids]
    save_state(state)
    return {"profile": profile, "all": all_services or profile is None, "results": results}


def status_payload() -> dict[str, Any]:
    state = load_state()
    services: list[dict[str, Any]] = []
    for service_id, spec in service_specs().items():
        live = spec.status_fn()
        record = state.get("services", {}).get(service_id, {})
        services.append(
            {
                "service_id": service_id,
                "display_name": spec.display_name,
                "healthy": live["healthy"],
                "url": live["url"],
                "port": spec.port,
                "managed": bool(record),
                "pid": record.get("pid"),
                "pid_alive": process_alive(record.get("pid")) if record else False,
                "started_at": record.get("started_at"),
                "log_path": record.get("log_path"),
                "metadata": record.get("metadata", {}),
                "live": live,
            }
        )
    return {
        "generated_at": now_iso(),
        "profiles": DEFAULT_PROFILES,
        "state_file": str(STATE_FILE),
        "services": services,
    }


def docker_daemon_running() -> bool:
    docker_bin = shutil.which("docker")
    if not docker_bin:
        return False
    result = subprocess.run([docker_bin, "info"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return result.returncode == 0


def gui_evidence_runtime_payload() -> dict[str, Any]:
    if not VENV_PYTHON.exists():
        return {"ok": False, "error": f"Repo venv python not found at {VENV_PYTHON}"}
    script = "import json; import Quartz; from AppKit import NSWorkspace; print(json.dumps({'ok': True, 'quartz': True, 'appkit': True}))"
    result = subprocess.run(
        [str(VENV_PYTHON), "-c", script],
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode != 0:
        return {
            "ok": False,
            "error": (result.stderr or result.stdout).strip() or "GUI evidence runtime check failed.",
        }
    try:
        payload = json.loads(result.stdout.strip())
    except json.JSONDecodeError:
        return {"ok": False, "error": f"Unexpected GUI evidence runtime payload: {result.stdout.strip()}"}
    payload["python"] = str(VENV_PYTHON)
    payload["script"] = str(GUI_EVIDENCE_PATH)
    return payload


def doctor_payload() -> dict[str, Any]:
    report: dict[str, Any] = {
        "generated_at": now_iso(),
        "checks": {},
    }
    report["checks"]["repo_venv_python"] = {
        "ok": VENV_PYTHON.exists(),
        "path": str(VENV_PYTHON),
    }
    report["checks"]["d2"] = {"ok": shutil.which("d2") is not None, "path": shutil.which("d2")}
    report["checks"]["structurizr_cli"] = {"ok": shutil.which("structurizr-cli") is not None or shutil.which("structurizr") is not None}
    report["checks"]["graphviz_dot"] = {"ok": shutil.which("dot") is not None, "path": shutil.which("dot")}
    report["checks"]["docker_binary"] = {"ok": shutil.which("docker") is not None, "path": shutil.which("docker")}
    report["checks"]["docker_daemon"] = {"ok": docker_daemon_running()}
    report["checks"]["sourcegraph_repo"] = {
        "ok": True,
        "repo_name": import_control_room().sourcegraph_repo_name(),
        "base_url": import_control_room().sourcegraph_base_url(),
    }
    phoenix_launcher = import_phoenix_launcher()
    report["checks"]["phoenix_sidecar_ready"] = {
        "ok": phoenix_launcher.PHOENIX_BIN.exists(),
        "sidecar_python": str(phoenix_launcher.PYTHON_BIN),
        "sidecar_bin": str(phoenix_launcher.PHOENIX_BIN),
    }
    report["checks"]["gui_evidence_runtime"] = gui_evidence_runtime_payload()
    try:
        snapshot = import_control_room().CACHE.get_or_build()
        report["checks"]["control_room_snapshot"] = {
            "ok": True,
            "status": snapshot.get("status"),
            "observability_available": snapshot.get("observability", {}).get("available"),
        }
    except Exception as exc:
        report["checks"]["control_room_snapshot"] = {
            "ok": False,
            "error": str(exc),
        }
    report["overall_ok"] = all(bool(item.get("ok")) for item in report["checks"].values() if item is not None)
    return report


def evidence_payload(
    app_name: str,
    *,
    require_frontmost: bool,
    capture: bool,
    strict: bool,
) -> dict[str, Any]:
    if not VENV_PYTHON.exists():
        raise RuntimeError(f"Repo venv python not found at {VENV_PYTHON}")
    cmd = [str(VENV_PYTHON), str(GUI_EVIDENCE_PATH), "--app", app_name]
    if require_frontmost:
        cmd.append("--require-frontmost")
    if capture:
        cmd.append("--capture")
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=20,
    )
    if result.returncode != 0:
        raise RuntimeError((result.stderr or result.stdout).strip() or "GUI evidence command failed.")
    try:
        payload = json.loads(result.stdout.strip())
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Unexpected GUI evidence payload: {result.stdout.strip()}") from exc
    if strict and not payload.get("ready_for_visible_task"):
        blockers = payload.get("blockers") or ["GUI evidence gate did not pass."]
        raise RuntimeError(
            f"Visible-task evidence gate failed for {app_name}: " + " ".join(str(item) for item in blockers)
        )
    return payload


def restart_profile(profile: str, *, open_browser: bool) -> dict[str, Any]:
    down_profile(profile)
    return up_profile(profile, open_browser=open_browser)


def open_profile_urls(profile: str) -> dict[str, Any]:
    status = status_payload()
    targets = set(desired_services(profile))
    urls = [service["url"] for service in status["services"] if service["service_id"] in targets and service["healthy"]]
    open_urls(urls)
    return {"profile": profile, "opened_urls": urls}


def print_text_status(payload: dict[str, Any]) -> None:
    print(f"Mission Control status @ {payload['generated_at']}")
    for service in payload["services"]:
        line = f"- {service['display_name']}: {'healthy' if service['healthy'] else 'down'} @ {service['url']}"
        if service["managed"]:
            line += f" (pid={service['pid']}, managed)"
        print(line)


def print_text_doctor(payload: dict[str, Any]) -> None:
    print(f"Mission Control doctor @ {payload['generated_at']}")
    for name, check in payload["checks"].items():
        print(f"- {name}: {'ok' if check.get('ok') else 'needs attention'}")
        for key, value in check.items():
            if key != "ok" and value is not None:
                print(f"    {key}: {value}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON output.")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--json", action="store_true", help=argparse.SUPPRESS)
    subparsers = parser.add_subparsers(dest="command", required=True)

    up_parser = subparsers.add_parser("up", help="Bring up a mission-control profile.", parents=[common])
    up_parser.add_argument("profile", choices=sorted(DEFAULT_PROFILES))
    up_parser.add_argument("--open", action="store_true", help="Open the healthy service URLs in a browser.")

    restart_parser = subparsers.add_parser("restart", help="Restart a mission-control profile.", parents=[common])
    restart_parser.add_argument("profile", choices=sorted(DEFAULT_PROFILES))
    restart_parser.add_argument("--open", action="store_true", help="Open the healthy service URLs in a browser.")

    down_parser = subparsers.add_parser("down", help="Stop a profile or all managed services.", parents=[common])
    down_parser.add_argument("profile", nargs="?", choices=sorted(DEFAULT_PROFILES))
    down_parser.add_argument("--all", action="store_true", help="Stop all managed services.")

    open_parser = subparsers.add_parser("open", help="Open healthy service URLs for a profile.", parents=[common])
    open_parser.add_argument("profile", choices=sorted(DEFAULT_PROFILES))

    subparsers.add_parser("status", help="Show current managed and live service status.", parents=[common])
    subparsers.add_parser("doctor", help="Run environment and stack health checks.", parents=[common])
    evidence_parser = subparsers.add_parser(
        "evidence",
        help="Run the GUI evidence protocol for a visible macOS task target.",
        parents=[common],
    )
    evidence_parser.add_argument("app", nargs="?", default="Safari")
    evidence_parser.add_argument("--require-frontmost", action="store_true")
    evidence_parser.add_argument("--capture", action="store_true")
    evidence_parser.add_argument("--strict", action="store_true", help="Exit non-zero if the visible-task evidence gate fails.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.command == "up":
            payload = up_profile(args.profile, open_browser=args.open)
        elif args.command == "restart":
            payload = restart_profile(args.profile, open_browser=args.open)
        elif args.command == "down":
            payload = down_profile(args.profile, all_services=args.all)
        elif args.command == "open":
            payload = open_profile_urls(args.profile)
        elif args.command == "status":
            payload = status_payload()
        elif args.command == "doctor":
            payload = doctor_payload()
        elif args.command == "evidence":
            payload = evidence_payload(
                args.app,
                require_frontmost=args.require_frontmost,
                capture=args.capture,
                strict=args.strict,
            )
        else:
            raise RuntimeError(f"Unsupported command: {args.command}")
    except Exception as exc:
        payload = {"ok": False, "error": str(exc)}
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=False))
        else:
            print(f"Mission Control error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=False))
        return 0

    if args.command == "status":
        print_text_status(payload)
    elif args.command == "doctor":
        print_text_doctor(payload)
    else:
        print(json.dumps(payload, indent=2, sort_keys=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
