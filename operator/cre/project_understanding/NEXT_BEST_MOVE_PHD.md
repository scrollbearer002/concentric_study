# Next Best Move (PhD)

**Date:** March 6, 2026

## 1. Research Question

Given the current state of `concentric_study`, what is the single best next move,
and what would it actually accomplish?

This memo answers that question at the level of the live repository, not just
the architecture corpus and not just external tool adoption.

## 2. Short Answer

The next best move is:

**implement an executable action-space conformance gate at the planner/executor boundary**

That means:
- make the declared planner-visible action vocabulary provably dispatchable
- make non-dispatchable actions fail in tests immediately
- align `action_space.py`, `research_agent.py`, and `action_handlers.py`
- only after that, move to scenario-based architecture evaluation

This is the best next move because it reduces the clearest live correctness gap
in the system and increases the validity of almost every later activity:
- planning
- recovery
- verification
- benchmarking
- architecture evaluation
- refactoring

## 3. Local Facts

The repository already contains two relevant sequencing claims.

### 3.1 The architecture corpus says the active next step is scenario-based evaluation

`operator/cre/project_understanding/PHD_PATH_REVALIDATION.md` says the next step
after conformance enforcement and dynamic execution recovery is:

- `Step C: scenario-based architecture evaluation`

That remains correct for the architecture corpus as a documentation and analysis program.

### 3.2 The live runtime surface reveals a more immediate executable gap

`operator/cre/project_understanding/MASTER_PHD_ARCHITECTURE_BRIEF.md` records the
strongest current live issue:

- semantic/runtime drift between the declared action vocabulary and the live dispatcher

The concrete evidence is visible in:

- `operator/action_space.py`
- `operator/agent_infra/research_agent.py`
- `operator/agent_infra/action_handlers.py`

Observed current mismatch:

- `UnifiedActionSpace` declares `33` action names
- `ACTION_HANDLERS` exposes `33` dispatchable keys
- but `9` planner-visible mappings still target handler keys that are not present in the live dispatcher

Examples:
- `type -> type_text`
- `draw_shape -> draw_shape`
- `go_back -> go_back`
- `bmw_details -> bmw_details`
- `bmw_shading -> bmw_shading`

This is not merely a documentation gap.
It is an executable contract gap.

## 4. Why This Beats The Other Candidate Next Moves

The other plausible candidates are:

1. scenario-based architecture evaluation
2. ADR/tool adoption work
3. verification calibration
4. perception failure taxonomy
5. broad refactoring

The literature and the repo both argue that these should come after the action-space contract is made executable.

### 4.1 Why not scenario-based evaluation first?

SEI QAW and ATAM are strongest when the architecture under evaluation already has
a stable contract surface. In this repo, one of the highest-priority candidate
scenarios is already:

- planner/executor mismatch during fallback action selection

If that mismatch is already known and concretely observable, then the strongest
next move is to close or gate it before using larger scenario work to decide
refactors. Otherwise scenario evaluation partly rediscovers a known unresolved defect.

### 4.2 Why not new tools first?

`MADR`, `Semgrep`, `Structurizr`, `Langfuse`, and `Playwright` are all useful,
but none of them directly resolves the current truth gap between:

- what the planner is told is legal
- what the executor can actually do

New tooling before contract repair would improve discipline around a still-misaligned runtime.

### 4.3 Why not verification calibration first?

Verification calibration matters, but a judge can only evaluate the outputs it sees.
If planning can emit or validate actions that are not truly executable, then some
evaluation variance is upstream of the judge rather than inside it.

### 4.4 Why not refactor first?

Architecture conformance literature is explicit: once drift is measured, the next
move is enforcement and containment, not broad cleanup. Refactoring first would
change the surface while the contract is still under-specified.

## 5. Research Basis

### 5.1 Architecture conformance and source/model agreement

Software Reflexion Models and SEI conformance guidance support this move directly.

Why:
- the system already has a high-level model of legal actions
- the live code already has a lower-level executable model
- the strongest next move is to make disagreement between those models explicit and testable

### 5.2 Scenario-based architecture evaluation sequencing

SEI QAW/ATAM guidance supports scenario evaluation after the model and conformance
surface are trustworthy enough to analyze.

Why:
- scenario evaluation is strongest when it compares tradeoffs, not when it is still
  discovering whether the primary interface contract exists

### 5.3 Agent evaluation realism

Recent web-agent work also supports fixing the contract before leaning harder on evaluation.

Why:
- recent benchmark literature shows that agent progress can look better than it is
  when the evaluation setup is overly convenient or insufficiently realistic
- a planner/executor mismatch is exactly the kind of hidden validity problem that
  can distort conclusions

## 6. What The Next Move Would Do

If implemented well, the action-space conformance gate would do six important things.

### 6.1 It would make planning honest

The planner would no longer be told that an action is available unless the runtime
can dispatch it.

### 6.2 It would make fallback planning safer

`research_agent.py` currently emits fallback actions such as `draw_shape` and
`go_back` in contexts where the live dispatcher does not expose those keys.
Closing that gap would reduce silent degradation during recovery and fallback.

### 6.3 It would turn semantic drift into a regression, not a latent risk

A failing test would prevent new planner vocabulary from landing unless it is:

- dispatchable
- intentional
- covered by contract or alias logic

### 6.4 It would improve benchmark validity

If the planner vocabulary and executor vocabulary are aligned, benchmark outcomes
are less contaminated by hidden interface mismatch.

### 6.5 It would make later architecture evaluation more meaningful

Once the planner/executor contract is real, scenario-based evaluation can focus on:

- recoverability
- observability
- security tradeoffs
- performance/cost tradeoffs

instead of rediscovering a basic contract mismatch.

### 6.6 It would reduce refactor risk

Refactors after contract hardening are safer because the repo has a smaller number
of implicit assumptions left in the runtime boundary.

## 7. What Implementation Should Contain

The minimal strong version of this move is:

1. one authoritative conformance test comparing `UnifiedActionSpace` against `ACTION_HANDLERS`
2. explicit alias policy for intentional renamed actions
3. stricter `ResearchAgent` validation so Phase 3 does not approve actions that are not dispatchable
4. an action coverage table showing which actions have:
   - dispatcher support
   - effect checks or contracts
   - benchmark coverage
   - trace semantics
5. a decision on each currently mismatched action:
   - add handler
   - rename mapping
   - remove from planner surface
   - reclassify as non-runtime/internal

## 8. What Comes Immediately After

Once the conformance gate exists, the next best move becomes:

**scenario-based architecture evaluation**

At that point, the strongest scenarios are:

- planner/executor mismatch under fallback and recovery
- verification disagreement on ambiguous visual outputs
- repeated GUI obstruction and recovery cost
- stale site knowledge after interface drift
- security-boundary clarity during auth workflows

So the sequence is:

1. executable action-space conformance gate
2. scenario-based architecture evaluation
3. verification calibration
4. perception failure taxonomy

## 9. Decision

### Context

The repo already has:
- architecture conformance enforcement for module boundaries
- a dynamic execution architecture view
- rich traces and run artifacts
- a clearly identified semantic/runtime drift at the planner/executor boundary

### Decision

The best next move is to harden the action-space contract before expanding tooling,
refactoring, or broad scenario work.

### Consequences

- Positive: removes the clearest live correctness gap
- Positive: improves trustworthiness of later evaluation
- Positive: creates a regression gate rather than a one-time cleanup
- Trade-off: it is less glamorous than new tools or large refactors
- Trade-off: it may require pruning or renaming planner-visible actions that were previously tolerated

## 10. Primary Sources

- SEI Quality Attribute Workshop: https://www.sei.cmu.edu/library/the-sei-quality-attribute-workshop/
- SEI Architecture Tradeoff Analysis Method Collection: https://www.sei.cmu.edu/library/architecture-tradeoff-analysis-method-collection/
- Murphy et al., Software Reflexion Models: https://www.cs.ubc.ca/~murphy/papers/rm/fse95.html
- SEI Why Architecture Conformance Matters: https://www.sei.cmu.edu/library/why-architecture-conformance-matters/
- SEI Architecture Reconstruction Guidelines: https://www.sei.cmu.edu/library/architecture-reconstruction-guidelines-third-edition/
- WebVoyager: https://aclanthology.org/2024.acl-long.371/
- OSWorld official benchmark site: https://os-world.github.io/
- An Illusion of Progress? Assessing the Current State of Web Agents: https://arxiv.org/abs/2504.01382
- REAL: Benchmarking Autonomous Agents on Deterministic Simulations of Real Websites: https://arxiv.org/abs/2504.11543
- AgentRewardBench: Evaluating Automatic Evaluations of Web Agent Trajectories: https://arxiv.org/abs/2504.08942
