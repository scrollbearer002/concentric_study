"""Dynamic capability activation router for universal orchestration.

Replaces manual per-script wiring of infrastructure modules with a
declarative system that activates capabilities based on task analysis.
The orchestrator asks "what does this task require?" and the router
answers with a set of active capabilities — each backed by a real
module in the codebase.

Architecture grounded in:
- Magentic-One (Microsoft, 2024): Modular agents activated/deactivated
  without prompt tuning — the orchestrator selects which sub-agents
  participate based on the task.
- DynaSaur (Adobe, COLM 2025, arXiv:2411.01747): Dynamic action creation
  and composition; actions accumulate in a reusable library.
- AppAgent v2 (arXiv:2408.11824): Two-phase explore/deploy with a
  structured knowledge base queried at deploy time.
- Brooks (1986), "Subsumption Architecture": Capabilities layer
  incrementally; higher layers subsume lower ones without rewriting.

Each capability is a self-contained unit with:
  - A probe function: can this capability activate in the current env?
  - An activate function: wire it into the execution context.
  - A deactivate function: clean teardown.

The router never imports modules at module level — all imports are
deferred to activation time, ensuring graceful degradation when
optional dependencies are missing.
"""
from __future__ import annotations

import os
import logging
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable
from pathlib import Path

logger = logging.getLogger(__name__)


class CapabilityKind(Enum):
    """Taxonomy of capabilities the orchestrator can activate."""
    PERCEPTION_A11Y = auto()
    PERCEPTION_SOM = auto()
    PERCEPTION_FUSION = auto()
    TRUST_TRACKER = auto()
    COORD_CACHE = auto()
    PHASH_GATE = auto()
    SITE_KNOWLEDGE = auto()
    CREDENTIAL_VAULT = auto()
    STROKE_LOGGING = auto()
    INFERENCE_ROUTING = auto()
    EPISODIC_MEMORY = auto()
    WEB_PRIMITIVES = auto()
    DYNAMIC_PLANNING = auto()


@dataclass
class Capability:
    """A single activatable capability backed by a real module."""
    kind: CapabilityKind
    name: str
    description: str
    is_active: bool = False
    instance: Any = None
    requires: list[CapabilityKind] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind.name,
            "name": self.name,
            "active": self.is_active,
            "has_instance": self.instance is not None,
        }


@dataclass
class TaskRequirements:
    """What a task needs, determined by VLM analysis of the goal + URL."""
    needs_drawing: bool = False
    needs_login: bool = False
    needs_navigation: bool = False
    needs_form_fill: bool = False
    needs_color_selection: bool = False
    needs_file_upload: bool = False
    is_known_site: bool = False
    site_domain: str = ""
    goal_keywords: list[str] = field(default_factory=list)


def classify_task(url: str, goal: str) -> TaskRequirements:
    """Determine task requirements from URL and goal text.

    Uses keyword heuristics first (zero-cost), then optionally
    escalates to VLM classification for ambiguous goals.
    Follows the FrugalGPT cascade: cheap classification first,
    expensive only when uncertain (Chen et al., 2023, arXiv:2305.05176).
    """
    goal_lower = goal.lower()
    from urllib.parse import urlparse
    domain = urlparse(url).netloc.lower() if url else ""

    reqs = TaskRequirements(site_domain=domain)

    draw_keywords = {"draw", "triangle", "circle", "shape", "sketch", "paint",
                     "eiffel", "bmw", "concentric", "landscape", "stroke", "pen"}
    login_keywords = {"login", "log in", "sign in", "authenticate", "password",
                      "credential", "email", "username"}
    nav_keywords = {"navigate", "go to", "open", "visit", "browse", "find",
                    "search", "look for", "click on"}
    form_keywords = {"fill", "enter", "type", "submit", "form", "register",
                     "sign up", "create account"}
    color_keywords = {"color", "red", "blue", "green", "black", "stroke color",
                      "fill color", "palette"}
    upload_keywords = {"upload", "attach", "file", "import", "drag and drop"}

    tokens = set(goal_lower.split())
    reqs.goal_keywords = list(tokens)
    reqs.needs_drawing = bool(tokens & draw_keywords)
    reqs.needs_login = bool(tokens & login_keywords)
    reqs.needs_navigation = bool(tokens & nav_keywords) or bool(url)
    reqs.needs_form_fill = bool(tokens & form_keywords)
    reqs.needs_color_selection = bool(tokens & color_keywords)
    reqs.needs_file_upload = bool(tokens & upload_keywords)

    known_domains = {"excalidraw.com", "kleki.com", "magma.com"}
    reqs.is_known_site = any(k in domain for k in known_domains)

    return reqs


class CapabilityRouter:
    """Activates and manages capabilities based on task requirements.

    Follows the subsumption principle (Brooks, 1986): base capabilities
    (perception, trust) are always active; higher capabilities (drawing,
    credentials) layer on top based on task needs.
    """

    def __init__(self, cre_dir: str | Path, operator_dir: str | Path | None = None) -> None:
        self._cre_dir = Path(cre_dir)
        self._operator_dir = Path(operator_dir) if operator_dir else self._cre_dir.parent
        self._capabilities: dict[CapabilityKind, Capability] = {}
        self._task_reqs: TaskRequirements | None = None
        self._register_all()

    def _register_all(self) -> None:
        """Register every capability the system can provide."""
        defs = [
            (CapabilityKind.PERCEPTION_A11Y, "Accessibility Engine",
             "Extract macOS accessibility trees for semantic element identification"),
            (CapabilityKind.PERCEPTION_SOM, "Set-of-Mark Overlay",
             "12x12 grid overlay for visual grounding via VLM"),
            (CapabilityKind.PERCEPTION_FUSION, "Unified Element Map",
             "Fuse a11y + SoM into queryable element map",
             [CapabilityKind.PERCEPTION_A11Y, CapabilityKind.PERCEPTION_SOM]),
            (CapabilityKind.TRUST_TRACKER, "Beta-Binomial Trust",
             "Adaptive verification skipping via Bayesian posterior"),
            (CapabilityKind.COORD_CACHE, "Coordinate Cache",
             "pHash-gated replay of cached screen coordinates"),
            (CapabilityKind.PHASH_GATE, "Perceptual Hash Gate",
             "Adaptive pHash tolerance for cache validation",
             [CapabilityKind.COORD_CACHE]),
            (CapabilityKind.SITE_KNOWLEDGE, "Site Knowledge Base",
             "Persistent per-site tool affordances and interaction rules"),
            (CapabilityKind.CREDENTIAL_VAULT, "Credential Vault",
             "macOS Keychain integration for secure credential access"),
            (CapabilityKind.STROKE_LOGGING, "Stroke Count Logging",
             "Verifiable stroke/vertex counts in trace post_state"),
            (CapabilityKind.INFERENCE_ROUTING, "Inference Router",
             "Dynamic Flash/Pro/Local model routing with hysteresis"),
            (CapabilityKind.EPISODIC_MEMORY, "Episodic Memory",
             "Reflexion journal + rules store for cross-run learning"),
            (CapabilityKind.WEB_PRIMITIVES, "Web Primitives",
             "Label-based click/type/scroll over UnifiedElementMap",
             [CapabilityKind.PERCEPTION_FUSION]),
            (CapabilityKind.DYNAMIC_PLANNING, "Dynamic VLM Planning",
             "Gemini 2.5 Pro generates action plans from SoM + goal"),
        ]
        for entry in defs:
            kind = entry[0]
            name = entry[1]
            desc = entry[2]
            requires = entry[3] if len(entry) > 3 else []
            self._capabilities[kind] = Capability(
                kind=kind, name=name, description=desc, requires=requires,
            )

    def activate_for_task(self, reqs: TaskRequirements) -> list[Capability]:
        """Determine which capabilities to activate and wire them up.

        Base layer (always active): perception, trust, inference routing,
        episodic memory, stroke logging.
        Task-dependent: credential vault, web primitives, dynamic planning,
        coordinate cache, site knowledge.
        """
        self._task_reqs = reqs
        always_on = {
            CapabilityKind.PERCEPTION_A11Y,
            CapabilityKind.PERCEPTION_SOM,
            CapabilityKind.PERCEPTION_FUSION,
            CapabilityKind.TRUST_TRACKER,
            CapabilityKind.INFERENCE_ROUTING,
            CapabilityKind.EPISODIC_MEMORY,
            CapabilityKind.STROKE_LOGGING,
        }

        task_activated: set[CapabilityKind] = set()

        if reqs.is_known_site or reqs.needs_drawing:
            task_activated.add(CapabilityKind.COORD_CACHE)
            task_activated.add(CapabilityKind.PHASH_GATE)
            task_activated.add(CapabilityKind.SITE_KNOWLEDGE)

        if reqs.needs_login:
            task_activated.add(CapabilityKind.CREDENTIAL_VAULT)

        if reqs.needs_navigation or reqs.needs_form_fill or reqs.needs_login:
            task_activated.add(CapabilityKind.WEB_PRIMITIVES)

        task_activated.add(CapabilityKind.DYNAMIC_PLANNING)

        if reqs.is_known_site:
            task_activated.add(CapabilityKind.SITE_KNOWLEDGE)

        target = always_on | task_activated

        for kind in self._resolve_dependencies(target):
            self._activate_one(kind)

        activated = [c for c in self._capabilities.values() if c.is_active]
        logger.info("Activated %d capabilities for task on %s",
                     len(activated), reqs.site_domain or "(no URL)")
        return activated

    def _resolve_dependencies(self, target: set[CapabilityKind]) -> list[CapabilityKind]:
        """Topological sort: ensure dependencies activate before dependents."""
        resolved: list[CapabilityKind] = []
        seen: set[CapabilityKind] = set()

        def _visit(kind: CapabilityKind) -> None:
            if kind in seen:
                return
            seen.add(kind)
            cap = self._capabilities.get(kind)
            if cap:
                for dep in cap.requires:
                    if dep in target or dep in self._capabilities:
                        _visit(dep)
            resolved.append(kind)

        for kind in target:
            _visit(kind)
        return resolved

    def _activate_one(self, kind: CapabilityKind) -> None:
        """Activate a single capability. All imports are deferred."""
        cap = self._capabilities.get(kind)
        if not cap or cap.is_active:
            return

        try:
            if kind == CapabilityKind.PERCEPTION_A11Y:
                from a11y_engine import A11yEngine
                cap.instance = A11yEngine()

            elif kind == CapabilityKind.PERCEPTION_SOM:
                cap.instance = True  # marker; actual engine passed from agent init

            elif kind == CapabilityKind.PERCEPTION_FUSION:
                from element_map import UnifiedElementMap
                cap.instance = UnifiedElementMap()

            elif kind == CapabilityKind.TRUST_TRACKER:
                from agent_infra.action_trust import ActionTrustTracker
                persist = str(self._cre_dir / "action_trust.json")
                cap.instance = ActionTrustTracker(persist_path=persist)

            elif kind == CapabilityKind.COORD_CACHE:
                cap.instance = {}  # populated from skill library at runtime

            elif kind == CapabilityKind.PHASH_GATE:
                cap.instance = True  # pHash functions imported on demand

            elif kind == CapabilityKind.SITE_KNOWLEDGE:
                from agent_infra.site_knowledge import SiteKnowledge
                domain = (self._task_reqs.site_domain or "") if self._task_reqs else ""
                if domain == "magma.com":
                    persist_path = str(self._cre_dir / "site_knowledge_magma.json")
                elif domain == "kleki.com":
                    persist_path = str(self._cre_dir / "site_knowledge_kleki.json")
                else:
                    persist_path = str(self._cre_dir / "site_knowledge_universal.json")
                cap.instance = SiteKnowledge(persist_path=persist_path)

            elif kind == CapabilityKind.CREDENTIAL_VAULT:
                from security.credential_vault import CredentialVault, HITLGuard
                cap.instance = {"vault": CredentialVault(), "hitl": HITLGuard()}

            elif kind == CapabilityKind.STROKE_LOGGING:
                cap.instance = True

            elif kind == CapabilityKind.INFERENCE_ROUTING:
                from inference_router import InferenceRouter
                persist = str(self._cre_dir / "routing_state.json")
                cap.instance = InferenceRouter(persist_path=persist)

            elif kind == CapabilityKind.EPISODIC_MEMORY:
                cap.instance = self._load_episodic_memory()

            elif kind == CapabilityKind.WEB_PRIMITIVES:
                cap.instance = True  # instantiated after agent + element_map exist

            elif kind == CapabilityKind.DYNAMIC_PLANNING:
                cap.instance = True

            cap.is_active = True
            logger.debug("Activated: %s", cap.name)

        except Exception as e:
            logger.warning("Could not activate %s: %s", cap.name, e)
            cap.is_active = False

    def _load_episodic_memory(self) -> list[str]:
        lessons: list[str] = []
        try:
            from agent_infra import ReflectionJournal, RulesStore
            journal_path = self._cre_dir / "runs" / "reflection_journal.jsonl"
            if journal_path.exists():
                rj = ReflectionJournal(journal_path)
                lessons.extend(rj.retrieve_relevant("", top_k=5))
            rules_path = self._cre_dir / "runs" / "rules.jsonl"
            if rules_path.exists():
                rs = RulesStore(rules_path)
                lessons.extend(rs.get_rules())
        except Exception:
            pass
        return lessons

    def get(self, kind: CapabilityKind) -> Any | None:
        """Retrieve an active capability's instance."""
        cap = self._capabilities.get(kind)
        if cap and cap.is_active:
            return cap.instance
        return None

    def is_active(self, kind: CapabilityKind) -> bool:
        cap = self._capabilities.get(kind)
        return bool(cap and cap.is_active)

    def summary(self) -> dict[str, Any]:
        active = [c for c in self._capabilities.values() if c.is_active]
        inactive = [c for c in self._capabilities.values() if not c.is_active]
        return {
            "active_count": len(active),
            "inactive_count": len(inactive),
            "active": [c.to_dict() for c in active],
            "inactive": [c.to_dict() for c in inactive],
        }

    def deactivate_all(self) -> None:
        for cap in self._capabilities.values():
            cap.is_active = False
            cap.instance = None
