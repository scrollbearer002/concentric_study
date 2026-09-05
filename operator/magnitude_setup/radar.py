"""Unicode radar (spider) chart for terminal detail panes."""

from __future__ import annotations

import math
from typing import Sequence


AXES = ("INTELLIGENCE", "SPEED", "SPECULATION", "MEMORY", "ACCURACY")


def _clamp01(v: float) -> float:
    return max(0.0, min(1.0, v))


def render_radar(
    values: Sequence[float],
    *,
    width: int = 28,
    height: int = 13,
    labels: Sequence[str] | None = None,
    fill_char: str = "·",
    edge_char: str = "◈",
    axis_char: str = "·",
) -> str:
    """Render a pentagon radar chart into a character grid.

    ``values`` are expected in 0..10 (one per axis). Returns a multiline string.
    """
    labels = list(labels or AXES)
    if len(values) != 5:
        raise ValueError("radar chart requires exactly 5 values")

    norms = [_clamp01(v / 10.0) for v in values]
    cx = (width - 1) / 2.0
    cy = (height - 1) / 2.0
    radius = min(cx, cy) - 1.2

    grid = [[" " for _ in range(width)] for _ in range(height)]

    def to_xy(axis_i: int, scale: float) -> tuple[float, float]:
        # Start at top, go clockwise.
        angle = -math.pi / 2 + axis_i * (2 * math.pi / 5)
        x = cx + math.cos(angle) * radius * scale
        y = cy + math.sin(angle) * radius * scale * 0.85  # slight vertical squash
        return x, y

    def plot(x: float, y: float, ch: str) -> None:
        ix, iy = int(round(x)), int(round(y))
        if 0 <= iy < height and 0 <= ix < width:
            grid[iy][ix] = ch

    def draw_line(x0: float, y0: float, x1: float, y1: float, ch: str) -> None:
        steps = int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 1
        for i in range(steps + 1):
            t = i / steps
            plot(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, ch)

    # Outer + mid rings
    for ring in (1.0, 0.6, 0.3):
        pts = [to_xy(i, ring) for i in range(5)]
        for i in range(5):
            draw_line(*pts[i], *pts[(i + 1) % 5], axis_char)

    # Axes from center
    for i in range(5):
        draw_line(cx, cy, *to_xy(i, 1.0), axis_char)

    # Value polygon
    vpts = [to_xy(i, norms[i]) for i in range(5)]
    for i in range(5):
        draw_line(*vpts[i], *vpts[(i + 1) % 5], edge_char)
        plot(*vpts[i], "●")

    # Soft fill toward center (sparse)
    for i in range(5):
        x0, y0 = vpts[i]
        for t in (0.35, 0.65):
            plot(cx + (x0 - cx) * t, cy + (y0 - cy) * t, fill_char)

    # Place abbreviated labels near vertices
    abbrev = {
        "INTELLIGENCE": "INT",
        "SPEED": "SPD",
        "SPECULATION": "SPC",
        "MEMORY": "MEM",
        "ACCURACY": "ACC",
    }
    for i, label in enumerate(labels):
        x, y = to_xy(i, 1.18)
        text = abbrev.get(label, label[:3])
        ix = int(round(x)) - len(text) // 2
        iy = int(round(y))
        for j, ch in enumerate(text):
            px = ix + j
            if 0 <= iy < height and 0 <= px < width:
                grid[iy][px] = ch

    return "\n".join("".join(row) for row in grid)


def metric_lines(ranked) -> list[str]:
    """Human-readable metric captions matching the screenshot detail pane."""
    low, high = ranked.speed_tok_s
    return [
        f"INTELLIGENCE  {ranked.intelligence_pct}%",
        f"SPEED         ~{low:g}-{high:g} tok/s",
        f"SPECULATION   {ranked.speculation_label}",
        f"MEMORY        {ranked.memory_label}",
        f"ACCURACY      {ranked.accuracy_label}",
    ]
