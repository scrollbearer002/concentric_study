#!/usr/bin/env python3
"""Build a whole-project truth audit for concentric_study.

Scope:
- Include the live repo on this machine
- Exclude operator/venv and operator/cre/runs from classification
- Audit-only: no cleanup/refactor mutations
"""
from __future__ import annotations

import ast
import csv
import json
import re
import subprocess
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[3]
CRE_DIR = ROOT / "operator" / "cre"
ARTIFACTS_DIR = CRE_DIR / "artifacts"

SKIP_PATH_PARTS = {
    ".git",
    "operator/venv",
    "operator/cre/runs",
    ".pytest_cache",
}
LOW_VALUE_SKIP_PARTS = {"__pycache__"}

CORE_RUNTIME_PATHS = {
    "operator/agent.py",
    "operator/agent_core.py",
    "operator/action_space.py",
    "operator/capability_router.py",
    "operator/inference_router.py",
    "operator/window_capture.py",
    "operator/visual_engine.py",
    "operator/a11y_engine.py",
    "operator/element_map.py",
    "operator/web_primitives.py",
}

SHARED_INFRA_PATHS = {
    "operator/agent_infra/__init__.py",
    "operator/agent_infra/action_allowlist.py",
    "operator/agent_infra/action_contracts.py",
    "operator/agent_infra/action_handlers.py",
    "operator/agent_infra/action_trust.py",
    "operator/agent_infra/benchmark_evaluator.py",
    "operator/agent_infra/decision_graph.py",
    "operator/agent_infra/diagnostic_reader.py",
    "operator/agent_infra/healing_orchestrator.py",
    "operator/agent_infra/host_tool_health.py",
    "operator/agent_infra/outer_loop.py",
    "operator/agent_infra/recovery.py",
    "operator/agent_infra/research_agent.py",
    "operator/agent_infra/site_knowledge.py",
    "operator/agent_infra/skill_library.py",
    "operator/agent_infra/startup.py",
    "operator/agent_infra/summarizer.py",
    "operator/agent_infra/trace_writer.py",
    "operator/agent_infra/verification_gate.py",
    "operator/agent_infra/visual_monitor.py",
}

SECURITY_PATHS = {
    "operator/security/__init__.py",
    "operator/security/credential_vault.py",
    "operator/security/sanitizer.py",
}

ROOT_SHIMS = {
    "operator/trace_writer.py",
    "operator/diagnostic_reader.py",
    "operator/healing_orchestrator.py",
    "operator/outer_loop.py",
    "operator/skill_library.py",
}

LEGACY_RUNTIME_PATHS = {
    "operator/codex_client.py",
    "operator/vlm_coordinator.py",
    "operator/cre/codex_kernel.lua",
    "operator/cre/showcase.sh",
    "operator/cre/verify_kernel.sh",
    "operator/cre/run_agent.sh",
    "operator/cre/run_ultimate_tests.sh",
}

HIGH_AUTHORITY_DOCS = {
    "AGENTS.md",
    "DUAL_AGENT_LOOP_PLAN.md",
    "operator/cre/PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md",
    "operator/cre/MASTER_TOOL_LIST_PHD.md",
    "operator/cre/TOOL_CHEAT_SHEET_PHD.md",
    "operator/cre/project_understanding/README.md",
}

CURRENT_SUPPORTING_DOCS = {
    "operator/cre/PHD_DECISION_PRACTICE.md",
    "operator/cre/PHASE_1_ENVIRONMENT_BENEFITS_PHD.md",
    "operator/cre/CANONICAL_RUNTIME_BASELINE_PHD.md",
    "operator/cre/PROJECT_SCIENTIFIC_COHERENCE_AUDIT_PHD.md",
    "operator/cre/project_understanding/SECTION_4_CONFORMANCE_ENFORCEMENT.md",
    "operator/cre/project_understanding/SECTION_5_DYNAMIC_EXECUTION_ARCHITECTURE.md",
}

GENERATED_PREFIXES = (
    "operator/cre/project_understanding/artifacts/",
    "operator/cre/artifacts/",
)

FIXTURE_PREFIXES = (
    "operator/cre/fixtures/",
    "operator/cre/evidence_concentric_clean/",
)

EXPERIMENTAL_SCRIPT_PATTERNS = (
    "operator/cre/jspaint_draw_",
    "operator/cre/magma_draw_",
    "operator/cre/test_canva_",
    "operator/cre/test_kleki_",
    "operator/cre/test_kreska_",
    "operator/cre/test_excalidraw_",
    "operator/cre/run_preclick_smoke.py",
    "operator/cre/magma_open_canvas.py",
    "operator/cre/magma_traced_run.py",
    "operator/cre/magma_bmw_e30_full_run.py",
)

TOPIC_BUCKETS = {
    "architecture": {"architecture", "conformance", "dependency", "runtime_flows", "diagram", "surface"},
    "project_understanding": {"understanding", "audit", "traceability", "walkthrough", "phd_depth"},
    "tooling": {"tool", "inventory", "cheat_sheet", "environment", "monitor", "compliance"},
    "research_agent": {"research", "subject_lookup", "placement"},
    "art_iq_demo": {"kleki", "jspaint", "magma", "reddit", "iq", "draw", "polo", "tiger", "bmw"},
    "report_summary": {"summary", "report", "final_report", "completion", "execution"},
}

RESEARCH_SOURCES = [
    {
        "title": "ISO/IEC/IEEE 42010 Architecture Descriptions",
        "url": "https://www.iso-architecture.org/ieee-1471/ads/",
        "source_class": "architecture_standard",
        "why_relevant": "Defines architecture-description rigor, viewpoints, and stakeholder-grounded documentation.",
        "claims_supported": ["doc truth", "architecture surface classification"],
    },
    {
        "title": "Documenting Software Architectures: Views and Beyond, Second Edition",
        "url": "https://www.sei.cmu.edu/library/documenting-software-architectures-views-and-beyond-second-edition/",
        "source_class": "architecture_guidance",
        "why_relevant": "Supports separating authoritative views from supporting or duplicated docs.",
        "claims_supported": ["doc authority", "current architecture surface"],
    },
    {
        "title": "Architecture Reconstruction Guidelines, Third Edition",
        "url": "https://www.sei.cmu.edu/library/architecture-reconstruction-guidelines-third-edition/",
        "source_class": "architecture_reconstruction",
        "why_relevant": "Supports reconstructing as-built architecture from code, tests, and artifacts.",
        "claims_supported": ["runtime truth audit", "legacy/current boundary"],
    },
    {
        "title": "Managing Technical Debt: Identify Technical Debt Items",
        "url": "https://www.sei.cmu.edu/library/managing-technical-debt-identify-technical-debt-items/",
        "source_class": "technical_debt",
        "why_relevant": "Supports identifying stale or duplicative surfaces as debt candidates rather than deleting by instinct.",
        "claims_supported": ["dead-weight signal analysis"],
    },
    {
        "title": "Got Technical Debt? Surfacing Elusive Technical Debt in Issue Trackers",
        "url": "https://www.sei.cmu.edu/library/got-technical-debt-surfacing-elusive-technical-debt-in-issue-trackers/",
        "source_class": "technical_debt",
        "why_relevant": "Supports explicit evidence-backed debt signaling and review recommendations.",
        "claims_supported": ["dead-weight signal analysis"],
    },
    {
        "title": "Why reproducible builds?",
        "url": "https://reproducible-builds.org/docs/why/",
        "source_class": "reproducibility",
        "why_relevant": "Supports keeping generated artifacts and evidence surfaces classified distinctly from source of truth.",
        "claims_supported": ["generated vs current", "artifact discipline"],
    },
    {
        "title": "Making plans — reproducible-builds.org",
        "url": "https://reproducible-builds.org/docs/plans/",
        "source_class": "reproducibility",
        "why_relevant": "Supports explicit plans for reproducible generated artifacts.",
        "claims_supported": ["generated vs current", "artifact discipline"],
    },
    {
        "title": "Hermeticity - Bazel",
        "url": "https://docs.bazel.build/versions/master/hermeticity.html",
        "source_class": "build_discipline",
        "why_relevant": "Supports separating checked source from generated/build outputs.",
        "claims_supported": ["generated classification", "dead-weight signals"],
    },
    {
        "title": "OSWorld",
        "url": "https://arxiv.org/abs/2404.07972",
        "source_class": "gui_agent_research",
        "why_relevant": "Supports evaluating whether GUI-agent claims in the repo remain scientifically coherent.",
        "claims_supported": ["scientific coherence", "runtime truth"],
    },
    {
        "title": "SeeAct",
        "url": "https://arxiv.org/abs/2401.01614",
        "source_class": "gui_agent_research",
        "why_relevant": "Supports grounding and action-planning claims for the current project.",
        "claims_supported": ["scientific coherence", "runtime truth"],
    },
    {
        "title": "AppAgent",
        "url": "https://arxiv.org/abs/2312.13771",
        "source_class": "gui_agent_research",
        "why_relevant": "Supports the research-first planning layer used by the repo.",
        "claims_supported": ["scientific coherence", "research_agent role"],
    },
    {
        "title": "GUI-explorer",
        "url": "https://arxiv.org/abs/2505.16827",
        "source_class": "gui_agent_research",
        "why_relevant": "Supports exploration and site-knowledge acquisition claims.",
        "claims_supported": ["site knowledge", "exploration loop"],
    },
    {
        "title": "MCP-Atlas",
        "url": "https://arxiv.org/abs/2602.00933",
        "source_class": "evaluation_research",
        "why_relevant": "Supports claims-based benchmark framing in the repo.",
        "claims_supported": ["benchmark evaluator", "scientific coherence"],
    },
    {
        "title": "OWASP Top 10 for LLM Applications 2025",
        "url": "https://genai.owasp.org/resource/owasp-top-10-for-llm-applications-2025/",
        "source_class": "security_guidance",
        "why_relevant": "Supports security-surface classification and policy grounding.",
        "claims_supported": ["security truth audit"],
    },
]


@dataclass
class TruthInventoryRecord:
    path: str
    kind: str
    status: str
    system_role: str
    declared_purpose: str
    observed_evidence: list[str]
    active_entrypoints: list[str]
    tests_covering_it: list[str]
    docs_describing_it: list[str]
    dead_weight_signal: str
    notes: str


@dataclass
class DocTruthRecord:
    path: str
    authority_level: str
    topic: str
    current_accuracy: str
    duplicates: list[str]
    generated_or_manual: str
    recommended_status: str
    notes: str


@dataclass
class DeadWeightSignalRecord:
    path_or_family: str
    signal_type: str
    evidence: list[str]
    confidence: str
    why_not_core: str
    why_not_legacy: str
    why_not_generated: str
    review_recommendation: str


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def should_skip(path: Path) -> bool:
    rel_path = rel(path)
    return any(part in rel_path for part in SKIP_PATH_PARTS) or any(part in rel_path for part in LOW_VALUE_SKIP_PARTS)


def is_text_like(path: Path) -> bool:
    return path.suffix.lower() in {
        ".py",
        ".md",
        ".txt",
        ".json",
        ".jsonl",
        ".yaml",
        ".yml",
        ".html",
        ".sh",
        ".lua",
        ".csv",
        ".mdc",
    }


def iter_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if path.is_dir():
            continue
        if should_skip(path):
            continue
        if path.suffix == ".pyc":
            continue
        files.append(path)
    return sorted(files, key=rel)


def iter_cache_artifacts() -> list[str]:
    cache_paths: list[str] = []
    for path in ROOT.rglob("*"):
        if path.is_dir():
            continue
        path_str = rel(path)
        if "__pycache__" in path_str or path.suffix == ".pyc":
            if "operator/venv/" in path_str or "operator/cre/runs/" in path_str:
                continue
            cache_paths.append(path_str)
    return sorted(cache_paths)


def run_command(cmd: str, cwd: Path | None = None) -> dict[str, object]:
    proc = subprocess.run(
        cmd,
        shell=True,
        cwd=cwd or ROOT,
        text=True,
        capture_output=True,
    )
    return {
        "command": cmd,
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }


def collect_baseline() -> dict[str, object]:
    python_files = [p for p in iter_files() if p.suffix == ".py"]
    py_excl_venv_runs = [p for p in python_files if "operator/venv/" not in rel(p) and "operator/cre/runs/" not in rel(p)]
    ext_counts = Counter(p.suffix or "<no_ext>" for p in iter_files() if "__pycache__" not in rel(p))
    top_dirs = Counter(rel(p).split("/")[0] if "/" in rel(p) else "." for p in iter_files() if "__pycache__" not in rel(p))
    git_probe = run_command("git rev-parse --is-inside-work-tree")
    test_baseline = run_command("./venv/bin/python -m pytest cre/test_*.py -q", cwd=ROOT / "operator")
    conformance = run_command("./venv/bin/python cre/project_understanding/tools/build_architecture_conformance.py --check", cwd=ROOT / "operator")
    host_health = run_command("./venv/bin/python -m agent_infra.host_tool_health --summary --has-url", cwd=ROOT / "operator")
    dependency_files = [
        path
        for path in ["operator/requirements.txt", "operator/requirements-base.txt", "operator/requirements-optional.txt", "operator/requirements-legacy.txt"]
        if (ROOT / path).exists()
    ]
    return {
        "repo_root": str(ROOT),
        "git_checkout": git_probe["stdout"] == "true",
        "python_file_count_excluding_venv_and_runs": len(py_excl_venv_runs),
        "top_level_structure": dict(top_dirs.most_common()),
        "extension_counts": dict(ext_counts.most_common()),
        "dependency_files": dependency_files,
        "test_baseline": test_baseline,
        "architecture_conformance_baseline": conformance,
        "host_tool_health_baseline": host_health,
    }


def module_variants(path_str: str) -> set[str]:
    path = Path(path_str)
    if path.suffix != ".py":
        return set()
    parts = list(path.with_suffix("").parts)
    variants = {".".join(parts)}
    if parts and parts[0] == "operator":
        variants.add(".".join(parts[1:]))
        if len(parts) >= 3 and parts[1] == "agent_infra":
            variants.add(f"agent_infra.{'.'.join(parts[2:])}")
        if len(parts) >= 3 and parts[1] == "security":
            variants.add(f"security.{'.'.join(parts[2:])}")
    return {v for v in variants if v}


def build_import_maps(files: list[Path]) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    module_to_path: dict[str, str] = {}
    py_files = [p for p in files if p.suffix == ".py"]
    for path in py_files:
        path_str = rel(path)
        for variant in module_variants(path_str):
            module_to_path[variant] = path_str

    importers_for_path: dict[str, set[str]] = defaultdict(set)
    imports_from_path: dict[str, set[str]] = defaultdict(set)
    for path in py_files:
        path_str = rel(path)
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                base = "." * node.level + (node.module or "")
                if node.level and path_str.startswith("operator/"):
                    # Resolve relative imports roughly inside the operator package.
                    current_parts = Path(path_str).with_suffix("").parts[1:-1]
                    if node.level <= len(current_parts) + 1:
                        anchor = list(current_parts[: len(current_parts) + 1 - node.level])
                        if node.module:
                            anchor.extend(node.module.split("."))
                        base = ".".join(anchor)
                    else:
                        base = node.module or ""
                if base:
                    names.append(base)
                for alias in node.names:
                    if base:
                        names.append(f"{base}.{alias.name}")
                    else:
                        names.append(alias.name)
            for name in names:
                matched = None
                if name in module_to_path:
                    matched = module_to_path[name]
                else:
                    for i in range(len(name.split(".")), 0, -1):
                        candidate = ".".join(name.split(".")[:i])
                        if candidate in module_to_path:
                            matched = module_to_path[candidate]
                            break
                if matched and matched != path_str:
                    importers_for_path[matched].add(path_str)
                    imports_from_path[path_str].add(matched)
    return (
        {k: sorted(v) for k, v in importers_for_path.items()},
        {k: sorted(v) for k, v in imports_from_path.items()},
    )


def load_text_cache(files: list[Path]) -> dict[str, str]:
    cache: dict[str, str] = {}
    for path in files:
        if not is_text_like(path):
            continue
        try:
            cache[rel(path)] = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
    return cache


def find_doc_mentions(target: str, text_cache: dict[str, str]) -> list[str]:
    basename = Path(target).name
    stem = Path(target).stem
    mentions: list[str] = []
    exact_patterns = [target, f"`{target}`", basename, f"`{basename}`"]
    stem_pattern = re.compile(rf"\b{re.escape(stem)}\b")
    for path, text in text_cache.items():
        if not path.endswith(".md") and not path.endswith(".mdc"):
            continue
        if path == target:
            continue
        if any(pat in text for pat in exact_patterns) or stem_pattern.search(text):
            mentions.append(path)
    return sorted(set(mentions))


def find_test_mentions(target: str, imports_for_path: dict[str, list[str]], text_cache: dict[str, str]) -> list[str]:
    basename = Path(target).stem
    results = [p for p in imports_for_path.get(target, []) if "/test_" in p]
    for path, text in text_cache.items():
        if not path.startswith("operator/cre/test_") and path != "operator/test_router_dryrun.py":
            continue
        if path == target:
            continue
        if target in text or basename in text:
            results.append(path)
    return sorted(set(results))


def classify_kind(path_str: str) -> str:
    if path_str.endswith(".py"):
        if path_str == "operator/cre/conftest.py":
            return "test"
        if path_str.startswith("operator/cre/test_") or path_str == "operator/test_router_dryrun.py":
            return "test"
        if path_str.startswith("operator/cre/tools/") or path_str.startswith("operator/cre/project_understanding/tools/"):
            return "script"
        if path_str.startswith("operator/cre/"):
            return "script"
        if path_str in LEGACY_RUNTIME_PATHS or path_str in ROOT_SHIMS or path_str in {"operator/codex_client.py", "operator/vlm_coordinator.py"}:
            return "legacy_runtime"
        return "runtime_code"
    if path_str.endswith(".md") or path_str.endswith(".mdc"):
        return "doc"
    if path_str.endswith(".sh") or path_str.endswith(".lua"):
        return "script"
    if path_str.endswith(".html"):
        return "fixture"
    if path_str.startswith(GENERATED_PREFIXES):
        return "generated"
    return "artifact"


def classify_status(path_str: str, kind: str, importers: list[str], tests: list[str], docs: list[str]) -> tuple[str, str]:
    name = Path(path_str).name
    if path_str in CORE_RUNTIME_PATHS or path_str in SHARED_INFRA_PATHS or path_str in SECURITY_PATHS:
        return "current", ""
    if path_str in ROOT_SHIMS:
        return "legacy", "Compatibility shim over canonical agent_infra implementation."
    if path_str in LEGACY_RUNTIME_PATHS:
        return "legacy", "Legacy runtime/tooling retained for compatibility or lineage."
    if path_str.startswith("operator/cre/project_understanding/artifacts/") or path_str.startswith("operator/cre/artifacts/"):
        return "generated", ""
    if path_str.startswith("operator/cre/project_understanding/tools/") or path_str.startswith("operator/cre/tools/"):
        return "current", "Audit/build tooling for repo governance and evidence layers."
    if path_str.startswith(FIXTURE_PREFIXES):
        return "experimental", "Fixture or curated evidence bundle."
    if path_str.startswith("operator/cre/transcripts/"):
        return "generated", "Transcript/handoff artifact."
    if path_str.startswith("operator/cre/reddit_research_demo/") or "iq_test_" in path_str or path_str.endswith(".png"):
        if tests or docs:
            return "experimental", "Evidence/demo artifact linked to current docs or tests."
        return "stale_candidate", "Artifact or screenshot with weak current linkage."
    if kind == "test":
        if path_str in {
            "operator/cre/test_trace_writer.py",
            "operator/cre/test_diagnostic_reader.py",
            "operator/cre/test_healing_orchestrator.py",
            "operator/cre/test_skill_library.py",
            "operator/cre/test_action_trust.py",
            "operator/cre/test_host_tool_health.py",
            "operator/cre/test_architecture_conformance.py",
            "operator/cre/test_preclick_confirmation.py",
            "operator/cre/test_window_capture.py",
            "operator/cre/test_screenshot_preprocessor.py",
            "operator/cre/test_runtime_tool_integration.py",
            "operator/cre/test_research_guided_planning.py",
            "operator/cre/test_phase2_method_brief.py",
            "operator/cre/test_phase3_equation_solver.py",
            "operator/cre/test_phase4_visual_monitoring.py",
            "operator/test_router_dryrun.py",
        }:
            return "current", "Protects strong core or governance path."
        if path_str in {
            "operator/cre/test_drag_drop.py",
            "operator/cre/test_smooth_movement.py",
            "operator/cre/test_excalidraw_autonomous.py",
            "operator/cre/test_excalidraw_covt.py",
        }:
            return "legacy", "Covers older/compatibility runtime surfaces."
        if path_str in {
            "operator/cre/test_canva_ai_image.py",
            "operator/cre/test_canva_draw.py",
            "operator/cre/test_kleki_bmw.py",
            "operator/cre/test_kreska_statue.py",
        }:
            return "experimental", "Demo/integration coverage for bounded art branches."
        return "current", "Active test surface."
    if kind == "doc":
        if path_str in HIGH_AUTHORITY_DOCS:
            return "current", "High-authority current doc."
        if path_str in CURRENT_SUPPORTING_DOCS or path_str.startswith("operator/cre/project_understanding/"):
            return "current", "Current supporting or generated-understanding doc."
        if any(token in name.upper() for token in {"SUMMARY", "FINAL_REPORT", "COMPLETION", "EXECUTION_SUMMARY"}) and len(docs) <= 1:
            return "stale_candidate", "Summary/report style doc with weak authority and weak linkage."
        if "PHD" in name.upper() or "AUDIT" in name.upper() or "RESEARCH" in name.upper():
            return "experimental", "Supporting research or audit memo."
        return "historical_reference", "Historical/supporting doc outside the current authoritative set."
    if kind == "fixture":
        return "experimental", "Local fixture or test input."
    if kind == "generated":
        return "generated", "Machine-generated artifact."
    if kind == "script":
        if path_str in LEGACY_RUNTIME_PATHS:
            return "legacy", "Legacy operational script."
        if path_str.startswith("operator/cre/"):
            return "experimental", "One-off operational or demo script."
        return "current", "Current repo script."
    if kind == "artifact":
        if path_str in {"injection_test.log"}:
            return "experimental", "One-off log artifact."
        return "experimental", "Evidence or demo artifact."
    return "experimental", ""


def classify_role(path_str: str, kind: str) -> str:
    if path_str in CORE_RUNTIME_PATHS:
        return "core_runtime"
    if path_str in SHARED_INFRA_PATHS:
        return "shared_infrastructure"
    if path_str in SECURITY_PATHS:
        return "security"
    if path_str in ROOT_SHIMS:
        return "compatibility_only"
    if path_str in LEGACY_RUNTIME_PATHS or path_str in {"operator/codex_client.py", "operator/vlm_coordinator.py"}:
        return "legacy_runtime"
    if kind == "test":
        mapping = {
            "operator/cre/test_trace_writer.py": "core_regression",
            "operator/cre/test_diagnostic_reader.py": "core_regression",
            "operator/cre/test_healing_orchestrator.py": "core_regression",
            "operator/cre/test_skill_library.py": "core_regression",
            "operator/cre/test_action_trust.py": "core_regression",
            "operator/cre/test_host_tool_health.py": "governance_regression",
            "operator/cre/test_architecture_conformance.py": "governance_regression",
            "operator/cre/test_preclick_confirmation.py": "governance_regression",
            "operator/cre/test_window_capture.py": "integration_current",
            "operator/cre/test_screenshot_preprocessor.py": "integration_current",
            "operator/cre/test_runtime_tool_integration.py": "integration_current",
            "operator/cre/test_research_guided_planning.py": "integration_current",
            "operator/cre/test_phase2_method_brief.py": "integration_current",
            "operator/cre/test_phase3_equation_solver.py": "integration_current",
            "operator/cre/test_phase4_visual_monitoring.py": "integration_current",
            "operator/test_router_dryrun.py": "governance_regression",
            "operator/cre/test_drag_drop.py": "legacy_compatibility",
            "operator/cre/test_smooth_movement.py": "legacy_compatibility",
            "operator/cre/test_excalidraw_autonomous.py": "legacy_compatibility",
            "operator/cre/test_excalidraw_covt.py": "legacy_compatibility",
            "operator/cre/test_canva_ai_image.py": "integration_experimental",
            "operator/cre/test_canva_draw.py": "integration_experimental",
            "operator/cre/test_kleki_bmw.py": "integration_experimental",
            "operator/cre/test_kreska_statue.py": "integration_experimental",
        }
        return mapping.get(path_str, "integration_current")
    if kind == "doc":
        return "documentation"
    if kind == "generated":
        return "generated_support"
    if kind == "artifact":
        return "artifact_or_demo"
    if kind == "script":
        if path_str.startswith("operator/cre/project_understanding/tools/"):
            return "governance_tooling"
        if path_str.startswith("operator/cre/tools/"):
            return "audit_tooling"
        return "operational_script"
    if kind == "fixture":
        return "fixture"
    return "support_path"


def declared_purpose(path_str: str, text_cache: dict[str, str]) -> str:
    if path_str == "AGENTS.md":
        return "Repository-level operating instructions and architecture overview."
    if path_str in CORE_RUNTIME_PATHS:
        stem = Path(path_str).stem.replace("_", " ")
        return f"Current runtime module for {stem}."
    if path_str in SHARED_INFRA_PATHS:
        stem = Path(path_str).stem.replace("_", " ")
        return f"Shared infrastructure module for {stem}."
    if path_str in SECURITY_PATHS:
        stem = Path(path_str).stem.replace("_", " ")
        return f"Security module for {stem}."
    if path_str in ROOT_SHIMS:
        return "Compatibility shim forwarding to operator/agent_infra."
    if path_str in LEGACY_RUNTIME_PATHS:
        return "Legacy runtime or operational surface retained for compatibility/history."
    if path_str.startswith("operator/cre/project_understanding/"):
        return "Project-understanding corpus, generated artifacts, or audit tooling."
    if path_str.startswith("operator/cre/artifacts/"):
        return "Generated audit or experiment artifact."
    if path_str.startswith("operator/cre/transcripts/"):
        return "Transcript or handoff artifact."
    if path_str.startswith("operator/cre/reddit_research_demo/"):
        return "Reddit demonstration artifact family."
    if path_str.startswith("operator/cre/fixtures/"):
        return "Local fixture for tests or demos."
    if path_str.startswith("operator/cre/test_") or path_str == "operator/test_router_dryrun.py":
        return "Regression/integration test."
    if path_str.endswith(".md") or path_str.endswith(".mdc"):
        first = text_cache.get(path_str, "").splitlines()[:3]
        text = " ".join(line.strip("# ").strip() for line in first if line.strip())
        return text or "Documentation or research memo."
    if path_str.endswith(".png"):
        return "Screenshot, evidence image, or generated visual artifact."
    if path_str.endswith(".json") or path_str.endswith(".csv") or path_str.endswith(".mmd"):
        return "Structured artifact or generated data export."
    if path_str.endswith(".sh") or path_str.endswith(".lua"):
        return "Operational or legacy helper script."
    return "Project file."


def active_entrypoints(path_str: str, importers: list[str]) -> list[str]:
    entrypoints: list[str] = []
    if path_str == "operator/agent.py":
        entrypoints.append("universal_agent_path")
    if path_str == "operator/agent_core.py":
        entrypoints.append("native_execution_core")
    if path_str.startswith("operator/cre/test_"):
        entrypoints.append("pytest")
    if path_str in LEGACY_RUNTIME_PATHS:
        entrypoints.append("legacy_operational_surface")
    if importers:
        entrypoints.extend(sorted(set(importers[:5])))
    return sorted(set(entrypoints))


def topic_for_doc(path_str: str) -> str:
    lower = Path(path_str).stem.lower()
    normalized = re.sub(r"[^a-z0-9_]+", "_", lower)
    for topic, keywords in TOPIC_BUCKETS.items():
        if any(keyword in normalized for keyword in keywords):
            return topic
    if "project_understanding" in path_str:
        return "project_understanding"
    return "misc"


def doc_authority(path_str: str, status: str) -> str:
    if path_str in HIGH_AUTHORITY_DOCS:
        return "high"
    if path_str.startswith("operator/cre/project_understanding/README.md"):
        return "high"
    if status == "current":
        return "medium"
    if status == "historical_reference":
        return "low"
    return "supporting"


def current_accuracy_for_doc(path_str: str, status: str) -> str:
    if path_str in HIGH_AUTHORITY_DOCS or path_str.startswith("operator/cre/project_understanding/"):
        return "current_or_generated_current"
    if status == "experimental":
        return "supporting_current"
    if status == "historical_reference":
        return "historical_or_superseded"
    if status == "stale_candidate":
        return "likely_stale"
    return "unknown"


def duplicate_docs(path_str: str, doc_paths: list[str]) -> list[str]:
    topic = topic_for_doc(path_str)
    candidates = [p for p in doc_paths if p != path_str and topic_for_doc(p) == topic]
    return sorted(candidates[:8])


def dead_weight_signals(records: list[TruthInventoryRecord], doc_records: list[DocTruthRecord], cache_artifacts: list[str]) -> list[DeadWeightSignalRecord]:
    signals: list[DeadWeightSignalRecord] = []

    if cache_artifacts:
        signals.append(
            DeadWeightSignalRecord(
                path_or_family="checked-in __pycache__ artifacts",
                signal_type="cache_artifacts",
                evidence=cache_artifacts[:20],
                confidence="high",
                why_not_core="Bytecode caches are not source of truth.",
                why_not_legacy="They are generated caches, not deliberate legacy surfaces.",
                why_not_generated="They are generated, but not current evidence anchors.",
                review_recommendation="Remove from repo in a later cleanup branch; keep out of future audits by default.",
            )
        )

    stale_docs = [r for r in doc_records if r.recommended_status == "stale_candidate"]
    if stale_docs:
        signals.append(
            DeadWeightSignalRecord(
                path_or_family="top-level report/summary memo sprawl",
                signal_type="duplicate_documentation",
                evidence=[r.path for r in stale_docs[:12]],
                confidence="medium",
                why_not_core="These files are not primary runtime or governance surfaces.",
                why_not_legacy="They are not required compatibility layers.",
                why_not_generated="They are hand-written but weakly authoritative.",
                review_recommendation="Consolidate into canonical docs or downgrade to historical/supporting in a later branch.",
            )
        )

    orphan_artifacts = [
        r
        for r in records
        if r.kind in {"artifact", "generated"} and r.status in {"stale_candidate", "experimental"} and not r.docs_describing_it and not r.tests_covering_it
    ]
    if orphan_artifacts:
        signals.append(
            DeadWeightSignalRecord(
                path_or_family="orphaned screenshots/demo artifacts",
                signal_type="weak_artifact_linkage",
                evidence=[r.path for r in orphan_artifacts[:20]],
                confidence="medium",
                why_not_core="These artifacts are not part of the hot path.",
                why_not_legacy="They are not established legacy compatibility surfaces.",
                why_not_generated="Many are manually retained evidence artifacts, but weakly linked.",
                review_recommendation="Review artifact families and retain only those linked from canonical docs or active tests.",
            )
        )

    weak_scripts = [
        r
        for r in records
        if r.kind in {"script", "runtime_code"} and r.status in {"experimental", "legacy"} and not r.tests_covering_it and len(r.docs_describing_it) <= 1
    ]
    if weak_scripts:
        signals.append(
            DeadWeightSignalRecord(
                path_or_family="one-off operational/demo scripts",
                signal_type="weak_script_linkage",
                evidence=[r.path for r in weak_scripts[:20]],
                confidence="medium",
                why_not_core="They are not on the universal-agent hot path.",
                why_not_legacy="Some are not required for compatibility.",
                why_not_generated="They are hand-written scripts, but lightly justified.",
                review_recommendation="Separate true lineage/legacy scripts from one-off demos before any cleanup.",
            )
        )

    weak_shims = [r for r in records if r.path in ROOT_SHIMS and not r.active_entrypoints and not r.tests_covering_it]
    if weak_shims:
        signals.append(
            DeadWeightSignalRecord(
                path_or_family="root compatibility shims with no live callers",
                signal_type="compatibility_surface_decay",
                evidence=[r.path for r in weak_shims],
                confidence="low",
                why_not_core="They are compatibility-only by design.",
                why_not_legacy="They may no longer justify legacy retention if no callers remain.",
                why_not_generated="They are source files, not generated artifacts.",
                review_recommendation="Confirm whether callers remain after the truth audit; only then consider cleanup.",
            )
        )
    return signals


def build_records() -> tuple[list[TruthInventoryRecord], list[DocTruthRecord], dict[str, object]]:
    files = iter_files()
    cache_artifacts = iter_cache_artifacts()
    text_cache = load_text_cache(files)
    importers_for_path, imports_from_path = build_import_maps(files)
    records: list[TruthInventoryRecord] = []
    for path in files:
        path_str = rel(path)
        kind = classify_kind(path_str)
        docs = find_doc_mentions(path_str, text_cache)
        tests = find_test_mentions(path_str, importers_for_path, text_cache)
        importers = importers_for_path.get(path_str, [])
        status, status_note = classify_status(path_str, kind, importers, tests, docs)
        role = classify_role(path_str, kind)
        evidence = []
        if importers:
            evidence.append(f"imported_by:{len(importers)}")
        if tests:
            evidence.append(f"tests:{len(tests)}")
        if docs:
            evidence.append(f"docs:{len(docs)}")
        if path_str in HIGH_AUTHORITY_DOCS:
            evidence.append("high_authority_doc")
        if path_str in CORE_RUNTIME_PATHS or path_str in SHARED_INFRA_PATHS:
            evidence.append("declared_runtime_surface")
        if path_str in LEGACY_RUNTIME_PATHS:
            evidence.append("declared_legacy_surface")
        if path_str.startswith(GENERATED_PREFIXES):
            evidence.append("generated_artifact_path")
        notes = status_note
        record = TruthInventoryRecord(
            path=path_str,
            kind=kind,
            status=status,
            system_role=role,
            declared_purpose=declared_purpose(path_str, text_cache),
            observed_evidence=evidence,
            active_entrypoints=active_entrypoints(path_str, importers),
            tests_covering_it=tests,
            docs_describing_it=docs,
            dead_weight_signal=status_note if status == "stale_candidate" else "",
            notes=notes,
        )
        records.append(record)

    doc_paths = [r.path for r in records if r.kind == "doc"]
    doc_records: list[DocTruthRecord] = []
    for record in records:
        if record.kind != "doc":
            continue
        doc_records.append(
            DocTruthRecord(
                path=record.path,
                authority_level=doc_authority(record.path, record.status),
                topic=topic_for_doc(record.path),
                current_accuracy=current_accuracy_for_doc(record.path, record.status),
                duplicates=duplicate_docs(record.path, doc_paths),
                generated_or_manual="manual" if not record.path.startswith("operator/cre/project_understanding/artifacts/") else "generated",
                recommended_status=record.status,
                notes=record.notes or record.declared_purpose,
            )
        )

    baseline = collect_baseline()
    baseline["cache_artifact_count"] = len(cache_artifacts)
    baseline["cache_artifact_examples"] = cache_artifacts[:20]
    return records, doc_records, baseline, cache_artifacts


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_reports(records: list[TruthInventoryRecord], doc_records: list[DocTruthRecord], signals: list[DeadWeightSignalRecord], baseline: dict[str, object]) -> tuple[str, str, str]:
    status_counts = Counter(r.status for r in records)
    kind_counts = Counter(r.kind for r in records)
    role_counts = Counter(r.system_role for r in records)

    current_runtime = [
        r
        for r in records
        if r.path in CORE_RUNTIME_PATHS or r.path in SHARED_INFRA_PATHS or r.path in SECURITY_PATHS
    ]
    legacy = [r for r in records if r.status == "legacy"]
    stale = [r for r in records if r.status == "stale_candidate"]
    high_docs = [d for d in doc_records if d.authority_level == "high"]

    architecture_md = f"""# Current Architecture Surface (PhD)

## Scope
- Live repo: `{ROOT}`
- Excludes: `operator/venv/`, `operator/cre/runs/`

## Baseline Truth
- Python code surface excluding `venv` and `runs`: `{baseline['python_file_count_excluding_venv_and_runs']}`
- Test baseline:
  - return code: `{baseline['test_baseline']['returncode']}`
  - summary: `{baseline['test_baseline']['stdout'].splitlines()[-1] if baseline['test_baseline']['stdout'] else ''}`
- Architecture conformance:
  - return code: `{baseline['architecture_conformance_baseline']['returncode']}`
- Host-tool health:
  - return code: `{baseline['host_tool_health_baseline']['returncode']}`

## Current Runtime Surface
The live current runtime is centered on:
- universal-agent path in `operator/agent.py`
- native execution in `operator/agent_core.py`
- typed action surface in `operator/action_space.py`
- shared infrastructure in `operator/agent_infra/`
- security in `operator/security/`
- perception/grounding in:
  - `operator/window_capture.py`
  - `operator/visual_engine.py`
  - `operator/a11y_engine.py`
  - `operator/element_map.py`
  - `operator/web_primitives.py`

## Counts
- `current`: `{status_counts['current']}`
- `optional`: `{status_counts['optional']}`
- `legacy`: `{status_counts['legacy']}`
- `experimental`: `{status_counts['experimental']}`
- `generated`: `{status_counts['generated']}`
- `historical_reference`: `{status_counts['historical_reference']}`
- `stale_candidate`: `{status_counts['stale_candidate']}`

## Major role counts
""" + "\n".join(f"- `{role}`: `{count}`" for role, count in role_counts.most_common()) + "\n\n## Live current runtime modules\n" + "\n".join(
        f"- `{r.path}` — {r.declared_purpose}" for r in current_runtime[:40]
    )

    dead_weight_md = """# Dead Weight Signals (PhD)\n\n## Method\nThese are signals, not delete instructions. A surface appears here only when live repo evidence suggests weak current justification.\n\n"""
    for signal in signals:
        dead_weight_md += f"## {signal.path_or_family}\n"
        dead_weight_md += f"- signal type: `{signal.signal_type}`\n"
        dead_weight_md += f"- confidence: `{signal.confidence}`\n"
        dead_weight_md += f"- evidence:\n"
        for item in signal.evidence:
            dead_weight_md += f"  - `{item}`\n"
        dead_weight_md += f"- why not core: {signal.why_not_core}\n"
        dead_weight_md += f"- why not legacy: {signal.why_not_legacy}\n"
        dead_weight_md += f"- why not generated: {signal.why_not_generated}\n"
        dead_weight_md += f"- review recommendation: {signal.review_recommendation}\n\n"

    whole_audit_md = f"""# Whole Project Truth Audit (PhD)

## Environment basis
- repo root: `{ROOT}`
- filesystem-based truth audit: no git checkout at this path
- scope excludes `operator/venv/` and `operator/cre/runs/`

## Executive summary
This audit classifies the live repo into current, optional, legacy, experimental, generated, historical-reference, and stale-candidate surfaces using live code, test, and documentation evidence.

## Baseline
- full test baseline: `{baseline['test_baseline']['stdout'].splitlines()[-1] if baseline['test_baseline']['stdout'] else ''}`
- architecture conformance baseline captured from `--check`
- host-tool health baseline captured from `agent_infra.host_tool_health`

## Inventory counts
""" + "\n".join(f"- `{kind}`: `{count}`" for kind, count in kind_counts.most_common()) + "\n\n## Status counts\n" + "\n".join(
        f"- `{status}`: `{count}`" for status, count in status_counts.most_common()
    ) + f"""

## Low-value generated noise outside the inventory
- checked-in cache artifacts: `{baseline.get('cache_artifact_count', 0)}`

## High-authority docs
""" + "\n".join(f"- `{doc.path}` — topic `{doc.topic}`" for doc in high_docs) + f"""

## Current core findings
- The universal-agent path and `agent_infra` shared infrastructure are the canonical current runtime.
- Root-level shim modules remain compatibility surfaces, not canonical implementations.
- `operator/codex_client.py`, `operator/vlm_coordinator.py`, and kernel-era scripts remain legacy, not current hot path.
- `operator/cre/project_understanding/` is current and generated-supporting, not dead weight by default.
- The largest dead-weight risk surface is memo/demo/artifact density under `operator/cre/`, especially screenshots, one-off reports, checked-in caches, and weakly linked demo scripts.

## Stale-candidate highlights
""" + "\n".join(f"- `{r.path}` — {r.dead_weight_signal or r.notes}" for r in stale[:40]) + """

## Legacy surfaces still justified
""" + "\n".join(f"- `{r.path}` — {r.notes or r.declared_purpose}" for r in legacy[:20]) + """

## Next cleanup branch should use
- `whole_project_truth_inventory.json`
- `module_truth_matrix.csv`
- `doc_truth_matrix.csv`
- `dead_weight_signals.json`
as the decision base before any deletion or archival.
"""
    return whole_audit_md, dead_weight_md, architecture_md


def main() -> None:
    records, doc_records, baseline, cache_artifacts = build_records()
    signals = dead_weight_signals(records, doc_records, cache_artifacts)

    inventory_payload = {
        "baseline": baseline,
        "records": [asdict(record) for record in records],
    }
    write_json(ARTIFACTS_DIR / "whole_project_truth_inventory.json", inventory_payload)
    write_csv(
        ARTIFACTS_DIR / "module_truth_matrix.csv",
        [asdict(r) for r in records if r.kind in {"runtime_code", "legacy_runtime", "script", "fixture", "test"}],
        [
            "path",
            "kind",
            "status",
            "system_role",
            "declared_purpose",
            "observed_evidence",
            "active_entrypoints",
            "tests_covering_it",
            "docs_describing_it",
            "dead_weight_signal",
            "notes",
        ],
    )
    write_csv(
        ARTIFACTS_DIR / "doc_truth_matrix.csv",
        [asdict(r) for r in doc_records],
        [
            "path",
            "authority_level",
            "topic",
            "current_accuracy",
            "duplicates",
            "generated_or_manual",
            "recommended_status",
            "notes",
        ],
    )
    write_json(ARTIFACTS_DIR / "dead_weight_signals.json", [asdict(s) for s in signals])
    source_payload = [
        {**source, "retrieved_date": "2026-03-03"}
        for source in RESEARCH_SOURCES
    ]
    write_json(ARTIFACTS_DIR / "research_source_register.json", source_payload)

    whole_audit_md, dead_weight_md, architecture_md = build_reports(records, doc_records, signals, baseline)
    (CRE_DIR / "WHOLE_PROJECT_TRUTH_AUDIT_PHD.md").write_text(whole_audit_md + "\n", encoding="utf-8")
    (CRE_DIR / "DEAD_WEIGHT_SIGNALS_PHD.md").write_text(dead_weight_md + "\n", encoding="utf-8")
    (CRE_DIR / "CURRENT_ARCHITECTURE_SURFACE_PHD.md").write_text(architecture_md + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
