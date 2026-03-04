# Rust Parent Environment Sophistication Audit (PhD)

## Scope
This memo treats `~/rust` as the parent environment that incubated `concentric_study`.
The question is not whether `~/rust` is interesting on its own. The question is:

1. Which mechanisms in `~/rust` already evolved into `concentric_study`?
2. Which mechanisms in `~/rust` are still stronger or more explicit there?
3. Which of those could make `concentric_study` more sophisticated if ported carefully?
4. Which should remain historical or local to the parent system?

## Method
Primary evidence from `~/rust`:
- `~/rust/README.md`
- `~/rust/QUICK_START.md`
- `~/rust/FIELD_NOTEBOOK.md`
- `~/rust/CANONICAL_OPERATOR_STATE.md`
- `~/rust/operator/README.md`
- `~/rust/operator/mac_core_agent/README.md`
- `~/rust/ai-bridge/PROTOCOL.md`
- `~/rust/capabilities/REGISTRY.md`
- `~/rust/operator/tool_catalog.yaml`
- `~/rust/operator/health_contract.yaml`
- `~/rust/operator/cursor_action_inventory.yaml`
- `~/rust/operator/learn_explore.py`
- `~/rust/operator/explore_analyze.py`
- `~/rust/operator/gauntlet_run.py`
- `~/rust/operator/report_claims_guard.py`
- `~/rust/operator/report_snapshot_sync.py`
- `~/rust/operator/safari_page_mapper.py`
- `~/rust/coach-control/*`

Comparison evidence from `concentric_study`:
- `AGENTS.md`
- `operator/cre/project_understanding/README.md`
- `operator/cre/MASTER_TOOL_LIST_PHD.md`
- targeted repo search across `operator/**/*.py`, docs, and artifacts

## Executive Judgment
`concentric_study` is already the more advanced runtime in the core agent loop:
- richer perception
- richer tracing
- stronger recovery
- stronger verification
- stronger architecture documentation
- stronger benchmark/evaluation surface

But `~/rust` still contains **six sophistication layers** that are either missing or materially more explicit there:

1. host-tool health discovery and backend selection
2. explicit health contracts and bounded curiosity exploration
3. canonical baseline/reset discipline for the operator environment
4. capability registry with proof/check commands
5. document-claim drift guards for major reports
6. attested run-pack verification for deterministic observation packs

Those six are the parent-environment mechanisms most likely to make `concentric_study` more sophisticated.

## What Was Clearly Inherited Already
These ideas exist in `~/rust` and have already evolved into stronger forms in `concentric_study`.

### 1. Test-first, prove-first culture
Parent evidence:
- `~/rust/FIELD_NOTEBOOK.md`
- `~/rust/QUICK_START.md`

Current descendant:
- `operator/cre/PHD_DECISION_PRACTICE.md`
- `.cursor/rules/concentric-study.mdc`
- `operator/cre/CONTEXT_LOCKED_RESEARCH_FILTER_PHD.md`
- `operator/cre/RECURSIVE_PHD_RESEARCH_LOOP.md`

Conclusion:
- inherited and strengthened
- do not port; already present in a better form

### 2. Run ledgers and evidence capture
Parent evidence:
- `~/rust/operator/new_run.sh`
- `~/rust/operator/log_event.sh`
- `~/rust/operator/runs/`

Current descendant:
- `operator/agent_infra/trace_writer.py`
- `operator/agent_infra/diagnostic_reader.py`
- `operator/cre/runs/`

Conclusion:
- inherited and generalized into structured trace/manifests
- current repo is stronger

### 3. Capability memory
Parent evidence:
- `~/rust/capabilities/REGISTRY.md`
- `~/rust/capabilities/registry.json`

Current descendant:
- `operator/agent_infra/skill_library.py`
- `operator/cre/skill_library.json`

Conclusion:
- inherited conceptually, but changed form
- current repo is stronger for task skills; parent still stronger for environment-level operational capabilities

### 4. Visual watchdog and supervision ideas
Parent evidence:
- `~/rust/coach-control/visual_watchdog.sh`
- `~/rust/FIELD_NOTEBOOK.md`

Current descendant:
- `operator/agent_infra/visual_monitor.py`
- recovery checkpoints added around monitor captures

Conclusion:
- inherited and generalized
- parent still has one supervision pattern not yet ported: watchdog-triggered coach review against long-running external agents

## Net-New Sophistication Worth Porting
These are the high-value candidates.

## Candidate A: Tool Catalog + Runtime Backend Selection
Parent evidence:
- `~/rust/operator/tool_catalog.yaml`
- `~/rust/operator/tool_status.py`
- `~/rust/package.json`

What it does in the parent:
- declares required tool classes (`cursor_ui_automation`, `browser_automation`, `runtime_python`, etc.)
- checks actual backend availability (`osascript`, `hammerspoon`, `playwright`, `jq`, `rg`, `ruby`, `git`, `docker`)
- selects the preferred available backend
- can fail closed if a required class has no valid provider

Current state in `concentric_study`:
- `operator/capability_router.py` activates higher-level capabilities
- but there is no equally explicit machine-verifiable host-tool class selection layer

Why this would improve sophistication:
- startup would stop assuming the machine is ready just because Python imports succeed
- environment degradation could be diagnosed before task execution
- backend choice could become explicit and testable

Recommendation:
- port the concept, not the exact YAML
- add a `tool_health` layer to `concentric_study` for host prerequisites and preferred backends

Value:
- high

## Candidate B: Health Contract + Bounded Curiosity Exploration
Parent evidence:
- `~/rust/operator/health_contract.yaml`
- `~/rust/operator/cursor_action_inventory.yaml`
- `~/rust/operator/learn_explore.py`
- `~/rust/operator/explore_analyze.py`

What it does in the parent:
- enumerates safe exploratory actions with explicit triggers, expectations, undo paths, and prerequisites
- enforces baseline restoration between actions
- limits curiosity budget
- computes mastered actions and next frontier actions from run history

Current state in `concentric_study`:
- `SiteKnowledge` and `ExplorationLoop` exist
- but exploration is more qualitative and site-knowledge-centric than contract-inventory-centric
- there is no equally explicit action frontier ledger for safe autonomous discovery

Why this would improve sophistication:
- exploration would become auditable and bounded
- newly discovered site behaviors could advance through a mastery pipeline
- risky exploration on novel sites would have stronger safety rails

Recommendation:
- port the concept as a site/action exploration contract layer
- do not keep it Cursor-specific; make it browser/site-action generic

Value:
- very high

## Candidate C: Canonical Baseline and Reset as a First-Class Contract
Parent evidence:
- `~/rust/CANONICAL_OPERATOR_STATE.md`
- `~/rust/cursor-nav/verify_nav_baseline.sh`
- `~/rust/operator/reset_cursor_baseline.sh`

What it does in the parent:
- defines a known-good operator environment state
- verifies it before work
- restores it deterministically when drift occurs
- treats broken baseline as a hard blocker, not a vague inconvenience

Current state in `concentric_study`:
- there are startup checks and recovery routines
- but there is no equally central, named, canonical operator-environment contract for the whole system
- local patches exist for Safari/Kleki state normalization, but not a unifying environment baseline doctrine

Why this would improve sophistication:
- preflight would become more deterministic
- recovery could reason from a named baseline instead of ad hoc local state repair
- environment drift could be tested and reported as a first-class failure category

Recommendation:
- create a `CANONICAL_RUNTIME_BASELINE.md` plus machine-verifiable preflight contract in `concentric_study`

Value:
- high

## Candidate D: Capability Registry for Operational Powers, Not Just Task Skills
Parent evidence:
- `~/rust/capabilities/registry.json`
- `~/rust/capabilities/REGISTRY.md`

What it does in the parent:
- stores named capabilities with:
  - status
  - automation level
  - entrypoint
  - check command
  - evidence paths
  - limits
  - last verification time

Current state in `concentric_study`:
- `SkillLibrary` stores reusable task plans and trace-derived skills
- the project-understanding corpus stores tool inventory and docs
- but there is no compact operational capability registry that answers:
  - what exact machine powers are proven here right now?
  - how are they re-verified?

Why this would improve sophistication:
- separates environment capabilities from task skills
- improves demo readiness and regression clarity
- reduces ambiguity about “what the system can actually do today”

Recommendation:
- add an `operational_capabilities.json` layer distinct from `skill_library.json`

Value:
- medium-high

## Candidate E: Report Snapshot Sync and Claims Guard
Parent evidence:
- `~/rust/operator/report_snapshot_sync.py`
- `~/rust/operator/report_claims_guard.py`
- `~/rust/package.json` gate scripts

What it does in the parent:
- syncs factual snapshot fields in major reports
- checks required factual claims and consistency
- prevents stale project-level summary docs from drifting away from current evidence

Current state in `concentric_study`:
- there is a strong understanding corpus and generated artifacts
- but there is no general doc-claim enforcement layer over major narrative reports

Why this would improve sophistication:
- long-form PhD memos would stay tighter to the generated evidence
- fewer stale “summary” docs would survive unnoticed

Recommendation:
- port this as a documentation-integrity gate for the understanding corpus and flagship memos

Value:
- medium-high

## Candidate F: Attested Run Packs for Deterministic Observation
Parent evidence:
- `~/rust/operator/mac_core_agent/README.md`
- `~/rust/operator/mac_core_agent/verify.sh`
- observe-only run pack with hashes and schema checks

What it does in the parent:
- creates self-contained run packs with:
  - policy
  - plan
  - mission
  - events
  - before/after UI snapshots
  - diffs
  - verdict
  - hash attestations

Current state in `concentric_study`:
- traces and manifests are rich
- screenshots and monitor timelines exist
- but attested run packs are not the standard artifact unit

Why this would improve sophistication:
- stronger reproducibility and auditability
- easier external review of a single run without replaying the whole repo context
- cleaner customer/demo evidence bundles

Recommendation:
- add an optional attested run bundle exporter for high-value runs and benchmarks

Value:
- medium

## Secondary Candidates Worth Considering

### Metaphor Guard
Parent evidence:
- `~/rust/operator/metaphor_guard.sh`
- `~/rust/METAPHOR_TO_RULES.md`

Why it matters:
- user instructions often contain metaphors and informal labels
- the parent system forces those into executable explicit rules

Current state in `concentric_study`:
- stronger research rigor exists, but no explicit metaphor-to-action guard

Value:
- medium
- especially useful because the human operator uses informal language frequently

### Research Refresh Memory
Parent evidence:
- `~/rust/operator/research_update.py`
- `~/rust/operator/research_diff.py`
- `~/rust/operator/research_status.py`
- `~/rust/operator/research/history/search_memory.jsonl`

Current state in `concentric_study`:
- task-specific `ResearchAgent` is stronger at pre-execution intelligence
- but there is no equally explicit persistent external-research refresh loop for the project itself

Value:
- medium

### Safari Page Mapper
Parent evidence:
- `~/rust/operator/safari_page_mapper.py`

Current state in `concentric_study`:
- stronger perception stack already exists (`window_capture.py`, `visual_engine.py`, `a11y_engine.py`, `element_map.py`)

Judgment:
- mostly superseded
- not a priority port

## Mechanisms That Should Stay In The Parent Project
These are important historically, but should not be treated as net-new sophistication for `concentric_study`.

### AI-to-AI file bridge as core architecture
Parent evidence:
- `~/rust/ai-bridge/PROTOCOL.md`
- `~/rust/ai-bridge/conversation.jsonl`

Reason to retain as parent-specific:
- `concentric_study` is now a visual web-agent runtime, not a Cursor-panel bridge system
- bridge patterns may still help with special workflows, but the core runtime should not regress toward this as its center of gravity

### Coach-control folder as a whole
Parent evidence:
- `~/rust/coach-control/*`

Judgment:
- valuable as historical supervision design
- not something to import wholesale
- only selective patterns are worth extracting:
  - watchdog-triggered review
  - overlap-layout verification logic
  - active target project bookkeeping

### Cursor-specific navigation mastery program as the main focus
Parent evidence:
- `~/rust/cursor-nav/*`

Judgment:
- useful for lineage and environment understanding
- but `concentric_study` has moved to cross-site browser automation
- only the baseline doctrine and verification discipline should transfer

## Ranked Transfer Plan

### Priority 1
1. Health Contract + action-inventory-based bounded exploration
2. Host tool catalog and runtime backend status selection
3. Canonical runtime baseline and reset contract

### Priority 2
4. Operational capability registry distinct from task skill library
5. Documentation claims guard and snapshot sync

### Priority 3
6. Optional attested run-pack exporter
7. Metaphor guard for informal operator language
8. Project-level research refresh memory

## Bottom Line
Yes. There is still material in `~/rust` that can make `concentric_study` more sophisticated.

The best candidates are not the obvious historical bridge scripts. The real value is the parent project's **operator discipline infrastructure**:
- explicit backend/tool health selection
- bounded curiosity with undoable action inventories
- canonical baseline/reset contracts
- operational capability proofs
- documentation drift guards
- attested observation packs

That is where the parent project is still ahead.

## Recommendation
If this lineage work becomes implementation work, the first concrete build should be:

1. `operator/runtime_health/` or equivalent
2. `operator/exploration_contracts/` or equivalent
3. `operator/operational_capabilities.json`
4. `operator/cre/CANONICAL_RUNTIME_BASELINE.md`
5. doc-claim integrity checks for the understanding corpus

That sequence imports the strongest parent sophistication without dragging `concentric_study` back into the old Cursor-bridge architecture.
