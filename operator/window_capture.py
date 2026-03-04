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


def get_frontmost_application_name() -> str | None:
    """Return the localized name of the frontmost application, if available."""
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
    if Quartz is None:
        return None

    owner_name = owner_name or get_frontmost_application_name()
    try:
        windows = Quartz.CGWindowListCopyWindowInfo(
            Quartz.kCGWindowListOptionOnScreenOnly,
            Quartz.kCGNullWindowID,
        ) or []
    except Exception:
        return None

    for window in windows:
        if owner_name and window.get(Quartz.kCGWindowOwnerName) != owner_name:
            continue
        if int(window.get(Quartz.kCGWindowLayer, 1) or 1) != 0:
            continue
        if float(window.get(Quartz.kCGWindowAlpha, 1.0) or 1.0) <= 0.0:
            continue

        bounds = window.get(Quartz.kCGWindowBounds) or {}
        x = int(bounds.get("X", 0))
        y = int(bounds.get("Y", 0))
        width = int(bounds.get("Width", 0))
        height = int(bounds.get("Height", 0))
        if width < _MIN_WINDOW_WIDTH or height < _MIN_WINDOW_HEIGHT:
            continue
        if width * height < _MIN_WINDOW_AREA:
            continue

        window_id = int(window.get(Quartz.kCGWindowNumber, 0) or 0)
        if window_id <= 0:
            continue

        return {
            "owner_name": str(window.get(Quartz.kCGWindowOwnerName) or owner_name or ""),
            "window_id": window_id,
            "bounds": {
                "x": x,
                "y": y,
                "width": width,
                "height": height,
            },
        }
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
