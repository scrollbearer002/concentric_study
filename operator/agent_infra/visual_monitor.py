"""Lightweight periodic visual monitoring for GUI agent execution.

Provides continuous visual state awareness via background screenshots,
enabling the agent to always know what the screen looks like and to
compare current state against reference images.

Architecture grounded in:
- Peekaboo MCP (Steinberger, 2025): zero-focus-change macOS screenshots
  for AI agents, but implemented natively to avoid Node.js dependency.
- ScreenAgent (IJCAI 2024): plan-action-reflection cycle with real
  screenshot observation at each step.
- MIRA (arXiv:2511.21087): perception-reasoning-action loop driven by
  visual feedback — the monitor provides the perception channel.
- VisionDirector (arXiv:2512.19243): closed-loop refinement with
  semantic verification after each edit step.

Design principles:
- ZERO imports from agent_infra (preserves unidirectional dependency chain)
- Background daemon thread (auto-dies with main process)
- Ring buffer prevents unbounded disk/memory usage
- Uses macOS native screencapture -x (~100ms, silent, no focus steal)
- Optional pixel-diff comparison via PIL (lightweight, no ML model)
"""

from __future__ import annotations

import json
import logging
import subprocess
import threading
import time
from collections import deque
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

from screenshot_preprocessor import inspect_image_artifact, load_normalized_image
from window_capture import capture_front_window

logger = logging.getLogger(__name__)


@dataclass
class Snapshot:
    """One captured screenshot with metadata."""
    path: str
    timestamp: float
    iso_time: str
    index: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ComparisonResult:
    """Result of comparing current state against a reference image."""
    reference_path: str
    current_path: str
    similarity_score: float
    diff_image_path: str | None = None
    changed_pixel_ratio: float = 0.0
    assessment: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class VisualMonitor:
    """Background screenshot service with ring buffer and comparison.

    Usage::

        monitor = VisualMonitor(interval_seconds=5, output_dir="/tmp/monitor")
        monitor.start()

        # ... agent executes task ...

        # Check current state
        latest = monitor.latest()

        # Compare against reference
        result = monitor.compare("reference_hands.png")
        if result.similarity_score < 0.8:
            print("Not matching reference yet, keep refining")

        # Review recent history
        timeline = monitor.timeline(last_n=10)

        monitor.stop()
    """

    def __init__(
        self,
        interval_seconds: float = 5.0,
        buffer_size: int = 50,
        output_dir: str | Path | None = None,
        capture_frontmost_window: bool = False,
    ) -> None:
        self._interval = max(0.5, interval_seconds)
        self._buffer_size = buffer_size
        self._output_dir = Path(output_dir) if output_dir else Path("/tmp/visual_monitor")
        self._output_dir.mkdir(parents=True, exist_ok=True)
        self._capture_frontmost_window = capture_frontmost_window

        self._buffer: deque[Snapshot] = deque(maxlen=buffer_size)
        self._index = 0
        self._running = False
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def snapshot_count(self) -> int:
        return len(self._buffer)

    def start(self) -> None:
        """Launch background daemon thread for periodic screenshots."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()
        logger.info(
            "VisualMonitor started: interval=%.1fs, buffer=%d, dir=%s",
            self._interval, self._buffer_size, self._output_dir,
        )

    def stop(self) -> None:
        """Stop the background thread and take one final snapshot."""
        if not self._running:
            return
        self._running = False
        if self._thread:
            self._thread.join(timeout=self._interval + 2)
        self._capture_once()
        logger.info("VisualMonitor stopped after %d captures", self._index)

    def capture_now(self) -> Snapshot | None:
        """Force an immediate capture outside the regular interval."""
        return self._capture_once()

    def latest(self) -> Snapshot | None:
        """Return the most recent snapshot."""
        with self._lock:
            return self._buffer[-1] if self._buffer else None

    def timeline(self, last_n: int = 10) -> list[Snapshot]:
        """Return the last N snapshots in chronological order."""
        with self._lock:
            items = list(self._buffer)
        return items[-last_n:]

    def compare(self, reference_path: str, current_path: str | None = None) -> ComparisonResult:
        """Compare current screen (or a specific screenshot) against a reference.

        Uses pixel-level comparison via PIL. Does NOT require a VLM —
        this is a fast, deterministic check suitable for calling after
        every drawing step.

        Returns a ComparisonResult with similarity_score in [0.0, 1.0]
        where 1.0 means identical.
        """
        if current_path is None:
            snap = self.latest()
            if snap is None:
                snap = self.capture_now()
            if snap is None:
                return ComparisonResult(
                    reference_path=reference_path,
                    current_path="",
                    similarity_score=0.0,
                    assessment="No screenshot available",
                )
            current_path = snap.path

        return self._pixel_compare(reference_path, current_path)

    def get_status(self) -> dict[str, Any]:
        """Return monitor status for logging/tracing."""
        latest = self.latest()
        return {
            "running": self._running,
            "total_captures": self._index,
            "buffer_size": len(self._buffer),
            "interval_seconds": self._interval,
            "capture_frontmost_window": self._capture_frontmost_window,
            "latest_path": latest.path if latest else None,
            "latest_time": latest.iso_time if latest else None,
        }

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _capture_loop(self) -> None:
        """Background loop: capture screenshots at regular intervals."""
        while self._running:
            self._capture_once()
            time.sleep(self._interval)

    def _capture_once(self) -> Snapshot | None:
        """Take a single screenshot using macOS screencapture."""
        ts = time.time()
        iso = time.strftime("%Y%m%d_%H%M%S", time.localtime(ts))
        filename = f"snap_{iso}_{self._index:04d}.png"
        path = self._output_dir / filename

        try:
            if self._capture_frontmost_window:
                capture_front_window(path, timeout_seconds=5)
            else:
                result = subprocess.run(
                    ["screencapture", "-x", str(path)],
                    timeout=5,
                    capture_output=True,
                )
                if result.returncode != 0 or not path.exists():
                    return None
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return None
        except Exception:
            return None

        snap = Snapshot(
            path=str(path),
            timestamp=ts,
            iso_time=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts)),
            index=self._index,
        )

        with self._lock:
            if len(self._buffer) >= self._buffer_size:
                oldest = self._buffer[0]
                try:
                    Path(oldest.path).unlink(missing_ok=True)
                except OSError:
                    pass
            self._buffer.append(snap)
            self._index += 1

        return snap

    @staticmethod
    def _pixel_compare(ref_path: str, cur_path: str) -> ComparisonResult:
        """Fast pixel-level image comparison using PIL."""
        try:
            import numpy as np

            ref_info = inspect_image_artifact(ref_path)
            if not ref_info.is_valid:
                return ComparisonResult(
                    reference_path=ref_path,
                    current_path=cur_path,
                    similarity_score=-1.0,
                    assessment=f"Invalid reference image: {ref_info.error}",
                )

            cur_info = inspect_image_artifact(cur_path)
            if not cur_info.is_valid:
                return ComparisonResult(
                    reference_path=ref_path,
                    current_path=cur_path,
                    similarity_score=-1.0,
                    assessment=f"Invalid current image: {cur_info.error}",
                )

            ref_img = load_normalized_image(ref_path)
            cur_img = load_normalized_image(cur_path)
            ref = np.array(ref_img)
            cur = np.array(cur_img)

            if ref.shape != cur.shape:
                cur_img = cur_img.resize(
                    (ref.shape[1], ref.shape[0]), Image.LANCZOS
                )
                cur = np.array(cur_img)

            diff = np.abs(ref.astype(float) - cur.astype(float))
            max_diff = 255.0 * 3
            pixel_diffs = diff.sum(axis=2) / max_diff
            similarity = 1.0 - float(pixel_diffs.mean())
            changed_ratio = float((pixel_diffs > 0.05).mean())

            diff_path = None
            try:
                from PIL import Image

                diff_img = Image.fromarray((pixel_diffs * 255).astype(np.uint8))
                diff_path = ref_path.replace(".png", "_diff.png")
                diff_img.save(diff_path)
            except Exception:
                pass

            if similarity > 0.95:
                assessment = "Excellent match — nearly identical to reference"
            elif similarity > 0.85:
                assessment = "Good match — minor differences from reference"
            elif similarity > 0.70:
                assessment = "Moderate match — visible differences, refinement needed"
            elif similarity > 0.50:
                assessment = "Partial match — significant gaps from reference"
            else:
                assessment = "Poor match — major revision needed"

            return ComparisonResult(
                reference_path=ref_path,
                current_path=cur_path,
                similarity_score=round(similarity, 4),
                diff_image_path=diff_path,
                changed_pixel_ratio=round(changed_ratio, 4),
                assessment=assessment,
            )

        except ImportError:
            return ComparisonResult(
                reference_path=ref_path,
                current_path=cur_path,
                similarity_score=-1.0,
                assessment="PIL/numpy not available for pixel comparison",
            )
        except Exception as e:
            return ComparisonResult(
                reference_path=ref_path,
                current_path=cur_path,
                similarity_score=-1.0,
                assessment=f"Comparison failed: {e}",
            )
