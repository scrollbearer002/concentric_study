#!/usr/bin/env python3
"""Build Section 3 architecture-conformance artifacts.

This checker does not try to infer architecture from scratch. It evaluates the
existing recovered model against explicit conformance rules drawn from the repo's
own layering claims and classical architecture-conformance literature.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import time
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[4]
UNDERSTANDING_DIR = ROOT / "operator" / "cre" / "project_understanding"
ARTIFACTS_DIR = UNDERSTANDING_DIR / "artifacts"
IMPORT_GRAPH_PATH = ARTIFACTS_DIR / "import_graph.json"
OUTPUT_JSON = ARTIFACTS_DIR / "architecture_conformance.json"
OUTPUT_CSV = ARTIFACTS_DIR / "architecture_conformance.csv"
DEBT_REGISTER_PATH = UNDERSTANDING_DIR / "ARCHITECTURE_DEBT_REGISTER.md"

EXTERNAL_REFS = [
    "Software Reflexion Models: Bridging the Gap Between Source and High-Level Models",
    "Why Architecture Conformance Matters for Evolvable Systems",
    "ISO/IEC/IEEE 42010",
    "Architecture Reconstruction Guidelines, Third Edition",
]

SHIM_PATHS = {
    "operator/trace_writer.py",
    "operator/diagnostic_reader.py",
    "operator/healing_orchestrator.py",
    "operator/outer_loop.py",
    "operator/skill_library.py",
}

AGENT_INFRA_FACADE = "operator/agent_infra/__init__.py"

FOUNDATIONAL_INFRA = {
    "operator/agent_infra/trace_writer.py",
    "operator/agent_infra/diagnostic_reader.py",
    "operator/agent_infra/skill_library.py",
    "operator/agent_infra/action_trust.py",
}

STAGE_ORDER = {
    "operator/agent_infra/trace_writer.py": 1,
    "operator/agent_infra/diagnostic_reader.py": 2,
    "operator/agent_infra/healing_orchestrator.py": 3,
    "operator/agent_infra/outer_loop.py": 4,
}

ALLOWED_SHARED_TO_RUNTIME = {
    (
        "operator/agent_infra/startup.py",
        "operator/agent_core.py",
        "agent_core",
    ),
    (
        "operator/agent_infra/startup.py",
        "operator/visual_engine.py",
        "visual_engine",
    ),
    (
        "operator/agent_infra/startup.py",
        "operator/inference_router.py",
        "inference_router",
    ),
    (
        "operator/agent_infra/recovery.py",
        "operator/agent_core.py",
        "agent_core",
    ),
}

ALLOWED_SHIM_IMPORTS = {
    ("operator/cre/test_excalidraw_covt.py", "operator/trace_writer.py", "trace_writer"),
    ("operator/cre/test_trace_writer.py", "operator/trace_writer.py", "trace_writer"),
    ("operator/cre/test_skill_library.py", "operator/skill_library.py", "skill_library"),
    ("operator/cre/test_outer_loop.py", "operator/trace_writer.py", "trace_writer"),
    ("operator/cre/test_trace_integration.py", "operator/trace_writer.py", "trace_writer"),
    ("operator/cre/test_healing_orchestrator.py", "operator/healing_orchestrator.py", "healing_orchestrator"),
    ("operator/cre/test_healing_orchestrator.py", "operator/trace_writer.py", "trace_writer"),
    ("operator/cre/test_diagnostic_reader.py", "operator/diagnostic_reader.py", "diagnostic_reader"),
    ("operator/cre/test_diagnostic_reader.py", "operator/trace_writer.py", "trace_writer"),
}

ALLOWED_FACADE_IMPORTS = {
    ("operator/capability_router.py", "operator/agent_infra/__init__.py", "agent_infra"),
    ("operator/agent.py", "operator/agent_infra/__init__.py", "agent_infra"),
    ("operator/cre/test_excalidraw_covt.py", "operator/agent_infra/__init__.py", "agent_infra"),
    ("operator/cre/test_kleki_bmw.py", "operator/agent_infra/__init__.py", "agent_infra"),
    ("operator/cre/test_canva_draw.py", "operator/agent_infra/__init__.py", "agent_infra"),
    ("operator/cre/test_login_flow.py", "operator/agent_infra/__init__.py", "agent_infra"),
}

AC006_DEBT_CONTRACT = {
    "status": "monitored_debt",
    "owner": "repo maintainer",
    "issue": "operator/cre/project_understanding/ARCHITECTURE_DEBT_REGISTER.md#AC006",
    "review_by": "2026-04-03",
    "rationale": (
        "Root-level compatibility shims are still used by a bounded set of tests and "
        "harnesses while canonical imports remain the target surface. Growth is blocked "
        "by the conformance gate; removal is expected over time rather than immediately."
    ),
    "scope": (
        "Allowed only for the caller set frozen in ALLOWED_SHIM_IMPORTS. Any new shim "
        "import outside that frozen set is a hard regression."
    ),
}


@dataclass
class RuleRecord:
    rule_id: str
    concern: str
    intended_rule: str
    source_refs: list[str]
    external_refs: list[str]
    status: str
    evidence: list[str]
    findings: list[str]
    recommendation: str
    debt_contract: dict[str, Any] | None = None


@dataclass
class EnforcementResult:
    passed: bool
    blocking_failures: list[str]
    warnings: list[str]
    unexpected_shim_imports: list[str]
    unexpected_facade_imports: list[str]
    rule_statuses: dict[str, str]


def build_live_graph() -> dict[str, object]:
    from build_understanding_artifacts import build_import_graph, iter_project_files  # type: ignore

    py_paths = [path for path in iter_project_files() if path.suffix == ".py"]
    return build_import_graph(py_paths)


def graph_digest(graph: dict[str, object]) -> str:
    payload = json.dumps(graph, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def read_graph_artifact() -> dict[str, object]:
    return json.loads(IMPORT_GRAPH_PATH.read_text(encoding="utf-8"))


def write_graph_artifact(graph: dict[str, object]) -> None:
    IMPORT_GRAPH_PATH.write_text(json.dumps(graph, indent=2) + "\n", encoding="utf-8")


def subsystem_for_graph_path(path_str: str) -> str:
    if path_str.startswith("operator/agent_infra/"):
        return "shared_infrastructure"
    if path_str in {
        "operator/window_capture.py",
        "operator/screenshot_preprocessor.py",
    }:
        return "shared_infrastructure"
    if path_str.startswith("operator/security/"):
        return "security"
    if path_str.startswith("operator/cre/test_") or path_str.startswith("operator/cre/ablation_") or path_str.startswith("operator/cre/magma_"):
        return "experiment_harnesses"
    if path_str.startswith("operator/cre/"):
        return "cre_docs_and_artifacts"
    if path_str.startswith("operator/"):
        return "runtime_orchestrator"
    if path_str.startswith(".cursor/") or path_str == "AGENTS.md":
        return "repo_governance"
    return "workspace_root"


def load_graph(source: str = "live") -> dict[str, object]:
    if source == "live":
        return build_live_graph()
    if source == "artifact":
        return read_graph_artifact()
    raise ValueError(f"Unsupported graph source: {source}")


def fmt_edge(edge: dict[str, str]) -> str:
    return f"{edge['from']} -> {edge['to']} [{edge['import']}]"


def edge_tuple(edge: dict[str, str]) -> tuple[str, str, str]:
    return edge["from"], edge["to"], edge["import"]


def edges_matching(edges: Iterable[dict[str, str]], *, src_subsystem: str | None = None, dst_subsystem: str | None = None) -> list[dict[str, str]]:
    matched = []
    for edge in edges:
        if src_subsystem and subsystem_for_graph_path(edge["from"]) != src_subsystem:
            continue
        if dst_subsystem and subsystem_for_graph_path(edge["to"]) != dst_subsystem:
            continue
        matched.append(edge)
    return matched


def collect_shim_import_edges(graph: dict[str, object]) -> list[dict[str, str]]:
    return [edge for edge in graph["edges"] if edge["to"] in SHIM_PATHS]


def collect_facade_import_edges(graph: dict[str, object]) -> list[dict[str, str]]:
    return [edge for edge in graph["edges"] if edge["to"] == AGENT_INFRA_FACADE]


def build_rule_records(graph: dict[str, object]) -> list[RuleRecord]:
    edges: list[dict[str, str]] = graph["edges"]
    rules: list[RuleRecord] = []

    shared_to_runtime = edges_matching(edges, src_subsystem="shared_infrastructure", dst_subsystem="runtime_orchestrator")
    unexpected_shared_to_runtime = [
        edge for edge in shared_to_runtime
        if (edge["from"], edge["to"], edge["import"]) not in ALLOWED_SHARED_TO_RUNTIME
    ]
    allowed_exception_lines = [fmt_edge(edge) for edge in shared_to_runtime]
    rules.append(
        RuleRecord(
            rule_id="AC001",
            concern="layering",
            intended_rule="Shared infrastructure should not depend downward on runtime orchestrator code, except narrow boundary adapters explicitly justified by execution bootstrap or runtime-grade assertion hooks.",
            source_refs=[
                "operator/agent_infra/__init__.py:5",
                "operator/cre/PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md:69",
                "operator/cre/PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md:173",
                "operator/cre/project_understanding/SUBSYSTEM_DEPENDENCY_REPORT.md:35",
            ],
            external_refs=EXTERNAL_REFS,
            status="conforms_with_exceptions" if not unexpected_shared_to_runtime else "drift",
            evidence=allowed_exception_lines,
            findings=(
                [
                    f"Observed {len(shared_to_runtime)} shared_infrastructure -> runtime_orchestrator edges, all confined to `operator/agent_infra/startup.py` and `operator/agent_infra/recovery.py`."
                ]
                if not unexpected_shared_to_runtime else
                [f"Unexpected reverse-layer edge: {fmt_edge(edge)}" for edge in unexpected_shared_to_runtime]
            ),
            recommendation="Keep boundary-adapter imports isolated to `operator/agent_infra/startup.py` and `operator/agent_infra/recovery.py`; do not allow broader infra modules to accumulate runtime dependencies.",
        )
    )

    foundational_failures = []
    foundational_evidence = []
    for edge in edges:
        if edge["from"] in FOUNDATIONAL_INFRA:
            foundational_evidence.append(fmt_edge(edge))
            if subsystem_for_graph_path(edge["to"]) != "shared_infrastructure":
                foundational_failures.append(edge)
    rules.append(
        RuleRecord(
            rule_id="AC002",
            concern="foundational independence",
            intended_rule="Foundational infra modules (`trace_writer`, `diagnostic_reader`, `skill_library`, `action_trust`) should remain independently usable and avoid downward runtime/security coupling.",
            source_refs=[
                "operator/cre/PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md:75",
                "operator/cre/PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md:76",
                "operator/cre/PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md:78",
                "operator/cre/PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md:80",
                "operator/agent_infra/__init__.py:11",
            ],
            external_refs=EXTERNAL_REFS,
            status="conforms" if not foundational_failures else "drift",
            evidence=foundational_evidence,
            findings=(
                ["No foundational infra module imports runtime orchestrator or security code."]
                if not foundational_failures else
                [f"Foundational module leaked downward dependency: {fmt_edge(edge)}" for edge in foundational_failures]
            ),
            recommendation="Keep foundational infra modules artifact-focused and reusable; if runtime hooks are needed, pass them through context or dependency injection instead of direct imports.",
        )
    )

    chain_reverse_edges = []
    chain_edges = []
    for edge in edges:
        src = edge["from"]
        dst = edge["to"]
        if src in STAGE_ORDER and dst in STAGE_ORDER:
            chain_edges.append(fmt_edge(edge))
            if STAGE_ORDER[src] < STAGE_ORDER[dst]:
                chain_reverse_edges.append(edge)
    rules.append(
        RuleRecord(
            rule_id="AC003",
            concern="unidirectional chain",
            intended_rule="The canonical infra chain should remain unidirectional: `TraceWriter -> DiagnosticReader -> HealingOrchestrator`, with `OuterLoop` as the integration layer above prior services.",
            source_refs=[
                "operator/agent_infra/__init__.py:5",
                "operator/agent_infra/__init__.py:7",
                "operator/agent_infra/__init__.py:9",
                "operator/cre/PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md:173",
            ],
            external_refs=EXTERNAL_REFS,
            status="conforms" if not chain_reverse_edges else "drift",
            evidence=chain_edges,
            findings=(
                ["No reverse edge violates the documented TraceWriter/DiagnosticReader/HealingOrchestrator/OuterLoop staging."]
                if not chain_reverse_edges else
                [f"Reverse chain dependency: {fmt_edge(edge)}" for edge in chain_reverse_edges]
            ),
            recommendation="Preserve the chain ordering; new orchestration or learning features should attach at the outer loop or adjacent extension modules, not back-propagate into tracing foundations.",
        )
    )

    reverse_into_harnesses = [
        edge for edge in edges if subsystem_for_graph_path(edge["to"]) == "experiment_harnesses" and subsystem_for_graph_path(edge["from"]) != "experiment_harnesses"
    ]
    rules.append(
        RuleRecord(
            rule_id="AC004",
            concern="harness directionality",
            intended_rule="Experiment harnesses may consume runtime, infrastructure, and security layers, but production subsystems should not depend on harness/test code.",
            source_refs=[
                "operator/cre/PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md:105",
                "operator/cre/project_understanding/SUBSYSTEM_DEPENDENCY_REPORT.md:11",
                "operator/cre/project_understanding/SUBSYSTEM_DEPENDENCY_REPORT.md:32",
                "operator/cre/project_understanding/SUBSYSTEM_DEPENDENCY_REPORT.md:33",
            ],
            external_refs=EXTERNAL_REFS,
            status="conforms" if not reverse_into_harnesses else "drift",
            evidence=[fmt_edge(edge) for edge in reverse_into_harnesses],
            findings=(
                ["No runtime, infrastructure, or security module imports experiment-harness code."]
                if not reverse_into_harnesses else
                [f"Subsystem depends on harness code: {fmt_edge(edge)}" for edge in reverse_into_harnesses]
            ),
            recommendation="Keep harnesses as consumers only; any reusable logic found there should be extracted into canonical runtime or infra modules rather than imported back into production layers.",
        )
    )

    security_outbound = [
        edge for edge in edges if subsystem_for_graph_path(edge["from"]) == "security" and subsystem_for_graph_path(edge["to"]) != "security"
    ]
    rules.append(
        RuleRecord(
            rule_id="AC005",
            concern="security isolation",
            intended_rule="Security should remain a narrow guardrail boundary and not grow outbound dependencies into runtime or harness layers.",
            source_refs=[
                "AGENTS.md",
                "operator/cre/project_understanding/SUBSYSTEM_DEPENDENCY_REPORT.md:14",
                "operator/cre/project_understanding/SUBSYSTEM_DEPENDENCY_REPORT.md:37",
            ],
            external_refs=EXTERNAL_REFS,
            status="conforms" if not security_outbound else "drift",
            evidence=[fmt_edge(edge) for edge in security_outbound],
            findings=(
                ["Security imports are self-contained within the security subsystem."]
                if not security_outbound else
                [f"Security leaked outward dependency: {fmt_edge(edge)}" for edge in security_outbound]
            ),
            recommendation="Keep sanitization and credential/HITL code inward-only so safety boundaries remain simple to audit.",
        )
    )

    shim_edges = [edge for edge in edges if edge["to"] in SHIM_PATHS]
    rules.append(
        RuleRecord(
            rule_id="AC006",
            concern="canonical import surface",
            intended_rule="Compatibility shims should remain backward-compatible only; active code should prefer canonical `agent_infra` imports over root-level shim modules.",
            source_refs=[
                "operator/cre/project_understanding/README.md:25",
                "operator/cre/project_understanding/FOLDER_ATLAS.md:38",
                "operator/cre/project_understanding/SUBSYSTEM_DEPENDENCY_REPORT.md:84",
                "operator/cre/project_understanding/PHD_DEPTH_AUDIT.md:103",
            ],
            external_refs=EXTERNAL_REFS,
            status="monitored_debt" if shim_edges else "conforms",
            evidence=[fmt_edge(edge) for edge in shim_edges],
            findings=(
                [f"Observed {len(shim_edges)} live imports that still target root-level compatibility shims."]
                if shim_edges else ["No live imports target compatibility shims."]
            ),
            recommendation="Migrate tests and harnesses from `trace_writer`, `diagnostic_reader`, `healing_orchestrator`, and `skill_library` shims to canonical `agent_infra.*` imports, then retire shims when callers reach zero.",
            debt_contract=AC006_DEBT_CONTRACT if shim_edges else None,
        )
    )

    facade_edges = [edge for edge in edges if edge["to"] == AGENT_INFRA_FACADE]
    rules.append(
        RuleRecord(
            rule_id="AC007",
            concern="facade coupling",
            intended_rule="The `agent_infra` package facade is acceptable as a convenience layer, but it should be monitored because it concentrates coupling and can hide module-boundary slippage.",
            source_refs=[
                "operator/cre/project_understanding/PHD_DEPTH_AUDIT.md:26",
                "operator/cre/project_understanding/SUBSYSTEM_DEPENDENCY_REPORT.md:61",
                "operator/cre/project_understanding/SUBSYSTEM_DEPENDENCY_REPORT.md:86",
            ],
            external_refs=EXTERNAL_REFS,
            status="advisory" if facade_edges else "conforms",
            evidence=[fmt_edge(edge) for edge in facade_edges],
            findings=(
                [f"Observed {len(facade_edges)} direct imports of the `agent_infra` package facade."]
                if facade_edges else ["No direct imports of the `agent_infra` package facade were observed."]
            ),
            recommendation="Prefer direct submodule imports in code paths where boundary clarity matters; keep facade imports for ergonomic entrypoints only.",
        )
    )

    return rules


def build_outputs(graph: dict[str, object]) -> dict[str, object]:
    rules = build_rule_records(graph)
    status_summary = Counter(rule.status for rule in rules)
    payload = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "graph_digest": graph_digest(graph),
        "rule_count": len(rules),
        "status_summary": dict(status_summary),
        "rules": [asdict(rule) for rule in rules],
    }
    rows = [
        {
            "rule_id": rule.rule_id,
            "concern": rule.concern,
            "status": rule.status,
            "intended_rule": rule.intended_rule,
            "source_refs": "; ".join(rule.source_refs),
            "external_refs": "; ".join(rule.external_refs),
            "evidence": " | ".join(rule.evidence),
            "findings": " | ".join(rule.findings),
            "recommendation": rule.recommendation,
            "debt_contract": json.dumps(rule.debt_contract, sort_keys=True) if rule.debt_contract else "",
        }
        for rule in rules
    ]
    return {"payload": payload, "rows": rows}


def write_outputs(result: dict[str, object]) -> None:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    payload = result["payload"]
    rows = result["rows"]
    OUTPUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def evaluate_enforcement(graph: dict[str, object] | None = None) -> EnforcementResult:
    if graph is None:
        graph = load_graph(source="live")

    rules = build_rule_records(graph)
    rule_map = {rule.rule_id: rule for rule in rules}
    blocking_failures: list[str] = []
    warnings: list[str] = []

    if rule_map["AC001"].status == "drift":
        blocking_failures.extend(rule_map["AC001"].findings)

    for rule_id in ("AC002", "AC003", "AC004", "AC005"):
        if rule_map[rule_id].status != "conforms":
            blocking_failures.extend(rule_map[rule_id].findings)

    unexpected_shim_edges = [
        edge for edge in collect_shim_import_edges(graph)
        if edge_tuple(edge) not in ALLOWED_SHIM_IMPORTS
    ]
    if unexpected_shim_edges:
        blocking_failures.extend(
            [f"Unexpected shim import regression: {fmt_edge(edge)}" for edge in unexpected_shim_edges]
        )

    unexpected_facade_edges = [
        edge for edge in collect_facade_import_edges(graph)
        if edge_tuple(edge) not in ALLOWED_FACADE_IMPORTS
    ]
    if unexpected_facade_edges:
        blocking_failures.extend(
            [f"Unexpected facade-import growth: {fmt_edge(edge)}" for edge in unexpected_facade_edges]
        )

    if rule_map["AC006"].status == "monitored_debt":
        warnings.extend(rule_map["AC006"].findings)
    if rule_map["AC007"].status == "advisory":
        warnings.extend(rule_map["AC007"].findings)

    return EnforcementResult(
        passed=not blocking_failures,
        blocking_failures=blocking_failures,
        warnings=warnings,
        unexpected_shim_imports=[fmt_edge(edge) for edge in unexpected_shim_edges],
        unexpected_facade_imports=[fmt_edge(edge) for edge in unexpected_facade_edges],
        rule_statuses={rule.rule_id: rule.status for rule in rules},
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check or explicitly regenerate architecture conformance artifacts.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Pure verification mode. Rebuilds the live import graph in memory, writes nothing, and exits non-zero on hard regressions.",
    )
    parser.add_argument(
        "--enforce",
        action="store_true",
        help="Backward-compatible alias for --check.",
    )
    parser.add_argument(
        "--regen-graph",
        action="store_true",
        help="Explicitly regenerate artifacts/import_graph.json from the live repo.",
    )
    parser.add_argument(
        "--write-artifacts",
        action="store_true",
        help="Explicitly write architecture_conformance.json and architecture_conformance.csv from the live repo graph.",
    )
    args = parser.parse_args(argv)

    if (args.check or args.enforce) and (args.regen_graph or args.write_artifacts):
        parser.error("--check/--enforce cannot be combined with --regen-graph or --write-artifacts")

    mode_check = args.check or args.enforce or not (args.regen_graph or args.write_artifacts)
    graph = load_graph(source="live")
    result = build_outputs(graph)
    summary = {
        "graph_digest": result["payload"]["graph_digest"],
        "rule_count": result["payload"]["rule_count"],
        "status_summary": result["payload"]["status_summary"],
    }

    if mode_check:
        enforcement = evaluate_enforcement(graph)
        payload = {
            **summary,
            "mode": "check",
            "writes_performed": [],
            "enforcement_passed": enforcement.passed,
            "blocking_failures": enforcement.blocking_failures,
            "warnings": enforcement.warnings,
            "unexpected_shim_imports": enforcement.unexpected_shim_imports,
            "unexpected_facade_imports": enforcement.unexpected_facade_imports,
            "rule_statuses": enforcement.rule_statuses,
        }
        print(json.dumps(payload, indent=2, sort_keys=False))
        return 0 if enforcement.passed else 1

    writes_performed: list[str] = []
    if args.regen_graph:
        ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
        write_graph_artifact(graph)
        writes_performed.append(str(IMPORT_GRAPH_PATH.relative_to(ROOT)))
    if args.write_artifacts:
        write_outputs(result)
        writes_performed.extend(
            [
                str(OUTPUT_JSON.relative_to(ROOT)),
                str(OUTPUT_CSV.relative_to(ROOT)),
            ]
        )

    payload = {
        **summary,
        "mode": "write",
        "writes_performed": writes_performed,
    }
    print(json.dumps(payload, indent=2, sort_keys=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
