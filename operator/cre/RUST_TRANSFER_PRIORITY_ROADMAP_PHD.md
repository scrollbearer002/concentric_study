# Rust-to-Concentric Transfer Priority Roadmap (PhD)

## Executive Summary
This roadmap ranks which sophistication layers from `~/rust` should be transferred into `concentric_study`, which should wait, and which should remain in the parent project.

The governing judgment is:
- `concentric_study` is already stronger in the core agent loop.
- `~/rust` is still stronger in selected operator-discipline layers.
- The highest-value transfers are the ones that make the environment model more explicit, exploration safer, and recovery more state-theoretic.

## Source Basis
Primary parent evidence:
- `~/rust/operator/tool_catalog.yaml`
- `~/rust/operator/tool_status.py`
- `~/rust/operator/health_contract.yaml`
- `~/rust/operator/cursor_action_inventory.yaml`
- `~/rust/operator/learn_explore.py`
- `~/rust/operator/explore_analyze.py`
- `~/rust/CANONICAL_OPERATOR_STATE.md`
- `~/rust/cursor-nav/verify_nav_baseline.sh`
- `~/rust/operator/reset_cursor_baseline.sh`
- `~/rust/capabilities/registry.json`
- `~/rust/capabilities/REGISTRY.md`
- `~/rust/operator/report_claims_guard.py`
- `~/rust/operator/report_snapshot_sync.py`
- `~/rust/operator/mac_core_agent/README.md`
- `~/rust/operator/mac_core_agent/verify.sh`

Current `concentric_study` overlap checked against:
- `operator/capability_router.py`
- `operator/agent_infra/site_knowledge.py`
- `operator/agent_infra/skill_library.py`
- `operator/agent_infra/verification_gate.py`
- `operator/agent_infra/visual_monitor.py`
- `operator/cre/RUST_PARENT_ENVIRONMENT_SOPHISTICATION_AUDIT_PHD.md`
- `operator/cre/artifacts/rust_parent_sophistication_candidates.json`

## Ranking Method
Each candidate is ranked by four criteria:
1. direct improvement to current runtime discipline
2. implementation leverage relative to blast radius
3. compatibility with `concentric_study`'s current architecture
4. whether the mechanism fills a real present gap rather than duplicating an already stronger subsystem

## Port First

### 1. Host-tool health discovery and backend selection
Parent evidence:
- `~/rust/operator/tool_catalog.yaml`
- `~/rust/operator/tool_status.py`

Why first:
- This fills a real preflight gap in `concentric_study`.
- It improves startup diagnostics before any task begins.
- It has low conceptual risk because it sits outside the core agent loop.

What it contributes:
- explicit tool classes
- concrete backend checks
- preferred provider selection
- fail-closed missing-capability detection

Why it matters now:
- `operator/capability_router.py` activates logical capabilities, but it does not prove the host substrate is healthy enough to deliver them.
- This would make environment readiness explicit instead of implicit.

Implementation shape in `concentric_study`:
- add a runtime host-tool catalog
- add a host-tool status checker
- add required-class gating at startup and before live demos

Expected benefit:
- fewer hidden environment failures
- better degraded-mode explanations
- more professional environment reporting

Migration risk:
- low

### 2. Bounded curiosity with explicit action inventories
Parent evidence:
- `~/rust/operator/health_contract.yaml`
- `~/rust/operator/cursor_action_inventory.yaml`
- `~/rust/operator/learn_explore.py`
- `~/rust/operator/explore_analyze.py`

Why first:
- This is the strongest sophistication gain for autonomous discovery.
- It complements `SiteKnowledge` and `ExplorationLoop` rather than replacing them.
- It directly upgrades safe learning on unfamiliar sites.

What it contributes:
- explicit action records with prerequisites, expected outcomes, and undo paths
- hard exploration budgets
- mastery thresholds
- frontier analysis for next safe actions

Why it matters now:
- `concentric_study` already explores sites, but its exploration layer is more qualitative than contract-driven.
- The parent model is better at turning exploration into bounded experiments.

Implementation shape in `concentric_study`:
- add site-generic exploration contracts
- add action frontier analysis
- separate exploratory actions from production-trusted actions

Expected benefit:
- safer autonomy on new sites
- clearer promotion path from observed affordance to reusable action
- less random drift during exploration

Migration risk:
- medium
- must stay site-generic, not Cursor-specific

### 3. Canonical runtime baseline and reset doctrine
Parent evidence:
- `~/rust/CANONICAL_OPERATOR_STATE.md`
- `~/rust/cursor-nav/verify_nav_baseline.sh`
- `~/rust/operator/reset_cursor_baseline.sh`

Why first:
- A serious agent needs a named recovery target.
- `concentric_study` has many local resets, but no single whole-system baseline doctrine.
- This will improve consistency across startup, recovery, and demo execution.

What it contributes:
- one named baseline state
- one canonical verification path
- one canonical reset path
- behavioral invariant checking, not only static state assumptions

Why it matters now:
- current reset logic is spread across site-specific handlers and local startup routines.
- this makes recovery more state-theoretic and less ad hoc.

Implementation shape in `concentric_study`:
- create `CANONICAL_RUNTIME_BASELINE.md`
- split the baseline into:
  - global runtime baseline
  - task-surface baseline
- add machine-verifiable baseline preflight
- add canonical reset entrypoints for both layers

Expected benefit:
- more deterministic preflight
- cleaner failure taxonomy for environment drift
- better live demo reliability

Migration risk:
- medium
- baseline must be defined at the right abstraction level so it does not overfit one site

## Port Later

### 4. Operational capability registry
Parent evidence:
- `~/rust/capabilities/registry.json`
- `~/rust/capabilities/REGISTRY.md`

Why later:
- It is valuable, but the system already has `SkillLibrary` and strong documentation.
- The first-wave items above improve runtime behavior more directly.

What it contributes:
- environment-level proven powers
- recheck commands
- evidence paths
- last-verified timestamps

What gap it fills:
- `SkillLibrary` tracks task skills, not system-level operational powers.

Expected benefit:
- clearer demos
- stronger self-audit
- cleaner operator trust model

Migration risk:
- low

### 5. Documentation claims drift guards
Parent evidence:
- `~/rust/operator/report_claims_guard.py`
- `~/rust/operator/report_snapshot_sync.py`

Why later:
- This strengthens repo integrity, but it does not directly improve runtime behavior.
- It becomes more valuable as flagship docs stabilize.

What it contributes:
- report snapshot sync
- required claim checks
- count drift detection
- narrative-doc gating

What gap it fills:
- `concentric_study` has many high-value docs but no general prose-drift guard.

Expected benefit:
- stronger documentation credibility
- less divergence between markdown narratives and generated artifacts

Migration risk:
- low

### 6. Attested run packs
Parent evidence:
- `~/rust/operator/mac_core_agent/README.md`
- `~/rust/operator/mac_core_agent/verify.sh`

Why later:
- `concentric_study` already has rich trace artifacts.
- An attested bundle layer is useful for demos, audits, or customer handoff, but it is not the highest immediate sophistication gain.

What it contributes:
- fixed run-pack structure
- hash attestation
- schema validation
- portable evidence bundles

What gap it fills:
- current run evidence is rich but spread across directories rather than packaged as one attested proof object.

Expected benefit:
- cleaner review packets
- easier external audit
- stronger customer-facing evidence packaging

Migration risk:
- medium
- should be added as export/packaging, not as a replacement for current trace storage

### 7. Metaphor guard / informal-language policy interpreter
Parent evidence:
- `~/rust/operator/metaphor_guard.sh`
- `~/rust/METAPHOR_TO_RULES.md`

Why later:
- It is useful, but it is not as foundational as environment health, bounded exploration, or baseline doctrine.
- It should be considered only after first-wave discipline layers are in place.

What it contributes:
- a way to map informal operator language into enforceable execution rules

Expected benefit:
- fewer ambiguous operator instructions
- clearer execution policy boundaries

Migration risk:
- medium
- risk of overfitting operator language conventions

## Keep in Parent

### 8. AI bridge protocol as a central runtime
Parent evidence:
- `~/rust/ai-bridge/PROTOCOL.md`
- `~/rust/ai-bridge/conversation.jsonl`

Why keep in parent:
- It is lineage-critical, but it belongs to the parent system's center of gravity.
- `concentric_study` has a different architectural center: visual web-agent runtime, not Cursor-side AI-to-AI handoff.

What to preserve:
- selective handoff patterns
- historical understanding of how the agent lineage emerged

What not to do:
- do not re-center `concentric_study` around the bridge protocol

### 9. Coach-control as a wholesale subsystem
Parent evidence:
- `~/rust/coach-control/`

Why keep in parent:
- It is specialized to the parent supervision workflow.
- It is best treated as a source of patterns, not as a module to import wholesale.

What to preserve:
- watchdog-triggered supervision ideas
- operator escalation concepts

What not to do:
- do not import the full subsystem into `concentric_study`

## Dependency Ordering
1. host-tool health discovery and backend selection
2. canonical runtime baseline and reset doctrine
3. bounded curiosity with explicit action inventories
4. operational capability registry
5. documentation claims drift guards
6. attested run packs
7. metaphor guard if still justified after first-wave gains

Rationale:
- host-tool health and canonical baseline define the environment model
- bounded exploration should sit on top of that stable environment model
- capability registry and doc guards describe and verify what the matured system can do
- attested run packs are best added after the run structure is stable

## Recommended Transfer Program
### Phase 1
- host-tool health discovery and backend selection
- canonical runtime baseline and reset doctrine

### Phase 2
- bounded curiosity with explicit action inventories

### Phase 3
- operational capability registry
- documentation claims drift guards

### Phase 4
- attested run packs
- optional metaphor guard

## Final Judgment
The best transfer strategy is not to copy subsystems mechanically.

The right move is:
- port first the parent's environment-discipline layers
- keep the current core runtime as the center of gravity
- treat `~/rust` as an operator-discipline source, not as a runtime to merge wholesale

That preserves the strongest property of `concentric_study` while still harvesting the parent system's best sophistication layers.
