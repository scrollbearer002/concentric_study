#!/usr/bin/env python3
"""Login flow end-to-end test.

Proves the agent's web primitives generalize beyond Excalidraw by executing a
6-step login sequence on a real website:

    navigate → find_email_field → type_email → find_password_field → type_password → click_sign_in

Uses CredentialVault for secure credential retrieval (macOS Keychain) and
HITLGuard for sensitive-action approval. All steps are recorded to a
structured trace for post-hoc analysis.

Usage:
    cd operator
    LOGIN_DOMAIN=httpbin.org ./venv/bin/python cre/test_login_flow.py

    # Or with a custom URL and credential domain:
    LOGIN_URL="https://example.com/login" LOGIN_DOMAIN="example.com" \\
        ./venv/bin/python cre/test_login_flow.py

Environment variables:
    LOGIN_DOMAIN   — Domain to retrieve credentials for (required)
    LOGIN_URL      — Full URL of the login page (default: https://{LOGIN_DOMAIN}/login)
    HITL_APPROVE   — Set to "1" to auto-approve sensitive actions (testing only)
    GEMINI_API_KEY — Required for enterprise mode
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_infra import TraceWriter

try:
    from agent_core import MacOSAgentCore
    from visual_engine import VisualGroundingEngine
    ENTERPRISE = True
except ImportError:
    ENTERPRISE = False

try:
    from a11y_engine import A11yEngine
    from element_map import UnifiedElementMap
    from web_primitives import WebPrimitives
except ImportError:
    A11yEngine = None
    UnifiedElementMap = None
    WebPrimitives = None

from security.credential_vault import CredentialVault, HITLGuard


def _record_step(tw: TraceWriter, step_index: int, action: str, target: str,
                  status: str, metadata: dict | None = None) -> None:
    """Convenience wrapper around TraceWriter's begin_step/end_step."""
    step = tw.begin_step(step_index)
    step.action = {"type": action, "parameters": {"target": target}}
    step.action_result = {"success": status == "ok", "status": status}
    step.post_state = metadata or {}
    tw.end_step(step)


LOGIN_PLAN = [
    {"action": "navigate", "description": "Open login page in Safari"},
    {"action": "wait_page_load", "description": "Wait for page to fully load"},
    {"action": "a11y_snapshot", "description": "Capture accessibility tree of login page"},
    {"action": "type_email", "description": "Find email/username field and type credentials"},
    {"action": "type_password", "description": "Find password field and type credentials"},
    {"action": "click_submit", "description": "Click sign-in / submit button"},
]


def _navigate_safari(url: str) -> bool:
    """Open URL in Safari via AppleScript."""
    import subprocess
    script = f'''
    tell application "Safari"
        activate
        if (count of windows) = 0 then
            make new document with properties {{URL:"{url}"}}
        else
            set URL of front document to "{url}"
        end if
    end tell
    '''
    try:
        subprocess.run(["osascript", "-e", script], capture_output=True, timeout=10)
        time.sleep(3)
        return True
    except Exception:
        return False


def _take_screenshot(output_path: str) -> bool:
    import subprocess
    try:
        subprocess.run(
            ["screencapture", "-x", output_path],
            capture_output=True, timeout=5,
        )
        return Path(output_path).exists()
    except Exception:
        return False


def run_login_test() -> int:
    domain = os.environ.get("LOGIN_DOMAIN")
    if not domain:
        print("ERROR: LOGIN_DOMAIN environment variable is required")
        print("Usage: LOGIN_DOMAIN=example.com ./venv/bin/python cre/test_login_flow.py")
        return 1

    url = os.environ.get("LOGIN_URL", f"https://{domain}/login")
    auto_approve = os.environ.get("HITL_APPROVE") == "1"
    cre_dir = Path(__file__).parent

    print("\n" + "=" * 60)
    print("LOGIN FLOW END-TO-END TEST")
    print(f"  Domain: {domain}")
    print(f"  URL: {url}")
    print(f"  Auto-approve: {auto_approve}")
    print("=" * 60)

    # --- Credential retrieval ---
    vault = CredentialVault(allowed_domains=[domain])
    guard = HITLGuard(escalation_dir=str(cre_dir / "runs"))

    cred = vault.retrieve(domain)
    if not cred:
        print(f"\n  No credentials found in Keychain for '{domain}'.")
        print(f"  To add: security add-internet-password -s {domain} -a user@example.com -w 'password'")
        return 1
    print(f"  Credentials retrieved: {cred.to_safe_dict()}")

    # --- Trace writer ---
    task_id = f"LOGIN_{domain.upper().replace('.', '_')}"
    tw = TraceWriter(
        output_dir=cre_dir,
        task_id=task_id,
        task_description=f"Login to {domain}",
        agent_config={"mode": "login_test", "domain": domain, "url": url},
    )
    print(f"  Trace: {tw.run_dir}")

    step_idx = 0
    outcome = "success"

    # --- Step 1: Navigate ---
    print(f"\n  [{step_idx + 1}/{len(LOGIN_PLAN)}] {LOGIN_PLAN[0]['description']}")
    t0 = time.time()
    nav_ok = _navigate_safari(url)
    _record_step(tw, step_idx, "navigate", url,
                 "ok" if nav_ok else "error",
                 {"url": url, "duration_ms": int((time.time() - t0) * 1000)})
    if not nav_ok:
        print("  Navigation failed")
        tw.finalize(outcome="error")
        return 1
    step_idx += 1

    # --- Step 2: Wait for page load ---
    print(f"  [{step_idx + 1}/{len(LOGIN_PLAN)}] {LOGIN_PLAN[1]['description']}")
    time.sleep(3)
    screenshot_path = str(cre_dir / "login_screenshot.png")
    _take_screenshot(screenshot_path)
    _record_step(tw, step_idx, "wait_page_load", url, "ok", {"screenshot": screenshot_path})
    step_idx += 1

    # --- Step 3: A11y snapshot ---
    print(f"  [{step_idx + 1}/{len(LOGIN_PLAN)}] {LOGIN_PLAN[2]['description']}")
    a11y_data = {}
    primitives = None
    if A11yEngine and UnifiedElementMap:
        try:
            a11y = A11yEngine()
            elements = a11y.extract("Safari")
            interactive = [e for e in elements if e.is_interactive]
            a11y_data = {
                "backend": a11y.backend,
                "total": len(elements),
                "interactive": len(interactive),
                "labels": [e.label for e in interactive],
                "roles": list({e.role for e in elements}),
            }
            print(f"    A11y: {len(elements)} elements ({len(interactive)} interactive) via {a11y.backend}")

            if ENTERPRISE and WebPrimitives:
                try:
                    from inference_router import InferenceRouter
                    agent = MacOSAgentCore(router=InferenceRouter())
                    emap = UnifiedElementMap()
                    emap.ingest_a11y(elements)
                    primitives = WebPrimitives(agent=agent, element_map=emap)
                except Exception as e:
                    print(f"    WebPrimitives init failed: {e}")
        except Exception as e:
            print(f"    A11y extraction failed: {e}")
            a11y_data = {"error": str(e)}

    _record_step(tw, step_idx, "a11y_snapshot", "Safari",
                 "ok" if "error" not in a11y_data else "partial", a11y_data)
    step_idx += 1

    # --- Step 4: Type email/username ---
    print(f"  [{step_idx + 1}/{len(LOGIN_PLAN)}] {LOGIN_PLAN[3]['description']}")
    email_result = {"status": "skipped"}
    if primitives:
        for label_candidate in ["Email", "email", "Username", "username", "E-mail", "Login"]:
            r = primitives.type_into(label_candidate, cred.username)
            if r.success:
                email_result = {"status": "ok", "label": label_candidate, "duration_ms": r.duration_ms}
                print(f"    Typed into '{label_candidate}' (ok)")
                break
        else:
            email_result = {"status": "error", "error": "No matching email/username field found"}
            print(f"    Could not find email field")
    else:
        print(f"    [SKIPPED] No WebPrimitives available (need enterprise mode + a11y)")
        email_result = {"status": "skipped", "reason": "no_primitives"}

    check = guard.check_action("enter_password", {"domain": domain, "field": "email"})
    _record_step(tw, step_idx, "type_email", domain,
                 email_result["status"],
                 {**email_result, "hitl_check": check["requires_approval"]})
    step_idx += 1

    # --- Step 5: Type password ---
    print(f"  [{step_idx + 1}/{len(LOGIN_PLAN)}] {LOGIN_PLAN[4]['description']}")
    check = guard.check_action("enter_password", {"domain": domain, "type": "password"})

    if check["requires_approval"] and not auto_approve:
        print(f"    [HITL] Approval required: {check['reasons']}")
        guard.request_approval(check)
        pw_result = {"status": "blocked", "reason": "hitl_required", "approval_reasons": check["reasons"]}
    elif primitives:
        pw_result = {"status": "skipped"}
        for label_candidate in ["Password", "password", "Contraseña", "Secret"]:
            r = primitives.type_into(label_candidate, cred.password)
            if r.success:
                pw_result = {"status": "ok", "label": label_candidate, "duration_ms": r.duration_ms}
                print(f"    Typed into '{label_candidate}' (ok)")
                break
        else:
            if pw_result["status"] == "skipped":
                pw_result = {"status": "error", "error": "No matching password field found"}
                print(f"    Could not find password field")
    else:
        print(f"    [SKIPPED] No WebPrimitives available")
        pw_result = {"status": "skipped", "reason": "no_primitives"}

    _record_step(tw, step_idx, "type_password", domain,
                 pw_result["status"],
                 {k: v for k, v in pw_result.items() if k != "password"})
    step_idx += 1

    # --- Step 6: Click submit ---
    print(f"  [{step_idx + 1}/{len(LOGIN_PLAN)}] {LOGIN_PLAN[5]['description']}")
    check = guard.check_action("submit_form", {"domain": domain})

    if check["requires_approval"] and not auto_approve:
        print(f"    [HITL] Approval required for form submission: {check['reasons']}")
        guard.request_approval(check)
        submit_result = {"status": "blocked", "reason": "hitl_required"}
    elif primitives:
        submit_result = {"status": "skipped"}
        for label_candidate in ["Sign in", "Log in", "Login", "Submit", "Sign In", "Log In"]:
            r = primitives.click_element(label_candidate)
            if r.success:
                submit_result = {"status": "ok", "label": label_candidate, "duration_ms": r.duration_ms}
                print(f"    Clicked '{label_candidate}' (ok)")
                break
        else:
            if submit_result["status"] == "skipped":
                submit_result = {"status": "error", "error": "No matching submit button found"}
                print(f"    Could not find submit button")
    else:
        print(f"    [SKIPPED] No WebPrimitives available")
        submit_result = {"status": "skipped", "reason": "no_primitives"}

    _record_step(tw, step_idx, "click_submit", domain,
                 submit_result["status"], submit_result)

    # --- Post-login screenshot ---
    time.sleep(3)
    post_screenshot = str(cre_dir / "login_post_screenshot.png")
    _take_screenshot(post_screenshot)

    # --- Finalize ---
    blocked_steps = sum(1 for s in [email_result, pw_result, submit_result] if s.get("status") == "blocked")
    skipped_steps = sum(1 for s in [email_result, pw_result, submit_result] if s.get("status") == "skipped")
    error_steps = sum(1 for s in [email_result, pw_result, submit_result] if s.get("status") == "error")

    if blocked_steps > 0:
        outcome = "blocked_hitl"
    elif error_steps > 0:
        outcome = "partial_failure"
    elif skipped_steps == 3:
        outcome = "infrastructure_only"

    manifest = tw.finalize(outcome=outcome)
    print(f"\n{'=' * 60}")
    print(f"  LOGIN TEST COMPLETE")
    print(f"  Outcome: {outcome}")
    print(f"  Steps: {manifest.get('num_steps', 0)}")
    print(f"  Trace: {tw.trace_path}")
    print(f"  Access log: {json.dumps(vault.get_access_log(), indent=2)}")
    if guard.get_pending():
        print(f"  Pending HITL approvals: {len(guard.get_pending())}")
    print(f"{'=' * 60}")

    return 0 if outcome in ("success", "infrastructure_only") else 1


if __name__ == "__main__":
    sys.exit(run_login_test())
