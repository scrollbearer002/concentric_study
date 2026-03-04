# Codex Runtime Environment (CRE) — What It Can Do

One-pager for colleagues: what CRE is, what it replaces, and how to demo it.

---

## What is CRE?

**CRE** is a **memory-resident automation kernel** for macOS. One long-lived process (Hammerspoon) listens on `localhost:9999` and executes UI actions (click, screenshot, state read, wait) in-process. Your Python or Bash “brain” sends JSON over HTTP instead of spawning `cliclick`, `screencapture`, or `osascript` for every action.

**Goal:** Remove process-spawn and disk I/O latency so real-time AI-driven control (vision → think → click → verify) is fast and stable instead of jittery or freezing.

---

## What CRE Replaces (and why it’s better)

| Old (process-bound) | CRE (memory-resident) | Benefit |
|--------------------|----------------------|--------|
| `cliclick c:x,y` (new process per click) | `POST {"command":"click","args":{"x",y}}` → `hs.eventtap.leftClick()` | Sub-ms click latency, no spawn overhead |
| `screencapture -x /tmp/img.png` + Python reads file | `POST screenshot` → kernel returns base64 in RAM | No disk I/O; 10–20× faster capture→use |
| `osascript` UI queries | `POST dump_state` → `hs.axuielement` + Electron hydration | Direct AX API, fewer dropped keystrokes |
| File watcher (write file → FSEvents → script) | `POST` to localhost:9999 | &lt;5 ms round-trip vs 100–500 ms |

---

## Quick demo (show off to colleagues)

1. **Start the kernel**  
   Open **Hammerspoon** → **Reload Config** (or ensure `~/.hammerspoon/init.lua` is the Codex kernel and restart Hammerspoon).

2. **Run the showcase script** (shows liveness, latency, screenshot, state, commands):
   ```bash
   bash operator/cre/showcase.sh
   ```
   - If the kernel is **down**: it prints what CRE can do and how to start it.
   - If the kernel is **up**: it runs GET/POST ping, latency sample, in-memory screenshot size/timing, and `dump_state` for Cursor.

3. **One-liner checks**
   ```bash
   curl -s http://127.0.0.1:9999
   curl -s -X POST http://127.0.0.1:9999 -H "Content-Type: application/json" -d '{"command":"ping"}'
   ```

4. **Full test suite** (all CRE phases: benchmarks, kernel, vision, input, state, wait, bridge, validation):
   ```bash
   bash operator/tests/run_cre_tests.sh
   ```

---

## Capabilities (what the kernel can do)

| Command | Purpose |
|--------|--------|
| `ping` | Health check; returns `{"status":"ok"}`. |
| `click` | Click at (x, y) via `hs.eventtap` (replaces cliclick). |
| `screenshot` | Full screen or region; returns base64 PNG (replaces screencapture). |
| `dump_state` | App title, focused window; forces Electron AX hydration (replaces osascript). |
| `wait_for_window` | Poll for an app’s window (optional timeout). |

---

## How to drive the kernel

- **curl:**  
  `curl -s -X POST http://127.0.0.1:9999 -H "Content-Type: application/json" -d '{"command":"ping"}'`
- **Python:**  
  `from operator.codex_client import CodexClient; CodexClient().ping()`, `.click(x,y)`, `.screenshot()`, `.get_ui_tree()`
- **Bridge script:**  
  `bash ai-bridge/cre_send_command.sh ping '{}'`

---

## Why the kernel starts reliably (even when IPC is broken)

Init is **HTTP-first**: the server on port 9999 is started **before** any `hs.ipc` / CLI install. IPC is deferred with `hs.timer.doAfter(2, ...)` and wrapped in `pcall`, so:

- The kernel is “up” as soon as HTTP responds; CRE tests use `curl` to 9999 and don’t depend on the `hs` CLI.
- IPC/CLI failures no longer block startup; you can verify with `operator/cre/verify_kernel.sh` or the showcase script.

---

## Files to point colleagues at

- **Demo:** `bash operator/cre/showcase.sh`
- **Verify kernel only:** `bash operator/cre/verify_kernel.sh`
- **Full CRE suite:** `bash operator/tests/run_cre_tests.sh`
- **This one-pager:** `operator/cre/SHOWCASE.md`
- **Kernel + verify + CLI notes:** `operator/cre/README.md`
