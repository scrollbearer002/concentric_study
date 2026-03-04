# Whole Project Truth Audit (PhD)

## Environment basis
- repo root: `/Users/christianpardo/Desktop/concentric_study`
- filesystem-based truth audit: no git checkout at this path
- scope excludes `operator/venv/` and `operator/cre/runs/`

## Executive summary
This audit classifies the live repo into current, optional, legacy, experimental, generated, historical-reference, and stale-candidate surfaces using live code, test, and documentation evidence.

## Baseline
- full test baseline: `193 passed, 3 skipped, 5 warnings in 22.30s`
- architecture conformance baseline captured from `--check`
- host-tool health baseline captured from `agent_infra.host_tool_health`

## Inventory counts
- `artifact`: `612`
- `doc`: `129`
- `generated`: `62`
- `test`: `42`
- `script`: `37`
- `runtime_code`: `35`
- `legacy_runtime`: `7`
- `fixture`: `2`

## Status counts
- `stale_candidate`: `510`
- `experimental`: `171`
- `current`: `107`
- `generated`: `67`
- `historical_reference`: `55`
- `legacy`: `16`

## Low-value generated noise outside the inventory
- checked-in cache artifacts: `132`

## High-authority docs
- `AGENTS.md` — topic `misc`
- `DUAL_AGENT_LOOP_PLAN.md` — topic `misc`
- `operator/cre/MASTER_TOOL_LIST_PHD.md` — topic `tooling`
- `operator/cre/PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md` — topic `misc`
- `operator/cre/TOOL_CHEAT_SHEET_PHD.md` — topic `tooling`
- `operator/cre/project_understanding/README.md` — topic `project_understanding`

## Current core findings
- The universal-agent path and `agent_infra` shared infrastructure are the canonical current runtime.
- Root-level shim modules remain compatibility surfaces, not canonical implementations.
- `operator/codex_client.py`, `operator/vlm_coordinator.py`, and kernel-era scripts remain legacy, not current hot path.
- `operator/cre/project_understanding/` is current and generated-supporting, not dead weight by default.
- The largest dead-weight risk surface is memo/demo/artifact density under `operator/cre/`, especially screenshots, one-off reports, checked-in caches, and weakly linked demo scripts.

## Stale-candidate highlights
- `operator/agent_infra/som_button_map.png` — Artifact or screenshot with weak current linkage.
- `operator/agent_infra/som_kleki_brush.png` — Artifact or screenshot with weak current linkage.
- `operator/agent_infra/som_kleki_opacity.png` — Artifact or screenshot with weak current linkage.
- `operator/agent_infra/som_kleki_panel.png` — Artifact or screenshot with weak current linkage.
- `operator/agent_infra/som_panel.png` — Artifact or screenshot with weak current linkage.
- `operator/agent_infra/som_stroke.png` — Artifact or screenshot with weak current linkage.
- `operator/cre/COMPLETION_SUMMARY.md` — Summary/report style doc with weak authority and weak linkage.
- `operator/cre/EXECUTIVE_SUMMARY_VERIFICATION.md` — Summary/report style doc with weak authority and weak linkage.
- `operator/cre/FINAL_TEST_SUMMARY.md` — Summary/report style doc with weak authority and weak linkage.
- `operator/cre/_bmw_center.png` — Artifact or screenshot with weak current linkage.
- `operator/cre/_bmw_center2.png` — Artifact or screenshot with weak current linkage.
- `operator/cre/_bmw_center3.png` — Artifact or screenshot with weak current linkage.
- `operator/cre/_bmw_center4.png` — Artifact or screenshot with weak current linkage.
- `operator/cre/_bmw_center5.png` — Artifact or screenshot with weak current linkage.
- `operator/cre/_checkpoint_00_start.png` — Artifact or screenshot with weak current linkage.
- `operator/cre/_checkpoint_01_sky.png` — Artifact or screenshot with weak current linkage.
- `operator/cre/_checkpoint_01_sky_ground.png` — Artifact or screenshot with weak current linkage.
- `operator/cre/_checkpoint_02_buildings.png` — Artifact or screenshot with weak current linkage.
- `operator/cre/_checkpoint_02_ground.png` — Artifact or screenshot with weak current linkage.
- `operator/cre/_checkpoint_03_buildings.png` — Artifact or screenshot with weak current linkage.
- `operator/cre/_checkpoint_03_tower_upper.png` — Artifact or screenshot with weak current linkage.
- `operator/cre/_checkpoint_04_tower_lattice.png` — Artifact or screenshot with weak current linkage.
- `operator/cre/_checkpoint_05_tower_done.png` — Artifact or screenshot with weak current linkage.
- `operator/cre/_checkpoint_06_final.png` — Artifact or screenshot with weak current linkage.
- `operator/cre/_checkpoint_06_trees.png` — Artifact or screenshot with weak current linkage.
- `operator/cre/_checkpoint_auto_10.png` — Artifact or screenshot with weak current linkage.
- `operator/cre/_checkpoint_auto_20.png` — Artifact or screenshot with weak current linkage.
- `operator/cre/_checkpoint_auto_30.png` — Artifact or screenshot with weak current linkage.
- `operator/cre/_checkpoint_auto_40.png` — Artifact or screenshot with weak current linkage.
- `operator/cre/_checkpoint_auto_50.png` — Artifact or screenshot with weak current linkage.
- `operator/cre/_checkpoint_auto_60.png` — Artifact or screenshot with weak current linkage.
- `operator/cre/_checkpoint_auto_70.png` — Artifact or screenshot with weak current linkage.
- `operator/cre/_checkpoint_bmw1_00_start.png` — Artifact or screenshot with weak current linkage.
- `operator/cre/_checkpoint_bmw1_10.png` — Artifact or screenshot with weak current linkage.
- `operator/cre/_checkpoint_bmw1_final.png` — Artifact or screenshot with weak current linkage.
- `operator/cre/_checkpoint_bmw2_00_start.png` — Artifact or screenshot with weak current linkage.
- `operator/cre/_checkpoint_bmw2_12.png` — Artifact or screenshot with weak current linkage.
- `operator/cre/_checkpoint_bmw2_24.png` — Artifact or screenshot with weak current linkage.
- `operator/cre/_checkpoint_bmw2_36.png` — Artifact or screenshot with weak current linkage.
- `operator/cre/_checkpoint_bmw2_48.png` — Artifact or screenshot with weak current linkage.

## Legacy surfaces still justified
- `operator/codex_client.py` — Legacy runtime/tooling retained for compatibility or lineage.
- `operator/cre/codex_kernel.lua` — Legacy runtime/tooling retained for compatibility or lineage.
- `operator/cre/run_agent.sh` — Legacy runtime/tooling retained for compatibility or lineage.
- `operator/cre/run_ultimate_tests.sh` — Legacy runtime/tooling retained for compatibility or lineage.
- `operator/cre/showcase.sh` — Legacy runtime/tooling retained for compatibility or lineage.
- `operator/cre/test_drag_drop.py` — Covers older/compatibility runtime surfaces.
- `operator/cre/test_excalidraw_autonomous.py` — Covers older/compatibility runtime surfaces.
- `operator/cre/test_excalidraw_covt.py` — Covers older/compatibility runtime surfaces.
- `operator/cre/test_smooth_movement.py` — Covers older/compatibility runtime surfaces.
- `operator/cre/verify_kernel.sh` — Legacy runtime/tooling retained for compatibility or lineage.
- `operator/diagnostic_reader.py` — Compatibility shim over canonical agent_infra implementation.
- `operator/healing_orchestrator.py` — Compatibility shim over canonical agent_infra implementation.
- `operator/outer_loop.py` — Compatibility shim over canonical agent_infra implementation.
- `operator/skill_library.py` — Compatibility shim over canonical agent_infra implementation.
- `operator/trace_writer.py` — Compatibility shim over canonical agent_infra implementation.
- `operator/vlm_coordinator.py` — Legacy runtime/tooling retained for compatibility or lineage.

## Next cleanup branch should use
- `whole_project_truth_inventory.json`
- `module_truth_matrix.csv`
- `doc_truth_matrix.csv`
- `dead_weight_signals.json`
as the decision base before any deletion or archival.

