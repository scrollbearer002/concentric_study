"""Window-scoped screenshot capture utilities for macOS GUI agents.

Uses Core Graphics window metadata plus the native ``screencapture`` CLI to
capture the frontmost application window instead of the entire desktop when
the task semantics are window-scoped.

Research and platform basis:
- Apple Window metadata guidance: CGWindowListCopyWindowInfo returns window
  size, position, and unique window identifier for onscreen windows.
  WWDC19, "Advances in macOS Security".
- macOS ``screencapture(1)`` supports ``-l <windowid>`` for window capture
  and ``-o`` to omit window shadows.
- Apple Quartz / high-resolution guidance: screen and window geometry must be
  handled carefully because capture APIs operate in global display space.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

try:
    import Quartz
    from AppKit import NSWorkspace
except Exception:  # pragma: no cover - pyobjc availability is environment-specific
    Quartz = None
    NSWorkspace = None


_MIN_WINDOW_WIDTH = 200
_MIN_WINDOW_HEIGHT = 160
_MIN_WINDOW_AREA = 60_000
_MAX_ELIGIBLE_LAYER = 1
_SYSTEM_WINDOW_OWNERS = {
    "Window Server",
    "Dock",
    "Control Center",
    "loginwindow",
    "Notification Center",
}


def _coerce_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(value)
    except Exception:
        return default


def _coerce_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def _onscreen_window_records() -> list[dict[str, Any]]:
    if Quartz is None:
        return []
    try:
        return Quartz.CGWindowListCopyWindowInfo(
            Quartz.kCGWindowListOptionOnScreenOnly,
            Quartz.kCGNullWindowID,
        ) or []
    except Exception:
        return []


def _eligible_window(window: dict[str, Any], *, owner_name: str | None = None) -> dict[str, Any] | None:
    owner = str(window.get(Quartz.kCGWindowOwnerName) or "")
    if owner_name and owner != owner_name:
        return None
    if not owner:
        return None
    if not owner_name and owner in _SYSTEM_WINDOW_OWNERS:
        return None

    layer = _coerce_int(window.get(Quartz.kCGWindowLayer), 999)
    if layer < 0 or layer > _MAX_ELIGIBLE_LAYER:
        return None
    if _coerce_float(window.get(Quartz.kCGWindowAlpha), 1.0) <= 0.0:
        return None

    bounds = window.get(Quartz.kCGWindowBounds) or {}
    x = _coerce_int(bounds.get("X"), 0)
    y = _coerce_int(bounds.get("Y"), 0)
    width = _coerce_int(bounds.get("Width"), 0)
    height = _coerce_int(bounds.get("Height"), 0)
    if width < _MIN_WINDOW_WIDTH or height < _MIN_WINDOW_HEIGHT:
        return None
    if width * height < _MIN_WINDOW_AREA:
        return None

    window_id = _coerce_int(window.get(Quartz.kCGWindowNumber), 0)
    if window_id <= 0:
        return None

    return {
        "owner_name": owner,
        "window_id": window_id,
        "bounds": {
            "x": x,
            "y": y,
            "width": width,
            "height": height,
        },
    }


def get_frontmost_application_name() -> str | None:
    """Return the best available frontmost-app signal for visible work.

    Quartz window z-order is the primary signal because it reflects visible
    onscreen ordering in the current Space. NSWorkspace remains a fallback for
    environments where Quartz metadata is unavailable.
    """
    for window in _onscreen_window_records():
        eligible = _eligible_window(window)
        if eligible is not None:
            return eligible["owner_name"]

    if NSWorkspace is None:
        return None
    try:
        app = NSWorkspace.sharedWorkspace().frontmostApplication()
        if app is None:
            return None
        name = app.localizedName()
        return str(name) if name else None
    except Exception:
        return None


def get_front_window_info(owner_name: str | None = None) -> dict[str, Any] | None:
    """Return metadata for the first eligible onscreen top-level window.

    Windows are returned in z-order by Core Graphics. Filtering to layer 0 and
    a minimum visible size eliminates menu bars, tooltips, and tiny utility
    panels that are not meaningful task surfaces.
    """
    owner_name = owner_name or get_frontmost_application_name()
    for window in _onscreen_window_records():
        eligible = _eligible_window(window, owner_name=owner_name)
        if eligible is not None:
            return eligible
    return None


def capture_front_window(
    path: str | Path,
    *,
    owner_name: str | None = None,
    fallback_to_fullscreen: bool = True,
    timeout_seconds: int = 5,
    include_cursor: bool = False,
) -> dict[str, Any]:
    """Capture the frontmost window when possible, else fall back to display.

    Returns metadata describing which capture path succeeded.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    info = get_front_window_info(owner_name=owner_name)
    if info is not None:
        cmd = ["screencapture", "-x", "-o"]
        if include_cursor:
            cmd.append("-C")
        cmd.extend(["-l", str(info["window_id"]), str(path)])
        result = subprocess.run(cmd, timeout=timeout_seconds, capture_output=True)
        if result.returncode == 0 and path.exists() and path.stat().st_size > 0:
            return {
                "mode": "window",
                "owner_name": info["owner_name"],
                "window_id": info["window_id"],
                "bounds": info["bounds"],
                "path": str(path),
            }

    if not fallback_to_fullscreen:
        raise RuntimeError("Could not capture front window")

    cmd = ["screencapture", "-x"]
    if include_cursor:
        cmd.append("-C")
    cmd.append(str(path))
    result = subprocess.run(cmd, timeout=timeout_seconds, capture_output=True)
    if result.returncode != 0 or not path.exists() or path.stat().st_size == 0:
        raise RuntimeError("Could not capture display screenshot")
    return {
        "mode": "display",
        "owner_name": owner_name or get_frontmost_application_name() or "",
        "window_id": None,
        "bounds": None,
        "path": str(path),
    }
