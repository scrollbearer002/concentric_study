#!/usr/bin/env python3
"""Build Section 5 dynamic execution architecture artifacts.

This tool recovers an execution-centered architectural view from observed run
artifacts rather than from imports alone. The method follows the running-system
reconstruction line from SEI's "Discovering Architectures from Running Systems"
and the dynamic-analysis line summarized by Cornelissen et al.: use runtime
traces to recover interaction structure that static dependencies cannot show.
"""
from __future__ import annotations

import csv
import json
import time
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median
from typing import Any

ROOT = Path(__file__).resolve().parents[4]
RUNS_DIR = ROOT / "operator" / "cre" / "runs"
UNDERSTANDING_DIR = ROOT / "operator" / "cre" / "project_understanding"
ARTIFACTS_DIR = UNDERSTANDING_DIR / "artifacts"
OUTPUT_JSON = ARTIFACTS_DIR / "dynamic_execution_architecture.json"
OUTPUT_CSV = ARTIFACTS_DIR / "dynamic_transition_matrix.csv"
OUTPUT_MMD = ARTIFACTS_DIR / "dynamic_execution_overview.mmd"

EXTERNAL_REFS = [
    "Discovering Architectures from Running Systems",
    "Dynamic Design Analysis to Support Architecture Design",
    "A Systematic Survey of Program Comprehension through Dynamic Analysis",
    "ISO/IEC/IEEE 42010",
]

PHASE_MAP = {
    "a11y_passive_snapshot": "observe",
    "metacognitive_audit": "audit",
    "go_to_url": "bootstrap",
    "magma_open_url": "bootstrap",
    "magma_navigate_app": "bootstrap",
    "magma_click_new_canvas": "bootstrap",
    "magma_click_landscape": "bootstrap",
    "clear_canvas": "reset_prepare",
    "keystroke": "reset_prepare",
    "sleep": "reset_prepare",
    "refresh_canvas_center": "reset_prepare",
    "set_stroke_color": "configure",
    "click": "configure",
    "draw_concentric_triangles": "produce",
    "draw_circle": "produce",
    "drag_shape": "produce",
    "draw_eiffel_landscape": "produce",
    "draw_eiffel_tower": "produce",
    "draw_path": "produce",
    "bmw_skeleton": "produce",
    "bmw_form_blocking": "produce",
    "bmw_mechanical": "produce",
    "bmw_lighting": "produce",
    "bmw_final": "produce",
    "magma_draw_bmw_e30": "produce",
    "verify_success": "verify",
}

PHASE_NODE_IDS = {
    "observe": "Observe",
    "bootstrap": "Bootstrap",
    "reset_prepare": "Reset",
    "configure": "Configure",
    "produce": "Produce",
    "verify": "Verify",
    "audit": "Audit",
    "other": "Other",
}

PHASE_NODE_LABELS = {
    "observe": "Observation Plane",
    "bootstrap": "Bootstrap Plane",
    "reset_prepare": "Reset / Prepare Plane",
    "configure": "Configure Plane",
    "produce": "Production Plane",
    "verify": "Verification Plane",
    "audit": "Audit Plane",
    "other": "Other / Unclassified",
}

CANONICAL_RUNTIME_COMPONENTS = [
    {
        "component": "observation_plane",
        "actions": ["a11y_passive_snapshot"],
        "meaning": "Passive state capture before action selection, concentrated in universal runs.",
    },
    {
        "component": "bootstrap_plane",
        "actions": [
            "go_to_url",
            "magma_open_url",
            "magma_navigate_app",
            "magma_click_new_canvas",
            "magma_click_landscape",
        ],
        "meaning": "Navigation and environment setup before artifact production begins.",
    },
    {
        "component": "reset_prepare_plane",
        "actions": ["clear_canvas", "keystroke", "sleep", "refresh_canvas_center"],
        "meaning": "Reset, dialog confirmation, timing, and center-refresh control path that dominates enterprise runs.",
    },
    {
        "component": "configure_plane",
        "actions": ["set_stroke_color", "click"],
        "meaning": "Tool and parameter configuration before production actions.",
    },
    {
        "component": "production_plane",
        "actions": [
            "draw_concentric_triangles",
            "draw_circle",
            "drag_shape",
            "draw_eiffel_landscape",
            "draw_eiffel_tower",
            "draw_path",
            "bmw_skeleton",
            "bmw_form_blocking",
            "bmw_mechanical",
            "bmw_lighting",
            "bmw_final",
            "magma_draw_bmw_e30",
        ],
        "meaning": "Artifact-producing actions across Excalidraw, Magma, and Kleki task families.",
    },
    {
        "component": "verification_plane",
        "actions": ["verify_success", "sleep(assertion-backed)", "sleep(trust-skipped)"],
        "meaning": "Explicit or encoded postcondition checks used to decide whether a run should continue or terminate.",
    },
    {
        "component": "audit_plane",
        "actions": ["metacognitive_audit"],
        "meaning": "Terminal explanation-coverage audit used by universal runs as a final self-check.",
    },
]


def phase_for(action_type: str, step: dict[str, Any]) -> str:
    if action_type == "sleep":
        output = step.get("action_result", {}).get("output")
        if output in {"assertion passed", "trust-skipped"}:
            return "verify"
    return PHASE_MAP.get(action_type, "other")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    steps: list[dict[str, Any]] = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                steps.append(json.loads(line))
    return steps


def path_signature(items: list[str], limit: int = 8) -> str:
    if not items:
        return "<empty>"
    return " -> ".join(items[:limit])


def duration_stats(values: list[float]) -> dict[str, float]:
    if not values:
        return {"avg": 0.0, "median": 0.0, "min": 0.0, "max": 0.0}
    return {
        "avg": round(mean(values), 2),
        "median": round(median(values), 2),
        "min": round(min(values), 2),
        "max": round(max(values), 2),
    }


def raw_mode_for(manifest: dict[str, Any]) -> str:
    return manifest.get("agent_config", {}).get("mode") or "unknown"


def execution_family_for(manifest: dict[str, Any], steps: list[dict[str, Any]]) -> str:
    raw_mode = raw_mode_for(manifest)
    if raw_mode != "unknown":
        return raw_mode

    task_id = manifest.get("task_id", "")
    actions = {step.get("action", {}).get("type", "unknown") for step in steps}
    if task_id == "KLEKI_BMW_E30_M3" or any(action.startswith("bmw_") for action in actions):
        return "iterative_art_study"
    return "unknown"


def build_outputs() -> dict[str, Any]:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    run_dirs = sorted([path for path in RUNS_DIR.iterdir() if path.is_dir()])
    complete_runs: list[tuple[Path, Path, Path]] = []
    incomplete_runs: list[str] = []
    for run_dir in run_dirs:
        manifest_path = run_dir / "manifest.json"
        trace_path = run_dir / "trace.jsonl"
        if manifest_path.exists() and trace_path.exists():
            complete_runs.append((run_dir, manifest_path, trace_path))
        else:
            incomplete_runs.append(run_dir.name)

    outcome_counts: Counter[str] = Counter()
    raw_mode_counts: Counter[str] = Counter()
    execution_family_counts: Counter[str] = Counter()
    task_counts: Counter[str] = Counter()
    action_counts: Counter[str] = Counter()
    phase_counts: Counter[str] = Counter()
    transition_counts: Counter[tuple[str, str]] = Counter()
    phase_aware_transition_counts: Counter[tuple[str, str, str, str]] = Counter()
    phase_transition_counts: Counter[tuple[str, str]] = Counter()
    failure_category_counts: Counter[str] = Counter()
    failure_action_counts: Counter[str] = Counter()
    execution_family_path_counts: defaultdict[str, Counter[str]] = defaultdict(Counter)
    task_path_counts: defaultdict[str, Counter[str]] = defaultdict(Counter)
    task_step_counts: defaultdict[str, list[int]] = defaultdict(list)
    step_index_counts: Counter[int] = Counter()
    execution_family_examples: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    failure_examples: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    execution_family_phase_counts: defaultdict[str, Counter[str]] = defaultdict(Counter)
    execution_family_action_counts: defaultdict[str, Counter[str]] = defaultdict(Counter)
    duration_by_execution_family: defaultdict[str, list[float]] = defaultdict(list)
    duration_by_outcome: defaultdict[str, list[float]] = defaultdict(list)
    verification_signals: Counter[str] = Counter()
    outlier_runs: list[dict[str, Any]] = []
    trace_semantics_mismatches: list[dict[str, Any]] = []
    escalation_md_count = 0
    escalation_json_count = 0

    for run_dir, manifest_path, trace_path in complete_runs:
        manifest = read_json(manifest_path)
        steps = read_jsonl(trace_path)
        outcome = manifest.get("outcome", "unknown")
        raw_mode = raw_mode_for(manifest)
        execution_family = execution_family_for(manifest, steps)
        task_id = manifest.get("task_id") or "<empty-task-id>"
        duration_seconds = round(manifest.get("total_duration_ms", 0) / 1000.0, 3)

        outcome_counts[outcome] += 1
        raw_mode_counts[raw_mode] += 1
        execution_family_counts[execution_family] += 1
        task_counts[task_id] += 1
        task_step_counts[task_id].append(len(steps))
        duration_by_execution_family[execution_family].append(duration_seconds)
        duration_by_outcome[outcome].append(duration_seconds)
        if (run_dir / "ESCALATION.md").exists():
            escalation_md_count += 1
        if (run_dir / "ESCALATION.json").exists():
            escalation_json_count += 1

        actions: list[str] = []
        phases: list[str] = []
        failed_steps = 0
        failed_action_types: list[str] = []
        for step in steps:
            action_type = step.get("action", {}).get("type", "unknown")
            phase = phase_for(action_type, step)
            output = step.get("action_result", {}).get("output")
            step_index = step.get("step")

            actions.append(action_type)
            phases.append(phase)
            action_counts[action_type] += 1
            phase_counts[phase] += 1
            execution_family_phase_counts[execution_family][phase] += 1
            execution_family_action_counts[execution_family][action_type] += 1
            if isinstance(step_index, int):
                step_index_counts[step_index] += 1

            if action_type == "verify_success":
                verification_signals["explicit_verify_success_steps"] += 1
            if action_type == "metacognitive_audit":
                verification_signals["metacognitive_audit_steps"] += 1
            if action_type == "sleep" and output == "assertion passed":
                verification_signals["assertion_backed_sleep_steps"] += 1
            if action_type == "sleep" and output == "trust-skipped":
                verification_signals["trust_skipped_sleep_steps"] += 1

            if step.get("action_result", {}).get("success") is False:
                failed_steps += 1
                failed_action_types.append(action_type)
                failure_action_counts[action_type] += 1
                failure_examples[action_type].append(
                    {
                        "run_id": run_dir.name,
                        "task_id": task_id,
                        "error": step.get("action_result", {}).get("error", ""),
                    }
                )

        if manifest.get("failure_category"):
            failure_category_counts[manifest["failure_category"]] += 1

        for from_action, to_action in zip(actions, actions[1:]):
            transition_counts[(from_action, to_action)] += 1
        for from_action, to_action, from_phase, to_phase in zip(actions, actions[1:], phases, phases[1:]):
            phase_aware_transition_counts[(from_action, to_action, from_phase, to_phase)] += 1
        for from_phase, to_phase in zip(phases, phases[1:]):
            phase_transition_counts[(from_phase, to_phase)] += 1

        action_signature = path_signature(actions)
        task_path_counts[task_id][action_signature] += 1
        execution_family_path_counts[execution_family][action_signature] += 1
        if len(execution_family_examples[execution_family]) < 3:
            execution_family_examples[execution_family].append(
                {
                    "run_id": run_dir.name,
                    "task_id": task_id,
                    "outcome": outcome,
                    "raw_mode": raw_mode,
                    "steps": [
                        {
                            "step": step.get("step"),
                            "action": step.get("action", {}).get("type", "unknown"),
                            "success": step.get("action_result", {}).get("success"),
                        }
                        for step in steps[:8]
                    ],
                }
            )

        if outcome == "success" and failed_steps:
            trace_semantics_mismatches.append(
                {
                    "run_id": run_dir.name,
                    "task_id": task_id,
                    "outcome": outcome,
                    "reason": "success_with_failed_steps",
                    "failed_step_count": failed_steps,
                    "failed_actions": failed_action_types[:5],
                }
            )
        elif outcome in {"failure", "error"} and not failed_steps:
            trace_semantics_mismatches.append(
                {
                    "run_id": run_dir.name,
                    "task_id": task_id,
                    "outcome": outcome,
                    "reason": "terminal_failure_without_failed_trace_step",
                    "failed_step_count": 0,
                    "failure_category": manifest.get("failure_category"),
                }
            )

        outlier_runs.append(
            {
                "run_id": run_dir.name,
                "task_id": task_id,
                "raw_mode": raw_mode,
                "execution_family": execution_family,
                "outcome": outcome,
                "duration_seconds": duration_seconds,
                "trace_steps": len(steps),
                "failed_step_count": failed_steps,
                "failure_category": manifest.get("failure_category"),
            }
        )

    execution_family_profiles = []
    for execution_family, counter in sorted(execution_family_path_counts.items()):
        top_path, top_path_count = counter.most_common(1)[0] if counter else ("<empty>", 0)
        phase_counter = execution_family_phase_counts[execution_family]
        phase_total = sum(phase_counter.values())
        execution_family_profiles.append(
            {
                "execution_family": execution_family,
                "run_count": execution_family_counts[execution_family],
                "top_path": top_path,
                "top_path_count": top_path_count,
                "duration_seconds": duration_stats(duration_by_execution_family[execution_family]),
                "phase_counts": dict(phase_counter),
                "phase_shares": {
                    phase: round(count / phase_total, 3)
                    for phase, count in sorted(phase_counter.items())
                } if phase_total else {},
                "dominant_actions": [
                    {"action": action, "count": count}
                    for action, count in execution_family_action_counts[execution_family].most_common(8)
                ],
                "examples": execution_family_examples[execution_family],
            }
        )

    task_runtime_families = []
    for task_id, counter in sorted(task_path_counts.items(), key=lambda item: (-task_counts[item[0]], item[0]))[:12]:
        top_path, top_path_count = counter.most_common(1)[0] if counter else ("<empty>", 0)
        counts = task_step_counts[task_id]
        task_runtime_families.append(
            {
                "task_id": task_id,
                "run_count": task_counts[task_id],
                "avg_steps": round(mean(counts), 2) if counts else 0.0,
                "min_steps": min(counts) if counts else 0,
                "max_steps": max(counts) if counts else 0,
                "top_path": top_path,
                "top_path_count": top_path_count,
            }
        )

    transition_rows = []
    for (from_action, to_action, from_phase, to_phase), count in phase_aware_transition_counts.most_common():
        transition_rows.append(
            {
                "from_action": from_action,
                "to_action": to_action,
                "from_phase": from_phase,
                "to_phase": to_phase,
                "count": count,
            }
        )

    failure_hotspots = []
    for action_type, count in failure_action_counts.most_common(12):
        failure_hotspots.append(
            {
                "action_type": action_type,
                "failure_count": count,
                "example_runs": failure_examples[action_type][:3],
            }
        )

    special_step_indices = {
        str(step_index): count
        for step_index, count in sorted(step_index_counts.items())
        if step_index in {0, 998, 999} or step_index > 100
    }

    overall_durations = [run["duration_seconds"] for run in outlier_runs]
    payload: dict[str, Any] = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "external_refs": EXTERNAL_REFS,
        "analyzed_run_dirs": len(complete_runs),
        "incomplete_run_dirs": incomplete_runs,
        "outcome_counts": dict(outcome_counts),
        "mode_counts": dict(raw_mode_counts),
        "execution_family_counts": dict(execution_family_counts),
        "task_counts": dict(task_counts),
        "action_counts": dict(action_counts.most_common()),
        "phase_counts": dict(phase_counts),
        "duration_seconds": {
            "overall": duration_stats(overall_durations),
            "by_outcome": {
                outcome: duration_stats(values)
                for outcome, values in sorted(duration_by_outcome.items())
            },
        },
        "verification_signals": {
            key: verification_signals.get(key, 0)
            for key in [
                "explicit_verify_success_steps",
                "assertion_backed_sleep_steps",
                "trust_skipped_sleep_steps",
                "metacognitive_audit_steps",
            ]
        },
        "top_action_transitions": [
            {"from_action": from_action, "to_action": to_action, "count": count}
            for (from_action, to_action), count in transition_counts.most_common(25)
        ],
        "top_phase_transitions": [
            {"from_phase": from_phase, "to_phase": to_phase, "count": count}
            for (from_phase, to_phase), count in phase_transition_counts.most_common(20)
        ],
        "failure_category_counts": dict(failure_category_counts),
        "failure_hotspots": failure_hotspots,
        "special_step_indices": special_step_indices,
        "escalation_md_count": escalation_md_count,
        "escalation_json_count": escalation_json_count,
        "canonical_runtime_components": CANONICAL_RUNTIME_COMPONENTS,
        "execution_family_profiles": execution_family_profiles,
        "task_runtime_families": task_runtime_families,
        "trace_semantics_mismatches": trace_semantics_mismatches,
        "outlier_runs": {
            "longest": sorted(outlier_runs, key=lambda run: (-run["duration_seconds"], run["run_id"]))[:10],
            "most_failed_steps": sorted(outlier_runs, key=lambda run: (-run["failed_step_count"], run["run_id"]))[:10],
        },
        "trace_semantics_notes": [
            "Sleep is not always idle time: zero-second or oracle-backed sleep steps sometimes encode verification semantics.",
            "Universal runs terminate with an explicit metacognitive audit sentinel at step 998 in observed traces.",
            "Manifest-level success can coexist with failed trace steps in iterative creative runs, so trace semantics must be analyzed directly instead of assuming manifest outcome implies per-step success.",
        ],
    }

    OUTPUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")

    fieldnames = ["from_action", "to_action", "from_phase", "to_phase", "count"]
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(transition_rows)

    mermaid_lines = ["flowchart LR"]
    for phase in ["observe", "bootstrap", "reset_prepare", "configure", "produce", "verify", "audit"]:
        mermaid_lines.append(f"    {PHASE_NODE_IDS[phase]}[{PHASE_NODE_LABELS[phase]}]")
    for (from_phase, to_phase), count in phase_transition_counts.most_common():
        if count <= 0:
            continue
        mermaid_lines.append(
            f"    {PHASE_NODE_IDS.get(from_phase, 'Other')} -->|{count}| {PHASE_NODE_IDS.get(to_phase, 'Other')}"
        )
    OUTPUT_MMD.write_text("\n".join(mermaid_lines) + "\n", encoding="utf-8")
    return payload


if __name__ == "__main__":
    result = build_outputs()
    print(
        json.dumps(
            {
                "analyzed_run_dirs": result["analyzed_run_dirs"],
                "mode_counts": result["mode_counts"],
                "execution_family_counts": result["execution_family_counts"],
                "outcome_counts": result["outcome_counts"],
                "verification_signals": result["verification_signals"],
            },
            indent=2,
            sort_keys=False,
        )
    )
