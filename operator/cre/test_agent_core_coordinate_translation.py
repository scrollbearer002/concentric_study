from __future__ import annotations

import pytest

# macOS-only: agent_core imports the native Quartz/AppKit stack at import time.
pytest.importorskip("Quartz", reason="macOS-only GUI automation (requires pyobjc/Quartz)")

from agent_core import pixel_to_global_from_capture


def test_pixel_to_global_from_fullscreen_capture():
    gx, gy = pixel_to_global_from_capture(
        400.0,
        300.0,
        scale_factor=2.0,
        screen_origin=(0.0, 0.0),
    )

    assert gx == 200.0
    assert gy == 150.0


def test_pixel_to_global_from_window_capture_applies_origin_offset():
    gx, gy = pixel_to_global_from_capture(
        400.0,
        300.0,
        scale_factor=2.0,
        screen_origin=(0.0, 0.0),
        capture_origin=(160.0, 96.0),
    )

    assert gx == 360.0
    assert gy == 246.0
