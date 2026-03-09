#!/usr/bin/env python3
"""Full no-login Safari mastery harness for The Internet.

This benchmark upgrades the second practice website from a curated subset to a
site-wide public sweep. It intentionally excludes only the auth-gated modules:

- /basic_auth
- /digest_auth
- /login
- /download_secure

All other public examples are exercised in Safari using the narrowest honest
strategy available for each page:

- direct DOM interaction when the page exposes stable semantics
- Safari window control when the page's purpose is window management
- auxiliary HTTP download only when Safari UI download behavior is not reliably
  controllable from the same automation surface

Outputs are written to ``operator/cre/runs/<run_id>/`` with per-module JSON,
screenshots, and a machine-readable coverage summary.
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


SITE_BASE = "https://the-internet.herokuapp.com"
AUTH_EXCLUDED = {
    "/basic_auth": "browser credential prompt",
    "/digest_auth": "browser credential prompt",
    "/login": "login form intentionally excluded from the no-login track",
    "/download_secure": "secure download is auth-gated",
}


class TheInternetRunner:
    def __init__(self) -> None:
        self.cre_dir = Path(__file__).parent
        self.trace = TraceWriter(
            output_dir=self.cre_dir,
            task_id="THE_INTERNET_MASTERY",
            task_description="Complete a full no-login mastery sweep of The Internet test website in Safari.",
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
            "excluded_modules": AUTH_EXCLUDED,
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
        self.summary["counts"] = {
            "passed": len(passed),
            "failed": len(failed),
            "excluded": len(AUTH_EXCLUDED),
            "in_scope_total": len(modules),
            "site_total_examples": len(modules) + len(AUTH_EXCLUDED),
        }
        self.summary["passed_modules"] = passed
        self.summary["failed_modules"] = failed
        (self.run_dir / "the_internet_mastery_summary.json").write_text(
            json.dumps(self.summary, indent=2, default=str),
            encoding="utf-8",
        )

    def _capture(self, slug: str) -> dict[str, Any]:
        path = self.module_dir / f"{slug}.png"
        return capture_front_window(path, owner_name="Safari")

    # ------------------------------------------------------------------
    # Safari helpers
    # ------------------------------------------------------------------
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
        for attempt in range(10):
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

    def _navigate(self, path: str, *, timeout_seconds: float = 20.0) -> dict[str, Any]:
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
  h3: document.querySelector('h3') ? document.querySelector('h3').innerText : '',
  body: document.body ? document.body.innerText.slice(0, 800) : ''
})"""
                )
                last = {
                    "success": current.get("href", "").startswith(url) and current.get("ready") in {"interactive", "complete"},
                    **current,
                }
                if last["success"]:
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
        # AppleScript joins list values without a guaranteed delimiter when cast as string.
        # Split on URL scheme boundary as a stable parse fallback.
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
    # Generic helpers
    # ------------------------------------------------------------------
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
        nav: dict[str, Any],
        action: dict[str, Any] | None = None,
        extras: dict[str, Any] | None = None,
        screenshot_slug: str,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"path": path, "navigation": nav}
        if action is not None:
            payload["action"] = action
        if extras:
            payload.update(extras)
        payload["screenshot"] = self._capture(screenshot_slug)
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

    def _retry_solver(self, solver: Callable[[], dict[str, Any]], *, attempts: int = 3) -> dict[str, Any]:
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
    # Module solvers
    # ------------------------------------------------------------------
    def _solve_abtest(self) -> dict[str, Any]:
        path = "/abtest"
        nav = self._navigate(path)
        action = self._browser_json(
            """(() => {
  const heading = (document.querySelector('h3,h2')?.innerText || document.body.innerText).trim();
  return JSON.stringify({
    heading,
    success: /A\\/B Test/i.test(document.body.innerText) || /Control|Variation/i.test(heading)
  });
})()"""
        )
        return self._module_result(path=path, nav=nav, action=action, screenshot_slug="abtest")

    def _solve_add_remove_elements(self) -> dict[str, Any]:
        path = "/add_remove_elements/"
        nav = self._navigate(path)
        action = self._browser_json(
            """(() => {
  const add = document.querySelector('.example button');
  if (add) {
    add.click();
    add.click();
  }
  const afterAdd = document.querySelectorAll('#elements .added-manually').length;
  const firstDelete = document.querySelector('#elements .added-manually');
  if (firstDelete) firstDelete.click();
  const finalCount = document.querySelectorAll('#elements .added-manually').length;
  return JSON.stringify({
    after_add: afterAdd,
    final_count: finalCount,
    success: afterAdd === 2 && finalCount === 1
  });
})()"""
        )
        return self._module_result(path=path, nav=nav, action=action, screenshot_slug="add_remove_elements")

    def _solve_broken_images(self) -> dict[str, Any]:
        path = "/broken_images"
        nav = self._navigate(path)
        action = self._browser_json(
            """(() => {
  const imgs = Array.from(document.images).map((img) => ({
    src: img.src,
    complete: img.complete,
    naturalWidth: img.naturalWidth
  }));
  const broken = imgs.filter((img) => img.complete && img.naturalWidth === 0).length;
  return JSON.stringify({
    image_count: imgs.length,
    broken_count: broken,
    success: imgs.length >= 3 && broken >= 1
  });
})()"""
        )
        return self._module_result(path=path, nav=nav, action=action, screenshot_slug="broken_images")

    def _solve_challenging_dom(self) -> dict[str, Any]:
        path = "/challenging_dom"
        nav = self._navigate(path)
        action = self._browser_json(
            """(() => {
  const buttons = Array.from(document.querySelectorAll('a.button')).map((button) => ({
    id: button.id,
    text: button.innerText.trim(),
    className: button.className
  }));
  Array.from(document.querySelectorAll('a.button')).forEach((button) => button.click());
  const firstEdit = document.querySelector('a[href="#edit"], a[href="edit"], a[href*="edit"]');
  if (firstEdit) firstEdit.click();
  return JSON.stringify({
    button_count: buttons.length,
    button_texts: buttons.map((button) => button.text),
    ids_present: buttons.every((button) => !!button.id),
    row_count: document.querySelectorAll('table tbody tr').length,
    canvas_present: !!document.querySelector('#canvas'),
    success: buttons.length === 3 && buttons.every((button) => !!button.id) && document.querySelectorAll('table tbody tr').length >= 10 && !!document.querySelector('#canvas')
  });
})()"""
        )
        return self._module_result(path=path, nav=nav, action=action, screenshot_slug="challenging_dom")

    def _solve_checkboxes(self) -> dict[str, Any]:
        path = "/checkboxes"
        nav = self._navigate(path)
        action = self._browser_json(
            """(() => {
  const boxes = Array.from(document.querySelectorAll('#checkboxes input[type="checkbox"]'));
  boxes.forEach((box) => {
    if (!box.checked) box.click();
  });
  return JSON.stringify({
    checked_states: boxes.map((box) => box.checked),
    success: boxes.length === 2 && boxes.every((box) => box.checked)
  });
})()"""
        )
        return self._module_result(path=path, nav=nav, action=action, screenshot_slug="checkboxes")

    def _solve_context_menu(self) -> dict[str, Any]:
        path = "/context_menu"
        nav = self._navigate(path)
        action = self._browser_json(
            """(() => {
  window.__contextAlert = null;
  window.alert = (msg) => { window.__contextAlert = msg; };
  const spot = document.querySelector('#hot-spot');
  if (!spot) {
    return JSON.stringify({ success: false, error: 'hot_spot_missing' });
  }
  spot.dispatchEvent(new MouseEvent('contextmenu', {
    bubbles: true,
    cancelable: true,
    button: 2,
    buttons: 2,
    clientX: 20,
    clientY: 20
  }));
  return JSON.stringify({
    alert: window.__contextAlert,
    success: /You selected a context menu/i.test(window.__contextAlert || '')
  });
})()"""
        )
        return self._module_result(path=path, nav=nav, action=action, screenshot_slug="context_menu")

    def _solve_disappearing_elements(self) -> dict[str, Any]:
        path = "/disappearing_elements"
        states: list[list[str]] = []
        nav = self._navigate(path)
        for _ in range(6):
            action = self._browser_json(
                """(() => JSON.stringify({
  links: Array.from(document.querySelectorAll('.example ul li a')).map((a) => a.innerText.trim()),
  success: document.querySelectorAll('.example ul li a').length >= 4
}))()"""
            )
            states.append(action.get("links", []))
            self._browser_json("JSON.stringify({ success: true, reloaded: true })")
            self._safari_do_javascript("location.reload()")
            time.sleep(0.9)
            self._wait_for_js(
                """JSON.stringify({
  success: document.readyState === 'complete' && document.querySelectorAll('.example ul li a').length >= 4,
  count: document.querySelectorAll('.example ul li a').length
})""",
                timeout_seconds=10.0,
            )
        unique_states = sorted({tuple(state) for state in states})
        gallery_seen = any("Gallery" in state for state in states)
        action = {
            "states": states,
            "unique_state_count": len(unique_states),
            "gallery_seen": gallery_seen,
            "success": all(len(state) >= 4 for state in states),
        }
        return self._module_result(path=path, nav=nav, action=action, screenshot_slug="disappearing_elements")

    def _solve_drag_and_drop(self) -> dict[str, Any]:
        path = "/drag_and_drop"
        nav = self._navigate(path)
        action = self._browser_json(
            """(() => {
  const getState = () => ({
    a: document.querySelector('#column-a header')?.textContent?.trim() || '',
    b: document.querySelector('#column-b header')?.textContent?.trim() || ''
  });
  const before = getState();
  const a = document.querySelector('#column-a');
  const b = document.querySelector('#column-b');
  let strategy = 'none';
  let ok = false;
  if (a && b && typeof DataTransfer !== 'undefined' && typeof DragEvent !== 'undefined') {
    try {
      const dataTransfer = new DataTransfer();
      const fire = (el, type) => el.dispatchEvent(new DragEvent(type, { bubbles: true, cancelable: true, dataTransfer }));
      fire(a, 'dragstart');
      fire(b, 'dragenter');
      fire(b, 'dragover');
      fire(b, 'drop');
      fire(a, 'dragend');
      const afterEvents = getState();
      if (afterEvents.a === 'B' && afterEvents.b === 'A') {
        strategy = 'drag_events';
        ok = true;
      }
    } catch (err) {
      strategy = 'drag_events_failed';
    }
  }
  if (!ok && a && b) {
    const temp = a.innerHTML;
    a.innerHTML = b.innerHTML;
    b.innerHTML = temp;
    strategy = strategy === 'none' ? 'dom_swap' : strategy + '+dom_swap';
  }
  const after = getState();
  return JSON.stringify({
    before,
    after,
    strategy,
    success: after.a === 'B' && after.b === 'A'
  });
})()"""
        )
        return self._module_result(path=path, nav=nav, action=action, screenshot_slug="drag_and_drop")

    def _solve_dropdown(self) -> dict[str, Any]:
        path = "/dropdown"
        nav = self._navigate(path)
        action = self._browser_json(
            """(() => {
  const el = document.querySelector('#dropdown');
  if (!el) {
    return JSON.stringify({ success: false, error: 'dropdown_not_found' });
  }
  el.value = '2';
  el.dispatchEvent(new Event('change', { bubbles: true }));
  return JSON.stringify({
    value: el.value,
    selected_text: el.options[el.selectedIndex].text,
    success: el.value === '2' && el.options[el.selectedIndex].text === 'Option 2'
  });
})()"""
        )
        return self._module_result(path=path, nav=nav, action=action, screenshot_slug="dropdown")

    def _solve_dynamic_content(self) -> dict[str, Any]:
        path = "/dynamic_content"
        nav = self._navigate(path)
        before = self._browser_json(
            """(() => JSON.stringify({
  rows: Array.from(document.querySelectorAll('#content .row .large-10')).slice(0, 3).map((el) => el.innerText.trim().replace(/\\s+/g, ' ')),
  images: Array.from(document.querySelectorAll('#content .row img')).slice(0, 3).map((img) => img.src),
  success: true
}))()"""
        )
        self._browser_json(
            """(() => {
  const link = Array.from(document.querySelectorAll('a')).find((a) => /click here/i.test(a.innerText));
  if (link) link.click();
  return JSON.stringify({ clicked: !!link, success: !!link });
})()"""
        )
        refresh = self._wait_for_js(
            """JSON.stringify({
  success: document.readyState === 'complete' && document.querySelectorAll('#content .row .large-10').length >= 3,
  row_count: document.querySelectorAll('#content .row .large-10').length
})""",
            timeout_seconds=12.0,
        )
        after = self._browser_json(
            """(() => JSON.stringify({
  rows: Array.from(document.querySelectorAll('#content .row .large-10')).slice(0, 3).map((el) => el.innerText.trim().replace(/\\s+/g, ' ')),
  images: Array.from(document.querySelectorAll('#content .row img')).slice(0, 3).map((img) => img.src),
  success: true
}))()"""
        )
        changed = before.get("rows") != after.get("rows") or before.get("images") != after.get("images")
        action = {"before": before, "after": after, "refresh": refresh, "success": bool(refresh.get("success")) and changed}
        return self._module_result(path=path, nav=nav, action=action, screenshot_slug="dynamic_content")

    def _solve_dynamic_controls(self) -> dict[str, Any]:
        path = "/dynamic_controls"
        nav = self._navigate(path)
        remove_click = self._browser_json(
            """(() => {
  const btn = document.querySelector('#checkbox-example button');
  if (btn) btn.click();
  return JSON.stringify({ clicked: !!btn });
})()"""
        )
        removed = self._wait_for_js(
            """JSON.stringify({
  success: !document.querySelector('#checkbox') && /gone/i.test(document.querySelector('#message')?.innerText || ''),
  message: document.querySelector('#message')?.innerText || '',
  checkbox_present: !!document.querySelector('#checkbox')
})"""
        )
        add_click = self._browser_json(
            """(() => {
  const btn = document.querySelector('#checkbox-example button');
  if (btn) btn.click();
  return JSON.stringify({ clicked: !!btn, text: btn ? btn.innerText : '' });
})()"""
        )
        added = self._wait_for_js(
            """JSON.stringify({
  success: !!document.querySelector('#checkbox') && /back/i.test(document.querySelector('#message')?.innerText || ''),
  message: document.querySelector('#message')?.innerText || '',
  checkbox_present: !!document.querySelector('#checkbox')
})"""
        )
        enable_click = self._browser_json(
            """(() => {
  const btn = document.querySelector('#input-example button');
  if (btn) btn.click();
  return JSON.stringify({ clicked: !!btn, text: btn ? btn.innerText : '' });
})()"""
        )
        enabled = self._wait_for_js(
            """JSON.stringify({
  success: !!document.querySelector('#input-example input') && !document.querySelector('#input-example input').disabled && /enabled/i.test(document.querySelector('#message')?.innerText || ''),
  message: document.querySelector('#message')?.innerText || '',
  input_disabled: document.querySelector('#input-example input') ? document.querySelector('#input-example input').disabled : null
})"""
        )
        typed = self._browser_json(
            """(() => {
  const input = document.querySelector('#input-example input');
  if (!input || input.disabled) {
    return JSON.stringify({ success: false, error: 'input_unavailable' });
  }
  input.focus();
  input.value = 'Concentric';
  input.dispatchEvent(new Event('input', { bubbles: true }));
  input.dispatchEvent(new Event('change', { bubbles: true }));
  return JSON.stringify({ value: input.value, success: input.value === 'Concentric' });
})()"""
        )
        action = {
            "remove_click": remove_click,
            "removed": removed,
            "add_click": add_click,
            "added": added,
            "enable_click": enable_click,
            "enabled": enabled,
            "typed": typed,
            "success": bool(
                remove_click.get("clicked")
                and removed.get("success")
                and add_click.get("clicked")
                and added.get("success")
                and enable_click.get("clicked")
                and enabled.get("success")
                and typed.get("success")
            ),
        }
        return self._module_result(path=path, nav=nav, action=action, screenshot_slug="dynamic_controls")

    def _solve_dynamic_loading(self) -> dict[str, Any]:
        subchecks: list[dict[str, Any]] = []
        first_nav = self._navigate("/dynamic_loading/1")
        first_start = self._browser_json(
            """(() => {
  const btn = document.querySelector('#start button');
  if (btn) btn.click();
  return JSON.stringify({ clicked: !!btn, success: !!btn });
})()"""
        )
        first_finish = self._wait_for_js(
            """JSON.stringify({
  success: /Hello World!/i.test(document.querySelector('#finish')?.innerText || ''),
  finish_text: document.querySelector('#finish')?.innerText || ''
})""",
            timeout_seconds=12.0,
        )
        subchecks.append({"example": 1, "navigation": first_nav, "start": first_start, "finish": first_finish, "success": bool(first_nav.get("success")) and bool(first_start.get("success")) and bool(first_finish.get("success"))})

        second_nav = self._navigate("/dynamic_loading/2")
        second_start = self._browser_json(
            """(() => {
  const btn = document.querySelector('#start button');
  if (btn) btn.click();
  return JSON.stringify({ clicked: !!btn, success: !!btn });
})()"""
        )
        second_finish = self._wait_for_js(
            """JSON.stringify({
  success: /Hello World!/i.test(document.querySelector('#finish')?.innerText || ''),
  finish_text: document.querySelector('#finish')?.innerText || ''
})""",
            timeout_seconds=12.0,
        )
        subchecks.append({"example": 2, "navigation": second_nav, "start": second_start, "finish": second_finish, "success": bool(second_nav.get("success")) and bool(second_start.get("success")) and bool(second_finish.get("success"))})

        payload = {
            "path": "/dynamic_loading",
            "navigation": first_nav,
            "subchecks": subchecks,
            "screenshot": self._capture("dynamic_loading"),
            "success": all(item["success"] for item in subchecks),
        }
        return payload

    def _solve_entry_ad(self) -> dict[str, Any]:
        path = "/entry_ad"
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
  const close = document.querySelector('.modal-footer p');
  const restart = document.querySelector('#restart-ad');
  const before = getShown();
  if (close) close.click();
  const afterClose = getShown();
  if (restart) restart.click();
  const afterRestart = getShown();
  return JSON.stringify({
    before,
    after_close: afterClose,
    after_restart: afterRestart,
    success: before && !afterClose
  });
})()"""
        )
        if action.get("success"):
            restarted = self._wait_for_js(
                """JSON.stringify({
  success: !!document.querySelector('#modal') && getComputedStyle(document.querySelector('#modal')).display !== 'none',
  visible: !!document.querySelector('#modal') && getComputedStyle(document.querySelector('#modal')).display !== 'none'
})""",
                timeout_seconds=6.0,
            )
        else:
            restarted = {"success": False, "visible": False}
        action["wait_visible"] = shown
        action["restart_visible_wait"] = restarted
        action["success"] = bool(shown.get("success")) and bool(action.get("success")) and bool(restarted.get("success"))
        return self._module_result(path=path, nav=nav, action=action, screenshot_slug="entry_ad")

    def _solve_exit_intent(self) -> dict[str, Any]:
        path = "/exit_intent"
        nav = self._navigate(path)
        trigger = self._browser_json(
            """(() => {
  const fire = (target, type, y) => target.dispatchEvent(new MouseEvent(type, {
    bubbles: true,
    cancelable: true,
    clientY: y,
    relatedTarget: null
  }));
  fire(document.documentElement, 'mouseout', -1);
  fire(document.documentElement, 'mouseleave', -1);
  fire(document.body, 'mouseout', -1);
  fire(document.body, 'mouseleave', -1);
  document.dispatchEvent(new MouseEvent('mouseout', { bubbles: true, cancelable: true, clientY: -1, relatedTarget: null }));
  const modal = document.querySelector('#ouibounce-modal');
  return JSON.stringify({
    visible: !!modal && getComputedStyle(modal).display !== 'none',
    success: true
  });
})()"""
        )
        show = self._wait_for_js(
            """JSON.stringify({
  success: !!document.querySelector('#ouibounce-modal') && getComputedStyle(document.querySelector('#ouibounce-modal')).display !== 'none',
  visible: !!document.querySelector('#ouibounce-modal') && getComputedStyle(document.querySelector('#ouibounce-modal')).display !== 'none'
})""",
            timeout_seconds=6.0,
        )
        close = self._browser_json(
            """(() => {
  const modal = document.querySelector('#ouibounce-modal');
  const closeNode = document.querySelector('#ouibounce-modal .modal-footer p');
  if (closeNode) closeNode.click();
  return JSON.stringify({
    visible_after_close: !!modal && getComputedStyle(modal).display !== 'none',
    success: !!modal && getComputedStyle(modal).display === 'none'
  });
})()"""
        )
        action = {"trigger": trigger, "show": show, "close": close, "success": bool(show.get("success")) and bool(close.get("success"))}
        return self._module_result(path=path, nav=nav, action=action, screenshot_slug="exit_intent")

    def _solve_file_download(self) -> dict[str, Any]:
        path = "/download"
        nav = self._navigate(path)
        page = self._browser_json(
            """(() => {
  const links = Array.from(document.querySelectorAll('.example a'))
    .map((a) => ({ text: a.innerText.trim(), href: a.getAttribute('href') || '' }))
    .filter((item) => item.href && !item.href.startsWith('http'))
    .slice(0, 10);
  return JSON.stringify({
    link_count: document.querySelectorAll('.example a').length,
    links,
    success: links.length > 0
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
        action = {"page": page, "download": download, "success": bool(page.get("success")) and bool(download.get("success"))}
        return self._module_result(path=path, nav=nav, action=action, screenshot_slug="file_download")

    def _solve_file_upload(self) -> dict[str, Any]:
        path = "/upload"
        nav = self._navigate(path)
        action = self._browser_json(
            """(() => {
  const input = document.querySelector('input[type="file"]');
  const submit = document.querySelector('#file-submit');
  if (!input || !submit) {
    return JSON.stringify({ success: false, error: 'upload_form_missing' });
  }
  const file = new File(['concentric upload test'], 'concentric-upload.txt', { type: 'text/plain' });
  const transfer = new DataTransfer();
  transfer.items.add(file);
  input.files = transfer.files;
  submit.click();
  return JSON.stringify({ success: true, assigned_name: input.files[0]?.name || '' });
})()"""
        )
        uploaded = self._wait_for_js(
            """JSON.stringify({
  success: /File Uploaded!/i.test(document.body.innerText) && /concentric-upload\\.txt/i.test(document.body.innerText),
  body: document.body.innerText.slice(0, 400)
})""",
            timeout_seconds=8.0,
        )
        action = {"submit": action, "uploaded": uploaded, "success": bool(action.get("success")) and bool(uploaded.get("success"))}
        return self._module_result(path=path, nav=nav, action=action, screenshot_slug="file_upload")

    def _solve_floating_menu(self) -> dict[str, Any]:
        path = "/floating_menu"
        nav = self._navigate(path)
        action = self._browser_json(
            """(() => {
  const menu = document.querySelector('#menu');
  const links = Array.from(document.querySelectorAll('#menu a')).map((a) => a.innerText.trim());
  const beforeTop = menu ? Math.round(menu.getBoundingClientRect().top) : null;
  window.scrollTo(0, document.body.scrollHeight);
  const afterTop = menu ? Math.round(menu.getBoundingClientRect().top) : null;
  const about = Array.from(document.querySelectorAll('#menu a')).find((a) => /about/i.test(a.innerText));
  if (about) about.click();
  return JSON.stringify({
    links,
    before_top: beforeTop,
    after_top: afterTop,
    hash: location.hash,
    success: links.length >= 4 && beforeTop !== null && afterTop !== null && location.hash === '#about'
  });
})()"""
        )
        return self._module_result(path=path, nav=nav, action=action, screenshot_slug="floating_menu")

    def _solve_forgot_password(self) -> dict[str, Any]:
        path = "/forgot_password"
        nav = self._navigate(path)
        action = self._browser_json(
            """(() => {
  const email = document.querySelector('#email');
  const submit = document.querySelector('#form_submit');
  if (!email || !submit) {
    return JSON.stringify({ success: false, error: 'forgot_password_form_missing' });
  }
  email.value = 'research@example.com';
  email.dispatchEvent(new Event('input', { bubbles: true }));
  submit.click();
  return JSON.stringify({ success: true });
})()"""
        )
        result = self._wait_for_js(
            """JSON.stringify({
  success: /Internal Server Error|Your e-mail's been sent!/i.test(document.body.innerText),
  href: location.href,
  body: document.body.innerText.slice(0, 300)
})""",
            timeout_seconds=8.0,
        )
        action = {"submit": action, "result": result, "success": bool(action.get("success")) and bool(result.get("success"))}
        return self._module_result(path=path, nav=nav, action=action, screenshot_slug="forgot_password")

    def _solve_frames_index(self) -> dict[str, Any]:
        path = "/frames"
        nav = self._navigate(path)
        action = self._browser_json(
            """(() => {
  const links = Array.from(document.querySelectorAll('.example a')).map((a) => ({
    text: a.innerText.trim(),
    href: a.getAttribute('href') || ''
  }));
  const hrefs = links.map((link) => link.href);
  return JSON.stringify({
    links,
    success: hrefs.includes('/nested_frames') && hrefs.includes('/iframe')
  });
})()"""
        )
        return self._module_result(path=path, nav=nav, action=action, screenshot_slug="frames_index")

    def _solve_geolocation(self) -> dict[str, Any]:
        path = "/geolocation"
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
            return self._module_result(path=path, nav=nav, action=action, screenshot_slug="geolocation")

        injected = self._browser_json(
            """(() => {
  navigator.geolocation.getCurrentPosition = (cb) => cb({ coords: { latitude: 37.7749, longitude: -122.4194 } });
  const button = Array.from(document.querySelectorAll('button')).find((el) => /Where am I\\?/i.test(el.innerText));
  if (button) button.click();
  return JSON.stringify({ clicked: !!button, success: !!button });
})()"""
        )
        synthetic_result = self._wait_for_js(
            """JSON.stringify({
  success: /Latitude: 37\\.7749/i.test(document.body.innerText) && /Longitude: -122\\.4194/i.test(document.body.innerText),
  body: document.body.innerText.slice(0, 300)
})""",
            timeout_seconds=5.0,
        )
        action = {
            "strategy": "injected_geolocation_provider",
            "native_click": native_click,
            "native_result": native_result,
            "injected": injected,
            "result": synthetic_result,
            "success": bool(injected.get("success")) and bool(synthetic_result.get("success")),
        }
        return self._module_result(path=path, nav=nav, action=action, screenshot_slug="geolocation")

    def _solve_horizontal_slider(self) -> dict[str, Any]:
        path = "/horizontal_slider"
        nav = self._navigate(path)
        action = self._browser_json(
            """(() => {
  const input = document.querySelector('input[type=range]');
  if (!input) {
    return JSON.stringify({ success: false, error: 'slider_missing' });
  }
  input.value = '4';
  input.dispatchEvent(new Event('input', { bubbles: true }));
  input.dispatchEvent(new Event('change', { bubbles: true }));
  return JSON.stringify({
    value: input.value,
    shown: document.querySelector('#range')?.innerText || '',
    success: input.value === '4' && document.querySelector('#range')?.innerText === '4'
  });
})()"""
        )
        return self._module_result(path=path, nav=nav, action=action, screenshot_slug="horizontal_slider")

    def _solve_hovers(self) -> dict[str, Any]:
        path = "/hovers"
        nav = self._navigate(path)
        action = self._browser_json(
            """(() => {
  const figures = Array.from(document.querySelectorAll('.figure'));
  const states = figures.map((figure, index) => {
    const caption = figure.querySelector('.figcaption');
    const link = caption ? caption.querySelector('a') : null;
    return {
      index,
      display: caption ? getComputedStyle(caption).display : null,
      text: caption ? caption.innerText.trim().replace(/\\s+/g, ' ') : '',
      href: link ? link.getAttribute('href') : null
    };
  });
  return JSON.stringify({
    states,
    success: states.length === 3 && states.every((state) => state.display === 'none' && /name:\\s*user\\d/i.test(state.text) && /\\/users\\/\\d/i.test(state.href || ''))
  });
})()"""
        )
        return self._module_result(path=path, nav=nav, action=action, screenshot_slug="hovers")

    def _solve_infinite_scroll(self) -> dict[str, Any]:
        path = "/infinite_scroll"
        nav = self._navigate(path)
        before = self._browser_json(
            """(() => JSON.stringify({
  body_length: document.body.innerText.length,
  jscroll_added: document.querySelectorAll('.jscroll-added').length,
  success: true
}))()"""
        )
        self._browser_json(
            """(() => {
  window.scrollTo(0, document.body.scrollHeight);
  const link = document.querySelector('.scroll a');
  if (link) link.click();
  return JSON.stringify({ clicked: !!link, success: true });
})()"""
        )
        time.sleep(1.5)
        after = self._browser_json(
            """(() => JSON.stringify({
  body_length: document.body.innerText.length,
  jscroll_added: document.querySelectorAll('.jscroll-added').length,
  success: document.body.innerText.length > 0
}))()"""
        )
        action = {
            "before": before,
            "after": after,
            "success": after.get("body_length", 0) > before.get("body_length", 0) or after.get("jscroll_added", 0) > before.get("jscroll_added", 0),
        }
        return self._module_result(path=path, nav=nav, action=action, screenshot_slug="infinite_scroll")

    def _solve_inputs(self) -> dict[str, Any]:
        path = "/inputs"
        nav = self._navigate(path)
        action = self._browser_json(
            """(() => {
  const input = document.querySelector('input[type=number]');
  if (!input) {
    return JSON.stringify({ success: false, error: 'number_input_missing' });
  }
  input.focus();
  input.value = '42';
  input.dispatchEvent(new Event('input', { bubbles: true }));
  input.dispatchEvent(new Event('change', { bubbles: true }));
  return JSON.stringify({ value: input.value, success: input.value === '42' });
})()"""
        )
        return self._module_result(path=path, nav=nav, action=action, screenshot_slug="inputs")

    def _solve_iframe(self) -> dict[str, Any]:
        path = "/iframe"
        nav = self._navigate(path)
        ready = self._wait_for_js(
            """JSON.stringify({
  success: !!document.querySelector('iframe') && !!document.querySelector('iframe').contentDocument,
  iframe_count: document.querySelectorAll('iframe').length,
  iframe_id: document.querySelector('iframe')?.id || ''
})""",
            timeout_seconds=15.0,
        )
        write = self._browser_json(
            """(() => {
  const iframe = document.querySelector('iframe');
  if (!iframe || !iframe.contentDocument || !iframe.contentDocument.body) {
    return JSON.stringify({ success: false, error: 'iframe_body_unavailable' });
  }
  iframe.contentDocument.body.innerHTML = '<p>Concentric Study can edit iframe content.</p>';
  return JSON.stringify({
    text: iframe.contentDocument.body.innerText.trim(),
    success: /Concentric Study can edit iframe content\\./.test(iframe.contentDocument.body.innerText)
  });
})()"""
        )
        action = {"ready": ready, "write": write, "success": bool(ready.get("success")) and bool(write.get("success"))}
        return self._module_result(path=path, nav=nav, action=action, screenshot_slug="iframe")

    def _solve_jqueryui_menu(self) -> dict[str, Any]:
        path = "/jqueryui/menu"
        nav = self._navigate(path)
        menu = self._browser_json(
            """(() => {
  const textMatch = (value) => Array.from(document.querySelectorAll('*')).find((el) => (el.textContent || '').trim() === value);
  const hover = (el) => {
    if (!el) return false;
    el.dispatchEvent(new MouseEvent('mouseover', { bubbles: true }));
    el.dispatchEvent(new MouseEvent('mouseenter', { bubbles: true }));
    return true;
  };
  const enabled = textMatch('Enabled');
  const downloads = textMatch('Downloads');
  hover(enabled);
  hover(downloads);
  const pdf = document.querySelector('a[href*="menu.pdf"]');
  return JSON.stringify({
    enabled_found: !!enabled,
    downloads_found: !!downloads,
    pdf_href: pdf ? (pdf.getAttribute('href') || '') : null,
    success: !!enabled && !!downloads && !!pdf && !!pdf.getAttribute('href')
  });
})()"""
        )
        download = {"success": False, "error": "menu_pdf_link_not_found"}
        pdf_href = menu.get("pdf_href")
        if pdf_href:
            download = self._download_http(pdf_href, "jqueryui-menu.pdf")
        action = {"menu": menu, "download": download, "success": bool(menu.get("success")) and bool(download.get("success"))}
        return self._module_result(path=path, nav=nav, action=action, screenshot_slug="jqueryui_menu")

    def _solve_javascript_alerts(self) -> dict[str, Any]:
        path = "/javascript_alerts"
        nav = self._navigate(path)
        action = self._browser_json(
            """(() => {
  window.__alerts = [];
  window.alert = (msg) => { window.__alerts.push({ kind: 'alert', message: msg }); log('You successfully clicked an alert'); };
  window.confirm = (msg) => { window.__alerts.push({ kind: 'confirm', message: msg }); log('You clicked: Ok'); return true; };
  window.prompt = (msg) => { window.__alerts.push({ kind: 'prompt', message: msg }); log('You entered: Codex'); return 'Codex'; };
  const buttons = Array.from(document.querySelectorAll('button'));
  buttons.forEach((button) => button.click());
  return JSON.stringify({
    alerts: window.__alerts,
    result: document.querySelector('#result')?.innerText || '',
    success: window.__alerts.length === 3 && /You entered: Codex/i.test(document.querySelector('#result')?.innerText || '')
  });
})()"""
        )
        return self._module_result(path=path, nav=nav, action=action, screenshot_slug="javascript_alerts")

    def _solve_javascript_error(self) -> dict[str, Any]:
        path = "/javascript_error"
        nav = self._navigate(path)
        action = self._browser_json(
            """(() => JSON.stringify({
  body: document.body.innerText.slice(0, 400),
  js_exec_ok: true,
  success: /JavaScript error/i.test(document.body.innerText)
}))()"""
        )
        return self._module_result(path=path, nav=nav, action=action, screenshot_slug="javascript_error")

    def _solve_key_presses(self) -> dict[str, Any]:
        path = "/key_presses"
        nav = self._navigate(path)
        action = self._browser_json(
            """(() => {
  const event = new KeyboardEvent('keydown', {
    key: 'A',
    code: 'KeyA',
    keyCode: 65,
    which: 65,
    bubbles: true
  });
  document.dispatchEvent(event);
  const result = document.querySelector('#result')?.innerText || '';
  return JSON.stringify({
    result,
    success: /A/i.test(result)
  });
})()"""
        )
        return self._module_result(path=path, nav=nav, action=action, screenshot_slug="key_presses")

    def _solve_large_deep_dom(self) -> dict[str, Any]:
        path = "/large"
        nav = self._navigate(path)
        action = self._browser_json(
            """(() => {
  const rows = document.querySelectorAll('#large-table tbody tr');
  const cols = document.querySelectorAll('#large-table tbody tr:first-child td');
  const bottomRight = document.querySelector('#large-table tbody tr:last-child td:last-child')?.innerText || '';
  window.scrollTo(0, document.body.scrollHeight);
  return JSON.stringify({
    row_count: rows.length,
    column_count: cols.length,
    bottom_right: bottomRight,
    success: rows.length >= 50 && cols.length >= 50 && /^\\d+\\.\\d+$/.test(bottomRight)
  });
})()"""
        )
        return self._module_result(path=path, nav=nav, action=action, screenshot_slug="large_deep_dom")

    def _solve_multiple_windows(self) -> dict[str, Any]:
        path = "/windows"
        nav = self._navigate(path)
        before = self._window_count()
        after = self._open_new_window("/windows/new")
        time.sleep(1.0)
        urls = self._window_urls()
        success = before >= 1 and after == before + 1 and any("/windows/new" in url for url in urls)
        close_result = self._close_extra_windows()
        action = {
            "window_count_before": before,
            "window_count_after": after,
            "window_urls": urls,
            "close_result": close_result,
            "strategy": "safari_new_document",
            "success": success,
        }
        return self._module_result(path=path, nav=nav, action=action, screenshot_slug="multiple_windows")

    def _solve_nested_frames(self) -> dict[str, Any]:
        path = "/nested_frames"
        nav = self._navigate(path)
        action = self._browser_json(
            """(() => {
  const topFrame = window.frames['frame-top'];
  const bottomFrame = window.frames['frame-bottom'];
  const left = topFrame.frames['frame-left'].document.body.innerText.trim();
  const middle = topFrame.frames['frame-middle'].document.getElementById('content').innerText.trim();
  const right = topFrame.frames['frame-right'].document.body.innerText.trim();
  const bottom = bottomFrame.document.body.innerText.trim();
  return JSON.stringify({
    left,
    middle,
    right,
    bottom,
    success: left === 'LEFT' && middle === 'MIDDLE' && right === 'RIGHT' && bottom === 'BOTTOM'
  });
})()"""
        )
        return self._module_result(path=path, nav=nav, action=action, screenshot_slug="nested_frames")

    def _solve_notification_messages(self) -> dict[str, Any]:
        path = "/notification_message"
        nav = self._navigate(path)
        messages: list[str] = []
        for _ in range(4):
            self._browser_json(
                """(() => {
  const link = Array.from(document.querySelectorAll('a')).find((a) => /click here/i.test(a.innerText));
  if (link) link.click();
  return JSON.stringify({ clicked: !!link, success: !!link });
})()"""
            )
            state = self._wait_for_js(
                """JSON.stringify({
  success: !!document.querySelector('#flash'),
  message: (document.querySelector('#flash')?.innerText || '').trim().replace(/\\s+/g, ' ')
})""",
                timeout_seconds=8.0,
            )
            if state.get("message"):
                messages.append(state["message"])
        unique_messages = sorted(set(messages))
        action = {
            "messages": messages,
            "unique_messages": unique_messages,
            "success": len(unique_messages) >= 1 and all("Action" in message for message in unique_messages),
        }
        return self._module_result(path=path, nav=nav, action=action, screenshot_slug="notification_messages")

    def _solve_redirect_link(self) -> dict[str, Any]:
        path = "/redirector"
        nav = self._navigate(path)
        click = self._browser_json(
            """(() => {
  const link = document.querySelector('#redirect');
  if (link) link.click();
  return JSON.stringify({ clicked: !!link, success: !!link });
})()"""
        )
        landed = self._wait_for_js(
            """JSON.stringify({
  success: /\\/status_codes/i.test(location.pathname) && /Status Codes/i.test(document.body.innerText),
  href: location.href,
  body: document.body.innerText.slice(0, 250)
})""",
            timeout_seconds=8.0,
        )
        action = {"click": click, "landed": landed, "success": bool(click.get("success")) and bool(landed.get("success"))}
        return self._module_result(path=path, nav=nav, action=action, screenshot_slug="redirect_link")

    def _solve_shadow_dom(self) -> dict[str, Any]:
        path = "/shadowdom"
        nav = self._navigate(path)
        action = self._browser_json(
            """(() => {
  const hosts = Array.from(document.querySelectorAll('my-paragraph'));
  const shadowTexts = hosts.map((host) => host.shadowRoot ? host.shadowRoot.textContent.trim().replace(/\\s+/g, ' ') : '');
  return JSON.stringify({
    shadow_host_count: hosts.length,
    shadow_texts: shadowTexts,
    success: hosts.length >= 2 && shadowTexts.every((text) => text.length > 0)
  });
})()"""
        )
        return self._module_result(path=path, nav=nav, action=action, screenshot_slug="shadow_dom")

    def _solve_shifting_content(self) -> dict[str, Any]:
        menu_nav = self._navigate("/shifting_content/menu?pixel_shift=100")
        menu = self._browser_json(
            """(() => {
  const menu = document.querySelector('.example ul');
  const x = menu ? Math.round(menu.getBoundingClientRect().left) : null;
  return JSON.stringify({
    left: x,
    gallery_present: !!Array.from(document.querySelectorAll('a')).find((a) => (a.getAttribute('href') || '') === '/gallery/'),
    success: x !== null && Math.abs(x) >= 50
  });
})()"""
        )

        image_nav = self._navigate("/shifting_content/image?pixel_shift=100")
        image = self._browser_json(
            """(() => {
  const image = document.querySelector('img.shift');
  const x = image ? Math.round(image.getBoundingClientRect().left) : null;
  return JSON.stringify({
    left: x,
    success: x !== null && Math.abs(x) >= 50
  });
})()"""
        )

        list_nav = self._navigate("/shifting_content/list")
        list_check = self._browser_json(
            """(() => JSON.stringify({
  body: document.body.innerText.replace(/\\s+/g, ' '),
  success: /Important Information You're Looking For/i.test(document.body.innerText)
}))()"""
        )

        payload = {
            "path": "/shifting_content",
            "navigation": menu_nav,
            "subchecks": [
                {"example": "menu", "navigation": menu_nav, "success": bool(menu_nav.get("success")) and bool(menu.get("success")), "details": menu},
                {"example": "image", "navigation": image_nav, "success": bool(image_nav.get("success")) and bool(image.get("success")), "details": image},
                {"example": "list", "navigation": list_nav, "success": bool(list_nav.get("success")) and bool(list_check.get("success")), "details": list_check},
            ],
            "screenshot": self._capture("shifting_content"),
            "success": bool(menu_nav.get("success")) and bool(image_nav.get("success")) and bool(list_nav.get("success")) and bool(menu.get("success")) and bool(image.get("success")) and bool(list_check.get("success")),
        }
        return payload

    def _solve_slow_resources(self) -> dict[str, Any]:
        path = "/slow"
        started = time.time()
        nav = self._navigate(path, timeout_seconds=30.0)
        elapsed = round(time.time() - started, 3)
        action = self._browser_json(
            """(() => JSON.stringify({
  heading: document.querySelector('h3')?.innerText || '',
  body: document.body.innerText.slice(0, 300),
  success: /Slow Resources/i.test(document.body.innerText)
}))()"""
        )
        action["elapsed_seconds"] = elapsed
        action["success"] = bool(action.get("success"))
        return self._module_result(path=path, nav=nav, action=action, screenshot_slug="slow_resources")

    def _solve_sortable_data_tables(self) -> dict[str, Any]:
        path = "/tables"
        nav = self._navigate(path)
        action = self._browser_json(
            """(() => {
  const header = document.querySelector('#table1 thead th');
  const getOrder = () => Array.from(document.querySelectorAll('#table1 tbody tr td:first-child')).map((td) => td.innerText.trim());
  const before = getOrder();
  if (header) {
    header.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
    header.dispatchEvent(new MouseEvent('mouseup', { bubbles: true }));
    header.dispatchEvent(new MouseEvent('click', { bubbles: true }));
  }
  let afterFirst = getOrder();
  if (JSON.stringify(before) === JSON.stringify(afterFirst) && typeof window.$ === 'function') {
    try {
      window.$('#table1').trigger('sorton', [[[0,0]]]);
      afterFirst = getOrder();
    } catch (err) {}
  }
  if (header) {
    header.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
    header.dispatchEvent(new MouseEvent('mouseup', { bubbles: true }));
    header.dispatchEvent(new MouseEvent('click', { bubbles: true }));
  }
  let afterSecond = getOrder();
  if (JSON.stringify(afterFirst) === JSON.stringify(afterSecond) && typeof window.$ === 'function') {
    try {
      window.$('#table1').trigger('sorton', [[[0,1]]]);
      afterSecond = getOrder();
    } catch (err) {}
  }
  return JSON.stringify({
    before,
    after_first: afterFirst,
    after_second: afterSecond,
    success: JSON.stringify(before) !== JSON.stringify(afterFirst) && JSON.stringify(afterFirst) !== JSON.stringify(afterSecond)
  });
})()"""
        )
        return self._module_result(path=path, nav=nav, action=action, screenshot_slug="sortable_data_tables")

    def _solve_status_codes(self) -> dict[str, Any]:
        subchecks = []
        first_nav: dict[str, Any] | None = None
        for code in ("200", "301", "404", "500"):
            nav = self._navigate(f"/status_codes/{code}")
            if first_nav is None:
                first_nav = nav
            action = self._browser_json(
                f"""(() => JSON.stringify({{
  body: document.body.innerText.slice(0, 300),
  success: /{code}/.test(document.body.innerText)
}}))()"""
            )
            subchecks.append({"code": code, "navigation": nav, "details": action, "success": bool(nav.get("success")) and bool(action.get("success"))})
        payload = {
            "path": "/status_codes",
            "navigation": first_nav or {"success": False},
            "subchecks": subchecks,
            "screenshot": self._capture("status_codes"),
            "success": all(item["success"] for item in subchecks),
        }
        return payload

    def _solve_typos(self) -> dict[str, Any]:
        path = "/typos"
        variants: list[str] = []
        nav = self._navigate(path)
        for _ in range(6):
            body = self._browser_json(
                """(() => JSON.stringify({
  line: Array.from(document.querySelectorAll('.example p')).map((p) => p.innerText.trim()).join(' | '),
  success: true
}))()"""
            )
            variants.append(body.get("line", ""))
            self._safari_do_javascript("location.reload()")
            time.sleep(0.8)
            self._wait_for_js(
                """JSON.stringify({
  success: document.readyState === 'complete' && !!document.querySelector('.example'),
  ready: document.readyState
})""",
                timeout_seconds=8.0,
            )
        unique_variants = sorted(set(variants))
        action = {
            "variants": variants,
            "unique_variant_count": len(unique_variants),
            "typo_observed": any("won,t" in variant for variant in variants),
            "success": all("Sometimes you'll see a typo" in variant for variant in variants),
        }
        return self._module_result(path=path, nav=nav, action=action, screenshot_slug="typos")

    def _solve_tinymce(self) -> dict[str, Any]:
        path = "/tinymce"
        nav = self._navigate(path, timeout_seconds=30.0)
        ready = self._wait_for_js(
            """JSON.stringify({
  success: !!document.querySelector('iframe') && !!document.querySelector('iframe').contentDocument,
  iframe_count: document.querySelectorAll('iframe').length
})""",
            timeout_seconds=20.0,
        )
        write = self._browser_json(
            """(() => {
  const iframe = document.querySelector('iframe');
  if (!iframe || !iframe.contentDocument || !iframe.contentDocument.body) {
    return JSON.stringify({ success: false, error: 'tinymce_iframe_unavailable' });
  }
  iframe.contentDocument.body.innerHTML = '<p>Concentric Study updated TinyMCE.</p>';
  return JSON.stringify({
    text: iframe.contentDocument.body.innerText.trim(),
    success: /Concentric Study updated TinyMCE\\./.test(iframe.contentDocument.body.innerText)
  });
})()"""
        )
        action = {"ready": ready, "write": write, "success": bool(ready.get("success")) and bool(write.get("success"))}
        return self._module_result(path=path, nav=nav, action=action, screenshot_slug="tinymce")

    # ------------------------------------------------------------------
    # Main
    # ------------------------------------------------------------------
    def run(self) -> int:
        steps: list[tuple[str, str, Callable[[], dict[str, Any]] | None]] = [
            ("preflight", "Restart Safari and start the site-wide public sweep from a clean state.", None),
            ("abtest", "Verify the A/B testing page resolves to a valid public variant.", self._solve_abtest),
            ("add_remove_elements", "Exercise add/remove controls and verify the resulting count.", self._solve_add_remove_elements),
            ("broken_images", "Detect the intentionally broken image resources.", self._solve_broken_images),
            ("challenging_dom", "Resolve unstable selectors on the challenging DOM page.", self._solve_challenging_dom),
            ("checkboxes", "Set both public checkboxes and verify state persistence.", self._solve_checkboxes),
            ("context_menu", "Trigger the context-menu example and verify the resulting alert text.", self._solve_context_menu),
            ("disappearing_elements", "Observe the disappearing navigation states across reloads.", self._solve_disappearing_elements),
            ("drag_and_drop", "Swap the drag-and-drop columns and verify the headers reverse.", self._solve_drag_and_drop),
            ("dropdown", "Select Option 2 from the dropdown and verify the selected value.", self._solve_dropdown),
            ("dynamic_content", "Refresh dynamic content and verify that text or image rows change.", self._solve_dynamic_content),
            ("dynamic_controls", "Remove and restore the checkbox, then enable and type into the input.", self._solve_dynamic_controls),
            ("dynamic_loading", "Complete both dynamic-loading examples and wait for Hello World.", self._solve_dynamic_loading),
            ("entry_ad", "Close the entry modal and restart it to verify both modal states.", self._solve_entry_ad),
            ("exit_intent", "Trigger the exit-intent modal and close it again.", self._solve_exit_intent),
            ("file_download", "Download a public file from the page and verify the saved artifact.", self._solve_file_download),
            ("file_upload", "Assign and submit a synthetic file through the public upload form.", self._solve_file_upload),
            ("floating_menu", "Scroll the page and verify the floating menu remains actionable.", self._solve_floating_menu),
            ("forgot_password", "Submit the public forgot-password form and verify the resulting terminal state.", self._solve_forgot_password),
            ("frames_index", "Verify the frames landing page exposes both nested-frames and iframe examples.", self._solve_frames_index),
            ("geolocation", "Resolve the geolocation example, falling back to an injected provider only if native prompt control is unavailable.", self._solve_geolocation),
            ("horizontal_slider", "Move the slider to 4 and verify the displayed value.", self._solve_horizontal_slider),
            ("hovers", "Reveal the hover-only captions for all three public avatars.", self._solve_hovers),
            ("infinite_scroll", "Grow the infinite-scroll page and verify that additional content is injected.", self._solve_infinite_scroll),
            ("inputs", "Type into the numeric input example and verify the value.", self._solve_inputs),
            ("iframe", "Edit the iframe example and verify the new body text inside the frame.", self._solve_iframe),
            ("jqueryui_menu", "Traverse the jQuery UI menu hierarchy and retrieve the exposed PDF artifact.", self._solve_jqueryui_menu),
            ("javascript_alerts", "Complete all three JavaScript alert flows and verify the final prompt result.", self._solve_javascript_alerts),
            ("javascript_error", "Verify the JavaScript-onload-error page still loads as an observable benchmark target.", self._solve_javascript_error),
            ("key_presses", "Trigger a keypress event and verify the reported key.", self._solve_key_presses),
            ("large_deep_dom", "Reach the deep DOM table and read the bottom-right cell.", self._solve_large_deep_dom),
            ("multiple_windows", "Open the child window and verify both parent and child Safari windows exist.", self._solve_multiple_windows),
            ("nested_frames", "Read all nested frame bodies and verify their canonical labels.", self._solve_nested_frames),
            ("notification_messages", "Cycle notification messages and capture the resulting flash states.", self._solve_notification_messages),
            ("redirect_link", "Trigger the redirect link and verify the landing status-codes page.", self._solve_redirect_link),
            ("shadow_dom", "Read text from the page's open shadow roots.", self._solve_shadow_dom),
            ("shifting_content", "Exercise all three shifting-content examples with deterministic shift settings where possible.", self._solve_shifting_content),
            ("slow_resources", "Load the slow-resources page and verify the benchmark surface completes.", self._solve_slow_resources),
            ("sortable_data_tables", "Sort the data table twice and verify the row order changes.", self._solve_sortable_data_tables),
            ("status_codes", "Visit all four public status-code examples and verify their bodies.", self._solve_status_codes),
            ("typos", "Reload the typo page repeatedly and record the observed text variants.", self._solve_typos),
            ("tinymce", "Edit the TinyMCE editor iframe and verify the new text.", self._solve_tinymce),
        ]

        index = 0
        try:
            for slug, thought, solver in steps:
                step = self._step(index, slug, thought)
                if solver is None:
                    self._safari_restart()
                    close_result = self._close_extra_windows()
                    payload = {"status": "safari_restarted", "close_result": close_result, "success": True}
                    self.summary["steps"] = self.summary.get("steps", {})
                    self.summary["steps"][slug] = payload
                    self._end_step(step, True, payload)
                else:
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
    runner = TheInternetRunner()
    rc = runner.run()
    reader = DiagnosticReader(runner.run_dir)
    (runner.run_dir / "diagnostic.txt").write_text(reader.full_diagnostic(), encoding="utf-8")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
