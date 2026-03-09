#!/usr/bin/env python3
"""Claim-based, evidence-gated live validation campaign runner."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[4]
OPERATOR_DIR = ROOT / "operator"
VENV_PYTHON = OPERATOR_DIR / "venv" / "bin" / "python"


def _bootstrap_reexec_in_venv(argv: list[str]) -> None:
    if os.environ.get("CONCENTRIC_LIVE_VALIDATION_VENV") == "1":
        return
    if not VENV_PYTHON.exists():
        return
    expected_prefix = (OPERATOR_DIR / "venv").resolve()
    current_prefix = Path(sys.prefix).resolve()
    if current_prefix == expected_prefix:
        return
    target = VENV_PYTHON
    env = os.environ.copy()
    env["CONCENTRIC_LIVE_VALIDATION_VENV"] = "1"
    os.execve(str(target), [str(target), str(Path(__file__).resolve()), *argv], env)


_bootstrap_reexec_in_venv(sys.argv[1:])

TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from live_validation_harnesses import (
    BLOCKED_BY_CORE_DEFECT,
    BLOCKED_BY_PERMISSION,
    FAIL,
    NOT_YET_RUN,
    PASS,
    run_harness,
)
from live_validation_registry import (
    all_claims,
    claim_by_id,
    claim_map,
    claims_by_family,
    claims_in_order,
    registry_snapshot,
)

ARTIFACTS_DIR = ROOT / "operator" / "cre" / "project_understanding" / "artifacts" / "live_validation"
RUNS_DIR = ARTIFACTS_DIR / "runs"
STATE_FILE = ARTIFACTS_DIR / "state.json"
REGISTRY_FILE = ARTIFACTS_DIR / "registry.json"
REPORT_JSON = ARTIFACTS_DIR / "report.json"
REPORT_MD = ARTIFACTS_DIR / "report.md"

CAMPAIGN_MODE = "core-fix-first"
BLOCKING_VERDICTS = {BLOCKED_BY_CORE_DEFECT, BLOCKED_BY_PERMISSION}


def maybe_reexec_in_venv(argv: list[str] | None) -> None:
    _bootstrap_reexec_in_venv(argv or [])


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def ensure_dirs() -> None:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    RUNS_DIR.mkdir(parents=True, exist_ok=True)


def save_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def load_state() -> dict[str, Any]:
    if not STATE_FILE.exists():
        return initialize_state()
    try:
        state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        state = initialize_state()
    return sync_state_with_registry(state)


def save_state(state: dict[str, Any]) -> None:
    state["updated_at"] = now_iso()
    save_json(STATE_FILE, state)
    save_json(REGISTRY_FILE, registry_snapshot())


def default_claim_status(claim_id: str) -> dict[str, Any]:
    claim = claim_by_id(claim_id)
    return {
        "claim_id": claim.claim_id,
        "family": claim.family,
        "criticality": claim.criticality,
        "verdict": NOT_YET_RUN,
        "last_run_id": None,
        "last_run_at": None,
        "latest_result_path": None,
        "root_cause_category": None,
        "fix_status": None,
        "retest_status": None,
        "implementation_confidence": None,
    }


def initialize_state() -> dict[str, Any]:
    ensure_dirs()
    state = {
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "campaign_mode": CAMPAIGN_MODE,
        "active_blocker": None,
        "claims": {claim_id: default_claim_status(claim_id) for claim_id in claims_in_order()},
        "run_history": [],
    }
    save_json(REGISTRY_FILE, registry_snapshot())
    save_json(STATE_FILE, state)
    return state


def sync_state_with_registry(state: dict[str, Any]) -> dict[str, Any]:
    state.setdefault("campaign_mode", CAMPAIGN_MODE)
    state.setdefault("active_blocker", None)
    state.setdefault("run_history", [])
    claim_states = state.setdefault("claims", {})
    for claim_id in claims_in_order():
        claim_states.setdefault(claim_id, default_claim_status(claim_id))
    for claim_id in list(claim_states.keys()):
        if claim_id not in claim_map():
            claim_states.pop(claim_id, None)
    return state


def make_run_id(claim_id: str) -> str:
    ts = time.strftime("%Y%m%dT%H%M%S")
    return f"{ts}_{claim_id.replace('.', '_')}"


def depends_on(blocker_id: str, claim_id: str, *, _seen: set[str] | None = None) -> bool:
    if blocker_id == claim_id:
        return True
    _seen = _seen or set()
    if claim_id in _seen:
        return False
    _seen.add(claim_id)
    claim = claim_by_id(claim_id)
    for dep in claim.depends_on:
        if dep == blocker_id or depends_on(blocker_id, dep, _seen=_seen):
            return True
    return False


def blocked_dependents(blocker_id: str | None) -> list[str]:
    if not blocker_id:
        return []
    return [claim_id for claim_id in claims_in_order() if claim_id != blocker_id and depends_on(blocker_id, claim_id)]


def result_summary(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "claim_id": result["claim_id"],
        "family": result["family"],
        "criticality": result["criticality"],
        "verdict": result["verdict"],
        "root_cause_category": result.get("root_cause_category"),
        "fix_status": result.get("fix_status"),
        "retest_status": result.get("retest_status"),
        "implementation_confidence": result.get("implementation_confidence"),
        "actual_observed_behavior": result.get("actual_observed_behavior"),
    }


def record_claim_result(state: dict[str, Any], claim_id: str, run_id: str, run_dir: Path, result: dict[str, Any]) -> None:
    status = state["claims"][claim_id]
    status.update(
        {
            "verdict": result["verdict"],
            "last_run_id": run_id,
            "last_run_at": now_iso(),
            "latest_result_path": str(run_dir / "result.json"),
            "root_cause_category": result.get("root_cause_category"),
            "fix_status": result.get("fix_status"),
            "retest_status": result.get("retest_status"),
            "implementation_confidence": result.get("implementation_confidence"),
        }
    )
    history_entry = {
        "run_id": run_id,
        "claim_id": claim_id,
        "result_path": str(run_dir / "result.json"),
        "verdict": result["verdict"],
        "at": now_iso(),
    }
    state["run_history"].append(history_entry)


def execute_claim(claim_id: str, state: dict[str, Any]) -> dict[str, Any]:
    blocker = state.get("active_blocker")
    if blocker and blocker.get("claim_id") and blocker["claim_id"] != claim_id:
        return {
            "ok": False,
            "blocked_by": blocker["claim_id"],
            "message": (
                "Campaign is paused on an active blocker. "
                f"Rerun or fix {blocker['claim_id']} before proceeding."
            ),
        }

    claim = claim_by_id(claim_id)
    run_id = make_run_id(claim_id)
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    result = run_harness(claim, run_dir, run_id)
    result["run_id"] = run_id
    save_json(run_dir / "result.json", result)
    record_claim_result(state, claim_id, run_id, run_dir, result)

    if result["verdict"] in BLOCKING_VERDICTS and claim.criticality == "blocker":
        state["active_blocker"] = {
            "claim_id": claim_id,
            "verdict": result["verdict"],
            "root_cause_category": result.get("root_cause_category"),
            "run_id": run_id,
            "at": now_iso(),
        }
    elif (state.get("active_blocker") or {}).get("claim_id") == claim_id and result["verdict"] == PASS:
        state["active_blocker"] = None

    save_state(state)
    return {
        "ok": True,
        "claim_id": claim_id,
        "run_id": run_id,
        "result_path": str(run_dir / "result.json"),
        "result": result_summary(result),
        "active_blocker": state.get("active_blocker"),
    }


def pending_claim_ids(state: dict[str, Any]) -> list[str]:
    return [
        claim_id
        for claim_id in claims_in_order()
        if state["claims"][claim_id]["verdict"] != PASS
    ]


def continue_claims(state: dict[str, Any], claim_ids: list[str]) -> dict[str, Any]:
    completed: list[dict[str, Any]] = []
    for claim_id in claim_ids:
        response = execute_claim(claim_id, state)
        completed.append(response)
        if not response.get("ok"):
            break
        verdict = response["result"]["verdict"]
        if verdict in BLOCKING_VERDICTS and claim_by_id(claim_id).criticality == "blocker":
            break
    return {
        "completed": completed,
        "active_blocker": state.get("active_blocker"),
        "status": campaign_status_payload(state),
    }


def campaign_start(*, fresh: bool) -> dict[str, Any]:
    state = initialize_state() if fresh or not STATE_FILE.exists() else load_state()
    return continue_claims(state, claims_in_order())


def campaign_resume() -> dict[str, Any]:
    state = load_state()
    blocker = state.get("active_blocker")
    if blocker and blocker.get("claim_id"):
        retry = execute_claim(blocker["claim_id"], state)
        if not retry.get("ok") or retry["result"]["verdict"] in BLOCKING_VERDICTS:
            return {
                "completed": [retry],
                "active_blocker": state.get("active_blocker"),
                "status": campaign_status_payload(state),
            }
    return continue_claims(state, pending_claim_ids(state))


def run_family(family: str) -> dict[str, Any]:
    state = load_state()
    ordered = [claim.claim_id for claim in claims_by_family(family)]
    return continue_claims(state, ordered)


def campaign_status_payload(state: dict[str, Any] | None = None) -> dict[str, Any]:
    state = load_state() if state is None else state
    counts = {PASS: 0, FAIL: 0, BLOCKED_BY_CORE_DEFECT: 0, BLOCKED_BY_PERMISSION: 0, NOT_YET_RUN: 0}
    for claim_id in claims_in_order():
        verdict = state["claims"][claim_id]["verdict"]
        counts.setdefault(verdict, 0)
        counts[verdict] += 1
    blocker = state.get("active_blocker")
    return {
        "generated_at": now_iso(),
        "campaign_mode": state.get("campaign_mode", CAMPAIGN_MODE),
        "claim_count": len(claims_in_order()),
        "counts": counts,
        "active_blocker": blocker,
        "blocked_dependents": blocked_dependents(blocker.get("claim_id") if blocker else None),
        "claims": [state["claims"][claim_id] for claim_id in claims_in_order()],
    }


def build_report_payload(state: dict[str, Any] | None = None) -> dict[str, Any]:
    state = load_state() if state is None else state
    status = campaign_status_payload(state)
    report_claims: list[dict[str, Any]] = []
    for claim_id in claims_in_order():
        claim = claim_by_id(claim_id)
        claim_status = state["claims"][claim_id]
        report_claims.append(
            {
                "claim_id": claim_id,
                "family": claim.family,
                "phase": claim.phase,
                "title": claim.title,
                "claimed_capability": claim.capability_claim,
                "success_oracle": claim.success_oracle,
                "verdict": claim_status["verdict"],
                "implementation_confidence": claim_status.get("implementation_confidence"),
                "root_cause_category": claim_status.get("root_cause_category"),
                "fix_status": claim_status.get("fix_status"),
                "retest_status": claim_status.get("retest_status"),
                "latest_result_path": claim_status.get("latest_result_path"),
            }
        )
    return {
        "generated_at": now_iso(),
        "status": status,
        "claims": report_claims,
    }


def build_report_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Live Validation Campaign Report",
        "",
        f"Generated: `{report['generated_at']}`",
        "",
        "## Summary",
        "",
        f"- Campaign mode: `{report['status']['campaign_mode']}`",
        f"- Claim count: `{report['status']['claim_count']}`",
        f"- Active blocker: `{report['status']['active_blocker']}`",
        "",
        "## Verdict Counts",
        "",
    ]
    for verdict, count in report["status"]["counts"].items():
        lines.append(f"- `{verdict}`: {count}")
    lines.extend(["", "## Claims", ""])
    for claim in report["claims"]:
        lines.extend(
            [
                f"### {claim['claim_id']}",
                "",
                f"- Family: `{claim['family']}`",
                f"- Phase: `{claim['phase']}`",
                f"- Claimed capability: {claim['claimed_capability']}",
                f"- Verdict: `{claim['verdict']}`",
                f"- Implementation confidence: `{claim['implementation_confidence']}`",
                f"- Root cause: `{claim['root_cause_category']}`",
                f"- Fix status: `{claim['fix_status']}`",
                f"- Retest status: `{claim['retest_status']}`",
                f"- Latest result path: `{claim['latest_result_path']}`",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def write_report(state: dict[str, Any] | None = None) -> dict[str, Any]:
    report = build_report_payload(state)
    save_json(REPORT_JSON, report)
    REPORT_MD.write_text(build_report_markdown(report), encoding="utf-8")
    return {
        "report_json": str(REPORT_JSON),
        "report_md": str(REPORT_MD),
        "status": report["status"],
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON output.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    start_parser = subparsers.add_parser("start", help="Initialize or restart the campaign and run claims in registry order.")
    start_parser.add_argument("--fresh", action="store_true", help="Reset campaign state before starting.")
    subparsers.add_parser("resume", help="Resume the campaign from the active blocker or next unfinished claim.")

    run_parser = subparsers.add_parser("run", help="Run a single claim by id.")
    run_parser.add_argument("claim_id")

    family_parser = subparsers.add_parser("run-family", help="Run claims for one family in registry order.")
    family_parser.add_argument("family")

    subparsers.add_parser("status", help="Show current campaign status.")
    subparsers.add_parser("report", help="Generate report artifacts and print their paths.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    maybe_reexec_in_venv(argv)
    args = parse_args(argv)
    try:
        if args.command == "start":
            payload = campaign_start(fresh=args.fresh)
        elif args.command == "resume":
            payload = campaign_resume()
        elif args.command == "run":
            payload = execute_claim(args.claim_id, load_state())
        elif args.command == "run-family":
            payload = run_family(args.family)
        elif args.command == "status":
            payload = campaign_status_payload()
        elif args.command == "report":
            payload = write_report()
        else:
            raise RuntimeError(f"Unsupported command: {args.command}")
    except Exception as exc:
        payload = {"ok": False, "error": str(exc)}
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=False))
        else:
            print(f"Live validation error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=False))
    else:
        print(json.dumps(payload, indent=2, sort_keys=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
