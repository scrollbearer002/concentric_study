from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOG_TOOL = ROOT / "operator" / "cre" / "tools" / "log_environment_compliance.py"
REVIEW_TOOL = ROOT / "operator" / "cre" / "tools" / "review_environment_compliance.py"
TEMPLATE = ROOT / "operator" / "cre" / "artifacts" / "environment_answer_compliance_template.json"


def test_log_environment_compliance_appends_valid_entry(tmp_path: Path) -> None:
    log_path = tmp_path / "compliance.jsonl"
    mirror_path = tmp_path / "mirror.jsonl"
    cmd = [
        "python3",
        str(LOG_TOOL),
        "--log", str(log_path),
        "--mirror-log", str(mirror_path),
        "--template", str(TEMPLATE),
        "--task-summary", "phase 1 host health recommendation",
        "--system-of-interest", "concentric_study",
        "--machine", "macOS 26.3 arm64",
        "--runtime", "./operator/venv/bin/python",
        "--repo", str(ROOT),
        "--apps", "Cursor||Safari",
        "--repo-specific-evidence", "operator/capability_router.py||operator/agent_infra/startup.py",
        "--stakeholder-objective", "reduce environment-specific answer drift",
        "--directly-supported", "rule exists in repo||environment fingerprint exists",
        "--inferred", "residual risk is reduced",
        "--non-regression-classification", "core enhancement with non-regression evidence",
    ]
    subprocess.run(cmd, check=True)
    lines = log_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["status"] == "pass"
    assert entry["system_of_interest"] == "concentric_study"
    assert entry["local_environment"]["apps"] == ["Cursor", "Safari"]
    mirror_lines = mirror_path.read_text(encoding="utf-8").splitlines()
    assert len(mirror_lines) == 1
    assert json.loads(mirror_lines[0])["task_summary"] == "phase 1 host health recommendation"


def test_review_environment_compliance_summarizes_misses(tmp_path: Path) -> None:
    log_path = tmp_path / "compliance.jsonl"
    entries = [
        {
            "timestamp_utc": "2026-03-03T00:00:00Z",
            "task_summary": "good answer",
            "system_of_interest": "concentric_study",
            "local_environment": {"machine": "macOS", "runtime": "venv", "repo": "repo", "apps": []},
            "repo_specific_evidence": ["a"],
            "stakeholder_objective": "obj",
            "directly_supported": ["one"],
            "inferred": [],
            "unknown": [],
            "answer_mode": "environment_specific",
            "status": "pass",
            "failure_reasons": [],
            "non_regression_classification": "not_applicable",
            "notes": ""
        },
        {
            "timestamp_utc": "2026-03-03T00:01:00Z",
            "task_summary": "missed answer",
            "system_of_interest": "concentric_study",
            "local_environment": {"machine": "macOS", "runtime": "venv", "repo": "repo", "apps": []},
            "repo_specific_evidence": ["a"],
            "stakeholder_objective": "obj",
            "directly_supported": [],
            "inferred": [],
            "unknown": ["need env check"],
            "answer_mode": "environment_specific",
            "status": "fail",
            "failure_reasons": ["missing_environment_basis"],
            "non_regression_classification": "not_applicable",
            "notes": ""
        }
    ]
    with log_path.open("w", encoding="utf-8") as fh:
        for entry in entries:
            fh.write(json.dumps(entry) + "\n")

    json_out = tmp_path / "review.json"
    md_out = tmp_path / "review.md"
    subprocess.run([
        "python3",
        str(REVIEW_TOOL),
        "--log", str(log_path),
        "--json-out", str(json_out),
        "--md-out", str(md_out),
    ], check=True)

    summary = json.loads(json_out.read_text(encoding="utf-8"))
    assert summary["total_entries"] == 2
    assert summary["miss_count"] == 1
    assert summary["status_counts"]["pass"] == 1
    assert summary["status_counts"]["fail"] == 1
    assert md_out.exists()
    assert "missing_environment_basis" in md_out.read_text(encoding="utf-8")
