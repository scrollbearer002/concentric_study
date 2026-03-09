"""Unified action space for the universal orchestrator.

Abstracts the flat ACTION_HANDLERS dictionary into a typed, semantically
rich action space that the VLM planner can reason about and the executor
can dispatch without per-task scripting.

Architecture grounded in:
- CogAgent (Hong et al., CVPR 2024): Single action space across web,
  desktop, and mobile — actions are {click, type, scroll, key, wait}.
- DynaSaur (Adobe, COLM 2025, arXiv:2411.01747): Agents dynamically
  create new actions as Python programs; actions accumulate in a
  reusable library for future tasks.
- WebVoyager (He et al., 2024): Minimal action space {click, type,
  scroll, wait, go_back, answer} generalizes across 15 live websites.
- OSWorld (Xie et al., NeurIPS 2024): Universal observation + action
  space across Ubuntu/Windows/macOS — mouse + keyboard primitives.
- SeeAct (Zheng et al., ICML 2024): Two-stage action generation
  (semantic description) then grounding (coordinate resolution).

The key insight from the literature: a small set of parameterized
semantic primitives (click, type, key, draw, scroll, wait, assert)
composes to handle any GUI task. Domain-specific compound actions
(draw_concentric_triangles, bmw_skeleton) are registered as
reusable macros that expand into primitive sequences.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any


class ActionCategory(Enum):
    """Broad categories following CogAgent's unified action taxonomy."""
    PRIMITIVE = auto()     # click, type, key, scroll, wait
    PERCEPTION = auto()    # screenshot, assert_visual, a11y_snapshot
    DRAWING = auto()       # draw_path, draw_shape (parameterized)
    NAVIGATION = auto()    # go_to_url, go_back, refresh
    COMPOUND = auto()      # domain-specific macros that expand to primitives


@dataclass
class ActionSpec:
    """Specification for a single action in the unified space."""
    name: str
    category: ActionCategory
    description: str
    parameters: dict[str, str]  # param_name -> type description
    required_params: list[str] = field(default_factory=list)
    visual_assert: str = ""
    handler_key: str = ""  # maps to ACTION_HANDLERS key if it exists
    planner_visible: bool = True  # surfaced to the universal planner by default

    def to_planner_schema(self) -> dict[str, Any]:
        """Produce schema the VLM planner can consume."""
        schema: dict[str, Any] = {
            "action": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }
        if self.required_params:
            schema["required"] = self.required_params
        return schema


# -----------------------------------------------------------------------
# Universal primitive actions (CogAgent / WebVoyager / OSWorld consensus)
# -----------------------------------------------------------------------

PRIMITIVE_ACTIONS: list[ActionSpec] = [
    ActionSpec(
        name="click",
        category=ActionCategory.PRIMITIVE,
        description="Click at absolute screen coordinates or on a labeled element",
        parameters={
            "x": "int (pixels)",
            "y": "int (pixels)",
            "label": "str (optional, resolved via element map)",
            "confirm_before_click": "bool (optional, capture cursor-visible screenshot and confirm risky click before executing)",
            "expected_effect": "str (optional, what the click is supposed to do)",
        },
        handler_key="click",
    ),
    ActionSpec(
        name="type",
        category=ActionCategory.PRIMITIVE,
        description="Type text into the currently focused element",
        parameters={"text": "str"},
        required_params=["text"],
        handler_key="type_text",
    ),
    ActionSpec(
        name="key",
        category=ActionCategory.PRIMITIVE,
        description="Press a keyboard key or shortcut",
        parameters={"key": "str (key name, char, or keycode)", "modifiers": "list[str] (optional: cmd, shift, ctrl, alt)"},
        required_params=["key"],
        handler_key="keystroke",
    ),
    ActionSpec(
        name="scroll",
        category=ActionCategory.PRIMITIVE,
        description="Scroll the page or a specific element",
        parameters={"direction": "str (up/down/left/right)", "amount": "int (pixels, default 300)"},
        handler_key="scroll",
    ),
    ActionSpec(
        name="wait",
        category=ActionCategory.PRIMITIVE,
        description="Wait for a specified duration or until a condition is met",
        parameters={"seconds": "float", "until": "str (optional visual assertion)"},
        handler_key="sleep",
    ),
]

PERCEPTION_ACTIONS: list[ActionSpec] = [
    ActionSpec(
        name="screenshot",
        category=ActionCategory.PERCEPTION,
        description="Capture the current screen state",
        parameters={"save_path": "str (optional)"},
        handler_key="screenshot",
    ),
    ActionSpec(
        name="assert_visual",
        category=ActionCategory.PERCEPTION,
        description="Ask the VLM to verify a visual condition (YES/NO)",
        parameters={"assertion": "str (the question to ask)"},
        required_params=["assertion"],
        handler_key="visual_assert",
    ),
    ActionSpec(
        name="a11y_snapshot",
        category=ActionCategory.PERCEPTION,
        description="Extract the accessibility tree of the frontmost application",
        parameters={"app_name": "str (default: Safari)"},
        handler_key="a11y_snapshot",
    ),
    ActionSpec(
        name="refresh_perception",
        category=ActionCategory.PERCEPTION,
        description="Re-capture screenshot, re-run SoM overlay, re-extract a11y, update element map",
        parameters={},
        handler_key="refresh_canvas_center",
    ),
]

DRAWING_ACTIONS: list[ActionSpec] = [
    ActionSpec(
        name="draw_path",
        category=ActionCategory.DRAWING,
        description="Draw a freehand path through a sequence of vertices",
        parameters={"vertices": "list[list[int]] — [[x1,y1],[x2,y2],...]",
                     "closed": "bool (connect last to first, default true)",
                     "drag_delay": "float (seconds between points, default 0.05)"},
        required_params=["vertices"],
        handler_key="draw_path",
    ),
    ActionSpec(
        name="draw_segments",
        category=ActionCategory.DRAWING,
        description="Draw independent straight or structural line segments without collapsing them into one polyline",
        parameters={
            "segments": "list[list[list[int]]] — [[[x1,y1],[x2,y2]], ...]",
            "straight": "bool (hold Shift-style straight-line mode when supported, default true)",
        },
        required_params=["segments"],
        handler_key="draw_segments",
    ),
    ActionSpec(
        name="draw_shape",
        category=ActionCategory.DRAWING,
        description="Draw a geometric shape by type (parameterized, not hardcoded)",
        parameters={"shape_type": "str (triangle/circle/rectangle/ellipse/polygon)",
                     "size": "int (radius or half-side in pixels)",
                     "center_x": "int (optional, default canvas center)",
                     "center_y": "int (optional, default canvas center)",
                     "sides": "int (for polygon, default 3)",
                     "fill_color": "str (optional)",
                     "stroke_color": "str (optional)"},
        required_params=["shape_type", "size"],
        handler_key="draw_shape",
    ),
    ActionSpec(
        name="set_stroke_color",
        category=ActionCategory.DRAWING,
        description="Set the drawing stroke color via keyboard shortcut + palette click",
        parameters={"color": "str (color name)"},
        required_params=["color"],
        handler_key="set_stroke_color",
    ),
    ActionSpec(
        name="kleki_set_color",
        category=ActionCategory.DRAWING,
        description="Set the active Kleki drawing color using the right-side color picker",
        parameters={"color": "str (for example: black, dark gray, light gray, white)"},
        required_params=["color"],
        handler_key="kleki_set_color",
    ),
    ActionSpec(
        name="kleki_set_brush_size",
        category=ActionCategory.DRAWING,
        description="Adjust Kleki brush thickness using the brush settings panel",
        parameters={"size": "str (for example: very thin, thin, medium, thick, wide)"},
        required_params=["size"],
        handler_key="kleki_set_brush_size",
    ),
    ActionSpec(
        name="kleki_set_opacity",
        category=ActionCategory.DRAWING,
        description="Adjust Kleki brush opacity using the brush settings panel",
        parameters={"opacity": "str (for example: 100%, high, medium, low)"},
        required_params=["opacity"],
        handler_key="kleki_set_opacity",
    ),
    ActionSpec(
        name="kleki_set_scatter",
        category=ActionCategory.DRAWING,
        description="Adjust Kleki brush scatter so tonal work stays controlled instead of noisy",
        parameters={"scatter": "str (for example: 0, low, medium, high)"},
        required_params=["scatter"],
        handler_key="kleki_set_scatter",
    ),
    ActionSpec(
        name="kleki_set_stabilizer",
        category=ActionCategory.DRAWING,
        description="Adjust Kleki brush stabilizer for deterministic line discipline",
        parameters={"stabilizer": "str (for example: 1, low, medium, high)"},
        required_params=["stabilizer"],
        handler_key="kleki_set_stabilizer",
    ),
    ActionSpec(
        name="kleki_select_tool",
        category=ActionCategory.DRAWING,
        description="Select a Kleki drawing tool such as brush, eraser, or shape/line mode",
        parameters={"tool": "str (for example: brush, eraser, shape)"},
        required_params=["tool"],
        handler_key="kleki_select_tool",
    ),
    ActionSpec(
        name="kleki_reset_render_state",
        category=ActionCategory.DRAWING,
        description="Normalize the Kleki render state before architectural drawing: tool, scatter, stabilizer, size, and opacity",
        parameters={
            "tool": "str (default brush)",
            "size": "str (default very thin)",
            "opacity": "str (default 100%)",
            "scatter": "str (default 0)",
            "stabilizer": "str (default 1)",
        },
        handler_key="kleki_reset_render_state",
    ),
]

NAVIGATION_ACTIONS: list[ActionSpec] = [
    ActionSpec(
        name="go_to_url",
        category=ActionCategory.NAVIGATION,
        description="Navigate to a URL in the browser",
        parameters={"url": "str"},
        required_params=["url"],
        handler_key="go_to_url",
    ),
    ActionSpec(
        name="go_back",
        category=ActionCategory.NAVIGATION,
        description="Navigate back in browser history",
        parameters={},
        handler_key="go_back",
    ),
    ActionSpec(
        name="browser_beforeunload_dialog",
        category=ActionCategory.NAVIGATION,
        description="Click the browser leave-page confirmation dialog to either stay on the current page or leave it",
        parameters={"choice": "str (stay or leave)"},
        required_params=["choice"],
        handler_key="browser_beforeunload_dialog",
    ),
]

COMPOUND_ACTIONS: list[ActionSpec] = [
    ActionSpec(
        name="clear_canvas",
        category=ActionCategory.COMPOUND,
        description="Clear the drawing canvas (Cmd+A, Delete, confirm dialog)",
        parameters={},
        handler_key="clear_canvas",
    ),
    ActionSpec(
        name="kleki_clear_canvas",
        category=ActionCategory.COMPOUND,
        description="Clear the Kleki raster canvas using select-all plus delete",
        parameters={},
        handler_key="kleki_clear_canvas",
    ),
    ActionSpec(
        name="draw_concentric_triangles",
        category=ActionCategory.COMPOUND,
        description="Draw N nested concentric triangles at canvas center",
        parameters={"sizes": "list[int] (radii, e.g. [220,160,100,50])",
                     "inter_triangle_delay": "float (seconds between triangles)"},
        handler_key="draw_concentric_triangles",
    ),
    ActionSpec(
        name="draw_eiffel_tower",
        category=ActionCategory.COMPOUND,
        description="Draw an Eiffel Tower with exponential-profile legs and details",
        parameters={"scale": "float (default 1.0)", "offset_x": "int", "offset_y": "int"},
        handler_key="draw_eiffel_tower",
    ),
    ActionSpec(
        name="draw_eiffel_landscape",
        category=ActionCategory.COMPOUND,
        description="Draw a complete Paris landscape with sky, ground, river, buildings, Eiffel Tower",
        parameters={},
        handler_key="draw_eiffel_landscape",
    ),
    ActionSpec(
        name="login_flow",
        category=ActionCategory.COMPOUND,
        description="Execute a login flow: find fields, enter credentials, submit",
        parameters={"domain": "str", "email_field_label": "str (optional)",
                     "password_field_label": "str (optional)"},
        handler_key="login_flow",
        planner_visible=False,
    ),
]

# BMW Kleki compound actions
BMW_ACTIONS: list[ActionSpec] = [
    ActionSpec(
        name="bmw_skeleton",
        category=ActionCategory.COMPOUND,
        description="Draw the BMW E30 M3 skeleton outline on Kleki canvas",
        parameters={},
        handler_key="bmw_skeleton",
    ),
    ActionSpec(
        name="bmw_details",
        category=ActionCategory.COMPOUND,
        description="Add detail features to the BMW drawing",
        parameters={},
        handler_key="bmw_details",
    ),
    ActionSpec(
        name="bmw_shading",
        category=ActionCategory.COMPOUND,
        description="Add shading and depth to the BMW drawing",
        parameters={},
        handler_key="bmw_shading",
    ),
    ActionSpec(
        name="bmw_final",
        category=ActionCategory.COMPOUND,
        description="Final refinement pass on the BMW drawing",
        parameters={},
        handler_key="bmw_final",
    ),
]


class UnifiedActionSpace:
    """The complete action space available to the universal orchestrator.

    Follows DynaSaur's principle: start with a base set of primitives,
    then dynamically register compound actions discovered during
    exploration or loaded from the skill library.
    """

    def __init__(self) -> None:
        self._actions: dict[str, ActionSpec] = {}
        for spec in (PRIMITIVE_ACTIONS + PERCEPTION_ACTIONS +
                     DRAWING_ACTIONS + NAVIGATION_ACTIONS +
                     COMPOUND_ACTIONS + BMW_ACTIONS):
            self._actions[spec.name] = spec

    def register(self, spec: ActionSpec) -> None:
        """Register a new action (e.g., from skill library or VLM-generated)."""
        self._actions[spec.name] = spec

    def get(self, name: str) -> ActionSpec | None:
        return self._actions.get(name)

    def list_names(self) -> list[str]:
        return sorted(self._actions.keys())

    def list_planner_names(self) -> list[str]:
        """Return only the action names that are safe to expose to planners."""
        return sorted(
            spec.name
            for spec in self._actions.values()
            if spec.planner_visible
        )

    def list_by_category(self, category: ActionCategory) -> list[ActionSpec]:
        return [a for a in self._actions.values() if a.category == category]

    def to_planner_context(
        self,
        categories: list[ActionCategory] | None = None,
        *,
        include_non_planner_visible: bool = False,
    ) -> str:
        """Generate a compact action schema string for VLM prompt injection.

        If categories is None, include all. Otherwise filter.
        """
        specs = [
            spec for spec in self._actions.values()
            if include_non_planner_visible or spec.planner_visible
        ]
        if categories:
            specs = [s for s in specs if s.category in categories]

        lines = []
        for spec in sorted(specs, key=lambda s: s.name):
            params = ", ".join(f"{k}: {v}" for k, v in spec.parameters.items())
            lines.append(f"  {spec.name}({params}) — {spec.description}")
        return "\n".join(lines)

    def to_handler_key_map(self) -> dict[str, str]:
        """Map action names to their ACTION_HANDLERS keys for dispatch."""
        return {
            name: spec.handler_key
            for name, spec in self._actions.items()
            if spec.handler_key
        }

    def planner_to_handler_key_map(self) -> dict[str, str]:
        """Map planner-visible action names to dispatcher keys."""
        return {
            name: spec.handler_key
            for name, spec in self._actions.items()
            if spec.planner_visible and spec.handler_key
        }

    def conformance_report(self, live_handler_keys: set[str] | list[str]) -> dict[str, list[str]]:
        """Compare planner-visible actions against the live dispatcher surface."""
        handler_keys = set(live_handler_keys)
        missing = [
            name
            for name, handler_key in sorted(self.planner_to_handler_key_map().items())
            if handler_key not in handler_keys
        ]
        hidden = [
            spec.name
            for spec in sorted(self._actions.values(), key=lambda spec: spec.name)
            if not spec.planner_visible
        ]
        return {
            "missing_handler_actions": missing,
            "hidden_actions": hidden,
        }

    def to_planner_schema_list(
        self,
        *,
        include_non_planner_visible: bool = False,
    ) -> list[dict[str, Any]]:
        return [
            spec.to_planner_schema()
            for spec in self._actions.values()
            if include_non_planner_visible or spec.planner_visible
        ]

    def resolve_action(self, action_dict: dict[str, Any]) -> dict[str, Any]:
        """Normalize an action dict from VLM output to executor format.

        The VLM planner may use unified action names (e.g., "key") or
        legacy handler keys (e.g., "keystroke"). This method normalizes
        both to the executor's expected format.
        """
        action_name = action_dict.get("action", "")
        spec = self._actions.get(action_name)

        if spec and spec.handler_key and spec.handler_key != action_name:
            resolved = dict(action_dict)
            resolved["action"] = spec.handler_key
            return resolved

        return action_dict
