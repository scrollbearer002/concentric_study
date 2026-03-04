"""Recovery, diagnosis, and verification logic for action execution.

Implements the Reflexion pattern (Shinn et al., NeurIPS 2023) for
self-healing: diagnose failures via VLM, execute recovery actions,
and verify postconditions (STRIPS, Fikes & Nilsson 1971).

Extracted from test_excalidraw_covt.py per Fowler (2018) Move Function.
"""
from __future__ import annotations

import os
import time
import json
import subprocess

from agent_infra.action_handlers import ACTION_HANDLERS, _SOM_DEPENDENT_ACTIONS, _ACTION_EFFECT_CHECKS
from agent_infra.action_allowlist import ActionAllowlist, AllowlistResult, get_screen_bounds_from_agent
from agent_infra.action_contracts import (
    apply_action_contract_repair,
    canvas_usability_prompt,
    get_action_effect_check,
    recovery_postcondition_prompt,
)
from window_capture import capture_front_window

# ---------------------------------------------------------------------------
# Dependency injection (same pattern as action_handlers.py)
# ---------------------------------------------------------------------------

_trace = None
_exec_log_line = None
_pass_log_line = None


def inject_dependencies(trace_fn, exec_log_fn, pass_log_fn):
    global _trace, _exec_log_line, _pass_log_line
    _trace = trace_fn
    _exec_log_line = exec_log_fn
    _pass_log_line = pass_log_fn


def _verify_action_effect(ctx, action_type: str, step_index: int, action_args: dict | None = None) -> bool:
    """Closed-loop Perceive-Act-Verify: confirm the action had its expected visual effect.
    Returns True if verified or if no check is defined. Raises RuntimeError on failure."""
    check = get_action_effect_check(ctx, action_type, action_args)
    if not check or not ctx.use_enterprise or not ctx.agent:
        return True

    verify_path = str(ctx.cre_dir / f"effect_verify_{step_index}.png")
    capture_front_window(verify_path, timeout_seconds=10)
    print(f"  [VERIFY] Checking effect of '{action_type}'...")
    _exec_log_line("verify_action_effect", action_type, {"check": check[:60]})
    ctx.agent.assert_visual_state(verify_path, check)
    print(f"  [VERIFY] '{action_type}' effect confirmed.")
    _exec_log_line("verify_action_effect_passed", action_type)
    return True


def _capture_diagnostic_screenshot(ctx, label: str) -> str:
    """Take a timestamped screenshot for diagnosis. Returns the file path."""
    ts = int(time.time() * 1000)
    path = str(ctx.cre_dir / f"diag_{label}_{ts}.png")
    capture_front_window(path, timeout_seconds=10)
    return path


def _capture_visual_monitor_checkpoint(
    ctx,
    phase: str,
    *,
    step_index: int | None = None,
    attempt: int | None = None,
    action_type: str | None = None,
    diagnosis: dict | None = None,
) -> dict | None:
    """Force an event-triggered monitor snapshot during recovery-critical phases.

    This supplements the periodic VisualMonitor timeline with deterministic
    before/after checkpoints around recovery actions so modal dialogs, focus
    drift, and short-lived overlays are not missed between polling intervals.
    """
    monitor = getattr(ctx, "visual_monitor", None)
    if monitor is None:
        return None
    try:
        snap = monitor.capture_now()
        if snap is None:
            return None
        checkpoint = {
            "phase": phase,
            "path": snap.path,
            "timestamp": snap.timestamp,
            "iso_time": snap.iso_time,
            "index": snap.index,
        }
        if step_index is not None:
            checkpoint["step"] = step_index
        if attempt is not None:
            checkpoint["attempt"] = attempt
        if action_type:
            checkpoint["action_type"] = action_type
        if diagnosis:
            checkpoint["recovery_action"] = diagnosis.get("recovery_action")
            checkpoint["obstruction"] = diagnosis.get("obstruction")
            checkpoint["diagnosis"] = diagnosis.get("description", "")[:240]
        checkpoints = getattr(ctx, "visual_monitor_checkpoints", None)
        if checkpoints is not None:
            checkpoints.append(checkpoint)
        _exec_log_line("visual_monitor_checkpoint", phase, checkpoint)
        return checkpoint
    except Exception as e:
        _exec_log_line("visual_monitor_checkpoint_failed", phase, {"error": str(e)})
        return None


_MAX_DIAGNOSIS_RULES = 5


def _diagnose_failure(ctx, screenshot_path: str, expected: str) -> dict:
    """Ask the VLM what went wrong (Reflexion pattern with episodic memory).

    Injects summarizer context when available, following VIGIL (arXiv:2512.07094)
    and Reflexion (Shinn et al., NeurIPS 2023) — trace summaries improve
    diagnosis accuracy by giving the VLM awareness of what succeeded so far.

    Rules injection follows ExpeL (Zhao et al., AAAI 2024, arXiv:2308.10144v2):
    natural-language generalizations from prior successes/failures are injected
    as a separate labeled block so the VLM can test for rule violations before
    generating novel diagnoses.  Rules are framed as "test violations first"
    rather than "follow these rules" to prevent anchoring on irrelevant rules
    for novel failure modes — a guardrail aligned with VIGIL's Roses/Buds/Thorns
    structured diagnosis (Cruz, 2025, arXiv:2512.07094).

    Gating: at most _MAX_DIAGNOSIS_RULES rules are injected (token budget
    ~250 chars, well under typical VLM context limits).  When ctx.rules is
    empty (no failures have produced rules yet), the block is omitted entirely
    with zero behavior change — dormant by design.

    Returns {"obstruction": bool, "description": str, "recovery_action": str}.
    """
    if not ctx.use_enterprise or not ctx.agent:
        return {"obstruction": False, "description": "unknown", "recovery_action": "none"}

    history_block = ctx.journal.format_for_prompt(n=5)

    summary_block = ""
    if hasattr(ctx, "summarizer") and ctx.summarizer:
        summary_text = ctx.summarizer.get_context()
        if summary_text:
            summary_block = f"\nExecution summary so far:\n{summary_text}\n"

    rules_block = ""
    if hasattr(ctx, "rules") and ctx.rules:
        top_rules = ctx.rules[:_MAX_DIAGNOSIS_RULES]
        rules_lines = "\n".join(f"- {r}" for r in top_rules)
        rules_block = (
            "\n=== GENERALIZATION RULES (test violations first) ===\n"
            f"{rules_lines}\n"
            "If any rule above is violated, flag the violation as likely root cause.\n"
        )

    prompt = (
        "The agent expected the following visual state but it was NOT achieved:\n"
        f'  Expected: "{expected}"\n\n'
        "Recent action history (episodic memory):\n"
        f"{history_block}\n"
        f"{summary_block}"
        f"{rules_block}\n"
        "Analyze the screenshot and the action history, then answer in JSON:\n"
        "{\n"
        '  "obstruction": true/false,  // Is there a BLOCKING dialog, popup, or modal that prevents clicking the toolbar/canvas?\n'
        '  "description": "...",       // Brief description of what you see instead of the expected state\n'
        '  "recovery_action": "...",   // One of: "escape", "enter", "click_away", "select_tool", "stay_on_page", "leave_page", "none"\n'
        '  "missing_precondition": "..." // If no obstruction: what precondition is missing? e.g. "drawing_tool_not_selected", "color_palette_not_visible", "none"\n'
        "}\n"
        "IMPORTANT: Decorative welcome text/logos on the canvas are NOT obstructions if the toolbar is visible.\n"
        "Reply ONLY with the JSON object."
    )
    try:
        uploaded = ctx.agent._client.files.upload(file=screenshot_path)
        diag_model = ctx.agent._model_for("diagnose_failure", "gemini-2.5-pro")
        response = ctx.agent._client.models.generate_content(
            model=diag_model,
            contents=[uploaded, prompt],
            config=ctx.agent._gen_config_json,
        )
        parsed = json.loads(response.text)
        _exec_log_line("diagnose_failure", None, parsed)
        _trace("resilience:diagnose_failure", "result", parsed)
        return parsed
    except Exception as e:
        _trace("resilience:diagnose_failure", "error", {"error": str(e)})
        return {"obstruction": False, "description": str(e), "recovery_action": "escape"}


def _execute_recovery(ctx, diagnosis: dict):
    """Execute a recovery action based on VLM diagnosis."""
    action = diagnosis.get("recovery_action", "escape")
    desc = diagnosis.get("description", "unknown obstruction")
    _exec_log_line("recovery_attempt", action, {"description": desc})
    print(f"  RECOVERY: Attempting '{action}' (reason: {desc})")
    _capture_visual_monitor_checkpoint(ctx, "before_recovery_action", action_type=action, diagnosis=diagnosis)

    if action == "escape":
        if ctx.use_enterprise and ctx.agent:
            ctx.agent.execute_keystroke(53)  # Escape
        time.sleep(0.5)
    elif action == "enter":
        if ctx.use_enterprise and ctx.agent:
            ctx.agent.execute_keystroke(36)  # Enter
        time.sleep(0.5)
    elif action == "click_away":
        if ctx.use_enterprise and ctx.agent:
            ctx.agent.execute_global_click(ctx.cx, ctx.cy)
        time.sleep(0.5)
    elif action in {"stay_on_page", "stay"}:
        if ctx.use_enterprise and ctx.agent:
            handler = ACTION_HANDLERS.get("browser_beforeunload_dialog")
            if handler is not None:
                handler(ctx, {"choice": "stay"})
        time.sleep(0.5)
    elif action in {"leave_page", "leave"}:
        if ctx.use_enterprise and ctx.agent:
            handler = ACTION_HANDLERS.get("browser_beforeunload_dialog")
            if handler is not None:
                handler(ctx, {"choice": "leave"})
        time.sleep(0.5)
    else:
        if ctx.use_enterprise and ctx.agent:
            ctx.agent.execute_keystroke(53)  # fallback: Escape
        time.sleep(0.5)

    _exec_log_line("recovery_executed", action)
    print(f"  RECOVERY: '{action}' executed")
    _capture_visual_monitor_checkpoint(ctx, "after_recovery_action", action_type=action, diagnosis=diagnosis)


def _verify_recovery_postcondition(ctx, diagnosis: dict, step_index: int, attempt: int):
    """Verify that the recovery action achieved its intended postcondition.

    Implements STRIPS-style postcondition verification (Fikes & Nilsson, 1971,
    "STRIPS: A New Approach to the Application of Theorem Proving to Problem
    Solving", Artificial Intelligence 2(3-4), pp.189-208). Every operator has
    a postcondition that must hold after execution — blind retry without
    verifying the postcondition is unsound.

    If the obstruction persists after recovery, the trace records the failure
    explicitly, enabling the outer loop to diagnose systematic recovery failures
    rather than masking them with silent retries (Shinn et al., 2023, "Reflexion:
    Language Agents with Verbal Reinforcement Learning", NeurIPS 2023).
    """
    if not ctx.use_enterprise or not ctx.agent:
        return
    if not diagnosis.get("obstruction"):
        return  # no obstruction was diagnosed — no postcondition to check

    time.sleep(0.3)
    post_path = _capture_diagnostic_screenshot(ctx, f"postcond_s{step_index}_a{attempt}")
    try:
        ctx.agent.assert_visual_state(
            post_path,
            recovery_postcondition_prompt(ctx),
        )
        _exec_log_line("recovery_postcondition", "PASSED", {"step": step_index, "attempt": attempt})
        print(f"  RECOVERY POSTCONDITION: PASSED — obstruction cleared")
        _capture_visual_monitor_checkpoint(
            ctx,
            "recovery_postcondition_passed",
            step_index=step_index,
            attempt=attempt,
            action_type=diagnosis.get("recovery_action"),
            diagnosis=diagnosis,
        )
    except (RuntimeError, Exception) as e:
        _exec_log_line("recovery_postcondition", "FAILED", {
            "step": step_index, "attempt": attempt, "error": str(e),
            "original_diagnosis": diagnosis,
        })
        print(f"  RECOVERY POSTCONDITION: FAILED — obstruction persists after '{diagnosis.get('recovery_action', 'unknown')}'")
        _capture_visual_monitor_checkpoint(
            ctx,
            "recovery_postcondition_failed",
            step_index=step_index,
            attempt=attempt,
            action_type=diagnosis.get("recovery_action"),
            diagnosis=diagnosis,
        )


_DISMISS_STRATEGIES = [
    ("escape", lambda ctx: ctx.agent.execute_keystroke(53)),
    ("enter", lambda ctx: ctx.agent.execute_keystroke(36)),
    ("click_center", lambda ctx: ctx.agent.execute_global_click(ctx.cx, ctx.cy)),
]


def _ensure_canvas_clear(ctx):
    """Pre-action sanity check: verify no popups/overlays block the canvas.
    Prevents visual grounding contamination in SoM-dependent actions.
    Skipped when the trust tracker shows enough consecutive clean passes.

    If obstruction persists after exhausting all recovery strategies,
    raises RuntimeError so the caller's retry loop can handle it
    rather than silently proceeding on a broken UI.
    """
    if not ctx.use_enterprise or not ctx.agent:
        return
    sanity_trust_key = ("sanity_check", "canvas_clear")
    if ctx.trust_tracker and not ctx.trust_tracker.should_verify(sanity_trust_key):
        _trace("resilience:sanity_check", "trust_skipped", {})
        return

    _ASSERT_PROMPT = canvas_usability_prompt(ctx)

    sanity_path = _capture_diagnostic_screenshot(ctx, "sanity")
    try:
        ctx.agent.assert_visual_state(sanity_path, _ASSERT_PROMPT)
        _trace("resilience:sanity_check", "passed", {})
        if ctx.trust_tracker:
            ctx.trust_tracker.record_success(sanity_trust_key)
        return
    except RuntimeError:
        pass

    print("  SANITY CHECK: Obstruction detected — attempting dismissal cascade...")
    if ctx.trust_tracker:
        ctx.trust_tracker.record_failure(sanity_trust_key)
    _exec_log_line("sanity_check_failed", "obstruction_detected")

    diagnosis = _diagnose_failure(ctx, sanity_path, "Canvas fully visible, no obstructions")

    suggested = diagnosis.get("recovery_action", "escape")
    strategies = [(suggested, None)] + [(name, fn) for name, fn in _DISMISS_STRATEGIES if name != suggested]

    for strategy_name, strategy_fn in strategies:
        if strategy_fn:
            try:
                strategy_fn(ctx)
            except Exception:
                pass
        else:
            _execute_recovery(ctx, {**diagnosis, "recovery_action": strategy_name})

        time.sleep(0.5)
        retry_path = _capture_diagnostic_screenshot(ctx, f"sanity_{strategy_name}")
        try:
            ctx.agent.assert_visual_state(retry_path, _ASSERT_PROMPT)
            print(f"  SANITY CHECK: Canvas clear after '{strategy_name}'")
            _exec_log_line("sanity_check_recovered", strategy_name)
            return
        except RuntimeError:
            print(f"  SANITY CHECK: '{strategy_name}' did not clear obstruction")
            _exec_log_line("sanity_recovery_failed", strategy_name)

    _exec_log_line("sanity_check_exhausted", "all_strategies_failed", {
        "diagnosis": diagnosis.get("description", "unknown"),
    })
    raise RuntimeError(
        f"Canvas obstruction persists after exhausting all dismissal strategies. "
        f"Diagnosis: {diagnosis.get('description', 'unknown')}. "
        f"Cannot proceed — UI state is unreliable."
    )


# ---------------------------------------------------------------------------
# Trace / journal finalization helpers
# ---------------------------------------------------------------------------

def _finalize_trace_success(ctx, trace_step, output: str, visual_assert=None,
                             screenshot_path: str | None = None):
    """Finalize a trace step as successful and ingest into summarizer."""
    if not trace_step:
        return
    tw = ctx.trace_writer
    trace_step.action_result = {"success": True, "output": output}
    if ctx._last_resolved_coords:
        trace_step.post_state["resolved_coords"] = ctx._last_resolved_coords
    if screenshot_path:
        trace_step.post_state["screenshot"] = screenshot_path
        trace_step.post_state["state_changed"] = True
    expected = visual_assert if visual_assert else "action effect"
    actual = output if output != "ok" else "verified"
    trace_step.evaluation = {"expected": expected, "actual": actual, "match": True}
    tw.end_step(trace_step)
    if ctx.summarizer:
        ctx.summarizer.ingest_step(trace_step.to_dict())


# ---------------------------------------------------------------------------
# Verification / skip path handlers
# ---------------------------------------------------------------------------

def _handle_no_assert_path(ctx, action_type: str, action_args: dict, step_index: int, trace_step) -> bool:
    """Success path when no visual_assert is required (closed-loop effect check only)."""
    _verify_action_effect(ctx, action_type, step_index, action_args)
    ctx.journal.record(step_index, action_type, "ok")
    _finalize_trace_success(ctx, trace_step, "ok")
    return True


def _handle_no_enterprise_path(ctx, action_type: str, step_index: int,
                                visual_assert: str, trace_step) -> bool:
    """Success path when enterprise mode is not available."""
    ctx.journal.record(step_index, action_type, "ok (no enterprise)")
    if trace_step:
        tw = ctx.trace_writer
        trace_step.action_result = {"success": True, "output": "ok (no enterprise)"}
        trace_step.evaluation = {"expected": visual_assert, "actual": "skipped (no enterprise)", "match": True}
        tw.end_step(trace_step)
    return True


def _handle_trust_skip_path(ctx, action_type: str, step_index: int,
                             visual_assert: str, trace_step) -> bool:
    """Success path when the trust tracker allows skipping VLM verification."""
    assert_trust_key = ("visual_assert", action_type)
    print(f"  [TRUST SKIP] Skipping visual assertion for {action_type} (trusted)")
    ctx.journal.record(step_index, action_type, "ok (trust-skipped)")
    if ctx.trust_tracker:
        ctx.trust_tracker.record_success(assert_trust_key)
    _finalize_trace_success(ctx, trace_step, "trust-skipped", visual_assert)
    return True


def _handle_vlm_verify_path(ctx, action_type: str, step_index: int,
                              visual_assert: str, trace_step) -> bool:
    """Full VLM assertion path — capture screenshot and verify.

    When GRADED_ASSERTIONS=1 is set, uses grade_visual_state (structured
    PASS/FAIL/PARTIAL with confidence 0-5) instead of binary assert_visual_state.
    This enables richer trust tracker signals: confidence >= GRADED_TRUST_THRESHOLD
    maps to success, below to failure — preserving PAC-Bayes invariants while
    catching unreliable "technical passes" (GUI benchmarks show 15-25% fewer
    false positives with this approach; GhostEI-Bench, arXiv:2510.20333v2).

    Option C (always grade under feature flag) during benchmarking maximises
    signal for empirical calibration of assertion complexity thresholds.
    Post-calibration, transition to keyword heuristic (Option A) for production.
    """
    assert_trust_key = ("visual_assert", action_type)
    assert_path = str(ctx.cre_dir / f"assert_after_{step_index}.png")
    capture_front_window(assert_path, timeout_seconds=10)
    print(f"  Visual assertion: {visual_assert[:60]}...")

    use_graded = os.environ.get("GRADED_ASSERTIONS") == "1"

    if use_graded and ctx.use_enterprise and ctx.agent and hasattr(ctx.agent, "grade_visual_state"):
        from agent_core import GRADED_TRUST_THRESHOLD
        result = ctx.agent.grade_visual_state(assert_path, visual_assert)
        trusted = result.verdict == "PASS" and result.confidence >= GRADED_TRUST_THRESHOLD
        print(
            f"  Graded assertion: {result.verdict} "
            f"(confidence={result.confidence}, threshold={GRADED_TRUST_THRESHOLD}) "
            f"— {result.rationale[:60]}"
        )
        if ctx.trust_tracker:
            if trusted:
                ctx.trust_tracker.record_success(assert_trust_key)
            else:
                ctx.trust_tracker.record_failure(assert_trust_key)

        if result.verdict == "FAIL":
            raise RuntimeError(
                f"Graded Assertion Failed: {visual_assert} "
                f"(confidence={result.confidence}, rationale={result.rationale})"
            )
        if result.verdict == "PARTIAL" and result.confidence < GRADED_TRUST_THRESHOLD:
            raise RuntimeError(
                f"Graded Assertion Partial (low confidence): {visual_assert} "
                f"(confidence={result.confidence}, rationale={result.rationale})"
            )

        output = (
            f"graded:{result.verdict}:c{result.confidence}"
            f":{result.rationale[:40]}"
        )
        ctx.journal.record(step_index, action_type, f"ok ({output})", assert_path)
        _finalize_trace_success(ctx, trace_step, output, visual_assert, assert_path)
        return True

    ctx.agent.assert_visual_state(assert_path, visual_assert)
    print("  Visual assertion passed.")
    if ctx.trust_tracker:
        ctx.trust_tracker.record_success(assert_trust_key)
    ctx.journal.record(step_index, action_type, "ok (assertion passed)", assert_path)
    _finalize_trace_success(ctx, trace_step, "assertion passed", visual_assert, assert_path)
    return True


def _log_concentric_pass(action_type: str, visual_assert: str | None):
    """Emit task-specific pass log lines for CONCENTRIC_TRIANGLES_CLEAN."""
    if not os.environ.get("CONCENTRIC_TRIANGLES_CLEAN") or not visual_assert:
        return
    if action_type == "verify_success":
        _pass_log_line("verify_success", "PASS", "Four nested triangles on canvas")
    elif "empty" in visual_assert.lower() and "canvas" in visual_assert.lower():
        _pass_log_line("verify_canvas_empty", "PASS", "State-based oracle: canvas empty")
        _pass_log_line("clear_canvas", "PASS", "Erase all drawings (oracle confirmed)")


# ---------------------------------------------------------------------------
# Recovery attempt + fatal exception handlers
# ---------------------------------------------------------------------------

def _handle_recovery_attempt(ctx, action_item: dict, step_index: int,
                              attempt: int, max_retries: int, trace_step,
                              error: RuntimeError):
    """Handle a RuntimeError during action execution — log, diagnose, recover, or raise."""
    action_type = action_item["action"]
    args = action_item["args"]
    visual_assert = action_item.get("visual_assert")

    ctx.journal.record(step_index, action_type, f"FAILED: {error}")
    if ctx.trust_tracker:
        ctx.trust_tracker.record_failure(("visual_assert", action_type))
        ctx.trust_tracker.record_failure(("set_stroke_color", args.get("color", "")))

    is_last_attempt = (attempt == max_retries)
    _exec_log_line("action_failed", None, {
        "step": step_index, "action": action_type,
        "attempt": attempt + 1, "max_retries": max_retries,
        "error": str(error), "will_retry": not is_last_attempt,
    })

    if is_last_attempt:
        print(f"  FAILED after {max_retries + 1} attempts: {error}")
        if trace_step:
            tw = ctx.trace_writer
            trace_step.action_result = {"success": False, "error": str(error), "attempts": max_retries + 1}
            diag_path_final = _capture_diagnostic_screenshot(ctx, f"final_fail_s{step_index}")
            trace_step.post_state = {"screenshot": diag_path_final, "state_changed": False}
            trace_step.evaluation = {"expected": visual_assert or "action success", "actual": str(error), "match": False}
            tw.end_step(trace_step)
            tw.record_failure(step_index, "action_failed", str(error))
        raise error

    print(f"  Attempt {attempt + 1}/{max_retries + 1} failed, diagnosing...")
    diag_path = _capture_diagnostic_screenshot(ctx, f"fail_s{step_index}_a{attempt}")
    diagnosis = _diagnose_failure(ctx, diag_path, visual_assert or "expected action success")
    _capture_visual_monitor_checkpoint(
        ctx,
        "diagnosed_failure",
        step_index=step_index,
        attempt=attempt,
        action_type=action_type,
        diagnosis=diagnosis,
    )

    _draw_actions = {"draw_concentric_triangles", "draw_path", "draw_circle",
                     "draw_eiffel_tower", "draw_eiffel_landscape", "draw_shape"}
    no_obstruction = not diagnosis.get("obstruction", False)
    is_draw = action_type in _draw_actions
    desc_lower = diagnosis.get("description", "").lower()
    canvas_empty = "empty" in desc_lower
    missing_precond = diagnosis.get("missing_precondition", "").lower()
    color_palette_missing = (
        "color_palette" in missing_precond
        or "drawing_tool" in missing_precond
        or ("color" in desc_lower and ("not visible" in desc_lower or "not currently" in desc_lower))
    )
    is_color_action = action_type in {"set_stroke_color", "kleki_set_color"}
    applied_precondition_repair = False

    if no_obstruction and is_color_action and color_palette_missing and ctx.use_enterprise and ctx.agent:
        print(f"  [PRECONDITION REPAIR] Color palette not visible — selecting drawing tool to expose it")
        _exec_log_line("precondition_repair", "expose_color_palette", {
            "action": action_type, "attempt": attempt + 1,
            "diagnosis": diagnosis.get("description", ""),
            "missing_precondition": missing_precond,
        })
        _capture_visual_monitor_checkpoint(
            ctx,
            "before_precondition_repair",
            step_index=step_index,
            attempt=attempt,
            action_type=action_type,
            diagnosis=diagnosis,
        )
        ctx.agent.enforce_app_focus("Safari")
        ctx.agent.execute_keystroke("r")
        time.sleep(0.5)
        _capture_visual_monitor_checkpoint(
            ctx,
            "after_precondition_repair",
            step_index=step_index,
            attempt=attempt,
            action_type=action_type,
            diagnosis=diagnosis,
        )
        applied_precondition_repair = True
    elif no_obstruction and apply_action_contract_repair(
        ctx,
        action_item,
        diagnosis,
        attempt,
        logger=_exec_log_line,
    ):
        _capture_visual_monitor_checkpoint(
            ctx,
            "after_contract_repair",
            step_index=step_index,
            attempt=attempt,
            action_type=action_type,
            diagnosis=diagnosis,
        )
        applied_precondition_repair = True
    elif no_obstruction and is_draw and canvas_empty and ctx.use_enterprise and ctx.agent:
        print(f"  [PRECONDITION REPAIR] Canvas empty after draw — likely wrong tool selected")
        _exec_log_line("precondition_repair", "pen_tool_reselect", {
            "action": action_type, "attempt": attempt + 1,
            "diagnosis": diagnosis.get("description", ""),
        })
        _capture_visual_monitor_checkpoint(
            ctx,
            "before_precondition_repair",
            step_index=step_index,
            attempt=attempt,
            action_type=action_type,
            diagnosis=diagnosis,
        )
        ctx.agent.enforce_app_focus("Safari")
        ctx.agent.execute_keystroke(53)
        time.sleep(0.3)
        ctx.agent.execute_keystroke("p")
        time.sleep(0.3)
        _capture_visual_monitor_checkpoint(
            ctx,
            "after_precondition_repair",
            step_index=step_index,
            attempt=attempt,
            action_type=action_type,
            diagnosis=diagnosis,
        )
        applied_precondition_repair = True

    if not applied_precondition_repair:
        _execute_recovery(ctx, diagnosis)
        _verify_recovery_postcondition(ctx, diagnosis, step_index, attempt)

    if action_type in _SOM_DEPENDENT_ACTIONS:
        _ensure_canvas_clear(ctx)
    print(f"  Retrying action (attempt {attempt + 2}/{max_retries + 1})...")


def _handle_fatal_exception(ctx, trace_step, step_index: int,
                             visual_assert: str | None, error: Exception):
    """Handle a non-recoverable exception — log and re-raise."""
    print(f"  Action execution failed (non-recoverable): {error}")
    if trace_step:
        tw = ctx.trace_writer
        trace_step.action_result = {"success": False, "error": str(error), "non_recoverable": True}
        trace_step.evaluation = {"expected": visual_assert or "action success", "actual": str(error), "match": False}
        tw.end_step(trace_step)
        tw.record_failure(step_index, "non_recoverable_error", str(error))
    raise error


# ---------------------------------------------------------------------------
# Main action router with recovery
# ---------------------------------------------------------------------------

def _execute_action_with_recovery(ctx, action_item: dict, step_index: int, max_retries: int = 2) -> bool:
    """Execute an action with Reflexion-based retry on failure.

    Decomposed per Fowler (2018) Extract Method and Campbell (2018) Cognitive
    Complexity reduction — the router delegates to focused sub-functions, each
    handling one concern (trust-skip, VLM-verify, recovery, fatal).
    Returns True if the action (and its visual assertion) succeeded.
    """
    action_type = action_item["action"]
    args = action_item["args"]
    visual_assert = action_item.get("visual_assert")
    description = action_item.get("description", action_type)
    handler = ACTION_HANDLERS.get(action_type)

    if handler is None:
        print(f"  Unknown action type: {action_type}")
        return False

    tw = ctx.trace_writer
    trace_step = tw.begin_step(step_index) if tw else None
    if trace_step:
        trace_step.thought = description
        trace_step.action = {"type": action_type, "parameters": args}
        focused_app = ""
        if ctx.use_enterprise and ctx.agent:
            try:
                focused_app = ctx.agent.get_frontmost_application_name()
            except Exception:
                pass
        trace_step.pre_state = {
            "focused_app": focused_app,
            "canvas_center": {"x": ctx.cx, "y": ctx.cy},
        }

    # Pre-action allowlist check (VeriSafe-style block-before-execute)
    allowlist = getattr(ctx, "action_allowlist", None)
    if allowlist is not None:
        screen_bounds = getattr(ctx, "screen_bounds", None)
        if screen_bounds is None and ctx.use_enterprise and ctx.agent:
            screen_bounds = get_screen_bounds_from_agent(ctx.agent)
        allow_result = allowlist.check_action(action_type, args, screen_bounds)
        if not allow_result.allowed:
            if trace_step:
                trace_step.action_result = {
                    "success": False,
                    "blocked_by_allowlist": True,
                    "reason": allow_result.reason or "unknown",
                }
                trace_step.evaluation = {
                    "expected": description,
                    "actual": f"blocked:{allow_result.reason}",
                    "match": False,
                }
                tw.end_step(trace_step)
            return False

    action_has_coord_cache = (
        action_type == "set_stroke_color"
        and ctx.coord_cache.get(("set_stroke_color", (args.get("color") or "black").strip().lower()))
    )
    if action_type in _SOM_DEPENDENT_ACTIONS and not action_has_coord_cache:
        _ensure_canvas_clear(ctx)

    for attempt in range(max_retries + 1):
        try:
            handler_result = handler(ctx, args)

            if trace_step and isinstance(handler_result, dict):
                for key in ("strokes", "vertices", "vertices_per_triangle",
                            "total_strokes", "layers", "radius", "speeds"):
                    if key in handler_result:
                        trace_step.post_state[key] = handler_result[key]

                if not visual_assert:
                    return _handle_no_assert_path(ctx, action_type, args, step_index, trace_step)

            if not ctx.use_enterprise or not ctx.agent:
                return _handle_no_enterprise_path(ctx, action_type, step_index, visual_assert, trace_step)

            assert_trust_key = ("visual_assert", action_type)
            skip_assert = ctx.trust_tracker and not ctx.trust_tracker.should_verify(assert_trust_key)
            if skip_assert:
                _handle_trust_skip_path(ctx, action_type, step_index, visual_assert, trace_step)
            else:
                _handle_vlm_verify_path(ctx, action_type, step_index, visual_assert, trace_step)

            _log_concentric_pass(action_type, visual_assert)
            return True

        except RuntimeError as e:
            _handle_recovery_attempt(ctx, action_item, step_index, attempt, max_retries, trace_step, e)

        except Exception as e:
            _handle_fatal_exception(ctx, trace_step, step_index, visual_assert, e)

    return False
