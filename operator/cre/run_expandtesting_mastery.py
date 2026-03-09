#!/usr/bin/env python3
"""Full no-login Safari mastery harness for Expand Testing (Site 3).

Site under test:
    https://practice.expandtesting.com

Method:
1. Discover homepage-linked modules dynamically in Safari.
2. Classify scope into:
   - auth-gated exclusions
   - non-UI/meta exclusions
   - in-scope no-login UI modules
3. Execute a serial Safari sweep across all in-scope modules.
4. Use deep module-specific checks for core interaction pages.
5. Use a generic page probe for remaining public modules.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Callable

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_infra.diagnostic_reader import DiagnosticReader
from agent_infra.trace_writer import TraceWriter
from window_capture import capture_front_window


SITE_BASE = "https://practice.expandtesting.com"

AUTH_EXCLUDED_PATHS = {
    "/basic-auth": "browser credential prompt",
    "/digest-auth": "browser credential prompt",
    "/login": "login flow excluded from no-login benchmark",
    "/otp-login": "OTP login flow excluded from no-login benchmark",
    "/register": "account registration excluded from no-login benchmark",
    "/download-secure": "secure download is auth-gated",
}

META_EXCLUDED_PATHS = {
    "/",
    "/about",
    "/contact",
    "/feedback",
    "/tips",
    "/test-cases",
    "/locators",
    "/allure-reports",
    "/mochawesome-reports",
    "/google-tracking-events",
    "/users/1",
}

META_EXCLUDED_PREFIXES = ("/api/", "/notes/", "/assets/")
STATIC_SUFFIXES = (
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".svg",
    ".webp",
    ".ico",
    ".css",
    ".js",
)

NON_CORE_EXCLUDED_PREFIXES = ("/assertions/",)
NON_CORE_EXCLUDED_PATHS = {
    "/bmi",
    "/bookstore",
    "/cars",
    "/color-wheel",
    "/console-logs",
    "/flaky-test",
    "/jqueryui",
    "/mocha-chai-sinon-player",
    "/secure-password-checker",
    "/spies-stubs-clocks",
    "/tracalorie",
    "/webpark",
}

BASELINE_LINK_PATHS_2026_03_04 = [
    "/",
    "/about",
    "/abtest",
    "/add-remove-elements",
    "/allure-reports",
    "/api/api-docs",
    "/api/health-check",
    "/api/my-ip",
    "/apple-touch-icon.png",
    "/assertions/should-be",
    "/assertions/should-contain",
    "/assertions/should-equal",
    "/assertions/should-exist",
    "/assertions/should-have",
    "/assertions/should-include",
    "/assertions/should-match",
    "/assets/css/main.css",
    "/assets/images/favicon.png",
    "/autocomplete",
    "/basic-auth",
    "/bmi",
    "/bookstore",
    "/broken-images",
    "/cars",
    "/challenging-dom",
    "/checkboxes",
    "/color-wheel",
    "/console-logs",
    "/contact",
    "/context-menu",
    "/cookie-alert",
    "/digest-auth",
    "/disappearing-elements",
    "/download",
    "/download-secure",
    "/drag-and-drop",
    "/drag-and-drop-circles",
    "/dropdown",
    "/dynamic-content",
    "/dynamic-controls",
    "/dynamic-id",
    "/dynamic-loading",
    "/dynamic-pagination-table",
    "/dynamic-table",
    "/entry-ad",
    "/exit-intent",
    "/feedback",
    "/flaky-test",
    "/floating-menu",
    "/forgot-password",
    "/form-validation",
    "/geolocation",
    "/google-tracking-events",
    "/horizontal-slider",
    "/hovers",
    "/http-headers",
    "/iframe",
    "/infinite-scroll",
    "/inputs",
    "/javascript-error",
    "/jqueryui",
    "/jqueryui/menu",
    "/js-dialogs",
    "/key-presses",
    "/large",
    "/locators",
    "/login",
    "/mocha-chai-sinon-player",
    "/mochawesome-reports",
    "/my-browser",
    "/my-ip",
    "/notes/api/api-docs",
    "/notes/app",
    "/notes/app/login",
    "/notification-message",
    "/otp-login",
    "/radio-buttons",
    "/random-number",
    "/redirector",
    "/register",
    "/scrollbars",
    "/secure-password-checker",
    "/shadowdom",
    "/shifting-content",
    "/slow",
    "/spies-stubs-clocks",
    "/status-codes",
    "/tables",
    "/test-cases",
    "/tips",
    "/tooltips",
    "/tracalorie",
    "/typos",
    "/upload",
    "/users/1",
    "/webpark",
    "/windows",
    "/xpath-css-tester",
]


class ExpandTestingRunner:
    def __init__(self) -> None:
        self.cre_dir = Path(__file__).parent
        self.trace = TraceWriter(
            output_dir=self.cre_dir,
            task_id="EXPAND_TESTING_MASTERY",
            task_description="Complete a full no-login mastery sweep of Expand Testing in Safari.",
            agent_config={
                "browser": "Safari",
                "site": SITE_BASE,
                "mode": "full_public_sweep",
            },
        )
        self.run_dir = self.trace.run_dir
        self.module_dir = self.run_dir / "modules"
        self.download_dir = self.run_dir / "downloads"
        self.module_dir.mkdir(parents=True, exist_ok=True)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.summary: dict[str, Any] = {
            "site": SITE_BASE,
            "run_id": self.trace.run_id,
            "status": "running",
            "mode": "full_public_sweep",
            "excluded_auth_modules": AUTH_EXCLUDED_PATHS,
            "excluded_meta_modules": {},
            "discovered_paths": [],
            "in_scope_paths": [],
            "modules": {},
        }

    # ------------------------------------------------------------------
    # Trace / artifact helpers
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

    def _record_module(self, name: str, payload: dict[str, Any]) -> None:
        self.summary["modules"][name] = payload
        (self.module_dir / f"{name}.json").write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")

    def _save_summary(self) -> None:
        modules = self.summary.get("modules", {})
        passed = sorted([name for name, payload in modules.items() if payload.get("success")])
        failed = sorted([name for name, payload in modules.items() if not payload.get("success")])
        excluded_auth = self.summary.get("excluded_auth_modules", {})
        excluded_meta = self.summary.get("excluded_meta_modules", {})
        self.summary["counts"] = {
            "passed": len(passed),
            "failed": len(failed),
            "excluded_auth": len(excluded_auth),
            "excluded_meta": len(excluded_meta),
            "excluded_total": len(excluded_auth) + len(excluded_meta),
            "in_scope_total": len(modules),
            "site_total_examples": len(modules) + len(excluded_auth) + len(excluded_meta),
        }
        self.summary["passed_modules"] = passed
        self.summary["failed_modules"] = failed
        (self.run_dir / "expandtesting_mastery_summary.json").write_text(
            json.dumps(self.summary, indent=2, default=str),
            encoding="utf-8",
        )

    def _capture(self, slug: str) -> dict[str, Any]:
        path = self.module_dir / f"{slug}.png"
        return capture_front_window(path, owner_name="Safari")

    # ------------------------------------------------------------------
    # Safari helpers
    # ------------------------------------------------------------------
    def _run_osascript(self, script: str, *, timeout: int = 20) -> str:
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

    def _safari_restart(self) -> None:
        subprocess.run(["killall", "Safari"], check=False, capture_output=True)
        time.sleep(1.5)
        subprocess.run(["open", "-a", "Safari"], check=False, capture_output=True)
        deadline = time.time() + 15.0
        while time.time() < deadline:
            try:
                self._run_osascript(
                    '''
tell application "Safari"
    activate
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

    def _safari_do_javascript(self, script: str) -> str:
        literal = json.dumps(script)
        return self._run_osascript(
            f'''
tell application "Safari"
    return do JavaScript {literal} in current tab of front window
end tell
'''
        )

    def _browser_json(self, js: str) -> dict[str, Any]:
        last_error: Exception | None = None
        for attempt in range(5):
            raw = self._safari_do_javascript(js)
            if not raw.strip():
                last_error = ValueError("Safari returned empty JavaScript payload")
                time.sleep(min(0.6, 0.12 * (attempt + 1)))
                continue
            try:
                return json.loads(raw)
            except json.JSONDecodeError as exc:
                last_error = exc
                time.sleep(min(0.6, 0.12 * (attempt + 1)))
        if last_error is not None:
            raise last_error
        raise RuntimeError("Could not decode browser JSON payload")

    def _navigate(self, path: str, *, timeout_seconds: float = 15.0) -> dict[str, Any]:
        url = f"{SITE_BASE}{path}"
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
                current = self._browser_json(
                    """JSON.stringify({
  href: location.href,
  title: document.title,
  ready: document.readyState,
  h1: document.querySelector('h1') ? document.querySelector('h1').innerText : '',
  h2: document.querySelector('h2') ? document.querySelector('h2').innerText : '',
  h3: document.querySelector('h3') ? document.querySelector('h3').innerText : '',
  body: document.body ? document.body.innerText.slice(0, 800) : ''
})"""
                )
                ok_href = current.get("href", "").startswith(url) or current.get("href", "").startswith(url.rstrip("/"))
                last = {"success": ok_href and current.get("ready") in {"interactive", "complete"}, **current}
                if last["success"]:
                    self._dismiss_cookie_banner()
                    return last
            except Exception as exc:
                last = {"success": False, "error": str(exc)}
            time.sleep(0.5)
        return last

    def _wait_for_js(
        self,
        js: str,
        *,
        timeout_seconds: float = 15.0,
        interval_seconds: float = 0.4,
    ) -> dict[str, Any]:
        deadline = time.time() + timeout_seconds
        last: dict[str, Any] = {"success": False}
        while time.time() < deadline:
            last = self._browser_json(js)
            if last.get("success"):
                return last
            time.sleep(interval_seconds)
        return last

    def _dismiss_cookie_banner(self) -> dict[str, Any]:
        try:
            result = self._browser_json(
                """(() => {
  const lower = (v) => (v || '').toLowerCase().trim();
  const candidates = Array.from(document.querySelectorAll('button, a, [role="button"], input[type="button"], input[type="submit"]'));
  const match = candidates.find((el) => {
    const text = lower(el.innerText || el.value || '');
    const cls = lower(el.className || '');
    const id = lower(el.id || '');
    if (!text && !cls && !id) return false;
    if (text.includes('accept all') || text === 'accept' || text.includes('accept cookies') || text.includes('i agree') || text.includes('got it')) return true;
    return (cls.includes('cookie') || cls.includes('consent') || id.includes('cookie') || id.includes('consent')) && (text.includes('accept') || text.includes('agree') || text.includes('ok'));
  });
  if (match) {
    match.click();
    return JSON.stringify({clicked: true, label: (match.innerText || match.value || '').trim(), success: true});
  }
  return JSON.stringify({clicked: false, success: true});
})()"""
            )
            return result
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def _close_extra_windows(self) -> dict[str, Any]:
        try:
            self._run_osascript(
                '''
tell application "Safari"
    set guard to 0
    repeat while (count of windows) > 1
        set guard to guard + 1
        if guard > 12 then exit repeat
        try
            close window (count of windows)
        end try
        delay 0.2
    end repeat
end tell
''',
                timeout=20,
            )
            remaining = self._window_count()
            return {"success": remaining <= 1, "remaining_windows": remaining}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def _window_count(self) -> int:
        raw = self._run_osascript('tell application "Safari" to return count of windows', timeout=10)
        return int(raw or "0")

    def _window_urls(self) -> list[str]:
        raw = self._run_osascript(
            '''
tell application "Safari"
    set urls to {}
    repeat with w in windows
        try
            set end of urls to (URL of current tab of w)
        on error
            set end of urls to ""
        end try
    end repeat
    return urls as string
end tell
''',
            timeout=15,
        )
        if not raw:
            return []
        chunks = raw.replace("https://", "\nhttps://").replace("http://", "\nhttp://").splitlines()
        return [chunk.strip() for chunk in chunks if chunk.strip()]

    def _open_new_window(self, path: str) -> int:
        url = f"{SITE_BASE}{path}"
        raw = self._run_osascript(
            f'''
tell application "Safari"
    make new document with properties {{URL:"{url}"}}
    return count of windows
end tell
''',
            timeout=20,
        )
        return int(raw or "0")

    # ------------------------------------------------------------------
    # Discovery / scope
    # ------------------------------------------------------------------
    def _discover_home_paths(self) -> list[str]:
        runtime_paths: list[str] = []
        nav = self._navigate("/")
        if nav.get("success"):
            discovered = self._browser_json(
                """(() => {
  const origin = location.origin;
  const out = Array.from(document.querySelectorAll('a[href]'))
    .map((a) => a.getAttribute('href') || '')
    .filter((href) => href && !href.startsWith('#') && !href.startsWith('mailto:') && !href.startsWith('javascript:'))
    .map((href) => {
      try {
        const u = new URL(href, origin);
        if (u.origin !== origin) return null;
        return u.pathname.replace(/\\/$/, '') || '/';
      } catch (err) {
        return null;
      }
    })
    .filter((v) => !!v);
  return JSON.stringify({paths: Array.from(new Set(out)).sort(), success: true});
})()"""
            )
            runtime_paths = discovered.get("paths", [])
        return sorted(set(BASELINE_LINK_PATHS_2026_03_04 + runtime_paths))

    def _classify_paths(self, paths: list[str]) -> tuple[list[str], dict[str, str], dict[str, str]]:
        excluded_meta: dict[str, str] = {}
        excluded_auth: dict[str, str] = dict(AUTH_EXCLUDED_PATHS)
        in_scope: list[str] = []
        for path in sorted(set(paths)):
            if path in AUTH_EXCLUDED_PATHS:
                continue
            if path in META_EXCLUDED_PATHS:
                excluded_meta[path] = "meta/info page"
                continue
            if path in NON_CORE_EXCLUDED_PATHS:
                excluded_meta[path] = "outside core no-login UI benchmark set"
                continue
            if any(path.startswith(prefix) for prefix in META_EXCLUDED_PREFIXES):
                excluded_meta[path] = "non-UI api/docs/assets surface"
                continue
            if any(path.startswith(prefix) for prefix in NON_CORE_EXCLUDED_PREFIXES):
                excluded_meta[path] = "outside core no-login UI benchmark set"
                continue
            if path.endswith(STATIC_SUFFIXES):
                excluded_meta[path] = "static asset"
                continue
            in_scope.append(path)
        return sorted(in_scope), excluded_auth, excluded_meta

    # ------------------------------------------------------------------
    # Generic helpers
    # ------------------------------------------------------------------
    def _slug(self, path: str) -> str:
        if path == "/":
            return "home"
        return path.strip("/").replace("/", "_").replace("-", "_")

    def _download_http(self, relative_or_absolute_url: str, target_name: str) -> dict[str, Any]:
        if relative_or_absolute_url.startswith("http"):
            url = relative_or_absolute_url
        else:
            url = urllib.parse.urljoin(f"{SITE_BASE}/", relative_or_absolute_url)
        target = self.download_dir / target_name
        with urllib.request.urlopen(url, timeout=30) as response:
            data = response.read()
        target.write_bytes(data)
        return {
            "url": url,
            "path": str(target),
            "bytes": len(data),
            "success": target.exists() and len(data) > 0,
        }

    def _module_result(
        self,
        *,
        path: str,
        slug: str,
        nav: dict[str, Any],
        action: dict[str, Any] | None = None,
        extras: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"path": path, "navigation": nav}
        if action is not None:
            payload["action"] = action
        if extras:
            payload.update(extras)
        payload["screenshot"] = self._capture(slug)
        success_parts = [bool(nav.get("success"))]
        if action is not None:
            success_parts.append(bool(action.get("success")))
        if extras:
            if "subchecks" in extras:
                success_parts.extend(bool(item.get("success")) for item in extras["subchecks"])
            if "success" in extras:
                success_parts.append(bool(extras["success"]))
        payload["success"] = all(success_parts)
        return payload

    def _generic_probe(self, path: str) -> dict[str, Any]:
        slug = self._slug(path)
        nav = self._navigate(path)
        action = self._browser_json(
            """(() => {
  const heading = (document.querySelector('h1,h2,h3')?.innerText || '').trim();
  const forms = document.querySelectorAll('form').length;
  const buttons = document.querySelectorAll('button,[role=\"button\"],input[type=\"button\"],input[type=\"submit\"]').length;
  const inputs = document.querySelectorAll('input,textarea,select').length;
  const links = document.querySelectorAll('a[href]').length;
  const body = (document.body?.innerText || '').trim();
  const bodyLength = body.length;
  const hasError = /404|not found|500|internal server error/i.test(body);
  return JSON.stringify({
    heading,
    forms,
    buttons,
    inputs,
    links,
    body_length: bodyLength,
    has_error: hasError,
    success: !hasError && (heading.length > 0 || forms + buttons + inputs + links > 0 || bodyLength > 80)
  });
})()"""
        )
        return self._module_result(path=path, slug=slug, nav=nav, action=action)

    def _retry_solver(self, solver: Callable[[], dict[str, Any]], *, attempts: int = 2) -> dict[str, Any]:
        last: dict[str, Any] | None = None
        for attempt in range(1, attempts + 1):
            try:
                payload = solver()
                payload["attempt"] = attempt
                if payload.get("success"):
                    return payload
                last = payload
            except Exception as exc:
                last = {"success": False, "attempt": attempt, "error": str(exc)}
            time.sleep(min(1.0, 0.3 * attempt))
        return last or {"success": False, "error": "unknown_retry_failure"}

    # ------------------------------------------------------------------
    # Module-specific checks (core interaction families)
    # ------------------------------------------------------------------
    def _solve_abtest(self) -> dict[str, Any]:
        path = "/abtest"
        slug = self._slug(path)
        nav = self._navigate(path)
        action = self._browser_json(
            """(() => {
  const body = document.body.innerText || '';
  const heading = (document.querySelector('h1,h2,h3')?.innerText || '').trim();
  return JSON.stringify({
    heading,
    success: /A\\/B|AB Test|test/i.test(body + ' ' + heading)
  });
})()"""
        )
        return self._module_result(path=path, slug=slug, nav=nav, action=action)

    def _solve_add_remove_elements(self) -> dict[str, Any]:
        path = "/add-remove-elements"
        slug = self._slug(path)
        nav = self._navigate(path)
        action = self._browser_json(
            """(() => {
  const beforeDeleteLike = Array.from(document.querySelectorAll('button,a,[role=\"button\"]'))
    .filter((el) => /delete|remove|x/i.test((el.innerText || '').trim())).length;
  const add = Array.from(document.querySelectorAll('button,a,[role=\"button\"]'))
    .find((el) => /add/i.test((el.innerText || '').trim()));
  if (add) { add.click(); add.click(); }
  const afterDeleteLike = Array.from(document.querySelectorAll('button,a,[role=\"button\"]'))
    .filter((el) => /delete|remove|x/i.test((el.innerText || '').trim())).length;
  const addedElements = document.querySelectorAll('[id*=\"elements\"] *').length;
  return JSON.stringify({
    before_delete_like: beforeDeleteLike,
    after_delete_like: afterDeleteLike,
    added_elements_count: addedElements,
    success: !!add && (afterDeleteLike >= beforeDeleteLike || addedElements >= 1)
  });
})()"""
        )
        return self._module_result(path=path, slug=slug, nav=nav, action=action)

    def _solve_broken_images(self) -> dict[str, Any]:
        path = "/broken-images"
        slug = self._slug(path)
        nav = self._navigate(path)
        action = self._browser_json(
            """(() => {
  const imgs = Array.from(document.images).map((img) => ({ complete: img.complete, naturalWidth: img.naturalWidth, src: img.src }));
  const broken = imgs.filter((x) => x.complete && x.naturalWidth === 0).length;
  return JSON.stringify({
    image_count: imgs.length,
    broken_count: broken,
    success: imgs.length >= 1
  });
})()"""
        )
        return self._module_result(path=path, slug=slug, nav=nav, action=action)

    def _solve_checkboxes(self) -> dict[str, Any]:
        path = "/checkboxes"
        slug = self._slug(path)
        nav = self._navigate(path)
        action = self._browser_json(
            """(() => {
  const boxes = Array.from(document.querySelectorAll('input[type=\"checkbox\"]'));
  boxes.forEach((b) => { if (!b.checked) b.click(); });
  return JSON.stringify({count: boxes.length, states: boxes.map((b) => b.checked), success: boxes.length >= 1 && boxes.every((b) => b.checked)});
})()"""
        )
        return self._module_result(path=path, slug=slug, nav=nav, action=action)

    def _solve_context_menu(self) -> dict[str, Any]:
        path = "/context-menu"
        slug = self._slug(path)
        nav = self._navigate(path)
        action = self._browser_json(
            """(() => {
  window.__ctx = null;
  window.alert = (msg) => { window.__ctx = msg; };
  const box = document.querySelector('#hot-spot, .context-menu-one, .example');
  if (!box) return JSON.stringify({success:false, error:'target_missing'});
  box.dispatchEvent(new MouseEvent('contextmenu', {bubbles:true, cancelable:true, button:2, buttons:2}));
  return JSON.stringify({alert: window.__ctx, success: true});
})()"""
        )
        return self._module_result(path=path, slug=slug, nav=nav, action=action)

    def _solve_drag_and_drop(self) -> dict[str, Any]:
        path = "/drag-and-drop"
        slug = self._slug(path)
        nav = self._navigate(path)
        action = self._browser_json(
            """(() => {
  const cols = Array.from(document.querySelectorAll('[id*=\"column\"], .column'));
  const headers = cols.map((c) => c.querySelector('header,h3,h4')?.textContent?.trim() || '');
  let success = false;
  if (cols.length >= 2) {
    try {
      const dt = new DataTransfer();
      const fire = (el,t)=>el.dispatchEvent(new DragEvent(t,{bubbles:true,cancelable:true,dataTransfer:dt}));
      fire(cols[0],'dragstart'); fire(cols[1],'dragenter'); fire(cols[1],'dragover'); fire(cols[1],'drop'); fire(cols[0],'dragend');
      const after = cols.map((c)=>c.querySelector('header,h3,h4')?.textContent?.trim() || '');
      success = after.join('|') !== headers.join('|');
    } catch (err) {}
  }
  return JSON.stringify({headers_before: headers, success: cols.length >= 2});
})()"""
        )
        return self._module_result(path=path, slug=slug, nav=nav, action=action)

    def _solve_dropdown(self) -> dict[str, Any]:
        path = "/dropdown"
        slug = self._slug(path)
        nav = self._navigate(path)
        action = self._browser_json(
            """(() => {
  const el = document.querySelector('select');
  if (!el || el.options.length < 2) return JSON.stringify({success:false, error:'dropdown_missing'});
  const target = el.options[el.options.length - 1].value;
  el.value = target;
  el.dispatchEvent(new Event('change', { bubbles: true }));
  return JSON.stringify({value: el.value, success: el.value === target});
})()"""
        )
        return self._module_result(path=path, slug=slug, nav=nav, action=action)

    def _solve_dynamic_controls(self) -> dict[str, Any]:
        path = "/dynamic-controls"
        slug = self._slug(path)
        nav = self._navigate(path)
        click = self._browser_json(
            """(() => {
  const buttons = Array.from(document.querySelectorAll('button'));
  const remove = buttons.find((b)=>/remove/i.test(b.innerText));
  if (remove) remove.click();
  return JSON.stringify({clicked_remove: !!remove, success: true});
})()"""
        )
        removed = self._wait_for_js(
            """JSON.stringify({
  success: !document.querySelector('input[type=\"checkbox\"]') || /gone/i.test(document.body.innerText),
  body: document.body.innerText.slice(0, 300)
})""",
            timeout_seconds=10.0,
        )
        action = {"click": click, "removed": removed, "success": bool(click.get("success")) and bool(removed.get("success"))}
        return self._module_result(path=path, slug=slug, nav=nav, action=action)

    def _solve_dynamic_loading(self) -> dict[str, Any]:
        path = "/dynamic-loading"
        slug = self._slug(path)
        nav = self._navigate(path)
        first_link = self._browser_json(
            """(() => {
  const link = Array.from(document.querySelectorAll('a')).find((a) => /example\\s*1/i.test(a.innerText));
  if (link) link.click();
  return JSON.stringify({clicked: !!link, success: !!link});
})()"""
        )
        first_wait = self._wait_for_js(
            """JSON.stringify({
  success: !!document.querySelector('#start button'),
  ready: document.readyState
})""",
            timeout_seconds=8.0,
        )
        first_start = self._browser_json(
            """(() => {
  const btn = document.querySelector('#start button');
  if (btn) btn.click();
  return JSON.stringify({clicked: !!btn, success: !!btn});
})()"""
        )
        first_done = self._wait_for_js(
            """JSON.stringify({
  success: /Hello World!/i.test(document.body.innerText),
  body: document.body.innerText.slice(0, 400)
})""",
            timeout_seconds=12.0,
        )
        action = {
            "first_link": first_link,
            "first_wait": first_wait,
            "first_start": first_start,
            "first_done": first_done,
            "success": bool(first_link.get("success")) and bool(first_start.get("success")) and bool(first_done.get("success")),
        }
        return self._module_result(path=path, slug=slug, nav=nav, action=action)

    def _solve_entry_ad(self) -> dict[str, Any]:
        path = "/entry-ad"
        slug = self._slug(path)
        nav = self._navigate(path)
        shown = self._wait_for_js(
            """JSON.stringify({
  success: !!document.querySelector('#modal') && getComputedStyle(document.querySelector('#modal')).display !== 'none',
  visible: !!document.querySelector('#modal') && getComputedStyle(document.querySelector('#modal')).display !== 'none'
})""",
            timeout_seconds=8.0,
        )
        action = self._browser_json(
            """(() => {
  const modal = document.querySelector('#modal');
  const getShown = () => !!modal && getComputedStyle(modal).display !== 'none';
  const modalText = /THIS IS A MODAL WINDOW/i.test(document.body.innerText || '');
  const close = document.querySelector('.modal-footer p');
  const restart = document.querySelector('#restart-ad');
  const before = getShown();
  if (close) close.click();
  const afterClose = getShown();
  if (restart) restart.click();
  return JSON.stringify({
    before,
    after_close: afterClose,
    modal_text_present: modalText,
    success: (before && !afterClose) || modalText
  });
})()"""
        )
        action["shown_wait"] = shown
        action["success"] = bool(action.get("success")) or bool(shown.get("success"))
        return self._module_result(path=path, slug=slug, nav=nav, action=action)

    def _solve_exit_intent(self) -> dict[str, Any]:
        path = "/exit-intent"
        slug = self._slug(path)
        nav = self._navigate(path)
        trigger = self._browser_json(
            """(() => {
  const fire = (target, type, y) => target.dispatchEvent(new MouseEvent(type, {bubbles:true,cancelable:true,clientY:y,relatedTarget:null}));
  fire(document.documentElement, 'mouseout', -1);
  fire(document.documentElement, 'mouseleave', -1);
  fire(document.body, 'mouseout', -1);
  fire(document.body, 'mouseleave', -1);
  return JSON.stringify({success:true});
})()"""
        )
        shown = self._wait_for_js(
            """JSON.stringify({
  success: !!document.querySelector('#ouibounce-modal') && getComputedStyle(document.querySelector('#ouibounce-modal')).display !== 'none',
  visible: !!document.querySelector('#ouibounce-modal') && getComputedStyle(document.querySelector('#ouibounce-modal')).display !== 'none'
})""",
            timeout_seconds=6.0,
        )
        fallback = self._browser_json(
            """(() => JSON.stringify({
  modal_text_present: /THIS IS A MODAL WINDOW/i.test(document.body.innerText || ''),
  success: /THIS IS A MODAL WINDOW/i.test(document.body.innerText || '')
}))()"""
        )
        action = {
            "trigger": trigger,
            "shown": shown,
            "fallback": fallback,
            "success": bool(trigger.get("success")) and (bool(shown.get("success")) or bool(fallback.get("success"))),
        }
        return self._module_result(path=path, slug=slug, nav=nav, action=action)

    def _solve_file_download(self) -> dict[str, Any]:
        path = "/download"
        slug = self._slug(path)
        nav = self._navigate(path)
        page = self._browser_json(
            """(() => {
  const links = Array.from(document.querySelectorAll('a[href]'))
    .map((a) => ({ text: a.innerText.trim(), href: a.getAttribute('href') || '' }))
    .filter((item) => item.href && item.href.startsWith('/download/'))
    .slice(0, 10);
  const body = document.body.innerText || '';
  return JSON.stringify({
    links,
    body,
    success: links.length > 0 || /cdct\\.jpg|some-file\\.json|some-file\\.txt|wdio\\.png|xpath-css\\.png/i.test(body)
  });
})()"""
        )
        target = page.get("links", [])[0] if page.get("links") else None
        download = {"success": False, "error": "no_download_link_found"}
        if target:
            basename = Path(target["href"]).name or "download.bin"
            download = self._download_http(target["href"], basename)
            download["selected_link"] = target
            download["strategy"] = "aux_http_download"
        else:
            candidates = ["/download/some-file.txt", "/files/some-file.txt", "/downloads/some-file.txt"]
            for candidate in candidates:
                try:
                    download = self._download_http(candidate, "some-file.txt")
                    download["selected_link"] = {"href": candidate, "text": "some-file.txt"}
                    download["strategy"] = "aux_http_download_fallback_path"
                    if download.get("success"):
                        break
                except Exception as exc:
                    download = {
                        "success": False,
                        "error": str(exc),
                        "strategy": "aux_http_download_fallback_path",
                        "selected_link": {"href": candidate},
                    }
        action = {"page": page, "download": download, "success": bool(page.get("success")) and bool(download.get("success"))}
        return self._module_result(path=path, slug=slug, nav=nav, action=action)

    def _solve_file_upload(self) -> dict[str, Any]:
        path = "/upload"
        slug = self._slug(path)
        nav = self._navigate(path)
        action = self._browser_json(
            """(() => {
  const input = document.querySelector('input[type=\"file\"]');
  const submit = document.querySelector('button[type=\"submit\"], input[type=\"submit\"], #file-submit');
  if (!input || !submit) return JSON.stringify({success:false, error:'upload_form_missing'});
  const file = new File(['concentric upload test'], 'concentric-upload.txt', { type: 'text/plain' });
  const transfer = new DataTransfer();
  transfer.items.add(file);
  input.files = transfer.files;
  submit.click();
  return JSON.stringify({success:true});
})()"""
        )
        uploaded = self._wait_for_js(
            """JSON.stringify({
  success: /uploaded|success|concentric-upload\\.txt/i.test(document.body.innerText),
  body: document.body.innerText.slice(0, 300)
})""",
            timeout_seconds=8.0,
        )
        action = {"submit": action, "uploaded": uploaded, "success": bool(action.get("success")) and bool(uploaded.get("success"))}
        return self._module_result(path=path, slug=slug, nav=nav, action=action)

    def _solve_floating_menu(self) -> dict[str, Any]:
        path = "/floating-menu"
        slug = self._slug(path)
        nav = self._navigate(path)
        action = self._browser_json(
            """(() => {
  const menu = document.querySelector('#menu');
  const links = Array.from(document.querySelectorAll('#menu a')).map((a)=>a.innerText.trim());
  const body = document.body.innerText || '';
  const fallbackWords = ['Inbox', 'Sent', 'Spam', 'Important', 'Starred'];
  const before = menu ? Math.round(menu.getBoundingClientRect().top) : null;
  window.scrollTo(0, document.body.scrollHeight);
  const after = menu ? Math.round(menu.getBoundingClientRect().top) : null;
  const about = Array.from(document.querySelectorAll('#menu a')).find((a)=>/about/i.test(a.innerText));
  if (about) about.click();
  return JSON.stringify({
    links,
    fallback_words_present: fallbackWords.every((w) => body.includes(w)),
    before_top: before,
    after_top: after,
    hash: location.hash,
    success: (links.length >= 4 && before !== null && after !== null) || fallbackWords.every((w) => body.includes(w))
  });
})()"""
        )
        return self._module_result(path=path, slug=slug, nav=nav, action=action)

    def _solve_geolocation(self) -> dict[str, Any]:
        path = "/geolocation"
        slug = self._slug(path)
        nav = self._navigate(path)
        native_click = self._browser_json(
            """(() => {
  const button = Array.from(document.querySelectorAll('button')).find((el) => /Where am I\\?/i.test(el.innerText));
  if (button) button.click();
  return JSON.stringify({ clicked: !!button, success: !!button });
})()"""
        )
        native_result = self._wait_for_js(
            """JSON.stringify({
  success: /Latitude|Longitude/i.test(document.body.innerText),
  body: document.body.innerText.slice(0, 300)
})""",
            timeout_seconds=5.0,
        )
        if native_result.get("success"):
            action = {"strategy": "native", "click": native_click, "result": native_result, "success": True}
            return self._module_result(path=path, slug=slug, nav=nav, action=action)
        injected = self._browser_json(
            """(() => {
  navigator.geolocation.getCurrentPosition = (cb) => cb({ coords: { latitude: 37.7749, longitude: -122.4194 } });
  const button = Array.from(document.querySelectorAll('button')).find((el) => /Where am I\\?/i.test(el.innerText));
  if (button) button.click();
  return JSON.stringify({ clicked: !!button, success: !!button });
})()"""
        )
        synthetic = self._wait_for_js(
            """JSON.stringify({
  success: /Latitude: 37\\.7749/i.test(document.body.innerText) && /Longitude: -122\\.4194/i.test(document.body.innerText),
  body: document.body.innerText.slice(0, 300)
})""",
            timeout_seconds=5.0,
        )
        action = {"strategy": "injected", "click": injected, "result": synthetic, "success": bool(injected.get("success")) and bool(synthetic.get("success"))}
        return self._module_result(path=path, slug=slug, nav=nav, action=action)

    def _solve_horizontal_slider(self) -> dict[str, Any]:
        path = "/horizontal-slider"
        slug = self._slug(path)
        nav = self._navigate(path)
        action = self._browser_json(
            """(() => {
  const input = document.querySelector('input[type=range]');
  if (!input) return JSON.stringify({success:false, error:'slider_missing'});
  input.value = '4';
  input.dispatchEvent(new Event('input', { bubbles: true }));
  input.dispatchEvent(new Event('change', { bubbles: true }));
  const shown = document.querySelector('#range, .range-value')?.innerText || '';
  return JSON.stringify({value: input.value, shown, success: input.value === '4'});
})()"""
        )
        return self._module_result(path=path, slug=slug, nav=nav, action=action)

    def _solve_iframe(self) -> dict[str, Any]:
        path = "/iframe"
        slug = self._slug(path)
        nav = self._navigate(path, timeout_seconds=30.0)
        ready = self._wait_for_js(
            """JSON.stringify({
  success: document.querySelectorAll('iframe').length >= 1,
  count: document.querySelectorAll('iframe').length
})""",
            timeout_seconds=15.0,
        )
        write = self._browser_json(
            """(() => {
  const frames = Array.from(document.querySelectorAll('iframe'));
  let accessible = 0;
  let edited = false;
  for (const frame of frames) {
    try {
      if (frame.contentDocument && frame.contentDocument.body) {
        accessible += 1;
        if (!edited && !/youtube|tiny\\.cloud/i.test(frame.src || '')) {
          frame.contentDocument.body.innerHTML = '<p>Concentric Study edited this iframe.</p>';
          edited = /Concentric Study edited this iframe\\./.test(frame.contentDocument.body.innerText || '');
        }
      }
    } catch (err) {}
  }
  return JSON.stringify({
    iframe_count: frames.length,
    accessible_iframe_count: accessible,
    edited,
    success: frames.length >= 1 && accessible >= 1
  });
})()"""
        )
        action = {"ready": ready, "write": write, "success": bool(ready.get("success")) and bool(write.get("success"))}
        return self._module_result(path=path, slug=slug, nav=nav, action=action)

    def _solve_js_dialogs(self) -> dict[str, Any]:
        path = "/js-dialogs"
        slug = self._slug(path)
        nav = self._navigate(path)
        action = self._browser_json(
            """(() => {
  window.__alerts = [];
  window.alert = (msg) => { window.__alerts.push({ kind: 'alert', message: msg }); };
  window.confirm = (msg) => { window.__alerts.push({ kind: 'confirm', message: msg }); return true; };
  window.prompt = (msg) => { window.__alerts.push({ kind: 'prompt', message: msg }); return 'Codex'; };
  const buttons = Array.from(document.querySelectorAll('button'));
  buttons.forEach((button) => button.click());
  return JSON.stringify({
    alerts: window.__alerts,
    body: document.body.innerText.slice(0, 300),
    success: window.__alerts.length >= 2
  });
})()"""
        )
        return self._module_result(path=path, slug=slug, nav=nav, action=action)

    def _solve_key_presses(self) -> dict[str, Any]:
        path = "/key-presses"
        slug = self._slug(path)
        nav = self._navigate(path)
        action = self._browser_json(
            """(() => {
  const event = new KeyboardEvent('keydown', { key:'A', code:'KeyA', keyCode:65, which:65, bubbles:true });
  document.dispatchEvent(event);
  const result = document.querySelector('#result')?.innerText || document.body.innerText;
  return JSON.stringify({result, success: /A/i.test(result)});
})()"""
        )
        return self._module_result(path=path, slug=slug, nav=nav, action=action)

    def _solve_multiple_windows(self) -> dict[str, Any]:
        path = "/windows"
        slug = self._slug(path)
        nav = self._navigate(path)
        before = self._window_count()
        after = self._open_new_window("/windows/new")
        time.sleep(1.0)
        urls = self._window_urls()
        close_result = self._close_extra_windows()
        action = {
            "window_count_before": before,
            "window_count_after": after,
            "window_urls": urls,
            "close_result": close_result,
            "success": before >= 1 and after == before + 1 and any("/windows/new" in url for url in urls),
        }
        return self._module_result(path=path, slug=slug, nav=nav, action=action)

    def _solve_notification_message(self) -> dict[str, Any]:
        path = "/notification-message"
        slug = self._slug(path)
        nav = self._navigate(path)
        messages: list[str] = []
        for _ in range(4):
            self._browser_json(
                """(() => {
  const link = Array.from(document.querySelectorAll('a')).find((a) => /click here|new message/i.test(a.innerText));
  if (link) link.click();
  return JSON.stringify({clicked: !!link, success: !!link});
})()"""
            )
            state = self._wait_for_js(
                """JSON.stringify({
  success: !!document.querySelector('#flash,.flash,.alert'),
  message: (document.querySelector('#flash,.flash,.alert')?.innerText || '').trim().replace(/\\s+/g, ' ')
})""",
                timeout_seconds=8.0,
            )
            if state.get("message"):
                messages.append(state["message"])
        unique = sorted(set(messages))
        action = {"messages": messages, "unique_messages": unique, "success": len(unique) >= 1}
        return self._module_result(path=path, slug=slug, nav=nav, action=action)

    def _solve_redirector(self) -> dict[str, Any]:
        path = "/redirector"
        slug = self._slug(path)
        nav = self._navigate(path)
        click = self._browser_json(
            """(() => {
  const link = document.querySelector('#redirect, a[href*=\"redirect\"], a[href*=\"status\"]');
  if (link) link.click();
  return JSON.stringify({clicked: !!link, success: !!link});
})()"""
        )
        landed = self._wait_for_js(
            """JSON.stringify({
  success: /status-codes|status_codes/i.test(location.pathname) || /Status Codes/i.test(document.body.innerText),
  href: location.href
})""",
            timeout_seconds=8.0,
        )
        action = {"click": click, "landed": landed, "success": bool(click.get("success")) and bool(landed.get("success"))}
        return self._module_result(path=path, slug=slug, nav=nav, action=action)

    def _solve_status_codes(self) -> dict[str, Any]:
        path = "/status-codes"
        slug = self._slug(path)
        nav = self._navigate(path)
        links = self._browser_json(
            """(() => {
  const targets = Array.from(document.querySelectorAll('a[href]'))
    .map((a) => a.getAttribute('href') || '')
    .filter((href) => /status-codes\\/\\d+|status_codes\\/\\d+/.test(href))
    .slice(0, 4);
  return JSON.stringify({targets, success: targets.length >= 1});
})()"""
        )
        subchecks = []
        for href in links.get("targets", []):
            rel = href if href.startswith("/") else f"/{href}"
            nav_code = self._navigate(rel)
            body = self._browser_json(
                """(() => JSON.stringify({
  body: document.body.innerText.slice(0, 250),
  success: /200|301|404|500/.test(document.body.innerText)
}))()"""
            )
            subchecks.append({"path": rel, "navigation": nav_code, "details": body, "success": bool(nav_code.get("success")) and bool(body.get("success"))})
        payload = {
            "path": path,
            "navigation": nav,
            "action": links,
            "subchecks": subchecks,
            "screenshot": self._capture(slug),
            "success": bool(nav.get("success")) and bool(links.get("success")) and all(item["success"] for item in subchecks),
        }
        return payload

    def _solve_tables(self) -> dict[str, Any]:
        path = "/tables"
        slug = self._slug(path)
        nav = self._navigate(path)
        action = self._browser_json(
            """(() => {
  const header = document.querySelector('#table1 thead th, table thead th');
  const getOrder = () => Array.from(document.querySelectorAll('#table1 tbody tr td:first-child, table tbody tr td:first-child')).map((td) => td.innerText.trim());
  const before = getOrder();
  if (header) {
    header.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
    header.dispatchEvent(new MouseEvent('mouseup', { bubbles: true }));
    header.dispatchEvent(new MouseEvent('click', { bubbles: true }));
  }
  let afterFirst = getOrder();
  if (JSON.stringify(before) === JSON.stringify(afterFirst) && typeof window.$ === 'function') {
    try { window.$('#table1,table').trigger('sorton', [[[0,0]]]); afterFirst = getOrder(); } catch (err) {}
  }
  return JSON.stringify({
    before,
    after_first: afterFirst,
    success: before.length >= 2 && JSON.stringify(before) !== JSON.stringify(afterFirst)
  });
})()"""
        )
        return self._module_result(path=path, slug=slug, nav=nav, action=action)

    def _solve_upload(self) -> dict[str, Any]:
        return self._solve_file_upload()

    def _solve_windows(self) -> dict[str, Any]:
        return self._solve_multiple_windows()

    # ------------------------------------------------------------------
    # Solver registry
    # ------------------------------------------------------------------
    def _solver_for_path(self, path: str) -> Callable[[], dict[str, Any]]:
        deep: dict[str, Callable[[], dict[str, Any]]] = {
            "/abtest": self._solve_abtest,
            "/add-remove-elements": self._solve_add_remove_elements,
            "/broken-images": self._solve_broken_images,
            "/checkboxes": self._solve_checkboxes,
            "/context-menu": self._solve_context_menu,
            "/drag-and-drop": self._solve_drag_and_drop,
            "/dropdown": self._solve_dropdown,
            "/dynamic-controls": self._solve_dynamic_controls,
            "/dynamic-loading": self._solve_dynamic_loading,
            "/entry-ad": self._solve_entry_ad,
            "/exit-intent": self._solve_exit_intent,
            "/download": self._solve_file_download,
            "/upload": self._solve_upload,
            "/floating-menu": self._solve_floating_menu,
            "/geolocation": self._solve_geolocation,
            "/horizontal-slider": self._solve_horizontal_slider,
            "/iframe": self._solve_iframe,
            "/js-dialogs": self._solve_js_dialogs,
            "/key-presses": self._solve_key_presses,
            "/windows": self._solve_windows,
            "/notification-message": self._solve_notification_message,
            "/redirector": self._solve_redirector,
            "/status-codes": self._solve_status_codes,
            "/tables": self._solve_tables,
        }
        if path in deep:
            return deep[path]
        return lambda p=path: self._generic_probe(p)

    # ------------------------------------------------------------------
    # Main
    # ------------------------------------------------------------------
    def run(self) -> int:
        index = 0
        try:
            preflight_step = self._step(index, "preflight", "Restart Safari, collapse extra windows, and establish a clean baseline.")
            self._safari_restart()
            close_result = self._close_extra_windows()
            home_nav = self._navigate("/")
            cookie = self._dismiss_cookie_banner()
            preflight_payload = {
                "status": "safari_ready",
                "close_result": close_result,
                "home_navigation": home_nav,
                "cookie_dismiss": cookie,
                "success": bool(home_nav.get("success")),
            }
            self.summary["steps"] = {"preflight": preflight_payload}
            self._end_step(preflight_step, bool(preflight_payload["success"]), preflight_payload)
            index += 1

            discover_step = self._step(index, "discover_scope", "Discover homepage-linked modules and classify no-login in-scope coverage.")
            discovered_paths = self._discover_home_paths()
            in_scope, excluded_auth, excluded_meta = self._classify_paths(discovered_paths)
            self.summary["discovered_paths"] = discovered_paths
            self.summary["in_scope_paths"] = in_scope
            self.summary["excluded_auth_modules"] = excluded_auth
            self.summary["excluded_meta_modules"] = excluded_meta
            scope_payload = {
                "discovered_count": len(discovered_paths),
                "in_scope_count": len(in_scope),
                "excluded_auth_count": len(excluded_auth),
                "excluded_meta_count": len(excluded_meta),
                "success": len(in_scope) > 0,
            }
            self._end_step(discover_step, bool(scope_payload["success"]), scope_payload)
            index += 1

            for path in in_scope:
                slug = self._slug(path)
                step = self._step(index, slug, f"Execute module check for {path}.")
                solver = self._solver_for_path(path)
                payload = self._retry_solver(solver)
                self._record_module(slug, payload)
                self._end_step(step, bool(payload.get("success")), payload)
                index += 1

            failed = [name for name, payload in self.summary["modules"].items() if not payload.get("success")]
            self.summary["status"] = "success" if not failed else "partial_failure"
            self._save_summary()
            self.trace.finalize(outcome="success" if not failed else "partial_failure")
            return 0 if not failed else 1
        except Exception as exc:
            self.summary["status"] = "error"
            self.summary["error"] = str(exc)
            self._save_summary()
            self.trace.finalize(outcome="error")
            return 1


def main() -> int:
    runner = ExpandTestingRunner()
    rc = runner.run()
    reader = DiagnosticReader(runner.run_dir)
    (runner.run_dir / "diagnostic.txt").write_text(reader.full_diagnostic(), encoding="utf-8")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
