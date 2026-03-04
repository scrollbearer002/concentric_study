#!/usr/bin/env python3
"""Build machine-readable understanding artifacts for the concentric_study repo.

The goal is repository comprehension, not runtime mutation. The script walks the
workspace, classifies every project-owned file, extracts a lightweight import
graph for Python modules, and emits CSV/JSON artifacts consumed by the PhD-level
understanding corpus.
"""
from __future__ import annotations

import ast
import csv
import json
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[4]
UNDERSTANDING_DIR = ROOT / "operator" / "cre" / "project_understanding"
ARTIFACTS_DIR = UNDERSTANDING_DIR / "artifacts"

SKIP_DIRS = {".git", "venv", "__pycache__", ".pytest_cache"}

HIGH_VALUE_PATHS = {
    "AGENTS.md",
    ".cursor/rules/concentric-study.mdc",
    "DUAL_AGENT_LOOP_PLAN.md",
    "operator/agent.py",
    "operator/agent_core.py",
    "operator/a11y_engine.py",
    "operator/visual_engine.py",
    "operator/element_map.py",
    "operator/web_primitives.py",
    "operator/inference_router.py",
    "operator/capability_router.py",
    "operator/action_space.py",
    "operator/agent_infra/__init__.py",
    "operator/agent_infra/action_allowlist.py",
    "operator/agent_infra/action_handlers.py",
    "operator/agent_infra/action_trust.py",
    "operator/agent_infra/benchmark_evaluator.py",
    "operator/agent_infra/decision_graph.py",
    "operator/agent_infra/diagnostic_reader.py",
    "operator/agent_infra/healing_orchestrator.py",
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
    "operator/security/credential_vault.py",
    "operator/security/sanitizer.py",
    "operator/cre/test_excalidraw_covt.py",
    "operator/cre/test_kleki_bmw.py",
    "operator/cre/PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md",
    "operator/cre/PHD_DECISION_PRACTICE.md",
    "operator/cre/ESSAY_PROJECT_OVERLAP_PHD.md",
    "operator/cre/DEEP_DIVE_ADDENDUM.md",
    "operator/cre/runs/LAST_20_RUNS_EXHAUSTIVE.md",
}

SHIM_MAP = {
    "operator/trace_writer.py": "operator/agent_infra/trace_writer.py",
    "operator/diagnostic_reader.py": "operator/agent_infra/diagnostic_reader.py",
    "operator/healing_orchestrator.py": "operator/agent_infra/healing_orchestrator.py",
    "operator/outer_loop.py": "operator/agent_infra/outer_loop.py",
    "operator/skill_library.py": "operator/agent_infra/skill_library.py",
}

FOLDER_MISSIONS = {
    ".": "Workspace root for governance docs, architectural memos, and the operator implementation tree.",
    ".cursor": "Editor automation context, including repository-wide operating rules.",
    ".cursor/rules": "Mandatory project-specific agent policies and PhD workflow rules.",
    "operator": "Primary Python implementation tree for runtime execution, perception, infrastructure, security, and experiments.",
    "operator/agent_infra": "Shared infrastructure package for tracing, diagnosis, self-healing, memory, verification, and benchmarking.",
    "operator/security": "Security-focused modules for sanitization, keychain integration, and HITL protections.",
    "operator/cre": "Experiment, evaluation, documentation, evidence, and test layer around the runtime.",
    "operator/cre/evidence": "Reserved evidence directory for curated screenshots or run exports.",
    "operator/cre/evidence_concentric_clean": "Evidence bundle for the concentric-triangles task family.",
    "operator/cre/project_understanding": "Generated project-comprehension corpus and its supporting artifacts.",
    "operator/cre/project_understanding/artifacts": "Machine-readable outputs derived from the understanding generator.",
    "operator/cre/project_understanding/tools": "Read-only tooling that builds the project-understanding artifact set.",
    "operator/cre/runs": "Persistent run-history store: manifests, traces, escalation docs, journals, rules, and per-run evidence.",
}

ARTIFACT_FLOWS = [
    {
        "artifact_path": "operator/cre/runs/<run_id>/trace.jsonl",
        "producer": "operator/agent_infra/trace_writer.py",
        "consumer": "operator/agent_infra/diagnostic_reader.py; operator/agent_infra/healing_orchestrator.py; operator/agent_infra/skill_library.py; operator/agent_infra/decision_graph.py; operator/agent_infra/benchmark_evaluator.py",
        "lifecycle_stage": "execution",
        "purpose": "Per-step structured execution trace for diagnosis, evaluation, and learning.",
        "persistence": "per-run persistent",
    },
    {
        "artifact_path": "operator/cre/runs/<run_id>/manifest.json",
        "producer": "operator/agent_infra/trace_writer.py",
        "consumer": "operator/agent_infra/diagnostic_reader.py; operator/agent_infra/healing_orchestrator.py; operator/agent_infra/outer_loop.py; operator/agent_infra/skill_library.py",
        "lifecycle_stage": "execution-finalize",
        "purpose": "Run outcome, timing, failure metadata, and manifest summary.",
        "persistence": "per-run persistent",
    },
    {
        "artifact_path": "operator/cre/runs/<run_id>/ESCALATION.md",
        "producer": "operator/agent_infra/outer_loop.py",
        "consumer": "human maintainer; code agent",
        "lifecycle_stage": "failure-escalation",
        "purpose": "Structured handoff when automated recovery is exhausted.",
        "persistence": "per-run persistent",
    },
    {
        "artifact_path": "operator/cre/runs/reflection_journal.jsonl",
        "producer": "operator/agent_infra/outer_loop.py::ReflectionJournal",
        "consumer": "operator/agent_infra/recovery.py; operator/agent_infra/outer_loop.py",
        "lifecycle_stage": "cross-run memory",
        "purpose": "Episodic lessons learned across runs.",
        "persistence": "global persistent",
    },
    {
        "artifact_path": "operator/cre/runs/rules.jsonl",
        "producer": "operator/agent_infra/outer_loop.py::RulesStore",
        "consumer": "operator/agent_infra/recovery.py; operator/agent_infra/outer_loop.py",
        "lifecycle_stage": "cross-run memory",
        "purpose": "Generalized rules distilled from past failures.",
        "persistence": "global persistent",
    },
    {
        "artifact_path": "operator/cre/skill_library.json",
        "producer": "operator/agent_infra/skill_library.py",
        "consumer": "operator/agent_infra/skill_library.py; operator/agent.py; operator/cre/test_excalidraw_covt.py",
        "lifecycle_stage": "learning",
        "purpose": "Persistent skill records, maturity state, and resolved coordinates.",
        "persistence": "global persistent",
    },
    {
        "artifact_path": "operator/cre/action_trust.json",
        "producer": "operator/agent_infra/action_trust.py",
        "consumer": "operator/agent_infra/action_trust.py; operator/agent_infra/recovery.py",
        "lifecycle_stage": "verification-control",
        "purpose": "Consecutive success counts that drive verification skipping.",
        "persistence": "global persistent",
    },
    {
        "artifact_path": "operator/cre/routing_state.json",
        "producer": "operator/inference_router.py",
        "consumer": "operator/inference_router.py; operator/agent_core.py; operator/agent.py",
        "lifecycle_stage": "model-routing",
        "purpose": "Persisted routing state for hybrid model selection.",
        "persistence": "global persistent",
    },
    {
        "artifact_path": "operator/cre/site_knowledge_*.json",
        "producer": "manual curation / maintainer updates",
        "consumer": "operator/agent_infra/site_knowledge.py; operator/agent.py",
        "lifecycle_stage": "planning-support",
        "purpose": "Site affordances, button maps, and interaction rules for supported domains.",
        "persistence": "global persistent",
    },
    {
        "artifact_path": "operator/cre/execution_log.txt",
        "producer": "operator/cre/test_excalidraw_covt.py; operator/agent.py",
        "consumer": "human maintainer",
        "lifecycle_stage": "debugging",
        "purpose": "Human-readable runtime log for low-level execution inspection.",
        "persistence": "workspace persistent",
    },
]

EXTERNAL_REFERENCES = [
    {
        "source_type": "external-standard",
        "title": "ISO/IEC/IEEE 42010",
        "link_or_path": "https://www.iso-architecture.org/ieee-1471/",
        "why_it_matters_here": "Primary architecture-description standard for views, viewpoints, stakeholders, concerns, and correspondences.",
        "used_in_sections": "README.md; BIBLIOGRAPHY.md; PHD_EXTERNAL_RESEARCH_VALIDATION.md",
    },
    {
        "source_type": "external-standard",
        "title": "ISO/IEC/IEEE 42010: Architecture Descriptions",
        "link_or_path": "https://www.iso-architecture.org/ieee-1471/ads/",
        "why_it_matters_here": "Explains the required contents of an architecture description and why multiple views are necessary.",
        "used_in_sections": "ARCHITECTURE_DIAGRAMS.md; BIBLIOGRAPHY.md; PHD_EXTERNAL_RESEARCH_VALIDATION.md",
    },
    {
        "source_type": "external-standard",
        "title": "ISO/IEC/IEEE 42010: Conceptual Model",
        "link_or_path": "https://www.iso-architecture.org/ieee-1471/cm/",
        "why_it_matters_here": "Defines the conceptual relationship between stakeholders, concerns, viewpoints, views, and models.",
        "used_in_sections": "BIBLIOGRAPHY.md; PHD_EXTERNAL_RESEARCH_VALIDATION.md",
    },
    {
        "source_type": "external-standard",
        "title": "ISO/IEC/IEEE 42010: Mappings Between Views",
        "link_or_path": "https://www.iso-architecture.org/ieee-1471/mv/",
        "why_it_matters_here": "Supports explicit correspondences across documentation, code, and evidence views in the traceability matrix.",
        "used_in_sections": "README.md; BIBLIOGRAPHY.md; SECTION_2_TRACEABILITY_MATRIX.md; PHD_EXTERNAL_RESEARCH_VALIDATION.md",
    },
    {
        "source_type": "external-paper",
        "title": "The Program Dependence Graph and Its Use in Optimization",
        "link_or_path": "https://dl.acm.org/doi/10.1145/24039.24041",
        "why_it_matters_here": "Foundational dependence-graph reasoning for trace-level causal analysis.",
        "used_in_sections": "RUNTIME_FLOWS.md; BIBLIOGRAPHY.md; PHD_EXTERNAL_RESEARCH_VALIDATION.md",
    },
    {
        "source_type": "external-paper",
        "title": "A Systematic Survey of Program Comprehension through Dynamic Analysis",
        "link_or_path": "https://ieeexplore.ieee.org/document/4634918",
        "why_it_matters_here": "Grounds the repo-comprehension method in static plus dynamic evidence, not only source reading.",
        "used_in_sections": "README.md; BIBLIOGRAPHY.md; PHD_EXTERNAL_RESEARCH_VALIDATION.md; SECTION_5_DYNAMIC_EXECUTION_ARCHITECTURE.md",
    },
    {
        "source_type": "external-paper",
        "title": "Requirements Tracing",
        "link_or_path": "https://cacm.acm.org/research/requirements-tracing/",
        "why_it_matters_here": "Provides the lifecycle-follow-through concept adapted from requirements tracing to architecture-claim tracing.",
        "used_in_sections": "BIBLIOGRAPHY.md; SECTION_2_TRACEABILITY_MATRIX.md; PHD_EXTERNAL_RESEARCH_VALIDATION.md",
    },
    {
        "source_type": "external-report",
        "title": "Views and Beyond: The SEI Approach for Architecture Documentation",
        "link_or_path": "https://www.sei.cmu.edu/library/views-and-beyond-the-sei-approach-for-architecture-documentation/",
        "why_it_matters_here": "Institutional guidance for documenting architecture as multiple views rather than a single flat narrative.",
        "used_in_sections": "README.md; BIBLIOGRAPHY.md; PHD_EXTERNAL_RESEARCH_VALIDATION.md",
    },
    {
        "source_type": "external-book",
        "title": "Documenting Software Architectures: Views and Beyond, Second Edition",
        "link_or_path": "https://www.sei.cmu.edu/library/documenting-software-architectures-views-and-beyond-second-edition/",
        "why_it_matters_here": "Canonical SEI guidance on architecture views, rationale capture, and documentation structure.",
        "used_in_sections": "BIBLIOGRAPHY.md; PHD_EXTERNAL_RESEARCH_VALIDATION.md",
    },
    {
        "source_type": "external-report",
        "title": "Architecture Reconstruction Guidelines, Third Edition",
        "link_or_path": "https://www.sei.cmu.edu/library/architecture-reconstruction-guidelines-third-edition/",
        "why_it_matters_here": "Authoritative guidance for recovering as-built architecture from implementation artifacts.",
        "used_in_sections": "ARCHITECTURE_DIAGRAMS.md; SUBSYSTEM_DEPENDENCY_REPORT.md; BIBLIOGRAPHY.md; PHD_EXTERNAL_RESEARCH_VALIDATION.md",
    },
    {
        "source_type": "external-report",
        "title": "View Extraction and View Fusion in Architectural Understanding",
        "link_or_path": "https://www.sei.cmu.edu/library/view-extraction-and-view-fusion-in-architectural-understanding/",
        "why_it_matters_here": "Supports multi-view reconstruction and fusion of architectural information recovered from code and artifacts.",
        "used_in_sections": "ARCHITECTURE_DIAGRAMS.md; BIBLIOGRAPHY.md; PHD_EXTERNAL_RESEARCH_VALIDATION.md",
    },
    {
        "source_type": "external-report",
        "title": "A Structured Approach for Reviewing Architecture Documentation",
        "link_or_path": "https://insights.sei.cmu.edu/library/a-structured-approach-for-reviewing-architecture-documentation/",
        "why_it_matters_here": "Supports stakeholder-centered review of architecture documentation quality.",
        "used_in_sections": "BIBLIOGRAPHY.md; PHD_EXTERNAL_RESEARCH_VALIDATION.md",
    },
    {
        "source_type": "external-report",
        "title": "Software Modeling: What to Model and Why",
        "link_or_path": "https://insights.sei.cmu.edu/library/software-modeling-what-to-model-and-why/",
        "why_it_matters_here": "Supports using models and correspondences to help readers move between concerns and levels of detail.",
        "used_in_sections": "BIBLIOGRAPHY.md; SECTION_2_TRACEABILITY_MATRIX.md; PHD_EXTERNAL_RESEARCH_VALIDATION.md",
    },
    {
        "source_type": "external-paper",
        "title": "SHML: Self-Healing Machine Learning",
        "link_or_path": "https://arxiv.org/abs/2411.00186",
        "why_it_matters_here": "Explains the monitor-diagnose-adapt-test loop implemented by the outer loop.",
        "used_in_sections": "RUNTIME_FLOWS.md; BIBLIOGRAPHY.md; PHD_EXTERNAL_RESEARCH_VALIDATION.md",
    },
    {
        "source_type": "external-paper",
        "title": "MindGuard",
        "link_or_path": "https://arxiv.org/abs/2508.20412",
        "why_it_matters_here": "Supports the Decision Dependence Graph analysis pattern used for failure attribution.",
        "used_in_sections": "RUNTIME_FLOWS.md; BIBLIOGRAPHY.md; PHD_EXTERNAL_RESEARCH_VALIDATION.md",
    },
    {
        "source_type": "external-paper",
        "title": "DependEval: Benchmarking LLMs for Repository Dependency Understanding",
        "link_or_path": "https://arxiv.org/abs/2503.06689",
        "why_it_matters_here": "Confirms repository dependency understanding is a distinct and difficult capability worth measuring explicitly.",
        "used_in_sections": "SUBSYSTEM_DEPENDENCY_REPORT.md; BIBLIOGRAPHY.md; PHD_EXTERNAL_RESEARCH_VALIDATION.md",
    },
    {
        "source_type": "external-paper",
        "title": "RepoFusion: Training Code Models to Understand Your Repository",
        "link_or_path": "https://arxiv.org/abs/2306.10998",
        "why_it_matters_here": "Shows repository context materially improves code understanding over file-local reasoning.",
        "used_in_sections": "BIBLIOGRAPHY.md; PHD_EXTERNAL_RESEARCH_VALIDATION.md",
    },
    {
        "source_type": "external-paper",
        "title": "Hierarchical Context Pruning",
        "link_or_path": "https://arxiv.org/abs/2406.18294",
        "why_it_matters_here": "Supports dependency-preserving pruning instead of naïvely concatenating an entire repository context.",
        "used_in_sections": "BIBLIOGRAPHY.md; PHD_EXTERNAL_RESEARCH_VALIDATION.md",
    },
    {
        "source_type": "external-paper",
        "title": "RepoScope",
        "link_or_path": "https://arxiv.org/abs/2507.14791",
        "why_it_matters_here": "Supports multi-view, structure-preserving repository context rather than flat retrieval.",
        "used_in_sections": "BIBLIOGRAPHY.md; PHD_EXTERNAL_RESEARCH_VALIDATION.md",
    },
    {
        "source_type": "external-paper",
        "title": "Code-Survey: An LLM-Driven Methodology for Analyzing Large-Scale Codebases",
        "link_or_path": "https://arxiv.org/abs/2410.01837",
        "why_it_matters_here": "Supports systematic survey-style analysis of large codebases rather than ad hoc reading.",
        "used_in_sections": "README.md; BIBLIOGRAPHY.md; PHD_EXTERNAL_RESEARCH_VALIDATION.md",
    },
    {
        "source_type": "external-paper",
        "title": "ArchAgent: Scalable Legacy Software Architecture Recovery with LLMs",
        "link_or_path": "https://arxiv.org/abs/2601.13007",
        "why_it_matters_here": "Supports multiview architecture recovery from large repositories using static analysis plus LLM synthesis.",
        "used_in_sections": "README.md; ARCHITECTURE_DIAGRAMS.md; BIBLIOGRAPHY.md; PHD_EXTERNAL_RESEARCH_VALIDATION.md",
    },
    {
        "source_type": "external-paper",
        "title": "Generating Software Architecture Description from Source Code using Reverse Engineering and Large Language Model",
        "link_or_path": "https://arxiv.org/abs/2511.05165",
        "why_it_matters_here": "Directly supports generating software architecture descriptions from source plus reverse engineering artifacts.",
        "used_in_sections": "ARCHITECTURE_DIAGRAMS.md; BIBLIOGRAPHY.md; PHD_EXTERNAL_RESEARCH_VALIDATION.md",
    },
    {
        "source_type": "external-paper",
        "title": "AppAgent: Multimodal Agents as Smartphone Users",
        "link_or_path": "https://arxiv.org/abs/2312.13771",
        "why_it_matters_here": "Supports the research-first study of task, tool affordances, and environment before execution.",
        "used_in_sections": "README.md; BIBLIOGRAPHY.md; PHD_EXTERNAL_RESEARCH_VALIDATION.md",
    },
    {
        "source_type": "external-paper",
        "title": "From Expert to Novice: An Empirical Study on Software Architecture Explanations",
        "link_or_path": "https://arxiv.org/abs/2503.08628",
        "why_it_matters_here": "Supports audience-sensitive walkthroughs and explanation strategies for onboarding.",
        "used_in_sections": "WALKTHROUGH_90_MINUTES.md; BIBLIOGRAPHY.md; PHD_EXTERNAL_RESEARCH_VALIDATION.md",
    },
    {
        "source_type": "external-paper",
        "title": "A Multi-agent Onboarding Assistant based on Large Language Models, Retrieval Augmented Generation, and Chain-of-Thought",
        "link_or_path": "https://arxiv.org/abs/2503.23421",
        "why_it_matters_here": "Supports retrieval-backed onboarding assistance for large evolving repositories.",
        "used_in_sections": "WALKTHROUGH_90_MINUTES.md; BIBLIOGRAPHY.md; PHD_EXTERNAL_RESEARCH_VALIDATION.md",
    },
    {
        "source_type": "external-paper",
        "title": "Software Architecture Meets LLMs: A Systematic Literature Review",
        "link_or_path": "https://arxiv.org/abs/2505.16697",
        "why_it_matters_here": "Provides a broader map of what LLM-based architecture methods can and cannot currently support.",
        "used_in_sections": "BIBLIOGRAPHY.md; PHD_EXTERNAL_RESEARCH_VALIDATION.md",
    },
    {
        "source_type": "external-paper",
        "title": "SourcererCC: Scaling Code Clone Detection to Big Code",
        "link_or_path": "https://arxiv.org/abs/1512.06448",
        "why_it_matters_here": "Supports near-miss clone reasoning and explains why structurally similar duplicate helpers are a maintenance risk.",
        "used_in_sections": "BIBLIOGRAPHY.md; SECTION_1_ENTRYPOINT_DUPLICATION_AUDIT.md",
    },
    {
        "source_type": "external-paper",
        "title": "Software Reflexion Models: Bridging the Gap Between Source and High-Level Models",
        "link_or_path": "https://www.cs.ubc.ca/~murphy/papers/rm/fse95.html",
        "why_it_matters_here": "Provides the classic source-vs-model conformance lens for later architecture-conformance checks.",
        "used_in_sections": "BIBLIOGRAPHY.md; PHD_EXTERNAL_RESEARCH_VALIDATION.md; SECTION_3_ARCHITECTURE_CONFORMANCE.md",
    },
    {
        "source_type": "external-report",
        "title": "Why Architecture Conformance Matters for Evolvable Systems",
        "link_or_path": "https://www.sei.cmu.edu/library/why-architecture-conformance-matters/",
        "why_it_matters_here": "Supports explicit architecture-conformance analysis as the next step after architecture recovery.",
        "used_in_sections": "BIBLIOGRAPHY.md; PHD_EXTERNAL_RESEARCH_VALIDATION.md; SECTION_3_ARCHITECTURE_CONFORMANCE.md",
    },
    {
        "source_type": "external-report",
        "title": "Discovering Architectures from Running Systems",
        "link_or_path": "https://www.sei.cmu.edu/library/discovering-architectures-from-running-systems/",
        "why_it_matters_here": "Supports recovering runtime interaction architecture from executing systems instead of relying only on static dependencies.",
        "used_in_sections": "BIBLIOGRAPHY.md; PHD_PATH_REVALIDATION.md; SECTION_5_DYNAMIC_EXECUTION_ARCHITECTURE.md",
    },
    {
        "source_type": "external-paper",
        "title": "Dynamic Design Analysis to Support Architecture Design",
        "link_or_path": "https://dl.acm.org/doi/10.1145/503271.503237",
        "why_it_matters_here": "Supports dynamic design and execution analysis as the next view after static recovery and conformance.",
        "used_in_sections": "BIBLIOGRAPHY.md; PHD_PATH_REVALIDATION.md; SECTION_5_DYNAMIC_EXECUTION_ARCHITECTURE.md",
    },
    {
        "source_type": "external-report",
        "title": "Discovering Architectures from Running Systems: Lessons Learned",
        "link_or_path": "https://insights.sei.cmu.edu/library/discovering-architectures-from-running-systems-lessons-learned/",
        "why_it_matters_here": "Explains how to separate dominant runtime patterns from outlier executions when reconstructing architecture from running systems.",
        "used_in_sections": "BIBLIOGRAPHY.md; SECTION_5_DYNAMIC_EXECUTION_ARCHITECTURE.md",
    },
    {
        "source_type": "external-report",
        "title": "Architecture Tradeoff Analysis Method Collection",
        "link_or_path": "https://www.sei.cmu.edu/library/architecture-tradeoff-analysis-method-collection/",
        "why_it_matters_here": "Supports scenario-based architecture evaluation before major refactors.",
        "used_in_sections": "BIBLIOGRAPHY.md; PHD_PATH_REVALIDATION.md",
    },
    {
        "source_type": "external-report",
        "title": "Quality Attribute Workshop Collection",
        "link_or_path": "https://www.sei.cmu.edu/library/quality-attribute-workshop-collection/",
        "why_it_matters_here": "Supports turning architectural concerns into concrete, evaluable scenarios.",
        "used_in_sections": "BIBLIOGRAPHY.md; PHD_PATH_REVALIDATION.md",
    },
    {
        "source_type": "external-report",
        "title": "A Playbook for Early Architecture Analysis",
        "link_or_path": "https://www.sei.cmu.edu/library/a-playbook-for-early-architecture-analysis/",
        "why_it_matters_here": "Supports disciplined early evaluation of architectural options before committing to code changes.",
        "used_in_sections": "BIBLIOGRAPHY.md; PHD_PATH_REVALIDATION.md",
    },
    {
        "source_type": "external-web",
        "title": "Documenting Architecture Decisions",
        "link_or_path": "https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions",
        "why_it_matters_here": "Primary ADR reference that matches the repo's facts-before-decisions rule.",
        "used_in_sections": "README.md; BIBLIOGRAPHY.md; PHD_EXTERNAL_RESEARCH_VALIDATION.md",
    },
    {
        "source_type": "external-web",
        "title": "Architecture Decision Records",
        "link_or_path": "https://adr.github.io/",
        "why_it_matters_here": "Canonical ADR practice reference for documenting evidence, decisions, and consequences.",
        "used_in_sections": "README.md; BIBLIOGRAPHY.md; PHD_EXTERNAL_RESEARCH_VALIDATION.md",
    },
    {
        "source_type": "external-paper",
        "title": "MCP-Atlas",
        "link_or_path": "https://arxiv.org/abs/2602.00933",
        "why_it_matters_here": "Supports claims-based evaluation of runs and artifacts.",
        "used_in_sections": "BIBLIOGRAPHY.md; PHD_EXTERNAL_RESEARCH_VALIDATION.md",
    },
]


@dataclass
class InventoryRecord:
    path: str
    artifact_class: str
    subsystem: str
    responsibility: str
    canonical_source: str
    produced_by: str
    consumed_by: str
    evidence_refs: list[str]
    deep_profile: bool
    notes: str
    size_bytes: int


@dataclass
class FolderRecord:
    path: str
    mission: str
    primary_contents: list[str]
    entrypoints: list[str]
    state_files: list[str]
    read_order: list[str]
    risks: list[str]


def should_skip(path: Path) -> bool:
    return any(part in SKIP_DIRS for part in path.parts)


def iter_project_files() -> Iterable[Path]:
    for path in sorted(ROOT.rglob("*"), key=lambda p: p.relative_to(ROOT).as_posix()):
        if not path.is_file():
            continue
        if should_skip(path):
            continue
        yield path


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def classify_markdown(path_str: str) -> str:
    name = Path(path_str).name.lower()
    if name in {"readme.md", "quick_start.md", "run_test.md", "setup.md", "setup_status.md", "api_key_setup.md"}:
        return "setup_doc"
    if path_str.startswith("operator/cre/project_understanding/"):
        return "research_doc"
    if path_str in {"AGENTS.md", "DUAL_AGENT_LOOP_PLAN.md"} or path_str.endswith(".mdc"):
        return "rule_or_policy"
    if any(token in name for token in ["plan", "outline", "spec", "roadmap", "design", "placement"]):
        return "design_doc"
    return "research_doc"


def classify_png(path_str: str) -> str:
    name = Path(path_str).name
    if name.startswith("som_") or name.startswith("_kleki") or name.startswith("_panel"):
        return "reference_image"
    if any(name.startswith(prefix) for prefix in ["diag_", "assert_", "effect_", "verify_", "_checkpoint", "_final_result", "current_state", "palette_", "color_", "dots_", "_welcome", "_readiness", "_post_run", "_bmw_center", "iteration_"]):
        return "evidence_image"
    return "reference_image"


def classify_file(path: Path) -> str:
    path_str = rel(path)
    name = path.name
    suffix = path.suffix.lower()

    if path_str in SHIM_MAP:
        return "compatibility_shim"
    if path_str.endswith(".mdc") or path_str == "AGENTS.md":
        return "rule_or_policy"
    if path_str.startswith(".cursor/"):
        return "rule_or_policy"
    if path_str.startswith("operator/agent_infra/") and suffix == ".py":
        return "library_module"
    if path_str.startswith("operator/security/") and suffix == ".py":
        return "security_module"
    if path_str.startswith("operator/cre/test_") and suffix == ".py":
        return "test"
    if name.startswith("test_") and suffix == ".py":
        return "test"
    if path_str.startswith("operator/cre/runs/"):
        if name in {"reflection_journal.jsonl", "rules.jsonl"}:
            return "state_store"
        return "run_artifact"
    if path_str.startswith("operator/cre/site_knowledge_") and suffix == ".json":
        return "site_knowledge"
    if name in {"skill_library.json", "action_trust.json", "routing_state.json"}:
        return "state_store"
    if suffix == ".py":
        return "entrypoint" if path_str in {"operator/agent.py", "operator/agent_core.py"} else "library_module"
    if suffix == ".md":
        return classify_markdown(path_str)
    if suffix == ".png":
        return classify_png(path_str)
    if suffix in {".json", ".jsonl"}:
        return "data_file"
    if suffix in {".sh", ".lua"}:
        return "script"
    if suffix in {".txt", ".log", ".html"}:
        return "data_file"
    return "data_file"


def subsystem_for(path_str: str) -> str:
    if path_str == "AGENTS.md" or path_str.startswith(".cursor/") or path_str.startswith("DUAL_AGENT_LOOP_PLAN"):
        return "repo-governance"
    if path_str.startswith("operator/agent_infra/"):
        return "shared-infrastructure"
    if path_str.startswith("operator/security/"):
        return "security"
    if path_str.startswith("operator/cre/project_understanding/"):
        return "project-understanding"
    if path_str.startswith("operator/cre/runs/"):
        return "runtime-evidence"
    if path_str.startswith("operator/cre/site_knowledge_"):
        return "site-knowledge"
    if path_str.startswith("operator/cre/"):
        return "experiments-and-docs"
    if path_str.startswith("operator/"):
        return "runtime-orchestrator"
    return "workspace-root"


def responsibility_for(path_str: str, artifact_class: str) -> str:
    name = Path(path_str).name
    if path_str in SHIM_MAP:
        return f"Backward-compatible import shim that redirects callers to `{SHIM_MAP[path_str]}`."
    if path_str == "operator/agent.py":
        return "Universal orchestrator that plans and executes tasks across supported sites using capability routing, tracing, and skill reuse."
    if path_str == "operator/agent_core.py":
        return "macOS execution core for focus, screenshots, Quartz input, and VLM-backed visual assertions."
    if path_str == "operator/cre/test_excalidraw_covt.py":
        return "Main traced Excalidraw harness that assembles context, plans actions, executes recovery-aware steps, and finalizes run artifacts."
    if path_str == "operator/agent_infra/outer_loop.py":
        return "Dual-agent orchestration loop that runs tasks, classifies failures, records lessons, and escalates unresolved runs."
    if path_str == "operator/agent_infra/recovery.py":
        return "Recovery pipeline for diagnosis, dismissal strategies, postcondition verification, and trust-aware action execution."
    if path_str == "operator/agent_infra/action_handlers.py":
        return "Concrete action implementations for navigation, drawing, color control, verification, and site-specific task phases."
    if path_str == "operator/agent_infra/action_allowlist.py":
        return "Deterministic pre-action safety layer that blocks disallowed actions or out-of-bounds parameters before execution."
    if path_str == "operator/agent_infra/trace_writer.py":
        return "Canonical trace writer for run directories, per-step JSONL events, and final manifests."
    if path_str == "operator/agent_infra/diagnostic_reader.py":
        return "Progressive-disclosure reader for manifests and traces."
    if path_str == "operator/agent_infra/healing_orchestrator.py":
        return "Failure classifier that turns run evidence into retry, adjust, escalate, or abort decisions."
    if path_str == "operator/agent_infra/skill_library.py":
        return "Persistent skill store with maturity gating, semantic retrieval, and coordinate reuse support."
    if path_str == "operator/security/sanitizer.py":
        return "Prompt-injection and MCP-poisoning defenses for inputs, tool descriptions, and tool responses."
    if path_str == "operator/security/credential_vault.py":
        return "Keychain-backed credential and HITL guard layer for sensitive workflows."
    if path_str.startswith("operator/cre/runs/") and name == "trace.jsonl":
        return "Per-run structured execution trace consumed by diagnosis, learning, and evaluation tooling."
    if path_str.startswith("operator/cre/runs/") and name == "manifest.json":
        return "Per-run manifest describing outcome, timing, task metadata, and summary statistics."
    if path_str.startswith("operator/cre/runs/") and name == "ESCALATION.md":
        return "Structured escalation brief for unresolved failures handed to a human or code agent."
    if path_str == "operator/cre/runs/reflection_journal.jsonl":
        return "Cross-run episodic memory log of lessons learned by the outer loop."
    if path_str == "operator/cre/runs/rules.jsonl":
        return "Cross-run generalized rule store extracted from recurrent failures."
    if path_str.startswith("operator/cre/site_knowledge_"):
        return "Curated site affordance and interaction-knowledge base used during planning and execution."
    if artifact_class == "test":
        return "Automated test or harness that validates a subsystem or executes a benchmark task."
    if artifact_class == "research_doc":
        return "Research-oriented documentation capturing architecture, validation, execution analysis, or experiment findings."
    if artifact_class == "design_doc":
        return "Design or planning memo that justifies an architectural or implementation direction."
    if artifact_class == "setup_doc":
        return "Setup or usage documentation for running the project locally."
    if artifact_class == "rule_or_policy":
        return "Governance or policy document that defines how humans and agents should work in this repo."
    if artifact_class == "run_artifact":
        return "Persisted artifact produced by a specific run, experiment, or failure-analysis workflow."
    if artifact_class == "evidence_image":
        return "Screenshot-style evidence captured during verification, diagnosis, or iterative drawing experiments."
    if artifact_class == "reference_image":
        return "Reference or helper image used by grounding, affordance mapping, or documentation."
    if artifact_class == "state_store":
        return "Persistent state file that influences behavior across runs."
    if artifact_class == "script":
        return "Helper script used to run, verify, or generate project workflows."
    if artifact_class == "data_file":
        return "Supporting data or log artifact used for analysis, evidence, or runtime configuration."
    if artifact_class == "security_module":
        return "Security-specific runtime module."
    if artifact_class == "library_module":
        return "Reusable Python module that contributes to the runtime or analysis stack."
    if artifact_class == "entrypoint":
        return "Top-level executable or orchestrator entrypoint."
    return "Project-owned file in the repository snapshot."


def produced_by_for(path_str: str, artifact_class: str) -> str:
    name = Path(path_str).name
    if path_str.startswith("operator/cre/runs/") and name == "trace.jsonl":
        return "operator/agent_infra/trace_writer.py"
    if path_str.startswith("operator/cre/runs/") and name == "manifest.json":
        return "operator/agent_infra/trace_writer.py"
    if path_str.startswith("operator/cre/runs/") and name == "ESCALATION.md":
        return "operator/agent_infra/outer_loop.py"
    if path_str == "operator/cre/runs/reflection_journal.jsonl":
        return "operator/agent_infra/outer_loop.py::ReflectionJournal"
    if path_str == "operator/cre/runs/rules.jsonl":
        return "operator/agent_infra/outer_loop.py::RulesStore"
    if path_str == "operator/cre/skill_library.json":
        return "operator/agent_infra/skill_library.py"
    if path_str == "operator/cre/action_trust.json":
        return "operator/agent_infra/action_trust.py"
    if path_str == "operator/cre/routing_state.json":
        return "operator/inference_router.py"
    if path_str.startswith("operator/cre/site_knowledge_"):
        return "manual curation"
    if artifact_class in {"research_doc", "design_doc", "setup_doc", "rule_or_policy"}:
        return "human maintainer"
    if artifact_class in {"run_artifact", "evidence_image"}:
        return "runtime harness or experiment"
    if artifact_class in {"entrypoint", "library_module", "security_module", "compatibility_shim", "script"}:
        return "human maintainer"
    return "unknown or mixed"


def consumed_by_for(path_str: str, artifact_class: str) -> str:
    name = Path(path_str).name
    if path_str.startswith("operator/cre/runs/") and name == "trace.jsonl":
        return "operator/agent_infra/diagnostic_reader.py; operator/agent_infra/healing_orchestrator.py; operator/agent_infra/skill_library.py; operator/agent_infra/decision_graph.py; operator/agent_infra/benchmark_evaluator.py"
    if path_str.startswith("operator/cre/runs/") and name == "manifest.json":
        return "operator/agent_infra/diagnostic_reader.py; operator/agent_infra/healing_orchestrator.py; operator/agent_infra/outer_loop.py; operator/agent_infra/skill_library.py"
    if path_str.startswith("operator/cre/runs/") and name == "ESCALATION.md":
        return "human maintainer; code agent"
    if path_str == "operator/cre/runs/reflection_journal.jsonl":
        return "operator/agent_infra/recovery.py; operator/agent_infra/outer_loop.py"
    if path_str == "operator/cre/runs/rules.jsonl":
        return "operator/agent_infra/recovery.py; operator/agent_infra/outer_loop.py"
    if path_str == "operator/cre/skill_library.json":
        return "operator/agent_infra/skill_library.py; operator/agent.py; operator/cre/test_excalidraw_covt.py"
    if path_str == "operator/cre/action_trust.json":
        return "operator/agent_infra/action_trust.py; operator/agent_infra/recovery.py"
    if path_str == "operator/cre/routing_state.json":
        return "operator/inference_router.py; operator/agent.py; operator/agent_core.py"
    if path_str.startswith("operator/cre/site_knowledge_"):
        return "operator/agent_infra/site_knowledge.py; operator/agent.py"
    if artifact_class in {"research_doc", "design_doc", "setup_doc", "rule_or_policy"}:
        return "human maintainer; collaborating agents"
    if artifact_class in {"run_artifact", "evidence_image", "reference_image", "data_file"}:
        return "human maintainer or analysis tooling"
    if artifact_class in {"entrypoint", "library_module", "security_module", "compatibility_shim", "script", "test"}:
        return "Python runtime or test harness"
    return "unknown or mixed"


def evidence_refs_for(path_str: str) -> list[str]:
    refs: list[str] = []
    if path_str.startswith("operator/agent_infra/"):
        refs.append("operator/cre/PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md")
    if path_str.startswith("operator/cre/runs/"):
        refs.append("operator/cre/runs/LAST_20_RUNS_EXHAUSTIVE.md")
    if path_str in {"operator/agent.py", "operator/action_space.py", "operator/capability_router.py"}:
        refs.append("operator/cre/DEEP_DIVE_ADDENDUM.md")
    if path_str.startswith("operator/security/"):
        refs.append("AGENTS.md")
    if path_str.endswith("action_allowlist.py"):
        refs.append("operator/cre/ALLOWLIST_PREACTION_IMPLEMENTATION_OUTLINE.md")
    return refs


def notes_for(path_str: str, artifact_class: str) -> str:
    if path_str in SHIM_MAP:
        return "Canonical implementation lives elsewhere; changes should normally target the mapped source file."
    if path_str.startswith("operator/cre/runs/") and Path(path_str).name == "manifest.json":
        return "Some run directories elsewhere in the tree are missing manifests; consumers must tolerate absent finalize artifacts."
    if path_str.startswith("operator/cre/runs/") and Path(path_str).name == "trace.jsonl":
        return "Read as append-only JSONL; traces are written live during execution."
    if path_str == "operator/cre/runs/rules.jsonl":
        return "May be absent until the outer loop has extracted at least one rule from failures."
    if artifact_class == "evidence_image":
        return "Use family-level explanations for repeated image sets; individual files still matter for provenance."
    if path_str.startswith("operator/cre/project_understanding/"):
        return "Generated or curated as part of the PhD-level repo-understanding corpus."
    return ""


def python_module_name(path_str: str) -> str | None:
    path = Path(path_str)
    if path.suffix != ".py":
        return None
    parts = path.parts
    if parts and parts[0] == "operator":
        parts = parts[1:]
    if not parts:
        return None
    if parts[-1] == "__init__.py":
        return ".".join(parts[:-1])
    return ".".join(parts[:-1] + (path.stem,))


def build_import_graph(py_paths: list[Path]) -> dict[str, object]:
    sorted_py_paths = sorted(py_paths, key=lambda path: rel(path))
    module_map = {}
    for path in sorted_py_paths:
        path_str = rel(path)
        module_name = python_module_name(path_str)
        if module_name:
            module_map[module_name] = path_str

    edges = []
    adjacency: dict[str, list[str]] = defaultdict(list)

    for path in sorted_py_paths:
        path_str = rel(path)
        source_module = python_module_name(path_str)
        if not source_module:
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue

        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    continue
                if node.module:
                    imports.add(node.module)

        for imported in sorted(imports):
            target_path = None
            if imported in module_map:
                target_path = module_map[imported]
            else:
                for candidate in sorted(module_map):
                    if candidate.startswith(imported + "."):
                        target_path = module_map[candidate]
                        break
            if not target_path:
                continue
            edge = {"from": path_str, "to": target_path, "import": imported}
            edges.append(edge)
            adjacency[path_str].append(target_path)

    return {
        "nodes": [{"path": path_str, "module": python_module_name(path_str)} for path_str in sorted(rel(p) for p in sorted_py_paths)],
        "edges": sorted(edges, key=lambda edge: (edge["from"], edge["to"], edge["import"])),
        "adjacency": {k: sorted(set(v)) for k, v in sorted(adjacency.items())},
    }


def subsystem_for_graph_path(path_str: str) -> str:
    if path_str.startswith("operator/agent_infra/"):
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


def build_subsystem_dependency_report(import_graph: dict[str, object], inventory: list[InventoryRecord]) -> dict[str, object]:
    nodes = import_graph["nodes"]
    edges = import_graph["edges"]
    subsystem_nodes: dict[str, set[str]] = defaultdict(set)
    indegree: Counter[str] = Counter()
    outdegree: Counter[str] = Counter()

    for node in nodes:
        subsystem = subsystem_for_graph_path(node["path"])
        subsystem_nodes[subsystem].add(node["path"])

    subsystem_edges: Counter[tuple[str, str]] = Counter()
    cross_subsystem_edges: list[dict[str, object]] = []
    for edge in edges:
        src_subsystem = subsystem_for_graph_path(edge["from"])
        dst_subsystem = subsystem_for_graph_path(edge["to"])
        subsystem_edges[(src_subsystem, dst_subsystem)] += 1
        outdegree[edge["from"]] += 1
        indegree[edge["to"]] += 1
        if src_subsystem != dst_subsystem:
            cross_subsystem_edges.append(
                {
                    "from": edge["from"],
                    "to": edge["to"],
                    "from_subsystem": src_subsystem,
                    "to_subsystem": dst_subsystem,
                    "import": edge["import"],
                }
            )

    high_value_set = {record.path for record in inventory if record.deep_profile}
    subsystem_summary = []
    for subsystem in sorted(subsystem_nodes):
        members = sorted(subsystem_nodes[subsystem])
        subsystem_summary.append(
            {
                "subsystem": subsystem,
                "node_count": len(members),
                "high_value_nodes": [member for member in members if member in high_value_set][:12],
                "sample_nodes": members[:12],
            }
        )

    top_importers = []
    for path_str, degree in outdegree.most_common(15):
        top_importers.append(
            {
                "path": path_str,
                "out_degree": degree,
                "subsystem": subsystem_for_graph_path(path_str),
            }
        )

    top_shared_dependencies = []
    for path_str, degree in indegree.most_common(15):
        top_shared_dependencies.append(
            {
                "path": path_str,
                "in_degree": degree,
                "subsystem": subsystem_for_graph_path(path_str),
            }
        )

    mermaid_lines = ["flowchart LR"]
    subsystem_labels = {
        "runtime_orchestrator": "Runtime Orchestrator",
        "shared_infrastructure": "Shared Infrastructure",
        "security": "Security",
        "experiment_harnesses": "Experiment Harnesses",
        "cre_docs_and_artifacts": "CRE Docs/Artifacts",
        "repo_governance": "Repo Governance",
        "workspace_root": "Workspace Root",
    }
    for subsystem in sorted(subsystem_nodes):
        mermaid_lines.append(f'    {subsystem}["{subsystem_labels.get(subsystem, subsystem)}"]')
    for (src, dst), weight in sorted(subsystem_edges.items()):
        if weight:
            mermaid_lines.append(f"    {src} -->|{weight}| {dst}")

    return {
        "subsystem_summary": subsystem_summary,
        "subsystem_edges": [
            {"from_subsystem": src, "to_subsystem": dst, "edge_count": weight}
            for (src, dst), weight in sorted(subsystem_edges.items())
        ],
        "cross_subsystem_edges": cross_subsystem_edges,
        "top_importers": top_importers,
        "top_shared_dependencies": top_shared_dependencies,
        "mermaid": "\n".join(mermaid_lines) + "\n",
    }


def build_folder_records(files: list[Path]) -> list[FolderRecord]:
    grouped: dict[str, list[str]] = defaultdict(list)
    for path in files:
        path_str = rel(path)
        parent = Path(path_str).parent.as_posix()
        grouped[parent].append(path_str)

    records = []
    for folder_path, mission in sorted(FOLDER_MISSIONS.items()):
        members = sorted(grouped.get(folder_path, []))
        entrypoints = [m for m in members if m.endswith("agent.py") or m.endswith("test_excalidraw_covt.py") or m.endswith("outer_loop.py")]
        state_files = [m for m in members if Path(m).name in {"skill_library.json", "action_trust.json", "routing_state.json", "reflection_journal.jsonl", "rules.jsonl"}]
        read_order = members[:5]
        risks = []
        if folder_path == "operator/agent_infra":
            risks.append("Architecture-critical package with a mostly unidirectional dependency chain.")
        if folder_path == "operator/cre":
            risks.append("Mixed concerns: runtime evidence, docs, images, state, and tests coexist in one flat surface.")
        if folder_path == "operator/cre/runs":
            risks.append("Consumers must handle incomplete run directories and missing manifests during live or crashed runs.")
        records.append(
            FolderRecord(
                path=folder_path,
                mission=mission,
                primary_contents=members[:12],
                entrypoints=entrypoints,
                state_files=state_files,
                read_order=read_order,
                risks=risks,
            )
        )
    return records


def build_inventory(files: list[Path]) -> list[InventoryRecord]:
    records = []
    for path in sorted(files):
        path_str = rel(path)
        artifact_class = classify_file(path)
        records.append(
            InventoryRecord(
                path=path_str,
                artifact_class=artifact_class,
                subsystem=subsystem_for(path_str),
                responsibility=responsibility_for(path_str, artifact_class),
                canonical_source=SHIM_MAP.get(path_str, path_str),
                produced_by=produced_by_for(path_str, artifact_class),
                consumed_by=consumed_by_for(path_str, artifact_class),
                evidence_refs=evidence_refs_for(path_str),
                deep_profile=path_str in HIGH_VALUE_PATHS,
                notes=notes_for(path_str, artifact_class),
                size_bytes=path.stat().st_size,
            )
        )
    return records


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_outputs() -> dict[str, object]:
    files = list(iter_project_files())
    inventory = build_inventory(files)
    py_paths = [p for p in files if p.suffix == ".py"]
    import_graph = build_import_graph(py_paths)
    subsystem_dependency_report = build_subsystem_dependency_report(import_graph, inventory)
    folder_records = build_folder_records(files)

    inventory_json = [asdict(record) for record in inventory]
    inventory_rows = []
    for record in inventory:
        row = asdict(record)
        row["evidence_refs"] = "; ".join(record.evidence_refs)
        inventory_rows.append(row)

    summary = {
        "root": str(ROOT),
        "total_files": len(files),
        "artifact_class_counts": dict(sorted(Counter(r.artifact_class for r in inventory).items())),
        "subsystem_counts": dict(sorted(Counter(r.subsystem for r in inventory).items())),
        "extension_counts": dict(sorted(Counter((Path(r.path).suffix or "[noext]") for r in inventory).items())),
        "high_value_files": sorted(r.path for r in inventory if r.deep_profile),
        "folder_records": len(folder_records),
        "artifact_flows": len(ARTIFACT_FLOWS),
    }

    write_json(ARTIFACTS_DIR / "repo_inventory.json", inventory_json)
    write_csv(ARTIFACTS_DIR / "file_catalog.csv", inventory_rows)
    write_json(ARTIFACTS_DIR / "import_graph.json", import_graph)
    write_json(ARTIFACTS_DIR / "subsystem_dependency_report.json", subsystem_dependency_report)
    (ARTIFACTS_DIR / "architecture_overview.mmd").write_text(subsystem_dependency_report["mermaid"], encoding="utf-8")
    write_json(ARTIFACTS_DIR / "folder_records.json", [asdict(record) for record in folder_records])
    write_csv(ARTIFACTS_DIR / "artifact_flow_matrix.csv", ARTIFACT_FLOWS)
    write_json(ARTIFACTS_DIR / "inventory_summary.json", summary)
    write_json(ARTIFACTS_DIR / "bibliography_seed.json", EXTERNAL_REFERENCES)
    return summary


def main() -> int:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    # First pass materializes generated files; second pass makes the snapshot self-inclusive.
    build_outputs()
    summary = build_outputs()

    print(json.dumps(summary, indent=2, sort_keys=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
