#!/usr/bin/env python3
"""Build a curated top-level document registry for operator/cre.

The goal is not to delete history automatically. The goal is to make the
top-level doc surface legible: identify the canonical reading spine, distinguish
supporting studies from case studies, and mark status/log documents that should
not be treated as current source-of-truth material.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CRE_DIR = ROOT / "operator" / "cre"
ARTIFACTS_DIR = CRE_DIR / "artifacts"
OUTPUT_JSON = ARTIFACTS_DIR / "cre_top_level_doc_registry.json"
OUTPUT_MD = CRE_DIR / "CANONICAL_RESEARCH_INDEX_PHD.md"
SOURCE_REGISTRY = ARTIFACTS_DIR / "cre_doc_surface_primary_sources.json"
TEXT_SUFFIXES = {".md", ".txt", ".log"}
SCAN_SUFFIXES = {".md", ".txt", ".json", ".py", ".mdc", ".log"}
SKIP_PARTS = {".git", "venv", "__pycache__", ".pytest_cache", "runs"}

CORE_ORDER = [
    "README.md",
    "CANONICAL_RESEARCH_INDEX_PHD.md",
    "DOC_SURFACE_GOVERNANCE_PHD.md",
    "PHD_DECISION_PRACTICE.md",
    "PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md",
    "CURRENT_ARCHITECTURE_SURFACE_PHD.md",
    "DEBUGGING_THIS_PROJECT_PHD.md",
    "PROJECT_TOOLING_DEEP_AUDIT_PHD.md",
    "MASTER_TOOL_LIST_PHD.md",
    "PROJECT_SCIENTIFIC_COHERENCE_AUDIT_PHD.md",
    "PHASE_1_ENVIRONMENT_BENEFITS_PHD.md",
    "HOST_TOOL_HEALTH_DISCOVERY_PHD.md",
    "MISSED_TOOL_WORKFLOW_VALUE_PHD.md",
    "PLACEMENT_RESEARCH.md",
    "CURSOR_MCP_LANDSCAPE_PHD.md",
    "CURSOR_2_6_PROJECT_FIT_PHD.md",
    "CURSOR_2_6_OPERATING_PROTOCOL_PHD.md",
    "EXTERNAL_MCP_GOVERNANCE_PHD.md",
    "CONTEXT7_PILOT_PHD.md",
    "CURSOR_CLOUD_AND_TEAM_SURFACES_PHD.md",
]

CANONICAL_SNAPSHOT = {
    "CANONICAL_RUNTIME_BASELINE_PHD.md",
    "CURSOR_ENVIRONMENT_MONITOR_PHD.md",
    "CURSOR_OFFICIAL_UPDATES_2026_PHD_RESEARCH.md",
}

SUPPORTING_RESEARCH = {
    "ACADEMIC_VALIDATION.md",
    "ALLOWLIST_PREACTION_IMPLEMENTATION_OUTLINE.md",
    "ANSWER_COMPLIANCE_AUDIT_PHD.md",
    "ARCHITECTURE_CONFORMANCE_DETERMINISM_PHD.md",
    "ARCHITECTURE_CONFORMANCE_NEXT_HARDENING_PHD.md",
    "BENCHMARK_STRATEGY_FOR_THIS_PROJECT_PHD.md",
    "CONTEXT_LOCKED_RESEARCH_FILTER_PHD.md",
    "DEAD_WEIGHT_SIGNALS_PHD.md",
    "DECOMPOSITION_HANDBOOK_PHD.md",
    "ENVIRONMENT_COMPLIANCE_AUTOMATION_PHD.md",
    "ENVIRONMENT_COMPLIANCE_REVIEW_PHD.md",
    "ENVIRONMENT_JUSTIFICATION_GATE_PHD.md",
    "ESSAY_PROJECT_OVERLAP_PHD.md",
    "FINAL_TOOL_COVERAGE_AUDIT_PHD.md",
    "HIGH_VALUE_TOOL_ROLLOUT_PHD.md",
    "PAST_TOOL_AWARENESS_AUDIT_PHD.md",
    "PHD_CHAT_TOOL_USE_RESEARCH.md",
    "PROJECT_TOOLING_DEEP_AUDIT_PHD.md",
    "RECURSIVE_PHD_RESEARCH_LOOP.md",
    "ROADMAP_PHD_RESEARCH_MEMO.md",
    "RUST_PARENT_ENVIRONMENT_SOPHISTICATION_AUDIT_PHD.md",
    "RUST_TRANSFER_PRIORITY_ROADMAP_PHD.md",
    "TOOL_CHEAT_SHEET_PHD.md",
    "TOOL_CONNECTIONS_DIAGRAM.md",
    "TOOLS_USED_IN_CHAT_PHD_RESEARCH.md",
    "VISUAL_REASONING_ENHANCEMENT_PHD.md",
    "WHAT_OTHERS_USE_TO_MASTER_VISUAL_BRANCH_PHD.md",
    "WHOLE_PROJECT_TRUTH_AUDIT_PHD.md",
}

CASE_STUDIES = {
    "COUSIN_VISUAL_REASONING_SHOWCASE.md",
    "FRESH_LIVE_ART_BENCHMARK_PHD.md",
    "IQ_TEST_PREPARATION_PROTOCOL_PHD.md",
    "JSPAINT_DRAW_FAILURE_FORENSICS_PHD.md",
    "KLEKI_RESET_AND_ART_BENCHMARK_PHD.md",
    "LAST_3_KLEKI_FIX_PROGRAM_PHD.md",
    "LAST_3_KLEKI_RUNS_LINE_BY_LINE_AUDIT_PHD.md",
    "MAGMA_LAST_RUN_RESEARCH.md",
    "MAGMA_REALISM_PRESETS.md",
    "MAGMA_TOOLS_PHD_RESEARCH.md",
    "MAGMA_TRACED_INTEGRATION.md",
    "PRECLICK_CONFIRMATION_RESEARCH_PHD.md",
    "RECOVERY_CHECKPOINTS_PHD.md",
    "REDDIT_AUTOMATION_FOUNDATION_PHD.md",
    "REDDIT_BRIAN_LIVE_DEMO.md",
    "REDDIT_PRODUCTIZATION_PLAN_PHD.md",
    "REDDIT_PRODUCTIZATION_PLAN_PHD_REVALIDATED.md",
    "RESEARCH_AGENT_DESIGN.md",
    "SUBJECT_LOOKUP_FOR_DRAWING.md",
}

HISTORICAL_REPORTS = {
    "BRILLIANT_LIVE_TEST_LOG.md",
    "COMPLETION_SUMMARY.md",
    "COVT_EXECUTION_STATUS.md",
    "COVT_IMPLEMENTATION.md",
    "EVIDENCE_DRIVEN_EXECUTION_SPEC.md",
    "EXECUTION_ANALYSIS.md",
    "EXECUTION_LOG_REFERENCE.md",
    "EXECUTION_STATUS.md",
    "EXECUTION_SUMMARY.md",
    "EXECUTIVE_SUMMARY_PROJECT_TYPE_VERIFICATION.md",
    "EXECUTIVE_SUMMARY_VERIFICATION.md",
    "EXHAUSTIVE_CODE_RUN_REPORT.md",
    "EXHAUSTIVE_TEST_ANALYSIS.md",
    "FINAL_IMPLEMENTATION_REPORT.md",
    "FINAL_REPORT.md",
    "FINAL_TEST_SUMMARY.md",
    "FIXES_APPLIED.md",
    "HYBRID_COVT_VALIDATION.md",
    "IMPLEMENTATION_COMPLETE.md",
    "IMPLEMENTATION_SUMMARY.md",
    "INITIALIZATION_REPORT.md",
    "IQ_TEST_LIVE_RUN_LOG.md",
    "MODEL_BASED_PLANNING_SOLUTION.md",
    "MODEL_UPDATE.md",
    "PHASE_2_3_STATUS.md",
    "PHD_REMEDIATION_PLAN.md",
    "PROBLEM_ANALYSIS.md",
    "TEST_EXECUTION_COMPLETE.md",
    "TEST_RESULTS.md",
    "ULTIMATE_TESTS.md",
    "ULTIMATE_TEST_COMPLETE.md",
    "ULTIMATE_TEST_EXECUTION_LOG.md",
    "ULTIMATE_TEST_RESULTS.md",
    "ULTIMATE_TEST_SUCCESS.md",
    "VLM_INTEGRATION_PLAN.md",
}

LOCAL_OPERATIONAL = {
    "API_KEY_SETUP.md",
    "DEMO_CHECKLIST.md",
    "FOR_COLLEAGUE.md",
    "SHOWCASE.md",
    "SLACK_OR_EMAIL.txt",
    "requirements-study.txt",
}

LOCAL_LOGS = {
    "agent_debug.log",
    "concentric_triangles_clean_pass_log.txt",
    "debug-a16689.log",
    "execution_log.txt",
    "kleki_execution_log.txt",
    "magma_story.md",
    "test_excalidraw_execution_log.md",
}

CATEGORY_META = {
    "canonical_core": {
        "placement_action": "keep_top_level",
        "recommended_target": "operator/cre/",
        "index_tier": "core",
        "rationale": "Current source-of-truth material for how the repo works or how current repo policy should be applied.",
    },
    "canonical_snapshot": {
        "placement_action": "keep_top_level",
        "recommended_target": "operator/cre/",
        "index_tier": "active_snapshot",
        "rationale": "Current snapshot memo worth keeping near the top level, but time-sensitive and expected to be refreshed.",
    },
    "supporting_research": {
        "placement_action": "retain_but_deemphasize",
        "recommended_target": "operator/cre/reference/",
        "index_tier": "supporting",
        "rationale": "Useful supporting memo or audit, but not part of the shortest canonical reading path.",
    },
    "case_study": {
        "placement_action": "move_to_case_studies",
        "recommended_target": "operator/cre/case_studies/",
        "index_tier": "appendix_only",
        "rationale": "Specific benchmark, site, or experiment study that should be retained but not left in the top-level reading spine.",
    },
    "historical_report": {
        "placement_action": "move_to_archive",
        "recommended_target": "operator/cre/history/",
        "index_tier": "appendix_only",
        "rationale": "Status, implementation, or completion report preserved for provenance but superseded by newer architecture/state documents.",
    },
    "local_operational": {
        "placement_action": "move_to_local_ops",
        "recommended_target": "operator/cre/local_ops/",
        "index_tier": "appendix_only",
        "rationale": "Local setup or presentation note that should not be treated as a canonical research or architecture document.",
    },
    "local_log": {
        "placement_action": "move_to_logs",
        "recommended_target": "operator/cre/history/logs/",
        "index_tier": "appendix_only",
        "rationale": "Execution byproduct or narrative log retained only for provenance; should not live in the canonical doc surface.",
    },
}

TOPIC_OVERRIDES = {
    "README.md": "directory_governance",
    "CANONICAL_RESEARCH_INDEX_PHD.md": "directory_governance",
    "DOC_SURFACE_GOVERNANCE_PHD.md": "directory_governance",
    "PHD_DECISION_PRACTICE.md": "method",
    "DECOMPOSITION_HANDBOOK_PHD.md": "method",
    "PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md": "project_definition",
    "CURRENT_ARCHITECTURE_SURFACE_PHD.md": "architecture",
    "DEBUGGING_THIS_PROJECT_PHD.md": "debugging",
    "PROJECT_TOOLING_DEEP_AUDIT_PHD.md": "tooling",
    "MASTER_TOOL_LIST_PHD.md": "tooling",
    "PROJECT_SCIENTIFIC_COHERENCE_AUDIT_PHD.md": "validation",
    "PHASE_1_ENVIRONMENT_BENEFITS_PHD.md": "environment",
    "HOST_TOOL_HEALTH_DISCOVERY_PHD.md": "environment",
    "MISSED_TOOL_WORKFLOW_VALUE_PHD.md": "workflow",
    "PLACEMENT_RESEARCH.md": "method",
    "CURSOR_MCP_LANDSCAPE_PHD.md": "cursor",
    "CURSOR_2_6_PROJECT_FIT_PHD.md": "cursor",
    "CURSOR_2_6_OPERATING_PROTOCOL_PHD.md": "cursor",
    "EXTERNAL_MCP_GOVERNANCE_PHD.md": "cursor",
    "CONTEXT7_PILOT_PHD.md": "cursor",
    "CURSOR_CLOUD_AND_TEAM_SURFACES_PHD.md": "cursor",
}

CORE_ROLE_OVERRIDES = {
    "README.md": "Directory entrypoint and index handoff.",
    "CANONICAL_RESEARCH_INDEX_PHD.md": "Curated map of the top-level research surface.",
    "DOC_SURFACE_GOVERNANCE_PHD.md": "External-evidence justification for why the top-level doc surface is classified and reduced the way it is.",
    "PHD_DECISION_PRACTICE.md": "Method rule for evidence-first decisions and research-first implementation.",
    "PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md": "Single broad description of what the project is and how its major components fit.",
    "CURRENT_ARCHITECTURE_SURFACE_PHD.md": "Snapshot of the live architecture and current test/runtime surface.",
    "DEBUGGING_THIS_PROJECT_PHD.md": "Canonical debugging order for the current layered GUI-agent stack.",
    "PROJECT_TOOLING_DEEP_AUDIT_PHD.md": "Current tool and dependency surface beyond package manifests alone.",
    "MASTER_TOOL_LIST_PHD.md": "Definitive inventory of project tools and their status.",
    "PROJECT_SCIENTIFIC_COHERENCE_AUDIT_PHD.md": "Evidence-level audit of what is implemented, analogical, or overstated.",
    "PHASE_1_ENVIRONMENT_BENEFITS_PHD.md": "Why environment discipline is a first-order requirement for this repo.",
    "HOST_TOOL_HEALTH_DISCOVERY_PHD.md": "Host-tool health layer rationale and substrate discovery basis.",
    "MISSED_TOOL_WORKFLOW_VALUE_PHD.md": "Workflow-value ranking for tools and capability gaps.",
    "PLACEMENT_RESEARCH.md": "Canonical example of facts-before-decision placement reasoning.",
    "CURSOR_MCP_LANDSCAPE_PHD.md": "Current Cursor MCP landscape, prioritization, and internal MCP opportunities.",
    "CURSOR_2_6_PROJECT_FIT_PHD.md": "Repo-specific Cursor 2.6 implementation strategy.",
    "CURSOR_2_6_OPERATING_PROTOCOL_PHD.md": "Operational protocol for using Cursor in this repo without tool sprawl.",
    "EXTERNAL_MCP_GOVERNANCE_PHD.md": "Explicit gate for external MCP rollout.",
    "CONTEXT7_PILOT_PHD.md": "Current external MCP pilot design and decision rule.",
    "CURSOR_CLOUD_AND_TEAM_SURFACES_PHD.md": "Deferred classification for account-gated Cursor surfaces.",
}

HISTORICAL_SUPERSEDERS = [
    "CANONICAL_RESEARCH_INDEX_PHD.md",
    "PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md",
    "CURRENT_ARCHITECTURE_SURFACE_PHD.md",
]

LOG_SUPERSEDERS = [
    "DEBUGGING_THIS_PROJECT_PHD.md",
    "CURRENT_ARCHITECTURE_SURFACE_PHD.md",
]


@dataclass
class DocRecord:
    path: str
    name: str
    title: str
    line_count: int
    repo_reference_count: int
    category: str
    topic: str
    placement_action: str
    recommended_target: str
    index_tier: str
    rationale: str
    role_summary: str
    superseded_by: list[str]


def iter_repo_text() -> list[tuple[str, str]]:
    records: list[tuple[str, str]] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_PARTS for part in path.parts):
            continue
        if path.suffix.lower() not in SCAN_SUFFIXES:
            continue
        try:
            text = path.read_text(errors="ignore")
        except OSError:
            continue
        records.append((str(path.relative_to(ROOT)), text))
    return records


def first_heading(path: Path) -> str:
    try:
        for line in path.read_text(errors="ignore").splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                return stripped.lstrip("#").strip()
    except OSError:
        pass
    return path.stem.replace("_", " ")


def classify(name: str) -> str:
    if name in CORE_ORDER:
        return "canonical_core"
    if name in CANONICAL_SNAPSHOT:
        return "canonical_snapshot"
    if name in SUPPORTING_RESEARCH:
        return "supporting_research"
    if name in CASE_STUDIES:
        return "case_study"
    if name in HISTORICAL_REPORTS:
        return "historical_report"
    if name in LOCAL_OPERATIONAL:
        return "local_operational"
    if name in LOCAL_LOGS:
        return "local_log"
    if name.endswith(".log") or "LOG" in name:
        return "local_log"
    if any(token in name for token in ("FINAL_", "IMPLEMENTATION", "EXECUTION_", "ULTIMATE_", "STATUS", "SUMMARY")):
        return "historical_report"
    if any(token in name for token in ("REDDIT", "MAGMA", "KLEKI", "JSPAINT", "IQ_TEST", "COUSIN")):
        return "case_study"
    return "supporting_research"


def topic_for(name: str, category: str) -> str:
    if name in TOPIC_OVERRIDES:
        return TOPIC_OVERRIDES[name]
    defaults = {
        "canonical_core": "core",
        "canonical_snapshot": "snapshot",
        "supporting_research": "supporting",
        "case_study": "case_study",
        "historical_report": "historical",
        "local_operational": "operations",
        "local_log": "logs",
    }
    return defaults[category]


def role_summary(name: str, category: str) -> str:
    if name in CORE_ROLE_OVERRIDES:
        return CORE_ROLE_OVERRIDES[name]
    summaries = {
        "canonical_snapshot": "Snapshot memo that is still useful, but date-sensitive.",
        "supporting_research": "Secondary research or audit that informs the project without defining the shortest canonical path.",
        "case_study": "Specific experiment or benchmark narrative preserved as a case study.",
        "historical_report": "Superseded status or implementation report retained for provenance.",
        "local_operational": "Local setup or presentation note, not a canonical research source.",
        "local_log": "Execution or debugging log retained only as local evidence.",
    }
    return summaries[category]


def superseders(name: str, category: str) -> list[str]:
    if category == "historical_report":
        return HISTORICAL_SUPERSEDERS
    if category == "local_log":
        return LOG_SUPERSEDERS
    if category == "local_operational":
        return ["CANONICAL_RESEARCH_INDEX_PHD.md", "README.md"]
    return []


def build_records() -> list[DocRecord]:
    repo_text = iter_repo_text()
    current_files = sorted(
        [
            path
            for path in CRE_DIR.iterdir()
            if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES
        ]
    )
    records: list[DocRecord] = []
    seen = set()
    for path in current_files:
        title = first_heading(path)
        lines = path.read_text(errors="ignore").splitlines()
        rel_path = str(path.relative_to(ROOT))
        ref_count = sum(text.count(path.name) + text.count(rel_path) for _, text in repo_text)
        category = classify(path.name)
        meta = CATEGORY_META[category]
        records.append(
            DocRecord(
                path=rel_path,
                name=path.name,
                title=title,
                line_count=len(lines),
                repo_reference_count=ref_count,
                category=category,
                topic=topic_for(path.name, category),
                placement_action=meta["placement_action"],
                recommended_target=meta["recommended_target"],
                index_tier=meta["index_tier"],
                rationale=meta["rationale"],
                role_summary=role_summary(path.name, category),
                superseded_by=superseders(path.name, category),
            )
        )
        seen.add(path.name)

    generated_name = OUTPUT_MD.name
    if generated_name not in seen:
        category = "canonical_core"
        meta = CATEGORY_META[category]
        records.append(
            DocRecord(
                path=str(OUTPUT_MD.relative_to(ROOT)),
                name=generated_name,
                title="Canonical Research Index (PhD)",
                line_count=0,
                repo_reference_count=0,
                category=category,
                topic="directory_governance",
                placement_action=meta["placement_action"],
                recommended_target=meta["recommended_target"],
                index_tier=meta["index_tier"],
                rationale=meta["rationale"],
                role_summary=CORE_ROLE_OVERRIDES[generated_name],
                superseded_by=[],
            )
        )

    return sorted(records, key=lambda record: (record.category, record.name))


def grouped(records: list[DocRecord]) -> dict[str, list[DocRecord]]:
    bucket: dict[str, list[DocRecord]] = defaultdict(list)
    for record in records:
        bucket[record.category].append(record)
    for values in bucket.values():
        values.sort(key=lambda record: (-record.repo_reference_count, record.name))
    return bucket


def render_markdown(records: list[DocRecord]) -> str:
    groups = grouped(records)
    text_doc_count = len(records)
    category_counts = Counter(record.category for record in records)
    core_records = {record.name: record for record in records}

    lines: list[str] = []
    lines.append("# Canonical Research Index (PhD)")
    lines.append("")
    lines.append("## Context")
    lines.append("")
    lines.append(f"- Top-level textual surface under `operator/cre`: `{text_doc_count}` files.")
    lines.append(f"- Markdown files in that surface: `{sum(1 for record in records if record.name.endswith('.md'))}`.")
    lines.append(
        "- The current top-level directory mixes canonical architecture memos, supporting audits, "
        "case-study writeups, historical status reports, and local operational notes."
    )
    lines.append(
        "- Treating all of them as equally current creates documentation noise, source-of-truth drift, "
        "and weak onboarding."
    )
    lines.append("")
    lines.append("## Decision")
    lines.append("")
    lines.append(
        "Use a curated index with explicit categories. Only `canonical_core` and "
        "`canonical_snapshot` documents belong in the default reading path."
    )
    lines.append("")
    lines.append("## Core Reading Path")
    lines.append("")
    for name in CORE_ORDER:
        record = core_records.get(name)
        if not record:
            continue
        lines.append(f"- `{record.name}`: {record.role_summary}")
    lines.append("")
    lines.append("## External Research Basis")
    lines.append("")
    lines.append(
        "This index is grounded in external architecture-documentation and repository-comprehension sources, not only local preference."
    )
    lines.append("")
    lines.append(
        f"- Primary source register: `{SOURCE_REGISTRY.relative_to(ROOT)}`"
    )
    lines.append("- ISO/IEC/IEEE 42010: architecture descriptions organize concerns, viewpoints, correspondences, and rationale.")
    lines.append("- SEI Views and Beyond: documentation should be organized around relevant stakeholder views, not a flat undifferentiated corpus.")
    lines.append("- SEI documentation guidance: architecture must be understandable and packaged for stakeholders, or it cannot be analyzed effectively.")
    lines.append("- CACM requirements tracing: cross-artifact traceability matters, which supports keeping a machine-readable registry.")
    lines.append("- SEI README and recent repository summarization / reconstruction work: rebuildable repository summaries are valid generated aids, but they should be distinguished from canonical authored docs.")
    lines.append("")
    lines.append("## Active Snapshot Docs")
    lines.append("")
    for record in groups.get("canonical_snapshot", []):
        lines.append(f"- `{record.name}`: {record.role_summary}")
    lines.append("")
    lines.append("## Supporting Research")
    lines.append("")
    for record in groups.get("supporting_research", []):
        lines.append(f"- `{record.name}`")
    lines.append("")
    lines.append("## Case Studies")
    lines.append("")
    for record in groups.get("case_study", []):
        lines.append(f"- `{record.name}`")
    lines.append("")
    lines.append("## Historical / Superseded Reports")
    lines.append("")
    lines.append(
        "These are useful for provenance, but they should not be cited as the current source of truth without checking the core docs first."
    )
    lines.append("")
    for record in groups.get("historical_report", []):
        superseded = ", ".join(f"`{name}`" for name in record.superseded_by)
        lines.append(f"- `{record.name}`: superseded by {superseded}")
    lines.append("")
    lines.append("## Local Operational Notes And Logs")
    lines.append("")
    for category in ("local_operational", "local_log"):
        for record in groups.get(category, []):
            lines.append(f"- `{record.name}` -> suggested target `{record.recommended_target}`")
    lines.append("")
    lines.append("## Category Counts")
    lines.append("")
    for category in (
        "canonical_core",
        "canonical_snapshot",
        "supporting_research",
        "case_study",
        "historical_report",
        "local_operational",
        "local_log",
    ):
        lines.append(f"- `{category}`: `{category_counts.get(category, 0)}`")
    lines.append("")
    lines.append("## Machine-Readable Registry")
    lines.append("")
    lines.append(f"- `{OUTPUT_JSON.relative_to(ROOT)}`")
    lines.append("")
    lines.append("## Regenerate")
    lines.append("")
    lines.append("```bash")
    lines.append("python3 operator/cre/tools/build_cre_doc_registry.py")
    lines.append("```")
    lines.append("")
    lines.append("## Appendix: Full Placement Classification")
    lines.append("")
    for category in (
        "canonical_core",
        "canonical_snapshot",
        "supporting_research",
        "case_study",
        "historical_report",
        "local_operational",
        "local_log",
    ):
        entries = groups.get(category, [])
        if not entries:
            continue
        lines.append(f"### `{category}`")
        lines.append("")
        for record in entries:
            lines.append(
                f"- `{record.name}` | refs `{record.repo_reference_count}` | action `{record.placement_action}` | target `{record.recommended_target}`"
            )
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    records = build_records()
    OUTPUT_JSON.write_text(
        json.dumps(
            {
                "generated_at": "2026-03-04",
                "top_level_path": str(CRE_DIR.relative_to(ROOT)),
                "source_registry": str(SOURCE_REGISTRY.relative_to(ROOT)),
                "counts": Counter(record.category for record in records),
                "core_reading_order": CORE_ORDER,
                "records": [asdict(record) for record in records],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    OUTPUT_MD.write_text(render_markdown(records), encoding="utf-8")
    print(f"Wrote {OUTPUT_JSON.relative_to(ROOT)}")
    print(f"Wrote {OUTPUT_MD.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
