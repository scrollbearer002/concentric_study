#!/usr/bin/env python3
"""Build Section 2 doc-to-code traceability artifacts.

This script encodes the architectural-claim traceability matrix for the
`concentric_study` understanding corpus. The goal is not full natural-language
extraction. The goal is a defensible, evidence-backed mapping from the repo's
main architectural claims to the code, persistent artifacts, and runtime
analysis evidence that substantiate them.
"""
from __future__ import annotations

import csv
import json
import re
import time
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
UNDERSTANDING_DIR = ROOT / "operator" / "cre" / "project_understanding"
ARTIFACTS_DIR = UNDERSTANDING_DIR / "artifacts"
OUTPUT_JSON = ARTIFACTS_DIR / "traceability_matrix.json"
OUTPUT_CSV = ARTIFACTS_DIR / "traceability_matrix.csv"

TRACEABILITY_METHOD_REFS = [
    "ISO/IEC/IEEE 42010: Mappings Between Views",
    "Software Modeling: What to Model and Why",
    "Requirements Tracing",
]


@dataclass
class ClaimTraceRecord:
    claim_id: str
    concern: str
    claim_text: str
    correspondence_type: str
    source_doc_refs: list[str]
    code_refs: list[str]
    artifact_refs: list[str]
    evidence_refs: list[str]
    external_refs: list[str]
    status: str
    notes: str
    validated_local_refs: list[str]
    invalid_local_refs: list[str]


CLAIMS: list[dict[str, object]] = [
    {
        "claim_id": "C001",
        "concern": "observability",
        "claim_text": "Traced runs create per-run directories with `trace.jsonl` and `manifest.json` as first-class runtime artifacts.",
        "correspondence_type": "doc -> code -> runtime artifact",
        "source_doc_refs": [
            "operator/cre/PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md:22",
            "operator/cre/PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md:75",
            "operator/cre/PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md:119",
            "operator/cre/PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md:120",
        ],
        "code_refs": [
            "operator/agent_infra/trace_writer.py:84",
            "operator/agent_infra/trace_writer.py:107",
            "operator/agent_infra/trace_writer.py:135",
            "operator/agent_infra/trace_writer.py:155",
        ],
        "artifact_refs": [
            "operator/cre/project_understanding/artifacts/artifact_flow_matrix.csv",
            "operator/cre/runs/<run_id>/trace.jsonl",
            "operator/cre/runs/<run_id>/manifest.json",
        ],
        "evidence_refs": [
            "operator/cre/runs/LAST_20_RUNS_EXHAUSTIVE.md:4",
        ],
        "external_refs": TRACEABILITY_METHOD_REFS + [
            "A Systematic Survey of Program Comprehension through Dynamic Analysis",
        ],
        "status": "verified",
        "notes": "The constructor creates the run directory and trace files; finalize emits the manifest exactly as the architecture docs claim.",
    },
    {
        "claim_id": "C002",
        "concern": "diagnostics",
        "claim_text": "`DiagnosticReader` implements progressive disclosure through Level 1 summary, Level 2 failure window, and Level 3 step detail.",
        "correspondence_type": "doc -> code",
        "source_doc_refs": [
            "operator/cre/PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md:22",
            "operator/cre/PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md:76",
        ],
        "code_refs": [
            "operator/agent_infra/diagnostic_reader.py:57",
            "operator/agent_infra/diagnostic_reader.py:87",
            "operator/agent_infra/diagnostic_reader.py:151",
            "operator/agent_infra/diagnostic_reader.py:165",
            "operator/agent_infra/diagnostic_reader.py:187",
        ],
        "artifact_refs": [
            "operator/cre/project_understanding/artifacts/artifact_flow_matrix.csv",
        ],
        "evidence_refs": [
            "operator/cre/runs/LAST_20_RUNS_EXHAUSTIVE.md:3",
        ],
        "external_refs": TRACEABILITY_METHOD_REFS + [
            "Views and Beyond: The SEI Approach for Architecture Documentation",
        ],
        "status": "verified",
        "notes": "The reader exposes exactly the three-detail-level interface claimed by the docs, plus a composed `full_diagnostic()` convenience path.",
    },
    {
        "claim_id": "C003",
        "concern": "healing",
        "claim_text": "`HealingOrchestrator` classifies failed runs and turns structured evidence into retry, adjust, escalate, or abort decisions.",
        "correspondence_type": "doc -> code -> runtime artifact",
        "source_doc_refs": [
            "operator/cre/PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md:22",
            "operator/cre/PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md:77",
        ],
        "code_refs": [
            "operator/agent_infra/healing_orchestrator.py:105",
            "operator/agent_infra/healing_orchestrator.py:121",
            "operator/agent_infra/healing_orchestrator.py:125",
            "operator/agent_infra/healing_orchestrator.py:136",
        ],
        "artifact_refs": [
            "operator/cre/project_understanding/artifacts/artifact_flow_matrix.csv",
            "operator/cre/runs/<run_id>/manifest.json",
            "operator/cre/runs/<run_id>/trace.jsonl",
        ],
        "evidence_refs": [
            "operator/cre/runs/LAST_20_RUNS_EXHAUSTIVE.md:8",
        ],
        "external_refs": TRACEABILITY_METHOD_REFS + [
            "Architecture Reconstruction Guidelines, Third Edition",
            "A Systematic Survey of Program Comprehension through Dynamic Analysis",
        ],
        "status": "verified",
        "notes": "The orchestration claim is supported directly by `analyze_run()` and its DDG-extended variant, both of which consume manifest/trace evidence.",
    },
    {
        "claim_id": "C004",
        "concern": "outer-loop memory and escalation",
        "claim_text": "`OuterLoop` persists reflection/rule memory and escalates unresolved runs through a structured escalation handoff.",
        "correspondence_type": "doc -> code -> persistent artifact",
        "source_doc_refs": [
            "operator/cre/PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md:26",
            "operator/cre/PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md:79",
            "operator/cre/PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md:121",
            "operator/cre/PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md:122",
            "operator/cre/PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md:123",
            "operator/cre/PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md:140",
        ],
        "code_refs": [
            "operator/agent_infra/outer_loop.py:93",
            "operator/agent_infra/outer_loop.py:189",
            "operator/agent_infra/outer_loop.py:283",
            "operator/agent_infra/outer_loop.py:308",
            "operator/agent_infra/outer_loop.py:379",
            "operator/agent_infra/outer_loop.py:509",
            "operator/agent_infra/outer_loop.py:637",
            "operator/agent_infra/outer_loop.py:664",
        ],
        "artifact_refs": [
            "operator/cre/runs/reflection_journal.jsonl",
            "operator/cre/runs/<run_id>/ESCALATION.md",
            "operator/cre/runs/<run_id>/ESCALATION.json",
        ],
        "evidence_refs": [
            "operator/cre/runs/LAST_20_RUNS_EXHAUSTIVE.md:12",
        ],
        "external_refs": TRACEABILITY_METHOD_REFS + [
            "ISO/IEC/IEEE 42010",
            "Documenting Software Architectures: Views and Beyond, Second Edition",
        ],
        "status": "refined",
        "notes": "The docs correctly describe journal, rules, and Markdown escalation. The code goes further by also writing `ESCALATION.json`, so the documentation currently understates the machine-readable part of the handoff. The current workspace snapshot contains `reflection_journal.jsonl` but not an observed `rules.jsonl`, which means the rules path is implemented but not yet evidenced in this snapshot.",
    },
    {
        "claim_id": "C005",
        "concern": "learning",
        "claim_text": "Successful runs are ingested into `SkillLibrary` with maturity gating (`candidate -> proven -> master`) and only trusted tiers are reused autonomously.",
        "correspondence_type": "doc -> code -> persistent artifact",
        "source_doc_refs": [
            "operator/cre/PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md:24",
            "operator/cre/PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md:78",
            "operator/cre/PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md:124",
        ],
        "code_refs": [
            "operator/agent_infra/skill_library.py:178",
            "operator/agent_infra/skill_library.py:217",
            "operator/agent_infra/skill_library.py:290",
            "operator/agent_infra/skill_library.py:330",
            "operator/agent_infra/skill_library.py:383",
        ],
        "artifact_refs": [
            "operator/cre/skill_library.json",
            "operator/cre/project_understanding/artifacts/artifact_flow_matrix.csv",
        ],
        "evidence_refs": [
            "operator/cre/runs/LAST_20_RUNS_EXHAUSTIVE.md:16",
        ],
        "external_refs": TRACEABILITY_METHOD_REFS + [
            "Views and Beyond: The SEI Approach for Architecture Documentation",
        ],
        "status": "verified",
        "notes": "The maturity model, ingestion gate, and trusted-tier retrieval are all implemented directly in the canonical module and persisted to `skill_library.json`.",
    },
    {
        "claim_id": "C006",
        "concern": "verification control",
        "claim_text": "`ActionTrustTracker` suppresses costly verification only after enough evidence has accumulated that an action is reliably succeeding.",
        "correspondence_type": "doc -> code -> persistent artifact",
        "source_doc_refs": [
            "operator/cre/PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md:28",
            "operator/cre/PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md:80",
            "AGENTS.md",
        ],
        "code_refs": [
            "operator/agent_infra/action_trust.py:1",
            "operator/agent_infra/action_trust.py:57",
            "operator/agent_infra/action_trust.py:85",
            "operator/agent_infra/action_trust.py:102",
            "operator/agent_infra/action_trust.py:112",
            "operator/agent_infra/action_trust.py:118",
        ],
        "artifact_refs": [
            "operator/cre/action_trust.json",
            "operator/cre/project_understanding/artifacts/artifact_flow_matrix.csv",
        ],
        "evidence_refs": [
            "operator/cre/PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md:125",
        ],
        "external_refs": TRACEABILITY_METHOD_REFS,
        "status": "refined",
        "notes": "The architecture claim is directionally correct, but the current code no longer uses the simplified 'skip after 5 successes' threshold described in some docs. It now uses a Beta-Binomial posterior bound, which is stricter and more defensible.",
    },
    {
        "claim_id": "C007",
        "concern": "recovery",
        "claim_text": "The recovery pipeline diagnoses failures, injects episodic/rule context, executes recovery actions, and verifies recovery postconditions before proceeding.",
        "correspondence_type": "doc -> code -> runtime evidence",
        "source_doc_refs": [
            "operator/cre/PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md:82",
            "operator/cre/PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md:122",
            "operator/cre/PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md:123",
            "operator/cre/PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md:140",
        ],
        "code_refs": [
            "operator/agent_infra/recovery.py:67",
            "operator/agent_infra/recovery.py:90",
            "operator/agent_infra/recovery.py:98",
            "operator/agent_infra/recovery.py:172",
            "operator/agent_infra/recovery.py:216",
            "operator/agent_infra/recovery.py:532",
        ],
        "artifact_refs": [
            "operator/cre/runs/reflection_journal.jsonl",
            "operator/cre/runs/<run_id>/trace.jsonl",
        ],
        "evidence_refs": [
            "operator/cre/runs/LAST_20_RUNS_EXHAUSTIVE.md:3",
        ],
        "external_refs": TRACEABILITY_METHOD_REFS + [
            "A Systematic Survey of Program Comprehension through Dynamic Analysis",
        ],
        "status": "verified",
        "notes": "The main recovery path is implemented exactly as a diagnose -> recover -> verify loop, with past lessons and extracted rules injected before diagnosis. In the current snapshot, the reflection journal exists while `rules.jsonl` has not yet been materialized by an observed run.",
    },
    {
        "claim_id": "C008",
        "concern": "security",
        "claim_text": "`InputSanitizer` defends against prompt injection and MCP-specific poisoning through both general sanitization and tool/schema checks.",
        "correspondence_type": "doc -> code",
        "source_doc_refs": [
            "operator/cre/PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md:30",
            "operator/cre/PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md:102",
        ],
        "code_refs": [
            "operator/security/sanitizer.py:198",
            "operator/security/sanitizer.py:210",
            "operator/security/sanitizer.py:275",
            "operator/security/sanitizer.py:316",
            "operator/security/sanitizer.py:332",
        ],
        "artifact_refs": [],
        "evidence_refs": [],
        "external_refs": TRACEABILITY_METHOD_REFS + [
            "ISO/IEC/IEEE 42010",
        ],
        "status": "verified",
        "notes": "The implementation covers the documented sanitization surface: free-text sanitization, tool-description sanitization, tool-response sanitization, and schema integrity checking.",
    },
    {
        "claim_id": "C009",
        "concern": "credential safety",
        "claim_text": "`CredentialVault` and `HITLGuard` enforce a sensitive-action boundary around credential access and human approval.",
        "correspondence_type": "doc -> code",
        "source_doc_refs": [
            "operator/cre/PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md:30",
            "operator/cre/PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md:103",
        ],
        "code_refs": [
            "operator/security/credential_vault.py:54",
            "operator/security/credential_vault.py:66",
            "operator/security/credential_vault.py:116",
            "operator/security/credential_vault.py:146",
            "operator/security/credential_vault.py:158",
        ],
        "artifact_refs": [],
        "evidence_refs": [],
        "external_refs": TRACEABILITY_METHOD_REFS + [
            "ISO/IEC/IEEE 42010",
        ],
        "status": "verified",
        "notes": "The boundary is explicit: domain-scoped keychain lookup, approval-required action classification, and password/new-domain checks in the HITL guard.",
    },
]


def _looks_like_pattern(ref: str) -> bool:
    return any(token in ref for token in ("<", "*", "?"))


def _parse_local_ref(ref: str) -> tuple[Path, int | None] | None:
    if ref.startswith("http://") or ref.startswith("https://"):
        return None
    if _looks_like_pattern(ref):
        return None
    match = re.match(r"^(.*?)(?::(\d+))?$", ref)
    if not match:
        return None
    path_str, line_str = match.groups()
    return ROOT / path_str, int(line_str) if line_str else None


def _validate_local_ref(ref: str) -> str | None:
    parsed = _parse_local_ref(ref)
    if parsed is None:
        return None
    path, line_no = parsed
    if not path.exists():
        return f"missing path: {ref}"
    if line_no is None:
        return None
    try:
        line_count = len(path.read_text(encoding="utf-8", errors="replace").splitlines())
    except OSError as exc:
        return f"unreadable path: {ref} ({exc})"
    if line_no < 1 or line_no > line_count:
        return f"invalid line: {ref} (line count {line_count})"
    return None


def _build_claim_record(spec: dict[str, object]) -> ClaimTraceRecord:
    local_refs: list[str] = []
    for key in ("source_doc_refs", "code_refs", "artifact_refs", "evidence_refs"):
        local_refs.extend(spec[key])
    validated: list[str] = []
    invalid: list[str] = []
    for ref in local_refs:
        problem = _validate_local_ref(ref)
        if problem is None:
            if not _looks_like_pattern(ref):
                validated.append(ref)
        else:
            invalid.append(problem)
    return ClaimTraceRecord(
        claim_id=spec["claim_id"],
        concern=spec["concern"],
        claim_text=spec["claim_text"],
        correspondence_type=spec["correspondence_type"],
        source_doc_refs=list(spec["source_doc_refs"]),
        code_refs=list(spec["code_refs"]),
        artifact_refs=list(spec["artifact_refs"]),
        evidence_refs=list(spec["evidence_refs"]),
        external_refs=list(spec["external_refs"]),
        status=spec["status"],
        notes=spec["notes"],
        validated_local_refs=validated,
        invalid_local_refs=invalid,
    )


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError("No rows to write")
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def build_outputs() -> dict[str, object]:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    claim_records = [_build_claim_record(spec) for spec in CLAIMS]
    status_summary = Counter(record.status for record in claim_records)
    invalid_refs = [problem for record in claim_records for problem in record.invalid_local_refs]
    payload = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "method_sources": TRACEABILITY_METHOD_REFS,
        "claim_count": len(claim_records),
        "status_summary": dict(status_summary),
        "validated_local_ref_count": sum(len(record.validated_local_refs) for record in claim_records),
        "invalid_local_ref_count": len(invalid_refs),
        "invalid_local_refs": invalid_refs,
        "claims": [asdict(record) for record in claim_records],
    }
    csv_rows = []
    for record in claim_records:
        csv_rows.append(
            {
                "claim_id": record.claim_id,
                "concern": record.concern,
                "status": record.status,
                "correspondence_type": record.correspondence_type,
                "claim_text": record.claim_text,
                "source_doc_refs": "; ".join(record.source_doc_refs),
                "code_refs": "; ".join(record.code_refs),
                "artifact_refs": "; ".join(record.artifact_refs),
                "evidence_refs": "; ".join(record.evidence_refs),
                "external_refs": "; ".join(record.external_refs),
                "notes": record.notes,
                "validated_local_refs": "; ".join(record.validated_local_refs),
                "invalid_local_refs": "; ".join(record.invalid_local_refs),
            }
        )
    _write_json(OUTPUT_JSON, payload)
    _write_csv(OUTPUT_CSV, csv_rows)
    return payload


if __name__ == "__main__":
    result = build_outputs()
    print(json.dumps({
        "claim_count": result["claim_count"],
        "status_summary": result["status_summary"],
        "invalid_local_ref_count": result["invalid_local_ref_count"],
        "validated_local_ref_count": result["validated_local_ref_count"],
    }, indent=2, sort_keys=False))
