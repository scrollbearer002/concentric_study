# Post-Conformance Next Move (PhD)

**Date:** March 5, 2026

## 1. Research Question

Now that the planner/executor conformance gate exists and the live contract gap
has been closed, what is the strongest next PhD-level move for `concentric_study`?

This memo answers that question for the live repository, not just for the
documentation corpus.

## 2. Short Answer

The next best move is:

**run a scenario-based architecture evaluation using a QAW/ATAM-style method**

In practice, that means:

- define the highest-value quality scenarios for the real system
- evaluate the current architecture against those scenarios
- identify sensitivity points, tradeoffs, and risk themes
- use that analysis to choose the next refactors and evaluations

This is now the right move because the strongest known contract defect has
already been turned into an executable regression gate.

## 3. Local Facts

### 3.1 The previous highest-priority gap is now closed

The recent conformance work changed the sequencing.

Current local evidence:

- `UnifiedActionSpace.conformance_report()` now reports:
  - `missing_handler_actions = []`
  - `hidden_actions = ['login_flow']`
- planner-visible actions: `32`
- total catalog actions: `33`

Interpretation:

- the planner-visible runtime surface is now truthful by default
- the one hidden catalog action is intentionally non-planner-visible
- the architecture no longer has the same first-order planner/executor mismatch

### 3.2 The corpus already anticipated this transition

Two earlier memos converge here:

- `NEXT_BEST_MOVE_PHD.md` explicitly says that **once the conformance gate exists**
  the next move becomes scenario-based architecture evaluation
- `PHD_PATH_REVALIDATION.md` identifies Step C as scenario-based evaluation after
  conformance enforcement and dynamic execution recovery

So the current recommendation is not a reversal. It is the next step in the
already-supported sequence.

## 4. Why This Is The Right Method Now

The external research is unusually consistent on this point.

### 4.1 SEI QAW

The Quality Attribute Workshop is designed to surface architecturally
significant requirements as concrete scenarios. That is exactly what this repo
needs next, because the remaining uncertainty is no longer basic interface
truthfulness. It is tradeoff structure.

### 4.2 SEI ATAM

ATAM is the right follow-on because it evaluates architecture through quality
attribute scenarios, architectural approaches, sensitivity points, tradeoffs,
and risks. That is the correct method when the question becomes:

- which subsystem boundary matters most next?
- which refactors are actually worth the cost?
- where are the main reliability, security, and modifiability risks?

### 4.3 Conformance literature

SEI conformance guidance argues that once model/code drift is made explicit, the
next step is not blind cleanup. It is disciplined evaluation and controlled
evolution. That fits the repo’s current state exactly.

### 4.4 Recent agent-evaluation literature

Recent web-agent work continues to show that strong-looking results can mask
evaluation artifacts when the setup is insufficiently realistic. For this repo,
the post-conformance question is therefore not “add more benchmark prose.” It is
“evaluate the architecture under realistic quality scenarios before selecting the
next code and evaluation investments.”

## 5. What This Move Would Actually Do

If executed well, a QAW/ATAM-style pass would do six things for `concentric_study`.

### 5.1 Convert architecture knowledge into decision pressure

Right now the repo has strong descriptions, traces, conformance checks, and
runtime views. Scenario evaluation converts that understanding into a ranked
decision structure.

### 5.2 Prioritize refactors by quality impact

Instead of asking “what looks messy?”, the repo can ask:

- which changes most improve recoverability?
- which changes most improve observability?
- which changes most reduce security ambiguity?
- which changes most reduce cost and latency without weakening assurance?

### 5.3 Expose true tradeoffs

This repo has real cross-pressure:

- verification strength vs. latency/cost
- recovery aggressiveness vs. safety
- site-specific adaptation vs. universal abstraction
- richer monitoring vs. operational overhead
- reusable skills/trust skipping vs. stale overconfidence

Scenario evaluation makes those tradeoffs explicit instead of leaving them as
intuitions spread across docs and code.

### 5.4 Focus later experiments

It will identify which empirical studies matter next:

- verification-gate calibration
- perception failure taxonomy
- benchmark validity work
- site-adapter/modularity studies

### 5.5 Improve architectural discipline

A utility tree and scenario set become a stable basis for later design reviews,
ADRs, and conformance checks. That raises the repo from “well-documented” to
“decision-governed.”

### 5.6 Make future refactors defensible

If a refactor follows a scenario evaluation, the justification is much stronger:

- stimulus
- environment
- response
- response measure
- architectural approaches affected
- risk/tradeoff rationale

That is PhD-level decision structure, not taste-driven cleanup.

## 6. The Right Scenario Families For This Repo

The strongest scenarios are not generic web-app scenarios. They should be drawn
from the system’s actual failure and design pressures.

### 6.1 Recoverability under GUI obstruction

Example:
- repeated unexpected dialogs
- canvas state contamination
- modal focus theft
- stale coordinate replay

Question:
- can the architecture recover without creating unsafe or opaque behavior?

### 6.2 Observability and root-cause clarity

Example:
- a run fails after several partially successful actions
- the trace, DDG analysis, monitor history, and verification result disagree

Question:
- can a human or agent determine root cause quickly and confidently?

### 6.3 Security boundary clarity during credentialed workflows

Example:
- a site presents mixed benign and suspicious authentication affordances
- fallback or recovery paths cross into sensitive action territory

Question:
- are sanitization, credential release, and HITL boundaries explicit enough?

### 6.4 Verification strength vs. cost/latency

Example:
- frequent post-action verification plus final verification on long tasks
- trust skipping and routing reduce cost but may weaken assurance

Question:
- where is the right architecture boundary between cheap checks, expensive
  checks, and mandatory checks?

### 6.5 Modifiability of site adaptation

Example:
- adding or changing a site-specific plan normalizer or handler family

Question:
- how much of the codebase must change to support new sites or retire old
  benchmark-specific behavior?

### 6.6 Reliability of learning and memory reuse

Example:
- skills, site knowledge, or action trust improve repeated performance on one
  task family but silently bias later runs

Question:
- does the architecture contain stale-memory risk strongly enough?

## 7. Why This Beats The Other Plausible Next Moves

### 7.1 Better than broad refactoring

Refactoring now would still be underdetermined. The repo needs ranked scenario
pressure first so the refactor target is evidence-based.

### 7.2 Better than adding more external tools first

`Structurizr`, `Langfuse`, `Phoenix`, `Playwright`, and related tools may help,
but they do not decide which architecture questions matter most. Scenario work
does.

### 7.3 Better than verification calibration as the immediate next step

Verification calibration is likely the strongest empirical study after scenario
evaluation, but scenario work should choose how urgent that study is relative to:

- recovery architecture
- site-modularity
- security-boundary clarity
- observability weaknesses

### 7.4 Better than benchmark expansion first

The recent literature warns against over-interpreting agent benchmark progress.
Architecture scenarios are a stronger next move because they test the system’s
design pressures directly rather than only expanding scoreboards.

## 8. What The Evaluation Should Produce

The minimal strong output is:

1. a stakeholder/concern/viewpoint matrix
2. a quality-attribute utility tree
3. 8-12 ranked concrete scenarios
4. architectural approaches mapped to each scenario
5. identified sensitivity points, tradeoffs, risks, and non-risks
6. a ranked list of follow-on actions

For this repo, the likely follow-on actions after that evaluation are:

- targeted architecture refactors
- verification-gate calibration against human judgment
- selected security-assurance work
- selected benchmark-validity work

## 9. Decision

### Context

- the planner/executor conformance gate is now live
- the strongest previously-known executable drift has been contained
- the architecture corpus already includes static recovery, dynamic execution,
  and conformance views
- the remaining high-value uncertainty is architectural tradeoff structure

### Decision

The next PhD-level move should be:

**a QAW/ATAM-style scenario-based architecture evaluation of the live system**

### Consequences

- Positive: refactors become ranked and defensible
- Positive: later empirical studies become easier to prioritize
- Positive: architecture work advances from description into evaluation
- Trade-off: this is slower than jumping straight into code changes
- Trade-off: it demands disciplined scenario formulation rather than generic review

## 10. Primary Sources

- SEI Quality Attribute Workshop Collection: https://www.sei.cmu.edu/library/the-sei-quality-attribute-workshop/
- SEI Architecture Tradeoff Analysis Method Collection: https://www.sei.cmu.edu/library/architecture-tradeoff-analysis-method-collection/
- SEI Why Architecture Conformance Matters for Evolvable Systems: https://www.sei.cmu.edu/library/why-architecture-conformance-matters/
- WebVoyager (ACL 2024): https://aclanthology.org/2024.acl-long.371/
- OSWorld benchmark site: https://os-world.github.io/
- An Illusion of Progress? Assessing the Current State of Web Agents: https://arxiv.org/abs/2504.01382
