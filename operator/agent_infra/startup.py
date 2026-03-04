"""Safari launch, readiness polling, and initial UI capture.

Extracted from test_excalidraw_covt.py per Fowler (2018) Move Function
to reduce monolith complexity.
"""
from __future__ import annotations

import os
import time
import subprocess

try:
    from agent_core import MacOSAgentCore
    from visual_engine import VisualGroundingEngine
    ENTERPRISE_AVAILABLE = True
except ImportError:
    MacOSAgentCore = None  # type: ignore
    VisualGroundingEngine = None  # type: ignore
    ENTERPRISE_AVAILABLE = False

_exec_log_line = None
_pass_log_line = None
get_screenshot_center = None


def inject_dependencies(exec_log_fn, pass_log_fn, get_center_fn):
    global _exec_log_line, _pass_log_line, get_screenshot_center
    _exec_log_line = exec_log_fn
    _pass_log_line = pass_log_fn
    get_screenshot_center = get_center_fn


def _init_agent() -> tuple[bool, object, object, object, object]:
    """Returns (use_enterprise, agent, vision_engine, client, vlm)."""
    use_enterprise = ENTERPRISE_AVAILABLE and (
        os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")
    )
    if use_enterprise:
        print("   Mode: Enterprise (MacOSAgentCore + native Quartz keystroke/draw + File API, kernel-free)")
        _exec_log_line("mode", "enterprise")
    else:
        print("   Mode: Legacy (VLMCoordinator + Hammerspoon kernel)")
        _exec_log_line("mode", "legacy")
        print("   (For kernel-free run: use venv + set GEMINI_API_KEY so Enterprise loads)")

    agent = None
    vision_engine = None
    client = None
    vlm = None

    if use_enterprise:
        try:
            from inference_router import InferenceRouter
            _router_state_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "cre", "routing_state.json")
            if os.environ.get("DISABLE_ADAPTIVE_ROUTING"):
                router = InferenceRouter(persist_path=None)
                print("  [ABLATION] Adaptive routing DISABLED (fixed Flash)")
                _exec_log_line("ablation", "adaptive_routing_disabled")
            else:
                router = InferenceRouter(persist_path=_router_state_path)
            agent = MacOSAgentCore(router=router)
            vision_engine = VisualGroundingEngine(grid_size=12, output_dir=os.path.dirname(os.path.abspath(__file__)) or ".")
            print("  MacOSAgentCore and VisualGroundingEngine initialized (kernel not required)")
            _exec_log_line("init", "MacOSAgentCore + InferenceRouter + VisualGroundingEngine")
        except Exception as e:
            print(f"  Enterprise init failed: {e} (falling back to legacy)")
            _exec_log_line("init_error", str(e))
            use_enterprise = False

    if not use_enterprise:
        client = CodexClient()
        try:
            ping_result = client.ping()
            print(f"  Kernel active: {ping_result}")
        except Exception as e:
            print(f"  Kernel not running: {e}")
            print("\n--- To run WITHOUT Hammerspoon (enterprise, kernel-free) ---")
            print("  1. From operator dir: python3 -m venv venv && ./venv/bin/pip install -r requirements.txt")
            print("  2. Set GEMINI_API_KEY (or OPENAI_API_KEY)")
            print("  3. Run: PYTHONPATH=$(pwd) ./venv/bin/python cre/test_excalidraw_covt.py")
            return use_enterprise, None, None, None, None
        try:
            screen_info = client.get_screen_info()
            print(f"  Screen info: Scale factor {screen_info.get('scale_factor')}x")
        except Exception as e:
            print(f"  Failed to get screen info: {e}")
            return use_enterprise, None, None, None, None
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("\n  OPENAI_API_KEY not set. CoVT requires VLM.")
            return use_enterprise, None, None, None, None
        vlm = VLMCoordinator(client, api_key=api_key, model="gemini-2.5-pro")
        print("  VLM Coordinator initialized")
    else:
        screen_info = agent.get_screen_info()
        print(f"  Screen info (native): Scale factor {screen_info.get('scale_factor')}x")

    return use_enterprise, agent, vision_engine, client, vlm


def _open_safari():
    """Launch Safari to Excalidraw. Best-effort — does not raise on failure."""
    print("\n  Opening Safari to Excalidraw...")
    _exec_log_line("safari_open", "open -a Safari https://excalidraw.com")
    try:
        subprocess.run(["open", "-a", "Safari", "https://excalidraw.com"], check=True, timeout=5)
        print("  Safari opened")
        _exec_log_line("safari_opened", "ok")
    except Exception as e:
        print(f"  Could not auto-open Safari: {e}")
        _exec_log_line("safari_open_error", str(e))


def _poll_readiness_enterprise(agent, cre_dir):
    """Smart readiness poll using Gemini Flash (replaces hardcoded 10s sleep)."""
    print("\n  Smart readiness poll (replacing hardcoded 10s sleep)...")
    time.sleep(3)
    _tmp_state = str(cre_dir / "_readiness_check.png")
    consecutive_yes = 0
    poll_count = 0
    max_polls = 9
    while consecutive_yes < 2 and poll_count < max_polls:
        poll_count += 1
        try:
            subprocess.run(["screencapture", "-x", _tmp_state], check=True, timeout=5)
            ready = agent.assert_visual_state(
                _tmp_state,
                "Is the Excalidraw canvas fully loaded with a white drawing area visible?",
                model="gemini-2.0-flash",
            )
            if ready:
                consecutive_yes += 1
                print(f"   Poll {poll_count}: READY ({consecutive_yes}/2)", flush=True)
            else:
                consecutive_yes = 0
                print(f"   Poll {poll_count}: not ready", flush=True)
        except Exception:
            consecutive_yes = 0
            print(f"   Poll {poll_count}: check failed, retrying...", flush=True)
        if consecutive_yes < 2:
            time.sleep(1)
    confirmed = consecutive_yes >= 2
    if confirmed:
        print(f"  Page confirmed ready after {poll_count} polls (~{3 + poll_count}s)")
    else:
        print(f"  Max polls reached — proceeding (page may still be loading)")
    _exec_log_line("wait_complete", "smart_poll", {"polls": poll_count, "confirmed": confirmed})


def _poll_readiness_legacy():
    """Legacy 10-second countdown when enterprise mode is not available."""
    print("\n  Waiting 10 seconds for full page load (legacy mode)...")
    for i in range(10, 0, -1):
        print("   %s..." % i, end="", flush=True)
        time.sleep(1)
    print("\n  Page load wait complete")
    _exec_log_line("wait_complete", "legacy_10s")


def _should_skip_analyze_ui(trust_tracker, current_state_path) -> bool:
    """Decide whether analyze_ui can be trust-skipped (Bayesian warm-start)."""
    if not os.environ.get("CONCENTRIC_TRIANGLES_CLEAN") or trust_tracker is None:
        return False
    _trust_key_analyze = "startup|analyze_ui"
    if trust_tracker.should_verify(_trust_key_analyze):
        return False
    cx, cy = get_screenshot_center(current_state_path)
    if abs(cx - 1440) <= 50 and abs(cy - 900) <= 50:
        print(f"  [TRUST-SKIP] analyze_ui skipped (trust={trust_tracker.consecutive_successes(_trust_key_analyze)})")
        _exec_log_line("analyze_ui_skip", "trust", {"cx": cx, "cy": cy})
        return True
    trust_tracker.record_failure(_trust_key_analyze)
    print(f"  [TRUST-RESET] Center ({cx},{cy}) outside tolerance — calling analyze_ui")
    return False


def _capture_enterprise_ui(agent, vision_engine, current_state_path, trust_tracker) -> dict:
    """Enterprise path: capture screenshot, optionally run SoM + analyze_ui."""
    print("\n  Capturing full-resolution screenshot (native screencapture)...")
    subprocess.run(["screencapture", "-x", current_state_path], check=True, timeout=10)

    if _should_skip_analyze_ui(trust_tracker, current_state_path):
        cx, cy = get_screenshot_center(current_state_path)
        ui_analysis = {
            "canvas_center_x": cx, "canvas_center_y": cy,
            "page_loaded": True, "canvas_center": {"x": cx, "y": cy},
        }
        print(f"   True middle from screenshot: ({cx}, {cy})")
        return ui_analysis

    coords_map, som_path = vision_engine.generate_som_overlay(
        current_state_path, output_filename="som_overlay.png"
    )
    print(f"  SoM overlay generated; {len(coords_map)} zones mapped")
    _exec_log_line("som_overlay", None, {"zones": len(coords_map)})
    ui_analysis = agent.analyze_ui(som_path)
    if os.environ.get("CONCENTRIC_TRIANGLES_CLEAN"):
        cx, cy = get_screenshot_center(current_state_path)
        ui_analysis["canvas_center"] = {"x": cx, "y": cy}
        ui_analysis["canvas_center_x"], ui_analysis["canvas_center_y"] = cx, cy
        print(f"   True middle from screenshot: ({cx}, {cy})")
    else:
        ui_analysis["canvas_center"] = {
            "x": ui_analysis["canvas_center_x"],
            "y": ui_analysis["canvas_center_y"],
        }
    if trust_tracker is not None:
        trust_tracker.record_success("startup|analyze_ui")
    return ui_analysis


def _capture_legacy_ui(client, vlm) -> dict:
    """Legacy path: kernel screenshot + VLM analysis."""
    print("\n  Capturing initial UI state (kernel screenshot)...")
    screen_info = client.get_screen_info()
    width = screen_info.get("logical_width", 1440)
    height = screen_info.get("logical_height", 900)
    region = {
        "x": int(width * 0.1), "y": int(height * 0.05),
        "w": int(width * 0.5), "h": int(height * 0.4),
    }
    initial_screenshot = client.screenshot(region=region, scale=0.15)
    print(f"  Initial screenshot captured: {len(initial_screenshot)} bytes")
    return analyze_ui_initial_state(vlm, initial_screenshot)


def _maximize_safari(use_enterprise, agent):
    if use_enterprise and agent:
        try:
            screen_info = agent.get_screen_info()
            w = int(screen_info.get("logical_width", 1440))
            h = int(screen_info.get("logical_height", 900))
            script = f'tell application "Safari" to set bounds of front window to {{0, 22, {w}, {h}}}'
            result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print("  Safari window maximized")
                _exec_log_line("safari_maximize", "ok", {"w": w, "h": h})
            else:
                print(f"  Safari maximize failed (continuing): {result.stderr or result.stdout}")
        except Exception as e:
            print(f"  Safari maximize error (continuing): {e}")
    else:
        try:
            script = 'tell application "Safari" to set bounds of front window to {0, 22, 1440, 900}'
            subprocess.run(["osascript", "-e", script], check=False, capture_output=True, timeout=5)
            print("  Safari window set to default bounds")
        except Exception:
            pass


def _launch_safari_and_capture(use_enterprise, agent, vision_engine, client, vlm, cre_dir, trust_tracker=None):
    """Opens Safari, waits for page load, takes initial screenshot.

    Decomposed per Parnas (1972) information hiding — each sub-step is a
    focused function with a single concern.
    Returns (ui_analysis, current_state_path) or raises on failure.
    """
    _exec_log_line("phase", "PHASE 1: PAGE LOAD & INITIAL OBSERVATION")
    print("\n" + "="*60)
    print("PHASE 1: PAGE LOAD & INITIAL OBSERVATION")
    print("="*60)

    _open_safari()

    _exec_log_line("wait_start", "smart_poll")
    if use_enterprise and agent:
        _poll_readiness_enterprise(agent, cre_dir)
    else:
        _poll_readiness_legacy()

    _maximize_safari(use_enterprise, agent)

    _exec_log_line("phase", "before enforce_app_focus")
    if use_enterprise and agent:
        try:
            agent.enforce_app_focus("Safari")
            _exec_log_line("enforce_focus", "Safari", {"frontmost": agent.get_frontmost_application_name()})
        except RuntimeError as e:
            print(f"  Focus enforcement failed: {e}")
            raise

    current_state_path = str(cre_dir / "current_state.png")

    if use_enterprise and agent and vision_engine:
        ui_analysis = _capture_enterprise_ui(agent, vision_engine, current_state_path, trust_tracker)
    else:
        ui_analysis = _capture_legacy_ui(client, vlm)

    return ui_analysis, current_state_path
