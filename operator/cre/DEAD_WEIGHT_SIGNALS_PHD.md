# Dead Weight Signals (PhD)

## Method
These are signals, not delete instructions. A surface appears here only when live repo evidence suggests weak current justification.

## checked-in __pycache__ artifacts
- signal type: `cache_artifacts`
- confidence: `high`
- evidence:
  - `operator/__pycache__/a11y_engine.cpython-314.pyc`
  - `operator/__pycache__/action_space.cpython-314.pyc`
  - `operator/__pycache__/agent.cpython-314.pyc`
  - `operator/__pycache__/agent_core.cpython-314.pyc`
  - `operator/__pycache__/capability_router.cpython-314.pyc`
  - `operator/__pycache__/codex_client.cpython-314.pyc`
  - `operator/__pycache__/diagnostic_reader.cpython-314.pyc`
  - `operator/__pycache__/element_map.cpython-314.pyc`
  - `operator/__pycache__/healing_orchestrator.cpython-314.pyc`
  - `operator/__pycache__/inference_router.cpython-314.pyc`
  - `operator/__pycache__/screenshot_preprocessor.cpython-314.pyc`
  - `operator/__pycache__/skill_library.cpython-314.pyc`
  - `operator/__pycache__/test_router_dryrun.cpython-314-pytest-9.0.2.pyc`
  - `operator/__pycache__/test_router_dryrun.cpython-314.pyc`
  - `operator/__pycache__/trace_writer.cpython-314.pyc`
  - `operator/__pycache__/visual_engine.cpython-314.pyc`
  - `operator/__pycache__/vlm_coordinator.cpython-314.pyc`
  - `operator/__pycache__/web_primitives.cpython-314.pyc`
  - `operator/__pycache__/window_capture.cpython-314.pyc`
  - `operator/agent_infra/__pycache__/__init__.cpython-314.pyc`
- why not core: Bytecode caches are not source of truth.
- why not legacy: They are generated caches, not deliberate legacy surfaces.
- why not generated: They are generated, but not current evidence anchors.
- review recommendation: Remove from repo in a later cleanup branch; keep out of future audits by default.

## top-level report/summary memo sprawl
- signal type: `duplicate_documentation`
- confidence: `medium`
- evidence:
  - `operator/cre/COMPLETION_SUMMARY.md`
  - `operator/cre/EXECUTIVE_SUMMARY_VERIFICATION.md`
  - `operator/cre/FINAL_TEST_SUMMARY.md`
- why not core: These files are not primary runtime or governance surfaces.
- why not legacy: They are not required compatibility layers.
- why not generated: They are hand-written but weakly authoritative.
- review recommendation: Consolidate into canonical docs or downgrade to historical/supporting in a later branch.

## orphaned screenshots/demo artifacts
- signal type: `weak_artifact_linkage`
- confidence: `medium`
- evidence:
  - `operator/agent_infra/som_button_map.png`
  - `operator/agent_infra/som_kleki_brush.png`
  - `operator/agent_infra/som_kleki_opacity.png`
  - `operator/agent_infra/som_kleki_panel.png`
  - `operator/agent_infra/som_panel.png`
  - `operator/agent_infra/som_stroke.png`
  - `operator/cre/_bmw_center.png`
  - `operator/cre/_bmw_center2.png`
  - `operator/cre/_bmw_center3.png`
  - `operator/cre/_bmw_center4.png`
  - `operator/cre/_bmw_center5.png`
  - `operator/cre/_checkpoint_00_start.png`
  - `operator/cre/_checkpoint_01_sky.png`
  - `operator/cre/_checkpoint_01_sky_ground.png`
  - `operator/cre/_checkpoint_02_buildings.png`
  - `operator/cre/_checkpoint_02_ground.png`
  - `operator/cre/_checkpoint_03_buildings.png`
  - `operator/cre/_checkpoint_03_tower_upper.png`
  - `operator/cre/_checkpoint_04_tower_lattice.png`
  - `operator/cre/_checkpoint_05_tower_done.png`
- why not core: These artifacts are not part of the hot path.
- why not legacy: They are not established legacy compatibility surfaces.
- why not generated: Many are manually retained evidence artifacts, but weakly linked.
- review recommendation: Review artifact families and retain only those linked from canonical docs or active tests.

## one-off operational/demo scripts
- signal type: `weak_script_linkage`
- confidence: `medium`
- evidence:
  - `operator/cre/build_reference_board_artifact.py`
  - `operator/cre/jspaint_draw_polo_bear_panther_enhanced.py`
  - `operator/cre/jspaint_draw_tiger_rl_ironman.py`
  - `operator/cre/jspaint_draw_tiger_rl_ironman_v2.py`
  - `operator/cre/jspaint_draw_tiger_rl_ironman_v3.py`
  - `operator/cre/magma_draw_polo_bear_panther.py`
  - `operator/cre/magma_draw_tiger_rl_ironman.py`
  - `operator/cre/run_preclick_smoke.py`
- why not core: They are not on the universal-agent hot path.
- why not legacy: Some are not required for compatibility.
- why not generated: They are hand-written scripts, but lightly justified.
- review recommendation: Separate true lineage/legacy scripts from one-off demos before any cleanup.


