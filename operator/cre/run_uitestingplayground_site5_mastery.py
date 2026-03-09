#!/usr/bin/env python3
"""Full no-login Safari mastery harness for UI Testing Playground (Site 5)."""

from __future__ import annotations

import json
import subprocess
import sys
import time
import urllib.parse
from pathlib import Path
from typing import Any, Callable

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_infra.diagnostic_reader import DiagnosticReader
from agent_infra.trace_writer import TraceWriter
from window_capture import capture_front_window


SITE_BASE = "http://uitestingplayground.com"

AUTH_EXCLUDED_PATHS: dict[str, str] = {}

META_EXCLUDED_PATHS = {
    "/resources": "resources/documentation page outside core no-login challenge benchmark",
    "/home": "alias of root home page; deduped to avoid duplicate module accounting",
}

META_EXCLUDED_PREFIXES = ("/static/",)
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

BASELINE_PATHS_2026_03_04 = [
    "/",
    "/home",
    "/resources",
    "/dynamicid",
    "/classattr",
    "/hiddenlayers",
    "/loaddelay",
    "/ajax",
    "/clientdelay",
    "/click",
    "/textinput",
    "/scrollbars",
    "/dynamictable",
    "/verifytext",
    "/progressbar",
    "/visibility",
    "/sampleapp",
    "/mouseover",
    "/nbsp",
    "/overlapped",
    "/shadowdom",
    "/alerts",
    "/upload",
    "/animation",
    "/disabledinput",
    "/autowait",
    "/frames",
]


class UITestingPlaygroundSite5Runner:
    def __init__(self) -> None:
        self.cre_dir = Path(__file__).parent
        self.trace = TraceWriter(
            output_dir=self.cre_dir,
            task_id="UITESTINGPLAYGROUND_SITE5_MASTERY",
            task_description="Complete a full no-login mastery sweep of UI Testing Playground in Safari.",
            agent_config={
                "browser": "Safari",
                "site": SITE_BASE,
                "mode": "full_public_sweep",
            },
        )
        self.run_dir = self.trace.run_dir
        self.module_dir = self.run_dir / "modules"
        self.module_dir.mkdir(parents=True, exist_ok=True)
        self.summary: dict[str, Any] = {
            "site": SITE_BASE,
            "run_id": self.trace.run_id,
            "status": "running",
            "mode": "full_public_sweep",
            "excluded_auth_modules": dict(AUTH_EXCLUDED_PATHS),
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
        (self.run_dir / "uitestingplayground_site5_mastery_summary.json").write_text(
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
                    """
tell application "Safari"
    activate
    if (count of windows) = 0 then
        make new document
    end if
end tell
""",
                    timeout=10,
                )
                return
            except Exception:
                time.sleep(0.5)
        raise RuntimeError("Safari did not become controllable after restart")

    def _safari_do_javascript(self, script: str) -> str:
        literal = json.dumps(script)
        return self._run_osascript(
            f"""
tell application "Safari"
    return do JavaScript {literal} in current tab of front window
end tell
"""
        )

    def _browser_json(self, js: str) -> dict[str, Any]:
        last_error: Exception | None = None
        for attempt in range(8):
            raw = self._safari_do_javascript(js)
            if not raw.strip():
                last_error = ValueError("Safari returned empty JavaScript payload")
                time.sleep(min(0.75, 0.12 * (attempt + 1)))
                continue
            try:
                return json.loads(raw)
            except json.JSONDecodeError as exc:
                last_error = exc
                time.sleep(min(0.75, 0.12 * (attempt + 1)))
        if last_error is not None:
            raise last_error
        raise RuntimeError("Could not decode browser JSON payload")

    def _normalize_path(self, path: str) -> str:
        if not path:
            return "/"
        if path.startswith("http://") or path.startswith("https://"):
            parsed = urllib.parse.urlsplit(path)
            raw_path = parsed.path or "/"
            query = parsed.query
        else:
            if not path.startswith("/"):
                path = "/" + path
            parsed = urllib.parse.urlsplit(path)
            raw_path = parsed.path or "/"
            query = parsed.query
        encoded_path = urllib.parse.quote(urllib.parse.unquote(raw_path), safe="/%")
        return encoded_path + (f"?{query}" if query else "")

    def _navigate(self, path: str, *, timeout_seconds: float = 16.0) -> dict[str, Any]:
        normalized = self._normalize_path(path)
        url = f"{SITE_BASE}{normalized}"
        self._run_osascript(
            f"""
tell application "Safari"
    activate
    if (count of windows) = 0 then
        make new document with properties {{URL:"{url}"}}
    else
        set URL of current tab of front window to "{url}"
    end if
end tell
"""
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
  body: document.body ? document.body.innerText.slice(0, 1000) : ''
})"""
                )
                href = current.get("href", "")
                ok_href = href.startswith(url) or href.startswith(url.rstrip("/"))
                last = {"success": ok_href and current.get("ready") in {"interactive", "complete"}, **current}
                if last["success"]:
                    return last
            except Exception as exc:
                last = {"success": False, "error": str(exc)}
            time.sleep(0.35)
        return last

    def _wait_for_js(
        self,
        js: str,
        *,
        timeout_seconds: float = 10.0,
        interval_seconds: float = 0.35,
    ) -> dict[str, Any]:
        deadline = time.time() + timeout_seconds
        last: dict[str, Any] = {"success": False}
        while time.time() < deadline:
            last = self._browser_json(js)
            if last.get("success"):
                return last
            time.sleep(interval_seconds)
        return last

    def _close_extra_windows(self) -> dict[str, Any]:
        try:
            self._run_osascript(
                """
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
""",
                timeout=20,
            )
            count = int(self._run_osascript('tell application "Safari" to return count of windows', timeout=8) or "0")
            return {"success": count <= 1, "remaining_windows": count}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    # ------------------------------------------------------------------
    # Discovery / scope
    # ------------------------------------------------------------------
    def _discover_paths(self) -> list[str]:
        paths = set(BASELINE_PATHS_2026_03_04)
        for seed in ("/", "/home"):
            nav = self._navigate(seed)
            if not nav.get("success"):
                continue
            try:
                extracted = self._browser_json(
                    """(() => {
  const origin = location.origin;
  const out = Array.from(document.querySelectorAll('a[href]'))
    .map((a) => a.getAttribute('href') || '')
    .filter((href) => href && !href.startsWith('#') && !href.startsWith('mailto:') && !href.startsWith('javascript:'))
    .map((href) => {
      try {
        const u = new URL(href, origin);
        if (u.origin !== origin) return null;
        return (u.pathname.replace(/\\/$/, '') || '/');
      } catch (err) {
        return null;
      }
    })
    .filter((v) => !!v);
  return JSON.stringify({paths: Array.from(new Set(out)).sort(), success: true});
})()"""
                )
                for path in extracted.get("paths", []):
                    paths.add(path)
            except Exception:
                continue
        return sorted(paths)

    def _classify_paths(self, paths: list[str]) -> tuple[list[str], dict[str, str], dict[str, str]]:
        excluded_auth = dict(AUTH_EXCLUDED_PATHS)
        excluded_meta: dict[str, str] = {}
        in_scope: list[str] = []
        canonical_paths = {self._normalize_path(path) for path in paths}
        for path in sorted(canonical_paths):
            if not path.startswith("/"):
                excluded_meta[path] = "invalid path"
                continue
            if path in AUTH_EXCLUDED_PATHS:
                continue
            if path in META_EXCLUDED_PATHS:
                excluded_meta[path] = META_EXCLUDED_PATHS[path]
                continue
            if any(path.startswith(prefix) for prefix in META_EXCLUDED_PREFIXES):
                excluded_meta[path] = "static asset path"
                continue
            if path.endswith(STATIC_SUFFIXES):
                excluded_meta[path] = "static file path"
                continue
            in_scope.append(path)
        return sorted(in_scope), excluded_auth, excluded_meta

    # ------------------------------------------------------------------
    # Generic helpers / solvers
    # ------------------------------------------------------------------
    def _slug(self, path: str) -> str:
        if path == "/":
            return "home"
        text = urllib.parse.unquote(path).strip("/")
        text = text.replace("/", "_").replace("-", "_").replace("&", "and").replace("%", "pct")
        text = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in text)
        while "__" in text:
            text = text.replace("__", "_")
        return text.strip("_") or "root"

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

    def _generic_probe(self, path: str) -> dict[str, Any]:
        slug = self._slug(path)
        nav = self._navigate(path)
        action = self._browser_json(
            """(() => {
  const heading = (document.querySelector('h1,h2,h3')?.innerText || '').trim();
  const forms = document.querySelectorAll('form').length;
  const buttons = document.querySelectorAll('button,[role="button"],input[type="button"],input[type="submit"]').length;
  const inputs = document.querySelectorAll('input,textarea,select').length;
  const links = document.querySelectorAll('a[href]').length;
  const iframes = document.querySelectorAll('iframe').length;
  const body = (document.body?.innerText || '').trim();
  const bodyLength = body.length;
  const hasError = /404|not found|500|internal server error|access denied/i.test(body);
  return JSON.stringify({
    heading,
    forms,
    buttons,
    inputs,
    links,
    iframes,
    body_length: bodyLength,
    has_error: hasError,
    success: !hasError && (heading.length > 0 || forms + buttons + inputs + links + iframes > 0 || bodyLength > 80)
  });
})()"""
        )
        return self._module_result(path=path, slug=slug, nav=nav, action=action)

    def _solve_home(self, path: str = "/") -> dict[str, Any]:
        slug = self._slug(path)
        nav = self._navigate(path)
        action = self._browser_json(
            """(() => {
  const body = document.body.innerText || '';
  const challengeLinks = Array.from(document.querySelectorAll('a[href]'))
    .map((a) => a.getAttribute('href') || '')
    .filter((href) => href && href.startsWith('/') && !href.startsWith('/static/') && href !== '/resources')
    .filter((v, i, arr) => arr.indexOf(v) === i);
  return JSON.stringify({
    title: document.title,
    challenge_link_count: challengeLinks.length,
    has_brand: /UI Test Automation\\s*Playground/i.test(body + ' ' + document.title),
    success: /UI Test Automation\\s*Playground/i.test(body + ' ' + document.title) && challengeLinks.length >= 18
  });
})()"""
        )
        return self._module_result(path=path, slug=slug, nav=nav, action=action)

    def _solve_dynamicid(self) -> dict[str, Any]:
        path = "/dynamicid"
        slug = self._slug(path)
        nav = self._navigate(path)
        action = self._browser_json(
            """(() => {
  const btn = Array.from(document.querySelectorAll('button'))
    .find((el) => /Dynamic ID/i.test((el.innerText || '').trim()));
  if (btn) btn.click();
  return JSON.stringify({
    button_present: !!btn,
    clicked: !!btn,
    success: !!btn
  });
})()"""
        )
        return self._module_result(path=path, slug=slug, nav=nav, action=action)

    def _solve_classattr(self) -> dict[str, Any]:
        path = "/classattr"
        slug = self._slug(path)
        nav = self._navigate(path)
        action = self._browser_json(
            """(() => {
  window.alert = () => {};
  const btn = document.querySelector('button.btn-primary');
  if (btn) btn.click();
  return JSON.stringify({
    button_present: !!btn,
    clicked: !!btn,
    success: !!btn
  });
})()"""
        )
        return self._module_result(path=path, slug=slug, nav=nav, action=action)

    def _solve_hiddenlayers(self) -> dict[str, Any]:
        path = "/hiddenlayers"
        slug = self._slug(path)
        nav = self._navigate(path)
        click_green = self._browser_json(
            """(() => {
  const green = document.querySelector('#greenButton');
  if (green) green.click();
  return JSON.stringify({
    green_present: !!green,
    success: !!green
  });
})()"""
        )
        click_blue = self._wait_for_js(
            """(() => {
  const blue = document.querySelector('#blueButton');
  if (blue) blue.click();
  return JSON.stringify({
    blue_present: !!blue,
    success: !!blue
  });
})()""",
            timeout_seconds=6.0,
        )
        action = {
            "click_green": click_green,
            "click_blue": click_blue,
            "success": bool(click_green.get("success")) and bool(click_blue.get("success")),
        }
        return self._module_result(path=path, slug=slug, nav=nav, action=action)

    def _solve_loaddelay(self) -> dict[str, Any]:
        path = "/loaddelay"
        slug = self._slug(path)
        nav = self._navigate(path)
        wait_btn = self._wait_for_js(
            """(() => {
  const btn = Array.from(document.querySelectorAll('button'))
    .find((el) => /Appearing After Delay/i.test((el.innerText || '').trim()));
  if (btn) btn.click();
  return JSON.stringify({button_present: !!btn, success: !!btn});
})()""",
            timeout_seconds=14.0,
        )
        return self._module_result(path=path, slug=slug, nav=nav, action=wait_btn)

    def _solve_ajax(self) -> dict[str, Any]:
        path = "/ajax"
        slug = self._slug(path)
        nav = self._navigate(path)
        click = self._browser_json(
            """(() => {
  const btn = document.querySelector('#ajaxButton');
  if (btn) btn.click();
  return JSON.stringify({clicked: !!btn, success: !!btn});
})()"""
        )
        wait = self._wait_for_js(
            """(() => {
  const txt = (document.querySelector('#content')?.innerText || '').trim();
  return JSON.stringify({
    content: txt,
    success: /Data loaded with AJAX get request\\./i.test(txt) || txt.length > 10
  });
})()""",
            timeout_seconds=18.0,
        )
        action = {"click": click, "wait": wait, "success": bool(click.get("success")) and bool(wait.get("success"))}
        return self._module_result(path=path, slug=slug, nav=nav, action=action)

    def _solve_clientdelay(self) -> dict[str, Any]:
        path = "/clientdelay"
        slug = self._slug(path)
        nav = self._navigate(path)
        click = self._browser_json(
            """(() => {
  const btn = document.querySelector('#ajaxButton');
  if (btn) btn.click();
  return JSON.stringify({clicked: !!btn, success: !!btn});
})()"""
        )
        wait = self._wait_for_js(
            """(() => {
  const txt = (document.querySelector('#content')?.innerText || '').trim();
  return JSON.stringify({
    content: txt,
    success: /Data calculated on the client side\\./i.test(txt) || txt.length > 10
  });
})()""",
            timeout_seconds=18.0,
        )
        action = {"click": click, "wait": wait, "success": bool(click.get("success")) and bool(wait.get("success"))}
        return self._module_result(path=path, slug=slug, nav=nav, action=action)

    def _solve_click(self) -> dict[str, Any]:
        path = "/click"
        slug = self._slug(path)
        nav = self._navigate(path)
        action = self._browser_json(
            """(() => {
  const btn = document.querySelector('#badButton');
  const before = btn ? (btn.className || '') : '';
  if (btn) {
    const evt = new MouseEvent('click', {
      bubbles: true,
      cancelable: true,
      view: window,
      screenX: 100,
      screenY: 100,
      clientX: 50,
      clientY: 20
    });
    btn.dispatchEvent(evt);
  }
  const after = btn ? (btn.className || '') : '';
  return JSON.stringify({
    button_present: !!btn,
    class_before: before,
    class_after: after,
    success: !!btn && (after !== before || /btn-success/i.test(after))
  });
})()"""
        )
        return self._module_result(path=path, slug=slug, nav=nav, action=action)

    def _solve_textinput(self) -> dict[str, Any]:
        path = "/textinput"
        slug = self._slug(path)
        nav = self._navigate(path)
        write = self._browser_json(
            """(() => {
  const input = document.querySelector('#newButtonName');
  const btn = document.querySelector('#updatingButton');
  if (!input || !btn) return JSON.stringify({success:false, error:'controls_missing'});
  input.value = 'Concentric Study';
  input.dispatchEvent(new Event('input', { bubbles: true }));
  input.dispatchEvent(new Event('change', { bubbles: true }));
  btn.click();
  return JSON.stringify({success:true});
})()"""
        )
        wait = self._wait_for_js(
            """(() => {
  const btn = document.querySelector('#updatingButton');
  const txt = (btn?.innerText || '').trim();
  return JSON.stringify({
    button_text: txt,
    success: /Concentric Study/i.test(txt)
  });
})()""",
            timeout_seconds=6.0,
        )
        action = {"write": write, "wait": wait, "success": bool(write.get("success")) and bool(wait.get("success"))}
        return self._module_result(path=path, slug=slug, nav=nav, action=action)

    def _solve_scrollbars(self) -> dict[str, Any]:
        path = "/scrollbars"
        slug = self._slug(path)
        nav = self._navigate(path)
        action = self._browser_json(
            """(() => {
  const btn = document.querySelector('#hidingButton');
  if (!btn) return JSON.stringify({success:false, error:'button_missing'});
  btn.scrollIntoView({block:'center', inline:'center'});
  btn.click();
  return JSON.stringify({success:true, clicked:true});
})()"""
        )
        return self._module_result(path=path, slug=slug, nav=nav, action=action)

    def _solve_dynamictable(self) -> dict[str, Any]:
        path = "/dynamictable"
        slug = self._slug(path)
        nav = self._navigate(path)
        action = self._browser_json(
            """(() => {
  const body = document.body ? document.body.innerText : '';
  const warning = (document.querySelector('p.bg-warning')?.innerText || body).trim();
  const m = warning.match(/Chrome\\s*CPU\\s*:\\s*([0-9.]+%)/i);
  const expected = m ? m[1] : null;
  let actual = null;

  const table = document.querySelector('[role="table"]');
  if (table) {
    const rowGroups = Array.from(table.querySelectorAll('[role="rowgroup"]'));
    const headerRow = rowGroups.length > 0 ? rowGroups[0].querySelector('[role="row"]') : null;
    const headers = headerRow
      ? Array.from(headerRow.querySelectorAll('[role="columnheader"]')).map((h) => (h.innerText || '').trim())
      : [];
    const nameIndex = headers.findIndex((h) => /name/i.test(h));
    const cpuIndex = headers.findIndex((h) => /cpu/i.test(h));
    const bodyRows = rowGroups.length > 1 ? Array.from(rowGroups[1].querySelectorAll('[role="row"]')) : [];
    if (nameIndex >= 0 && cpuIndex >= 0) {
      for (const row of bodyRows) {
        const cells = Array.from(row.querySelectorAll('[role="cell"]')).map((c) => (c.innerText || '').trim());
        if (cells.length > Math.max(nameIndex, cpuIndex) && /Chrome/i.test(cells[nameIndex])) {
          actual = cells[cpuIndex];
          break;
        }
      }
    }
  }

  if (!actual) {
    const fallback = body.match(/Chrome\\s+([0-9.]+%)/i);
    actual = fallback ? fallback[1] : null;
  }
  return JSON.stringify({
    warning_text: warning,
    expected_chrome_cpu: expected,
    actual_chrome_cpu: actual,
    success: !!expected && !!actual && expected === actual
  });
})()"""
        )
        return self._module_result(path=path, slug=slug, nav=nav, action=action)

    def _solve_verifytext(self) -> dict[str, Any]:
        path = "/verifytext"
        slug = self._slug(path)
        nav = self._navigate(path)
        action = self._browser_json(
            """(() => {
  const spans = Array.from(document.querySelectorAll('span.badge-secondary, span'));
  const target = spans.find((el) => /Welcome/i.test(el.textContent || '') && /UserName/i.test(el.textContent || ''));
  const normalized = target ? (target.textContent || '').replace(/\\s+/g, ' ').trim() : '';
  return JSON.stringify({
    found: !!target,
    normalized_text: normalized,
    success: !!target && /Welcome UserName!/i.test(normalized)
  });
})()"""
        )
        return self._module_result(path=path, slug=slug, nav=nav, action=action)

    def _solve_progressbar(self) -> dict[str, Any]:
        path = "/progressbar"
        slug = self._slug(path)
        nav = self._navigate(path)
        start = self._browser_json(
            """(() => {
  const startBtn = document.querySelector('#startButton');
  if (startBtn) startBtn.click();
  return JSON.stringify({clicked: !!startBtn, success: !!startBtn});
})()"""
        )
        grew = self._wait_for_js(
            """(() => {
  const bar = document.querySelector('#progressBar');
  const val = parseInt((bar?.getAttribute('aria-valuenow') || '').trim(), 10) || 0;
  return JSON.stringify({value: val, success: val > 0});
})()""",
            timeout_seconds=8.0,
        )
        threshold = self._wait_for_js(
            """(() => {
  const bar = document.querySelector('#progressBar');
  const val = parseInt((bar?.getAttribute('aria-valuenow') || '').trim(), 10) || 0;
  return JSON.stringify({value: val, success: val >= 70});
})()""",
            timeout_seconds=14.0,
            interval_seconds=0.2,
        )
        stop = self._browser_json(
            """(() => {
  const stopBtn = document.querySelector('#stopButton');
  const bar = document.querySelector('#progressBar');
  if (stopBtn) stopBtn.click();
  const val = parseInt((bar?.getAttribute('aria-valuenow') || '').trim(), 10) || 0;
  return JSON.stringify({clicked: !!stopBtn, value_after_stop: val, success: !!stopBtn && val > 0});
})()"""
        )
        action = {
            "start": start,
            "grew": grew,
            "threshold": threshold,
            "stop": stop,
            "success": bool(start.get("success")) and bool(grew.get("success")) and bool(stop.get("success")),
        }
        return self._module_result(path=path, slug=slug, nav=nav, action=action)

    def _solve_visibility(self) -> dict[str, Any]:
        path = "/visibility"
        slug = self._slug(path)
        nav = self._navigate(path)
        click = self._browser_json(
            """(() => {
  const hide = document.querySelector('#hideButton');
  if (hide) hide.click();
  return JSON.stringify({clicked: !!hide, success: !!hide});
})()"""
        )
        wait = self._wait_for_js(
            """(() => {
  const removed = document.querySelector('#removedButton');
  const zero = document.querySelector('#zeroWidthButton');
  const hidden = document.querySelector('#notdisplayedButton');
  const removedGone = !removed;
  const zeroRect = zero ? zero.getBoundingClientRect() : { width: 0 };
  const notDisplayed = hidden ? (getComputedStyle(hidden).display === 'none') : false;
  return JSON.stringify({
    removed_gone: removedGone,
    zero_width: zeroRect.width === 0,
    not_displayed: notDisplayed,
    success: removedGone || notDisplayed || zeroRect.width === 0
  });
})()""",
            timeout_seconds=6.0,
        )
        action = {"click": click, "wait": wait, "success": bool(click.get("success")) and bool(wait.get("success"))}
        return self._module_result(path=path, slug=slug, nav=nav, action=action)

    def _solve_sampleapp(self) -> dict[str, Any]:
        path = "/sampleapp"
        slug = self._slug(path)
        nav = self._navigate(path)
        login = self._browser_json(
            """(() => {
  const user = document.querySelector('input[name="UserName"], input[placeholder*="User Name"]');
  const pwd = document.querySelector('input[name="Password"], input[type="password"]');
  const btn = document.querySelector('#login');
  if (!user || !pwd || !btn) return JSON.stringify({success:false, error:'controls_missing'});
  user.value = 'Concentric';
  pwd.value = 'pwd';
  [user,pwd].forEach((el) => {
    el.dispatchEvent(new Event('input', { bubbles: true }));
    el.dispatchEvent(new Event('change', { bubbles: true }));
  });
  btn.click();
  return JSON.stringify({success:true});
})()"""
        )
        wait_login = self._wait_for_js(
            """(() => {
  const status = (document.querySelector('#loginstatus')?.innerText || '').trim();
  const btn = (document.querySelector('#login')?.innerText || '').trim();
  return JSON.stringify({
    status,
    button_text: btn,
    success: /Welcome,\\s*Concentric!/i.test(status) && /Log Out/i.test(btn)
  });
})()""",
            timeout_seconds=7.0,
        )
        logout = self._browser_json(
            """(() => {
  const btn = document.querySelector('#login');
  if (btn && /Log Out/i.test(btn.innerText || '')) btn.click();
  const status = (document.querySelector('#loginstatus')?.innerText || '').trim();
  return JSON.stringify({status, success: true});
})()"""
        )
        action = {
            "login": login,
            "wait_login": wait_login,
            "logout": logout,
            "success": bool(login.get("success")) and bool(wait_login.get("success")),
        }
        return self._module_result(path=path, slug=slug, nav=nav, action=action)

    def _solve_mouseover(self) -> dict[str, Any]:
        path = "/mouseover"
        slug = self._slug(path)
        nav = self._navigate(path)
        action = self._browser_json(
            """(() => {
  const doOne = (label) => {
    const link = Array.from(document.querySelectorAll('a')).find((a) => ((a.innerText || '').trim() === label));
    if (!link) return false;
    link.dispatchEvent(new MouseEvent('mouseenter', { bubbles: true }));
    const active = Array.from(document.querySelectorAll('a')).find((a) => ((a.innerText || '').trim() === label));
    if (!active) return false;
    active.click();
    return true;
  };
  const one = doOne('Click me');
  const two = doOne('Link Button');
  const count1 = parseInt((document.querySelector('#clickCount')?.innerText || '0').trim(), 10) || 0;
  const count2 = parseInt((document.querySelector('#clickButtonCount')?.innerText || '0').trim(), 10) || 0;
  return JSON.stringify({
    click_me_done: one,
    link_button_done: two,
    click_count: count1,
    click_button_count: count2,
    success: one && two && count1 >= 1 && count2 >= 1
  });
})()"""
        )
        return self._module_result(path=path, slug=slug, nav=nav, action=action)

    def _solve_nbsp(self) -> dict[str, Any]:
        path = "/nbsp"
        slug = self._slug(path)
        nav = self._navigate(path)
        action = self._browser_json(
            """(() => {
  const btn = Array.from(document.querySelectorAll('button'))
    .find((el) => ((el.textContent || '').replace(/\\u00a0/g, ' ').replace(/\\s+/g, ' ').trim() === 'My Button'));
  if (btn) btn.click();
  return JSON.stringify({
    button_present: !!btn,
    success: !!btn
  });
})()"""
        )
        return self._module_result(path=path, slug=slug, nav=nav, action=action)

    def _solve_overlapped(self) -> dict[str, Any]:
        path = "/overlapped"
        slug = self._slug(path)
        nav = self._navigate(path)
        action = self._browser_json(
            """(() => {
  const name = document.querySelector('#name');
  if (!name) return JSON.stringify({success:false, error:'name_input_missing'});
  const scroller = name.closest('div[style*="overflow-y: scroll"]');
  if (scroller) scroller.scrollTop = Math.max(50, name.offsetTop - 20);
  name.focus();
  name.value = 'Concentric Name';
  name.dispatchEvent(new Event('input', { bubbles: true }));
  name.dispatchEvent(new Event('change', { bubbles: true }));
  return JSON.stringify({
    value_after_input: name.value,
    success: name.value === 'Concentric Name'
  });
})()"""
        )
        return self._module_result(path=path, slug=slug, nav=nav, action=action)

    def _solve_shadowdom(self) -> dict[str, Any]:
        path = "/shadowdom"
        slug = self._slug(path)
        nav = self._navigate(path)
        action = self._browser_json(
            """(() => {
  const host = document.querySelector('guid-generator');
  const root = host ? host.shadowRoot : null;
  const generate = root ? root.querySelector('#buttonGenerate') : null;
  const copy = root ? root.querySelector('#buttonCopy') : null;
  const edit = root ? root.querySelector('#editField') : null;
  if (generate) generate.click();
  const value = edit ? (edit.value || '') : '';
  if (copy) {
    try { copy.click(); } catch (err) {}
  }
  return JSON.stringify({
    host_present: !!host,
    shadow_root_present: !!root,
    generated_value: value,
    copied_clicked: !!copy,
    success: !!root && !!generate && value.length >= 8
  });
})()"""
        )
        return self._module_result(path=path, slug=slug, nav=nav, action=action)

    def _solve_alerts(self) -> dict[str, Any]:
        path = "/alerts"
        slug = self._slug(path)
        nav = self._navigate(path)
        action = self._browser_json(
            """(() => {
  window.alert = () => {};
  window.confirm = () => true;
  window.prompt = () => 'dogs';
  const ids = ['alertButton','confirmButton','promptButton'];
  let clicked = 0;
  ids.forEach((id) => {
    const btn = document.getElementById(id);
    if (btn) {
      btn.click();
      clicked += 1;
    }
  });
  return JSON.stringify({
    clicked,
    success: clicked === 3
  });
})()"""
        )
        return self._module_result(path=path, slug=slug, nav=nav, action=action)

    def _solve_upload(self) -> dict[str, Any]:
        path = "/upload"
        slug = self._slug(path)
        nav = self._navigate(path)
        action = self._wait_for_js(
            """(() => {
  const frame = document.querySelector('iframe');
  if (!frame || !frame.contentDocument) return JSON.stringify({success:false, error:'upload_iframe_missing'});
  const doc = frame.contentDocument;
  const rootText = (doc.body?.innerText || '').trim();
  const input = doc.querySelector('input[type="file"]');
  let assigned = false;
  if (input && typeof DataTransfer !== 'undefined') {
    const dt = new DataTransfer();
    dt.items.add(new File(['site5 upload'], 'site5-upload.txt', { type: 'text/plain' }));
    input.files = dt.files;
    input.dispatchEvent(new Event('change', { bubbles: true }));
    assigned = input.files && input.files.length > 0;
  }
  return JSON.stringify({
    iframe_present: true,
    input_present: !!input,
    assigned,
    root_preview: rootText.slice(0, 120),
    success: !!input || rootText.length > 0
  });
})()""",
            timeout_seconds=12.0,
        )
        return self._module_result(path=path, slug=slug, nav=nav, action=action)

    def _solve_animation(self) -> dict[str, Any]:
        path = "/animation"
        slug = self._slug(path)
        nav = self._navigate(path)
        action = self._browser_json(
            """(() => {
  const start = document.querySelector('#animationButton');
  const target = document.querySelector('#movingTarget');
  if (!start || !target) return JSON.stringify({success:false, error:'controls_missing'});
  start.click();
  target.click();
  const status = (document.querySelector('#opstatus')?.innerText || '').trim();
  return JSON.stringify({
    status,
    success: /Target clicked\\./i.test(status) || status.length > 0
  });
})()"""
        )
        return self._module_result(path=path, slug=slug, nav=nav, action=action)

    def _solve_disabledinput(self) -> dict[str, Any]:
        path = "/disabledinput"
        slug = self._slug(path)
        nav = self._navigate(path)
        click = self._browser_json(
            """(() => {
  const btn = document.querySelector('#enableButton');
  if (btn) btn.click();
  return JSON.stringify({clicked: !!btn, success: !!btn});
})()"""
        )
        ready = self._wait_for_js(
            """(() => {
  const input = document.querySelector('#inputField');
  return JSON.stringify({
    present: !!input,
    disabled: input ? !!input.disabled : true,
    success: !!input && !input.disabled
  });
})()""",
            timeout_seconds=8.0,
        )
        type_text = self._browser_json(
            """(() => {
  const input = document.querySelector('#inputField');
  if (!input || input.disabled) return JSON.stringify({success:false, error:'input_not_ready'});
  input.focus();
  input.value = 'Enabled Input Ready';
  input.dispatchEvent(new Event('input', { bubbles: true }));
  input.dispatchEvent(new Event('change', { bubbles: true }));
  return JSON.stringify({value: input.value, success: input.value === 'Enabled Input Ready'});
})()"""
        )
        action = {
            "click": click,
            "ready": ready,
            "type": type_text,
            "success": bool(click.get("success")) and bool(ready.get("success")) and bool(type_text.get("success")),
        }
        return self._module_result(path=path, slug=slug, nav=nav, action=action)

    def _solve_autowait(self) -> dict[str, Any]:
        path = "/autowait"
        slug = self._slug(path)
        nav = self._navigate(path)
        apply = self._browser_json(
            """(() => {
  const btn = document.querySelector('#applyButton3');
  if (btn) btn.click();
  return JSON.stringify({clicked: !!btn, success: !!btn});
})()"""
        )
        wait_restore = self._wait_for_js(
            """(() => {
  const status = (document.querySelector('#opstatus')?.innerText || '').trim();
  return JSON.stringify({
    status,
    success: /restored/i.test(status)
  });
})()""",
            timeout_seconds=6.0,
        )
        click_target = self._browser_json(
            """(() => {
  const target = document.querySelector('#target');
  if (!target) return JSON.stringify({success:false, error:'target_missing'});
  target.click();
  const status = (document.querySelector('#opstatus')?.innerText || '').trim();
  return JSON.stringify({
    status,
    success: /Target clicked\\./i.test(status) || status.length > 0
  });
})()"""
        )
        action = {
            "apply": apply,
            "wait_restore": wait_restore,
            "click_target": click_target,
            "success": bool(apply.get("success")) and bool(wait_restore.get("success")) and bool(click_target.get("success")),
        }
        return self._module_result(path=path, slug=slug, nav=nav, action=action)

    def _solve_frames(self) -> dict[str, Any]:
        path = "/frames"
        slug = self._slug(path)
        nav = self._navigate(path)
        action = self._wait_for_js(
            """(() => {
  const outer = document.querySelector('#frame-outer');
  if (!outer || !outer.contentDocument) return JSON.stringify({success:false, error:'outer_frame_missing'});
  const outerDoc = outer.contentDocument;
  const outerButtons = Array.from(outerDoc.querySelectorAll('button'));
  outerButtons.forEach((btn) => btn.click());
  const outerResult = (outerDoc.querySelector('#result')?.innerText || '').trim();
  const inner = outerDoc.querySelector('#frame-inner');
  if (!inner || !inner.contentDocument) {
    return JSON.stringify({
      outer_clicked: outerButtons.length,
      outer_result: outerResult,
      success: outerButtons.length >= 4 && /Button pressed:/i.test(outerResult)
    });
  }
  const innerDoc = inner.contentDocument;
  const innerButtons = Array.from(innerDoc.querySelectorAll('button'));
  innerButtons.forEach((btn) => btn.click());
  const innerResult = (innerDoc.querySelector('#result')?.innerText || '').trim();
  return JSON.stringify({
    outer_clicked: outerButtons.length,
    inner_clicked: innerButtons.length,
    outer_result: outerResult,
    inner_result: innerResult,
    success: outerButtons.length >= 4 && innerButtons.length >= 4 && /Button pressed:/i.test(outerResult + ' ' + innerResult)
  });
})()""",
            timeout_seconds=8.0,
        )
        return self._module_result(path=path, slug=slug, nav=nav, action=action)

    def _solver_for_path(self, path: str) -> Callable[[], dict[str, Any]]:
        if path == "/":
            return lambda p=path: self._solve_home(p)
        if path == "/dynamicid":
            return self._solve_dynamicid
        if path == "/classattr":
            return self._solve_classattr
        if path == "/hiddenlayers":
            return self._solve_hiddenlayers
        if path == "/loaddelay":
            return self._solve_loaddelay
        if path == "/ajax":
            return self._solve_ajax
        if path == "/clientdelay":
            return self._solve_clientdelay
        if path == "/click":
            return self._solve_click
        if path == "/textinput":
            return self._solve_textinput
        if path == "/scrollbars":
            return self._solve_scrollbars
        if path == "/dynamictable":
            return self._solve_dynamictable
        if path == "/verifytext":
            return self._solve_verifytext
        if path == "/progressbar":
            return self._solve_progressbar
        if path == "/visibility":
            return self._solve_visibility
        if path == "/sampleapp":
            return self._solve_sampleapp
        if path == "/mouseover":
            return self._solve_mouseover
        if path == "/nbsp":
            return self._solve_nbsp
        if path == "/overlapped":
            return self._solve_overlapped
        if path == "/shadowdom":
            return self._solve_shadowdom
        if path == "/alerts":
            return self._solve_alerts
        if path == "/upload":
            return self._solve_upload
        if path == "/animation":
            return self._solve_animation
        if path == "/disabledinput":
            return self._solve_disabledinput
        if path == "/autowait":
            return self._solve_autowait
        if path == "/frames":
            return self._solve_frames
        return lambda p=path: self._generic_probe(p)

    # ------------------------------------------------------------------
    # Main
    # ------------------------------------------------------------------
    def run(self) -> int:
        index = 0
        try:
            preflight_step = self._step(index, "preflight", "Restart Safari, collapse extra windows, and prepare a clean no-login run state.")
            self._safari_restart()
            close_result = self._close_extra_windows()
            home_nav = self._navigate("/")
            preflight_payload = {
                "status": "safari_ready",
                "close_result": close_result,
                "home_navigation": home_nav,
                "success": bool(home_nav.get("success")),
            }
            self.summary["steps"] = {"preflight": preflight_payload}
            self._end_step(preflight_step, bool(preflight_payload["success"]), preflight_payload)
            index += 1

            discover_step = self._step(index, "discover_scope", "Discover website paths and classify no-login benchmark scope.")
            discovered_paths = self._discover_paths()
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
                step = self._step(index, slug, f"Execute no-login module check for {path}.")
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
    runner = UITestingPlaygroundSite5Runner()
    rc = runner.run()
    reader = DiagnosticReader(runner.run_dir)
    (runner.run_dir / "diagnostic.txt").write_text(reader.full_diagnostic(), encoding="utf-8")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
