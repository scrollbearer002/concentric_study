#!/usr/bin/env python3
"""End-to-end mastery harness for QA Practice Platform in Safari.

This script is intentionally site-specific. It exercises the full QA Practice
surface as a learning task for the current macOS/Safari runtime:

- account creation and UI login
- cookie banner suppression/acceptance
- public module completion
- auth-gated file operations
- Capybara API coverage
- self-healing page actions across mutation difficulties

Outputs:
- structured trace + manifest in ``operator/cre/runs/<run_id>/``
- per-module screenshots
- API artifacts
- mastery summary JSON
"""

from __future__ import annotations

import json
import math
import os
import random
import string
import subprocess
import sys
import time
import uuid
import zipfile
import base64
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_infra.diagnostic_reader import DiagnosticReader
from agent_infra.trace_writer import TraceWriter
from window_capture import capture_front_window


SITE_BASE = "https://www.learnaqa.info"
API_BASE = "https://api.learnaqa.info/api"
COOKIE_CONSENT_PAYLOAD = {
    "essential": True,
    "analytics": True,
    "performance": True,
}
XLSX_NS = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


@dataclass(frozen=True)
class Account:
    email: str
    password: str
    full_name: str


class QAPracticeRunner:
    def __init__(self) -> None:
        self.cre_dir = Path(__file__).parent
        self.trace = TraceWriter(
            output_dir=self.cre_dir,
            task_id="QA_PRACTICE_MASTERY",
            task_description="Complete QA Practice Platform end-to-end in Safari.",
            agent_config={
                "browser": "Safari",
                "site": SITE_BASE,
                "api": API_BASE,
                "mode": "mastery",
            },
        )
        self.run_dir = self.trace.run_dir
        self.api_dir = self.run_dir / "api"
        self.module_dir = self.run_dir / "modules"
        self.api_dir.mkdir(parents=True, exist_ok=True)
        self.module_dir.mkdir(parents=True, exist_ok=True)
        self.summary: dict[str, Any] = {
            "site": SITE_BASE,
            "api": API_BASE,
            "run_id": self.trace.run_id,
            "accounts": {},
            "modules": {},
            "api_tests": {},
            "self_healing": {},
            "status": "running",
        }
        self.session = requests.Session()
        self.primary_account: Account | None = None
        self.secondary_account: Account | None = None
        self.primary_tokens: dict[str, str] = {}
        self.secondary_tokens: dict[str, str] = {}

    # ------------------------------------------------------------------
    # Trace helpers
    # ------------------------------------------------------------------
    def _step(self, index: int, action_type: str, thought: str) -> Any:
        step = self.trace.begin_step(index)
        step.thought = thought
        step.action = {"type": action_type, "parameters": {}}
        return step

    def _end_step(self, step: Any, success: bool, post_state: dict[str, Any]) -> None:
        step.action_result = {"success": success, "status": "ok" if success else "error"}
        step.post_state = post_state
        self.trace.end_step(step)

    def _record_module_result(self, name: str, payload: dict[str, Any]) -> None:
        self.summary["modules"][name] = payload
        path = self.module_dir / f"{name}.json"
        path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")

    def _save_json(self, path: Path, payload: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")

    def _run_solver_with_retries(self, name: str, solver: Any, *, attempts: int = 3) -> dict[str, Any]:
        history: list[dict[str, Any]] = []
        final_payload: dict[str, Any] = {"success": False}
        for attempt in range(1, attempts + 1):
            payload = solver()
            history.append(
                {
                    "attempt": attempt,
                    "success": bool(payload.get("success")),
                    "summary": {
                        key: payload.get(key)
                        for key in ("success", "status", "body")
                        if key in payload
                    },
                }
            )
            final_payload = payload
            if payload.get("success"):
                if attempt > 1:
                    final_payload["retry_history"] = history
                return final_payload
            time.sleep(0.75)
        final_payload["retry_history"] = history
        final_payload["retry_exhausted"] = True
        return final_payload

    # ------------------------------------------------------------------
    # Safari helpers
    # ------------------------------------------------------------------
    def _run_osascript(self, script: str, *, timeout: int = 30) -> str:
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

    def _safari_current_url(self) -> str:
        return self._run_osascript(
            'tell application "Safari" to return URL of current tab of front window'
        )

    def _safari_restart(self) -> None:
        subprocess.run(["killall", "Safari"], check=False, capture_output=True)
        time.sleep(1.5)
        subprocess.run(["open", "-a", "Safari"], check=False, capture_output=True)
        deadline = time.time() + 15.0
        while time.time() < deadline:
            try:
                self._run_osascript('tell application "Safari" to activate', timeout=10)
                self._run_osascript(
                    '''
tell application "Safari"
    if (count of windows) = 0 then
        make new document
    end if
end tell
''',
                    timeout=10,
                )
                return
            except Exception:
                time.sleep(0.5)
        raise RuntimeError("Safari did not become controllable after restart")

    def _safari_navigate(self, url: str, *, timeout_seconds: float = 20.0) -> dict[str, Any]:
        script = f'''
tell application "Safari"
    activate
    if (count of windows) = 0 then
        make new document with properties {{URL:"{url}"}}
    else
        set URL of current tab of front window to "{url}"
    end if
end tell
'''
        self._run_osascript(script)
        deadline = time.time() + timeout_seconds
        last: dict[str, Any] = {"success": False}
        while time.time() < deadline:
            try:
                current_url = self._safari_current_url()
                ready_state = self._safari_do_javascript("document.readyState")
                last = {
                    "success": current_url.startswith(url) and ready_state in {"interactive", "complete"},
                    "current_url": current_url,
                    "ready_state": ready_state,
                }
                if last["success"]:
                    return last
            except Exception as exc:
                last = {"success": False, "error": str(exc)}
            time.sleep(0.5)
        return last

    def _browser_json(self, js: str) -> dict[str, Any]:
        last_error: Exception | None = None
        for attempt in range(12):
            raw = self._safari_do_javascript(js)
            if not raw.strip():
                last_error = ValueError("Safari returned empty JavaScript payload")
                time.sleep(min(1.0, 0.15 * (attempt + 1)))
                continue
            try:
                return json.loads(raw)
            except json.JSONDecodeError as exc:
                last_error = exc
                time.sleep(min(1.0, 0.15 * (attempt + 1)))
        if last_error is not None:
            raise last_error
        raise RuntimeError("Could not decode browser JSON payload")

    def _wait_for_js(self, js: str, *, timeout_seconds: float = 20.0, interval_seconds: float = 0.5) -> dict[str, Any]:
        deadline = time.time() + timeout_seconds
        last: dict[str, Any] = {"success": False}
        while time.time() < deadline:
            last = self._browser_json(js)
            if last.get("success"):
                return last
            time.sleep(interval_seconds)
        return last

    def _ensure_cookie_consent(self) -> None:
        payload = dict(COOKIE_CONSENT_PAYLOAD)
        payload["timestamp"] = int(time.time() * 1000)
        js = f"""
(() => {{
  try {{
    localStorage.setItem('cookie-consent', JSON.stringify({json.dumps(payload)}));
  }} catch (e) {{}}
  const btn = Array.from(document.querySelectorAll('button')).find((b) => /accept all/i.test((b.innerText || '').trim()));
  if (btn) btn.click();
  return JSON.stringify({{
    success: true,
    href: location.href,
    consent_visible: Array.from(document.querySelectorAll('button')).some((b) => /accept all/i.test((b.innerText || '').trim()))
  }});
}})()
"""
        try:
            self._browser_json(js)
            self._wait_for_js(
                """
JSON.stringify({
  success: !Array.from(document.querySelectorAll('button')).some((b) => /accept all/i.test((b.innerText || '').trim()))
})
""",
                timeout_seconds=8.0,
                interval_seconds=0.25,
            )
        except Exception:
            pass

    def _capture(self, label: str) -> dict[str, Any]:
        path = self.module_dir / f"{label}.png"
        return capture_front_window(path, owner_name="Safari")

    # ------------------------------------------------------------------
    # Account / auth helpers
    # ------------------------------------------------------------------
    def _random_email(self, tag: str) -> str:
        suffix = uuid.uuid4().hex[:10]
        return f"codex.qa.{tag}.{suffix}@example.com"

    def _random_password(self) -> str:
        chars = string.ascii_letters + string.digits
        return "Concentric!" + "".join(random.choice(chars) for _ in range(10))

    def _register_account(self, tag: str, *, full_name: str) -> Account:
        account = Account(
            email=self._random_email(tag),
            password=self._random_password(),
            full_name=full_name,
        )
        resp = self.session.post(
            f"{API_BASE}/auth/register",
            json={
                "email": account.email,
                "password": account.password,
                "full_name": account.full_name,
            },
            timeout=30,
        )
        if resp.status_code != 201:
            raise RuntimeError(f"Account registration failed: {resp.status_code} {resp.text[:300]}")
        return account

    def _login_api(self, account: Account) -> dict[str, str]:
        resp = self.session.post(
            f"{API_BASE}/auth/login",
            json={"email": account.email, "password": account.password},
            timeout=30,
        )
        if resp.status_code != 200:
            raise RuntimeError(f"API login failed: {resp.status_code} {resp.text[:300]}")
        payload = resp.json()
        return {
            "access_token": str(payload["access_token"]),
            "refresh_token": str(payload["refresh_token"]),
        }

    def _headers(self, tokens: dict[str, str]) -> dict[str, str]:
        return {"Authorization": f"Bearer {tokens['access_token']}"}

    def _page_state(self) -> dict[str, Any]:
        return self._browser_json(
            """
JSON.stringify({
  success: true,
  href: location.href,
  email_input: !!document.querySelector('input[name="email"]'),
  password_input: !!document.querySelector('input[name="password"]'),
  sign_in_button: Array.from(document.querySelectorAll('button')).some((b) => /sign in/i.test((b.innerText || '').trim())),
  logout_button: Array.from(document.querySelectorAll('button')).some((b) => /logout/i.test((b.innerText || '').trim())),
  guest_mode: document.body.innerText.includes('Guest Mode'),
  my_profile: document.body.innerText.includes('My Profile'),
  body: document.body.innerText.slice(0, 1200)
})
"""
        )

    def _clear_browser_auth(self) -> None:
        self._browser_json(
            """
JSON.stringify((() => {
  try {
    localStorage.removeItem('qa_platform_token');
    localStorage.removeItem('qa_platform_refresh_token');
    sessionStorage.clear();
  } catch (e) {}
  return {success: true};
})())
"""
        )

    def _logout_browser_session(self) -> dict[str, Any]:
        self._browser_json(
            """
JSON.stringify((() => {
  const clickLogout = () => {
    const button = Array.from(document.querySelectorAll('button')).find((b) => /logout/i.test((b.innerText || '').trim()));
    if (!button) return false;
    button.click();
    button.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
    const key = Object.keys(button).find((k) => k.startsWith('__reactProps'));
    if (key && typeof button[key]?.onClick === 'function') {
      button[key].onClick({preventDefault() {}, stopPropagation() {}, target: button, currentTarget: button});
    }
    return true;
  };
  clickLogout();
  try {
    localStorage.removeItem('qa_platform_token');
    localStorage.removeItem('qa_platform_refresh_token');
    sessionStorage.clear();
  } catch (e) {}
  setTimeout(() => { window.location.href = 'https://www.learnaqa.info/dashboard/'; }, 150);
  return {success: true};
})())
"""
        )
        return self._wait_for_js(
            """
JSON.stringify({
  success: document.body.innerText.includes('Guest Mode')
    && Array.from(document.querySelectorAll('button')).some((b) => /sign in/i.test((b.innerText || '').trim())),
  href: location.href,
  body: document.body.innerText.slice(0, 1200)
})
""",
            timeout_seconds=18.0,
            interval_seconds=0.25,
        )

    def _login_safari(self, account: Account) -> dict[str, Any]:
        last_state: dict[str, Any] = {"success": False, "reason": "uninitialized"}
        for _ in range(3):
            nav = self._safari_navigate(f"{SITE_BASE}/dashboard/")
            if not nav.get("success"):
                last_state = {"success": False, "reason": "dashboard_bootstrap_failed", "nav": nav}
                continue
            self._ensure_cookie_consent()
            state = self._page_state()
            last_state = state

            # If Safari already holds the exact account for this run, reuse it.
            if state.get("my_profile") and account.full_name in str(state.get("body", "")):
                return {
                    "success": True,
                    "href": str(state.get("href", "")),
                    "body": str(state.get("body", "")),
                }

            # Drive Safari into a clean guest state so the browser session
            # matches the fresh API account created for this run.
            if state.get("logout_button") or state.get("my_profile"):
                state = self._logout_browser_session()
                if not state.get("success"):
                    self._clear_browser_auth()
                    nav = self._safari_navigate(f"{SITE_BASE}/dashboard/")
                    if not nav.get("success"):
                        last_state = {"success": False, "reason": "dashboard_refresh_failed", "nav": nav}
                        continue
                    self._ensure_cookie_consent()
                    state = self._page_state()
                last_state = state

            if not state.get("email_input") or not state.get("password_input"):
                nav = self._safari_navigate(f"{SITE_BASE}/login/")
                if nav.get("success"):
                    self._ensure_cookie_consent()
                    state = self._wait_for_js(
                        """
JSON.stringify({
  success: !!document.querySelector('input[name="email"]') && !!document.querySelector('input[name="password"]'),
  email_input: !!document.querySelector('input[name="email"]'),
  password_input: !!document.querySelector('input[name="password"]'),
  href: location.href,
  body: document.body.innerText.slice(0, 1000)
})
""",
                        timeout_seconds=15.0,
                        interval_seconds=0.25,
                    )
                    last_state = state
                if not state.get("success"):
                    self._browser_json(
                        """
JSON.stringify((() => {
  const button = Array.from(document.querySelectorAll('button')).find((b) => /sign in/i.test((b.innerText || '').trim()));
  if (button) button.click();
  return {success: !!button, href: location.href};
})())
"""
                    )
                    state = self._wait_for_js(
                        """
JSON.stringify({
  success: !!document.querySelector('input[name="email"]') && !!document.querySelector('input[name="password"]'),
  email_input: !!document.querySelector('input[name="email"]'),
  password_input: !!document.querySelector('input[name="password"]'),
  href: location.href,
  body: document.body.innerText.slice(0, 1000)
})
""",
                        timeout_seconds=8.0,
                        interval_seconds=0.25,
                    )
                    last_state = state

            if not state.get("email_input") or not state.get("password_input"):
                time.sleep(0.5)
                continue

            js = f"""
(() => {{
  const setValue = (selector, value) => {{
    const el = document.querySelector(selector);
    if (!el) return false;
    const proto = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
    proto.call(el, value);
    el.dispatchEvent(new Event('input', {{bubbles: true}}));
    el.dispatchEvent(new Event('change', {{bubbles: true}}));
    return true;
  }};
  const emailOk = setValue('input[name="email"]', {json.dumps(account.email)});
  const passwordOk = setValue('input[name="password"]', {json.dumps(account.password)});
  const button = Array.from(document.querySelectorAll('button')).find((b) => /sign in/i.test((b.innerText || '').trim()));
  if (button) {{
    button.click();
  }}
  const form = document.querySelector('form');
  if (form && typeof form.requestSubmit === 'function') {{
    form.requestSubmit();
  }}
  return JSON.stringify({{
    success: emailOk && passwordOk && !!button,
    href: location.href
  }});
}})()
"""
            result = self._browser_json(js)
            last_state = result
            if not result.get("success"):
                time.sleep(0.5)
                continue

            post = self._wait_for_js(
                """
JSON.stringify({
  success: /dashboard/.test(location.pathname) && document.body.innerText.includes('My Profile'),
  href: location.href,
  body: document.body.innerText.slice(0, 500)
})
""",
                timeout_seconds=20.0,
            )
            last_state = post
            if not post.get("success"):
                time.sleep(0.5)
                continue
            self._ensure_cookie_consent()
            return post

        try:
            tokens = self._login_api(account)
            injected = self._browser_json(
                f"""
(() => {{
  try {{
    localStorage.setItem('qa_platform_token', {json.dumps(tokens["access_token"])});
    localStorage.setItem('qa_platform_refresh_token', {json.dumps(tokens["refresh_token"])});
  }} catch (e) {{
    return JSON.stringify({{success: false, error: String(e)}});
  }}
  window.location.href = {json.dumps(f"{SITE_BASE}/dashboard/")};
  return JSON.stringify({{success: true}});
}})()
"""
            )
            post = self._wait_for_js(
                f"""
JSON.stringify({{
  success: /dashboard/.test(location.pathname)
    && document.body.innerText.includes('My Profile')
    && document.body.innerText.includes({json.dumps(account.full_name)}),
  href: location.href,
  body: document.body.innerText.slice(0, 500)
}})
""",
                timeout_seconds=20.0,
                interval_seconds=0.25,
            )
            last_state = {
                "success": bool(post.get("success")),
                "reason": "token_injection_fallback",
                "injected": injected,
                "post": post,
            }
            if post.get("success"):
                self._ensure_cookie_consent()
                return post
        except Exception as exc:
            last_state = {
                "success": False,
                "reason": "token_injection_exception",
                "error": str(exc),
            }

        raise RuntimeError(f"Could not complete UI login flow: {last_state}")

    # ------------------------------------------------------------------
    # Workbook parsing
    # ------------------------------------------------------------------
    def _parse_xlsx_rows(self, path: Path) -> list[dict[str, str]]:
        with zipfile.ZipFile(path) as archive:
            sheet = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
            rows: list[dict[str, str]] = []
            headers: list[str] = []
            for row in sheet.findall(".//a:row", XLSX_NS):
                cells: dict[str, str] = {}
                for cell in row.findall("a:c", XLSX_NS):
                    ref = str(cell.get("r") or "")
                    column = "".join(ch for ch in ref if ch.isalpha())
                    value = self._cell_text(cell)
                    cells[column] = value
                if not headers:
                    for column in sorted(cells.keys(), key=self._excel_col_to_num):
                        headers.append(cells[column])
                    continue
                row_payload: dict[str, str] = {}
                for column in sorted(cells.keys(), key=self._excel_col_to_num):
                    idx = self._excel_col_to_num(column) - 1
                    if idx < len(headers):
                        row_payload[headers[idx]] = cells[column]
                if row_payload:
                    rows.append(row_payload)
            return rows

    def _cell_text(self, cell: ET.Element) -> str:
        inline = cell.find("a:is", XLSX_NS)
        if inline is not None:
            return "".join(text.text or "" for text in inline.iterfind(".//a:t", XLSX_NS))
        value = cell.find("a:v", XLSX_NS)
        return value.text or "" if value is not None else ""

    def _excel_col_to_num(self, col: str) -> int:
        total = 0
        for char in col:
            total = total * 26 + (ord(char.upper()) - 64)
        return total

    # ------------------------------------------------------------------
    # Module solvers
    # ------------------------------------------------------------------
    def _solve_drag_and_drop(self) -> dict[str, Any]:
        self._safari_navigate(f"{SITE_BASE}/drag-and-drop/")
        self._ensure_cookie_consent()
        start = """
(() => {
  window.__qaDragDone = false;
  window.__qaDragStatus = 'started';
  const zone = document.getElementById('drop-zone');
  const items = Array.from(document.querySelectorAll('[draggable="true"]'));
  const zoneKey = Object.keys(zone).find((k) => k.startsWith('__reactProps'));
  let idx = 0;
  function step() {
    if (idx >= items.length) {
      window.__qaDragDone = true;
      window.__qaDragStatus = document.body.innerText.match(/Items moved:\\s*\\d+\\s*\\/\\s*\\d+/)?.[0] || 'done';
      return;
    }
    const el = items[idx++];
    const key = Object.keys(el).find((k) => k.startsWith('__reactProps'));
    const dragEvent = {
      dataTransfer: {effectAllowed: '', setData() {}, getData() { return ''; }},
      preventDefault() {},
      stopPropagation() {},
      target: el,
      currentTarget: el,
    };
    el[key].onDragStart(dragEvent);
    setTimeout(() => {
      zone[zoneKey].onDrop({preventDefault() {}, stopPropagation() {}, target: zone, currentTarget: zone});
      setTimeout(step, 150);
    }, 150);
  }
  step();
  return JSON.stringify({success: true});
})()
"""
        self._browser_json(start)
        result = self._wait_for_js(
            """
JSON.stringify({
  success: window.__qaDragDone === true && /Items moved: 4 \\/ 4/.test(document.body.innerText),
  status: window.__qaDragStatus || '',
  body: document.body.innerText.slice(0, 800)
})
""",
            timeout_seconds=20.0,
        )
        result["screenshot"] = self._capture("drag_and_drop")
        return result

    def _solve_dynamic_elements(self) -> dict[str, Any]:
        self._safari_navigate(f"{SITE_BASE}/dynamic-elements/")
        self._ensure_cookie_consent()
        ready = self._wait_for_js(
            """
JSON.stringify({
  success: !!document.getElementById('trigger-delayed')
    && !!document.getElementById('load-ajax-data')
    && !!document.getElementById('reveal-hidden')
    && !!document.getElementById('generate-content'),
  body: document.body.innerText.slice(0, 1200)
})
""",
            timeout_seconds=10.0,
            interval_seconds=0.25,
        )
        delayed_click = self._browser_json(
            """
(() => {
  const button = document.getElementById('trigger-delayed');
  button?.click();
  return JSON.stringify({success: !!button});
})()
"""
        )
        delayed = self._wait_for_js(
            """
JSON.stringify({
  success: /Element appeared after 5 second delay!/i.test(document.body.innerText),
  body: document.body.innerText.slice(0, 1800)
})
""",
            timeout_seconds=8.0,
            interval_seconds=0.25,
        )

        ajax_click = self._browser_json(
            """
(() => {
  const button = document.getElementById('load-ajax-data');
  button?.click();
  return JSON.stringify({success: !!button});
})()
"""
        )
        ajax = self._wait_for_js(
            """
JSON.stringify({
  success: /Dynamic Item 5/i.test(document.body.innerText) && /loaded via AJAX/i.test(document.body.innerText),
  dynamic_items: (document.body.innerText.match(/Dynamic Item \\d+/g) || []).length,
  body: document.body.innerText.slice(0, 2200)
})
""",
            timeout_seconds=10.0,
            interval_seconds=0.25,
        )

        hidden_click = self._browser_json(
            """
(() => {
  const button = document.getElementById('reveal-hidden');
  button?.click();
  return JSON.stringify({success: !!button});
})()
"""
        )
        hidden = self._wait_for_js(
            """
JSON.stringify({
  success: /Hidden element revealed!/i.test(document.body.innerText) && /Hide Elements/i.test(document.body.innerText),
  body: document.body.innerText.slice(0, 2400)
})
""",
            timeout_seconds=6.0,
            interval_seconds=0.25,
        )

        generated_click = self._browser_json(
            """
(() => {
  const button = document.getElementById('generate-content');
  button?.click();
  return JSON.stringify({success: !!button});
})()
"""
        )
        generated = self._wait_for_js(
            """
JSON.stringify({
  success: /(This text changes each time!|Timestamp:|Random value:)/i.test(document.body.innerText),
  body: document.body.innerText.slice(0, 2600)
})
""",
            timeout_seconds=6.0,
            interval_seconds=0.25,
        )

        lazy_scroll = self._browser_json(
            """
(() => {
  const anchor = document.querySelector('[data-id="3"]');
  anchor?.scrollIntoView({block: 'center'});
  const container = anchor?.parentElement;
  if (!container) {
    return JSON.stringify({success: false, reason: 'no_lazy_container'});
  }
  window.__qaLazyDone = false;
  let steps = 0;
  const tick = () => {
    container.scrollTop = Math.min(container.scrollHeight, container.scrollTop + 260);
    container.dispatchEvent(new Event('scroll', {bubbles: true}));
    steps += 1;
    if (steps < 12 && container.scrollTop + container.clientHeight < container.scrollHeight - 4) {
      setTimeout(tick, 450);
      return;
    }
    setTimeout(() => {
      container.scrollTop = container.scrollHeight;
      container.dispatchEvent(new Event('scroll', {bubbles: true}));
      window.__qaLazyDone = true;
    }, 700);
  };
  setTimeout(tick, 500);
  return JSON.stringify({success: true, scroll_height: container.scrollHeight});
})()
"""
        )
        lazy = self._wait_for_js(
            """
JSON.stringify({
  success: window.__qaLazyDone === true && document.querySelectorAll('img').length >= 10,
  image_count: document.querySelectorAll('img').length,
  images: Array.from(document.querySelectorAll('img')).map((img) => img.alt || '').slice(0, 12),
  body: document.body.innerText.slice(0, 2800)
})
""",
            timeout_seconds=15.0,
            interval_seconds=0.5,
        )

        infinite_scroll = self._browser_json(
            """
(() => {
  const container = document.getElementById('infinite-scroll-container');
  if (!container) {
    return JSON.stringify({success: false, reason: 'no_infinite_container'});
  }
  window.__qaInfiniteDone = false;
  let ticks = 0;
  const step = () => {
    container.scrollTop = container.scrollHeight;
    container.dispatchEvent(new Event('scroll', {bubbles: true}));
    window.scrollTo(0, document.body.scrollHeight);
    ticks += 1;
    if (ticks < 6) {
      setTimeout(step, 700);
      return;
    }
    window.__qaInfiniteDone = true;
  };
  step();
  return JSON.stringify({success: true});
})()
"""
        )
        infinite = self._wait_for_js(
            """
JSON.stringify({
  success: window.__qaInfiniteDone === true && (document.body.innerText.match(/Item \\d+/g) || []).length >= 15,
  item_count: (document.body.innerText.match(/Item \\d+/g) || []).length,
  body: document.body.innerText.slice(-1800)
})
""",
            timeout_seconds=12.0,
            interval_seconds=0.5,
        )

        result = {
            "success": all(
                [
                    ready.get("success"),
                    delayed_click.get("success"),
                    delayed.get("success"),
                    ajax_click.get("success"),
                    ajax.get("success"),
                    hidden_click.get("success"),
                    hidden.get("success"),
                    generated_click.get("success"),
                    generated.get("success"),
                    lazy_scroll.get("success"),
                    lazy.get("success"),
                    infinite_scroll.get("success"),
                    infinite.get("success"),
                ]
            ),
            "details": {
                "ready": ready,
                "delayed_click": delayed_click,
                "delayed": delayed,
                "ajax_click": ajax_click,
                "ajax": ajax,
                "hidden_click": hidden_click,
                "hidden": hidden,
                "generated_click": generated_click,
                "generated": generated,
                "lazy_scroll": lazy_scroll,
                "lazy": lazy,
                "infinite_scroll": infinite_scroll,
                "infinite": infinite,
            },
            "body": infinite.get("body") or lazy.get("body") or generated.get("body") or ajax.get("body") or delayed.get("body") or "",
        }
        result["screenshot"] = self._capture("dynamic_elements")
        return result

    def _solve_keyboard_mouse(self) -> dict[str, Any]:
        self._safari_navigate(f"{SITE_BASE}/keyboard-mouse-events/")
        self._ensure_cookie_consent()
        body_snapshot_js = """
JSON.stringify({
  success: true,
  body: document.body.innerText
})
"""

        def wait_body_contains(needle: str, *, timeout_seconds: float = 8.0) -> dict[str, Any]:
            deadline = time.time() + timeout_seconds
            last: dict[str, Any] = {"success": False, "body": ""}
            while time.time() < deadline:
                last = self._browser_json(body_snapshot_js)
                body = str(last.get("body", ""))
                if needle in body:
                    return {"success": True, "body": body}
                time.sleep(0.25)
            return {"success": False, "body": str(last.get("body", ""))}

        page_ready = self._wait_for_js(
            """
JSON.stringify({
  success: document.body.innerText.includes('Keyboard & Mouse Events')
    && !!document.getElementById('start-clear-scenario')
    && !!document.getElementById('start-dialog-scenario')
    && !!document.getElementById('editable-text')
    && !!document.getElementById('hover-card'),
  body: document.body.innerText.slice(0, 1200)
})
""",
            timeout_seconds=10.0,
            interval_seconds=0.25,
        )
        if not page_ready.get("success"):
            return page_ready

        self._browser_json(
            """
JSON.stringify((() => {
  document.getElementById('start-clear-scenario')?.click();
  const input = document.getElementById('search-field');
  if (input) {
    const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
    setter.call(input, '');
    input.dispatchEvent(new Event('input', {bubbles: true}));
    input.dispatchEvent(new Event('change', {bubbles: true}));
    input.dispatchEvent(new KeyboardEvent('keydown', {key: 'Backspace', bubbles: true}));
  }
  return {success: true};
})())
"""
        )
        clear_done = wait_body_contains("Clear Field\n✓")

        self._browser_json(
            """
JSON.stringify((() => {
  document.getElementById('start-dialog-scenario')?.click();
  return {success: true};
})())
"""
        )
        time.sleep(0.4)
        self._browser_json(
            """
JSON.stringify((() => {
  document.dispatchEvent(new KeyboardEvent('keydown', {key: 'Enter', bubbles: true}));
  return {success: true};
})())
"""
        )
        time.sleep(0.5)
        self._browser_json(
            """
JSON.stringify((() => {
  document.dispatchEvent(new KeyboardEvent('keydown', {key: 'Escape', bubbles: true}));
  return {success: true};
})())
"""
        )
        dialog_done = wait_body_contains("Dialog Flow\n✓")

        self._browser_json(
            """
JSON.stringify((() => {
  const edit = document.getElementById('editable-text');
  if (!edit) return {success: false};
  edit.dispatchEvent(new MouseEvent('dblclick', {bubbles: true, cancelable: true}));
  const key = Object.keys(edit).find((k) => k.startsWith('__reactProps'));
  if (key && typeof edit[key]?.onDoubleClick === 'function') {
    edit[key].onDoubleClick({target: edit, currentTarget: edit});
  }
  return {success: true};
})())
"""
        )
        double_done = wait_body_contains("Double-click\n✓")

        self._browser_json(
            """
JSON.stringify((() => {
  const hover = document.getElementById('hover-card');
  if (!hover) return {success: false};
  hover.dispatchEvent(new MouseEvent('mouseenter', {bubbles: true, cancelable: true}));
  hover.dispatchEvent(new MouseEvent('mouseover', {bubbles: true, cancelable: true}));
  const key = Object.keys(hover).find((k) => k.startsWith('__reactProps'));
  if (key && typeof hover[key]?.onMouseEnter === 'function') {
    hover[key].onMouseEnter({target: hover, currentTarget: hover});
  }
  return {success: true};
})())
"""
        )
        hover_done = wait_body_contains("Hover\n✓", timeout_seconds=10.0)

        body = str(hover_done.get("body", ""))
        result = {
            "success": all(
                [
                    clear_done.get("success"),
                    dialog_done.get("success"),
                    double_done.get("success"),
                    hover_done.get("success"),
                ]
            ),
            "body": body,
            "clear_done": clear_done.get("success"),
            "dialog_done": dialog_done.get("success"),
            "double_done": double_done.get("success"),
            "hover_done": hover_done.get("success"),
        }
        progress_start = body.find("Action Log & Progress")
        progress_end = body.find("Keyboard Keys:")
        if progress_start != -1 and progress_end != -1 and progress_end > progress_start:
            result["progress"] = body[progress_start:progress_end]
        result["screenshot"] = self._capture("keyboard_mouse")
        return result

    def _solve_shadow_dom(self) -> dict[str, Any]:
        self._safari_navigate(f"{SITE_BASE}/shadow-dom/")
        self._ensure_cookie_consent()
        start = """
(() => {
  window.__qaShadowDone = false;
  document.getElementById('create-basic-shadow')?.click();
  setTimeout(() => {
    const host = document.getElementById('shadow-host-element');
    const button = host?.shadowRoot?.querySelector('#shadow-btn');
    if (button) {
      button.click();
    }
    setTimeout(() => { window.__qaShadowDone = true; }, 2200);
  }, 300);
  return JSON.stringify({success: true});
})()
"""
        self._browser_json(start)
        result = self._wait_for_js(
            """
JSON.stringify({
  success: window.__qaShadowDone === true,
  body: document.body.innerText
})
""",
            timeout_seconds=15.0,
        )
        body = str(result.get("body", ""))
        result["success"] = (
            result.get("success")
            and "Basic Shadow DOM\n✓ Completed" in body
            and "Scenario completed(Basic Shadow DOM)" in body
        )
        result["body"] = body[:1800]
        result["screenshot"] = self._capture("shadow_dom")
        return result

    def _solve_iframe_windows(self) -> dict[str, Any]:
        self._safari_navigate(f"{SITE_BASE}/iframe-windows/")
        self._ensure_cookie_consent()
        page_ready = self._wait_for_js(
            """
JSON.stringify({
  success: document.body.innerText.includes('iFrames & Multiple Windows')
    && !!document.getElementById('basic-iframe')
    && !!document.getElementById('send-iframe-message'),
  body: document.body.innerText.slice(0, 1200)
})
""",
            timeout_seconds=12.0,
            interval_seconds=0.25,
        )
        if not page_ready.get("success"):
            return page_ready

        setup = """
(() => {
  window.__qaPopupCalls = [];
  window.open = (url, name, features) => {
    const stub = {
      __url: url,
      __name: name,
      __features: features,
      closed: false,
      focus() { this.focused = true; },
      close() { this.closed = true; },
      location: { href: url },
    };
    window.__qaPopupCalls.push({url, name, features});
    return stub;
  };
  window.__lastAlert = '';
  window.__lastConfirm = '';
  window.__lastPrompt = '';
  window.__formAlert = '';
  window.alert = (msg) => { window.__lastAlert = String(msg); };
  window.confirm = (msg) => { window.__lastConfirm = String(msg); return true; };
  window.prompt = (msg) => { window.__lastPrompt = String(msg); return 'Codex'; };
  return JSON.stringify({success: true});
})()
"""
        self._browser_json(setup)

        basic_parent_start = self._browser_json(
            """
JSON.stringify({
  success: !!document.getElementById('send-iframe-message') && !!document.getElementById('basic-iframe')
})
""",
        )
        if not basic_parent_start.get("success"):
            return basic_parent_start

        self._browser_json(
            """
JSON.stringify((() => {
  document.getElementById('send-iframe-message')?.click();
  return {success: true};
})())
"""
        )
        basic_parent = self._wait_for_js(
            """
JSON.stringify({
  success: /Message from parent:/i.test(document.getElementById('basic-iframe')?.contentDocument?.body?.innerText || ''),
  frame_body: document.getElementById('basic-iframe')?.contentDocument?.body?.innerText || ''
})
""",
            timeout_seconds=8.0,
            interval_seconds=0.25,
        )

        self._browser_json(
            """
JSON.stringify((() => {
  document.getElementById('basic-iframe')?.contentDocument?.querySelector('button')?.click();
  return {success: true};
})())
"""
        )
        basic_child = self._wait_for_js(
            """
JSON.stringify({
  success: /basic iframe/i.test(document.getElementById('iframe-message-display')?.innerText || ''),
  iframe_message: document.getElementById('iframe-message-display')?.innerText || ''
})
""",
            timeout_seconds=8.0,
            interval_seconds=0.25,
        )

        self._browser_json(
            """
JSON.stringify((() => {
  const tab = Array.from(document.querySelectorAll('button')).find((b) => (b.innerText || '').trim() === 'Form');
  if (tab) tab.click();
  return {success: !!tab};
})())
"""
        )
        form_ready = self._wait_for_js(
            """
JSON.stringify({
  success: !!document.getElementById('basic-iframe')?.contentDocument?.querySelector('#iframe-name')
    && !!document.getElementById('basic-iframe')?.contentDocument?.querySelector('#iframe-email')
    && !!document.getElementById('basic-iframe')?.contentDocument?.querySelector('#iframe-comment'),
  frame_body: document.getElementById('basic-iframe')?.contentDocument?.body?.innerText || ''
})
""",
            timeout_seconds=8.0,
            interval_seconds=0.25,
        )
        self._browser_json(
            """
JSON.stringify((() => {
  const formDoc = document.getElementById('basic-iframe')?.contentDocument;
  if (!formDoc) return {success: false};
  formDoc.defaultView.alert = (msg) => { window.__formAlert = String(msg); };
  const setValue = (selector, value) => {
    const el = formDoc.querySelector(selector);
    if (!el) return false;
    const proto = Object.getOwnPropertyDescriptor(
      el.tagName === 'TEXTAREA' ? window.HTMLTextAreaElement.prototype : window.HTMLInputElement.prototype,
      'value'
    ).set;
    proto.call(el, value);
    el.dispatchEvent(new Event('input', {bubbles: true}));
    el.dispatchEvent(new Event('change', {bubbles: true}));
    return true;
  };
  const ok = setValue('#iframe-name', 'Codex')
    && setValue('#iframe-email', 'codex@example.com')
    && setValue('#iframe-comment', 'Hello from automation');
  formDoc.querySelector('button')?.click();
  return {success: ok};
})())
"""
        )
        form_submit = self._wait_for_js(
            """
JSON.stringify({
  success: window.__formAlert === 'Form submitted from iframe!'
    && /Form submitted with name: Codex/i.test(document.getElementById('iframe-message-display')?.innerText || ''),
  iframe_message: document.getElementById('iframe-message-display')?.innerText || '',
  form_alert: window.__formAlert || ''
})
""",
            timeout_seconds=8.0,
            interval_seconds=0.25,
        )

        self._browser_json(
            """
JSON.stringify((() => {
  const tab = Array.from(document.querySelectorAll('button')).find((b) => (b.innerText || '').trim() === 'Nested');
  if (tab) tab.click();
  return {success: !!tab};
})())
"""
        )
        nested_loaded = self._wait_for_js(
            """
JSON.stringify({
  success: /Nested iFrame Container/i.test(document.getElementById('basic-iframe')?.contentDocument?.body?.innerText || '')
    && !!document.getElementById('basic-iframe')?.contentDocument?.querySelector('iframe'),
  frame_body: document.getElementById('basic-iframe')?.contentDocument?.body?.innerText || ''
})
""",
            timeout_seconds=8.0,
            interval_seconds=0.25,
        )

        self._browser_json(
            """
JSON.stringify((() => {
  document.getElementById('open-basic-popup')?.click();
  document.getElementById('open-small-popup')?.click();
  document.getElementById('open-new-tab')?.click();
  return {success: true};
})())
"""
        )
        popups = self._wait_for_js(
            """
JSON.stringify({
  success: Array.isArray(window.__qaPopupCalls) && window.__qaPopupCalls.length === 3
    && document.body.innerText.includes('Open Windows/Tabs:'),
  popup_calls: window.__qaPopupCalls || [],
  body: document.body.innerText.slice(0, 2200)
})
""",
            timeout_seconds=6.0,
            interval_seconds=0.25,
        )

        self._browser_json(
            """
JSON.stringify((() => {
  document.getElementById('trigger-alert')?.click();
  document.getElementById('trigger-confirm')?.click();
  document.getElementById('trigger-prompt')?.click();
  return {success: true};
})())
"""
        )
        dialogs = self._wait_for_js(
            """
JSON.stringify({
  success: window.__lastConfirm === 'Do you want to proceed?'
    && window.__lastPrompt === 'Please enter your name:'
    && /Prompt result: Codex/i.test(document.body.innerText),
  last_alert: window.__lastAlert || '',
  last_confirm: window.__lastConfirm || '',
  last_prompt: window.__lastPrompt || '',
  body: document.body.innerText.slice(0, 2200)
})
""",
            timeout_seconds=6.0,
            interval_seconds=0.25,
        )

        self._browser_json(
            """
JSON.stringify((() => {
  document.getElementById('open-modal')?.click();
  return {success: true};
})())
"""
        )
        modal_ready = self._wait_for_js(
            """
JSON.stringify({
  success: !!document.getElementById('modal-action'),
  body: document.body.innerText.slice(0, 2400)
})
""",
            timeout_seconds=6.0,
            interval_seconds=0.25,
        )
        self._browser_json(
            """
JSON.stringify((() => {
  document.getElementById('modal-action')?.click();
  return {success: true};
})())
"""
        )
        modal = self._wait_for_js(
            """
JSON.stringify({
  success: window.__lastAlert === 'Modal action triggered!',
  last_alert: window.__lastAlert || '',
  body: document.body.innerText.slice(0, 2400)
})
""",
            timeout_seconds=6.0,
            interval_seconds=0.25,
        )

        result = {
            "success": all(
                [
                    basic_parent.get("success"),
                    basic_child.get("success"),
                    form_ready.get("success"),
                    form_submit.get("success"),
                    nested_loaded.get("success"),
                    popups.get("success"),
                    dialogs.get("success"),
                    modal_ready.get("success"),
                    modal.get("success"),
                ]
            ),
            "basic_parent": basic_parent,
            "basic_child": basic_child,
            "form_ready": form_ready,
            "form_submit": form_submit,
            "nested_loaded": nested_loaded,
            "popups": popups,
            "dialogs": dialogs,
            "modal_ready": modal_ready,
            "modal": modal,
        }
        result["screenshot"] = self._capture("iframe_windows")
        return result

    # ------------------------------------------------------------------
    # Auth-gated flows
    # ------------------------------------------------------------------
    def _solve_file_operations(self) -> dict[str, Any]:
        assert self.primary_account is not None
        self._safari_navigate(f"{SITE_BASE}/file-operations/")
        self._ensure_cookie_consent()

        template_path = self.api_dir / "template_data.xlsx"
        processed_path = self.api_dir / "processed_template.xlsx"

        template_resp = self.session.get(
            f"{API_BASE}/files/template-excel",
            headers=self._headers(self.primary_tokens),
            timeout=30,
        )
        if template_resp.status_code != 200:
            raise RuntimeError(f"Template download failed: {template_resp.status_code}")
        template_path.write_bytes(template_resp.content)

        with template_path.open("rb") as handle:
            processed_resp = self.session.post(
                f"{API_BASE}/files/process-excel",
                headers=self._headers(self.primary_tokens),
                files={"file": ("template_data.xlsx", handle, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
                timeout=30,
            )
        if processed_resp.status_code != 200:
            raise RuntimeError(f"File processing failed: {processed_resp.status_code} {processed_resp.text[:300]}")
        processed_path.write_bytes(processed_resp.content)

        template_b64 = base64.b64encode(template_path.read_bytes()).decode("ascii")
        browser_upload = """
(() => {{
  window.__qaFileDone = false;
  window.__qaFileStatus = 'started';
  (async () => {{
    try {{
      const base64 = {template_b64};
      const bytes = Uint8Array.from(atob(base64), (c) => c.charCodeAt(0));
      const file = new File([bytes], 'template_data.xlsx', {{
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      }});
      const input = document.querySelector('input[type="file"]');
      const dt = new DataTransfer();
      dt.items.add(file);
      input.files = dt.files;
      input.dispatchEvent(new Event('change', {{bubbles: true}}));
      for (let i = 0; i < 30; i++) {{
        await new Promise((resolve) => setTimeout(resolve, 500));
        if (document.getElementById('download-processed')) {{
          window.__qaFileDone = true;
          window.__qaFileStatus = document.body.innerText;
          return;
        }}
      }}
      window.__qaFileDone = true;
      window.__qaFileStatus = document.body.innerText;
    }} catch (e) {{
      window.__qaFileDone = true;
      window.__qaFileStatus = 'error:' + e;
    }}
  }})();
  return JSON.stringify({{
    success: !!document.querySelector('input[type="file"]'),
    disabled: !!document.getElementById('download-template')?.disabled
  }});
}})()
""".format(template_b64=json.dumps(template_b64))
        browser_state = self._browser_json(browser_upload)
        browser_done = self._wait_for_js(
            """
JSON.stringify({
  success: window.__qaFileDone === true
    && document.getElementById('download-template')?.disabled === false
    && !!document.getElementById('download-processed')
    && /File processed successfully!/i.test(document.body.innerText),
  body: document.body.innerText
})
""",
            timeout_seconds=25.0,
        )

        template_rows = self._parse_xlsx_rows(template_path)
        processed_rows = self._parse_xlsx_rows(processed_path)
        first_template = template_rows[0]
        first_processed = processed_rows[0]
        verification = {
            "name_uppercase": first_processed.get("Name") == str(first_template.get("Name", "")).upper(),
            "score_x_1_1": math.isclose(
                float(first_processed.get("Score", "0")),
                round(float(first_template.get("Score", "0")) * 1.1, 1),
                rel_tol=0.0,
                abs_tol=0.01,
            ),
            "date_reformatted": first_processed.get("Date") == "15/01/2024",
            "processed_by": first_processed.get("ProcessedBy") == self.primary_account.email,
            "processed_flag": first_processed.get("Processed") == "Yes",
        }
        result = {
            "success": browser_state.get("success")
            and browser_done.get("success")
            and all(verification.values()),
            "browser": {
                "initial": browser_state,
                "final": browser_done,
            },
            "api": {
                "template_path": str(template_path),
                "processed_path": str(processed_path),
                "template_rows": template_rows[:2],
                "processed_rows": processed_rows[:2],
            },
            "verification": verification,
            "screenshot": self._capture("file_operations"),
        }
        self.summary["file_operations_artifacts"] = {
            "template_path": str(template_path),
            "processed_path": str(processed_path),
        }
        return result

    def _run_capybara_api_tests(self) -> dict[str, Any]:
        assert self.primary_account is not None
        assert self.secondary_account is not None
        primary_headers = self._headers(self.primary_tokens)
        secondary_headers = self._headers(self.secondary_tokens)

        def req(method: str, path: str, *, headers: dict[str, str] | None = None, **kwargs: Any) -> requests.Response:
            return self.session.request(method, f"{API_BASE}{path}", headers=headers, timeout=30, **kwargs)

        pools = req("GET", "/spa/pools")
        pools_payload = pools.json()
        non_vip_pool = next(pool for pool in pools_payload["pools"] if not pool["is_vip"])

        primary_a = req(
            "POST",
            "/capybaras",
            headers=primary_headers,
            json={"name": f"Primary-{uuid.uuid4().hex[:6]}", "age": 3, "bio": "Primary automation capybara", "favorite_food": "orange"},
        )
        primary_b = req(
            "POST",
            "/capybaras",
            headers=primary_headers,
            json={"name": f"Friend-{uuid.uuid4().hex[:6]}", "age": 4, "bio": "Friend automation capybara", "favorite_food": "banana"},
        )
        if primary_a.status_code != 201 or primary_b.status_code != 201:
            raise RuntimeError("Could not create capybaras for API suite")
        cap_a = primary_a.json()
        cap_b = primary_b.json()

        mood_before = req("GET", f"/capybaras/{cap_a['id']}/mood")
        add_friend = req(
            "POST",
            f"/capybaras/{cap_a['id']}/friends",
            headers=primary_headers,
            json={"friend_id": cap_b["id"]},
        )
        duplicate_friend = req(
            "POST",
            f"/capybaras/{cap_a['id']}/friends",
            headers=primary_headers,
            json={"friend_id": cap_b["id"]},
        )
        friends_a = req("GET", f"/capybaras/{cap_a['id']}/friends")
        friends_b = req("GET", f"/capybaras/{cap_b['id']}/friends")
        enter_pool = req(
            "POST",
            f"/spa/pools/{non_vip_pool['id']}/enter",
            headers=primary_headers,
            json={"capybara_id": cap_a["id"]},
        )
        leave_pool = req(
            "POST",
            f"/spa/pools/{non_vip_pool['id']}/leave",
            headers=primary_headers,
            json={"capybara_id": cap_a["id"]},
        )
        feed_ok = req(
            "POST",
            f"/capybaras/{cap_a['id']}/feed",
            headers=primary_headers,
            json={"food": "orange"},
        )
        feed_cooldown = req(
            "POST",
            f"/capybaras/{cap_a['id']}/feed",
            headers=primary_headers,
            json={"food": "orange"},
        )
        unauthorized_patch = req(
            "PATCH",
            f"/capybaras/{cap_a['id']}",
            headers=secondary_headers,
            json={"name": "Hacked"},
        )
        invalid_uuid = req("GET", "/capybaras/not-a-uuid")

        result = {
            "success": all(
                [
                    pools.status_code == 200,
                    mood_before.status_code == 200,
                    add_friend.status_code in {200, 201},
                    duplicate_friend.status_code in {400, 409},
                    friends_a.status_code == 200,
                    friends_b.status_code == 200,
                    enter_pool.status_code == 200,
                    leave_pool.status_code == 200,
                    feed_ok.status_code == 200,
                    feed_cooldown.status_code == 400,
                    unauthorized_patch.status_code in {401, 403},
                    invalid_uuid.status_code in {404, 422},
                ]
            ),
            "capybara_a": cap_a,
            "capybara_b": cap_b,
            "checks": {
                "pools": pools_payload["pools"][:3],
                "mood_before": mood_before.json(),
                "add_friend": add_friend.json(),
                "duplicate_friend": {"status": duplicate_friend.status_code, "body": duplicate_friend.json()},
                "friends_a": friends_a.json(),
                "friends_b": friends_b.json(),
                "enter_pool": enter_pool.json(),
                "leave_pool": leave_pool.json(),
                "feed_ok": feed_ok.json(),
                "feed_cooldown": feed_cooldown.json(),
                "unauthorized_patch": {"status": unauthorized_patch.status_code, "body": unauthorized_patch.text[:400]},
                "invalid_uuid": {"status": invalid_uuid.status_code, "body": invalid_uuid.text[:400]},
            },
        }
        self.summary["api_tests"] = result
        self._save_json(self.api_dir / "capybara_api_suite.json", result)
        self.summary["self_healing_seed"] = {
            "capybara_a": cap_a,
            "capybara_b": cap_b,
        }
        return result

    # ------------------------------------------------------------------
    # Self-healing solver
    # ------------------------------------------------------------------
    def _select_capybara_in_self_healing(self, name: str) -> dict[str, Any]:
        attempts: list[dict[str, Any]] = []
        for _ in range(3):
            current = self._wait_for_js(
                f"""
JSON.stringify((() => {{
  const body = document.body.innerText || '';
  const currentName = (body.match(/Name:\\s*\\n([^\\n]+)/) || [])[1] || '';
  return {{
    success: true,
    current_name: currentName,
    body: body.slice(0, 1200)
  }};
}})())
""",
                timeout_seconds=2.0,
                interval_seconds=0.2,
            )
            if current.get("current_name") == name:
                return {
                    "success": True,
                    "already_selected": True,
                    "attempts": attempts,
                    "current": current,
                }

            opened = self._browser_json(
                """
(() => {
  const textish = (el) => (((el?.innerText) || '') + ' ' + ((el?.textContent) || '')).replace(/\\s+/g, ' ').trim();
  const open = Array.from(document.querySelectorAll('button[aria-haspopup="listbox"], button')).find((b) => {
    const text = textish(b);
    return /select capybara/i.test(text) || /\\(\\d+y\\)/.test(text) || /friend-|primary-/i.test(text);
  });
  open?.scrollIntoView({block: 'center'});
  open?.click();
  return JSON.stringify({
    success: !!open,
    opened: !!open,
    text: open ? textish(open) : ''
  });
})()
"""
            )
            expanded = self._wait_for_js(
                f"""
JSON.stringify((() => {{
  const textish = (el) => (((el?.innerText) || '') + ' ' + ((el?.textContent) || '')).replace(/\\s+/g, ' ').trim();
  const options = Array.from(document.querySelectorAll('[role="option"], button')).filter((el) => textish(el).includes({json.dumps(name)}));
  const expanded = Array.from(document.querySelectorAll('button[aria-haspopup="listbox"]')).some((b) => /friend-|primary-|select capybara/i.test(textish(b)) && b.getAttribute('aria-expanded') === 'true');
  return {{
    success: expanded || options.length > 0,
    expanded,
    option_count: options.length
  }};
}})())
""",
                timeout_seconds=6.0,
                interval_seconds=0.25,
            )
            selected = self._browser_json(
                f"""
(() => {{
  const textish = (el) => (((el?.innerText) || '') + ' ' + ((el?.textContent) || '')).replace(/\\s+/g, ' ').trim();
  const option = Array.from(document.querySelectorAll('[role="option"], button')).find((el) => textish(el).includes({json.dumps(name)}));
  option?.scrollIntoView({{block: 'center'}});
  option?.click();
  return JSON.stringify({{
    success: !!option,
    option_found: !!option,
    option_text: option ? textish(option) : ''
  }});
}})()
"""
            )
            settled = self._wait_for_js(
                f"""
JSON.stringify((() => {{
  const body = document.body.innerText || '';
  const currentName = (body.match(/Name:\\s*\\n([^\\n]+)/) || [])[1] || '';
  return {{
    success: currentName === {json.dumps(name)},
    current_name: currentName,
    body: body.slice(0, 1800)
  }};
}})())
""",
                timeout_seconds=8.0,
                interval_seconds=0.25,
            )
            attempts.append(
                {
                    "current": current,
                    "opened": opened,
                    "expanded": expanded,
                    "selected": selected,
                    "settled": settled,
                }
            )
            if settled.get("success"):
                return {
                    "success": True,
                    "attempts": attempts,
                }
        return {
            "success": False,
            "attempts": attempts,
        }

    def _set_self_healing_difficulty(self, label: str) -> dict[str, Any]:
        attempts: list[dict[str, Any]] = []
        target = json.dumps(label.lower())
        for _ in range(3):
            progress = self._self_healing_progress()
            if progress.get("difficulty", "").lower() == label.lower() and label.lower() in progress.get("tips_line", "").lower():
                return {
                    "success": True,
                    "attempts": attempts,
                    "state": progress,
                    "already_correct": True,
                }

            opened = self._browser_json(
                """
(() => {
  const textish = (el) => (((el?.innerText) || '') + ' ' + ((el?.textContent) || '')).replace(/\\s+/g, ' ').trim();
  const trigger = Array.from(document.querySelectorAll('button[aria-haspopup="listbox"]')).find((b) => {
    const text = textish(b);
    return /\\b(Easy|Medium|Hard)\\b/i.test(text) && !/Manual/i.test(text);
  });
  if (!trigger) {
    return JSON.stringify({success: false, reason: 'no_trigger'});
  }
  trigger.scrollIntoView({block: 'center'});
  trigger.click();
  return JSON.stringify({
    success: true,
    text: textish(trigger),
    expanded: trigger.getAttribute('aria-expanded')
  });
})()
"""
            )
            expanded = self._wait_for_js(
                """
JSON.stringify((() => {
  const textish = (el) => (((el?.innerText) || '') + ' ' + ((el?.textContent) || '')).replace(/\\s+/g, ' ').trim();
  return {
    success: Array.from(document.querySelectorAll('button[aria-haspopup="listbox"]')).some(
      (b) => /\\b(Easy|Medium|Hard)\\b/i.test(textish(b)) && !/Manual/i.test(textish(b)) && b.getAttribute('aria-expanded') === 'true'
    ),
    buttons: Array.from(document.querySelectorAll('button[aria-haspopup="listbox"]')).map((b) => ({
      text: textish(b),
      expanded: b.getAttribute('aria-expanded')
    }))
  };
})())
""",
                timeout_seconds=4.0,
                interval_seconds=0.2,
            )
            selected = self._browser_json(
                f"""
(() => {{
  const textish = (el) => (((el?.innerText) || '') + ' ' + ((el?.textContent) || '')).replace(/\\s+/g, ' ').trim();
  const option = Array.from(document.querySelectorAll('[role="option"]')).find(
    (el) => textish(el).toLowerCase().startsWith({target})
  );
  if (!option) {{
    return JSON.stringify({{
      success: false,
      reason: 'no_option',
      options: Array.from(document.querySelectorAll('[role="option"]')).map((el) => textish(el))
    }});
  }}
  option.scrollIntoView({{block: 'center'}});
  option.click();
  return JSON.stringify({{
    success: true,
    option_text: textish(option),
    selected: option.getAttribute('aria-selected')
  }});
}})()
"""
            )
            settled = self._wait_for_js(
                f"""
JSON.stringify((() => {{
  const body = document.body.innerText || '';
  const textish = (el) => (((el?.innerText) || '') + ' ' + ((el?.textContent) || '')).replace(/\\s+/g, ' ').trim();
  const trigger = Array.from(document.querySelectorAll('button[aria-haspopup="listbox"]')).find((b) => /\\b(Easy|Medium|Hard)\\b/i.test(textish(b)) && !/Manual/i.test(textish(b)));
  const difficulty = (textish(trigger).match(/Easy|Medium|Hard/i) || [''])[0];
  const tips = (body.match(/Showing tips for [^\\n]+/) || [])[0] || '';
  return {{
    success: difficulty.toLowerCase() === {target} || tips.toLowerCase().includes({target}),
    difficulty,
    tips
  }};
}})())
""",
                timeout_seconds=8.0,
                interval_seconds=0.25,
            )
            attempts.append(
                {
                    "opened": opened,
                    "expanded": expanded,
                    "selected": selected,
                    "settled": settled,
                }
            )
            if settled.get("success"):
                return {
                    "success": True,
                    "attempts": attempts,
                    "state": self._self_healing_progress(),
                }
        return {
            "success": False,
            "attempts": attempts,
            "state": self._self_healing_progress(),
        }

    def _open_self_healing_tab(self, label: str, panel_hint: str) -> dict[str, Any]:
        clicked = self._browser_json(
            f"""
(() => {{
  const tab = Array.from(document.querySelectorAll('button[role="tab"], button')).find((b) => ((b.innerText || b.textContent || '').replace(/\\s+/g, ' ').trim()) === {json.dumps(label)});
  tab?.scrollIntoView({{block: 'center'}});
  tab?.click();
  return JSON.stringify({{
    success: !!tab,
    tab_text: tab ? ((tab.innerText || tab.textContent || '').replace(/\\s+/g, ' ').trim()) : ''
  }});
}})()
"""
        )
        settled = self._wait_for_js(
            f"""
JSON.stringify((() => {{
  const body = document.body.innerText || '';
  return {{
    success: body.includes({json.dumps(panel_hint)}),
    body: body.slice(0, 1800)
  }};
}})())
""",
            timeout_seconds=8.0,
            interval_seconds=0.25,
        )
        return {
            "success": clicked.get("success") and settled.get("success"),
            "clicked": clicked,
            "settled": settled,
        }

    def _self_healing_progress(self) -> dict[str, Any]:
        return self._browser_json(
            """
JSON.stringify((() => {
  const body = document.body.innerText || '';
  const textish = (el) => (((el?.innerText) || '') + ' ' + ((el?.textContent) || '')).replace(/\\s+/g, ' ').trim();
  const difficultyButton = Array.from(document.querySelectorAll('button[aria-haspopup="listbox"]')).find((b) => /\\b(Easy|Medium|Hard)\\b/i.test(textish(b)) && !/Manual/i.test(textish(b)));
  const difficulty = (textish(difficultyButton).match(/Easy|Medium|Hard/i) || [''])[0];
  const tipsLine = (body.match(/Showing tips for [^\\n]+/) || [])[0] || '';
  const poolStatus = (body.match(/Pool:\\s*([^\\n]+)/) || [])[1] || '';
  const lastFed = (body.match(/Last Fed:\\s*([^\\n]+)/) || [])[1] || '';
  return {
    success: true,
    difficulty,
    mutation_count: Number((body.match(/Mutations:\\s*(\\d+)/) || [])[1] || '0'),
    tips_line: tipsLine,
    pool_status: poolStatus,
    last_fed: lastFed,
    body: body.slice(0, 3000)
  };
})())
"""
        )

    def _solve_self_healing(self, capybara_name: str) -> dict[str, Any]:
        self._safari_navigate(f"{SITE_BASE}/self-healing-testing/")
        self._ensure_cookie_consent()
        time.sleep(2.0)
        selection = self._select_capybara_in_self_healing(capybara_name)
        time.sleep(1.0)

        phases: list[dict[str, Any]] = []
        for difficulty, action in [
            ("Easy", "schedule"),
            ("Medium", "pools"),
            ("Hard", "food"),
        ]:
            phase_start = self._self_healing_progress()
            difficulty_state = self._set_self_healing_difficulty(difficulty)
            mutate_click = self._browser_json(
                """
(() => {
  Array.from(document.querySelectorAll('button')).find((b) => (b.innerText || '').trim() === 'Mutate')?.click();
  return JSON.stringify({success: true});
})()
"""
            )
            mutated = self._wait_for_js(
                f"""
JSON.stringify((() => {{
  const body = document.body.innerText || '';
  return {{
    success: Number((body.match(/Mutations:\\s*(\\d+)/) || [])[1] || '0') >= {phase_start.get("mutation_count", 0) + 1},
    mutation_count: Number((body.match(/Mutations:\\s*(\\d+)/) || [])[1] || '0'),
    body: body.slice(0, 1800)
  }};
}})())
""",
                timeout_seconds=8.0,
                interval_seconds=0.25,
            )
            if action == "schedule":
                tab_state = self._open_self_healing_tab("Schedule", "Daily Schedule")
                row_click = self._browser_json(
                    """
(() => {
  const header = Array.from(document.querySelectorAll('th')).find((th) => ((th.innerText || th.textContent || '').replace(/\\s+/g, ' ').trim()) === 'Time');
  header?.click();
  const row = document.querySelector('tbody tr');
  row?.click();
  return JSON.stringify({
    success: !!document.querySelector('[role="grid"], table') && !!header && !!row,
    selected: ((row?.innerText || row?.textContent || '').replace(/\\s+/g, ' ').trim())
  });
})()
"""
                )
                action_state = self._wait_for_js(
                    """
JSON.stringify((() => {
  const body = document.body.innerText || '';
  return {
    success: /Daily Schedule/.test(body) && /(Morning Stretch|Breakfast|Morning Swim)/.test(body),
    body: body.slice(0, 1800)
  };
})())
""",
                    timeout_seconds=6.0,
                    interval_seconds=0.25,
                )
                phase_action = {
                    "success": tab_state.get("success") and row_click.get("success") and action_state.get("success"),
                    "tab": tab_state,
                    "row_click": row_click,
                    "state": action_state,
                }
            elif action == "pools":
                tab_state = self._open_self_healing_tab("Pools", "Spa Pools")
                pool_click = self._browser_json(
                    """
(() => {
  const body = document.body.innerText || '';
  if (/Leave Pool/i.test(body) || /You are here!/i.test(body)) {
    return JSON.stringify({success: true, already_in_pool: true});
  }
  const enter = Array.from(document.querySelectorAll('button')).find((b) => /^Enter Pool$/i.test(((b.innerText || b.textContent || '').replace(/\\s+/g, ' ').trim())));
  enter?.scrollIntoView({block: 'center'});
  enter?.click();
  return JSON.stringify({
    success: !!enter,
    button_text: enter ? ((enter.innerText || enter.textContent || '').replace(/\\s+/g, ' ').trim()) : ''
  });
})()
"""
                )
                pool_state = self._wait_for_js(
                    """
JSON.stringify((() => {
  const body = document.body.innerText || '';
  return {
    success: /Leave Pool/i.test(body) || /You are here!/i.test(body) || /Pool:\\s*(?!Not in a pool)/i.test(body),
    body: body.slice(0, 2200)
  };
})())
""",
                    timeout_seconds=8.0,
                    interval_seconds=0.25,
                )
                phase_action = {
                    "success": tab_state.get("success") and pool_click.get("success") and pool_state.get("success"),
                    "tab": tab_state,
                    "pool_click": pool_click,
                    "state": pool_state,
                }
            else:
                tab_state = self._open_self_healing_tab("Food", "Feeding Station")
                food_action = self._browser_json(
                    """
(() => {
  const textish = (el) => (((el?.innerText) || '') + ' ' + ((el?.textContent) || '')).replace(/\\s+/g, ' ').trim();
  let feedButton = Array.from(document.querySelectorAll('button')).find((b) => /^Feed(\\s|$)/i.test(textish(b)));
  if (!feedButton) {
    const foodTrigger = Array.from(document.querySelectorAll('button[aria-haspopup="listbox"], button')).find((b) => {
      const text = textish(b).toLowerCase();
      return /select food|banana|orange|corn|lettuce|apple|pumpkin/.test(text) && !/easy|medium|hard|manual/.test(text);
    });
    foodTrigger?.click();
    const option = Array.from(document.querySelectorAll('[role="option"]')).find((el) => /banana|orange|corn|lettuce|apple|pumpkin/i.test(textish(el)));
    option?.click();
    feedButton = Array.from(document.querySelectorAll('button')).find((b) => /^Feed(\\s|$)/i.test(textish(b)));
  }
  const before = feedButton ? textish(feedButton) : '';
  feedButton?.scrollIntoView({block: 'center'});
  feedButton?.click();
  return JSON.stringify({
    success: !!feedButton,
    before_button: before
  });
})()
"""
                )
                food_state = self._wait_for_js(
                    """
JSON.stringify((() => {
  const body = document.body.innerText || '';
  return {
    success: /Cooldown active/i.test(body) || /Feed available in/i.test(body) || !/Last Fed:\\s*Never/i.test(body),
    body: body.slice(0, 2200)
  };
})())
""",
                    timeout_seconds=8.0,
                    interval_seconds=0.25,
                )
                phase_action = {
                    "success": tab_state.get("success") and food_action.get("success") and food_state.get("success"),
                    "tab": tab_state,
                    "food_action": food_action,
                    "state": food_state,
                }
            phase_state = self._self_healing_progress()
            phases.append(
                {
                    "difficulty": difficulty,
                    "action": action,
                    "phase_start": phase_start,
                    "difficulty_state": difficulty_state,
                    "mutate_click": mutate_click,
                    "mutated": mutated,
                    "phase_action": phase_action,
                    "state": phase_state,
                }
            )

        success = selection.get("success") and all(
            phase["difficulty_state"].get("success")
            and phase["mutated"].get("success")
            and phase["phase_action"].get("success")
            and phase["state"]["mutation_count"] >= phase["phase_start"]["mutation_count"] + 1
            for phase in phases
        )
        result = {
            "success": success,
            "selection": selection,
            "phases": phases,
            "screenshot": self._capture("self_healing"),
        }
        self.summary["self_healing"] = result
        return result

    # ------------------------------------------------------------------
    # Runner
    # ------------------------------------------------------------------
    def run(self) -> int:
        step_index = 1
        try:
            self._safari_restart()

            step = self._step(step_index, "register_accounts", "Create fresh QA Practice accounts so the run has clean auth-gated state.")
            name_suffix = self.trace.run_id[:6]
            self.primary_account = self._register_account("primary", full_name=f"Codex QA Primary {name_suffix}")
            self.secondary_account = self._register_account("secondary", full_name=f"Codex QA Secondary {name_suffix}")
            self.primary_tokens = self._login_api(self.primary_account)
            self.secondary_tokens = self._login_api(self.secondary_account)
            self.summary["accounts"] = {
                "primary": {"email": self.primary_account.email, "full_name": self.primary_account.full_name},
                "secondary": {"email": self.secondary_account.email, "full_name": self.secondary_account.full_name},
            }
            self._save_json(self.api_dir / "accounts.json", self.summary["accounts"])
            self._end_step(step, True, self.summary["accounts"])
            step_index += 1

            step = self._step(step_index, "ui_login", "Log into the live Safari session and ensure cookie banners do not obscure the surface.")
            login_payload = self._login_safari(self.primary_account)
            self._end_step(step, True, login_payload)
            step_index += 1

            for name, solver in [
                ("drag_and_drop", self._solve_drag_and_drop),
                ("dynamic_elements", self._solve_dynamic_elements),
                ("keyboard_mouse", self._solve_keyboard_mouse),
                ("shadow_dom", self._solve_shadow_dom),
                ("iframe_windows", self._solve_iframe_windows),
            ]:
                step = self._step(step_index, name, f"Complete the {name.replace('_', ' ')} module to the site's own completion state.")
                payload = self._run_solver_with_retries(name, solver)
                self._record_module_result(name, payload)
                self._end_step(step, bool(payload.get("success")), payload)
                if not payload.get("success"):
                    raise RuntimeError(f"{name} failed")
                step_index += 1

            step = self._step(step_index, "file_operations", "Exercise authenticated file download, upload, processing, and workbook verification.")
            file_payload = self._run_solver_with_retries("file_operations", self._solve_file_operations)
            self._record_module_result("file_operations", file_payload)
            self._end_step(step, bool(file_payload.get("success")), file_payload)
            if not file_payload.get("success"):
                raise RuntimeError("file_operations failed")
            step_index += 1

            step = self._step(step_index, "capybara_api", "Use the published API surface to cover core resource, friendship, pool, auth, and cooldown rules.")
            api_payload = self._run_capybara_api_tests()
            self._end_step(step, bool(api_payload.get("success")), api_payload)
            if not api_payload.get("success"):
                raise RuntimeError("capybara_api failed")
            step_index += 1

            seed = self.summary["self_healing_seed"]["capybara_a"]["name"]
            step = self._step(step_index, "self_healing", "Exercise the self-healing page under mutation across Easy, Medium, and Hard.")
            self._safari_restart()
            self._login_safari(self.primary_account)
            self._ensure_cookie_consent()
            self._end_step(
                step,
                True,
                {"status": "browser_reset_and_relogin_complete", "capybara_name": seed},
            )
            step_index += 1

            step = self._step(step_index, "self_healing_actions", "Use stable locators on the mutation page after manual mutations at each difficulty.")
            self_healing_payload = self._run_solver_with_retries("self_healing", lambda: self._solve_self_healing(seed))
            self._record_module_result("self_healing", self_healing_payload)
            self._end_step(step, bool(self_healing_payload.get("success")), self_healing_payload)
            if not self_healing_payload.get("success"):
                raise RuntimeError("self_healing failed")

            self.summary["status"] = "success"
            self._save_json(self.run_dir / "qa_practice_mastery_summary.json", self.summary)
            self.trace.finalize(outcome="success")
            diag = DiagnosticReader(self.run_dir)
            (self.run_dir / "diagnostic.txt").write_text(diag.full_diagnostic(), encoding="utf-8")
            return 0
        except Exception as exc:
            self.summary["status"] = "failure"
            self.summary["error"] = str(exc)
            self._save_json(self.run_dir / "qa_practice_mastery_summary.json", self.summary)
            self.trace.record_failure(step_index, "mastery_failure", str(exc))
            self.trace.finalize(outcome="failure")
            return 1


def main() -> int:
    runner = QAPracticeRunner()
    return runner.run()


if __name__ == "__main__":
    raise SystemExit(main())
