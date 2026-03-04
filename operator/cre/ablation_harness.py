#!/usr/bin/env python3
"""Ablation study harness for concentric triangles task.

Runs the test under four conditions (5 repetitions each) to isolate each
optimization component's independent contribution:

  A: Bare VLM (baseline)   — no cache, no trust, fixed Flash routing
  B: Cache only             — coord cache on, no trust, fixed Flash
  C: Cache + Trust          — coord cache + trust tracker, fixed Flash
  D: Full system            — coord cache + trust + adaptive routing
  E: Full system + allowlist (permissive) — pre-action allowlist ON
  F: Full system + allowlist (tightened)  — allowlist ON + ACTION_ALLOWLIST_TIGHTENED=1

Usage:
    cd operator
    ./venv/bin/python cre/ablation_harness.py [--reps 5] [--conditions A,B,C,D]
    ./venv/bin/python cre/ablation_harness.py [--conditions D,E,F]  # allowlist ablation

Results are written to operator/cre/runs/ablation_<timestamp>/
with a summary CSV and per-run trace links.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

HARNESS_DIR = Path(__file__).parent
OPERATOR_DIR = HARNESS_DIR.parent
VENV_PYTHON = str(OPERATOR_DIR / "venv" / "bin" / "python")
TEST_SCRIPT = str(HARNESS_DIR / "test_excalidraw_covt.py")

ABLATION_ENV_VAR = "ABLATION_CONDITION"


@dataclass
class Condition:
    name: str
    label: str
    env: dict[str, str] = field(default_factory=dict)


CONDITIONS: dict[str, Condition] = {
    "A": Condition(
        name="A",
        label="Bare VLM (baseline)",
        env={
            "DISABLE_COORD_CACHE": "1",
            "DISABLE_TRUST_TRACKER": "1",
            "DISABLE_ADAPTIVE_ROUTING": "1",
            "DISABLE_ACTION_ALLOWLIST": "1",
        },
    ),
    "B": Condition(
        name="B",
        label="Cache only",
        env={
            "DISABLE_TRUST_TRACKER": "1",
            "DISABLE_ADAPTIVE_ROUTING": "1",
            "DISABLE_ACTION_ALLOWLIST": "1",
        },
    ),
    "C": Condition(
        name="C",
        label="Cache + Trust",
        env={
            "DISABLE_ADAPTIVE_ROUTING": "1",
            "DISABLE_ACTION_ALLOWLIST": "1",
        },
    ),
    "D": Condition(
        name="D",
        label="Full system",
        env={"DISABLE_ACTION_ALLOWLIST": "1"},
    ),
    "E": Condition(
        name="E",
        label="Full system + allowlist (permissive)",
        env={
            # Allowlist ON; default config allows all handler types + loose bounds
            "DISABLE_ACTION_ALLOWLIST": "0",
        },
    ),
    "F": Condition(
        name="F",
        label="Full system + allowlist (tightened)",
        env={
            "DISABLE_ACTION_ALLOWLIST": "0",
            "ACTION_ALLOWLIST_TIGHTENED": "1",
        },
    ),
}


@dataclass
class RunResult:
    condition: str
    rep: int
    run_id: str
    outcome: str
    wall_time_s: float
    num_steps: int
    vlm_calls: int
    cache_hits: int
    cache_misses: int
    trust_skips: int
    routing_adaptations: int
    blocked_by_allowlist_count: int = 0
    allowlist_reasons: str = ""  # JSON or "reason:count,..." for CSV


def _find_latest_run_dir(runs_dir: Path) -> Path | None:
    """Return the most recently modified run directory."""
    candidates = sorted(runs_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
    for c in candidates:
        if c.is_dir() and (c / "manifest.json").exists():
            return c
    return None


def _parse_manifest(run_dir: Path) -> dict:
    """Extract metrics from a completed run's manifest."""
    manifest_path = run_dir / "manifest.json"
    if not manifest_path.exists():
        return {}
    with open(manifest_path) as f:
        return json.load(f)


def _count_trace_events(run_dir: Path) -> dict[str, int]:
    """Scan trace.jsonl for cache/trust/routing events."""
    trace_path = run_dir / "trace.jsonl"
    counts = {"vlm_calls": 0, "cache_hits": 0, "cache_misses": 0,
              "trust_skips": 0, "routing_adaptations": 0}
    if not trace_path.exists():
        return counts
    with open(trace_path) as f:
        for line in f:
            try:
                step = json.loads(line)
            except json.JSONDecodeError:
                continue
            action = step.get("action", "")
            metadata = step.get("metadata", {})
            if "vlm" in action.lower() or metadata.get("vlm_call"):
                counts["vlm_calls"] += 1
            if metadata.get("cache_hit"):
                counts["cache_hits"] += 1
            if metadata.get("cache_miss") or metadata.get("cache_stale"):
                counts["cache_misses"] += 1
            if metadata.get("trust_skip") or metadata.get("verification_skipped"):
                counts["trust_skips"] += 1
            if metadata.get("routing_adaptation"):
                counts["routing_adaptations"] += 1
    return counts


def _count_allowlist_blocks(run_dir: Path) -> tuple[int, dict[str, int]]:
    """Scan trace.jsonl for steps blocked by the action allowlist.
    Returns (blocked_count, reason -> count).
    """
    trace_path = run_dir / "trace.jsonl"
    count = 0
    reasons: dict[str, int] = {}
    if not trace_path.exists():
        return 0, reasons
    with open(trace_path) as f:
        for line in f:
            try:
                step = json.loads(line)
            except json.JSONDecodeError:
                continue
            ar = step.get("action_result", {})
            if not ar.get("blocked_by_allowlist"):
                continue
            count += 1
            reason = ar.get("reason", "unknown")
            reasons[reason] = reasons.get(reason, 0) + 1
    return count, reasons


def run_single(condition: Condition, rep: int, ablation_dir: Path) -> RunResult:
    """Execute one test run under the given ablation condition."""
    env = os.environ.copy()
    env["CONCENTRIC_TRIANGLES_CLEAN"] = "1"
    env[ABLATION_ENV_VAR] = condition.name
    env.update(condition.env)

    run_label = f"{condition.name}_rep{rep}"
    print(f"\n{'='*60}")
    print(f"  ABLATION: {condition.label} | Rep {rep}")
    print(f"{'='*60}")

    t0 = time.monotonic()
    result = subprocess.run(
        [VENV_PYTHON, TEST_SCRIPT],
        cwd=str(OPERATOR_DIR),
        env=env,
        capture_output=True,
        text=True,
        timeout=600,
    )
    wall_time = time.monotonic() - t0

    log_path = ablation_dir / f"{run_label}.log"
    log_path.write_text(
        f"=== STDOUT ===\n{result.stdout}\n=== STDERR ===\n{result.stderr}\n",
        encoding="utf-8",
    )

    runs_dir = HARNESS_DIR / "runs"
    run_dir = _find_latest_run_dir(runs_dir)
    run_id = run_dir.name if run_dir else "unknown"
    manifest = _parse_manifest(run_dir) if run_dir else {}
    trace_counts = _count_trace_events(run_dir) if run_dir else {}
    blocked_allowlist, allowlist_reasons = _count_allowlist_blocks(run_dir) if run_dir else (0, {})
    allowlist_reasons_str = json.dumps(allowlist_reasons) if allowlist_reasons else ""

    outcome = manifest.get("outcome", "error" if result.returncode != 0 else "unknown")
    num_steps = manifest.get("num_steps", 0)

    return RunResult(
        condition=condition.name,
        rep=rep,
        run_id=run_id,
        outcome=outcome,
        wall_time_s=round(wall_time, 2),
        num_steps=num_steps,
        vlm_calls=trace_counts.get("vlm_calls", 0),
        cache_hits=trace_counts.get("cache_hits", 0),
        cache_misses=trace_counts.get("cache_misses", 0),
        trust_skips=trace_counts.get("trust_skips", 0),
        routing_adaptations=trace_counts.get("routing_adaptations", 0),
        blocked_by_allowlist_count=blocked_allowlist,
        allowlist_reasons=allowlist_reasons_str,
    )


def write_csv(results: list[RunResult], path: Path):
    fieldnames = [
        "condition", "rep", "run_id", "outcome", "wall_time_s",
        "num_steps", "vlm_calls", "cache_hits", "cache_misses",
        "trust_skips", "routing_adaptations",
        "blocked_by_allowlist_count", "allowlist_reasons",
    ]
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow(r.__dict__)


def write_summary(results: list[RunResult], path: Path):
    """Write human-readable summary with per-condition statistics."""
    from collections import defaultdict
    groups: dict[str, list[RunResult]] = defaultdict(list)
    for r in results:
        groups[r.condition].append(r)

    lines = ["# Ablation Study Results\n"]
    lines.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    lines.append(f"Total runs: {len(results)}\n")

    for cond_name in sorted(groups):
        runs = groups[cond_name]
        cond = CONDITIONS[cond_name]
        times = [r.wall_time_s for r in runs]
        successes = sum(1 for r in runs if r.outcome == "success")
        mean_t = sum(times) / len(times) if times else 0
        min_t = min(times) if times else 0
        max_t = max(times) if times else 0

        lines.append(f"\n## Condition {cond_name}: {cond.label}")
        lines.append(f"  Success rate: {successes}/{len(runs)} ({100*successes/len(runs):.0f}%)")
        lines.append(f"  Wall time: mean={mean_t:.1f}s, min={min_t:.1f}s, max={max_t:.1f}s")
        lines.append(f"  VLM calls (mean): {sum(r.vlm_calls for r in runs)/len(runs):.1f}")
        lines.append(f"  Cache hits (mean): {sum(r.cache_hits for r in runs)/len(runs):.1f}")
        lines.append(f"  Trust skips (mean): {sum(r.trust_skips for r in runs)/len(runs):.1f}")
        lines.append(f"  Routing adaptations: {sum(r.routing_adaptations for r in runs)}")
        if any(r.blocked_by_allowlist_count for r in runs):
            lines.append(f"  Allowlist blocks (total): {sum(r.blocked_by_allowlist_count for r in runs)}")
            reasons_agg: dict[str, int] = {}
            for r in runs:
                if r.allowlist_reasons:
                    try:
                        for k, v in json.loads(r.allowlist_reasons).items():
                            reasons_agg[k] = reasons_agg.get(k, 0) + v
                    except json.JSONDecodeError:
                        pass
            if reasons_agg:
                lines.append(f"  Allowlist reasons: {reasons_agg}")
        lines.append(f"  Run IDs: {', '.join(r.run_id for r in runs)}")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Ablation study for concentric triangles task")
    parser.add_argument("--reps", type=int, default=5, help="Repetitions per condition (default: 5)")
    parser.add_argument("--conditions", type=str, default="A,B,C,D",
                        help="Comma-separated condition names (default: A,B,C,D)")
    parser.add_argument("--dry-run", action="store_true", help="Print plan without running")
    args = parser.parse_args()

    cond_names = [c.strip().upper() for c in args.conditions.split(",")]
    for name in cond_names:
        if name not in CONDITIONS:
            print(f"Unknown condition: {name}. Available: {list(CONDITIONS.keys())}")
            return 1

    ts = time.strftime("%Y%m%d_%H%M%S")
    ablation_dir = HARNESS_DIR / "runs" / f"ablation_{ts}"
    ablation_dir.mkdir(parents=True, exist_ok=True)

    total_runs = len(cond_names) * args.reps
    print(f"\n  Ablation Study: {total_runs} runs ({len(cond_names)} conditions × {args.reps} reps)")
    print(f"  Output: {ablation_dir}")
    for name in cond_names:
        c = CONDITIONS[name]
        print(f"    {name}: {c.label} [{', '.join(f'{k}={v}' for k, v in c.env.items()) or 'all enabled'}]")

    if args.dry_run:
        print("\n  (dry run — no tests executed)")
        return 0

    results: list[RunResult] = []
    for name in cond_names:
        for rep in range(1, args.reps + 1):
            try:
                r = run_single(CONDITIONS[name], rep, ablation_dir)
                results.append(r)
                print(f"  -> {r.condition} rep{r.rep}: {r.outcome} in {r.wall_time_s}s "
                      f"(steps={r.num_steps}, vlm={r.vlm_calls}, cache_hits={r.cache_hits})")
            except subprocess.TimeoutExpired:
                print(f"  -> {name} rep{rep}: TIMEOUT (600s)")
                results.append(RunResult(
                    condition=name, rep=rep, run_id="timeout",
                    outcome="timeout", wall_time_s=600.0, num_steps=0,
                    vlm_calls=0, cache_hits=0, cache_misses=0,
                    trust_skips=0, routing_adaptations=0,
                    blocked_by_allowlist_count=0, allowlist_reasons="",
                ))
            except Exception as e:
                print(f"  -> {name} rep{rep}: ERROR ({e})")
                results.append(RunResult(
                    condition=name, rep=rep, run_id="error",
                    outcome="error", wall_time_s=0.0, num_steps=0,
                    vlm_calls=0, cache_hits=0, cache_misses=0,
                    trust_skips=0, routing_adaptations=0,
                    blocked_by_allowlist_count=0, allowlist_reasons="",
                ))

    csv_path = ablation_dir / "results.csv"
    summary_path = ablation_dir / "summary.md"
    write_csv(results, csv_path)
    write_summary(results, summary_path)

    print(f"\n{'='*60}")
    print(f"  ABLATION COMPLETE")
    print(f"  CSV: {csv_path}")
    print(f"  Summary: {summary_path}")
    print(f"{'='*60}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
