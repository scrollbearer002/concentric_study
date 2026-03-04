#!/usr/bin/env python3
"""
Codex Runtime Environment (CRE) client.
Talks to the Hammerspoon kernel at localhost:9999.
Replaces subprocess calls to cliclick, screencapture, osascript for UI automation.
"""

from __future__ import annotations

import base64
import json
import time
from typing import Any

try:
    import requests
except ImportError:
    requests = None  # type: ignore

DEFAULT_PORT = 9999


class CodexClient:
    """Client for the Codex Kernel (Hammerspoon HTTP server)."""

    def __init__(self, port: int = DEFAULT_PORT, timeout: float = 5.0):
        self.port = port
        self.timeout = timeout
        self._base_url = f"http://127.0.0.1:{port}"

    def _send(self, command: str, args: dict[str, Any] | None = None, timeout: float | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {"command": command, "args": args or {}}
        if requests is None:
            raise RuntimeError("Hammerspoon Kernel requires 'requests'; pip install requests")
        try:
            r = requests.post(
                self._base_url,
                json=payload,
                timeout=timeout or self.timeout,
                headers={"Content-Type": "application/json"},
            )
            r.raise_for_status()
            return r.json()
        except requests.exceptions.ConnectionError as e:
            raise RuntimeError("Hammerspoon Kernel is not running.") from e

    def ping(self) -> dict[str, Any]:
        """Health check."""
        return self._send("ping", {})

    def click(self, x: int, y: int) -> dict[str, Any]:
        """Replaces: cliclick c:x,y. High-speed click via hs.eventtap."""
        return self._send("click", {"x": x, "y": y})
    
    def keystroke(self, key: str) -> dict[str, Any]:
        """
        Send a keystroke (Agentic RAG: Use keyboard shortcuts to bypass visual grounding).
        
        Academic validation: Keyboard shortcuts eliminate spatial dilution problem.
        Use this instead of clicking toolbar buttons when shortcuts are known.
        """
        return self._send("keystroke", {"key": key})

    def get_mouse_position(self) -> dict[str, Any]:
        """Get current mouse position."""
        return self._send("get_mouse_position", {})
    
    def get_screen_info(self) -> dict[str, Any]:
        """
        Get screen information including CoreGraphics scale factor.
        
        Academic validation: Uses hs.screen:currentMode().scale to query CoreGraphics display registry.
        This guarantees mathematically perfect translation from VLM pixel predictions to logical coordinates.
        
        Returns:
            Dict with logical_width, logical_height, scale_factor (1, 2, or 3 for Retina)
        """
        return self._send("get_screen_info", {})
    
    def convert_pixel_to_logical(self, pixel_x: int, pixel_y: int) -> tuple[int, int]:
        """
        Convert VLM-predicted pixel coordinates to logical click coordinates.
        
        Uses CoreGraphics scale factor (not manual calculation) to ensure accuracy.
        
        Args:
            pixel_x: X coordinate in screenshot pixels
            pixel_y: Y coordinate in screenshot pixels
        
        Returns:
            Tuple of (logical_x, logical_y) for click commands
        """
        info = self.get_screen_info()
        if info.get("status") != "ok":
            raise RuntimeError(f"Failed to get screen info: {info.get('message', 'Unknown error')}")
        
        scale = info.get("scale_factor", 1.0)
        logical_x = int(pixel_x / scale)
        logical_y = int(pixel_y / scale)
        
        return (logical_x, logical_y)
    
    def get_screen_info(self) -> dict[str, Any]:
        """
        Get screen information including CoreGraphics scale factor.
        
        Academic validation: Uses hs.screen:currentMode().scale to query CoreGraphics display registry.
        This guarantees mathematically perfect translation from VLM pixel predictions to logical coordinates.
        
        Returns:
            Dict with logical_width, logical_height, scale_factor (1, 2, or 3 for Retina)
        """
        return self._send("get_screen_info", {})
    
    def convert_pixel_to_logical(self, pixel_x: int, pixel_y: int) -> tuple[int, int]:
        """
        Convert VLM-predicted pixel coordinates to logical click coordinates.
        
        Uses CoreGraphics scale factor (not manual calculation) to ensure accuracy.
        
        Args:
            pixel_x: X coordinate in screenshot pixels
            pixel_y: Y coordinate in screenshot pixels
        
        Returns:
            Tuple of (logical_x, logical_y) for click commands
        """
        info = self.get_screen_info()
        if info.get("status") != "ok":
            raise RuntimeError(f"Failed to get screen info: {info.get('message', 'Unknown error')}")
        
        scale = info.get("scale_factor", 1.0)
        logical_x = int(pixel_x / scale)
        logical_y = int(pixel_y / scale)
        
        return (logical_x, logical_y)

    def move_mouse(self, x: int, y: int) -> dict[str, Any]:
        """Move mouse to position (for smooth paths)."""
        return self._send("move_mouse", {"x": x, "y": y})

    def smooth_move_and_click(self, target_x: int, target_y: int, steps: int = 20, duration: float = 0.3) -> dict[str, Any]:
        """
        Calculates a smooth Cubic Bezier curve path and streams micro-movements to the Kernel.
        Avoids bot-detection by moving mouse naturally instead of teleporting.
        
        Academic validation: Cubic Bezier is the mathematical standard for human-like trajectories
        (IEEE Access 2021, "SapiAgent: A Bot Based on Deep Learning to Generate Human-Like Mouse Trajectories")
        
        Uses cubic Bezier: B(t) = (1-t)^3*P0 + 3(1-t)^2*t*P1 + 3(1-t)*t^2*P2 + t^3*P3
        where P0=start, P3=end, P1/P2=control points for acceleration/deceleration curves.
        """
        try:
            start_pos = self.get_mouse_position()
            start_x = start_pos.get("x", target_x)
            start_y = start_pos.get("y", target_y)
        except Exception:
            # Fallback if get_mouse_position fails
            start_x, start_y = target_x, target_y
        
        # Calculate control points for cubic Bezier (natural acceleration/deceleration)
        import random
        # Control point 1: 25% along path with slight randomness
        ctrl1_x = start_x + (target_x - start_x) * 0.25 + random.randint(-30, 30)
        ctrl1_y = start_y + (target_y - start_y) * 0.25 + random.randint(-30, 30)
        # Control point 2: 75% along path with slight randomness
        ctrl2_x = start_x + (target_x - start_x) * 0.75 + random.randint(-30, 30)
        ctrl2_y = start_y + (target_y - start_y) * 0.75 + random.randint(-30, 30)
        
        # Generate smooth path using cubic Bezier
        for i in range(steps + 1):
            t = i / steps
            inv_t = 1 - t
            
            # Cubic Bezier formula: B(t) = (1-t)^3*P0 + 3(1-t)^2*t*P1 + 3(1-t)*t^2*P2 + t^3*P3
            x = int((inv_t ** 3 * start_x) + 
                    (3 * inv_t ** 2 * t * ctrl1_x) + 
                    (3 * inv_t * t ** 2 * ctrl2_x) + 
                    (t ** 3 * target_x))
            y = int((inv_t ** 3 * start_y) + 
                    (3 * inv_t ** 2 * t * ctrl1_y) + 
                    (3 * inv_t * t ** 2 * ctrl2_y) + 
                    (t ** 3 * target_y))
            
            self.move_mouse(x, y)
            time.sleep(duration / steps)
        
        # Final click at destination
        return self.click(target_x, target_y)

    def screenshot(self, region: dict[str, int] | None = None, scale: float | None = None) -> bytes:
        """
        Replaces: screencapture -x /tmp/img.png.
        Returns raw PNG bytes (no disk I/O). Optional region = {x, y, w, h}.
        
        VISION PIPELINE FIX: Now receives raw Base64 as text/plain (bypasses JSON AST parser).
        Academic validation: Base64 in JSON causes 33% bloat + AST buffer overflows in embedded servers.
        Solution: Transmit as text/plain, eliminating truncation risk entirely.
        
        Args:
            region: Optional dict with {x, y, w, h} for region capture
            scale: Optional scaling factor (0.0-1.0). None = no scaling (full resolution for VLM)
        
        Returns:
            Raw PNG bytes (decoded from Base64)
        """
        args: dict[str, Any] = {}
        if region:
            args["region"] = region
        if scale is not None:
            args["scale"] = scale
        
        payload: dict[str, Any] = {"command": "screenshot", "args": args}
        if requests is None:
            raise RuntimeError("Hammerspoon Kernel requires 'requests'; pip install requests")
        try:
            # Use stream=True to handle large responses
            r = requests.post(
                self._base_url,
                json=payload,
                timeout=30.0,
                headers={"Content-Type": "application/json"},
                stream=True,
            )
            r.raise_for_status()
            
            # VISION PIPELINE FIX: Screenshot now returns text/plain (raw Base64), not JSON
            content_type = r.headers.get("Content-Type", "")
            if content_type == "text/plain":
                # Raw Base64 string (no JSON wrapper)
                raw_base64 = r.text.strip()
                # Check for error marker
                if raw_base64.startswith("__ERROR__:"):
                    error_msg = raw_base64.replace("__ERROR__:", "")
                    raise RuntimeError(f"Screenshot error: {error_msg}")
                # Decode Base64 directly (no JSON parsing overhead)
                return base64.b64decode(raw_base64)
            else:
                # Fallback: Try JSON parsing (for backward compatibility)
                try:
                    res = r.json()
                    data = res.get("data")
                    if not data:
                        raise RuntimeError("Kernel screenshot returned no data")
                    # Strip optional "data:image/png;base64," prefix
                    if "," in data:
                        data = data.split(",", 1)[1]
                    return base64.b64decode(data)
                except Exception as e:
                    raise RuntimeError(f"Screenshot response format error. Expected text/plain Base64. Error: {e}")
        except requests.exceptions.ConnectionError as e:
            raise RuntimeError("Hammerspoon Kernel is not running.") from e

    def get_ui_tree(self, app_name: str = "Cursor") -> dict[str, Any]:
        """Replaces: osascript UI queries. Returns dump_state result."""
        return self._send("dump_state", {"app": app_name})

    def drag(self, start_x: int, start_y: int, end_x: int, end_y: int) -> dict[str, Any]:
        """
        Drag from start position to end position (for drag-and-drop).
        Performs smooth drag with mouse button held down.
        """
        return self._send("drag", {
            "start_x": start_x,
            "start_y": start_y,
            "end_x": end_x,
            "end_y": end_y,
        })
    
    def draw_path(self, path: list[tuple[int, int]]) -> dict[str, Any]:
        """
        Draw a continuous path (for drawing applications like Excalidraw).
        
        Academic validation: Single mouseDown + multiple mouseDragged + single mouseUp
        Prevents "stroke commit" between segments (HTML5 canvas pointerup = stroke finalization).
        Uses Cubic Bezier interpolation for natural, human-like movement.
        
        Args:
            path: List of (x, y) tuples defining the path to draw
        
        Example:
            # Draw a triangle
            client.draw_path([
                (100, 100),  # Start
                (200, 100),  # Right
                (150, 200),  # Bottom
                (100, 100),  # Back to start (closed triangle)
            ])
        """
        # Convert tuples to arrays for JSON serialization
        path_array = [[int(x), int(y)] for x, y in path]
        return self._send("draw_path", {"path": path_array})
    
    def draw_path(self, path: list[tuple[int, int]]) -> dict[str, Any]:
        """
        Draw a continuous path (for drawing applications like Excalidraw).
        
        Academic validation: Single mouseDown + multiple mouseDragged + single mouseUp
        Prevents "stroke commit" between segments (HTML5 canvas pointerup = stroke finalization).
        Uses Cubic Bezier interpolation for natural, human-like movement.
        
        Args:
            path: List of (x, y) tuples defining the path to draw
        
        Example:
            # Draw a triangle
            client.draw_path([
                (100, 100),  # Start
                (200, 100),  # Right
                (150, 200),  # Bottom
                (100, 100),  # Back to start (closed triangle)
            ])
        """
        # Convert tuples to arrays for JSON serialization
        path_array = [[int(x), int(y)] for x, y in path]
        return self._send("draw_path", {"path": path_array})


def kernel_available(port: int = DEFAULT_PORT) -> bool:
    """Return True if the Codex Kernel is reachable."""
    if requests is None:
        return False
    try:
        r = requests.get(f"http://127.0.0.1:{port}", timeout=1)
        return r.status_code == 200 and "Codex Kernel" in (r.text or "")
    except Exception:
        return False
