# PhD Deep Dive Addendum: Full Project + 15 Most Recent Test Runs

**Purpose:** Cross-check the full `concentric_study` codebase and the 15 most recent test runs against PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md and ESSAY_PROJECT_OVERLAP_PHD.md to capture anything missed. **Facts only.**

**Date:** Run directory listing and manifest/trace inspection as of the latest runs under `operator/cre/runs/`.

---

# Part I — Run Diversity and the 15 Most Recent Runs

## 1.1 How “15 most recent” was defined

Run directories under `operator/cre/runs/` were ordered by modification time. The following count as “recent” for this addendum (excluding the `reflection_journal.jsonl` file): **38ccf14da0f3, ada333efcf90, 906d2c8a354d, f983c31a49a4, a2731e00f68d, 9627f400774b, de4f52371a9b, 1292149a502a, db33f14b75f8, ablation_20260223_121639, d07655943ebf, 070f6b51ff4a, 3537e37f831e, 7071c4ab92c2, 4272ee0431ea.**

## 1.2 Run types observed in the repo (all runs, not just 15)

From manifest `task_id` and `agent_config` across all runs with `manifest.json`:

| Run type | task_id (examples) | Entry point / harness | Manifest shape |
|----------|--------------------|------------------------|----------------|
| **Concentric triangles (covt)** | `CONCENTRIC_TRIANGLES_CLEAN` | test_excalidraw_covt.py (CONCENTRIC_TRIANGLES_CLEAN=1) | agent_config: mode "enterprise", model; num_steps often 12+ |
| **Universal agent** | `DRAW_4_CONCENTRIC_BLACK_TRIANGLES` | agent.py | agent_config: mode "universal", url, **capabilities** list (Accessibility Engine, Set-of-Mark Overlay, Unified Element Map, Beta-Binomial Trust, Coordinate Cache, Perceptual Hash Gate, Site Knowledge Base, Stroke Count Logging, Inference Router, Episodic Memory, Web Primitives, Dynamic VLM Planning); num_steps 3–4; steps like a11y_passive_snapshot, set_stroke_color, click, draw_concentric_triangles |
| **Kleki BMW** | `KLEKI_BMW_E30_M3` | test_kleki_bmw.py (or similar) | agent_config: platform "kleki.com", iterations 5, subject "1991 BMW E30 M3"; steps_summary can list phase names (bmw_skeleton, bmw_form_blocking, bmw_mechanical, bmw_lighting, bmw_final) with "failed" even when outcome is "success" (phase-level success) |
| **Eiffel / landscape** | `DRAW_THE_PARIS_EIFFEL_TOWER_LANDSCAPE:_1`, `DRAW_A_DETAILED_EIFFEL_TOWER_ON_EXCALIDR` | agent.py | agent_config: mode "enterprise"; steps e.g. clear_canvas, draw_eiffel_landscape, verify_success |
| **Red circle / composition** | `DRAW_A_RED_CIRCLE_ON_THE_EXCALIDRAW_CANV`, `CLEAR_THE_CANVAS_AND_DRAW_A_RED_CIRCLE_I`, `CREATE_AN_EXCALIDRAW_MASTERPIECE:_1)_CLE`, `CREATE_A_COMPOSITION_ON_EXCALIDRAW:_1)_C` | agent.py | Dynamic goal-derived task_ids; outcome success/failure/error |
| **Escalation (failure)** | task_id `""` in one run | test_excalidraw_covt.py + OuterLoop | outcome "failure"; run b7dcf9ee41f5 has ESCALATION.md |

So the project supports **multiple task types and entry points**, not only CONCENTRIC_TRIANGLES_CLEAN. The “primary target” is Excalidraw, but **agent.py** produces a different manifest (capabilities list, fewer steps, different step names) and handles multiple goals (concentric triangles, Eiffel, red circle, composition). Kleki BMW runs produce **experiment_summary.md** and **iteration_N.png / iteration_N_annotation.md** — a separate artifact set for multi-phase iterative tasks.

## 1.3 The 15 most recent runs: summary

| Run ID | Has manifest | task_id | outcome | Notes |
|--------|--------------|---------|---------|--------|
| 38ccf14da0f3 | Yes | DRAW_4_CONCENTRIC_BLACK_TRIANGLES | success | Universal agent; 4 steps |
| ada333efcf90 | Yes | DRAW_4_CONCENTRIC_BLACK_TRIANGLES | success | Universal agent |
| 906d2c8a354d | Yes | DRAW_4_CONCENTRIC_BLACK_TRIANGLES | success | Universal agent |
| f983c31a49a4 | Yes | DRAW_4_CONCENTRIC_BLACK_TRIANGLES | success | Universal agent |
| a2731e00f68d | Yes | DRAW_4_CONCENTRIC_BLACK_TRIANGLES | failure | Universal agent |
| 9627f400774b | Yes | DRAW_4_CONCENTRIC_BLACK_TRIANGLES | failure | Universal agent |
| de4f52371a9b | Yes | DRAW_4_CONCENTRIC_BLACK_TRIANGLES | failure | Universal agent |
| 1292149a502a | Yes | DRAW_4_CONCENTRIC_BLACK_TRIANGLES | success | Universal agent; 3 steps |
| db33f14b75f8 | Yes | DRAW_4_CONCENTRIC_BLACK_TRIANGLES | failure | Universal agent |
| ablation_20260223_121639 | **No** | — | — | Ablation harness output dir; **empty** (harness writes logs/csv/summary into this dir but each rep’s trace goes to main runs/; latest run_dir is found by mtime) |
| d07655943ebf | Yes | KLEKI_BMW_E30_M3 | success | 5 iterations; experiment_summary.md, iteration_1..5.png, iteration_*_annotation.md; steps_summary lists 5 phases all "failed" but outcome success |
| 070f6b51ff4a | **No** | — | — | trace.jsonl + iteration_1..3.png + iteration_*_annotation.md; **no manifest.json** (incomplete or different harness) |
| 3537e37f831e | **No** | — | — | Same as above |
| 7071c4ab92c2 | **No** | — | — | trace.jsonl + screenshots only; **no manifest** (run likely crashed before finalize) |
| 4272ee0431ea | Yes | DRAW_THE_PARIS_EIFFEL_TOWER_LANDSCAPE:_1 | success | clear_canvas, draw_eiffel_landscape, verify_success |

**Findings:** (1) Several recent runs are **universal agent** (agent.py) with task_id DRAW_4_CONCENTRIC_BLACK_TRIANGLES and a **capabilities** list in the manifest — this manifest shape was not explicitly described in the exhaustive project description. (2) **Runs without manifest** exist (070f6b51ff4a, 3537e37f831e, 7071c4ab92c2) — important for any tool that assumes “every run dir has manifest.json”. (3) **Ablation** creates a timestamped subdir that can be empty of trace/manifest because the harness discovers the latest run in the parent `runs/` directory after each rep. (4) **Kleki BMW** run has phase-level steps marked "failed" in steps_summary while outcome is "success" — task success is defined at the experiment level, not per-phase.

---

# Part II — Components and Artifacts Not Fully Documented

## 2.1 Ablation harness (`cre/ablation_harness.py`)

- **Purpose:** Run the concentric triangles task under four conditions (A: Bare VLM, B: Cache only, C: Cache + Trust, D: Full system) with configurable reps (default 5). Writes to `operator/cre/runs/ablation_<timestamp>/`: per-run logs (`<condition>_rep<n>.log`), **results.csv**, **summary.md**.
- **Mechanism:** Sets env vars (DISABLE_COORD_CACHE, DISABLE_TRUST_TRACKER, DISABLE_ADAPTIVE_ROUTING) per condition; invokes test_excalidraw_covt.py as subprocess; after each run, finds **latest** run dir in `cre/runs/` by manifest mtime and reads manifest + trace for outcome and metrics.
- **Trace metrics:** `_count_trace_events` scans trace.jsonl for `metadata.vlm_call`, `metadata.cache_hit`, `metadata.cache_miss`/`cache_stale`, `metadata.trust_skip`/`verification_skipped`, `metadata.routing_adaptation`. In the inspected traces, **trust skip** is recorded as `action_result.output = "trust-skipped"` and `evaluation.actual = "trust-skipped"`, not necessarily in a top-level `metadata` object — so ablation counts may undercount unless the test also writes those metadata fields. **Recommendation:** Confirm trace schema for ablation (add metadata block or document that counts use evaluation.actual).
- **Omission:** Not listed in PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md or ESSAY_PROJECT_OVERLAP_PHD.md. It is a **controlled-experiment layer** for isolating coord cache, trust tracker, and adaptive routing — directly relevant to the essay’s “Bayesian trust” and “process-level” evaluation.

## 2.2 Capability router (`capability_router.py`)

- **Purpose:** “Dynamic capability activation router for universal orchestration.” Answers “what does this task require?” and returns a set of **active capabilities**, each backed by a real module. Used by **agent.py** (universal) to wire capabilities instead of per-script wiring.
- **Concepts:** **CapabilityKind** enum (PERCEPTION_A11Y, PERCEPTION_SOM, PERCEPTION_FUSION, TRUST_TRACKER, COORD_CACHE, PHASH_GATE, SITE_KNOWLEDGE, CREDENTIAL_VAULT, STROKE_LOGGING, INFERENCE_ROUTING, EPISODIC_MEMORY, WEB_PRIMITIVES, DYNAMIC_PLANNING). **TaskRequirements** (needs_drawing, needs_login, needs_navigation, needs_form_fill, needs_color_selection, needs_file_upload, is_known_site, site_domain, goal_keywords). **classify_task(url, goal)** uses keyword heuristics first (FrugalGPT-style cascade). Each capability has probe/activate/deactivate; **imports are deferred** to activation time for graceful degradation.
- **Research basis (in code):** Magentic-One, DynaSaur (arXiv:2411.01747), AppAgent v2 (arXiv:2408.11824), Brooks (1986) subsumption architecture.
- **Omission:** Not in the tool inventory in PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md. The manifest’s **capabilities** list (e.g. in 38ccf14da0f3) is the serialized output of this router — it should be described as “capability_router-derived capability set recorded in manifest when using agent.py.”

## 2.3 Unified action space (`action_space.py`)

- **Purpose:** “Unified action space for the universal orchestrator.” Abstracts the flat ACTION_HANDLERS into a **typed, semantically rich** action space for the VLM planner and executor.
- **Concepts:** **ActionCategory** (PRIMITIVE, PERCEPTION, DRAWING, NAVIGATION, COMPOUND). **ActionSpec** (name, category, description, parameters, required_params, visual_assert, handler_key). **PRIMITIVE_ACTIONS** (click, type, key, scroll, wait), **PERCEPTION_ACTIONS** (screenshot, assert_visual, a11y_snapshot, refresh_perception), **DRAWING_ACTIONS** (draw_path, draw_shape, set_stroke_color), **NAVIGATION_ACTIONS** (go_to_url, go_back), **COMPOUND_ACTIONS** (clear_canvas, draw_concentric_triangles, draw_eiffel_tower, draw_eiffel_landscape, login_flow), **BMW_ACTIONS** (bmw_skeleton, bmw_details, bmw_shading, bmw_final — note: manifest step names in d07655943ebf use bmw_form_blocking, bmw_mechanical, bmw_lighting; handler keys may differ). **UnifiedActionSpace**: register(), get(), list_names(), to_planner_context(), to_planner_schema_list(), resolve_action() (VLM name → handler key).
- **Research basis (in code):** CogAgent (CVPR 2024), DynaSaur, WebVoyager, OSWorld, SeeAct.
- **Omission:** Not in the exhaustive project description. It is the **schema layer** for agent.py’s dynamic planning and ties directly to “modular skills” and “progressive context loading” (essay §1.4) — the planner receives action schemas from this space.

## 2.4 rules.jsonl

- **Status:** Not present under `operator/cre/runs/` in the checked paths. **RulesStore** (outer_loop.py) writes to `Path(journal_path).parent / "rules.jsonl"` — i.e. alongside reflection_journal.jsonl. So **rules.jsonl** is created when the outer loop first writes a rule; if no escalation/rule extraction has occurred, the file may not exist yet. **Recommendation:** Document that rules.jsonl is created on first rule write; absence is expected before any rule-extraction cycle.

## 2.5 Kleki BMW run artifacts

- **experiment_summary.md:** Human-readable summary of the iterative run (phases, durations, screenshot refs, evaluation metrics, constraint ceiling, “theoretical extrapolation”). Generated as part of the “Concentric Study experimental protocol.”
- **iteration_N.png**, **iteration_N_annotation.md:** Per-iteration screenshot and a structured annotation (technical objective, tool affordance analysis, iterative learning, cognitive-visual reasoning, constraint assessment, references). The annotation format is PhD-style (cites Axiomatic Design, Loomis, Gestalt, etc.). These were **not** listed in the data-artifact table in PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md. They are **task-type-specific** (Kleki BMW multi-phase runs).

## 2.6 ESCALATION.md (real example)

- **Run b7dcf9ee41f5:** Contains full Level 1 (run summary), Level 2 (failure window steps 3–5), Level 3 (failed step JSON), “Attempt History,” “Suggested Investigation,” “Architecture-Critical Files.” Confirms the progressive-disclosure and code-agent handoff design. **Task_id in manifest is empty** for this run — worth noting for parsers.

---

# Part III — Trace and Manifest Nuances

## 3.1 Trace: trust-skip representation

- **test_excalidraw_covt.py** (and recovery/action_handlers): When verification is skipped by the trust tracker, trace step has `action_result.output = "trust-skipped"` and `evaluation.actual = "trust-skipped"`. There is no mandatory top-level `metadata.trust_skip` or `metadata.verification_skipped` in the step JSON.
- **ablation_harness** `_count_trace_events` looks for `metadata.get("trust_skip")` or `metadata.get("verification_skipped")`. So **ablation’s trust_skips count may be 0** unless the test or recovery layer also writes those metadata fields. **Recommendation:** Either have the trace writer (or recovery) set a `metadata` block with `trust_skip: true` when a step is trust-skipped, or document that ablation should infer trust-skip from `evaluation.actual == "trust-skipped"`.

## 3.2 Manifest: agent_config variants

- **test_excalidraw_covt / test_kleki_bmw:** Typically `agent_config: { "mode": "enterprise", "model": "gemini-2.5-pro" }` (or similar).
- **agent.py (universal):** `agent_config: { "mode": "universal", "url": "https://excalidraw.com", "capabilities": [ "Accessibility Engine", "Set-of-Mark Overlay", … ] }`. The **capabilities** array is the capability_router’s active set and should be documented as part of the manifest schema.

## 3.3 Outcome values

- Observed in manifests: **"success"**, **"failure"**, **"error"**. “error” may indicate crash or unhandled exception before a clean failure classification.

---

# Part IV — Gaps vs. Previous Docs

| Item | PROJECT_PHD_EXHAUSTIVE_DESCRIPTION | ESSAY_PROJECT_OVERLAP_PHD | Status |
|------|-------------------------------------|----------------------------|--------|
| Ablation harness | Not listed | Not listed | **Added in this addendum** |
| Capability router | Not in tool table | Not mentioned | **Added in this addendum** |
| action_space.py / UnifiedActionSpace | Not in tool table | Not mentioned | **Added in this addendum** |
| Run types (universal vs covt vs Kleki vs Eiffel) | Only generic “entry points” | Not detailed | **Added in §1.2, §1.3** |
| Manifest capabilities list (agent.py) | Not described | — | **Added in §3.2** |
| Runs without manifest | Not discussed | — | **Added in §1.3** |
| Kleki experiment_summary, iteration_* | Not in artifact table | — | **Added in §2.5** |
| rules.jsonl creation / absence | Not stated | — | **Added in §2.4** |
| Trace metadata vs evaluation.actual for trust-skip | Not stated | — | **Added in §3.1** |
| Phase-level “failed” vs run-level “success” (Kleki) | Not stated | — | **Added in §1.2, §1.3** |

---

# Part V — Recommendations

1. **Project description:** Add **ablation_harness**, **capability_router**, and **action_space** to the “Tools and Components” section, with one-line roles and research basis. Add a short “Run types and manifest variants” subsection (covt vs universal vs Kleki vs Eiffel; capabilities list; runs without manifest).
2. **Data artifacts table:** Add **experiment_summary.md**, **iteration_N.png**, **iteration_N_annotation.md** (for Kleki BMW runs) and **results.csv** / **summary.md** (for ablation runs). Note that **rules.jsonl** may be absent until first rule write.
3. **Ablation:** Align trace schema with ablation counters: either emit `metadata.trust_skip` / `metadata.cache_hit` etc. in trace steps, or document and implement parsing from `evaluation.actual` and existing fields so summary.md and results.csv are accurate.
4. **Essay overlap:** The **capability router** (task-based activation of modules) and **unified action space** (typed action schema for planner and executor) align with the essay’s “modular, skill-equipped architectures” and “progressive context loading” — they could be explicitly tied to §1.4 in the overlap doc. The **ablation harness** supports rigorous evaluation of Bayesian trust and cost-control components (essay §5 and process/dense feedback).

This addendum is the PhD deep-dive supplement to the exhaustive project description and essay overlap analysis. Use it to update PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md and ESSAY_PROJECT_OVERLAP_PHD.md and to fix any tooling that assumes every run has a manifest or that trust-skip is only in metadata.
