#!/usr/bin/env python3
"""
Enterprise-grade macOS GUI agent core.

Implements:
- NSWorkspace state management (<1ms focus verification)
- Gemini File API for high-resolution screenshots (no local Base64 bloat)
- Pydantic structured outputs (constrained decoding, no regex)
- Quartz global coordinates (multi-monitor support)
"""

from __future__ import annotations

import json
import os
import time
import logging
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from window_capture import get_frontmost_application_name as get_visible_frontmost_application_name

# #region agent log
def _trace(loc: str, msg: str, data: dict | None = None):
    try:
        with open("/Users/christianpardo/rust/.cursor/debug-a16689.log", "a") as f:
            f.write(json.dumps({"sessionId": "a16689", "location": loc, "message": msg, "data": data or {}, "timestamp": int(time.time() * 1000)}) + "\n")
    except Exception:
        pass


def _debug_log(location: str, message: str, data: dict, hypothesis_id: str | list[str]):
    try:
        _dir = os.path.join(os.path.dirname(__file__), "cre")
        _path = os.path.join(_dir, "debug-a16689.log")
        if not os.path.isdir(_dir):
            _path = os.path.join(os.environ.get("TMPDIR", "/tmp"), "debug-a16689.log")
        payload = {"sessionId": "a16689", "hypothesisId": hypothesis_id, "location": location, "message": message, "data": data, "timestamp": int(time.time() * 1000)}
        with open(_path, "a") as f:
            f.write(json.dumps(payload) + "\n")
    except Exception:
        pass


def _exec_log(event: str, detail: str | None = None, data: dict | None = None):
    """Append one line to the session execution log (when EXECUTION_LOG_PATH is set)."""
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
# #endregion

try:
    import Quartz
    from AppKit import (
        NSWorkspace,
        NSScreen,
        NSApplicationActivateAllWindows,
        NSApplicationActivateIgnoringOtherApps,
    )
    from Cocoa import NSRunningApplication
except ImportError:
    raise ImportError(
        "Critical Dependency Missing: pip install pyobjc-framework-Cocoa pyobjc-framework-Quartz"
    )

logger = logging.getLogger(__name__)


def pixel_to_global_from_capture(
    pixel_x: float,
    pixel_y: float,
    *,
    scale_factor: float,
    screen_origin: tuple[float, float] = (0.0, 0.0),
    capture_origin: tuple[float, float] | None = None,
) -> tuple[float, float]:
    """Convert screenshot-local pixels into global logical coordinates.

    When the screenshot is a full-display capture, ``capture_origin`` is
    omitted and the pixel origin is the primary-screen origin. When the
    screenshot is a front-window capture, ``capture_origin`` must be the
    window's logical top-left so the posted HID event lands on the same
    visual surface the screenshot came from.
    """
    logical_x = pixel_x / scale_factor
    logical_y = pixel_y / scale_factor
    origin_x, origin_y = capture_origin if capture_origin is not None else screen_origin
    return (origin_x + logical_x, origin_y + logical_y)


class TargetExtraction(BaseModel):
    """Pydantic schema for constrained VLM output. Eliminates regex parsing."""

    target_box_id: int = Field(
        description="The exact integer ID of the bounding box containing the user's requested target element."
    )


class UIAnalysis(BaseModel):
    """Structured UI analysis for Excalidraw (canvas center, etc.)."""

    canvas_center_x: int = Field(description="X coordinate of the canvas center in image pixels.")
    canvas_center_y: int = Field(description="Y coordinate of the canvas center in image pixels.")
    page_loaded: bool = Field(description="True if the page appears fully loaded.")


class VisualAssertionResult(BaseModel):
    """Strict YES/NO answer for visual state verification. Prevents VLM hallucination."""

    answer: str = Field(description="Exactly one of: YES or NO.")


class GradedAssertionResult(BaseModel):
    """Structured grading for complex visual assertions.

    Extends the agent's verification capability beyond binary YES/NO to handle
    spatial relations, partial matches, multi-element states, and temporal
    conditions where VLM hallucination rates rise 12-22% (VisualWebArena,
    Koh et al., 2024; GhostEI-Bench, arXiv:2510.20333v2).

    Separate from VisualAssertionResult to avoid forking existing consumers.
    The inference router always selects Pro for graded assertions (complex
    reasoning requires higher-capability models).

    Trust tracker integration: verdict + confidence map to binary signals
    via a threshold (confidence >= GRADED_TRUST_THRESHOLD counts as success).
    This preserves PAC-Bayes invariants while giving richer demotion signals
    for unreliable assertions that happen to be technically correct.
    """

    verdict: str = Field(description="Exactly one of: PASS, FAIL, or PARTIAL.")
    confidence: int = Field(
        ge=0, le=5,
        description="Confidence in the verdict from 0 (no confidence) to 5 (certain).",
    )
    rationale: str = Field(
        max_length=200,
        description="Brief explanation of the verdict and any evidence observed.",
    )
    evidence_regions: list[str] = Field(
        default_factory=list,
        description="SoM zone IDs or bounding box descriptions supporting the verdict.",
    )


GRADED_TRUST_THRESHOLD = 4


class PreClickConfirmationResult(BaseModel):
    """Structured go/no-go judgment before a risky GUI click.

    This is intentionally narrower than a general page-analysis schema.
    It answers one question: should the agent click *here* *now*?
    """

    approved: bool = Field(
        description="True only if the cursor appears over the intended target, no blocking UI is visible, and the expected effect is plausible."
    )
    target_under_cursor: bool = Field(
        description="True if the screenshot suggests the cursor is over the intended target."
    )
    blockers_present: bool = Field(
        description="True if a popup, dialog, overlay, or obvious conflicting state could make the click unsafe."
    )
    expected_effect_likely: bool = Field(
        description="True if the intended click is likely to produce the expected effect in the current state."
    )
    confidence: int = Field(
        ge=0, le=5,
        description="Confidence from 0 (low) to 5 (certain).",
    )
    rationale: str = Field(
        max_length=240,
        description="Short explanation of the decision and any visible risk.",
    )
    suggested_action: str = Field(
        max_length=120,
        description="Short recommended next move if the click should not proceed.",
    )


class ColoredDot(BaseModel):
    """One colored dot on the canvas (e.g. red, blue, green, orange)."""

    color: str = Field(description="Color of the dot: one of red, blue, green, orange.")
    x: int = Field(description="X pixel coordinate of the dot center in the screenshot.")
    y: int = Field(description="Y pixel coordinate of the dot center in the screenshot.")


class ColoredDotsResponse(BaseModel):
    """List of colored dots detected in the screenshot."""

    dots: list[ColoredDot] = Field(
        default_factory=list,
        description="All colored dots found, each with color and x,y pixel coordinates.",
    )


class MacOSAgentCore:
    """
    Enterprise-grade macOS agent: deterministic state management,
    File API visual reasoning, and hardware-agnostic execution.
    """

    def __init__(self, router=None) -> None:
        self.api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise RuntimeError(
                "GEMINI_API_KEY or OPENAI_API_KEY environment variable not set."
            )
        self.client = genai.Client(api_key=self.api_key)
        self.workspace = NSWorkspace.sharedWorkspace()
        self._router = router

    def _model_for(self, task_type: str, default: str) -> str:
        """Route to the appropriate model via InferenceRouter, or use the default."""
        if self._router:
            return self._router.get_model_for(task_type)
        return default

    def _record_outcome(self, task_type: str, start_time: float, success: bool) -> None:
        """Report VLM call outcome to the router for adaptive learning."""
        if self._router and hasattr(self._router, "record_outcome"):
            latency_ms = int((time.time() - start_time) * 1000)
            self._router.record_outcome(task_type, latency_ms, success)

    @property
    def _client(self):
        """Alias so resilience-layer code (e.g. _diagnose_failure) can use ctx.agent._client."""
        return self.client

    @property
    def _gen_config_json(self):
        """Reusable config for free-form JSON responses (no Pydantic schema)."""
        return types.GenerateContentConfig(
            temperature=0.0,
            response_mime_type="application/json",
        )

    def get_frontmost_application_name(self) -> str:
        """Return the best visible frontmost-app signal available."""
        front = get_visible_frontmost_application_name()
        if front:
            return front
        workspace_front = self.workspace.frontmostApplication()
        return (workspace_front.localizedName() or "Unknown") if workspace_front else "Unknown"

    def enforce_app_focus(
        self,
        app_name: str = "Safari",
        timeout_seconds: float = 5.0,
        poll_interval: float = 0.05,
    ) -> bool:
        """
        Brings the given app to front and verifies it is frontmost.
        Uses NSRunningApplication.activateWithOptions(NSApplicationActivateIgnoringOtherApps)
        so the app is forced to front even when this script runs from another app (e.g. Cursor).
        Falls back to osascript if the app is not yet in runningApplications().
        """
        logger.info("Enforcing deterministic focus on '%s'...", app_name)
        app_name_lower = app_name.lower()
        activated = False
        for app in self.workspace.runningApplications():
            try:
                name = app.localizedName() or ""
                if app_name_lower in name.lower():
                    flags = NSApplicationActivateIgnoringOtherApps | NSApplicationActivateAllWindows
                    if app.activateWithOptions_(flags):
                        activated = True
                        break
            except Exception:
                continue
        if not activated:
            os.system(f'osascript -e \'tell application "{app_name}" to activate\'')

        start_time = time.time()
        while (time.time() - start_time) < timeout_seconds:
            current = self.get_frontmost_application_name()
            if current and app_name.lower() in current.lower():
                logger.info("State Verified: '%s' is frontmost.", app_name)
                # #region agent log
                _debug_log("agent_core.py:enforce_app_focus", "focus_verified", {"requested": app_name, "frontmost_exact": current}, ["H2", "H4"])
                # #endregion
                time.sleep(0.55)  # macOS: let window server finish focus handoff before posting input (H2)
                return True

            time.sleep(poll_interval)

        current = self.get_frontmost_application_name()
        raise RuntimeError(
            f"State Failure: Expected '{app_name}', but '{current}' is active. Halting."
        )

    def visually_extract_target(self, prompt_text: str, image_path: str) -> int:
        """
        Executes constrained decoding via Gemini 2.5 Pro using the File API
        to process full-resolution Retina screenshots without local memory bloat.
        Returns the integer target box ID from the SoM coordinate map.
        """
        # #region agent log
        _trace("agent_core.py:visually_extract_target", "entry", {"prompt": prompt_text[:60]})
        # #endregion
        logger.info("Uploading high-resolution screenshot to Gemini File API...")
        uploaded_file = None
        _t0 = time.time()

        try:
            uploaded_file = self.client.files.upload(file=image_path)
            logger.info("Upload complete. Remote URI established: %s", uploaded_file.uri)

            config = types.GenerateContentConfig(
                temperature=0.0,
                response_mime_type="application/json",
                response_schema=TargetExtraction,
            )

            logger.info("Executing constrained inference...")
            response = self.client.models.generate_content(
                model=self._model_for("extract_target", "gemini-2.5-pro"),
                contents=[prompt_text, uploaded_file],
                config=config,
            )

            extracted_data: TargetExtraction | None = response.parsed
            if extracted_data is None:
                self._record_outcome("extract_target", _t0, False)
                raise ValueError("API returned empty parsed data. Schema violation.")

            logger.info(
                "VLM mathematically resolved Target Box ID: %s",
                extracted_data.target_box_id,
            )
            self._record_outcome("extract_target", _t0, True)
            return extracted_data.target_box_id

        finally:
            if uploaded_file:
                logger.info("Purging remote file buffer...")
                try:
                    self.client.files.delete(name=uploaded_file.name)
                except Exception as e:
                    logger.warning("Failed to delete remote file %s: %s", uploaded_file.name, e)

    def analyze_ui(self, image_path: str) -> dict[str, int | bool]:
        """
        Analyzes UI from screenshot via File API with structured output.
        Returns dict with canvas_center_x, canvas_center_y, page_loaded.
        """
        logger.info("Uploading screenshot for UI analysis...")
        uploaded_file = None
        _t0 = time.time()
        try:
            uploaded_file = self.client.files.upload(file=image_path)
            prompt = """Analyze this Excalidraw interface screenshot.
Return the canvas center coordinates in image pixels and whether the page is fully loaded."""
            config = types.GenerateContentConfig(
                temperature=0.0,
                response_mime_type="application/json",
                response_schema=UIAnalysis,
            )
            response = self.client.models.generate_content(
                model=self._model_for("analyze_ui", "gemini-2.5-pro"),
                contents=[prompt, uploaded_file],
                config=config,
            )
            parsed: UIAnalysis | None = response.parsed
            if parsed is None:
                self._record_outcome("analyze_ui", _t0, False)
                raise ValueError("API returned empty parsed data.")
            self._record_outcome("analyze_ui", _t0, True)
            return {
                "canvas_center_x": parsed.canvas_center_x,
                "canvas_center_y": parsed.canvas_center_y,
                "page_loaded": parsed.page_loaded,
            }
        finally:
            if uploaded_file:
                try:
                    self.client.files.delete(name=uploaded_file.name)
                except Exception as e:
                    logger.warning("Failed to delete remote file: %s", e)

    def assert_visual_state(
        self, image_path: str, question: str,
        model: str = "gemini-2.0-flash",
    ) -> bool:
        """
        Visual state verification: ask VLM a YES/NO question about the screenshot.
        Returns True only if the VLM answers YES. Raises RuntimeError on NO (failsafe halt).
        Prevents zombie automation: do not proceed if the expected UI state is not present.

        Uses Gemini Flash by default for binary assertions (AOrchestra tiered
        model selection, arXiv:2602.03786). Falls back to Pro on ambiguous
        responses to maintain reliability.
        """
        _trace("agent_core.py:assert_visual_state", "entry", {"image_path": image_path, "question": question[:80], "model": model})
        logger.info("Visual assertion (%s): %s", model, question)
        uploaded_file = None
        _t0 = time.time()
        try:
            uploaded_file = self.client.files.upload(file=image_path)
            prompt = f"{question}\nReply with exactly one word: YES or NO."
            config = types.GenerateContentConfig(
                temperature=0.0,
                response_mime_type="application/json",
                response_schema=VisualAssertionResult,
            )
            response = self.client.models.generate_content(
                model=model,
                contents=[prompt, uploaded_file],
                config=config,
            )
            parsed: VisualAssertionResult | None = response.parsed
            if parsed is None:
                self._record_outcome("assert_visual_state", _t0, False)
                raise RuntimeError("Visual Assertion Failed: VLM returned no parseable answer.")
            answer = (parsed.answer or "").strip().upper()

            if answer not in ("YES", "NO") and model != "gemini-2.5-pro":
                self._record_outcome("assert_visual_state", _t0, False)
                fallback_model = self._model_for("assert_visual_state_fallback", "gemini-2.5-pro")
                _t0_fb = time.time()
                logger.info("Flash returned ambiguous %r, retrying with %s", answer, fallback_model)
                response = self.client.models.generate_content(
                    model=fallback_model,
                    contents=[prompt, uploaded_file],
                    config=config,
                )
                parsed = response.parsed
                if parsed is None:
                    self._record_outcome("assert_visual_state_fallback", _t0_fb, False)
                    raise RuntimeError("Visual Assertion Failed: VLM returned no parseable answer (Pro fallback).")
                answer = (parsed.answer or "").strip().upper()
                self._record_outcome("assert_visual_state_fallback", _t0_fb, answer in ("YES", "NO"))

            if answer == "NO":
                self._record_outcome("assert_visual_state", _t0, False)
                raise RuntimeError(f"Visual Assertion Failed: {question}")
            if answer != "YES":
                self._record_outcome("assert_visual_state", _t0, False)
                raise RuntimeError(f"Visual Assertion Failed: expected YES or NO, got {answer!r}")
            self._record_outcome("assert_visual_state", _t0, True)
            logger.info("Visual assertion passed: YES")
            return True
        finally:
            if uploaded_file:
                try:
                    self.client.files.delete(name=uploaded_file.name)
                except Exception as e:
                    logger.warning("Failed to delete remote file: %s", e)

    def grade_visual_state(
        self, image_path: str, assertion: str,
    ) -> GradedAssertionResult:
        """Structured grading for complex visual assertions.

        Unlike assert_visual_state (binary YES/NO), this returns a
        GradedAssertionResult with verdict (PASS/FAIL/PARTIAL), confidence
        (0-5), rationale, and evidence regions.  Always uses Pro model
        for the reasoning depth complex assertions require.

        Designed for assertions involving spatial relations between
        non-adjacent elements, negation with exceptions, temporal state,
        or partial success — cases where binary YES/NO error rates rise
        12-22% per GUI-agent benchmarks (VisualWebArena, GhostEI-Bench).

        Trust tracker integration: callers map confidence >= GRADED_TRUST_THRESHOLD
        to record_success(), < threshold to record_failure(). This preserves
        the PAC-Bayes safety invariant while enriching the demotion signal.

        Gated behind GRADED_ASSERTIONS=1 environment variable — callers
        check the flag and fall back to assert_visual_state when unset.
        """
        _trace("agent_core.py:grade_visual_state", "entry", {
            "image_path": image_path, "assertion": assertion[:80],
        })
        logger.info("Graded visual assertion (pro): %s", assertion[:80])
        uploaded_file = None
        _t0 = time.time()
        try:
            uploaded_file = self.client.files.upload(file=image_path)
            prompt = (
                f"Evaluate the following assertion about this screenshot:\n"
                f'  "{assertion}"\n\n'
                "Grade the assertion with:\n"
                "- verdict: PASS if fully true, FAIL if false, PARTIAL if partly true\n"
                "- confidence: 0 (no confidence) to 5 (certain)\n"
                "- rationale: brief explanation (max 200 chars)\n"
                "- evidence_regions: list of UI regions or SoM zone IDs supporting your verdict\n"
            )
            model = self._model_for("grade_visual_state", "gemini-2.5-pro")
            config = types.GenerateContentConfig(
                temperature=0.0,
                response_mime_type="application/json",
                response_schema=GradedAssertionResult,
            )
            response = self.client.models.generate_content(
                model=model,
                contents=[prompt, uploaded_file],
                config=config,
            )
            parsed: GradedAssertionResult | None = response.parsed
            if parsed is None:
                self._record_outcome("grade_visual_state", _t0, False)
                return GradedAssertionResult(
                    verdict="FAIL", confidence=0,
                    rationale="VLM returned no parseable graded result.",
                    evidence_regions=[],
                )

            parsed.verdict = parsed.verdict.strip().upper()
            if parsed.verdict not in ("PASS", "FAIL", "PARTIAL"):
                parsed.verdict = "FAIL"
                parsed.confidence = min(parsed.confidence, 1)

            success = parsed.verdict == "PASS" and parsed.confidence >= GRADED_TRUST_THRESHOLD
            self._record_outcome("grade_visual_state", _t0, success)

            _trace("agent_core.py:grade_visual_state", "result", {
                "verdict": parsed.verdict,
                "confidence": parsed.confidence,
                "rationale": parsed.rationale[:100],
            })
            logger.info(
                "Graded assertion: %s (confidence=%d) — %s",
                parsed.verdict, parsed.confidence, parsed.rationale[:60],
            )
            return parsed

        except Exception as e:
            self._record_outcome("grade_visual_state", _t0, False)
            logger.error("grade_visual_state failed: %s", e)
            return GradedAssertionResult(
                verdict="FAIL", confidence=0,
                rationale=f"Grading error: {str(e)[:150]}",
                evidence_regions=[],
            )
        finally:
            if uploaded_file:
                try:
                    self.client.files.delete(name=uploaded_file.name)
                except Exception as e:
                    logger.warning("Failed to delete remote file: %s", e)

    def detect_colored_dots(self, image_path: str) -> list[dict]:
        """
        Detect colored dots (red, blue, green, orange) in screenshot via VLM.
        Returns list of {"color": str, "x": int, "y": int} in screenshot pixel coords.
        """
        logger.info("Detecting colored dots in screenshot...")
        uploaded_file = None
        _t0 = time.time()
        try:
            uploaded_file = self.client.files.upload(file=image_path)
            prompt = """Look at this Excalidraw canvas screenshot. Find all small colored dots (red, blue, green, orange).
For each dot, report its color (exactly one of: red, blue, green, orange) and the pixel coordinates (x, y) of the center of the dot.
Return a list of objects in the "dots" array, each with keys: color, x, y. Use the full screenshot resolution for x,y."""
            config = types.GenerateContentConfig(
                temperature=0.0,
                response_mime_type="application/json",
                response_schema=ColoredDotsResponse,
            )
            response = self.client.models.generate_content(
                model=self._model_for("detect_colored_dots", "gemini-2.5-pro"),
                contents=[prompt, uploaded_file],
                config=config,
            )
            parsed: ColoredDotsResponse | None = response.parsed
            if parsed is None or not parsed.dots:
                self._record_outcome("detect_colored_dots", _t0, True)
                return []
            out = [{"color": d.color.strip().lower(), "x": d.x, "y": d.y} for d in parsed.dots]
            self._record_outcome("detect_colored_dots", _t0, True)
            logger.info("Detected %d colored dots", len(out))
            return out
        finally:
            if uploaded_file:
                try:
                    self.client.files.delete(name=uploaded_file.name)
                except Exception as e:
                    logger.warning("Failed to delete remote file: %s", e)

    def confirm_click_target(
        self,
        image_path: str,
        *,
        site_url: str = "",
        target_label: str = "",
        expected_effect: str = "",
        model: str = "gemini-2.0-flash",
        timeout_seconds: int = 15,
    ) -> PreClickConfirmationResult:
        """Judge whether a risky click should proceed based on a cursor-visible screenshot."""
        _trace(
            "agent_core.py:confirm_click_target",
            "entry",
            {
                "image_path": image_path,
                "site_url": site_url[:120],
                "target_label": target_label[:80],
                "expected_effect": expected_effect[:120],
                "model": model,
            },
        )
        logger.info("Pre-click confirmation (%s): target=%r effect=%r", model, target_label, expected_effect)
        _t0 = time.time()
        try:
            prompt = (
                "The screenshot includes the current cursor position.\n"
                "Reply YES only if all of the following are true:\n"
                f"1. The cursor is over the intended target: {target_label or 'the intended screen target'}.\n"
                "2. No modal, popup, overlay, or conflicting UI blocks the click.\n"
                f"3. Clicking now would likely cause this effect: {expected_effect or 'activate the intended target'}.\n"
                "Otherwise reply NO."
            )
            approved = self.assert_visual_state(
                image_path,
                prompt,
                model=self._model_for("confirm_click_target", model),
            )
            self._record_outcome("confirm_click_target", _t0, approved)
            logger.info(
                "Pre-click confirmation: approved=%s",
                approved,
            )
            return PreClickConfirmationResult(
                approved=approved,
                target_under_cursor=approved,
                blockers_present=not approved,
                expected_effect_likely=approved,
                confidence=4 if approved else 1,
                rationale=(
                    "Binary visual confirmation approved the click."
                    if approved
                    else "Binary visual confirmation did not approve the click."
                ),
                suggested_action=(
                    "Proceed with the click."
                    if approved
                    else "Re-capture the screen and verify the target again."
                ),
            )
        except Exception as e:
            self._record_outcome("confirm_click_target", _t0, False)
            logger.error("confirm_click_target failed: %s", e)
            return PreClickConfirmationResult(
                approved=False,
                target_under_cursor=False,
                blockers_present=True,
                expected_effect_likely=False,
                confidence=0,
                rationale=f"Confirmation error: {str(e)[:180]}",
                suggested_action="Re-capture the screen and retry confirmation.",
            )

    def _pixel_to_global_quartz(
        self,
        pixel_x: float,
        pixel_y: float,
        *,
        capture_origin: tuple[float, float] | None = None,
    ) -> tuple[float, float]:
        """
        Convert screenshot pixels to Quartz global coordinates.
        screencapture and CGEvent/CoreGraphics use top-left origin; scale to logical.
        """
        primary_screen = NSScreen.mainScreen()
        if primary_screen is None:
            raise RuntimeError("No primary screen available")
        scale_factor = primary_screen.backingScaleFactor()
        screen_frame = primary_screen.frame()
        return pixel_to_global_from_capture(
            pixel_x,
            pixel_y,
            scale_factor=scale_factor,
            screen_origin=(screen_frame.origin.x, screen_frame.origin.y),
            capture_origin=capture_origin,
        )

    def execute_global_click(
        self,
        local_pixel_x: int,
        local_pixel_y: int,
        app_focus: str | None = "Safari",
        *,
        capture_origin: tuple[float, float] | None = None,
    ) -> None:
        """
        Translates raw image pixels into global CoreGraphics coordinates and posts a click.
        JIT focus: coords and logging before enforce_app_focus; zero work between lock and post.
        """
        final_global_x, final_global_y = self._pixel_to_global_quartz(
            float(local_pixel_x),
            float(local_pixel_y),
            capture_origin=capture_origin,
        )
        logger.info(
            "Firing Quartz Native Click at Global [X:%s, Y:%s]",
            final_global_x,
            final_global_y,
        )
        _exec_log("click_prep", None, {"pixel": [local_pixel_x, local_pixel_y], "global": [round(final_global_x, 2), round(final_global_y, 2)]})
        if app_focus:
            self.enforce_app_focus(app_focus, timeout_seconds=2.0, poll_interval=0.05)
        try:
            _exec_log("click_post", "down_then_up", {"x": round(final_global_x, 2), "y": round(final_global_y, 2)})
            mouse_position = Quartz.CGPointMake(final_global_x, final_global_y)
            event_down = Quartz.CGEventCreateMouseEvent(
                None,
                Quartz.kCGEventLeftMouseDown,
                mouse_position,
                Quartz.kCGMouseButtonLeft,
            )
            event_up = Quartz.CGEventCreateMouseEvent(
                None,
                Quartz.kCGEventLeftMouseUp,
                mouse_position,
                Quartz.kCGMouseButtonLeft,
            )
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, event_down)
            time.sleep(0.05)
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, event_up)
        except Exception as e:
            logger.error("Execution Phase Failure: %s", e)
            raise

    def execute_move_mouse(
        self,
        local_pixel_x: int,
        local_pixel_y: int,
        app_focus: str | None = "Safari",
        *,
        capture_origin: tuple[float, float] | None = None,
    ) -> None:
        """
        Move the cursor to the given pixel coordinates without clicking.
        JIT focus: coords and logging before enforce_app_focus; then post move-only event.
        """
        final_global_x, final_global_y = self._pixel_to_global_quartz(
            float(local_pixel_x),
            float(local_pixel_y),
            capture_origin=capture_origin,
        )
        logger.info(
            "Moving mouse to Global [X:%s, Y:%s] (no click)",
            final_global_x,
            final_global_y,
        )
        _exec_log("move_mouse", None, {"pixel": [local_pixel_x, local_pixel_y], "global": [round(final_global_x, 2), round(final_global_y, 2)]})
        if app_focus:
            self.enforce_app_focus(app_focus, timeout_seconds=2.0, poll_interval=0.05)
        try:
            mouse_position = Quartz.CGPointMake(final_global_x, final_global_y)
            event_move = Quartz.CGEventCreateMouseEvent(
                None,
                Quartz.kCGEventMouseMoved,
                mouse_position,
                Quartz.kCGMouseButtonLeft,
            )
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, event_move)
        except Exception as e:
            logger.error("Move mouse failure: %s", e)
            raise

    # macOS ANSI virtual key codes (kVK_ANSI_*). Use lowercase keys for tools to avoid Shift+P.
    # Excalidraw: p/7=pen, S=stroke color, G=fill color. Do NOT use 0 (opens Live Collaboration).
    _KEYCHAR_TO_KEYCODE: dict[str | int, int] = {
        "p": 35, "P": 35,   # kVK_ANSI_P (Pen tool — send unmodified so it's lowercase)
        "b": 11, "B": 11,   # kVK_ANSI_B (Brush tool)
        "e": 14, "E": 14,   # kVK_ANSI_E (Eraser tool)
        "u": 32, "U": 32,   # kVK_ANSI_U (Kleki shape tool shortcut)
        "S": 1, "s": 1,     # kVK_ANSI_S (Stroke color picker / smudge tool on some sites)
        "G": 5, "g": 5,     # kVK_ANSI_G (Background color)
        "[": 33, "]": 30,   # Brush size shortcuts in apps that support them
        "0": 29, "1": 18, "2": 19, "3": 20, "4": 21, "5": 23, "6": 22, "7": 26, "8": 28, "9": 25,
        "V": 9, "v": 9, "R": 15, "O": 31, "A": 0, "a": 0, "L": 37, "T": 17, "I": 34,
    }

    _MODIFIER_FLAGS: dict[str, int] = {
        "cmd": getattr(Quartz, "kCGEventFlagMaskCommand", 0x100000),
        "control": getattr(Quartz, "kCGEventFlagMaskControl", 0x40000),
        "shift": getattr(Quartz, "kCGEventFlagMaskShift", 0x20000),
        "alt": getattr(Quartz, "kCGEventFlagMaskAlternate", 0x80000),
        "option": getattr(Quartz, "kCGEventFlagMaskAlternate", 0x80000),
    }

    def execute_keystroke(
        self,
        key: int | str,
        app_focus: str | None = "Safari",
        modifiers: list[str] | None = None,
    ) -> None:
        """
        Synthesizes a native macOS keyboard event using Quartz.
        Sends key with optional modifiers (e.g. modifiers=["cmd"] for Cmd+key).
        JIT focus: all prep (keycode, logging) before enforce_app_focus; zero work between lock and post.
        """
        # #region agent log
        _trace("agent_core.py:execute_keystroke", "entry", {"key": str(key), "app_focus": app_focus, "modifiers": modifiers})
        # #endregion
        keycode = int(key) if isinstance(key, int) else self._KEYCHAR_TO_KEYCODE.get(str(key), 35)
        flags = 0
        if modifiers:
            for m in modifiers:
                m_lower = (m or "").strip().lower()
                if m_lower in self._MODIFIER_FLAGS:
                    flags |= self._MODIFIER_FLAGS[m_lower]
        logger.info("Preparing Quartz keystroke (keycode=%s, modifiers=%s)...", keycode, modifiers)
        _debug_log("agent_core.py:execute_keystroke", "before_post_keystroke", {"key": str(key), "keycode": keycode, "flags": flags}, ["H1", "H2", "H5"])
        _exec_log("keystroke_prep", None, {"key": str(key), "keycode": keycode, "modifiers": modifiers})
        if app_focus:
            self.enforce_app_focus(app_focus, timeout_seconds=2.0, poll_interval=0.05)
        try:
            _exec_log("keystroke_post", "key_down")
            event_down = Quartz.CGEventCreateKeyboardEvent(None, keycode, True)
            event_up = Quartz.CGEventCreateKeyboardEvent(None, keycode, False)
            Quartz.CGEventSetFlags(event_down, flags)
            Quartz.CGEventSetFlags(event_up, flags)
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, event_down)
            time.sleep(0.05)
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, event_up)
            _exec_log("keystroke_post", "key_up")
        except Exception as e:
            logger.error("Native keystroke failure: %s", e)
            _exec_log("keystroke_error", str(e))
            raise

    def execute_clear_canvas(self, app_focus: str | None = "Safari") -> None:
        """
        Sends Command+Backspace to clear the Excalidraw canvas (Mac shortcut).
        Call with Safari focused so the key combo is received by the canvas.
        """
        # #region agent log
        _trace("agent_core.py:execute_clear_canvas", "entry", {"app_focus": app_focus})
        # #endregion
        # kVK_Delete (Backspace) = 51; Command = kCGEventFlagMaskCommand = 0x100000
        keycode = 51
        flags = getattr(Quartz, "kCGEventFlagMaskCommand", 0x100000)
        _exec_log("clear_canvas_prep", None, {"keycode": keycode, "flags_hex": hex(flags)})
        if app_focus:
            self.enforce_app_focus(app_focus, timeout_seconds=2.0, poll_interval=0.05)
        try:
            event_down = Quartz.CGEventCreateKeyboardEvent(None, keycode, True)
            event_up = Quartz.CGEventCreateKeyboardEvent(None, keycode, False)
            Quartz.CGEventSetFlags(event_down, flags)
            Quartz.CGEventSetFlags(event_up, flags)
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, event_down)
            time.sleep(0.05)
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, event_up)
            _exec_log("clear_canvas_post", "ok")
        except Exception as e:
            logger.error("Clear canvas (Cmd+Backspace) failure: %s", e)
            _exec_log("clear_canvas_error", str(e))
            raise

    def execute_draw_path(
        self,
        path_coordinates: list[tuple[int, int]],
        center_x: int,
        center_y: int,
        app_focus: str | None = "Safari",
        drag_delay: float = 0.02,
        capture_origin: tuple[float, float] | None = None,
    ) -> None:
        """
        Executes a native click-and-drag drawing motion using Quartz.
        path_coordinates: list of relative (x, y) offsets from canvas center (image pixels).
        drag_delay: seconds between each mouse_dragged event (higher = slower stroke; helps canvas sample at 60Hz).
        JIT focus: all coordinate math and logging before enforce_app_focus; zero work between lock and post.
        """
        if not path_coordinates:
            return
        global_points: list[tuple[float, float]] = []
        for px, py in path_coordinates:
            gx, gy = self._pixel_to_global_quartz(
                float(center_x + px),
                float(center_y + py),
                capture_origin=capture_origin,
            )
            global_points.append((gx, gy))
        start_x, start_y = global_points[0]
        logger.info(
            "Math complete. Firing Quartz draw path [drag_delay=%.3fs] at global [X:%s, Y:%s]...",
            drag_delay, start_x, start_y,
        )
        _debug_log("agent_core.py:execute_draw_path", "before_post_draw_path", {"center_x": center_x, "center_y": center_y, "num_points": len(global_points), "drag_delay": drag_delay}, ["H1", "H2", "H5"])
        _exec_log("draw_path_prep", None, {"center_x": center_x, "center_y": center_y, "drag_delay": drag_delay, "relative_path": path_coordinates, "global_points": [[round(gx, 2), round(gy, 2)] for gx, gy in global_points]})
        if app_focus:
            self.enforce_app_focus(app_focus, timeout_seconds=2.0, poll_interval=0.05)
        try:
            _exec_log("draw_path_event", "mouse_down", {"x": start_x, "y": start_y})
            start_point = Quartz.CGPointMake(start_x, start_y)
            event_down = Quartz.CGEventCreateMouseEvent(
                None, Quartz.kCGEventLeftMouseDown, start_point, Quartz.kCGMouseButtonLeft
            )
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, event_down)
            time.sleep(0.15)  # Let canvas register pen-down before first drag
            for idx, (gx, gy) in enumerate(global_points[1:], 1):
                _exec_log("draw_path_event", "mouse_dragged", {"index": idx, "x": gx, "y": gy})
                drag_point = Quartz.CGPointMake(gx, gy)
                event_drag = Quartz.CGEventCreateMouseEvent(
                    None, Quartz.kCGEventLeftMouseDragged, drag_point, Quartz.kCGMouseButtonLeft
                )
                Quartz.CGEventPost(Quartz.kCGHIDEventTap, event_drag)
                time.sleep(drag_delay)
            end_x, end_y = global_points[-1]
            _exec_log("draw_path_event", "mouse_up", {"x": end_x, "y": end_y})
            event_up = Quartz.CGEventCreateMouseEvent(
                None, Quartz.kCGEventLeftMouseUp,
                Quartz.CGPointMake(end_x, end_y),
                Quartz.kCGMouseButtonLeft,
            )
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, event_up)
            time.sleep(0.5)  # Let canvas finalize stroke before next action or screenshot
            _exec_log("draw_path_done", None, {"points_posted": len(global_points), "drag_delay": drag_delay})
        except Exception as e:
            logger.error("Native draw path failure: %s", e)
            _exec_log("draw_path_error", str(e))
            raise

    def execute_draw_path_with_modifier(
        self,
        path_coordinates: list[tuple[int, int]],
        center_x: int,
        center_y: int,
        *,
        modifier: str = "shift",
        app_focus: str | None = "Safari",
        drag_delay: float = 0.02,
        capture_origin: tuple[float, float] | None = None,
    ) -> None:
        """Execute a drag path while holding a keyboard modifier.

        This is primarily used for Kleki's documented Shift-draw line mode.
        """
        if len(path_coordinates) < 2:
            return

        modifier = (modifier or "shift").strip().lower()
        modifier_keycode = {
            "shift": 56,   # kVK_Shift
        }.get(modifier)
        modifier_flag = {
            "shift": getattr(Quartz, "kCGEventFlagMaskShift", 0x20000),
        }.get(modifier, 0)
        if modifier_keycode is None or modifier_flag == 0:
            self.execute_draw_path(
                path_coordinates,
                center_x,
                center_y,
                app_focus=app_focus,
                drag_delay=drag_delay,
                capture_origin=capture_origin,
            )
            return

        global_points: list[tuple[float, float]] = []
        for px, py in path_coordinates:
            gx, gy = self._pixel_to_global_quartz(
                float(center_x + px),
                float(center_y + py),
                capture_origin=capture_origin,
            )
            global_points.append((gx, gy))

        if app_focus:
            self.enforce_app_focus(app_focus, timeout_seconds=2.0, poll_interval=0.05)

        try:
            modifier_down = Quartz.CGEventCreateKeyboardEvent(None, modifier_keycode, True)
            modifier_up = Quartz.CGEventCreateKeyboardEvent(None, modifier_keycode, False)
            Quartz.CGEventSetFlags(modifier_down, modifier_flag)
            Quartz.CGEventSetFlags(modifier_up, 0)
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, modifier_down)
            time.sleep(0.05)

            start_x, start_y = global_points[0]
            start_point = Quartz.CGPointMake(start_x, start_y)
            event_down = Quartz.CGEventCreateMouseEvent(
                None, Quartz.kCGEventLeftMouseDown, start_point, Quartz.kCGMouseButtonLeft
            )
            Quartz.CGEventSetFlags(event_down, modifier_flag)
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, event_down)
            time.sleep(0.15)

            for gx, gy in global_points[1:]:
                drag_point = Quartz.CGPointMake(gx, gy)
                event_drag = Quartz.CGEventCreateMouseEvent(
                    None, Quartz.kCGEventLeftMouseDragged, drag_point, Quartz.kCGMouseButtonLeft
                )
                Quartz.CGEventSetFlags(event_drag, modifier_flag)
                Quartz.CGEventPost(Quartz.kCGHIDEventTap, event_drag)
                time.sleep(drag_delay)

            end_x, end_y = global_points[-1]
            event_up = Quartz.CGEventCreateMouseEvent(
                None, Quartz.kCGEventLeftMouseUp,
                Quartz.CGPointMake(end_x, end_y),
                Quartz.kCGMouseButtonLeft,
            )
            Quartz.CGEventSetFlags(event_up, modifier_flag)
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, event_up)
            time.sleep(0.2)
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, modifier_up)
            time.sleep(0.3)
        except Exception as e:
            logger.error("Modified draw path failure: %s", e)
            _exec_log("draw_path_with_modifier_error", str(e))
            try:
                modifier_up = Quartz.CGEventCreateKeyboardEvent(None, modifier_keycode, False)
                Quartz.CGEventSetFlags(modifier_up, 0)
                Quartz.CGEventPost(Quartz.kCGHIDEventTap, modifier_up)
            except Exception:
                pass
            raise

    def execute_draw_path_segments(
        self,
        path_coordinates: list[tuple[int, int]],
        center_x: int,
        center_y: int,
        app_focus: str | None = "Safari",
        drag_delay: float = 0.02,
        capture_origin: tuple[float, float] | None = None,
    ) -> None:
        """
        Draws a polygon by releasing the mouse at every corner (one segment per edge).
        path_coordinates: list of relative (x, y) vertices (image pixels). Polygon is closed (last to first).
        Each segment: mouse_down at A, drag to B, mouse_up at B; then next segment from B to C, etc.
        """
        # #region agent log
        _trace("agent_core.py:execute_draw_path_segments", "entry", {"center": [center_x, center_y], "vertices": len(path_coordinates)})
        # #endregion
        if len(path_coordinates) < 2:
            return
        global_points: list[tuple[float, float]] = []
        for px, py in path_coordinates:
            gx, gy = self._pixel_to_global_quartz(
                float(center_x + px),
                float(center_y + py),
                capture_origin=capture_origin,
            )
            global_points.append((gx, gy))
        n = len(global_points)
        logger.info(
            "Firing draw path (segments: release at each corner) [%d vertices] at center (%s, %s)...",
            n, center_x, center_y,
        )
        _exec_log("draw_path_segments_prep", None, {"center_x": center_x, "center_y": center_y, "num_vertices": n})
        if app_focus:
            self.enforce_app_focus(app_focus, timeout_seconds=2.0, poll_interval=0.05)
        try:
            for i in range(n):
                j = (i + 1) % n
                ax, ay = global_points[i]
                bx, by = global_points[j]
                _exec_log("draw_path_segment", "mouse_down", {"segment": i, "x": ax, "y": ay})
                event_down = Quartz.CGEventCreateMouseEvent(
                    None, Quartz.kCGEventLeftMouseDown,
                    Quartz.CGPointMake(ax, ay),
                    Quartz.kCGMouseButtonLeft,
                )
                Quartz.CGEventPost(Quartz.kCGHIDEventTap, event_down)
                time.sleep(0.15)
                _exec_log("draw_path_segment", "mouse_dragged", {"segment": i, "x": bx, "y": by})
                event_drag = Quartz.CGEventCreateMouseEvent(
                    None, Quartz.kCGEventLeftMouseDragged,
                    Quartz.CGPointMake(bx, by),
                    Quartz.kCGMouseButtonLeft,
                )
                Quartz.CGEventPost(Quartz.kCGHIDEventTap, event_drag)
                time.sleep(drag_delay)
                _exec_log("draw_path_segment", "mouse_up", {"segment": i, "x": bx, "y": by})
                event_up = Quartz.CGEventCreateMouseEvent(
                    None, Quartz.kCGEventLeftMouseUp,
                    Quartz.CGPointMake(bx, by),
                    Quartz.kCGMouseButtonLeft,
                )
                Quartz.CGEventPost(Quartz.kCGHIDEventTap, event_up)
                time.sleep(0.1)
            _exec_log("draw_path_segments_done", None, {"segments": n})
        except Exception as e:
            logger.error("Native draw path segments failure: %s", e)
            _exec_log("draw_path_segments_error", str(e))
            raise

    def get_screen_info(self) -> dict[str, int | float]:
        """
        Returns logical dimensions and scale factor from NSScreen (kernel-free).
        Keys: logical_width, logical_height, scale_factor.
        """
        primary_screen = NSScreen.mainScreen()
        if primary_screen is None:
            return {"logical_width": 1440, "logical_height": 900, "scale_factor": 2.0}
        frame = primary_screen.frame()
        scale = primary_screen.backingScaleFactor()
        return {
            "logical_width": int(frame.size.width),
            "logical_height": int(frame.size.height),
            "scale_factor": scale,
        }
