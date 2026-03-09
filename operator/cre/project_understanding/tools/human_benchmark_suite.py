#!/usr/bin/env python3
"""Visible Human Benchmark task harnesses for Safari.

Current focus:
- Aim Trainer optimization with visible cursor movement, physical clicks, and score save.

The harness is deliberately evidence-gated and records per-run artifacts so live-task
claims can be checked against page state rather than shell success.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from Quartz import (
    CGEventCreateMouseEvent,
    CGEventPost,
    kCGEventLeftMouseDown,
    kCGEventLeftMouseUp,
    kCGEventMouseMoved,
    kCGHIDEventTap,
    kCGMouseButtonLeft,
)


REPO_ROOT = Path("/Users/christianpardo/Desktop/concentric_study")
VENV_PYTHON = REPO_ROOT / "operator" / "venv" / "bin" / "python"
MISSION_CONTROL = (
    REPO_ROOT / "operator" / "cre" / "project_understanding" / "tools" / "mission_control.py"
)
ARTIFACT_DIR = (
    REPO_ROOT / "operator" / "cre" / "project_understanding" / "artifacts" / "human_benchmark"
)
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

HUMAN_BENCHMARK_URLS = {
    "aim": "https://humanbenchmark.com/tests/aim",
    "sequence": "https://humanbenchmark.com/tests/sequence",
    "chimp": "https://humanbenchmark.com/tests/chimp",
    "typing": "https://humanbenchmark.com/tests/typing",
    "verbal-memory": "https://humanbenchmark.com/tests/verbal-memory",
    "number-memory": "https://humanbenchmark.com/tests/number-memory",
    "memory": "https://humanbenchmark.com/tests/memory",
    "reactiontime": "https://humanbenchmark.com/tests/reactiontime",
}

# Calibrated from live page-side event telemetry.
SAFARI_VERTICAL_OFFSET = 139
START_CLIENT_CENTER = (720.0, 318.0)


def _run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, capture_output=True, check=True)


def _run_optional(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, capture_output=True, check=False)


def _osascript(script: str) -> str:
    return _run(["osascript", "-e", script]).stdout.strip()


def _do_js(js: str) -> str:
    escaped = json.dumps(js)
    return _osascript(
        f'tell application "Safari" to do JavaScript {escaped} in current tab of front window'
    )


def _global_from_client(cx: float, cy: float) -> tuple[float, float]:
    return round(cx, 1), round(cy + SAFARI_VERTICAL_OFFSET, 1)


def _smooth_move(x: float, y: float, duration: float, steps: int) -> None:
    try:
        out = _run(["/opt/homebrew/bin/cliclick", "p"]).stdout.strip()
        sx, sy = map(float, out.split(","))
    except Exception:
        sx, sy = x, y
    for i in range(1, steps + 1):
        t = i / steps
        cx = sx + (x - sx) * t
        cy = sy + (y - sy) * t
        event = CGEventCreateMouseEvent(None, kCGEventMouseMoved, (cx, cy), kCGMouseButtonLeft)
        CGEventPost(kCGHIDEventTap, event)
        time.sleep(duration / steps)


def _click_here(x: float, y: float) -> None:
    for event_type in (kCGEventLeftMouseDown, kCGEventLeftMouseUp):
        event = CGEventCreateMouseEvent(None, event_type, (x, y), kCGMouseButtonLeft)
        CGEventPost(kCGHIDEventTap, event)
        time.sleep(0.015)


def _hide_cursor_app_and_activate_safari() -> None:
    _run_optional(
        [
            "osascript",
            "-e",
            'tell application "Cursor" to activate',
            "-e",
            'tell application "System Events" to keystroke "h" using command down',
            "-e",
            'tell application "Safari" to activate',
        ]
    )


def _safari_evidence() -> dict[str, Any]:
    return json.loads(
        _run(
            [
                str(VENV_PYTHON),
                str(MISSION_CONTROL),
                "evidence",
                "Safari",
                "--require-frontmost",
                "--capture",
                "--json",
            ]
        ).stdout
    )


def _ensure_live_profile() -> None:
    _run([str(VENV_PYTHON), str(MISSION_CONTROL), "up", "live", "--json"])


def _ensure_safari_ready() -> dict[str, Any]:
    _hide_cursor_app_and_activate_safari()
    time.sleep(0.6)
    evidence = _safari_evidence()
    if not evidence.get("ready_for_visible_task"):
        raise RuntimeError(
            f"Safari not ready for visible task: {evidence.get('blockers', ['unknown blocker'])}"
        )
    return evidence


@dataclass
class MotionProfile:
    name: str
    move_duration: float
    move_steps: int
    settle_sleep: float


class HumanBenchmarkHarness:
    def __init__(self, artifact_prefix: str) -> None:
        self.artifact_prefix = artifact_prefix
        self.log_path = ARTIFACT_DIR / f"{artifact_prefix}_log.json"
        self.log_path.write_text("[]")

    def log(self, event: str, **payload: Any) -> None:
        try:
            data = json.loads(self.log_path.read_text())
        except Exception:
            data = []
        data.append({"ts": time.time(), "event": event, **payload})
        self.log_path.write_text(json.dumps(data, indent=2))

    def goto(self, test_id: str, wait_seconds: float = 2.8) -> None:
        url = HUMAN_BENCHMARK_URLS[test_id]
        _osascript(f'tell application "Safari" to set URL of current tab of front window to "{url}"')
        time.sleep(wait_seconds)
        self.log("navigated", test_id=test_id, url=url)

    def query_aim_state(self) -> dict[str, Any]:
        js = r'''
(() => {
  const body = document.body.innerText;
  const remainingMatch = body.match(/Remaining\s*(\d+)/);
  const targetRoot = document.querySelector('[data-aim-target="true"]');
  let target = null;
  if (targetRoot) {
    let best = null;
    for (const el of targetRoot.children) {
      const r = el.getBoundingClientRect();
      if (Math.abs(r.width - 100) < 2 && Math.abs(r.height - 100) < 2) best = r;
    }
    const r = best || targetRoot.getBoundingClientRect();
    target = {x:r.x, y:r.y, width:r.width, height:r.height, cx:r.x + r.width / 2, cy:r.y + r.height / 2};
  }
  const save = Array.from(document.querySelectorAll('button,a,div')).find(el => (el.innerText || '').trim() === 'Save score');
  const tryAgain = Array.from(document.querySelectorAll('button,a,div')).find(el => (el.innerText || '').trim() === 'Try again');
  const rect = el => {
    if (!el) return null;
    const r = el.getBoundingClientRect();
    return {x:r.x, y:r.y, width:r.width, height:r.height, cx:r.x + r.width / 2, cy:r.y + r.height / 2, tag:el.tagName};
  };
  return JSON.stringify({
    title: document.title,
    body: body.slice(0, 500),
    remaining: remainingMatch ? Number(remainingMatch[1]) : null,
    target,
    saveRect: rect(save),
    tryRect: rect(tryAgain),
    averageVisible: body.includes('Average time per target'),
  });
})();
'''
        return json.loads(_do_js(js))

    def click_client_point(self, client_x: float, client_y: float, profile: MotionProfile) -> tuple[float, float]:
        gx, gy = _global_from_client(client_x, client_y)
        _smooth_move(gx, gy, duration=profile.move_duration, steps=profile.move_steps)
        _click_here(gx, gy)
        time.sleep(profile.settle_sleep)
        return gx, gy

    def run_aim(self, profile: MotionProfile, *, save_score: bool = True) -> dict[str, Any]:
        _ensure_live_profile()
        evidence = _ensure_safari_ready()
        self.log("evidence", evidence=evidence)

        self.goto("aim")
        sx, sy = self.click_client_point(*START_CLIENT_CENTER, profile=MotionProfile(
            name="start",
            move_duration=max(profile.move_duration * 1.2, 0.06),
            move_steps=max(profile.move_steps + 1, 6),
            settle_sleep=max(profile.settle_sleep, 0.30),
        ))
        self.log(
            "start_click",
            client_center=list(START_CLIENT_CENTER),
            global_point=[sx, sy],
        )

        started = False
        start_deadline = time.time() + 3.0
        while time.time() < start_deadline:
            state = self.query_aim_state()
            if state.get("remaining") == 30:
                started = True
                break
            time.sleep(0.05)
        if not started:
            self.log("start_failed", state=state)
            return {"status": "start_failed", "state": state, "log": str(self.log_path)}

        start_ts = time.time()
        for step in range(1, 40):
            state = self.query_aim_state()
            if state["averageVisible"]:
                self.log("result_reached", step=step, state=state)
                break
            target = state["target"]
            if not target:
                self.log("no_target", step=step, state=state)
                return {"status": "no_target", "state": state, "log": str(self.log_path)}
            gx, gy = self.click_client_point(target["cx"], target["cy"], profile=profile)
            self.log(
                "target_click",
                step=step,
                remaining=state["remaining"],
                client_center=[target["cx"], target["cy"]],
                global_point=[gx, gy],
            )
            post = self.query_aim_state()
            self.log(
                "post_click",
                step=step,
                pre_remaining=state["remaining"],
                post_remaining=post["remaining"],
                averageVisible=post["averageVisible"],
            )
            if post["averageVisible"]:
                state = post
                break

        elapsed = round(time.time() - start_ts, 3)
        state = self.query_aim_state()
        average_ms = None
        match = re.search(r"Average time per target\s+(\d+)ms", state["body"])
        if match:
            average_ms = int(match.group(1))

        if save_score and state.get("saveRect"):
            gx, gy = self.click_client_point(
                state["saveRect"]["cx"],
                state["saveRect"]["cy"],
                profile=MotionProfile(
                    name="save",
                    move_duration=max(profile.move_duration, 0.05),
                    move_steps=max(profile.move_steps, 5),
                    settle_sleep=max(profile.settle_sleep, 0.25),
                ),
            )
            self.log(
                "save_click",
                client_center=[state["saveRect"]["cx"], state["saveRect"]["cy"]],
                global_point=[gx, gy],
            )
            time.sleep(0.4)
            state = self.query_aim_state()

        result = {
            "status": "ok" if average_ms is not None else "inconclusive",
            "average_ms": average_ms,
            "elapsed_seconds": elapsed,
            "final_state": state,
            "log": str(self.log_path),
        }
        self.log("final_state", result=result)
        return result

    def query_sequence_state(self) -> dict[str, Any]:
        js = r'''
(() => {
  const body = document.body.innerText;
  const levelMatch = body.match(/Level:(\d+)/);
  const squares = Array.from(document.querySelectorAll('.square')).map((el, idx) => {
    const s = getComputedStyle(el);
    const r = el.getBoundingClientRect();
    return {
      idx,
      cls: el.className,
      opacity: Number(s.opacity),
      bg: s.backgroundColor,
      x: r.x, y: r.y, width: r.width, height: r.height,
      cx: r.x + r.width / 2, cy: r.y + r.height / 2,
    };
  });
  const start = Array.from(document.querySelectorAll('button')).find(el => (el.innerText || '').trim() === 'Start');
  const save = Array.from(document.querySelectorAll('button,a,div')).find(el => (el.innerText || '').trim() === 'Save score');
  const rect = el => {
    if (!el) return null;
    const r = el.getBoundingClientRect();
    return {x:r.x, y:r.y, width:r.width, height:r.height, cx:r.x + r.width/2, cy:r.y + r.height/2};
  };
  return JSON.stringify({
    title: document.title,
    body: body.slice(0, 600),
    level: levelMatch ? Number(levelMatch[1]) : null,
    squares,
    startRect: rect(start),
    saveRect: rect(save),
    activeIndices: squares.filter(s => s.cls.includes('active') || s.opacity > 0.55).map(s => s.idx),
  });
})();
'''
        return json.loads(_do_js(js))

    def run_sequence(
        self,
        profile: MotionProfile,
        *,
        save_score: bool = True,
        max_level: int = 12,
        fail_to_save: bool = True,
    ) -> dict[str, Any]:
        _ensure_live_profile()
        evidence = _ensure_safari_ready()
        self.log("evidence", evidence=evidence)

        self.goto("sequence", wait_seconds=2.5)
        state = self.query_sequence_state()
        if not state.get("startRect"):
            self.log("start_missing", state=state)
            return {"status": "start_missing", "state": state, "log": str(self.log_path)}

        sx, sy = self.click_client_point(
            state["startRect"]["cx"],
            state["startRect"]["cy"],
            profile=MotionProfile(
                name="sequence_start",
                move_duration=max(profile.move_duration, 0.06),
                move_steps=max(profile.move_steps, 6),
                settle_sleep=0.05,
            ),
        )
        self.log(
            "start_click",
            client_center=[state["startRect"]["cx"], state["startRect"]["cy"]],
            global_point=[sx, sy],
        )

        target_level = 1
        while True:
            # Record the flashed sequence by polling for active squares.
            observed: list[int] = []
            last_active: int | None = None
            seen_any = False
            quiet_since: float | None = None
            deadline = time.time() + 12.0
            while time.time() < deadline:
                state = self.query_sequence_state()
                active = state.get("activeIndices", [])
                if active:
                    seen_any = True
                    quiet_since = None
                    idx = active[0]
                    if idx != last_active:
                        observed.append(idx)
                        last_active = idx
                        self.log(
                            "sequence_flash",
                            level=target_level,
                            flash_index=len(observed),
                            square_index=idx,
                        )
                else:
                    if seen_any:
                        if quiet_since is None:
                            quiet_since = time.time()
                        elif time.time() - quiet_since > 0.45:
                            break
                    last_active = None
                time.sleep(0.02)

            if len(observed) != target_level:
                self.log(
                    "sequence_capture_failed",
                    level=target_level,
                    observed=observed,
                    state=state,
                )
                return {
                    "status": "sequence_capture_failed",
                    "level": target_level,
                    "observed": observed,
                    "state": state,
                    "log": str(self.log_path),
                }

            # If we've reached the target level and need a saved score, intentionally fail
            # the next input round with a visible wrong click to surface the save screen.
            if target_level > max_level:
                wrong_index = next(i for i in range(9) if i != observed[0])
                current = self.query_sequence_state()
                square = current["squares"][wrong_index]
                gx, gy = self.click_client_point(square["cx"], square["cy"], profile=profile)
                self.log(
                    "intentional_fail_click",
                    level=target_level,
                    wrong_square_index=wrong_index,
                    global_point=[gx, gy],
                )
                time.sleep(0.45)
                state = self.query_sequence_state()
                self.log("post_intentional_fail", level=target_level, state=state)
                break

            # Replay the sequence visibly.
            for index, square_index in enumerate(observed, start=1):
                current = self.query_sequence_state()
                square = current["squares"][square_index]
                gx, gy = self.click_client_point(square["cx"], square["cy"], profile=profile)
                self.log(
                    "sequence_click",
                    level=target_level,
                    index=index,
                    square_index=square_index,
                    global_point=[gx, gy],
                )

            time.sleep(0.35)
            state = self.query_sequence_state()
            self.log("post_sequence", level=target_level, state=state)
            if state.get("saveRect"):
                break
            if state.get("level") == target_level + 1:
                target_level += 1
                continue
            # If the page stayed on the same level without a save screen, treat it as a failure.
            return {
                "status": "sequence_progress_failed",
                "level": target_level,
                "state": state,
                "log": str(self.log_path),
            }

        state = self.query_sequence_state()
        if save_score and state.get("saveRect"):
            gx, gy = self.click_client_point(
                state["saveRect"]["cx"],
                state["saveRect"]["cy"],
                profile=MotionProfile(
                    name="sequence_save",
                    move_duration=max(profile.move_duration, 0.05),
                    move_steps=max(profile.move_steps, 5),
                    settle_sleep=max(profile.settle_sleep, 0.20),
                ),
            )
            self.log(
                "save_click",
                client_center=[state["saveRect"]["cx"], state["saveRect"]["cy"]],
                global_point=[gx, gy],
            )
            time.sleep(0.35)
            state = self.query_sequence_state()

        result = {
            "status": "ok",
            "final_level": target_level,
            "final_state": state,
            "log": str(self.log_path),
        }
        self.log("final_state", result=result)
        return result

    def query_chimp_state(self) -> dict[str, Any]:
        js = r'''
(() => {
  const body = document.body.innerText;
  const numbersMatch = body.match(/NUMBERS\s*(\d+)/);
  const strikesMatch = body.match(/STRIKES\s*(\d+)\s*of\s*3/);
  const numbered = Array.from(document.querySelectorAll('div')).map(el => {
    const txt = (el.innerText || '').trim();
    if (!/^\d+$/.test(txt)) return null;
    const r = el.getBoundingClientRect();
    if (r.width < 40 || r.height < 40 || r.width > 100 || r.height > 100) return null;
    return {num:Number(txt), x:r.x,y:r.y,width:r.width,height:r.height,cx:r.x+r.width/2, cy:r.y+r.height/2, cls:el.className};
  }).filter(Boolean).sort((a,b) => a.num - b.num);
  const button = label => {
    const el = Array.from(document.querySelectorAll('button,a,div')).find(node => (node.innerText || '').trim() === label);
    if (!el) return null;
    const r = el.getBoundingClientRect();
    return {x:r.x, y:r.y, width:r.width, height:r.height, cx:r.x+r.width/2, cy:r.y+r.height/2, tag:el.tagName};
  };
  return JSON.stringify({
    title: document.title,
    body: body.slice(0, 700),
    numbersCount: numbersMatch ? Number(numbersMatch[1]) : null,
    strikes: strikesMatch ? Number(strikesMatch[1]) : null,
    numbered,
    startRect: button('Start Test'),
    continueRect: button('Continue'),
    saveRect: button('Save score'),
    averageVisible: body.includes('Save your score'),
  });
})();
'''
        return json.loads(_do_js(js))

    def run_chimp(
        self,
        profile: MotionProfile,
        *,
        save_score: bool = True,
        max_numbers: int = 20,
    ) -> dict[str, Any]:
        _ensure_live_profile()
        evidence = _ensure_safari_ready()
        self.log("evidence", evidence=evidence)

        self.goto("chimp", wait_seconds=2.5)
        state = self.query_chimp_state()
        if not state.get("startRect"):
            self.log("start_missing", state=state)
            return {"status": "start_missing", "state": state, "log": str(self.log_path)}

        gx, gy = self.click_client_point(
            state["startRect"]["cx"],
            state["startRect"]["cy"],
            profile=MotionProfile(
                name="chimp_start",
                move_duration=max(profile.move_duration, 0.06),
                move_steps=max(profile.move_steps, 6),
                settle_sleep=0.05,
            ),
        )
        self.log("start_click", global_point=[gx, gy], client_center=[state["startRect"]["cx"], state["startRect"]["cy"]])

        while True:
            state = self.query_chimp_state()
            if state.get("saveRect"):
                break

            if state.get("continueRect"):
                # If we've reached the chosen difficulty, intentionally burn remaining strikes
                # until the save-score screen appears: click Continue -> get board -> click
                # highest number first (wrong order) -> strike -> repeat until save screen.
                if state.get("numbersCount") and state["numbersCount"] > max_numbers:
                    strikes_burned = 0
                    while strikes_burned < 3 and not state.get("saveRect"):
                        # Advance to next round's board
                        gx, gy = self.click_client_point(
                            state["continueRect"]["cx"],
                            state["continueRect"]["cy"],
                            profile=MotionProfile(
                                name="chimp_continue",
                                move_duration=max(profile.move_duration, 0.05),
                                move_steps=max(profile.move_steps, 5),
                                settle_sleep=0.20,
                            ),
                        )
                        self.log("continue_for_fail", global_point=[gx, gy], numbersCount=state.get("numbersCount"), strikes=state.get("strikes"))
                        time.sleep(0.35)
                        state = self.query_chimp_state()
                        if state.get("saveRect"):
                            break
                        numbered = state.get("numbered", [])
                        if numbered:
                            # Click highest number first to force one wrong-order strike
                            wrong_cell = max(numbered, key=lambda x: x["num"])
                            gx, gy = self.click_client_point(
                                wrong_cell["cx"],
                                wrong_cell["cy"],
                                profile=MotionProfile(
                                    name="chimp_fail",
                                    move_duration=max(profile.move_duration, 0.05),
                                    move_steps=max(profile.move_steps, 5),
                                    settle_sleep=0.20,
                                ),
                            )
                            self.log(
                                "intentional_fail_click",
                                wrong_num=wrong_cell["num"],
                                global_point=[gx, gy],
                            )
                            time.sleep(0.45)
                            state = self.query_chimp_state()
                            strikes_burned += 1
                    if state.get("saveRect"):
                        break

                gx, gy = self.click_client_point(
                    state["continueRect"]["cx"],
                    state["continueRect"]["cy"],
                    profile=MotionProfile(
                        name="chimp_continue",
                        move_duration=max(profile.move_duration, 0.05),
                        move_steps=max(profile.move_steps, 5),
                        settle_sleep=0.20,
                    ),
                )
                self.log("continue_click", global_point=[gx, gy], state=state)
                time.sleep(0.35)
                continue

            numbered = state.get("numbered", [])
            if numbered:
                seen_nums: set[int] = set()
                ordered: list[dict[str, Any]] = []
                for item in numbered:
                    if item["num"] in seen_nums:
                        continue
                    seen_nums.add(item["num"])
                    ordered.append(item)
                self.log("numbered_state", numbers_count=state.get("numbersCount"), ordered=ordered)
                for item in ordered:
                    gx, gy = self.click_client_point(item["cx"], item["cy"], profile=profile)
                    self.log(
                        "number_click",
                        numbers_count=state.get("numbersCount"),
                        num=item["num"],
                        global_point=[gx, gy],
                    )
                time.sleep(0.30)
                continue

            return {
                "status": "chimp_state_unknown",
                "state": state,
                "log": str(self.log_path),
            }

        state = self.query_chimp_state()
        if save_score and state.get("saveRect"):
            gx, gy = self.click_client_point(
                state["saveRect"]["cx"],
                state["saveRect"]["cy"],
                profile=MotionProfile(
                    name="chimp_save",
                    move_duration=max(profile.move_duration, 0.05),
                    move_steps=max(profile.move_steps, 5),
                    settle_sleep=0.20,
                ),
            )
            self.log("save_click", global_point=[gx, gy], client_center=[state["saveRect"]["cx"], state["saveRect"]["cy"]])
            time.sleep(0.4)
            state = self.query_chimp_state()

        result = {
            "status": "ok",
            "final_state": state,
            "log": str(self.log_path),
        }
        self.log("final_state", result=result)
        return result

    def query_typing_state(self) -> dict[str, Any]:
        js = r'''
(() => {
  const body = document.body.innerText;
  const input = document.querySelector('textarea, input[type="text"], [contenteditable="true"], .letters.notranslate, [class*="letters"]') || document.querySelector('div.view');
  const promptEl = document.querySelector('.letters.notranslate') || document.querySelector('[class*="letters"]') || document.querySelector('div.view');
  let toType = '';
  if (promptEl) toType = (promptEl.innerText || promptEl.textContent || '').replace(/\s+/g, ' ').trim();
  const save = Array.from(document.querySelectorAll('button,a,div')).find(el => (el.innerText || '').trim() === 'Save score');
  const rect = el => {
    if (!el) return null;
    const r = el.getBoundingClientRect();
    return {x:r.x,y:r.y,width:r.width,height:r.height,cx:r.x+r.width/2,cy:r.y+r.height/2};
  };
  const inputOrPrompt = input || promptEl;
  return JSON.stringify({
    body: body.slice(0, 500),
    toType: toType.slice(0, 2000),
    inputRect: inputOrPrompt ? rect(inputOrPrompt) : null,
    saveRect: rect(save),
    done: body.includes('Test complete') || body.includes('Save score'),
  });
})();
'''
        return json.loads(_do_js(js))

    def run_typing(self, profile: MotionProfile, *, save_score: bool = True) -> dict[str, Any]:
        _ensure_live_profile()
        _ensure_safari_ready()
        self.log("evidence")
        self.goto("typing", wait_seconds=2.5)
        state = self.query_typing_state()
        if not state.get("toType") or not state.get("inputRect"):
            self.log("typing_setup_missing", state=state)
            return {"status": "typing_setup_missing", "state": state, "log": str(self.log_path)}
        text = state["toType"]
        subprocess.run(["pbcopy"], input=text, text=True, check=True)
        self.log("typing_paste_prep", to_type_len=len(text))
        gx, gy = self.click_client_point(
            state["inputRect"]["cx"],
            state["inputRect"]["cy"],
            profile=profile,
        )
        self.log("typing_focus_click", global_point=[gx, gy])
        time.sleep(0.2)
        _run(["osascript", "-e", 'tell application "System Events" to keystroke "v" using command down'])
        time.sleep(6.0)
        state = self.query_typing_state()
        if not (state.get("done") and state.get("saveRect")):
            self.log("typing_paste_incomplete_fallback_to_keystroke")
            for i, ch in enumerate(text):
                if i % 50 == 0:
                    state = self.query_typing_state()
                    if state.get("done") and state.get("saveRect"):
                        break
                esc = ch.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "")
                if esc:
                    _run(["osascript", "-e", f'tell application "System Events" to keystroke "{esc}"'])
                time.sleep(0.018)
            time.sleep(1.0)
        deadline = time.time() + 30.0
        while time.time() < deadline:
            state = self.query_typing_state()
            if state.get("done") and state.get("saveRect"):
                break
            time.sleep(0.3)
        if save_score and state.get("saveRect"):
            gx, gy = self.click_client_point(
                state["saveRect"]["cx"],
                state["saveRect"]["cy"],
                profile=MotionProfile(name="save", move_duration=0.05, move_steps=5, settle_sleep=0.25),
            )
            self.log("save_click", global_point=[gx, gy])
            time.sleep(0.4)
        result = {"status": "ok", "final_state": self.query_typing_state(), "log": str(self.log_path)}
        self.log("final_state", result=result)
        return result

    def query_reaction_state(self) -> dict[str, Any]:
        js = r'''
(() => {
  const body = document.body.innerText;
  const candidates = document.querySelectorAll('[class*="view"], .view-go, .view-wait, [class*="reaction"]');
  let box = null;
  let isGreen = false;
  for (const el of candidates) {
    const r = el.getBoundingClientRect();
    if (r.width < 100 || r.height < 100) continue;
    const s = getComputedStyle(el);
    const bg = (s.backgroundColor || '').toLowerCase();
    const cls = (el.className || '').toString();
    if (cls.includes('go') || bg.includes('rgb(0, 255') || bg.includes('green')) {
      isGreen = true;
      box = el;
      break;
    }
    if (!box) box = el;
  }
  if (!box) box = document.querySelector('main') || document.body;
  const save = Array.from(document.querySelectorAll('button,a,div')).find(el => (el.innerText || '').trim() === 'Save score');
  const rect = el => {
    if (!el) return null;
    const r = el.getBoundingClientRect();
    return {x:r.x,y:r.y,width:r.width,height:r.height,cx:r.x+r.width/2,cy:r.y+r.height/2};
  };
  return JSON.stringify({
    body: body.slice(0, 400),
    isGreen: !!isGreen,
    boxRect: box ? rect(box) : {cx: 720, cy: 400, width: 800, height: 400},
    saveRect: rect(save),
    hasSave: body.includes('Save score'),
  });
})();
'''
        return json.loads(_do_js(js))

    def run_reactiontime(self, profile: MotionProfile, *, save_score: bool = True, num_clicks: int = 5) -> dict[str, Any]:
        _ensure_live_profile()
        _ensure_safari_ready()
        self.log("evidence")
        self.goto("reactiontime", wait_seconds=2.5)
        state = self.query_reaction_state()
        box = state.get("boxRect") or {"cx": 720, "cy": 400}
        gx, gy = self.click_client_point(box["cx"], box["cy"], profile=profile)
        self.log("reaction_start_click", global_point=[gx, gy])
        time.sleep(1.0)
        clicks_done = 0
        deadline = time.time() + 90.0
        while clicks_done < num_clicks and time.time() < deadline:
            state = self.query_reaction_state()
            if state.get("hasSave") and state.get("saveRect"):
                break
            state_box = state.get("boxRect") or box
            if state.get("isGreen"):
                gx, gy = self.click_client_point(state_box["cx"], state_box["cy"], profile=profile)
                self.log("reaction_click", click=clicks_done + 1, global_point=[gx, gy])
                clicks_done += 1
                time.sleep(0.5)
            time.sleep(0.03)
        state = self.query_reaction_state()
        if save_score and state.get("saveRect"):
            gx, gy = self.click_client_point(
                state["saveRect"]["cx"],
                state["saveRect"]["cy"],
                profile=MotionProfile(name="save", move_duration=0.05, move_steps=5, settle_sleep=0.25),
            )
            self.log("save_click", global_point=[gx, gy])
            time.sleep(0.4)
        result = {"status": "ok", "clicks": clicks_done, "final_state": self.query_reaction_state(), "log": str(self.log_path)}
        self.log("final_state", result=result)
        return result

    def query_verbal_state(self) -> dict[str, Any]:
        js = r'''
(() => {
  const body = document.body.innerText;
  const wordEl = document.querySelector('.word') || document.querySelector('[class*="word"]') || document.querySelector('h1');
  const word = wordEl ? (wordEl.innerText || wordEl.textContent || '').trim() : '';
  const btn = label => {
    const el = Array.from(document.querySelectorAll('button,a,div')).find(node => (node.innerText || '').trim() === label);
    if (!el) return null;
    const r = el.getBoundingClientRect();
    return {cx:r.x+r.width/2, cy:r.y+r.height/2};
  };
  return JSON.stringify({
    body: body.slice(0, 500),
    word,
    startRect: btn('Start'),
    newRect: btn('NEW'),
    seenRect: btn('SEEN'),
    saveRect: btn('Save score'),
    hasSave: body.includes('Save score') || body.includes('Save your score'),
  });
})();
'''
        return json.loads(_do_js(js))

    def run_verbal_memory(
        self, profile: MotionProfile, *, save_score: bool = True, max_turns: int = 300
    ) -> dict[str, Any]:
        _ensure_live_profile()
        _ensure_safari_ready()
        self.log("evidence")
        self.goto("verbal-memory", wait_seconds=2.5)
        state = self.query_verbal_state()
        if state.get("startRect"):
            gx, gy = self.click_client_point(
                state["startRect"]["cx"], state["startRect"]["cy"],
                profile=MotionProfile(name="start", move_duration=0.06, move_steps=6, settle_sleep=0.1),
            )
            self.log("start_click", global_point=[gx, gy])
            time.sleep(0.5)
        seen: set[str] = set()
        for turn in range(max_turns):
            state = self.query_verbal_state()
            if state.get("saveRect") or state.get("hasSave"):
                self.log("verbal_save_screen", turn=turn)
                break
            word = (state.get("word") or "").strip()
            if not word:
                time.sleep(0.2)
                continue
            is_seen = word in seen
            if is_seen:
                rect = state.get("seenRect")
            else:
                seen.add(word)
                rect = state.get("newRect")
            if not rect:
                break
            gx, gy = self.click_client_point(rect["cx"], rect["cy"], profile=profile)
            self.log("verbal_click", word=word[:20], clicked="SEEN" if is_seen else "NEW", global_point=[gx, gy])
            time.sleep(0.25)
        state = self.query_verbal_state()
        if save_score and state.get("saveRect"):
            gx, gy = self.click_client_point(
                state["saveRect"]["cx"], state["saveRect"]["cy"],
                profile=MotionProfile(name="save", move_duration=0.05, move_steps=5, settle_sleep=0.25),
            )
            self.log("save_click", global_point=[gx, gy])
            time.sleep(0.4)
        result = {"status": "ok", "turns": len(seen), "final_state": self.query_verbal_state(), "log": str(self.log_path)}
        self.log("final_state", result=result)
        return result

    def query_number_memory_state(self) -> dict[str, Any]:
        js = r'''
(() => {
  const body = document.body.innerText;
  const numEl = document.querySelector('.big-number') || document.querySelector('[class*="number"]') || document.querySelector('h1');
  const num = numEl ? (numEl.innerText || numEl.textContent || '').trim().replace(/\D/g, '') : '';
  const btn = label => {
    const upper = (t) => (t || '').trim().toUpperCase();
    const el = Array.from(document.querySelectorAll('button,a,input,div')).find(node => upper(node.innerText) === upper(label) || upper(node.textContent) === upper(label) || (node.placeholder || '').trim() === label);
    if (!el) return null;
    const r = el.getBoundingClientRect();
    return {cx:r.x+r.width/2, cy:r.y+r.height/2, tag: el.tagName};
  };
  const input = document.querySelector('input[type="text"], input[type="number"], input:not([type="submit"]):not([type="button"])') || document.querySelector('input');
  const save = Array.from(document.querySelectorAll('button,a,div')).find(el => (el.innerText || '').trim() === 'Save score');
  const rect = el => el ? {cx: el.getBoundingClientRect().x + el.getBoundingClientRect().width/2, cy: el.getBoundingClientRect().y + el.getBoundingClientRect().height/2} : null;
  return JSON.stringify({
    body: body.slice(0, 500),
    number: num,
    startRect: btn('Start'),
    submitRect: btn('Submit') || btn('Next') || btn('NEXT'),
    inputRect: input ? rect(input) : null,
    saveRect: rect(save),
    hasSave: body.includes('Save score'),
  });
})();
'''
        return json.loads(_do_js(js))

    def run_number_memory(
        self, profile: MotionProfile, *, save_score: bool = True, max_level: int = 10
    ) -> dict[str, Any]:
        _ensure_live_profile()
        _ensure_safari_ready()
        self.log("evidence")
        self.goto("number-memory", wait_seconds=2.5)
        state = self.query_number_memory_state()
        if state.get("startRect"):
            gx, gy = self.click_client_point(
                state["startRect"]["cx"], state["startRect"]["cy"],
                profile=MotionProfile(name="start", move_duration=0.06, move_steps=6, settle_sleep=0.2),
            )
            self.log("start_click", global_point=[gx, gy])
            time.sleep(1.0)
        for level in range(max_level):
            state = self.query_number_memory_state()
            if state.get("hasSave") and state.get("saveRect"):
                break
            num = (state.get("number") or "").strip().replace(" ", "")
            if num:
                self.log("number_seen", level=level + 1, num_len=len(num))
                time.sleep(1.2)
                for _ in range(25):
                    state = self.query_number_memory_state()
                    if state.get("inputRect") and state.get("submitRect"):
                        break
                    time.sleep(0.1)
                input_rect = state.get("inputRect")
                submit_rect = state.get("submitRect")
                if input_rect:
                    gx, gy = self.click_client_point(input_rect["cx"], input_rect["cy"], profile=profile)
                    time.sleep(0.15)
                    esc = num.replace("\\", "\\\\").replace('"', '\\"')
                    _run(["osascript", "-e", f'tell application "System Events" to keystroke "{esc}"'])
                    time.sleep(0.25)
                    state = self.query_number_memory_state()
                    submit_rect = state.get("submitRect")
                    if submit_rect:
                        gx, gy = self.click_client_point(
                            submit_rect["cx"], submit_rect["cy"], profile=profile
                        )
                        self.log("number_submit", level=level + 1, global_point=[gx, gy])
                time.sleep(0.6)
            else:
                time.sleep(0.3)
        state = self.query_number_memory_state()
        if save_score and state.get("saveRect"):
            gx, gy = self.click_client_point(
                state["saveRect"]["cx"], state["saveRect"]["cy"],
                profile=MotionProfile(name="save", move_duration=0.05, move_steps=5, settle_sleep=0.25),
            )
            self.log("save_click", global_point=[gx, gy])
            time.sleep(0.4)
        result = {"status": "ok", "final_state": self.query_number_memory_state(), "log": str(self.log_path)}
        self.log("final_state", result=result)
        return result

    def query_visual_memory_state(self) -> dict[str, Any]:
        js = r'''
(() => {
  const body = document.body.innerText;
  const levelMatch = body.match(/Level\s*(\d+)/i);
  const selectors = '.square, [class*="square"], [class*="cell"], [class*="tile"], .memory-grid div, [class*="game"] div, [class*="grid"] > div';
  let nodes = Array.from(document.querySelectorAll(selectors));
  if (nodes.length === 0) {
    const container = document.querySelector('[class*="game"], [class*="grid"], [class*="memory"]');
    if (container) nodes = Array.from(container.querySelectorAll('div')).filter(d => {
      const r = d.getBoundingClientRect();
      return r.width > 20 && r.height > 20 && r.width < 150 && r.height < 150;
    });
  }
  const squares = nodes.map((el, idx) => {
    const s = getComputedStyle(el);
    const r = el.getBoundingClientRect();
    const bg = (s.backgroundColor || '').toLowerCase();
    const opacity = Number(s.opacity);
    const isActive = bg.includes('255') || (s.background || '').includes('255') || (el.className || '').includes('active') || opacity > 0.9;
    return { idx, cls: el.className, bg: s.backgroundColor, cx: r.x + r.width/2, cy: r.y + r.height/2, isActive };
  }).filter(s => s.cx > 0 && s.cy > 0);
  const start = Array.from(document.querySelectorAll('button,a,div')).find(el => (el.innerText || '').trim() === 'Start');
  const save = Array.from(document.querySelectorAll('button,a,div')).find(el => (el.innerText || '').trim() === 'Save score');
  const rect = el => {
    if (!el) return null;
    const r = el.getBoundingClientRect();
    return {cx: r.x + r.width/2, cy: r.y + r.height/2};
  };
  const activeIndices = squares.filter(s => s.isActive).map(s => s.idx);
  return JSON.stringify({
    body: body.slice(0, 400),
    level: levelMatch ? Number(levelMatch[1]) : null,
    squares: squares.slice(0, 36).map(s => ({ idx: s.idx, cx: s.cx, cy: s.cy })),
    startRect: rect(start),
    saveRect: rect(save),
    activeIndices,
    hasSave: body.includes('Save score'),
  });
})();
'''
        return json.loads(_do_js(js))

    def run_visual_memory(
        self, profile: MotionProfile, *, save_score: bool = True, max_level: int = 8
    ) -> dict[str, Any]:
        _ensure_live_profile()
        _ensure_safari_ready()
        self.log("evidence")
        self.goto("memory", wait_seconds=2.5)
        state = self.query_visual_memory_state()
        if state.get("startRect"):
            gx, gy = self.click_client_point(
                state["startRect"]["cx"], state["startRect"]["cy"],
                profile=MotionProfile(name="start", move_duration=0.06, move_steps=6, settle_sleep=0.2),
            )
            self.log("start_click", global_point=[gx, gy])
            time.sleep(0.8)
        for level in range(max_level):
            state = self.query_visual_memory_state()
            if state.get("hasSave") and state.get("saveRect"):
                break
            observed: list[int] = []
            deadline = time.time() + 8.0
            while time.time() < deadline:
                state = self.query_visual_memory_state()
                active = state.get("activeIndices") or []
                for idx in active:
                    if idx not in observed:
                        observed.append(idx)
                if observed and not active and time.time() > deadline - 6:
                    break
                time.sleep(0.03)
            squares = state.get("squares") or []
            if not squares:
                break
            for idx in observed:
                sq = next((s for s in squares if s.get("idx") == idx), None)
                if sq:
                    gx, gy = self.click_client_point(sq["cx"], sq["cy"], profile=profile)
                    self.log("visual_click", level=level + 1, idx=idx, global_point=[gx, gy])
            time.sleep(0.4)
        state = self.query_visual_memory_state()
        if save_score and state.get("saveRect"):
            gx, gy = self.click_client_point(
                state["saveRect"]["cx"], state["saveRect"]["cy"],
                profile=MotionProfile(name="save", move_duration=0.05, move_steps=5, settle_sleep=0.25),
            )
            self.log("save_click", global_point=[gx, gy])
            time.sleep(0.4)
        result = {"status": "ok", "final_state": self.query_visual_memory_state(), "log": str(self.log_path)}
        self.log("final_state", result=result)
        return result


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Visible Human Benchmark harness")
    sub = parser.add_subparsers(dest="cmd", required=True)

    aim = sub.add_parser("aim", help="Run a single Aim Trainer pass")
    aim.add_argument("--name", default="aim_manual")
    aim.add_argument("--move-duration", type=float, default=0.055)
    aim.add_argument("--move-steps", type=int, default=6)
    aim.add_argument("--settle-sleep", type=float, default=0.02)
    aim.add_argument("--no-save-score", action="store_true")

    sequence = sub.add_parser("sequence", help="Run Sequence Memory")
    sequence.add_argument("--name", default="sequence_manual")
    sequence.add_argument("--move-duration", type=float, default=0.050)
    sequence.add_argument("--move-steps", type=int, default=5)
    sequence.add_argument("--settle-sleep", type=float, default=0.025)
    sequence.add_argument("--max-level", type=int, default=12)
    sequence.add_argument("--no-save-score", action="store_true")

    chimp = sub.add_parser("chimp", help="Run Chimp Test")
    chimp.add_argument("--name", default="chimp_manual")
    chimp.add_argument("--move-duration", type=float, default=0.050)
    chimp.add_argument("--move-steps", type=int, default=5)
    chimp.add_argument("--settle-sleep", type=float, default=0.025)
    chimp.add_argument("--max-numbers", type=int, default=20)
    chimp.add_argument("--no-save-score", action="store_true")

    typing = sub.add_parser("typing", help="Run Typing Test")
    typing.add_argument("--name", default="typing_manual")
    typing.add_argument("--move-duration", type=float, default=0.05)
    typing.add_argument("--move-steps", type=int, default=5)
    typing.add_argument("--settle-sleep", type=float, default=0.02)
    typing.add_argument("--no-save-score", action="store_true")

    reaction = sub.add_parser("reactiontime", help="Run Reaction Time Test")
    reaction.add_argument("--name", default="reaction_manual")
    reaction.add_argument("--move-duration", type=float, default=0.05)
    reaction.add_argument("--move-steps", type=int, default=5)
    reaction.add_argument("--settle-sleep", type=float, default=0.02)
    reaction.add_argument("--num-clicks", type=int, default=5)
    reaction.add_argument("--no-save-score", action="store_true")

    verbal = sub.add_parser("verbal-memory", help="Run Verbal Memory Test")
    verbal.add_argument("--name", default="verbal_manual")
    verbal.add_argument("--move-duration", type=float, default=0.05)
    verbal.add_argument("--move-steps", type=int, default=5)
    verbal.add_argument("--settle-sleep", type=float, default=0.02)
    verbal.add_argument("--max-turns", type=int, default=300)
    verbal.add_argument("--no-save-score", action="store_true")

    number = sub.add_parser("number-memory", help="Run Number Memory Test")
    number.add_argument("--name", default="number_manual")
    number.add_argument("--move-duration", type=float, default=0.05)
    number.add_argument("--move-steps", type=int, default=5)
    number.add_argument("--settle-sleep", type=float, default=0.02)
    number.add_argument("--max-level", type=int, default=10)
    number.add_argument("--no-save-score", action="store_true")

    visual = sub.add_parser("visual-memory", help="Run Visual Memory Test")
    visual.add_argument("--name", default="visual_manual")
    visual.add_argument("--move-duration", type=float, default=0.05)
    visual.add_argument("--move-steps", type=int, default=5)
    visual.add_argument("--settle-sleep", type=float, default=0.02)
    visual.add_argument("--max-level", type=int, default=8)
    visual.add_argument("--no-save-score", action="store_true")

    suite = sub.add_parser("suite", help="Run all tests in order: Sequence → Aim → Chimp → Typing → Verbal → Number → Visual → Reaction Time")
    suite.add_argument("--name", default="suite_run")
    suite.add_argument("--from-test", default="sequence", choices=["sequence", "aim", "chimp", "typing", "verbal-memory", "number-memory", "visual-memory", "reactiontime"], help="First test to run")
    suite.add_argument("--no-save-score", action="store_true", help="Do not save score on any test")

    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    if args.cmd == "aim":
        harness = HumanBenchmarkHarness(args.name)
        result = harness.run_aim(
            MotionProfile(
                name=args.name,
                move_duration=args.move_duration,
                move_steps=args.move_steps,
                settle_sleep=args.settle_sleep,
            ),
            save_score=not args.no_save_score,
        )
        print(json.dumps(result, indent=2))
    elif args.cmd == "sequence":
        harness = HumanBenchmarkHarness(args.name)
        result = harness.run_sequence(
            MotionProfile(
                name=args.name,
                move_duration=args.move_duration,
                move_steps=args.move_steps,
                settle_sleep=args.settle_sleep,
            ),
            save_score=not args.no_save_score,
            max_level=args.max_level,
            fail_to_save=True,
        )
        print(json.dumps(result, indent=2))
    elif args.cmd == "chimp":
        harness = HumanBenchmarkHarness(args.name)
        result = harness.run_chimp(
            MotionProfile(
                name=args.name,
                move_duration=args.move_duration,
                move_steps=args.move_steps,
                settle_sleep=args.settle_sleep,
            ),
            save_score=not args.no_save_score,
            max_numbers=args.max_numbers,
        )
        print(json.dumps(result, indent=2))
    elif args.cmd == "typing":
        harness = HumanBenchmarkHarness(args.name)
        result = harness.run_typing(
            MotionProfile(
                name=args.name,
                move_duration=args.move_duration,
                move_steps=args.move_steps,
                settle_sleep=args.settle_sleep,
            ),
            save_score=not args.no_save_score,
        )
        print(json.dumps(result, indent=2))
    elif args.cmd == "reactiontime":
        harness = HumanBenchmarkHarness(args.name)
        result = harness.run_reactiontime(
            MotionProfile(
                name=args.name,
                move_duration=args.move_duration,
                move_steps=args.move_steps,
                settle_sleep=args.settle_sleep,
            ),
            save_score=not args.no_save_score,
            num_clicks=args.num_clicks,
        )
        print(json.dumps(result, indent=2))
    elif args.cmd == "verbal-memory":
        harness = HumanBenchmarkHarness(args.name)
        result = harness.run_verbal_memory(
            MotionProfile(
                name=args.name,
                move_duration=args.move_duration,
                move_steps=args.move_steps,
                settle_sleep=args.settle_sleep,
            ),
            save_score=not args.no_save_score,
            max_turns=args.max_turns,
        )
        print(json.dumps(result, indent=2))
    elif args.cmd == "number-memory":
        harness = HumanBenchmarkHarness(args.name)
        result = harness.run_number_memory(
            MotionProfile(
                name=args.name,
                move_duration=args.move_duration,
                move_steps=args.move_steps,
                settle_sleep=args.settle_sleep,
            ),
            save_score=not args.no_save_score,
            max_level=args.max_level,
        )
        print(json.dumps(result, indent=2))
    elif args.cmd == "visual-memory":
        harness = HumanBenchmarkHarness(args.name)
        result = harness.run_visual_memory(
            MotionProfile(
                name=args.name,
                move_duration=args.move_duration,
                move_steps=args.move_steps,
                settle_sleep=args.settle_sleep,
            ),
            save_score=not args.no_save_score,
            max_level=args.max_level,
        )
        print(json.dumps(result, indent=2))
    elif args.cmd == "suite":
        order = ["sequence", "aim", "chimp", "typing", "verbal-memory", "number-memory", "visual-memory", "reactiontime"]
        try:
            start_idx = order.index(args.from_test)
        except ValueError:
            start_idx = 0
        save = not args.no_save_score
        profile = MotionProfile(name=args.name, move_duration=0.05, move_steps=5, settle_sleep=0.025)
        results = []
        for test_id in order[start_idx:]:
            name = f"{args.name}_{test_id}"
            harness = HumanBenchmarkHarness(name)
            if test_id == "sequence":
                r = harness.run_sequence(profile, save_score=save, max_level=12, fail_to_save=True)
            elif test_id == "aim":
                r = harness.run_aim(profile, save_score=save)
            elif test_id == "chimp":
                r = harness.run_chimp(profile, save_score=save, max_numbers=20)
            elif test_id == "typing":
                r = harness.run_typing(profile, save_score=save)
            elif test_id == "verbal-memory":
                r = harness.run_verbal_memory(profile, save_score=save, max_turns=300)
            elif test_id == "number-memory":
                r = harness.run_number_memory(profile, save_score=save, max_level=10)
            elif test_id == "visual-memory":
                r = harness.run_visual_memory(profile, save_score=save, max_level=8)
            elif test_id == "reactiontime":
                r = harness.run_reactiontime(profile, save_score=save, num_clicks=5)
            else:
                r = {"status": "skipped", "test": test_id}
            results.append({"test": test_id, "status": r.get("status", "?"), "log": r.get("log")})
            print(json.dumps({"test": test_id, "result": r}, indent=2))
        print(json.dumps({"suite": "complete", "results": results}, indent=2))


if __name__ == "__main__":
    main()
