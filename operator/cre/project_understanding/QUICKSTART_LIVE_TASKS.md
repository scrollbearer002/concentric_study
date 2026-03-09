# Quick start for live tasks (Safari / visible browser)

Minimal sequence to run a live Safari task with the full stack. For the full checklist, see **LIVE_SAFARI_STACK_CHECKLIST.md**. For done vs next per angle, see **NEXT_MOVES_PHD.md**.

## 1. Bring up the live stack

```bash
cd operator
python3 cre/project_understanding/tools/mission_control.py up live --json
```

Optional: add `--open` to open Control Room and Phoenix in the browser.

## 2. Evidence gate (Safari readiness)

With **Safari frontmost** (hide Cursor with Cmd+H, then activate Safari):

```bash
python3 cre/project_understanding/tools/mission_control.py evidence Safari --require-frontmost --capture --json
```

Proceed only when the payload has `"ready_for_visible_task": true`.

## 3. Run a harness

Examples (from `operator/`):

| Task | Command |
|------|---------|
| **BrowserBotics PhD robot** | `./venv/bin/python cre/run_browserbotics_safari_phd.py` |
| **Human Benchmark** | See `cre/project_understanding/tools/human_benchmark_suite.py` |
| **Mouse Accuracy** | See `cre/project_understanding/tools/mouse_accuracy_suite.py` |
| **XBitLabs Path Follow** | See `cre/project_understanding/tools/xbitlabs_path_follow.py` |

Harnesses that use the full stack call the evidence gate (or `_ensure_safari_ready()`) and use bounds + viewport for coordinates.

## Optional: health check before a run

```bash
python3 cre/project_understanding/tools/mission_control.py doctor --json
python3 cre/project_understanding/tools/mission_control.py status --json
```

## See also

- **LIVE_SAFARI_STACK_CHECKLIST.md** — mandatory steps and tools
- **MISSION_CONTROL_STACK_AND_PROFILES.md** — profiles (live, debug, architecture, full)
- **NEXT_MOVES_PHD.md** — done vs next from all angles
