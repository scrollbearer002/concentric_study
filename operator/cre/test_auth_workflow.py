from __future__ import annotations

from security.auth_workflow import (
    AuthSurfaceObservation,
    AuthWorkflowContext,
    classify_auth_surface,
    plan_auth_workflow,
)
from security.credential_vault import HITLGuard


def test_classify_login_surface_from_generic_cues() -> None:
    observation = AuthSurfaceObservation(
        url="https://example.com/login",
        heading_text="Sign in",
        submit_labels=("Continue",),
        has_email_field=True,
        has_password_field=True,
    )
    assert classify_auth_surface(observation) == "login_existing"


def test_classify_signup_surface_from_confirm_password_and_copy() -> None:
    observation = AuthSurfaceObservation(
        url="https://example.com/register",
        heading_text="Create your account",
        submit_labels=("Create account",),
        has_email_field=True,
        has_password_field=True,
        has_confirm_password_field=True,
    )
    assert classify_auth_surface(observation) == "signup_new"


def test_classify_two_factor_surface_from_textual_signal() -> None:
    observation = AuthSurfaceObservation(
        url="https://example.com/challenge",
        visible_text="Enter the verification code from your authenticator app",
        submit_labels=("Verify",),
        has_totp_field=True,
    )
    assert classify_auth_surface(observation) == "two_factor_challenge"


def test_plan_login_with_proton_pass_uses_existing_credential_path() -> None:
    observation = AuthSurfaceObservation(
        url="https://example.com/login",
        heading_text="Log in",
        has_email_field=True,
        has_password_field=True,
    )
    plan = plan_auth_workflow(
        AuthWorkflowContext(
            observation=observation,
            provider="proton_pass",
            has_existing_credential=True,
            proton_pass_available=True,
            proton_pass_unlocked=True,
        )
    )
    assert plan.surface_intent == "login_existing"
    assert plan.generalization_family == "existing_credential_login"
    assert plan.credential_operation == "retrieve_existing_login"
    assert "retrieve_password_manager_secret" in plan.sensitive_actions
    assert plan.blocked_reason is None


def test_plan_signup_with_proton_pass_prefers_generate_and_save() -> None:
    observation = AuthSurfaceObservation(
        url="https://example.com/signup",
        heading_text="Sign up",
        submit_labels=("Create account",),
        has_email_field=True,
        has_password_field=True,
        has_confirm_password_field=True,
    )
    plan = plan_auth_workflow(
        AuthWorkflowContext(
            observation=observation,
            provider="proton_pass",
            proton_pass_available=True,
            proton_pass_unlocked=True,
            proton_pass_alias_available=True,
            wants_alias=True,
        )
    )
    assert plan.surface_intent == "signup_new"
    assert plan.generalization_family == "new_account_signup_and_save"
    assert plan.credential_operation == "generate_and_save_new_login"
    assert plan.recommended_steps[1] == "create_hide_my_email_alias"
    assert "save_password_manager_secret" in plan.sensitive_actions


def test_plan_passkey_enrollment_requires_confirmed_provider() -> None:
    observation = AuthSurfaceObservation(
        url="https://example.com/security",
        heading_text="Create a passkey",
        submit_labels=("Create passkey",),
        has_passkey_button=True,
    )
    plan = plan_auth_workflow(
        AuthWorkflowContext(
            observation=observation,
            provider="proton_pass",
            proton_pass_available=True,
            proton_pass_unlocked=True,
            site_supports_passkey=True,
            wants_passkey=True,
        )
    )
    assert plan.surface_intent == "passkey_enrollment"
    assert plan.credential_operation == "create_and_register_passkey"
    assert plan.blocked_reason is None
    assert "create_passkey" in plan.sensitive_actions


def test_hitl_guard_requires_approval_for_password_manager_retrieval() -> None:
    guard = HITLGuard()
    result = guard.check_action(
        "retrieve_password_manager_secret",
        {"domain": "example.com", "credential_provider": "proton_pass"},
    )
    assert result["requires_approval"] is True
    assert any("Credential provider involved: proton_pass" == reason for reason in result["reasons"])


def test_hitl_guard_requires_approval_for_password_manager_save() -> None:
    guard = HITLGuard()
    result = guard.check_action(
        "save_password_manager_secret",
        {"domain": "example.com", "credential_provider": "proton_pass"},
    )
    assert result["requires_approval"] is True
    assert any("Action 'save_password_manager_secret' is classified as sensitive" == reason for reason in result["reasons"])
