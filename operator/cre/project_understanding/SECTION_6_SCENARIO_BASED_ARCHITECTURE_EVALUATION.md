# Section 6: Scenario-Based Architecture Evaluation

## 1. Purpose

Sections 1 through 5 established the static architecture, traceability, live
conformance enforcement, and recovered runtime structure.

This section answers the next stronger question from
`operator/cre/project_understanding/PHD_PATH_REVALIDATION.md`:

**Given the architecture now visible in both code and traces, which quality
scenarios matter most, what risks and tradeoffs do they expose, and what should
the repo do next?**

This section uses a QAW/ATAM-style method rather than a generic review.

## 2. Research Basis

- SEI's Quality Attribute Workshop supports surfacing architecturally significant
  requirements as concrete scenarios rather than vague quality goals.
- SEI's ATAM supports evaluating architecture through sensitivity points,
  tradeoffs, risks, and non-risks across competing quality attributes.
- ISO/IEC/IEEE 42010 supports tying views to stakeholder concerns rather than
  treating architecture description as a file inventory.
- `operator/cre/project_understanding/POST_CONFORMANCE_NEXT_MOVE_PHD.md`
  established that this is the correct move after the planner/executor
  conformance gate exists.

## 3. Evidence Base

This evaluation is grounded in the current local repository state.

### 3.1 Corpus evidence used

- `operator/cre/project_understanding/MASTER_PHD_ARCHITECTURE_BRIEF.md`
- `operator/cre/project_understanding/SECTION_4_CONFORMANCE_ENFORCEMENT.md`
- `operator/cre/project_understanding/SECTION_5_DYNAMIC_EXECUTION_ARCHITECTURE.md`
- `operator/cre/project_understanding/RUNTIME_FLOWS.md`
- `operator/cre/project_understanding/SUBSYSTEM_DEPENDENCY_REPORT.md`
- `operator/cre/project_understanding/POST_CONFORMANCE_NEXT_MOVE_PHD.md`

### 3.2 Fresh local validation

Observed on March 5, 2026:

- `UnifiedActionSpace.conformance_report()` now reports:
  - `missing_handler_actions = []`
  - `hidden_actions = ['login_flow']`
- host readiness for URL-driven tasks reports all required substrate classes
  ready
- the architecture conformance tool is now green with:
  - `enforcement_passed = true`
  - no blocking failures
  - monitored debt only for frozen shim imports and facade imports

Interpretation:

- the planner/executor contract is now truthful by default
- the runtime substrate is available on this machine
- architecture governance is back to a stable enforced baseline

### 3.3 Runtime evidence already established in Section 5

- 56 complete run directories were analyzed
- outcome split:
  - 42 `success`
  - 12 `failure`
  - 2 `error`
- runtime evidence showed:
  - control-loop-heavy execution
  - implicit verification inside oracle-backed `sleep`
  - manifest and trace outcomes can disagree
  - universal and enterprise families have materially different flow shapes

This matters because the strongest scenarios should be drawn from the live
runtime, not invented from the abstract architecture alone.

## 4. Stakeholders, Concerns, and Views

| Stakeholder | Main concerns | Views and evidence that answer them |
| --- | --- | --- |
| Runtime engineer | recovery reliability, handler behavior, substrate readiness | Runtime flows, dynamic execution architecture, action handlers, recovery |
| Architecture maintainer | boundary integrity, orchestration sprawl, modifiability | subsystem report, conformance enforcement, master architecture brief |
| Evaluation researcher | benchmark validity, verification semantics, outcome truth | dynamic execution architecture, verification gate, benchmark evaluator |
| Security reviewer | sanitization boundary, credential release, HITL scope | security modules, auth workflow, architecture brief |
| Incident debugger | root-cause clarity, evidence completeness, causal chains | trace writer, diagnostic reader, visual monitor, DDG, manifests |
| Future extender | adding sites/capabilities without spreading special cases | agent.py, action space, capability router, site knowledge, action handlers |

## 5. Utility Tree

| Quality attribute | Priority | Why it is high or low | Key scenarios | Current fit |
| --- | --- | --- | --- | --- |
| Observability and diagnosability | Very high | this repo is a research platform and must explain failures, not only execute | S1, S2 | Mixed |
| Recoverability and reliability | Very high | the runtime is built around retries, recovery, and self-healing | S3, S4 | Mixed to strong |
| Modifiability and boundary integrity | Very high | the repo is still evolving from benchmark harness to universal agent | S5, S8 | Weak to mixed |
| Assurance and security clarity | High | sensitive auth and tool-poisoning boundaries must remain explicit | S6 | Strong to mixed |
| Performance and cost efficiency | High | verification and routing costs can dominate longer tasks | S4, S7 | Mixed |
| Scientific validity of evaluation | Very high | benchmark claims are only useful if outcome semantics are trustworthy | S1, S7 | Mixed |
| Learning and memory governance | High | skills, site knowledge, and trust skipping can silently overfit | S7 | Mixed |

## 6. Ranked Scenario Set

The scenarios below are ranked by architectural importance, not by ease.

### S1. Root-cause clarity when run outcome and step outcome diverge

**Quality attribute:** observability and scientific validity

**Stimulus:** a run finishes with `manifest.json` reporting failure or success,
but the step-level trace does not cleanly agree.

**Environment:** real enterprise or universal run after partial retries or
implicit verification steps.

**Desired response:** the architecture should preserve enough structured evidence
for a human or agent to explain the true failure or acceptance boundary without
replaying the task.

**Response measure:**
- root cause should be derivable from trace, manifest, and artifacts without
  ambiguity
- run-level outcome, step-level outcome, and verification outcome should be
  machine-correspondent

**Architectural approaches involved:**
- `TraceWriter`
- `DiagnosticReader`
- `DecisionDependenceAnalyzer`
- `VerificationGate`
- `BenchmarkEvaluator`

**Evidence:**
- Section 5 found runs that fail at manifest level without failed trace steps
- Section 5 also found successful runs containing failed steps

**Current judgment:** weak to mixed

This is the highest-value scenario because it directly affects diagnosis,
benchmark validity, and future verification calibration.

### S2. Explain a complex failure quickly from the evidence stack

**Quality attribute:** diagnosability

**Stimulus:** a multi-step run partially succeeds, partially recovers, and then
terminates with ambiguous state.

**Environment:** debugger or outer-loop agent inspects an existing run
directory.

**Desired response:** the architecture should support quick causal explanation
through progressive disclosure rather than requiring raw trace spelunking.

**Response measure:**
- a debugger should localize the failure family and likely root cause quickly
- evidence should align across trace, DDG, monitor timeline, and verification

**Architectural approaches involved:**
- `DiagnosticReader`
- `DecisionDependenceAnalyzer`
- `VisualMonitor`
- `OuterLoop`

**Evidence:**
- the repo already has unusually strong evidence infrastructure
- Section 5 also shows evidence semantics are not perfectly unified

**Current judgment:** mixed

This is stronger than a normal logging scenario because the repo is intended to
support scientific diagnosis and self-healing.

### S3. Recover safely from GUI obstruction or state contamination

**Quality attribute:** recoverability and reliability

**Stimulus:** an unexpected dialog, focus theft, stale coordinate replay, or
contaminated canvas state appears during execution.

**Environment:** live GUI task with recovery enabled.

**Desired response:** the architecture should detect the obstruction, attempt
bounded recovery, and avoid compounding the error with unsafe actions.

**Response measure:**
- the run should either recover or fail with an explicit diagnosis
- retries should remain bounded and interpretable
- recovery should not silently cross into unsafe action territory

**Architectural approaches involved:**
- `Recovery`
- `ActionContracts`
- `ActionAllowlist`
- `VisualMonitor`
- `HostToolHealth`

**Evidence:**
- the dynamic execution corpus is control-loop heavy
- recovery is a core architectural assumption, not a fallback afterthought

**Current judgment:** mixed to strong

This is one of the system’s better-supported scenarios, but it remains highly
sensitive to effect checks, verification policy, and site-specific handlers.

### S4. Hold assurance while keeping long tasks economically viable

**Quality attribute:** assurance versus cost and latency

**Stimulus:** a long or repetitive task triggers many verification opportunities.

**Environment:** enterprise or universal run with trust skipping, final
verification, and model routing enabled.

**Desired response:** the architecture should preserve meaningful assurance while
reducing unnecessary expensive checks.

**Response measure:**
- skipped checks should remain justified by confidence policy
- final verification should still provide an authoritative outcome boundary
- latency and model cost should remain bounded relative to task complexity

**Architectural approaches involved:**
- `ActionTrustTracker`
- `VerificationGate`
- `Recovery`
- `InferenceRouter`

**Evidence:**
- Section 5 found verification encoded partly in explicit steps and partly in
  oracle-backed `sleep`
- the repo already acknowledges trust-skipped verification paths

**Current judgment:** mixed

This is a genuine tradeoff zone rather than a simple bug surface.

### S5. Add or change site-specific behavior without spreading special cases

**Quality attribute:** modifiability

**Stimulus:** a new site capability, new task family, or changed site behavior
must be supported.

**Environment:** active development in the universal agent path.

**Desired response:** the architecture should permit change through bounded site
adapters rather than broad edits across orchestrator, planner, handlers, and
benchmark harnesses.

**Response measure:**
- new site work should touch a small and predictable set of files
- site-specific logic should not keep accreting inside the universal
  composition root

**Architectural approaches involved:**
- `agent.py`
- `CapabilityRouter`
- `UnifiedActionSpace`
- `SiteKnowledge`
- `ActionHandlers`

**Evidence:**
- the architecture brief already identified `agent.py` as carrying too much
  site-specific normalization logic
- the legacy harness remains a second orchestration center

**Current judgment:** weak

This is the repo’s clearest structural evolution pressure.

### S6. Handle credentialed workflows without boundary ambiguity

**Quality attribute:** security and assurance

**Stimulus:** a site presents an authentication or sensitive-action surface with
mixed benign and suspicious cues.

**Environment:** universal web task involving forms, submission, or secrets.

**Desired response:** the architecture should sanitize inputs, classify the auth
surface, keep credentials out of traces/prompts, and require approval when
necessary.

**Response measure:**
- secret release paths remain explicit
- HITL gating remains predictable
- tool or prompt poisoning does not silently alter the policy boundary

**Architectural approaches involved:**
- `InputSanitizer`
- `CredentialVault`
- `HITLGuard`
- `auth_workflow`

**Evidence:**
- the security subsystem is intentionally narrow and explicit
- the architecture brief already treated this as a strength

**Current judgment:** strong to mixed

The security boundary is comparatively well-shaped, but it still depends on
clear integration with recovery and fallback behavior.

### S7. Reuse skills, site knowledge, and trust without silent overfitting

**Quality attribute:** learning governance and scientific validity

**Stimulus:** a previously successful task family is retried on a changed site
or slightly different goal.

**Environment:** runs with `SkillLibrary`, `SiteKnowledge`, and
`ActionTrustTracker` enabled.

**Desired response:** the architecture should exploit prior success without
letting stale memory silently dominate new conditions.

**Response measure:**
- reuse should be freshness-aware and reversible
- failures caused by stale reuse should remain diagnosable
- trust should decay or reset appropriately when site behavior changes

**Architectural approaches involved:**
- `SkillLibrary`
- `SiteKnowledge`
- `ActionTrustTracker`
- `OuterLoop`

**Evidence:**
- the repo is explicitly stateful across runs
- trust skipping and master-skill reuse are core optimizations

**Current judgment:** mixed

This is a high-value long-term scenario because the repo increasingly depends on
cross-run memory for efficiency.

### S8. Preserve architectural boundaries during rapid iteration

**Quality attribute:** modifiability and governance

**Stimulus:** a developer adds a convenient import or helper to solve a local
problem quickly.

**Environment:** active iteration across planning, execution, and infrastructure
code.

**Desired response:** the architecture should either reject reverse-layer
coupling or force it to appear through explicit boundary adapters and decisions.

**Response measure:**
- architecture conformance should remain green unless a justified boundary
  change is explicitly accepted
- new coupling should be visible immediately

**Architectural approaches involved:**
- architecture conformance enforcement
- subsystem model
- boundary adapters

**Evidence:**
- the current live conformance check is green, but still tracks bounded shim and
  facade debt that must not grow

**Current judgment:** mixed

This remains a live governance pressure even after the reverse-layer edge repair.

## 7. Sensitivity Points

The following points have outsized influence across multiple scenarios.

### SP1. Outcome semantics and trace schema

If run outcome, step outcome, and verification outcome are not aligned, then
diagnosis, benchmarking, and calibration all weaken at once.

Affected scenarios:
- S1
- S2
- S4
- S7

### SP2. Verification boundary design

The line between cheap checks, expensive checks, trust skipping, and final
verification directly shapes reliability, latency, and confidence.

Affected scenarios:
- S3
- S4
- S7

### SP3. Location of site-specific logic

The more site-specific compilation and normalization remain in `agent.py` and
mixed handler tables, the harder controlled change becomes.

Affected scenarios:
- S5
- S8

### SP4. Boundary adapter discipline

If reverse-layer imports are tolerated informally, the architecture model stops
being a stable decision tool.

Affected scenarios:
- S5
- S8

### SP5. Memory freshness and invalidation

Skill reuse, trust skipping, and site knowledge are valuable only if stale
reuse remains visible and bounded.

Affected scenarios:
- S4
- S7

## 8. Tradeoffs

| Tradeoff | Side A | Side B | Why it matters here |
| --- | --- | --- | --- |
| Assurance vs. cost | more checks, stronger confidence | fewer checks, lower latency and cost | this repo verifies frequently and also tries to become efficient |
| Recovery aggressiveness vs. safety | more autonomous repair | lower risk of compounding error | the runtime is explicitly recovery-oriented |
| Generality vs. site competence | universal abstractions | site-specific optimizations | the repo is transitioning away from benchmark-specific roots |
| Observability richness vs. overhead | denser traces and artifacts | leaner runs and simpler tooling | the project is both a runtime and a research instrument |
| Fast iteration vs. architectural integrity | convenience imports and local fixes | explicit adapters and cleaner layering | current conformance evidence shows this is a live pressure |

## 9. Ranked Risk Themes

| Rank | Risk theme | Why it is ranked here | Current evidence |
| --- | --- | --- | --- |
| 1 | fragmented outcome semantics | it undermines diagnosis, benchmarking, and verification interpretation simultaneously | manifest/trace mismatches and implicit verification paths |
| 2 | site-specific logic concentration | it raises the cost of extension and makes the universal path less universal | `agent.py` normalization burden and duplicated orchestration |
| 3 | reverse-layer architectural erosion | it weakens the value of the conformance model itself | historically observed reverse-layer edges plus still-frozen shim/facade debt |
| 4 | verification-policy ambiguity | it affects both reliability and cost | trust skipping and implicit verification semantics |
| 5 | stale memory reuse | it can create silent overconfidence on changed sites | persistent skills, trust, and site knowledge |
| 6 | security-boundary drift through fallback or recovery | lower probability but high consequence | sensitive workflows must remain explicit across runtime paths |

## 10. Non-Risks And Strengths

The evaluation also identifies several areas that are currently strengths rather
than pressing weaknesses.

- explicit host-readiness gating is strong
- the planner/executor contract is now truthful by default
- the evidence stack is unusually rich for an experimental agent system
- the security subsystem is comparatively narrow and disciplined
- the repo already has the right conceptual machinery for diagnosis and learning

## 11. Decision

### 11.1 Best substantive next move after this evaluation

The highest-leverage next architecture move is:

**formalize and unify outcome semantics across trace steps, manifest outcome,
and verification outcome**

Why this wins:

- it directly addresses the top-ranked risk theme
- it improves diagnosis, benchmark validity, and future verification calibration
- it sharpens the meaning of success, failure, recovery, and acceptable partial
  success across execution families

Concretely, that should mean:

- explicit outcome taxonomy for step, run, and final verification
- explicit correspondence rules between trace and manifest
- removal of ambiguous success/failure interpretation where possible
- scenario-aware evaluation hooks for later benchmarks and judges

### 11.2 Governance requirement while that work proceeds

The repo should keep the architecture conformance gate green while outcome
semantics work proceeds.

This remains important because bounded shim and facade debt are still frozen by
policy. The architecture baseline is now stable, but it still needs to stay
that way during the larger substantive change.

## 12. Follow-On Actions

Recommended order after this section:

1. formalize unified outcome semantics and artifact correspondences
2. calibrate `VerificationGate` and related effect checks against human judgment
3. extract or harden a bounded site-adaptation layer outside the universal
   orchestration root
4. add a scenario-to-test and scenario-to-artifact coverage map

## 13. What This Section Changes In The Overall Corpus

- the corpus now includes an actual evaluation view, not only description and
  recovery views
- the next move is no longer generic “do scenario evaluation”
- the next move is now specific:
  - keep architectural layering green
  - unify outcome semantics as the highest-leverage substantive change

## 14. Usage

Read this section when you need:

- the stakeholder and concern structure for architecture work
- a ranked utility tree
- explicit scenario pressure for design decisions
- the strongest evidence-based next move after scenario evaluation

## 15. Primary Sources

- Quality Attribute Workshop Collection: https://www.sei.cmu.edu/library/the-sei-quality-attribute-workshop/
- Architecture Tradeoff Analysis Method Collection: https://www.sei.cmu.edu/library/architecture-tradeoff-analysis-method-collection/
- ISO/IEC/IEEE 42010 overview: https://www.iso-architecture.org/ieee-1471/
- Why Architecture Conformance Matters for Evolvable Systems: https://www.sei.cmu.edu/library/why-architecture-conformance-matters/
