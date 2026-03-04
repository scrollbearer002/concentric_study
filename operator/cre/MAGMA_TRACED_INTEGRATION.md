# Why Magma Wasn’t Using Screenshots, Self-Healing, or Learning

## The gap

The Magma flow (`magma_open_canvas.py`, `magma_draw_bmw_e30.py`, `magma_bmw_e30_full_run.py`) was implemented as **standalone ad-hoc scripts**. They do **not** use the project’s shared infrastructure, so:

| Capability | Main flow (Excalidraw/Kleki/agent.py) | Magma flow (current) |
|------------|--------------------------------------|------------------------|
| **Screenshots** | TraceWriter run dir + `screencapture` at each step; `pre_state`/`post_state` include screenshot paths; diagnostic screenshots on failure | No TraceWriter; no per-step screenshots; no run dir or trace |
| **Self-healing** | recovery._execute_action_with_recovery: on failure → _diagnose_failure (VLM), _execute_recovery, retry; OuterLoop + HealingOrchestrator on run failure | JS returns "not_found" → script continues; no diagnosis, no retry, no alternative strategy |
| **Learning** | Summarizer.ingest_step per step; SkillLibrary.ingest_from_trace on success; ReflectionJournal + RulesStore on failure, injected into diagnosis | No trace → no ingestion; no reflection or rules; nothing learned from Magma runs |

So screenshots, self-healing, and learning weren’t “implied” for Magma because **the Magma scripts were never wired to the agent_infra stack** (TraceWriter, recovery, HealingOrchestrator, SkillLibrary, ReflectionJournal, RulesStore).

## Fix: traced Magma run

To make Magma use the same stack:

1. **Screenshots** — Use TraceWriter; for each step call `screencapture` and attach the path to `trace_step.pre_state["screenshot"]` and/or `post_state["screenshot"]`; write steps to `cre/runs/<run_id>/trace.jsonl` and finalize `manifest.json`.
2. **Self-healing** — On "not_found" (or any step failure): capture a diagnostic screenshot, record the step as failed in the trace, try a fallback (e.g. different JS selector or Quartz click), and retry; if still failing, finalize the run as failure so HealingOrchestrator can classify it.
3. **Learning** — On success: call `SkillLibrary.ingest_from_trace(run_dir)` so the Magma BMW E30 run becomes a reusable skill; on failure: append to ReflectionJournal (and optionally RulesStore) so future runs or diagnosis can use “lessons learned” from Magma.

The script **`cre/magma_traced_run.py`** implements this integration:

- **Screenshots:** Every step runs `screencapture` → `run_dir/screenshots/step_NN_pre.png` and `step_NN_post.png` (or `_fail` on error); paths go into `pre_state["screenshot"]` and `post_state["screenshot"]`.
- **Self-healing:** For "New canvas" and "Landscape drawing", if the first JS returns `not_found`, a second attempt uses a broader selector. Failures are recorded in the trace and `tw.record_failure()` so the run has a proper failure_step and error_summary.
- **Learning:** On success, `SkillLibrary.ingest_from_trace(tw.run_dir)` is called. On failure, `ReflectionJournal.record(...)` is called with a short lesson.

**Usage:** From `operator/`: `./venv/bin/python cre/magma_traced_run.py`
