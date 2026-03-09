"""Site-independent auth workflow classification and credential routing.

This module does not touch live secrets. It translates observed auth-page
signals into an intent classification and a credential-handling plan so the
agent can reuse the same policy across websites.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Literal
from urllib.parse import urlparse


AuthSurfaceIntent = Literal[
    "login_existing",
    "signup_new",
    "password_reset_request",
    "password_change",
    "two_factor_challenge",
    "passkey_enrollment",
    "account_profile",
    "unknown",
]

CredentialProvider = Literal[
    "proton_pass",
    "macos_keychain",
    "manual",
    "none",
]


def _normalize(text: str) -> str:
    return " ".join(text.lower().split())


def _domain_from_url(url: str) -> str:
    parsed = urlparse(url)
    return parsed.netloc.lower()


@dataclass(frozen=True)
class AuthSurfaceObservation:
    """Minimal website-independent auth cues observed on a page."""

    url: str
    visible_text: str = ""
    heading_text: str = ""
    submit_labels: tuple[str, ...] = ()
    has_email_field: bool = False
    has_username_field: bool = False
    has_password_field: bool = False
    has_confirm_password_field: bool = False
    has_current_password_field: bool = False
    has_totp_field: bool = False
    has_passkey_button: bool = False
    is_logged_in_profile: bool = False

    @property
    def domain(self) -> str:
        return _domain_from_url(self.url)

    def normalized_text(self) -> str:
        bits = [self.visible_text, self.heading_text, " ".join(self.submit_labels)]
        return _normalize(" ".join(bit for bit in bits if bit))


@dataclass(frozen=True)
class AuthWorkflowContext:
    """Execution context for choosing a credential workflow."""

    observation: AuthSurfaceObservation
    provider: CredentialProvider
    has_existing_credential: bool = False
    proton_pass_available: bool = False
    proton_pass_unlocked: bool = False
    proton_pass_alias_available: bool = False
    wants_alias: bool = False
    wants_passkey: bool = False
    site_supports_passkey: bool = False
    is_new_domain: bool = False


@dataclass(frozen=True)
class AuthWorkflowPlan:
    """Resolved site-independent plan for auth and credential handling."""

    surface_intent: AuthSurfaceIntent
    provider: CredentialProvider
    generalization_family: str
    credential_operation: str
    recommended_steps: tuple[str, ...]
    sensitive_actions: tuple[str, ...]
    requires_hitl: bool
    blocked_reason: str | None = None
    rationale: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def classify_auth_surface(observation: AuthSurfaceObservation) -> AuthSurfaceIntent:
    """Classify an auth surface from website-independent structural cues."""

    if observation.is_logged_in_profile:
        return "account_profile"

    text = observation.normalized_text()

    if observation.has_totp_field or any(
        token in text
        for token in (
            "verification code",
            "two-factor",
            "2fa",
            "authenticator",
            "one-time password",
            "otp",
        )
    ):
        return "two_factor_challenge"

    if observation.has_current_password_field and observation.has_password_field:
        return "password_change"

    if any(token in text for token in ("forgot password", "reset password")) and not observation.has_password_field:
        return "password_reset_request"

    if observation.has_passkey_button or "passkey" in text:
        return "passkey_enrollment"

    if observation.has_confirm_password_field or any(
        token in text for token in ("sign up", "signup", "create account", "register", "join now")
    ):
        return "signup_new"

    if observation.has_password_field and (observation.has_email_field or observation.has_username_field):
        return "login_existing"

    return "unknown"


def plan_auth_workflow(context: AuthWorkflowContext) -> AuthWorkflowPlan:
    """Choose the credential workflow that should be used on this page."""

    intent = classify_auth_surface(context.observation)
    domain = context.observation.domain
    provider = context.provider
    new_domain_note = " The domain is new and must stay human-approved." if context.is_new_domain else ""

    if intent == "unknown":
        return AuthWorkflowPlan(
            surface_intent=intent,
            provider=provider,
            generalization_family="unclassified_auth_surface",
            credential_operation="manual_triage",
            recommended_steps=(
                "capture_dom_and_visual_evidence",
                "classify_page_before_any_secret_use",
                "ask_for_human_confirmation",
            ),
            sensitive_actions=("navigate_to_unknown",) if context.is_new_domain else (),
            requires_hitl=context.is_new_domain,
            blocked_reason="Surface not confidently classified.",
            rationale="The observed cues do not yet distinguish login, signup, reset, or 2FA reliably.",
        )

    if intent == "login_existing":
        if provider == "proton_pass" and context.proton_pass_available:
            blocked_reason = None
            if not context.has_existing_credential:
                blocked_reason = f"No Proton Pass login is known for {domain}."
            elif not context.proton_pass_unlocked:
                blocked_reason = "Proton Pass is not unlocked in the current browser session."
            return AuthWorkflowPlan(
                surface_intent=intent,
                provider=provider,
                generalization_family="existing_credential_login",
                credential_operation="retrieve_existing_login",
                recommended_steps=(
                    "verify_domain_matches_target",
                    "open_proton_pass",
                    "select_existing_profile",
                    "fill_identifier",
                    "fill_password",
                    "submit_login",
                ),
                sensitive_actions=(
                    "retrieve_password_manager_secret",
                    "enter_password",
                    "submit_form",
                ),
                requires_hitl=True,
                blocked_reason=blocked_reason,
                rationale=(
                    "Existing-account login should prefer a domain-matched password-manager retrieval path."
                    + new_domain_note
                ),
            )

        if provider == "macos_keychain" and context.has_existing_credential:
            return AuthWorkflowPlan(
                surface_intent=intent,
                provider=provider,
                generalization_family="existing_credential_login",
                credential_operation="retrieve_existing_login",
                recommended_steps=(
                    "verify_domain_matches_target",
                    "retrieve_keychain_credential",
                    "fill_identifier",
                    "fill_password",
                    "submit_login",
                ),
                sensitive_actions=("enter_password", "submit_form"),
                requires_hitl=True,
                rationale=(
                    "The Keychain path is a fallback when a browser password manager is unavailable."
                    + new_domain_note
                ),
            )

        return AuthWorkflowPlan(
            surface_intent=intent,
            provider=provider,
            generalization_family="existing_credential_login",
            credential_operation="manual_login_required",
            recommended_steps=("confirm_credential_source", "fill_identifier", "fill_password", "submit_login"),
            sensitive_actions=("enter_password", "submit_form"),
            requires_hitl=True,
            blocked_reason=f"No approved credential source is ready for {domain}.",
            rationale="Login can be recognized, but not executed safely until an approved credential source is available.",
        )

    if intent == "signup_new":
        if provider == "proton_pass" and context.proton_pass_available:
            identifier_step = "create_hide_my_email_alias" if context.wants_alias and context.proton_pass_alias_available else "fill_email_or_username"
            blocked_reason = None if context.proton_pass_unlocked else "Proton Pass is not unlocked in the current browser session."
            return AuthWorkflowPlan(
                surface_intent=intent,
                provider=provider,
                generalization_family="new_account_signup_and_save",
                credential_operation="generate_and_save_new_login",
                recommended_steps=(
                    "verify_domain_matches_target",
                    identifier_step,
                    "generate_password",
                    "fill_registration_form",
                    "save_login_in_proton_pass",
                    "submit_signup",
                ),
                sensitive_actions=(
                    "generate_password",
                    "save_password_manager_secret",
                    "create_password_manager_login",
                    "submit_form",
                ),
                requires_hitl=True,
                blocked_reason=blocked_reason,
                rationale=(
                    "New-account signup should couple password generation with immediate password-manager persistence."
                    + new_domain_note
                ),
            )

        return AuthWorkflowPlan(
            surface_intent=intent,
            provider=provider,
            generalization_family="new_account_signup_and_save",
            credential_operation="manual_signup_required",
            recommended_steps=("fill_identifier", "generate_password", "save_login", "submit_signup"),
            sensitive_actions=("generate_password", "submit_form"),
            requires_hitl=True,
            blocked_reason="A write-capable password-manager path is not available.",
            rationale="Signup without safe secret persistence is not acceptable for a real production workflow.",
        )

    if intent == "password_change":
        return AuthWorkflowPlan(
            surface_intent=intent,
            provider=provider,
            generalization_family="credential_rotation",
            credential_operation="rotate_and_update_password",
            recommended_steps=(
                "retrieve_existing_credential",
                "generate_password",
                "fill_current_password",
                "fill_new_password",
                "update_password_manager_record",
                "submit_change",
            ),
            sensitive_actions=(
                "retrieve_password_manager_secret",
                "generate_password",
                "save_password_manager_secret",
                "submit_form",
            ),
            requires_hitl=True,
            rationale="Password rotation is a dual-secret workflow and should never run without approval.",
        )

    if intent == "password_reset_request":
        return AuthWorkflowPlan(
            surface_intent=intent,
            provider=provider,
            generalization_family="credential_recovery",
            credential_operation="request_password_reset",
            recommended_steps=("fill_identifier", "submit_reset_request", "wait_for_recovery_channel"),
            sensitive_actions=("submit_form",),
            requires_hitl=True,
            rationale="Password reset requests are low-complexity but still safety-relevant because they affect account access.",
        )

    if intent == "two_factor_challenge":
        return AuthWorkflowPlan(
            surface_intent=intent,
            provider=provider,
            generalization_family="secondary_factor_auth",
            credential_operation="retrieve_and_fill_second_factor",
            recommended_steps=(
                "retrieve_totp_or_device_challenge",
                "fill_verification_code",
                "submit_verification",
            ),
            sensitive_actions=("retrieve_totp_code", "submit_form"),
            requires_hitl=True,
            rationale="2FA is a separate credential channel and should remain explicitly gated.",
        )

    if intent == "passkey_enrollment":
        blocked_reason = None
        if not context.site_supports_passkey:
            blocked_reason = "The site does not expose a confirmed passkey path."
        elif provider != "proton_pass" or not context.proton_pass_available:
            blocked_reason = "No approved passkey-capable provider is available."
        return AuthWorkflowPlan(
            surface_intent=intent,
            provider=provider,
            generalization_family="passkey_enrollment",
            credential_operation="create_and_register_passkey",
            recommended_steps=(
                "verify_domain_matches_target",
                "open_passkey_provider",
                "create_passkey",
                "approve_registration",
            ),
            sensitive_actions=("create_passkey", "submit_form"),
            requires_hitl=True,
            blocked_reason=blocked_reason,
            rationale="Passkeys are first-class credentials and need an approved provider and domain confirmation.",
        )

    return AuthWorkflowPlan(
        surface_intent=intent,
        provider=provider,
        generalization_family="account_profile_state",
        credential_operation="no_secret_action",
        recommended_steps=("inspect_profile_state", "decide_if_switch_or_logout_is_needed"),
        sensitive_actions=(),
        requires_hitl=False,
        rationale="A logged-in profile page should not trigger credential retrieval automatically.",
    )
