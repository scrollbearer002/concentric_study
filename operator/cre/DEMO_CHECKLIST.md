# CRE demo checklist (show off to colleagues)

## 1. Live demo

1. **Start the kernel:** Open **Hammerspoon** (menu bar or Applications) → **Reload Config** (or restart Hammerspoon so `~/.hammerspoon/init.lua` loads).
2. **Run the showcase:**
   ```bash
   cd /Users/christianpardo/rust   # or your repo root
   bash operator/cre/showcase.sh
   ```
3. **Point out:** Latency (avg ms for POST ping), screenshot timing/size, Cursor state (if Cursor is running). Compare to “old” numbers in the script output or in SHOWCASE.md (e.g. process spawn ~107 ms, disk I/O ~294 ms).

## 2. Slack / email (copy-paste)

Use the text in **operator/cre/SLACK_OR_EMAIL.txt**. Edit the repo path if needed, then send.

## 3. Deep dive (full test suite)

After the showcase, run:

```bash
bash operator/tests/run_cre_tests.sh
```

**Phases 0–7 (walk-through):**

| Phase | What it does |
|-------|----------------|
| **0** | Baseline benchmarks: process spawn (~107 ms), disk I/O (~294 ms), sleep blocking, file watcher (~45 ms). Proves “old” overhead. |
| **1** | Kernel startup (GET/POST), backward compat (full_system_check), kernel latency (<10 ms target). |
| **2** | Vision: screenshot latency (old vs new), OCR accuracy, memory usage, vision integration. |
| **3** | Input: click latency (old vs new), click accuracy, Bezier (skip), send_to_right_chat integration. |
| **4** | State: state read latency, Electron hydration, tree completeness, observe_run integration. |
| **5** | Wait: UI responsiveness, wait accuracy, event delivery, wait integration. |
| **6** | Bridge: IPC latency (file vs HTTP), command reliability, concurrent commands, bridge integration. |
| **7** | Validation: performance regression, stress, academic validation (baseline vs CRE). |

**Note:** With the kernel **down**, many tests skip (they report PASS or SKIP). With the kernel **up**, you get real latency and integration results. `test_backward_compat` runs `full_system_check.sh`; that check fails if `rg` (ripgrep) is not installed—install with `brew install ripgrep` if you want all 26 checks to pass.
