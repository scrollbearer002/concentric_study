"""Security hardening modules for the visual web agent.

Provides input sanitization, credential vault integration, and
human-in-the-loop escalation for sensitive actions.
"""

from security.auth_workflow import (
    AuthSurfaceObservation,
    AuthWorkflowContext,
    AuthWorkflowPlan,
    classify_auth_surface,
    plan_auth_workflow,
)
from security.sanitizer import InputSanitizer, SanitizationResult
from security.credential_vault import CredentialVault

__all__ = [
    "AuthSurfaceObservation",
    "AuthWorkflowContext",
    "AuthWorkflowPlan",
    "InputSanitizer",
    "SanitizationResult",
    "CredentialVault",
    "classify_auth_surface",
    "plan_auth_workflow",
]
