#!/usr/bin/env python3
"""Universal Visual Web Agent — single entry point for any task on any site.

Accepts a URL and a natural language goal, then autonomously activates
the correct capabilities, generates an action plan, and executes it
with full structured tracing, self-healing, and verification.

This replaces the per-task scripts (test_excalidraw_covt.py,
test_kleki_bmw.py, test_login_flow.py) with a single orchestrator
that dynamically wires every module based on task requirements.

Architecture grounded in:
- CogAgent (Hong et al., CVPR 2024): Single agent, unified action space
  across web/desktop/mobile — no per-site scripting.
- Magentic-One (Microsoft, 2024): Orchestrator creates task-specific
  plans and dynamically revises them; sub-agents are modular and can be
  added/removed without prompt tuning.
- WebVoyager (He et al., 2024): End-to-end web agent on live sites with
  minimal action space {click, type, scroll, wait, go_back, answer}.
- OSWorld (Xie et al., NeurIPS 2024, arXiv:2404.07972): Universal
  observation space (screenshot + a11y tree) across OS environments.
- SeeAct (Zheng et al., ICML 2024, arXiv:2401.01614): Two-stage
  action generation (VLM) then grounding (coordinate resolution).
- AppAgent v2 (arXiv:2408.11824): Explore-then-deploy with structured
  knowledge base; RAG retrieval at deploy time.
- DynaSaur (Adobe, COLM 2025, arXiv:2411.01747): Dynamic action
  creation beyond predefined sets; actions accumulate for reuse.
- ExpeL (Zhao et al., AAAI 2024, arXiv:2308.10144): Experiential
  learning — extract natural language rules from trajectories that
  transfer to novel tasks without parameter updates.
- UGround (Gur et al., ICLR 2025 Oral, arXiv:2410.05243): Universal
  visual grounding — pixel-level operations across platforms.
- Magma (Yang et al., CVPR 2025, arXiv:2502.13130): Foundation model
  for multimodal agents — perceive, reason, act in one model.
- Brooks (1986), "A Robust Layered Control System for a Mobile Robot":
  Subsumption architecture — capabilities layer incrementally.

Usage:
  python3 agent.py --url https://excalidraw.com \\
                   --goal "Draw 4 concentric black triangles"

  python3 agent.py --url https://mail.google.com \\
                   --goal "Log in and compose a new email to john@example.com"

  python3 agent.py --goal "Draw a BMW E30 M3 on Kleki" \\
                   --url https://kleki.com
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import logging
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("agent")

sys.path.insert(0, str(Path(__file__).parent))

from capability_router import CapabilityRouter, CapabilityKind, classify_task
from action_space import UnifiedActionSpace, ActionCategory
from window_capture import capture_front_window
from agent_infra.host_tool_health import HostToolHealth


# =========================================================================
# LOGGING — universal, not per-script
# =========================================================================

def _exec_log(event: str, detail: str = "", data: dict | None = None) -> None:
    path = os.environ.get("EXECUTION_LOG_PATH")
    if not path:
        return
    try:
        ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        ms = f".{int((time.time() % 1) * 1000):03d}"
        line = f"[{ts}{ms}] {event}"
        if detail:
            line += f" | {detail}"
        if data:
            line += f" | {json.dumps(data)}"
        with open(path, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass


def _trace(loc: str, msg: str, data: dict | None = None) -> None:
    try:
        log_dir = Path(__file__).parent / "cre"
        log_path = log_dir / "agent_debug.log"
        with open(str(log_path), "a") as f:
            f.write(json.dumps({
                "location": loc, "message": msg,
                "data": data or {},
                "timestamp": int(time.time() * 1000),
            }) + "\n")
    except Exception:
        pass


# =========================================================================
# IMAGE UTILITIES (shared by all tasks)
# =========================================================================

def _get_screenshot_center(path: str) -> tuple[int, int]:
    try:
        from PIL import Image
        with Image.open(path) as im:
            w, h = im.size
        return (w // 2, h // 2)
    except Exception:
        return (720, 450)


def _nearest_neighbor_order(points: list[tuple[int, int]]) -> list[tuple[int, int]]:
    if len(points) <= 2:
        return list(points)
    remaining = list(points)
    ordered = [remaining.pop(0)]
    while remaining:
        last = ordered[-1]
        nearest_idx = min(range(len(remaining)),
                          key=lambda i: ((last[0] - remaining[i][0]) ** 2 +
                                         (last[1] - remaining[i][1]) ** 2))
        ordered.append(remaining.pop(nearest_idx))
    return ordered


# =========================================================================
# pHash CACHE VALIDATION (universal, not per-script)
# =========================================================================

_PHASH_BASE_TOLERANCE = 0.15
_PHASH_MAX_TOLERANCE = 0.35
_PHASH_HISTORY_WINDOW = 20
_phash_distance_history: list[float] = []
_phash_comparison_log: list[dict] = []


def _compute_region_phash(screenshot_path: str, x: int, y: int, radius: int = 40) -> str | None:
    try:
        from PIL import Image
        import imagehash
        with Image.open(screenshot_path) as im:
            box = (max(0, x - radius), max(0, y - radius),
                   min(im.width, x + radius), min(im.height, y + radius))
            region = im.crop(box).convert("L").resize((32, 32))
            return str(imagehash.phash(region))
    except Exception:
        return None


def _validate_coord_cache_entry(screenshot_path: str, cached: dict, tolerance: float | None = None) -> bool:
    """Validate a cached coordinate via adaptive pHash comparison.

    Parameter order matches the legacy test's signature (screenshot_path first)
    because action_handlers.py calls it as (ctx.current_state_path, cached).
    """
    stored_hash = cached.get("region_hash")
    if not stored_hash:
        return True
    current_hash = _compute_region_phash(screenshot_path, cached["x"], cached["y"])
    if current_hash is None:
        return True
    try:
        import imagehash
        distance = (imagehash.hex_to_hash(stored_hash) - imagehash.hex_to_hash(current_hash)) / 64.0

        if tolerance is not None:
            effective_tolerance = tolerance
        else:
            effective_tolerance = _PHASH_BASE_TOLERANCE
            if len(_phash_distance_history) >= 5:
                import statistics
                mu = statistics.mean(_phash_distance_history)
                sigma = statistics.stdev(_phash_distance_history)
                effective_tolerance = min(_PHASH_MAX_TOLERANCE, mu + 2 * sigma)

        valid = distance <= effective_tolerance
        _phash_distance_history.append(distance)
        if len(_phash_distance_history) > _PHASH_HISTORY_WINDOW:
            _phash_distance_history.pop(0)

        stored_hash_hex = stored_hash[:8] if len(stored_hash) >= 8 else stored_hash
        current_hash_hex = current_hash[:8] if len(current_hash) >= 8 else current_hash
        _phash_comparison_log.append({
            "x": cached["x"], "y": cached["y"],
            "distance": round(distance, 4),
            "tolerance": round(effective_tolerance, 4),
            "valid": valid,
            "stored_hash": stored_hash_hex,
            "current_hash": current_hash_hex,
        })
        return valid
    except Exception:
        return True


def _get_phash_log() -> list[dict]:
    return list(_phash_comparison_log)


# =========================================================================
# AGENT INITIALIZATION
# =========================================================================

def _init_enterprise_agent(router_instance=None):
    """Initialize MacOSAgentCore with optional pre-built InferenceRouter."""
    try:
        from agent_core import MacOSAgentCore
        from visual_engine import VisualGroundingEngine
    except ImportError:
        return None, None

    try:
        if router_instance is None:
            from inference_router import InferenceRouter
            router_instance = InferenceRouter()

        agent = MacOSAgentCore(router=router_instance)
        vision_engine = VisualGroundingEngine(
            grid_size=12,
            output_dir=str(Path(__file__).parent),
        )
        return agent, vision_engine
    except Exception as e:
        logger.warning("Enterprise agent init failed: %s", e)
        return None, None


# =========================================================================
# SAFARI CONTROL (universal — works for any URL)
# =========================================================================

def _open_safari(url: str) -> None:
    """Launch Safari to the given URL. Best-effort."""
    logger.info("Opening Safari to %s", url)
    _exec_log("safari_open", url)
    try:
        subprocess.run(["open", "-a", "Safari", url], check=True, timeout=5)
    except Exception as e:
        logger.warning("Could not open Safari: %s", e)


def _maximize_safari(agent=None) -> None:
    try:
        if agent:
            info = agent.get_screen_info()
            w = int(info.get("logical_width", 1440))
            h = int(info.get("logical_height", 900))
        else:
            w, h = 1440, 900
        script = f'tell application "Safari" to set bounds of front window to {{0, 22, {w}, {h}}}'
        subprocess.run(["osascript", "-e", script], check=False,
                       capture_output=True, timeout=5)
    except Exception:
        pass


def _poll_readiness(agent, url: str, cre_dir: Path) -> bool:
    """Smart readiness poll using Gemini Flash.

    Generalizes the Excalidraw-specific poll to work with any URL by
    asking a generic "is the page loaded" question.
    """
    time.sleep(3)
    tmp = str(cre_dir / "_readiness_check.png")
    consecutive_yes = 0
    max_polls = 9

    from urllib.parse import urlparse
    domain = urlparse(url).netloc

    for poll in range(1, max_polls + 1):
        try:
            capture_front_window(tmp)
            ready = agent.assert_visual_state(
                tmp,
                f"Is the {domain} page fully loaded with interactive content visible? "
                "Reply YES if the main page content is rendered and usable.",
                model="gemini-2.0-flash",
            )
            if ready:
                consecutive_yes += 1
                if consecutive_yes >= 2:
                    logger.info("Page ready after %d polls", poll)
                    return True
            else:
                consecutive_yes = 0
        except Exception:
            consecutive_yes = 0
        time.sleep(1)

    logger.warning("Max readiness polls reached — proceeding anyway")
    return False


def _dismiss_welcome_screen(agent, cre_dir: Path):
    """Detect and dismiss any welcome/splash screen before action execution.

    Many web apps (Excalidraw, Figma, etc.) show a welcome overlay or
    empty-state content on first load.  This function detects it and
    applies targeted dismissal strategies.

    Excalidraw-specific: the "welcome screen" is actually decorative
    empty-state content (logo + menu items) rendered ON the canvas.
    It's not a blocking modal — the toolbar is functional.  Clicking
    anywhere on the canvas or starting to draw clears it.
    """
    _ASSERT_CLEAN = (
        "Is the main application workspace fully usable? Specifically: "
        "is the toolbar visible at the top AND is the canvas area clear "
        "of any large centered welcome logos, intro text, or menu lists? "
        "Reply YES or NO."
    )

    check_path = str(cre_dir / "_welcome_check.png")
    capture_front_window(check_path)
    try:
        agent.assert_visual_state(check_path, _ASSERT_CLEAN)
        logger.info("No welcome screen detected")
        return
    except (RuntimeError, Exception):
        pass

    logger.info("Welcome screen / empty-state content detected — dismissing...")

    agent.execute_global_click(200, 800)
    time.sleep(0.3)

    agent.execute_keystroke("v")
    time.sleep(0.2)

    agent.execute_global_click(200, 800)
    time.sleep(0.5)

    verify_path = str(cre_dir / "_welcome_dismiss_verify.png")
    capture_front_window(verify_path)
    try:
        agent.assert_visual_state(verify_path, _ASSERT_CLEAN)
        logger.info("Welcome screen dismissed via canvas click")
    except (RuntimeError, Exception):
        logger.info("Empty-state content may still be visible — toolbar is functional, proceeding")


# =========================================================================
# PERCEPTION PIPELINE (universal)
# =========================================================================

def _build_perception(agent, vision_engine, capabilities: CapabilityRouter,
                      screenshot_path: str) -> dict[str, Any]:
    """Build the full perception state: screenshot + SoM + a11y + element map.

    This is the universal equivalent of _capture_enterprise_ui from
    startup.py, but it dynamically uses whatever capabilities are active.
    """
    perception: dict[str, Any] = {}

    subprocess.run(["screencapture", "-x", screenshot_path], check=True, timeout=10)
    cx, cy = _get_screenshot_center(screenshot_path)
    perception["canvas_center"] = {"x": cx, "y": cy}
    perception["canvas_center_x"] = cx
    perception["canvas_center_y"] = cy
    perception["page_loaded"] = True

    if capabilities.is_active(CapabilityKind.PERCEPTION_SOM) and vision_engine:
        try:
            coords_map, som_path = vision_engine.generate_som_overlay(
                screenshot_path, output_filename="som_overlay.png",
            )
            perception["som_coords"] = coords_map
            perception["som_path"] = som_path
            perception["som_zones"] = len(coords_map)
            logger.info("SoM overlay: %d zones", len(coords_map))
        except Exception as e:
            logger.warning("SoM failed: %s", e)

    if capabilities.is_active(CapabilityKind.PERCEPTION_A11Y):
        a11y_engine = capabilities.get(CapabilityKind.PERCEPTION_A11Y)
        if a11y_engine:
            try:
                elements = a11y_engine.extract("Safari")
                interactive = [e for e in elements if e.is_interactive]
                perception["a11y_total"] = len(elements)
                perception["a11y_interactive"] = len(interactive)
                perception["a11y_elements"] = elements
                logger.info("A11y: %d elements (%d interactive)",
                           len(elements), len(interactive))
            except Exception as e:
                logger.warning("A11y extraction failed: %s", e)

    if capabilities.is_active(CapabilityKind.PERCEPTION_FUSION):
        element_map = capabilities.get(CapabilityKind.PERCEPTION_FUSION)
        if element_map:
            a11y_elements = perception.get("a11y_elements", [])
            if a11y_elements:
                element_map.ingest_a11y(a11y_elements)
            som_coords = perception.get("som_coords")
            if som_coords:
                element_map.ingest_som(som_coords)
            if a11y_elements and som_coords:
                element_map.merge_a11y_and_som()
            perception["element_map"] = element_map

    return perception


# =========================================================================
# VLM PLAN GENERATION (universal, with constrained decoding)
# =========================================================================

# --- Intervention 2: Pydantic Constrained Decoding (Lightweight LLaMPPL) ---
# Instead of hoping the VLM outputs valid JSON, we enforce structural validity
# at the API level using Pydantic response_schema. This prevents the Semantic
# Trap (TrapEval, arXiv:2601.22655) where models match surface patterns
# instead of producing structurally correct output.
#
# Research basis:
# - DisCIPL (MIT CSAIL, COLM 2025): LLaMPPL encodes "strict, mathematically
#   verifiable constraints" as executable code. Pydantic schemas are the
#   lightweight equivalent for API-level constrained decoding.
# - PydanticAI: "Employing Pydantic to marshal a VLM's latent space outputs
#   into strict, object-oriented data structures is a fundamental,
#   non-negotiable requirement for production-grade reliability."
# - Google Gemini API (Nov 2025): Native expanded JSON Schema support with
#   implicit property ordering, ensuring key sequence preservation.

try:
    from pydantic import BaseModel as _PydanticBase

    class _PlanStep(_PydanticBase):
        """One step in a VLM-generated action plan. Schema enforced at API level."""
        action: str
        args: dict[str, Any] = {}
        description: str = ""

    class _ActionPlan(_PydanticBase):
        """Constrained schema for VLM plan output. Prevents malformed JSON."""
        steps: list[_PlanStep]

    _PLAN_SCHEMA_AVAILABLE = True
except ImportError:
    _PLAN_SCHEMA_AVAILABLE = False


def _get_subject_brief(agent, goal: str) -> str | None:
    """Look up in detail what to draw using Google Search grounding.

    For drawing goals, asks Gemini to produce a short visual reference
    (proportions, silhouette, key features) so the planner can generate
    accurate geometry. See SUBJECT_LOOKUP_FOR_DRAWING.md.
    """
    if not agent or not getattr(agent, "_client", None):
        return None
    goal_lower = goal.lower()
    if "draw" not in goal_lower and "sketch" not in goal_lower and "paint" not in goal_lower:
        return None
    try:
        from google.genai import types
        config = types.GenerateContentConfig(
            temperature=0.2,
            tools=[types.Tool(google_search=types.GoogleSearch())],
            response_mime_type="text/plain",
        )
        prompt = (
            f"The user wants to create this drawing: \"{goal}\".\n\n"
            "Use web search to find accurate visual details for a realistic drawing. "
            "Output a single short paragraph (3-6 sentences) that describes:\n"
            "- Key proportions and silhouette (e.g. side view: relative lengths, curves, angles).\n"
            "- Distinctive features that must appear for the subject to be recognizable.\n"
            "- Any notable shapes, lines, or landmarks (e.g. wheel arches, roofline, windows).\n\n"
            "Write only the paragraph, no preamble. This will be given to a drawing planner."
        )
        response = agent._client.models.generate_content(
            model="gemini-2.5-pro",
            contents=[prompt],
            config=config,
        )
        raw = (response.text or "").strip()
        if len(raw) > 50:
            logger.info("Subject brief obtained (%d chars) for drawing goal", len(raw))
            return raw
    except Exception as e:
        logger.warning("Subject brief lookup failed: %s", e)
    return None


def _strip_json_fence(raw: str) -> str:
    text = (raw or "").strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text
        if text.endswith("```"):
            text = text[:-3]
    return text.strip()


def _parse_json_response(raw: str) -> Any:
    text = _strip_json_fence(raw)
    return json.loads(text)


def _method_brief_dict(research_brief) -> dict[str, Any]:
    method_brief = getattr(research_brief, "method_brief", None)
    if method_brief is None:
        return {}
    if hasattr(method_brief, "to_dict"):
        try:
            return method_brief.to_dict()
        except Exception:
            return {}
    if isinstance(method_brief, dict):
        return method_brief
    return {}


def _build_research_planner_block(research_brief) -> str:
    if not research_brief:
        return ""

    lines: list[str] = []

    method_brief = _method_brief_dict(research_brief)
    method_steps = method_brief.get("steps", [])
    if method_steps:
        lines.append("Research-backed method steps:")
        for step in method_steps[:6]:
            if isinstance(step, dict):
                desc = step.get("description") or step.get("objective") or str(step)
            else:
                desc = str(step)
            lines.append(f"  - {desc}")

    execution_plan = getattr(research_brief, "execution_plan", []) or []
    if execution_plan:
        lines.append("Research-backed execution strategy:")
        for step in execution_plan[:6]:
            desc = step.get("description") or step.get("step") or step.get("how") or str(step)
            tool = step.get("tool", "")
            suffix = f" [tool: {tool}]" if tool else ""
            lines.append(f"  - {desc}{suffix}")

    quality_criteria = getattr(research_brief, "quality_criteria", []) or []
    if quality_criteria:
        lines.append("Quality criteria the result must satisfy:")
        for criterion in quality_criteria[:8]:
            lines.append(f"  - {criterion}")

    references = method_brief.get("references", [])
    if references:
        lines.append("Research references consulted:")
        for ref in references[:3]:
            title = (ref or {}).get("title", "").strip()
            url = (ref or {}).get("url", "").strip()
            if title:
                suffix = f" ({url})" if url else ""
                lines.append(f"  - {title}{suffix}")

    if not lines:
        return ""
    return "\nResearch brief:\n" + "\n".join(lines) + "\n"


def _normalize_research_quality_criteria(goal: str, criteria: list[str] | None) -> list[str]:
    if not criteria:
        return []

    goal_lower = goal.lower()
    wants_grayscale = any(token in goal_lower for token in ["grayscale", "monochrome", "black and white"])
    normalized: list[str] = []
    seen: set[str] = set()

    for item in criteria:
        text = str(item or "").strip()
        if not text:
            continue
        lower = text.lower()
        if wants_grayscale and "color" in lower and "varied" in lower:
            continue
        if lower in seen:
            continue
        normalized.append(text)
        seen.add(lower)

    return normalized[:8]


def _make_research_search_fn(agent):
    if not agent:
        return None

    def _search(query: str) -> list[dict[str, str]]:
        from google.genai.types import GenerateContentConfig, GoogleSearch, Tool

        prompt = (
            f'Search the web for: "{query}".\n'
            "Return a JSON array of up to 5 objects with keys title, url, snippet. "
            "Use reputable sources and output ONLY JSON."
        )
        config = GenerateContentConfig(
            temperature=0.0,
            tools=[Tool(google_search=GoogleSearch())],
            response_mime_type="text/plain",
        )
        response = agent._client.models.generate_content(
            model=agent._model_for("research_web_search", "gemini-2.5-pro"),
            contents=[prompt],
            config=config,
        )
        data = _parse_json_response(response.text or "[]")
        if isinstance(data, dict):
            data = data.get("results", [])
        if not isinstance(data, list):
            return []
        cleaned: list[dict[str, str]] = []
        for item in data[:5]:
            if not isinstance(item, dict):
                continue
            cleaned.append({
                "title": str(item.get("title", "")),
                "url": str(item.get("url", "")),
                "snippet": str(item.get("snippet", "")),
            })
        return cleaned

    return _search


def _make_research_vlm_fn(agent):
    if not agent:
        return None

    def _vlm(prompt: str, image_paths: list[str]) -> str:
        uploaded = []
        try:
            for image_path in image_paths:
                uploaded.append(agent.client.files.upload(file=image_path))
            response = agent.client.models.generate_content(
                model=agent._model_for("research_reasoning", "gemini-2.5-pro"),
                contents=[prompt, *uploaded],
            )
            return response.text or ""
        finally:
            for item in uploaded:
                try:
                    agent.client.files.delete(name=item.name)
                except Exception:
                    pass

    return _vlm


def _run_pre_execution_research(agent, goal: str, url: str, site_knowledge, run_dir: Path | None):
    if not agent:
        return None
    try:
        from agent_infra import ResearchAgent
        from agent_infra.research_agent import (
            evaluate_phase2_method_gate,
            evaluate_phase3_equation_gate,
        )
        from action_space import UnifiedActionSpace

        output_dir = run_dir or (Path(__file__).parent / "cre" / "research")
        researcher = ResearchAgent(output_dir=output_dir)
        brief = researcher.research(
            task=goal,
            site_url=url,
            search_fn=_make_research_search_fn(agent),
            vlm_fn=_make_research_vlm_fn(agent),
            site_knowledge=site_knowledge,
        )
        phase2_gate = evaluate_phase2_method_gate(getattr(brief, "method_brief", None))
        setattr(agent, "_phase2_gate_result", phase2_gate)
        _exec_log("phase2_gate", None, phase2_gate)
        if not phase2_gate.get("passed", False):
            raise RuntimeError(f"phase2_gate_failed: {phase2_gate.get('fail_reasons', [])}")
        phase3_gate = evaluate_phase3_equation_gate(
            getattr(brief, "equation_solution", None),
            UnifiedActionSpace().list_names(),
        )
        setattr(agent, "_phase3_gate_result", phase3_gate)
        _exec_log("phase3_gate", None, phase3_gate)
        if not phase3_gate.get("passed", False):
            raise RuntimeError(f"phase3_gate_failed: {phase3_gate.get('fail_reasons', [])}")
        _exec_log("research_brief", None, {
            "steps": len(getattr(brief, "execution_plan", []) or []),
            "quality_criteria": len(getattr(brief, "quality_criteria", []) or []),
            "references": len((_method_brief_dict(brief) or {}).get("references", [])),
            "reference_images": len(getattr(brief, "reference_images", []) or []),
        })
        return brief
    except Exception as e:
        logger.warning("Pre-execution research failed: %s", e)
        setattr(agent, "_phase2_gate_result", {"passed": False, "error": str(e)})
        setattr(agent, "_phase3_gate_result", {"passed": False, "error": str(e)})
        _exec_log("research_brief_failed", None, {"error": str(e)})
        return None


_OBSERVATION_ONLY_ACTIONS = {
    "screenshot",
    "a11y_snapshot",
    "visual_assert",
    "assert_visual",
    "wait",
    "sleep",
}

_DRAWING_EXECUTION_ACTIONS = {
    "draw_path",
    "draw_segments",
    "set_stroke_color",
    "select_brush",
    "select_pen",
    "select_tool",
    "clear_canvas",
    "kleki_clear_canvas",
    "kleki_reset_render_state",
    "kleki_select_tool",
    "kleki_set_color",
    "kleki_set_brush_size",
    "kleki_set_opacity",
    "kleki_set_scatter",
    "kleki_set_stabilizer",
}


def _goal_is_drawing(goal: str) -> bool:
    goal_lower = goal.lower()
    return any(token in goal_lower for token in ["draw", "sketch", "paint", "illustrate", "render", "shade"])


def _goal_is_high_fidelity(goal: str) -> bool:
    goal_lower = goal.lower()
    return any(token in goal_lower for token in [
        "exhaustive", "profuse", "detailed", "detail", "finished",
        "facade", "perspective", "shading", "shadow", "highlight",
    ])


def _goal_is_architectural_art(goal: str) -> bool:
    goal_lower = goal.lower()
    return _goal_is_drawing(goal) and any(
        token in goal_lower for token in ("skyscraper", "tower", "high-rise", "building", "facade", "perspective", "architectural")
    )


def _plan_is_viable(plan: list[dict], goal: str) -> bool:
    if not plan:
        return False

    productive_steps = [
        step for step in plan
        if str(step.get("action", "")).strip() not in _OBSERVATION_ONLY_ACTIONS
    ]
    if not productive_steps:
        return False

    if _goal_is_drawing(goal):
        has_drawing_action = any(
            str(step.get("action", "")).strip() in _DRAWING_EXECUTION_ACTIONS
            for step in productive_steps
        )
        if not has_drawing_action:
            return False
        if _goal_is_high_fidelity(goal) and len(productive_steps) < 6:
            return False

    return True


def _generate_plan_vlm(agent, goal: str, action_space: UnifiedActionSpace,
                       perception: dict, capabilities: CapabilityRouter,
                       site_knowledge=None, lessons: list[str] | None = None,
                       subject_brief: str | None = None,
                       research_brief=None,
                       ) -> list[dict] | None:
    """Ask Gemini 2.5 Pro to generate an action plan from the current state.

    Follows SeeAct's two-stage approach: the VLM generates semantic
    action descriptions, then the executor grounds them via the
    unified action space.

    Uses Pydantic response_schema when available for constrained decoding,
    falling back to free-form JSON parsing otherwise.
    """
    som_path = perception.get("som_path")
    if not som_path or not agent:
        return None

    action_schema = action_space.to_planner_context()

    knowledge_block = ""
    if site_knowledge:
        kb_text = site_knowledge.get_planner_context()
        if kb_text:
            knowledge_block = f"\nSite knowledge:\n{kb_text}\n"

    lessons_block = ""
    if lessons:
        lessons_block = "\nLessons from past runs:\n"
        for lesson in lessons:
            lessons_block += f"  - {lesson}\n"

    subject_block = ""
    if subject_brief:
        subject_block = f"\nReference for what to draw (use this to plan accurate shapes and proportions):\n{subject_brief}\n"

    research_block = _build_research_planner_block(research_brief)

    element_map = perception.get("element_map")
    element_block = ""
    if element_map:
        desc = element_map.to_text_description(max_items=30)
        if desc:
            element_block = f"\nDetected interactive elements:\n{desc}\n"

    prompt = (
        f"You are a universal GUI automation planner. Your goal: {goal}\n\n"
        f"Available actions:\n{action_schema}\n"
        f"{knowledge_block}{lessons_block}{subject_block}{research_block}{element_block}\n"
        "Look at the SoM overlay screenshot. Plan a sequence of actions.\n"
        'Return a "steps" array of objects with keys: action, args, description.\n\n'
        "RULES:\n"
        "- Use the EXACT action names from the list above.\n"
        "- For drawing: select tool FIRST, then set color, then draw.\n"
        "- Include verification steps after critical actions.\n"
        "- If repeated parallel lines, hatching, grid lines, or facade subdivisions are needed, emit separate draw_path steps for separate strokes rather than one connected polyline.\n"
        "- Use the research brief to cover base structure, major subdivisions, secondary details, and finishing passes when the task demands them.\n"
        "- Be concise — no unnecessary waits or redundant steps."
    )

    try:
        uploaded = [agent._client.files.upload(file=som_path)]
        for ref_path in getattr(research_brief, "reference_images", [])[:2] if research_brief else []:
            if Path(ref_path).exists():
                uploaded.append(agent._client.files.upload(file=ref_path))

        if _PLAN_SCHEMA_AVAILABLE:
            from google.genai import types
            config = types.GenerateContentConfig(
                temperature=0.0,
                response_mime_type="application/json",
                response_schema=_ActionPlan,
            )
            try:
                response = agent._client.models.generate_content(
                    model="gemini-2.5-pro",
                    contents=[*uploaded, prompt],
                    config=config,
                )
            except ValueError as ve:
                if "additionalProperties" in str(ve):
                    config = types.GenerateContentConfig(
                        temperature=0.0,
                        response_mime_type="application/json",
                    )
                    response = agent._client.models.generate_content(
                        model="gemini-2.5-pro",
                        contents=[*uploaded, prompt],
                        config=config,
                    )
                else:
                    raise
            parsed = _parse_json_response(response.text or "")
            steps = parsed.get("steps", parsed) if isinstance(parsed, dict) else parsed
            if isinstance(steps, list) and len(steps) > 0:
                plan = [dict(s) if not isinstance(s, dict) else s for s in steps]
                logger.info("VLM generated %d-step plan (schema-constrained)", len(plan))
                return plan
        else:
            response = agent._client.models.generate_content(
                model="gemini-2.5-pro",
                contents=[*uploaded, prompt],
                config=agent._gen_config_json,
            )
            plan = _parse_json_response(response.text or "")
            if isinstance(plan, dict) and "steps" in plan:
                plan = plan["steps"]
            if isinstance(plan, list) and len(plan) > 0:
                logger.info("VLM generated %d-step plan (free-form)", len(plan))
                return plan
    except Exception as e:
        logger.warning("VLM plan generation failed: %s", e)
    finally:
        for item in locals().get("uploaded", []):
            try:
                agent._client.files.delete(name=item.name)
            except Exception:
                pass
    return None


def _refine_plan_with_research(agent, goal: str, plan: list[dict], action_space: UnifiedActionSpace,
                               perception: dict, site_knowledge=None, research_brief=None) -> list[dict]:
    if not agent or not plan or not research_brief:
        return plan

    research_block = _build_research_planner_block(research_brief)
    if not research_block:
        return plan

    som_path = perception.get("som_path")
    if not som_path:
        return plan

    action_schema = action_space.to_planner_context()

    knowledge_block = ""
    if site_knowledge:
        kb_text = site_knowledge.get_planner_context()
        if kb_text:
            knowledge_block = f"\nSite knowledge:\n{kb_text}\n"

    element_map = perception.get("element_map")
    element_block = ""
    if element_map:
        desc = element_map.to_text_description(max_items=30)
        if desc:
            element_block = f"\nDetected interactive elements:\n{desc}\n"

    prompt = (
        f"You are auditing and refining a GUI action plan before execution.\n\n"
        f"Goal: {goal}\n\n"
        f"Current plan JSON:\n{json.dumps(plan, indent=2)}\n\n"
        f"Available actions:\n{action_schema}\n"
        f"{knowledge_block}{research_block}{element_block}\n"
        "Return an improved JSON object with a single key \"steps\".\n\n"
        "Refinement rules:\n"
        "- Preserve correct setup steps when they already work.\n"
        "- Add or rewrite steps if the current plan under-covers structure, detail, scale, shading, or validation required by the research brief.\n"
        "- If repeated parallel lines, hatching, grid lines, facade lines, or shadow bands are needed, emit separate draw_path steps for separate strokes instead of one connected polyline.\n"
        "- Keep exact action names from the action list.\n"
        "- Include verification after major phases, not only at the end.\n"
        "- If the current plan already satisfies the research brief, return it unchanged.\n"
        "Output ONLY JSON."
    )

    uploaded = []
    try:
        uploaded.append(agent._client.files.upload(file=som_path))
        for ref_path in getattr(research_brief, "reference_images", [])[:2]:
            if Path(ref_path).exists():
                uploaded.append(agent._client.files.upload(file=ref_path))

        if _PLAN_SCHEMA_AVAILABLE:
            from google.genai import types

            config = types.GenerateContentConfig(
                temperature=0.0,
                response_mime_type="application/json",
                response_schema=_ActionPlan,
            )
            try:
                response = agent._client.models.generate_content(
                    model=agent._model_for("plan_refinement", "gemini-2.5-pro"),
                    contents=[*uploaded, prompt],
                    config=config,
                )
            except ValueError as ve:
                if "additionalProperties" in str(ve):
                    config = types.GenerateContentConfig(
                        temperature=0.0,
                        response_mime_type="application/json",
                    )
                    response = agent._client.models.generate_content(
                        model=agent._model_for("plan_refinement", "gemini-2.5-pro"),
                        contents=[*uploaded, prompt],
                        config=config,
                    )
                else:
                    raise
        else:
            response = agent._client.models.generate_content(
                model=agent._model_for("plan_refinement", "gemini-2.5-pro"),
                contents=[*uploaded, prompt],
                config=agent._gen_config_json,
            )

        parsed = _parse_json_response(response.text or "")
        steps = parsed.get("steps", parsed) if isinstance(parsed, dict) else parsed
        if isinstance(steps, list) and steps:
            refined = [dict(step) if not isinstance(step, dict) else step for step in steps]
            if not _plan_is_viable(refined, goal):
                logger.warning("Research-guided refinement rejected non-viable plan; keeping original")
                return plan
            logger.info("Research-guided refinement updated plan: %d -> %d steps", len(plan), len(refined))
            return refined
    except Exception as e:
        logger.warning("Research-guided plan refinement failed: %s", e)
    finally:
        for item in uploaded:
            try:
                agent._client.files.delete(name=item.name)
            except Exception:
                pass
    return plan


# =========================================================================
# HARDCODED PLAN FALLBACKS (for known tasks when VLM is unavailable)
# =========================================================================

def _fallback_plan_excalidraw_triangles(cx: int, cy: int) -> list[dict]:
    return [
        {"action": "clear_canvas", "args": {}, "description": "Clear canvas"},
        {"action": "key", "args": {"key": "Return"}, "description": "Confirm clear dialog"},
        {"action": "wait", "args": {"seconds": 1.0}, "description": "Wait for clear"},
        {"action": "assert_visual", "args": {"assertion": "Is the Excalidraw canvas empty?"}, "description": "Verify empty"},
        {"action": "wait", "args": {"seconds": 0.5}, "description": "Brief pause"},
        {"action": "refresh_perception", "args": {}, "description": "Re-capture canvas center"},
        {"action": "wait", "args": {"seconds": 0.5}, "description": "Pause before pen"},
        {"action": "key", "args": {"key": "p"}, "description": "Select pen tool"},
        {"action": "key", "args": {"key": "S"}, "description": "Open stroke color picker"},
        {"action": "set_stroke_color", "args": {"color": "black"}, "description": "Set stroke to black"},
        {"action": "wait", "args": {"seconds": 0.5}, "description": "Pause before drawing"},
        {"action": "draw_concentric_triangles", "args": {"sizes": [220, 160, 100, 50], "inter_triangle_delay": 0.6},
         "description": "Draw 4 concentric triangles",
         "visual_assert": "Are there four nested black-outline triangles?",
         "verify": True},
    ]


def _segments_from_positions(xs: list[int], y1: int, y2: int) -> list[list[list[int]]]:
    return [[[x, y1], [x, y2]] for x in xs]


def _horizontal_segments(x1: int, x2: int, ys: list[int]) -> list[list[list[int]]]:
    return [[[x1, y], [x2, y]] for y in ys]


def _fallback_plan_kleki_skyscraper(cx: int, cy: int) -> list[dict]:
    scale = min(cx, cy)
    front_left = cx - int(scale * 0.36)
    front_right = cx + int(scale * 0.20)
    top_y = cy - int(scale * 0.65)
    bottom_y = cy + int(scale * 0.72)
    vp_x = cx + int(scale * 0.46)
    vp_y = cy - int(scale * 0.24)
    rear_x = front_right + int(scale * 0.20)

    def _line_y_for_x(x0: int, y0: int, x1: int, y1: int, target_x: int) -> int:
        if x1 == x0:
            return y0
        t = (target_x - x0) / (x1 - x0)
        return int(round(y0 + t * (y1 - y0)))

    rear_top = [rear_x, _line_y_for_x(front_right, top_y, vp_x, vp_y, rear_x)]
    rear_bottom = [rear_x, _line_y_for_x(front_right, bottom_y, vp_x, vp_y, rear_x)]

    front_cols = [front_left + int((front_right - front_left) * ratio) for ratio in (0.16, 0.32, 0.48, 0.64, 0.80)]
    front_rows = [top_y + int((bottom_y - top_y) * ratio) for ratio in (0.10, 0.20, 0.31, 0.43, 0.56, 0.69, 0.82, 0.93)]
    accent_rows = [top_y + int((bottom_y - top_y) * ratio) for ratio in (0.16, 0.38, 0.60, 0.82)]

    front_face_quad = [[front_left, bottom_y], [front_left, top_y], [front_right, top_y], [front_right, bottom_y]]
    side_face_quad = [[front_right, bottom_y], [front_right, top_y], rear_top, rear_bottom]
    cast_shadow_quad = [
        [front_left + int(scale * 0.08), bottom_y + int(scale * 0.02)],
        [front_right + int(scale * 0.02), bottom_y + int(scale * 0.02)],
        [rear_bottom[0] + int(scale * 0.34), rear_bottom[1] + int(scale * 0.09)],
        [front_left + int(scale * 0.52), bottom_y + int(scale * 0.14)],
    ]

    front_shading = _quad_to_scanline_segments(front_face_quad, spacing=max(16, int(scale * 0.03)))
    side_shading = _quad_to_scanline_segments(side_face_quad, spacing=max(16, int(scale * 0.035)))
    ground_shadow = _quad_to_scanline_segments(cast_shadow_quad, spacing=max(18, int(scale * 0.04)))
    highlight_segments = [
        [[front_left + int(scale * 0.03), top_y + int(scale * 0.04)], [front_left + int(scale * 0.03), bottom_y - int(scale * 0.04)]],
        [[front_left + int(scale * 0.06), top_y + int(scale * 0.08)], [front_left + int(scale * 0.06), bottom_y - int(scale * 0.08)]],
    ]
    side_verticals = [
        [[front_right + int(scale * 0.08), _line_y_for_x(front_right, top_y, vp_x, vp_y, front_right + int(scale * 0.08))],
         [front_right + int(scale * 0.08), _line_y_for_x(front_right, bottom_y, vp_x, vp_y, front_right + int(scale * 0.08))]],
        [[front_right + int(scale * 0.14), _line_y_for_x(front_right, top_y, vp_x, vp_y, front_right + int(scale * 0.14))],
         [front_right + int(scale * 0.14), _line_y_for_x(front_right, bottom_y, vp_x, vp_y, front_right + int(scale * 0.14))]],
    ]
    side_bands = []
    for ratio in (0.16, 0.34, 0.52, 0.70, 0.88):
        y_front = top_y + int((bottom_y - top_y) * ratio)
        y_rear = rear_top[1] + int((rear_bottom[1] - rear_top[1]) * ratio)
        side_bands.append([[front_right, y_front], [rear_x, y_rear]])

    return [
        {"action": "kleki_clear_canvas", "args": {}, "description": "Clear the canvas and dismiss the confirm dialog"},
        _make_kleki_render_reset_step(),
        {"action": "kleki_set_color", "args": {"color": "black"}, "description": "Set the architectural line color to black"},
        {
            "action": "draw_segments",
            "args": {"segments": _closed_vertices_to_segments(front_face_quad), "straight": True},
            "description": "Draw the front face of the skyscraper with verticals vertical and horizontals horizontal",
        },
        {
            "action": "draw_segments",
            "args": {"segments": [[ [front_right, top_y], rear_top ], [ [front_right, bottom_y], rear_bottom ], [ rear_top, rear_bottom ]], "straight": True},
            "description": "Draw the receding side face toward a single vanishing point",
        },
        _make_kleki_visual_checkpoint(
            "Verify the scaffold before facade work",
            "Does the Kleki canvas show a tall building scaffold with a strong front face, vertical main edges, horizontal front edges, and a single coherent depth direction? Reply YES or NO.",
        ),
        {
            "action": "draw_segments",
            "args": {"segments": _segments_from_positions(front_cols, top_y + int(scale * 0.03), bottom_y - int(scale * 0.04)), "straight": True},
            "description": "Lay in vertical facade mullions on the front face",
        },
        {
            "action": "draw_segments",
            "args": {"segments": _horizontal_segments(front_left + int(scale * 0.03), front_right - int(scale * 0.03), front_rows), "straight": True},
            "description": "Lay in floor bands across the front facade",
        },
        {
            "action": "draw_segments",
            "args": {"segments": side_verticals, "straight": True},
            "description": "Add side-face vertical guides that remain architecturally legible",
        },
        {
            "action": "draw_segments",
            "args": {"segments": side_bands, "straight": True},
            "description": "Add receding floor bands on the side face toward the same vanishing point",
        },
        _make_kleki_visual_checkpoint(
            "Verify facade organization before shading",
            "Are windows, mullions, and floor bands clearly visible and organized into a coherent facade rather than random lines? Reply YES or NO.",
        ),
        {"action": "kleki_set_color", "args": {"color": "dark gray"}, "description": "Switch to dark gray for shadow massing"},
        {"action": "kleki_set_brush_size", "args": {"size": "medium"}, "description": "Use a medium brush for tonal massing"},
        {"action": "kleki_set_opacity", "args": {"opacity": "medium"}, "description": "Lower opacity for layered shadow bands"},
        {"action": "kleki_set_scatter", "args": {"scatter": "0"}, "description": "Keep scatter at zero so shading stays controlled"},
        {
            "action": "draw_path",
            "args": {"segments": side_shading},
            "description": "Shade the receding side face with dark controlled tonal bands",
        },
        {
            "action": "draw_path",
            "args": {"segments": ground_shadow},
            "description": "Add a cast shadow on the ground so the composition occupies more of the canvas",
        },
        {"action": "kleki_set_color", "args": {"color": "light gray"}, "description": "Switch to light gray for the sunlit facade tone"},
        {"action": "kleki_set_opacity", "args": {"opacity": "low"}, "description": "Use low opacity for broad front-face light passes"},
        {
            "action": "draw_path",
            "args": {"segments": front_shading},
            "description": "Build the front facade tone with broad grayscale passes",
        },
        {"action": "kleki_set_color", "args": {"color": "white"}, "description": "Switch to white for highlight accents"},
        {
            "action": "draw_path",
            "args": {"segments": highlight_segments},
            "description": "Add highlight strips along the lit front edge",
        },
        _make_kleki_visual_checkpoint(
            "Verify shading and coverage before final accents",
            "Does the Kleki drawing show deliberate grayscale shading, no obvious scatter-noise contamination, and a substantial portion of the canvas occupied by the skyscraper and its shadow? Reply YES or NO.",
        ),
        {"action": "kleki_set_color", "args": {"color": "black"}, "description": "Return to black for final architectural detailing"},
        {"action": "kleki_set_brush_size", "args": {"size": "thin"}, "description": "Use a thin brush for final facade accents"},
        {"action": "kleki_set_opacity", "args": {"opacity": "100%"}, "description": "Restore full opacity for final accents"},
        {
            "action": "draw_segments",
            "args": {"segments": _horizontal_segments(front_left + int(scale * 0.05), front_right - int(scale * 0.05), accent_rows), "straight": True},
            "description": "Add bold facade accents so the tower reads clearly as architecture",
        },
        {
            "action": "draw_segments",
            "args": {"segments": _closed_vertices_to_segments(front_face_quad) + [[[front_right, top_y], rear_top], [[front_right, bottom_y], rear_bottom], [rear_top, rear_bottom]], "straight": True},
            "description": "Redraw the final outline so the skyscraper silhouette remains crisp and architectural",
        },
        _make_kleki_visual_checkpoint(
            "Verify final architectural readability before the final gate",
            "Does the Kleki canvas clearly show a tall recognizable skyscraper with coherent one-point perspective, legible facade structure, layered grayscale shading, and intentional linework? Reply YES or NO.",
        ),
    ]


def _generate_fallback_plan(goal: str, url: str, cx: int, cy: int) -> list[dict]:
    """Generate a plan from known patterns when VLM planning is unavailable."""
    goal_lower = goal.lower()
    url_lower = (url or "").lower()

    if "concentric" in goal_lower and "triangle" in goal_lower:
        return _fallback_plan_excalidraw_triangles(cx, cy)

    # Magma: navigate to app, open canvas, then draw (realistic car / BMW E30)
    if "magma" in url_lower or "magma" in goal_lower:
        return [
            {"action": "go_to_url", "args": {"url": "https://magma.com/app"}, "description": "Open Magma app"},
            {"action": "sleep", "args": {"seconds": 2}, "description": "Wait for app to load"},
            {"action": "click", "args": {"label": "New canvas"}, "description": "Click New canvas"},
            {"action": "sleep", "args": {"seconds": 1}, "description": "Wait for dialog"},
            {"action": "click", "args": {"label": "Landscape drawing"}, "description": "Select Landscape"},
            {"action": "sleep", "args": {"seconds": 2}, "description": "Wait for canvas"},
            {"action": "set_stroke_color", "args": {"color": "black"}, "description": "Set stroke to black"},
            {"action": "draw_path", "args": {"vertices": [[200, 400], [400, 380], [600, 400], [620, 450], [620, 520], [200, 520], [200, 400]]}, "description": "Draw car body outline"},
            {"action": "draw_path", "args": {"vertices": [[280, 520], [340, 520], [340, 580], [280, 580], [280, 520]]}, "description": "Draw front wheel"},
            {"action": "draw_path", "args": {"vertices": [[480, 520], [540, 520], [540, 580], [480, 580], [480, 520]]}, "description": "Draw rear wheel"},
        ]

    if "kleki" in url_lower and any(token in goal_lower for token in ["skyscraper", "tower", "building", "high-rise"]):
        return _fallback_plan_kleki_skyscraper(cx, cy)

    if _goal_is_drawing(goal):
        return [
            {"action": "kleki_clear_canvas", "args": {}, "description": "Clear the canvas before drawing"},
            {"action": "kleki_set_color", "args": {"color": "black"}, "description": "Set a visible line color"},
            {"action": "kleki_set_brush_size", "args": {"size": "thin"}, "description": "Use a controllable drawing brush"},
            {
                "action": "draw_path",
                "args": {"vertices": [[cx - 120, cy + 120], [cx, cy - 120], [cx + 120, cy + 120], [cx - 120, cy + 120]]},
                "description": "Draw a simple visible scaffold instead of an observation-only fallback",
            },
        ]

    return [{"action": "wait", "args": {"seconds": 1.0}, "description": "Pause briefly before failing cleanly"}]


def _site_domain(url: str) -> str:
    return (urlparse(url or "").netloc or "").lower()


def _is_kleki_url(url: str) -> bool:
    return "kleki.com" in _site_domain(url)


def _infer_kleki_color(step: dict) -> str:
    args = step.get("args", {}) or {}
    if args.get("color"):
        return str(args["color"]).strip().lower()
    text = " ".join(
        [
            str(step.get("description", "")),
            str(step.get("action", "")),
            json.dumps(args, sort_keys=True),
        ]
    ).lower()
    for color in (
        "very dark gray",
        "dark gray",
        "medium gray",
        "light gray",
        "near-black",
        "near black",
        "black",
        "white",
        "red",
        "blue",
    ):
        if color in text:
            return color
    return "black"


def _infer_kleki_size(step: dict) -> str:
    args = step.get("args", {}) or {}
    if args.get("size"):
        return str(args["size"]).strip().lower()
    text = " ".join(
        [
            str(step.get("description", "")),
            json.dumps(args, sort_keys=True),
        ]
    ).lower()
    if "very thin" in text:
        return "very thin"
    if any(token in text for token in ("thin", "small", "size 4", "linework")):
        return "thin"
    if any(token in text for token in ("large", "thick", "wide")):
        return "thick"
    if "medium" in text:
        return "medium"
    return "thin"


def _infer_kleki_opacity(step: dict) -> str:
    args = step.get("args", {}) or {}
    if args.get("opacity"):
        return str(args["opacity"]).strip().lower()
    text = " ".join(
        [
            str(step.get("description", "")),
            json.dumps(args, sort_keys=True),
        ]
    ).lower()
    match = re.search(r"(\d{1,3})\s*%", text)
    if match:
        return f"{match.group(1)}%"
    if "low" in text:
        return "low"
    if "medium" in text:
        return "medium"
    if "high" in text or "opaque" in text:
        return "100%"
    return "100%"


def _infer_kleki_scatter(step: dict) -> str:
    args = step.get("args", {}) or {}
    if args.get("scatter") is not None:
        return str(args["scatter"]).strip().lower()
    text = " ".join([str(step.get("description", "")), json.dumps(args, sort_keys=True)]).lower()
    if "scatter 0" in text or "scatter zero" in text or "no scatter" in text:
        return "0"
    if "low scatter" in text:
        return "low"
    if "medium scatter" in text:
        return "medium"
    if "high scatter" in text:
        return "high"
    return "0"


def _pair_vertices_as_segments(vertices: list[list[int]]) -> list[list[list[int]]]:
    segments: list[list[list[int]]] = []
    for i in range(0, len(vertices), 2):
        pair = vertices[i:i + 2]
        if len(pair) == 2:
            segments.append([pair[0], pair[1]])
    return segments


def _closed_vertices_to_segments(vertices: list[list[int]]) -> list[list[list[int]]]:
    if len(vertices) < 2:
        return []
    cleaned = [list(v[:2]) for v in vertices if len(v) >= 2]
    if len(cleaned) >= 2 and cleaned[0] == cleaned[-1]:
        cleaned = cleaned[:-1]
    if len(cleaned) < 2:
        return []
    segments: list[list[list[int]]] = []
    for i, start in enumerate(cleaned):
        end = cleaned[(i + 1) % len(cleaned)]
        segments.append([start, end])
    return segments


def _quad_to_scanline_segments(vertices: list[list[int]], spacing: int = 22) -> list[list[list[int]]]:
    if len(vertices) != 4:
        return []
    p0, p1, p2, p3 = vertices
    left_bottom, left_top = sorted([p0, p1], key=lambda p: p[1], reverse=True)
    right_top, right_bottom = sorted([p2, p3], key=lambda p: p[1])
    top_y = max(left_top[1], right_top[1])
    bottom_y = min(left_bottom[1], right_bottom[1])
    if bottom_y <= top_y:
        return []

    def interp(a: list[int], b: list[int], y: float) -> float:
        ay, by = a[1], b[1]
        if ay == by:
            return float(a[0])
        t = (y - ay) / (by - ay)
        return a[0] + t * (b[0] - a[0])

    segments: list[list[list[int]]] = []
    y = float(bottom_y)
    while y >= top_y:
        x_left = interp(left_bottom, left_top, y)
        x_right = interp(right_bottom, right_top, y)
        if x_right < x_left:
            x_left, x_right = x_right, x_left
        segments.append([[int(round(x_left)), int(round(y))], [int(round(x_right)), int(round(y))]])
        y -= spacing
    return segments


def _normalize_kleki_draw_path_step(step: dict, text: str) -> dict:
    resolved = dict(step)
    args = dict(step.get("args", {}) or {})
    vertices = [list(v) for v in args.get("vertices", []) if len(v) >= 2]
    segments = [segment for segment in args.get("segments", []) if len(segment) >= 2]
    line_family_tokens = (
        "grid",
        "grid lines",
        "vertical grid",
        "horizontal grid",
        "facade",
        "floor lines",
        "floors",
        "shadow",
        "shading",
        "fill",
        "highlight",
        "tone",
        "window lines",
        "parallel lines",
        "zigzag fill pattern",
    )
    structural_tokens = (
        "left vertical edge",
        "right vertical edge",
        "top edge",
        "bottom edge",
        "silhouette",
        "outline",
        "mullion",
        "facade",
        "floor line",
        "roof",
        "roof cap",
        "setback",
        "front face",
        "side face",
        "guide",
        "window lines",
        "architectural",
    )
    tonal_tokens = ("fill", "block in", "shade", "shading", "shadow", "highlight", "base tone", "gradient", "wash", "tone")

    if segments and any(token in text for token in structural_tokens):
        resolved["action"] = "draw_segments"
        resolved["args"] = {**args, "segments": segments, "straight": True}
        return resolved

    if len(vertices) == 2 and any(token in text for token in structural_tokens):
        resolved["action"] = "draw_segments"
        resolved["args"] = {"segments": [[vertices[0], vertices[1]]], "straight": True}
        return resolved

    if bool(args.get("closed")) and len(vertices) >= 3 and any(token in text for token in structural_tokens):
        closed_segments = _closed_vertices_to_segments(vertices)
        if closed_segments:
            resolved["action"] = "draw_segments"
            resolved["args"] = {"segments": closed_segments, "straight": True}
            return resolved

    if (
        len(vertices) >= 5
        and not bool(args.get("closed"))
        and any(token in text for token in line_family_tokens)
    ):
        segments = _pair_vertices_as_segments(vertices)
        if len(segments) >= 2:
            action_name = "draw_segments" if any(token in text for token in structural_tokens) else "draw_path"
            resolved["action"] = action_name
            resolved["args"] = {**args, "segments": segments, **({"straight": True} if action_name == "draw_segments" else {})}
            return resolved

    if (
        len(vertices) >= 4
        and len(vertices) % 2 == 0
        and any(token in text for token in ("facade grid", "horizontal lines", "parallel lines", "window lines", "floor bands", "mullion"))
    ):
        resolved["action"] = "draw_segments"
        resolved["args"] = {**args, "segments": _pair_vertices_as_segments(vertices), "straight": True}
        return resolved

    if (
        len(vertices) == 4
        and any(token in text for token in tonal_tokens)
    ):
        spacing = 18 if "highlight" in text else 24
        segments = _quad_to_scanline_segments(vertices, spacing=spacing)
        if segments:
            resolved["args"] = {**args, "segments": segments}
        return resolved

    return resolved


def _make_kleki_render_reset_step() -> dict:
    return {
        "action": "kleki_reset_render_state",
        "args": {
            "tool": "brush",
            "size": "very thin",
            "opacity": "100%",
            "scatter": "0",
            "stabilizer": "1",
        },
        "description": "Normalize Kleki render state for architectural linework before drawing",
    }


def _make_kleki_visual_checkpoint(description: str, assertion: str) -> dict:
    return {
        "action": "visual_assert",
        "args": {"assertion": assertion},
        "description": description,
        "visual_assert": assertion,
    }


def _inject_kleki_art_checkpoints(plan: list[dict], goal: str) -> list[dict]:
    if not _goal_is_architectural_art(goal):
        return plan

    injected: list[dict] = []
    scaffold_added = False
    facade_added = False
    shading_added = False
    final_added = False
    for step in plan:
        injected.append(step)
        action = str(step.get("action", ""))
        desc = str(step.get("description", "")).lower()
        if not scaffold_added and action == "draw_segments" and any(token in desc for token in ("front face", "roof cap", "side face", "silhouette")):
            injected.append(_make_kleki_visual_checkpoint(
                "Verify the skyscraper scaffold reads as a building before detailed work",
                "Does the Kleki canvas now show a recognizable skyscraper scaffold with a strong front face, vertical edges, and coherent one-point depth direction? Reply YES or NO.",
            ))
            scaffold_added = True
            continue
        if not facade_added and action == "draw_segments" and any(token in desc for token in ("facade", "floor bands", "mullion", "window")):
            injected.append(_make_kleki_visual_checkpoint(
                "Verify facade structure before shading",
                "Are facade subdivisions such as mullions, floor bands, or window lines clearly visible and organized rather than random or tangled? Reply YES or NO.",
            ))
            facade_added = True
            continue
        if not shading_added and action in {"draw_path", "draw_segments"} and any(token in desc for token in ("shade", "shadow", "highlight", "tone", "wash")):
            injected.append(_make_kleki_visual_checkpoint(
                "Verify shading pass quality and render-state control",
                "Does the Kleki drawing show deliberate grayscale shading with no obvious scatter-noise contamination and a substantial amount of the canvas occupied by the structure? Reply YES or NO.",
            ))
            shading_added = True
            continue
        if not final_added and action == "draw_segments" and "final outline" in desc:
            injected.append(_make_kleki_visual_checkpoint(
                "Verify final architectural readability before the final gate",
                "Does the Kleki canvas clearly show a recognizable tall skyscraper with coherent one-point perspective, legible facade structure, and intentional linework? Reply YES or NO.",
            ))
            final_added = True
    return injected


def _normalize_plan_for_site(plan: list[dict], url: str, goal: str) -> list[dict]:
    """Rewrite brittle generic steps into site-native actions."""
    if not _is_kleki_url(url):
        return plan

    normalized: list[dict] = []
    needs_render_reset = _goal_is_architectural_art(goal)
    render_reset_inserted = False
    for step in plan:
        resolved = dict(step)
        args = dict(step.get("args", {}) or {})
        action = str(step.get("action", ""))
        description = str(step.get("description", ""))
        text = " ".join([action, description, json.dumps(args, sort_keys=True)]).lower()
        label = str(args.get("label", "")).lower()

        if action == "clear_canvas":
            resolved["action"] = "kleki_clear_canvas"
            resolved.setdefault(
                "visual_assert",
                "Is the main Kleki canvas blank with no user-drawn marks visible? "
                "Ignore the right-side tool panel. Reply YES or NO.",
            )
            normalized.append(resolved)
            if needs_render_reset and not render_reset_inserted:
                normalized.append(_make_kleki_render_reset_step())
                render_reset_inserted = True
            continue

        if action == "kleki_clear_canvas":
            normalized.append(resolved)
            if needs_render_reset and not render_reset_inserted:
                normalized.append(_make_kleki_render_reset_step())
                render_reset_inserted = True
            continue

        if action == "key" and str(args.get("key", "")).lower() in {"b", "e", "u"}:
            tool = {"b": "brush", "e": "eraser", "u": "shape"}[str(args.get("key", "")).lower()]
            resolved["action"] = "kleki_select_tool"
            resolved["args"] = {"tool": tool}
            resolved["description"] = f"Select Kleki {tool} tool"
            normalized.append(resolved)
            continue

        if (
            action in {"click", "set_stroke_color"}
            and (
                "hex_color_input" in label
                or "color picker" in text
                or "select black color" in text
                or "select white color" in text
                or "dark gray" in text
                or "light gray" in text
                or "medium gray" in text
                or "set color" in text
            )
        ):
            color = _infer_kleki_color(step)
            resolved["action"] = "kleki_set_color"
            resolved["args"] = {"color": color}
            resolved["description"] = f"Set Kleki drawing color to {color}"
            resolved.setdefault(
                "visual_assert",
                f"Is the active Kleki drawing color set to {color} or a close visual equivalent "
                "in the active color swatch? Reply YES or NO.",
            )
            normalized.append(resolved)
            continue

        if action == "click" and ("scatter" in text):
            scatter = _infer_kleki_scatter(step)
            resolved["action"] = "kleki_set_scatter"
            resolved["args"] = {"scatter": scatter}
            resolved["description"] = f"Set Kleki scatter to {scatter}"
            normalized.append(resolved)
            continue

        if action == "click" and ("stabilizer" in text):
            resolved["action"] = "kleki_set_stabilizer"
            resolved["args"] = {"stabilizer": "1" if "low" in text or "1" in text else "4"}
            resolved["description"] = f"Set Kleki stabilizer to {resolved['args']['stabilizer']}"
            normalized.append(resolved)
            continue

        if action == "click" and ("size" in text or "brush size" in text or "line width" in text):
            size = _infer_kleki_size(step)
            resolved["action"] = "kleki_set_brush_size"
            resolved["args"] = {"size": size}
            resolved["description"] = f"Set Kleki brush size to {size}"
            normalized.append(resolved)
            continue

        if action == "click" and ("opacity" in text or "transparent" in text):
            opacity = _infer_kleki_opacity(step)
            resolved["action"] = "kleki_set_opacity"
            resolved["args"] = {"opacity": opacity}
            resolved["description"] = f"Set Kleki opacity to {opacity}"
            normalized.append(resolved)
            continue

        if action == "draw_path":
            normalized.append(_normalize_kleki_draw_path_step(resolved, text))
            continue

        normalized.append(resolved)

    if needs_render_reset and not render_reset_inserted:
        normalized.insert(0, _make_kleki_render_reset_step())

    normalized = _inject_kleki_art_checkpoints(normalized, goal)

    logger.info(
        "Applied Kleki plan normalization: %d -> %d steps for goal '%s'",
        len(plan), len(normalized), goal[:80],
    )
    return normalized


# =========================================================================
# EXECUTION CONTEXT (universal _Ctx)
# =========================================================================

class ExecutionContext:
    """Shared state for the execution loop — replaces per-script _Ctx.

    Holds all runtime state: agent, capabilities, perception, trace writer.
    Passed to action handlers and recovery logic via the same interface
    the existing modules expect.
    """
    __slots__ = (
        "use_enterprise", "agent", "vision_engine", "client", "vlm",
        "ui_analysis", "cre_dir", "current_state_path", "journal",
        "trace_writer", "coord_cache", "trust_tracker",
        "_last_resolved_coords", "summarizer", "element_map", "primitives",
        "rules", "capabilities", "action_space", "url", "goal",
        "site_knowledge", "research_brief", "_palette_tool_used", "action_allowlist", "screen_bounds",
        "visual_monitor", "visual_monitor_checkpoints", "execution_checkpoints",
    )

    def __init__(self, *, use_enterprise: bool, agent, vision_engine,
                 ui_analysis: dict, cre_dir: Path, current_state_path: str,
                 trace_writer=None, capabilities: CapabilityRouter | None = None,
                 action_space: UnifiedActionSpace | None = None,
                 url: str = "", goal: str = "") -> None:
        self.use_enterprise = use_enterprise
        self.agent = agent
        self.vision_engine = vision_engine
        self.client = None
        self.vlm = None
        self.ui_analysis = ui_analysis
        self.cre_dir = cre_dir
        self.current_state_path = current_state_path
        self.trace_writer = trace_writer
        self.capabilities = capabilities
        self.action_space = action_space
        self.url = url
        self.goal = goal

        self.trust_tracker = (
            capabilities.get(CapabilityKind.TRUST_TRACKER) if capabilities else None
        )
        self.coord_cache = (
            capabilities.get(CapabilityKind.COORD_CACHE) if capabilities else {}
        ) or {}
        self.summarizer = None
        self.element_map = ui_analysis.get("element_map")
        self.primitives = None
        self.rules: list[str] = []
        self._last_resolved_coords = None
        self.site_knowledge = None
        self.research_brief = None
        self._palette_tool_used = None
        self.action_allowlist = None
        self.screen_bounds = None
        self.visual_monitor = None
        self.visual_monitor_checkpoints: list[dict[str, Any]] = []
        self.execution_checkpoints: list[dict[str, Any]] = []

        if capabilities and capabilities.is_active(CapabilityKind.EPISODIC_MEMORY):
            self.rules = capabilities.get(CapabilityKind.EPISODIC_MEMORY) or []

        if (capabilities and capabilities.is_active(CapabilityKind.WEB_PRIMITIVES)
                and agent and self.element_map):
            try:
                from web_primitives import WebPrimitives
                self.primitives = WebPrimitives(agent=agent, element_map=self.element_map)
            except Exception:
                pass

        try:
            from agent_infra import Summarizer
            self.summarizer = Summarizer(token_budget=500)
        except Exception:
            pass

        from collections import deque

        class _Journal:
            def __init__(self, max_entries=20):
                self._entries: list[dict] = []
                self._max = max_entries
            def record(self, step, action, result, screenshot_path=None):
                self._entries.append({"step": step, "action": action, "result": result})
                if len(self._entries) > self._max:
                    self._entries = self._entries[-self._max:]
            def recent(self, n=5):
                return self._entries[-n:]
            def format_for_prompt(self, n=5):
                entries = self.recent(n)
                if not entries:
                    return "No prior actions."
                return "\n".join(f"  Step {e['step']}: {e['action']} -> {e['result']}" for e in entries)

        self.journal = _Journal()

    @property
    def canvas_center(self) -> dict:
        return self.ui_analysis.get("canvas_center", {})

    @property
    def cx(self) -> int:
        return self.canvas_center.get("x", 720)

    @property
    def cy(self) -> int:
        return self.canvas_center.get("y", 450)


@dataclass
class ExecutionCheckpoint:
    checkpoint_id: str
    trigger_step_index: int
    description: str
    reference_paths: list[str] = field(default_factory=list)
    comparison_mode: str = "reference-free"
    threshold: float = 0.7
    refinement_required_on_fail: bool = True
    assertion: str = ""
    method_step_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CheckpointResult:
    checkpoint_id: str
    current_image: str
    comparison_result: dict[str, Any]
    passed: bool
    deficiencies: list[str] = field(default_factory=list)
    next_action: str = ""
    trigger_step_index: int = 0
    method_step_id: str = ""
    comparison_mode: str = "reference-free"
    iteration: int = 1

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# =========================================================================
# EXECUTION LOOP
# =========================================================================


def _iter_checkpoint_reference_paths(ctx: ExecutionContext) -> list[str]:
    return [
        path
        for path in getattr(getattr(ctx, "research_brief", None), "reference_images", [])[:2]
        if Path(path).exists()
    ]


def _coerce_equation_plan(ctx: ExecutionContext) -> list[dict[str, Any]]:
    brief = getattr(ctx, "research_brief", None)
    if brief is None:
        return []

    equation_solution = getattr(brief, "equation_solution", None)
    if hasattr(equation_solution, "execution_plan"):
        execution_plan = getattr(equation_solution, "execution_plan", None)
        if isinstance(execution_plan, list):
            return execution_plan
    if isinstance(equation_solution, dict):
        plan = equation_solution.get("execution_plan")
        if isinstance(plan, list):
            return plan

    plan = getattr(brief, "execution_plan", None)
    if isinstance(plan, list):
        return plan
    return []


def _build_execution_checkpoints(ctx: ExecutionContext, plan: list[dict[str, Any]]) -> list[ExecutionCheckpoint]:
    references = _iter_checkpoint_reference_paths(ctx)
    checkpoints: list[ExecutionCheckpoint] = []
    seen_indices: set[int] = set()

    for entry in _coerce_equation_plan(ctx):
        if not isinstance(entry, dict):
            continue
        try:
            step_index = int(entry.get("step_index"))
        except Exception:
            continue
        if step_index < 1 or step_index > len(plan):
            continue
        description = str(
            entry.get("verification_hint")
            or entry.get("description")
            or f"Checkpoint after step {step_index}"
        ).strip()
        if not description:
            description = f"Checkpoint after step {step_index}"
        comparison_mode = "hybrid" if references else "reference-free"
        checkpoints.append(
            ExecutionCheckpoint(
                checkpoint_id=f"step_{step_index:03d}",
                trigger_step_index=step_index,
                description=description,
                reference_paths=references,
                comparison_mode=comparison_mode,
                threshold=0.7,
                refinement_required_on_fail=bool(entry.get("is_major", True)),
                assertion=description,
                method_step_id=str(entry.get("step_id", "")),
            )
        )
        seen_indices.add(step_index)

    for index, action_item in enumerate(plan, 1):
        action = str(action_item.get("action", "")).strip()
        if index in seen_indices:
            continue
        if action in {"visual_assert", "assert_visual"}:
            assertion = str(
                action_item.get("visual_assert")
                or action_item.get("args", {}).get("assertion")
                or action_item.get("description", "")
            ).strip()
            if not assertion:
                continue
            checkpoints.append(
                ExecutionCheckpoint(
                    checkpoint_id=f"step_{index:03d}",
                    trigger_step_index=index,
                    description=assertion,
                    reference_paths=[],
                    comparison_mode="reference-free",
                    threshold=1.0,
                    refinement_required_on_fail=True,
                    assertion=assertion,
                )
            )

    checkpoints.sort(key=lambda item: (item.trigger_step_index, item.checkpoint_id))
    return checkpoints


def _capture_execution_checkpoint(ctx: ExecutionContext, step_index: int, checkpoint: ExecutionCheckpoint, iteration: int) -> str:
    output_dir = (
        Path(ctx.trace_writer.run_dir) / "execution_checkpoints"
        if getattr(ctx, "trace_writer", None) is not None
        else ctx.cre_dir / "execution_checkpoints"
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{checkpoint.checkpoint_id}_iter{iteration:02d}.png"
    capture_front_window(path)
    return str(path)


def _record_monitor_checkpoint(ctx: ExecutionContext, checkpoint: ExecutionCheckpoint, screenshot_path: str) -> None:
    monitor = getattr(ctx, "visual_monitor", None)
    if monitor is None:
        return
    try:
        snap = monitor.capture_now()
        entry = {
            "checkpoint_id": checkpoint.checkpoint_id,
            "trigger_step_index": checkpoint.trigger_step_index,
            "description": checkpoint.description,
            "comparison_mode": checkpoint.comparison_mode,
            "artifacts_screenshot": screenshot_path,
            "monitor_snapshot_path": snap.path if snap else None,
        }
        ctx.visual_monitor_checkpoints.append(entry)
    except Exception as e:
        logger.debug("VisualMonitor checkpoint capture failed: %s", e)


def _run_reference_free_checkpoint(
    ctx: ExecutionContext,
    checkpoint: ExecutionCheckpoint,
    screenshot_path: str,
    *,
    iteration: int,
) -> CheckpointResult:
    assertion = checkpoint.assertion or checkpoint.description
    try:
        if ctx.agent is None:
            raise RuntimeError("agent unavailable")
        ctx.agent.assert_visual_state(screenshot_path, assertion)
        return CheckpointResult(
            checkpoint_id=checkpoint.checkpoint_id,
            current_image=screenshot_path,
            comparison_result={"assertion": assertion, "mode": "reference-free", "result": "passed"},
            passed=True,
            deficiencies=[],
            next_action="continue",
            trigger_step_index=checkpoint.trigger_step_index,
            method_step_id=checkpoint.method_step_id,
            comparison_mode=checkpoint.comparison_mode,
            iteration=iteration,
        )
    except Exception as e:
        return CheckpointResult(
            checkpoint_id=checkpoint.checkpoint_id,
            current_image=screenshot_path,
            comparison_result={"assertion": assertion, "mode": "reference-free", "result": "failed", "error": str(e)},
            passed=False,
            deficiencies=[str(e)],
            next_action="refine" if checkpoint.refinement_required_on_fail else "escalate",
            trigger_step_index=checkpoint.trigger_step_index,
            method_step_id=checkpoint.method_step_id,
            comparison_mode=checkpoint.comparison_mode,
            iteration=iteration,
        )


def _run_hybrid_checkpoint(
    ctx: ExecutionContext,
    checkpoint: ExecutionCheckpoint,
    screenshot_path: str,
    *,
    iteration: int,
) -> CheckpointResult:
    from agent_infra import VerificationGate

    output_dir = (
        Path(ctx.trace_writer.run_dir) / "execution_checkpoints"
        if getattr(ctx, "trace_writer", None) is not None
        else ctx.cre_dir / "execution_checkpoints"
    )
    gate = VerificationGate(
        task_description=ctx.goal,
        output_dir=output_dir,
        vlm_judge_fn=_make_final_verification_judge(ctx.agent) if (ctx.use_enterprise and ctx.agent) else None,
        extra_criteria=[checkpoint.description],
    )
    verification = gate.verify(
        iteration=iteration,
        screenshot_path=screenshot_path,
        reference_paths=checkpoint.reference_paths,
    )
    return CheckpointResult(
        checkpoint_id=checkpoint.checkpoint_id,
        current_image=screenshot_path,
        comparison_result={
            "mode": "hybrid",
            "score": verification.score,
            "verdict": verification.verdict,
            "reference_paths": checkpoint.reference_paths,
        },
        passed=verification.passed,
        deficiencies=list(verification.deficiencies),
        next_action="continue" if verification.passed else ("refine" if checkpoint.refinement_required_on_fail else "escalate"),
        trigger_step_index=checkpoint.trigger_step_index,
        method_step_id=checkpoint.method_step_id,
        comparison_mode=checkpoint.comparison_mode,
        iteration=iteration,
    )


def _run_execution_checkpoint_once(
    ctx: ExecutionContext,
    checkpoint: ExecutionCheckpoint,
    *,
    iteration: int,
) -> CheckpointResult:
    screenshot_path = _capture_execution_checkpoint(ctx, checkpoint.trigger_step_index, checkpoint, iteration)
    _record_monitor_checkpoint(ctx, checkpoint, screenshot_path)
    if checkpoint.comparison_mode == "hybrid" and checkpoint.reference_paths:
        return _run_hybrid_checkpoint(ctx, checkpoint, screenshot_path, iteration=iteration)
    return _run_reference_free_checkpoint(ctx, checkpoint, screenshot_path, iteration=iteration)


def _run_execution_checkpoint(ctx: ExecutionContext, checkpoint: ExecutionCheckpoint) -> CheckpointResult:
    result = _run_execution_checkpoint_once(ctx, checkpoint, iteration=1)
    if result.passed or not checkpoint.refinement_required_on_fail:
        return result

    if ctx.agent:
        try:
            ctx.agent.enforce_app_focus("Safari")
            time.sleep(0.2)
        except Exception:
            pass
    refined = _run_execution_checkpoint_once(ctx, checkpoint, iteration=2)
    if refined.passed:
        refined.next_action = "refined_and_continue"
        return refined
    refined.next_action = "escalate"
    return refined


def _persist_execution_checkpoints(ctx: ExecutionContext) -> None:
    if getattr(ctx, "trace_writer", None) is None:
        return
    run_dir = Path(ctx.trace_writer.run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    path = run_dir / "execution_checkpoints.json"
    path.write_text(
        json.dumps(getattr(ctx, "execution_checkpoints", []), indent=2),
        encoding="utf-8",
    )

def _execute_plan(ctx: ExecutionContext, plan: list[dict],
                  action_space: UnifiedActionSpace) -> list[dict]:
    """Execute an action plan with recovery, verification, and tracing.

    Reuses the existing agent_infra.recovery._execute_action_with_recovery
    for backward compatibility with all demonstrated modules.
    """
    from agent_infra.recovery import _execute_action_with_recovery

    _exec_log("phase", "EXECUTION", {"steps": len(plan)})
    logger.info("Executing %d-step plan", len(plan))

    if ctx.use_enterprise and ctx.agent and ctx.ui_analysis.get("canvas_center"):
        try:
            ctx.agent.execute_move_mouse(ctx.cx, ctx.cy)
            time.sleep(0.2)
        except Exception:
            pass

    evidence: list[dict] = []
    evidence_dir = ctx.cre_dir / "evidence"
    evidence_dir.mkdir(exist_ok=True)
    scheduled_checkpoints = _build_execution_checkpoints(ctx, plan)
    checkpoints_by_step: dict[int, list[ExecutionCheckpoint]] = {}
    for checkpoint in scheduled_checkpoints:
        checkpoints_by_step.setdefault(checkpoint.trigger_step_index, []).append(checkpoint)

    for i, action_item in enumerate(plan, 1):
        resolved = action_space.resolve_action(action_item)
        action_type = resolved.get("action", "")
        description = resolved.get("description", action_type)
        logger.info("Step %d/%d: %s", i, len(plan), description)
        _exec_log("action_start", None, {"index": i, "type": action_type})

        _execute_action_with_recovery(ctx, resolved, i)

        for checkpoint in checkpoints_by_step.get(i, []):
            checkpoint_result = _run_execution_checkpoint(ctx, checkpoint)
            ctx.execution_checkpoints.append(checkpoint_result.to_dict())
            _exec_log(
                "execution_checkpoint",
                checkpoint.checkpoint_id,
                {
                    "step_index": i,
                    "passed": checkpoint_result.passed,
                    "next_action": checkpoint_result.next_action,
                    "comparison_mode": checkpoint.comparison_mode,
                },
            )
            if not checkpoint_result.passed:
                raise RuntimeError(
                    f"Execution checkpoint failed at step {i} ({checkpoint.checkpoint_id}): "
                    + "; ".join(checkpoint_result.deficiencies or [checkpoint.description])
                )

        if resolved.get("verify") and ctx.use_enterprise and ctx.agent:
            _capture_step_evidence(ctx, evidence_dir, evidence, i, description)

    return evidence


def _capture_step_evidence(ctx, evidence_dir, evidence, step, description):
    try:
        path = evidence_dir / f"step_{step:02d}.png"
        capture_front_window(path)
        evidence.append({
            "step": step, "description": description,
            "status": "PASS", "filename": path.name,
        })
    except Exception as e:
        logger.warning("Evidence capture failed at step %d: %s", step, e)


# =========================================================================
# FINALIZATION
# =========================================================================

def _finalize(trace_writer, outcome: str, plan: list, evidence: list,
              agent=None, capabilities: CapabilityRouter | None = None,
              final_verification=None,
              visual_monitor_artifact: dict[str, Any] | None = None) -> None:
    """Write trace, pHash audit, evidence report, and print summary."""

    phash_log = _get_phash_log()
    if phash_log and trace_writer:
        step = trace_writer.begin_step(999)
        step.thought = "pHash audit — all cache comparisons"
        step.action = {"type": "phash_audit", "parameters": {"target": "coord_cache"}}
        step.action_result = {"success": True}
        step.post_state = {
            "total_comparisons": len(phash_log),
            "valid_count": sum(1 for e in phash_log if e["valid"]),
            "invalid_count": sum(1 for e in phash_log if not e["valid"]),
            "comparisons": phash_log,
        }
        trace_writer.end_step(step)

    if trace_writer and final_verification is not None:
        verify_step = trace_writer.begin_step(997)
        verify_step.thought = "Mandatory final verification gate"
        verify_step.action = {"type": "final_verification_gate", "parameters": {}}
        verify_step.action_result = {"success": bool(final_verification.passed)}
        verify_step.post_state = final_verification.to_dict()
        trace_writer.end_step(verify_step)

    if trace_writer and visual_monitor_artifact is not None:
        monitor_step = trace_writer.begin_step(996)
        monitor_step.thought = "Visual monitor timeline summary"
        monitor_step.action = {"type": "visual_monitor_summary", "parameters": {}}
        monitor_step.action_result = {"success": True}
        monitor_step.post_state = visual_monitor_artifact
        trace_writer.end_step(monitor_step)

    # --- Intervention 3: Metacognitive Gate (Explanation Coverage Audit) ---
    # Inspired by the Explanation Gate / Teach-Back protocol (arXiv:2511.04144),
    # this audits the executed plan for "explanation coverage." Every step that
    # modifies state should have a non-empty thought/description explaining WHY.
    # Steps without explanation are flagged — preventing silent epistemic debt
    # accumulation (failingfast.io; arXiv:2601.07786 GIST).
    #
    # Research basis:
    # - Teach-Back protocol (OpenReview:0d3Nloe9pB): Forces explanation before
    #   action integration; reduces failure rate from 77% to 39%.
    # - GIST (arXiv:2601.07786): Developers explicitly acknowledge uncertainty
    #   about AI-generated code — automated flagging catches this.
    # - MemSkill (2026): Designer module reviews traces to identify hard cases
    #   where skills yielded incorrect memory states.
    if trace_writer and plan:
        explained = 0
        unexplained_steps = []
        for i, step_item in enumerate(plan, 1):
            has_thought = bool(step_item.get("thought", "").strip())
            has_desc = bool(step_item.get("description", "").strip())
            if has_thought or has_desc:
                explained += 1
            else:
                unexplained_steps.append(i)

        coverage = explained / len(plan) if plan else 0
        gate_step = trace_writer.begin_step(998)
        gate_step.thought = "Metacognitive Gate — explanation coverage audit"
        gate_step.action = {"type": "metacognitive_audit", "parameters": {}}
        gate_step.action_result = {"success": coverage >= 0.8}
        gate_step.post_state = {
            "total_steps": len(plan),
            "explained_steps": explained,
            "coverage_pct": round(coverage * 100, 1),
            "unexplained_step_indices": unexplained_steps,
            "gate_passed": coverage >= 0.8,
        }
        if unexplained_steps:
            logger.warning(
                "Metacognitive Gate: %d/%d steps lack explanation (indices: %s). "
                "Coverage: %.0f%%. Epistemic debt risk.",
                len(unexplained_steps), len(plan), unexplained_steps, coverage * 100,
            )
        else:
            logger.info("Metacognitive Gate: 100%% explanation coverage (%d steps)", len(plan))
        trace_writer.end_step(gate_step)

    if trace_writer:
        manifest = trace_writer.finalize(outcome=outcome)
        logger.info("Trace: %s | Outcome: %s | Steps: %s",
                    trace_writer.run_id, outcome, manifest.get("num_steps"))
        benchmark = _run_benchmark_evaluation(trace_writer, plan)
        if benchmark:
            logger.info(
                "Benchmark: claims=%.2f discovery=%.2f recovery=%.2f optimality=%.2f",
                benchmark.get("claims_score", 0.0),
                benchmark.get("discovery_precision", 0.0),
                benchmark.get("recovery_rate", 0.0),
                benchmark.get("plan_optimality", 0.0),
            )

    if capabilities:
        logger.info("Capabilities: %s", json.dumps(capabilities.summary(), indent=2))

    if agent and hasattr(agent, "_router") and agent._router:
        stats = agent._router.stats
        logger.info("Routing stats: %s", stats.to_dict())
        if hasattr(agent._router, "adaptations") and agent._router.adaptations:
            logger.info("Adaptations: %s", agent._router.adaptations)


# =========================================================================
# COORD CACHE LOADING (universal, from skill library)
# =========================================================================

def _load_coord_cache(cre_dir: Path, task_id: str) -> dict:
    try:
        from agent_infra import SkillLibrary
        lib = SkillLibrary(library_dir=str(cre_dir))
        skill = lib.retrieve_exact(task_id)
        if skill and skill.maturity.tier == "master" and skill.action_plan:
            if skill.is_stale():
                return {}
            cache = {}
            for entry in skill.action_plan:
                rc = entry.get("resolved_coords")
                if rc and rc.get("action"):
                    key = (rc["action"], rc.get("color", ""))
                    cache[key] = {
                        "x": rc["x"], "y": rc["y"],
                        "box_id": rc.get("box_id", -1),
                        "region_hash": rc.get("region_hash"),
                    }
            return cache
    except Exception:
        pass
    return {}


def _make_final_verification_judge(agent):
    def _judge(prompt: str, images: list[str]) -> str:
        uploaded = []
        try:
            for image_path in images:
                uploaded.append(agent.client.files.upload(file=image_path))
            model = agent._model_for("final_task_verification", "gemini-2.5-pro")
            response = agent.client.models.generate_content(
                model=model,
                contents=[prompt, *uploaded],
            )
            return response.text or "[]"
        finally:
            for item in uploaded:
                try:
                    agent.client.files.delete(name=item.name)
                except Exception:
                    pass
    return _judge


def _run_final_verification(ctx: ExecutionContext):
    from agent_infra import VerificationGate

    output_dir = (
        Path(ctx.trace_writer.run_dir) / "verification"
        if getattr(ctx, "trace_writer", None) is not None
        else ctx.cre_dir / "verification"
    )
    extra_criteria = _normalize_research_quality_criteria(
        ctx.goal,
        getattr(getattr(ctx, "research_brief", None), "quality_criteria", []),
    )
    gate = VerificationGate(
        task_description=ctx.goal,
        output_dir=output_dir,
        vlm_judge_fn=_make_final_verification_judge(ctx.agent) if (ctx.use_enterprise and ctx.agent) else None,
        extra_criteria=extra_criteria,
    )
    screenshot_path = str(output_dir / "verify_01.png")
    capture_front_window(screenshot_path)
    reference_paths = [
        path for path in getattr(getattr(ctx, "research_brief", None), "reference_images", [])[:2]
        if Path(path).exists()
    ]
    return gate.verify(iteration=1, screenshot_path=screenshot_path, reference_paths=reference_paths)


def _start_visual_monitor(trace_writer) -> Any | None:
    """Start the background VisualMonitor for the current run, if enabled."""
    if trace_writer is None:
        return None
    if os.environ.get("DISABLE_VISUAL_MONITOR"):
        return None

    try:
        from agent_infra import VisualMonitor

        interval = float(os.environ.get("CONCENTRIC_VISUAL_MONITOR_INTERVAL_S", "5"))
        buffer_size = int(os.environ.get("CONCENTRIC_VISUAL_MONITOR_BUFFER_SIZE", "40"))
        monitor_dir = Path(trace_writer.run_dir) / "visual_monitor"
        monitor = VisualMonitor(
            interval_seconds=interval,
            buffer_size=buffer_size,
            output_dir=monitor_dir,
            capture_frontmost_window=True,
        )
        monitor.start()
        _exec_log("visual_monitor_started", None, {
            "interval_seconds": interval,
            "buffer_size": buffer_size,
            "output_dir": str(monitor_dir),
        })
        return monitor
    except Exception as e:
        logger.warning("VisualMonitor start failed: %s", e)
        _exec_log("visual_monitor_start_failed", None, {"error": str(e)})
        return None


def _stop_visual_monitor(monitor, trace_writer=None, checkpoints: list[dict[str, Any]] | None = None) -> dict[str, Any] | None:
    """Stop the VisualMonitor and persist timeline metadata into the run dir."""
    if monitor is None:
        return None

    run_dir = Path(trace_writer.run_dir) if trace_writer is not None else None
    try:
        monitor.stop()
        timeline = [snap.to_dict() for snap in monitor.timeline(last_n=max(monitor.snapshot_count, 1))]
        status = monitor.get_status()
        artifact = {
            "status": status,
            "timeline": timeline,
            "checkpoints": list(checkpoints or []),
        }
        if run_dir is not None:
            monitor_dir = run_dir / "visual_monitor"
            monitor_dir.mkdir(parents=True, exist_ok=True)
            (monitor_dir / "timeline.json").write_text(
                json.dumps(timeline, indent=2),
                encoding="utf-8",
            )
            (monitor_dir / "status.json").write_text(
                json.dumps(status, indent=2),
                encoding="utf-8",
            )
            (monitor_dir / "checkpoints.json").write_text(
                json.dumps(list(checkpoints or []), indent=2),
                encoding="utf-8",
            )
        _exec_log("visual_monitor_stopped", None, {
            "captures": status.get("total_captures", 0),
            "latest_path": status.get("latest_path"),
            "checkpoints": len(checkpoints or []),
        })
        return artifact
    except Exception as e:
        logger.warning("VisualMonitor stop failed: %s", e)
        _exec_log("visual_monitor_stop_failed", None, {"error": str(e)})
        return {
            "status": {"running": False, "error": str(e)},
            "timeline": [],
        }


def _build_default_benchmark_evaluator(
    task_id: str,
    planned_steps: int,
    *,
    task_description: str = "",
    site_url: str = "",
):
    """Create a generic BenchmarkEvaluator config for any completed run."""
    from agent_infra import BenchmarkEvaluator, TaskClaim

    evaluator = BenchmarkEvaluator()
    task_lower = " ".join([task_id, task_description, site_url]).lower()

    evaluator.register_claims(task_id, [
        TaskClaim("Run outcome is success", "check_success", weight=1.0),
        TaskClaim("Final verification gate passed", "check_final_verification_passed", weight=1.5),
        TaskClaim("Trace contains productive execution", "check_has_productive_execution", weight=1.0),
        TaskClaim("No grounding errors surfaced", "check_no_grounding_errors", weight=0.75),
    ])

    ideal_steps = max(1, planned_steps) + 4
    evaluator.register_optimal_steps(task_id, ideal_steps)

    def _check_final_verification_passed(manifest: dict[str, Any], steps: list[dict[str, Any]]) -> bool:
        for step in steps:
            if step.get("action", {}).get("type") == "final_verification_gate":
                return bool(step.get("action_result", {}).get("success", False))
        return manifest.get("outcome") == "success"

    def _check_has_productive_execution(_manifest: dict[str, Any], steps: list[dict[str, Any]]) -> bool:
        meta_actions = {
            "a11y_passive_snapshot",
            "final_verification_gate",
            "metacognitive_audit",
            "phash_audit",
            "visual_monitor_summary",
        }
        return any(
            step.get("action", {}).get("type") not in meta_actions
            for step in steps
        )

    def _final_verification_state(steps: list[dict[str, Any]]) -> dict[str, Any]:
        for step in steps:
            if step.get("action", {}).get("type") == "final_verification_gate":
                payload = step.get("post_state", {})
                if isinstance(payload, dict):
                    return payload
        return {}

    def _final_constraints(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
        payload = _final_verification_state(steps)
        constraints = payload.get("constraints", [])
        return [c for c in constraints if isinstance(c, dict)]

    def _constraint_ratio(
        steps: list[dict[str, Any]],
        *,
        category_names: set[str] | None = None,
        text_markers: tuple[str, ...] = (),
    ) -> float | None:
        category_names = category_names or set()
        candidates = []
        for constraint in _final_constraints(steps):
            desc = str(constraint.get("description", "")).lower()
            category = str(constraint.get("category", "")).lower()
            if category_names and category in category_names:
                candidates.append(constraint)
                continue
            if text_markers and any(marker in desc for marker in text_markers):
                candidates.append(constraint)
        if not candidates:
            return None
        satisfied = sum(1 for c in candidates if bool(c.get("satisfied", False)))
        return satisfied / max(len(candidates), 1)

    def _count_successful_actions(steps: list[dict[str, Any]], action_names: set[str]) -> int:
        return sum(
            1
            for step in steps
            if step.get("action", {}).get("type") in action_names
            and bool(step.get("action_result", {}).get("success", False))
        )

    def _constraint_satisfied(steps: list[dict[str, Any]], *markers: str) -> bool:
        markers = tuple(marker.lower() for marker in markers)
        for constraint in _final_constraints(steps):
            desc = str(constraint.get("description", "")).lower()
            if any(marker in desc for marker in markers):
                return bool(constraint.get("satisfied", False))
        return False

    def _verification_mentions(steps: list[dict[str, Any]], *markers: str) -> bool:
        markers = tuple(marker.lower() for marker in markers)
        payload = _final_verification_state(steps)
        corpus = []
        for deficiency in payload.get("deficiencies", []):
            corpus.append(str(deficiency).lower())
        for constraint in _final_constraints(steps):
            corpus.append(str(constraint.get("description", "")).lower())
            corpus.append(str(constraint.get("critique", "")).lower())
        text = " ".join(corpus)
        return any(marker in text for marker in markers)

    evaluator.register_custom_check("check_final_verification_passed", _check_final_verification_passed)
    evaluator.register_custom_check("check_has_productive_execution", _check_has_productive_execution)

    is_art_task = any(
        marker in task_lower
        for marker in (
            "draw ",
            "paint ",
            "sketch",
            "illustrat",
            "canvas",
            "kleki",
            "magma",
            "canva",
        )
    )
    if is_art_task:
        art_claims = list(evaluator._claim_registry.get(task_id, []))
        art_claims.extend([
            TaskClaim("Art task reached active drawing phase", "check_art_reached_drawing_phase", weight=0.75),
            TaskClaim("Art task exercised rendering controls relevant to style", "check_art_used_render_controls", weight=0.5),
            TaskClaim("Art verification shows meaningful visual progress", "check_art_verification_progress", weight=1.0),
            TaskClaim("Art composition coverage is substantial", "check_art_composition_coverage", weight=1.0),
            TaskClaim("Art output is a recognizable subject", "check_art_recognizable_subject", weight=1.25),
            TaskClaim("Art output maintains perspective coherence", "check_art_perspective_coherence", weight=1.25),
            TaskClaim("Art facade or structural subdivisions remain legible", "check_art_facade_legibility", weight=1.0),
            TaskClaim("Art detail density matches the requested fidelity", "check_art_detail_density", weight=1.0),
            TaskClaim("Art render state remained normalized and controlled", "check_art_render_state_normalized", weight=0.75),
        ])
        evaluator.register_claims(task_id, art_claims)

        def _check_art_reached_drawing_phase(_manifest: dict[str, Any], steps: list[dict[str, Any]]) -> bool:
            draw_successes = _count_successful_actions(
                steps,
                {"draw_path", "draw_segments", "draw_shape", "draw_circle", "draw_concentric_triangles"},
            )
            threshold = 1 if planned_steps <= 6 else 3
            return draw_successes >= threshold

        def _check_art_used_render_controls(_manifest: dict[str, Any], steps: list[dict[str, Any]]) -> bool:
            if not any(marker in task_lower for marker in ("shade", "shading", "grayscale", "color", "opacity", "detail")):
                return True
            control_successes = _count_successful_actions(
                steps,
                {"kleki_set_color", "kleki_set_opacity", "kleki_set_brush_size", "kleki_set_scatter", "kleki_set_stabilizer", "kleki_reset_render_state", "set_stroke_color"},
            )
            return control_successes >= 2

        def _check_art_verification_progress(_manifest: dict[str, Any], steps: list[dict[str, Any]]) -> bool:
            ratio = _constraint_ratio(
                steps,
                category_names={"existence", "composition", "subject"},
                text_markers=("skyscraper", "building", "facade", "perspective", "detail", "shade", "grayscale"),
            )
            if ratio is None:
                return False
            return ratio >= 0.4

        def _check_art_composition_coverage(_manifest: dict[str, Any], steps: list[dict[str, Any]]) -> bool:
            return _constraint_satisfied(steps, "substantial portion", "canvas (>30%)", "composition coverage")

        def _check_art_recognizable_subject(_manifest: dict[str, Any], steps: list[dict[str, Any]]) -> bool:
            return _constraint_satisfied(steps, "recognizable tall skyscraper", "recognizable building structure")

        def _check_art_perspective_coherence(_manifest: dict[str, Any], steps: list[dict[str, Any]]) -> bool:
            return _constraint_satisfied(steps, "coherent perspective", "vanishing point", "front-facing verticals", "front-facing horizontals")

        def _check_art_facade_legibility(_manifest: dict[str, Any], steps: list[dict[str, Any]]) -> bool:
            return _constraint_satisfied(steps, "facade structure", "facade grid", "panel lines", "architectural subdivisions")

        def _check_art_detail_density(_manifest: dict[str, Any], steps: list[dict[str, Any]]) -> bool:
            detail_ratio = _constraint_ratio(
                steps,
                text_markers=("detail", "exhaust", "rich", "fine detail", "thorough"),
            )
            return detail_ratio is not None and detail_ratio >= 0.6

        def _check_art_render_state_normalized(_manifest: dict[str, Any], steps: list[dict[str, Any]]) -> bool:
            has_reset = _count_successful_actions(steps, {"kleki_reset_render_state"}) >= 1
            has_scatter = _count_successful_actions(steps, {"kleki_set_scatter"}) >= 1
            no_noise = not _verification_mentions(steps, "scatter", "noise", "scribble", "tangled")
            return has_reset and has_scatter and no_noise

        evaluator.register_custom_check("check_art_reached_drawing_phase", _check_art_reached_drawing_phase)
        evaluator.register_custom_check("check_art_used_render_controls", _check_art_used_render_controls)
        evaluator.register_custom_check("check_art_verification_progress", _check_art_verification_progress)
        evaluator.register_custom_check("check_art_composition_coverage", _check_art_composition_coverage)
        evaluator.register_custom_check("check_art_recognizable_subject", _check_art_recognizable_subject)
        evaluator.register_custom_check("check_art_perspective_coherence", _check_art_perspective_coherence)
        evaluator.register_custom_check("check_art_facade_legibility", _check_art_facade_legibility)
        evaluator.register_custom_check("check_art_detail_density", _check_art_detail_density)
        evaluator.register_custom_check("check_art_render_state_normalized", _check_art_render_state_normalized)

    return evaluator


def _run_benchmark_evaluation(trace_writer, plan: list[dict]) -> dict[str, Any] | None:
    """Evaluate the completed run and save benchmark_result.json beside it."""
    if trace_writer is None:
        return None

    try:
        manifest = json.loads(Path(trace_writer.manifest_path).read_text(encoding="utf-8"))
        task_id = str(manifest.get("task_id", "")).strip()
        if not task_id:
            return None
        evaluator = _build_default_benchmark_evaluator(
            task_id,
            planned_steps=len(plan or []),
            task_description=str(manifest.get("task_description", "")).strip(),
            site_url=str(manifest.get("agent_config", {}).get("url", "")).strip(),
        )
        result = evaluator.evaluate_run(trace_writer.run_dir)
        payload = result.to_dict()
        _exec_log("benchmark_evaluation", None, {
            "claims_score": payload.get("claims_score"),
            "recovery_rate": payload.get("recovery_rate"),
            "plan_optimality": payload.get("plan_optimality"),
        })
        return payload
    except Exception as e:
        logger.warning("Benchmark evaluation failed: %s", e)
        _exec_log("benchmark_evaluation_failed", None, {"error": str(e)})
        return None


# =========================================================================
# MAIN ORCHESTRATOR
# =========================================================================

def run(url: str, goal: str) -> int:
    """Universal entry point. Accepts any URL and any natural language goal.

    Orchestration pipeline (follows Magentic-One's dynamic plan pattern):
    1. Classify task requirements from URL + goal
    2. Activate capabilities based on requirements
    3. Launch browser to URL
    4. Build perception (screenshot + a11y + SoM + element map)
    5. Generate action plan (VLM or fallback)
    6. Execute plan with recovery + verification
    7. Finalize trace and report
    """
    t0 = time.time()
    cre_dir = Path(__file__).parent / "cre"

    log_path = cre_dir / "execution_log.txt"
    log_path.write_text(f"=== UNIVERSAL AGENT LOG === {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n")
    os.environ["EXECUTION_LOG_PATH"] = str(log_path)

    logger.info("=" * 60)
    logger.info("UNIVERSAL VISUAL WEB AGENT")
    logger.info("URL:  %s", url or "(none)")
    logger.info("Goal: %s", goal)
    logger.info("=" * 60)

    # --- 1. Classify task ---
    reqs = classify_task(url, goal)
    logger.info("Task requirements: drawing=%s login=%s nav=%s form=%s known_site=%s",
               reqs.needs_drawing, reqs.needs_login, reqs.needs_navigation,
               reqs.needs_form_fill, reqs.is_known_site)
    _exec_log("classify_task", None, {
        "url": url, "goal": goal,
        "drawing": reqs.needs_drawing, "login": reqs.needs_login,
        "known_site": reqs.is_known_site, "domain": reqs.site_domain,
    })

    # --- 1b. Host-tool health discovery ---
    host_health = HostToolHealth(operator_dir=Path(__file__).parent, cre_dir=cre_dir)
    host_health_payload = host_health.evaluate(reqs, has_url=bool(url))
    host_health_summary = host_health.summary(host_health_payload)
    logger.info(
        "Host tool health: ready=%s selected=%s missing=%s",
        host_health_summary["all_required_ready"],
        host_health_summary["selected"],
        host_health_summary["missing_required_classes"],
    )
    _exec_log("host_tool_health", None, host_health_summary)
    if not host_health_payload["all_required_ready"]:
        logger.error(
            "Host tool health failed: missing required classes %s",
            host_health_payload["missing_required_classes"],
        )
        return 1

    # --- 2. Activate capabilities ---
    capabilities = CapabilityRouter(cre_dir=cre_dir, operator_dir=Path(__file__).parent)
    activated = capabilities.activate_for_task(reqs)
    logger.info("Activated %d capabilities: %s",
               len(activated), [c.name for c in activated])
    _exec_log("capabilities", None, capabilities.summary())

    # --- 3. Initialize agent ---
    router = capabilities.get(CapabilityKind.INFERENCE_ROUTING)
    agent, vision_engine = _init_enterprise_agent(router_instance=router)
    use_enterprise = agent is not None

    if not use_enterprise:
        logger.error("Enterprise agent unavailable (set GEMINI_API_KEY)")
        return 1

    # --- 4. Launch browser ---
    if url:
        _open_safari(url)
        _poll_readiness(agent, url, cre_dir)
        _maximize_safari(agent)
        try:
            agent.enforce_app_focus("Safari")
        except Exception as e:
            logger.warning("Focus enforcement failed: %s", e)

        _dismiss_welcome_screen(agent, cre_dir)

    # --- 5. Build perception ---
    screenshot_path = str(cre_dir / "current_state.png")
    perception = _build_perception(agent, vision_engine, capabilities, screenshot_path)
    cx = perception.get("canvas_center_x", 720)
    cy = perception.get("canvas_center_y", 450)

    # --- 5b. Passive a11y observation (always, for trace) ---
    trace_writer = None
    try:
        from agent_infra import TraceWriter
        task_id = goal.upper().replace(" ", "_")[:40]
        trace_writer = TraceWriter(
            output_dir=cre_dir, task_id=task_id,
            task_description=goal,
            agent_config={
                "mode": "universal",
                "url": url,
                "capabilities": [c.name for c in activated],
            },
        )
        logger.info("Trace: %s", trace_writer.run_dir)
    except Exception as e:
        logger.warning("TraceWriter init failed: %s", e)

    if trace_writer and perception.get("a11y_elements"):
        a11y_elements = perception["a11y_elements"]
        interactive = [e for e in a11y_elements if e.is_interactive]
        step = trace_writer.begin_step(0)
        step.thought = "Passive a11y observation"
        step.action = {"type": "a11y_passive_snapshot", "parameters": {"app": "Safari"}}
        step.action_result = {"success": True}
        step.post_state = {
            "total_elements": len(a11y_elements),
            "interactive_elements": len(interactive),
            "roles_seen": list({e.role for e in a11y_elements}),
            "interactive_labels": [e.label for e in interactive[:20]],
        }
        trace_writer.end_step(step)

    visual_monitor = _start_visual_monitor(trace_writer)

    # --- 6. Site knowledge exploration ---
    site_knowledge = capabilities.get(CapabilityKind.SITE_KNOWLEDGE)
    if site_knowledge and agent:
        from agent_infra.site_knowledge import ExplorationLoop
        summary = site_knowledge.get_summary()
        if not summary.get("has_research") and vision_engine:
            logger.info("No site knowledge — running exploration pipeline...")
            explorer = ExplorationLoop(
                agent=agent, knowledge=site_knowledge,
                vision_engine=vision_engine,
                site_name=reqs.site_domain or "unknown",
            )
            explorer.full_exploration(screenshot_path)
        elif summary.get("num_tools", 0) > 0:
            logger.info("Loaded site knowledge: %s", summary)

    # --- 7. Generate action plan ---
    action_space = UnifiedActionSpace()

    # Inject dependencies for existing modules
    from agent_infra.action_handlers import inject_dependencies as _inject_ah
    from agent_infra.recovery import inject_dependencies as _inject_rec
    _inject_ah(
        _trace, _exec_log, lambda *a, **k: None,
        _validate_coord_cache_entry, _compute_region_phash,
        _get_screenshot_center, _nearest_neighbor_order,
    )
    _inject_rec(_trace, _exec_log, lambda *a, **k: None)

    lessons = capabilities.get(CapabilityKind.EPISODIC_MEMORY) or []
    coord_cache = {}
    task_id_for_cache = goal.upper().replace(" ", "_")[:40]

    if capabilities.is_active(CapabilityKind.COORD_CACHE):
        coord_cache = _load_coord_cache(cre_dir, task_id_for_cache)
        if coord_cache:
            logger.info("Loaded %d cached coordinates from skill library", len(coord_cache))

    # --- Intervention 1: Deterministic Skill Replay (DisCIPL Planner-Follower) ---
    # If a proven/master skill exists for this task, bypass VLM planning entirely
    # and replay the stored action plan. This eliminates the Intrinsic Reasoning Gap
    # (REval, arXiv:2403.16437) by converting probabilistic VLM planning into
    # deterministic coordinate replay. Any model — or a simple loop — can execute
    # stored pixel coordinates without requiring compositional reasoning.
    #
    # Research basis:
    # - DisCIPL (MIT CSAIL, COLM 2025): Planner compiles constraints once;
    #   Followers execute deterministically without understanding strategy.
    # - AutoRefine (ALFWorld 98.4%): Dual-form experience extraction enables
    #   skill reuse without re-planning.
    # - ViReSkill (arXiv:2509.24219): Skill memory with resolved coordinates
    #   for zero-inference replay.
    plan = None
    skill_replay = False
    research_brief = None
    try:
        from agent_infra import SkillLibrary
        lib = SkillLibrary(library_dir=str(cre_dir))
        skill = lib.retrieve_proven(task_id_for_cache)
        if skill is None:
            similar = lib.retrieve_by_similarity(goal, top_k=1, min_score=0.5)
            if similar:
                candidate, score = similar[0]
                if candidate.maturity.tier in ("proven", "master"):
                    skill = candidate
                    logger.info("Skill matched by similarity (score=%.2f): %s",
                               score, candidate.task_id)

        if skill and skill.action_plan and not skill.is_stale():
            plan = skill.action_plan
            skill_replay = True
            logger.info(
                "SKILL REPLAY: Using %s-tier skill (%d steps, %d successes, 0 failures) "
                "— bypassing VLM planning entirely",
                skill.maturity.tier, len(plan), skill.maturity.success_count,
            )
            _exec_log("skill_replay", None, {
                "task_id": skill.task_id,
                "tier": skill.maturity.tier,
                "success_count": skill.maturity.success_count,
                "steps": len(plan),
                "source_run": skill.provenance.get("run_id", "unknown"),
            })
    except Exception as e:
        logger.debug("Skill library check failed (non-fatal): %s", e)

    subject_brief = None
    if plan is None and reqs.needs_drawing and agent:
        subject_brief = _get_subject_brief(agent, goal)

    if plan is None:
        research_brief = _run_pre_execution_research(
            agent,
            goal,
            url,
            site_knowledge,
            Path(trace_writer.run_dir) if trace_writer else None,
        )
        phase2_gate = getattr(agent, "_phase2_gate_result", None) if agent else None
        if phase2_gate and not phase2_gate.get("passed", False):
            logger.error("Phase 2 gate failed: %s", phase2_gate)
            return 1
        phase3_gate = getattr(agent, "_phase3_gate_result", None) if agent else None
        if phase3_gate and not phase3_gate.get("passed", False):
            logger.error("Phase 3 gate failed: %s", phase3_gate)
            return 1

    if plan is None:
        plan = _generate_plan_vlm(
            agent, goal, action_space, perception, capabilities,
            site_knowledge=site_knowledge, lessons=lessons,
            subject_brief=subject_brief,
            research_brief=research_brief,
        )

    if plan is not None and not _plan_is_viable(plan, goal):
        logger.warning("Planner produced non-viable plan; discarding it")
        plan = None

    if plan is None:
        logger.info("VLM planning unavailable — using fallback plan")
        plan = _generate_fallback_plan(goal, url, cx, cy)

    if plan and research_brief and not skill_replay:
        plan = _refine_plan_with_research(
            agent,
            goal,
            plan,
            action_space,
            perception,
            site_knowledge=site_knowledge,
            research_brief=research_brief,
        )

    if not _plan_is_viable(plan, goal):
        logger.error("Planner and fallback both produced non-viable plans; execution may fail early")

    plan = _normalize_plan_for_site(plan, url, goal)

    logger.info("Plan: %d steps", len(plan))
    for i, step in enumerate(plan, 1):
        logger.info("  %d. %s", i, step.get("description", step.get("action")))

    # --- 8. Execute ---
    ctx = ExecutionContext(
        use_enterprise=use_enterprise,
        agent=agent,
        vision_engine=vision_engine,
        ui_analysis=perception,
        cre_dir=cre_dir,
        current_state_path=screenshot_path,
        trace_writer=trace_writer,
        capabilities=capabilities,
        action_space=action_space,
        url=url,
        goal=goal,
    )
    ctx.coord_cache = coord_cache
    ctx.site_knowledge = site_knowledge
    ctx.research_brief = research_brief
    ctx.visual_monitor = visual_monitor

    if not os.environ.get("DISABLE_ACTION_ALLOWLIST"):
        try:
            from agent_infra.action_allowlist import (
                ActionAllowlist,
                get_screen_bounds_from_agent,
                DEFAULT_SCREEN_BOUNDS,
            )
            from agent_infra.action_handlers import ACTION_HANDLERS
            ctx.action_allowlist = ActionAllowlist.from_handlers(set(ACTION_HANDLERS.keys()))
            ctx.screen_bounds = get_screen_bounds_from_agent(agent) if agent else None
            if ctx.screen_bounds is None:
                ctx.screen_bounds = DEFAULT_SCREEN_BOUNDS
        except Exception as e:
            logger.debug("Action allowlist not loaded (non-fatal): %s", e)

    outcome = "success"
    final_verification = None
    visual_monitor_artifact = None
    try:
        evidence = _execute_plan(ctx, plan, action_space)
        if outcome == "success":
            final_verification = _run_final_verification(ctx)
            if not final_verification.passed:
                logger.error("Final verification failed: %s", final_verification.verdict)
                for deficiency in final_verification.deficiencies:
                    logger.error("Final verification deficiency: %s", deficiency)
                outcome = "failure"
    except Exception as e:
        logger.error("Execution failed: %s", e)
        outcome = "failure"
        evidence = []
    finally:
        visual_monitor_artifact = _stop_visual_monitor(
            visual_monitor,
            trace_writer,
            checkpoints=getattr(ctx, "visual_monitor_checkpoints", []),
        )
        _persist_execution_checkpoints(ctx)

    # --- 9. Finalize ---
    elapsed = time.time() - t0
    _exec_log("run_complete", None, {"elapsed_s": round(elapsed, 1), "outcome": outcome})
    _finalize(trace_writer, outcome, plan, evidence,
              agent=agent, capabilities=capabilities,
              final_verification=final_verification,
              visual_monitor_artifact=visual_monitor_artifact)

    logger.info("=" * 60)
    logger.info("COMPLETE in %.1fs | Outcome: %s", elapsed, outcome)
    logger.info("=" * 60)

    return 0 if outcome == "success" else 1


# =========================================================================
# CLI
# =========================================================================

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Universal Visual Web Agent — any URL, any goal",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 agent.py --url https://excalidraw.com --goal "Draw 4 concentric black triangles"
  python3 agent.py --url https://kleki.com --goal "Draw a BMW E30 M3"
  python3 agent.py --url https://mail.google.com --goal "Log in and compose an email"
  python3 agent.py --goal "Navigate to Excalidraw and draw a red circle"
        """,
    )
    parser.add_argument("--url", type=str, default="",
                        help="Target URL (e.g., https://excalidraw.com)")
    parser.add_argument("--goal", type=str, required=True,
                        help="Natural language goal (e.g., 'Draw 4 concentric triangles')")
    args = parser.parse_args()

    url = args.url
    if not url and "excalidraw" in args.goal.lower():
        url = "https://excalidraw.com"
    elif not url and "kleki" in args.goal.lower():
        url = "https://kleki.com"
    elif not url and "magma" in args.goal.lower():
        url = "https://www.magma.com"

    return run(url=url, goal=args.goal)


if __name__ == "__main__":
    sys.exit(main())
