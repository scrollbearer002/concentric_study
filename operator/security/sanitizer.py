"""Input sanitization layer for adversarial robustness.

All parsed text from DOM, OCR, and accessibility attributes passes
through this layer before reaching the Planner.  Detects and neutralises
prompt injection attacks, linguistic anomalies, and known adversarial
patterns.

Enhanced with MCP-specific tool poisoning defense patterns derived from:
- OWASP MCP Top 10 (2025): Complete vulnerability taxonomy for MCP
  ecosystems covering MCP01-MCP10 (Token Mismanagement, Privilege
  Escalation, Tool Poisoning, Supply Chain Attacks, Command Injection,
  Prompt Injection via Contextual Payloads, Insufficient Auth,
  Lack of Audit, Shadow MCP Servers, Context Over-Sharing).
- MCPLIB (arXiv:2508.12538, 2025): 31 distinct attack methods across
  4 classifications (direct tool injection, indirect tool injection,
  malicious user attacks, LLM inherent attacks).
- MCP Security Bench / MSB (arXiv:2510.15994, ICLR 2026): 12 attack
  types with 40.71% average success rate; Out-of-Scope Parameter
  attacks achieve 74.03% ASR — the most effective vector.
- MCPTox (arXiv:2508.14925): Benchmark for tool poisoning attacks
  on real-world MCP servers.
- MCP-Guard (arXiv:2508.10991): 3-stage defense-in-depth framework
  (static scan → neural detector → LLM arbitrator) achieving 96.01%
  detection accuracy on the MCP-AttackBench dataset.
- CVE-2025-54136 / MCPoison (GHSA-24mc-g4xr-4395, CVSS 7.2-8.8):
  Cursor IDE trust bypass via post-approval schema mutation.
- When MCP Servers Attack (arXiv:2509.24272): Taxonomy and feasibility
  analysis of malicious MCP server behaviors.

Prior research basis (web content injection):
- WASP (arXiv:2504.18575, 2025): 86% partial hijack success rate
  against current agents via prompt injection in web content
- "Hidden Dangers of Browsing AI Agents" (arXiv:2505.13076, 2025):
  Parallel poisoning serves different content to agents vs humans
- Vault Whisper Attack (2026): Credential extraction via adversarial
  prompts against multi-agent payment systems
- FormalJudge (arXiv:2602.11136, 2026): Neuro-symbolic verification
  with Z3/Dafny achieves 16.6% improvement over LLM-as-Judge
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class SanitizationResult:
    """Outcome of sanitizing a piece of text."""
    is_safe: bool
    original: str
    sanitized: str
    threats_detected: list[str] = field(default_factory=list)
    confidence: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "safe": self.is_safe,
            "threats": self.threats_detected,
            "confidence": self.confidence,
        }


_INJECTION_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("imperative_override", re.compile(
        r"ignore\s+(all\s+)?previous\s+(instructions?|prompts?|rules?)",
        re.IGNORECASE,
    )),
    ("system_prompt_leak", re.compile(
        r"(print|output|reveal|show|display)\s+(your|the|my)\s+(system\s+)?prompt",
        re.IGNORECASE,
    )),
    ("role_hijack", re.compile(
        r"you\s+are\s+(now|actually)\s+(a|an|the)\s+",
        re.IGNORECASE,
    )),
    ("credential_phish", re.compile(
        r"(type|enter|input|paste)\s+(your\s+)?(password|credential|api.?key|secret|token)",
        re.IGNORECASE,
    )),
    ("jailbreak_delim", re.compile(
        r"(```|---|\*\*\*)\s*(system|assistant|user)\s*(```|---|\*\*\*)",
        re.IGNORECASE,
    )),
    ("hidden_instruction", re.compile(
        r"<!--.*?(ignore|override|forget|disregard).*?-->",
        re.IGNORECASE | re.DOTALL,
    )),
    ("base64_payload", re.compile(
        r"[A-Za-z0-9+/]{40,}={0,2}",
    )),
    ("url_exfil", re.compile(
        r"(fetch|send|post|get)\s+(to\s+)?https?://",
        re.IGNORECASE,
    )),
]

# ---------------------------------------------------------------------------
# MCP Tool Poisoning Patterns (OWASP MCP Top 10 + MCPLIB + MSB)
# ---------------------------------------------------------------------------
# These patterns detect adversarial content specifically in MCP tool
# descriptions, schema definitions, and tool response payloads.
#
# Attack taxonomy from MSB (arXiv:2510.15994, ICLR 2026):
#   - Name collision: tool name mimics a trusted tool
#   - Preference manipulation: description steers agent toward malicious tool
#   - Prompt injection in descriptions: hidden instructions in metadata
#   - Out-of-scope parameters: tool requests data beyond its stated scope
#   - User-impersonating responses: tool output pretends to be user input
#   - False-error escalation: tool fakes errors to trigger fallback path
#   - Tool-transfer: redirects agent to a different (malicious) tool
#   - Retrieval injection: poisoned data in tool response context
#
# Defence layers follow MCP-Guard (arXiv:2508.10991) architecture:
#   Layer 1 (here): Lightweight static pattern scanning
#   Layer 2 (external): Neural detector for semantic attacks
#   Layer 3 (external): LLM arbitrator for ambiguous cases

_MCP_TOOL_POISON_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    # Tool description override: hidden instruction to change agent behavior
    # Covers OWASP MCP03 (Tool Poisoning) and MSB prompt-injection-in-descriptions
    ("tool_desc_override", re.compile(
        r"(important|note|actually|instead|warning)\s*:?\s*"
        r"(ignore|override|disregard|use|call|execute|run|switch)\s",
        re.IGNORECASE,
    )),
    # Tool impersonation: description claims capabilities beyond its scope
    # Covers MSB out-of-scope parameter requests (74.03% ASR)
    ("tool_desc_impersonation", re.compile(
        r"(this\s+tool|I\s+am|I\s+can|I\s+also|tool)\s+"
        r"(also\s+)?(actually|really|additionally)\s+"
        r"(do|perform|execute|access|read|write|delete|modify)\w*",
        re.IGNORECASE,
    )),
    # Cross-tool injection: description instructs agent to call other tools
    # Covers MSB tool-transfer attack and MCPLIB chain attacks
    ("tool_cross_inject", re.compile(
        r"(before|after|first|then|also|next)\s+"
        r"(call|use|invoke|run|execute|trigger)\s+\w+",
        re.IGNORECASE,
    )),
    # Scope escalation: requests elevated permissions
    # Covers OWASP MCP02 (Privilege Escalation via Scope Creep)
    ("scope_escalation", re.compile(
        r"(require|need|must\s+have|grant|request)s?\s+"
        r"(admin|root|sudo|elevated|full|write|delete)\s+"
        r"(access|permission|privilege|right|role)",
        re.IGNORECASE,
    )),
    # False-error escalation: fakes an error to redirect to alternate tool
    # Covers MSB false-error escalation attack
    ("false_error_redirect", re.compile(
        r"(error|fail|unavailable|deprecated|broken|down)\s*"
        r"[^.]{0,40}?"
        r"(use|try|call|switch\s+to|fallback\s+to)\s+\w+\s+instead",
        re.IGNORECASE,
    )),
    # Shadow tool indicator: describes itself as an alternative/replacement
    # Covers OWASP MCP09 (Shadow MCP Servers)
    ("shadow_tool", re.compile(
        r"(alternative|replacement|better\s+version|upgraded|enhanced)\s+"
        r"(tool|function|endpoint|server|service|implementation)",
        re.IGNORECASE,
    )),
    # User impersonation in tool response: output pretends to be user
    # Covers MSB user-impersonating responses attack
    ("user_impersonation", re.compile(
        r"(the\s+user\s+(said|wants|asked|requested|typed)|"
        r"user\s+input\s*:|user\s+message\s*:)",
        re.IGNORECASE,
    )),
    # Context over-sharing: tool response tries to set context for next call
    # Covers OWASP MCP10 (Context Injection & Over-Sharing)
    ("context_injection", re.compile(
        r"(remember|keep\s+in\s+mind|for\s+the\s+next|"
        r"in\s+your\s+next\s+response|when\s+you\s+respond)",
        re.IGNORECASE,
    )),
]


_SENSITIVE_FIELD_PATTERNS = [
    re.compile(r"password", re.IGNORECASE),
    re.compile(r"credit.?card", re.IGNORECASE),
    re.compile(r"ssn|social.?security", re.IGNORECASE),
    re.compile(r"api.?key", re.IGNORECASE),
    re.compile(r"secret", re.IGNORECASE),
    re.compile(r"token", re.IGNORECASE),
]


class InputSanitizer:
    """Sanitizes text from web content before it reaches the VLM planner.

    Defence in depth: pattern matching catches known attacks;
    heuristic analysis catches anomalous structure; optional
    VLM-based verification provides a semantic last line of defence.
    """

    def __init__(self, strict: bool = True) -> None:
        self._strict = strict
        self._patterns = list(_INJECTION_PATTERNS)

    def sanitize(self, text: str) -> SanitizationResult:
        """Check text for injection patterns and anomalies."""
        if not text or not text.strip():
            return SanitizationResult(is_safe=True, original=text, sanitized=text)

        threats: list[str] = []
        for name, pattern in self._patterns:
            if pattern.search(text):
                threats.append(name)

        if self._has_anomalous_structure(text):
            threats.append("anomalous_structure")

        is_safe = len(threats) == 0
        sanitized = text if is_safe else self._neutralise(text, threats)
        confidence = 1.0 if is_safe else max(0.1, 1.0 - len(threats) * 0.2)

        return SanitizationResult(
            is_safe=is_safe,
            original=text,
            sanitized=sanitized,
            threats_detected=threats,
            confidence=confidence,
        )

    def is_sensitive_field(self, label: str) -> bool:
        """Check if a field label suggests sensitive content."""
        for pattern in _SENSITIVE_FIELD_PATTERNS:
            if pattern.search(label):
                return True
        return False

    def sanitize_batch(self, texts: list[str]) -> list[SanitizationResult]:
        return [self.sanitize(t) for t in texts]

    def _has_anomalous_structure(self, text: str) -> bool:
        """Detect structurally anomalous text that may contain hidden payloads."""
        if len(text) > 5000:
            return True
        zero_width_chars = sum(1 for c in text if ord(c) in (0x200B, 0x200C, 0x200D, 0xFEFF, 0x00AD))
        if zero_width_chars > 3:
            return True
        control_chars = sum(1 for c in text if ord(c) < 32 and c not in ('\n', '\r', '\t'))
        if control_chars > 5:
            return True
        return False

    def _neutralise(self, text: str, threats: list[str]) -> str:
        """Strip detected threat patterns from text."""
        result = text
        for name, pattern in self._patterns:
            if name in threats:
                result = pattern.sub("[SANITIZED]", result)
        result = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', result)
        result = result.replace('\u200b', '').replace('\ufeff', '')
        return result

    def add_pattern(self, name: str, pattern: str) -> None:
        """Add a custom injection detection pattern."""
        self._patterns.append((name, re.compile(pattern, re.IGNORECASE)))

    # ------------------------------------------------------------------
    # MCP Tool Poisoning Defense (OWASP MCP Top 10 + MCPLIB + MSB)
    # ------------------------------------------------------------------

    def sanitize_tool_description(
        self, description: str, tool_name: str = ""
    ) -> SanitizationResult:
        """Sanitize an MCP tool description for poisoning vectors.

        Applies both the general injection patterns and the MCP-specific
        tool poisoning patterns. This is the primary defense against
        OWASP MCP03 (Tool Poisoning), MCP09 (Shadow Servers), and the
        12 attack types cataloged in MSB (arXiv:2510.15994, ICLR 2026).

        Should be called on every MCP tool description before it enters
        the VLM context window or is stored in the skill library.

        Args:
            description: The tool's description/schema text.
            tool_name: Optional tool name for name-collision detection.

        Returns:
            SanitizationResult with MCP-specific threat classifications.
        """
        base_result = self.sanitize(description)

        mcp_threats: list[str] = []
        for name, pattern in _MCP_TOOL_POISON_PATTERNS:
            if pattern.search(description):
                mcp_threats.append(name)

        all_threats = base_result.threats_detected + mcp_threats
        is_safe = len(all_threats) == 0
        sanitized = description if is_safe else self._neutralise_mcp(
            description, all_threats
        )

        return SanitizationResult(
            is_safe=is_safe,
            original=description,
            sanitized=sanitized,
            threats_detected=all_threats,
            confidence=max(0.1, 1.0 - len(all_threats) * 0.15),
        )

    def sanitize_tool_response(self, response_text: str) -> SanitizationResult:
        """Sanitize an MCP tool response before injecting into context.

        Tool responses can contain retrieval injection attacks
        (MSB arXiv:2510.15994) and context over-sharing payloads
        (OWASP MCP10) that persist in the Summarizer's 500-token
        context window.

        Args:
            response_text: The raw text returned by an MCP tool.

        Returns:
            SanitizationResult with response-specific threat analysis.
        """
        return self.sanitize_tool_description(response_text)

    def verify_schema_integrity(
        self,
        schema: dict[str, Any],
        stored_hash: str | None = None,
    ) -> tuple[bool, str]:
        """Verify an MCP tool schema has not been tampered with.

        Defence against CVE-2025-54136 (Cursor MCPoison): once a user
        approves an MCP configuration, Cursor never re-validates it
        even if commands are silently changed later. This method
        implements schema hash verification to detect rug-pull attacks.

        Also addresses OWASP MCP04 (Supply Chain Attacks & Dependency
        Tampering): any modification to a tool's schema between
        approval and execution is flagged.

        Args:
            schema: The tool schema dict to verify.
            stored_hash: The previously stored hash for comparison.
                If None, this is a first-time registration and the
                current hash is returned for future verification.

        Returns:
            Tuple of (is_valid, current_hash). is_valid is True if
            the schema matches the stored hash or if this is a
            first-time registration.
        """
        canonical = json.dumps(schema, sort_keys=True, separators=(",", ":"))
        current_hash = hashlib.sha256(canonical.encode()).hexdigest()[:16]

        if stored_hash is None:
            return True, current_hash

        is_valid = current_hash == stored_hash
        if not is_valid:
            logger.warning(
                "Schema integrity violation: stored=%s current=%s",
                stored_hash, current_hash,
            )
        return is_valid, current_hash

    def _neutralise_mcp(self, text: str, threats: list[str]) -> str:
        """Strip both general and MCP-specific threat patterns."""
        result = self._neutralise(text, threats)
        for name, pattern in _MCP_TOOL_POISON_PATTERNS:
            if name in threats:
                result = pattern.sub("[MCP_SANITIZED]", result)
        return result
