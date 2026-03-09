# Section 9: Master Systems Diagram

## Purpose

This section turns the Concentric architecture story into one explicit,
end-to-end systems diagram in prose. It answers six questions:

1. What enters the republic as input?
2. Which ministries process that input, and in what order?
3. What constitutional laws constrain those ministries?
4. What outputs leave the runtime after a mission?
5. What feedback loops turn one run into future state?
6. What legitimacy loop sits above the runtime and judges the judge itself?

The goal is not to replace the subsystem reports or the narrative trilogy. The
goal is to provide a single master account of how all major architectural
parts connect and why those connections exist.

## Thesis

Concentric is a republic for converting `human intent` into `audited,
learnable, and eventually legitimate action`.

The whole system is held together by two interlocking loops:

- `operational loop`: see -> understand -> plan -> act -> recover -> verify
  -> record -> learn
- `constitutional loop`: describe the state -> constrain the state -> audit
  the state -> judge the judge -> reform the state

The runtime can be understood as a layered dependency chain. The broader
project can be understood as the same chain placed under increasingly stronger
truth and legitimacy conditions.

## 1. Input Plane

Every mission enters the republic as a bundle of state pressure rather than a
single string.

### Input classes

- `human intent`: task description, target state, or desired artifact
- `target context`: URL, app, site, or local GUI state
- `host substrate`: what this machine can currently support
- `persistent civic memory`: skills, trust, site knowledge, rules, and
  reflections
- `current visual/semantic frontier`: what the system can currently perceive

### Primary runtime entrypoints

- `operator/agent.py`
- `operator/cre/test_excalidraw_covt.py`

### Input gating and conditioning

- `operator/agent_infra/host_tool_health.py`
- `operator/agent_infra/skill_library.py`
- `operator/agent_infra/action_trust.py`
- `operator/agent_infra/site_knowledge.py`
- `operator/agent_infra/summarizer.py`

### Why this plane exists

The republic cannot act correctly unless it first distinguishes:

- what is being asked
- whether this machine can currently support the mission
- what it already knows from prior missions
- what present territory the mission is actually about

This is why Concentric does not begin with action. It begins with state
qualification.

## 2. Ministry Dependency Chain

The core runtime is a ministry chain. Each ministry solves the insufficiency
of the previous one.

### 2.1 Executive Office

Canonical file:

- `operator/agent.py`

Role:

- classify the mission
- activate needed capability classes
- initialize the execution context
- choose research/planning mode
- call execution
- invoke final verification
- finalize the run into archive state

Why it connects first:

Because the republic needs a sovereign interpretation of the task before it
can know which institutions should exist for this mission at all.

### 2.2 Civil Service Commission and Staffing Layer

Primary file:

- `operator/capability_router.py`

Related layer:

- `operator/inference_router.py`

Role:

- determine which capabilities are required, optional, or irrelevant
- activate the right perception, tool, memory, and safety institutions
- route cognition according to cost/capability tradeoffs

Why it connects after the Executive:

Because a mission must be politically framed before staffing can be
appropriate. The executive defines the problem; the staffing layer defines the
active state apparatus for that problem.

### 2.3 Survey Office and Cartographic Service

Primary files:

- `operator/a11y_engine.py`
- `operator/visual_engine.py`
- `operator/element_map.py`
- `operator/window_capture.py`
- `operator/web_primitives.py`

Role:

- observe the frontmost world
- recover visual and accessibility structure
- fuse visual and semantic evidence into a usable element map
- expose site-agnostic semantic operations over that recovered world

Why it connects here:

Because the republic cannot plan over a world it has not yet observed. This is
the first major anti-fantasy institution in the system.

### 2.4 Planning Ministry

Primary file:

- `operator/agent_infra/research_agent.py`

Supporting files:

- `operator/agent_infra/site_knowledge.py`
- `operator/agent_infra/skill_library.py`
- `operator/action_space.py`

Role:

- study the task subject
- study methods for achieving it
- study available tools in the target province
- map those methods into the republic's lawful action vocabulary

Why it connects after the Survey Office:

Because planning must be grounded in observed territory rather than purely in
textual desire.

### 2.5 Legislature and Public Action Code

Primary file:

- `operator/action_space.py`

Role:

- define the action vocabulary
- distinguish public planner-visible actions from hidden or special actions
- provide the lawful semantic surface for planning and execution
- expose conformance reporting against live dispatchability

Why it connects here:

Because planning needs not just strategy, but a legal grammar. Without this
layer, plans remain prose rather than state-sanctioned action.

### 2.6 Ministry of Interior and Public Works

Primary file:

- `operator/agent_infra/action_handlers.py`

Supporting files:

- `operator/agent_infra/action_contracts.py`
- `operator/agent_infra/action_allowlist.py`

Role:

- translate lawful verbs into concrete procedures
- enforce site-conditioned execution contracts
- provide generic actions, browser/UI-specialized actions, and site-specific
  macros

Why it connects after the Legislature:

Because laws must become dispatch. This ministry is where public action names
become local labor.

### 2.7 State Machinery Depot

Primary file:

- `operator/agent_core.py`

Role:

- perform clicks, drags, keystrokes, screenshots, confirmations, and visual
  assertions against the macOS substrate

Why it connects here:

Because even perfectly mapped procedures still need actual machine force.
Handlers define operational semantics. The machinery depot makes them
physically true.

### 2.8 Emergency Authority

Primary files:

- `operator/agent_infra/recovery.py`
- `operator/agent_infra/healing_orchestrator.py`
- `operator/agent_infra/decision_graph.py`
- `operator/agent_infra/outer_loop.py`

Role:

- verify action effects
- retry or repair failed steps
- classify failures by type
- reconstruct causal chains
- convert failure into structured lessons and, when necessary, escalation

Why it connects here:

Because the republic governs foreign territory. Failure is not exceptional
enough to be treated as a surprise. It must be institutionalized.

### 2.9 Supreme Inspectorate

Primary file:

- `operator/agent_infra/verification_gate.py`

Supporting file:

- `operator/agent_infra/visual_monitor.py`

Role:

- inspect the final state
- decompose task constraints
- judge whether the mission truly satisfied the civic demand

Why it connects after execution and recovery:

Because successful motion is not identical to accepted result. The republic
requires a final office that can say whether the task actually counts as done.

## 3. Constitutional Law Layer

The runtime is governed by laws that were added to prevent specific classes of
state falsehood.

### 3.1 Truthful Lawbook Act

Primary file:

- `operator/action_space.py`

Settlement:

- public planner-visible law must be narrower than "everything we know how to
  mention"
- public law must remain checkable against the live dispatcher

Prevents:

- legal overstatement of runtime capability

### 3.2 Executive Dispatchability Act

Primary file:

- `operator/agent_infra/action_handlers.py`

Settlement:

- planner-visible verbs must have live handler support
- semantic drift between planning and execution becomes a regression

Prevents:

- public verbs that exist only on paper

### 3.3 Emergency Powers Validity Act

Primary file:

- `operator/agent_infra/research_agent.py`

Settlement:

- fallback action types must be as lawful as primary action types

Prevents:

- imaginary contingency plans

### 3.4 Boundary Discipline Act

Primary files:

- `operator/agent_infra/action_handlers.py`
- `operator/agent.py`
- `operator/agent_infra/research_agent.py`

Settlement:

- ministries must communicate through ports and injected interfaces rather
  than private tunnels

Prevents:

- hidden cross-layer coupling and drift

### 3.5 Unified Civil Registry Act

Primary file:

- `operator/agent_infra/trace_writer.py`

Settlement:

- task result, execution result, verification result, and step outcomes must
  be represented separately but coherently

Prevents:

- fragmented sovereignty over mission truth

### 3.6 Auditor Alignment Act

Primary files:

- `operator/agent_infra/diagnostic_reader.py`
- `operator/agent_infra/benchmark_evaluator.py`

Settlement:

- diagnostics and benchmark scoring must consume the same normalized outcome
  contract

Prevents:

- archives and evaluators speaking different languages about the same run

### 3.7 Inspectorate Accountability Act

Primary files:

- `operator/cre/project_understanding/tools/build_verification_calibration.py`
- `operator/cre/project_understanding/SECTION_8_VERIFICATION_GATE_CALIBRATION.md`

Settlement:

- the final judge must be calibratable against blinded human review and
  adjudicated ground truth

Prevents:

- permanent unreviewable authority in the verification layer

## 4. Output Plane

The republic does not produce a single "result." It produces a family of
outputs, each serving a different civic function.

### Output classes

- `physical output`: the changed screen, page state, artifact, or completed UI
  task
- `verdict output`: final verification pass/fail plus deficiencies
- `archive output`: trace, manifest, screenshots, and monitor artifacts
- `analytic output`: diagnostics, benchmarks, causal reports, recovery
  assessments
- `memory output`: skill promotions, trust updates, site knowledge, lessons,
  and rules

### Primary producing files

- `operator/agent_infra/trace_writer.py`
- `operator/agent_infra/verification_gate.py`
- `operator/agent_infra/visual_monitor.py`
- `operator/agent_infra/benchmark_evaluator.py`
- `operator/agent_infra/skill_library.py`
- `operator/agent_infra/outer_loop.py`

### Why outputs are plural

Because a republic needs different truths for different functions:

- what changed in the world
- whether the mission should count as accepted
- how the mission unfolded
- how the mission compares to others
- what should be remembered for the future

## 5. Feedback Loop Map

Concentric is defined as much by its loops as by its layers.

### 5.1 Tactical execution loop

`plan -> execute -> verify local effect -> recover if needed -> continue`

Primary file:

- `operator/agent_infra/recovery.py`

Purpose:

- keep the mission alive inside unstable territory

### 5.2 Archive and diagnosis loop

`run -> trace -> manifest -> diagnostic reading -> benchmark evaluation`

Primary files:

- `operator/agent_infra/trace_writer.py`
- `operator/agent_infra/diagnostic_reader.py`
- `operator/agent_infra/benchmark_evaluator.py`

Purpose:

- convert action history into state-readable evidence

### 5.3 Memory and policy loop

`successful traces and repeated outcomes -> skill/trust/site knowledge/rules -> future planning and execution bias`

Primary files:

- `operator/agent_infra/skill_library.py`
- `operator/agent_infra/action_trust.py`
- `operator/agent_infra/site_knowledge.py`
- `operator/agent_infra/outer_loop.py`

Purpose:

- make the republic stateful across missions

### 5.4 Failure-to-reform loop

`failure -> classification -> causal analysis -> reflection -> retry, rule, or escalation`

Primary files:

- `operator/agent_infra/healing_orchestrator.py`
- `operator/agent_infra/decision_graph.py`
- `operator/agent_infra/outer_loop.py`

Purpose:

- ensure failure becomes civic knowledge rather than isolated pain

## 6. Legitimacy Loop

The legitimacy loop sits above the runtime rather than inside it.

### Sequence

1. `VerificationGate` produces verdict artifacts during or after missions.
2. Archived verification records are exported as calibration candidates.
3. Blind review packets are created so human raters do not see the gate's own
   verdict first.
4. Two independent human raters label the same packets.
5. If needed, adjudication resolves disagreement into effective ground truth.
6. Agreement metrics compare the machine judge to human civic judgment.

### Primary files and artifacts

- `operator/cre/project_understanding/tools/build_verification_calibration.py`
- `operator/cre/project_understanding/artifacts/verification_calibration_candidates.jsonl`
- `operator/cre/project_understanding/artifacts/verification_calibration_report.json`
- `operator/cre/project_understanding/artifacts/verification_review_packets/`

### Why this loop is higher than the runtime

Because the runtime can be internally coherent and still not yet deserve
trust. The legitimacy loop is the mechanism by which the republic tests
whether its own highest judge should remain authoritative.

## 7. Why Everything Connects

The architecture is not arbitrary. Every major connection exists because the
layer below it, by itself, is insufficient.

- `intent` without perception is blindness
- `perception` without planning is wandering
- `planning` without lawful verbs is rhetoric
- `lawful verbs` without handlers is fiction
- `handlers` without machine control is theater
- `execution` without recovery is fragility
- `recovery` without verification is self-deception
- `verification` without records is amnesia
- `records` without learning is waste
- `learning` without audit is drift
- `audit` without human calibration is incomplete legitimacy

That chain is the strongest single explanation of why Concentric has so many
institutions. Each one exists because the republic refuses to collapse the
problem into a simpler but less truthful one.

## 8. Whole-System Reading

The shortest complete reading of Concentric is:

- the Executive receives a mission
- the staffing layer decides which ministries are active
- the Survey Office builds a world model
- the Planning Ministry translates desire into doctrine
- the Legislature provides the public action code
- the operational ministries dispatch those actions through machine force
- the Emergency Authority handles failure
- the Supreme Inspectorate judges the final result
- the Ministry of Records preserves what happened
- the auditors interpret it
- the memory institutions shape future runs
- the legitimacy loop waits above all of this to judge the judge

This is the master systems diagram in prose.

It is the clearest explanation of how the story, the code, the reforms, and
the remaining future trial all belong to one republic rather than a pile of
parts.
