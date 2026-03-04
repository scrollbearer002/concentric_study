"""Geometry helpers for fitting stroke plans to a real canvas."""

from __future__ import annotations

from typing import Iterable

Point = tuple[float, float]
Stroke = list[Point]


def strokes_bbox(strokes: Iterable[Stroke]) -> tuple[float, float, float, float]:
    xs: list[float] = []
    ys: list[float] = []
    for stroke in strokes:
        for x, y in stroke:
            xs.append(float(x))
            ys.append(float(y))
    if not xs or not ys:
        raise ValueError("strokes_bbox() requires at least one point")
    return min(xs), min(ys), max(xs), max(ys)


def normalize_strokes_to_canvas(
    strokes: list[Stroke],
    canvas_w: float,
    canvas_h: float,
    *,
    margin_ratio_x: float = 0.08,
    margin_ratio_top: float = 0.08,
    margin_ratio_bottom: float = 0.08,
) -> list[Stroke]:
    """Scale and translate strokes so they fit within the canvas.

    The transformation preserves aspect ratio and centers the result inside the
    drawable region defined by the provided margins.
    """
    min_x, min_y, max_x, max_y = strokes_bbox(strokes)
    bbox_w = max_x - min_x
    bbox_h = max_y - min_y
    if bbox_w <= 0 or bbox_h <= 0:
        raise ValueError("stroke bounding box must have positive width and height")

    left_margin = canvas_w * margin_ratio_x
    right_margin = canvas_w * margin_ratio_x
    top_margin = canvas_h * margin_ratio_top
    bottom_margin = canvas_h * margin_ratio_bottom

    usable_w = canvas_w - left_margin - right_margin
    usable_h = canvas_h - top_margin - bottom_margin
    if usable_w <= 0 or usable_h <= 0:
        raise ValueError("canvas margins leave no drawable area")

    scale = min(usable_w / bbox_w, usable_h / bbox_h)
    scaled_w = bbox_w * scale
    scaled_h = bbox_h * scale

    target_min_x = left_margin + (usable_w - scaled_w) / 2.0
    target_min_y = top_margin + (usable_h - scaled_h) / 2.0

    normalized: list[Stroke] = []
    for stroke in strokes:
        normalized.append(
            [
                (
                    target_min_x + (x - min_x) * scale,
                    target_min_y + (y - min_y) * scale,
                )
                for x, y in stroke
            ]
        )
    return normalized
