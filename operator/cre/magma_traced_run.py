#!/usr/bin/env python3
"""Magma BMW E30 run with screenshots, self-healing, and learning.

Uses TraceWriter (per-step screenshots, trace.jsonl, manifest.json),
retries/fallbacks when steps fail (self-healing), and on success ingests
into SkillLibrary; on failure appends to ReflectionJournal (learning).

Usage:
  cd operator && ./venv/bin/python cre/magma_traced_run.py
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

CRE_DIR = Path(__file__).resolve().parent
OPERATOR_DIR = CRE_DIR.parent
VENV_PYTHON = str(OPERATOR_DIR / "venv" / "bin" / "python")

# Add operator to path for agent_infra
sys.path.insert(0, str(OPERATOR_DIR))

from agent_infra.trace_writer import TraceWriter, TraceStep


def _screenshot(tw: TraceWriter, name: str) -> str:
    path = tw.screenshots_dir / f"{name}.png"
    subprocess.run(["screencapture", "-x", str(path)], check=True, timeout=10)
    return str(path)


def _osascript(script: str) -> subprocess.CompletedProcess:
    return subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=15)


def _safari_set_url(url: str) -> None:
    _osascript(f'tell application "Safari" to set URL of current tab of front window to "{url}"')


def _safari_do_js(js: str) -> str:
    one_line = " ".join(js.split())
    escaped = one_line.replace("\\", "\\\\").replace('"', '\\"')
    r = _osascript(
        f'tell application "Safari" to do JavaScript "{escaped}" in current tab of front window'
    )
    return (r.stdout or "").strip() if r.returncode == 0 else ""


def _safari_get_url() -> str:
    r = _osascript('tell application "Safari" to get URL of current tab of front window')
    return (r.stdout or "").strip() if r.returncode == 0 else ""


def main() -> int:
    task_id = "MAGMA_BMW_E30_REALISM"
    task_description = "Open Magma in Safari and draw a realistic 1991 BMW M3 E30 (realism / PhD arts)"

    tw = TraceWriter(
        output_dir=CRE_DIR,
        task_id=task_id,
        task_description=task_description,
        agent_config={"mode": "magma_traced", "task": "bmw_e30"},
    )
    print(f"Run dir: {tw.run_dir}")

    outcome = "success"
    step_index = 0

    def step(action_type: str, thought: str, run_fn):
        nonlocal step_index, outcome
        step_index += 1
        s = tw.begin_step(step_index)
        s.thought = thought
        s.action = {"type": action_type, "parameters": {}}
        s.pre_state["screenshot"] = _screenshot(tw, f"step_{step_index:02d}_pre")
        try:
            result = run_fn()
            s.post_state["screenshot"] = _screenshot(tw, f"step_{step_index:02d}_post")
            if result is False:
                s.action_result = {"success": False, "reason": "step_failed"}
                s.evaluation = {"expected": thought, "actual": "failed", "match": False}
                tw.record_failure(step_index, "action_failed", thought)
                outcome = "failure"
            else:
                s.action_result = {"success": True, "output": str(result) if result is not True else "ok"}
                s.evaluation = {"expected": thought, "actual": "ok", "match": True}
        except Exception as e:
            s.post_state["screenshot"] = _screenshot(tw, f"step_{step_index:02d}_fail")
            s.action_result = {"success": False, "error": str(e)}
            s.evaluation = {"expected": thought, "actual": str(e), "match": False}
            tw.record_failure(step_index, "error", str(e))
            outcome = "failure"
        tw.end_step(s)
        return outcome == "success"

    # Step 1: Open Safari to Magma
    def open_magma():
        subprocess.run(["open", "-a", "Safari", "https://www.magma.com"], check=True, timeout=5)
        time.sleep(3)
        _safari_set_url("https://www.magma.com")
        time.sleep(2)
        return True

    if not step("magma_open_url", "Open Safari to www.magma.com", open_magma):
        tw.finalize(outcome)
        _record_failure(tw, outcome)
        return 1

    # Step 2: Navigate to My artworks
    def nav_app():
        _safari_set_url("https://magma.com/app")
        time.sleep(4)
        url = _safari_get_url()
        if "/my/artworks" not in url and "magma.com" in url:
            time.sleep(2)
            url = _safari_get_url()
        return "/my/artworks" in url or "magma.com" in url

    if not step("magma_navigate_app", "Navigate to magma.com/app (My artworks)", nav_app):
        tw.finalize(outcome)
        _record_failure(tw, outcome)
        return 1

    # Step 3: Click "New canvas" (with self-healing: retry with alternate selector)
    def click_new_canvas():
        sel = 'button, a, [role="button"]'
        js = "(function(){ var el = Array.from(document.querySelectorAll('" + sel + "')).find(function(e){ return e.innerText && e.innerText.trim().indexOf('New canvas') >= 0; }); if (el) { el.click(); return 'clicked'; } return 'not_found'; })();"
        r = _safari_do_js(js)
        if r == "clicked":
            return True
        time.sleep(1)
        js2 = "(function(){ var nodes = document.querySelectorAll('*'); for (var i=0;i<nodes.length;i++){ if (nodes[i].innerText && nodes[i].innerText.trim().indexOf('New canvas')>=0){ nodes[i].click(); return 'clicked'; } } return 'not_found'; })();"
        r2 = _safari_do_js(js2)
        return r2 == "clicked"

    if not step("magma_click_new_canvas", "Click 'New canvas' to open dropdown", click_new_canvas):
        tw.finalize(outcome)
        _record_failure(tw, outcome)
        return 1

    time.sleep(1.5)

    # Step 4: Click "Landscape drawing" (with retry)
    def click_landscape():
        sel = 'button, a, [role="menuitem"], div'
        js = "(function(){ var el = Array.from(document.querySelectorAll('" + sel + "')).find(function(e){ return e.innerText && e.innerText.trim().indexOf('Landscape') >= 0; }); if (el) { el.click(); return 'clicked'; } return 'not_found'; })();"
        r = _safari_do_js(js)
        if r == "clicked":
            return True
        js2 = "(function(){ var nodes = document.querySelectorAll('*'); for (var i=0;i<nodes.length;i++){ if (nodes[i].innerText && nodes[i].innerText.trim().indexOf('Landscape')>=0){ nodes[i].click(); return 'clicked'; } } return 'not_found'; })();"
        return _safari_do_js(js2) == "clicked"

    if not step("magma_click_landscape", "Click 'Landscape drawing' to create canvas", click_landscape):
        tw.finalize(outcome)
        _record_failure(tw, outcome)
        return 1

    time.sleep(8)
    url = _safari_get_url()
    if "/d/" not in url:
        step_index += 1
        s = tw.begin_step(step_index)
        s.thought = "Canvas URL check"
        s.action = {"type": "magma_canvas_check", "parameters": {}}
        s.pre_state["screenshot"] = _screenshot(tw, f"step_{step_index:02d}_pre")
        s.action_result = {"success": False, "reason": "canvas_not_loaded", "url": url}
        s.evaluation = {"expected": "URL contains /d/", "actual": url, "match": False}
        tw.record_failure(step_index, "canvas_not_loaded", url)
        tw.end_step(s)
        outcome = "failure"
        tw.finalize(outcome)
        _record_failure(tw, outcome)
        return 1

    # Step 5: Draw BMW E30
    def draw_e30():
        r = subprocess.run(
            [VENV_PYTHON, str(CRE_DIR / "magma_draw_bmw_e30.py")],
            cwd=str(OPERATOR_DIR),
            timeout=60,
            capture_output=True,
            text=True,
        )
        return r.returncode == 0

    step("magma_draw_bmw_e30", "Draw realistic 1991 BMW M3 E30 on canvas", draw_e30)

    tw.finalize(outcome)

    if outcome == "success":
        try:
            from agent_infra.skill_library import SkillLibrary
            lib = SkillLibrary(library_dir=str(CRE_DIR))
            record = lib.ingest_from_trace(tw.run_dir)
            if record:
                print(f"  Ingested into SkillLibrary: {record.task_id}")
        except Exception as e:
            print(f"  SkillLibrary ingest (non-fatal): {e}")
    else:
        _record_failure(tw, outcome)

    print(f"\nOutcome: {outcome} | Run: {tw.run_dir}")
    return 0 if outcome == "success" else 1


def _record_failure(tw: TraceWriter, outcome: str) -> None:
    """Append to ReflectionJournal so future runs can learn."""
    try:
        from agent_infra.outer_loop import ReflectionJournal
        journal_path = CRE_DIR / "runs" / "reflection_journal.jsonl"
        journal = ReflectionJournal(journal_path)
        lesson = (
            f"Magma BMW E30 run {tw.run_id} ended with {outcome}. "
            f"Check trace for steps where action_result.success is false; "
            f"e.g. 'New canvas' or 'Landscape' not_found may need different JS selectors on current Magma UI."
        )
        journal.record(
            run_id=tw.run_id,
            outcome=outcome,
            cycle=0,
            classification=None,
            lesson=lesson,
        )
        print("  Recorded in ReflectionJournal.")
    except Exception as e:
        print(f"  ReflectionJournal (non-fatal): {e}")


if __name__ == "__main__":
    sys.exit(main())
