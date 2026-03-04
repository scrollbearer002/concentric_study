"""Dry-run unit test for InferenceRouter wiring.

Tests the router logic in isolation — no API keys, no Quartz, no screenshots.
Validates that:
1. Router instantiates correctly
2. Known task types route to expected models
3. Unknown task types fall back to Pro
4. Stats are tracked accurately
5. _model_for() helper works with and without a router
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from inference_router import InferenceRouter, ModelTier


def test_router_instantiation():
    router = InferenceRouter()
    assert router is not None
    assert router.stats.total_queries == 0
    print("  [PASS] Router instantiates correctly")


def test_known_routes():
    router = InferenceRouter()

    assert router.get_model_for("assert_visual_state") == "gemini-2.0-flash"
    assert router.get_model_for("confirm_click_target") == "gemini-2.0-flash"
    assert router.get_model_for("readiness_poll") == "gemini-2.0-flash"
    assert router.get_model_for("extract_target") == "gemini-2.5-pro"
    assert router.get_model_for("analyze_ui") == "gemini-2.5-pro"
    assert router.get_model_for("diagnose_failure") == "gemini-2.5-pro"
    assert router.get_model_for("detect_colored_dots") == "gemini-2.5-pro"
    print("  [PASS] Known task types route to correct models")


def test_unknown_fallback():
    router = InferenceRouter()
    model = router.get_model_for("totally_unknown_task")
    assert model == "gemini-2.5-pro", f"Expected Pro fallback, got {model}"
    print("  [PASS] Unknown tasks fall back to Pro")


def test_stats_tracking():
    router = InferenceRouter()

    router.get_model_for("assert_visual_state")  # Flash
    router.get_model_for("assert_visual_state")  # Flash
    router.get_model_for("extract_target")        # Pro
    router.get_model_for("analyze_ui")            # Pro
    router.get_model_for("unknown_thing")         # Pro (fallback)

    stats = router.stats
    assert stats.total_queries == 5, f"Expected 5 queries, got {stats.total_queries}"
    assert stats.flash_count == 2, f"Expected 2 Flash, got {stats.flash_count}"
    assert stats.pro_count == 3, f"Expected 3 Pro, got {stats.pro_count}"
    assert stats.local_count == 0, f"Expected 0 Local, got {stats.local_count}"
    assert 0.3 < stats.estimated_cost_savings < 0.5, f"Savings outside expected range: {stats.estimated_cost_savings}"
    print(f"  [PASS] Stats tracked: {stats.to_dict()}")


def test_model_for_helper():
    """Test _model_for pattern used in agent_core.py (without importing MacOSAgentCore)."""
    router = InferenceRouter()

    def _model_for(task_type, default):
        if router:
            return router.get_model_for(task_type)
        return default

    assert _model_for("extract_target", "gemini-2.5-pro") == "gemini-2.5-pro"
    assert _model_for("assert_visual_state", "gemini-2.0-flash") == "gemini-2.0-flash"

    def _model_for_no_router(task_type, default):
        router_none = None
        if router_none:
            return router_none.get_model_for(task_type)
        return default

    assert _model_for_no_router("extract_target", "gemini-2.5-pro") == "gemini-2.5-pro"
    assert _model_for_no_router("assert_visual_state", "gemini-2.0-flash") == "gemini-2.0-flash"
    print("  [PASS] _model_for() works with and without router")


def test_custom_routes():
    router = InferenceRouter(custom_routes={"analyze_ui": ModelTier.FLASH})
    assert router.get_model_for("analyze_ui") == "gemini-2.0-flash"
    assert router.get_model_for("extract_target") == "gemini-2.5-pro"
    print("  [PASS] Custom routes override defaults")


def test_local_fallback():
    router = InferenceRouter(enable_local=False)
    model = router.get_model_for("temporal_poll")
    assert model == "gemini-2.0-flash", f"Expected Flash fallback (local disabled), got {model}"
    print("  [PASS] Local tier falls back to Flash when disabled")


def test_adaptive_promotion():
    """Flash task with high error rate gets promoted to Pro."""
    router = InferenceRouter()
    assert router.get_model_for("assert_visual_state") == "gemini-2.0-flash"

    for _ in range(10):
        router.record_outcome("assert_visual_state", latency_ms=3000, success=False)

    assert router.get_model_for("assert_visual_state") == "gemini-2.5-pro", \
        "Expected promotion to Pro after sustained failures"
    assert len(router.adaptations) >= 1
    assert "Promoted" in router.adaptations[-1]
    print(f"  [PASS] Adaptive promotion: Flash->Pro on high error rate")


def test_adaptive_demotion():
    """Pro task with fast latency and zero errors gets demoted to Flash."""
    router = InferenceRouter()
    assert router.get_model_for("extract_target") == "gemini-2.5-pro"

    for _ in range(10):
        router.record_outcome("extract_target", latency_ms=1500, success=True)

    assert router.get_model_for("extract_target") == "gemini-2.0-flash", \
        "Expected demotion to Flash after sustained fast + successful calls"
    assert any("Demoted" in a for a in router.adaptations)
    print(f"  [PASS] Adaptive demotion: Pro->Flash on low latency + zero errors")


def test_no_premature_adaptation():
    """Adaptation should not trigger before MIN_OBSERVATIONS."""
    router = InferenceRouter()
    for _ in range(3):
        router.record_outcome("assert_visual_state", latency_ms=3000, success=False)
    assert router.get_model_for("assert_visual_state") == "gemini-2.0-flash", \
        "Should NOT promote before MIN_OBSERVATIONS"
    assert len(router.adaptations) == 0
    print("  [PASS] No premature adaptation before MIN_OBSERVATIONS")


def test_persistence_roundtrip():
    """Learned state survives save/load cycle."""
    import tempfile, os
    tmp = os.path.join(tempfile.mkdtemp(), "router_state.json")

    r1 = InferenceRouter(persist_path=tmp)
    for _ in range(10):
        r1.record_outcome("assert_visual_state", latency_ms=3000, success=False)
    assert r1.get_model_for("assert_visual_state") == "gemini-2.5-pro"

    r2 = InferenceRouter(persist_path=tmp)
    assert r2.get_model_for("assert_visual_state") == "gemini-2.5-pro", \
        "Learned promotion should survive persistence roundtrip"
    perf = r2.get_performance_summary()
    assert "assert_visual_state" in perf
    assert perf["assert_visual_state"]["total_calls"] == 10
    print(f"  [PASS] Persistence roundtrip: learned routes survive save/load")


def test_performance_summary():
    router = InferenceRouter()
    router.record_outcome("analyze_ui", latency_ms=5000, success=True)
    router.record_outcome("analyze_ui", latency_ms=4500, success=True)
    router.record_outcome("assert_visual_state", latency_ms=1200, success=True)
    summary = router.get_performance_summary()
    assert "analyze_ui" in summary
    assert "assert_visual_state" in summary
    assert summary["analyze_ui"]["total_calls"] == 2
    assert summary["analyze_ui"]["ema_latency_ms"] > 0
    print(f"  [PASS] Performance summary: {summary}")


if __name__ == "__main__":
    print("\n=== InferenceRouter Dry-Run Tests ===\n")
    tests = [
        test_router_instantiation,
        test_known_routes,
        test_unknown_fallback,
        test_stats_tracking,
        test_model_for_helper,
        test_custom_routes,
        test_local_fallback,
        test_adaptive_promotion,
        test_adaptive_demotion,
        test_no_premature_adaptation,
        test_persistence_roundtrip,
        test_performance_summary,
    ]
    passed = 0
    failed = 0
    for test_fn in tests:
        try:
            test_fn()
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {test_fn.__name__}: {e}")
            failed += 1

    print(f"\n=== Results: {passed} passed, {failed} failed ===\n")
    sys.exit(1 if failed > 0 else 0)
