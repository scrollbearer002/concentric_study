#!/usr/bin/env python3
"""Serve a repo-local Concentric visual control room."""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import webbrowser
from dataclasses import asdict, is_dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlencode, urlparse


ROOT = Path(__file__).resolve().parents[4]
OPERATOR_DIR = ROOT / "operator"
UNDERSTANDING_DIR = ROOT / "operator" / "cre" / "project_understanding"
CONTROL_ROOM_DIR = UNDERSTANDING_DIR / "control_room"
ARTIFACTS_DIR = UNDERSTANDING_DIR / "artifacts"
GENERATED_DIR = ARTIFACTS_DIR / "control_room_generated"
D2_DIR = GENERATED_DIR / "d2"
D2_SRC_DIR = D2_DIR / "src"
D2_SVG_DIR = D2_DIR / "svg"
STRUCTURIZR_DIR = GENERATED_DIR / "structurizr"
STRUCTURIZR_DOCS_DIR = STRUCTURIZR_DIR / "docs"
STRUCTURIZR_ADRS_DIR = STRUCTURIZR_DIR / "decisions"
STRUCTURIZR_EXPORT_DIR = STRUCTURIZR_DIR / "export"
STRUCTURIZR_STATIC_DIR = STRUCTURIZR_EXPORT_DIR / "static"
STRUCTURIZR_JSON_DIR = STRUCTURIZR_EXPORT_DIR / "json"
STRUCTURIZR_WORKSPACE_DSL = STRUCTURIZR_DIR / "workspace.dsl"
STRUCTURIZR_INSPECT_TXT = STRUCTURIZR_EXPORT_DIR / "inspect.txt"
RUNS_DIR = ROOT / "operator" / "cre" / "runs"
TOOLS_DIR = Path(__file__).resolve().parent
D2_BIN = shutil.which("d2")
STRUCTURIZR_BIN = shutil.which("structurizr-cli") or shutil.which("structurizr")
DOCKER_BIN = shutil.which("docker")
for path in (TOOLS_DIR, OPERATOR_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import build_architecture_conformance as arch_conf  # type: ignore
import build_dynamic_execution_architecture as dyn_exec  # type: ignore
import build_verification_calibration as ver_cal  # type: ignore
from action_space import UnifiedActionSpace
from concentric_observability import ensure_observability, span as obs_span, status_payload as observability_status_payload


MASTER_SYSTEMS_BODY = r"""
flowchart LR
    subgraph IN["Input Plane"]
        direction TB
        I1["Human Task / Goal"]
        I2["URL / App / Site Context"]
        I3["Host Readiness / Tool Health"]
        I4["Current Visual + Semantic State"]
        I5["Persistent Memory<br/>Skills / Trust / Site Knowledge / Rules"]
    end

    subgraph RUN["Ministry Dependency Chain"]
        direction LR
        E["Executive<br/>agent.py"]
        C["Capability Router<br/>capability_router.py"]
        S["Survey Office<br/>a11y + visual + element map + window capture"]
        P["Planning Ministry<br/>research_agent.py"]
        A["Action Law<br/>action_space.py"]
        D["Action Dispatch<br/>action_handlers.py"]
        G["Machine Control<br/>agent_core.py"]
        X["Emergency Authority<br/>recovery + healing + DDG + outer_loop"]
        V["Supreme Inspectorate<br/>verification_gate.py"]
        R["Records Office<br/>trace_writer.py"]

        E --> C --> S --> P --> A --> D --> G --> X --> V --> R
    end

    subgraph LAW["Constitutional Law Layer (Cross-cutting governance)"]
        direction LR
        L1["Planner Visibility"]
        L2["Dispatchability"]
        L3["Boundary Discipline"]
        L4["Outcome Semantics"]
        L5["Judge Accountability"]
    end

    subgraph OUT["Output Plane"]
        direction TB
        O1["Changed World / UI State"]
        O2["Verification Verdict"]
        O3["Trace + Manifest"]
        O4["Diagnostics + Benchmarks"]
        O5["Memory Updates<br/>Skills / Trust / Site Knowledge / Rules"]
    end

    subgraph LEG["Legitimacy Loop"]
        direction LR
        J1["Archived Verification Artifacts"]
        J2["Blind Human Review"]
        J3["Adjudicated Ground Truth"]
        J4["Calibration Metrics"]
        J5["Future Verification / Trust / Benchmark Reform"]

        J1 --> J2 --> J3 --> J4 --> J5
    end

    I1 --> E
    I2 --> E
    I3 --> E
    I4 --> S
    I5 --> E
    I5 --> P

    L1 -. constrains .-> A
    L2 -. constrains .-> D
    L3 -. constrains .-> E
    L3 -. constrains .-> P
    L3 -. constrains .-> D
    L4 -. constrains .-> R
    L5 -. constrains .-> V

    G --> O1
    X --> O1
    V --> O2
    R --> O3
    O3 --> O4
    O3 --> O5

    O1 -. becomes new observed state .-> I4
    O4 -. informs diagnosis / policy .-> E
    O4 -. informs recovery / healing .-> X
    O5 -. updates persistent memory .-> I5

    O2 --> J1
    O3 --> J1
    J5 -. recalibrates .-> V
    J5 -. informs benchmark / trust policy .-> O4
    J5 -. pressures future judge-governance changes .-> L5
"""


VIEWPOINTS = [
    {
        "id": "founder-architect",
        "name": "Founder / Architect",
        "subtitle": "Shape of the republic, boundaries, reforms, and leverage points.",
        "concerns": [
            "System shape and ministry boundaries",
            "Where to enhance the architecture next",
            "How reforms propagate across the republic",
        ],
        "station_ids": [
            "executive-office",
            "capability-staffing",
            "survey-office",
            "planning-ministry",
            "interior-public-works",
            "emergency-authority",
            "records-and-treasury",
            "supreme-inspectorate",
        ],
        "law_ids": [
            "planner-visibility",
            "dispatchability",
            "boundary-discipline",
            "outcome-semantics",
            "judge-accountability",
        ],
    },
    {
        "id": "runtime-operator",
        "name": "Runtime Operator",
        "subtitle": "How the live mission moves, stalls, and recovers.",
        "concerns": [
            "Current run condition",
            "What station is acting now",
            "Where state changes and recoveries happen",
        ],
        "station_ids": [
            "executive-office",
            "capability-staffing",
            "survey-office",
            "planning-ministry",
            "interior-public-works",
            "emergency-authority",
            "supreme-inspectorate",
        ],
        "law_ids": ["dispatchability", "boundary-discipline", "outcome-semantics"],
    },
    {
        "id": "debugger",
        "name": "Debugger",
        "subtitle": "Failure entry points, propagation, and evidence.",
        "concerns": [
            "Where failure entered the run",
            "What evidence is available for diagnosis",
            "Which stations absorb or amplify defects",
        ],
        "station_ids": [
            "survey-office",
            "interior-public-works",
            "emergency-authority",
            "records-and-treasury",
            "supreme-inspectorate",
        ],
        "law_ids": ["dispatchability", "boundary-discipline", "outcome-semantics"],
    },
    {
        "id": "governance-steward",
        "name": "Governance Steward",
        "subtitle": "Conformance, boundaries, and constitutional drift.",
        "concerns": [
            "Where boundary discipline could drift",
            "Which rules hold the republic together",
            "What should be enforced mechanically",
        ],
        "station_ids": [
            "executive-office",
            "capability-staffing",
            "planning-ministry",
            "interior-public-works",
            "records-and-treasury",
            "supreme-inspectorate",
        ],
        "law_ids": [
            "planner-visibility",
            "dispatchability",
            "boundary-discipline",
            "outcome-semantics",
            "judge-accountability",
        ],
    },
    {
        "id": "evaluator-researcher",
        "name": "Evaluator / Researcher",
        "subtitle": "Outcome validity, benchmark meaning, and legitimacy.",
        "concerns": [
            "What the run means scientifically",
            "Whether outcomes and judgments are trustworthy",
            "How evidence feeds calibration and future experiments",
        ],
        "station_ids": [
            "survey-office",
            "planning-ministry",
            "records-and-treasury",
            "supreme-inspectorate",
        ],
        "law_ids": ["outcome-semantics", "judge-accountability"],
    },
]


LAW_BLUEPRINTS = [
    {
        "id": "planner-visibility",
        "name": "Planner Visibility",
        "node_id": "L1",
        "description": "Only actions safe for planners should be visible in the public lawbook.",
        "station_ids": ["planning-ministry"],
    },
    {
        "id": "dispatchability",
        "name": "Dispatchability",
        "node_id": "L2",
        "description": "Planner-visible actions must map to live dispatcher handlers.",
        "station_ids": ["planning-ministry", "interior-public-works"],
    },
    {
        "id": "boundary-discipline",
        "name": "Boundary Discipline",
        "node_id": "L3",
        "description": "Ministries should coordinate through ports, not secret tunnels.",
        "station_ids": ["executive-office", "capability-staffing", "planning-ministry", "interior-public-works"],
    },
    {
        "id": "outcome-semantics",
        "name": "Outcome Semantics",
        "node_id": "L4",
        "description": "Execution, acceptance, and verification truth must be recorded in one normalized civil registry.",
        "station_ids": ["records-and-treasury"],
    },
    {
        "id": "judge-accountability",
        "name": "Judge Accountability",
        "node_id": "L5",
        "description": "The final inspector must be calibratable against human judgment.",
        "station_ids": ["supreme-inspectorate", "records-and-treasury"],
    },
]


STATIONS = [
    {
        "id": "executive-office",
        "name": "Executive Office",
        "metaphor": "The palace that turns a wish into a state mission.",
        "role": "Classifies the task, activates capabilities, assembles context, chooses planning mode, executes the run, and closes the mission.",
        "node_ids": ["E"],
        "context_node_ids": ["I1", "I2", "I3"],
        "law_ids": ["boundary-discipline"],
        "viewpoint_ids": ["founder-architect", "runtime-operator", "governance-steward"],
        "legitimacy_note": "The executive shapes missions and closures, but it does not get to self-certify them.",
        "files": [
            "operator/agent.py",
            "operator/cre/test_excalidraw_covt.py",
        ],
    },
    {
        "id": "capability-staffing",
        "name": "Capability Staffing",
        "metaphor": "The civil service commission that decides which ministries open for this case.",
        "role": "Selects the perception, tooling, memory, and model-routing institutions needed for the current mission.",
        "node_ids": ["C"],
        "context_node_ids": ["I3"],
        "law_ids": ["boundary-discipline"],
        "viewpoint_ids": ["founder-architect", "runtime-operator", "governance-steward"],
        "legitimacy_note": "A mission cannot be legitimate if the republic silently assumes capabilities it does not actually possess.",
        "files": [
            "operator/capability_router.py",
            "operator/inference_router.py",
            "operator/agent_infra/host_tool_health.py",
        ],
    },
    {
        "id": "survey-office",
        "name": "Survey Office",
        "metaphor": "The cartographers who tell the republic what territory actually exists.",
        "role": "Builds a visual and semantic world model from accessibility data, screenshots, visual grounding, and fused element maps.",
        "node_ids": ["S"],
        "context_node_ids": ["I4"],
        "law_ids": [],
        "viewpoint_ids": ["founder-architect", "runtime-operator", "debugger", "evaluator-researcher"],
        "legitimacy_note": "Bad maps poison both execution and evaluation; the judge can only see what the republic preserves.",
        "files": [
            "operator/a11y_engine.py",
            "operator/visual_engine.py",
            "operator/element_map.py",
            "operator/window_capture.py",
            "operator/web_primitives.py",
        ],
    },
    {
        "id": "planning-ministry",
        "name": "Planning Ministry",
        "metaphor": "The doctrine bureau that studies the problem before marching.",
        "role": "Researches the task, method, and tool surface, then maps them into lawful executable action plans.",
        "node_ids": ["P", "A"],
        "context_node_ids": ["I5", "L1"],
        "law_ids": ["planner-visibility", "dispatchability", "boundary-discipline"],
        "viewpoint_ids": ["founder-architect", "runtime-operator", "governance-steward", "evaluator-researcher"],
        "legitimacy_note": "Planning gains legitimacy only when its public verbs are real and its contingencies are executable.",
        "files": [
            "operator/agent_infra/research_agent.py",
            "operator/agent_infra/site_knowledge.py",
            "operator/agent_infra/skill_library.py",
            "operator/action_space.py",
        ],
    },
    {
        "id": "interior-public-works",
        "name": "Interior and Public Works",
        "metaphor": "The street bureaucracy that turns law into municipal labor.",
        "role": "Transforms public action verbs into concrete procedures across generic actions, browser/UI actions, and site-specific macros.",
        "node_ids": ["D", "G"],
        "context_node_ids": ["O1", "L2"],
        "law_ids": ["dispatchability", "boundary-discipline"],
        "viewpoint_ids": ["founder-architect", "runtime-operator", "debugger", "governance-steward"],
        "legitimacy_note": "This station is where most missions visibly succeed or fail, because this is where law becomes motion.",
        "files": [
            "operator/agent_infra/action_handlers.py",
            "operator/agent_infra/action_contracts.py",
            "operator/agent_infra/action_allowlist.py",
            "operator/agent_core.py",
        ],
    },
    {
        "id": "emergency-authority",
        "name": "Emergency Authority",
        "metaphor": "The disaster office that assumes foreign territory will resist.",
        "role": "Checks action effects, retries or repairs failures, classifies failure modes, extracts causal chains, and escalates when needed.",
        "node_ids": ["X"],
        "context_node_ids": ["O1", "O4"],
        "law_ids": [],
        "viewpoint_ids": ["founder-architect", "runtime-operator", "debugger"],
        "legitimacy_note": "This is the republic's refusal to treat first failure as final truth.",
        "files": [
            "operator/agent_infra/recovery.py",
            "operator/agent_infra/healing_orchestrator.py",
            "operator/agent_infra/decision_graph.py",
            "operator/agent_infra/outer_loop.py",
        ],
    },
    {
        "id": "records-and-treasury",
        "name": "Records and Treasury",
        "metaphor": "The archive and statistics bureau that decide what the republic remembers about a mission.",
        "role": "Writes traces and manifests, normalizes outcome semantics, interprets runs, and turns them into comparative evidence and memory.",
        "node_ids": ["R"],
        "context_node_ids": ["O3", "O4", "O5", "L4"],
        "law_ids": ["outcome-semantics", "judge-accountability"],
        "viewpoint_ids": ["founder-architect", "debugger", "governance-steward", "evaluator-researcher"],
        "legitimacy_note": "Without this station, the republic would have action but not memory, evidence, or comparative judgment.",
        "files": [
            "operator/agent_infra/trace_writer.py",
            "operator/agent_infra/diagnostic_reader.py",
            "operator/agent_infra/benchmark_evaluator.py",
            "operator/agent_infra/visual_monitor.py",
            "operator/agent_infra/action_trust.py",
        ],
    },
    {
        "id": "supreme-inspectorate",
        "name": "Supreme Inspectorate",
        "metaphor": "The final judge that says whether motion deserves to count as success.",
        "role": "Verifies the final result, records deficiencies, and feeds the legitimacy loop that eventually judges the judge.",
        "node_ids": ["V"],
        "context_node_ids": ["O2", "J1", "J2", "J3", "J4", "J5", "L5"],
        "law_ids": ["judge-accountability"],
        "viewpoint_ids": ["founder-architect", "runtime-operator", "debugger", "governance-steward", "evaluator-researcher"],
        "legitimacy_note": "This is the one station whose own legitimacy must ultimately come from outside the palace.",
        "files": [
            "operator/agent_infra/verification_gate.py",
            "operator/cre/project_understanding/tools/build_verification_calibration.py",
            "operator/cre/project_understanding/SECTION_8_VERIFICATION_GATE_CALIBRATION.md",
        ],
    },
]


TOOL_HOOKS = [
    {"name": "D2", "command": "d2 --watch operator/cre/project_understanding/artifacts/control_room_generated/d2/src/master_systems.d2", "purpose": "Live architecture diagram window."},
    {"name": "Structurizr", "command": "python3 operator/cre/project_understanding/tools/run_structurizr_atlas.py --open-browser", "purpose": "Canonical architecture atlas."},
    {"name": "Phoenix", "command": "python3 operator/cre/project_understanding/tools/run_phoenix_control_room.py", "purpose": "Runtime trace and eval observatory."},
    {"name": "Sourcegraph", "command": "Sourcegraph / Cody", "purpose": "Semantic code graph and local indexing."},
    {"name": "Understand", "command": "und / GUI project refresh", "purpose": "Deep structural code archaeology."},
    {"name": "Import Linter", "command": "lint-imports", "purpose": "Constitution monitor for boundaries."},
]


class SnapshotCache:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._snapshot: dict[str, Any] | None = None
        self._key: tuple[float, float] | None = None

    def get_or_build(self) -> dict[str, Any]:
        key = snapshot_cache_key()
        with self._lock:
            if self._snapshot is not None and self._key == key:
                return self._snapshot
            snapshot = build_snapshot()
            self._snapshot = snapshot
            self._key = key
            return snapshot


def snapshot_cache_key() -> tuple[float, float]:
    return (latest_python_mtime(ROOT / "operator"), latest_run_mtime(RUNS_DIR))


def latest_python_mtime(root: Path) -> float:
    latest = 0.0
    for path in root.rglob("*.py"):
        try:
            latest = max(latest, path.stat().st_mtime)
        except OSError:
            continue
    return latest


def latest_run_mtime(runs_dir: Path) -> float:
    latest = 0.0
    for pattern in ("manifest.json", "trace.jsonl", "verification/verification_*.json"):
        for path in runs_dir.glob(f"*/{pattern}"):
            try:
                latest = max(latest, path.stat().st_mtime)
            except OSError:
                continue
    return latest


def to_builtin(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): to_builtin(val) for key, val in value.items()}
    if isinstance(value, list):
        return [to_builtin(item) for item in value]
    return value


def write_if_changed(path: Path, content: str) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    previous = None
    if path.exists():
        try:
            previous = path.read_text(encoding="utf-8")
        except OSError:
            previous = None
    if previous == content:
        return False
    path.write_text(content, encoding="utf-8")
    return True


def run_structurizr_cli(*args: str) -> subprocess.CompletedProcess[str]:
    if not STRUCTURIZR_BIN:
        raise RuntimeError("Structurizr CLI is not available on this machine.")
    return subprocess.run(
        [STRUCTURIZR_BIN, *args],
        cwd=str(STRUCTURIZR_DIR),
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )


def stable_file_id(path: str) -> str:
    return "file:" + path.replace("/", "::").replace(".", "_")


def build_master_systems_mermaid(
    *,
    focus_station_ids: list[str] | None = None,
    focus_law_ids: list[str] | None = None,
) -> str:
    focus_station_ids = focus_station_ids or []
    focus_law_ids = focus_law_ids or []

    station_nodes = {
        node
        for station in STATIONS
        if station["id"] in focus_station_ids
        for node in station.get("node_ids", [])
    }
    context_nodes = {
        node
        for station in STATIONS
        if station["id"] in focus_station_ids
        for node in station.get("context_node_ids", [])
    }
    law_nodes = {
        law["node_id"]
        for law in LAW_BLUEPRINTS
        if law["id"] in focus_law_ids
    }
    context_nodes |= law_nodes
    context_nodes -= station_nodes

    lines = [MASTER_SYSTEMS_BODY.strip(), "", 'classDef focus fill:#ffe7bf,stroke:#c46a00,stroke-width:4px,color:#111;']
    lines.append('classDef context fill:#f6efe2,stroke:#b8892d,stroke-width:2px,color:#111;')
    if station_nodes:
        lines.append(f"class {','.join(sorted(station_nodes))} focus;")
    if context_nodes:
        lines.append(f"class {','.join(sorted(context_nodes))} context;")
    return "\n".join(lines)


def d2_string(value: Any) -> str:
    return json.dumps(str(value), ensure_ascii=True)


def d2_link(*, station_id: str | None = None, viewpoint_id: str | None = None) -> str:
    params: dict[str, str] = {}
    if station_id:
        params["station"] = station_id
    if viewpoint_id:
        params["viewpoint"] = viewpoint_id
    return "/?" + urlencode(params) if params else "/"


def sourcegraph_base_url() -> str | None:
    explicit = os.environ.get("CONCENTRIC_SOURCEGRAPH_URL")
    if explicit:
        return explicit.rstrip("/")
    return "https://sourcegraph.com"


def sourcegraph_repo_name() -> str | None:
    explicit = os.environ.get("CONCENTRIC_SOURCEGRAPH_REPO")
    if explicit:
        return explicit
    try:
        remote = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            check=True,
            cwd=str(ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        ).stdout.strip()
    except Exception:
        return None
    if not remote:
        return None
    remote = remote.removesuffix(".git")
    https_match = re.match(r"https://([^/]+)/(.*)", remote)
    ssh_match = re.match(r"git@([^:]+):(.*)", remote)
    if https_match:
        return f"{https_match.group(1)}/{https_match.group(2)}"
    if ssh_match:
        return f"{ssh_match.group(1)}/{ssh_match.group(2)}"
    return remote


def sourcegraph_escape_regex(value: str) -> str:
    return re.escape(value)


def sourcegraph_query_for_files(paths: list[str], repo_name: str | None) -> str:
    filters: list[str] = []
    if repo_name:
        filters.append(f"repo:^{sourcegraph_escape_regex(repo_name)}$")
    if paths:
        if len(paths) == 1:
            filters.append(f"file:^{sourcegraph_escape_regex(paths[0])}$")
        else:
            joined = "|".join(sourcegraph_escape_regex(path) for path in paths)
            filters.append(f"file:^({joined})$")
    return " ".join(filters)


def sourcegraph_local_index_status() -> dict[str, Any]:
    roots = [
        Path.home() / "Library/Application Support/Code/User/globalStorage/sourcegraph.cody-ai/symf/indexroot",
        Path.home() / ".config/Code/User/globalStorage/sourcegraph.cody-ai/symf/indexroot",
    ]
    existing_root = next((root for root in roots if root.exists()), None)
    if not existing_root:
        return {
            "local_index_present": False,
            "index_root": None,
            "workspace_indexes_detected": 0,
            "signal": "No local Cody symf index detected on this machine.",
        }
    workspace_indexes = [path for path in existing_root.iterdir() if path.is_dir()]
    latest_mtime = max((path.stat().st_mtime for path in workspace_indexes), default=0.0)
    return {
        "local_index_present": bool(workspace_indexes),
        "index_root": str(existing_root),
        "workspace_indexes_detected": len(workspace_indexes),
        "latest_index_mtime": latest_mtime,
        "signal": f"Detected {len(workspace_indexes)} local Cody symf index root(s).",
    }


def append_d2_style(lines: list[str], style: dict[str, Any], indent: int) -> None:
    prefix = "  " * indent
    lines.append(f"{prefix}style: {{")
    for key, value in style.items():
        lines.append(f"{prefix}  {key}: {d2_string(value)}")
    lines.append(f"{prefix}}}")


def append_d2_node(
    lines: list[str],
    *,
    indent: int,
    key: str,
    label: str,
    tooltip: str | None = None,
    link: str | None = None,
    style: dict[str, Any] | None = None,
) -> None:
    prefix = "  " * indent
    lines.append(f"{prefix}{key}: {{")
    lines.append(f"{prefix}  label: {d2_string(label)}")
    if tooltip:
        lines.append(f"{prefix}  tooltip: {d2_string(tooltip)}")
    if link:
        lines.append(f"{prefix}  link: {d2_string(link)}")
    if style:
        append_d2_style(lines, style, indent + 1)
    lines.append(f"{prefix}}}")


def station_style(station_id: str, focus_station_ids: set[str]) -> dict[str, str]:
    if station_id in focus_station_ids:
        return {"fill": "#ffe7bf", "stroke": "#c46a00", "stroke-width": "3"}
    return {"fill": "#fff7d6", "stroke": "#b8892d", "stroke-width": "2"}


def law_style(law_id: str, focus_law_ids: set[str], status: str) -> dict[str, str]:
    if law_id in focus_law_ids:
        return {"fill": "#ffe7bf", "stroke": "#c46a00", "stroke-width": "3"}
    if status == "blocking":
        return {"fill": "#ffe8e6", "stroke": "#c1463a", "stroke-width": "2"}
    if status == "attention":
        return {"fill": "#fff3d6", "stroke": "#b8892d", "stroke-width": "2"}
    return {"fill": "#efe7c2", "stroke": "#8b7a00", "stroke-width": "2"}


def node_id_for_station(station_id: str) -> str:
    return station_id.replace("-", "_")


def master_systems_d2(
    *,
    laws: list[dict[str, Any]],
    focus_station_ids: list[str] | None = None,
    focus_law_ids: list[str] | None = None,
) -> str:
    focus_station_ids = focus_station_ids or []
    focus_law_ids = focus_law_ids or []
    focus_station_set = set(focus_station_ids)
    focus_law_set = set(focus_law_ids)
    law_statuses = {law["id"]: law["status"] for law in laws}

    station_index = {station["id"]: station for station in STATIONS}
    law_index = {law["id"]: law for law in laws}

    lines = [
        "vars: {",
        "  d2-config: {",
        '    layout-engine: "dagre"',
        "  }",
        "}",
        "",
        "input_plane: {",
        '  label: "Input Plane"',
    ]
    append_d2_style(lines, {"fill": "#eaf3ff", "stroke": "#2f6db2", "stroke-width": "2"}, 1)
    for key, label in [
        ("human_task", "Human Task / Goal"),
        ("site_context", "URL / App / Site Context"),
        ("host_readiness", "Host Readiness / Tool Health"),
        ("current_state", "Current Visual + Semantic State"),
        ("persistent_memory", "Persistent Memory"),
    ]:
        append_d2_node(lines, indent=1, key=key, label=label, style={"fill": "#ffffff", "stroke": "#2f6db2"})
    lines.append("}")
    lines.extend([
        "",
        "runtime_chain: {",
        '  label: "Ministry Dependency Chain"',
    ])
    append_d2_style(lines, {"fill": "#fff7d6", "stroke": "#b8892d", "stroke-width": "2"}, 1)
    for station_id in [
        "executive-office",
        "capability-staffing",
        "survey-office",
        "planning-ministry",
        "interior-public-works",
        "emergency-authority",
        "supreme-inspectorate",
        "records-and-treasury",
    ]:
        station = station_index[station_id]
        append_d2_node(
            lines,
            indent=1,
            key=node_id_for_station(station_id),
            label=station["name"],
            tooltip=f'{station["metaphor"]} {station["role"]}',
            link=d2_link(station_id=station_id, viewpoint_id=station["viewpoint_ids"][0]),
            style=station_style(station_id, focus_station_set),
        )
    lines.append("}")
    lines.extend([
        "",
        "law_layer: {",
        '  label: "Constitutional Law Layer"',
    ])
    append_d2_style(lines, {"fill": "#f6f0d0", "stroke": "#8b7a00", "stroke-width": "2"}, 1)
    for law_id in ["planner-visibility", "dispatchability", "boundary-discipline", "outcome-semantics", "judge-accountability"]:
        law = law_index[law_id]
        append_d2_node(
            lines,
            indent=1,
            key=law_id.replace("-", "_"),
            label=f'{law["name"]}\\n{law["status"]}',
            tooltip=f'{law["description"]} {law["signal"]}',
            link=d2_link(station_id=law["station_ids"][0], viewpoint_id="governance-steward"),
            style=law_style(law_id, focus_law_set, law_statuses[law_id]),
        )
    lines.append("}")
    lines.extend([
        "",
        "output_plane: {",
        '  label: "Output Plane"',
    ])
    append_d2_style(lines, {"fill": "#e7f8e7", "stroke": "#2e8b57", "stroke-width": "2"}, 1)
    for key, label in [
        ("changed_world", "Changed World / UI State"),
        ("verification_verdict", "Verification Verdict"),
        ("trace_manifest", "Trace + Manifest"),
        ("diagnostics_benchmarks", "Diagnostics + Benchmarks"),
        ("memory_updates", "Memory Updates"),
    ]:
        append_d2_node(lines, indent=1, key=key, label=label, style={"fill": "#ffffff", "stroke": "#2e8b57"})
    lines.append("}")
    lines.extend([
        "",
        "legitimacy_loop: {",
        '  label: "Legitimacy Loop"',
    ])
    append_d2_style(lines, {"fill": "#ffe9e2", "stroke": "#c65a28", "stroke-width": "2"}, 1)
    for key, label in [
        ("archived_artifacts", "Archived Verification Artifacts"),
        ("blind_review", "Blind Human Review"),
        ("ground_truth", "Adjudicated Ground Truth"),
        ("calibration_metrics", "Calibration Metrics"),
        ("future_reform", "Future Verification / Trust Reform"),
    ]:
        append_d2_node(lines, indent=1, key=key, label=label, style={"fill": "#ffffff", "stroke": "#c65a28"})
    lines.append("}")

    edge_lines = [
        "input_plane.human_task -> runtime_chain.executive_office",
        "input_plane.site_context -> runtime_chain.executive_office",
        "input_plane.host_readiness -> runtime_chain.executive_office",
        "input_plane.current_state -> runtime_chain.survey_office",
        "input_plane.persistent_memory -> runtime_chain.executive_office",
        "input_plane.persistent_memory -> runtime_chain.planning_ministry",
        "runtime_chain.executive_office -> runtime_chain.capability_staffing -> runtime_chain.survey_office -> runtime_chain.planning_ministry -> runtime_chain.interior_public_works -> runtime_chain.emergency_authority -> runtime_chain.supreme_inspectorate -> runtime_chain.records_and_treasury",
        "law_layer.planner_visibility -> runtime_chain.planning_ministry",
        "law_layer.dispatchability -> runtime_chain.interior_public_works",
        "law_layer.boundary_discipline -> runtime_chain.executive_office",
        "law_layer.boundary_discipline -> runtime_chain.planning_ministry",
        "law_layer.outcome_semantics -> runtime_chain.records_and_treasury",
        "law_layer.judge_accountability -> runtime_chain.supreme_inspectorate",
        "runtime_chain.interior_public_works -> output_plane.changed_world",
        "runtime_chain.emergency_authority -> output_plane.changed_world",
        "runtime_chain.supreme_inspectorate -> output_plane.verification_verdict",
        "runtime_chain.records_and_treasury -> output_plane.trace_manifest",
        "output_plane.trace_manifest -> output_plane.diagnostics_benchmarks",
        "output_plane.trace_manifest -> output_plane.memory_updates",
        "output_plane.changed_world -> input_plane.current_state",
        "output_plane.diagnostics_benchmarks -> runtime_chain.executive_office",
        "output_plane.diagnostics_benchmarks -> runtime_chain.emergency_authority",
        "output_plane.memory_updates -> input_plane.persistent_memory",
        "output_plane.verification_verdict -> legitimacy_loop.archived_artifacts",
        "output_plane.trace_manifest -> legitimacy_loop.archived_artifacts",
        "legitimacy_loop.archived_artifacts -> legitimacy_loop.blind_review -> legitimacy_loop.ground_truth -> legitimacy_loop.calibration_metrics -> legitimacy_loop.future_reform",
        "legitimacy_loop.future_reform -> runtime_chain.supreme_inspectorate",
        "legitimacy_loop.future_reform -> output_plane.diagnostics_benchmarks",
        "legitimacy_loop.future_reform -> law_layer.judge_accountability",
    ]
    lines.extend(["", *edge_lines, ""])
    return "\n".join(lines)


RUNTIME_PHASE_IDS = {
    "observe": "observe",
    "bootstrap": "bootstrap",
    "reset_prepare": "reset_prepare",
    "configure": "configure",
    "produce": "produce",
    "verify": "verify",
    "audit": "audit",
    "other": "other",
}

RUNTIME_STATION_PHASES = {
    "executive-office": {"bootstrap"},
    "capability-staffing": {"bootstrap"},
    "survey-office": {"observe"},
    "planning-ministry": {"audit", "other"},
    "interior-public-works": {"reset_prepare", "configure", "produce"},
    "emergency-authority": {"verify", "other"},
    "records-and-treasury": {"verify", "audit"},
    "supreme-inspectorate": {"verify", "audit"},
}


def runtime_overview_d2(dynamic_payload: dict[str, Any], *, focus_station_id: str | None = None) -> str:
    phase_counts = dynamic_payload.get("phase_counts", {}) or {}
    top_phase_transitions = dynamic_payload.get("top_phase_transitions", []) or []
    family_counts = dynamic_payload.get("execution_family_counts", {}) or {}
    focus_phases = RUNTIME_STATION_PHASES.get(focus_station_id or "", set())

    lines = [
        "vars: {",
        "  d2-config: {",
        '    layout-engine: "dagre"',
        "  }",
        "}",
        "",
        "runtime_planes: {",
        '  label: "Runtime Planes"',
    ]
    append_d2_style(lines, {"fill": "#fff7d6", "stroke": "#b8892d", "stroke-width": "2"}, 1)
    for phase_key in ["observe", "bootstrap", "reset_prepare", "configure", "produce", "verify", "audit", "other"]:
        count = phase_counts.get(phase_key, 0)
        label = f'{dyn_exec.PHASE_NODE_LABELS.get(phase_key, phase_key)}\\n{count} step(s)'
        style = {"fill": "#ffffff", "stroke": "#7d6a3f", "stroke-width": "2"}
        if phase_key in focus_phases:
            style = {"fill": "#ffe7bf", "stroke": "#c46a00", "stroke-width": "3"}
        append_d2_node(
            lines,
            indent=1,
            key=RUNTIME_PHASE_IDS[phase_key],
            label=label,
            tooltip=f"Observed {count} step(s) in the {phase_key} phase across live run artifacts.",
            style=style,
        )
    lines.append("}")
    lines.extend([
        "",
        "execution_families: {",
        '  label: "Execution Families"',
    ])
    append_d2_style(lines, {"fill": "#eef5ff", "stroke": "#2f6db2", "stroke-width": "2"}, 1)
    for idx, (family, count) in enumerate(sorted(family_counts.items(), key=lambda item: item[1], reverse=True)[:5], start=1):
        append_d2_node(
            lines,
            indent=1,
            key=f"family_{idx}",
            label=f"{family}\\n{count} run(s)",
            tooltip=f"Recovered execution family {family} appears in {count} analyzed run(s).",
            style={"fill": "#ffffff", "stroke": "#2f6db2"},
        )
    lines.append("}")
    lines.append("")
    for transition in top_phase_transitions[:8]:
        src = RUNTIME_PHASE_IDS.get(transition.get("from_phase", "other"), "other")
        dst = RUNTIME_PHASE_IDS.get(transition.get("to_phase", "other"), "other")
        count = transition.get("count", 0)
        lines.append(f'runtime_planes.{src} -> runtime_planes.{dst}: {d2_string(str(count))}')
    if family_counts:
        lines.append("runtime_planes.verify -> execution_families.family_1")
    lines.append("")
    return "\n".join(lines)


def render_d2_diagram(source: str, *, source_path: Path, svg_path: Path, salt: str) -> None:
    D2_SRC_DIR.mkdir(parents=True, exist_ok=True)
    D2_SVG_DIR.mkdir(parents=True, exist_ok=True)
    source_path.write_text(source, encoding="utf-8")
    if not D2_BIN:
        return
    env = os.environ.copy()
    env["DEBUG"] = "0"
    subprocess.run(
        [
            D2_BIN,
            str(source_path),
            str(svg_path),
            "--bundle",
            "--no-xml-tag",
            "--layout",
            "dagre",
            "--salt",
            salt,
        ],
        check=True,
        cwd=str(ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
    )


def build_d2_artifacts(snapshot: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "available": bool(D2_BIN),
        "master_systems": None,
        "runtime_overview": None,
        "station_focus": {},
        "source_dir": "/generated/control_room_generated/d2/src/",
    }
    if not D2_BIN:
        return payload

    master_src = D2_SRC_DIR / "master_systems.d2"
    master_svg = D2_SVG_DIR / "master_systems.svg"
    render_d2_diagram(
        master_systems_d2(laws=snapshot["laws"]),
        source_path=master_src,
        svg_path=master_svg,
        salt="master-systems",
    )
    payload["master_systems"] = "/generated/control_room_generated/d2/svg/master_systems.svg"

    runtime_src = D2_SRC_DIR / "runtime_overview.d2"
    runtime_svg = D2_SVG_DIR / "runtime_overview.svg"
    render_d2_diagram(
        runtime_overview_d2(snapshot["dynamic_execution"]),
        source_path=runtime_src,
        svg_path=runtime_svg,
        salt="runtime-overview",
    )
    payload["runtime_overview"] = "/generated/control_room_generated/d2/svg/runtime_overview.svg"

    for station in snapshot["stations"]:
        source_path = D2_SRC_DIR / f'{station["id"]}.d2'
        svg_path = D2_SVG_DIR / f'{station["id"]}.svg'
        render_d2_diagram(
            master_systems_d2(
                laws=snapshot["laws"],
                focus_station_ids=[station["id"]],
                focus_law_ids=station.get("law_ids", []),
            ),
            source_path=source_path,
            svg_path=svg_path,
            salt=f'station-{station["id"]}',
        )
        payload["station_focus"][station["id"]] = f'/generated/control_room_generated/d2/svg/{station["id"]}.svg'
    return payload


def infer_station_ids(action_type: str) -> list[str]:
    lowered = (action_type or "").lower()
    if not lowered:
        return ["interior-public-works"]
    if lowered == "host_tool_health":
        return ["capability-staffing"]
    if lowered.startswith("site_start_"):
        return ["executive-office"]
    if any(token in lowered for token in ("verify", "verification", "judge", "constraint", "assert")):
        return ["supreme-inspectorate"]
    if any(token in lowered for token in ("recovery", "retry", "heal", "ddg", "diagnostic", "escalat")):
        return ["emergency-authority"]
    if any(token in lowered for token in ("trace", "manifest", "benchmark", "monitor", "trust", "summar")):
        return ["records-and-treasury"]
    if any(token in lowered for token in ("research", "plan", "equation", "knowledge", "skill")):
        return ["planning-ministry"]
    if any(token in lowered for token in ("probe", "a11y", "snapshot", "screenshot", "refresh_perception")):
        return ["survey-office"]
    if any(
        token in lowered
        for token in (
            "navigate",
            "follow",
            "back",
            "go_to",
            "go_back",
            "click",
            "type",
            "scroll",
            "key",
            "draw",
            "kleki",
            "browser_",
            "set_",
            "sleep",
        )
    ):
        return ["interior-public-works"]
    return ["interior-public-works"]


def action_space_payload() -> dict[str, Any]:
    with obs_span("control_room.action_space_payload"):
        action_space = UnifiedActionSpace()
        handler_keys = parse_action_handler_keys(OPERATOR_DIR / "agent_infra" / "action_handlers.py")
        report = action_space.conformance_report(handler_keys)
        return {
            "planner_visible_actions": action_space.list_planner_names(),
            "missing_handler_actions": report["missing_handler_actions"],
            "hidden_actions": report["hidden_actions"],
        }


def parse_action_handler_keys(path: Path) -> set[str]:
    try:
        module = ast.parse(path.read_text(encoding="utf-8"))
    except OSError:
        return set()

    for node in module.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "ACTION_HANDLERS" and isinstance(node.value, ast.Dict):
                    keys: set[str] = set()
                    for key_node in node.value.keys:
                        if isinstance(key_node, ast.Constant) and isinstance(key_node.value, str):
                            keys.add(key_node.value)
                    return keys
    return set()


def station_signal(station: dict[str, Any], law_statuses: dict[str, dict[str, Any]], activity_counts: dict[str, int]) -> str:
    statuses = [law_statuses[law_id]["status"] for law_id in station.get("law_ids", []) if law_id in law_statuses]
    hits = activity_counts.get(station["id"], 0)
    if "blocking" in statuses:
        return "Needs constitutional repair."
    if "attention" in statuses:
        return "Operationally healthy, but still waiting on a legitimacy or evidence step."
    if hits:
        return f"Active in the latest mission with {hits} traced step(s)."
    return "Ready, but not active in the latest trace sample."


def latest_run_summary() -> dict[str, Any]:
    with obs_span("control_room.latest_run_summary"):
        manifests = sorted(
            (path for path in RUNS_DIR.glob("*/manifest.json")),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        if not manifests:
            return {
                "run_id": "",
                "task_id": "",
                "outcome": "unknown",
                "task_result": "unknown",
                "has_outcome_semantics": False,
                "final_verification_status": "unknown",
                "duration_seconds": 0.0,
                "step_count": 0,
                "trace_tail": [],
                "station_activity_counts": {},
                "run_dir": "",
            }

        manifest_path = manifests[0]
        run_dir = manifest_path.parent
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        semantics = manifest.get("outcome_semantics", {}) if isinstance(manifest.get("outcome_semantics"), dict) else {}
        final_ver = semantics.get("final_verification", {}) if isinstance(semantics.get("final_verification"), dict) else {}

        trace_path = run_dir / "trace.jsonl"
        trace_tail: list[dict[str, Any]] = []
        step_count = 0
        station_activity_counts: dict[str, int] = {}
        if trace_path.exists():
            steps = [json.loads(line) for line in trace_path.read_text(encoding="utf-8").splitlines() if line.strip()]
            step_count = len(steps)
            for step in steps:
                station_ids = infer_station_ids(step.get("action", {}).get("type", ""))
                for station_id in station_ids:
                    station_activity_counts[station_id] = station_activity_counts.get(station_id, 0) + 1
            tail = steps[-8:]
            for idx, step in enumerate(tail, start=max(len(steps) - len(tail), 0)):
                station_ids = infer_station_ids(step.get("action", {}).get("type", ""))
                trace_tail.append(
                    {
                        "index": idx,
                        "action_type": step.get("action", {}).get("type", ""),
                        "status": step.get("status", ""),
                        "thought": step.get("thought", ""),
                        "station_ids": station_ids,
                        "primary_station_id": station_ids[0],
                    }
                )

        return {
            "run_id": manifest.get("run_id", run_dir.name),
            "task_id": manifest.get("task_id", ""),
            "outcome": manifest.get("outcome", "unknown"),
            "task_result": semantics.get("task_result", "unknown"),
            "has_outcome_semantics": bool(semantics),
            "final_verification_status": final_ver.get("status", "unknown"),
            "duration_seconds": round(manifest.get("total_duration_ms", 0) / 1000.0, 3),
            "step_count": step_count,
            "trace_tail": trace_tail,
            "station_activity_counts": station_activity_counts,
            "run_dir": str(run_dir),
        }


def dynamic_execution_payload() -> dict[str, Any]:
    with obs_span("control_room.dynamic_execution_payload"):
        payload = dyn_exec.build_outputs()
        dyn_exec.OUTPUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")
        return payload


def conformance_payload() -> tuple[dict[str, Any], dict[str, Any]]:
    with obs_span("control_room.conformance_payload"):
        graph = arch_conf.load_graph(source="live")
        outputs = arch_conf.build_outputs(graph)
        arch_conf.write_outputs(outputs)
        enforcement = arch_conf.evaluate_enforcement(graph)
        return to_builtin(outputs["payload"]), to_builtin(enforcement)


def calibration_payload() -> dict[str, Any]:
    with obs_span("control_room.calibration_payload"):
        records = ver_cal.build_candidate_records()
        ver_cal.write_jsonl(ver_cal.OUTPUT_JSONL, records)
        ver_cal.write_review_packets(records, ver_cal.PACKETS_DIR)
        summary = ver_cal.build_candidate_summary(records, ver_cal.RUNS_DIR)
        ver_cal.write_json(ver_cal.OUTPUT_JSON, summary)
        return summary


def sourcegraph_payload(stations: list[dict[str, Any]], files: list[dict[str, Any]]) -> dict[str, Any]:
    base_url = sourcegraph_base_url()
    repo_name = sourcegraph_repo_name()
    local_index = sourcegraph_local_index_status()
    file_queries: dict[str, dict[str, Any]] = {}
    for file in files:
        query = sourcegraph_query_for_files([file["path"]], repo_name)
        file_queries[file["id"]] = {
            "query": query,
            "url": f"{base_url}/search?q={urlencode({'q': query})[2:]}" if base_url and query else None,
            "path": file["path"],
            "station_ids": file.get("station_ids", []),
        }

    station_queries: dict[str, dict[str, Any]] = {}
    for station in stations:
        query = sourcegraph_query_for_files(station.get("files", []), repo_name)
        station_queries[station["id"]] = {
            "query": query,
            "url": f"{base_url}/search?q={urlencode({'q': query})[2:]}" if base_url and query else None,
            "file_paths": station.get("files", []),
        }

    return {
        "available": bool(base_url),
        "base_url": base_url,
        "repo_name": repo_name,
        "local_index": local_index,
        "station_queries": station_queries,
        "file_queries": file_queries,
        "signal": (
            "Sourcegraph drilldown is configured and can open repo-aware search queries."
            if base_url and repo_name
            else "Sourcegraph drilldown is partially configured; repo-aware search URLs are not yet fully derived."
        ),
    }


def structurizr_docs_payload(
    *,
    stations: list[dict[str, Any]],
    laws: list[dict[str, Any]],
    viewpoints: list[dict[str, Any]],
    latest_run: dict[str, Any],
    action_conformance: dict[str, Any],
    calibration: dict[str, Any],
) -> dict[str, str]:
    station_lines = "\n".join(
        f"- **{station['name']}**: {station['role']} Files: {', '.join(station.get('files', []))}."
        for station in stations
    )
    law_lines = "\n".join(
        f"- **{law['name']}** (`{law['status']}`): {law['signal']}"
        for law in laws
    )
    viewpoint_lines = "\n".join(
        f"- **{viewpoint['name']}**: {viewpoint['subtitle']} Concerns: {', '.join(viewpoint.get('concerns', []))}."
        for viewpoint in viewpoints
    )
    overview = f"""# Concentric Canonical Atlas

This Structurizr workspace is the canonical architecture atlas for Concentric Study.
It is generated from the same control-room entity model that drives the local visual
control room, so the atlas stays grounded in the live repo rather than a parallel,
hand-maintained architecture story.

## Current Runtime Signal

- Latest run: `{latest_run.get('run_id', 'unknown')}`
- Task result: `{latest_run.get('task_result', 'unknown')}`
- Final verification: `{latest_run.get('final_verification_status', 'unknown')}`
- Planner-visible actions: `{len(action_conformance.get('planner_visible_actions', []))}`
- Calibration records: `{calibration.get('total_records', 0)}`
- Unlabeled calibration packets: `{calibration.get('review_state_counts', {}).get('unlabeled', 0)}`

## Ministry Chain

{station_lines}
"""
    viewpoints_doc = f"""# Viewpoints and Concerns

The workspace is organized around explicit viewpoints rather than generic panels.

{viewpoint_lines}

## Constitutional Laws

{law_lines}
"""
    legitimacy = f"""# Legitimacy Loop

Concentric's legitimacy loop begins after runtime verification.

1. Archived verification artifacts are written into the evidence layer.
2. Blind human review packets are generated from those artifacts.
3. Adjudicated ground truth is established when raters disagree.
4. Calibration metrics feed future verification, trust, and benchmark reform.

This is why the Supreme Inspectorate and the Records & Treasury station sit closest
to the legitimacy loop in the canonical views.
"""
    return {
        "overview.md": overview,
        "viewpoints.md": viewpoints_doc,
        "legitimacy-loop.md": legitimacy,
    }


def structurizr_adr_payload() -> dict[str, str]:
    return {
        "0001-control-room-is-the-local-multi-view-workspace.md": """# 1. Use the control room as the local multi-view workspace

Date: 2026-03-06

## Status

Accepted

## Context

Concentric needs a repo-local environment where architecture, runtime, conformance,
and legitimacy can be inspected together without relying on scattered scripts or
memory of past research passes.

## Decision

Use the control room as the primary local workspace and generate external artifacts
from the same canonical model instead of maintaining separate manual diagrams.

## Consequences

- Architecture, runtime, and legitimacy views stay synchronized.
- New external integrations must attach to the canonical model.
- The control room becomes the integration shell for external windows.
""",
        "0002-phoenix-before-visual-polish.md": """# 2. Integrate Phoenix before richer architecture publishing

Date: 2026-03-06

## Status

Accepted

## Context

The control room had a structural view before it had true runtime telemetry.
The largest missing truth layer was live span-level observability.

## Decision

Integrate Phoenix and OpenTelemetry before expanding further visual publishing
surfaces.

## Consequences

- Runtime traces become first-class data in the workspace.
- Future architecture views can correlate static structure with live behavior.
""",
        "0003-use-a-hybrid-visual-stack.md": """# 3. Use a hybrid visual stack for Concentric

Date: 2026-03-06

## Status

Accepted

## Context

No single external tool covers architecture publishing, runtime telemetry,
semantic code drilldown, and canonical documentation equally well.

## Decision

Adopt a hybrid stack:

- D2 for live architecture diagrams
- Sourcegraph/Cody for semantic drilldown
- Structurizr for the canonical architecture atlas

## Consequences

- Each tool remains specialized.
- The control room must coordinate rather than replace those tools.
""",
    }


def structurizr_workspace_dsl(
    *,
    stations: list[dict[str, Any]],
    laws: list[dict[str, Any]],
    viewpoints: list[dict[str, Any]],
) -> str:
    law_signals = {law["id"]: law["signal"] for law in laws}
    station_tags = {
        "executive-office": ("Orchestration", "Governance"),
        "capability-staffing": ("Staffing", "Governance"),
        "survey-office": ("Perception", "Runtime"),
        "planning-ministry": ("Planning", "Runtime"),
        "interior-public-works": ("Execution", "Runtime"),
        "emergency-authority": ("Recovery", "Runtime"),
        "supreme-inspectorate": ("Verification", "Legitimacy"),
        "records-and-treasury": ("Evidence", "Legitimacy"),
    }
    station_var_names = {
        "executive-office": "executive",
        "capability-staffing": "capability",
        "survey-office": "survey",
        "planning-ministry": "planning",
        "interior-public-works": "dispatch",
        "emergency-authority": "emergency",
        "supreme-inspectorate": "inspector",
        "records-and-treasury": "records",
    }
    station_by_id = {station["id"]: station for station in stations}
    station_order = [
        "executive-office",
        "capability-staffing",
        "survey-office",
        "planning-ministry",
        "interior-public-works",
        "emergency-authority",
        "supreme-inspectorate",
        "records-and-treasury",
    ]
    station_components = []
    for station_id in station_order:
        station = station_by_id[station_id]
        concern, perspective = station_tags[station_id]
        files = ", ".join(station.get("files", []))
        law_text = "; ".join(law_signals.get(law_id, law_id) for law_id in station.get("law_ids", []))
        station_components.append(
            f"""            {station_var_names[station_id]} = component "{station['name']}" "{station['role']} Governing files: {files}. Constitutional signals: {law_text}" "Python" {{
                tags "{concern},{perspective}"
                perspectives {{
                    Concern "{concern}"
                    GoverningLaw "{', '.join(station.get('law_ids', [])) or 'none'}"
                }}
            }}"""
        )
    viewpoint_text = "\\n".join(
        f"- {viewpoint['name']}: {viewpoint['subtitle']}"
        for viewpoint in viewpoints
    )
    return f"""workspace "Concentric Study Atlas" "Canonical architecture atlas for Concentric Study." {{
    !identifiers hierarchical

    model {{
        christian = person "Christian" "Founder, architect, and constitutional reformer of the republic."
        operator = person "Human Operator" "Supplies missions, reviews outcomes, and eventually participates in legitimacy checks."

        macos = softwareSystem "macOS + Safari" "The execution substrate that the envoy acts through."
        phoenix = softwareSystem "Phoenix" "Runtime trace and evaluation observatory."
        sourcegraph = softwareSystem "Sourcegraph / Cody" "Semantic code graph and local indexing surface."
        atlasViewer = softwareSystem "Structurizr Atlas Viewer" "Local viewer and static-site presentation layer for the canonical atlas."

        concentric = softwareSystem "Concentric Study" "General-purpose visual web agent on macOS with architecture, runtime, and legitimacy loops." {{
            runtime = container "Runtime Core" "Plans, executes, verifies, and records missions." "Python/macOS" {{
{chr(10).join(station_components)}
            }}
            evidence = container "Evidence and Memory" "Traces, manifests, benchmarks, calibration packets, skills, trust, and rules." "JSONL/JSON + local files"
            control = container "Visual Control Room" "Coordinated multi-view workspace for structure, runtime, conformance, and legitimacy." "Python + HTML/JavaScript" {{
                controlUI = component "Coordinated Views" "Selection-aware architecture, runtime, conformance, and legitimacy views." "Python + HTML/JavaScript" {{
                    tags "Governance"
                    perspectives {{
                        Concern "Governance"
                    }}
                }}
                d2Bridge = component "D2 Bridge" "Renders watched architecture diagrams from the canonical model." "D2" {{
                    tags "Governance"
                    perspectives {{
                        Concern "Architecture"
                    }}
                }}
                sourcegraphBridge = component "Sourcegraph Bridge" "Generates repo-aware semantic drilldown links and local-index signals." "Sourcegraph/Cody bridge" {{
                    tags "Governance"
                    perspectives {{
                        Concern "Semantic"
                    }}
                }}
                phoenixBridge = component "Phoenix Bridge" "Correlates stations and runs with live trace spans." "OpenTelemetry + Phoenix" {{
                    tags "Governance"
                    perspectives {{
                        Concern "Runtime"
                    }}
                }}
                structurizrBridge = component "Structurizr Bridge" "Publishes the canonical atlas workspace and static exports." "Structurizr DSL/CLI" {{
                    tags "Legitimacy"
                    perspectives {{
                        Concern "Atlas"
                    }}
                }}
            }}
            atlas = container "Structurizr Atlas Bundle" "Generated DSL, documentation, ADRs, and static-site exports." "Structurizr DSL + Markdown"

            !docs docs
            !adrs decisions
        }}

        christian -> concentric.control "Uses to understand and redesign the republic" "Browser / local workspace"
        operator -> concentric.runtime "Supplies missions" "Task prompt"
        operator -> concentric.control "Reviews architecture and runtime state" "Browser / local workspace"

        concentric.runtime -> macos "Acts through" "Quartz HID + Safari"
        concentric.runtime -> concentric.evidence "Writes traces, manifests, verification artifacts, benchmarks, skills, and trust" "JSONL/JSON artifacts"
        concentric.control -> concentric.evidence "Reads latest run, conformance, calibration, and memory artifacts" "Filesystem"
        concentric.control -> phoenix "Links to live traces" "OTLP / browser"
        concentric.control -> sourcegraph "Opens semantic drilldown" "Search URLs"
        concentric.control -> concentric.atlas "Publishes canonical atlas artifacts" "Generated workspace files"
        concentric.atlas -> atlasViewer "Viewed through" "Structurizr Lite / static export"

        concentric.runtime.executive -> concentric.runtime.capability "Activates required ministries" "Python call"
        concentric.runtime.capability -> concentric.runtime.survey "Selects perception stack" "Python call"
        concentric.runtime.survey -> concentric.runtime.planning "Provides world model" "Hybrid perception payload"
        concentric.runtime.planning -> concentric.runtime.dispatch "Issues lawful executable actions" "Action plan"
        concentric.runtime.dispatch -> macos "Emits clicks, drags, and keystrokes" "Quartz HID"
        concentric.runtime.dispatch -> concentric.runtime.emergency "Hands off live execution state" "Execution state"
        concentric.runtime.emergency -> concentric.runtime.inspector "Requests final verification" "Verification handoff"
        concentric.runtime.inspector -> concentric.runtime.records "Produces verdicts, deficiencies, and legitimacy evidence" "Verification result"
        concentric.runtime.records -> concentric.evidence "Persists run truth" "Trace + manifest"

        concentric.control.controlUI -> concentric.control.d2Bridge "Renders architecture surface" "SVG diagram request"
        concentric.control.controlUI -> concentric.control.sourcegraphBridge "Requests semantic drilldown" "Repo-aware search"
        concentric.control.controlUI -> concentric.control.phoenixBridge "Requests live trace context" "Trace query"
        concentric.control.controlUI -> concentric.control.structurizrBridge "Requests canonical atlas output" "Workspace export"
        concentric.control.phoenixBridge -> phoenix "Publishes/reads traces" "OTLP + browser"
        concentric.control.sourcegraphBridge -> sourcegraph "Opens repo-aware searches" "Search URLs"
        concentric.control.structurizrBridge -> concentric.atlas "Writes DSL, docs, ADRs, and exports" "Structurizr CLI"
    }}

    views {{
        systemContext concentric "SystemContext" {{
            include *
            autoLayout lr
            title "Concentric Study - System Context"
        }}

        container concentric "ContainerAtlas" {{
            include *
            autoLayout lr
            title "Concentric Study - Container Atlas"
        }}

        component concentric.runtime "RuntimeMinistries" {{
            include *
            autoLayout lr
            title "Concentric Study - Runtime Ministry Chain"
        }}

        component concentric.control "ControlRoomBridges" {{
            include *
            autoLayout lr
            title "Concentric Study - Control Room External Bridges"
        }}

        styles {{
            element "Person" {{
                shape person
                background #305f8d
                color #ffffff
            }}
            element "Software System" {{
                background #486581
                color #ffffff
            }}
            element "Container" {{
                background #b8892d
                color #ffffff
            }}
            element "Component" {{
                background #fff7d6
                color #1d1b19
                stroke #b8892d
            }}
            element "Legitimacy" {{
                stroke #c1463a
                strokeWidth 3
            }}
            element "Governance" {{
                stroke #2f6db2
                strokeWidth 3
            }}
            element "Runtime" {{
                stroke #3f7a4f
                strokeWidth 3
            }}
            relationship "Relationship" {{
                color #4b4a47
            }}
        }}
    }}

    configuration {{
        scope softwaresystem
    }}

}}
"""


def build_structurizr_artifacts(snapshot: dict[str, Any]) -> dict[str, Any]:
    with obs_span("control_room.structurizr_artifacts"):
        STRUCTURIZR_DIR.mkdir(parents=True, exist_ok=True)
        STRUCTURIZR_DOCS_DIR.mkdir(parents=True, exist_ok=True)
        STRUCTURIZR_ADRS_DIR.mkdir(parents=True, exist_ok=True)
        STRUCTURIZR_EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        STRUCTURIZR_STATIC_DIR.mkdir(parents=True, exist_ok=True)
        STRUCTURIZR_JSON_DIR.mkdir(parents=True, exist_ok=True)

        docs_written = 0
        for name, content in structurizr_docs_payload(
            stations=snapshot["stations"],
            laws=snapshot["laws"],
            viewpoints=snapshot["viewpoints"],
            latest_run=snapshot["latest_run"],
            action_conformance=snapshot["action_space_conformance"],
            calibration=snapshot["calibration"],
        ).items():
            docs_written += int(write_if_changed(STRUCTURIZR_DOCS_DIR / name, content))

        adrs_written = 0
        for name, content in structurizr_adr_payload().items():
            adrs_written += int(write_if_changed(STRUCTURIZR_ADRS_DIR / name, content))

        dsl = structurizr_workspace_dsl(
            stations=snapshot["stations"],
            laws=snapshot["laws"],
            viewpoints=snapshot["viewpoints"],
        )
        workspace_changed = write_if_changed(STRUCTURIZR_WORKSPACE_DSL, dsl)

        exported_static = False
        exported_json = False
        validate_output = None
        inspect_output = None
        export_error = None

        if STRUCTURIZR_BIN:
            try:
                validate_output = run_structurizr_cli("validate", "-w", str(STRUCTURIZR_WORKSPACE_DSL)).stdout.strip()
                inspect_output = run_structurizr_cli("inspect", "-w", str(STRUCTURIZR_WORKSPACE_DSL)).stdout.strip()
                write_if_changed(STRUCTURIZR_INSPECT_TXT, inspect_output + "\n")
                if workspace_changed or not (STRUCTURIZR_STATIC_DIR / "index.html").exists():
                    run_structurizr_cli("export", "-w", str(STRUCTURIZR_WORKSPACE_DSL), "-f", "static", "-o", str(STRUCTURIZR_STATIC_DIR))
                if workspace_changed or not any(STRUCTURIZR_JSON_DIR.glob("*.json")):
                    run_structurizr_cli("export", "-w", str(STRUCTURIZR_WORKSPACE_DSL), "-f", "json", "-o", str(STRUCTURIZR_JSON_DIR))
                exported_static = (STRUCTURIZR_STATIC_DIR / "index.html").exists()
                exported_json = any(STRUCTURIZR_JSON_DIR.glob("*.json"))
            except subprocess.CalledProcessError as exc:
                export_error = exc.stdout.strip() or str(exc)

        json_exports = sorted(STRUCTURIZR_JSON_DIR.glob("*.json"))
        return {
            "available": STRUCTURIZR_WORKSPACE_DSL.exists(),
            "tooling": {
                "cli_available": bool(STRUCTURIZR_BIN),
                "docker_available": bool(DOCKER_BIN),
            },
            "workspace_dsl": "/generated/control_room_generated/structurizr/workspace.dsl" if STRUCTURIZR_WORKSPACE_DSL.exists() else None,
            "docs": {
                "count": len(list(STRUCTURIZR_DOCS_DIR.glob("*.md"))),
                "directory": "/generated/control_room_generated/structurizr/docs/",
            },
            "adrs": {
                "count": len(list(STRUCTURIZR_ADRS_DIR.glob("*.md"))),
                "directory": "/generated/control_room_generated/structurizr/decisions/",
            },
            "exports": {
                "static_index": "/generated/control_room_generated/structurizr/export/static/index.html" if exported_static else None,
                "json_workspace": f"/generated/control_room_generated/structurizr/export/json/{json_exports[0].name}" if json_exports else None,
                "inspect_report": "/generated/control_room_generated/structurizr/export/inspect.txt" if STRUCTURIZR_INSPECT_TXT.exists() else None,
            },
            "validate_output": validate_output,
            "inspect_summary": inspect_output.splitlines()[:8] if inspect_output else [],
            "signal": (
                "Structurizr atlas is generated and export-ready."
                if STRUCTURIZR_BIN and not export_error
                else "Structurizr atlas source files are generated; CLI export is unavailable or failed."
            ),
            "export_error": export_error,
            "workspace_changed": workspace_changed,
            "docs_written": docs_written,
            "adrs_written": adrs_written,
        }


def build_law_entities(
    *,
    enforcement: dict[str, Any],
    action_conformance: dict[str, Any],
    latest_run: dict[str, Any],
    calibration: dict[str, Any],
) -> list[dict[str, Any]]:
    planner_visible_count = len(action_conformance["planner_visible_actions"])
    hidden_count = len(action_conformance["hidden_actions"])
    missing_count = len(action_conformance["missing_handler_actions"])
    unlabeled = calibration.get("review_state_counts", {}).get("unlabeled", 0)
    total_records = calibration.get("total_records", 0)

    states = {
        "planner-visibility": {
            "status": "passing",
            "signal": f"{planner_visible_count} planner-visible actions; {hidden_count} intentionally hidden.",
        },
        "dispatchability": {
            "status": "passing" if missing_count == 0 else "blocking",
            "signal": "All planner-visible actions dispatch to live handlers." if missing_count == 0 else f"{missing_count} planner-visible actions are not dispatchable.",
        },
        "boundary-discipline": {
            "status": "passing" if enforcement["passed"] else "blocking",
            "signal": "Architecture conformance is passing." if enforcement["passed"] else f"{len(enforcement.get('blocking_failures', []))} blocking conformance failures present.",
        },
        "outcome-semantics": {
            "status": "passing" if latest_run["has_outcome_semantics"] else "attention",
            "signal": "Latest run manifest includes normalized outcome semantics." if latest_run["has_outcome_semantics"] else "Latest run does not expose normalized outcome semantics.",
        },
        "judge-accountability": {
            "status": "passing" if total_records > 0 and unlabeled == 0 else ("attention" if total_records > 0 else "blocking"),
            "signal": "Calibration packets are fully human-labeled." if total_records > 0 and unlabeled == 0 else (f"{unlabeled} calibration packet(s) still await human labels." if total_records > 0 else "No calibration records exist yet."),
        },
    }

    return [
        {**blueprint, **states[blueprint["id"]]}
        for blueprint in LAW_BLUEPRINTS
    ]


def build_station_entities(
    latest_run: dict[str, Any],
    laws: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    law_statuses = {law["id"]: law for law in laws}
    file_map: dict[str, dict[str, Any]] = {}
    stations: list[dict[str, Any]] = []
    trace_tail = latest_run.get("trace_tail", [])
    activity_counts = latest_run.get("station_activity_counts", {})

    for blueprint in STATIONS:
        file_ids: list[str] = []
        for path in blueprint["files"]:
            file_id = stable_file_id(path)
            file_ids.append(file_id)
            if file_id not in file_map:
                file_map[file_id] = {
                    "id": file_id,
                    "path": path,
                    "label": Path(path).name,
                    "station_ids": [blueprint["id"]],
                }
            else:
                file_map[file_id]["station_ids"].append(blueprint["id"])

        latest_steps = [step for step in trace_tail if blueprint["id"] in step.get("station_ids", [])]
        stations.append(
            {
                **blueprint,
                "file_ids": file_ids,
                "latest_trace_hits": len(latest_steps),
                "latest_trace_steps": latest_steps,
                "focus_metrics": {
                    "file_count": len(file_ids),
                    "law_count": len(blueprint.get("law_ids", [])),
                    "trace_hits": activity_counts.get(blueprint["id"], 0),
                },
                "current_signal": station_signal(blueprint, law_statuses, activity_counts),
            }
        )

    return stations, sorted(file_map.values(), key=lambda item: item["path"])


def build_viewpoint_entities() -> list[dict[str, Any]]:
    return VIEWPOINTS


def detect_tools() -> list[dict[str, Any]]:
    detected: list[dict[str, Any]] = []
    for entry in TOOL_HOOKS:
        command_name = entry["command"].split()[0]
        available = any(
            (Path(path) / command_name).exists()
            for path in os.environ.get("PATH", "").split(os.pathsep)
        )
        if entry["name"] == "Phoenix":
            sidecar_phoenix = ROOT / "operator" / "cre" / "local_ops" / "phoenix_sidecar" / "venv" / "bin" / "phoenix"
            launcher = ROOT / "operator" / "cre" / "project_understanding" / "tools" / "run_phoenix_control_room.py"
            available = available or sidecar_phoenix.exists() or launcher.exists()
        if entry["name"] == "Sourcegraph":
            sourcegraph_state = sourcegraph_local_index_status()
            available = available or bool(sourcegraph_base_url()) or bool(sourcegraph_state.get("local_index_present"))
        if entry["name"] == "Structurizr":
            launcher = ROOT / "operator" / "cre" / "project_understanding" / "tools" / "run_structurizr_atlas.py"
            available = available or bool(STRUCTURIZR_BIN) or bool(DOCKER_BIN) or launcher.exists()
        detected.append({**entry, "available": available})
    return detected


def encode_sse(event: str, payload: dict[str, Any]) -> bytes:
    data = json.dumps(payload, sort_keys=False)
    lines = [f"event: {event}"] + [f"data: {line}" for line in data.splitlines()]
    return ("\n".join(lines) + "\n\n").encode("utf-8")


def build_snapshot() -> dict[str, Any]:
    with obs_span("control_room.build_snapshot"):
        latest_run = latest_run_summary()
        dynamic_payload = dynamic_execution_payload()
        conformance_report, enforcement = conformance_payload()
        calibration = calibration_payload()
        action_conformance = action_space_payload()
        laws = build_law_entities(
            enforcement=enforcement,
            action_conformance=action_conformance,
            latest_run=latest_run,
            calibration=calibration,
        )
        stations, files = build_station_entities(latest_run, laws)
        viewpoints = build_viewpoint_entities()

        runtime_mermaid = dyn_exec.OUTPUT_MMD.read_text(encoding="utf-8") if dyn_exec.OUTPUT_MMD.exists() else "flowchart LR\nA[No dynamic runtime diagram yet]"

        snapshot = {
            "status": "Conformance Passing" if enforcement["passed"] else "Conformance Blocking",
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S %Z"),
            "selection": {
                "default_station_id": "executive-office",
                "default_viewpoint_id": "founder-architect",
            },
            "observability": observability_status_payload(),
            "diagrams": {
                "master_systems": build_master_systems_mermaid(),
                "runtime_overview": runtime_mermaid,
                "station_focus": {
                    station["id"]: build_master_systems_mermaid(
                        focus_station_ids=[station["id"]],
                        focus_law_ids=station.get("law_ids", []),
                    )
                    for station in stations
                },
                "viewpoint_focus": {
                    viewpoint["id"]: build_master_systems_mermaid(
                        focus_station_ids=viewpoint["station_ids"],
                        focus_law_ids=viewpoint["law_ids"],
                    )
                    for viewpoint in viewpoints
                },
            },
            "metrics": {
                "conformance_passed": enforcement["passed"],
                "latest_task_result": latest_run["task_result"],
                "calibration_records": calibration.get("total_records", 0),
                "calibration_unlabeled": calibration.get("review_state_counts", {}).get("unlabeled", 0),
                "execution_families": len(dynamic_payload.get("execution_family_counts", {})),
                "latest_step_count": latest_run["step_count"],
                "planner_visible_actions": len(action_conformance["planner_visible_actions"]),
            },
            "viewpoints": viewpoints,
            "laws": laws,
            "files": files,
            "stations": stations,
            "latest_run": latest_run,
            "dynamic_execution": dynamic_payload,
            "conformance": enforcement,
            "conformance_report": conformance_report,
            "action_space_conformance": action_conformance,
            "calibration": calibration,
            "sourcegraph": sourcegraph_payload(stations, files),
            "tool_hooks": detect_tools(),
        }
        snapshot["diagrams"]["d2"] = build_d2_artifacts(snapshot)
        snapshot["structurizr"] = build_structurizr_artifacts(snapshot)
        return snapshot


CACHE = SnapshotCache()


class ControlRoomHandler(BaseHTTPRequestHandler):
    server_version = "ConcentricControlRoom/0.1"

    def _send_bytes(self, payload: bytes, content_type: str, status: int = HTTPStatus.OK) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/":
            html = (CONTROL_ROOM_DIR / "index.html").read_bytes()
            self._send_bytes(html, "text/html; charset=utf-8")
            return
        if parsed.path.startswith("/static/"):
            rel = parsed.path.removeprefix("/static/")
            target = CONTROL_ROOM_DIR / rel
            if target.exists():
                content_type = "text/plain; charset=utf-8"
                if target.suffix == ".css":
                    content_type = "text/css; charset=utf-8"
                elif target.suffix == ".js":
                    content_type = "application/javascript; charset=utf-8"
                self._send_bytes(target.read_bytes(), content_type)
                return
            self._send_bytes(b"not found", "text/plain; charset=utf-8", status=HTTPStatus.NOT_FOUND)
            return
        if parsed.path.startswith("/generated/"):
            rel = parsed.path.removeprefix("/generated/")
            target = ARTIFACTS_DIR / rel
            if target.exists():
                content_type = "text/plain; charset=utf-8"
                if target.suffix == ".svg":
                    content_type = "image/svg+xml; charset=utf-8"
                elif target.suffix == ".d2":
                    content_type = "text/plain; charset=utf-8"
                elif target.suffix == ".json":
                    content_type = "application/json; charset=utf-8"
                self._send_bytes(target.read_bytes(), content_type)
                return
            self._send_bytes(b"not found", "text/plain; charset=utf-8", status=HTTPStatus.NOT_FOUND)
            return
        if parsed.path == "/api/state":
            with obs_span("control_room.http.state"):
                payload = json.dumps(CACHE.get_or_build(), indent=2, sort_keys=False).encode("utf-8")
            self._send_bytes(payload, "application/json; charset=utf-8")
            return
        if parsed.path == "/api/events":
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.end_headers()

            last_key: tuple[float, float] | None = None
            try:
                while True:
                    current_key = snapshot_cache_key()
                    if current_key != last_key:
                        with obs_span("control_room.http.events.snapshot"):
                            payload = CACHE.get_or_build()
                        self.wfile.write(encode_sse("snapshot", payload))
                        self.wfile.flush()
                        last_key = current_key
                    else:
                        self.wfile.write(b": keepalive\n\n")
                        self.wfile.flush()
                    time.sleep(2.0)
            except (BrokenPipeError, ConnectionResetError):
                return
        self._send_bytes(b"not found", "text/plain; charset=utf-8", status=HTTPStatus.NOT_FOUND)

    def log_message(self, fmt: str, *args: Any) -> None:
        return


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--open-browser", action="store_true")
    parser.add_argument("--print-snapshot", action="store_true", help="Build one snapshot and print it as JSON.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    ensure_observability(service_name="concentric-control-room", project_name="concentric-control-room")
    if args.print_snapshot:
        print(json.dumps(CACHE.get_or_build(), indent=2, sort_keys=False))
        return 0

    address = (args.host, args.port)
    server = ThreadingHTTPServer(address, ControlRoomHandler)
    url = f"http://{args.host}:{args.port}/"
    print(f"Concentric Control Room listening on {url}")
    if args.open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
