# Evidence And Run Artifacts

## Why This Matters

A large fraction of the repo is evidence, not executable logic. To understand the
project correctly, you need to distinguish:
- canonical code
- persistent state
- run outputs
- curated research documentation
- screenshots and verification artifacts

Without that separation, the size of `operator/cre/` is misleading.

## Canonical Run Directory Shape

Typical per-run directory under `operator/cre/runs/<run_id>/`:
- `trace.jsonl`: append-only structured step log
- `manifest.json`: final run summary written at finalize time
- `ESCALATION.md`: present only when the outer loop escalates

Global cross-run files in `operator/cre/runs/`:
- `reflection_journal.jsonl`
- `rules.jsonl` when rules have been extracted
- aggregate reports such as `LAST_20_RUNS_EXHAUSTIVE.md`

## Important Nuances

- Some run directories can exist without `manifest.json`.
  This usually means the run crashed or did not finalize cleanly.
- The absence of `rules.jsonl` is not necessarily a bug.
  It may simply mean no rules have been extracted yet.
- Different harnesses produce different artifact families.
  Excalidraw, universal-agent, Kleki, and ablation runs are not identical.

## Evidence Families In `operator/cre/`

### Diagnostic screenshots
Pattern examples:
- `diag_fail_*`
- `diag_final_fail_*`
- `diag_postcond_*`
- `diag_sanity_*`

Meaning:
- captured by recovery and diagnosis flows
- show what blocked progress, what the recovery step saw, and whether the obstruction cleared

### Verification screenshots
Pattern examples:
- `assert_after_*`
- `effect_verify_*`
- `verify_*.png`
- `color_verify_*.png`

Meaning:
- record the post-action or post-step state used to confirm correctness
- support trust-skip analysis and visual debugging

### Checkpoints and iterative outputs
Pattern examples:
- `_checkpoint_*`
- `_final_result*.png`
- `iteration_*.png`
- `iteration_*_annotation.md`

Meaning:
- intermediate or final outputs from long-running artistic tasks
- especially important for Kleki BMW and landscape-style experiments

### Grounding and reference images
Pattern examples:
- `som_*.png`
- `_kleki_*.png`
- `_panel_click.png`
- `current_state_buttonmap.png`

Meaning:
- static or semi-static visual aids used for Set-of-Mark, panel selection,
  or affordance debugging

## State Files That Influence Future Runs

- `operator/cre/skill_library.json`
- `operator/cre/action_trust.json`
- `operator/cre/routing_state.json`
- `operator/cre/runs/reflection_journal.jsonl`
- `operator/cre/runs/rules.jsonl`

These are not passive logs. They change later behavior.

## How To Read Old Evidence Efficiently

1. Start with the run manifest if it exists.
2. Read `trace.jsonl` or a synthesized report such as `LAST_20_RUNS_EXHAUSTIVE.md`.
3. Only then inspect diagnostic screenshots for the failing step.
4. If the task is iterative art generation, inspect checkpoints in order.
5. Use `artifacts/file_catalog.csv` to see whether a file is evidence, state,
   code, or documentation before drawing conclusions from it.
