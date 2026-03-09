# Live Safari / Visible Browser Task — Mandatory Stack Checklist

This checklist encodes what we learned from Human Benchmark (success) and mouseaccuracy.com (failures): **visible clicks only land when Safari is truly frontmost, and claims must be backed by evidence, not shell success.**

## When This Applies

**Any** task that involves:
- Driving the cursor to click or interact in Safari (or another visible browser)
- Aim trainers, puzzle sites, canvas sites, form submission, etc.

Use the **full stack** every time. Do not default to `--skip-evidence` or ad hoc scripts.

## Mandatory Steps (No Omissions)

1. **Mission Control up (live profile)**
   - Run: `mission_control.py up live --json` (optionally `--open` to open Control Room and Phoenix in the browser).
   - Brings up **Phoenix + Control Room** so (a) the evidence pipeline and capture can run, and (b) the run is **observable** (live traces, runtime state). For profile details and when to use other profiles (architecture, full), see `MISSION_CONTROL_STACK_AND_PROFILES.md`.

2. **Hide Cursor, activate Safari**
   - Before any visible click: hide Cursor (e.g. Cmd+H), then activate Safari.
   - Proven: when Cursor stayed frontmost, Safari received **zero** DOM mouse events from our Quartz path.

3. **Evidence gate (Safari readiness)**
   - Run: `mission_control.py evidence Safari --require-frontmost --capture --json`
   - Equivalent in code: `_ensure_safari_ready()` which calls `_hide_cursor_app_and_activate_safari()` then the evidence command.
   - **Do not proceed** until `ready_for_visible_task` is true. If it fails, fix blockers (focus, accessibility, etc.) before clicking.

4. **Coordinate discipline**
   - Use **window bounds + content inset** (or page viewport origin when available) to convert DOM/client coordinates to **screen-global** coordinates.
   - Do **not** use raw screenshot/window-relative pixel coordinates as click coordinates (Retina scaling and window offset break this).

5. **Post-action proof (where applicable)**
   - For mastery or diagnostic runs: capture a screenshot **after** start click (or after key transitions) to prove the page state (e.g. countdown cleared, live targets visible).
   - Use the capture path returned by the evidence payload when `--capture` is set.

6. **Artifact logging**
   - Log evidence payload, viewport_origin, and per-step state (e.g. targets found, clicks, mode) so failures can be diagnosed from logs, not memory.

## Tools and Code Surfaces

| Tool / surface | Purpose |
|----------------|--------|
| `mission_control.py up live` | Bring up live profile (Phoenix + Control Room) for evidence, capture, and run observability |
| `mission_control.py evidence Safari --require-frontmost --capture` | GUI evidence gate + optional screenshot |
| `gui_evidence.py` | Frontmost check, Quartz window, capture_front_window, blockers |
| `_hide_cursor_app_and_activate_safari()` | Focus acquisition so clicks land in Safari |
| `_ensure_safari_ready()` | Hide Cursor → activate Safari → evidence gate; raise if not ready |
| `_get_safari_window_bounds()` | Safari window rect for coordinate mapping |
| `_global_from_client(cx, cy, viewport_origin=...)` | Client/page coords → screen-global for Quartz |

## Reference Harnesses

- **Human Benchmark:** `human_benchmark_suite.py` — uses full evidence, frontmost, bounds+inset, artifact log.
- **Mouse Accuracy:** `mouse_accuracy_suite.py` — same: mission_control up, _ensure_safari_ready(), viewport origin, per-click correction, log.
- **XBitLabs:** `xbitlabs_path_follow.py` — must use the same stack by default (evidence on unless explicit `--skip-evidence` for a fast rerun).

## Why This Exists

We repeatedly saw:
- Shell/AppleScript success **≠** visible click received by the page.
- Safari not frontmost **⇒** zero DOM events from our clicks.
- Window-relative screenshot coordinates used as screen coords **⇒** clicks off target or in the wrong app.

So: **no blind retries.** Prove state before action; use the full stack for every live Safari task.

## Related: Mission-control profiles and other tools

For **which profile** to use (live vs architecture vs full) and what **Phoenix, Control Room, Structurizr, Sourcegraph** are for, see **`MISSION_CONTROL_STACK_AND_PROFILES.md`**. Summary: live Safari/browser task → **up live** (Phoenix + Control Room); architecture-heavy → add **architecture** or **full**; code-path debugging → use Sourcegraph bridge from the Control Room. For a single checklist of what is done vs next from all angles (operational, control room, integration, docs, verification), see **`NEXT_MOVES_PHD.md`**.
