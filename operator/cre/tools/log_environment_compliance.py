from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
ARTIFACTS = ROOT / "operator" / "cre" / "artifacts"
DEFAULT_LOG = ARTIFACTS / "environment_answer_compliance_log.jsonl"
DEFAULT_TEMPLATE = ARTIFACTS / "environment_answer_compliance_template.json"
AUTOMATION_ROOT = Path.home() / "Library/Application Support" / "ConcentricStudy" / "environment_compliance"
DEFAULT_MIRROR_LOG = AUTOMATION_ROOT / "environment_answer_compliance_log.jsonl"

ALLOWED_STATUS = {"pass", "fail", "relaxed"}
ALLOWED_ANSWER_MODE = {"environment_specific", "abstract_relaxed"}
ALLOWED_NON_REGRESSION = {
    "not_applicable",
    "core enhancement with non-regression evidence",
    "isolated experimental branch to avoid weakening the core",
}


def _load_template(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _split_list(values: list[str] | None) -> list[str]:
    if not values:
        return []
    out: list[str] = []
    for value in values:
        for part in value.split("||"):
            item = part.strip()
            if item:
                out.append(item)
    return out


def build_entry(args: argparse.Namespace) -> dict[str, Any]:
    template = _load_template(Path(args.template))
    entry = dict(template)
    entry["timestamp_utc"] = datetime.now(timezone.utc).isoformat()
    entry["task_summary"] = args.task_summary
    entry["system_of_interest"] = args.system_of_interest
    entry["local_environment"] = {
        "machine": args.machine,
        "runtime": args.runtime,
        "repo": args.repo,
        "apps": _split_list(args.apps),
    }
    entry["repo_specific_evidence"] = _split_list(args.repo_specific_evidence)
    entry["stakeholder_objective"] = args.stakeholder_objective
    entry["directly_supported"] = _split_list(args.directly_supported)
    entry["inferred"] = _split_list(args.inferred)
    entry["unknown"] = _split_list(args.unknown)
    entry["answer_mode"] = args.answer_mode
    entry["status"] = args.status
    entry["failure_reasons"] = _split_list(args.failure_reasons)
    entry["non_regression_classification"] = args.non_regression_classification
    entry["notes"] = args.notes or ""
    validate_entry(entry)
    return entry


def validate_entry(entry: dict[str, Any]) -> None:
    if entry["status"] not in ALLOWED_STATUS:
        raise ValueError(f"invalid status: {entry['status']}")
    if entry["answer_mode"] not in ALLOWED_ANSWER_MODE:
        raise ValueError(f"invalid answer mode: {entry['answer_mode']}")
    if entry["non_regression_classification"] not in ALLOWED_NON_REGRESSION:
        raise ValueError(
            f"invalid non-regression classification: {entry['non_regression_classification']}"
        )
    if not entry["task_summary"].strip():
        raise ValueError("task_summary is required")
    if not entry["system_of_interest"].strip():
        raise ValueError("system_of_interest is required")
    if not entry["stakeholder_objective"].strip():
        raise ValueError("stakeholder_objective is required")
    if entry["status"] == "pass" and not entry["directly_supported"] and not entry["inferred"]:
        raise ValueError("pass entries require directly_supported or inferred evidence")
    if entry["status"] in {"fail", "relaxed"} and not entry["failure_reasons"]:
        raise ValueError("fail/relaxed entries require failure_reasons")


def _append_one(entry: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=True) + "\n")


def append_entry(entry: dict[str, Any], log_path: Path, mirror_log_path: Path | None = None) -> None:
    _append_one(entry, log_path)
    if mirror_log_path and mirror_log_path != log_path:
        _append_one(entry, mirror_log_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Append an environment-justification compliance entry.")
    parser.add_argument("--log", default=str(DEFAULT_LOG))
    parser.add_argument("--mirror-log", default=str(DEFAULT_MIRROR_LOG))
    parser.add_argument("--no-mirror", action="store_true")
    parser.add_argument("--template", default=str(DEFAULT_TEMPLATE))
    parser.add_argument("--task-summary", required=True)
    parser.add_argument("--system-of-interest", required=True)
    parser.add_argument("--machine", default="")
    parser.add_argument("--runtime", default="")
    parser.add_argument("--repo", default="")
    parser.add_argument("--apps", action="append")
    parser.add_argument("--repo-specific-evidence", action="append")
    parser.add_argument("--stakeholder-objective", required=True)
    parser.add_argument("--directly-supported", action="append")
    parser.add_argument("--inferred", action="append")
    parser.add_argument("--unknown", action="append")
    parser.add_argument("--answer-mode", default="environment_specific")
    parser.add_argument("--status", default="pass")
    parser.add_argument("--failure-reasons", action="append")
    parser.add_argument("--non-regression-classification", default="not_applicable")
    parser.add_argument("--notes", default="")
    parser.add_argument("--print-entry", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    entry = build_entry(args)
    mirror_path = None if args.no_mirror else Path(args.mirror_log)
    append_entry(entry, Path(args.log), mirror_path)
    if args.print_entry:
        print(json.dumps(entry, indent=2))
    else:
        print(Path(args.log))
        if mirror_path:
            print(mirror_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
