"""Site-agnostic web navigation primitives.

Provides a high-level abstraction over Quartz HID events, allowing
actions to be expressed in terms of semantic labels rather than raw
coordinates.  Each primitive queries the UnifiedElementMap to resolve
labels to screen coordinates, then fires native Quartz events.

Research basis:
- CogAgent (Hong et al., CVPR 2024): Abstracted action spaces are key
  to cross-site transfer
- GUI-Actor (arXiv 2025): Coordinate-free VLM grounding via attention
  heads cuts inference time by 30-50%
- EmbeWebAgent (2026): Mixed-granularity actions enable reliable
  cross-domain navigation
- Web Verbs (2025): Typed semantic functions expose site capabilities
  through uniform interfaces
"""

from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass, field
from typing import Any

from element_map import UnifiedElementMap, UnifiedElement


@dataclass
class PrimitiveResult:
    """Outcome of a web primitive execution."""
    success: bool
    action: str
    label: str
    element: dict[str, Any] | None = None
    error: str = ""
    duration_ms: int = 0

    def to_dict(self) -> dict[str, Any]:
        d = {"success": self.success, "action": self.action, "label": self.label}
        if self.element:
            d["element"] = self.element
        if self.error:
            d["error"] = self.error
        d["duration_ms"] = self.duration_ms
        return d


@dataclass
class SiteProfile:
    """Cached knowledge about a website's interactive structure."""
    domain: str
    url: str
    elements: list[dict[str, Any]] = field(default_factory=list)
    timestamp: str = ""
    visit_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "domain": self.domain,
            "url": self.url,
            "element_count": len(self.elements),
            "timestamp": self.timestamp,
            "visit_count": self.visit_count,
        }


class WebPrimitives:
    """High-level, site-agnostic web interaction primitives.

    All primitives resolve labels to coordinates via the UnifiedElementMap,
    then delegate to an agent's Quartz event methods.
    """

    def __init__(self, agent: Any, element_map: UnifiedElementMap) -> None:
        self._agent = agent
        self._map = element_map
        self._site_profiles: dict[str, SiteProfile] = {}

    @property
    def element_map(self) -> UnifiedElementMap:
        return self._map

    def update_map(self, new_map: UnifiedElementMap) -> None:
        self._map = new_map

    def _resolve(self, label: str) -> UnifiedElement | None:
        matches = self._map.find_by_label(label)
        interactive = [m for m in matches if m.is_interactive and m.coordinates]
        if interactive:
            return interactive[0]
        with_coords = [m for m in matches if m.coordinates]
        return with_coords[0] if with_coords else None

    def click_element(self, label: str) -> PrimitiveResult:
        """Click the element whose label matches the query."""
        t0 = time.time()
        elem = self._resolve(label)
        if not elem or not elem.coordinates:
            return PrimitiveResult(
                success=False, action="click", label=label,
                error=f"Element '{label}' not found or has no coordinates",
                duration_ms=int((time.time() - t0) * 1000),
            )
        x, y = elem.coordinates
        try:
            self._agent.execute_global_click(x, y)
            return PrimitiveResult(
                success=True, action="click", label=label,
                element=elem.to_dict(),
                duration_ms=int((time.time() - t0) * 1000),
            )
        except Exception as e:
            return PrimitiveResult(
                success=False, action="click", label=label,
                element=elem.to_dict(), error=str(e),
                duration_ms=int((time.time() - t0) * 1000),
            )

    def type_into(self, label: str, text: str) -> PrimitiveResult:
        """Click a text field by label, then type text into it."""
        t0 = time.time()
        click_result = self.click_element(label)
        if not click_result.success:
            return PrimitiveResult(
                success=False, action="type", label=label,
                error=f"Could not click '{label}': {click_result.error}",
                duration_ms=int((time.time() - t0) * 1000),
            )
        time.sleep(0.3)
        try:
            for char in text:
                self._agent.execute_keystroke(char)
                time.sleep(0.05)
            return PrimitiveResult(
                success=True, action="type", label=label,
                element=click_result.element,
                duration_ms=int((time.time() - t0) * 1000),
            )
        except Exception as e:
            return PrimitiveResult(
                success=False, action="type", label=label,
                error=str(e),
                duration_ms=int((time.time() - t0) * 1000),
            )

    def scroll_to(self, label: str) -> PrimitiveResult:
        """Scroll until the element with the given label is visible."""
        t0 = time.time()
        elem = self._resolve(label)
        if elem and elem.coordinates:
            return PrimitiveResult(
                success=True, action="scroll", label=label,
                element=elem.to_dict(),
                duration_ms=int((time.time() - t0) * 1000),
            )
        for _ in range(10):
            try:
                self._agent.execute_keystroke("space")
                time.sleep(0.5)
            except Exception:
                pass
            elem = self._resolve(label)
            if elem and elem.coordinates:
                return PrimitiveResult(
                    success=True, action="scroll", label=label,
                    element=elem.to_dict(),
                    duration_ms=int((time.time() - t0) * 1000),
                )
        return PrimitiveResult(
            success=False, action="scroll", label=label,
            error=f"Could not find '{label}' after scrolling",
            duration_ms=int((time.time() - t0) * 1000),
        )

    def read_text(self, label: str) -> PrimitiveResult:
        """Read the text content of an element by label."""
        t0 = time.time()
        elem = self._resolve(label)
        if not elem:
            return PrimitiveResult(
                success=False, action="read", label=label,
                error=f"Element '{label}' not found",
                duration_ms=int((time.time() - t0) * 1000),
            )
        value = elem.extra.get("text", elem.a11y_label)
        return PrimitiveResult(
            success=True, action="read", label=label,
            element={**elem.to_dict(), "text": value},
            duration_ms=int((time.time() - t0) * 1000),
        )

    def wait_for(self, label: str, timeout_s: float = 10.0) -> PrimitiveResult:
        """Wait until an element with the given label appears."""
        t0 = time.time()
        while (time.time() - t0) < timeout_s:
            elem = self._resolve(label)
            if elem and elem.coordinates:
                return PrimitiveResult(
                    success=True, action="wait", label=label,
                    element=elem.to_dict(),
                    duration_ms=int((time.time() - t0) * 1000),
                )
            time.sleep(0.5)
        return PrimitiveResult(
            success=False, action="wait", label=label,
            error=f"Timed out waiting for '{label}'",
            duration_ms=int((time.time() - t0) * 1000),
        )

    def cache_site_profile(self, domain: str, url: str) -> SiteProfile:
        """Cache the current element map as a site profile for reuse."""
        profile = SiteProfile(
            domain=domain, url=url,
            elements=self._map.to_dict_list(),
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            visit_count=1,
        )
        existing = self._site_profiles.get(domain)
        if existing:
            profile.visit_count = existing.visit_count + 1
        self._site_profiles[domain] = profile
        return profile

    def get_site_profile(self, domain: str) -> SiteProfile | None:
        return self._site_profiles.get(domain)

    def list_site_profiles(self) -> list[str]:
        return list(self._site_profiles.keys())
