#!/usr/bin/env python3
"""Architecture conformance regression tests.

These tests enforce the bounded architecture model recovered in the
project-understanding corpus. They follow the source-vs-model conformance line
from Software Reflexion Models and the SEI guidance that conformance checks
should remain live rather than one-off analysis artifacts.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Import the conformance tool directly from the understanding corpus tooling.
TOOLS_DIR = Path(__file__).resolve().parent / "project_understanding" / "tools"
sys.path.insert(0, str(TOOLS_DIR))

from build_architecture_conformance import (  # type: ignore
    ALLOWED_FACADE_IMPORTS,
    ALLOWED_SHIM_IMPORTS,
    AC006_DEBT_CONTRACT,
    build_outputs,
    collect_facade_import_edges,
    collect_shim_import_edges,
    edge_tuple,
    evaluate_enforcement,
    load_graph,
)
from build_understanding_artifacts import build_import_graph, iter_project_files  # type: ignore


def test_architecture_conformance_enforcement_passes() -> None:
    """The current repo should satisfy the hard conformance gate.

    Existing documented shim debt is tolerated as baseline, but new regressions
    must fail immediately.
    """
    enforcement = evaluate_enforcement()
    assert enforcement.passed, enforcement.blocking_failures



def test_shim_import_surface_is_not_growing() -> None:
    """No new callers should target compatibility shims."""
    graph = load_graph()
    current = {edge_tuple(edge) for edge in collect_shim_import_edges(graph)}
    unexpected = current - ALLOWED_SHIM_IMPORTS
    assert not unexpected, f"Unexpected shim imports: {sorted(unexpected)}"



def test_facade_import_surface_is_not_growing() -> None:
    """The `agent_infra` facade is tolerated, but its caller set is frozen."""
    graph = load_graph()
    current = {edge_tuple(edge) for edge in collect_facade_import_edges(graph)}
    unexpected = current - ALLOWED_FACADE_IMPORTS
    assert not unexpected, f"Unexpected facade imports: {sorted(unexpected)}"


def test_live_import_graph_generation_is_deterministic() -> None:
    """Live graph rebuilding should be invariant to filesystem enumeration order."""
    py_paths = [path for path in iter_project_files() if path.suffix == ".py"]
    forward = build_import_graph(py_paths)
    reverse = build_import_graph(list(reversed(py_paths)))
    assert forward == reverse


def test_check_mode_is_pure(monkeypatch, tmp_path: Path) -> None:
    """Pure check mode must not mutate conformance artifacts."""
    import build_architecture_conformance as conformance  # type: ignore

    monkeypatch.setattr(conformance, "IMPORT_GRAPH_PATH", tmp_path / "import_graph.json")
    monkeypatch.setattr(conformance, "OUTPUT_JSON", tmp_path / "architecture_conformance.json")
    monkeypatch.setattr(conformance, "OUTPUT_CSV", tmp_path / "architecture_conformance.csv")

    exit_code = conformance.main(["--check"])
    assert exit_code == 0
    assert not conformance.IMPORT_GRAPH_PATH.exists()
    assert not conformance.OUTPUT_JSON.exists()
    assert not conformance.OUTPUT_CSV.exists()


def test_ac006_is_encoded_as_monitored_debt() -> None:
    """Shim debt should be explicit monitored debt, not generic drift."""
    graph = load_graph(source="live")
    payload = build_outputs(graph)["payload"]
    ac006 = next(rule for rule in payload["rules"] if rule["rule_id"] == "AC006")
    assert ac006["status"] == "monitored_debt"
    assert ac006["debt_contract"] == AC006_DEBT_CONTRACT
