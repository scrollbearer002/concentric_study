from __future__ import annotations

import math

from art_geometry import normalize_strokes_to_canvas, strokes_bbox


def test_normalize_strokes_to_canvas_fits_within_margins() -> None:
    strokes = [
        [(185.5, 53.52), (497.5, 683.52)],
        [(250.0, 100.0), (430.0, 620.0)],
    ]
    normalized = normalize_strokes_to_canvas(
        strokes,
        683.0,
        384.0,
        margin_ratio_x=0.10,
        margin_ratio_top=0.08,
        margin_ratio_bottom=0.06,
    )
    min_x, min_y, max_x, max_y = strokes_bbox(normalized)
    assert min_x >= 683.0 * 0.10 - 1e-6
    assert max_x <= 683.0 * 0.90 + 1e-6
    assert min_y >= 384.0 * 0.08 - 1e-6
    assert max_y <= 384.0 * 0.94 + 1e-6


def test_normalize_strokes_to_canvas_preserves_aspect_ratio() -> None:
    strokes = [[(0.0, 0.0), (100.0, 200.0)]]
    normalized = normalize_strokes_to_canvas(strokes, 500.0, 300.0)
    orig_min_x, orig_min_y, orig_max_x, orig_max_y = strokes_bbox(strokes)
    new_min_x, new_min_y, new_max_x, new_max_y = strokes_bbox(normalized)

    orig_ratio = (orig_max_x - orig_min_x) / (orig_max_y - orig_min_y)
    new_ratio = (new_max_x - new_min_x) / (new_max_y - new_min_y)
    assert math.isclose(orig_ratio, new_ratio, rel_tol=1e-9)
