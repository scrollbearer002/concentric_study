"""Action contracts for environment-aware execution guarantees.

This module separates semantic actions from site-conditioned execution
contracts. The planner should express intent ("set color to black"), while the
contract layer owns the environment-specific preconditions, postconditions, and
repair policies required to make that intent reliable.

Research basis:
- SeeAct (ICML 2024, arXiv:2401.01614): semantic planning must be grounded
  into executable UI interactions rather than left as free-form guesses.
- WebVoyager (arXiv:2401.13919): live-site success depends on reliable
  environment-specific execution, not only high-level plans.
- OSWorld (arXiv:2404.07972): modern GUI agents still fail mainly on grounding
  and operational knowledge in real environments.
- SEI contract-driven systems guidance: explicit contracts are a defensible
  way to encode assumptions, obligations, and guarantees across boundaries.
"""
from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Any, Callable
from urllib.parse import urlparse

from agent_infra.action_handlers import ACTION_HANDLERS, _ACTION_EFFECT_CHECKS


Context = Any
RepairLogger = Callable[[str, str, dict[str, Any]], None] | None


@dataclass(frozen=True)
class ActionContract:
    """Environment-aware contract for an action family."""

    name: str
    matches: Callable[[Context, str, dict[str, Any]], bool]
    effect_check: Callable[[Context, str, dict[str, Any]], str | None] | None = None
    repair: Callable[[Context, dict[str, Any], dict[str, Any], int, RepairLogger], bool] | None = None


def site_domain(ctx) -> str:
    url = getattr(ctx, "url", "") or ""
    return (urlparse(url).netloc or "").lower()


def is_kleki(ctx) -> bool:
    return "kleki.com" in site_domain(ctx)


def canvas_usability_prompt(ctx) -> str:
    if is_kleki(ctx):
        return (
            "Is the Kleki workspace usable? The main drawing canvas should be visible, "
            "and the right-side tool panel may remain visible. Only answer NO if a modal, "
            "popup, permission prompt, or browser overlay blocks interaction with the "
            "canvas or tools. Reply YES or NO."
        )
    return (
        "Is the Excalidraw drawing canvas usable? The toolbar should be visible "
        "at the top with drawing tools. Ignore any decorative welcome text or "
        "logo on the canvas itself — those are non-blocking empty-state content "
        "that disappears when you start drawing. Only answer NO if there is a "
        "modal dialog, popup, or overlay that BLOCKS interaction with the toolbar "
        "and canvas. Reply YES or NO."
    )


def recovery_postcondition_prompt(ctx) -> str:
    if is_kleki(ctx):
        return (
            "The Kleki workspace is now clear of any dialogs, popups, modals, banners, "
            "or overlays. The main drawing canvas and right-side tool panel are both "
            "visible and interactable."
        )
    return (
        "The canvas is now clear of any dialogs, popups, modals, banners, "
        "or overlays. The Excalidraw drawing canvas is fully visible and accessible."
    )


def needs_contrast_repair(diagnosis: dict[str, Any]) -> bool:
    text = " ".join(
        [
            str(diagnosis.get("description", "")),
            str(diagnosis.get("missing_precondition", "")),
        ]
    ).lower()
    return any(
        marker in text
        for marker in (
            "white",
            "background",
            "invisible",
            "contrasting",
            "same as the canvas",
            "same as the background",
        )
    )


def needs_canvas_clear_repair(diagnosis: dict[str, Any]) -> bool:
    text = " ".join(
        [
            str(diagnosis.get("description", "")),
            str(diagnosis.get("missing_precondition", "")),
        ]
    ).lower()
    return any(
        marker in text
        for marker in (
            "canvas is not blank",
            "canvas is not clear",
            "clear the canvas was not successful",
            "clear canvas was not successful",
            "black lines drawn",
            "marks visible",
            "not successful",
        )
    )


def needs_beforeunload_dialog_repair(diagnosis: dict[str, Any]) -> bool:
    text = " ".join(
        [
            str(diagnosis.get("description", "")),
            str(diagnosis.get("missing_precondition", "")),
        ]
    ).lower()
    return any(
        marker in text
        for marker in (
            "are you sure you want to leave this page",
            "stay on page",
            "leave page",
            "browser confirmation dialog",
            "from \"kleki.com\"",
            "from 'kleki.com'",
        )
    )


def needs_render_state_repair(diagnosis: dict[str, Any]) -> bool:
    text = " ".join(
        [
            str(diagnosis.get("description", "")),
            str(diagnosis.get("missing_precondition", "")),
        ]
    ).lower()
    return any(
        marker in text
        for marker in (
            "brush settings are incorrect",
            "scatter",
            "size is set",
            "size field",
            "opacity",
            "stabilizer",
            "controlled architectural linework",
        )
    )


def _kleki_color_effect_check(_ctx, _action_type: str, action_args: dict[str, Any]) -> str:
    color = (str(action_args.get("color", "black")) or "black").strip().lower()
    if color in {"black", "near-black", "near black", "very dark gray"}:
        return (
            "In the Kleki color picker square, is the selection indicator positioned "
            "in the dark lower-left grayscale region so the next brush stroke would "
            "appear black or near-black on the white canvas? Reply YES or NO."
        )
    if color == "dark gray":
        return (
            "In the Kleki color picker square, is the selection indicator positioned "
            "on the left grayscale column at a dark-gray brightness level? Reply YES or NO."
        )
    if color == "light gray":
        return (
            "In the Kleki color picker square, is the selection indicator positioned "
            "on the left grayscale column at a light-gray brightness level? Reply YES or NO."
        )
    if color == "white":
        return (
            "In the Kleki color picker square, is the selection indicator positioned "
            "near the bright top-left white region? Reply YES or NO."
        )
    return (
        f"Is the Kleki color picker configured so the next brush stroke would appear as "
        f"{color} or a close visual equivalent? Reply YES or NO."
    )


def _kleki_draw_effect_check(_ctx, _action_type: str, _action_args: dict[str, Any]) -> str:
    return (
        "Is there a visible stroke or shape on the main Kleki canvas that is "
        "distinct from the blank white background? Ignore the right-side UI panel. "
        "Reply YES or NO."
    )


def _kleki_structural_draw_effect_check(_ctx, _action_type: str, _action_args: dict[str, Any]) -> str:
    return (
        "On the main Kleki canvas, is there a visible straight or deliberate structural line segment "
        "that reads as intentional architectural construction rather than a loose scribble? "
        "Ignore the right-side UI panel. Reply YES or NO."
    )


def _kleki_clear_effect_check(_ctx, _action_type: str, _action_args: dict[str, Any]) -> str:
    return (
        "Is the main Kleki canvas blank with no user-drawn marks visible? "
        "Ignore the right-side tool panel and browser chrome. Reply YES or NO."
    )


def _kleki_brush_size_effect_check(_ctx, _action_type: str, action_args: dict[str, Any]) -> str:
    size = (str(action_args.get("size", "thin")) or "thin").strip().lower()
    if size == "very thin":
        return (
            "In the Kleki brush settings, does the Size field show 1 or another clearly minimal "
            "value suitable for crisp thin linework? Reply YES or NO."
        )
    if size in {"thin", "small"}:
        return (
            "In the Kleki brush settings, does the Size field show a small value around 4? "
            "Reply YES or NO."
        )
    if size == "medium":
        return (
            "In the Kleki brush settings, does the Size field show a medium value around 18? "
            "Reply YES or NO."
        )
    return (
        "In the Kleki brush settings, does the Size field show a large wide brush value "
        "well above the thin-line range? Reply YES or NO."
    )


def _kleki_opacity_effect_check(_ctx, _action_type: str, action_args: dict[str, Any]) -> str:
    opacity = (str(action_args.get("opacity", "100%")) or "100%").strip().lower()
    if opacity == "low":
        return (
            "In the Kleki brush settings, does the Opacity control indicate a low value "
            "well below fully opaque? Reply YES or NO."
        )
    if opacity == "medium":
        return (
            "In the Kleki brush settings, does the Opacity control indicate a medium value "
            "around the middle of the slider, not near zero or full opacity? Reply YES or NO."
        )
    if opacity == "high":
        return (
            "In the Kleki brush settings, does the Opacity control indicate a high value "
            "near the right side but not necessarily fully opaque? Reply YES or NO."
        )
    return (
        "In the Kleki brush settings, does the Opacity field show 100 or another clearly "
        "full-opacity value? Reply YES or NO."
    )


def _kleki_scatter_effect_check(_ctx, _action_type: str, action_args: dict[str, Any]) -> str:
    scatter = (str(action_args.get("scatter", "0")) or "0").strip().lower()
    if scatter in {"0", "zero", "none"}:
        return (
            "In the Kleki brush settings, does the Scatter field show 0 or another clearly zero "
            "value, so brush marks would not break into dotted noise? Reply YES or NO."
        )
    if scatter == "low":
        return (
            "In the Kleki brush settings, does the Scatter control indicate a low value left of center? "
            "Reply YES or NO."
        )
    if scatter == "medium":
        return (
            "In the Kleki brush settings, does the Scatter control indicate a medium value around the middle? "
            "Reply YES or NO."
        )
    return (
        "In the Kleki brush settings, does the Scatter control indicate a high value near the right side? "
        "Reply YES or NO."
    )


def _kleki_stabilizer_effect_check(_ctx, _action_type: str, action_args: dict[str, Any]) -> str:
    stabilizer = (str(action_args.get("stabilizer", "1")) or "1").strip().lower()
    return (
        f"In the Kleki brush settings, does the Stabilizer control show a value near {stabilizer}? "
        "Reply YES or NO."
    )


def _kleki_tool_effect_check(_ctx, _action_type: str, action_args: dict[str, Any]) -> str:
    tool = (str(action_args.get("tool", "brush")) or "brush").strip().lower()
    if tool in {"shape", "line"}:
        return (
            "Is Kleki in a straight-line-capable drawing mode, such as the shape tool or Shift-line behavior, "
            "rather than a freehand brush-only state? Reply YES or NO."
        )
    return f"Is the Kleki {tool} tool active? Reply YES or NO."


def _kleki_render_state_effect_check(_ctx, _action_type: str, action_args: dict[str, Any]) -> str:
    tool = (str(action_args.get("tool", "brush")) or "brush").strip().lower()
    size = (str(action_args.get("size", "very thin")) or "very thin").strip().lower()
    opacity = (str(action_args.get("opacity", "100%")) or "100%").strip().lower()
    scatter = (str(action_args.get("scatter", "0")) or "0").strip().lower()
    stabilizer = (str(action_args.get("stabilizer", "1")) or "1").strip().lower()
    return (
        f"Is Kleki now configured for controlled architectural linework: tool={tool}, size={size} "
        f"(for very thin expect Size 1), opacity={opacity} (expect Opacity 100 for full opacity), "
        f"scatter={scatter} (expect Scatter 0), and stabilizer={stabilizer}? Reply YES or NO."
    )


def _emit_repair_log(logger: RepairLogger, kind: str, details: dict[str, Any]) -> None:
    if logger is None:
        return
    logger("precondition_repair", kind, details)


def _repair_kleki_color(ctx, action_item: dict[str, Any], diagnosis: dict[str, Any], attempt: int,
                        logger: RepairLogger) -> bool:
    if not needs_contrast_repair(diagnosis):
        return False
    _emit_repair_log(logger, "kleki_color_retry", {
        "action": action_item["action"],
        "attempt": attempt + 1,
        "diagnosis": diagnosis.get("description", ""),
        "missing_precondition": diagnosis.get("missing_precondition", ""),
        "contract": "kleki_color_selection",
    })
    color_handler = ACTION_HANDLERS.get("kleki_set_color")
    if color_handler is None:
        return False
    color_handler(ctx, {"color": action_item.get("args", {}).get("color", "black")})
    time.sleep(0.3)
    return True


def _repair_kleki_visible_draw(ctx, action_item: dict[str, Any], diagnosis: dict[str, Any], attempt: int,
                               logger: RepairLogger) -> bool:
    if not needs_contrast_repair(diagnosis):
        return False
    _emit_repair_log(logger, "kleki_restore_contrast", {
        "action": action_item["action"],
        "attempt": attempt + 1,
        "diagnosis": diagnosis.get("description", ""),
        "missing_precondition": diagnosis.get("missing_precondition", ""),
        "contract": "kleki_visible_draw",
    })
    ctx.agent.enforce_app_focus("Safari")
    ctx.agent.execute_keystroke("b")
    time.sleep(0.3)
    color_handler = ACTION_HANDLERS.get("kleki_set_color")
    if color_handler is None:
        return False
    color_handler(ctx, {"color": "black"})
    time.sleep(0.3)
    return True


def _repair_kleki_clear_canvas(ctx, action_item: dict[str, Any], diagnosis: dict[str, Any], attempt: int,
                               logger: RepairLogger) -> bool:
    dialog_handler = ACTION_HANDLERS.get("browser_beforeunload_dialog")
    if needs_beforeunload_dialog_repair(diagnosis) and dialog_handler is not None:
        _emit_repair_log(logger, "browser_beforeunload_stay", {
            "action": action_item["action"],
            "attempt": attempt + 1,
            "diagnosis": diagnosis.get("description", ""),
            "contract": "browser_beforeunload_dialog",
        })
        dialog_handler(ctx, {"choice": "stay"})
        time.sleep(0.4)

    if not needs_canvas_clear_repair(diagnosis) and not needs_beforeunload_dialog_repair(diagnosis):
        return False
    clear_handler = ACTION_HANDLERS.get("kleki_clear_canvas")
    if clear_handler is None:
        return False
    _emit_repair_log(logger, "kleki_clear_canvas_retry", {
        "action": action_item["action"],
        "attempt": attempt + 1,
        "diagnosis": diagnosis.get("description", ""),
        "contract": "kleki_clear_canvas",
    })
    clear_handler(ctx, {})
    time.sleep(0.4)
    return True


def _repair_kleki_render_state(ctx, action_item: dict[str, Any], diagnosis: dict[str, Any], attempt: int,
                               logger: RepairLogger) -> bool:
    if not needs_render_state_repair(diagnosis):
        return False
    render_handler = ACTION_HANDLERS.get("kleki_reset_render_state")
    if render_handler is None:
        return False
    _emit_repair_log(logger, "kleki_render_state_retry", {
        "action": action_item["action"],
        "attempt": attempt + 1,
        "diagnosis": diagnosis.get("description", ""),
        "contract": "kleki_render_state",
    })
    render_handler(ctx, action_item.get("args", {}) or {})
    time.sleep(0.4)
    return True


ACTION_CONTRACTS: tuple[ActionContract, ...] = (
    ActionContract(
        name="kleki_clear_canvas",
        matches=lambda ctx, action_type, _args: is_kleki(ctx) and action_type in {"clear_canvas", "kleki_clear_canvas"},
        effect_check=_kleki_clear_effect_check,
        repair=_repair_kleki_clear_canvas,
    ),
    ActionContract(
        name="kleki_color_selection",
        matches=lambda ctx, action_type, _args: is_kleki(ctx) and action_type == "kleki_set_color",
        effect_check=_kleki_color_effect_check,
        repair=_repair_kleki_color,
    ),
    ActionContract(
        name="kleki_visible_draw",
        matches=lambda ctx, action_type, _args: is_kleki(ctx) and action_type in {"draw_concentric_triangles", "draw_path", "draw_circle"},
        effect_check=_kleki_draw_effect_check,
        repair=_repair_kleki_visible_draw,
    ),
    ActionContract(
        name="kleki_structural_draw",
        matches=lambda ctx, action_type, _args: is_kleki(ctx) and action_type == "draw_segments",
        effect_check=_kleki_structural_draw_effect_check,
        repair=_repair_kleki_visible_draw,
    ),
    ActionContract(
        name="kleki_brush_size",
        matches=lambda ctx, action_type, _args: is_kleki(ctx) and action_type == "kleki_set_brush_size",
        effect_check=_kleki_brush_size_effect_check,
    ),
    ActionContract(
        name="kleki_opacity",
        matches=lambda ctx, action_type, _args: is_kleki(ctx) and action_type == "kleki_set_opacity",
        effect_check=_kleki_opacity_effect_check,
    ),
    ActionContract(
        name="kleki_scatter",
        matches=lambda ctx, action_type, _args: is_kleki(ctx) and action_type == "kleki_set_scatter",
        effect_check=_kleki_scatter_effect_check,
    ),
    ActionContract(
        name="kleki_stabilizer",
        matches=lambda ctx, action_type, _args: is_kleki(ctx) and action_type == "kleki_set_stabilizer",
        effect_check=_kleki_stabilizer_effect_check,
    ),
    ActionContract(
        name="kleki_tool_selection",
        matches=lambda ctx, action_type, _args: is_kleki(ctx) and action_type == "kleki_select_tool",
        effect_check=_kleki_tool_effect_check,
    ),
    ActionContract(
        name="kleki_render_state",
        matches=lambda ctx, action_type, _args: is_kleki(ctx) and action_type == "kleki_reset_render_state",
        effect_check=_kleki_render_state_effect_check,
        repair=_repair_kleki_render_state,
    ),
)


def resolve_action_contract(ctx, action_type: str, action_args: dict[str, Any]) -> ActionContract | None:
    for contract in ACTION_CONTRACTS:
        if contract.matches(ctx, action_type, action_args):
            return contract
    return None


def get_action_effect_check(ctx, action_type: str, action_args: dict[str, Any] | None = None) -> str | None:
    args = action_args or {}
    contract = resolve_action_contract(ctx, action_type, args)
    if contract and contract.effect_check:
        return contract.effect_check(ctx, action_type, args)
    return _ACTION_EFFECT_CHECKS.get(action_type)


def apply_action_contract_repair(ctx, action_item: dict[str, Any], diagnosis: dict[str, Any], attempt: int,
                                 logger: RepairLogger = None) -> bool:
    action_type = action_item.get("action", "")
    args = action_item.get("args", {}) or {}
    contract = resolve_action_contract(ctx, action_type, args)
    if contract and contract.repair:
        return contract.repair(ctx, action_item, diagnosis, attempt, logger)
    return False
