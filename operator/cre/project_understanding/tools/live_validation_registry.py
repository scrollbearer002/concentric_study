#!/usr/bin/env python3
"""Canonical claim registry for Concentric live validation."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class LiveValidationClaim:
    claim_id: str
    family: str
    phase: str
    title: str
    capability_claim: str
    required_substrate: list[str]
    required_profile: str
    harness: str
    live_task_recipe: list[str]
    expected_evidence: list[str]
    success_oracle: str
    criticality: str
    user_visible: bool
    destructive: bool
    permission_sensitive: bool
    depends_on: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


CLAIMS: list[LiveValidationClaim] = [
    LiveValidationClaim(
        claim_id="mission.live_profile_health",
        family="mission_control_observability",
        phase="A",
        title="Live mission profile health",
        capability_claim="Mission control can bring up and verify the live runtime stack (Phoenix + Control Room).",
        required_substrate=["mission_control", "phoenix", "control_room"],
        required_profile="live",
        harness="mission_profile_health",
        live_task_recipe=[
            "Run mission-control doctor.",
            "Start or reuse the live profile.",
            "Verify Phoenix and Control Room are healthy.",
        ],
        expected_evidence=[
            "doctor_overall_ok",
            "phoenix_healthy",
            "control_room_healthy",
            "observability_enabled",
        ],
        success_oracle="Doctor passes and the live profile services report healthy with observability enabled.",
        criticality="blocker",
        user_visible=False,
        destructive=False,
        permission_sensitive=False,
    ),
    LiveValidationClaim(
        claim_id="mission.architecture_profile_health",
        family="mission_control_observability",
        phase="A",
        title="Architecture profile health",
        capability_claim="Mission control can bring up and verify the architecture stack (Control Room + Structurizr).",
        required_substrate=["mission_control", "control_room", "structurizr", "docker"],
        required_profile="architecture",
        harness="mission_profile_health",
        live_task_recipe=[
            "Run mission-control doctor.",
            "Start or reuse the architecture profile.",
            "Verify Control Room and Structurizr are healthy.",
        ],
        expected_evidence=[
            "doctor_overall_ok",
            "control_room_healthy",
            "structurizr_healthy",
        ],
        success_oracle="Doctor passes and the architecture profile services report healthy.",
        criticality="high",
        user_visible=False,
        destructive=False,
        permission_sensitive=False,
    ),
    LiveValidationClaim(
        claim_id="gui.safari_visible_readiness",
        family="gui_evidence_window_management",
        phase="A",
        title="Safari visible readiness",
        capability_claim="The stack can prove Safari is visibly frontmost and capturable before any visible task begins.",
        required_substrate=["Safari", "Apple Events", "System Events", "Quartz capture"],
        required_profile="live",
        harness="safari_visible_readiness",
        live_task_recipe=[
            "Activate Safari.",
            "Open a bounded page.",
            "Run the GUI evidence gate with frontmost + capture requirements.",
        ],
        expected_evidence=[
            "frontmost_match",
            "system_events_visible_window",
            "quartz_front_window",
            "window_capture_ok",
        ],
        success_oracle="GUI evidence reports ready_for_visible_task=true with no contradictions or blockers.",
        criticality="blocker",
        user_visible=True,
        destructive=False,
        permission_sensitive=True,
        depends_on=["mission.live_profile_health"],
    ),
    LiveValidationClaim(
        claim_id="browser.safari_visible_click_fixture",
        family="safari_browser_substrate",
        phase="B",
        title="Visible click on local Safari fixture",
        capability_claim="Concentric can perform a visible cursor move + click in Safari and verify the resulting on-screen state.",
        required_substrate=["Safari", "local fixture", "cursor move", "click backend", "GUI evidence"],
        required_profile="live",
        harness="safari_visible_click_fixture",
        live_task_recipe=[
            "Open the local preclick fixture in Safari.",
            "Focus Safari and verify visible readiness.",
            "Locate the button, move the cursor, click it, and verify the status changed.",
        ],
        expected_evidence=[
            "pre_click_capture",
            "post_click_capture",
            "status_before",
            "status_after",
            "cursor_click_action_log",
        ],
        success_oracle="The fixture status changes from 'Awaiting confirmed click' to 'Clicked safely' after a physical click.",
        criticality="blocker",
        user_visible=True,
        destructive=False,
        permission_sensitive=True,
        depends_on=["gui.safari_visible_readiness"],
    ),
    LiveValidationClaim(
        claim_id="web.public_navigation_workflow",
        family="generic_web_workflow",
        phase="B",
        title="Public web navigation readiness",
        capability_claim="Concentric can navigate to a public web page in Safari and verify the resulting page state with visible evidence.",
        required_substrate=["Safari", "network", "GUI evidence"],
        required_profile="live",
        harness="public_navigation_readiness",
        live_task_recipe=[
            "Open a public site in Safari.",
            "Wait for the page to settle.",
            "Capture visible evidence and confirm URL/title alignment.",
        ],
        expected_evidence=[
            "visible_capture",
            "current_url",
            "page_title",
        ],
        success_oracle="The public page loads in Safari and visible evidence aligns with the intended destination.",
        criticality="high",
        user_visible=True,
        destructive=False,
        permission_sensitive=False,
        depends_on=["browser.safari_visible_click_fixture"],
    ),
    LiveValidationClaim(
        claim_id="puzzle.mysterymaster_page_readiness",
        family="puzzle_reasoning_sites",
        phase="B",
        title="Mystery Master page readiness",
        capability_claim="Concentric can bring a Mystery Master puzzle page into a visibly ready state for later reasoning tasks.",
        required_substrate=["Safari", "Mystery Master", "GUI evidence"],
        required_profile="live",
        harness="mysterymaster_readiness",
        live_task_recipe=[
            "Open a public Mystery Master page in Safari.",
            "Verify the page title/URL and capture the front window.",
        ],
        expected_evidence=[
            "visible_capture",
            "mysterymaster_title",
            "mysterymaster_url",
        ],
        success_oracle="The target Mystery Master page loads and remains evidence-gated for visible interaction.",
        criticality="high",
        user_visible=True,
        destructive=False,
        permission_sensitive=False,
        depends_on=["browser.safari_visible_click_fixture"],
    ),
    LiveValidationClaim(
        claim_id="canvas.excalidraw_visible_readiness",
        family="canvas_drawing_tasks",
        phase="C",
        title="Excalidraw visible readiness",
        capability_claim="Concentric can bring Excalidraw into a visible, capturable, evidence-gated ready state for bounded drawing.",
        required_substrate=["Safari", "Excalidraw", "GUI evidence"],
        required_profile="live",
        harness="canvas_readiness",
        live_task_recipe=[
            "Open Excalidraw in Safari.",
            "Verify the page is visibly ready and capturable.",
        ],
        expected_evidence=[
            "visible_capture",
            "canvas_page_title",
            "canvas_url",
        ],
        success_oracle="Excalidraw is frontmost, capturable, and clearly loaded enough for a bounded drawing task.",
        criticality="high",
        user_visible=True,
        destructive=False,
        permission_sensitive=False,
        depends_on=["browser.safari_visible_click_fixture"],
    ),
    LiveValidationClaim(
        claim_id="canvas.kleki_visible_readiness",
        family="canvas_drawing_tasks",
        phase="C",
        title="Kleki visible readiness",
        capability_claim="Concentric can bring Kleki into a visible, capturable, evidence-gated ready state for bounded drawing.",
        required_substrate=["Safari", "Kleki", "GUI evidence"],
        required_profile="live",
        harness="canvas_readiness",
        live_task_recipe=[
            "Open Kleki in Safari.",
            "Verify the page is visibly ready and capturable.",
        ],
        expected_evidence=[
            "visible_capture",
            "canvas_page_title",
            "canvas_url",
        ],
        success_oracle="Kleki is frontmost, capturable, and clearly loaded enough for a bounded drawing task.",
        criticality="high",
        user_visible=True,
        destructive=False,
        permission_sensitive=False,
        depends_on=["browser.safari_visible_click_fixture"],
    ),
    LiveValidationClaim(
        claim_id="canvas.jspaint_visible_readiness",
        family="canvas_drawing_tasks",
        phase="C",
        title="JSPaint visible readiness",
        capability_claim="Concentric can bring JSPaint into a visible, capturable, evidence-gated ready state for bounded drawing.",
        required_substrate=["Safari", "JSPaint", "GUI evidence"],
        required_profile="live",
        harness="canvas_readiness",
        live_task_recipe=[
            "Open JSPaint in Safari.",
            "Verify the page is visibly ready and capturable.",
        ],
        expected_evidence=[
            "visible_capture",
            "canvas_page_title",
            "canvas_url",
        ],
        success_oracle="JSPaint is frontmost, capturable, and clearly loaded enough for a bounded drawing task.",
        criticality="high",
        user_visible=True,
        destructive=False,
        permission_sensitive=False,
        depends_on=["browser.safari_visible_click_fixture"],
    ),
    LiveValidationClaim(
        claim_id="verification.outcome_semantics_contract",
        family="verification_outcome_semantics",
        phase="E",
        title="Outcome semantics contract",
        capability_claim="Run manifests and diagnostics preserve normalized outcome semantics for downstream evaluation.",
        required_substrate=["trace_writer", "diagnostic_reader", "benchmark_evaluator"],
        required_profile="debug",
        harness="verification_contract",
        live_task_recipe=[
            "Build the control-room snapshot and inspect live validation artifacts.",
            "Confirm normalized outcome semantics fields exist where expected.",
        ],
        expected_evidence=[
            "manifest_outcome_semantics",
            "diagnostic_outcome_semantics",
        ],
        success_oracle="Outcome semantics are present and readable without collapsing script success into feature success.",
        criticality="high",
        user_visible=False,
        destructive=False,
        permission_sensitive=False,
        depends_on=["mission.live_profile_health"],
    ),
    LiveValidationClaim(
        claim_id="verification.calibration_artifacts_contract",
        family="verification_outcome_semantics",
        phase="E",
        title="Verification calibration artifacts contract",
        capability_claim="Calibration artifacts remain exportable and distinguish unlabeled vs adjudicated state.",
        required_substrate=["verification_calibration", "artifacts"],
        required_profile="debug",
        harness="calibration_contract",
        live_task_recipe=[
            "Read the calibration summary artifacts.",
            "Confirm candidate records and review packet index remain available.",
        ],
        expected_evidence=[
            "calibration_total_records",
            "calibration_unlabeled",
            "review_packet_index",
        ],
        success_oracle="Calibration artifacts load successfully and preserve label-state distinctions.",
        criticality="medium",
        user_visible=False,
        destructive=False,
        permission_sensitive=False,
        depends_on=["mission.live_profile_health"],
    ),
    LiveValidationClaim(
        claim_id="outer_loop.recovery_contract",
        family="outer_loop_recovery_trust",
        phase="E",
        title="Outer-loop recovery contract",
        capability_claim="The outer loop classifies failures and persists escalation/retry outcomes as structured state.",
        required_substrate=["outer_loop", "healing_orchestrator", "runs"],
        required_profile="debug",
        harness="outer_loop_contract",
        live_task_recipe=[
            "Inspect the outer-loop runtime contracts and fixture traces.",
            "Confirm escalation/retry outputs are structurally readable.",
        ],
        expected_evidence=[
            "outer_loop_contract_ok",
            "healing_classification_fields",
        ],
        success_oracle="Outer-loop and healing outputs remain structurally readable for remediation decisions.",
        criticality="high",
        user_visible=False,
        destructive=False,
        permission_sensitive=False,
        depends_on=["mission.live_profile_health"],
    ),
    LiveValidationClaim(
        claim_id="outer_loop.trust_tracker_contract",
        family="outer_loop_recovery_trust",
        phase="E",
        title="Trust tracker contract",
        capability_claim="Trust-tracker persistence remains readable and preserves skip/verify semantics.",
        required_substrate=["action_trust", "persisted trust state"],
        required_profile="debug",
        harness="trust_contract",
        live_task_recipe=[
            "Read the trust tracker persistence file.",
            "Confirm records remain structured enough to explain verify/skip behavior.",
        ],
        expected_evidence=[
            "trust_records_present",
            "trust_schema_readable",
        ],
        success_oracle="The trust tracker persistence remains readable and keyed enough for runtime decisions.",
        criticality="medium",
        user_visible=False,
        destructive=False,
        permission_sensitive=False,
        depends_on=["mission.live_profile_health"],
    ),
    LiveValidationClaim(
        claim_id="security.auth_surface_classifier",
        family="security_auth",
        phase="D",
        title="Auth surface classifier contract",
        capability_claim="The auth-workflow layer classifies login/signup/2FA observations into explicit intents.",
        required_substrate=["security.auth_workflow"],
        required_profile="debug",
        harness="auth_surface_contract",
        live_task_recipe=[
            "Run representative auth-surface observations through the classifier.",
            "Confirm the resulting intents and plans are structurally valid.",
        ],
        expected_evidence=[
            "auth_classifier_cases",
            "auth_plan_steps",
        ],
        success_oracle="Representative auth observations classify into explicit workflow intents and plans.",
        criticality="high",
        user_visible=False,
        destructive=False,
        permission_sensitive=True,
        depends_on=["mission.live_profile_health"],
    ),
]


def all_claims() -> list[LiveValidationClaim]:
    return list(CLAIMS)


def claim_map() -> dict[str, LiveValidationClaim]:
    return {claim.claim_id: claim for claim in CLAIMS}


def claim_by_id(claim_id: str) -> LiveValidationClaim:
    return claim_map()[claim_id]


def claims_by_family(family: str) -> list[LiveValidationClaim]:
    return [claim for claim in CLAIMS if claim.family == family]


def claims_in_order() -> list[str]:
    preferred_order = [
        "mission.live_profile_health",
        "gui.safari_visible_readiness",
        "browser.safari_visible_click_fixture",
        "web.public_navigation_workflow",
        "puzzle.mysterymaster_page_readiness",
        "mission.architecture_profile_health",
        "canvas.excalidraw_visible_readiness",
        "canvas.kleki_visible_readiness",
        "canvas.jspaint_visible_readiness",
        "verification.outcome_semantics_contract",
        "verification.calibration_artifacts_contract",
        "outer_loop.recovery_contract",
        "outer_loop.trust_tracker_contract",
        "security.auth_surface_classifier",
    ]
    registry_ids = {claim.claim_id for claim in CLAIMS}
    ordered = [claim_id for claim_id in preferred_order if claim_id in registry_ids]
    for claim in CLAIMS:
        if claim.claim_id not in ordered:
            ordered.append(claim.claim_id)
    return ordered


def registry_snapshot() -> dict[str, Any]:
    families = sorted({claim.family for claim in CLAIMS})
    return {
        "families": families,
        "claims": [claim.to_dict() for claim in CLAIMS],
        "claim_count": len(CLAIMS),
    }
