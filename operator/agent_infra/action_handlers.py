"""GUI action handlers for Excalidraw — one function per action_type.

Extracted from test_excalidraw_covt.py per Fowler (2018, Refactoring Ch.8 "Move
Function") to reduce monolith complexity. Each handler accepts a context object
and args dict, returns a result dict.
"""
from __future__ import annotations

import os
import json
import time
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING
from screenshot_preprocessor import prepare_image_copy
from window_capture import capture_front_window, get_front_window_info

if TYPE_CHECKING:
    from typing import Any

# These are injected at module level by the caller to avoid circular imports
_trace = None
_exec_log_line = None
_pass_log_line = None
_validate_coord_cache_entry = None
_compute_region_phash = None
get_screenshot_center = None
nearest_neighbor_order = None
_get_a11y_snapshot = None


def inject_dependencies(
    trace_fn,
    exec_log_fn,
    pass_log_fn,
    validate_cache_fn,
    compute_phash_fn,
    get_center_fn,
    nn_order_fn,
    a11y_snapshot_fn=None,
):
    global _trace, _exec_log_line, _pass_log_line, _validate_coord_cache_entry, _compute_region_phash, get_screenshot_center, nearest_neighbor_order, _get_a11y_snapshot
    _trace = trace_fn
    _exec_log_line = exec_log_fn
    _pass_log_line = pass_log_fn
    _validate_coord_cache_entry = validate_cache_fn
    _compute_region_phash = compute_phash_fn
    get_screenshot_center = get_center_fn
    nearest_neighbor_order = nn_order_fn
    _get_a11y_snapshot = a11y_snapshot_fn


_COLOR_PICKER_FALLBACK_REGION = (0, 350, 500, 800)
_REGION_PADDING = 150
_PRECLICK_CONFIRM_ENV = "PRECLICK_CONFIRM"


def _derive_color_picker_region(ctx) -> tuple[int, int, int, int] | None:
    """Derive a crop region for the color picker from cached coordinates.

    Checks ctx.coord_cache for any set_stroke_color entry. If found, builds
    a padded bounding box around the known swatch position. Falls back to a
    default region covering Excalidraw's left panel.  Returns None only if
    the vision_engine lacks the adaptive method.
    """
    if not hasattr(ctx.vision_engine, "generate_som_overlay_adaptive"):
        return None

    for key, val in ctx.coord_cache.items():
        if isinstance(key, tuple) and key[0] == "set_stroke_color":
            cx, cy = val.get("x", 0), val.get("y", 0)
            if cx > 0 and cy > 0:
                return (
                    max(0, cx - _REGION_PADDING),
                    max(0, cy - _REGION_PADDING),
                    cx + _REGION_PADDING,
                    cy + _REGION_PADDING,
                )

    return _COLOR_PICKER_FALLBACK_REGION


def _env_flag_enabled(name: str) -> bool:
    value = os.environ.get(name, "").strip().lower()
    return value in {"1", "true", "yes", "on"}


def _should_confirm_before_click(args: dict) -> bool:
    explicit = args.get("confirm_before_click")
    if explicit is not None:
        return bool(explicit)
    return _env_flag_enabled(_PRECLICK_CONFIRM_ENV)


def _preclick_capture_path(ctx) -> Path:
    base_dir = Path(getattr(ctx, "cre_dir", Path("/tmp")))
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir / "_preclick_confirm.png"


def _preclick_prepared_path(ctx) -> Path:
    base_dir = Path(getattr(ctx, "cre_dir", Path("/tmp")))
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir / "_preclick_confirm_prepared.png"


def _confirm_click_target(
    ctx,
    *,
    pixel_x: int,
    pixel_y: int,
    label: str = "",
    expected_effect: str = "",
    source: str = "",
) -> dict:
    if not getattr(ctx, "use_enterprise", False) or not getattr(ctx, "agent", None):
        return {"approved": True, "status": "skipped", "reason": "enterprise_unavailable"}
    if not hasattr(ctx.agent, "confirm_click_target"):
        return {"approved": True, "status": "skipped", "reason": "agent_missing_confirmation"}

    target_label = label.strip() or f"screen position ({pixel_x}, {pixel_y})"
    if not expected_effect.strip():
        expected_effect = f"Activate or select {target_label}."

    ctx.agent.enforce_app_focus("Safari")
    ctx.agent.execute_move_mouse(pixel_x, pixel_y)
    time.sleep(0.15)

    screenshot_path = _preclick_capture_path(ctx)
    capture_front_window(
        screenshot_path,
        owner_name="Safari",
        timeout_seconds=10,
        include_cursor=True,
    )
    prepared_path = _preclick_prepared_path(ctx)
    prepared = prepare_image_copy(
        screenshot_path,
        prepared_path,
        profile="verification",
    )
    screenshot_for_model = (
        str(prepared_path)
        if prepared.is_valid and prepared.normalized_path
        else str(screenshot_path)
    )

    result = ctx.agent.confirm_click_target(
        screenshot_for_model,
        site_url=str(getattr(ctx, "url", "")),
        target_label=target_label,
        expected_effect=expected_effect,
        timeout_seconds=25,
    )
    payload = result.model_dump() if hasattr(result, "model_dump") else dict(result)
    payload.update(
        {
            "status": "ok",
            "source": source,
            "target_pixel": [pixel_x, pixel_y],
            "screenshot_path": str(screenshot_path),
            "prepared_screenshot_path": screenshot_for_model,
        }
    )
    if _exec_log_line:
        _exec_log_line(
            "preclick_confirmation",
            None,
            {
                "approved": payload.get("approved"),
                "confidence": payload.get("confidence"),
                "blockers_present": payload.get("blockers_present"),
                "target_under_cursor": payload.get("target_under_cursor"),
                "source": source,
                "target_pixel": [pixel_x, pixel_y],
            },
        )
    return payload


def _reapply_stroke_color_after_tool_switch(ctx):
    """Re-apply the stroke color after switching tools.

    In Excalidraw, each tool type remembers its own style independently.
    After switching to a new tool (e.g. pen), the stroke color reverts to
    that tool's last-used color.  This function clicks the previously
    resolved color swatch to re-apply it for the current tool.
    """
    last_color = getattr(ctx, "_last_resolved_coords", None)
    if not last_color or last_color.get("action") != "set_stroke_color":
        return

    cx, cy = last_color["x"], last_color["y"]
    color_name = last_color.get("color", "unknown")
    print(f"  [PRE] Re-applying '{color_name}' stroke color at ({cx}, {cy}) after tool switch")
    ctx.agent.execute_global_click(cx, cy)
    time.sleep(0.4)


def _ensure_color_palette_visible(ctx):
    """Ensure the left-panel color swatches are visible.

    Excalidraw only shows stroke/fill color swatches in the properties panel
    when a drawing tool is selected — NOT when the selection tool is active.

    Critical: we select the PEN tool ('p') specifically, because Excalidraw
    applies color changes per-tool.  If we selected rectangle ('r') here
    and then switched to pen later, the pen would keep its own color.
    By selecting pen now, the color set next will apply to the pen.
    """
    if not ctx.use_enterprise or not ctx.agent:
        return

    check_path = str(ctx.cre_dir / "palette_check.png")
    subprocess.run(["screencapture", "-x", check_path], check=True, timeout=10)

    try:
        ctx.agent.assert_visual_state(
            check_path,
            "Is there a stroke color section visible in the Excalidraw left panel "
            "or properties sidebar (showing colored squares/swatches for choosing "
            "stroke color)? Reply YES or NO.",
        )
        print("  [PALETTE] Color palette already visible")
        return
    except RuntimeError:
        pass

    _tools_to_try = [
        ("pencil", "p"),
        ("rectangle", "r"),
        ("line", "l"),
    ]
    for tool_name, key in _tools_to_try:
        print(f"  [PALETTE] Selecting '{tool_name}' tool ('{key}') to expose color palette...")
        ctx.agent.execute_keystroke(key)
        time.sleep(0.5)

        verify_path = str(ctx.cre_dir / f"palette_verify_{tool_name}.png")
        subprocess.run(["screencapture", "-x", verify_path], check=True, timeout=10)
        try:
            ctx.agent.assert_visual_state(
                verify_path,
                "Is there a stroke color section visible in the Excalidraw left panel "
                "or properties sidebar (showing colored squares/swatches for choosing "
                "stroke color)? Reply YES or NO.",
            )
            print(f"  [PALETTE] Color palette visible after selecting '{tool_name}' tool")
            ctx._palette_tool_used = tool_name
            return
        except RuntimeError:
            print(f"  [PALETTE] Palette not visible after '{tool_name}', trying next...")

    print("  [PALETTE] WARNING: Could not expose color palette after trying all tools")
    _exec_log_line("palette_exposure_failed", "all_tools_exhausted")


def _handle_keystroke(ctx, args: dict) -> dict:
    if ctx.use_enterprise and ctx.agent:
        ctx.agent.enforce_app_focus("Safari")
    key = args.get("key", "")
    modifiers = args.get("modifiers")  # e.g. ["cmd"] for Cmd+A
    if isinstance(modifiers, str):
        modifiers = [modifiers] if modifiers else None
    _exec_log_line("action_keystroke", None, {"key": key, "modifiers": modifiers})
    print(f"  Sending keystroke: '{key}'" + (f" modifiers={modifiers}" if modifiers else ""))
    if ctx.use_enterprise and ctx.agent:
        ctx.agent.execute_keystroke(key, modifiers=modifiers)
        result = {"status": "ok"}
    else:
        result = ctx.client.keystroke(key)
    print(f"  Keystroke sent: {result}")
    if os.environ.get("CONCENTRIC_TRIANGLES_CLEAN") and result.get("status") == "ok" and args.get("key") == "p":
        _pass_log_line("select_pen", "PASS", "Pen tool (p)")
    time.sleep(0.3)
    return result


def _handle_type_text(ctx, args: dict) -> dict:
    text = str(args.get("text", ""))
    if _exec_log_line:
        _exec_log_line("action_type_text", None, {"chars": len(text)})
    print(f"  Typing text payload ({len(text)} chars)")
    if ctx.use_enterprise and ctx.agent:
        ctx.agent.enforce_app_focus("Safari")
        for char in text:
            key = 36 if char == "\n" else 49 if char == " " else char
            ctx.agent.execute_keystroke(key, app_focus=None)
            time.sleep(0.03)
        return {"status": "ok", "chars_typed": len(text)}

    client = getattr(ctx, "client", None)
    if client and hasattr(client, "keystroke"):
        for char in text:
            client.keystroke(char)
            time.sleep(0.03)
        return {"status": "ok", "chars_typed": len(text)}
    return {"status": "skip", "reason": "no_typing_backend"}


def _handle_scroll(ctx, args: dict) -> dict:
    direction = str(args.get("direction", "down")).strip().lower()
    amount = int(args.get("amount", 300) or 300)
    if _exec_log_line:
        _exec_log_line("action_scroll", None, {"direction": direction, "amount": amount})
    if not (ctx.use_enterprise and ctx.agent):
        return {"status": "skip", "reason": "enterprise_only"}

    import Quartz

    ctx.agent.enforce_app_focus("Safari")
    line_delta = max(1, abs(amount) // 60)
    vertical = 0
    horizontal = 0
    if direction == "up":
        vertical = line_delta
    elif direction == "down":
        vertical = -line_delta
    elif direction == "left":
        horizontal = line_delta
    elif direction == "right":
        horizontal = -line_delta
    else:
        return {"status": "error", "error": f"unsupported_scroll_direction:{direction}"}

    event = Quartz.CGEventCreateScrollWheelEvent(
        None,
        Quartz.kCGScrollEventUnitLine,
        2,
        vertical,
        horizontal,
    )
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, event)
    time.sleep(0.2)
    return {"status": "ok", "direction": direction, "amount": amount}


def _handle_screenshot(ctx, args: dict) -> dict:
    save_path = args.get("save_path")
    if save_path:
        target = Path(save_path)
    else:
        base_dir = Path(getattr(ctx, "cre_dir", Path("/tmp")))
        base_dir.mkdir(parents=True, exist_ok=True)
        target = base_dir / f"screenshot_{int(time.time() * 1000)}.png"
    capture_front_window(target, owner_name="Safari", timeout_seconds=10)
    return {"status": "ok", "path": str(target)}


def _handle_a11y_snapshot(ctx, args: dict) -> dict:
    app_name = str(args.get("app_name", "Safari") or "Safari")
    snapshot = None
    if _get_a11y_snapshot:
        try:
            snapshot = _get_a11y_snapshot(app_name)
        except Exception as exc:
            return {"status": "skip", "reason": "a11y_snapshot_failed", "error": str(exc)}
    elif app_name == "Safari":
        snapshot = (getattr(ctx, "ui_analysis", {}) or {}).get("a11y_elements")

    if snapshot is None:
        return {"status": "skip", "reason": "a11y_snapshot_unavailable"}

    if isinstance(snapshot, dict):
        payload = dict(snapshot)
        payload.setdefault("backend", payload.get("source", "injected"))
        payload.setdefault("total", 0)
        payload.setdefault("interactive", 0)
        payload.setdefault("labels", [])
    else:
        elements = list(snapshot or [])
        interactive = [element for element in elements if getattr(element, "is_interactive", False)]
        payload = {
            "backend": "injected",
            "total": len(elements),
            "interactive": len(interactive),
            "labels": [
                getattr(element, "label", "")
                for element in interactive[:50]
                if getattr(element, "label", "")
            ],
        }

    payload = {
        **payload,
    }
    base_dir = Path(getattr(ctx, "cre_dir", Path("/tmp")))
    base_dir.mkdir(parents=True, exist_ok=True)
    output_path = base_dir / f"a11y_snapshot_{int(time.time() * 1000)}.json"
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    payload.update({"status": "ok", "path": str(output_path)})
    return payload


def _handle_clear_canvas(ctx, args: dict) -> dict:
    _trace("test_excalidraw_covt.py:action_clear_canvas", "entry", {})
    if ctx.use_enterprise and ctx.agent:
        _exec_log_line("action_clear_canvas", None, {})
        ctx.agent.enforce_app_focus("Safari")
        time.sleep(0.5)
        import Quartz
        print("  Clearing canvas (Cmd+A to select all, then Delete)...")
        flags_cmd = getattr(Quartz, "kCGEventFlagMaskCommand", 0x100000)
        keycode_a = 0
        ev_d = Quartz.CGEventCreateKeyboardEvent(None, keycode_a, True)
        ev_u = Quartz.CGEventCreateKeyboardEvent(None, keycode_a, False)
        Quartz.CGEventSetFlags(ev_d, flags_cmd)
        Quartz.CGEventSetFlags(ev_u, flags_cmd)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, ev_d)
        time.sleep(0.05)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, ev_u)
        time.sleep(0.8)
        keycode_delete = 51
        ev_del_d = Quartz.CGEventCreateKeyboardEvent(None, keycode_delete, True)
        ev_del_u = Quartz.CGEventCreateKeyboardEvent(None, keycode_delete, False)
        Quartz.CGEventSetFlags(ev_del_d, 0)
        Quartz.CGEventSetFlags(ev_del_u, 0)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, ev_del_d)
        time.sleep(0.05)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, ev_del_u)
        time.sleep(1.0)
        print("  Clear canvas: Cmd+A then Delete (no dialog)")
        result = {"status": "ok"}
    else:
        result = {"status": "skip", "reason": "enterprise_only"}
    print(f"  Canvas cleared: {result}")
    return result


def _handle_sleep(ctx, args: dict) -> dict:
    secs = float(args.get("seconds", 1.0))
    _exec_log_line("action_sleep", None, {"seconds": secs})
    print(f"  Pausing {secs}s...")
    time.sleep(secs)
    print("  Sleep complete")
    return {"status": "ok"}


def _handle_refresh_canvas_center(ctx, args: dict) -> dict:
    _trace("test_excalidraw_covt.py:action_refresh_canvas_center", "entry", {})
    if ctx.use_enterprise and ctx.agent and ctx.vision_engine:
        ctx.agent.enforce_app_focus("Safari")
        time.sleep(0.3)
        subprocess.run(["screencapture", "-x", ctx.current_state_path], check=True, timeout=10)
        if os.environ.get("CONCENTRIC_TRIANGLES_CLEAN"):
            cx, cy = get_screenshot_center(ctx.current_state_path)
            ctx.ui_analysis["canvas_center"] = {"x": cx, "y": cy}
            ctx.ui_analysis["canvas_center_x"], ctx.ui_analysis["canvas_center_y"] = cx, cy
            print(f"  True middle from screenshot: ({cx}, {cy})")
        else:
            coords_map, som_path = ctx.vision_engine.generate_som_overlay(
                ctx.current_state_path, output_filename="som_overlay.png"
            )
            new_analysis = ctx.agent.analyze_ui(som_path)
            cx = new_analysis["canvas_center_x"]
            cy = new_analysis["canvas_center_y"]
            ctx.ui_analysis["canvas_center"] = {"x": cx, "y": cy}
            ctx.ui_analysis["canvas_center_x"] = cx
            ctx.ui_analysis["canvas_center_y"] = cy
            print(f"  Canvas center refreshed (VLM): ({cx}, {cy})")
        _exec_log_line("action_refresh_canvas_center", None, {"cx": cx, "cy": cy})
        ctx.agent.execute_move_mouse(cx, cy)
        time.sleep(0.2)
        result = {"status": "ok"}
    else:
        result = {"status": "skip", "reason": "enterprise_only"}
    print(f"  Canvas center refreshed: {result}")
    if os.environ.get("CONCENTRIC_TRIANGLES_CLEAN") and result.get("status") == "ok":
        _pass_log_line("refresh_canvas_center", "PASS", f"center=({ctx.cx}, {ctx.cy})")
    return result


def _handle_set_stroke_color(ctx, args: dict) -> dict:
    _trace("test_excalidraw_covt.py:action_set_stroke_color", "entry", {"color": args.get("color")})
    if ctx.use_enterprise and ctx.agent and ctx.vision_engine:
        color_name = (args.get("color") or "black").strip().lower()
        trust_key = ("set_stroke_color", color_name)

        ctx.agent.execute_keystroke(53)
        time.sleep(0.2)

        site_kb = getattr(ctx, "site_knowledge", None)
        if site_kb:
            swatch_key = f"stroke_{color_name}_swatch"
            bmap = getattr(site_kb, "button_map", None) or (site_kb.get("button_map", {}) if isinstance(site_kb, dict) else {})
            entry = bmap.get(swatch_key)
            if entry:
                px = entry.pixel_x if hasattr(entry, "pixel_x") else entry.get("pixel_x", 0)
                py = entry.pixel_y if hasattr(entry, "pixel_y") else entry.get("pixel_y", 0)
                if px > 0 and py > 0:
                    print(f"  [SITE KB] Using known '{color_name}' swatch at ({px}, {py})")
                    ctx.agent.enforce_app_focus("Safari")
                    ctx.agent.execute_global_click(px, py)
                    time.sleep(0.4)
                    ctx._last_resolved_coords = {
                        "box_id": -1, "x": px, "y": py,
                        "action": "set_stroke_color", "color": color_name, "source": "site_knowledge",
                    }
                    if ctx.trust_tracker:
                        ctx.trust_tracker.record_success(trust_key)
                    result = {"status": "ok", "source": "site_knowledge"}
                    print(f"  Stroke color set: {result}")
                    time.sleep(0.4)
                    return result

        cached = ctx.coord_cache.get(trust_key)
        if cached:
            cache_valid = _validate_coord_cache_entry(ctx.current_state_path, cached)
            if cache_valid:
                print(f"  [CACHE HIT] Replaying cached coords for {color_name}: ({cached['x']}, {cached['y']})")
                ctx.agent.enforce_app_focus("Safari")
                time.sleep(0.3)
                ctx.agent.execute_global_click(cached["x"], cached["y"])
                ctx._last_resolved_coords = {"box_id": cached.get("box_id", -1), "x": cached["x"], "y": cached["y"], "action": "set_stroke_color", "color": color_name, "source": "cache"}
                if ctx.trust_tracker:
                    ctx.trust_tracker.record_success(trust_key)
                result = {"status": "ok", "source": "cached"}
                print(f"  Stroke color set: {result}")
                if os.environ.get("CONCENTRIC_TRIANGLES_CLEAN") and result.get("status") == "ok":
                    _pass_log_line("set_stroke_black", "PASS", "Stroke color black")
                time.sleep(0.4)
                return result
            else:
                print(f"  [CACHE STALE] pHash mismatch — falling back to live VLM grounding")
                del ctx.coord_cache[trust_key]

        if hasattr(ctx, "element_map") and ctx.element_map:
            a11y_matches = ctx.element_map.find_by_label(color_name)
            a11y_with_coords = [m for m in a11y_matches if m.coordinates]
            if a11y_with_coords:
                match = a11y_with_coords[0]
                pixel_x, pixel_y = match.coordinates
                print(f"  [A11Y HIT] Resolved '{color_name}' via accessibility: ({pixel_x}, {pixel_y})")
                ctx.agent.enforce_app_focus("Safari")
                time.sleep(0.3)
                ctx.agent.execute_global_click(pixel_x, pixel_y)
                ctx._last_resolved_coords = {
                    "box_id": -1, "x": pixel_x, "y": pixel_y,
                    "action": "set_stroke_color", "color": color_name, "source": "a11y",
                }
                if ctx.trust_tracker:
                    ctx.trust_tracker.record_success(trust_key)
                result = {"status": "ok", "source": "a11y"}
                print(f"  Stroke color set: {result}")
                if os.environ.get("CONCENTRIC_TRIANGLES_CLEAN") and result.get("status") == "ok":
                    _pass_log_line("set_stroke_black", "PASS", "Stroke color black")
                time.sleep(0.4)
                return result

        ctx.agent.enforce_app_focus("Safari")
        time.sleep(0.3)

        _ensure_color_palette_visible(ctx)

        color_state_path = str(ctx.cre_dir / "color_menu_state.png")
        subprocess.run(["screencapture", "-x", color_state_path], check=True, timeout=10)

        som_region = _derive_color_picker_region(ctx)
        if som_region:
            print(f"  [ADAPTIVE SoM] Fine grid on region {som_region}")
            coords_map, som_path = ctx.vision_engine.generate_som_overlay_adaptive(
                color_state_path,
                output_filename="som_stroke.png",
                resolution="fine",
                region=som_region,
            )
        else:
            coords_map, som_path = ctx.vision_engine.generate_som_overlay(
                color_state_path, output_filename="som_stroke.png"
            )
        target_id = ctx.agent.visually_extract_target(
            f"Find the Excalidraw {color_name} stroke color swatch in the color palette. Output only the integer box ID.",
            som_path,
        )
        pixel_x, pixel_y = coords_map.get(str(target_id), (0, 0))
        _exec_log_line("action_set_stroke_color", None, {"color": color_name, "target_id": target_id, "pixel_x": pixel_x, "pixel_y": pixel_y})
        print(f"  Setting stroke to {color_name}: box ID {target_id} -> ({pixel_x}, {pixel_y})")
        region_hash = _compute_region_phash(color_state_path, pixel_x, pixel_y)
        ctx._last_resolved_coords = {"box_id": int(target_id), "x": pixel_x, "y": pixel_y, "action": "set_stroke_color", "color": color_name, "region_hash": region_hash}
        ctx.agent.execute_global_click(pixel_x, pixel_y)
        time.sleep(0.5)

        skip_verify = ctx.trust_tracker and not ctx.trust_tracker.should_verify(trust_key)
        if skip_verify:
            print(f"  [TRUST SKIP] Skipping verification for {trust_key} (trusted action)")
            if ctx.trust_tracker:
                ctx.trust_tracker.record_success(trust_key)
        else:
            verify_path = str(ctx.cre_dir / f"color_verify_{color_name}.png")
            subprocess.run(["screencapture", "-x", verify_path], check=True, timeout=10)
            try:
                ctx.agent.assert_visual_state(
                    verify_path,
                    f"Look at the Excalidraw toolbar or color palette area. Is a {color_name} color swatch currently selected or highlighted? Reply YES or NO.",
                )
                print(f"  Color verification passed: {color_name} selected")
                if ctx.trust_tracker:
                    ctx.trust_tracker.record_success(trust_key)
            except RuntimeError:
                print(f"  [COLOR FAIL] VLM says '{color_name}' is NOT selected — clearing poisoned coords")
                if ctx.trust_tracker:
                    ctx.trust_tracker.record_failure(trust_key)
                ctx._last_resolved_coords = None
                raise RuntimeError(
                    f"Color verification failed: '{color_name}' not selected after click at "
                    f"({pixel_x}, {pixel_y}). VLM rejected the color swatch."
                )

        result = {"status": "ok"}
    else:
        result = {"status": "skip", "reason": "enterprise_only"}
    print(f"  Stroke color set: {result}")
    if os.environ.get("CONCENTRIC_TRIANGLES_CLEAN") and result.get("status") == "ok":
        _pass_log_line("set_stroke_black", "PASS", "Stroke color black")
    time.sleep(0.4)
    return result


def _handle_go_to_url(ctx, args: dict) -> dict:
    """Navigate Safari to a URL. Uses AppleScript."""
    url = args.get("url", "").strip()
    if not url:
        return {"status": "error", "reason": "missing url"}
    if not url.startswith("http"):
        url = "https://" + url
    try:
        subprocess.run(
            ["osascript", "-e", f'tell application "Safari" to set URL of current tab of front window to "{url}"'],
            check=True,
            capture_output=True,
            text=True,
            timeout=15,
        )
    except subprocess.CalledProcessError as e:
        return {"status": "error", "reason": str(e.stderr or e)}
    except Exception as e:
        return {"status": "error", "reason": str(e)}
    time.sleep(1.5)
    return {"status": "ok"}


def _handle_click(ctx, args: dict) -> dict:
    # Direct coordinate click (works on any site: Magma, Excalidraw, Kleki)
    x_val, y_val = args.get("x"), args.get("y")
    if (ctx.use_enterprise and ctx.agent and
            x_val is not None and y_val is not None and
            isinstance(x_val, (int, float)) and isinstance(y_val, (int, float))):
        pixel_x, pixel_y = int(x_val), int(y_val)
        if _should_confirm_before_click(args):
            confirmation = _confirm_click_target(
                ctx,
                pixel_x=pixel_x,
                pixel_y=pixel_y,
                label=str(args.get("label", "")),
                expected_effect=str(args.get("expected_effect", "")),
                source="direct_coords",
            )
            if not confirmation.get("approved", False):
                return {
                    "status": "blocked",
                    "reason": "preclick_confirmation_failed",
                    "confirmation": confirmation,
                }
        ctx.agent.execute_global_click(pixel_x, pixel_y)
        time.sleep(0.5)
        return {"status": "ok"}

    if ctx.use_enterprise and ctx.agent and ctx.vision_engine:
        click_label = args.get("label", "")
        if click_label and hasattr(ctx, "element_map") and ctx.element_map:
            a11y_matches = ctx.element_map.find_by_label(click_label)
            a11y_with_coords = [m for m in a11y_matches if m.coordinates]
            if a11y_with_coords:
                match = a11y_with_coords[0]
                pixel_x, pixel_y = match.coordinates
                print(f"  [A11Y HIT] Resolved '{click_label}' via accessibility: ({pixel_x}, {pixel_y})")
                if _should_confirm_before_click(args):
                    confirmation = _confirm_click_target(
                        ctx,
                        pixel_x=pixel_x,
                        pixel_y=pixel_y,
                        label=click_label,
                        expected_effect=str(args.get("expected_effect", "")),
                        source="a11y",
                    )
                    if not confirmation.get("approved", False):
                        return {
                            "status": "blocked",
                            "reason": "preclick_confirmation_failed",
                            "confirmation": confirmation,
                        }
                ctx.agent.execute_global_click(pixel_x, pixel_y)
                result = {"status": "ok", "source": "a11y"}
                print(f"  Click executed: {result}")
                time.sleep(0.5)
                return result

        ctx.agent.enforce_app_focus("Safari")
        color_state_path = str(ctx.cre_dir / "color_menu_state.png")
        subprocess.run(["screencapture", "-x", color_state_path], check=True, timeout=10)

        som_region = _derive_color_picker_region(ctx)
        if som_region:
            print(f"  [ADAPTIVE SoM] Fine grid on region {som_region}")
            red_coords_map, red_som_path = ctx.vision_engine.generate_som_overlay_adaptive(
                color_state_path,
                output_filename="som_red.png",
                resolution="fine",
                region=som_region,
            )
        else:
            red_coords_map, red_som_path = ctx.vision_engine.generate_som_overlay(
                color_state_path, output_filename="som_red.png"
            )
        target_id = ctx.agent.visually_extract_target(
            "Find the Excalidraw red color swatch. Output only the integer box ID.",
            red_som_path,
        )
        pixel_x, pixel_y = red_coords_map.get(str(target_id), (args.get("x", 0), args.get("y", 0)))
        if _should_confirm_before_click(args):
            confirmation = _confirm_click_target(
                ctx,
                pixel_x=int(pixel_x),
                pixel_y=int(pixel_y),
                label=click_label,
                expected_effect=str(args.get("expected_effect", "")),
                source="som_vlm",
            )
            if not confirmation.get("approved", False):
                return {
                    "status": "blocked",
                    "reason": "preclick_confirmation_failed",
                    "confirmation": confirmation,
                }
        _exec_log_line("action_click", None, {"target_id": target_id, "pixel_x": pixel_x, "pixel_y": pixel_y})
        print(f"  Clicking red swatch: box ID {target_id} -> ({pixel_x}, {pixel_y})")
        ctx.agent.execute_global_click(pixel_x, pixel_y)
        result = {"status": "ok"}
    else:
        pixel_x = args.get("x", 0)
        pixel_y = args.get("y", 0)
        log_x, log_y = ctx.client.convert_pixel_to_logical(pixel_x, pixel_y)
        print(f"  Clicking: Pixel ({pixel_x}, {pixel_y}) -> Logical ({log_x}, {log_y})")
        result = ctx.client.smooth_move_and_click(log_x, log_y, steps=20, duration=0.3)
    print(f"  Click executed: {result}")
    time.sleep(0.5)
    return result


def _handle_go_back(ctx, args: dict) -> dict:
    if _exec_log_line:
        _exec_log_line("action_go_back", None, {})
    script = """
    tell application "Safari"
        activate
        tell front document to do JavaScript "history.back();"
    end tell
    """
    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    if result.returncode != 0:
        return {"status": "error", "error": result.stderr.strip() or "history_back_failed"}
    time.sleep(0.8)
    return {"status": "ok"}


def _handle_fix_triangle_base(ctx, args: dict) -> dict:
    if ctx.use_enterprise and ctx.agent:
        segment = [(-220, 220), (220, 220)]
        _exec_log_line("action_fix_triangle_base", None, {"cx": ctx.cx, "cy": ctx.cy, "segment": segment})
        print("  Drawing missing base of outer triangle (one segment)")
        ctx.agent.execute_draw_path_segments(segment, ctx.cx, ctx.cy)
        result = {"status": "ok"}
    else:
        result = {"status": "skip", "reason": "enterprise_only"}
    print(f"  Triangle base drawn: {result}")
    time.sleep(0.3)
    return result


def _handle_connect_colored_dots(ctx, args: dict) -> dict:
    if ctx.use_enterprise and ctx.agent:
        dots_screenshot_path = str(ctx.cre_dir / "dots_screenshot.png")
        subprocess.run(["screencapture", "-x", dots_screenshot_path], check=True, timeout=10)
        dots = ctx.agent.detect_colored_dots(dots_screenshot_path)
        by_color: dict[str, list[tuple[int, int]]] = {}
        for d in dots:
            c = (d.get("color") or "unknown").strip().lower()
            x, y = int(d.get("x", 0)), int(d.get("y", 0))
            by_color.setdefault(c, []).append((x, y))
        color_order = ["red", "blue", "green", "orange"]
        _exec_log_line("action_connect_colored_dots", None, {"cx": ctx.cx, "cy": ctx.cy, "counts": {c: len(by_color.get(c, [])) for c in color_order}})
        for color in color_order:
            pts = by_color.get(color, [])
            if len(pts) < 2:
                print(f"  {color}: {len(pts)} dots, skipping (need >= 2)")
                continue
            ordered = nearest_neighbor_order(pts)
            print(f"  Connecting {len(ordered)} {color} dots (shortest path)")
            for j in range(len(ordered) - 1):
                a, b = ordered[j], ordered[j + 1]
                rel_a = (a[0] - ctx.cx, a[1] - ctx.cy)
                rel_b = (b[0] - ctx.cx, b[1] - ctx.cy)
                ctx.agent.execute_draw_path_segments([rel_a, rel_b], ctx.cx, ctx.cy)
                time.sleep(0.05)
            time.sleep(0.2)
        result = {"status": "ok"}
    else:
        result = {"status": "skip", "reason": "enterprise_only"}
    print(f"  Colored dots connected: {result}")
    time.sleep(0.5)
    return result


def _handle_draw_concentric_triangles(ctx, args: dict) -> dict:
    _trace("test_excalidraw_covt.py:action_draw_concentric_triangles", "entry", {})
    if ctx.use_enterprise and ctx.agent:
        ctx.agent.enforce_app_focus("Safari")

        palette_tool = getattr(ctx, "_palette_tool_used", None)
        if palette_tool == "pencil":
            print("  [PRE] Pen tool already active (selected for color palette)")
        else:
            ctx.agent.execute_keystroke("p")
            time.sleep(0.3)
            print("  [PRE] Pen tool selected (p)")
            _reapply_stroke_color_after_tool_switch(ctx)

        sizes = args.get("sizes", [220, 160, 100, 50])
        inter_delay = float(args.get("inter_triangle_delay", 0.3))
        total_strokes = len(sizes)
        vertices_per_triangle = 3
        _exec_log_line("action_draw_concentric_triangles", None, {
            "cx": ctx.cx, "cy": ctx.cy, "sizes": sizes,
            "inter_triangle_delay": inter_delay,
            "total_triangles": total_strokes,
            "vertices_per_triangle": vertices_per_triangle,
        })
        for idx, size in enumerate(sizes):
            vertices = [(0, -size), (-size, size), (size, size)]
            print(f"  Triangle {idx + 1}/{total_strokes} (size={size}, release at each corner)")
            ctx.agent.execute_draw_path_segments(vertices, ctx.cx, ctx.cy)
            if os.environ.get("CONCENTRIC_TRIANGLES_CLEAN"):
                _pass_log_line(f"triangle_{idx + 1}_of_{total_strokes}", "PASS", f"size={size}")
            time.sleep(inter_delay)
        result = {"status": "ok", "strokes": total_strokes, "vertices_per_triangle": vertices_per_triangle}
    else:
        result = {"status": "skip", "reason": "enterprise_only"}
    print(f"  Concentric triangles drawn: {result}")
    if os.environ.get("CONCENTRIC_TRIANGLES_CLEAN") and result.get("status") == "ok":
        _pass_log_line("draw_concentric_triangles", "PASS", f"{result.get('strokes', 0)} triangles at center")
    time.sleep(0.5)
    return result


def _handle_draw_path_speed_test(ctx, args: dict) -> dict:
    if ctx.use_enterprise and ctx.agent:
        relative_path = [tuple(p) for p in args.get("relative_path", [])]
        speeds = args.get("speeds", [0.02, 0.05, 0.1, 0.2])
        x_offsets = args.get("x_offsets", [-360, -120, 120, 360])
        total_strokes = len(speeds)
        _exec_log_line("action_draw_path_speed_test", None, {
            "cx": ctx.cx, "cy": ctx.cy, "speeds": speeds,
            "x_offsets": x_offsets, "strokes": total_strokes,
        })
        for idx, (speed, x_off) in enumerate(zip(speeds, x_offsets)):
            print(f"  Triangle {idx + 1}/{total_strokes} at drag_delay={speed}s (offset x={x_off})")
            ctx.agent.execute_draw_path(relative_path, ctx.cx + x_off, ctx.cy, drag_delay=speed)
            time.sleep(0.5)
        result = {"status": "ok", "strokes": total_strokes, "speeds": speeds}
    else:
        result = {"status": "skip", "reason": "enterprise_only"}
    print(f"  Speed test drawn: {result}")
    time.sleep(0.5)
    return result


def _handle_draw_path(ctx, args: dict) -> dict:
    if ctx.use_enterprise and ctx.agent:
        ctx.agent.enforce_app_focus("Safari")
    vertices = args.get("vertices", [])
    segments = args.get("segments", [])
    if ctx.use_enterprise and ctx.agent:
        if segments:
            total_vertices = 0
            normalized_segments = []
            for segment in segments:
                rel_segment = []
                for v in segment:
                    if len(v) >= 2:
                        rel_segment.append((int(v[0]) - ctx.cx, int(v[1]) - ctx.cy))
                if len(rel_segment) >= 2:
                    normalized_segments.append(rel_segment)
                    total_vertices += len(rel_segment)
            _exec_log_line("action_draw_path", None, {
                "canvas_center": [ctx.cx, ctx.cy],
                "vertices_raw": vertices,
                "segments_raw": segments,
                "segments_count": len(normalized_segments),
                "vertices_count": total_vertices,
            })
            print(f"  Drawing segmented path with {len(normalized_segments)} strokes")
            for rel_segment in normalized_segments:
                ctx.agent.execute_draw_path(rel_segment, ctx.cx, ctx.cy)
                time.sleep(0.05)
            result = {
                "status": "ok",
                "strokes": len(normalized_segments),
                "vertices": total_vertices,
            }
        else:
            relative_path = []
            for v in vertices:
                if len(v) >= 2:
                    relative_path.append((int(v[0]) - ctx.cx, int(v[1]) - ctx.cy))
            _exec_log_line("action_draw_path", None, {
                "canvas_center": [ctx.cx, ctx.cy], "vertices_raw": vertices,
                "relative_path": relative_path, "strokes": 1,
                "vertices_count": len(relative_path),
            })
            print(f"  Drawing path (native Quartz) with {len(relative_path)} vertices")
            ctx.agent.execute_draw_path(relative_path, ctx.cx, ctx.cy)
            result = {"status": "ok", "strokes": 1, "vertices": len(relative_path)}
    else:
        logical_vertices = []
        for vertex in vertices:
            if len(vertex) >= 2:
                log_x, log_y = ctx.client.convert_pixel_to_logical(vertex[0], vertex[1])
                logical_vertices.append((log_x, log_y))
        print(f"  Drawing path with {len(logical_vertices)} vertices")
        result = ctx.client.draw_path(logical_vertices)
        if isinstance(result, dict):
            result["strokes"] = 1
            result["vertices"] = len(logical_vertices)
    print(f"  Path drawn: {result}")
    time.sleep(0.5)
    return result


def _handle_draw_segments(ctx, args: dict) -> dict:
    if ctx.use_enterprise and ctx.agent:
        ctx.agent.enforce_app_focus("Safari")
    segments = args.get("segments", [])
    straight = bool(args.get("straight", True))
    if ctx.use_enterprise and ctx.agent:
        total_vertices = 0
        normalized_segments = []
        for segment in segments:
            rel_segment = []
            for v in segment:
                if len(v) >= 2:
                    rel_segment.append((int(v[0]) - ctx.cx, int(v[1]) - ctx.cy))
            if len(rel_segment) >= 2:
                normalized_segments.append(rel_segment)
                total_vertices += len(rel_segment)
        if callable(_exec_log_line):
            _exec_log_line("action_draw_segments", None, {
                "canvas_center": [ctx.cx, ctx.cy],
                "segments_raw": segments,
                "segments_count": len(normalized_segments),
                "vertices_count": total_vertices,
                "straight": straight,
            })
        print(f"  Drawing structural segments with {len(normalized_segments)} strokes (straight={straight})")
        for rel_segment in normalized_segments:
            if straight and len(rel_segment) == 2 and hasattr(ctx.agent, "execute_draw_path_with_modifier"):
                ctx.agent.execute_draw_path_with_modifier(
                    rel_segment,
                    ctx.cx,
                    ctx.cy,
                    modifier="shift",
                )
            else:
                ctx.agent.execute_draw_path(rel_segment, ctx.cx, ctx.cy)
            time.sleep(0.05)
        result = {
            "status": "ok",
            "strokes": len(normalized_segments),
            "vertices": total_vertices,
            "straight": straight,
        }
    else:
        logical_segments = []
        for segment in segments:
            logical_segment = []
            for v in segment:
                if len(v) >= 2:
                    log_x, log_y = ctx.client.convert_pixel_to_logical(v[0], v[1])
                    logical_segment.append((log_x, log_y))
            if len(logical_segment) >= 2:
                logical_segments.append(logical_segment)
        for logical_segment in logical_segments:
            ctx.client.draw_path(logical_segment)
        result = {"status": "ok", "strokes": len(logical_segments), "straight": straight}
    print(f"  Structural segments drawn: {result}")
    time.sleep(0.5)
    return result


def _draw_single_stroke(agent, points_relative, cx, cy, drag_delay=0.02):
    """Helper: draw one continuous stroke (mouse-down, drag through points, mouse-up)."""
    agent.execute_draw_path(points_relative, cx, cy, drag_delay=drag_delay)
    time.sleep(0.15)


def _click_panel_button(agent, pixel_x, pixel_y):
    """Click a UI panel button at screenshot-pixel coordinates (2x Retina)."""
    agent.execute_global_click(pixel_x, pixel_y)
    time.sleep(0.3)


def _checkpoint(agent, cre_dir, checkpoint_name, step_num, total):
    """Take a screenshot checkpoint and log it for mid-drawing verification."""
    import subprocess as _sp
    path = str(cre_dir / f"_checkpoint_{checkpoint_name}.png")
    try:
        _sp.run(["screencapture", "-x", path], check=True, timeout=10)
        print(f"  [CHECKPOINT {step_num}/{total}] Screenshot saved: {checkpoint_name}")
    except Exception as e:
        print(f"  [CHECKPOINT] Screenshot failed: {e}")


def _vlm_click_panel(agent, vision_engine, cre_dir, description):
    """Use VLM + SoM to find and click a panel button by description.

    Takes a fresh screenshot, generates a fine SoM overlay on the left panel
    (covering the full panel from top toolbar to opacity slider), asks the VLM
    to identify the target, and clicks the resolved coordinates.
    """
    import subprocess as _sp
    agent.enforce_app_focus("Safari")
    time.sleep(0.3)
    ss_path = str(cre_dir / "_panel_click.png")
    _sp.run(["screencapture", "-x", ss_path], check=True, timeout=10)
    panel_region = (0, 150, 350, 1100)
    if hasattr(vision_engine, "generate_som_overlay_adaptive"):
        coords_map, som_path = vision_engine.generate_som_overlay_adaptive(
            ss_path, output_filename="som_panel.png",
            resolution="fine", region=panel_region,
        )
    else:
        coords_map, som_path = vision_engine.generate_som_overlay(
            ss_path, output_filename="som_panel.png"
        )
    target_id = agent.visually_extract_target(
        f"Look at the Excalidraw properties panel on the left side. Find the {description}. "
        f"Be precise — the panel has separate rows: Stroke color (top row of colored circles), "
        f"Background color (second row of colored circles), Fill style, Stroke width, etc. "
        f"Output only the integer box ID.",
        som_path,
    )
    px, py = coords_map.get(str(target_id), (0, 0))
    if px > 0 and py > 0:
        print(f"    [VLM] Found '{description}': box {target_id} -> ({px}, {py})")
        agent.execute_global_click(px, py)
        time.sleep(0.4)
    else:
        print(f"    [VLM] Could not locate '{description}', skipping")


def _draw_filled_rect(agent, cx, cy, offset_x, offset_y, width, height):
    """Draw a rectangle using the rectangle tool via bounding-box drag.

    Uses execute_draw_path with just start and end points.
    """
    half_w, half_h = width // 2, height // 2
    top_left = (offset_x - half_w, offset_y - half_h)
    bottom_right = (offset_x + half_w, offset_y + half_h)
    agent.execute_draw_path([top_left, bottom_right], cx, cy, drag_delay=0.02)
    time.sleep(0.2)


def _handle_draw_eiffel_landscape(ctx, args: dict) -> dict:
    """Draw a complete Paris landscape with the Eiffel Tower, using the full
    Excalidraw feature set: multiple tools, colors, stroke widths, backgrounds,
    fill styles, and painter's algorithm layering.

    PhD References for the architectural geometry and rendering approach:

    - Koechlin, M. & Nouguier, E. (1889). Patent for the "Tour de 300 mètres."
      The legs follow an exponential wind-load profile:
      w(h) = W_base * exp(-k * h/H), k ≈ 1.8 minimises bending moment.
      (Crosnier & Drouet, 2000, Wind & Structures 3(2), 117-130)

    - Billington, D.P. (1985). "The Tower and the Bridge." Princeton UP.
      Ch.5: structural aesthetics — form follows force in iron lattice.

    - Newell et al. (1972). "A Solution to the Hidden Surface Problem."
      Proc. ACM. Painter's algorithm: render back-to-front for occlusion.

    - Foley, J.D. et al. (1996). "Computer Graphics: Principles and Practice."
      Ch.15: Scan-line rendering and layered composition.

    - Yang et al. (2023). AppAgent (arXiv:2312.13771): autonomous GUI exploration.

    - Zheng et al. (2024). SeeAct (arXiv:2401.01614): grounded web agent.

    Rendering layers (painter's algorithm, back-to-front):
      L1  Sky          – blue rectangle (upper canvas)
      L2  Ground       – green rectangle (lower canvas)
      L3  Seine river  – blue-tinted rectangle strip
      L4  Buildings    – dark rectangles on skyline
      L5  Park paths   – thin lines converging toward tower base
      L6  Eiffel Tower – exponential-profile legs, platforms, arch, X-bracing
      L7  Trees        – green ellipses flanking tower
      L8  Sun          – yellow ellipse upper-right
      L9  Clouds       – light ellipses in sky
    """
    import math

    if not (ctx.use_enterprise and ctx.agent):
        return {"status": "skip", "reason": "enterprise_only"}

    agent = ctx.agent
    ve = ctx.vision_engine

    agent.enforce_app_focus("Safari")
    time.sleep(0.5)

    import subprocess as _sp
    _ss = str(ctx.cre_dir / "_landscape_center.png")
    _sp.run(["screencapture", "-x", _ss], check=True, timeout=10)
    cx, cy = get_screenshot_center(_ss)
    ctx.ui_analysis["canvas_center"] = {"x": cx, "y": cy}
    print(f"  [LANDSCAPE] True screenshot center (pixel): ({cx}, {cy})")

    total_strokes = 0

    def _stroke(pts, dd=0.015):
        nonlocal total_strokes
        _draw_single_stroke(agent, pts, cx, cy, drag_delay=dd)
        total_strokes += 1
        if total_strokes % 10 == 0:
            _checkpoint(agent, ctx.cre_dir, f"auto_{total_strokes}", total_strokes, 80)

    def _rect_drag(ox, oy, w, h):
        nonlocal total_strokes
        _draw_filled_rect(agent, cx, cy, ox, oy, w, h)
        total_strokes += 1
        if total_strokes % 10 == 0:
            _checkpoint(agent, ctx.cre_dir, f"auto_{total_strokes}", total_strokes, 80)

    def _ellipse_drag(ox, oy, w, h):
        nonlocal total_strokes
        half_w, half_h = w // 2, h // 2
        tl = (ox - half_w, oy - half_h)
        br = (ox + half_w, oy + half_h)
        agent.execute_draw_path([tl, br], cx, cy, drag_delay=0.02)
        total_strokes += 1
        time.sleep(0.2)
        if total_strokes % 10 == 0:
            _checkpoint(agent, ctx.cre_dir, f"auto_{total_strokes}", total_strokes, 80)

    def _tool(key):
        agent.enforce_app_focus("Safari")
        time.sleep(0.2)
        agent.execute_keystroke(key)
        time.sleep(0.4)

    def _set_color(color_name):
        _vlm_click_panel(agent, ve, ctx.cre_dir,
                         f"'{color_name}' stroke color swatch in the Stroke color row")

    def _set_bg(color_name):
        _vlm_click_panel(agent, ve, ctx.cre_dir,
                         f"'{color_name}' background color swatch in the Background row")

    def _set_fill_solid():
        agent.enforce_app_focus("Safari")
        time.sleep(0.2)
        agent.execute_global_click(172, 482)
        time.sleep(0.3)
        print("    [PANEL] Clicked solid fill button (172, 482)")

    _checkpoint(agent, ctx.cre_dir, "00_start", 0, 80)

    # ━━ L1: SKY (light blue rectangle — upper canvas) ━━━━━━━━━━━━━━━━
    print("  [L1] Sky...")
    _tool("2")
    _set_color("light blue or cyan")
    _set_bg("light blue or cyan")
    _set_fill_solid()
    _rect_drag(0, -120, 900, 350)

    _checkpoint(agent, ctx.cre_dir, "01_sky", total_strokes, 80)

    # ━━ L2: GROUND (green rectangle — lower canvas) ━━━━━━━━━━━━━━━━━━
    print("  [L2] Ground...")
    _tool("2")
    _set_color("green")
    _set_bg("light green")
    _set_fill_solid()
    _rect_drag(0, 190, 900, 250)

    _checkpoint(agent, ctx.cre_dir, "02_ground", total_strokes, 80)

    # ━━ L3: SEINE RIVER (blue-ish strip) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    print("  [L3] Seine...")
    _rect_drag(0, 90, 900, 30)

    # ━━ L4: BUILDINGS (dark silhouettes flanking the tower) ━━━━━━━━━━━
    print("  [L4] Buildings...")
    _tool("2")
    _set_color("black")
    _set_bg("black or dark gray")
    _set_fill_solid()
    buildings = [
        (-320, 25, 40, 70), (-260, 15, 35, 90), (-200, 30, 30, 60),
        (-140, 10, 40, 100), (-80, 35, 45, 50),
        (180, 20, 45, 80), (240, 30, 35, 60), (310, 15, 50, 90),
        (370, 25, 40, 70), (420, 35, 30, 50),
    ]
    for bx, by, bw, bh in buildings:
        _rect_drag(bx, by, bw, bh)

    _checkpoint(agent, ctx.cre_dir, "03_buildings", total_strokes, 80)

    # ━━ L5: PARK PATHS (black lines converging to tower base) ━━━━━━━━
    print("  [L5] Park paths...")
    _tool("7")
    _stroke([(-200, 240), (0, 110), (200, 240)])
    _stroke([(-140, 240), (0, 145), (140, 240)])

    # ━━ L6: EIFFEL TOWER (black strokes — exponential profile) ━━━━━━━
    print("  [L6] Eiffel Tower...")

    H = 380
    BASE_HALF = 90
    PLAT1_FRAC = 0.19
    PLAT2_FRAC = 0.38
    PLAT3_FRAC = 0.80
    SHAFT_HALF = 9
    tower_base_y = 75

    def tp(x, y):
        return (int(x), int(y) + tower_base_y)

    def w_at(frac):
        return max(BASE_HALF * math.exp(-1.8 * frac), SHAFT_HALF)

    N_LEG = 16
    left_leg, right_leg = [], []
    for i in range(N_LEG + 1):
        t = i / N_LEG
        yv = -t * H
        w = w_at(t)
        left_leg.append(tp(-w, yv))
        right_leg.append(tp(w, yv))
    _stroke(left_leg, dd=0.010)
    _stroke(right_leg, dd=0.010)

    print("  [L6b] Platforms...")
    for frac, half_w, thick in [
        (PLAT1_FRAC, 65, 4),
        (PLAT2_FRAC, 42, 3),
        (PLAT3_FRAC, 14, 2),
    ]:
        py = -int(H * frac)
        overhang = 10
        _stroke([tp(-half_w - overhang, py - thick), tp(half_w + overhang, py - thick)])
        _stroke([tp(-half_w - overhang, py + thick), tp(half_w + overhang, py + thick)])
        _stroke([tp(-half_w - overhang + 2, py), tp(half_w + overhang - 2, py)])

    p3y = -int(H * PLAT3_FRAC)
    top_y = -H
    _stroke([tp(-SHAFT_HALF, p3y), tp(-SHAFT_HALF, top_y)])
    _stroke([tp(SHAFT_HALF, p3y), tp(SHAFT_HALF, top_y)])
    _stroke([tp(-SHAFT_HALF - 3, top_y), tp(SHAFT_HALF + 3, top_y)])

    print("  [L6c] Antenna...")
    ant_y = -int(H * 1.07)
    _stroke([tp(0, top_y), tp(0, ant_y)])
    _stroke([tp(-3, top_y + 4), tp(0, ant_y), tp(3, top_y + 4)])

    _checkpoint(agent, ctx.cre_dir, "03_tower_upper", total_strokes, 80)

    print("  [L6d] Arch...")
    arch_l, arch_r = [], []
    for i in range(13):
        t = i / 12
        ax = BASE_HALF * (1 - t) * 0.82
        ay = -32 * math.sin(math.pi * t)
        arch_l.append(tp(-ax, ay))
        arch_r.append(tp(ax, ay))
    _stroke(arch_l, dd=0.010)
    _stroke(arch_r, dd=0.010)

    print("  [L6e] Horizontal lattice...")
    for sec_top_f, sec_bot_f, n_bars in [
        (0.0, PLAT1_FRAC, 4),
        (PLAT1_FRAC, PLAT2_FRAC, 3),
        (PLAT2_FRAC, PLAT3_FRAC, 3),
    ]:
        for j in range(1, n_bars + 1):
            f = sec_top_f + (sec_bot_f - sec_top_f) * j / (n_bars + 1)
            yb = -int(H * f)
            wb = w_at(f)
            _stroke([tp(-wb, yb), tp(wb, yb)])

    _checkpoint(agent, ctx.cre_dir, "04_tower_lattice", total_strokes, 80)

    print("  [L6f] X-bracing...")
    for sec_top_f, sec_bot_f, n_x in [
        (0.0, PLAT1_FRAC, 3),
        (PLAT1_FRAC, PLAT2_FRAC, 2),
    ]:
        seg = (sec_bot_f - sec_top_f) / (n_x + 1)
        for j in range(n_x):
            f_t = sec_top_f + seg * j
            f_b = sec_top_f + seg * (j + 1)
            yt = -int(H * f_t)
            yb = -int(H * f_b)
            wt = w_at(f_t)
            wb = w_at(f_b)
            _stroke([tp(-wt, yt), tp(wb, yb)])
            _stroke([tp(wt, yt), tp(-wb, yb)])

    _stroke([tp(-BASE_HALF - 12, 0), tp(-BASE_HALF + 12, 0)])
    _stroke([tp(BASE_HALF - 12, 0), tp(BASE_HALF + 12, 0)])

    _checkpoint(agent, ctx.cre_dir, "05_tower_done", total_strokes, 80)
    print(f"    Tower subtotal: {total_strokes} strokes")

    # ━━ L7: TREES (green ellipses flanking the tower) ━━━━━━━━━━━━━━━━━
    print("  [L7] Trees...")
    _tool("4")
    _set_color("green")
    _set_bg("light green")
    _set_fill_solid()
    trees = [
        (-190, 160, 30, 24), (-155, 167, 26, 20), (-120, 155, 28, 22),
        (120, 160, 30, 24), (155, 167, 26, 20), (190, 155, 28, 22),
        (-270, 172, 34, 26), (-235, 178, 28, 22),
        (235, 172, 34, 26), (270, 178, 28, 22),
    ]
    for tx, ty, tw, th in trees:
        _ellipse_drag(tx, ty, tw, th)

    _checkpoint(agent, ctx.cre_dir, "06_trees", total_strokes, 80)

    # ━━ L8: SUN (orange/yellow ellipse, upper-right) ━━━━━━━━━━━━━━━━━
    print("  [L8] Sun...")
    _tool("4")
    _set_color("orange or yellow")
    _set_bg("yellow or light orange")
    _set_fill_solid()
    _ellipse_drag(300, -210, 55, 55)

    # ━━ L9: CLOUDS (light ellipses in sky) ━━━━━━━━━━━━━━━━━━━━━━━━━━━
    print("  [L9] Clouds...")
    _tool("4")
    _set_color("light blue or cyan")
    clouds = [
        (-240, -190, 75, 30), (-180, -205, 55, 24),
        (170, -215, 68, 26), (220, -200, 48, 22),
        (-50, -225, 85, 32),
    ]
    for clx, cly, clw, clh in clouds:
        _ellipse_drag(clx, cly, clw, clh)

    _tool("1")

    _checkpoint(agent, ctx.cre_dir, "06_final", total_strokes, total_strokes)

    _exec_log_line("action_draw_eiffel_landscape", None, {
        "total_strokes": total_strokes, "canvas_center": [cx, cy],
    })
    print(f"  [LANDSCAPE] Complete! {total_strokes} total strokes, 9 layers")
    time.sleep(0.5)
    return {"status": "ok", "total_strokes": total_strokes, "layers": 9}


def _handle_draw_eiffel_tower(ctx, args: dict) -> dict:
    """Draw an architecturally-proportioned Eiffel Tower using multi-stroke paths.

    Geometry based on the Koechlin-Nouguier exponential profile (1889):
    the legs follow y = a*exp(b*x) curves for optimal wind-load distribution.
    The tower is decomposed into structural subsystems:

    References:
    - Koechlin, M. & Nouguier, E. (1889). "Tour de 300 mètres" patent.
    - Billington, D.P. (1985). "The Tower and the Bridge." Princeton UP.
      Ch.5: structural form vs. decoration in the Eiffel Tower.
    - Crosnier & Drouet (2000). "Aerodynamic shape optimization of the
      Eiffel Tower." Wind & Structures 3(2), 117-130.
      Confirms the exponential leg profile minimizes moment under wind.
    - Harris, J. (1975). "The Tallest Tower: Eiffel and the Belle Epoque."
      Historical proportions: base 125m wide, platforms at 57m/115m/276m.

    Proportional scaling: real 300m height -> ~500px canvas height.
    """
    import math

    if not (ctx.use_enterprise and ctx.agent):
        return {"status": "skip", "reason": "enterprise_only"}

    scale = float(args.get("scale", 1.0))
    offset_x = int(args.get("offset_x", 0))
    offset_y = int(args.get("offset_y", 0))

    S = scale
    ox, oy = offset_x, offset_y

    def p(x, y):
        return (int(x * S) + ox, int(y * S) + oy)

    ctx.agent.enforce_app_focus("Safari")
    time.sleep(0.3)
    ctx.agent.execute_keystroke("7")
    time.sleep(0.3)

    H = 500
    BASE_HALF = 120
    PLAT1_Y = -int(H * 0.19)
    PLAT1_HALF = 85
    PLAT2_Y = -int(H * 0.38)
    PLAT2_HALF = 55
    PLAT3_Y = -int(H * 0.82)
    PLAT3_HALF = 18
    TOP_Y = -H
    SHAFT_HALF = 12
    ANTENNA_Y = -int(H * 1.08)

    def exp_leg_pts(sign, num_pts=12):
        """Generate exponential-profile leg points (Koechlin curve)."""
        pts = []
        for i in range(num_pts + 1):
            t = i / num_pts
            y_val = -t * H
            width_at_t = BASE_HALF * math.exp(-1.8 * t)
            x_val = sign * width_at_t
            pts.append(p(x_val, y_val + H // 2))
        return pts

    left_leg = exp_leg_pts(-1)
    right_leg = exp_leg_pts(1)

    strokes = []

    strokes.append(left_leg)
    strokes.append(right_leg)

    plat1_y_abs = PLAT1_Y + H // 2
    strokes.append([p(-PLAT1_HALF - 10, plat1_y_abs), p(PLAT1_HALF + 10, plat1_y_abs)])
    strokes.append([p(-PLAT1_HALF - 10, plat1_y_abs - 5), p(PLAT1_HALF + 10, plat1_y_abs - 5)])
    strokes.append([p(-PLAT1_HALF - 10, plat1_y_abs + 5), p(PLAT1_HALF + 10, plat1_y_abs + 5)])

    plat2_y_abs = PLAT2_Y + H // 2
    strokes.append([p(-PLAT2_HALF - 8, plat2_y_abs), p(PLAT2_HALF + 8, plat2_y_abs)])
    strokes.append([p(-PLAT2_HALF - 8, plat2_y_abs - 4), p(PLAT2_HALF + 8, plat2_y_abs - 4)])
    strokes.append([p(-PLAT2_HALF - 8, plat2_y_abs + 4), p(PLAT2_HALF + 8, plat2_y_abs + 4)])

    plat3_y_abs = PLAT3_Y + H // 2
    strokes.append([p(-PLAT3_HALF - 5, plat3_y_abs), p(PLAT3_HALF + 5, plat3_y_abs)])
    strokes.append([p(-PLAT3_HALF - 5, plat3_y_abs - 3), p(PLAT3_HALF + 5, plat3_y_abs - 3)])

    top_y_abs = TOP_Y + H // 2
    strokes.append([p(-SHAFT_HALF, plat3_y_abs), p(-SHAFT_HALF, top_y_abs)])
    strokes.append([p(SHAFT_HALF, plat3_y_abs), p(SHAFT_HALF, top_y_abs)])
    strokes.append([p(-SHAFT_HALF - 3, top_y_abs), p(SHAFT_HALF + 3, top_y_abs)])

    antenna_y_abs = ANTENNA_Y + H // 2
    strokes.append([p(0, top_y_abs), p(0, antenna_y_abs)])
    strokes.append([p(-4, top_y_abs + 5), p(0, antenna_y_abs), p(4, top_y_abs + 5)])

    arch_pts_left = []
    arch_pts_right = []
    base_y_abs = H // 2
    for i in range(9):
        t = i / 8
        arch_x = BASE_HALF * (1 - t)
        arch_y = base_y_abs - 40 * math.sin(math.pi * t)
        arch_pts_left.append(p(-arch_x, arch_y))
        arch_pts_right.append(p(arch_x, arch_y))
    strokes.append(arch_pts_left)
    strokes.append(arch_pts_right)

    sections = [
        (base_y_abs, plat1_y_abs, 4),
        (plat1_y_abs, plat2_y_abs, 4),
        (plat2_y_abs, plat3_y_abs, 3),
    ]
    for sec_bottom, sec_top, num_x in sections:
        sec_h = sec_bottom - sec_top
        for i in range(num_x):
            t_bot = (sec_bottom - H // 2 + H) / H
            t_mid = ((sec_bottom + sec_top) / 2 - H // 2 + H) / H
            t_top = (sec_top - H // 2 + H) / H

            w_bot = BASE_HALF * math.exp(-1.8 * (1 - t_bot / 1.0)) if t_bot > 0 else BASE_HALF
            w_mid = BASE_HALF * math.exp(-1.8 * (1 - t_mid / 1.0)) if t_mid > 0 else BASE_HALF
            w_top = BASE_HALF * math.exp(-1.8 * (1 - t_top / 1.0)) if t_top > 0 else BASE_HALF

            frac = (i + 0.5) / num_x
            y_cross = sec_bottom - int(sec_h * frac)
            w_at = BASE_HALF * math.exp(-1.8 * ((H // 2 - y_cross + H) / H))
            w_at = max(w_at, SHAFT_HALF + 2)

            strokes.append([p(-w_at, y_cross), p(w_at, y_cross)])

    for sec_bottom, sec_top, num_x in sections[:2]:
        sec_h = sec_bottom - sec_top
        for i in range(num_x):
            frac_bot = i / num_x
            frac_top = (i + 1) / num_x
            y_b = sec_bottom - int(sec_h * frac_bot)
            y_t = sec_bottom - int(sec_h * frac_top)
            t_b = (H // 2 - y_b + H) / H
            t_t = (H // 2 - y_t + H) / H
            w_b = max(BASE_HALF * math.exp(-1.8 * t_b), SHAFT_HALF + 2)
            w_t = max(BASE_HALF * math.exp(-1.8 * t_t), SHAFT_HALF + 2)
            strokes.append([p(-w_b, y_b), p(w_t, y_t)])
            strokes.append([p(w_b, y_b), p(-w_t, y_t)])

    base_y = H // 2
    foot_w = 15
    strokes.append([p(-BASE_HALF - foot_w, base_y), p(-BASE_HALF + foot_w, base_y)])
    strokes.append([p(BASE_HALF - foot_w, base_y), p(BASE_HALF + foot_w, base_y)])

    _exec_log_line("action_draw_eiffel_tower", None, {
        "total_strokes": len(strokes), "scale": scale,
        "offset": [offset_x, offset_y],
    })
    print(f"  Drawing Eiffel Tower: {len(strokes)} strokes (scale={scale})")

    for i, stroke in enumerate(strokes):
        _draw_single_stroke(ctx.agent, stroke, ctx.cx, ctx.cy, drag_delay=0.015)
        if (i + 1) % 10 == 0:
            print(f"    ... {i + 1}/{len(strokes)} strokes complete")

    print(f"  Eiffel Tower complete: {len(strokes)} strokes drawn")
    time.sleep(0.5)
    return {"status": "ok", "strokes": len(strokes)}


def _handle_drag_shape(ctx, args: dict) -> dict:
    """Draw a shape using bounding-box drag (Rectangle, Ellipse, Diamond).

    Excalidraw's shape tools work by clicking a start point and dragging to
    an end point, defining the bounding box. This handler:
    1. Presses the tool shortcut key
    2. Computes the bounding box from center offset + width/height
    3. Performs a single mouse-down→drag→mouse-up via execute_draw_path
    """
    if ctx.use_enterprise and ctx.agent:
        tool_key = str(args.get("tool_key", "2"))
        width = int(args.get("width", 200))
        height = int(args.get("height", 150))
        offset_x = int(args.get("offset_x", 0))
        offset_y = int(args.get("offset_y", 0))

        ctx.agent.enforce_app_focus("Safari")
        time.sleep(0.3)
        ctx.agent.execute_keystroke(tool_key)
        time.sleep(0.3)

        half_w, half_h = width // 2, height // 2
        top_left = (offset_x - half_w, offset_y - half_h)
        bottom_right = (offset_x + half_w, offset_y + half_h)

        _exec_log_line("action_drag_shape", None, {
            "tool_key": tool_key, "cx": ctx.cx, "cy": ctx.cy,
            "offset": [offset_x, offset_y], "size": [width, height],
        })
        print(f"  Drawing shape (tool='{tool_key}', {width}x{height} at offset ({offset_x},{offset_y}))")
        ctx.agent.execute_draw_path([top_left, bottom_right], ctx.cx, ctx.cy)
        result = {"status": "ok"}
    else:
        result = {"status": "skip", "reason": "enterprise_only"}
    print(f"  Shape drawn: {result}")
    time.sleep(0.5)
    return result


def _handle_draw_shape(ctx, args: dict) -> dict:
    """Draw a semantic geometric shape from the unified planner surface."""
    shape_type = str(args.get("shape_type", "rectangle")).strip().lower()
    size = int(args.get("size", 120))
    center_x = int(args.get("center_x", 0))
    center_y = int(args.get("center_y", 0))

    if shape_type in {"rectangle", "square"}:
        return _handle_drag_shape(
            ctx,
            {
                "tool_key": "2",
                "width": size * 2,
                "height": size * 2,
                "offset_x": center_x,
                "offset_y": center_y,
            },
        )
    if shape_type in {"circle", "ellipse"}:
        return _handle_drag_shape(
            ctx,
            {
                "tool_key": "4",
                "width": size * 2,
                "height": size * 2,
                "offset_x": center_x,
                "offset_y": center_y,
            },
        )
    if shape_type in {"diamond"}:
        return _handle_drag_shape(
            ctx,
            {
                "tool_key": "3",
                "width": size * 2,
                "height": size * 2,
                "offset_x": center_x,
                "offset_y": center_y,
            },
        )

    if shape_type in {"triangle", "polygon"}:
        import math

        sides = max(3, int(args.get("sides", 3) or 3))
        vertices = []
        for index in range(sides):
            angle = (-math.pi / 2) + (2 * math.pi * index / sides)
            vertices.append(
                [
                    center_x + int(size * math.cos(angle)),
                    center_y + int(size * math.sin(angle)),
                ]
            )
        return _handle_draw_path(
            ctx,
            {
                "vertices": vertices,
                "closed": True,
                "drag_delay": args.get("drag_delay", 0.05),
            },
        )

    return {"status": "error", "error": f"unsupported_shape_type:{shape_type}"}


def _handle_draw_circle(ctx, args: dict) -> dict:
    """Draw a circle as an N-gon polygon at the canvas center.

    Uses the same execute_draw_path_segments primitive as triangles, but
    with N vertices distributed uniformly around the circumference.
    N=36 gives 10-degree resolution — visually smooth on Excalidraw's
    canvas at any practical radius.
    """
    import math
    if ctx.use_enterprise and ctx.agent:
        radius = int(args.get("radius", 150))
        num_points = int(args.get("num_points", 36))
        _exec_log_line("action_draw_circle", None, {
            "cx": ctx.cx, "cy": ctx.cy, "radius": radius,
            "num_points": num_points, "strokes": 1,
        })
        vertices = []
        for i in range(num_points):
            angle = 2 * math.pi * i / num_points
            x = int(radius * math.cos(angle))
            y = int(radius * math.sin(angle))
            vertices.append((x, y))
        print(f"  Drawing circle (radius={radius}, {num_points} vertices, 1 stroke)")
        ctx.agent.execute_draw_path_segments(vertices, ctx.cx, ctx.cy)
        result = {"status": "ok", "strokes": 1, "vertices": num_points, "radius": radius}
    else:
        result = {"status": "skip", "reason": "enterprise_only"}
    print(f"  Circle drawn: {result}")
    time.sleep(0.5)
    return result


def _handle_verify_success(ctx, args: dict) -> dict:
    print("  Final verification...")
    return {"status": "ok"}


def _handle_visual_assert(ctx, args: dict) -> dict:
    """Planner-issued verification checkpoint.

    The actual assertion is executed by the recovery/verification layer using
    the prompt attached to the action item. This handler marks the action as a
    deliberate verification step so the executor does not treat it as unknown.
    """
    print("  Visual assertion checkpoint...")
    return {"status": "ok"}


def _normalize_beforeunload_choice(choice: str | None) -> tuple[str, str]:
    raw = (choice or "stay").strip().lower().replace("-", "_").replace(" ", "_")
    if raw in {"leave", "leave_page", "confirm_leave"}:
        return "leave", "Leave Page"
    return "stay", "Stay on Page"


def _estimate_beforeunload_button_point(
    bounds: dict[str, int] | None,
    choice: str,
    *,
    fallback_center: tuple[int, int] = (1440, 900),
) -> tuple[int, int]:
    """Estimate Safari beforeunload button coordinates from front-window bounds.

    The native browser confirmation dialog is centered in the content area.
    The button centers are nearly symmetric about the window midpoint and are
    much more stable relative to the window than relative to the full desktop.
    """
    if not bounds:
        cx, cy = fallback_center
        return (cx - 90, cy - 210) if choice == "stay" else (cx + 90, cy - 210)

    x = int(bounds.get("x", 0))
    y = int(bounds.get("y", 0))
    width = int(bounds.get("width", 0))
    height = int(bounds.get("height", 0))
    center_x = x + width // 2
    button_offset_x = max(72, min(108, int(width * 0.042)))
    button_y = y + max(180, min(int(height * 0.39), height - 140))
    if choice == "stay":
        return center_x - button_offset_x, button_y
    return center_x + button_offset_x, button_y


def _try_beforeunload_choice_via_vlm(ctx, choice: str, label: str) -> tuple[int, int] | None:
    """Locate the browser leave-page dialog button with SoM + VLM when available."""
    if not (ctx.use_enterprise and ctx.agent):
        return None
    vision_engine = getattr(ctx, "vision_engine", None)
    if vision_engine is None:
        return None

    base_dir = Path(getattr(ctx, "cre_dir", "/tmp"))
    screenshot_path = base_dir / "_browser_beforeunload_dialog.png"
    try:
        capture_front_window(screenshot_path, owner_name="Safari", timeout_seconds=10)
    except Exception:
        return None

    try:
        from PIL import Image as _PILImage

        img = _PILImage.open(screenshot_path)
        width, height = img.size
        region = (
            max(0, int(width * 0.28)),
            max(0, int(height * 0.10)),
            min(width, int(width * 0.72)),
            min(height, int(height * 0.60)),
        )
        if hasattr(vision_engine, "generate_som_overlay_adaptive"):
            coords_map, som_path = vision_engine.generate_som_overlay_adaptive(
                str(screenshot_path),
                output_filename="som_browser_beforeunload.png",
                resolution="fine",
                region=region,
            )
        else:
            coords_map, som_path = vision_engine.generate_som_overlay(
                str(screenshot_path),
                output_filename="som_browser_beforeunload.png",
            )

        target_id = ctx.agent.visually_extract_target(
            "Look at the Safari browser confirmation dialog that says "
            "'Are you sure you want to leave this page?'. "
            f"Find the button labeled '{label}'. Output only the integer box ID.",
            som_path,
        )
        px, py = coords_map.get(str(target_id), (0, 0))
        if px > 0 and py > 0:
            return int(px), int(py)
    except Exception:
        return None
    return None


def _handle_browser_beforeunload_dialog(ctx, args: dict) -> dict:
    """Click the Safari/browser leave-page confirmation dialog with the cursor."""
    if not (ctx.use_enterprise and ctx.agent):
        return {"status": "skip", "reason": "enterprise_only"}

    choice, label = _normalize_beforeunload_choice(args.get("choice"))
    ctx.agent.enforce_app_focus("Safari")
    time.sleep(0.25)

    strategy = "geometry"
    coords = _try_beforeunload_choice_via_vlm(ctx, choice, label)
    if coords is None:
        window_info = get_front_window_info(owner_name="Safari") or {}
        bounds = window_info.get("bounds") or {}
        coords = _estimate_beforeunload_button_point(
            bounds,
            choice,
            fallback_center=(int(getattr(ctx, "cx", 1440)), int(getattr(ctx, "cy", 900))),
        )
    else:
        strategy = "vlm"

    px, py = coords
    ctx.agent.execute_global_click(px, py)
    time.sleep(0.5)
    print(f"  Browser leave-page dialog: clicked '{label}' via {strategy} at ({px}, {py})")
    return {
        "status": "ok",
        "choice": choice,
        "label": label,
        "x": px,
        "y": py,
        "strategy": strategy,
    }


# =========================================================================
# KLEKI-SPECIFIC HANDLERS — raster drawing primitives for kleki.com
#
# Kleki.com is a browser-based raster painting tool with its own shortcut
# and panel layout. These handlers adapt the existing Quartz drawing
# primitives to Kleki's interaction model.
#
# References:
# - Yang et al. (2023). AppAgent (arXiv:2312.13771): autonomous UI exploration.
# - Zheng et al. (2024). SeeAct (arXiv:2401.01614): grounded web agent.
# =========================================================================

def _handle_kleki_clear_canvas(ctx, args: dict) -> dict:
    """Clear Kleki canvas safely on macOS.

    Kleki documents ``Delete`` or ``Backspace`` as the clear-layer shortcut.
    We therefore focus a canvas point inside the front Safari window, dismiss
    stale dialogs, then send the documented clear command instead of trying to
    emulate selection semantics from other drawing apps.
    """
    if not (ctx.use_enterprise and ctx.agent):
        return {"status": "skip", "reason": "enterprise_only"}

    agent = ctx.agent
    agent.enforce_app_focus("Safari")
    time.sleep(0.3)

    # Dismiss any lingering browser dialog before sending destructive keys.
    try:
        agent.execute_keystroke(53)
        time.sleep(0.2)
    except Exception:
        pass

    # Focus a point in the visible canvas, not the generic screen center.
    focus_x = getattr(ctx, "cx", 1440)
    focus_y = getattr(ctx, "cy", 900)
    try:
        window_info = get_front_window_info(owner_name="Safari") or {}
        bounds = window_info.get("bounds") or {}
        if bounds:
            focus_x = int(bounds["x"] + bounds["width"] * 0.36)
            focus_y = int(bounds["y"] + bounds["height"] * 0.52)
        agent.execute_global_click(focus_x, focus_y)
        time.sleep(0.3)
    except Exception:
        pass

    # Kleki help: Clear Layer = Delete or Backspace.
    agent.execute_keystroke(51)
    time.sleep(0.5)
    agent.execute_keystroke(51)
    time.sleep(0.8)

    print("  Kleki canvas cleared (Escape + canvas focus + Delete/Backspace)")
    return {
        "status": "ok",
        "focus_point": {"x": focus_x, "y": focus_y},
        "shortcut": "delete_backspace",
    }


def _kleki_tool(agent, key):
    """Press a Kleki shortcut key (e.g., 'b' for brush, 'e' for eraser)."""
    agent.enforce_app_focus("Safari")
    time.sleep(0.2)
    agent.execute_keystroke(key)
    time.sleep(0.4)


def _kleki_set_color_via_vlm(agent, vision_engine, cre_dir, color_description):
    """Use VLM to click a specific color in Kleki's right-panel color picker."""
    import subprocess as _sp
    agent.enforce_app_focus("Safari")
    time.sleep(0.3)
    ss_path = str(cre_dir / "_kleki_panel.png")
    _sp.run(["screencapture", "-x", ss_path], check=True, timeout=10)

    # Kleki's tool panel is on the right side (unlike Excalidraw's left)
    from PIL import Image as _PILImage
    img = _PILImage.open(ss_path)
    w = img.width
    panel_region = (w - 450, 80, w, img.height - 50)

    if hasattr(vision_engine, "generate_som_overlay_adaptive"):
        coords_map, som_path = vision_engine.generate_som_overlay_adaptive(
            ss_path, output_filename="som_kleki_panel.png",
            resolution="fine", region=panel_region,
        )
    else:
        coords_map, som_path = vision_engine.generate_som_overlay(
            ss_path, output_filename="som_kleki_panel.png"
        )
    target_id = agent.visually_extract_target(
        f"Look at the Kleki painting tool panel. Find the {color_description}. "
        f"Kleki has a color picker area with a gradient square and a hue slider bar. "
        f"Output only the integer box ID of the target.",
        som_path,
    )
    px, py = coords_map.get(str(target_id), (0, 0))
    if px > 0 and py > 0:
        print(f"    [VLM] Found '{color_description}': box {target_id} -> ({px}, {py})")
        agent.execute_global_click(px, py)
        time.sleep(0.4)
    else:
        print(f"    [VLM] Could not locate '{color_description}', skipping")


def _kleki_color_description(color_name: str) -> str:
    """Map semantic color requests to stable Kleki picker descriptions."""
    color = (color_name or "black").strip().lower()
    mapping = {
        "black": "black color in the color picker (fully dark area)",
        "near-black": "very dark gray or near-black color in the color picker",
        "near black": "very dark gray or near-black color in the color picker",
        "very dark gray": "very dark gray or near-black color in the color picker",
        "dark gray": "dark gray color in the color picker gradient",
        "medium gray": "medium gray color in the color picker gradient",
        "light gray": "light gray color in the color picker gradient",
        "white": "white color near the top-left of the color picker",
        "red": "red color in the color picker",
        "blue": "blue color in the color picker",
    }
    return mapping.get(color, f"{color} color in the Kleki color picker")


def _kleki_try_grayscale_click_from_site_knowledge(ctx, color_name: str) -> bool:
    """Use the learned Kleki color-picker anchor for stable grayscale selection.

    The site knowledge base already stores a `color_picker_box` center for this
    machine. For grayscale colors, the left edge of the SV square is the
    zero-saturation column, so vertical movement alone selects white→gray→black.
    """
    site_kb = getattr(ctx, "site_knowledge", None)
    button_map = getattr(site_kb, "button_map", {}) if site_kb else {}
    anchor = button_map.get("color_picker_box")
    if not anchor:
        return False

    color = (color_name or "black").strip().lower()
    offsets = {
        "white": (-160, -115),
        "light gray": (-160, -55),
        "medium gray": (-160, 0),
        "dark gray": (-160, 55),
        "very dark gray": (-160, 130),
        "near-black": (-160, 160),
        "near black": (-160, 160),
        "black": (-160, 185),
    }
    offset = offsets.get(color)
    if offset is None:
        return False

    px = anchor.pixel_x + offset[0]
    py = anchor.pixel_y + offset[1]
    print(f"    [SITE KB] Kleki grayscale '{color}': ({px}, {py}) from color_picker_box")
    ctx.agent.execute_global_click(px, py)
    time.sleep(0.4)
    return True


def _kleki_site_button_entry(ctx, key: str):
    site_kb = getattr(ctx, "site_knowledge", None)
    button_map = getattr(site_kb, "button_map", {}) if site_kb else {}
    return button_map.get(key)


def _kleki_site_button_coords(ctx, *keys: str) -> tuple[int, int] | None:
    for key in keys:
        entry = _kleki_site_button_entry(ctx, key)
        if not entry:
            continue
        px = entry.pixel_x if hasattr(entry, "pixel_x") else int(entry.get("pixel_x", 0))
        py = entry.pixel_y if hasattr(entry, "pixel_y") else int(entry.get("pixel_y", 0))
        if px > 0 and py > 0:
            return px, py
    return None


def _kleki_click_site_button(ctx, *keys: str) -> bool:
    coords = _kleki_site_button_coords(ctx, *keys)
    if not coords:
        return False
    px, py = coords
    print(f"    [SITE KB] Kleki button {keys[0]!r}: ({px}, {py})")
    ctx.agent.execute_global_click(px, py)
    time.sleep(0.3)
    return True


def _kleki_click_slider_position(ctx, slider_key: str, offset_x: int) -> bool:
    coords = _kleki_site_button_coords(ctx, slider_key)
    if not coords:
        return False
    px, py = coords
    target_x = px + offset_x
    print(f"    [SITE KB] Kleki slider '{slider_key}': ({target_x}, {py})")
    ctx.agent.execute_global_click(target_x, py)
    time.sleep(0.4)
    return True


def _send_command_select_all() -> None:
    import Quartz

    flags_cmd = getattr(Quartz, "kCGEventFlagMaskCommand", 0x100000)
    keycode_a = 0
    ev_d = Quartz.CGEventCreateKeyboardEvent(None, keycode_a, True)
    ev_u = Quartz.CGEventCreateKeyboardEvent(None, keycode_a, False)
    Quartz.CGEventSetFlags(ev_d, flags_cmd)
    Quartz.CGEventSetFlags(ev_u, flags_cmd)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, ev_d)
    time.sleep(0.05)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, ev_u)


def _kleki_type_numeric_control(ctx, control_key: str, value: str) -> bool:
    coords = _kleki_site_button_coords(ctx, control_key)
    if not coords:
        return False
    px, py = coords
    print(f"    [SITE KB] Kleki numeric control '{control_key}': ({px}, {py}) -> {value}")
    ctx.agent.execute_global_click(px, py)
    time.sleep(0.2)
    _send_command_select_all()
    time.sleep(0.1)
    ctx.agent.execute_keystroke(51, app_focus=None)
    time.sleep(0.05)
    ctx.agent.execute_keystroke(51, app_focus=None)
    time.sleep(0.05)
    for ch in str(value):
        ctx.agent.execute_keystroke(ch, app_focus=None)
        time.sleep(0.05)
    ctx.agent.execute_keystroke(36, app_focus=None)
    time.sleep(0.3)
    return True


def _kleki_try_brush_size_from_site_knowledge(ctx, size_name: str) -> bool:
    size = (size_name or "thin").strip().lower()
    offsets = {
        # Empirically calibrated from live runs: the stored x anchor sits near
        # the control midpoint, so very-thin linework must click much farther
        # left than the original implementation.
        "very thin": -240,
        "thin": -210,
        "small": -210,
        "medium": -90,
        "thick": 10,
        "large": 120,
        "wide": 210,
    }
    offset = offsets.get(size)
    if offset is None:
        return False
    return _kleki_click_slider_position(ctx, "brush_size_slider", offset)


def _kleki_try_opacity_from_site_knowledge(ctx, opacity_name: str) -> bool:
    opacity = (opacity_name or "100%").strip().lower()
    values = {
        "low": "25",
        "medium": "55",
        "high": "80",
        "100%": "100",
    }
    value = values.get(opacity)
    if value is None:
        return False
    return _kleki_type_numeric_control(ctx, "brush_opacity_slider", value)


def _kleki_try_scatter_from_site_knowledge(ctx, scatter_name: str) -> bool:
    scatter = (scatter_name or "0").strip().lower()
    offsets = {
        "0": -240,
        "zero": -240,
        "none": -240,
        "low": -140,
        "medium": 0,
        "high": 140,
    }
    offset = offsets.get(scatter)
    if offset is None:
        return False
    return _kleki_click_slider_position(ctx, "brush_scatter_slider", offset)


def _kleki_try_stabilizer_from_site_knowledge(ctx, stabilizer_name: str) -> bool:
    stabilizer = (stabilizer_name or "1").strip().lower()
    value = {
        "low": "1",
        "1": "1",
        "medium": "4",
        "4": "4",
        "high": "8",
        "8": "8",
    }.get(stabilizer, stabilizer_name)
    coords = _kleki_site_button_coords(ctx, "brush_stabilizer_control", "stabilizer_setting")
    if not coords:
        return False
    px, py = coords
    print(f"    [SITE KB] Kleki stabilizer '{value}': ({px}, {py})")
    ctx.agent.execute_global_click(px, py)
    time.sleep(0.2)
    for _ in range(2):
        ctx.agent.execute_keystroke(51, app_focus=None)
        time.sleep(0.05)
    for ch in str(value):
        ctx.agent.execute_keystroke(ch, app_focus=None)
        time.sleep(0.05)
    ctx.agent.execute_keystroke(36, app_focus=None)
    time.sleep(0.3)
    return True


def _kleki_brush_size_description(size_name: str) -> str:
    size = (size_name or "thin").strip().lower()
    mapping = {
        "very thin": "brush size slider — very thin end",
        "thin": "brush size slider — click near the small/thin end (left side)",
        "small": "brush size slider — click near the small/thin end (left side)",
        "medium": "brush size slider — click around the middle",
        "thick": "brush size slider — click near the large/thick end (right side)",
        "large": "brush size slider — click near the large/thick end (right side)",
        "wide": "brush size slider — click near the large/thick end (right side)",
    }
    return mapping.get(size, f"brush size slider — set to {size}")


def _kleki_opacity_description(opacity_name: str) -> str:
    opacity = (opacity_name or "100%").strip().lower()
    mapping = {
        "100%": "opacity slider — set near the maximum / fully opaque end",
        "high": "opacity slider — set near the maximum / fully opaque end",
        "medium": "opacity slider — set around the middle",
        "low": "opacity slider — set near the low-opacity end",
    }
    return mapping.get(opacity, f"opacity slider — set to {opacity}")


def _kleki_scatter_description(scatter_name: str) -> str:
    scatter = (scatter_name or "0").strip().lower()
    mapping = {
        "0": "scatter slider — set to zero / far left",
        "zero": "scatter slider — set to zero / far left",
        "none": "scatter slider — set to zero / far left",
        "low": "scatter slider — set to a low value left of center",
        "medium": "scatter slider — set around the middle",
        "high": "scatter slider — set near the right side",
    }
    return mapping.get(scatter, f"scatter slider — set to {scatter}")


def _kleki_set_brush_size_via_vlm(agent, vision_engine, cre_dir, size_description) -> bool:
    """Use VLM to adjust brush size in Kleki's panel."""
    import subprocess as _sp
    agent.enforce_app_focus("Safari")
    time.sleep(0.3)
    ss_path = str(cre_dir / "_kleki_brush.png")
    _sp.run(["screencapture", "-x", ss_path], check=True, timeout=10)

    from PIL import Image as _PILImage
    img = _PILImage.open(ss_path)
    w = img.width
    panel_region = (w - 450, 80, w, 400)

    if hasattr(vision_engine, "generate_som_overlay_adaptive"):
        coords_map, som_path = vision_engine.generate_som_overlay_adaptive(
            ss_path, output_filename="som_kleki_brush.png",
            resolution="fine", region=panel_region,
        )
    else:
        coords_map, som_path = vision_engine.generate_som_overlay(
            ss_path, output_filename="som_kleki_brush.png"
        )
    target_id = agent.visually_extract_target(
        f"Look at the Kleki brush settings panel. Find the {size_description}. "
        f"Output only the integer box ID.",
        som_path,
    )
    px, py = coords_map.get(str(target_id), (0, 0))
    if px > 0 and py > 0:
        print(f"    [VLM] Brush size '{size_description}': box {target_id} -> ({px}, {py})")
        agent.execute_global_click(px, py)
        time.sleep(0.3)
        return True
    else:
        print(f"    [VLM] Could not locate brush size control, skipping")
        return False


def _kleki_set_opacity_via_vlm(agent, vision_engine, cre_dir, opacity_description) -> bool:
    """Use VLM to adjust opacity in Kleki's panel."""
    import subprocess as _sp
    agent.enforce_app_focus("Safari")
    time.sleep(0.3)
    ss_path = str(cre_dir / "_kleki_opacity.png")
    _sp.run(["screencapture", "-x", ss_path], check=True, timeout=10)

    from PIL import Image as _PILImage
    img = _PILImage.open(ss_path)
    w = img.width
    panel_region = (w - 450, 80, w, 400)

    if hasattr(vision_engine, "generate_som_overlay_adaptive"):
        coords_map, som_path = vision_engine.generate_som_overlay_adaptive(
            ss_path, output_filename="som_kleki_opacity.png",
            resolution="fine", region=panel_region,
        )
    else:
        coords_map, som_path = vision_engine.generate_som_overlay(
            ss_path, output_filename="som_kleki_opacity.png"
        )
    target_id = agent.visually_extract_target(
        f"Look at the Kleki tool settings panel. Find the {opacity_description}. "
        f"Output only the integer box ID.",
        som_path,
    )
    px, py = coords_map.get(str(target_id), (0, 0))
    if px > 0 and py > 0:
        print(f"    [VLM] Opacity '{opacity_description}': box {target_id} -> ({px}, {py})")
        agent.execute_global_click(px, py)
        time.sleep(0.3)
        return True
    else:
        print(f"    [VLM] Could not locate opacity control, skipping")
        return False


def _kleki_set_scatter_via_vlm(agent, vision_engine, cre_dir, scatter_description) -> bool:
    import subprocess as _sp
    agent.enforce_app_focus("Safari")
    time.sleep(0.3)
    ss_path = str(cre_dir / "_kleki_scatter.png")
    _sp.run(["screencapture", "-x", ss_path], check=True, timeout=10)

    from PIL import Image as _PILImage
    img = _PILImage.open(ss_path)
    w = img.width
    panel_region = (w - 450, 80, w, 600)

    if hasattr(vision_engine, "generate_som_overlay_adaptive"):
        coords_map, som_path = vision_engine.generate_som_overlay_adaptive(
            ss_path, output_filename="som_kleki_scatter.png",
            resolution="fine", region=panel_region,
        )
    else:
        coords_map, som_path = vision_engine.generate_som_overlay(
            ss_path, output_filename="som_kleki_scatter.png"
        )
    target_id = agent.visually_extract_target(
        f"Look at the Kleki tool settings panel. Find the {scatter_description}. "
        f"Output only the integer box ID.",
        som_path,
    )
    px, py = coords_map.get(str(target_id), (0, 0))
    if px > 0 and py > 0:
        print(f"    [VLM] Scatter '{scatter_description}': box {target_id} -> ({px}, {py})")
        agent.execute_global_click(px, py)
        time.sleep(0.3)
        return True
    print(f"    [VLM] Could not locate scatter control, skipping")
    return False


def _handle_kleki_set_color(ctx, args: dict) -> dict:
    if not (ctx.use_enterprise and ctx.agent and ctx.vision_engine):
        return {"status": "skip", "reason": "enterprise_only"}
    color = str(args.get("color", "black")).strip().lower() or "black"
    used_site_knowledge = _kleki_try_grayscale_click_from_site_knowledge(ctx, color)
    if not used_site_knowledge:
        _kleki_set_color_via_vlm(
            ctx.agent,
            ctx.vision_engine,
            ctx.cre_dir,
            _kleki_color_description(color),
        )
    return {"status": "ok", "color": color}


def _handle_kleki_set_brush_size(ctx, args: dict) -> dict:
    if not (ctx.use_enterprise and ctx.agent and ctx.vision_engine):
        return {"status": "skip", "reason": "enterprise_only"}
    size = str(args.get("size", "thin")).strip().lower() or "thin"
    used_site_knowledge = _kleki_try_brush_size_from_site_knowledge(ctx, size)
    if not used_site_knowledge:
        used_vlm = _kleki_set_brush_size_via_vlm(
            ctx.agent,
            ctx.vision_engine,
            ctx.cre_dir,
            _kleki_brush_size_description(size),
        )
        if not used_vlm:
            raise RuntimeError(f"Could not ground Kleki brush size control for '{size}'")
    return {"status": "ok", "size": size}


def _handle_kleki_set_opacity(ctx, args: dict) -> dict:
    if not (ctx.use_enterprise and ctx.agent and ctx.vision_engine):
        return {"status": "skip", "reason": "enterprise_only"}
    opacity = str(args.get("opacity", "100%")).strip().lower() or "100%"
    used_site_knowledge = _kleki_try_opacity_from_site_knowledge(ctx, opacity)
    if not used_site_knowledge:
        used_vlm = _kleki_set_opacity_via_vlm(
            ctx.agent,
            ctx.vision_engine,
            ctx.cre_dir,
            _kleki_opacity_description(opacity),
        )
        if not used_vlm:
            raise RuntimeError(f"Could not ground Kleki opacity control for '{opacity}'")
    return {"status": "ok", "opacity": opacity}


def _handle_kleki_set_scatter(ctx, args: dict) -> dict:
    if not (ctx.use_enterprise and ctx.agent and ctx.vision_engine):
        return {"status": "skip", "reason": "enterprise_only"}
    scatter = str(args.get("scatter", "0")).strip().lower() or "0"
    used_site_knowledge = _kleki_try_scatter_from_site_knowledge(ctx, scatter)
    if not used_site_knowledge:
        used_vlm = _kleki_set_scatter_via_vlm(
            ctx.agent,
            ctx.vision_engine,
            ctx.cre_dir,
            _kleki_scatter_description(scatter),
        )
        if not used_vlm:
            raise RuntimeError(f"Could not ground Kleki scatter control for '{scatter}'")
    return {"status": "ok", "scatter": scatter}


def _handle_kleki_set_stabilizer(ctx, args: dict) -> dict:
    if not (ctx.use_enterprise and ctx.agent):
        return {"status": "skip", "reason": "enterprise_only"}
    stabilizer = str(args.get("stabilizer", "1")).strip().lower() or "1"
    if not _kleki_try_stabilizer_from_site_knowledge(ctx, stabilizer):
        raise RuntimeError(f"Could not ground Kleki stabilizer control for '{stabilizer}'")
    return {"status": "ok", "stabilizer": stabilizer}


def _handle_kleki_select_tool(ctx, args: dict) -> dict:
    if not (ctx.use_enterprise and ctx.agent):
        return {"status": "skip", "reason": "enterprise_only"}
    tool = str(args.get("tool", "brush")).strip().lower() or "brush"
    ctx.agent.enforce_app_focus("Safari")
    time.sleep(0.2)

    shortcut_map = {
        "brush": "b",
        "eraser": "e",
        "shape": "u",
        "line": "u",
    }
    button_keys = {
        "brush": ("brush_tool_button", "brush_tool"),
        "shape": ("shape_tool_button",),
    }
    if tool in button_keys:
        _kleki_click_site_button(ctx, *button_keys[tool])
    key = shortcut_map.get(tool)
    if key:
        ctx.agent.execute_keystroke(key, app_focus=None)
        time.sleep(0.3)
        return {"status": "ok", "tool": tool, "shortcut": key}
    raise RuntimeError(f"Unsupported Kleki tool selection '{tool}'")


def _handle_kleki_reset_render_state(ctx, args: dict) -> dict:
    if not (ctx.use_enterprise and ctx.agent):
        return {"status": "skip", "reason": "enterprise_only"}
    tool = str(args.get("tool", "brush")).strip().lower() or "brush"
    size = str(args.get("size", "very thin")).strip().lower() or "very thin"
    opacity = str(args.get("opacity", "100%")).strip().lower() or "100%"
    scatter = str(args.get("scatter", "0")).strip().lower() or "0"
    stabilizer = str(args.get("stabilizer", "1")).strip().lower() or "1"

    _handle_kleki_select_tool(ctx, {"tool": tool})
    _kleki_click_site_button(ctx, "brush_shape_round")
    _handle_kleki_set_scatter(ctx, {"scatter": scatter})
    _handle_kleki_set_stabilizer(ctx, {"stabilizer": stabilizer})
    _handle_kleki_set_brush_size(ctx, {"size": size})
    _handle_kleki_set_opacity(ctx, {"opacity": opacity})
    return {
        "status": "ok",
        "tool": tool,
        "size": size,
        "opacity": opacity,
        "scatter": scatter,
        "stabilizer": stabilizer,
    }


# =========================================================================
# BMW E30 M3 DRAWING HANDLERS — Five iterations of progressive fidelity
#
# Each handler draws the full car from scratch on a blank canvas.
# Geometry based on the real E30 M3 dimensions:
#   Overall: 4325 x 1680 x 1365 mm
#   Wheelbase: 2562 mm (59.3% of length)
#   Box flares: +40 mm per side (DTM homologation)
#   Hofmeister kink at C-pillar (BMW signature since Neue Klasse 1962)
#
# References:
# - BMW AG (1986). E30 M3 Homologation Technical Specification.
# - Patton, P. (2019). "BMW: The Ultimate Driving Machine." DK Publishing.
# - Bangle, C. (2006). "Great Cars Are Art." TED Talk.
# - Macey, S. (2009). "H-Point: Fundamentals of Car Design." Design Studio.
# - Loomis, A. (1951). "Successful Drawing." Viking Press.
# - Torrance, K.E. & Sparrow, E.M. (1967). Off-specular reflection. JOSA.
# =========================================================================

def _handle_bmw_skeleton(ctx, args: dict) -> dict:
    """Iteration I — Geometric Skeleton Model.

    Single-brush wireframe establishing proportional foundation:
    wheelbase ratio, roofline angle, fender flare geometry, greenhouse.
    """
    if not (ctx.use_enterprise and ctx.agent):
        return {"status": "skip", "reason": "enterprise_only"}

    agent = ctx.agent
    ve = ctx.vision_engine
    agent.enforce_app_focus("Safari")
    time.sleep(0.5)

    import subprocess as _sp
    _ss = str(ctx.cre_dir / "_bmw_center.png")
    _sp.run(["screencapture", "-x", _ss], check=True, timeout=10)
    cx, cy = get_screenshot_center(_ss)
    ctx.ui_analysis["canvas_center"] = {"x": cx, "y": cy}
    print(f"  [BMW-I] Canvas center: ({cx}, {cy})")

    total_strokes = 0

    def _stroke(pts, dd=0.015):
        nonlocal total_strokes
        _draw_single_stroke(agent, pts, cx, cy, drag_delay=dd)
        total_strokes += 1
        if total_strokes % 10 == 0:
            _checkpoint(agent, ctx.cre_dir, f"bmw1_{total_strokes}", total_strokes, 35)

    # Select brush tool, thin black line
    _kleki_tool(agent, "b")
    _kleki_set_color_via_vlm(agent, ve, ctx.cre_dir,
                              "black color in the color picker (fully dark area)")
    _kleki_set_brush_size_via_vlm(agent, ve, ctx.cre_dir,
                                   "brush size slider — click near the small/thin end (left side)")

    _checkpoint(agent, ctx.cre_dir, "bmw1_00_start", 0, 35)

    # === CAR PROPORTIONS (scaled to ~600 px wide, ~190 px tall) ===
    # The E30 M3 in profile, centered on canvas
    W = 600       # total car length in px
    H_BODY = 130  # body height
    H_ROOF = 60   # roof height above body
    WB = int(W * 0.593)  # wheelbase
    FRONT_OH = int(W * 0.190)  # front overhang
    REAR_OH = W - WB - FRONT_OH
    WHEEL_R = 38  # wheel radius
    BODY_Y = 40   # vertical offset of body bottom from center
    GROUND_Y = BODY_Y + 8

    # Coordinate origin: (0,0) = canvas center; positive x = right, positive y = down
    left_edge = -W // 2
    right_edge = W // 2
    front_wheel_x = left_edge + FRONT_OH
    rear_wheel_x = front_wheel_x + WB

    # ─── BODY OUTLINE (continuous stroke) ───
    print("  [BMW-I] Body outline...")
    body_outline = [
        # Start at front bumper bottom
        (left_edge, BODY_Y),
        # Front bumper face
        (left_edge, BODY_Y - 30),
        # Hood line (slight upward slope to windshield base)
        (left_edge + 40, BODY_Y - 50),
        (left_edge + FRONT_OH + 30, BODY_Y - 55),
        # A-pillar (windshield base to roof)
        (left_edge + FRONT_OH + 80, BODY_Y - H_BODY),
        # Roofline (gentle arc to C-pillar)
        (left_edge + FRONT_OH + 120, BODY_Y - H_BODY - H_ROOF + 5),
        (0, BODY_Y - H_BODY - H_ROOF),
        (50, BODY_Y - H_BODY - H_ROOF + 2),
        # Hofmeister kink at C-pillar
        (rear_wheel_x - 60, BODY_Y - H_BODY - H_ROOF + 10),
        (rear_wheel_x - 40, BODY_Y - H_BODY - 5),
        # Rear window and trunk
        (rear_wheel_x + 10, BODY_Y - H_BODY + 10),
        (right_edge - 20, BODY_Y - 55),
        # Rear bumper
        (right_edge, BODY_Y - 35),
        (right_edge, BODY_Y),
    ]
    _stroke(body_outline, dd=0.012)

    # ─── SILL LINE (bottom of body) ───
    print("  [BMW-I] Sill line...")
    _stroke([(left_edge, BODY_Y), (right_edge, BODY_Y)])

    # ─── BELTLINE / SHOULDER CREASE ───
    print("  [BMW-I] Beltline...")
    belt_y = BODY_Y - 60
    _stroke([
        (left_edge + 50, belt_y + 5),
        (0, belt_y),
        (right_edge - 30, belt_y + 5),
    ])

    # ─── FRONT WHEEL ARCH (box flare) ───
    print("  [BMW-I] Front wheel arch...")
    import math
    fwa_pts = []
    for angle_deg in range(0, 181, 12):
        a = math.radians(angle_deg)
        ax = front_wheel_x + int(WHEEL_R * 1.25 * math.cos(a))
        ay = BODY_Y - int(WHEEL_R * 1.25 * abs(math.sin(a)))
        fwa_pts.append((ax, ay))
    _stroke(fwa_pts)

    # ─── REAR WHEEL ARCH (box flare — slightly larger for M3) ───
    print("  [BMW-I] Rear wheel arch...")
    rwa_pts = []
    for angle_deg in range(0, 181, 12):
        a = math.radians(angle_deg)
        ax = rear_wheel_x + int(WHEEL_R * 1.35 * math.cos(a))
        ay = BODY_Y - int(WHEEL_R * 1.35 * abs(math.sin(a)))
        rwa_pts.append((ax, ay))
    _stroke(rwa_pts)

    # ─── FRONT WHEEL (circle) ───
    print("  [BMW-I] Front wheel...")
    fw_pts = []
    for angle_deg in range(0, 361, 15):
        a = math.radians(angle_deg)
        fw_pts.append((
            front_wheel_x + int(WHEEL_R * math.cos(a)),
            BODY_Y + int(WHEEL_R * math.sin(a)),
        ))
    _stroke(fw_pts)

    # ─── REAR WHEEL (circle) ───
    print("  [BMW-I] Rear wheel...")
    rw_pts = []
    for angle_deg in range(0, 361, 15):
        a = math.radians(angle_deg)
        rw_pts.append((
            rear_wheel_x + int(WHEEL_R * math.cos(a)),
            BODY_Y + int(WHEEL_R * math.sin(a)),
        ))
    _stroke(rw_pts)

    # ─── WINDSHIELD ───
    print("  [BMW-I] Windshield...")
    _stroke([
        (left_edge + FRONT_OH + 80, BODY_Y - H_BODY),
        (left_edge + FRONT_OH + 85, BODY_Y - 55),
    ])

    # ─── REAR WINDOW ───
    print("  [BMW-I] Rear window...")
    _stroke([
        (rear_wheel_x - 40, BODY_Y - H_BODY - 5),
        (rear_wheel_x + 10, BODY_Y - H_BODY + 10),
    ])

    # ─── DOOR LINE ───
    print("  [BMW-I] Door line...")
    _stroke([
        (left_edge + FRONT_OH + 140, BODY_Y - H_BODY - H_ROOF + 10),
        (left_edge + FRONT_OH + 140, BODY_Y),
    ])

    # ─── GRILLE AREA (simple rectangles) ───
    print("  [BMW-I] Grille outline...")
    grille_top = BODY_Y - 45
    grille_bot = BODY_Y - 20
    grille_left = left_edge + 8
    grille_right = left_edge + 55
    # Left kidney
    _stroke([(grille_left, grille_top), (grille_left + 18, grille_top),
             (grille_left + 18, grille_bot), (grille_left, grille_bot),
             (grille_left, grille_top)])
    # Right kidney
    _stroke([(grille_left + 22, grille_top), (grille_right, grille_top),
             (grille_right, grille_bot), (grille_left + 22, grille_bot),
             (grille_left + 22, grille_top)])

    # ─── HEADLIGHTS (twin circles) ───
    print("  [BMW-I] Headlights...")
    hl_cx = left_edge + 35
    hl_cy = BODY_Y - 38
    for r, offset in [(12, -15), (10, 8)]:
        pts = []
        for angle_deg in range(0, 361, 20):
            a = math.radians(angle_deg)
            pts.append((hl_cx + offset + int(r * math.cos(a)),
                        hl_cy + int(r * math.sin(a))))
        _stroke(pts)

    # ─── TAIL LIGHTS ───
    print("  [BMW-I] Tail lights...")
    tl_cx = right_edge - 15
    tl_top = BODY_Y - 50
    tl_bot = BODY_Y - 25
    _stroke([(tl_cx, tl_top), (tl_cx + 10, tl_top),
             (tl_cx + 10, tl_bot), (tl_cx, tl_bot),
             (tl_cx, tl_top)])

    # ─── SIDE MIRROR ───
    print("  [BMW-I] Side mirror...")
    mir_x = left_edge + FRONT_OH + 75
    mir_y = BODY_Y - H_BODY + 5
    _stroke([(mir_x, mir_y), (mir_x - 12, mir_y - 8), (mir_x - 12, mir_y + 4), (mir_x, mir_y)])

    # ─── BUMPER DETAILS ───
    print("  [BMW-I] Bumpers...")
    # Front bumper line
    _stroke([(left_edge, BODY_Y - 15), (left_edge + 60, BODY_Y - 15)])
    # Rear bumper line
    _stroke([(right_edge - 60, BODY_Y - 15), (right_edge, BODY_Y - 15)])

    _checkpoint(agent, ctx.cre_dir, "bmw1_final", total_strokes, 35)
    print(f"  [BMW-I] Complete: {total_strokes} strokes")
    return {"status": "ok", "strokes": total_strokes}


def _handle_bmw_form_blocking(ctx, args: dict) -> dict:
    """Iteration II — Proportional Correction & Form Blocking.

    Rebuilds the car with corrected proportions and introduces mass/shadow.
    """
    if not (ctx.use_enterprise and ctx.agent):
        return {"status": "skip", "reason": "enterprise_only"}

    agent = ctx.agent
    ve = ctx.vision_engine
    agent.enforce_app_focus("Safari")
    time.sleep(0.5)

    import subprocess as _sp
    import math
    _ss = str(ctx.cre_dir / "_bmw_center2.png")
    _sp.run(["screencapture", "-x", _ss], check=True, timeout=10)
    cx, cy = get_screenshot_center(_ss)
    ctx.ui_analysis["canvas_center"] = {"x": cx, "y": cy}
    print(f"  [BMW-II] Canvas center: ({cx}, {cy})")

    total_strokes = 0

    def _stroke(pts, dd=0.015):
        nonlocal total_strokes
        _draw_single_stroke(agent, pts, cx, cy, drag_delay=dd)
        total_strokes += 1
        if total_strokes % 12 == 0:
            _checkpoint(agent, ctx.cre_dir, f"bmw2_{total_strokes}", total_strokes, 50)

    # ─── SHADOW LAYER (dark gray fill under body) ───
    print("  [BMW-II] Shadow fill...")
    _kleki_tool(agent, "b")
    _kleki_set_color_via_vlm(agent, ve, ctx.cre_dir,
                              "dark gray color in the color picker gradient")
    _kleki_set_brush_size_via_vlm(agent, ve, ctx.cre_dir,
                                   "brush size slider — click near the large/thick end (right side) for a wide brush")

    _checkpoint(agent, ctx.cre_dir, "bmw2_00_start", 0, 50)

    W = 620
    H_BODY = 135
    H_ROOF = 62
    WB = int(W * 0.593)
    FRONT_OH = int(W * 0.190)
    WHEEL_R = 40
    BODY_Y = 40
    left_edge = -W // 2
    right_edge = W // 2
    front_wheel_x = left_edge + FRONT_OH
    rear_wheel_x = front_wheel_x + WB

    # Shadow under body (wide dark strokes)
    shadow_y = BODY_Y + 12
    for dy in range(0, 20, 4):
        _stroke([(left_edge + 20, shadow_y + dy), (right_edge - 20, shadow_y + dy)])

    # ─── BODY SILHOUETTE (filled with medium gray) ───
    print("  [BMW-II] Body mass fill...")
    _kleki_set_color_via_vlm(agent, ve, ctx.cre_dir,
                              "medium gray color in the color picker (middle brightness)")
    _kleki_set_brush_size_via_vlm(agent, ve, ctx.cre_dir,
                                   "brush size slider — click near the large/thick end for a wide brush")

    # Fill body by scanning horizontal strokes
    for scan_y in range(-H_BODY - H_ROOF + 20, BODY_Y, 6):
        x_left = left_edge + 10
        x_right = right_edge - 10
        # Taper for roof
        if scan_y < BODY_Y - H_BODY:
            frac_roof = (BODY_Y - H_BODY - scan_y) / H_ROOF
            x_left = left_edge + FRONT_OH + 70 + int(frac_roof * 30)
            x_right = rear_wheel_x - 20 - int(frac_roof * 40)
        _stroke([(x_left, scan_y), (x_right, scan_y)], dd=0.008)

    _checkpoint(agent, ctx.cre_dir, "bmw2_body_fill", total_strokes, 50)

    # ─── OUTLINE (thinner, black, corrected proportions) ───
    print("  [BMW-II] Corrected outline...")
    _kleki_set_color_via_vlm(agent, ve, ctx.cre_dir,
                              "black color in the color picker (fully dark)")
    _kleki_set_brush_size_via_vlm(agent, ve, ctx.cre_dir,
                                   "brush size slider — click near the thin/small end (left side)")

    body_outline = [
        (left_edge, BODY_Y),
        (left_edge, BODY_Y - 32),
        (left_edge + 42, BODY_Y - 52),
        (left_edge + FRONT_OH + 35, BODY_Y - 57),
        (left_edge + FRONT_OH + 82, BODY_Y - H_BODY),
        (left_edge + FRONT_OH + 125, BODY_Y - H_BODY - H_ROOF + 6),
        (0, BODY_Y - H_BODY - H_ROOF),
        (55, BODY_Y - H_BODY - H_ROOF + 2),
        (rear_wheel_x - 55, BODY_Y - H_BODY - H_ROOF + 12),
        (rear_wheel_x - 38, BODY_Y - H_BODY - 3),
        (rear_wheel_x + 12, BODY_Y - H_BODY + 12),
        (right_edge - 18, BODY_Y - 57),
        (right_edge, BODY_Y - 37),
        (right_edge, BODY_Y),
    ]
    _stroke(body_outline, dd=0.010)
    _stroke([(left_edge, BODY_Y), (right_edge, BODY_Y)])

    # Beltline
    belt_y = BODY_Y - 62
    _stroke([
        (left_edge + 52, belt_y + 5),
        (0, belt_y),
        (right_edge - 28, belt_y + 5),
    ])

    # Wheel arches (box flares)
    for wx, r_mult in [(front_wheel_x, 1.28), (rear_wheel_x, 1.38)]:
        arch_pts = []
        for angle_deg in range(0, 181, 10):
            a = math.radians(angle_deg)
            arch_pts.append((
                wx + int(WHEEL_R * r_mult * math.cos(a)),
                BODY_Y - int(WHEEL_R * r_mult * abs(math.sin(a))),
            ))
        _stroke(arch_pts)

    # Wheels
    for wx in [front_wheel_x, rear_wheel_x]:
        wpts = []
        for angle_deg in range(0, 361, 12):
            a = math.radians(angle_deg)
            wpts.append((
                wx + int(WHEEL_R * math.cos(a)),
                BODY_Y + int(WHEEL_R * math.sin(a)),
            ))
        _stroke(wpts)

    # Grille area blocked in (filled rectangles)
    print("  [BMW-II] Grille blocking...")
    grille_top = BODY_Y - 47
    grille_bot = BODY_Y - 18
    grille_l = left_edge + 10
    # Fill the grille area dark
    for sy in range(grille_top, grille_bot, 3):
        _stroke([(grille_l, sy), (grille_l + 48, sy)])

    _checkpoint(agent, ctx.cre_dir, "bmw2_final", total_strokes, 50)
    print(f"  [BMW-II] Complete: {total_strokes} strokes")
    return {"status": "ok", "strokes": total_strokes}


def _handle_bmw_mechanical(ctx, args: dict) -> dict:
    """Iteration III — Mechanical Detail Integration.

    Adds kidney grille, twin headlights, bumper segments, BBS wheels,
    window trim, door handles, mirrors.
    """
    if not (ctx.use_enterprise and ctx.agent):
        return {"status": "skip", "reason": "enterprise_only"}

    agent = ctx.agent
    ve = ctx.vision_engine
    agent.enforce_app_focus("Safari")
    time.sleep(0.5)

    import subprocess as _sp
    import math
    _ss = str(ctx.cre_dir / "_bmw_center3.png")
    _sp.run(["screencapture", "-x", _ss], check=True, timeout=10)
    cx, cy = get_screenshot_center(_ss)
    ctx.ui_analysis["canvas_center"] = {"x": cx, "y": cy}
    print(f"  [BMW-III] Canvas center: ({cx}, {cy})")

    total_strokes = 0

    def _stroke(pts, dd=0.015):
        nonlocal total_strokes
        _draw_single_stroke(agent, pts, cx, cy, drag_delay=dd)
        total_strokes += 1
        if total_strokes % 15 == 0:
            _checkpoint(agent, ctx.cre_dir, f"bmw3_{total_strokes}", total_strokes, 80)

    W = 620
    H_BODY = 135
    H_ROOF = 62
    WB = int(W * 0.593)
    FRONT_OH = int(W * 0.190)
    WHEEL_R = 40
    BODY_Y = 40
    left_edge = -W // 2
    right_edge = W // 2
    front_wheel_x = left_edge + FRONT_OH
    rear_wheel_x = front_wheel_x + WB

    # ─── BODY FILL (medium gray) ───
    print("  [BMW-III] Body fill...")
    _kleki_tool(agent, "b")
    _kleki_set_color_via_vlm(agent, ve, ctx.cre_dir,
                              "light gray color in the color picker (bright but not white)")
    _kleki_set_brush_size_via_vlm(agent, ve, ctx.cre_dir,
                                   "brush size slider — click near the large/thick end")

    for scan_y in range(-H_BODY - H_ROOF + 20, BODY_Y, 5):
        x_left = left_edge + 10
        x_right = right_edge - 10
        if scan_y < BODY_Y - H_BODY:
            frac_roof = (BODY_Y - H_BODY - scan_y) / H_ROOF
            x_left = left_edge + FRONT_OH + 70 + int(frac_roof * 30)
            x_right = rear_wheel_x - 20 - int(frac_roof * 40)
        _stroke([(x_left, scan_y), (x_right, scan_y)], dd=0.006)

    _checkpoint(agent, ctx.cre_dir, "bmw3_body", total_strokes, 80)

    # ─── OUTLINE ───
    print("  [BMW-III] Outline...")
    _kleki_set_color_via_vlm(agent, ve, ctx.cre_dir, "black color (fully dark)")
    _kleki_set_brush_size_via_vlm(agent, ve, ctx.cre_dir,
                                   "brush size slider — click near the thin end (left)")

    body_outline = [
        (left_edge, BODY_Y), (left_edge, BODY_Y - 32),
        (left_edge + 42, BODY_Y - 52), (left_edge + FRONT_OH + 35, BODY_Y - 57),
        (left_edge + FRONT_OH + 82, BODY_Y - H_BODY),
        (left_edge + FRONT_OH + 125, BODY_Y - H_BODY - H_ROOF + 6),
        (0, BODY_Y - H_BODY - H_ROOF),
        (55, BODY_Y - H_BODY - H_ROOF + 2),
        (rear_wheel_x - 55, BODY_Y - H_BODY - H_ROOF + 12),
        (rear_wheel_x - 38, BODY_Y - H_BODY - 3),
        (rear_wheel_x + 12, BODY_Y - H_BODY + 12),
        (right_edge - 18, BODY_Y - 57), (right_edge, BODY_Y - 37),
        (right_edge, BODY_Y),
    ]
    _stroke(body_outline, dd=0.010)
    _stroke([(left_edge, BODY_Y), (right_edge, BODY_Y)])

    # Beltline
    _stroke([
        (left_edge + 52, BODY_Y - 57),
        (0, BODY_Y - 62),
        (right_edge - 28, BODY_Y - 57),
    ])

    # ─── KIDNEY GRILLE (detailed with vertical slats) ───
    print("  [BMW-III] Kidney grille...")
    grille_top = BODY_Y - 47
    grille_bot = BODY_Y - 20
    gl = left_edge + 10

    # Left kidney outline
    _stroke([(gl, grille_top), (gl + 20, grille_top), (gl + 20, grille_bot),
             (gl, grille_bot), (gl, grille_top)])
    # Left kidney slats
    for sx in range(gl + 3, gl + 20, 3):
        _stroke([(sx, grille_top + 2), (sx, grille_bot - 2)])

    # Right kidney outline
    _stroke([(gl + 24, grille_top), (gl + 48, grille_top), (gl + 48, grille_bot),
             (gl + 24, grille_bot), (gl + 24, grille_top)])
    # Right kidney slats
    for sx in range(gl + 27, gl + 48, 3):
        _stroke([(sx, grille_top + 2), (sx, grille_bot - 2)])

    _checkpoint(agent, ctx.cre_dir, "bmw3_grille", total_strokes, 80)

    # ─── TWIN HEADLIGHTS ───
    print("  [BMW-III] Twin headlights...")
    hl_cy = BODY_Y - 38
    for r, hx in [(13, left_edge + 20), (11, left_edge + 48)]:
        pts = []
        for angle_deg in range(0, 361, 15):
            a = math.radians(angle_deg)
            pts.append((hx + int(r * math.cos(a)), hl_cy + int(r * math.sin(a))))
        _stroke(pts)
        # Inner ring
        pts_inner = []
        for angle_deg in range(0, 361, 20):
            a = math.radians(angle_deg)
            pts_inner.append((hx + int((r - 3) * math.cos(a)), hl_cy + int((r - 3) * math.sin(a))))
        _stroke(pts_inner)

    # ─── TAIL LIGHTS ───
    print("  [BMW-III] Tail lights...")
    tl_x = right_edge - 18
    _stroke([(tl_x, BODY_Y - 52), (tl_x + 12, BODY_Y - 52),
             (tl_x + 12, BODY_Y - 22), (tl_x, BODY_Y - 22),
             (tl_x, BODY_Y - 52)])
    _stroke([(tl_x, BODY_Y - 37), (tl_x + 12, BODY_Y - 37)])

    # ─── BBS WHEELS (5-double-spoke pattern) ───
    print("  [BMW-III] BBS wheels...")
    for wx in [front_wheel_x, rear_wheel_x]:
        # Outer tire
        for r in [WHEEL_R, WHEEL_R - 4]:
            wpts = []
            for angle_deg in range(0, 361, 10):
                a = math.radians(angle_deg)
                wpts.append((wx + int(r * math.cos(a)), BODY_Y + int(r * math.sin(a))))
            _stroke(wpts)

        # Hub (inner circle)
        hub_r = 10
        hpts = []
        for angle_deg in range(0, 361, 20):
            a = math.radians(angle_deg)
            hpts.append((wx + int(hub_r * math.cos(a)), BODY_Y + int(hub_r * math.sin(a))))
        _stroke(hpts)

        # 5 spokes
        spoke_r = WHEEL_R - 8
        for spoke_i in range(5):
            angle = math.radians(spoke_i * 72 - 90)
            sx = wx + int(spoke_r * math.cos(angle))
            sy = BODY_Y + int(spoke_r * math.sin(angle))
            _stroke([(wx, BODY_Y), (sx, sy)])

    _checkpoint(agent, ctx.cre_dir, "bmw3_wheels", total_strokes, 80)

    # ─── WHEEL ARCHES ───
    print("  [BMW-III] Wheel arches...")
    for wxc, r_mult in [(front_wheel_x, 1.28), (rear_wheel_x, 1.38)]:
        arch_pts = []
        for angle_deg in range(0, 181, 8):
            a = math.radians(angle_deg)
            arch_pts.append((
                wxc + int(WHEEL_R * r_mult * math.cos(a)),
                BODY_Y - int(WHEEL_R * r_mult * abs(math.sin(a))),
            ))
        _stroke(arch_pts)

    # ─── WINDOW TRIM ───
    print("  [BMW-III] Window trim...")
    # Windshield
    _stroke([
        (left_edge + FRONT_OH + 82, BODY_Y - H_BODY),
        (left_edge + FRONT_OH + 87, BODY_Y - 57),
    ])
    # Rear window
    _stroke([
        (rear_wheel_x - 38, BODY_Y - H_BODY - 3),
        (rear_wheel_x + 12, BODY_Y - H_BODY + 12),
    ])
    # Side windows (roofline to beltline)
    _stroke([
        (left_edge + FRONT_OH + 90, BODY_Y - H_BODY + 2),
        (left_edge + FRONT_OH + 90, BODY_Y - 60),
    ])

    # ─── DOOR HANDLES ───
    print("  [BMW-III] Door handles...")
    dh_x = left_edge + FRONT_OH + 155
    dh_y = BODY_Y - 50
    _stroke([(dh_x, dh_y), (dh_x + 20, dh_y)])

    # ─── SIDE MIRROR ───
    print("  [BMW-III] Mirror...")
    mir_x = left_edge + FRONT_OH + 78
    mir_y = BODY_Y - H_BODY + 8
    _stroke([(mir_x, mir_y), (mir_x - 14, mir_y - 10),
             (mir_x - 14, mir_y + 5), (mir_x, mir_y)])

    # ─── BUMPER DETAILS ───
    print("  [BMW-III] Bumpers...")
    _stroke([(left_edge, BODY_Y - 15), (left_edge + 65, BODY_Y - 15)])
    _stroke([(right_edge - 65, BODY_Y - 15), (right_edge, BODY_Y - 15)])
    # Front fog light housings
    _stroke([(left_edge + 5, BODY_Y - 10), (left_edge + 18, BODY_Y - 10),
             (left_edge + 18, BODY_Y - 2), (left_edge + 5, BODY_Y - 2),
             (left_edge + 5, BODY_Y - 10)])

    # Door line
    _stroke([
        (left_edge + FRONT_OH + 142, BODY_Y - H_BODY - H_ROOF + 12),
        (left_edge + FRONT_OH + 142, BODY_Y),
    ])

    _checkpoint(agent, ctx.cre_dir, "bmw3_final", total_strokes, 80)
    print(f"  [BMW-III] Complete: {total_strokes} strokes")
    return {"status": "ok", "strokes": total_strokes}


def _handle_bmw_lighting(ctx, args: dict) -> dict:
    """Iteration IV — Surface Physics & Light Modeling.

    Light source upper-left, specular highlights, shadow gradients,
    glass transparency, tire rubber differentiation.
    """
    if not (ctx.use_enterprise and ctx.agent):
        return {"status": "skip", "reason": "enterprise_only"}

    agent = ctx.agent
    ve = ctx.vision_engine
    agent.enforce_app_focus("Safari")
    time.sleep(0.5)

    import subprocess as _sp
    import math
    _ss = str(ctx.cre_dir / "_bmw_center4.png")
    _sp.run(["screencapture", "-x", _ss], check=True, timeout=10)
    cx, cy = get_screenshot_center(_ss)
    ctx.ui_analysis["canvas_center"] = {"x": cx, "y": cy}
    print(f"  [BMW-IV] Canvas center: ({cx}, {cy})")

    total_strokes = 0

    def _stroke(pts, dd=0.015):
        nonlocal total_strokes
        _draw_single_stroke(agent, pts, cx, cy, drag_delay=dd)
        total_strokes += 1
        if total_strokes % 15 == 0:
            _checkpoint(agent, ctx.cre_dir, f"bmw4_{total_strokes}", total_strokes, 70)

    W = 620
    H_BODY = 135
    H_ROOF = 62
    WB = int(W * 0.593)
    FRONT_OH = int(W * 0.190)
    WHEEL_R = 40
    BODY_Y = 40
    left_edge = -W // 2
    right_edge = W // 2
    front_wheel_x = left_edge + FRONT_OH
    rear_wheel_x = front_wheel_x + WB

    _kleki_tool(agent, "b")
    _checkpoint(agent, ctx.cre_dir, "bmw4_00_start", 0, 70)

    # ─── GROUND SHADOW (dark, soft) ───
    print("  [BMW-IV] Ground shadow...")
    _kleki_set_color_via_vlm(agent, ve, ctx.cre_dir,
                              "dark gray color in the color picker")
    _kleki_set_brush_size_via_vlm(agent, ve, ctx.cre_dir,
                                   "brush size slider — large/thick end")
    _kleki_set_opacity_via_vlm(agent, ve, ctx.cre_dir,
                                "opacity slider — click at about 40-50% (middle-left area)")

    for dy in range(0, 25, 4):
        _stroke([(left_edge + 30, BODY_Y + 15 + dy), (right_edge - 30, BODY_Y + 15 + dy)], dd=0.008)

    # ─── BODY BASE (light gray) ───
    print("  [BMW-IV] Body base fill...")
    _kleki_set_color_via_vlm(agent, ve, ctx.cre_dir,
                              "light gray color (bright) in the color picker")
    _kleki_set_opacity_via_vlm(agent, ve, ctx.cre_dir,
                                "opacity slider — click at about 100% (far right)")
    _kleki_set_brush_size_via_vlm(agent, ve, ctx.cre_dir,
                                   "brush size slider — large/thick end")

    for scan_y in range(-H_BODY - H_ROOF + 20, BODY_Y, 5):
        x_left = left_edge + 10
        x_right = right_edge - 10
        if scan_y < BODY_Y - H_BODY:
            frac_roof = (BODY_Y - H_BODY - scan_y) / H_ROOF
            x_left = left_edge + FRONT_OH + 70 + int(frac_roof * 30)
            x_right = rear_wheel_x - 20 - int(frac_roof * 40)
        _stroke([(x_left, scan_y), (x_right, scan_y)], dd=0.006)

    _checkpoint(agent, ctx.cre_dir, "bmw4_body", total_strokes, 70)

    # ─── LOWER BODY SHADOW (darker sill area) ───
    print("  [BMW-IV] Lower body shadow...")
    _kleki_set_color_via_vlm(agent, ve, ctx.cre_dir,
                              "medium-dark gray color in the color picker")
    _kleki_set_opacity_via_vlm(agent, ve, ctx.cre_dir,
                                "opacity slider — about 60% (slightly past middle)")
    _kleki_set_brush_size_via_vlm(agent, ve, ctx.cre_dir,
                                   "brush size slider — medium size")

    for scan_y in range(BODY_Y - 25, BODY_Y, 4):
        _stroke([(left_edge + 15, scan_y), (right_edge - 15, scan_y)], dd=0.008)

    # ─── SPECULAR HIGHLIGHTS (white, low opacity) ───
    print("  [BMW-IV] Specular highlights...")
    _kleki_set_color_via_vlm(agent, ve, ctx.cre_dir,
                              "white color in the color picker (top-left of gradient or white swatch)")
    _kleki_set_opacity_via_vlm(agent, ve, ctx.cre_dir,
                                "opacity slider — about 40% (middle-left)")
    _kleki_set_brush_size_via_vlm(agent, ve, ctx.cre_dir,
                                   "brush size slider — medium size")

    # Hood highlight
    _stroke([(left_edge + 60, BODY_Y - 55), (left_edge + FRONT_OH + 50, BODY_Y - 58)], dd=0.012)
    # Roof highlight
    _stroke([(left_edge + FRONT_OH + 130, BODY_Y - H_BODY - H_ROOF + 3),
             (30, BODY_Y - H_BODY - H_ROOF + 1)], dd=0.012)
    # Front fender highlight
    _stroke([(left_edge + 35, BODY_Y - 40), (left_edge + FRONT_OH + 60, BODY_Y - 45)], dd=0.012)

    _checkpoint(agent, ctx.cre_dir, "bmw4_highlights", total_strokes, 70)

    # ─── GLASS (light blue tint) ───
    print("  [BMW-IV] Glass...")
    _kleki_set_color_via_vlm(agent, ve, ctx.cre_dir,
                              "light blue color in the color picker")
    _kleki_set_opacity_via_vlm(agent, ve, ctx.cre_dir,
                                "opacity slider — about 30%")
    _kleki_set_brush_size_via_vlm(agent, ve, ctx.cre_dir,
                                   "brush size slider — medium size")

    # Windshield fill
    for ws_y in range(BODY_Y - H_BODY, BODY_Y - 58, 4):
        frac = (ws_y - (BODY_Y - H_BODY)) / (BODY_Y - 58 - (BODY_Y - H_BODY))
        x_l = left_edge + FRONT_OH + 83 + int(frac * 3)
        x_r = left_edge + FRONT_OH + 83 + int(frac * 3) + 4
        _stroke([(x_l, ws_y), (x_r, ws_y)], dd=0.010)

    # Side windows
    for ws_y in range(BODY_Y - H_BODY - H_ROOF + 15, BODY_Y - 62, 4):
        _stroke([(left_edge + FRONT_OH + 92, ws_y), (left_edge + FRONT_OH + 140, ws_y)], dd=0.008)
    for ws_y in range(BODY_Y - H_BODY - H_ROOF + 15, BODY_Y - 62, 4):
        _stroke([(left_edge + FRONT_OH + 145, ws_y), (rear_wheel_x - 42, ws_y)], dd=0.008)

    # ─── BLACK OUTLINES ───
    print("  [BMW-IV] Outlines...")
    _kleki_set_color_via_vlm(agent, ve, ctx.cre_dir, "black color (fully dark)")
    _kleki_set_opacity_via_vlm(agent, ve, ctx.cre_dir, "opacity slider — 100% (far right)")
    _kleki_set_brush_size_via_vlm(agent, ve, ctx.cre_dir,
                                   "brush size slider — thin end (left side)")

    body_outline = [
        (left_edge, BODY_Y), (left_edge, BODY_Y - 32),
        (left_edge + 42, BODY_Y - 52), (left_edge + FRONT_OH + 35, BODY_Y - 57),
        (left_edge + FRONT_OH + 82, BODY_Y - H_BODY),
        (left_edge + FRONT_OH + 125, BODY_Y - H_BODY - H_ROOF + 6),
        (0, BODY_Y - H_BODY - H_ROOF),
        (55, BODY_Y - H_BODY - H_ROOF + 2),
        (rear_wheel_x - 55, BODY_Y - H_BODY - H_ROOF + 12),
        (rear_wheel_x - 38, BODY_Y - H_BODY - 3),
        (rear_wheel_x + 12, BODY_Y - H_BODY + 12),
        (right_edge - 18, BODY_Y - 57), (right_edge, BODY_Y - 37),
        (right_edge, BODY_Y),
    ]
    _stroke(body_outline, dd=0.010)
    _stroke([(left_edge, BODY_Y), (right_edge, BODY_Y)])

    # Beltline
    _stroke([(left_edge + 52, BODY_Y - 57), (0, BODY_Y - 62), (right_edge - 28, BODY_Y - 57)])

    # Wheel arches
    for wxc, r_mult in [(front_wheel_x, 1.28), (rear_wheel_x, 1.38)]:
        arch_pts = []
        for angle_deg in range(0, 181, 8):
            a = math.radians(angle_deg)
            arch_pts.append((wxc + int(WHEEL_R * r_mult * math.cos(a)),
                             BODY_Y - int(WHEEL_R * r_mult * abs(math.sin(a)))))
        _stroke(arch_pts)

    # ─── TIRES (dark rubber) ───
    print("  [BMW-IV] Tires...")
    _kleki_set_color_via_vlm(agent, ve, ctx.cre_dir, "very dark gray or near-black")
    _kleki_set_brush_size_via_vlm(agent, ve, ctx.cre_dir, "brush size slider — medium-thin")

    for wx in [front_wheel_x, rear_wheel_x]:
        for r in [WHEEL_R, WHEEL_R - 3]:
            wpts = []
            for angle_deg in range(0, 361, 10):
                a = math.radians(angle_deg)
                wpts.append((wx + int(r * math.cos(a)), BODY_Y + int(r * math.sin(a))))
            _stroke(wpts)
        # Spokes
        spoke_r = WHEEL_R - 8
        for spoke_i in range(5):
            angle = math.radians(spoke_i * 72 - 90)
            sx = wx + int(spoke_r * math.cos(angle))
            sy = BODY_Y + int(spoke_r * math.sin(angle))
            _stroke([(wx, BODY_Y), (sx, sy)])
        # Hub
        hpts = []
        for angle_deg in range(0, 361, 20):
            a = math.radians(angle_deg)
            hpts.append((wx + int(10 * math.cos(a)), BODY_Y + int(10 * math.sin(a))))
        _stroke(hpts)

    # Grille, headlights, details (same as Iteration III)
    print("  [BMW-IV] Grille & headlights...")
    gl = left_edge + 10
    grille_top = BODY_Y - 47
    grille_bot = BODY_Y - 20
    _stroke([(gl, grille_top), (gl + 20, grille_top), (gl + 20, grille_bot),
             (gl, grille_bot), (gl, grille_top)])
    for sx in range(gl + 3, gl + 20, 3):
        _stroke([(sx, grille_top + 2), (sx, grille_bot - 2)])
    _stroke([(gl + 24, grille_top), (gl + 48, grille_top), (gl + 48, grille_bot),
             (gl + 24, grille_bot), (gl + 24, grille_top)])
    for sx in range(gl + 27, gl + 48, 3):
        _stroke([(sx, grille_top + 2), (sx, grille_bot - 2)])

    hl_cy = BODY_Y - 38
    for r, hx in [(13, left_edge + 20), (11, left_edge + 48)]:
        pts = []
        for angle_deg in range(0, 361, 15):
            a = math.radians(angle_deg)
            pts.append((hx + int(r * math.cos(a)), hl_cy + int(r * math.sin(a))))
        _stroke(pts)

    # Door, mirror, bumpers
    _stroke([(left_edge + FRONT_OH + 142, BODY_Y - H_BODY - H_ROOF + 12),
             (left_edge + FRONT_OH + 142, BODY_Y)])
    mir_x = left_edge + FRONT_OH + 78
    mir_y = BODY_Y - H_BODY + 8
    _stroke([(mir_x, mir_y), (mir_x - 14, mir_y - 10),
             (mir_x - 14, mir_y + 5), (mir_x, mir_y)])
    _stroke([(left_edge, BODY_Y - 15), (left_edge + 65, BODY_Y - 15)])
    _stroke([(right_edge - 65, BODY_Y - 15), (right_edge, BODY_Y - 15)])

    _checkpoint(agent, ctx.cre_dir, "bmw4_final", total_strokes, 70)
    print(f"  [BMW-IV] Complete: {total_strokes} strokes")
    return {"status": "ok", "strokes": total_strokes}


def _handle_bmw_final(ctx, args: dict) -> dict:
    """Iteration V — High-Fidelity Render & Technical Completion.

    Multi-layer compositing with atmospheric background, shadow grounding
    plane, metallic paint reflections, and environmental context.
    Color: Alpine White (#F2F2F0) — the E30 M3 signature color.
    """
    if not (ctx.use_enterprise and ctx.agent):
        return {"status": "skip", "reason": "enterprise_only"}

    agent = ctx.agent
    ve = ctx.vision_engine
    agent.enforce_app_focus("Safari")
    time.sleep(0.5)

    import subprocess as _sp
    import math
    _ss = str(ctx.cre_dir / "_bmw_center5.png")
    _sp.run(["screencapture", "-x", _ss], check=True, timeout=10)
    cx, cy = get_screenshot_center(_ss)
    ctx.ui_analysis["canvas_center"] = {"x": cx, "y": cy}
    print(f"  [BMW-V] Canvas center: ({cx}, {cy})")

    total_strokes = 0

    def _stroke(pts, dd=0.015):
        nonlocal total_strokes
        _draw_single_stroke(agent, pts, cx, cy, drag_delay=dd)
        total_strokes += 1
        if total_strokes % 15 == 0:
            _checkpoint(agent, ctx.cre_dir, f"bmw5_{total_strokes}", total_strokes, 100)

    W = 620
    H_BODY = 135
    H_ROOF = 62
    WB = int(W * 0.593)
    FRONT_OH = int(W * 0.190)
    WHEEL_R = 40
    BODY_Y = 40
    left_edge = -W // 2
    right_edge = W // 2
    front_wheel_x = left_edge + FRONT_OH
    rear_wheel_x = front_wheel_x + WB

    _kleki_tool(agent, "b")
    _checkpoint(agent, ctx.cre_dir, "bmw5_00_start", 0, 100)

    # ─── L1: SKY GRADIENT (light blue to white, top to middle) ───
    print("  [BMW-V] Sky gradient...")
    _kleki_set_color_via_vlm(agent, ve, ctx.cre_dir,
                              "light blue color in the color picker")
    _kleki_set_brush_size_via_vlm(agent, ve, ctx.cre_dir,
                                   "brush size slider — very large/thick end")
    _kleki_set_opacity_via_vlm(agent, ve, ctx.cre_dir,
                                "opacity slider — about 50%")

    for scan_y in range(-350, -80, 8):
        _stroke([(-450, scan_y), (450, scan_y)], dd=0.005)

    _checkpoint(agent, ctx.cre_dir, "bmw5_sky", total_strokes, 100)

    # ─── L2: GROUND PLANE (gray asphalt) ───
    print("  [BMW-V] Ground plane...")
    _kleki_set_color_via_vlm(agent, ve, ctx.cre_dir,
                              "medium gray color in the color picker")
    _kleki_set_opacity_via_vlm(agent, ve, ctx.cre_dir,
                                "opacity slider — 80% (mostly right)")

    for scan_y in range(BODY_Y + 45, 300, 6):
        _stroke([(-450, scan_y), (450, scan_y)], dd=0.005)

    # ─── L3: CAR SHADOW (ground plane) ───
    print("  [BMW-V] Ground shadow...")
    _kleki_set_color_via_vlm(agent, ve, ctx.cre_dir,
                              "dark gray color")
    _kleki_set_opacity_via_vlm(agent, ve, ctx.cre_dir,
                                "opacity slider — about 40%")
    _kleki_set_brush_size_via_vlm(agent, ve, ctx.cre_dir,
                                   "brush size slider — large/thick end")

    for dy in range(0, 30, 4):
        _stroke([(left_edge + 25, BODY_Y + 15 + dy), (right_edge - 15, BODY_Y + 20 + dy)], dd=0.008)

    _checkpoint(agent, ctx.cre_dir, "bmw5_shadow", total_strokes, 100)

    # ─── L4: BODY — ALPINE WHITE ───
    print("  [BMW-V] Body (Alpine White)...")
    _kleki_set_color_via_vlm(agent, ve, ctx.cre_dir,
                              "very light gray or near-white in the color picker (top-left of gradient)")
    _kleki_set_opacity_via_vlm(agent, ve, ctx.cre_dir,
                                "opacity slider — 100% (far right)")
    _kleki_set_brush_size_via_vlm(agent, ve, ctx.cre_dir,
                                   "brush size slider — large/thick end")

    for scan_y in range(-H_BODY - H_ROOF + 20, BODY_Y, 4):
        x_left = left_edge + 10
        x_right = right_edge - 10
        if scan_y < BODY_Y - H_BODY:
            frac_roof = (BODY_Y - H_BODY - scan_y) / H_ROOF
            x_left = left_edge + FRONT_OH + 70 + int(frac_roof * 30)
            x_right = rear_wheel_x - 20 - int(frac_roof * 40)
        _stroke([(x_left, scan_y), (x_right, scan_y)], dd=0.005)

    _checkpoint(agent, ctx.cre_dir, "bmw5_body", total_strokes, 100)

    # ─── L5: LOWER BODY SHADOW ───
    print("  [BMW-V] Lower body shadow...")
    _kleki_set_color_via_vlm(agent, ve, ctx.cre_dir, "medium gray")
    _kleki_set_opacity_via_vlm(agent, ve, ctx.cre_dir, "opacity slider — about 50%")
    _kleki_set_brush_size_via_vlm(agent, ve, ctx.cre_dir, "brush size slider — medium")

    for scan_y in range(BODY_Y - 28, BODY_Y, 3):
        _stroke([(left_edge + 15, scan_y), (right_edge - 15, scan_y)], dd=0.008)

    # ─── L6: SPECULAR HIGHLIGHTS (white, low opacity) ───
    print("  [BMW-V] Highlights...")
    _kleki_set_color_via_vlm(agent, ve, ctx.cre_dir, "white color")
    _kleki_set_opacity_via_vlm(agent, ve, ctx.cre_dir, "opacity slider — about 35-40%")
    _kleki_set_brush_size_via_vlm(agent, ve, ctx.cre_dir, "brush size slider — medium")

    # Hood highlight
    _stroke([(left_edge + 55, BODY_Y - 54), (left_edge + FRONT_OH + 50, BODY_Y - 57)])
    # Roof highlight
    _stroke([(left_edge + FRONT_OH + 125, BODY_Y - H_BODY - H_ROOF + 3),
             (35, BODY_Y - H_BODY - H_ROOF + 1)])
    # Front fender highlight
    _stroke([(left_edge + 30, BODY_Y - 42), (left_edge + FRONT_OH + 60, BODY_Y - 47)])
    # Rear quarter panel highlight
    _stroke([(rear_wheel_x - 40, BODY_Y - 55), (right_edge - 25, BODY_Y - 58)])
    # Metallic edge streak along beltline
    _kleki_set_brush_size_via_vlm(agent, ve, ctx.cre_dir, "brush size slider — thin end")
    _stroke([(left_edge + 55, BODY_Y - 59), (0, BODY_Y - 64), (right_edge - 30, BODY_Y - 59)])

    _checkpoint(agent, ctx.cre_dir, "bmw5_highlights", total_strokes, 100)

    # ─── L7: GLASS (tinted blue) ───
    print("  [BMW-V] Glass...")
    _kleki_set_color_via_vlm(agent, ve, ctx.cre_dir, "light blue color")
    _kleki_set_opacity_via_vlm(agent, ve, ctx.cre_dir, "opacity slider — about 35%")
    _kleki_set_brush_size_via_vlm(agent, ve, ctx.cre_dir, "brush size slider — medium")

    for ws_y in range(BODY_Y - H_BODY, BODY_Y - 58, 3):
        frac = (ws_y - (BODY_Y - H_BODY)) / max((BODY_Y - 58 - (BODY_Y - H_BODY)), 1)
        x_l = left_edge + FRONT_OH + 83 + int(frac * 3)
        _stroke([(x_l, ws_y), (x_l + 5, ws_y)])
    for ws_y in range(BODY_Y - H_BODY - H_ROOF + 15, BODY_Y - 63, 3):
        _stroke([(left_edge + FRONT_OH + 92, ws_y), (rear_wheel_x - 42, ws_y)])

    # ─── L8: OUTLINES (crisp black) ───
    print("  [BMW-V] Outlines...")
    _kleki_set_color_via_vlm(agent, ve, ctx.cre_dir, "black (fully dark)")
    _kleki_set_opacity_via_vlm(agent, ve, ctx.cre_dir, "opacity slider — 100%")
    _kleki_set_brush_size_via_vlm(agent, ve, ctx.cre_dir, "brush size slider — thin end")

    body_outline = [
        (left_edge, BODY_Y), (left_edge, BODY_Y - 32),
        (left_edge + 42, BODY_Y - 52), (left_edge + FRONT_OH + 35, BODY_Y - 57),
        (left_edge + FRONT_OH + 82, BODY_Y - H_BODY),
        (left_edge + FRONT_OH + 125, BODY_Y - H_BODY - H_ROOF + 6),
        (0, BODY_Y - H_BODY - H_ROOF),
        (55, BODY_Y - H_BODY - H_ROOF + 2),
        (rear_wheel_x - 55, BODY_Y - H_BODY - H_ROOF + 12),
        (rear_wheel_x - 38, BODY_Y - H_BODY - 3),
        (rear_wheel_x + 12, BODY_Y - H_BODY + 12),
        (right_edge - 18, BODY_Y - 57), (right_edge, BODY_Y - 37),
        (right_edge, BODY_Y),
    ]
    _stroke(body_outline, dd=0.010)
    _stroke([(left_edge, BODY_Y), (right_edge, BODY_Y)])

    # Beltline
    _stroke([(left_edge + 52, BODY_Y - 57), (0, BODY_Y - 62), (right_edge - 28, BODY_Y - 57)])

    # Wheel arches
    for wxc, r_mult in [(front_wheel_x, 1.28), (rear_wheel_x, 1.38)]:
        arch_pts = []
        for angle_deg in range(0, 181, 8):
            a = math.radians(angle_deg)
            arch_pts.append((wxc + int(WHEEL_R * r_mult * math.cos(a)),
                             BODY_Y - int(WHEEL_R * r_mult * abs(math.sin(a)))))
        _stroke(arch_pts)

    # Tires + wheels
    _kleki_set_color_via_vlm(agent, ve, ctx.cre_dir, "very dark gray near-black")
    for wx in [front_wheel_x, rear_wheel_x]:
        for r in [WHEEL_R, WHEEL_R - 3]:
            wpts = []
            for angle_deg in range(0, 361, 10):
                a = math.radians(angle_deg)
                wpts.append((wx + int(r * math.cos(a)), BODY_Y + int(r * math.sin(a))))
            _stroke(wpts)
        spoke_r = WHEEL_R - 8
        for spoke_i in range(5):
            angle = math.radians(spoke_i * 72 - 90)
            sx = wx + int(spoke_r * math.cos(angle))
            sy = BODY_Y + int(spoke_r * math.sin(angle))
            _stroke([(wx, BODY_Y), (sx, sy)])
        hpts = []
        for angle_deg in range(0, 361, 20):
            a = math.radians(angle_deg)
            hpts.append((wx + int(10 * math.cos(a)), BODY_Y + int(10 * math.sin(a))))
        _stroke(hpts)

    # Grille (black, detailed)
    _kleki_set_color_via_vlm(agent, ve, ctx.cre_dir, "black (fully dark)")
    gl = left_edge + 10
    grille_top = BODY_Y - 47
    grille_bot = BODY_Y - 20
    _stroke([(gl, grille_top), (gl + 20, grille_top), (gl + 20, grille_bot),
             (gl, grille_bot), (gl, grille_top)])
    for sx in range(gl + 3, gl + 20, 3):
        _stroke([(sx, grille_top + 2), (sx, grille_bot - 2)])
    _stroke([(gl + 24, grille_top), (gl + 48, grille_top), (gl + 48, grille_bot),
             (gl + 24, grille_bot), (gl + 24, grille_top)])
    for sx in range(gl + 27, gl + 48, 3):
        _stroke([(sx, grille_top + 2), (sx, grille_bot - 2)])

    # Headlights
    hl_cy = BODY_Y - 38
    for r, hx in [(13, left_edge + 20), (11, left_edge + 48)]:
        pts = []
        for angle_deg in range(0, 361, 15):
            a = math.radians(angle_deg)
            pts.append((hx + int(r * math.cos(a)), hl_cy + int(r * math.sin(a))))
        _stroke(pts)

    # Tail lights (red tint)
    _kleki_set_color_via_vlm(agent, ve, ctx.cre_dir, "red color")
    tl_x = right_edge - 18
    for tly in range(BODY_Y - 52, BODY_Y - 22, 3):
        _stroke([(tl_x, tly), (tl_x + 12, tly)])

    # Detail lines (black)
    _kleki_set_color_via_vlm(agent, ve, ctx.cre_dir, "black")
    _stroke([(left_edge + FRONT_OH + 142, BODY_Y - H_BODY - H_ROOF + 12),
             (left_edge + FRONT_OH + 142, BODY_Y)])
    mir_x = left_edge + FRONT_OH + 78
    mir_y = BODY_Y - H_BODY + 8
    _stroke([(mir_x, mir_y), (mir_x - 14, mir_y - 10),
             (mir_x - 14, mir_y + 5), (mir_x, mir_y)])
    _stroke([(left_edge, BODY_Y - 15), (left_edge + 65, BODY_Y - 15)])
    _stroke([(right_edge - 65, BODY_Y - 15), (right_edge, BODY_Y - 15)])

    # Door handle
    dh_x = left_edge + FRONT_OH + 155
    dh_y = BODY_Y - 50
    _stroke([(dh_x, dh_y), (dh_x + 20, dh_y)])

    # Window frames
    _stroke([(left_edge + FRONT_OH + 82, BODY_Y - H_BODY),
             (left_edge + FRONT_OH + 87, BODY_Y - 57)])
    _stroke([(rear_wheel_x - 38, BODY_Y - H_BODY - 3),
             (rear_wheel_x + 12, BODY_Y - H_BODY + 12)])
    _stroke([(left_edge + FRONT_OH + 90, BODY_Y - H_BODY + 2),
             (left_edge + FRONT_OH + 90, BODY_Y - 60)])

    # Front fog lights
    _stroke([(left_edge + 5, BODY_Y - 10), (left_edge + 18, BODY_Y - 10),
             (left_edge + 18, BODY_Y - 2), (left_edge + 5, BODY_Y - 2),
             (left_edge + 5, BODY_Y - 10)])

    # "M3" badge hint on trunk
    _kleki_set_brush_size_via_vlm(agent, ve, ctx.cre_dir, "brush size slider — very thin end")
    badge_x = right_edge - 70
    badge_y = BODY_Y - 48
    # M
    _stroke([(badge_x, badge_y + 8), (badge_x, badge_y), (badge_x + 4, badge_y + 5),
             (badge_x + 8, badge_y), (badge_x + 8, badge_y + 8)])
    # 3
    _stroke([(badge_x + 12, badge_y), (badge_x + 18, badge_y),
             (badge_x + 18, badge_y + 4), (badge_x + 13, badge_y + 4)])
    _stroke([(badge_x + 18, badge_y + 4), (badge_x + 18, badge_y + 8),
             (badge_x + 12, badge_y + 8)])

    _checkpoint(agent, ctx.cre_dir, "bmw5_final", total_strokes, 100)
    print(f"  [BMW-V] Complete: {total_strokes} strokes")
    return {"status": "ok", "strokes": total_strokes}


def _handle_bmw_details(ctx, args: dict) -> dict:
    """Legacy alias for the old detail phase.

    Preserves dispatchability while routing through the modern BMW middle passes.
    """
    form_result = _handle_bmw_form_blocking(ctx, args)
    if form_result.get("status") != "ok":
        return form_result
    mechanical_result = _handle_bmw_mechanical(ctx, args)
    if mechanical_result.get("status") != "ok":
        return mechanical_result
    return {
        "status": "ok",
        "strokes": int(form_result.get("strokes", 0)) + int(mechanical_result.get("strokes", 0)),
        "phases": ["bmw_form_blocking", "bmw_mechanical"],
    }


def _handle_bmw_shading(ctx, args: dict) -> dict:
    """Legacy alias for the old shading phase."""
    lighting_result = _handle_bmw_lighting(ctx, args)
    if lighting_result.get("status") != "ok":
        return lighting_result
    return {
        "status": "ok",
        "strokes": int(lighting_result.get("strokes", 0)),
        "phases": ["bmw_lighting"],
    }


ACTION_HANDLERS = {
    "keystroke": _handle_keystroke,
    "type_text": _handle_type_text,
    "scroll": _handle_scroll,
    "screenshot": _handle_screenshot,
    "a11y_snapshot": _handle_a11y_snapshot,
    "clear_canvas": _handle_clear_canvas,
    "sleep": _handle_sleep,
    "refresh_canvas_center": _handle_refresh_canvas_center,
    "set_stroke_color": _handle_set_stroke_color,
    "click": _handle_click,
    "go_to_url": _handle_go_to_url,
    "go_back": _handle_go_back,
    "fix_triangle_base": _handle_fix_triangle_base,
    "connect_colored_dots": _handle_connect_colored_dots,
    "draw_concentric_triangles": _handle_draw_concentric_triangles,
    "draw_path_speed_test": _handle_draw_path_speed_test,
    "draw_path": _handle_draw_path,
    "draw_segments": _handle_draw_segments,
    "draw_circle": _handle_draw_circle,
    "draw_shape": _handle_draw_shape,
    "drag_shape": _handle_drag_shape,
    "draw_eiffel_tower": _handle_draw_eiffel_tower,
    "draw_eiffel_landscape": _handle_draw_eiffel_landscape,
    "verify_success": _handle_verify_success,
    "visual_assert": _handle_visual_assert,
    "browser_beforeunload_dialog": _handle_browser_beforeunload_dialog,
    "kleki_clear_canvas": _handle_kleki_clear_canvas,
    "kleki_set_color": _handle_kleki_set_color,
    "kleki_select_tool": _handle_kleki_select_tool,
    "kleki_set_brush_size": _handle_kleki_set_brush_size,
    "kleki_set_opacity": _handle_kleki_set_opacity,
    "kleki_set_scatter": _handle_kleki_set_scatter,
    "kleki_set_stabilizer": _handle_kleki_set_stabilizer,
    "kleki_reset_render_state": _handle_kleki_reset_render_state,
    "bmw_skeleton": _handle_bmw_skeleton,
    "bmw_details": _handle_bmw_details,
    "bmw_shading": _handle_bmw_shading,
    "bmw_form_blocking": _handle_bmw_form_blocking,
    "bmw_mechanical": _handle_bmw_mechanical,
    "bmw_lighting": _handle_bmw_lighting,
    "bmw_final": _handle_bmw_final,
}

_SOM_DEPENDENT_ACTIONS = {
    "set_stroke_color",
    "click",
    "kleki_set_color",
    "kleki_set_brush_size",
    "kleki_set_opacity",
    "kleki_set_scatter",
}
_RECOVERY_KEYCODES = {"escape": 53, "enter": 36, "space": 49}
_ACTION_EFFECT_CHECKS: dict[str, str | None] = {
    "clear_canvas": "Is the Excalidraw canvas now empty with no drawings visible? Reply YES or NO.",
    "keystroke": None, "type_text": None, "scroll": None, "screenshot": None,
    "a11y_snapshot": None, "sleep": None, "refresh_canvas_center": None,
    "set_stroke_color": None,
    "draw_concentric_triangles": "Are there nested triangles drawn on the Excalidraw canvas? Reply YES or NO.",
    "draw_path": "Is there a shape drawn on the Excalidraw canvas? Reply YES or NO.",
    "draw_segments": None,
    "draw_circle": "Is there a circle or circular shape drawn on the Excalidraw canvas? Reply YES or NO.",
    "draw_shape": None,
    "drag_shape": None,
    "draw_eiffel_tower": None,
    "draw_eiffel_landscape": None,
    "click": None, "go_to_url": None, "go_back": None, "fix_triangle_base": None, "connect_colored_dots": None,
    "draw_path_speed_test": None, "verify_success": None, "visual_assert": None,
    "browser_beforeunload_dialog": "Is the browser confirmation dialog asking whether to leave the page now gone? Reply YES or NO.",
    "kleki_clear_canvas": "Is the main drawing canvas now empty with no user-drawn marks visible? Reply YES or NO.",
    "kleki_set_color": None,
    "kleki_select_tool": None,
    "kleki_set_brush_size": None,
    "kleki_set_opacity": None,
    "kleki_set_scatter": None,
    "kleki_set_stabilizer": None,
    "kleki_reset_render_state": None,
    "bmw_skeleton": None,
    "bmw_form_blocking": None,
    "bmw_mechanical": None,
    "bmw_lighting": None,
    "bmw_final": None,
}
