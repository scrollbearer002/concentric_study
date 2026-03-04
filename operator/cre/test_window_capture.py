from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import window_capture
from agent_infra.visual_monitor import VisualMonitor


def test_capture_front_window_prefers_window_capture(monkeypatch, tmp_path: Path):
    out = tmp_path / "window.png"

    monkeypatch.setattr(
        window_capture,
        "get_front_window_info",
        lambda owner_name=None: {
            "owner_name": "Safari",
            "window_id": 123,
            "bounds": {"x": 0, "y": 22, "width": 1440, "height": 900},
        },
    )

    calls = []

    def fake_run(cmd, timeout=None, capture_output=None):
        calls.append(cmd)
        out.write_bytes(b"png")
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(window_capture.subprocess, "run", fake_run)

    result = window_capture.capture_front_window(out)

    assert result["mode"] == "window"
    assert result["window_id"] == 123
    assert calls[0][:5] == ["screencapture", "-x", "-o", "-l", "123"]


def test_capture_front_window_can_include_cursor(monkeypatch, tmp_path: Path):
    out = tmp_path / "window_cursor.png"

    monkeypatch.setattr(
        window_capture,
        "get_front_window_info",
        lambda owner_name=None: {
            "owner_name": "Safari",
            "window_id": 456,
            "bounds": {"x": 0, "y": 22, "width": 1440, "height": 900},
        },
    )

    calls = []

    def fake_run(cmd, timeout=None, capture_output=None):
        calls.append(cmd)
        out.write_bytes(b"png")
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(window_capture.subprocess, "run", fake_run)

    result = window_capture.capture_front_window(out, include_cursor=True)

    assert result["mode"] == "window"
    assert calls[0] == ["screencapture", "-x", "-o", "-C", "-l", "456", str(out)]


def test_capture_front_window_falls_back_to_display(monkeypatch, tmp_path: Path):
    out = tmp_path / "display.png"
    monkeypatch.setattr(window_capture, "get_front_window_info", lambda owner_name=None: None)
    monkeypatch.setattr(window_capture, "get_frontmost_application_name", lambda: "Safari")

    calls = []

    def fake_run(cmd, timeout=None, capture_output=None):
        calls.append(cmd)
        out.write_bytes(b"png")
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(window_capture.subprocess, "run", fake_run)

    result = window_capture.capture_front_window(out)

    assert result["mode"] == "display"
    assert calls[0] == ["screencapture", "-x", str(out)]


def test_capture_front_window_fallback_can_include_cursor(monkeypatch, tmp_path: Path):
    out = tmp_path / "display_cursor.png"
    monkeypatch.setattr(window_capture, "get_front_window_info", lambda owner_name=None: None)
    monkeypatch.setattr(window_capture, "get_frontmost_application_name", lambda: "Safari")

    calls = []

    def fake_run(cmd, timeout=None, capture_output=None):
        calls.append(cmd)
        out.write_bytes(b"png")
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(window_capture.subprocess, "run", fake_run)

    result = window_capture.capture_front_window(out, include_cursor=True)

    assert result["mode"] == "display"
    assert calls[0] == ["screencapture", "-x", "-C", str(out)]


def test_visual_monitor_uses_window_capture_when_enabled(monkeypatch, tmp_path: Path):
    calls = []

    def fake_capture(path, **kwargs):
        calls.append((str(path), kwargs))
        Path(path).write_bytes(b"png")
        return {"mode": "window", "path": str(path)}

    monkeypatch.setattr("agent_infra.visual_monitor.capture_front_window", fake_capture)

    monitor = VisualMonitor(
        interval_seconds=5,
        buffer_size=5,
        output_dir=tmp_path / "monitor",
        capture_frontmost_window=True,
    )

    snap = monitor.capture_now()

    assert snap is not None
    assert len(calls) == 1
    assert monitor.get_status()["capture_frontmost_window"] is True
