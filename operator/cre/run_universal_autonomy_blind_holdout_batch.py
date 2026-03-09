#!/usr/bin/env python3
"""Blind holdout batch for universal-autonomy transfer in Safari.

Protocol: UNIVERSAL_AUTONOMY_BLIND_BATCH_V1
Source: operator/cre/artifacts/universal_autonomy_blind_holdout_batch_protocol.json

This runner keeps code frozen during execution and evaluates required tasks
across a locked 5-site sequence. It emits:
- trace + manifest
- per-task module JSON + screenshots
- batch summary with first-pass/stabilized/recovery metrics
- transfer curve series (cumulative by site order)
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_infra.diagnostic_reader import DiagnosticReader
from agent_infra.host_tool_health import HostToolHealth
from agent_infra.trace_writer import TraceWriter
from window_capture import capture_front_window


@dataclass(frozen=True)
class SiteSpec:
    site_id: str
    name: str
    url: str
    expected_host_token: str


@dataclass(frozen=True)
class TaskSpec:
    task_id: str
    family: str
    name: str


class UniversalAutonomyBlindHoldoutBatchRunner:
    def __init__(self) -> None:
        self.cre_dir = Path(__file__).parent
        self.protocol_path = self.cre_dir / "artifacts" / "universal_autonomy_blind_holdout_batch_protocol.json"
        self.protocol = json.loads(self.protocol_path.read_text(encoding="utf-8"))
        contract = self.protocol["evaluation_contract"]
        self.max_attempts = int(contract["max_attempts_per_task"])

        self.sites: list[SiteSpec] = [
            SiteSpec(
                site_id=raw["site_id"],
                name=raw["name"],
                url=raw["url"],
                expected_host_token=raw["expected_host_token"],
            )
            for raw in self.protocol["site_order"]
        ]
        self.tasks: list[TaskSpec] = [
            TaskSpec(task_id=raw["task_id"], family=raw["family"], name=raw["name"])
            for raw in self.protocol["required_tasks"]
        ]

        self.trace = TraceWriter(
            output_dir=self.cre_dir,
            task_id="UNIVERSAL_AUTONOMY_BLIND_HOLDOUT_BATCH",
            task_description="Frozen-code blind holdout batch across 5 public websites in Safari.",
            agent_config={
                "browser": "Safari",
                "protocol_id": self.protocol["protocol_id"],
                "site_count": len(self.sites),
                "task_count_per_site": len(self.tasks),
                "max_attempts_per_task": self.max_attempts,
                "code_mutation_during_batch": bool(contract["code_mutation_during_batch"]),
            },
        )
        self.run_dir = self.trace.run_dir
        self.module_dir = self.run_dir / "modules"
        self.module_dir.mkdir(parents=True, exist_ok=True)
        self.summary: dict[str, Any] = {
            "protocol_id": self.protocol["protocol_id"],
            "run_id": self.trace.run_id,
            "status": "running",
            "site_order": [s.__dict__ for s in self.sites],
            "required_tasks": [t.__dict__ for t in self.tasks],
            "max_attempts_per_task": self.max_attempts,
            "code_mutation_during_batch": bool(contract["code_mutation_during_batch"]),
            "sites": {},
            "transfer_curve": [],
        }

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

    def _capture(self, slug: str) -> dict[str, Any]:
        path = self.module_dir / f"{slug}.png"
        return capture_front_window(path, owner_name="Safari")

    def _record_module(self, site_id: str, task_name: str, payload: dict[str, Any]) -> None:
        slug = f"{site_id}__{task_name}"
        (self.module_dir / f"{slug}.json").write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )

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
        deadline = time.time() + 20.0
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

    def _close_extra_windows(self) -> dict[str, Any]:
        try:
            self._run_osascript(
                """
tell application "Safari"
    set guard to 0
    repeat while (count of windows) > 1
        set guard to guard + 1
        if guard > 20 then exit repeat
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
        for attempt in range(10):
            raw = self._safari_do_javascript(js)
            if not raw.strip():
                last_error = ValueError("Safari returned empty JavaScript payload")
                time.sleep(min(0.9, 0.12 * (attempt + 1)))
                continue
            try:
                return json.loads(raw)
            except json.JSONDecodeError as exc:
                last_error = exc
                time.sleep(min(0.9, 0.12 * (attempt + 1)))
        if last_error is not None:
            raise last_error
        raise RuntimeError("Could not decode browser JSON payload")

    def _navigate_url(self, url: str, *, timeout_seconds: float = 25.0) -> dict[str, Any]:
        escaped = url.replace("\\", "\\\\").replace('"', '\\"')
        self._run_osascript(
            f"""
tell application "Safari"
    activate
    if (count of windows) = 0 then
        make new document with properties {{URL:"{escaped}"}}
    else
        set URL of current tab of front window to "{escaped}"
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
  host: location.host,
  pathname: location.pathname,
  title: document.title,
  ready: document.readyState,
  h1: (document.querySelector('h1')?.innerText || '').trim(),
  links: document.querySelectorAll('a[href]').length
})"""
                )
                href = str(current.get("href", ""))
                ready = current.get("ready")
                ok = href.startswith("https://") and ready in {"interactive", "complete"}
                last = {"success": ok, **current}
                if ok:
                    return last
            except Exception as exc:
                last = {"success": False, "error": str(exc)}
            time.sleep(0.4)
        return last

    def _wait_for_js(
        self,
        js: str,
        *,
        timeout_seconds: float = 15.0,
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

    def _dismiss_cookie_banner(self) -> dict[str, Any]:
        return self._browser_json(
            """(() => {
  const labels = [
    'accept all',
    'accept cookies',
    'allow all',
    'allow all cookies',
    'i agree',
    'agree',
    'consent',
    'yes, i agree'
  ];
  const consentTerms = ['cookie', 'cookies', 'consent', 'privacy'];
  const visible = (el) => {
    const r = el.getBoundingClientRect();
    const style = window.getComputedStyle(el);
    return r.width > 2 && r.height > 2 && style.visibility !== 'hidden' && style.display !== 'none';
  };
  const hasConsentContext = (el) => {
    const own = ((el.innerText || el.value || el.getAttribute('aria-label') || '') + '').toLowerCase();
    if (consentTerms.some((term) => own.includes(term))) return true;
    let p = el.parentElement;
    let hops = 0;
    while (p && hops < 3) {
      const t = ((p.innerText || '') + '').toLowerCase();
      if (consentTerms.some((term) => t.includes(term))) return true;
      p = p.parentElement;
      hops += 1;
    }
    return false;
  };
  const nodes = Array.from(document.querySelectorAll('button, a, input[type="button"], input[type="submit"], [role="button"]'));
  for (const node of nodes) {
    const text = ((node.innerText || node.value || node.getAttribute('aria-label') || '') + '').trim().toLowerCase();
    if (!text || !visible(node)) continue;
    const textMatch = labels.some((label) => text === label || text.startsWith(label + ' '));
    if (!textMatch) continue;
    if (!hasConsentContext(node)) continue;
    if (node.tagName.toLowerCase() === 'a' && node.hasAttribute('href') && !node.getAttribute('href')) continue;
    if (!node.disabled) {
      node.click();
      return JSON.stringify({success: true, clicked_text: text});
    }
  }
  return JSON.stringify({success: false, reason: 'no_cookie_button_match'});
})()"""
        )

    # ------------------------------------------------------------------
    # Task solvers
    # ------------------------------------------------------------------
    def _normalize_url(self, url: str) -> str:
        parsed = urlparse(url)
        path = parsed.path.rstrip("/")
        return f"{parsed.scheme}://{parsed.netloc}{path}"

    def _same_host(self, href: str, expected_host_token: str) -> bool:
        try:
            host = (urlparse(href).hostname or "").lower()
        except Exception:
            return False
        return expected_host_token.lower() in host

    def _solve_navigate_home(self, site: SiteSpec, site_state: dict[str, Any]) -> dict[str, Any]:
        nav = self._navigate_url(site.url)
        dismiss = self._dismiss_cookie_banner()
        href = str(nav.get("href", ""))
        host_ok = self._same_host(href, site.expected_host_token)
        site_state["home_href"] = href
        site_state["home_normalized"] = self._normalize_url(href) if href else self._normalize_url(site.url)
        return {
            "site_id": site.site_id,
            "task": "navigate_home",
            "navigation": nav,
            "cookie_banner": dismiss,
            "host_ok": host_ok,
            "success": bool(nav.get("success")) and host_ok,
        }

    def _solve_probe_home_structure(self, site: SiteSpec, site_state: dict[str, Any]) -> dict[str, Any]:
        probe = self._browser_json(
            """(() => {
  const heading = (document.querySelector('h1')?.innerText || '').trim();
  const title = (document.title || '').trim();
  const body = (document.body?.innerText || '').replace(/\\s+/g, ' ').trim();
  const links = document.querySelectorAll('a[href]').length;
  const forms = document.querySelectorAll('form').length;
  const buttons = document.querySelectorAll('button, [role="button"], input[type="submit"], input[type="button"]').length;
  return JSON.stringify({
    href: location.href,
    host: location.host,
    pathname: location.pathname,
    title,
    heading,
    body_chars: body.length,
    links,
    forms,
    buttons,
    success: title.length > 0 && links >= 3 && body.length > 100
  });
})()"""
        )
        href = str(probe.get("href", ""))
        host_ok = self._same_host(href, site.expected_host_token)
        return {
            "site_id": site.site_id,
            "task": "probe_home_structure",
            "probe": probe,
            "host_ok": host_ok,
            "success": bool(probe.get("success")) and host_ok,
        }

    def _solve_follow_internal_link(
        self,
        site: SiteSpec,
        site_state: dict[str, Any],
        *,
        link_slot: int,
    ) -> dict[str, Any]:
        blocked = set(site_state.get("used_links", []))
        blocked_literal = json.dumps(sorted(blocked))
        choose = self._browser_json(
            f"""(() => {{
  const blocked = new Set({blocked_literal});
  const homeHost = location.host;
  const homeHref = location.href;
  const norm = (href) => {{
    try {{
      const u = new URL(href, location.href);
      u.hash = '';
      return u.href.replace(/\\/$/, '');
    }} catch (_e) {{
      return '';
    }}
  }};
  const badPrefix = ['mailto:', 'tel:', 'javascript:'];
  const isVisible = (el) => {{
    const r = el.getBoundingClientRect();
    const style = window.getComputedStyle(el);
    return r.width > 2 && r.height > 2 && style.visibility !== 'hidden' && style.display !== 'none';
  }};
  const anchors = Array.from(document.querySelectorAll('a[href]'));
  let rank = 0;
  for (const a of anchors) {{
    if (!isVisible(a)) continue;
    const raw = a.getAttribute('href') || '';
    if (!raw) continue;
    if (badPrefix.some((p) => raw.toLowerCase().startsWith(p))) continue;
    let url;
    try {{
      url = new URL(raw, location.href);
    }} catch (_e) {{
      continue;
    }}
    if (!url.protocol.startsWith('http')) continue;
    if (url.host !== homeHost) continue;
    const canonical = norm(url.href);
    const here = norm(homeHref);
    if (!canonical || canonical === here) continue;
    if (canonical.toLowerCase().includes('/ignoreme')) continue;
    if (canonical.includes('/login') || canonical.includes('/signin') || canonical.includes('/signup')) continue;
    if (blocked.has(canonical)) continue;
    const text = ((a.innerText || a.textContent || '') + '').replace(/\\s+/g, ' ').trim();
    if (text.length < 2) continue;
    rank += 1;
    location.href = url.href;
    return JSON.stringify({{
      success: true,
      chosen_href: url.href,
      chosen_canonical: canonical,
      chosen_text: text,
      rank
    }});
  }}
  return JSON.stringify({{success: false, error: 'no_internal_link_candidate'}});
}})()"""
        )
        if choose.get("success"):
            wait = self._wait_for_js(
                """(() => {
  const title = (document.title || '').trim();
  const href = location.href;
  const links = document.querySelectorAll('a[href]').length;
  const body = (document.body?.innerText || '').replace(/\\s+/g, ' ').trim();
  return JSON.stringify({
    href,
    title,
    links,
    body_chars: body.length,
    success: title.length > 0 && links >= 1 && body.length > 50
  });
})()""",
                timeout_seconds=18.0,
            )
        else:
            wait = {"success": False, "error": "choose_failed"}
        chosen_canonical = choose.get("chosen_canonical")
        if choose.get("success") and isinstance(chosen_canonical, str) and chosen_canonical:
            site_state.setdefault("used_links", []).append(chosen_canonical)
            site_state[f"destination_{link_slot}_href"] = str(wait.get("href", choose.get("chosen_href", "")))
        host_ok = self._same_host(str(wait.get("href", "")), site.expected_host_token)
        return {
            "site_id": site.site_id,
            "task": f"follow_internal_link_{link_slot}",
            "choose": choose,
            "wait": wait,
            "host_ok": host_ok,
            "success": bool(choose.get("success")) and bool(wait.get("success")) and host_ok,
        }

    def _solve_probe_destination(self, site: SiteSpec, *, slot: int) -> dict[str, Any]:
        probe = self._browser_json(
            """(() => {
  const heading = (document.querySelector('h1,h2')?.innerText || '').trim();
  const title = (document.title || '').trim();
  const links = document.querySelectorAll('a[href]').length;
  const paragraphs = document.querySelectorAll('p').length;
  const listItems = document.querySelectorAll('li').length;
  const codeBlocks = document.querySelectorAll('pre, code').length;
  const body = (document.body?.innerText || '').replace(/\\s+/g, ' ').trim();
  return JSON.stringify({
    href: location.href,
    host: location.host,
    pathname: location.pathname,
    title,
    heading,
    links,
    paragraphs,
    list_items: listItems,
    code_blocks: codeBlocks,
    body_chars: body.length,
    success: title.length > 0 && body.length > 80
  });
})()"""
        )
        host_ok = self._same_host(str(probe.get("href", "")), site.expected_host_token)
        return {
            "site_id": site.site_id,
            "task": f"probe_destination_{slot}",
            "probe": probe,
            "host_ok": host_ok,
            "success": bool(probe.get("success")) and host_ok,
        }

    def _solve_back_to_home(self, site: SiteSpec, site_state: dict[str, Any]) -> dict[str, Any]:
        back = self._browser_json(
            """(() => {
  history.back();
  return JSON.stringify({success: true});
})()"""
        )
        home_norm = str(site_state.get("home_normalized") or self._normalize_url(site.url))
        wait = self._wait_for_js(
            f"""(() => {{
  const href = location.href;
  const title = (document.title || '').trim();
  const norm = (() => {{
    try {{
      const u = new URL(href);
      u.hash = '';
      return u.href.replace(/\\/$/, '');
    }} catch (_e) {{
      return href;
    }}
  }})();
  return JSON.stringify({{
    href,
    title,
    normalized_href: norm,
    success: norm === {json.dumps(home_norm)} || norm.startsWith({json.dumps(home_norm + "/")})
  }});
}})()""",
            timeout_seconds=15.0,
        )
        host_ok = self._same_host(str(wait.get("href", "")), site.expected_host_token)
        return {
            "site_id": site.site_id,
            "task": "back_to_home",
            "back": back,
            "wait": wait,
            "host_ok": host_ok,
            "success": bool(back.get("success")) and bool(wait.get("success")) and host_ok,
        }

    def _solve_task(self, site: SiteSpec, task: TaskSpec, site_state: dict[str, Any]) -> dict[str, Any]:
        if task.name == "navigate_home":
            return self._solve_navigate_home(site, site_state)
        if task.name == "probe_home_structure":
            return self._solve_probe_home_structure(site, site_state)
        if task.name == "follow_internal_link_1":
            return self._solve_follow_internal_link(site, site_state, link_slot=1)
        if task.name == "probe_destination_1":
            return self._solve_probe_destination(site, slot=1)
        if task.name == "back_to_home":
            return self._solve_back_to_home(site, site_state)
        if task.name == "follow_internal_link_2":
            return self._solve_follow_internal_link(site, site_state, link_slot=2)
        if task.name == "probe_destination_2":
            return self._solve_probe_destination(site, slot=2)
        raise ValueError(f"Unknown task: {task.name}")

    # ------------------------------------------------------------------
    # Metrics
    # ------------------------------------------------------------------
    def _compute_site_metrics(self, task_rows: list[dict[str, Any]]) -> dict[str, Any]:
        first_pass = sum(1 for row in task_rows if row.get("first_pass_success"))
        stabilized = sum(1 for row in task_rows if row.get("success"))
        failed = len(task_rows) - stabilized
        recovered = sum(1 for row in task_rows if (not row.get("first_pass_success")) and row.get("success"))
        initial_failures = len(task_rows) - first_pass
        return {
            "task_count": len(task_rows),
            "first_pass_success_count": first_pass,
            "stabilized_success_count": stabilized,
            "failed_count": failed,
            "recovered_count": recovered,
            "initial_failure_count": initial_failures,
            "first_pass_success_rate": (first_pass / len(task_rows)) if task_rows else 0.0,
            "stabilized_success_rate": (stabilized / len(task_rows)) if task_rows else 0.0,
            "recovery_rate": (recovered / initial_failures) if initial_failures > 0 else 1.0,
        }

    def _save_summary(self) -> None:
        all_rows: list[dict[str, Any]] = []
        cumulative_rows: list[dict[str, Any]] = []
        self.summary["transfer_curve"] = []

        for site_index, site in enumerate(self.sites, start=1):
            site_payload = self.summary["sites"].get(site.site_id, {})
            task_rows = list(site_payload.get("tasks", {}).values())
            site_metrics = self._compute_site_metrics(task_rows)
            site_payload["metrics"] = site_metrics
            self.summary["sites"][site.site_id] = site_payload

            all_rows.extend(task_rows)
            cumulative_rows.extend(task_rows)
            cumulative_metrics = self._compute_site_metrics(cumulative_rows)
            self.summary["transfer_curve"].append(
                {
                    "site_index": site_index,
                    "site_id": site.site_id,
                    "site_name": site.name,
                    "site_first_pass_success_rate": site_metrics["first_pass_success_rate"],
                    "site_stabilized_success_rate": site_metrics["stabilized_success_rate"],
                    "site_recovery_rate": site_metrics["recovery_rate"],
                    "cumulative_first_pass_success_rate": cumulative_metrics["first_pass_success_rate"],
                    "cumulative_stabilized_success_rate": cumulative_metrics["stabilized_success_rate"],
                    "cumulative_recovery_rate": cumulative_metrics["recovery_rate"],
                    "cumulative_task_count": cumulative_metrics["task_count"],
                }
            )

        overall = self._compute_site_metrics(all_rows)
        targets = self.protocol["metrics"]
        gates = {
            "first_pass_target_met": overall["first_pass_success_rate"]
            >= float(targets["first_pass_success_rate"]["target"]),
            "stabilized_target_met": overall["stabilized_success_rate"]
            >= float(targets["stabilized_success_rate"]["target"]),
            "recovery_target_met": overall["recovery_rate"] >= float(targets["recovery_rate"]["target"]),
        }
        gates["all_targets_met"] = all(gates.values())

        self.summary["metrics"] = overall
        self.summary["gates"] = gates
        self.summary["status"] = "success" if overall["failed_count"] == 0 else "partial_failure"
        (self.run_dir / "universal_autonomy_blind_holdout_batch_summary.json").write_text(
            json.dumps(self.summary, indent=2, default=str),
            encoding="utf-8",
        )

    # ------------------------------------------------------------------
    # Run
    # ------------------------------------------------------------------
    def run(self) -> int:
        index = 0
        try:
            health = HostToolHealth().evaluate(has_url=True)
            health_step = self._step(index, "host_tool_health", "Verify host-tool readiness before blind holdout batch.")
            self._end_step(health_step, bool(health.get("all_required_ready")), health)
            index += 1
            if not health.get("all_required_ready"):
                self.summary["status"] = "blocked"
                self.summary["blocker"] = "HostToolHealth required classes not ready"
                self._save_summary()
                self.trace.finalize(outcome="blocked")
                return 1

            for site in self.sites:
                site_start = self._step(index, f"site_start_{site.site_id}", f"Initialize clean Safari state for {site.name}.")
                self._safari_restart()
                close_result = self._close_extra_windows()
                self._end_step(site_start, bool(close_result.get("success")), {"site": site.__dict__, "close_result": close_result})
                index += 1

                site_state: dict[str, Any] = {"used_links": []}
                site_payload: dict[str, Any] = {
                    "site_id": site.site_id,
                    "site_name": site.name,
                    "start_url": site.url,
                    "expected_host_token": site.expected_host_token,
                    "tasks": {},
                }

                for task in self.tasks:
                    step = self._step(
                        index,
                        f"{site.site_id}__{task.name}",
                        f"Execute {task.name} on {site.name} with max {self.max_attempts} attempts.",
                    )
                    attempts: list[dict[str, Any]] = []
                    first_pass_success = False
                    success = False

                    for attempt in range(1, self.max_attempts + 1):
                        payload = self._solve_task(site, task, site_state)
                        payload["attempt"] = attempt
                        payload["screenshot"] = self._capture(f"{site.site_id}__{task.name}__attempt{attempt}")
                        attempts.append(payload)
                        if payload.get("success"):
                            success = True
                            first_pass_success = attempt == 1
                            break
                        time.sleep(min(1.0, 0.35 * attempt))

                    final_payload = attempts[-1] if attempts else {"success": False}
                    task_payload = {
                        "task_id": task.task_id,
                        "family": task.family,
                        "name": task.name,
                        "first_pass_success": first_pass_success,
                        "attempt_count": len(attempts),
                        "attempts": attempts,
                        "success": success,
                    }
                    site_payload["tasks"][task.name] = task_payload
                    self._record_module(site.site_id, task.name, task_payload)
                    self._end_step(step, bool(success), final_payload)
                    index += 1

                self.summary["sites"][site.site_id] = site_payload

            self._save_summary()
            outcome = "success" if self.summary["status"] == "success" else "partial_failure"
            self.trace.finalize(outcome=outcome)
            return 0 if outcome == "success" else 1
        except Exception as exc:
            self.summary["status"] = "error"
            self.summary["error"] = str(exc)
            self._save_summary()
            self.trace.finalize(outcome="error")
            return 1


def main() -> int:
    runner = UniversalAutonomyBlindHoldoutBatchRunner()
    rc = runner.run()
    reader = DiagnosticReader(runner.run_dir)
    diagnostic_path = runner.run_dir / "diagnostic.txt"
    diagnostic_path.write_text(reader.full_diagnostic(), encoding="utf-8")

    batch_summary_path = runner.run_dir / "universal_autonomy_blind_holdout_batch_summary.json"
    if batch_summary_path.exists():
        payload = json.loads(batch_summary_path.read_text(encoding="utf-8"))
        payload["diagnostic_path"] = str(diagnostic_path)
        payload["run_dir"] = str(runner.run_dir)
        artifact_path = runner.cre_dir / "artifacts" / "universal_autonomy_blind_holdout_batch_result.json"
        artifact_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
