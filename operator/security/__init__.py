"""Security hardening modules for the visual web agent.

Provides input sanitization, credential vault integration, and
human-in-the-loop escalation for sensitive actions.
"""

from security.sanitizer import InputSanitizer, SanitizationResult
from security.credential_vault import CredentialVault

__all__ = ["InputSanitizer", "SanitizationResult", "CredentialVault"]
