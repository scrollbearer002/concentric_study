"""Accessibility tree extraction engine for macOS applications.

Provides structured access to the accessibility hierarchy of running
applications via the macOS AXUIElement API.  Falls back gracefully when
accessibility packages are unavailable or when the target app uses
opaque rendering (e.g. HTML5 <canvas>).

Research basis:
- Mind2Web (Deng et al., NeurIPS 2023): Hybrid Vision+Accessibility
  agents outperform vision-only by 27-35%
- Agent S (2025): Fusing OCR bounding boxes into the a11y tree makes
  custom canvas controls visible
- macOSWorld (arXiv:2506.04135, 2025): macOS-specific GUI benchmark
  using a11y trees; agents exceed 30% success with hybrid perception
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from typing import Any


@dataclass
class A11yElement:
    """A single interactive element extracted from the accessibility tree."""
    role: str
    label: str
    value: str | None = None
    position: tuple[int, int] | None = None
    size: tuple[int, int] | None = None
    is_interactive: bool = False
    children_count: int = 0
    attributes: dict[str, Any] = field(default_factory=dict)

    @property
    def center(self) -> tuple[int, int] | None:
        if self.position and self.size:
            return (
                self.position[0] + self.size[0] // 2,
                self.position[1] + self.size[1] // 2,
            )
        return self.position

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "role": self.role,
            "label": self.label,
            "is_interactive": self.is_interactive,
        }
        if self.value is not None:
            d["value"] = self.value
        if self.position:
            d["position"] = list(self.position)
        if self.size:
            d["size"] = list(self.size)
        if self.center:
            d["center"] = list(self.center)
        return d


_INTERACTIVE_ROLES = {
    "AXButton", "AXLink", "AXTextField", "AXTextArea",
    "AXCheckBox", "AXRadioButton", "AXPopUpButton",
    "AXMenuButton", "AXSlider", "AXComboBox", "AXTab",
    "AXMenuItem", "AXIncrementor", "AXDisclosureTriangle",
    "button", "link", "textfield", "textarea", "checkbox",
    "radiobutton", "popupbutton", "menubutton", "slider",
    "combobox", "tab", "menuitem",
}


class A11yEngine:
    """Extracts structured accessibility trees from macOS applications.

    Attempts to use macapptree (MacPaw, 2026) first, then pyax as
    fallback, then falls back to AppleScript-based basic extraction.
    """

    def __init__(self) -> None:
        self._backend = self._detect_backend()

    @staticmethod
    def _detect_backend() -> str:
        try:
            import macapptree  # noqa: F401
            return "macapptree"
        except ImportError:
            pass
        try:
            import pyax  # noqa: F401
            return "pyax"
        except ImportError:
            pass
        return "applescript"

    @property
    def backend(self) -> str:
        return self._backend

    def extract(self, app_name: str = "Safari", max_depth: int = 6) -> list[A11yElement]:
        if self._backend == "macapptree":
            return self._extract_macapptree(app_name, max_depth)
        elif self._backend == "pyax":
            return self._extract_pyax(app_name, max_depth)
        return self._extract_applescript(app_name)

    def _extract_macapptree(self, app_name: str, max_depth: int) -> list[A11yElement]:
        try:
            import macapptree
            tree = macapptree.dump(app_name, max_depth=max_depth)
            return self._parse_tree_json(tree)
        except Exception:
            return self._extract_applescript(app_name)

    def _extract_pyax(self, app_name: str, max_depth: int) -> list[A11yElement]:
        try:
            import pyax
            app = pyax.get_application(app_name)
            tree = app.dump(max_depth=max_depth)
            return self._parse_tree_json(tree)
        except Exception:
            return self._extract_applescript(app_name)

    def _extract_applescript(self, app_name: str) -> list[A11yElement]:
        """Minimal a11y extraction via AppleScript for when no library is available."""
        script = f'''
tell application "System Events"
    tell process "{app_name}"
        set windowList to every window
        set results to {{}}
        repeat with w in windowList
            set winName to name of w
            set winPos to position of w
            set winSize to size of w
            try
                set uiElements to every UI element of w
                repeat with elem in uiElements
                    try
                        set elemRole to role of elem
                        set elemDesc to description of elem
                        set elemPos to position of elem
                        set elemSize to size of elem
                        set end of results to (elemRole & "|" & elemDesc & "|" & (item 1 of elemPos as text) & "," & (item 2 of elemPos as text) & "|" & (item 1 of elemSize as text) & "," & (item 2 of elemSize as text))
                    end try
                end repeat
            end try
        end repeat
        return results
    end tell
end tell
'''
        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True, text=True, timeout=10,
            )
            elements: list[A11yElement] = []
            for line in result.stdout.strip().split(", "):
                parts = line.strip().split("|")
                if len(parts) >= 4:
                    role = parts[0].strip()
                    label = parts[1].strip()
                    pos_parts = parts[2].split(",")
                    size_parts = parts[3].split(",")
                    try:
                        pos = (int(float(pos_parts[0])), int(float(pos_parts[1])))
                        size = (int(float(size_parts[0])), int(float(size_parts[1])))
                    except (ValueError, IndexError):
                        pos, size = None, None
                    elements.append(A11yElement(
                        role=role, label=label,
                        position=pos, size=size,
                        is_interactive=role in _INTERACTIVE_ROLES,
                    ))
            return elements
        except Exception:
            return []

    def _parse_tree_json(self, tree: Any) -> list[A11yElement]:
        """Parse a JSON tree structure from macapptree or pyax."""
        elements: list[A11yElement] = []
        if isinstance(tree, str):
            try:
                tree = json.loads(tree)
            except json.JSONDecodeError:
                return elements

        def _walk(node: dict[str, Any]) -> None:
            role = node.get("role", node.get("AXRole", ""))
            label = node.get("label", node.get("AXDescription", node.get("AXTitle", "")))
            value = node.get("value", node.get("AXValue"))
            pos = node.get("position", node.get("AXPosition"))
            size = node.get("size", node.get("AXSize"))
            pos_tuple = tuple(pos) if isinstance(pos, (list, tuple)) and len(pos) == 2 else None
            size_tuple = tuple(size) if isinstance(size, (list, tuple)) and len(size) == 2 else None
            children = node.get("children", node.get("AXChildren", []))

            elements.append(A11yElement(
                role=str(role),
                label=str(label or ""),
                value=str(value) if value is not None else None,
                position=pos_tuple,
                size=size_tuple,
                is_interactive=str(role) in _INTERACTIVE_ROLES,
                children_count=len(children) if isinstance(children, list) else 0,
            ))
            if isinstance(children, list):
                for child in children:
                    if isinstance(child, dict):
                        _walk(child)

        if isinstance(tree, dict):
            _walk(tree)
        elif isinstance(tree, list):
            for item in tree:
                if isinstance(item, dict):
                    _walk(item)
        return elements

    def extract_interactive(self, app_name: str = "Safari") -> list[A11yElement]:
        """Convenience: return only interactive elements with coordinates."""
        return [
            e for e in self.extract(app_name)
            if e.is_interactive and e.center is not None
        ]
