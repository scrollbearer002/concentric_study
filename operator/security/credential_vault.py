"""Credential vault integration via macOS Keychain.

Provides secure credential retrieval for the visual web agent without
exposing secrets in traces, logs, VLM prompts, or skill library entries.

Uses the macOS `security` CLI to interact with the system Keychain.
Credentials are fetched by domain name and returned through a secure
channel that is never serialised to any persistent storage.

Research basis:
- Vault Whisper Attack (2026): Credential extraction via adversarial
  prompts against multi-agent payment systems
- AgentBound (2025): First access control framework for MCP servers
- Magentic-UI (2025): Formalised HITL protocols for co-planning and
  action guards on sensitive operations
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import Any


@dataclass
class Credential:
    """A retrieved credential. Never serialise this to logs or traces."""
    domain: str
    username: str
    _password: str

    @property
    def password(self) -> str:
        return self._password

    def __repr__(self) -> str:
        return f"Credential(domain={self.domain!r}, username={self.username!r}, password=***)"

    def to_safe_dict(self) -> dict[str, str]:
        """Return a dict safe for logging (no password)."""
        return {"domain": self.domain, "username": self.username, "has_password": "yes"}


_SENSITIVE_ACTIONS = {
    "submit_form",
    "enter_password",
    "navigate_to_unknown",
    "execute_terminal",
    "download_file",
    "upload_file",
}


class CredentialVault:
    """Interface to macOS Keychain for secure credential retrieval.

    Credentials are never written to any trace, log, VLM prompt,
    or SkillLibrary entry.  The vault only responds to explicit
    domain-based lookups.
    """

    def __init__(self, allowed_domains: list[str] | None = None) -> None:
        self._allowed = set(allowed_domains) if allowed_domains else None
        self._access_log: list[dict[str, str]] = []

    def retrieve(self, domain: str) -> Credential | None:
        """Retrieve credentials for a domain from macOS Keychain.

        Returns None if no credentials are found or if the domain
        is not in the allowed list.
        """
        if self._allowed is not None and domain not in self._allowed:
            self._log_access(domain, "denied_not_allowed")
            return None

        try:
            result = subprocess.run(
                [
                    "security", "find-internet-password",
                    "-s", domain,
                    "-g",
                ],
                capture_output=True, text=True, timeout=5,
            )

            if result.returncode != 0:
                self._log_access(domain, "not_found")
                return None

            username = ""
            password = ""
            for line in result.stdout.splitlines() + result.stderr.splitlines():
                line = line.strip()
                if '"acct"' in line:
                    username = self._extract_value(line)
                elif line.startswith("password:"):
                    password = line.split(":", 1)[1].strip().strip('"')

            if username:
                self._log_access(domain, "retrieved")
                return Credential(domain=domain, username=username, _password=password)

            self._log_access(domain, "parse_failed")
            return None

        except subprocess.TimeoutExpired:
            self._log_access(domain, "timeout")
            return None
        except FileNotFoundError:
            self._log_access(domain, "security_cli_not_found")
            return None
        except Exception:
            self._log_access(domain, "error")
            return None

    def requires_approval(self, action_type: str) -> bool:
        """Check if an action requires human-in-the-loop approval."""
        return action_type in _SENSITIVE_ACTIONS

    def get_access_log(self) -> list[dict[str, str]]:
        """Return the audit log (no passwords ever appear here)."""
        return list(self._access_log)

    def add_allowed_domain(self, domain: str) -> None:
        if self._allowed is None:
            self._allowed = set()
        self._allowed.add(domain)

    def _log_access(self, domain: str, status: str) -> None:
        import time
        self._access_log.append({
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "domain": domain,
            "status": status,
        })

    @staticmethod
    def _extract_value(line: str) -> str:
        """Extract the value from a Keychain dump line like '    "acct"<blob>="user@example.com"'."""
        if '=' in line:
            val = line.split('=', 1)[1].strip().strip('"')
            return val
        return ""


class HITLGuard:
    """Human-in-the-loop guard for sensitive actions.

    When the agent encounters a sensitive action (password field,
    form submission, terminal command, unknown domain), execution
    pauses and the guard generates an escalation request.
    """

    def __init__(self, escalation_dir: str | None = None) -> None:
        self._escalation_dir = escalation_dir
        self._pending: list[dict[str, Any]] = []

    def check_action(
        self,
        action_type: str,
        context: dict[str, Any],
        sanitizer_result: Any = None,
    ) -> dict[str, Any]:
        """Evaluate whether an action needs human approval.

        Returns a dict with 'requires_approval' boolean and 'reason'.
        """
        reasons: list[str] = []

        if action_type in _SENSITIVE_ACTIONS:
            reasons.append(f"Action '{action_type}' is classified as sensitive")

        a11y_role = context.get("a11y_role", "")
        if a11y_role in ("AXTextField",) and context.get("type") == "password":
            reasons.append("Password field detected")

        if sanitizer_result and hasattr(sanitizer_result, "is_safe") and not sanitizer_result.is_safe:
            reasons.append(f"Content failed sanitization: {sanitizer_result.threats_detected}")

        domain = context.get("domain", "")
        if domain and context.get("is_new_domain", False):
            reasons.append(f"Navigating to unverified domain: {domain}")

        return {
            "requires_approval": len(reasons) > 0,
            "reasons": reasons,
            "action_type": action_type,
            "context_summary": {
                k: v for k, v in context.items()
                if k not in ("password", "credential", "secret")
            },
        }

    def request_approval(self, check_result: dict[str, Any]) -> None:
        """Queue an approval request for human review."""
        self._pending.append(check_result)

    def get_pending(self) -> list[dict[str, Any]]:
        return list(self._pending)

    def clear_pending(self) -> None:
        self._pending.clear()
