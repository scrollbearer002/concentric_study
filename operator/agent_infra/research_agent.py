"""Pre-execution research pipeline for task intelligence gathering.

Implements the "Research Before Execute" principle: before any task is
attempted, the agent studies what it's building, how to build it, and
what tools are available — then solves the equation between requirements
and capabilities.

Architecture grounded in:
- AppAgent Phase 1 (Yang et al., 2023, arXiv:2312.13771): autonomous
  exploration before deployment. The agent learns affordances, THEN uses them.
- GUI-explorer (ACL 2025, arXiv:2505.16827): transition-aware knowledge
  extraction through systematic UI probing.
- SeeAct (Zheng et al., 2024, arXiv:2401.01614): grounding VLM actions
  in external documentation reduces hallucination by 30-40%.
- MIRA (arXiv:2511.21087): iterative perception-reasoning-action loop
  with visual feedback driving each decision.
- VisionDirector (arXiv:2512.19243): closed-loop refinement with
  semantic verification and rollback after each edit.
- RefineEdit-Agent (arXiv:2508.17435): LVLM-driven feedback loop for
  iterative refinement against a target specification.
- PG-Agent (arXiv:2509.03536): retrieval-augmented perception guidelines
  from page graphs for cross-scenario generalization.

Design principles:
- ZERO imports from agent_infra (preserves unidirectional dependency chain)
- All outputs are JSON-serializable for trace storage
- Research phase produces artifacts (reference images, method briefs)
  that persist in the run directory for post-mortem analysis
- The "equation solver" maps method requirements to tool capabilities
"""

from __future__ import annotations

import json
import logging
import subprocess
import time
from dataclasses import dataclass, field, asdict, is_dataclass
from pathlib import Path
from typing import Any, Callable

logger = logging.getLogger(__name__)


PHASE3_ACTION_HINTS = [
    "click",
    "type",
    "key",
    "scroll",
    "wait",
    "screenshot",
    "assert_visual",
    "draw_path",
    "draw_segments",
    "draw_shape",
    "go_to_url",
    "go_back",
    "browser_beforeunload_dialog",
]


def _jsonify(value: Any) -> Any:
    """Recursively convert dataclasses into JSON-serializable objects."""
    if is_dataclass(value):
        return {k: _jsonify(v) for k, v in asdict(value).items()}
    if isinstance(value, dict):
        return {str(k): _jsonify(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_jsonify(v) for v in value]
    return value


@dataclass
class MethodReference:
    title: str
    url: str
    source_tier: str = "secondary"
    published_or_retrieved_date: str = ""
    relevance_note: str = ""

    @classmethod
    def from_raw(cls, raw: dict[str, Any]) -> "MethodReference":
        return cls(
            title=str(raw.get("title", "")),
            url=str(raw.get("url", "")),
            source_tier=str(raw.get("source_tier", "secondary")),
            published_or_retrieved_date=str(raw.get("published_or_retrieved_date", "")),
            relevance_note=str(raw.get("relevance_note", "")),
        )


@dataclass
class MethodStep:
    step_id: str
    description: str
    objective: str = ""
    required_visual_outcome: str = ""
    common_failure_modes: list[str] = field(default_factory=list)
    depends_on_step_ids: list[str] = field(default_factory=list)

    @classmethod
    def from_raw(cls, raw: dict[str, Any]) -> "MethodStep":
        return cls(
            step_id=str(raw.get("step_id", "")),
            description=str(raw.get("description", "")),
            objective=str(raw.get("objective", "")),
            required_visual_outcome=str(raw.get("required_visual_outcome", "")),
            common_failure_modes=[str(v) for v in raw.get("common_failure_modes", []) if str(v).strip()],
            depends_on_step_ids=[str(v) for v in raw.get("depends_on_step_ids", []) if str(v).strip()],
        )


@dataclass
class MethodBrief:
    subject_family: str = "general"
    task_family: str = "mixed"
    steps: list[MethodStep] = field(default_factory=list)
    pitfalls: list[str] = field(default_factory=list)
    references: list[MethodReference] = field(default_factory=list)
    acceptance_clues: list[str] = field(default_factory=list)
    method_confidence: float = 0.0
    coverage_gaps: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return _jsonify(self)

    @classmethod
    def from_raw(cls, raw: dict[str, Any] | "MethodBrief" | None) -> "MethodBrief":
        if isinstance(raw, MethodBrief):
            return raw
        if not raw:
            return cls()
        return cls(
            subject_family=str(raw.get("subject_family", "general")),
            task_family=str(raw.get("task_family", "mixed")),
            steps=[MethodStep.from_raw(step) for step in raw.get("steps", []) if isinstance(step, dict)],
            pitfalls=[str(v) for v in raw.get("pitfalls", []) if str(v).strip()],
            references=[MethodReference.from_raw(ref) for ref in raw.get("references", []) if isinstance(ref, dict)],
            acceptance_clues=[str(v) for v in raw.get("acceptance_clues", []) if str(v).strip()],
            method_confidence=float(raw.get("method_confidence", 0.0) or 0.0),
            coverage_gaps=[str(v) for v in raw.get("coverage_gaps", []) if str(v).strip()],
        )


@dataclass
class ToolInventoryEntry:
    tool_name: str
    interaction_mode: str = "unknown"
    shortcut: str | None = None
    description: str = ""
    preconditions: list[str] = field(default_factory=list)
    postconditions: list[str] = field(default_factory=list)
    known_failures: list[str] = field(default_factory=list)
    source: str = "inferred"
    confidence: float = 0.0

    @classmethod
    def from_raw(cls, raw: dict[str, Any] | "ToolInventoryEntry") -> "ToolInventoryEntry":
        if isinstance(raw, ToolInventoryEntry):
            return raw
        return cls(
            tool_name=str(raw.get("tool_name", "")),
            interaction_mode=str(raw.get("interaction_mode", "unknown")),
            shortcut=raw.get("shortcut"),
            description=str(raw.get("description", "")),
            preconditions=[str(v) for v in raw.get("preconditions", []) if str(v).strip()],
            postconditions=[str(v) for v in raw.get("postconditions", []) if str(v).strip()],
            known_failures=[str(v) for v in raw.get("known_failures", []) if str(v).strip()],
            source=str(raw.get("source", "inferred")),
            confidence=float(raw.get("confidence", 0.0) or 0.0),
        )


@dataclass
class EquationMapping:
    method_step_id: str
    tool_name: str
    action_type: str
    action_parameters_hint: dict[str, Any] = field(default_factory=dict)
    why_this_mapping: str = ""
    fallback_tool_name: str = ""
    fallback_action_type: str = ""
    verification_hint: str = ""

    @classmethod
    def from_raw(cls, raw: dict[str, Any] | "EquationMapping") -> "EquationMapping":
        if isinstance(raw, EquationMapping):
            return raw
        return cls(
            method_step_id=str(raw.get("method_step_id", "")),
            tool_name=str(raw.get("tool_name", "")),
            action_type=str(raw.get("action_type", "")),
            action_parameters_hint=dict(raw.get("action_parameters_hint", {}) or {}),
            why_this_mapping=str(raw.get("why_this_mapping", "")),
            fallback_tool_name=str(raw.get("fallback_tool_name", "")),
            fallback_action_type=str(raw.get("fallback_action_type", "")),
            verification_hint=str(raw.get("verification_hint", "")),
        )


@dataclass
class EquationSolution:
    mappings: list[EquationMapping] = field(default_factory=list)
    uncovered_method_steps: list[str] = field(default_factory=list)
    tool_gaps: list[str] = field(default_factory=list)
    execution_plan: list[dict[str, Any]] = field(default_factory=list)
    quality_criteria: list[str] = field(default_factory=list)
    solution_confidence: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return _jsonify(self)

    @classmethod
    def from_raw(cls, raw: dict[str, Any] | "EquationSolution" | None) -> "EquationSolution":
        if isinstance(raw, EquationSolution):
            return raw
        if not raw:
            return cls()
        return cls(
            mappings=[EquationMapping.from_raw(v) for v in raw.get("mappings", []) if isinstance(v, dict)],
            uncovered_method_steps=[str(v) for v in raw.get("uncovered_method_steps", []) if str(v).strip()],
            tool_gaps=[str(v) for v in raw.get("tool_gaps", []) if str(v).strip()],
            execution_plan=[dict(v) for v in raw.get("execution_plan", []) if isinstance(v, dict)],
            quality_criteria=[str(v) for v in raw.get("quality_criteria", []) if str(v).strip()],
            solution_confidence=float(raw.get("solution_confidence", 0.0) or 0.0),
        )


def evaluate_phase2_method_gate(method_brief: MethodBrief | dict[str, Any] | None) -> dict[str, Any]:
    """Return a structured gate result for Phase 2 method research."""
    brief = MethodBrief.from_raw(method_brief)
    references = brief.references or []
    steps = brief.steps or []
    pitfalls = brief.pitfalls or []
    clues = brief.acceptance_clues or []
    primary_count = sum(1 for ref in references if ref.source_tier == "primary")
    references_gap_explicit = any(
        "fewer than three method references" in gap.lower()
        for gap in brief.coverage_gaps
    )
    primary_gap_explicit = any(
        "no primary/repo-local" in gap.lower()
        for gap in brief.coverage_gaps
    )
    requirements = {
        "references_min_met": len(references) >= 3 or references_gap_explicit,
        "primary_or_repo_local_present": primary_count >= 1 or primary_gap_explicit,
        "method_steps_min_met": len(steps) >= 3,
        "pitfalls_min_met": len(pitfalls) >= 2,
        "acceptance_clues_min_met": len(clues) >= 2,
        "coverage_gaps_explicit": True,
    }
    reasons = [
        name for name, passed in requirements.items()
        if not passed
    ]
    return {
        "passed": not reasons,
        "task_family": brief.task_family,
        "subject_family": brief.subject_family,
        "references": len(references),
        "primary_references": primary_count,
        "references_gap_explicit": references_gap_explicit,
        "primary_gap_explicit": primary_gap_explicit,
        "steps": len(steps),
        "pitfalls": len(pitfalls),
        "acceptance_clues": len(clues),
        "coverage_gaps": list(brief.coverage_gaps),
        "requirements": requirements,
        "fail_reasons": reasons,
        "method_confidence": brief.method_confidence,
    }


def evaluate_phase3_equation_gate(
    equation_solution: EquationSolution | dict[str, Any] | None,
    valid_action_names: list[str],
) -> dict[str, Any]:
    """Return a structured gate result for Phase 3 tool/equation solving."""
    solution = EquationSolution.from_raw(equation_solution)
    valid_actions = set(valid_action_names)
    invalid_actions = sorted(
        {
            mapping.action_type
            for mapping in solution.mappings
            if mapping.action_type and mapping.action_type not in valid_actions
        }
    )
    high_risk_prefixes = ("draw_",)
    high_risk_actions = {"click", "type", "browser_beforeunload_dialog"}
    missing_fallbacks = sorted(
        {
            mapping.method_step_id
            for mapping in solution.mappings
            if (
                mapping.action_type in high_risk_actions
                or mapping.action_type.startswith(high_risk_prefixes)
            )
            and not mapping.fallback_action_type
        }
    )
    requirements = {
        "required_method_steps_covered": len(solution.uncovered_method_steps) == 0,
        "all_action_mappings_valid": len(invalid_actions) == 0,
        "high_risk_fallbacks_present": len(missing_fallbacks) == 0,
        "solution_confidence_or_gaps_explicit": (
            solution.solution_confidence >= 0.6 or len(solution.tool_gaps) > 0
        ),
    }
    reasons = [name for name, passed in requirements.items() if not passed]
    return {
        "passed": not reasons,
        "mappings": len(solution.mappings),
        "uncovered_method_steps": list(solution.uncovered_method_steps),
        "tool_gaps": list(solution.tool_gaps),
        "invalid_action_types": invalid_actions,
        "missing_fallbacks": missing_fallbacks,
        "solution_confidence": solution.solution_confidence,
        "requirements": requirements,
        "fail_reasons": reasons,
    }


@dataclass
class ResearchBrief:
    """Complete pre-execution intelligence package.

    Produced by the ResearchAgent before any task execution begins.
    Contains everything the executor needs to work from knowledge
    rather than guesswork.
    """
    task_description: str
    reference_images: list[str] = field(default_factory=list)
    method_brief: MethodBrief | dict[str, Any] = field(default_factory=MethodBrief)
    tool_inventory: list[ToolInventoryEntry] | list[dict[str, Any]] = field(default_factory=list)
    equation_solution: EquationSolution | dict[str, Any] = field(default_factory=EquationSolution)
    execution_plan: list[dict[str, Any]] = field(default_factory=list)
    quality_criteria: list[str] = field(default_factory=list)
    research_duration_ms: int = 0
    timestamp: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["method_brief"] = _jsonify(self.method_brief)
        return _jsonify(payload)

    def save(self, path: str | Path) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, default=str)

    @classmethod
    def load(cls, path: str | Path) -> ResearchBrief:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        allowed = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        allowed["method_brief"] = MethodBrief.from_raw(allowed.get("method_brief"))
        allowed["tool_inventory"] = [
            ToolInventoryEntry.from_raw(entry)
            for entry in allowed.get("tool_inventory", [])
            if isinstance(entry, dict)
        ]
        allowed["equation_solution"] = EquationSolution.from_raw(allowed.get("equation_solution"))
        return cls(**allowed)

    def get_plan_summary(self) -> str:
        """Human-readable summary of the execution plan."""
        if not self.execution_plan:
            return "No execution plan generated."
        lines = [f"Execution Plan ({len(self.execution_plan)} steps):"]
        for i, step in enumerate(self.execution_plan, 1):
            desc = step.get("description", step.get("action", "unknown"))
            tool = step.get("tool", "")
            tool_str = f" [using: {tool}]" if tool else ""
            lines.append(f"  {i}. {desc}{tool_str}")
        if self.quality_criteria:
            lines.append("\nQuality Criteria:")
            for c in self.quality_criteria:
                lines.append(f"  - {c}")
        return "\n".join(lines)


class ResearchAgent:
    """Pre-execution intelligence gatherer.

    Runs BEFORE any task execution to produce a ResearchBrief.
    The brief contains reference images, technique knowledge,
    tool inventory, and an execution plan.

    Usage::

        agent = ResearchAgent(output_dir="operator/cre/runs/abc123")
        brief = agent.research(
            task="Draw two interlaced hands over a shattered glass sphere",
            site_url="https://www.canva.com/draw/",
            search_fn=my_web_search,       # optional
            screenshot_fn=my_screenshot,    # optional
        )
        print(brief.get_plan_summary())
    """

    def __init__(self, output_dir: str | Path) -> None:
        self._output_dir = Path(output_dir)
        self._refs_dir = self._output_dir / "reference_images"
        self._refs_dir.mkdir(parents=True, exist_ok=True)

    def research(
        self,
        task: str,
        site_url: str = "",
        search_fn: Callable[[str], list[dict[str, str]]] | None = None,
        screenshot_fn: Callable[[str], str] | None = None,
        vlm_fn: Callable[[str, list[str]], str] | None = None,
        site_knowledge: Any | None = None,
    ) -> ResearchBrief:
        """Run the full four-phase research pipeline.

        Args:
            task: Natural language description of what to create/do.
            site_url: URL of the target website/tool.
            search_fn: Web search function. Takes query, returns list of
                       {title, url, snippet} dicts.
            screenshot_fn: Function to capture a URL as screenshot.
                          Takes URL, returns path to saved PNG.
            vlm_fn: Vision-language model function. Takes (prompt, image_paths),
                    returns text response.
            site_knowledge: Optional SiteKnowledge instance for tool inventory.

        Returns:
            ResearchBrief with all gathered intelligence.
        """
        start = time.time()
        brief = ResearchBrief(
            task_description=task,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        )

        # Phase 1: Study the subject
        logger.info("Research Phase 1: Studying the subject")
        print(f"\n  [RESEARCH] Phase 1: Studying the subject...")
        brief.reference_images = self._study_subject(task, search_fn, screenshot_fn)
        print(f"  [RESEARCH]   Found {len(brief.reference_images)} reference images")

        # Phase 2: Study the method
        logger.info("Research Phase 2: Studying the method")
        print(f"  [RESEARCH] Phase 2: Studying the method...")
        brief.method_brief = self._study_method(task, search_fn, vlm_fn)
        print(
            f"  [RESEARCH]   Method brief: "
            f"{len(getattr(brief.method_brief, 'steps', []) or [])} steps, "
            f"{len(getattr(brief.method_brief, 'references', []) or [])} references"
        )

        # Phase 3: Study the tools
        logger.info("Research Phase 3: Studying the tools")
        print(f"  [RESEARCH] Phase 3: Studying the tools...")
        brief.tool_inventory = self._study_tools(site_url, site_knowledge, screenshot_fn)
        print(f"  [RESEARCH]   Tool inventory: {len(brief.tool_inventory)} entries")

        # Phase 4: Solve the equation
        logger.info("Research Phase 4: Solving the equation")
        print(f"  [RESEARCH] Phase 4: Solving the equation...")
        brief.equation_solution = self._solve_equation(
            task, brief.method_brief, brief.tool_inventory, vlm_fn,
        )
        brief.execution_plan = list(brief.equation_solution.execution_plan)
        brief.quality_criteria = list(brief.equation_solution.quality_criteria)
        print(f"  [RESEARCH]   Plan: {len(brief.execution_plan)} steps, "
              f"{len(brief.quality_criteria)} quality criteria")

        brief.research_duration_ms = int((time.time() - start) * 1000)

        brief_path = self._output_dir / "research_brief.json"
        brief.save(brief_path)
        (self._output_dir / "method_brief.json").write_text(
            json.dumps(MethodBrief.from_raw(brief.method_brief).to_dict(), indent=2),
            encoding="utf-8",
        )
        (self._output_dir / "tool_inventory.json").write_text(
            json.dumps([_jsonify(entry) for entry in brief.tool_inventory], indent=2),
            encoding="utf-8",
        )
        (self._output_dir / "equation_solution.json").write_text(
            json.dumps(EquationSolution.from_raw(brief.equation_solution).to_dict(), indent=2),
            encoding="utf-8",
        )
        (self._output_dir / "execution_plan.json").write_text(
            json.dumps(list(brief.execution_plan), indent=2),
            encoding="utf-8",
        )
        print(f"  [RESEARCH] Complete in {brief.research_duration_ms}ms. "
              f"Saved to {brief_path}")

        return brief

    # ------------------------------------------------------------------
    # Phase 1: Study the Subject
    # ------------------------------------------------------------------

    def _study_subject(
        self,
        task: str,
        search_fn: Callable | None,
        screenshot_fn: Callable | None,
    ) -> list[str]:
        """Find reference images for what we're building.

        Decomposes the task into visual subjects, searches for each,
        and captures reference images as ground truth targets.
        """
        subjects = self._extract_visual_subjects(task)
        ref_paths: list[str] = []

        for i, subject in enumerate(subjects):
            query = f"{subject} reference image high quality"
            logger.info("Searching for reference: %s", query)

            if search_fn:
                try:
                    results = search_fn(query)
                    for j, result in enumerate(results[:2]):
                        url = result.get("url", "")
                        if url and screenshot_fn:
                            path = screenshot_fn(url)
                            if path:
                                ref_paths.append(path)
                except Exception as e:
                    logger.warning("Reference search failed for '%s': %s", subject, e)

            if screenshot_fn and not ref_paths:
                search_url = f"https://www.google.com/search?q={subject.replace(' ', '+')}&tbm=isch"
                try:
                    path = screenshot_fn(search_url)
                    if path:
                        ref_paths.append(path)
                except Exception as e:
                    logger.warning("Reference screenshot failed: %s", e)

        return ref_paths

    def _extract_visual_subjects(self, task: str) -> list[str]:
        """Extract distinct visual subjects from a task description.

        Simple NLP extraction: looks for noun phrases that describe
        visual elements. A VLM could do this more accurately but we
        keep this dependency-free.
        """
        task_lower = task.lower()
        subjects = []

        visual_keywords = [
            "hands", "hand", "fingers", "sphere", "glass", "ball",
            "face", "eye", "body", "figure", "landscape", "building",
            "skyscraper", "tower", "high-rise", "facade",
            "flower", "tree", "animal", "car", "person", "portrait",
        ]

        for keyword in visual_keywords:
            if keyword in task_lower:
                idx = task_lower.index(keyword)
                start = max(0, task_lower.rfind(" ", 0, max(0, idx - 1)))
                end = task_lower.find(" ", idx + len(keyword) + 10)
                if end == -1:
                    end = len(task_lower)
                phrase = task[start:end].strip(" ,.")
                if phrase and phrase not in subjects:
                    subjects.append(phrase)

        if not subjects:
            subjects = [task[:80]]

        return subjects[:5]

    # ------------------------------------------------------------------
    # Phase 2: Study the Method
    # ------------------------------------------------------------------

    def _study_method(
        self,
        task: str,
        search_fn: Callable | None,
        vlm_fn: Callable | None,
    ) -> MethodBrief:
        """Research how to build/create what the task requires.

        Searches for tutorials, techniques, and step-by-step guides.
        """
        task_family = self._infer_task_family(task)
        subject_family = self._infer_subject_family(task, task_family)
        method = MethodBrief(
            task_family=task_family,
            subject_family=subject_family,
        )
        subjects = self._extract_visual_subjects(task)
        timestamp = time.strftime("%Y-%m-%d")

        if search_fn:
            for subject in subjects[:3]:
                queries = [
                    f"how to draw {subject} step by step tutorial",
                    f"{subject} drawing technique guide",
                ]
                for query in queries:
                    try:
                        results = search_fn(query)
                        for r in results[:3]:
                            method.references.append(MethodReference(
                                title=str(r.get("title", "")),
                                url=str(r.get("url", "")),
                                source_tier=self._classify_source_tier(str(r.get("url", ""))),
                                published_or_retrieved_date=timestamp,
                                relevance_note=str(r.get("snippet", ""))[:200],
                            ))
                            snippet = r.get("snippet", "")
                            if snippet:
                                lowered = snippet.lower()
                                if "avoid" in lowered or "mistake" in lowered:
                                    method.pitfalls.append(snippet)
                    except Exception as e:
                        logger.warning("Method search failed for '%s': %s", query, e)

        if vlm_fn:
            prompt = (
                f"I need to draw/create: {task}\n\n"
                f"Task family: {task_family}\n"
                f"Subject family: {subject_family}\n\n"
                f"Break this down into an executable method.\n"
                f"Output JSON with keys:\n"
                f"- steps: list of objects with step_id, description, objective, required_visual_outcome, common_failure_modes, depends_on_step_ids\n"
                f"- pitfalls: list of strings\n"
                f"- acceptance_clues: list of strings\n"
            )
            try:
                response = vlm_fn(prompt, [])
                data = json.loads(response)
                for idx, raw_step in enumerate(data.get("steps", []), 1):
                    if isinstance(raw_step, str):
                        raw_step = {
                            "step_id": f"step_{idx:02d}",
                            "description": raw_step,
                        }
                    if isinstance(raw_step, dict):
                        raw_step.setdefault("step_id", f"step_{idx:02d}")
                        method.steps.append(MethodStep.from_raw(raw_step))
                method.pitfalls.extend(
                    str(v) for v in data.get("pitfalls", []) if str(v).strip()
                )
                method.acceptance_clues.extend(
                    str(v) for v in data.get("acceptance_clues", []) if str(v).strip()
                )
            except Exception as e:
                logger.warning("VLM method study failed: %s", e)

        if not method.steps:
            method.steps = self._default_method_steps(task_family, subject_family)
            method.coverage_gaps.append("No structured method steps extracted from external/VLM sources; using local fallback method model.")

        if len(method.pitfalls) < 2:
            method.pitfalls.extend(self._default_pitfalls(task_family, subject_family))
        if len(method.acceptance_clues) < 2:
            method.acceptance_clues.extend(self._default_acceptance_clues(task_family, subject_family))

        method.pitfalls = self._dedupe_strings(method.pitfalls)[:8]
        method.acceptance_clues = self._dedupe_strings(method.acceptance_clues)[:8]
        method.references = self._dedupe_references(method.references)[:8]
        method.method_confidence = self._estimate_method_confidence(method)

        if len(method.references) < 3:
            method.coverage_gaps.append("Fewer than three method references were recovered.")
        if not any(ref.source_tier == "primary" for ref in method.references):
            method.coverage_gaps.append("No primary/repo-local high-confidence method source was recovered.")

        return method

    def _infer_task_family(self, task: str) -> str:
        task_lower = task.lower()
        if any(marker in task_lower for marker in ("draw ", "paint ", "sketch", "illustrat", "design ", "render ")):
            return "drawing"
        if any(marker in task_lower for marker in ("login", "sign in", "sign-in", "form", "submit", "checkout")):
            return "form_interaction"
        if any(marker in task_lower for marker in ("read ", "extract", "summarize", "find ", "collect", "scrape")):
            return "reading/extraction"
        if any(marker in task_lower for marker in ("go to", "navigate", "browse", "open ", "visit ")):
            return "navigation"
        return "mixed"

    def _infer_subject_family(self, task: str, task_family: str) -> str:
        task_lower = task.lower()
        if task_family != "drawing":
            return "general"
        if any(marker in task_lower for marker in ("bear", "tiger", "fox", "owl", "animal", "cat", "dog")):
            return "animal"
        if any(marker in task_lower for marker in ("car", "truck", "vehicle", "plane", "bike")):
            return "vehicle"
        if any(marker in task_lower for marker in ("skyscraper", "tower", "building", "architecture", "facade")):
            return "architecture"
        if any(marker in task_lower for marker in ("portrait", "face", "person", "character")):
            return "portrait"
        return "editorial_character"

    def _classify_source_tier(self, url: str) -> str:
        lowered = url.lower()
        if any(host in lowered for host in ("docs.", "developer.", ".gov/", ".edu/", "w3.org", "mdn", "react.dev")):
            return "primary"
        return "secondary"

    def _default_method_steps(self, task_family: str, subject_family: str) -> list[MethodStep]:
        if task_family == "drawing":
            return [
                MethodStep(
                    step_id="step_01",
                    description="Establish the overall silhouette and primary masses.",
                    objective="Get the major composition and proportions correct before detail.",
                    required_visual_outcome="The subject reads clearly from a distance as the intended form.",
                    common_failure_modes=["cropped composition", "incoherent silhouette"],
                ),
                MethodStep(
                    step_id="step_02",
                    description="Add secondary structure and major internal subdivisions.",
                    objective="Place anatomy, clothing, or architectural subdivisions before fine detail.",
                    required_visual_outcome="Key internal forms align with the silhouette and remain legible.",
                    common_failure_modes=["floating details", "misaligned proportions"],
                    depends_on_step_ids=["step_01"],
                ),
                MethodStep(
                    step_id="step_03",
                    description="Finish with detail, material cues, and final verification passes.",
                    objective="Add enough specificity that the result matches the requested identity and finish.",
                    required_visual_outcome="The result contains recognizable subject-specific details and requested style cues.",
                    common_failure_modes=["generic styling", "missing requested detail"],
                    depends_on_step_ids=["step_01", "step_02"],
                ),
            ]
        if task_family == "navigation":
            return [
                MethodStep("step_01", "Reach the correct surface.", "Get to the requested page or workflow.", "The intended page is visible and interactive.", ["wrong page", "modal obstruction"]),
                MethodStep("step_02", "Confirm the target affordance.", "Identify the exact button, link, or element to use.", "The target action is unambiguous before clicking.", ["ambiguous click target"], ["step_01"]),
                MethodStep("step_03", "Execute and verify the transition.", "Perform the action and confirm the expected state change.", "The next page or state matches the intended destination.", ["silent no-op", "wrong transition"], ["step_02"]),
            ]
        if task_family == "form_interaction":
            return [
                MethodStep("step_01", "Locate and confirm the correct form fields.", "Avoid typing into the wrong controls.", "Each required field is identified before entry.", ["wrong field", "missing field"]),
                MethodStep("step_02", "Populate fields with the required values.", "Enter the right values in the right order.", "The entered values are visible and accepted.", ["failed input", "format rejection"], ["step_01"]),
                MethodStep("step_03", "Submit and verify the resulting state.", "Confirm that the form action succeeded.", "The post-submit state clearly reflects success or bounded failure.", ["submit blocked", "unknown outcome"], ["step_02"]),
            ]
        if task_family == "reading/extraction":
            return [
                MethodStep("step_01", "Reach the source surface.", "Load the page/document that contains the requested information.", "The source content is visible.", ["wrong page", "truncated content"]),
                MethodStep("step_02", "Identify the relevant sections.", "Focus on the specific region containing the answer.", "The extraction target is isolated.", ["irrelevant content", "missed section"], ["step_01"]),
                MethodStep("step_03", "Extract and cross-check the answer.", "Return the requested information accurately.", "The extracted answer is traceable to visible source evidence.", ["hallucinated extraction", "partial extraction"], ["step_02"]),
            ]
        return [
            MethodStep("step_01", "Establish the target surface and main objective.", "Get into the right state before execution.", "The target surface is visible and ready.", ["wrong surface", "blocked start"]),
            MethodStep("step_02", "Execute the main transformation steps.", "Perform the task’s core actions in the right order.", "Visible progress toward the task is evident.", ["order mismatch", "state drift"], ["step_01"]),
            MethodStep("step_03", "Verify that the final state matches the task.", "Close the loop against the requested outcome.", "The visible result satisfies the task description.", ["premature success", "unverified completion"], ["step_02"]),
        ]

    def _default_pitfalls(self, task_family: str, subject_family: str) -> list[str]:
        pitfalls = [
            "Do not rush into detail before the major structure or target surface is correct.",
            "Do not treat a completed gesture as proof that the site accepted the intended state change.",
        ]
        if task_family == "drawing":
            pitfalls.extend([
                "Avoid letting the subject drift generic; keep the requested identity cues visible.",
                "Avoid clipping or crowding the composition against the canvas bounds.",
            ])
        if task_family == "form_interaction":
            pitfalls.extend([
                "Avoid typing before the correct field is confirmed focused.",
                "Avoid assuming submission succeeded without a visible post-submit confirmation.",
            ])
        return pitfalls

    def _default_acceptance_clues(self, task_family: str, subject_family: str) -> list[str]:
        clues = [
            "The visible result should match the task description without relying on hidden assumptions.",
            "The output should contain the primary requested structure before secondary detail.",
        ]
        if task_family == "drawing":
            clues.extend([
                "The silhouette should read clearly as the requested subject at a glance.",
                "Requested style or identity details should be visibly present, not implied.",
            ])
        return clues

    def _estimate_method_confidence(self, method: MethodBrief) -> float:
        score = 0.3
        if len(method.steps) >= 3:
            score += 0.25
        if len(method.references) >= 3:
            score += 0.2
        if any(ref.source_tier == "primary" for ref in method.references):
            score += 0.15
        if len(method.acceptance_clues) >= 2:
            score += 0.05
        if len(method.pitfalls) >= 2:
            score += 0.05
        return round(min(score, 1.0), 3)

    def _dedupe_strings(self, values: list[str]) -> list[str]:
        seen: set[str] = set()
        deduped: list[str] = []
        for value in values:
            text = str(value or "").strip()
            if not text:
                continue
            key = text.lower()
            if key in seen:
                continue
            seen.add(key)
            deduped.append(text)
        return deduped

    def _dedupe_references(self, refs: list[MethodReference]) -> list[MethodReference]:
        seen: set[tuple[str, str]] = set()
        deduped: list[MethodReference] = []
        for ref in refs:
            key = (ref.title.strip().lower(), ref.url.strip().lower())
            if key in seen:
                continue
            seen.add(key)
            deduped.append(ref)
        return deduped

    # ------------------------------------------------------------------
    # Phase 3: Study the Tools
    # ------------------------------------------------------------------

    def _study_tools(
        self,
        site_url: str,
        site_knowledge: Any | None,
        screenshot_fn: Callable | None,
    ) -> list[ToolInventoryEntry]:
        """Inventory what tools the target platform provides.

        Leverages existing SiteKnowledge if available, otherwise
        builds a basic inventory from the site URL.
        """
        inventory: list[ToolInventoryEntry] = []
        if site_knowledge is not None:
            try:
                for tool_name, tool in sorted(site_knowledge.tools.items()):
                    confidence = 0.55
                    if tool.success_count > 0:
                        confidence = min(0.95, confidence + 0.1 + 0.05 * tool.success_count)
                    if tool.failure_count > 0:
                        confidence = max(0.2, confidence - 0.05 * tool.failure_count)
                    if tool.shortcut:
                        confidence = min(0.98, confidence + 0.05)
                    inventory.append(
                        ToolInventoryEntry(
                            tool_name=tool_name,
                            interaction_mode=tool.interaction_mode or "unknown",
                            shortcut=tool.shortcut,
                            description=tool.description,
                            preconditions=list(tool.preconditions),
                            postconditions=list(tool.postconditions),
                            known_failures=list(tool.known_failures),
                            source="site_knowledge",
                            confidence=round(confidence, 3),
                        )
                    )
            except Exception as e:
                logger.warning("SiteKnowledge extraction failed: %s", e)

        if site_url:
            inventory.append(
                ToolInventoryEntry(
                    tool_name="browser_surface",
                    interaction_mode="pointer+keyboard",
                    description=f"Interact with the live browser surface at {site_url} using the universal action space.",
                    preconditions=["target page is loaded and visible"],
                    postconditions=["page state changes are visibly reflected in the browser"],
                    known_failures=["surface can drift due to dialogs, overlays, or wrong active page state"],
                    source="hardcoded",
                    confidence=0.7,
                )
            )

        if screenshot_fn is not None:
            inventory.append(
                ToolInventoryEntry(
                    tool_name="screenshot_capture",
                    interaction_mode="perception",
                    description="Capture the visible surface for visual verification and comparison.",
                    preconditions=["front window is available for capture"],
                    postconditions=["fresh screenshot artifact exists for verification"],
                    source="inferred",
                    confidence=0.75,
                )
            )

        inventory.append(
            ToolInventoryEntry(
                tool_name="universal_action_space",
                interaction_mode="semantic_actions",
                description="The current repo action surface available to the universal agent.",
                preconditions=["host-tool health gate passed", "capability router activated required capabilities"],
                postconditions=["semantic actions can be dispatched through the executor"],
                source="hardcoded",
                confidence=0.9,
            )
        )

        deduped: dict[str, ToolInventoryEntry] = {}
        for entry in inventory:
            if not entry.tool_name:
                continue
            deduped[entry.tool_name] = entry

        return [deduped[name] for name in sorted(deduped)]

    # ------------------------------------------------------------------
    # Phase 4: Solve the Equation
    # ------------------------------------------------------------------

    def _solve_equation(
        self,
        task: str,
        method: MethodBrief | dict[str, Any],
        tools: list[ToolInventoryEntry] | list[dict[str, Any]],
        vlm_fn: Callable | None,
    ) -> EquationSolution:
        """Find the optimal intersection of requirements and capabilities.

        Maps method steps to available tools, producing an executable plan.
        """
        method_brief = MethodBrief.from_raw(method)
        tool_entries = [
            ToolInventoryEntry.from_raw(entry)
            for entry in (tools or [])
            if isinstance(entry, (ToolInventoryEntry, dict))
        ]
        solution = EquationSolution()
        tool_names = [entry.tool_name for entry in tool_entries if entry.tool_name]
        tool_lookup = {entry.tool_name: entry for entry in tool_entries if entry.tool_name}

        if vlm_fn and method_brief.steps and tool_entries:
            prompt = (
                f"Task: {task}\n\n"
                f"Task family: {method_brief.task_family}\n"
                f"Subject family: {method_brief.subject_family}\n\n"
                f"Method steps to follow:\n"
                + "\n".join(
                    (
                        f"  {i+1}. {step.step_id}: {step.description} "
                        f"(objective: {step.objective}; visual outcome: {step.required_visual_outcome})"
                    )
                    for i, step in enumerate(method_brief.steps)
                )
                + f"\n\nAvailable tools:\n"
                + "\n".join(
                    f"  - {entry.tool_name}: {entry.description} "
                    f"(mode={entry.interaction_mode}, shortcut={entry.shortcut or 'none'})"
                    for entry in tool_entries
                )
                + "\n\nValid action types:\n"
                + "\n".join(f"  - {name}" for name in sorted(PHASE3_ACTION_HINTS))
                + "\n\nSolve the equation by mapping each method step to one concrete tool and one concrete action."
                + "\nReturn JSON with this schema:"
                + ' {"mappings":[{"method_step_id":"","tool_name":"","action_type":"","action_parameters_hint":{},'
                + '"why_this_mapping":"","fallback_tool_name":"","fallback_action_type":"","verification_hint":""}],'
                + '"tool_gaps":[],"execution_plan":[],"quality_criteria":[]}'
            )
            try:
                response = vlm_fn(prompt, [])
                data = json.loads(response)
                candidate = EquationSolution.from_raw(data)
                if candidate.mappings:
                    solution = candidate
            except Exception as e:
                logger.warning("VLM equation solving failed: %s", e)

        if not solution.mappings:
            solution.mappings = [
                self._default_action_mapping(step, method_brief, tool_entries)
                for step in method_brief.steps
            ]

        if not solution.execution_plan:
            solution.execution_plan = [
                {
                    "step_index": index,
                    "step_id": mapping.method_step_id,
                    "description": next(
                        (step.description for step in method_brief.steps if step.step_id == mapping.method_step_id),
                        mapping.method_step_id,
                    ),
                    "tool": mapping.tool_name,
                    "action": mapping.action_type,
                    "args_hint": dict(mapping.action_parameters_hint),
                    "verification_hint": mapping.verification_hint,
                    "is_major": True,
                }
                for index, mapping in enumerate(solution.mappings, start=1)
            ]

        if not solution.quality_criteria:
            solution.quality_criteria = self._dedupe_strings(
                list(method_brief.acceptance_clues)
                + [
                    f"Output matches the task description: {task[:100]}",
                    "Every major method step leaves a visible or otherwise verifiable state change.",
                ]
            )

        covered = {mapping.method_step_id for mapping in solution.mappings if mapping.method_step_id}
        solution.uncovered_method_steps = [
            step.step_id for step in method_brief.steps if step.step_id not in covered
        ]

        if not solution.tool_gaps:
            solution.tool_gaps = [
                f"Mapped tool '{mapping.tool_name}' is not in the current tool inventory"
                for mapping in solution.mappings
                if mapping.tool_name and mapping.tool_name not in tool_names
            ]

        solution.solution_confidence = self._estimate_equation_confidence(
            solution,
            method_brief,
            tool_lookup,
        )
        return solution

    def _default_tool_name(
        self,
        preferred_names: list[str],
        tool_entries: list[ToolInventoryEntry],
        fallback: str = "browser_surface",
    ) -> str:
        entry_names = {entry.tool_name for entry in tool_entries if entry.tool_name}
        for name in preferred_names:
            if name in entry_names:
                return name
        return fallback if fallback in entry_names or not entry_names else sorted(entry_names)[0]

    def _default_action_mapping(
        self,
        step: MethodStep,
        method_brief: MethodBrief,
        tool_entries: list[ToolInventoryEntry],
    ) -> EquationMapping:
        description = f"{step.description} {step.objective} {step.required_visual_outcome}".lower()
        task_family = method_brief.task_family
        if task_family == "drawing":
            if any(token in description for token in ("silhouette", "structure", "subdivision", "layout", "grid")):
                return EquationMapping(
                    method_step_id=step.step_id,
                    tool_name=self._default_tool_name(["universal_action_space", "browser_surface"], tool_entries),
                    action_type="draw_segments",
                    action_parameters_hint={"segments": "derive straight structural guides from the subject brief"},
                    why_this_mapping="Structural drawing steps benefit from independent straight segments and explicit geometry control.",
                    fallback_tool_name="universal_action_space",
                    fallback_action_type="draw_path",
                    verification_hint=step.required_visual_outcome or "The main structure and silhouette are visibly established.",
                )
            return EquationMapping(
                method_step_id=step.step_id,
                tool_name=self._default_tool_name(["universal_action_space", "browser_surface"], tool_entries),
                action_type="draw_path",
                action_parameters_hint={"vertices": "derive curved or freehand detail paths from the subject brief"},
                why_this_mapping="Detail/material passes usually require freeform stroke work rather than only straight segments.",
                fallback_tool_name="universal_action_space",
                fallback_action_type="draw_shape",
                verification_hint=step.required_visual_outcome or "Requested details and finish cues are visibly present.",
            )
        if task_family == "navigation":
            action_type = "go_to_url" if "reach" in description or "surface" in description else "click"
            fallback_action = "go_back" if action_type == "go_to_url" else "key"
            return EquationMapping(
                method_step_id=step.step_id,
                tool_name=self._default_tool_name(["browser_surface", "universal_action_space"], tool_entries),
                action_type=action_type,
                action_parameters_hint={"goal": step.objective},
                why_this_mapping="Navigation steps must first reach or activate the correct visible browser surface.",
                fallback_tool_name="browser_surface",
                fallback_action_type=fallback_action,
                verification_hint=step.required_visual_outcome or "The intended page or affordance is visible before proceeding.",
            )
        if task_family == "form_interaction":
            action_type = "type" if any(token in description for token in ("populate", "enter", "field", "value")) else "click"
            fallback_action = "key" if action_type == "type" else "type"
            return EquationMapping(
                method_step_id=step.step_id,
                tool_name=self._default_tool_name(["browser_surface", "universal_action_space"], tool_entries),
                action_type=action_type,
                action_parameters_hint={"goal": step.objective},
                why_this_mapping="Form tasks alternate between focusing controls and entering values into them.",
                fallback_tool_name="browser_surface",
                fallback_action_type=fallback_action,
                verification_hint=step.required_visual_outcome or "The form visibly reflects the intended values or submission outcome.",
            )
        if task_family == "reading/extraction":
            return EquationMapping(
                method_step_id=step.step_id,
                tool_name=self._default_tool_name(["screenshot_capture", "browser_surface", "universal_action_space"], tool_entries),
                action_type="assert_visual",
                action_parameters_hint={"assertion": step.required_visual_outcome or step.objective},
                why_this_mapping="Reading/extraction steps should verify the visible source state instead of mutating it immediately.",
                fallback_tool_name="browser_surface",
                fallback_action_type="screenshot",
                verification_hint=step.required_visual_outcome or "Visible source evidence supports the extracted answer.",
            )
        return EquationMapping(
            method_step_id=step.step_id,
            tool_name=self._default_tool_name(["browser_surface", "universal_action_space"], tool_entries),
            action_type="click",
            action_parameters_hint={"goal": step.objective},
            why_this_mapping="The mixed-task fallback starts from a bounded visible action on the active surface.",
            fallback_tool_name="browser_surface",
            fallback_action_type="key",
            verification_hint=step.required_visual_outcome or "The expected visible state change occurred.",
        )

    def _estimate_equation_confidence(
        self,
        solution: EquationSolution,
        method_brief: MethodBrief,
        tool_lookup: dict[str, ToolInventoryEntry],
    ) -> float:
        score = 0.2
        if len(solution.mappings) >= len(method_brief.steps) and method_brief.steps:
            score += 0.35
        if not solution.uncovered_method_steps:
            score += 0.15
        if not solution.tool_gaps:
            score += 0.1
        if solution.quality_criteria:
            score += 0.05
        if solution.execution_plan:
            score += 0.05
        if solution.mappings:
            avg_tool_conf = sum(
                tool_lookup.get(mapping.tool_name, ToolInventoryEntry(tool_name="", confidence=0.4)).confidence
                for mapping in solution.mappings
            ) / max(1, len(solution.mappings))
            score += min(0.1, avg_tool_conf / 10)
        return round(min(score, 1.0), 3)
