"""Unified Element Map: fuses SoM visual grounding with accessibility tree data.

Merges the discrete SoM grid zones from VisualGroundingEngine with the
structured a11y tree from A11yEngine into a single queryable data structure.
For standard HTML sites, a11y provides semantic labels; for opaque <canvas>
apps, SoM + VLM provides visual grounding.

Research basis:
- Mind2Web (Deng et al., NeurIPS 2023): Hybrid perception outperforms
  either modality alone by 27-35%
- Agent S (2025): Fusing OCR bounding boxes into the a11y tree
- OmniParser (Microsoft, arXiv:2408.00203): Adaptive element parsing
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from a11y_engine import A11yElement


@dataclass
class UnifiedElement:
    """An element in the merged map with both visual and semantic info."""
    element_id: int
    visual_zone: int | None = None
    a11y_label: str = ""
    a11y_role: str = ""
    element_type: str = "unknown"
    coordinates: tuple[int, int] | None = None
    size: tuple[int, int] | None = None
    is_interactive: bool = False
    source: str = "unknown"
    confidence: float = 0.0
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "id": self.element_id,
            "type": self.element_type,
            "label": self.a11y_label,
            "role": self.a11y_role,
            "interactive": self.is_interactive,
            "source": self.source,
        }
        if self.coordinates:
            d["x"], d["y"] = self.coordinates
        if self.visual_zone is not None:
            d["zone"] = self.visual_zone
        return d


_ROLE_TO_TYPE = {
    "AXButton": "button", "button": "button",
    "AXLink": "link", "link": "link",
    "AXTextField": "input", "textfield": "input",
    "AXTextArea": "textarea", "textarea": "textarea",
    "AXCheckBox": "checkbox", "checkbox": "checkbox",
    "AXPopUpButton": "dropdown", "popupbutton": "dropdown",
    "AXMenuItem": "menuitem", "menuitem": "menuitem",
    "AXTab": "tab", "tab": "tab",
    "AXSlider": "slider", "slider": "slider",
    "AXImage": "image", "image": "image",
    "AXStaticText": "text", "statictext": "text",
    "AXGroup": "group", "group": "group",
    "AXWebArea": "webarea", "webarea": "webarea",
}


class UnifiedElementMap:
    """Merges SoM zones and a11y elements into a unified queryable map."""

    def __init__(self) -> None:
        self._elements: list[UnifiedElement] = []
        self._next_id = 0

    @property
    def elements(self) -> list[UnifiedElement]:
        return list(self._elements)

    def ingest_a11y(self, a11y_elements: list[A11yElement]) -> None:
        """Add accessibility tree elements to the map."""
        for elem in a11y_elements:
            self._elements.append(UnifiedElement(
                element_id=self._next_id,
                a11y_label=elem.label,
                a11y_role=elem.role,
                element_type=_ROLE_TO_TYPE.get(elem.role, "unknown"),
                coordinates=elem.center,
                size=elem.size,
                is_interactive=elem.is_interactive,
                source="a11y",
                confidence=0.9 if elem.center else 0.5,
            ))
            self._next_id += 1

    def ingest_som(self, coords_map: dict[int, tuple[int, int]]) -> None:
        """Add SoM grid zones as visual elements."""
        for zone_id, (x, y) in coords_map.items():
            self._elements.append(UnifiedElement(
                element_id=self._next_id,
                visual_zone=zone_id,
                element_type="visual_zone",
                coordinates=(x, y),
                source="som",
                confidence=0.6,
            ))
            self._next_id += 1

    def ingest_vlm_results(self, vlm_elements: list[dict[str, Any]]) -> None:
        """Add VLM-identified elements from parallel scout dispatch."""
        for item in vlm_elements:
            self._elements.append(UnifiedElement(
                element_id=self._next_id,
                a11y_label=item.get("label", ""),
                element_type=item.get("type", "unknown"),
                coordinates=tuple(item["coords"]) if "coords" in item else None,
                is_interactive=item.get("interactive", False),
                source="vlm",
                confidence=item.get("confidence", 0.7),
                extra=item,
            ))
            self._next_id += 1

    def merge_a11y_and_som(self, proximity_threshold: int = 30) -> None:
        """Fuse overlapping a11y and SoM elements within pixel proximity.

        When an a11y element and a SoM zone are within the threshold,
        merge them into a single high-confidence element with both
        semantic label and visual zone.
        """
        a11y_elems = [e for e in self._elements if e.source == "a11y" and e.coordinates]
        som_elems = [e for e in self._elements if e.source == "som" and e.coordinates]
        merged_som_ids: set[int] = set()

        for a_elem in a11y_elems:
            ax, ay = a_elem.coordinates
            best_som = None
            best_dist = float("inf")
            for s_elem in som_elems:
                if s_elem.element_id in merged_som_ids:
                    continue
                sx, sy = s_elem.coordinates
                dist = abs(ax - sx) + abs(ay - sy)
                if dist < best_dist:
                    best_dist = dist
                    best_som = s_elem
            if best_som and best_dist <= proximity_threshold:
                a_elem.visual_zone = best_som.visual_zone
                a_elem.confidence = min(1.0, a_elem.confidence + 0.2)
                a_elem.source = "fused"
                merged_som_ids.add(best_som.element_id)

        self._elements = [
            e for e in self._elements
            if e.element_id not in merged_som_ids
        ]

    def find_by_label(self, label: str) -> list[UnifiedElement]:
        """Find elements whose label contains the query string."""
        label_lower = label.lower()
        return [
            e for e in self._elements
            if label_lower in e.a11y_label.lower()
        ]

    def find_by_type(self, element_type: str) -> list[UnifiedElement]:
        return [e for e in self._elements if e.element_type == element_type]

    def find_interactive(self) -> list[UnifiedElement]:
        return [e for e in self._elements if e.is_interactive and e.coordinates]

    def find_nearest(self, x: int, y: int, max_distance: int = 100) -> UnifiedElement | None:
        """Find the closest interactive element to the given coordinates."""
        best = None
        best_dist = float("inf")
        for e in self._elements:
            if not e.coordinates:
                continue
            ex, ey = e.coordinates
            dist = abs(x - ex) + abs(y - ey)
            if dist < best_dist and dist <= max_distance:
                best_dist = dist
                best = e
        return best

    def to_text_description(self, max_items: int = 50) -> str:
        """Produce a compact text description for VLM context injection."""
        interactive = self.find_interactive()
        items = interactive[:max_items] if len(interactive) > max_items else interactive
        if not items:
            all_with_labels = [e for e in self._elements if e.a11y_label]
            items = all_with_labels[:max_items]
        lines = []
        for e in items:
            coords = f"({e.coordinates[0]},{e.coordinates[1]})" if e.coordinates else "(?)"
            lines.append(f"[{e.element_type}] {e.a11y_label or '(unnamed)'} at {coords}")
        return "\n".join(lines)

    def to_dict_list(self) -> list[dict[str, Any]]:
        return [e.to_dict() for e in self._elements]
