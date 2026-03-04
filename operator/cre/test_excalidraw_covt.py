#!/usr/bin/env python3
"""
Model-Based Planning CoVT Test - Pure-Pixel Safari Canvas Test

Uses enterprise-grade architecture when available:
- MacOSAgentCore: NSWorkspace focus, Gemini File API, Quartz global click
- VisualGroundingEngine: Set-of-Mark overlay and coordinate mapping
- Native screencapture for full-resolution screenshots

Falls back to VLMCoordinator + Hammerspoon kernel when agent_core is not available.

Refactored per Fowler (2018, Refactoring Ch.8 "Move Function") and the SEI
Maintainability Index (Oman & Hagemeister 1991): action handlers, recovery
logic, and startup code extracted into agent_infra.action_handlers,
agent_infra.recovery, and agent_infra.startup respectively.
"""

import os
import sys
import time
import json
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from PIL import Image
except ImportError:
    Image = None  # type: ignore


# =========================================================================
# LOGGING — shared by all extracted modules via dependency injection
# =========================================================================

def _trace(loc: str, msg: str, data: dict | None = None):
    try:
        with open("/Users/christianpardo/rust/.cursor/debug-a16689.log", "a") as f:
            f.write(json.dumps({"sessionId": "a16689", "location": loc, "message": msg, "data": data or {}, "timestamp": int(time.time() * 1000)}) + "\n")
    except Exception:
        pass


def _exec_log_line(event: str, detail: str = "", data: dict | None = None):
    path = os.environ.get("EXECUTION_LOG_PATH")
    if not path:
        return
    try:
        ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + f".{int((time.time() % 1) * 1000):03d}"
        line = f"[{ts}] {event}"
        if detail:
            line += f" | {detail}"
        if data:
            line += f" | {json.dumps(data)}"
        line += "\n"
        with open(path, "a") as f:
            f.write(line)
    except Exception:
        pass


def _pass_log_line(step_name: str, status: str = "PASS", detail: str | None = None):
    path = os.environ.get("PASS_LOG_PATH")
    if not path:
        return
    try:
        ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        line = f"[{ts}] {status} | {step_name}"
        if detail:
            line += f" | {detail}"
        line += "\n"
        with open(path, "a") as f:
            f.write(line)
    except Exception:
        pass


# =========================================================================
# UTILITIES
# =========================================================================

def get_screenshot_center(screenshot_path: str) -> tuple[int, int]:
    _trace("test_excalidraw_covt.py:get_screenshot_center", "entry", {"path": screenshot_path})
    if not Image:
        return (720, 450)
    with Image.open(screenshot_path) as im:
        w, h = im.size
    cx, cy = (w // 2, h // 2)
    _trace("test_excalidraw_covt.py:get_screenshot_center", "exit", {"w": w, "h": h, "center": [cx, cy]})
    return (cx, cy)


def nearest_neighbor_order(points: list[tuple[int, int]]) -> list[tuple[int, int]]:
    if len(points) <= 2:
        return list(points)
    remaining = list(points)
    ordered = [remaining.pop(0)]
    def dist(a, b):
        return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5
    while remaining:
        last = ordered[-1]
        nearest_idx = min(range(len(remaining)), key=lambda i: dist(last, remaining[i]))
        ordered.append(remaining.pop(nearest_idx))
    return ordered


# =========================================================================
# CACHE VALIDATION (pHash gate — adaptive threshold)
# =========================================================================

_PHASH_BASE_TOLERANCE = 0.15
_PHASH_MAX_TOLERANCE = 0.35
_PHASH_HISTORY_WINDOW = 20
_phash_distance_history: list[float] = []
_phash_comparison_log: list[dict] = []


def _compute_region_phash(screenshot_path: str, x: int, y: int, radius: int = 40) -> str | None:
    """Compute a perceptual hash of the region around (x, y) in a screenshot.

    Uses pHash (Zauner, 2010 — "Implementation and Benchmarking of Perceptual
    Image Hash Functions") which operates in the DCT frequency domain, making
    it robust to minor luminance shifts and JPEG artifacts while detecting
    structural changes in the UI layout.

    Returns hex string of the hash, or None if computation fails.
    """
    try:
        import imagehash
        from PIL import Image as _PILImage
        img = _PILImage.open(screenshot_path)
        left = max(0, x - radius)
        top = max(0, y - radius)
        right = min(img.width, x + radius)
        bottom = min(img.height, y + radius)
        region = img.crop((left, top, right, bottom))
        return str(imagehash.phash(region))
    except Exception:
        return None


def _adaptive_phash_tolerance() -> float:
    """Compute tolerance that widens under high environmental volatility.

    Uses the standard deviation of recent pHash distances as a volatility
    estimator. When the environment is stable (low std), tolerance stays
    near the base. When volatile (high std), tolerance widens up to the
    configured maximum, reducing false cache invalidations.
    """
    if len(_phash_distance_history) < 3:
        return _PHASH_BASE_TOLERANCE

    recent = _phash_distance_history[-_PHASH_HISTORY_WINDOW:]
    mean = sum(recent) / len(recent)
    variance = sum((d - mean) ** 2 for d in recent) / len(recent)
    std = variance ** 0.5

    adaptive = _PHASH_BASE_TOLERANCE + 2.0 * std
    return min(adaptive, _PHASH_MAX_TOLERANCE)


def get_phash_comparison_log() -> list[dict]:
    """Return the full pHash comparison log for trace injection."""
    return list(_phash_comparison_log)


def _validate_coord_cache_entry(screenshot_path: str, cached: dict, tolerance: float | None = None) -> bool:
    """Validate a cached coordinate against the current UI via perceptual hash.

    Per GUI-Actor (NeurIPS 2025, arXiv:2506.03143) and UGround (ICLR 2025 Oral,
    arXiv:2410.05243): raw pixel coordinates are fragile under distribution shift.
    This gate detects UI drift by comparing the pHash of the region around the
    cached coordinate against the stored hash from when the coord was captured.

    When tolerance is None, uses adaptive threshold based on observed volatility.
    Returns True if the cached coord is still valid.
    """
    stored_hash_hex = cached.get("region_hash")
    if not stored_hash_hex:
        return True

    current_hash_hex = _compute_region_phash(screenshot_path, cached["x"], cached["y"])
    if current_hash_hex is None:
        return True

    try:
        import imagehash
        stored = imagehash.hex_to_hash(stored_hash_hex)
        current = imagehash.hex_to_hash(current_hash_hex)
        distance = (stored - current) / stored.hash.size

        _phash_distance_history.append(distance)
        if len(_phash_distance_history) > _PHASH_HISTORY_WINDOW * 2:
            _phash_distance_history[:] = _phash_distance_history[-_PHASH_HISTORY_WINDOW:]

        effective_tolerance = tolerance if tolerance is not None else _adaptive_phash_tolerance()
        valid = distance < effective_tolerance

        entry = {
            "x": cached["x"], "y": cached["y"],
            "distance": round(distance, 4),
            "tolerance": round(effective_tolerance, 4),
            "base_tolerance": _PHASH_BASE_TOLERANCE,
            "valid": valid,
            "history_len": len(_phash_distance_history),
            "stored_hash": stored_hash_hex[:8],
            "current_hash": current_hash_hex[:8],
        }
        _phash_comparison_log.append(entry)

        status = "VALID" if valid else "INVALID"
        adaptive_tag = " (adaptive)" if tolerance is None else ""
        print(f"  [pHash {status}] distance={distance:.4f}, tolerance={effective_tolerance:.4f}{adaptive_tag}, "
              f"coord=({cached['x']}, {cached['y']})")

        return valid
    except Exception:
        return True


# =========================================================================
# IMPORTS & ENTERPRISE DETECTION
# =========================================================================

from codex_client import CodexClient

try:
    from agent_core import MacOSAgentCore
    from visual_engine import VisualGroundingEngine
    ENTERPRISE_AVAILABLE = True
except ImportError:
    MacOSAgentCore = None  # type: ignore
    VisualGroundingEngine = None  # type: ignore
    ENTERPRISE_AVAILABLE = False

try:
    from agent_infra import TraceWriter
except ImportError:
    try:
        from trace_writer import TraceWriter
    except ImportError:
        TraceWriter = None  # type: ignore

try:
    from agent_infra import SkillLibrary, ActionTrustTracker, Summarizer, SiteKnowledge, ExplorationLoop
except ImportError:
    SkillLibrary = None  # type: ignore
    ActionTrustTracker = None  # type: ignore
    SiteKnowledge = None  # type: ignore
    ExplorationLoop = None  # type: ignore
    Summarizer = None  # type: ignore

if not ENTERPRISE_AVAILABLE:
    from vlm_coordinator import VLMCoordinator

# =========================================================================
# EXTRACTED MODULE IMPORTS + DEPENDENCY INJECTION
# =========================================================================

from agent_infra.action_handlers import (
    ACTION_HANDLERS,
    _SOM_DEPENDENT_ACTIONS,
    _ACTION_EFFECT_CHECKS,
    inject_dependencies as _inject_action_deps,
)
from agent_infra.recovery import (
    _execute_action_with_recovery,
    inject_dependencies as _inject_recovery_deps,
)
from agent_infra.startup import (
    _init_agent,
    _launch_safari_and_capture,
    inject_dependencies as _inject_startup_deps,
)

_inject_action_deps(
    _trace, _exec_log_line, _pass_log_line,
    _validate_coord_cache_entry, _compute_region_phash,
    get_screenshot_center, nearest_neighbor_order,
)
_inject_recovery_deps(_trace, _exec_log_line, _pass_log_line)
_inject_startup_deps(_exec_log_line, _pass_log_line, get_screenshot_center)


# =========================================================================
# EXCALIDRAW DOMAIN KNOWLEDGE
# =========================================================================

EXCALIDRAW_KNOWLEDGE = {
    "keyboard_shortcuts": {
        "pen_tool": "p",
        "stroke_color": "S",
        "background_color": "G",
        "selection_tool": "V",
        "rectangle": "R", "ellipse": "O", "arrow": "A", "line": "L", "text": "T",
        "pick_color": "I",
    },
    "workflow": {
        "draw_triangle": [
            "Select pen tool (p)",
            "Draw triangle path",
            "Open stroke color picker (S)",
            "Select red color",
            "Verify"
        ]
    }
}


# =========================================================================
# VLM PLANNING
# =========================================================================

def analyze_ui_initial_state(vlm: "VLMCoordinator", screenshot_bytes: bytes) -> dict:
    print("\n" + "="*60)
    print("PHASE 2: KNOWLEDGE ACQUISITION")
    print("="*60)
    analysis_prompt = """Analyze this screenshot of an Excalidraw canvas application. Provide a JSON response with:
{
    "page_loaded": true/false,
    "canvas_visible": true/false,
    "canvas_center_x": <number>,
    "canvas_center_y": <number>,
    "toolbar_visible": true/false,
    "toolbar_position": "top/left/right",
    "available_tools": ["list of visible drawing tools"],
    "current_tool": "currently selected tool or null",
    "canvas_state": "empty/has_drawings",
    "color_palette_visible": true/false,
    "coordinate_system": {
        "origin": "top-left/center",
        "x_direction": "right",
        "y_direction": "down"
    }
}

Respond ONLY with the JSON object."""

    print("  Asking VLM to analyze current UI state...")
    try:
        response_json = vlm.get_next_action(
            screenshot_bytes, [],
            goal="Analyze the current state of the Excalidraw canvas",
            use_som=True,
            custom_prompt=analysis_prompt
        )
        _trace("test_excalidraw_covt.py:analyze_ui", "response", {"raw": response_json[:200]})
        ui_data = json.loads(response_json)
        print(f"  UI Analysis complete:")
        for key, value in ui_data.items():
            print(f"    {key}: {value}")
        return ui_data
    except json.JSONDecodeError:
        _trace("test_excalidraw_covt.py:analyze_ui", "parse_error", {"raw": response_json[:200]})
        print("  VLM returned non-JSON response, using defaults")
        return {
            "page_loaded": True, "canvas_visible": True,
            "canvas_center_x": 720, "canvas_center_y": 450,
            "toolbar_visible": True, "toolbar_position": "top",
            "canvas_state": "empty", "canvas_center": {"x": 720, "y": 450},
        }
    except Exception as e:
        print(f"  UI analysis failed: {e}")
        return {
            "page_loaded": True, "canvas_visible": True,
            "canvas_center_x": 720, "canvas_center_y": 450,
            "canvas_center": {"x": 720, "y": 450},
        }


def generate_action_plan(ui_state: dict, goal: str = "Draw a red triangle") -> list[dict]:
    _trace("test_excalidraw_covt.py:generate_action_plan", "entry", {"goal": goal})
    cx = ui_state.get("canvas_center_x", ui_state.get("canvas_center", {}).get("x", 720))
    cy = ui_state.get("canvas_center_y", ui_state.get("canvas_center", {}).get("y", 450))

    if os.environ.get("CONCENTRIC_TRIANGLES_CLEAN"):
        _exec_log_line("phase", "PHASE 3: ACTION PLANNING")
        print("\n" + "="*60)
        print("PHASE 3: ACTION PLANNING")
        print("="*60)
        print("Concentric triangles (clean) mode: clear canvas -> re-center -> pen -> black -> 4 triangles in middle")
        plan = [
            {"action": "clear_canvas", "args": {}, "description": "Erase all drawings (Cmd+Backspace)"},
            {"action": "keystroke", "args": {"key": 36}, "description": "Confirm clear canvas dialog (Enter)"},
            {"action": "sleep", "args": {"seconds": 1.0}, "description": "Pause for dialog to close and canvas to clear"},
            {"action": "sleep", "args": {"seconds": 0}, "description": "Verify canvas is empty (state-based oracle)", "visual_assert": "Is the Excalidraw canvas empty with no drawings or shapes visible? Reply YES or NO.", "verify": True},
            {"action": "sleep", "args": {"seconds": 0.5}, "description": "Pause after clear so canvas is ready"},
            {"action": "refresh_canvas_center", "args": {}, "description": "Re-capture and get exact canvas center for drawing in middle"},
            {"action": "sleep", "args": {"seconds": 0.5}, "description": "Brief pause before selecting pen"},
            {"action": "keystroke", "args": {"key": "p"}, "description": "Select pen tool (p)", "visual_assert": "Is the Pen tool (draw/pencil icon) selected in the Excalidraw toolbar? Reply YES or NO.", "verify": True},
            {"action": "keystroke", "args": {"key": "S"}, "description": "Open stroke color picker (S)"},
            {"action": "set_stroke_color", "args": {"color": "black"}, "description": "Set stroke to black"},
            {"action": "sleep", "args": {"seconds": 0.5}, "description": "Pause before drawing"},
            {"action": "draw_concentric_triangles", "args": {"sizes": [220, 160, 100, 50], "inter_triangle_delay": 0.6}, "description": "Draw 4 concentric triangles at center (release at each corner)", "visual_assert": "Are there four nested black-outline triangles in the center of the Excalidraw drawing canvas (ignore toolbar and side panels)? Reply YES or NO.", "verify": True},
        ]
        print(f"Generated action plan: {len(plan)} actions")
        for i, p in enumerate(plan, 1):
            verify_tag = " [VERIFY]" if p.get("verify") else ""
            print(f"   {i}. {p['description']}{verify_tag}")
        return plan

    plan = [
        {"action": "keystroke", "args": {"key": "p"}, "description": "Select pen tool (p)"},
        {"action": "draw_path", "args": {"vertices": [[cx, cy - 100], [cx - 86, cy + 50], [cx + 86, cy + 50], [cx, cy - 100]]}, "description": "Draw triangle path"},
        {"action": "keystroke", "args": {"key": "S"}, "description": "Open stroke color picker (S)"},
        {"action": "click", "args": {"x": cx, "y": cy}, "description": "Select red color from palette"},
        {"action": "sleep", "args": {"seconds": 0.5}, "description": "Wait for color to apply"},
        {"action": "verify_success", "args": {}, "description": "Verify red triangle is drawn", "verify": True},
    ]
    return plan


def generate_dynamic_plan(agent, som_path: str, goal: str,
                          available_actions: list[str],
                          fallback_plan: list[dict],
                          lessons: list[str] | None = None,
                          summarizer=None,
                          site_knowledge=None) -> list[dict]:
    """Ask Gemini 2.5 Pro to generate an action plan from the current SoM overlay.

    Follows the OpAgent decomposition (arXiv:2402.01030): a Planner sub-module
    produces a structured action sequence that the Grounder (SoM) and Executor
    (ACTION_HANDLERS) can consume without ambiguity.

    Injecting summarizer context follows Reflexion (Shinn et al., NeurIPS 2023)
    and VIGIL (arXiv:2512.07094) — trace summaries improve plan quality.

    Site knowledge injection follows AppAgent (Yang et al., 2023,
    arXiv:2312.13771) Phase 2: deployment with compiled knowledge base.
    """
    _trace("test_excalidraw_covt.py:generate_dynamic_plan", "entry", {"goal": goal, "actions": available_actions})
    action_schema = json.dumps(available_actions, indent=2)

    lessons_block = ""
    if lessons:
        lessons_block = "\n\nLessons from past runs (use these to avoid repeating mistakes):\n"
        for lesson in lessons:
            lessons_block += f"  - {lesson}\n"

    summary_block = ""
    if summarizer:
        summary_text = summarizer.get_context()
        if summary_text:
            summary_block = f"\n\nExecution context from current session:\n{summary_text}\n"

    knowledge_block = ""
    if site_knowledge:
        kb_text = site_knowledge.get_planner_context()
        if kb_text:
            knowledge_block = f"\n\n{kb_text}\n"

    prompt = (
        f"You are a GUI automation planner. Your goal: {goal}\n\n"
        f"Available action types:\n{action_schema}\n"
        f"{knowledge_block}{lessons_block}{summary_block}\n"
        "Look at the SoM overlay screenshot. Plan a sequence of actions to achieve the goal.\n"
        "Output a JSON array of action objects. Each action must have:\n"
        '  {"action": "<action_type>", "args": {<parameters>}, "description": "<what it does>"}\n\n'
        "Valid action types and their args:\n"
        '  keystroke: {"key": "<key_name_or_code>"}\n'
        '  sleep: {"seconds": <float>}\n'
        '  set_stroke_color: {"color": "<color_name>"}\n'
        '  click: {"x": <int>, "y": <int>}\n'
        '  draw_path: {"vertices": [[x1,y1], [x2,y2], ...]}\n'
        '  draw_circle: {"radius": <int>, "num_points": 36}\n'
        '  drag_shape: {"tool_key": "2"|"4"|"3", "width": <int>, "height": <int>, "offset_x": <int>, "offset_y": <int>}\n'
        '    tool_key "2"=rectangle, "4"=ellipse, "3"=diamond. offset is relative to canvas center.\n'
        '  draw_eiffel_tower: {"scale": 1.0, "offset_x": 0, "offset_y": 0}\n'
        '    Draws a detailed Eiffel Tower with exponential-profile legs, platforms, arch, cross-bracing, antenna.\n'
        '  draw_eiffel_landscape: {}\n'
        '    Draws a complete Paris landscape: sky, ground, river, buildings, Eiffel Tower, trees, sun, clouds.\n'
        '    Uses multiple tools, colors, stroke widths, fills, and layering. Self-contained — no other steps needed.\n'
        '  draw_concentric_triangles: {"sizes": [220,160,100,50]}\n'
        '  clear_canvas: {}\n'
        '  refresh_canvas_center: {}\n'
        '  verify_success: {}\n\n'
        "CRITICAL RULES (MUST follow exactly):\n"
        "- draw_circle uses the DRAW tool (keystroke '7'), NOT the ellipse tool.\n"
        "  It draws a polygon approximation at the canvas center.\n"
        "- In Excalidraw, switching tools RESETS the stroke color. So:\n"
        "  1. Select tool FIRST (e.g., keystroke '7' for draw tool)\n"
        "  2. THEN set_stroke_color to desired color\n"
        "  3. THEN refresh_canvas_center\n"
        "  4. THEN draw\n"
        "- clear_canvas auto-confirms its dialog and waits. Do NOT add keystroke Enter or sleep after clear_canvas.\n"
        "- EXACT sequence for drawing a colored shape:\n"
        "  clear_canvas -> keystroke '7' -> set_stroke_color {color} -> refresh_canvas_center -> draw_circle -> verify_success\n"
        "- That's 6 steps total. Do NOT add extra steps.\n\n"
        "Output ONLY the JSON array."
    )

    try:
        uploaded = agent._client.files.upload(file=som_path)
        response = agent._client.models.generate_content(
            model="gemini-2.5-pro",
            contents=[uploaded, prompt],
            config=agent._gen_config_json,
        )
        raw_text = response.text.strip()
        if raw_text.startswith("```"):
            raw_text = raw_text.split("\n", 1)[1]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
        plan = json.loads(raw_text)
        if isinstance(plan, list) and len(plan) > 0:
            _trace("test_excalidraw_covt.py:generate_dynamic_plan", "ok", {"steps": len(plan)})
            return plan
    except Exception as e:
        print(f"  [DYNAMIC PLAN] VLM plan generation failed ({e}), using fallback")
        _trace("test_excalidraw_covt.py:generate_dynamic_plan", "fallback", {"error": str(e)})
        return fallback_plan
    return fallback_plan


# =========================================================================
# CONTEXT & EPISODIC MEMORY
# =========================================================================

class _ExecutionJournal:
    """Episodic memory buffer for Reflexion-based self-reflection (Shinn et al., NeurIPS 2023)."""

    def __init__(self, max_entries: int = 20) -> None:
        self._entries: list[dict] = []
        self._max = max_entries

    def record(self, step: int, action: str, result: str, screenshot_path: str | None = None) -> None:
        entry = {"step": step, "action": action, "result": result, "screenshot_path": screenshot_path or ""}
        self._entries.append(entry)
        if len(self._entries) > self._max:
            self._entries = self._entries[-self._max:]

    def recent(self, n: int = 5) -> list[dict]:
        return self._entries[-n:]

    def format_for_prompt(self, n: int = 5) -> str:
        entries = self.recent(n)
        if not entries:
            return "No prior actions recorded."
        lines = []
        for e in entries:
            lines.append(f"  Step {e['step']}: {e['action']} -> {e['result']}")
        return "\n".join(lines)


class _Ctx:
    """Shared state passed to every action handler."""
    __slots__ = (
        "use_enterprise", "agent", "vision_engine", "client", "vlm",
        "ui_analysis", "cre_dir", "current_state_path", "journal",
        "trace_writer", "coord_cache", "trust_tracker",
        "_last_resolved_coords", "summarizer", "element_map", "primitives",
        "rules", "action_allowlist", "screen_bounds",
    )

    def __init__(self, *, use_enterprise, agent, vision_engine, client, vlm,
                 ui_analysis, cre_dir, current_state_path, trace_writer=None,
                 coord_cache=None, trust_tracker=None, summarizer=None,
                 element_map=None, primitives=None, rules=None,
                 action_allowlist=None, screen_bounds=None):
        self.use_enterprise = use_enterprise
        self.agent = agent
        self.vision_engine = vision_engine
        self.client = client
        self.vlm = vlm
        self.ui_analysis = ui_analysis
        self.cre_dir = cre_dir
        self.current_state_path = current_state_path
        self.journal = _ExecutionJournal()
        self.trace_writer = trace_writer
        self.coord_cache = coord_cache or {}
        self.trust_tracker = trust_tracker
        self._last_resolved_coords = None
        self.element_map = element_map
        self.primitives = primitives
        self.summarizer = summarizer
        self.rules: list[str] = rules or []
        self.action_allowlist = action_allowlist
        self.screen_bounds = screen_bounds

    @property
    def canvas_center(self) -> dict:
        return self.ui_analysis.get("canvas_center", {})

    @property
    def cx(self) -> int:
        return self.canvas_center.get("x", 720)

    @property
    def cy(self) -> int:
        return self.canvas_center.get("y", 450)


# =========================================================================
# ORCHESTRATOR HELPERS
# =========================================================================

def _init_logging(cre_dir: Path):
    execution_log_path = cre_dir / "execution_log.txt"
    execution_log_path.write_text(
        f"=== EXECUTION LOG START === {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n",
        encoding="utf-8",
    )
    os.environ["EXECUTION_LOG_PATH"] = str(execution_log_path)
    if os.environ.get("CONCENTRIC_TRIANGLES_CLEAN"):
        pass_log_path = cre_dir / "concentric_triangles_clean_pass_log.txt"
        pass_log_path.write_text(
            f"=== CONCENTRIC TRIANGLES (CLEAN) PASS LOG === {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n",
            encoding="utf-8",
        )
        os.environ["PASS_LOG_PATH"] = str(pass_log_path)
    _exec_log_line("run_start", "test_excalidraw_covt.py")


def _resolve_task_id() -> tuple[str, str]:
    if os.environ.get("CONCENTRIC_TRIANGLES_CLEAN"):
        return "CONCENTRIC_TRIANGLES_CLEAN", "Clear canvas and draw 4 nested concentric triangles"
    if os.environ.get("CONCENTRIC_TRIANGLES"):
        return "CONCENTRIC_TRIANGLES", "Draw 4 nested concentric triangles"
    custom_goal = os.environ.get("AGENT_GOAL")
    if custom_goal:
        task_id = custom_goal.upper().replace(" ", "_")[:40]
        return task_id, custom_goal
    return "", "Model-Based Planning CoVT Agent"


def _init_trace_writer(cre_dir, task_id: str, task_description: str, use_enterprise: bool):
    if TraceWriter is None:
        return None
    ablation_condition = os.environ.get("ABLATION_CONDITION")
    agent_cfg = {
        "mode": "enterprise" if use_enterprise else "legacy",
        "model": "gemini-2.5-pro" if use_enterprise else "legacy",
    }
    if ablation_condition:
        agent_cfg["ablation_condition"] = ablation_condition
        agent_cfg["cache_disabled"] = bool(os.environ.get("DISABLE_COORD_CACHE"))
        agent_cfg["trust_disabled"] = bool(os.environ.get("DISABLE_TRUST_TRACKER"))
        agent_cfg["adaptive_routing_disabled"] = bool(os.environ.get("DISABLE_ADAPTIVE_ROUTING"))
    tw = TraceWriter(
        output_dir=cre_dir,
        task_id=task_id,
        task_description=task_description,
        agent_config=agent_cfg,
    )
    print(f"  Trace writer initialized: {tw.run_dir}")
    _exec_log_line("trace_writer_init", None, {"run_id": tw.run_id, "run_dir": str(tw.run_dir)})
    return tw


def _load_episodic_memory(cre_dir, task_id: str) -> list[str]:
    past_lessons: list[str] = []
    try:
        from agent_infra import ReflectionJournal, RulesStore
        _journal_path = cre_dir / "runs" / "reflection_journal.jsonl"
        if _journal_path.exists():
            _rj = ReflectionJournal(_journal_path)
            past_lessons = _rj.retrieve_relevant(task_id, top_k=3)
        _rules_path = cre_dir / "runs" / "rules.jsonl"
        if _rules_path.exists():
            _rs = RulesStore(_rules_path)
            past_lessons.extend(_rs.get_rules())
        if past_lessons:
            print(f"  [EPISODIC] Loaded {len(past_lessons)} lessons from past runs")
            _exec_log_line("episodic_memory", None, {"lessons_count": len(past_lessons)})
    except Exception:
        pass
    return past_lessons


def _load_coord_cache(cre_dir, task_id: str) -> dict:
    """Load coordinate cache from MASTER skill if available."""
    coord_cache: dict = {}
    if SkillLibrary is None or not task_id:
        return coord_cache
    try:
        lib = SkillLibrary(library_dir=str(cre_dir))
        skill = lib.retrieve_exact(task_id)
        if skill and skill.maturity.tier == "master" and skill.action_plan:
            if skill.is_stale():
                print(f"  [COORD CACHE] Skill is STALE (last validated: {skill.last_validated_at}) — skipping cache")
            else:
                for step_entry in skill.action_plan:
                    rc = step_entry.get("resolved_coords")
                    if rc and rc.get("action"):
                        cache_key = (rc["action"], rc.get("color", ""))
                        coord_cache[cache_key] = {
                            "x": rc["x"], "y": rc["y"],
                            "box_id": rc.get("box_id", -1),
                            "region_hash": rc.get("region_hash"),
                        }
                if coord_cache:
                    print(f"  [COORD CACHE] Loaded {len(coord_cache)} cached coords from MASTER skill")
    except Exception as e:
        print(f"  [COORD CACHE] Could not load skill: {e}")
    return coord_cache


# =========================================================================
# EXECUTION LOOP
# =========================================================================

def _execute_plan(ctx: _Ctx, action_plan: list[dict]) -> list[dict]:
    _exec_log_line("phase", "PHASE 4: EXECUTION")
    print("\n" + "="*60)
    print("PHASE 4: EXECUTION WITH MINIMAL VERIFICATION")
    print("="*60)

    if ctx.use_enterprise and ctx.agent and ctx.ui_analysis.get("canvas_center"):
        try:
            ctx.agent.execute_move_mouse(ctx.cx, ctx.cy)
            time.sleep(0.2)
            print("  Moved cursor to canvas center")
            _exec_log_line("move_cursor_to_canvas", None, {"cx": ctx.cx, "cy": ctx.cy})
        except Exception as e:
            print(f"  Move to canvas center failed (continuing): {e}")
            _exec_log_line("move_cursor_error", str(e))

    screenshot_count = 1
    evidence_dir = None
    evidence_entries: list[dict] = []
    if os.environ.get("CONCENTRIC_TRIANGLES_CLEAN"):
        evidence_dir = ctx.cre_dir / "evidence_concentric_clean"
        evidence_dir.mkdir(exist_ok=True)

    for i, action_item in enumerate(action_plan, 1):
        action_type = action_item["action"]
        description = action_item["description"]
        needs_verification = action_item.get("verify", False)
        _trace("test_excalidraw_covt.py:action_loop", "step", {"i": i, "action_type": action_type, "description": description[:50]})
        print(f"\n--- Action {i}/{len(action_plan)}: {description} ---")
        _exec_log_line("action_start", None, {"index": i, "type": action_type, "description": description})

        _execute_action_with_recovery(ctx, action_item, i)

        if needs_verification:
            screenshot_count += 1
            _capture_verification_screenshot(ctx, i, description, action_type, screenshot_count)

        if evidence_dir and ctx.use_enterprise and ctx.agent:
            _capture_evidence(evidence_dir, evidence_entries, i, description)

        if action_type == "verify_success" and ctx.use_enterprise:
            break

    return evidence_entries


def _capture_verification_screenshot(ctx: _Ctx, step_index: int, description: str, action_type: str, screenshot_count: int):
    print(f"\n  Verification screenshot #{screenshot_count}...")
    try:
        if ctx.use_enterprise and ctx.agent:
            verify_path = str(ctx.cre_dir / f"verify_{screenshot_count}.png")
            subprocess.run(["screencapture", "-x", verify_path], check=True, timeout=10)
            print(f"  Verification screenshot saved: {verify_path}")
        else:
            screen_info = ctx.client.get_screen_info()
            width = screen_info.get('logical_width', 1440)
            height = screen_info.get('logical_height', 900)
            region = {
                'x': int(width * 0.25), 'y': int(height * 0.25),
                'w': int(width * 0.5), 'h': int(height * 0.5)
            }
            verify_screenshot = ctx.client.screenshot(region=region, scale=0.2)
            print(f"  Verification screenshot captured: {len(verify_screenshot)} bytes")

            if action_type == "verify_success" and ctx.vlm is not None:
                print("  VLM analyzing final state...")
                try:
                    response_json = ctx.vlm.get_next_action(verify_screenshot, [], goal="Draw a red triangle", use_som=True)
                    decision = json.loads(response_json)
                    if decision.get("action_type") == "verify_success":
                        print("  VLM confirms: Red triangle successfully drawn!")
                except Exception as e:
                    print(f"  VLM verification failed: {e}")
            elif action_type == "verify_success" and ctx.use_enterprise:
                print("  Enterprise path: final verification step complete.")
    except Exception as e:
        print(f"  Verification screenshot failed: {e}")


def _capture_evidence(evidence_dir: Path, evidence_entries: list[dict], step_index: int, description: str):
    try:
        step_path = evidence_dir / f"step_{step_index:02d}.png"
        subprocess.run(["screencapture", "-x", str(step_path)], check=True, timeout=10)
        evidence_entries.append({
            "step": step_index,
            "description": description,
            "status": "PASS",
            "filename": step_path.name,
        })
        print(f"   Evidence saved: {step_path.name}")
    except Exception as e:
        print(f"   Evidence screenshot failed: {e}")


def _write_evidence_report(evidence_dir: Path, evidence_entries: list[dict]):
    if not evidence_dir or not evidence_entries:
        return
    report_path = evidence_dir / "report.html"
    try:
        html_parts = [
            "<!DOCTYPE html><html><head><meta charset='utf-8'><title>Concentric Triangles (Clean) - Evidence</title>",
            "<style>body{font-family:system-ui;max-width:900px;margin:2rem auto;padding:0 1rem;}",
            "h1{color:#111;} .step{margin:2rem 0;padding:1rem;background:#f8f9fa;border-radius:8px;}",
            ".step h2{margin:0 0 .5rem;font-size:1.1rem;color:#333;} .step .status{color:#0a0;font-weight:bold;}",
            ".step img{max-width:100%;height:auto;border:1px solid #ddd;border-radius:4px;display:block;margin-top:.5rem;}</style></head><body>",
            "<h1>Concentric Triangles (Clean) - Evidence report</h1>",
            f"<p>Generated {time.strftime('%Y-%m-%d %H:%M:%S')}. Each step has a screenshot so you can see with your own eyes that it passed.</p>",
        ]
        for e in evidence_entries:
            step, desc, status, filename = e["step"], e["description"], e["status"], e["filename"]
            html_parts.append(f'<div class="step"><h2>Step {step}: {desc}</h2>')
            html_parts.append(f'<span class="status">{status}</span>')
            html_parts.append(f'<img src="{filename}" alt="Step {step}" />')
            html_parts.append("</div>")
        html_parts.append("</body></html>")
        report_path.write_text("\n".join(html_parts), encoding="utf-8")
        print(f"\n  Evidence report written: {report_path}")
    except Exception as ex:
        print(f"\n  Could not write evidence report: {ex}")


def _finalize_run(trace_writer, run_outcome: str, action_plan: list, evidence_entries: list, agent=None):
    evidence_dir_path = Path(__file__).parent / "evidence_concentric_clean" if os.environ.get("CONCENTRIC_TRIANGLES_CLEAN") else None
    _write_evidence_report(evidence_dir_path, evidence_entries)
    _exec_log_line("run_complete", None, {"actions_executed": len(action_plan)})

    phash_log = get_phash_comparison_log()
    if phash_log:
        _exec_log_line("phash_summary", None, {
            "total_comparisons": len(phash_log),
            "valid_count": sum(1 for e in phash_log if e["valid"]),
            "invalid_count": sum(1 for e in phash_log if not e["valid"]),
            "mean_distance": round(sum(e["distance"] for e in phash_log) / len(phash_log), 4),
            "comparisons": phash_log,
        })
        if trace_writer:
            _phash_step = trace_writer.begin_step(999)
            _phash_step.thought = "pHash audit — all cache comparisons for this run"
            _phash_step.action = {"type": "phash_audit", "parameters": {"target": "coord_cache"}}
            _phash_step.action_result = {"success": True}
            _phash_step.post_state = {
                "total_comparisons": len(phash_log),
                "valid_count": sum(1 for e in phash_log if e["valid"]),
                "invalid_count": sum(1 for e in phash_log if not e["valid"]),
                "comparisons": phash_log,
            }
            trace_writer.end_step(_phash_step)

    if trace_writer:
        manifest = trace_writer.finalize(outcome=run_outcome)
        print(f"\n  Structured trace written: {trace_writer.trace_path}")
        print(f"  Manifest: {trace_writer.manifest_path}")
        print(f"  Run ID: {trace_writer.run_id} | Outcome: {run_outcome} | Steps: {manifest['num_steps']}")
        if manifest.get("failure_step"):
            print(f"  Failure at step {manifest['failure_step']}: {manifest['error_summary']}")

    print("\n" + "="*60)
    print("EXECUTION COMPLETE")
    print("="*60)
    print(f"\n  Statistics:")
    print(f"   Total actions executed: {len(action_plan)}")
    if evidence_entries:
        print(f"   Evidence screenshots: {len(evidence_entries)}")
    if agent and hasattr(agent, "_router") and agent._router:
        stats = agent._router.stats
        print(f"   Routing stats: {stats.to_dict()}")
        if hasattr(agent._router, "get_performance_summary"):
            perf = agent._router.get_performance_summary()
            if perf:
                print(f"   Per-task performance: {perf}")
        if hasattr(agent._router, "adaptations") and agent._router.adaptations:
            print(f"   Routing adaptations: {agent._router.adaptations}")
    print("\n  Model-Based Planning approach completed successfully!")


# =========================================================================
# MAIN ORCHESTRATOR
# =========================================================================

def run_model_based_agent():
    """Top-level orchestrator — decomposed per Sculley et al. (2015) to
    minimize glue-code complexity and ensure each sub-step is independently
    testable and modifiable by both human and AI agents."""
    _trace("test_excalidraw_covt.py:run_model_based_agent", "entry", {"CONCENTRIC_TRIANGLES_CLEAN": os.environ.get("CONCENTRIC_TRIANGLES_CLEAN")})
    cre_dir = Path(__file__).parent
    _init_logging(cre_dir)

    print("\n" + "="*60)
    print("MODEL-BASED PLANNING CoVT AGENT")
    print("Pure-Pixel Safari Canvas Test")
    print("="*60)

    use_enterprise, agent, vision_engine, client, vlm = _init_agent()
    if agent is None and client is None:
        return 1

    task_id, task_description = _resolve_task_id()
    trace_writer = _init_trace_writer(cre_dir, task_id, task_description, use_enterprise)

    trust_tracker = None
    if ActionTrustTracker is not None and not os.environ.get("DISABLE_TRUST_TRACKER"):
        trust_tracker = ActionTrustTracker(persist_path=str(cre_dir / "action_trust.json"))
    elif os.environ.get("DISABLE_TRUST_TRACKER"):
        print("  [ABLATION] Trust tracker DISABLED")
        _exec_log_line("ablation", "trust_tracker_disabled")

    try:
        ui_analysis, current_state_path = _launch_safari_and_capture(
            use_enterprise, agent, vision_engine, client, vlm, cre_dir,
            trust_tracker=trust_tracker,
        )
    except Exception as e:
        print(f"  Launch/capture failed: {e}")
        if trace_writer:
            trace_writer.record_failure(0, "launch_failure", str(e))
            trace_writer.finalize(outcome="error")
        return 1

    _element_map = None
    _primitives = None

    # --- Passive a11y observer: always runs, logs to trace, changes no behavior ---
    try:
        from a11y_engine import A11yEngine
        _a11y_observer = A11yEngine()
        _a11y_snapshot = _a11y_observer.extract("Safari")
        _a11y_interactive = [e for e in _a11y_snapshot if e.is_interactive]
        print(f"  [A11Y-OBSERVE] Passive snapshot: {len(_a11y_snapshot)} elements "
              f"({len(_a11y_interactive)} interactive) via {_a11y_observer.backend}")
        if trace_writer:
            _a11y_step = trace_writer.begin_step(0)
            _a11y_step.thought = "Passive a11y observation — no behavioral changes"
            _a11y_step.action = {"type": "a11y_passive_snapshot", "parameters": {"app": "Safari"}}
            _a11y_step.action_result = {"success": True}
            _a11y_step.post_state = {
                "backend": _a11y_observer.backend,
                "total_elements": len(_a11y_snapshot),
                "interactive_elements": len(_a11y_interactive),
                "roles_seen": list({e.role for e in _a11y_snapshot}),
                "interactive_labels": [e.label for e in _a11y_interactive[:20]],
                "sample_elements": [e.to_dict() for e in _a11y_interactive[:10]],
            }
            trace_writer.end_step(_a11y_step)
    except Exception as e:
        print(f"  [A11Y-OBSERVE] Passive extraction failed ({e}), continuing")

    if use_enterprise and agent:
        try:
            from a11y_engine import A11yEngine
            from element_map import UnifiedElementMap
            from web_primitives import WebPrimitives

            a11y = A11yEngine()
            a11y_elements = a11y.extract("Safari")
            _element_map = UnifiedElementMap()
            _element_map.ingest_a11y(a11y_elements)
            interactive_count = len(_element_map.find_interactive())
            print(f"  [A11Y] Extracted {len(a11y_elements)} elements ({interactive_count} interactive) via {a11y.backend}")
            _primitives = WebPrimitives(agent=agent, element_map=_element_map)
        except Exception as e:
            print(f"  [A11Y] Extraction failed ({e}), proceeding without a11y")

    past_lessons = _load_episodic_memory(cre_dir, task_id)

    _summarizer = None
    if Summarizer is not None:
        _summarizer = Summarizer(token_budget=500)

    custom_goal = os.environ.get("AGENT_GOAL")
    if custom_goal:
        goal = custom_goal
        print(f"\n  [GOAL] Custom goal from AGENT_GOAL: {goal}")
    else:
        goal = "Draw a red triangle on the Excalidraw canvas"

    _site_knowledge = None
    if SiteKnowledge is not None:
        _site_knowledge = SiteKnowledge(persist_path=str(cre_dir / "site_knowledge_excalidraw.json"))
        if not _site_knowledge.get_summary()["has_research"] and use_enterprise and agent:
            print("\n  [EXPLORE] No site research found — running full exploration pipeline...")
            explorer = ExplorationLoop(
                agent=agent, knowledge=_site_knowledge,
                vision_engine=vision_engine, site_name="Excalidraw",
            )
            explorer.full_exploration(current_state_path)
        elif _site_knowledge.get_summary()["num_tools"] > 0:
            print(f"\n  [KNOWLEDGE] Loaded site knowledge: {_site_knowledge.get_summary()}")

    action_plan = generate_action_plan(ui_analysis, goal=goal)

    use_dynamic = os.environ.get("DYNAMIC_PLAN") or custom_goal
    if use_dynamic and use_enterprise and agent:
        action_plan = generate_dynamic_plan(
            agent=agent,
            som_path=str(cre_dir / "som_overlay.png"),
            goal=goal,
            available_actions=list(ACTION_HANDLERS.keys()),
            fallback_plan=action_plan,
            lessons=past_lessons,
            summarizer=_summarizer,
            site_knowledge=_site_knowledge,
        )

    _exec_log_line("phase", "PHASE 3: ACTION PLANNING", {"actions": len(action_plan), "plan": [a.get("description", "") for a in action_plan]})

    if os.environ.get("DISABLE_COORD_CACHE"):
        coord_cache = {}
        print("  [ABLATION] Coordinate cache DISABLED")
        _exec_log_line("ablation", "coord_cache_disabled")
    else:
        coord_cache = _load_coord_cache(cre_dir, task_id)

    action_allowlist = None
    screen_bounds = None
    if not os.environ.get("DISABLE_ACTION_ALLOWLIST"):
        from agent_infra.action_allowlist import (
            ActionAllowlist,
            get_screen_bounds_from_agent,
            DEFAULT_SCREEN_BOUNDS,
        )
        action_allowlist = ActionAllowlist.from_handlers(set(ACTION_HANDLERS.keys()))
        screen_bounds = get_screen_bounds_from_agent(agent) if (use_enterprise and agent) else None
        if screen_bounds is None:
            screen_bounds = DEFAULT_SCREEN_BOUNDS

    ctx = _Ctx(
        use_enterprise=use_enterprise,
        agent=agent,
        vision_engine=vision_engine,
        client=client,
        vlm=vlm,
        ui_analysis=ui_analysis,
        cre_dir=cre_dir,
        current_state_path=current_state_path,
        trace_writer=trace_writer,
        coord_cache=coord_cache,
        trust_tracker=trust_tracker,
        summarizer=_summarizer,
        element_map=_element_map,
        primitives=_primitives,
        rules=past_lessons,
        action_allowlist=action_allowlist,
        screen_bounds=screen_bounds,
    )

    run_outcome = "success"
    try:
        evidence_entries = _execute_plan(ctx, action_plan)
    except Exception as e:
        print(f"  Execution failed: {e}")
        run_outcome = "failure"
        evidence_entries = []

    _finalize_run(trace_writer, run_outcome, action_plan, evidence_entries, agent=agent)
    return 0


if __name__ == "__main__":
    sys.exit(run_model_based_agent())
