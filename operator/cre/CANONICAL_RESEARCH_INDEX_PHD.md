# Canonical Research Index (PhD)

## Context

- Top-level textual surface under `operator/cre`: `126` files.
- Markdown files in that surface: `121`.
- The current top-level directory mixes canonical architecture memos, supporting audits, case-study writeups, historical status reports, and local operational notes.
- Treating all of them as equally current creates documentation noise, source-of-truth drift, and weak onboarding.

## Decision

Use a curated index with explicit categories. Only `canonical_core` and `canonical_snapshot` documents belong in the default reading path.

## Core Reading Path

- `README.md`: Directory entrypoint and index handoff.
- `CANONICAL_RESEARCH_INDEX_PHD.md`: Curated map of the top-level research surface.
- `DOC_SURFACE_GOVERNANCE_PHD.md`: External-evidence justification for why the top-level doc surface is classified and reduced the way it is.
- `PHD_DECISION_PRACTICE.md`: Method rule for evidence-first decisions and research-first implementation.
- `PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md`: Single broad description of what the project is and how its major components fit.
- `CURRENT_ARCHITECTURE_SURFACE_PHD.md`: Snapshot of the live architecture and current test/runtime surface.
- `DEBUGGING_THIS_PROJECT_PHD.md`: Canonical debugging order for the current layered GUI-agent stack.
- `PROJECT_TOOLING_DEEP_AUDIT_PHD.md`: Current tool and dependency surface beyond package manifests alone.
- `MASTER_TOOL_LIST_PHD.md`: Definitive inventory of project tools and their status.
- `PROJECT_SCIENTIFIC_COHERENCE_AUDIT_PHD.md`: Evidence-level audit of what is implemented, analogical, or overstated.
- `PHASE_1_ENVIRONMENT_BENEFITS_PHD.md`: Why environment discipline is a first-order requirement for this repo.
- `HOST_TOOL_HEALTH_DISCOVERY_PHD.md`: Host-tool health layer rationale and substrate discovery basis.
- `MISSED_TOOL_WORKFLOW_VALUE_PHD.md`: Workflow-value ranking for tools and capability gaps.
- `PLACEMENT_RESEARCH.md`: Canonical example of facts-before-decision placement reasoning.
- `CURSOR_MCP_LANDSCAPE_PHD.md`: Current Cursor MCP landscape, prioritization, and internal MCP opportunities.
- `CURSOR_2_6_PROJECT_FIT_PHD.md`: Repo-specific Cursor 2.6 implementation strategy.
- `CURSOR_2_6_OPERATING_PROTOCOL_PHD.md`: Operational protocol for using Cursor in this repo without tool sprawl.
- `EXTERNAL_MCP_GOVERNANCE_PHD.md`: Explicit gate for external MCP rollout.
- `CONTEXT7_PILOT_PHD.md`: Current external MCP pilot design and decision rule.
- `CURSOR_CLOUD_AND_TEAM_SURFACES_PHD.md`: Deferred classification for account-gated Cursor surfaces.

## External Research Basis

This index is grounded in external architecture-documentation and repository-comprehension sources, not only local preference.

- Primary source register: `operator/cre/artifacts/cre_doc_surface_primary_sources.json`
- ISO/IEC/IEEE 42010: architecture descriptions organize concerns, viewpoints, correspondences, and rationale.
- SEI Views and Beyond: documentation should be organized around relevant stakeholder views, not a flat undifferentiated corpus.
- SEI documentation guidance: architecture must be understandable and packaged for stakeholders, or it cannot be analyzed effectively.
- CACM requirements tracing: cross-artifact traceability matters, which supports keeping a machine-readable registry.
- SEI README and recent repository summarization / reconstruction work: rebuildable repository summaries are valid generated aids, but they should be distinguished from canonical authored docs.

## Active Snapshot Docs

- `CANONICAL_RUNTIME_BASELINE_PHD.md`: Snapshot memo that is still useful, but date-sensitive.
- `CURSOR_ENVIRONMENT_MONITOR_PHD.md`: Snapshot memo that is still useful, but date-sensitive.
- `CURSOR_OFFICIAL_UPDATES_2026_PHD_RESEARCH.md`: Snapshot memo that is still useful, but date-sensitive.

## Supporting Research

- `DECOMPOSITION_HANDBOOK_PHD.md`
- `ACADEMIC_VALIDATION.md`
- `DEEP_DIVE_ADDENDUM.md`
- `ESSAY_PROJECT_OVERLAP_PHD.md`
- `CONCENTRIC_STUDY_PHD_TOOL_INTELLIGENCE.md`
- `PHD_CHAT_TOOL_USE_RESEARCH.md`
- `RECURSIVE_PHD_RESEARCH_LOOP.md`
- `TOOLS_USED_IN_CHAT_PHD_RESEARCH.md`
- `TOOL_CHEAT_SHEET_PHD.md`
- `ALLOWLIST_PREACTION_IMPLEMENTATION_OUTLINE.md`
- `ROADMAP_PHD_RESEARCH_MEMO.md`
- `CONTEXT_LOCKED_RESEARCH_FILTER_PHD.md`
- `ENVIRONMENT_JUSTIFICATION_GATE_PHD.md`
- `RUST_PARENT_ENVIRONMENT_SOPHISTICATION_AUDIT_PHD.md`
- `RUST_TRANSFER_PRIORITY_ROADMAP_PHD.md`
- `DEAD_WEIGHT_SIGNALS_PHD.md`
- `ENVIRONMENT_COMPLIANCE_REVIEW_PHD.md`
- `HIGH_VALUE_TOOL_ROLLOUT_PHD.md`
- `WHOLE_PROJECT_TRUTH_AUDIT_PHD.md`
- `DECISION_SUPPORT_TOOL_ADOPTION_PHD.md`
- `PAST_TOOL_AWARENESS_AUDIT_PHD.md`
- `TOOL_CONNECTIONS_DIAGRAM.md`
- `VISUAL_REASONING_ENHANCEMENT_PHD.md`
- `ANSWER_COMPLIANCE_AUDIT_PHD.md`
- `ARCHITECTURE_CONFORMANCE_DETERMINISM_PHD.md`
- `ARCHITECTURE_CONFORMANCE_NEXT_HARDENING_PHD.md`
- `BENCHMARK_STRATEGY_FOR_THIS_PROJECT_PHD.md`
- `ENVIRONMENT_COMPLIANCE_AUTOMATION_PHD.md`
- `FINAL_TOOL_COVERAGE_AUDIT_PHD.md`
- `WHAT_OTHERS_USE_TO_MASTER_VISUAL_BRANCH_PHD.md`
- `AUTOMATION_EXERCISE_SITE4_FULL_SWEEP_PHD.md`
- `EXPAND_TESTING_SITE3_FULL_SWEEP_PHD.md`
- `THE_INTERNET_SITE2_FULL_SWEEP_PHD.md`
- `UITESTING_PLAYGROUND_SITE5_FULL_SWEEP_PHD.md`
- `WEB_AUTH_AND_PROTON_PASS_GENERALIZATION_PHD.md`
- `WIKIPEDIA_SITE6_UNIVERSAL_AUTONOMY_PHD.md`
- `AI_JURY_API_KEYS.md`

## Case Studies

- `SUBJECT_LOOKUP_FOR_DRAWING.md`
- `FRESH_LIVE_ART_BENCHMARK_PHD.md`
- `JSPAINT_DRAW_FAILURE_FORENSICS_PHD.md`
- `MAGMA_LAST_RUN_RESEARCH.md`
- `REDDIT_AUTOMATION_FOUNDATION_PHD.md`
- `LAST_3_KLEKI_FIX_PROGRAM_PHD.md`
- `LAST_3_KLEKI_RUNS_LINE_BY_LINE_AUDIT_PHD.md`
- `MAGMA_REALISM_PRESETS.md`
- `MAGMA_TOOLS_PHD_RESEARCH.md`
- `REDDIT_PRODUCTIZATION_PLAN_PHD_REVALIDATED.md`
- `RESEARCH_AGENT_DESIGN.md`
- `COUSIN_VISUAL_REASONING_SHOWCASE.md`
- `IQ_TEST_PREPARATION_PROTOCOL_PHD.md`
- `KLEKI_RESET_AND_ART_BENCHMARK_PHD.md`
- `MAGMA_TRACED_INTEGRATION.md`
- `PRECLICK_CONFIRMATION_RESEARCH_PHD.md`
- `RECOVERY_CHECKPOINTS_PHD.md`
- `REDDIT_BRIAN_LIVE_DEMO.md`
- `REDDIT_PRODUCTIZATION_PLAN_PHD.md`

## Historical / Superseded Reports

These are useful for provenance, but they should not be cited as the current source of truth without checking the core docs first.

- `IQ_TEST_LIVE_RUN_LOG.md`: superseded by `CANONICAL_RESEARCH_INDEX_PHD.md`, `PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md`, `CURRENT_ARCHITECTURE_SURFACE_PHD.md`
- `ULTIMATE_TESTS.md`: superseded by `CANONICAL_RESEARCH_INDEX_PHD.md`, `PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md`, `CURRENT_ARCHITECTURE_SURFACE_PHD.md`
- `EXHAUSTIVE_CODE_RUN_REPORT.md`: superseded by `CANONICAL_RESEARCH_INDEX_PHD.md`, `PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md`, `CURRENT_ARCHITECTURE_SURFACE_PHD.md`
- `EXECUTION_STATUS.md`: superseded by `CANONICAL_RESEARCH_INDEX_PHD.md`, `PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md`, `CURRENT_ARCHITECTURE_SURFACE_PHD.md`
- `EXECUTION_SUMMARY.md`: superseded by `CANONICAL_RESEARCH_INDEX_PHD.md`, `PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md`, `CURRENT_ARCHITECTURE_SURFACE_PHD.md`
- `COMPLETION_SUMMARY.md`: superseded by `CANONICAL_RESEARCH_INDEX_PHD.md`, `PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md`, `CURRENT_ARCHITECTURE_SURFACE_PHD.md`
- `EXECUTIVE_SUMMARY_VERIFICATION.md`: superseded by `CANONICAL_RESEARCH_INDEX_PHD.md`, `PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md`, `CURRENT_ARCHITECTURE_SURFACE_PHD.md`
- `FINAL_TEST_SUMMARY.md`: superseded by `CANONICAL_RESEARCH_INDEX_PHD.md`, `PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md`, `CURRENT_ARCHITECTURE_SURFACE_PHD.md`
- `TEST_RESULTS.md`: superseded by `CANONICAL_RESEARCH_INDEX_PHD.md`, `PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md`, `CURRENT_ARCHITECTURE_SURFACE_PHD.md`
- `BRILLIANT_LIVE_TEST_LOG.md`: superseded by `CANONICAL_RESEARCH_INDEX_PHD.md`, `PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md`, `CURRENT_ARCHITECTURE_SURFACE_PHD.md`
- `EXECUTIVE_SUMMARY_PROJECT_TYPE_VERIFICATION.md`: superseded by `CANONICAL_RESEARCH_INDEX_PHD.md`, `PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md`, `CURRENT_ARCHITECTURE_SURFACE_PHD.md`
- `FINAL_REPORT.md`: superseded by `CANONICAL_RESEARCH_INDEX_PHD.md`, `PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md`, `CURRENT_ARCHITECTURE_SURFACE_PHD.md`
- `IMPLEMENTATION_SUMMARY.md`: superseded by `CANONICAL_RESEARCH_INDEX_PHD.md`, `PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md`, `CURRENT_ARCHITECTURE_SURFACE_PHD.md`
- `INITIALIZATION_REPORT.md`: superseded by `CANONICAL_RESEARCH_INDEX_PHD.md`, `PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md`, `CURRENT_ARCHITECTURE_SURFACE_PHD.md`
- `VLM_INTEGRATION_PLAN.md`: superseded by `CANONICAL_RESEARCH_INDEX_PHD.md`, `PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md`, `CURRENT_ARCHITECTURE_SURFACE_PHD.md`
- `COVT_IMPLEMENTATION.md`: superseded by `CANONICAL_RESEARCH_INDEX_PHD.md`, `PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md`, `CURRENT_ARCHITECTURE_SURFACE_PHD.md`
- `EXECUTION_ANALYSIS.md`: superseded by `CANONICAL_RESEARCH_INDEX_PHD.md`, `PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md`, `CURRENT_ARCHITECTURE_SURFACE_PHD.md`
- `EXHAUSTIVE_TEST_ANALYSIS.md`: superseded by `CANONICAL_RESEARCH_INDEX_PHD.md`, `PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md`, `CURRENT_ARCHITECTURE_SURFACE_PHD.md`
- `FINAL_IMPLEMENTATION_REPORT.md`: superseded by `CANONICAL_RESEARCH_INDEX_PHD.md`, `PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md`, `CURRENT_ARCHITECTURE_SURFACE_PHD.md`
- `IMPLEMENTATION_COMPLETE.md`: superseded by `CANONICAL_RESEARCH_INDEX_PHD.md`, `PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md`, `CURRENT_ARCHITECTURE_SURFACE_PHD.md`
- `ULTIMATE_TEST_COMPLETE.md`: superseded by `CANONICAL_RESEARCH_INDEX_PHD.md`, `PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md`, `CURRENT_ARCHITECTURE_SURFACE_PHD.md`
- `ULTIMATE_TEST_EXECUTION_LOG.md`: superseded by `CANONICAL_RESEARCH_INDEX_PHD.md`, `PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md`, `CURRENT_ARCHITECTURE_SURFACE_PHD.md`
- `ULTIMATE_TEST_RESULTS.md`: superseded by `CANONICAL_RESEARCH_INDEX_PHD.md`, `PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md`, `CURRENT_ARCHITECTURE_SURFACE_PHD.md`
- `ULTIMATE_TEST_SUCCESS.md`: superseded by `CANONICAL_RESEARCH_INDEX_PHD.md`, `PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md`, `CURRENT_ARCHITECTURE_SURFACE_PHD.md`
- `MODEL_BASED_PLANNING_SOLUTION.md`: superseded by `CANONICAL_RESEARCH_INDEX_PHD.md`, `PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md`, `CURRENT_ARCHITECTURE_SURFACE_PHD.md`
- `PHD_REMEDIATION_PLAN.md`: superseded by `CANONICAL_RESEARCH_INDEX_PHD.md`, `PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md`, `CURRENT_ARCHITECTURE_SURFACE_PHD.md`
- `COVT_EXECUTION_STATUS.md`: superseded by `CANONICAL_RESEARCH_INDEX_PHD.md`, `PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md`, `CURRENT_ARCHITECTURE_SURFACE_PHD.md`
- `EVIDENCE_DRIVEN_EXECUTION_SPEC.md`: superseded by `CANONICAL_RESEARCH_INDEX_PHD.md`, `PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md`, `CURRENT_ARCHITECTURE_SURFACE_PHD.md`
- `EXECUTION_LOG_REFERENCE.md`: superseded by `CANONICAL_RESEARCH_INDEX_PHD.md`, `PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md`, `CURRENT_ARCHITECTURE_SURFACE_PHD.md`
- `FIXES_APPLIED.md`: superseded by `CANONICAL_RESEARCH_INDEX_PHD.md`, `PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md`, `CURRENT_ARCHITECTURE_SURFACE_PHD.md`
- `HYBRID_COVT_VALIDATION.md`: superseded by `CANONICAL_RESEARCH_INDEX_PHD.md`, `PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md`, `CURRENT_ARCHITECTURE_SURFACE_PHD.md`
- `MODEL_UPDATE.md`: superseded by `CANONICAL_RESEARCH_INDEX_PHD.md`, `PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md`, `CURRENT_ARCHITECTURE_SURFACE_PHD.md`
- `PHASE_2_3_STATUS.md`: superseded by `CANONICAL_RESEARCH_INDEX_PHD.md`, `PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md`, `CURRENT_ARCHITECTURE_SURFACE_PHD.md`
- `PROBLEM_ANALYSIS.md`: superseded by `CANONICAL_RESEARCH_INDEX_PHD.md`, `PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md`, `CURRENT_ARCHITECTURE_SURFACE_PHD.md`
- `TEST_EXECUTION_COMPLETE.md`: superseded by `CANONICAL_RESEARCH_INDEX_PHD.md`, `PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md`, `CURRENT_ARCHITECTURE_SURFACE_PHD.md`

## Local Operational Notes And Logs

- `SHOWCASE.md` -> suggested target `operator/cre/local_ops/`
- `SLACK_OR_EMAIL.txt` -> suggested target `operator/cre/local_ops/`
- `requirements-study.txt` -> suggested target `operator/cre/local_ops/`
- `API_KEY_SETUP.md` -> suggested target `operator/cre/local_ops/`
- `DEMO_CHECKLIST.md` -> suggested target `operator/cre/local_ops/`
- `FOR_COLLEAGUE.md` -> suggested target `operator/cre/local_ops/`
- `execution_log.txt` -> suggested target `operator/cre/history/logs/`
- `magma_story.md` -> suggested target `operator/cre/history/logs/`
- `SETUP_LOG.md` -> suggested target `operator/cre/history/logs/`
- `concentric_triangles_clean_pass_log.txt` -> suggested target `operator/cre/history/logs/`
- `kleki_execution_log.txt` -> suggested target `operator/cre/history/logs/`
- `test_excalidraw_execution_log.md` -> suggested target `operator/cre/history/logs/`

## Category Counts

- `canonical_core`: `20`
- `canonical_snapshot`: `3`
- `supporting_research`: `37`
- `case_study`: `19`
- `historical_report`: `35`
- `local_operational`: `6`
- `local_log`: `6`

## Machine-Readable Registry

- `operator/cre/artifacts/cre_top_level_doc_registry.json`

## Regenerate

```bash
python3 operator/cre/tools/build_cre_doc_registry.py
```

## Appendix: Full Placement Classification

### `canonical_core`

- `PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md` | refs `229` | action `keep_top_level` | target `operator/cre/`
- `CANONICAL_RESEARCH_INDEX_PHD.md` | refs `96` | action `keep_top_level` | target `operator/cre/`
- `CURRENT_ARCHITECTURE_SURFACE_PHD.md` | refs `93` | action `keep_top_level` | target `operator/cre/`
- `README.md` | refs `81` | action `keep_top_level` | target `operator/cre/`
- `PHD_DECISION_PRACTICE.md` | refs `60` | action `keep_top_level` | target `operator/cre/`
- `MISSED_TOOL_WORKFLOW_VALUE_PHD.md` | refs `33` | action `keep_top_level` | target `operator/cre/`
- `MASTER_TOOL_LIST_PHD.md` | refs `32` | action `keep_top_level` | target `operator/cre/`
- `PHASE_1_ENVIRONMENT_BENEFITS_PHD.md` | refs `27` | action `keep_top_level` | target `operator/cre/`
- `CURSOR_MCP_LANDSCAPE_PHD.md` | refs `25` | action `keep_top_level` | target `operator/cre/`
- `DEBUGGING_THIS_PROJECT_PHD.md` | refs `19` | action `keep_top_level` | target `operator/cre/`
- `PLACEMENT_RESEARCH.md` | refs `18` | action `keep_top_level` | target `operator/cre/`
- `EXTERNAL_MCP_GOVERNANCE_PHD.md` | refs `16` | action `keep_top_level` | target `operator/cre/`
- `DOC_SURFACE_GOVERNANCE_PHD.md` | refs `15` | action `keep_top_level` | target `operator/cre/`
- `CURSOR_2_6_OPERATING_PROTOCOL_PHD.md` | refs `13` | action `keep_top_level` | target `operator/cre/`
- `CURSOR_2_6_PROJECT_FIT_PHD.md` | refs `13` | action `keep_top_level` | target `operator/cre/`
- `PROJECT_SCIENTIFIC_COHERENCE_AUDIT_PHD.md` | refs `13` | action `keep_top_level` | target `operator/cre/`
- `PROJECT_TOOLING_DEEP_AUDIT_PHD.md` | refs `12` | action `keep_top_level` | target `operator/cre/`
- `CONTEXT7_PILOT_PHD.md` | refs `11` | action `keep_top_level` | target `operator/cre/`
- `HOST_TOOL_HEALTH_DISCOVERY_PHD.md` | refs `11` | action `keep_top_level` | target `operator/cre/`
- `CURSOR_CLOUD_AND_TEAM_SURFACES_PHD.md` | refs `9` | action `keep_top_level` | target `operator/cre/`

### `canonical_snapshot`

- `CANONICAL_RUNTIME_BASELINE_PHD.md` | refs `8` | action `keep_top_level` | target `operator/cre/`
- `CURSOR_ENVIRONMENT_MONITOR_PHD.md` | refs `8` | action `keep_top_level` | target `operator/cre/`
- `CURSOR_OFFICIAL_UPDATES_2026_PHD_RESEARCH.md` | refs `8` | action `keep_top_level` | target `operator/cre/`

### `supporting_research`

- `DECOMPOSITION_HANDBOOK_PHD.md` | refs `24` | action `retain_but_deemphasize` | target `operator/cre/reference/`
- `ACADEMIC_VALIDATION.md` | refs `23` | action `retain_but_deemphasize` | target `operator/cre/reference/`
- `DEEP_DIVE_ADDENDUM.md` | refs `21` | action `retain_but_deemphasize` | target `operator/cre/reference/`
- `ESSAY_PROJECT_OVERLAP_PHD.md` | refs `21` | action `retain_but_deemphasize` | target `operator/cre/reference/`
- `CONCENTRIC_STUDY_PHD_TOOL_INTELLIGENCE.md` | refs `18` | action `retain_but_deemphasize` | target `operator/cre/reference/`
- `PHD_CHAT_TOOL_USE_RESEARCH.md` | refs `15` | action `retain_but_deemphasize` | target `operator/cre/reference/`
- `RECURSIVE_PHD_RESEARCH_LOOP.md` | refs `12` | action `retain_but_deemphasize` | target `operator/cre/reference/`
- `TOOLS_USED_IN_CHAT_PHD_RESEARCH.md` | refs `12` | action `retain_but_deemphasize` | target `operator/cre/reference/`
- `TOOL_CHEAT_SHEET_PHD.md` | refs `12` | action `retain_but_deemphasize` | target `operator/cre/reference/`
- `ALLOWLIST_PREACTION_IMPLEMENTATION_OUTLINE.md` | refs `11` | action `retain_but_deemphasize` | target `operator/cre/reference/`
- `ROADMAP_PHD_RESEARCH_MEMO.md` | refs `11` | action `retain_but_deemphasize` | target `operator/cre/reference/`
- `CONTEXT_LOCKED_RESEARCH_FILTER_PHD.md` | refs `10` | action `retain_but_deemphasize` | target `operator/cre/reference/`
- `ENVIRONMENT_JUSTIFICATION_GATE_PHD.md` | refs `10` | action `retain_but_deemphasize` | target `operator/cre/reference/`
- `RUST_PARENT_ENVIRONMENT_SOPHISTICATION_AUDIT_PHD.md` | refs `10` | action `retain_but_deemphasize` | target `operator/cre/reference/`
- `RUST_TRANSFER_PRIORITY_ROADMAP_PHD.md` | refs `10` | action `retain_but_deemphasize` | target `operator/cre/reference/`
- `DEAD_WEIGHT_SIGNALS_PHD.md` | refs `9` | action `retain_but_deemphasize` | target `operator/cre/reference/`
- `ENVIRONMENT_COMPLIANCE_REVIEW_PHD.md` | refs `9` | action `retain_but_deemphasize` | target `operator/cre/reference/`
- `HIGH_VALUE_TOOL_ROLLOUT_PHD.md` | refs `9` | action `retain_but_deemphasize` | target `operator/cre/reference/`
- `WHOLE_PROJECT_TRUTH_AUDIT_PHD.md` | refs `9` | action `retain_but_deemphasize` | target `operator/cre/reference/`
- `DECISION_SUPPORT_TOOL_ADOPTION_PHD.md` | refs `8` | action `retain_but_deemphasize` | target `operator/cre/reference/`
- `PAST_TOOL_AWARENESS_AUDIT_PHD.md` | refs `8` | action `retain_but_deemphasize` | target `operator/cre/reference/`
- `TOOL_CONNECTIONS_DIAGRAM.md` | refs `8` | action `retain_but_deemphasize` | target `operator/cre/reference/`
- `VISUAL_REASONING_ENHANCEMENT_PHD.md` | refs `8` | action `retain_but_deemphasize` | target `operator/cre/reference/`
- `ANSWER_COMPLIANCE_AUDIT_PHD.md` | refs `6` | action `retain_but_deemphasize` | target `operator/cre/reference/`
- `ARCHITECTURE_CONFORMANCE_DETERMINISM_PHD.md` | refs `6` | action `retain_but_deemphasize` | target `operator/cre/reference/`
- `ARCHITECTURE_CONFORMANCE_NEXT_HARDENING_PHD.md` | refs `6` | action `retain_but_deemphasize` | target `operator/cre/reference/`
- `BENCHMARK_STRATEGY_FOR_THIS_PROJECT_PHD.md` | refs `6` | action `retain_but_deemphasize` | target `operator/cre/reference/`
- `ENVIRONMENT_COMPLIANCE_AUTOMATION_PHD.md` | refs `6` | action `retain_but_deemphasize` | target `operator/cre/reference/`
- `FINAL_TOOL_COVERAGE_AUDIT_PHD.md` | refs `6` | action `retain_but_deemphasize` | target `operator/cre/reference/`
- `WHAT_OTHERS_USE_TO_MASTER_VISUAL_BRANCH_PHD.md` | refs `6` | action `retain_but_deemphasize` | target `operator/cre/reference/`
- `AUTOMATION_EXERCISE_SITE4_FULL_SWEEP_PHD.md` | refs `5` | action `retain_but_deemphasize` | target `operator/cre/reference/`
- `EXPAND_TESTING_SITE3_FULL_SWEEP_PHD.md` | refs `5` | action `retain_but_deemphasize` | target `operator/cre/reference/`
- `THE_INTERNET_SITE2_FULL_SWEEP_PHD.md` | refs `5` | action `retain_but_deemphasize` | target `operator/cre/reference/`
- `UITESTING_PLAYGROUND_SITE5_FULL_SWEEP_PHD.md` | refs `5` | action `retain_but_deemphasize` | target `operator/cre/reference/`
- `WEB_AUTH_AND_PROTON_PASS_GENERALIZATION_PHD.md` | refs `5` | action `retain_but_deemphasize` | target `operator/cre/reference/`
- `WIKIPEDIA_SITE6_UNIVERSAL_AUTONOMY_PHD.md` | refs `5` | action `retain_but_deemphasize` | target `operator/cre/reference/`
- `AI_JURY_API_KEYS.md` | refs `0` | action `retain_but_deemphasize` | target `operator/cre/reference/`

### `case_study`

- `SUBJECT_LOOKUP_FOR_DRAWING.md` | refs `11` | action `move_to_case_studies` | target `operator/cre/case_studies/`
- `FRESH_LIVE_ART_BENCHMARK_PHD.md` | refs `10` | action `move_to_case_studies` | target `operator/cre/case_studies/`
- `JSPAINT_DRAW_FAILURE_FORENSICS_PHD.md` | refs `10` | action `move_to_case_studies` | target `operator/cre/case_studies/`
- `MAGMA_LAST_RUN_RESEARCH.md` | refs `10` | action `move_to_case_studies` | target `operator/cre/case_studies/`
- `REDDIT_AUTOMATION_FOUNDATION_PHD.md` | refs `8` | action `move_to_case_studies` | target `operator/cre/case_studies/`
- `LAST_3_KLEKI_FIX_PROGRAM_PHD.md` | refs `7` | action `move_to_case_studies` | target `operator/cre/case_studies/`
- `LAST_3_KLEKI_RUNS_LINE_BY_LINE_AUDIT_PHD.md` | refs `7` | action `move_to_case_studies` | target `operator/cre/case_studies/`
- `MAGMA_REALISM_PRESETS.md` | refs `7` | action `move_to_case_studies` | target `operator/cre/case_studies/`
- `MAGMA_TOOLS_PHD_RESEARCH.md` | refs `7` | action `move_to_case_studies` | target `operator/cre/case_studies/`
- `REDDIT_PRODUCTIZATION_PLAN_PHD_REVALIDATED.md` | refs `7` | action `move_to_case_studies` | target `operator/cre/case_studies/`
- `RESEARCH_AGENT_DESIGN.md` | refs `7` | action `move_to_case_studies` | target `operator/cre/case_studies/`
- `COUSIN_VISUAL_REASONING_SHOWCASE.md` | refs `6` | action `move_to_case_studies` | target `operator/cre/case_studies/`
- `IQ_TEST_PREPARATION_PROTOCOL_PHD.md` | refs `6` | action `move_to_case_studies` | target `operator/cre/case_studies/`
- `KLEKI_RESET_AND_ART_BENCHMARK_PHD.md` | refs `6` | action `move_to_case_studies` | target `operator/cre/case_studies/`
- `MAGMA_TRACED_INTEGRATION.md` | refs `6` | action `move_to_case_studies` | target `operator/cre/case_studies/`
- `PRECLICK_CONFIRMATION_RESEARCH_PHD.md` | refs `6` | action `move_to_case_studies` | target `operator/cre/case_studies/`
- `RECOVERY_CHECKPOINTS_PHD.md` | refs `6` | action `move_to_case_studies` | target `operator/cre/case_studies/`
- `REDDIT_BRIAN_LIVE_DEMO.md` | refs `6` | action `move_to_case_studies` | target `operator/cre/case_studies/`
- `REDDIT_PRODUCTIZATION_PLAN_PHD.md` | refs `6` | action `move_to_case_studies` | target `operator/cre/case_studies/`

### `historical_report`

- `IQ_TEST_LIVE_RUN_LOG.md` | refs `36` | action `move_to_archive` | target `operator/cre/history/`
- `ULTIMATE_TESTS.md` | refs `16` | action `move_to_archive` | target `operator/cre/history/`
- `EXHAUSTIVE_CODE_RUN_REPORT.md` | refs `15` | action `move_to_archive` | target `operator/cre/history/`
- `EXECUTION_STATUS.md` | refs `13` | action `move_to_archive` | target `operator/cre/history/`
- `EXECUTION_SUMMARY.md` | refs `13` | action `move_to_archive` | target `operator/cre/history/`
- `COMPLETION_SUMMARY.md` | refs `12` | action `move_to_archive` | target `operator/cre/history/`
- `EXECUTIVE_SUMMARY_VERIFICATION.md` | refs `12` | action `move_to_archive` | target `operator/cre/history/`
- `FINAL_TEST_SUMMARY.md` | refs `12` | action `move_to_archive` | target `operator/cre/history/`
- `TEST_RESULTS.md` | refs `12` | action `move_to_archive` | target `operator/cre/history/`
- `BRILLIANT_LIVE_TEST_LOG.md` | refs `10` | action `move_to_archive` | target `operator/cre/history/`
- `EXECUTIVE_SUMMARY_PROJECT_TYPE_VERIFICATION.md` | refs `9` | action `move_to_archive` | target `operator/cre/history/`
- `FINAL_REPORT.md` | refs `9` | action `move_to_archive` | target `operator/cre/history/`
- `IMPLEMENTATION_SUMMARY.md` | refs `9` | action `move_to_archive` | target `operator/cre/history/`
- `INITIALIZATION_REPORT.md` | refs `9` | action `move_to_archive` | target `operator/cre/history/`
- `VLM_INTEGRATION_PLAN.md` | refs `9` | action `move_to_archive` | target `operator/cre/history/`
- `COVT_IMPLEMENTATION.md` | refs `8` | action `move_to_archive` | target `operator/cre/history/`
- `EXECUTION_ANALYSIS.md` | refs `8` | action `move_to_archive` | target `operator/cre/history/`
- `EXHAUSTIVE_TEST_ANALYSIS.md` | refs `8` | action `move_to_archive` | target `operator/cre/history/`
- `FINAL_IMPLEMENTATION_REPORT.md` | refs `8` | action `move_to_archive` | target `operator/cre/history/`
- `IMPLEMENTATION_COMPLETE.md` | refs `8` | action `move_to_archive` | target `operator/cre/history/`
- `ULTIMATE_TEST_COMPLETE.md` | refs `8` | action `move_to_archive` | target `operator/cre/history/`
- `ULTIMATE_TEST_EXECUTION_LOG.md` | refs `8` | action `move_to_archive` | target `operator/cre/history/`
- `ULTIMATE_TEST_RESULTS.md` | refs `8` | action `move_to_archive` | target `operator/cre/history/`
- `ULTIMATE_TEST_SUCCESS.md` | refs `8` | action `move_to_archive` | target `operator/cre/history/`
- `MODEL_BASED_PLANNING_SOLUTION.md` | refs `7` | action `move_to_archive` | target `operator/cre/history/`
- `PHD_REMEDIATION_PLAN.md` | refs `7` | action `move_to_archive` | target `operator/cre/history/`
- `COVT_EXECUTION_STATUS.md` | refs `6` | action `move_to_archive` | target `operator/cre/history/`
- `EVIDENCE_DRIVEN_EXECUTION_SPEC.md` | refs `6` | action `move_to_archive` | target `operator/cre/history/`
- `EXECUTION_LOG_REFERENCE.md` | refs `6` | action `move_to_archive` | target `operator/cre/history/`
- `FIXES_APPLIED.md` | refs `6` | action `move_to_archive` | target `operator/cre/history/`
- `HYBRID_COVT_VALIDATION.md` | refs `6` | action `move_to_archive` | target `operator/cre/history/`
- `MODEL_UPDATE.md` | refs `6` | action `move_to_archive` | target `operator/cre/history/`
- `PHASE_2_3_STATUS.md` | refs `6` | action `move_to_archive` | target `operator/cre/history/`
- `PROBLEM_ANALYSIS.md` | refs `6` | action `move_to_archive` | target `operator/cre/history/`
- `TEST_EXECUTION_COMPLETE.md` | refs `6` | action `move_to_archive` | target `operator/cre/history/`

### `local_operational`

- `SHOWCASE.md` | refs `18` | action `move_to_local_ops` | target `operator/cre/local_ops/`
- `SLACK_OR_EMAIL.txt` | refs `8` | action `move_to_local_ops` | target `operator/cre/local_ops/`
- `requirements-study.txt` | refs `7` | action `move_to_local_ops` | target `operator/cre/local_ops/`
- `API_KEY_SETUP.md` | refs `6` | action `move_to_local_ops` | target `operator/cre/local_ops/`
- `DEMO_CHECKLIST.md` | refs `6` | action `move_to_local_ops` | target `operator/cre/local_ops/`
- `FOR_COLLEAGUE.md` | refs `6` | action `move_to_local_ops` | target `operator/cre/local_ops/`

### `local_log`

- `execution_log.txt` | refs `34` | action `move_to_logs` | target `operator/cre/history/logs/`
- `magma_story.md` | refs `13` | action `move_to_logs` | target `operator/cre/history/logs/`
- `SETUP_LOG.md` | refs `11` | action `move_to_logs` | target `operator/cre/history/logs/`
- `concentric_triangles_clean_pass_log.txt` | refs `10` | action `move_to_logs` | target `operator/cre/history/logs/`
- `kleki_execution_log.txt` | refs `7` | action `move_to_logs` | target `operator/cre/history/logs/`
- `test_excalidraw_execution_log.md` | refs `6` | action `move_to_logs` | target `operator/cre/history/logs/`
