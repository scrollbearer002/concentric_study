#!/usr/bin/env python3
"""Build VerificationGate calibration artifacts.

This tool now supports the full first-pass human calibration workflow:

1. export archived verification artifacts into review-ready candidate records
2. generate blinded review packets for independent human rating
3. support dual-rater plus adjudication ground truth
4. compute both human-human and gate-human agreement metrics

The method follows evaluator-calibration literature rather than ad hoc manual
inspection: use blinded human labels first, then compare the gate to an
adjudicated or otherwise effective human ground truth.
"""
from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from statistics import mean
from typing import Any

ROOT = Path(__file__).resolve().parents[4]
RUNS_DIR = ROOT / "operator" / "cre" / "runs"
UNDERSTANDING_DIR = ROOT / "operator" / "cre" / "project_understanding"
ARTIFACTS_DIR = UNDERSTANDING_DIR / "artifacts"
OUTPUT_JSONL = ARTIFACTS_DIR / "verification_calibration_candidates.jsonl"
OUTPUT_JSON = ARTIFACTS_DIR / "verification_calibration_report.json"
PACKETS_DIR = ARTIFACTS_DIR / "verification_review_packets"

EXTERNAL_REFS = [
    "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena",
    "Judge's Verdict: A Comprehensive Analysis of LLM Judge Capability Through Human Agreement",
    "Inter-Coder Agreement for Computational Linguistics",
    "WebVoyager",
    "Multimodal Auto Validation For Self-Refinement in Web Agents",
]


@dataclass
class HumanConstraintLabel:
    description: str
    satisfied: bool | None = None
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "description": self.description,
            "satisfied": self.satisfied,
            "notes": self.notes,
        }


@dataclass
class HumanVerificationLabel:
    overall_passed: bool | None = None
    overall_verdict: str = ""
    notes: str = ""
    rater_id: str = ""
    adjudicated: bool = False
    constraint_labels: list[HumanConstraintLabel] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "overall_passed": self.overall_passed,
            "overall_verdict": self.overall_verdict,
            "notes": self.notes,
            "rater_id": self.rater_id,
            "adjudicated": self.adjudicated,
            "constraint_labels": [label.to_dict() for label in self.constraint_labels],
        }


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def blank_human_label() -> dict[str, Any]:
    return HumanVerificationLabel().to_dict()


def blank_human_review() -> dict[str, Any]:
    return {
        "blind_review_required": True,
        "labels": [],
        "adjudicated_label": blank_human_label(),
        "adjudication_notes": "",
    }


def iter_verification_artifacts(runs_dir: Path) -> list[Path]:
    artifacts: list[Path] = []
    for run_dir in sorted(path for path in runs_dir.iterdir() if path.is_dir()):
        verification_dir = run_dir / "verification"
        if not verification_dir.exists():
            continue
        artifacts.extend(sorted(verification_dir.glob("verification_*.json")))
    return artifacts


def verification_iteration_for(path: Path) -> int:
    stem = path.stem
    suffix = stem.rsplit("_", 1)[-1]
    try:
        return int(suffix)
    except ValueError:
        return 0


def build_review_record(verification_path: Path) -> dict[str, Any]:
    run_dir = verification_path.parents[1]
    manifest_path = run_dir / "manifest.json"
    manifest = read_json(manifest_path)
    verification = read_json(verification_path)
    outcome_semantics = manifest.get("outcome_semantics", {})
    final_verification = outcome_semantics.get("final_verification", {})
    constraints = verification.get("constraints", [])

    return {
        "record_id": f"{manifest.get('run_id', run_dir.name)}:{verification_path.stem}",
        "run_id": manifest.get("run_id", run_dir.name),
        "task_id": manifest.get("task_id", ""),
        "task_description": manifest.get("task_description", ""),
        "run_outcome": manifest.get("outcome", "unknown"),
        "task_result": outcome_semantics.get("task_result", "unknown"),
        "final_verification_status": final_verification.get(
            "status",
            "passed" if verification.get("passed") else "failed",
        ),
        "manifest_path": str(manifest_path),
        "verification_artifact_path": str(verification_path),
        "verification_iteration": verification.get(
            "iteration",
            verification_iteration_for(verification_path),
        ),
        "verification_timestamp": verification.get("timestamp", ""),
        "screenshot_path": verification.get("screenshot_path", ""),
        "reference_paths": verification.get("reference_paths", []),
        "gate_passed": bool(verification.get("passed", False)),
        "gate_score": float(verification.get("score", 0.0)),
        "gate_verdict": verification.get("verdict", ""),
        "gate_deficiencies": verification.get("deficiencies", []),
        "gate_constraints": constraints,
        "gate_constraint_count": len(constraints),
        "gate_deficiency_count": len(verification.get("deficiencies", [])),
        "human_review": blank_human_review(),
        "human_label": blank_human_label(),  # legacy single-rater compatibility
    }


def build_candidate_records(runs_dir: Path = RUNS_DIR, limit: int | None = None) -> list[dict[str, Any]]:
    artifacts = iter_verification_artifacts(runs_dir)
    if limit is not None:
        artifacts = artifacts[: max(limit, 0)]
    return [build_review_record(path) for path in artifacts]


def mean_or_none(values: list[float]) -> float | None:
    if not values:
        return None
    return round(mean(values), 4)


def safe_ratio(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return round(numerator / denominator, 4)


def cohen_kappa(predicted: list[bool], human: list[bool]) -> float | None:
    if not predicted or len(predicted) != len(human):
        return None

    n = len(predicted)
    observed = sum(1 for pred, gold in zip(predicted, human) if pred == gold) / n
    pred_true = sum(1 for pred in predicted if pred) / n
    pred_false = 1.0 - pred_true
    human_true = sum(1 for gold in human if gold) / n
    human_false = 1.0 - human_true
    expected = (pred_true * human_true) + (pred_false * human_false)
    if expected == 1.0:
        return 1.0 if observed == 1.0 else 0.0
    return round((observed - expected) / (1.0 - expected), 4)


def binary_summary(predicted: list[bool], human: list[bool]) -> dict[str, Any]:
    tp = sum(1 for pred, gold in zip(predicted, human) if pred and gold)
    tn = sum(1 for pred, gold in zip(predicted, human) if not pred and not gold)
    fp = sum(1 for pred, gold in zip(predicted, human) if pred and not gold)
    fn = sum(1 for pred, gold in zip(predicted, human) if not pred and gold)
    total = len(predicted)
    return {
        "compared": total,
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "accuracy": safe_ratio(tp + tn, total),
        "precision": safe_ratio(tp, tp + fp),
        "recall": safe_ratio(tp, tp + fn),
        "f1": safe_ratio(2 * tp, (2 * tp) + fp + fn),
        "observed_agreement": safe_ratio(tp + tn, total),
        "cohen_kappa": cohen_kappa(predicted, human),
    }


def normalize_completed_label(label: Any) -> dict[str, Any] | None:
    if not isinstance(label, dict):
        return None
    overall_passed = label.get("overall_passed")
    if not isinstance(overall_passed, bool):
        return None
    normalized = dict(label)
    normalized.setdefault("overall_verdict", "")
    normalized.setdefault("notes", "")
    normalized.setdefault("rater_id", "")
    normalized.setdefault("adjudicated", False)
    normalized.setdefault("constraint_labels", [])
    return normalized


def completed_human_labels(record: dict[str, Any]) -> list[dict[str, Any]]:
    labels: list[dict[str, Any]] = []
    human_review = record.get("human_review")
    if isinstance(human_review, dict):
        for label in human_review.get("labels", []):
            normalized = normalize_completed_label(label)
            if normalized is not None:
                labels.append(normalized)

    if labels:
        return labels

    normalized_legacy = normalize_completed_label(record.get("human_label"))
    return [normalized_legacy] if normalized_legacy is not None else []


def effective_human_label(record: dict[str, Any]) -> tuple[dict[str, Any] | None, str]:
    human_review = record.get("human_review")
    if isinstance(human_review, dict):
        adjudicated = normalize_completed_label(human_review.get("adjudicated_label"))
        if adjudicated is not None:
            adjudicated["adjudicated"] = True
            return adjudicated, "adjudicated"

    labels = completed_human_labels(record)
    if not labels:
        return None, "missing"
    if len(labels) == 1:
        return labels[0], "single_rater"

    passes = {label["overall_passed"] for label in labels}
    if len(passes) == 1:
        consensus = dict(labels[0])
        consensus["notes"] = "Consensus across multiple human raters."
        return consensus, "multi_rater_consensus"

    return None, "pending_adjudication"


def review_state_for(record: dict[str, Any]) -> str:
    label, source = effective_human_label(record)
    if label is not None:
        return source

    labels = completed_human_labels(record)
    if not labels:
        return "unlabeled"
    return "pending_adjudication"


def summarize_review_states(records: list[dict[str, Any]]) -> dict[str, int]:
    states = {
        "unlabeled": 0,
        "single_rater": 0,
        "multi_rater_consensus": 0,
        "pending_adjudication": 0,
        "adjudicated": 0,
    }
    for record in records:
        state = review_state_for(record)
        states[state] = states.get(state, 0) + 1
    return states


def summarize_human_inter_rater(records: list[dict[str, Any]]) -> dict[str, Any]:
    predicted: list[bool] = []
    human: list[bool] = []
    disagreements: list[dict[str, Any]] = []

    for record in records:
        labels = completed_human_labels(record)
        if len(labels) < 2:
            continue
        first, second = labels[0], labels[1]
        first_passed = bool(first["overall_passed"])
        second_passed = bool(second["overall_passed"])
        predicted.append(first_passed)
        human.append(second_passed)
        if first_passed != second_passed:
            disagreements.append(
                {
                    "record_id": record.get("record_id", ""),
                    "first_rater": first.get("rater_id", ""),
                    "second_rater": second.get("rater_id", ""),
                    "first_overall_passed": first_passed,
                    "second_overall_passed": second_passed,
                }
            )

    if not predicted:
        return {"compared": 0, "disagreements": []}

    return {**binary_summary(predicted, human), "disagreements": disagreements}


def iter_constraint_pairs(
    record: dict[str, Any],
    human_label: dict[str, Any],
) -> tuple[list[bool], list[bool], int]:
    gate_constraints = record.get("gate_constraints", [])
    gate_by_description = {
        str(constraint.get("description", "")).strip().lower(): bool(constraint.get("satisfied", False))
        for constraint in gate_constraints
        if str(constraint.get("description", "")).strip()
    }

    predicted: list[bool] = []
    human: list[bool] = []
    unmatched = 0
    for label in human_label.get("constraint_labels", []):
        description = str(label.get("description", "")).strip().lower()
        satisfied = label.get("satisfied")
        if not description or not isinstance(satisfied, bool):
            continue
        if description not in gate_by_description:
            unmatched += 1
            continue
        predicted.append(gate_by_description[description])
        human.append(satisfied)
    return predicted, human, unmatched


def summarize_calibration(records: list[dict[str, Any]], dataset_path: str = "") -> dict[str, Any]:
    labeled_records = []
    predicted: list[bool] = []
    human: list[bool] = []
    disagreements: list[dict[str, Any]] = []
    score_when_human_pass: list[float] = []
    score_when_human_fail: list[float] = []
    constraint_predicted: list[bool] = []
    constraint_human: list[bool] = []
    unmatched_constraint_labels = 0
    source_counts: dict[str, int] = {}

    for record in records:
        effective_label, source = effective_human_label(record)
        source_counts[source] = source_counts.get(source, 0) + 1
        if effective_label is None:
            continue

        labeled_records.append(record)
        gate_passed = bool(record.get("gate_passed", False))
        gate_score = float(record.get("gate_score", 0.0))
        human_passed = bool(effective_label["overall_passed"])
        predicted.append(gate_passed)
        human.append(human_passed)

        if human_passed:
            score_when_human_pass.append(gate_score)
        else:
            score_when_human_fail.append(gate_score)

        if gate_passed != human_passed:
            disagreements.append(
                {
                    "record_id": record.get("record_id", ""),
                    "gate_passed": gate_passed,
                    "human_passed": human_passed,
                    "gate_score": gate_score,
                    "task_id": record.get("task_id", ""),
                    "human_ground_truth_source": source,
                }
            )

        pair_predicted, pair_human, unmatched = iter_constraint_pairs(record, effective_label)
        constraint_predicted.extend(pair_predicted)
        constraint_human.extend(pair_human)
        unmatched_constraint_labels += unmatched

    summary = {
        "mode": "agreement_report",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "dataset_path": dataset_path,
        "external_refs": EXTERNAL_REFS,
        "total_records": len(records),
        "labeled_records": len(labeled_records),
        "unlabeled_records": len(records) - len(labeled_records),
        "review_state_counts": summarize_review_states(records),
        "ground_truth_source_counts": source_counts,
        "pass_fail_counts": {
            "gate_passed": sum(1 for record in records if record.get("gate_passed")),
            "gate_failed": sum(1 for record in records if not record.get("gate_passed")),
        },
        "score_separation": {
            "mean_gate_score_when_human_pass": mean_or_none(score_when_human_pass),
            "mean_gate_score_when_human_fail": mean_or_none(score_when_human_fail),
        },
        "overall_metrics": binary_summary(predicted, human) if labeled_records else None,
        "constraint_metrics": (
            {
                **binary_summary(constraint_predicted, constraint_human),
                "unmatched_human_constraint_labels": unmatched_constraint_labels,
            }
            if constraint_predicted else {
                "compared": 0,
                "unmatched_human_constraint_labels": unmatched_constraint_labels,
            }
        ),
        "human_inter_rater": summarize_human_inter_rater(records),
        "disagreements": disagreements,
    }
    return summary


def packet_stem(record_id: str) -> str:
    return (
        record_id.replace(":", "__")
        .replace("/", "_")
        .replace(" ", "_")
    )


def blind_review_template_json() -> str:
    template = HumanVerificationLabel(
        overall_passed=None,
        overall_verdict="",
        notes="",
        rater_id="rater_a",
        adjudicated=False,
    ).to_dict()
    return json.dumps(template, indent=2)


def render_blind_review_packet(record: dict[str, Any]) -> str:
    references = record.get("reference_paths", [])
    reference_block = "\n".join(f"- `{path}`" for path in references) if references else "- None"
    return "\n".join(
        [
            f"# Blind Review Packet: {record.get('record_id', '')}",
            "",
            "Do not consult the gate verdict, gate score, deficiencies, or constraint list before rating.",
            "This packet is for independent initial human judgment.",
            "",
            "## Task",
            f"- Task ID: `{record.get('task_id', '')}`",
            f"- Task Description: {record.get('task_description', '')}",
            "",
            "## Evidence",
            f"- Screenshot: `{record.get('screenshot_path', '')}`",
            "- Reference Images:",
            reference_block,
            "",
            "## Questions",
            "1. Does the screenshot satisfy the task description as written?",
            "2. If not, what is missing or wrong?",
            "3. If the judgment is ambiguous, explain why.",
            "",
            "## Label Template",
            "```json",
            blind_review_template_json(),
            "```",
        ]
    ) + "\n"


def render_adjudication_packet(record: dict[str, Any]) -> str:
    constraints = record.get("gate_constraints", [])
    deficiencies = record.get("gate_deficiencies", [])
    labels = completed_human_labels(record)
    human_label_lines = []
    if not labels:
        human_label_lines.append("- No completed human labels yet.")
    else:
        for label in labels:
            human_label_lines.extend(
                [
                    f"- Rater `{label.get('rater_id', '') or '<unset>'}`: overall_passed={label.get('overall_passed')}",
                    f"  Verdict: {label.get('overall_verdict', '')}",
                    f"  Notes: {label.get('notes', '')}",
                ]
            )

    constraint_lines = [
        f"- [{'PASS' if constraint.get('satisfied') else 'FAIL'}] {constraint.get('description', '')}"
        for constraint in constraints
    ] or ["- None"]
    deficiency_lines = [f"- {item}" for item in deficiencies] or ["- None"]

    return "\n".join(
        [
            f"# Adjudication Packet: {record.get('record_id', '')}",
            "",
            "Use this packet only after independent blind labels exist or disagreement requires resolution.",
            "",
            "## Task",
            f"- Task ID: `{record.get('task_id', '')}`",
            f"- Task Description: {record.get('task_description', '')}",
            "",
            "## Evidence",
            f"- Screenshot: `{record.get('screenshot_path', '')}`",
            "",
            "## Independent Human Labels",
            *human_label_lines,
            "",
            "## Gate Verdict",
            f"- Gate Passed: {record.get('gate_passed')}",
            f"- Gate Score: {record.get('gate_score')}",
            f"- Gate Verdict: {record.get('gate_verdict', '')}",
            "",
            "## Gate Constraints",
            *constraint_lines,
            "",
            "## Gate Deficiencies",
            *deficiency_lines,
            "",
            "## Adjudicated Label Template",
            "```json",
            json.dumps(
                HumanVerificationLabel(
                    overall_passed=None,
                    overall_verdict="",
                    notes="",
                    rater_id="adjudicator",
                    adjudicated=True,
                ).to_dict(),
                indent=2,
            ),
            "```",
        ]
    ) + "\n"


def write_review_packets(records: list[dict[str, Any]], packets_dir: Path) -> dict[str, str]:
    blind_dir = packets_dir / "blind"
    adjudication_dir = packets_dir / "adjudication"
    blind_dir.mkdir(parents=True, exist_ok=True)
    adjudication_dir.mkdir(parents=True, exist_ok=True)

    index_lines = [
        "# Verification Review Packet Index",
        "",
        "This directory contains blinded initial-review packets and adjudication packets.",
        "",
    ]

    for record in records:
        stem = packet_stem(record.get("record_id", "record"))
        blind_path = blind_dir / f"{stem}.md"
        blind_template_path = blind_dir / f"{stem}.label_template.json"
        adjudication_path = adjudication_dir / f"{stem}.md"

        blind_path.write_text(render_blind_review_packet(record), encoding="utf-8")
        blind_template_path.write_text(blind_review_template_json() + "\n", encoding="utf-8")
        adjudication_path.write_text(render_adjudication_packet(record), encoding="utf-8")

        index_lines.extend(
            [
                f"- `{record.get('record_id', '')}`",
                f"  - blind: `{blind_path}`",
                f"  - blind label template: `{blind_template_path}`",
                f"  - adjudication: `{adjudication_path}`",
            ]
        )

    index_path = packets_dir / "INDEX.md"
    index_path.write_text("\n".join(index_lines) + "\n", encoding="utf-8")
    return {
        "blind_dir": str(blind_dir),
        "adjudication_dir": str(adjudication_dir),
        "index_path": str(index_path),
    }


def build_candidate_summary(records: list[dict[str, Any]], runs_dir: Path) -> dict[str, Any]:
    pass_count = sum(1 for record in records if record.get("gate_passed"))
    fail_count = len(records) - pass_count
    return {
        "mode": "candidate_census",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "runs_dir": str(runs_dir),
        "external_refs": EXTERNAL_REFS,
        "total_records": len(records),
        "gate_passed": pass_count,
        "gate_failed": fail_count,
        "mean_gate_score": mean_or_none([float(record.get("gate_score", 0.0)) for record in records]),
        "review_state_counts": summarize_review_states(records),
        "records_pending_human_label": sum(
            1 for record in records if review_state_for(record) == "unlabeled"
        ),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs-dir", type=Path, default=RUNS_DIR)
    parser.add_argument("--build-candidates", action="store_true")
    parser.add_argument("--dataset", type=Path, help="Annotated calibration JSONL to score.")
    parser.add_argument("--output-jsonl", type=Path, default=OUTPUT_JSONL)
    parser.add_argument("--output-json", type=Path, default=OUTPUT_JSON)
    parser.add_argument("--write-review-packets", action="store_true")
    parser.add_argument("--packets-dir", type=Path, default=PACKETS_DIR)
    parser.add_argument("--limit", type=int, default=None)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    build_candidates = args.build_candidates or args.dataset is None
    records: list[dict[str, Any]]

    if build_candidates:
        records = build_candidate_records(args.runs_dir, limit=args.limit)
        write_jsonl(args.output_jsonl, records)
        if args.write_review_packets:
            write_review_packets(records, args.packets_dir)
        candidate_summary = build_candidate_summary(records, args.runs_dir)
        if args.dataset is None:
            write_json(args.output_json, candidate_summary)
            print(json.dumps(candidate_summary, indent=2))
            return 0

    dataset_path = args.dataset or args.output_jsonl
    records = load_jsonl(dataset_path)
    if args.write_review_packets:
        write_review_packets(records, args.packets_dir)
    summary = summarize_calibration(records, dataset_path=str(dataset_path))
    write_json(args.output_json, summary)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
