# Allowlist-First Pre-Action Verification: PhD-Level Implementation Outline

**Purpose:** Concrete implementation plan for the first enhancement in the ROADMAP_PHD_RESEARCH_MEMO — deterministic pre-action checks that block invalid or unsafe actions before handler execution. This document provides rationale, literature tie-in, pseudocode, integration points, ablation design, and extension paths.

**References:** VeriSafe Agent (Lee et al., arXiv:2503.18492, ACM MobiCom 2025); FormalJudge (arXiv:2602.11136); ROADMAP_PHD_RESEARCH_MEMO.md §3.2.

---

# Part I — Rationale and Literature Tie-In

## 1.1 Why allowlist-first

- **VeriSafe Agent** (Lee et al., 2025) shows that **pre-action** logic-based verification (intent → formal spec, rule check before execution) achieves 94–98% verification accuracy and blocks unsafe GUI actions. Concentric Study currently has **post-action** verification (VerificationGate, CRAFT-style) and **pre-action semantic** checks (_ensure_canvas_clear, VLM-based). A **deterministic pre-action** layer closes the gap without requiring full autoformalization (NL → DSL → SMT) in the first step.
- **FormalJudge** (2026) demonstrates that a **formal-of-thought** pipeline (LLM decomposes intent → constraints verified by Z3) improves oversight over pure LLM-as-judge. An allowlist is a minimal formal layer: allowed action types + parameter constraints (e.g. coordinates in screen bounds, keys from a fixed set). It provides **block-before-execute** semantics and a clear extension path to Horn clauses or Z3 later.
- **Incremental risk:** Allowlist is **additive**. It does not replace VerificationGate or _ensure_canvas_clear; it runs **before** the handler. If the allowlist is permissive (e.g. all known action types allowed with loose bounds), behavior matches current system; tightening constraints then removes invalid actions without changing the rest of the pipeline.

## 1.2 Design principles

- **Deterministic:** No LLM call inside the allowlist check. Rules are data-driven (allowed types, bounds, key set).
- **Traceable:** When an action is blocked, record the reason (e.g. `action_type_not_allowed`, `coords_out_of_bounds`) in the trace so ablation and diagnosis can measure false positives and blocked-unsafe counts.
- **Pluggable:** Allowlist is optional (e.g. env `DISABLE_ACTION_ALLOWLIST=1` or `ctx.action_allowlist = None`) so ablation can run with/without it.
- **Extensible:** Schema supports (1) action-type allowlist, (2) per-action parameter constraints (bounds, enums), (3) optional future “critical action” set that could later be fed to a DSL/Z3 path.

---

# Part II — ActionAllowlist Module: Pseudocode and Schema

## 2.1 Data structures

```text
# Allowlist configuration (JSON or in-code)
ActionAllowlistConfig:
  allowed_action_types: set[str]     # e.g. {"click", "keystroke", "set_stroke_color", "draw_concentric_triangles", ...}
  screen_bounds: optional { x_min, x_max, y_min, y_max }  # pixel bounds; None = skip coord check
  coord_actions: set[str]           # action types that require x,y in screen_bounds (e.g. {"click", "draw_path", ...})
  keystroke_allowed_keys: optional set[str]  # None = allow any; else restrict to safe keys
  critical_actions: set[str]        # subset that may later get DSL checks (e.g. {"click", "type_text"})
```

## 2.2 Core API

```python
def check_action(action_type: str, args: dict, config: ActionAllowlistConfig,
                 screen_bounds: tuple[int,int,int,int] | None) -> AllowlistResult:
    """
    Returns AllowlistResult(allowed: bool, reason: str | None).
    If allowed is False, reason is the violation (e.g. "action_type_not_in_allowlist",
    "coords_out_of_bounds", "keystroke_key_not_allowed").
    """
    if action_type not in config.allowed_action_types:
        return AllowlistResult(False, "action_type_not_in_allowlist")

    if action_type in config.coord_actions and config.screen_bounds and screen_bounds:
        x, y = args.get("x"), args.get("y")
        if x is not None and y is not None:
            x_min, x_max, y_min, y_max = screen_bounds  # or config.screen_bounds
            if not (x_min <= x <= x_max and y_min <= y <= y_max):
                return AllowlistResult(False, "coords_out_of_bounds")

    if action_type in ("keystroke", "key") and config.keystroke_allowed_keys is not None:
        key = args.get("key")
        if key is not None and key not in config.keystroke_allowed_keys:
            return AllowlistResult(False, "keystroke_key_not_allowed")

    return AllowlistResult(True, None)
```

## 2.3 AllowlistResult and trace representation

```text
AllowlistResult:
  allowed: bool
  reason: str | None   # violation code if not allowed

# When blocked, trace step should include:
# action_result: { "success": false, "blocked_by_allowlist": true, "reason": "coords_out_of_bounds" }
# so that (1) DiagnosticReader and HealingOrchestrator can classify, (2) ablation can count blocks.
```

## 2.4 Population of allowed_action_types

- **Option A (minimal):** Derive from `ACTION_HANDLERS.keys()` at load time so any registered handler is allowed by default; then restrict with `critical_actions` or parameter constraints.
- **Option B (explicit):** Maintain a config file (e.g. `cre/action_allowlist.json`) listing allowed types and constraints; load in recovery or agent init. Enables “deny by default” for unknown actions.
- **Recommendation for MVP:** Option A with optional override file. If no file, `allowed_action_types = set(ACTION_HANDLERS.keys())`; if file exists, use it so you can shrink the set for safety experiments.

---

# Part III — Integration Points

## 3.1 Hook in recovery.py (_execute_action_with_recovery)

**Location:** After `handler = ACTION_HANDLERS.get(action_type)` and `if handler is None: return False`, and **before** `tw = ctx.trace_writer` (or immediately after `begin_step` and before the `for attempt` loop).

**Recommended:** After `trace_step = tw.begin_step(step_index)` and pre_state fill, **before** `_ensure_canvas_clear` and the `for attempt` loop. That way:
- The step is started and the proposed action is recorded.
- If allowlist blocks, set `trace_step.action_result = {"success": False, "blocked_by_allowlist": True, "reason": result.reason}`; call `tw.end_step(trace_step)`; return False (or raise a dedicated exception so the plan loop can record failure and optionally retry).
- If allowlist passes, proceed to _ensure_canvas_clear (if applicable) and handler as today.

**Pseudocode insertion:**

```text
# After trace_step.pre_state is set; before "if action_type in _SOM_DEPENDENT_ACTIONS..."

if getattr(ctx, "action_allowlist", None) is not None:
    screen_bounds = getattr(ctx, "screen_bounds", None)  # or from NSScreen helper
    allow_result = ctx.action_allowlist.check_action(action_type, args, ctx.action_allowlist.config, screen_bounds)
    if not allow_result.allowed:
        if trace_step:
            trace_step.action_result = {"success": False, "blocked_by_allowlist": True, "reason": allow_result.reason}
            tw.end_step(trace_step)
        return False
```

## 3.2 Hook in agent.py (universal orchestrator)

- **agent.py** builds `ctx` and calls `_execute_action_with_recovery(ctx, resolved, i)`. The same allowlist check lives inside recovery; **ctx** must carry `action_allowlist` (and optionally `screen_bounds`) when allowlist is enabled.
- **Initialization:** In test_excalidraw_covt.py and agent.py, after building _Ctx, optionally instantiate `ActionAllowlist(config)` and set `ctx.action_allowlist = allowlist`. Config can come from env (e.g. `ACTION_ALLOWLIST_CONFIG_PATH`) or default in-code. If `DISABLE_ACTION_ALLOWLIST=1`, set `ctx.action_allowlist = None`.

## 3.3 Screen bounds

- **Option A:** Constant for a known display (e.g. `(0, 0, 2880, 1800)` for Retina). Simple but brittle across machines.
- **Option B:** Query once at init from NSScreen (e.g. in startup or agent_core) and attach to ctx as `ctx.screen_bounds = (x_min, x_max, y_min, y_max)` in logical or pixel space consistent with click args. agent_core already has `_pixel_to_global_quartz` and NSScreen; a small helper `get_screen_bounds_pixels()` would suffice.
- **Recommendation:** Option B with fallback to Option A if NSScreen unavailable (e.g. headless test).

---

# Part IV — Ablation Design

## 4.1 Conditions

- **Baseline (current):** No allowlist; `ctx.action_allowlist = None`.
- **Allowlist ON:** Allowlist enabled with config (allowed types = ACTION_HANDLERS.keys(), screen_bounds set, optional keystroke restrict). No change to allowed actions initially; then tighten (e.g. restrict to safe keys, or shrink allowed_action_types) to measure **blocked_unsafe** and **false_positive** (legitimate actions blocked).

## 4.2 Extension of ablation_harness.py

- Add condition **E: Allowlist** (e.g. `DISABLE_ACTION_ALLOWLIST=0` and load default allowlist config).
- Add condition **F: Allowlist + tightened** (e.g. keystroke_allowed_keys = safe subset, or coords clamped to canvas region).
- **Metrics to log per run:**
  - `blocked_by_allowlist_count`: number of steps where `action_result.blocked_by_allowlist == true`.
  - `allowlist_reasons`: dict of reason → count (for diagnosis).
  - Outcome (success/failure), wall time, num_steps — as today. Compare E vs baseline (A/B/C/D) and F vs E to measure impact of pre-action blocking on success rate and false positives.

## 4.3 Trace schema for ablation

- Ensure each trace step can include `action_result.blocked_by_allowlist` and `action_result.reason` when blocked. Then `_count_trace_events` (or a new `_count_allowlist_blocks`) can scan trace.jsonl for these fields. No change to trust_skip counting; this is additive.

## 4.4 Suggested ablation table (summary)

| Condition | Description | Metrics |
|-----------|-------------|---------|
| D | Full system (current) | baseline success, steps, latency |
| E | Full system + allowlist (permissive) | blocked_allowlist_count (expect 0 if permissive), success, steps |
| F | Full system + allowlist (tightened) | blocked_allowlist_count, allowlist_reasons, success, steps; measure false positives |

---

# Part V — Potential Extensions

## 5.1 LLM-assisted allowlist population

- For **critical_actions**, an optional step: before execution, LLM sees intent + proposed action and outputs a structured verdict (allow/deny + reason). That verdict is then checked against the **deterministic** allowlist (e.g. type + bounds); LLM output is not trusted alone but can feed into a human review queue or into a future DSL. Keeps the “deterministic pre-check” property while allowing learned policies later.

## 5.2 Progression to Horn clauses / Z3

- **FormalJudge** and **VeriSafe** use formal specs. A natural next step: for actions in `critical_actions`, define a small DSL (e.g. “precondition: canvas_focused AND coord_in_canvas”) and translate to SMT (Z3) or Horn clauses. The allowlist remains the **first** gate; a second gate “formal_verify(action, state)” can be added for a subset of actions when the pipeline is ready. The memo’s “start with allowlist” is exactly this staging.

## 5.3 Dual judge (formal + contextual)

- **OS-Sentinel** and the essay (§3) describe a **formal verifier** plus a **contextual judge** (VLM). In Concentric Study terms: allowlist = formal verifier; VerificationGate (and _ensure_canvas_clear) = contextual. Document the two as complementary: allowlist blocks on **syntax and bounds**; VLM checks on **semantics and visual state**.

---

# Part VI — File and Module Layout

| Item | Location | Responsibility |
|------|----------|----------------|
| ActionAllowlist class + AllowlistResult | New: `operator/agent_infra/action_allowlist.py` (or `operator/security/action_allowlist.py`) | check_action(action_type, args, config, screen_bounds); config load from JSON or defaults |
| Config file (optional) | `operator/cre/action_allowlist.json` | allowed_action_types, screen_bounds, coord_actions, keystroke_allowed_keys, critical_actions |
| Integration | `operator/agent_infra/recovery.py` | After begin_step; if ctx.action_allowlist: check; on block set action_result and end_step, return False |
| Context wiring | `operator/cre/test_excalidraw_covt.py`, `operator/agent.py` | Build ActionAllowlist(config); set ctx.action_allowlist; set ctx.screen_bounds if available |
| Ablation | `operator/cre/ablation_harness.py` | Add conditions E, F; env DISABLE_ACTION_ALLOWLIST; parse trace for blocked_by_allowlist_count, allowlist_reasons |

---

# Part VII — References

- Lee et al. (2025). VeriSafe Agent: Safeguarding Mobile GUI Agent via Logic-based Action Verification. arXiv:2503.18492; ACM MobiCom 2025.
- FormalJudge (2026). A Neuro-Symbolic Paradigm for Agentic Oversight. arXiv:2602.11136.
- ROADMAP_PHD_RESEARCH_MEMO.md — Pre-action verification §3.2, effort/impact table.

This outline is the implementation plan for allowlist-first pre-action verification. Proceed with Part II (module + schema) and Part III (integration) for the MVP; then Part IV (ablation) and Part V (extensions) for evaluation and thesis narrative.
