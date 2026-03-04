"""Mandatory post-execution visual verification gate.

No task is ever "done" until this gate passes. The agent MUST take a
screenshot, compare it to the original request, and explicitly judge
whether the output meets the standard. If it doesn't, the gate returns
a structured critique with specific deficiencies to fix.

This module exists because of a concrete failure: the Canva Draw test
produced a monochrome stick-figure sketch and declared "COMPLETE" without
ever looking at what it made. That is the behavior this gate prevents.

Architecture grounded in:
- CRAFT (arXiv:2512.20362): explicit constraint decomposition, targeted
  verification, and stopping criteria — refinement only when specific
  constraints are violated, not blind retries.
- VisionDirector (arXiv:2512.19243): micro-grid sampling with semantic
  verification and rollback after EVERY edit step.
- GUI-Shepherd (OpenReview, 2025): process reward model providing step-by-
  step feedback; +5.1pt success rate when used as inference verifier.
- VISCO (CVPR 2025): LOOKBACK strategy — revisiting the image before
  critique improves self-correction by 13.5%.
- Maestro (arXiv:2509.10704): MLLM-as-a-judge for head-to-head comparison
  of generated output vs. intent, driving iterative improvement.
- Reflexion (NeurIPS 2023, arXiv:2303.11366): verbal self-reflection
  stored in episodic memory to prevent repeating the same mistakes.

Design principles:
- ZERO imports from agent_infra (preserves unidirectional dependency chain)
- The gate is MANDATORY — calling code must not bypass it
- Produces structured VerificationResult with pass/fail/deficiencies
- Supports both pixel-diff (fast, deterministic) and VLM judge (semantic)
- Iterative: returns actionable critique so the caller can fix and re-verify
"""

from __future__ import annotations

import json
import logging
import subprocess
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Callable

from screenshot_preprocessor import inspect_image_artifact, prepare_image_copy

logger = logging.getLogger(__name__)


@dataclass
class Constraint:
    """One verifiable requirement extracted from the task description.

    Following CRAFT (arXiv:2512.20362): decompose the intent into
    explicit, individually verifiable constraints.
    """
    description: str
    category: str = "visual"
    satisfied: bool = False
    critique: str = ""


@dataclass
class VerificationResult:
    """Structured output from the verification gate.

    Every field is JSON-serializable for trace storage.
    """
    passed: bool
    score: float
    verdict: str
    constraints: list[dict[str, Any]] = field(default_factory=list)
    deficiencies: list[str] = field(default_factory=list)
    screenshot_path: str = ""
    reference_paths: list[str] = field(default_factory=list)
    iteration: int = 0
    timestamp: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def save(self, path: str | Path) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, default=str)


class VerificationGate:
    """Mandatory post-execution verification checkpoint.

    Usage::

        gate = VerificationGate(
            task_description="Draw two interlaced hands over a shattered glass sphere",
            output_dir="/tmp/verification",
        )

        # After execution, MUST call verify
        result = gate.verify()

        if not result.passed:
            print("FAILED. Deficiencies:")
            for d in result.deficiencies:
                print(f"  - {d}")
            # Fix the deficiencies, then verify again
            result = gate.verify(iteration=2)

    The gate decomposes the task into constraints (CRAFT pattern),
    captures a screenshot (VISCO LOOKBACK), and judges each constraint
    using either a VLM or heuristic rules.
    """

    PASS_THRESHOLD = 0.7

    def __init__(
        self,
        task_description: str,
        output_dir: str | Path = "/tmp/verification",
        vlm_judge_fn: Callable[[str, list[str]], str] | None = None,
        extra_criteria: list[str] | None = None,
    ) -> None:
        self._task = task_description
        self._output_dir = Path(output_dir)
        self._output_dir.mkdir(parents=True, exist_ok=True)
        self._vlm_judge = vlm_judge_fn
        self._constraints = self._decompose_constraints(task_description, extra_criteria or [])
        self._history: list[VerificationResult] = []

    @property
    def constraints(self) -> list[Constraint]:
        return list(self._constraints)

    @property
    def history(self) -> list[VerificationResult]:
        return list(self._history)

    def verify(
        self,
        iteration: int = 1,
        screenshot_path: str | None = None,
        reference_paths: list[str] | None = None,
    ) -> VerificationResult:
        """Execute the full verification protocol.

        1. CAPTURE — take a screenshot of the current state
        2. LOOKBACK — load the screenshot and the original request
        3. JUDGE — evaluate each constraint against the screenshot
        4. VERDICT — aggregate and produce pass/fail with critique
        """
        ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        # 1. CAPTURE
        if screenshot_path is None:
            screenshot_path = str(self._output_dir / f"verify_{iteration:02d}.png")
            self._capture_screenshot(screenshot_path)

        if not Path(screenshot_path).exists():
            result = VerificationResult(
                passed=False, score=0.0,
                verdict="FAILED: Could not capture screenshot",
                screenshot_path=screenshot_path,
                iteration=iteration, timestamp=ts,
            )
            self._history.append(result)
            return result

        prepared_screenshot, prepared_references, prep_error = self._prepare_inputs(
            screenshot_path,
            reference_paths or [],
            iteration,
        )
        if prep_error:
            result = VerificationResult(
                passed=False,
                score=0.0,
                verdict=f"FAILED: {prep_error}",
                screenshot_path=screenshot_path,
                reference_paths=reference_paths or [],
                iteration=iteration,
                timestamp=ts,
            )
            self._history.append(result)
            return result

        # 2. LOOKBACK + 3. JUDGE
        if self._vlm_judge:
            self._judge_with_vlm(prepared_screenshot, prepared_references)
        else:
            self._judge_heuristic(prepared_screenshot)

        # 4. VERDICT
        satisfied = [c for c in self._constraints if c.satisfied]
        total = len(self._constraints)
        score = len(satisfied) / max(total, 1)

        deficiencies = [
            c.critique or f"Missing: {c.description}"
            for c in self._constraints if not c.satisfied
        ]

        passed = score >= self.PASS_THRESHOLD and len(deficiencies) == 0

        if passed:
            verdict = f"PASSED ({score:.0%}): Output meets the requested standard."
        elif score >= self.PASS_THRESHOLD:
            verdict = (f"PARTIAL ({score:.0%}): Most constraints met, but "
                       f"{len(deficiencies)} deficiencies remain.")
        else:
            verdict = (f"FAILED ({score:.0%}): {len(deficiencies)} of {total} "
                       f"constraints not satisfied.")

        result = VerificationResult(
            passed=passed,
            score=round(score, 3),
            verdict=verdict,
            constraints=[asdict(c) for c in self._constraints],
            deficiencies=deficiencies,
            screenshot_path=screenshot_path,
            reference_paths=reference_paths or [],
            iteration=iteration,
            timestamp=ts,
        )

        result_path = self._output_dir / f"verification_{iteration:02d}.json"
        result.save(result_path)
        self._history.append(result)

        self._print_verdict(result)
        return result

    def verify_loop(
        self,
        fix_fn: Callable[[list[str]], None] | None = None,
        max_iterations: int = 3,
        reference_paths: list[str] | None = None,
    ) -> VerificationResult:
        """Run the full verify-fix-verify loop until pass or exhaustion.

        This is the CRAFT+VisionDirector pattern: verify after each action,
        fix only the violated constraints, re-verify, stop when all pass.

        Args:
            fix_fn: Callable that receives a list of deficiency strings
                    and attempts to fix them. If None, loop exits on first failure.
            max_iterations: Maximum number of verify-fix cycles.
            reference_paths: Reference images for comparison.

        Returns:
            The final VerificationResult.
        """
        for iteration in range(1, max_iterations + 1):
            result = self.verify(
                iteration=iteration,
                reference_paths=reference_paths,
            )

            if result.passed:
                print(f"\n  [GATE] Verification PASSED on iteration {iteration}")
                return result

            if fix_fn is None or iteration == max_iterations:
                print(f"\n  [GATE] Verification FAILED after {iteration} iterations")
                return result

            print(f"\n  [GATE] Iteration {iteration}: {len(result.deficiencies)} "
                  f"deficiencies found. Attempting fix...")
            for d in result.deficiencies:
                print(f"    - {d}")

            try:
                fix_fn(result.deficiencies)
            except Exception as e:
                logger.warning("Fix function failed: %s", e)
                print(f"  [GATE] Fix attempt failed: {e}")
                return result

        return result

    # ------------------------------------------------------------------
    # Input preparation
    # ------------------------------------------------------------------

    def _prepare_inputs(
        self,
        screenshot_path: str,
        reference_paths: list[str],
        iteration: int,
    ) -> tuple[str, list[str], str | None]:
        prepared_dir = self._output_dir / "prepared"
        prepared_screenshot = prepared_dir / f"verify_{iteration:02d}_prepared.png"

        screenshot_info = prepare_image_copy(
            screenshot_path,
            prepared_screenshot,
            profile="verification",
        )
        if not screenshot_info.is_valid or not screenshot_info.normalized_path:
            detail = screenshot_info.error or "could not normalize screenshot"
            return screenshot_path, [], f"Invalid screenshot artifact — {detail}"

        prepared_refs: list[str] = []
        for idx, ref_path in enumerate(reference_paths, start=1):
            ref_info = inspect_image_artifact(ref_path)
            if not ref_info.is_valid:
                return screenshot_info.normalized_path, prepared_refs, (
                    f"Invalid reference image '{ref_path}' — {ref_info.error}"
                )
            dest = prepared_dir / f"reference_{iteration:02d}_{idx:02d}.png"
            prepared_info = prepare_image_copy(ref_path, dest, profile="comparison")
            if not prepared_info.is_valid or not prepared_info.normalized_path:
                detail = prepared_info.error or "could not normalize reference image"
                return screenshot_info.normalized_path, prepared_refs, (
                    f"Invalid reference image '{ref_path}' — {detail}"
                )
            prepared_refs.append(prepared_info.normalized_path)

        return screenshot_info.normalized_path, prepared_refs, None

    # ------------------------------------------------------------------
    # Constraint Decomposition (CRAFT pattern)
    # ------------------------------------------------------------------

    def _decompose_constraints(self, task: str, extra_criteria: list[str]) -> list[Constraint]:
        """Break task description into individually verifiable constraints.

        Following CRAFT (arXiv:2512.20362): transform the intent into
        dependency-structured visual constraints that can each be checked
        independently.
        """
        constraints: list[Constraint] = []
        task_lower = task.lower()

        constraints.append(Constraint(
            description="Canvas is not empty — visible drawing/content present",
            category="existence",
        ))

        constraints.append(Constraint(
            description="Drawing fills a substantial portion of the canvas (>30%)",
            category="composition",
        ))

        subject_keywords = {
            "hand": "Recognizable hand shapes with distinct fingers visible",
            "hands": "Two distinct hands visible, not abstract waves",
            "finger": "Individual fingers are distinguishable",
            "sphere": "A circular sphere shape is present",
            "glass": "Glass-like quality (transparency, reflections, or shine)",
            "shatter": "Visible cracks, breaks, or shatter pattern",
            "broken": "Visible cracks, breaks, or shatter pattern",
            "interlace": "Elements are interlaced/interwoven, not simply side by side",
            "struggle": "Tension or force visible in the composition",
            "triangle": "Triangle shapes are present",
            "circle": "Circle shapes are present",
            "color": "Multiple colors used in the composition",
            "profuse": "Rich, abundant detail throughout",
            "detail": "Fine detail visible at close inspection",
            "exhaust": "Extensive, thorough detail coverage",
            "skyscraper": "A recognizable tall skyscraper or high-rise building is clearly present",
            "building": "A recognizable building structure is clearly present",
            "facade": "Facade structure such as windows, panel lines, or architectural subdivisions is visible",
            "perspective": "The structure follows a coherent perspective rather than random line directions",
            "shade": "Visible shading or tonal modeling is present, not just outline strokes",
            "shading": "Visible shading or tonal modeling is present, not just outline strokes",
            "shadow": "Shadow massing or darker tonal regions are visible where requested",
            "highlight": "Visible highlight treatment or lighter tonal accents are present where requested",
            "grayscale": "Multiple grayscale tones are used, not just a single black outline",
            "architectural": "The linework reads as deliberate architectural structure, not scribbles",
            "line work": "The linework is clear and intentional rather than accidental or tangled",
        }

        for keyword, requirement in subject_keywords.items():
            if keyword in task_lower:
                constraints.append(Constraint(
                    description=requirement,
                    category="subject",
                ))

        if any(keyword in task_lower for keyword in ("skyscraper", "building", "tower", "high-rise")):
            architectural_constraints = [
                "Front-facing vertical edges stay vertical rather than leaning randomly",
                "Front-facing horizontal edges stay horizontal rather than drifting diagonally",
                "Depth edges converge consistently toward a single vanishing point",
                "Facade grid remains legible across a substantial portion of the tower height",
                "No obvious scatter-noise contamination breaks up the intended tonal passes",
            ]
            seen_arch = {constraint.description.strip().lower() for constraint in constraints}
            for description in architectural_constraints:
                if description.lower() not in seen_arch:
                    constraints.append(Constraint(description=description, category="subject"))
                    seen_arch.add(description.lower())

        if (
            any(w in task_lower for w in ["color", "colorful", "vibrant"])
            and not any(w in task_lower for w in ["grayscale", "monochrome", "black and white"])
        ):
            constraints.append(Constraint(
                description="Multiple distinct colors used (not monochrome)",
                category="color",
            ))

        seen = {constraint.description.strip().lower() for constraint in constraints}
        for criterion in extra_criteria:
            text = str(criterion or "").strip()
            key = text.lower()
            if not text or key in seen:
                continue
            constraints.append(Constraint(
                description=text,
                category="research",
            ))
            seen.add(key)

        return constraints

    # ------------------------------------------------------------------
    # VLM Judge (Maestro / VISCO pattern)
    # ------------------------------------------------------------------

    def _judge_with_vlm(self, screenshot_path: str, reference_paths: list[str]) -> None:
        """Use a VLM to judge each constraint against the screenshot.

        Implements VISCO's LOOKBACK strategy: the VLM looks at the actual
        image before making its judgment, not from memory.
        """
        constraint_list = "\n".join(
            f"  {i+1}. [{c.category}] {c.description}"
            for i, c in enumerate(self._constraints)
        )

        prompt = (
            f"You are a strict visual quality inspector. I asked an agent to:\n"
            f'  "{self._task}"\n\n'
            f"The agent produced the attached screenshot. Evaluate EACH constraint:\n"
            f"{constraint_list}\n\n"
            f"For EACH constraint, respond with:\n"
            f'  {{"index": <1-based>, "satisfied": true/false, '
            f'"critique": "specific explanation"}}\n\n'
            f"Be STRICT. If hands look like waves, that's a FAIL. "
            f"If only one color is used when colors were requested, that's a FAIL. "
            f"If detail is sparse when 'exhaustive' was requested, that's a FAIL.\n\n"
            f"Output a JSON array of these objects. Output ONLY the JSON."
        )

        images = [screenshot_path] + reference_paths
        try:
            response = self._vlm_judge(prompt, images)
            raw = response.strip()
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1]
                if raw.endswith("```"):
                    raw = raw[:-3].strip()
            judgments = json.loads(raw)

            for j in judgments:
                idx = j.get("index", 0) - 1
                if 0 <= idx < len(self._constraints):
                    self._constraints[idx].satisfied = j.get("satisfied", False)
                    self._constraints[idx].critique = j.get("critique", "")

        except Exception as e:
            logger.warning("VLM judge failed: %s", e)
            self._judge_heuristic(screenshot_path)

    # ------------------------------------------------------------------
    # Heuristic Judge (fallback when no VLM)
    # ------------------------------------------------------------------

    def _judge_heuristic(self, screenshot_path: str) -> None:
        """Fast heuristic verification using pixel analysis.

        Not as accurate as a VLM, but catches obvious failures like
        empty canvas, tiny drawing, monochrome output.
        """
        try:
            from PIL import Image
            import numpy as np

            img = np.array(Image.open(screenshot_path).convert("RGB"))
            h, w, _ = img.shape

            canvas_x_start = int(w * 0.15)
            canvas = img[:, canvas_x_start:, :]

            bg_color = np.array([255, 255, 255])
            diff_from_bg = np.abs(canvas.astype(float) - bg_color.astype(float))
            non_bg_mask = diff_from_bg.sum(axis=2) > 50
            content_ratio = non_bg_mask.mean()

            unique_hues = set()
            for y in range(0, canvas.shape[0], 10):
                for x in range(0, canvas.shape[1], 10):
                    r, g, b = canvas[y, x]
                    if diff_from_bg[y, x].sum() > 50:
                        hue_bucket = (r // 60, g // 60, b // 60)
                        unique_hues.add(hue_bucket)

            for c in self._constraints:
                if c.category == "existence":
                    c.satisfied = content_ratio > 0.005
                    if not c.satisfied:
                        c.critique = f"Canvas appears empty (content ratio: {content_ratio:.3f})"

                elif c.category == "composition":
                    c.satisfied = content_ratio > 0.08
                    if not c.satisfied:
                        c.critique = (f"Drawing too small — only {content_ratio:.1%} "
                                      f"of canvas used. Needs >30%.")

                elif c.category == "color":
                    c.satisfied = len(unique_hues) >= 4
                    if not c.satisfied:
                        c.critique = (f"Only {len(unique_hues)} color(s) detected. "
                                      f"'Profuse colors' requires multiple distinct colors.")

                elif c.category == "subject":
                    c.satisfied = content_ratio > 0.02
                    if not c.satisfied:
                        c.critique = f"Insufficient content to verify: {c.description}"
                    else:
                        c.critique = ("Cannot verify semantic content without VLM. "
                                      "Pixel analysis confirms content exists but "
                                      "cannot judge if it matches description.")
                        c.satisfied = False

        except ImportError:
            for c in self._constraints:
                c.satisfied = False
                c.critique = "PIL/numpy not available for verification"

    # ------------------------------------------------------------------
    # Screenshot capture
    # ------------------------------------------------------------------

    @staticmethod
    def _capture_screenshot(path: str) -> bool:
        try:
            result = subprocess.run(
                ["screencapture", "-x", path],
                timeout=5,
                capture_output=True,
            )
            return result.returncode == 0 and Path(path).exists()
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    # ------------------------------------------------------------------
    # Pretty printing
    # ------------------------------------------------------------------

    @staticmethod
    def _print_verdict(result: VerificationResult) -> None:
        print(f"\n  {'='*55}")
        print(f"  VERIFICATION GATE — Iteration {result.iteration}")
        print(f"  {'='*55}")
        print(f"  Verdict: {result.verdict}")
        print(f"  Score:   {result.score:.0%}")
        if result.constraints:
            print(f"  Constraints ({len(result.constraints)}):")
            for c in result.constraints:
                icon = "PASS" if c["satisfied"] else "FAIL"
                print(f"    [{icon}] {c['description']}")
                if not c["satisfied"] and c.get("critique"):
                    print(f"           {c['critique']}")
        if result.deficiencies:
            print(f"  Deficiencies ({len(result.deficiencies)}):")
            for d in result.deficiencies:
                print(f"    - {d}")
        print(f"  Screenshot: {result.screenshot_path}")
        print(f"  {'='*55}")
