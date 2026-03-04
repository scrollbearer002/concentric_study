"""Unit tests for ActionTrustTracker — adaptive verification skipping."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from agent_infra.action_trust import ActionTrustTracker


def _effective_threshold(reliability: float = 0.90, confidence: float = 0.90) -> int:
    """Find minimum consecutive successes needed to skip verification."""
    tracker = ActionTrustTracker(reliability=reliability, confidence=confidence)
    key = "__probe__"
    for i in range(1, 500):
        tracker.record_success(key)
        if not tracker.should_verify(key):
            return i
    raise RuntimeError("Could not determine effective threshold within 500 iterations")


EFFECTIVE_THRESHOLD = _effective_threshold()


class TestThresholdLogic:

    def test_initially_requires_verification(self):
        tracker = ActionTrustTracker()
        assert tracker.should_verify("click_ok") is True

    def test_below_threshold_requires_verification(self):
        tracker = ActionTrustTracker()
        for _ in range(EFFECTIVE_THRESHOLD - 1):
            tracker.record_success("click_ok")
        assert tracker.should_verify("click_ok") is True

    def test_at_threshold_skips_verification(self):
        tracker = ActionTrustTracker()
        for _ in range(EFFECTIVE_THRESHOLD):
            tracker.record_success("click_ok")
        assert tracker.should_verify("click_ok") is False

    def test_above_threshold_still_skips(self):
        tracker = ActionTrustTracker()
        for _ in range(EFFECTIVE_THRESHOLD + 3):
            tracker.record_success("click_ok")
        assert tracker.should_verify("click_ok") is False

    def test_failure_resets_trust(self):
        tracker = ActionTrustTracker()
        for _ in range(EFFECTIVE_THRESHOLD + 1):
            tracker.record_success("click_ok")
        assert tracker.should_verify("click_ok") is False
        tracker.record_failure("click_ok")
        assert tracker.should_verify("click_ok") is True
        assert tracker.consecutive_successes("click_ok") == 0

    def test_independent_keys(self):
        tracker = ActionTrustTracker()
        for _ in range(EFFECTIVE_THRESHOLD):
            tracker.record_success("action_a")
        assert tracker.should_verify("action_a") is False
        assert tracker.should_verify("action_b") is True

    def test_tuple_key_normalisation(self):
        tracker = ActionTrustTracker()
        key = ("set_stroke_color", "black")
        for _ in range(EFFECTIVE_THRESHOLD):
            tracker.record_success(key)
        assert tracker.should_verify(key) is False
        assert tracker.consecutive_successes(key) == EFFECTIVE_THRESHOLD


class TestPersistence:

    def test_persist_and_reload(self, tmp_path: Path):
        path = tmp_path / "trust.json"
        t1 = ActionTrustTracker(persist_path=path)
        for _ in range(3):
            t1.record_success("action_x")

        t2 = ActionTrustTracker(persist_path=path)
        assert t2.consecutive_successes("action_x") == 3
        assert t2.should_verify("action_x") is True

    def test_persist_threshold_survives_reload(self, tmp_path: Path):
        path = tmp_path / "trust.json"
        t1 = ActionTrustTracker(persist_path=path)
        for _ in range(EFFECTIVE_THRESHOLD):
            t1.record_success("action_y")

        t2 = ActionTrustTracker(persist_path=path)
        assert t2.should_verify("action_y") is False

    def test_failure_persists(self, tmp_path: Path):
        path = tmp_path / "trust.json"
        t1 = ActionTrustTracker(persist_path=path)
        for _ in range(EFFECTIVE_THRESHOLD):
            t1.record_success("z")
        t1.record_failure("z")

        t2 = ActionTrustTracker(persist_path=path)
        assert t2.should_verify("z") is True
        assert t2.consecutive_successes("z") == 0

    def test_corrupt_file_gracefully_handled(self, tmp_path: Path):
        path = tmp_path / "trust.json"
        path.write_text("not valid json!!!", encoding="utf-8")
        tracker = ActionTrustTracker(persist_path=path)
        assert tracker.should_verify("anything") is True

    def test_no_persist_path_works(self):
        tracker = ActionTrustTracker()
        for _ in range(EFFECTIVE_THRESHOLD):
            tracker.record_success("a")
        assert tracker.should_verify("a") is False


class TestConsecutiveSuccesses:

    def test_returns_zero_for_unknown(self):
        tracker = ActionTrustTracker()
        assert tracker.consecutive_successes("unknown") == 0

    def test_tracks_count_accurately(self):
        tracker = ActionTrustTracker()
        tracker.record_success("x")
        tracker.record_success("x")
        assert tracker.consecutive_successes("x") == 2
        tracker.record_failure("x")
        assert tracker.consecutive_successes("x") == 0
        tracker.record_success("x")
        assert tracker.consecutive_successes("x") == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
