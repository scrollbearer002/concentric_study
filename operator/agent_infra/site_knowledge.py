"""Site-specific interaction knowledge base with exhaustive web research.

Implements a three-phase learning approach grounded in peer-reviewed
agentic-AI research:

Phase 0 (Research): Screenshot the page, use Gemini + Google Search
grounding to exhaustively research how the website works — every shortcut,
every tool, every interaction pattern — from official documentation and
community knowledge.  Inspired by SeeAct (Zheng et al., 2024,
arXiv:2401.01614) which showed that grounding VLM actions in external
documentation reduces hallucination by 30-40%% vs screenshot-only.

Phase 1 (Button Mapping): Take a second screenshot, apply SoM overlay,
and use the VLM to build a precise pixel-coordinate map of every
interactive element.  Follows the Set-of-Mark paradigm (Yang et al.,
2023, arXiv:2310.11441) with GUI-explorer's transition-aware extraction
(ACL 2025, arXiv:2505.16827).

Phase 2 (Deployment): The planner queries the knowledge base to generate
correct action sequences, avoiding the tool-interaction mismatches that
caused the red-circle failure (ellipse tool bounding-box vs. path-trace).
Follows AppAgent (Yang et al., 2023, arXiv:2312.13771) Phase 2.

Knowledge is stored as a persistent JSON file per site, enabling
cross-session learning and incremental refinement per ExpeL (Zhao et al.,
AAAI 2024, arXiv:2308.10144).
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ToolAffordance:
    """What a single UI tool does and how to interact with it.

    Models the (observation, action, outcome) triple from GUI-explorer's
    transition-aware knowledge extraction.
    """
    tool_name: str
    shortcut: str | None = None
    interaction_mode: str = "unknown"
    description: str = ""
    preconditions: list[str] = field(default_factory=list)
    postconditions: list[str] = field(default_factory=list)
    known_failures: list[str] = field(default_factory=list)
    success_count: int = 0
    failure_count: int = 0

    def to_planner_hint(self) -> str:
        parts = [f"Tool '{self.tool_name}'"]
        if self.shortcut:
            parts.append(f"(shortcut: '{self.shortcut}')")
        parts.append(f"— {self.interaction_mode} mode.")
        if self.description:
            parts.append(self.description)
        if self.preconditions:
            parts.append(f"Preconditions: {'; '.join(self.preconditions)}.")
        if self.known_failures:
            parts.append(f"Known pitfalls: {'; '.join(self.known_failures)}.")
        return " ".join(parts)


@dataclass
class ButtonMapEntry:
    """Precise pixel-coordinate location of a UI element.

    Captured during Phase 1 (Button Mapping) via SoM overlay analysis.
    Stores both the SoM zone ID and the resolved pixel coordinates so the
    planner can reference buttons by name and the executor can click them
    without re-running VLM grounding.
    """
    element_name: str
    pixel_x: int = 0
    pixel_y: int = 0
    som_zone_id: int = -1
    element_type: str = "button"
    description: str = ""


@dataclass
class InteractionRule:
    """A learned sequencing or interaction constraint.

    Extracted from failure analysis per ExpeL's insight-extraction phase.
    """
    rule: str
    source: str = "exploration"
    confidence: float = 1.0
    supporting_runs: list[str] = field(default_factory=list)


class SiteKnowledge:
    """Persistent per-site knowledge base.

    Stores tool affordances, interaction rules, keyboard shortcuts, and
    modal handling patterns for a specific website. Loaded before planning
    and injected into the VLM planner's prompt.
    """

    def __init__(self, persist_path: str | Path) -> None:
        self._path = Path(persist_path)
        self.site_name: str = ""
        self.site_url: str = ""
        self.tools: dict[str, ToolAffordance] = {}
        self.rules: list[InteractionRule] = []
        self.shortcuts: dict[str, str] = {}
        self.modal_patterns: list[dict[str, str]] = []
        self.button_map: dict[str, ButtonMapEntry] = {}
        self.research_notes: str = ""
        self._load()

    def _load(self) -> None:
        if self._path.exists():
            try:
                data = json.loads(self._path.read_text(encoding="utf-8"))
                self.site_name = data.get("site_name", "")
                self.site_url = data.get("site_url", "")
                for name, tdata in data.get("tools", {}).items():
                    self.tools[name] = ToolAffordance(**tdata)
                for rdata in data.get("rules", []):
                    self.rules.append(InteractionRule(**rdata))
                self.shortcuts = data.get("shortcuts", {})
                self.modal_patterns = data.get("modal_patterns", [])
                for name, bdata in data.get("button_map", {}).items():
                    self.button_map[name] = ButtonMapEntry(**bdata)
                self.research_notes = data.get("research_notes", "")
            except (json.JSONDecodeError, OSError, TypeError) as e:
                logger.warning("Failed to load site knowledge: %s", e)

    def _persist(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "site_name": self.site_name,
            "site_url": self.site_url,
            "tools": {name: asdict(t) for name, t in self.tools.items()},
            "rules": [asdict(r) for r in self.rules],
            "shortcuts": self.shortcuts,
            "modal_patterns": self.modal_patterns,
            "button_map": {name: asdict(b) for name, b in self.button_map.items()},
            "research_notes": self.research_notes,
        }
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

    def add_tool(self, affordance: ToolAffordance) -> None:
        existing = self.tools.get(affordance.tool_name)
        if existing:
            if affordance.shortcut:
                existing.shortcut = affordance.shortcut
            if affordance.interaction_mode != "unknown":
                existing.interaction_mode = affordance.interaction_mode
            if affordance.description:
                existing.description = affordance.description
            existing.preconditions = list(set(existing.preconditions + affordance.preconditions))
            existing.postconditions = list(set(existing.postconditions + affordance.postconditions))
            existing.known_failures = list(set(existing.known_failures + affordance.known_failures))
        else:
            self.tools[affordance.tool_name] = affordance
        self._persist()

    def add_rule(self, rule: InteractionRule) -> None:
        for existing in self.rules:
            if existing.rule == rule.rule:
                existing.confidence = max(existing.confidence, rule.confidence)
                existing.supporting_runs = list(set(existing.supporting_runs + rule.supporting_runs))
                self._persist()
                return
        self.rules.append(rule)
        self._persist()

    def add_shortcut(self, key: str, description: str) -> None:
        self.shortcuts[key] = description
        self._persist()

    def add_modal_pattern(self, trigger: str, handler: str) -> None:
        for existing in self.modal_patterns:
            if existing.get("trigger") == trigger:
                existing["handler"] = handler
                self._persist()
                return
        self.modal_patterns.append({"trigger": trigger, "handler": handler})
        self._persist()

    def add_button(self, entry: ButtonMapEntry) -> None:
        self.button_map[entry.element_name] = entry
        self._persist()

    def record_tool_outcome(self, tool_name: str, success: bool, failure_note: str = "") -> None:
        tool = self.tools.get(tool_name)
        if tool:
            if success:
                tool.success_count += 1
            else:
                tool.failure_count += 1
                if failure_note:
                    tool.known_failures = list(set(tool.known_failures + [failure_note]))
            self._persist()

    def get_planner_context(self) -> str:
        """Generate a knowledge block for injection into the VLM planner prompt.

        Follows the SeeAct grounding paradigm (Zheng et al., 2024,
        arXiv:2401.01614): inject external documentation knowledge directly
        into the planner prompt so the VLM generates actions grounded in
        verified facts rather than screenshot-only guesses.
        """
        if not self.tools and not self.rules and not self.shortcuts and not self.research_notes:
            return ""
        sections = []
        if self.site_name:
            sections.append(f"=== SITE KNOWLEDGE: {self.site_name} ===")
        else:
            sections.append("=== SITE KNOWLEDGE ===")

        if self.research_notes:
            sections.append("DOCUMENTATION (from web research):")
            for line in self.research_notes.strip().split("\n"):
                sections.append(f"  {line}")

        if self.tools:
            tool_hints = [t.to_planner_hint() for t in self.tools.values()]
            sections.append("TOOL AFFORDANCES:")
            sections.extend(f"  - {h}" for h in tool_hints)

        if self.shortcuts:
            sections.append("KEYBOARD SHORTCUTS:")
            sections.extend(f"  - '{k}': {v}" for k, v in self.shortcuts.items())

        if self.button_map:
            sections.append("BUTTON LOCATIONS (pixel coords at 2x Retina):")
            for name, btn in self.button_map.items():
                sections.append(f"  - {name}: ({btn.pixel_x}, {btn.pixel_y}) [{btn.element_type}] {btn.description}")

        if self.rules:
            high_conf = [r for r in self.rules if r.confidence >= 0.7]
            if high_conf:
                sections.append("INTERACTION RULES (from past experience):")
                sections.extend(f"  - {r.rule}" for r in high_conf)

        if self.modal_patterns:
            sections.append("MODAL HANDLING:")
            sections.extend(f"  - When: {m['trigger']} -> Do: {m['handler']}" for m in self.modal_patterns)

        return "\n".join(sections)

    def get_summary(self) -> dict[str, Any]:
        return {
            "site_name": self.site_name,
            "num_tools": len(self.tools),
            "num_rules": len(self.rules),
            "num_shortcuts": len(self.shortcuts),
            "num_modal_patterns": len(self.modal_patterns),
            "num_buttons_mapped": len(self.button_map),
            "has_research": bool(self.research_notes),
        }


class ExplorationLoop:
    """Pre-task autonomous exploration of a website's UI.

    Implements AppAgent's Phase 1 (Yang et al., 2023): the agent
    systematically probes UI elements to discover affordances, then
    stores them in a SiteKnowledge base for Phase 2 (deployment).

    Also incorporates GUI-explorer's transition-aware extraction
    (arXiv:2505.16827, ACL 2025): each probe records a
    (screenshot_before, action, screenshot_after) triple, and a VLM
    extracts the affordance from the visual state transition.
    """

    _EXPLORE_PROMPT = (
        "You are analyzing a GUI application. I will show you a screenshot.\n"
        "Identify the main interactive tools, buttons, and controls visible.\n"
        "For each tool, determine:\n"
        "1. tool_name: A short identifier (e.g., 'pen_tool', 'ellipse_tool')\n"
        "2. shortcut: The keyboard shortcut if visible or known (e.g., 'p', 'o')\n"
        "3. interaction_mode: How the tool works when active. One of:\n"
        '   - "path_trace" (user draws by dragging through points)\n'
        '   - "bounding_box" (user drags to define a rectangle/ellipse)\n'
        '   - "click_place" (user clicks to place an object)\n'
        '   - "click_type" (user clicks then types text)\n'
        '   - "toggle" (clicking toggles a state on/off)\n'
        '   - "select" (clicking selects from options)\n'
        "4. description: One sentence explaining what the tool does\n\n"
        "Also identify:\n"
        "- Keyboard shortcuts visible in tooltips or menus\n"
        "- Color picker / style controls and how they work\n"
        "- Any modal dialogs or confirmation patterns\n\n"
        "Output a JSON object with this structure:\n"
        '{"tools": [...], "shortcuts": {...}, "modal_patterns": [...], '
        '"operation_rules": [...]}\n'
        "Where operation_rules are sequencing constraints like "
        '"set color BEFORE drawing" or "confirm dialog after clear".\n'
        "Output ONLY the JSON."
    )

    _TRANSITION_PROMPT = (
        "I'm showing you two screenshots: BEFORE and AFTER pressing '{key}'.\n"
        "What changed? What tool or mode was activated?\n"
        "How does this tool expect the user to interact (drag bounding box, "
        "trace path, click to place, etc.)?\n\n"
        "Output JSON: "
        '{{"tool_name": "...", "shortcut": "{key}", '
        '"interaction_mode": "...", "description": "...", '
        '"visual_change": "..."}}\n'
        "Output ONLY the JSON."
    )

    _RESEARCH_PROMPT = (
        "You are a PhD-level GUI automation researcher. I am showing you a "
        "screenshot of a web application. Your task is to produce an EXHAUSTIVE "
        "reference manual for automating this application via keyboard and mouse.\n\n"
        "Use Google Search to look up the official documentation, keyboard shortcuts, "
        "and community guides for this application.\n\n"
        "You MUST cover ALL of the following in exhaustive detail:\n\n"
        "1. EVERY keyboard shortcut (letter keys, number keys, modifier combos)\n"
        "2. EVERY tool in the toolbar — what it does, how it expects interaction:\n"
        "   - Does it use bounding-box drag? (user drags to define a rectangle)\n"
        "   - Does it use path tracing? (user clicks/drags to draw freeform)\n"
        "   - Does it use click-to-place? (user clicks to place an object)\n"
        "3. The CORRECT order of operations for:\n"
        "   - Changing stroke/fill color (before or after tool selection?)\n"
        "   - Drawing shapes (which tool, which interaction mode)\n"
        "   - Clearing the canvas (what dialog appears, how to confirm)\n"
        "4. ALL modal dialogs, confirmation prompts, and how to dismiss them\n"
        "5. Color picker behavior — how to select stroke vs fill colors\n"
        "6. Any gotchas, edge cases, or common mistakes\n\n"
        "Output a JSON object with this EXACT structure:\n"
        "{\n"
        '  "site_name": "<name of the application>",\n'
        '  "site_url": "<url pattern>",\n'
        '  "tools": [{"tool_name": "...", "shortcut": "...", '
        '"interaction_mode": "path_trace|bounding_box|click_place|click_type|toggle|select", '
        '"description": "...", '
        '"preconditions": ["..."], "postconditions": ["..."]}],\n'
        '  "shortcuts": {"key": "description", ...},\n'
        '  "modal_patterns": [{"trigger": "...", "handler": "..."}],\n'
        '  "operation_rules": ["rule 1", "rule 2", ...],\n'
        '  "color_workflow": "step-by-step description of how to change color",\n'
        '  "gotchas": ["gotcha 1", "gotcha 2", ...]\n'
        "}\n"
        "Be EXHAUSTIVE. This will be used to automate the app with zero human intervention.\n"
        "Output ONLY the JSON."
    )

    _BUTTON_MAP_PROMPT = (
        "You are a pixel-precise GUI element mapper. I am showing you a "
        "screenshot of a web application with a numbered Set-of-Mark (SoM) "
        "overlay grid. Each numbered zone corresponds to a region of the page.\n\n"
        "For EVERY interactive element you can see (buttons, tools, color "
        "swatches, sliders, toggles, icons), identify:\n"
        "1. element_name: a short identifier (e.g., 'red_swatch', 'pen_tool', 'undo_button')\n"
        "2. som_zone_id: the SoM zone number that best covers this element\n"
        "3. element_type: 'button', 'tool', 'swatch', 'slider', 'toggle', 'icon'\n"
        "4. description: what clicking/interacting with this element does\n\n"
        "IMPORTANT: Map EVERY color swatch individually (e.g., 'stroke_black_swatch', "
        "'stroke_red_swatch', 'stroke_green_swatch', etc.)\n"
        "IMPORTANT: Map EVERY toolbar tool individually.\n\n"
        "Output a JSON object:\n"
        '{"buttons": [{"element_name": "...", "som_zone_id": <int>, '
        '"element_type": "...", "description": "..."}]}\n'
        "Output ONLY the JSON."
    )

    def __init__(
        self,
        agent,
        knowledge: SiteKnowledge,
        vision_engine=None,
        site_name: str = "",
    ) -> None:
        self._agent = agent
        self._knowledge = knowledge
        self._vision_engine = vision_engine
        self._knowledge.site_name = site_name

    def research_site(self, screenshot_path: str) -> SiteKnowledge:
        """Phase 0: Exhaustive web research about the website.

        Takes a screenshot, sends it to Gemini 2.5 Pro WITH Google Search
        grounding enabled. The VLM identifies the application, searches for
        its documentation, and produces a comprehensive interaction manual.

        This implements the SeeAct principle (Zheng et al., 2024,
        arXiv:2401.01614): grounding VLM actions in external documentation
        rather than relying solely on visual perception, which reduces
        hallucination rates by 30-40%%.

        Also aligned with CogAgent (Hong et al., 2023, arXiv:2312.08914)
        which demonstrated that pre-training on UI screenshots + text docs
        yields superior GUI understanding vs. screenshots alone.
        """
        from google.genai.types import GenerateContentConfig, GoogleSearch, Tool

        logger.info("Phase 0: Researching site from screenshot via Google Search grounding")
        print("  [RESEARCH] Phase 0: Sending screenshot to Gemini + Google Search...")
        try:
            uploaded = self._agent._client.files.upload(file=screenshot_path)

            config = GenerateContentConfig(
                temperature=0.1,
                tools=[Tool(google_search=GoogleSearch())],
                response_mime_type="text/plain",
            )

            response = self._agent._client.models.generate_content(
                model="gemini-2.5-pro",
                contents=[uploaded, self._RESEARCH_PROMPT],
                config=config,
            )

            raw = response.text.strip()
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1]
                if raw.endswith("```"):
                    raw = raw[:-3].strip()

            try:
                data = json.loads(raw)
                self._ingest_exploration_data(data)
                self._knowledge.site_url = data.get("site_url", "")

                color_workflow = data.get("color_workflow", "")
                gotchas = data.get("gotchas", [])
                research_parts = []
                if color_workflow:
                    research_parts.append(f"COLOR WORKFLOW: {color_workflow}")
                for g in gotchas:
                    research_parts.append(f"GOTCHA: {g}")
                if research_parts:
                    self._knowledge.research_notes = "\n".join(research_parts)

                for g in gotchas:
                    self._knowledge.add_rule(InteractionRule(
                        rule=g, source="web_research", confidence=0.95,
                    ))

            except json.JSONDecodeError:
                logger.info("Research returned prose instead of JSON, storing as notes")
                self._knowledge.research_notes = raw[:3000]

            try:
                self._agent._client.files.delete(name=uploaded.name)
            except Exception:
                pass

            print(f"  [RESEARCH] Learned {self._knowledge.get_summary()['num_tools']} tools, "
                  f"{self._knowledge.get_summary()['num_shortcuts']} shortcuts, "
                  f"{self._knowledge.get_summary()['num_rules']} rules from web research")
        except Exception as e:
            logger.warning("Phase 0 research failed: %s", e)
            print(f"  [RESEARCH] Web research failed ({e}), falling back to visual-only")

        return self._knowledge

    def map_buttons(self, screenshot_path: str, som_path: str = "",
                    coords_map: dict | None = None) -> SiteKnowledge:
        """Phase 1: Precise button mapping via SoM overlay.

        Takes a second screenshot with the SoM overlay applied, and uses
        the VLM to identify every interactive element with its SoM zone ID.
        The zone IDs are then resolved to pixel coordinates via the
        coords_map from the VisualGroundingEngine.

        This follows Set-of-Mark (Yang et al., 2023, arXiv:2310.11441):
        numbered visual marks provide unambiguous spatial references that
        the VLM can use to report element locations precisely.
        """
        import subprocess

        logger.info("Phase 1: Mapping all buttons from SoM overlay")
        print("  [BUTTONS] Phase 1: Mapping all interactive elements...")

        if not som_path and self._vision_engine:
            subprocess.run(["screencapture", "-x", screenshot_path], check=True, timeout=10)
            coords_map, som_path = self._vision_engine.generate_som_overlay(
                screenshot_path, output_filename="som_button_map.png"
            )

        if not som_path:
            logger.warning("No SoM path available for button mapping")
            return self._knowledge

        try:
            uploaded = self._agent._client.files.upload(file=som_path)
            response = self._agent._client.models.generate_content(
                model="gemini-2.5-pro",
                contents=[uploaded, self._BUTTON_MAP_PROMPT],
                config=self._agent._gen_config_json,
            )
            raw = response.text.strip()
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1]
                if raw.endswith("```"):
                    raw = raw[:-3]
            data = json.loads(raw)

            mapped_count = 0
            for btn_data in data.get("buttons", []):
                name = btn_data.get("element_name", "unknown")
                zone_id = btn_data.get("som_zone_id", -1)
                px, py = 0, 0
                if coords_map and str(zone_id) in coords_map:
                    px, py = coords_map[str(zone_id)]
                elif coords_map and zone_id in coords_map:
                    px, py = coords_map[zone_id]
                entry = ButtonMapEntry(
                    element_name=name,
                    pixel_x=px,
                    pixel_y=py,
                    som_zone_id=zone_id,
                    element_type=btn_data.get("element_type", "button"),
                    description=btn_data.get("description", ""),
                )
                self._knowledge.add_button(entry)
                mapped_count += 1

            try:
                self._agent._client.files.delete(name=uploaded.name)
            except Exception:
                pass

            print(f"  [BUTTONS] Mapped {mapped_count} interactive elements with pixel coordinates")
        except Exception as e:
            logger.warning("Phase 1 button mapping failed: %s", e)
            print(f"  [BUTTONS] Button mapping failed ({e})")

        return self._knowledge

    def full_exploration(self, screenshot_path: str) -> SiteKnowledge:
        """Run the complete three-phase exploration pipeline.

        Phase 0: Web research (screenshot + Google Search grounding)
        Phase 1: Button mapping (SoM overlay + VLM coordinate extraction)
        Phase 1.5: Visual-only affordance extraction (original explore_from_screenshot)
        """
        import subprocess

        print("\n  " + "="*50)
        print("  EXPLORATION PIPELINE: Learning the website")
        print("  " + "="*50)

        print("\n  --- Phase 0: Web Research (Google Search + VLM) ---")
        self.research_site(screenshot_path)

        print("\n  --- Phase 1: Button Mapping (SoM + VLM) ---")
        if self._vision_engine:
            map_screenshot = screenshot_path.replace(".png", "_buttonmap.png")
            subprocess.run(["screencapture", "-x", map_screenshot], check=True, timeout=10)
            coords_map, som_path = self._vision_engine.generate_som_overlay(
                map_screenshot, output_filename="som_button_map.png"
            )
            self.map_buttons(map_screenshot, som_path, coords_map)
        else:
            print("  [BUTTONS] Skipped (no vision engine)")

        print("\n  --- Phase 1.5: Visual Affordance Extraction (VLM) ---")
        self.explore_from_screenshot(screenshot_path)

        summary = self._knowledge.get_summary()
        print(f"\n  [EXPLORE] Exploration complete:")
        print(f"    Tools: {summary['num_tools']}")
        print(f"    Shortcuts: {summary['num_shortcuts']}")
        print(f"    Rules: {summary['num_rules']}")
        print(f"    Buttons mapped: {summary['num_buttons_mapped']}")
        print(f"    Web research: {'Yes' if summary['has_research'] else 'No'}")
        print(f"    Modal patterns: {summary['num_modal_patterns']}")
        print("  " + "="*50)

        return self._knowledge

    def explore_from_screenshot(self, screenshot_path: str) -> SiteKnowledge:
        """Phase 1A: Extract tool affordances from a single screenshot via VLM.

        This is the lightweight exploration path -- no interaction needed,
        just visual analysis of the current UI state.
        """
        logger.info("Exploring site from screenshot: %s", screenshot_path)
        try:
            uploaded = self._agent._client.files.upload(file=screenshot_path)
            response = self._agent._client.models.generate_content(
                model="gemini-2.5-pro",
                contents=[uploaded, self._EXPLORE_PROMPT],
                config=self._agent._gen_config_json,
            )
            raw = response.text.strip()
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1]
                if raw.endswith("```"):
                    raw = raw[:-3]
            data = json.loads(raw)
            self._ingest_exploration_data(data)
            try:
                self._agent._client.files.delete(name=uploaded.name)
            except Exception:
                pass
        except Exception as e:
            logger.warning("Exploration from screenshot failed: %s", e)
        return self._knowledge

    def explore_shortcut(self, key: str, pre_screenshot: str) -> ToolAffordance | None:
        """Phase 1B: Probe a single keyboard shortcut via transition analysis.

        Implements GUI-explorer's transition-aware extraction:
        1. Capture pre-state screenshot
        2. Press the key
        3. Capture post-state screenshot
        4. VLM compares the two to extract the affordance

        This is the interactive exploration path -- requires OS-level access.
        """
        import subprocess
        logger.info("Exploring shortcut '%s' via transition analysis", key)
        try:
            self._agent.enforce_app_focus("Safari")
            time.sleep(0.3)

            self._agent.execute_keystroke(key)
            time.sleep(0.5)

            post_screenshot = pre_screenshot.replace(".png", f"_after_{key}.png")
            subprocess.run(["screencapture", "-x", post_screenshot], check=True, timeout=10)

            pre_uploaded = self._agent._client.files.upload(file=pre_screenshot)
            post_uploaded = self._agent._client.files.upload(file=post_screenshot)

            prompt = self._TRANSITION_PROMPT.format(key=key)
            response = self._agent._client.models.generate_content(
                model="gemini-2.5-pro",
                contents=[
                    "BEFORE screenshot:", pre_uploaded,
                    "AFTER screenshot:", post_uploaded,
                    prompt,
                ],
                config=self._agent._gen_config_json,
            )
            raw = response.text.strip()
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1]
                if raw.endswith("```"):
                    raw = raw[:-3]
            data = json.loads(raw)

            affordance = ToolAffordance(
                tool_name=data.get("tool_name", f"shortcut_{key}"),
                shortcut=key,
                interaction_mode=data.get("interaction_mode", "unknown"),
                description=data.get("description", ""),
            )
            self._knowledge.add_tool(affordance)
            self._knowledge.add_shortcut(key, data.get("description", f"Activates {affordance.tool_name}"))

            for uploaded in (pre_uploaded, post_uploaded):
                try:
                    self._agent._client.files.delete(name=uploaded.name)
                except Exception:
                    pass

            return affordance
        except Exception as e:
            logger.warning("Shortcut exploration for '%s' failed: %s", key, e)
            return None

    def explore_common_shortcuts(self, pre_screenshot: str, keys: list[str] | None = None) -> SiteKnowledge:
        """Probe a set of common shortcuts via transition analysis."""
        if keys is None:
            keys = ["p", "o", "r", "l", "a", "t", "d", "e"]
        for key in keys:
            self.explore_shortcut(key, pre_screenshot)
            self._agent.execute_keystroke("escape")
            time.sleep(0.3)
        return self._knowledge

    def learn_from_failure(
        self, run_id: str, action_type: str, goal: str, error: str,
    ) -> None:
        """Post-task learning: extract a rule from a failure.

        Implements ExpeL's insight extraction phase (Zhao et al., AAAI 2024)
        and AgentDebug's root-cause isolation (Zhu et al., 2025,
        arXiv:2509.25370) for cascading error prevention.
        """
        rule_text = f"When attempting '{action_type}' for goal '{goal}': {error}"
        self._knowledge.add_rule(InteractionRule(
            rule=rule_text,
            source="failure",
            confidence=0.9,
            supporting_runs=[run_id],
        ))
        tool = self._knowledge.tools.get(action_type)
        if tool:
            tool.failure_count += 1
            tool.known_failures = list(set(tool.known_failures + [error]))
        self._knowledge._persist()

    def _ingest_exploration_data(self, data: dict) -> None:
        for tool_data in data.get("tools", []):
            affordance = ToolAffordance(
                tool_name=tool_data.get("tool_name", "unknown"),
                shortcut=tool_data.get("shortcut"),
                interaction_mode=tool_data.get("interaction_mode", "unknown"),
                description=tool_data.get("description", ""),
            )
            self._knowledge.add_tool(affordance)

        for key, desc in data.get("shortcuts", {}).items():
            self._knowledge.add_shortcut(key, desc)

        for pattern in data.get("modal_patterns", []):
            trigger = pattern.get("trigger", "")
            handler = pattern.get("handler", "")
            if trigger:
                self._knowledge.add_modal_pattern(trigger, handler)

        for rule_text in data.get("operation_rules", []):
            self._knowledge.add_rule(InteractionRule(
                rule=rule_text,
                source="exploration",
                confidence=0.8,
            ))
