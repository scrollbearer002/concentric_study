#!/usr/bin/env python3
"""Cross-site auth benchmark for Automation Exercise in Safari.

This is the second live website benchmark after QA Practice. It stresses a
different auth topology:

- split login and signup teaser surfaces on the same page
- a full account-information signup page
- persisted logged-in state
- logout
- re-login with the created credential
- account deletion

The benchmark also records how the generic auth router classifies each surface,
so the result is not just a site script but evidence about transfer.
"""

from __future__ import annotations

import json
import random
import string
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_infra.diagnostic_reader import DiagnosticReader
from agent_infra.trace_writer import TraceWriter
from security.auth_workflow import (
    AuthSurfaceObservation,
    AuthWorkflowContext,
    classify_auth_surface,
    plan_auth_workflow,
)


SITE_BASE = "https://automationexercise.com"
LOGIN_URL = f"{SITE_BASE}/login"


@dataclass(frozen=True)
class Account:
    name: str
    email: str
    password: str


def build_login_surface_snapshot(page: dict[str, Any]) -> AuthSurfaceObservation:
    return AuthSurfaceObservation(
        url=page["href"],
        visible_text=page.get("body", ""),
        heading_text=page.get("login_heading", ""),
        submit_labels=("Login",),
        has_email_field=bool(page.get("login_email_present")),
        has_password_field=bool(page.get("login_password_present")),
    )


def build_signup_teaser_surface_snapshot(page: dict[str, Any]) -> AuthSurfaceObservation:
    return AuthSurfaceObservation(
        url=page["href"],
        visible_text=page.get("body", ""),
        heading_text=page.get("signup_heading", ""),
        submit_labels=("Signup",),
        has_email_field=bool(page.get("signup_email_present")),
    )


def build_subscription_surface_snapshot(page: dict[str, Any]) -> AuthSurfaceObservation:
    return AuthSurfaceObservation(
        url=page["href"],
        visible_text=page.get("body", ""),
        heading_text="SUBSCRIPTION",
        submit_labels=("Subscribe",),
        has_email_field=bool(page.get("subscription_email_present")),
    )


class AutomationExerciseAuthRunner:
    def __init__(self) -> None:
        self.cre_dir = Path(__file__).parent
        self.trace = TraceWriter(
            output_dir=self.cre_dir,
            task_id="AUTOMATIONEXERCISE_AUTH_BENCHMARK",
            task_description="Exercise Automation Exercise signup, logout, login, and account deletion in Safari.",
            agent_config={
                "browser": "Safari",
                "site": SITE_BASE,
                "mode": "auth_benchmark",
            },
        )
        self.run_dir = self.trace.run_dir
        self.summary: dict[str, Any] = {
            "site": SITE_BASE,
            "run_id": self.trace.run_id,
            "status": "running",
            "account": {},
            "surface_classification": {},
            "steps": {},
        }
        self.account = self._build_account()

    def _build_account(self) -> Account:
        suffix = "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(8))
        return Account(
            name=f"Codex {suffix}",
            email=f"codex.{suffix}@example.com",
            password="Aa!" + "".join(random.choice(string.ascii_letters + string.digits) for _ in range(12)),
        )

    def _step(self, index: int, action_type: str, thought: str) -> Any:
        step = self.trace.begin_step(index)
        step.thought = thought
        step.action = {"type": action_type, "parameters": {}}
        return step

    def _end_step(self, step: Any, success: bool, post_state: dict[str, Any]) -> None:
        step.action_result = {"success": success, "status": "ok" if success else "error"}
        step.post_state = post_state
        self.trace.end_step(step)

    def _save_summary(self) -> None:
        path = self.run_dir / "automationexercise_auth_summary.json"
        path.write_text(json.dumps(self.summary, indent=2, default=str), encoding="utf-8")

    def _run_osascript(self, script: str, *, timeout: int = 40) -> str:
        proc = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if proc.returncode != 0:
            stderr = proc.stderr.strip() or proc.stdout.strip() or "osascript failed"
            raise RuntimeError(stderr)
        return proc.stdout.strip()

    def _safari_do_javascript(self, script: str) -> str:
        literal = json.dumps(script)
        applescript = f'''
tell application "Safari"
    return do JavaScript {literal} in current tab of front window
end tell
'''
        return self._run_osascript(applescript)

    def _browser_json(self, js: str) -> dict[str, Any]:
        last_error: Exception | None = None
        for attempt in range(8):
            raw = self._safari_do_javascript(js)
            if not raw.strip():
                last_error = ValueError("Safari returned empty JavaScript payload")
                time.sleep(0.15 * (attempt + 1))
                continue
            try:
                return json.loads(raw)
            except json.JSONDecodeError as exc:
                last_error = exc
                time.sleep(0.15 * (attempt + 1))
        if last_error is not None:
            raise last_error
        raise RuntimeError("Could not decode browser JSON payload")

    def _navigate(self, url: str, *, timeout_seconds: float = 20.0) -> dict[str, Any]:
        self._run_osascript(
            f'''
tell application "Safari"
    activate
    if (count of windows) = 0 then
        make new document with properties {{URL:"{url}"}}
    else
        set URL of current tab of front window to "{url}"
    end if
end tell
'''
        )
        deadline = time.time() + timeout_seconds
        last: dict[str, Any] = {"success": False}
        while time.time() < deadline:
            try:
                state = self._browser_json(
                    """JSON.stringify({
  href: location.href,
  ready: document.readyState,
  title: document.title
})"""
                )
                last = {
                    "success": state.get("ready") in {"interactive", "complete"} and state.get("href", "").startswith(url),
                    **state,
                }
                if last["success"]:
                    return last
            except Exception as exc:
                last = {"success": False, "error": str(exc)}
            time.sleep(0.5)
        return last

    def _observe_login_page(self) -> dict[str, Any]:
        return self._browser_json(
            """JSON.stringify({
  href: location.href,
  title: document.title,
  login_heading: Array.from(document.querySelectorAll('h2')).find(el => /login to your account/i.test(el.innerText || ''))?.innerText || '',
  signup_heading: Array.from(document.querySelectorAll('h2')).find(el => /new user signup/i.test(el.innerText || ''))?.innerText || '',
  body: document.body ? document.body.innerText.slice(0, 1200) : '',
  login_email_present: !!Array.from(document.querySelectorAll('input[name="email"]'))[0],
  login_password_present: !!document.querySelector('input[name="password"]'),
  signup_name_present: !!document.querySelector('input[name="name"]'),
  signup_email_present: !!Array.from(document.querySelectorAll('input[name="email"]'))[1],
  subscription_email_present: !!document.querySelector('#susbscribe_email')
})"""
        )

    def _classify_login_page_surfaces(self, page: dict[str, Any]) -> dict[str, Any]:
        login_obs = build_login_surface_snapshot(page)
        signup_obs = build_signup_teaser_surface_snapshot(page)
        subscription_obs = build_subscription_surface_snapshot(page)

        login_plan = plan_auth_workflow(
            AuthWorkflowContext(
                observation=login_obs,
                provider="proton_pass",
                has_existing_credential=True,
                proton_pass_available=True,
                proton_pass_unlocked=True,
            )
        )
        signup_plan = plan_auth_workflow(
            AuthWorkflowContext(
                observation=signup_obs,
                provider="proton_pass",
                proton_pass_available=True,
                proton_pass_unlocked=True,
            )
        )
        subscription_plan = plan_auth_workflow(
            AuthWorkflowContext(
                observation=subscription_obs,
                provider="none",
            )
        )

        return {
            "login": {
                "intent": classify_auth_surface(login_obs),
                "plan": login_plan.to_dict(),
            },
            "signup_teaser": {
                "intent": classify_auth_surface(signup_obs),
                "plan": signup_plan.to_dict(),
            },
            "subscription_negative_control": {
                "intent": classify_auth_surface(subscription_obs),
                "plan": subscription_plan.to_dict(),
            },
        }

    def _start_signup(self) -> dict[str, Any]:
        return self._browser_json(
            f"""(() => {{
  const set = (sel, value, idx = 0) => {{
    const el = document.querySelectorAll(sel)[idx];
    if (!el) return false;
    el.focus();
    el.value = value;
    el.dispatchEvent(new Event('input', {{ bubbles: true }}));
    el.dispatchEvent(new Event('change', {{ bubbles: true }}));
    return true;
  }};
  const nameOk = set('input[name="name"]', {json.dumps(self.account.name)});
  const emailOk = set('input[name="email"]', {json.dumps(self.account.email)}, 1);
  const button = Array.from(document.querySelectorAll('button')).find(btn => /signup/i.test((btn.innerText || btn.textContent || '').trim()));
  if (button) button.click();
  return JSON.stringify({{
    name_ok: nameOk,
    email_ok: emailOk,
    clicked: !!button
  }});
}})()"""
        )

    def _observe_signup_page(self) -> dict[str, Any]:
        return self._browser_json(
            """JSON.stringify({
  href: location.href,
  title: document.title,
  heading: document.querySelector('b, h2')?.innerText || '',
  body: document.body ? document.body.innerText.slice(0, 1400) : '',
  password_present: !!document.querySelector('#password'),
  confirm_password_present: false,
  passkey_button_present: !!Array.from(document.querySelectorAll('button,a')).find(el => /passkey/i.test((el.innerText || el.textContent || '').trim()))
})"""
        )

    def _classify_signup_page(self, page: dict[str, Any]) -> dict[str, Any]:
        obs = AuthSurfaceObservation(
            url=page["href"],
            visible_text=page.get("body", ""),
            heading_text=page.get("heading", ""),
            submit_labels=("Create Account",),
            has_email_field=True,
            has_password_field=bool(page.get("password_present")),
            has_confirm_password_field=bool(page.get("confirm_password_present")),
            has_passkey_button=bool(page.get("passkey_button_present")),
        )
        plan = plan_auth_workflow(
            AuthWorkflowContext(
                observation=obs,
                provider="proton_pass",
                proton_pass_available=True,
                proton_pass_unlocked=True,
                proton_pass_alias_available=True,
                wants_alias=True,
            )
        )
        return {"intent": classify_auth_surface(obs), "plan": plan.to_dict()}

    def _complete_signup(self) -> dict[str, Any]:
        return self._browser_json(
            f"""(() => {{
  const set = (sel, value) => {{
    const el = document.querySelector(sel);
    if (!el) return false;
    el.focus();
    el.value = value;
    el.dispatchEvent(new Event('input', {{ bubbles: true }}));
    el.dispatchEvent(new Event('change', {{ bubbles: true }}));
    return true;
  }};
  const setSelect = (sel, value) => {{
    const el = document.querySelector(sel);
    if (!el) return false;
    el.value = value;
    el.dispatchEvent(new Event('change', {{ bubbles: true }}));
    return true;
  }};
  const click = (sel) => {{
    const el = document.querySelector(sel);
    if (!el) return false;
    el.click();
    return true;
  }};
  const payload = {{
    gender: click('#id_gender1'),
    password: set('#password', {json.dumps(self.account.password)}),
    days: setSelect('#days', '10'),
    months: setSelect('#months', '5'),
    years: setSelect('#years', '1990'),
    first_name: set('#first_name', 'Codex'),
    last_name: set('#last_name', 'Tester'),
    company: set('#company', 'Concentric Study'),
    address1: set('#address1', '123 Test Street'),
    address2: set('#address2', 'Suite 9'),
    country: setSelect('#country', 'United States'),
    state: set('#state', 'CA'),
    city: set('#city', 'San Francisco'),
    zipcode: set('#zipcode', '94107'),
    mobile_number: set('#mobile_number', '4155550101')
  }};
  const button = Array.from(document.querySelectorAll('button')).find(btn => /create account/i.test((btn.innerText || btn.textContent || '').trim()));
  if (button) button.click();
  payload.clicked = !!button;
  return JSON.stringify(payload);
}})()"""
        )

    def _wait_for_account_state(self, expected: str, *, timeout_seconds: float = 20.0) -> dict[str, Any]:
        deadline = time.time() + timeout_seconds
        last: dict[str, Any] = {"success": False}
        while time.time() < deadline:
            last = self._browser_json(
                """JSON.stringify({
  href: location.href,
  body: document.body ? document.body.innerText.slice(0, 1000) : '',
  links: Array.from(document.querySelectorAll('a')).map(a => (a.innerText || a.textContent || '').trim()).filter(Boolean).slice(0, 30)
})"""
            )
            body = last.get("body", "")
            links = last.get("links", [])
            if expected == "logged_in" and ("Logout" in links or "Delete Account" in links) and "Logged in as" in body:
                return {"success": True, **last}
            if expected == "deleted" and "ACCOUNT DELETED!" in body:
                return {"success": True, **last}
            if expected == "login_page" and last.get("href", "").startswith(LOGIN_URL):
                return {"success": True, **last}
            time.sleep(0.5)
        return {"success": False, **last}

    def _click_link(self, pattern: str) -> dict[str, Any]:
        return self._browser_json(
            f"""(() => {{
  const link = Array.from(document.querySelectorAll('a')).find(a => new RegExp({json.dumps(pattern)}, 'i').test((a.innerText || a.textContent || '').trim()));
  if (link) link.click();
  return JSON.stringify({{ clicked: !!link, text: link ? (link.innerText || link.textContent || '').trim() : '' }});
}})()"""
        )

    def _login_existing_account(self) -> dict[str, Any]:
        return self._browser_json(
            f"""(() => {{
  const email = Array.from(document.querySelectorAll('input[name="email"]'))[0];
  const password = document.querySelector('input[name="password"]');
  const set = (el, value) => {{
    if (!el) return false;
    el.focus();
    el.value = value;
    el.dispatchEvent(new Event('input', {{ bubbles: true }}));
    el.dispatchEvent(new Event('change', {{ bubbles: true }}));
    return true;
  }};
  const emailOk = set(email, {json.dumps(self.account.email)});
  const passwordOk = set(password, {json.dumps(self.account.password)});
  const button = Array.from(document.querySelectorAll('button')).find(btn => /login/i.test((btn.innerText || btn.textContent || '').trim()));
  if (button) button.click();
  return JSON.stringify({{
    email_ok: emailOk,
    password_ok: passwordOk,
    clicked: !!button
  }});
}})()"""
        )

    def run(self) -> int:
        index = 0
        try:
            self.summary["account"] = {"name": self.account.name, "email": self.account.email}

            step = self._step(index, "navigate_login_page", "Open Automation Exercise login/signup page and inspect all auth-adjacent surfaces.")
            nav = self._navigate(LOGIN_URL)
            page = self._observe_login_page()
            surfaces = self._classify_login_page_surfaces(page)
            self.summary["surface_classification"]["login_page"] = surfaces
            payload = {"navigation": nav, "page": page, "surfaces": surfaces}
            self.summary["steps"]["navigate_login_page"] = payload
            self._end_step(step, bool(nav.get("success")) and surfaces["login"]["intent"] == "login_existing" and surfaces["signup_teaser"]["intent"] == "signup_new" and surfaces["subscription_negative_control"]["intent"] == "unknown", payload)
            index += 1

            step = self._step(index, "start_signup", "Use the new-user surface to start account creation with a fresh credential.")
            start = self._start_signup()
            time.sleep(4)
            signup_page = self._observe_signup_page()
            signup_surface = self._classify_signup_page(signup_page)
            self.summary["surface_classification"]["signup_page"] = signup_surface
            payload = {"start": start, "signup_page": signup_page, "signup_surface": signup_surface}
            self.summary["steps"]["start_signup"] = payload
            self._end_step(step, bool(start.get("clicked")) and signup_surface["intent"] == "signup_new", payload)
            index += 1

            step = self._step(index, "complete_signup", "Fill the account-information form, create the account, and verify logged-in state.")
            fill = self._complete_signup()
            time.sleep(5)
            logged_in = self._wait_for_account_state("logged_in")
            payload = {"fill": fill, "logged_in": logged_in}
            self.summary["steps"]["complete_signup"] = payload
            self._end_step(step, bool(fill.get("clicked")) and bool(logged_in.get("success")), payload)
            index += 1

            step = self._step(index, "logout", "Exit the logged-in session cleanly so the account can be exercised as an existing-credential login.")
            logout_click = self._click_link("logout")
            time.sleep(4)
            login_page_after_logout = self._wait_for_account_state("login_page")
            payload = {"logout_click": logout_click, "login_page": login_page_after_logout}
            self.summary["steps"]["logout"] = payload
            self._end_step(step, bool(logout_click.get("clicked")) and bool(login_page_after_logout.get("success")), payload)
            index += 1

            step = self._step(index, "login_existing", "Log back in with the newly created credential and verify the website now behaves like an existing-account auth surface.")
            login = self._login_existing_account()
            time.sleep(5)
            logged_in_again = self._wait_for_account_state("logged_in")
            payload = {"login": login, "logged_in_again": logged_in_again}
            self.summary["steps"]["login_existing"] = payload
            self._end_step(step, bool(login.get("clicked")) and bool(logged_in_again.get("success")), payload)
            index += 1

            step = self._step(index, "delete_account", "Delete the benchmark account so the site is returned to a clean post-run state.")
            delete_click = self._click_link("delete account")
            time.sleep(5)
            deleted = self._wait_for_account_state("deleted")
            payload = {"delete_click": delete_click, "deleted": deleted}
            self.summary["steps"]["delete_account"] = payload
            self._end_step(step, bool(delete_click.get("clicked")) and bool(deleted.get("success")), payload)

            self.summary["status"] = "success"
            self._save_summary()
            self.trace.finalize(outcome="success")
            return 0
        except Exception as exc:
            self.summary["status"] = "error"
            self.summary["error"] = str(exc)
            self._save_summary()
            self.trace.finalize(outcome="error")
            return 1


def main() -> int:
    runner = AutomationExerciseAuthRunner()
    rc = runner.run()
    reader = DiagnosticReader(runner.run_dir)
    (runner.run_dir / "diagnostic.txt").write_text(reader.full_diagnostic(), encoding="utf-8")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
