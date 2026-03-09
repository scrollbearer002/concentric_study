#!/usr/bin/env python3
"""VerificationGate calibration tooling regression tests."""

from __future__ import annotations

import json
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent / "project_understanding" / "tools"
sys.path.insert(0, str(TOOLS_DIR))

from build_verification_calibration import (  # type: ignore
    build_candidate_records,
    completed_human_labels,
    effective_human_label,
    render_adjudication_packet,
    render_blind_review_packet,
    summarize_calibration,
    write_review_packets,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def test_build_candidate_records_exports_review_packets(tmp_path: Path) -> None:
    runs_dir = tmp_path / "runs"
    run_dir = runs_dir / "run123"
    verification_dir = run_dir / "verification"

    _write_json(
        run_dir / "manifest.json",
        {
            "run_id": "run123",
            "task_id": "TASK_ALPHA",
            "task_description": "Click the visible continue button.",
            "outcome": "success",
            "outcome_semantics": {
                "task_result": "accepted",
                "final_verification": {"status": "passed"},
            },
        },
    )
    _write_json(
        verification_dir / "verification_01.json",
        {
            "passed": True,
            "score": 1.0,
            "verdict": "PASSED (100%): Output meets the requested standard.",
            "constraints": [
                {
                    "description": "Status text changed to clicked",
                    "category": "research",
                    "satisfied": True,
                    "critique": "Visible in screenshot.",
                }
            ],
            "deficiencies": [],
            "screenshot_path": "/tmp/run123/verify_01.png",
            "reference_paths": [],
            "iteration": 1,
            "timestamp": "2026-03-05T00:00:00Z",
        },
    )

    records = build_candidate_records(runs_dir)

    assert len(records) == 1
    record = records[0]
    assert record["record_id"] == "run123:verification_01"
    assert record["task_id"] == "TASK_ALPHA"
    assert record["task_result"] == "accepted"
    assert record["final_verification_status"] == "passed"
    assert record["gate_passed"] is True
    assert record["gate_constraint_count"] == 1
    assert record["human_review"]["labels"] == []
    assert record["human_review"]["blind_review_required"] is True
    assert record["human_review"]["adjudicated_label"]["overall_passed"] is None
    assert record["human_label"]["overall_passed"] is None


def test_effective_human_label_prefers_adjudicated_then_consensus_then_single() -> None:
    record = {
        "human_review": {
            "labels": [
                {"rater_id": "a", "overall_passed": True, "constraint_labels": []},
                {"rater_id": "b", "overall_passed": False, "constraint_labels": []},
            ],
            "adjudicated_label": {"rater_id": "adj", "overall_passed": True, "adjudicated": True},
        }
    }

    label, source = effective_human_label(record)
    assert source == "adjudicated"
    assert label["overall_passed"] is True

    record = {
        "human_review": {
            "labels": [
                {"rater_id": "a", "overall_passed": False, "constraint_labels": []},
                {"rater_id": "b", "overall_passed": False, "constraint_labels": []},
            ],
            "adjudicated_label": {"overall_passed": None},
        }
    }
    label, source = effective_human_label(record)
    assert source == "multi_rater_consensus"
    assert label["overall_passed"] is False

    record = {
        "human_review": {
            "labels": [
                {"rater_id": "a", "overall_passed": True, "constraint_labels": []},
            ],
            "adjudicated_label": {"overall_passed": None},
        }
    }
    label, source = effective_human_label(record)
    assert source == "single_rater"
    assert label["overall_passed"] is True


def test_summarize_calibration_scores_gate_vs_effective_human_ground_truth() -> None:
    records = [
        {
            "record_id": "r1",
            "task_id": "A",
            "gate_passed": True,
            "gate_score": 0.95,
            "gate_constraints": [
                {"description": "Button clicked", "satisfied": True},
                {"description": "Status updated", "satisfied": True},
            ],
            "human_review": {
                "labels": [
                    {
                        "rater_id": "r1a",
                        "overall_passed": True,
                        "constraint_labels": [
                            {"description": "Button clicked", "satisfied": True},
                            {"description": "Status updated", "satisfied": True},
                        ],
                    },
                    {
                        "rater_id": "r1b",
                        "overall_passed": True,
                        "constraint_labels": [
                            {"description": "Button clicked", "satisfied": True},
                            {"description": "Status updated", "satisfied": True},
                        ],
                    },
                ],
                "adjudicated_label": {"overall_passed": None},
            },
        },
        {
            "record_id": "r2",
            "task_id": "B",
            "gate_passed": False,
            "gate_score": 0.2,
            "gate_constraints": [
                {"description": "Drawing visible", "satisfied": False},
                {"description": "Subject recognizable", "satisfied": False},
            ],
            "human_review": {
                "labels": [
                    {
                        "rater_id": "r2a",
                        "overall_passed": False,
                        "constraint_labels": [
                            {"description": "Drawing visible", "satisfied": False},
                            {"description": "Subject recognizable", "satisfied": False},
                        ],
                    },
                    {
                        "rater_id": "r2b",
                        "overall_passed": False,
                        "constraint_labels": [
                            {"description": "Drawing visible", "satisfied": False},
                            {"description": "Subject recognizable", "satisfied": False},
                        ],
                    },
                ],
                "adjudicated_label": {"overall_passed": None},
            },
        },
        {
            "record_id": "r3",
            "task_id": "C",
            "gate_passed": True,
            "gate_score": 0.81,
            "gate_constraints": [
                {"description": "Layout correct", "satisfied": True},
            ],
            "human_review": {
                "labels": [
                    {"rater_id": "r3a", "overall_passed": False, "constraint_labels": []},
                    {"rater_id": "r3b", "overall_passed": True, "constraint_labels": []},
                ],
                "adjudicated_label": {
                    "rater_id": "adj",
                    "overall_passed": False,
                    "adjudicated": True,
                    "constraint_labels": [
                        {"description": "Layout correct", "satisfied": False},
                    ],
                },
            },
        },
        {
            "record_id": "r4",
            "task_id": "D",
            "gate_passed": False,
            "gate_score": 0.1,
            "gate_constraints": [
                {"description": "Form submitted", "satisfied": False},
            ],
            "human_review": {
                "labels": [
                    {"rater_id": "r4a", "overall_passed": False, "constraint_labels": []},
                    {"rater_id": "r4b", "overall_passed": False, "constraint_labels": []},
                ],
                "adjudicated_label": {"overall_passed": None},
            },
        },
    ]

    summary = summarize_calibration(records, dataset_path="synthetic.jsonl")

    assert summary["total_records"] == 4
    assert summary["labeled_records"] == 4
    assert summary["review_state_counts"]["adjudicated"] == 1
    assert summary["review_state_counts"]["multi_rater_consensus"] == 3
    assert summary["ground_truth_source_counts"]["adjudicated"] == 1
    assert summary["ground_truth_source_counts"]["multi_rater_consensus"] == 3
    assert summary["overall_metrics"]["tp"] == 1
    assert summary["overall_metrics"]["tn"] == 2
    assert summary["overall_metrics"]["fp"] == 1
    assert summary["overall_metrics"]["fn"] == 0
    assert summary["overall_metrics"]["accuracy"] == 0.75
    assert summary["overall_metrics"]["precision"] == 0.5
    assert summary["overall_metrics"]["recall"] == 1.0
    assert summary["overall_metrics"]["f1"] == 0.6667
    assert summary["constraint_metrics"]["compared"] == 5
    assert summary["human_inter_rater"]["compared"] == 4
    assert len(summary["human_inter_rater"]["disagreements"]) == 1
    assert summary["disagreements"][0]["record_id"] == "r3"


def test_completed_human_labels_falls_back_to_legacy_single_label() -> None:
    record = {
        "human_label": {"rater_id": "legacy", "overall_passed": True, "constraint_labels": []}
    }

    labels = completed_human_labels(record)

    assert len(labels) == 1
    assert labels[0]["rater_id"] == "legacy"


def test_blind_and_adjudication_packets_separate_gate_exposure(tmp_path: Path) -> None:
    record = {
        "record_id": "run123:verification_01",
        "task_id": "TASK_ALPHA",
        "task_description": "Click the visible continue button.",
        "screenshot_path": "/tmp/run123/verify_01.png",
        "reference_paths": [],
        "gate_passed": True,
        "gate_score": 0.95,
        "gate_verdict": "PASSED",
        "gate_constraints": [
            {"description": "Status changed", "satisfied": True},
        ],
        "gate_deficiencies": [],
        "human_review": {
            "labels": [{"rater_id": "rater_a", "overall_passed": True, "constraint_labels": []}],
            "adjudicated_label": {"overall_passed": None},
        },
    }

    blind = render_blind_review_packet(record)
    adjudication = render_adjudication_packet(record)
    assert "Gate Score" not in blind
    assert "Do not consult the gate verdict" in blind
    assert "Gate Score" in adjudication
    assert "Status changed" in adjudication

    packet_info = write_review_packets([record], tmp_path / "packets")
    blind_path = Path(packet_info["blind_dir"]) / "run123__verification_01.md"
    adjudication_path = Path(packet_info["adjudication_dir"]) / "run123__verification_01.md"
    template_path = Path(packet_info["blind_dir"]) / "run123__verification_01.label_template.json"

    assert blind_path.exists()
    assert adjudication_path.exists()
    assert template_path.exists()


def test_summarize_calibration_tolerates_unlabeled_records() -> None:
    records = [
        {
            "record_id": "r1",
            "gate_passed": True,
            "gate_score": 0.9,
            "gate_constraints": [],
            "human_review": {
                "labels": [],
                "adjudicated_label": {"overall_passed": None},
            },
        }
    ]

    summary = summarize_calibration(records)

    assert summary["labeled_records"] == 0
    assert summary["overall_metrics"] is None
    assert summary["constraint_metrics"]["compared"] == 0
    assert summary["unlabeled_records"] == 1
