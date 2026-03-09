# Master PhD Architecture Brief

**Date:** March 6, 2026

## 1. Purpose

This brief is the single synthesis layer for `concentric_study`.

It answers four questions:

1. What kinds of code are in this repository?
2. How are those code families supposed to connect?
3. What would "best possible PhD-level form" mean for this architecture?
4. What deep research should happen next, based on the live repo rather than aspiration?

This is not a replacement for the rest of the corpus. It is the shortest
artifact that still preserves a research-grade whole-system view.

## 2. Thesis

`concentric_study` is best understood as a research platform for embodied GUI and
web agents on macOS.

It is not primarily:
- a normal application
- a pure benchmark harness
- a pure library
- a thin shell around a model API

It is a layered cybernetic system with:
- perception and grounding
- semantic planning and policy selection
- executable GUI actuation
- verification and evidence capture
- cross-run learning and self-healing
- safety and authorization boundaries
- benchmark and governance surfaces around the runtime

The architecture is already stronger than a typical experimental agent repo
because the runtime is instrumented, verified, and persistently stateful.
Its main problem is not absence of structure. Its main problem is partial drift
between intended semantics and executable semantics, plus duplicated orchestration
across the universal and legacy entrypoints.

## 3. Method

This brief follows the repo's own evidence-first decision rules and uses:

- live source inspection across `operator/`
- the existing understanding corpus in `operator/cre/project_understanding/`
- fresh local validation from architecture conformance, host-tool health, and regression tests
- primary external sources in architecture description, architecture recovery,
  quality attributes, dynamic program comprehension, and agent-system evaluation

Fresh local validation performed for this brief:

- `python3 operator/cre/project_understanding/tools/build_architecture_conformance.py --check`
- `cd operator && ./venv/bin/python -m agent_infra.host_tool_health --summary --has-url`
- `cd operator && ./venv/bin/python -m pytest cre/test_phase3_equation_solver.py test_router_dryrun.py cre/test_auth_workflow.py -q --tb=short`

Observed live facts from those runs:

- architecture conformance enforcement passed
- the conformance check still reports `9` live imports targeting root-level compatibility shims
- the conformance check still reports `6` direct imports of the `agent_infra` package facade
- host readiness for URL-driven tasks reports all required substrate classes ready
- the focused regression slice passed: `25 passed`

Additional live fact established from the runtime surface:

- `UnifiedActionSpace` declares `33` action names
- `ACTION_HANDLERS` exposes `33` dispatchable keys
- `9` declared action names still map to handler keys not present in the live dispatcher:
  - `type -> type_text`
  - `scroll -> scroll`
  - `screenshot -> screenshot`
  - `a11y_snapshot -> a11y_snapshot`
  - `draw_shape -> draw_shape`
  - `go_back -> go_back`
  - `login_flow -> login_flow`
  - `bmw_details -> bmw_details`
  - `bmw_shading -> bmw_shading`

## 4. What Kinds Of Code These Are

The repo contains at least nine distinct code species.

### 4.1 Runtime orchestration code

Purpose:
- convert a task and site into a live execution session

Primary files:
- `operator/agent.py`
- `operator/cre/test_excalidraw_covt.py`

Interpretation:
- these are composition roots
- `operator/agent.py` is the universal path
- `operator/cre/test_excalidraw_covt.py` is the historical benchmark lineage path

### 4.2 Semantic and policy-plane code

Purpose:
- define the abstract action language
- activate task-relevant capabilities
- choose inference providers
- translate research into executable plan vocabulary

Primary files:
- `operator/action_space.py`
- `operator/capability_router.py`
- `operator/inference_router.py`
- `operator/agent_infra/research_agent.py`

Interpretation:
- this layer defines what the agent thinks it can do
- it is the architectural contract between planning and execution

### 4.3 Perception and grounding code

Purpose:
- recover what is on screen
- attach semantics to visible regions
- build stable references for action selection

Primary files:
- `operator/window_capture.py`
- `operator/visual_engine.py`
- `operator/a11y_engine.py`
- `operator/element_map.py`
- `operator/web_primitives.py`

Interpretation:
- this is a hybrid grounding stack, not a pure-vision stack
- it combines screenshots, Set-of-Mark overlays, accessibility extraction,
  and fused semantic maps

### 4.4 Execution semantics code

Purpose:
- convert semantic actions into actual GUI behavior
- define what counts as a valid or failed action
- repair failures when execution diverges from intent

Primary files:
- `operator/agent_core.py`
- `operator/agent_infra/action_handlers.py`
- `operator/agent_infra/action_contracts.py`
- `operator/agent_infra/action_allowlist.py`
- `operator/agent_infra/recovery.py`

Interpretation:
- this is the real machine interface of the project
- it is where abstract agent intent becomes Quartz, Safari, AppleScript,
  PyObjC, and screenshot-backed verification

### 4.5 Evidence, learning, and evaluation code

Purpose:
- make every run inspectable
- turn traces into diagnosis
- turn successes into reusable memory
- score runs beyond binary pass/fail

Primary files:
- `operator/agent_infra/trace_writer.py`
- `operator/agent_infra/diagnostic_reader.py`
- `operator/agent_infra/skill_library.py`
- `operator/agent_infra/action_trust.py`
- `operator/agent_infra/visual_monitor.py`
- `operator/agent_infra/verification_gate.py`
- `operator/agent_infra/decision_graph.py`
- `operator/agent_infra/benchmark_evaluator.py`
- `operator/agent_infra/outer_loop.py`

Interpretation:
- this is what makes the repo scientific rather than merely operational
- the runtime is designed to leave recoverable evidence and to improve
  across runs

### 4.6 Safety and authorization code

Purpose:
- constrain unsafe or poisoned inputs
- isolate secrets
- require human approval for risky actions

Primary files:
- `operator/security/sanitizer.py`
- `operator/security/credential_vault.py`
- `operator/security/auth_workflow.py`

Interpretation:
- this is a real boundary subsystem, not incidental utility code

### 4.7 IDE and MCP integration code

Purpose:
- expose repo-local health and trace information back into the editor
- support read-only observability over the runtime

Primary files:
- `operator/cursor_integration/mcp/base.py`
- `operator/cursor_integration/mcp/trace_server.py`

Interpretation:
- these are sidecar observation surfaces
- they should not become shadow orchestration paths

### 4.8 Benchmark and experiment code

Purpose:
- evaluate the runtime
- preserve historical site-specific competence
- host demonstrations and regression surfaces

Primary files:
- `operator/cre/test_*.py`
- `operator/cre/test_excalidraw_covt.py`

Interpretation:
- `operator/cre` is not "just tests"
- it is the experiment and evidence layer around the runtime

### 4.9 Governance and evidence corpus

Purpose:
- preserve architecture descriptions, decisions, inventories,
  audits, screenshots, traces, and research memos

Primary files:
- `operator/cre/*.md`
- `operator/cre/project_understanding/*.md`
- `operator/cre/runs/*`

Interpretation:
- this is the repo's memory and research-governance surface
- it is large because the project treats evidence as a first-class output

## 5. How These Code Families Are Supposed To Connect

The intended system is:

`goal -> readiness gate -> capability activation -> perception + site/tool research -> typed planning -> action dispatch -> verification/recovery -> final judgment -> trace + memory + benchmarking`

That high-level flow decomposes into the following architectural contract.

### 5.1 Northbound flow

- the orchestrator accepts task intent and site context
- the router activates only the capabilities needed for that task
- the research layer studies the subject, method, and tool affordances before execution
- the action space defines the planner-visible vocabulary

### 5.2 Grounding flow

- the capture layer produces screenshots and window-local geometry
- SoM and accessibility layers produce complementary views of the UI
- the unified element map fuses those views
- semantic primitives and planner prompts consume the fused representation

### 5.3 Southbound execution flow

- the planner emits semantic actions
- the action space resolves aliases into dispatcher keys
- action handlers implement those semantics
- contracts, allowlists, and recovery logic constrain and verify execution
- `agent_core` performs OS-level actuation and VLM-backed assertions

### 5.4 Cross-cutting evidence flow

- action execution emits trace steps
- visual monitoring captures background screenshots
- final verification determines whether the run is actually complete
- diagnostics and DDG analysis explain failures
- the skill library and trust tracker update future execution behavior

### 5.5 Boundary rules

At PhD-grade maturity, these dependency rules should hold:

- `operator/agent.py` may compose subsystems, but should not accumulate site-specific compilation logic indefinitely
- `action_space.py` must not advertise semantics that the dispatcher cannot execute
- `action_handlers.py` should be the only place that translates abstract actions into concrete runtime behavior
- `operator/cre/` should depend inward on runtime code, not become a second permanent runtime core
- MCP servers should read runtime evidence, not mutate runtime state
- security components should wrap planning and sensitive execution, not be bypassed by site-specific shortcuts

## 6. What "Best Possible PhD-Level Form" Means

The best form is not "more code" or "more documents." It is a system whose
architecture is explicit, executable, verifiable, and empirically calibrated.

### 6.1 Architecture description should be standards-grade

The repo should maintain:

- explicit viewpoints and views
- correspondences between code, traces, docs, and persistent state
- a clear distinction between intended architecture and recovered as-built architecture

This repo is already close because the understanding corpus is layered. The next
quality jump is to treat that layering as a maintained architecture description,
not just a set of good memos.

### 6.2 Quality attributes should be explicit and measured

The right quality model here is not generic "clean code." It is a targeted
agent-systems quality model.

Core attributes:

- `reliability`: task success under real GUI noise and recovery conditions
- `modifiability`: ability to change handlers, routers, or site adapters without silent breakage
- `observability`: ability to explain why a run failed from evidence already collected
- `security`: resistance to prompt injection, tool poisoning, credential misuse, and unauthorized workflows
- `performance efficiency`: time, model cost, and verification overhead per successful run
- `portability`: ability to preserve architecture if substrate providers change
- `traceability`: ability to connect claims, code, traces, and benchmark outcomes
- `generality`: transfer from benchmark-specific macros to site-agnostic web operation

### 6.3 The semantic contract should be executable, not aspirational

This is the strongest immediate requirement.

At present, the semantic layer is ahead of the executor in a few places.
The action vocabulary therefore functions partly as an aspiration surface
instead of a purely executable contract.

At PhD-grade maturity, every declared planner action should have:

- a live dispatcher implementation
- a contract or justification for why none is needed
- benchmark and verification coverage
- trace semantics that make failures diagnosable

### 6.4 The system should converge to one canonical runtime path

The universal orchestrator in `operator/agent.py` is the correct strategic
direction, but the legacy harness in `operator/cre/test_excalidraw_covt.py`
still acts as a second composition root.

The best architecture is:

- one canonical orchestration path
- shared inner execution substrate
- benchmark harnesses as clients of that runtime, not peers of it

### 6.5 Site-specific intelligence should become an explicit adapter layer

`operator/agent.py` currently carries significant site-aware plan rewriting,
especially for Kleki and benchmark drawing tasks.

That logic is valuable, but its current placement increases orchestration
entropy. In the best architecture, site-specific normalization becomes:

- explicit adapter modules
- bounded plugin or compiler surfaces
- separate from the universal composition root

### 6.6 Evaluation should be calibrated, not only internal

The repo already has strong internal evidence infrastructure.
The next step is stronger calibration:

- compare verification decisions to human judgment
- compare benchmark scores to user-relevant task completion
- compare trust skipping to actual error leakage
- compare site-knowledge reuse to fresh exploration outcomes

## 7. Current Strengths

The repo is already unusually strong in these areas:

- `agent_infra` centralizes tracing, verification, memory, healing, and evaluation
- host-tool health makes substrate assumptions explicit before execution
- the runtime treats failure diagnosis as a product, not an afterthought
- security is a bounded subsystem rather than diffuse ad hoc checks
- the project-understanding corpus is large but methodologically coherent
- architecture conformance enforcement exists and currently passes
- the run model is evidence-rich enough to support real post-mortem reasoning

## 8. Current Architectural Risks

### 8.1 Semantic/runtime drift

This is the clearest live issue.

`UnifiedActionSpace` and the live `ACTION_HANDLERS` table are not in full
conformance. The mismatch is not theoretical; it is present in current code.

Implication:
- some planner-visible semantics are not guaranteed to be dispatchable
- equation-solving and fallback planning can validate against a vocabulary that
  is broader than the live executor

### 8.2 Dual-entrypoint drift

`operator/agent.py` and `operator/cre/test_excalidraw_covt.py` still preserve
two orchestration centers.

Implication:
- fixes, instrumentation, and policy changes can land unevenly
- architectural understanding becomes more expensive than necessary

### 8.3 Orchestrator accretion

`operator/agent.py` is a good composition root but now also contains
site-specific plan normalization and domain compilation logic.

Implication:
- the universal runtime risks becoming harder to reason about than the
  subsystems it is supposed to compose

### 8.4 Benchmark-specific macro gravity

High-level task macros remain useful for historical competence and regression
value, but they can distort the system toward benchmark-local success.

Implication:
- benchmark strength may overstate general web-agent competence if not
  separated from general-purpose primitives

### 8.5 Compatibility-shim persistence

The conformance check still reports root-level compatibility imports and direct
facade imports.

Implication:
- layering is improving, but erosion pressure has not fully disappeared

## 9. The Deep Research Agenda That Follows From What We Saw

This is the most important forward-looking section.

### 9.1 Executable action-space conformance study

Question:
- does every planner-visible action correspond to a live dispatcher key,
  contract, verification path, and benchmark surface?

Why this is first:
- it targets the clearest current semantic/runtime drift
- it can be turned into a regression gate

Deliverables:
- action vocabulary audit
- alias-normalization policy
- failing test for any new non-dispatchable action
- benchmark and trace coverage matrix per action

### 9.2 Scenario-based architecture evaluation

Question:
- does the current architecture satisfy the quality scenarios that matter most
  for embodied web agents?

Candidate scenarios:
- repeated GUI obstruction and recovery
- hidden prompt injection during tool use
- verification disagreement under ambiguous visual output
- reuse of stale site knowledge after UI drift
- planner/executor mismatch during fallback action selection

Why this is second:
- the repo already has static conformance and dynamic evidence
- the strongest missing layer is scenario-based tradeoff analysis

### 9.3 Verification-gate reliability and calibration study

Question:
- when `VerificationGate` passes or fails a run, how often does a careful human agree?

Why this matters:
- verification is a central success authority in this architecture
- uncalibrated internal judges can create a false sense of rigor

Deliverables:
- sampled run set with blinded human ratings
- precision and recall of verification outcomes
- failure-mode taxonomy for false pass and false fail

### 9.4 Perception failure taxonomy from traces

Question:
- among failed runs, what fraction come from screenshot capture issues,
  SoM misses, a11y misses, fusion errors, stale coordinates, focus changes,
  or site-knowledge drift?

Why this matters:
- current failure reports are strong, but a formal failure taxonomy would let
  the project target the highest-value perception fixes rather than rely on anecdotes

### 9.5 Memory and trust calibration study

Question:
- when do skill reuse, action trust, and site knowledge reduce cost without
  hiding real failures?

Why this matters:
- the repo is already stateful across runs
- persistent memory and trust mechanisms are strengths only if they are calibrated

### 9.6 Benchmark validity study

Question:
- do current benchmarks measure broad GUI-web competence, or do they partly
  reward benchmark-specific macro engineering?

Why this matters:
- the project is evolving from site-specific art tasks toward general web navigation
- benchmark validity determines whether reported progress is strategically meaningful

### 9.7 Security assurance case

Question:
- can the repo make a structured assurance argument for prompt/tool poisoning
  resistance, secret isolation, HITL enforcement, and auth workflow control?

Why this matters:
- the runtime handles real browser surfaces and sensitive workflows
- security claims should become evidence-backed arguments, not only feature lists

### 9.8 Legacy substrate deprecation study

Question:
- which parts of the older `vlm_coordinator.py` and `codex_client.py` lineage
  remain strategically useful, and which should be retired or quarantined?

Why this matters:
- architectural clarity depends on keeping lineage visible without letting it
  silently function as an alternative runtime

## 10. Best Next Research Sequence

The strongest order is:

1. executable action-space conformance study
2. scenario-based architecture evaluation
3. verification-gate calibration study
4. perception failure taxonomy from traces
5. memory and trust calibration study
6. benchmark validity study
7. security assurance case
8. legacy substrate deprecation study

Reason:
- the first step fixes the clearest live architecture gap
- the next three steps calibrate the runtime's strongest internal claims
- the later steps decide how much of the historical surface should remain

## 11. Reading Map

Use this brief together with the rest of the corpus:

- `README.md` for the full corpus map
- `ARCHITECTURE_DIAGRAMS.md` for static subsystem views
- `SUBSYSTEM_DEPENDENCY_REPORT.md` for dependency structure
- `RUNTIME_FLOWS.md` for end-to-end execution paths
- `SECTION_3_ARCHITECTURE_CONFORMANCE.md` for layering conformance
- `SECTION_5_DYNAMIC_EXECUTION_ARCHITECTURE.md` for runtime-recovered architecture
- `ARCHITECTURE_DEBT_REGISTER.md` for tracked debt
- `PHD_EXTERNAL_RESEARCH_VALIDATION.md` for methodology validation
- `PHD_PATH_REVALIDATION.md` for strongest research-backed sequencing

## 12. Decision

### Context

The repo already has a serious runtime, serious instrumentation, and a serious
architecture-understanding corpus.

### Decision

Treat `concentric_study` as a research platform for embodied web agents with
four first-order concerns:

- executable semantics
- evidence-backed evaluation
- safe and bounded autonomy
- architecture clarity under ongoing evolution

### Consequences

- Positive: this framing explains why the repo contains both runtime code and
  unusually large evidence/governance surfaces
- Positive: it gives a coherent target architecture for future changes
- Positive: it identifies the next research tasks from live evidence rather than from fashion
- Trade-off: it makes architectural discipline a permanent requirement, not a cleanup phase

## 13. Primary External Sources

Architecture description and recovery:

- ISO/IEC/IEEE 42010 overview: https://www.iso-architecture.org/ieee-1471/
- IEEE 42010 standard page: https://standards.ieee.org/ieee/42010/6846/
- SEI Views and Beyond: https://www.sei.cmu.edu/library/views-and-beyond-the-sei-approach-for-architecture-documentation/
- SEI Documenting Software Architectures, 2nd ed.: https://www.sei.cmu.edu/library/documenting-software-architectures-views-and-beyond-second-edition/
- SEI Architecture Reconstruction Guidelines, Third Edition: https://www.sei.cmu.edu/library/architecture-reconstruction-guidelines-third-edition/
- SEI View Extraction and View Fusion in Architectural Understanding: https://www.sei.cmu.edu/library/view-extraction-and-view-fusion-in-architectural-understanding/
- SEI Architecture Analysis Techniques and When to Use Them: https://www.sei.cmu.edu/library/sei-architecture-analysis-techniques-and-when-to-use-them/

Quality attributes and architecture evaluation:

- ISO/IEC 25010 quality model: https://www.iso.org/standard/78176.html

Program comprehension and dependence reasoning:

- Ferrante et al., Program Dependence Graph: https://dl.acm.org/doi/10.1145/24039.24041
- Cornelissen et al., dynamic-analysis survey: https://ieeexplore.ieee.org/document/4634918
- Eisenbarth et al., static and dynamic feature analysis: https://www.cs.kent.edu/~jmaletic/cs69995-PC/papers/Elsenbath01.pdf
- Murphy et al., Software Reflexion Models: https://www.cs.ubc.ca/~murphy/papers/rm/fse95.html

Embodied web and computer-use agents:

- Mind2Web: https://arxiv.org/abs/2306.06070
- AppAgent: https://arxiv.org/abs/2312.13771
- SeeAct: https://arxiv.org/abs/2401.01614
- WebVoyager: https://aclanthology.org/2024.acl-long.371/
- OSWorld: https://os-world.github.io/
- Agent S: https://arxiv.org/abs/2410.08164

Security context:

- OWASP MCP Top 10: https://owasp.org/www-project-mcp-top-10/
