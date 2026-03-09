from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


def _load_module(name: str, relative_path: str):
    path = Path(__file__).resolve().parent / "project_understanding" / "tools" / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_registry_covers_expected_families():
    module = _load_module("live_validation_registry_module", "live_validation_registry.py")

    families = {claim.family for claim in module.all_claims()}

    assert "mission_control_observability" in families
    assert "gui_evidence_window_management" in families
    assert "safari_browser_substrate" in families
    assert "generic_web_workflow" in families
    assert "puzzle_reasoning_sites" in families
    assert "canvas_drawing_tasks" in families
    assert "verification_outcome_semantics" in families
    assert "outer_loop_recovery_trust" in families
    assert "security_auth" in families


def test_campaign_initialization_creates_claim_state(tmp_path):
    module = _load_module("live_validation_campaign_module_init", "live_validation_campaign.py")
    module.ARTIFACTS_DIR = tmp_path / "live_validation"
    module.RUNS_DIR = module.ARTIFACTS_DIR / "runs"
    module.STATE_FILE = module.ARTIFACTS_DIR / "state.json"
    module.REGISTRY_FILE = module.ARTIFACTS_DIR / "registry.json"
    module.REPORT_JSON = module.ARTIFACTS_DIR / "report.json"
    module.REPORT_MD = module.ARTIFACTS_DIR / "report.md"

    state = module.initialize_state()

    assert state["campaign_mode"] == "core-fix-first"
    assert state["active_blocker"] is None
    assert module.STATE_FILE.exists()
    assert module.REGISTRY_FILE.exists()
    assert state["claims"]["mission.live_profile_health"]["verdict"] == "NOT_YET_RUN"


def test_execute_claim_sets_active_blocker_for_blocker_claim(tmp_path, monkeypatch):
    module = _load_module("live_validation_campaign_module_blocker", "live_validation_campaign.py")
    module.ARTIFACTS_DIR = tmp_path / "live_validation"
    module.RUNS_DIR = module.ARTIFACTS_DIR / "runs"
    module.STATE_FILE = module.ARTIFACTS_DIR / "state.json"
    module.REGISTRY_FILE = module.ARTIFACTS_DIR / "registry.json"
    module.REPORT_JSON = module.ARTIFACTS_DIR / "report.json"
    module.REPORT_MD = module.ARTIFACTS_DIR / "report.md"

    state = module.initialize_state()

    def fake_run_harness(claim, run_dir, run_id):
        run_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "claim_id": claim.claim_id,
            "family": claim.family,
            "phase": claim.phase,
            "criticality": claim.criticality,
            "verdict": "BLOCKED_BY_CORE_DEFECT",
            "root_cause_category": "cursor_click_typing_backend",
            "actual_observed_behavior": "synthetic blocker",
            "evidence_quality": "visible",
            "fix_status": "required",
            "retest_status": "required",
            "actions": [],
            "evidence": {},
            "implementation_confidence": "live_evidence_gated",
        }
        (run_dir / "result.json").write_text(json.dumps(payload), encoding="utf-8")
        return payload

    monkeypatch.setattr(module, "run_harness", fake_run_harness)

    payload = module.execute_claim("browser.safari_visible_click_fixture", state)

    assert payload["ok"] is True
    assert state["active_blocker"]["claim_id"] == "browser.safari_visible_click_fixture"
    assert state["claims"]["browser.safari_visible_click_fixture"]["verdict"] == "BLOCKED_BY_CORE_DEFECT"


def test_execute_claim_passes_without_active_blocker_crash(tmp_path, monkeypatch):
    module = _load_module("live_validation_campaign_module_pass", "live_validation_campaign.py")
    module.ARTIFACTS_DIR = tmp_path / "live_validation"
    module.RUNS_DIR = module.ARTIFACTS_DIR / "runs"
    module.STATE_FILE = module.ARTIFACTS_DIR / "state.json"
    module.REGISTRY_FILE = module.ARTIFACTS_DIR / "registry.json"
    module.REPORT_JSON = module.ARTIFACTS_DIR / "report.json"
    module.REPORT_MD = module.ARTIFACTS_DIR / "report.md"

    state = module.initialize_state()

    def fake_run_harness(claim, run_dir, run_id):
        run_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "claim_id": claim.claim_id,
            "family": claim.family,
            "phase": claim.phase,
            "criticality": claim.criticality,
            "verdict": "PASS",
            "root_cause_category": None,
            "actual_observed_behavior": "synthetic pass",
            "evidence_quality": "system_health",
            "fix_status": "not_required",
            "retest_status": "not_required",
            "actions": [],
            "evidence": {},
            "implementation_confidence": "contract_smoke",
        }
        (run_dir / "result.json").write_text(json.dumps(payload), encoding="utf-8")
        return payload

    monkeypatch.setattr(module, "run_harness", fake_run_harness)

    payload = module.execute_claim("mission.live_profile_health", state)

    assert payload["ok"] is True
    assert state["active_blocker"] is None
    assert state["claims"]["mission.live_profile_health"]["verdict"] == "PASS"


def test_blocked_dependents_follow_dependency_graph():
    module = _load_module("live_validation_campaign_module_deps", "live_validation_campaign.py")

    blocked = module.blocked_dependents("browser.safari_visible_click_fixture")

    assert "web.public_navigation_workflow" in blocked
    assert "puzzle.mysterymaster_page_readiness" in blocked
    assert "canvas.excalidraw_visible_readiness" in blocked
