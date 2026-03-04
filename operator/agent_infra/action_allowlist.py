"""Pre-action allowlist verification for GUI agents.

Deterministic block-before-execute checks: allowed action types and parameter
constraints (e.g. coordinates in screen bounds, keystrokes from a safe set).
Aligns with VeriSafe Agent (Lee et al., arXiv:2503.18492) and FormalJudge
(arXiv:2602.11136). See operator/cre/ALLOWLIST_PREACTION_IMPLEMENTATION_OUTLINE.md.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class AllowlistResult:
    """Result of a single allowlist check."""
    allowed: bool
    reason: str | None = None  # violation code if not allowed


@dataclass
class ActionAllowlistConfig:
    """Configuration for the action allowlist."""
    allowed_action_types: set[str] = field(default_factory=set)
    screen_bounds: tuple[int, int, int, int] | None = None  # (x_min, x_max, y_min, y_max) pixels
    coord_actions: set[str] = field(default_factory=lambda: {"click", "draw_path", "draw_shape"})
    keystroke_allowed_keys: set[str] | None = None  # None = allow any key
    critical_actions: set[str] = field(default_factory=lambda: {"click", "keystroke"})

    @classmethod
    def from_json(cls, path: str | Path) -> "ActionAllowlistConfig":
        """Load config from JSON. Keys: allowed_action_types (list), coord_actions (list),
        keystroke_allowed_keys (list or null), critical_actions (list), screen_bounds (list of 4 ints or null).
        """
        with open(path) as f:
            data = json.load(f)
        allowed = set(data.get("allowed_action_types", []))
        coord = set(data.get("coord_actions", ["click", "draw_path", "draw_shape"]))
        keys = data.get("keystroke_allowed_keys")
        keystroke = set(keys) if isinstance(keys, list) else None
        critical = set(data.get("critical_actions", ["click", "keystroke"]))
        bounds = data.get("screen_bounds")
        if isinstance(bounds, list) and len(bounds) == 4:
            screen_bounds = (int(bounds[0]), int(bounds[1]), int(bounds[2]), int(bounds[3]))
        else:
            screen_bounds = None
        return cls(
            allowed_action_types=allowed,
            screen_bounds=screen_bounds,
            coord_actions=coord,
            keystroke_allowed_keys=keystroke,
            critical_actions=critical,
        )


def get_screen_bounds_from_agent(agent: Any) -> tuple[int, int, int, int] | None:
    """Derive pixel bounds (x_min, x_max, y_min, y_max) from agent.get_screen_info().
    Returns None if agent or get_screen_info is unavailable.
    """
    if agent is None or not hasattr(agent, "get_screen_info"):
        return None
    try:
        info = agent.get_screen_info()
        w = int(info.get("logical_width", 1440) * info.get("scale_factor", 2.0))
        h = int(info.get("logical_height", 900) * info.get("scale_factor", 2.0))
        return (0, w, 0, h)
    except Exception:
        return None


# Fallback for headless or when NSScreen is unavailable (e.g. Retina 2880x1800).
DEFAULT_SCREEN_BOUNDS = (0, 2880, 0, 1800)


class ActionAllowlist:
    """Pre-action verifier: checks proposed actions against an allowlist before execution."""

    def __init__(self, config: ActionAllowlistConfig) -> None:
        self.config = config

    def check_action(
        self,
        action_type: str,
        args: dict[str, Any],
        screen_bounds: tuple[int, int, int, int] | None = None,
    ) -> AllowlistResult:
        """
        Returns AllowlistResult(allowed, reason). If allowed is False, reason is the
        violation code (e.g. action_type_not_in_allowlist, coords_out_of_bounds,
        keystroke_key_not_allowed).
        """
        if action_type not in self.config.allowed_action_types:
            return AllowlistResult(False, "action_type_not_in_allowlist")

        bounds = screen_bounds or self.config.screen_bounds
        if action_type in self.config.coord_actions and bounds:
            x, y = args.get("x"), args.get("y")
            if x is not None and y is not None:
                x_min, x_max, y_min, y_max = bounds
                if not (x_min <= x <= x_max and y_min <= y <= y_max):
                    return AllowlistResult(False, "coords_out_of_bounds")

        if action_type in ("keystroke", "key") and self.config.keystroke_allowed_keys is not None:
            key = args.get("key")
            if key is not None:
                key_str = str(key).strip().lower()
                if key_str not in self.config.keystroke_allowed_keys:
                    return AllowlistResult(False, "keystroke_key_not_allowed")

        return AllowlistResult(True, None)

    @classmethod
    def from_handlers(cls, handler_keys: set[str] | list[str], **config_overrides: Any) -> "ActionAllowlist":
        """Build allowlist with allowed_action_types = handler_keys. Optional overrides
        for coord_actions, keystroke_allowed_keys, screen_bounds, critical_actions.
        """
        allowed = set(handler_keys)
        config = ActionAllowlistConfig(
            allowed_action_types=allowed,
            coord_actions=config_overrides.get("coord_actions") or {"click", "draw_path", "draw_shape"},
            keystroke_allowed_keys=config_overrides.get("keystroke_allowed_keys"),
            screen_bounds=config_overrides.get("screen_bounds"),
            critical_actions=config_overrides.get("critical_actions") or {"click", "keystroke"},
        )
        return cls(config)

    @classmethod
    def from_json(cls, path: str | Path) -> "ActionAllowlist":
        """Load config from JSON file and return ActionAllowlist instance."""
        return cls(ActionAllowlistConfig.from_json(path))
