# Environment Justification Gate (PhD)

## Executive Summary
This memo defines the strongest repo-local enforcement pattern for making answers stay environment-specific in `concentric_study`.

The conclusion is:
- a prose rule alone is not enough
- the strongest practical mechanism is a **locked, human-authored pre-final-answer gate**
- that gate should require the agent to justify each answer against the actual:
  - system of interest
  - local machine/runtime environment
  - repo architecture
  - task context
  - stakeholder objective
- if those anchors are missing, the answer should fail closed and say so

This is the right design for this repo because the project is highly environment-dependent:
- macOS GUI agent
- Cursor/Safari control
- Quartz/Cocoa event injection
- AppleScript/System Events
- accessibility and screen-capture permissions
- repo-specific architecture and artifact conventions

A generic answer can be technically strong and still wrong for this environment.

## Local Problem
Current repo state:
- `.cursor/rules/concentric-study.mdc` already encodes:
  - serious-by-default
  - recursive PhD research loop
  - context-locked research filter
- but prose rules alone still leave room for under-enforcement
- the practical failure mode is not missing research skill
- the practical failure mode is premature closure before the answer is explicitly tied back to this environment

The user requirement is stronger than “do more research.”
The requirement is:
- every answer should be justified against the actual local environment by default
- not only non-trivial implementation tasks
- not only when the user reminds the agent

## Research Frame
- `system_of_interest`: `concentric_study` and the local machine/workflow it operates in
- `domain`: environment-specific reasoning and enforcement for a macOS GUI-agent repo
- `environment`: Cursor on macOS arm64, Safari-based automation, repo-local rule stack
- `task`: choose the best enforcement design so answers stay environment-specific by default
- `stakeholder`: repo operator / builder who wants stronger answer discipline
- `success_criteria`: a repo-local mechanism that reduces generic answers and under-applied context grounding
- `excluded_adjacent_domains`: generic prompt tricks with no enforcement implications, unrelated education or creativity advice, abstract agent philosophy
- `transfer_rules`: adjacent-domain evidence is allowed only if it supports explicit context structuring, evaluation, verification, or rubric integrity

## Primary Sources
### Official guidance
1. Anthropic prompt engineering: be clear, direct, and detailed
- `https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/be-clear-and-direct`
- Supports: explicit context, workflow, goal, and success framing improve output quality.

2. Anthropic prompt engineering: use XML tags
- `https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/use-xml-tags`
- Supports: structured, explicitly separated context improves reliability and reduces cross-contamination between instructions.

3. Anthropic long-context prompting tips
- `https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/long-context-tips`
- Supports: grounded document organization matters; large context alone is insufficient.

4. OpenAI evaluation best practices
- `https://platform.openai.com/docs/guides/evaluation-best-practices`
- Supports: evaluation quality depends on explicit criteria and clearly defined success conditions.

### Research papers
5. Self-Refine
- `https://arxiv.org/abs/2303.17651`
- Supports: draft -> feedback -> revision improves outputs.

6. Chain-of-Verification
- `https://arxiv.org/abs/2309.11495`
- Supports: draft first, then verify the answer independently.

7. RubricBench
- `https://arxiv.org/abs/2603.01562`
- Supports: rubric quality matters; model-generated rubric behavior still trails stronger human-authored evaluation structures.

8. Rubrics as an Attack Surface
- `https://arxiv.org/abs/2602.13576`
- Supports: rubrics can drift or be manipulated; locked evaluation criteria are safer than fluid self-generated criteria.

9. Re-Invoke (Google Research)
- `https://research.google/blog/re-invoke-tool-invocation-rewriting-for-zero-shot-tool-retrieval/`
- Supports: explicit intent rewriting improves tool retrieval by filtering irrelevant context.

10. REAR relevance-aware RAG
- `https://aclanthology.org/2024.emnlp-main.321/`
- Supports: relevance must be assessed, not assumed.

## What Changed After Recursive Review
First-pass candidate answer:
- “Add a stronger reminder in the repo rules.”

Problems found in critique:
- too weak; still prose-only
- does not force pre-final-answer verification
- does not protect against criterion drift
- does not define fail-closed behavior when environment evidence is missing

Revised answer:
- add a **locked environment-justification gate**
- define a fixed, human-authored checklist
- require pre-final-answer pass/fail behavior
- explicitly separate `directly_supported`, `inferred`, and `unknown`
- require local inspection if environment evidence is missing

That is materially stronger than a simple wording change.

## Design Options Evaluated
### Option A. Stronger prose reminder only
Description:
- keep adding stronger wording to the existing rules

Strengths:
- low effort

Weaknesses:
- does not force a pre-final-answer check
- easy to under-apply
- no explicit fail-closed behavior

Verdict:
- insufficient

### Option B. Model-generated rubric every time
Description:
- let the model generate a fresh environment-specific rubric per answer

Strengths:
- flexible

Weaknesses:
- rubric quality becomes unstable
- criteria can drift between answers
- weak protection against omission or self-serving grading

Verdict:
- insufficient as the primary enforcement layer

Research basis:
- RubricBench
- Rubrics as an Attack Surface

### Option C. Locked human-authored environment gate plus recursive critique
Description:
- keep the recursive research loop
- keep the context-locked research filter
- add a fixed environment-justification gate that runs before every final answer

Strengths:
- stable criteria
- explicit fail-closed behavior
- consistent across sessions
- compatible with the current repo rule stack
- supports both short and long answers

Weaknesses:
- adds discipline overhead
- still relies on the agent to execute the gate honestly unless additional external auditing is added later

Verdict:
- best current design for this repo

## The Gate
Before finalizing any answer, the agent must silently check:

1. `system_of_interest`
- what exact system is being discussed?

2. `local_environment`
- what machine/runtime/app environment is relevant here?
- if unknown but discoverable, inspect first

3. `repo_specific_constraints`
- what files, architecture, conventions, or artifacts constrain the answer?

4. `task_and_stakeholder`
- what exact task is being solved and for whom?

5. `evidence_status`
- which parts are:
  - `directly_supported`
  - `inferred`
  - `unknown`

### Fail-closed rule
If the gate cannot be satisfied:
- do not present the answer as definitive
- say what environment evidence is missing
- say how that limits the recommendation
- if possible, inspect the local environment before answering

## Why This Is Best for This Repo
`concentric_study` is unusually environment-bound.

Examples:
- the same answer can be right on macOS and wrong on Windows
- the same Cursor guidance can be right for one version and wrong for another
- the same repo advice can be wrong if it ignores the local architecture or artifact conventions
- the same GUI-agent advice can be wrong if it ignores accessibility and screenshot permissions

Therefore the best enforcement layer is one that explicitly forces answers back through the actual local environment rather than a generic category-level answer.

## Repo-Local Implementation
Implemented artifacts:
- rule update in `.cursor/rules/concentric-study.mdc`
- this memo: `operator/cre/ENVIRONMENT_JUSTIFICATION_GATE_PHD.md`
- reusable checklist prompt: `operator/cre/artifacts/environment_justification_gate_template.txt`

## Recommended Operator Interpretation
The repo should treat the gate as:
- mandatory by default
- short for simple answers
- fuller for serious planning, architecture, research, or productization work

The gate is not meant to make every answer verbose.
It is meant to make every answer **situated**.

## Double-Check Revision
A second-pass review found one remaining weakness in the first implementation:
- the gate could still be applied silently, which makes compliance hard to audit from the outside

Correction adopted:
- non-trivial answers should include an explicit `Environment basis:` line or an equivalent clearly labeled statement
- if an answer is intentionally abstract, that relaxation should be stated explicitly

Why this change matters:
- it converts the gate from a hidden internal discipline into a visible answer contract
- it gives the operator evidence that the gate actually ran
- it reduces the chance that a good internal check is skipped or only half-applied

## Stopping Rationale
A second critique-and-reresearch pass did not change the recommended enforcement pattern.
The stronger answer remained:
- locked human-authored gate
- fail-closed behavior
- environment inspection when missing evidence is discoverable

So this answer is currently evidence-saturated for the present repo and source set.

## Reopen Conditions
Reopen this design if:
- the repo later gains an external answer-auditing mechanism
- the editor/runtime exposes native answer-schema enforcement
- a stronger primary source emerges showing a better enforcement pattern than locked human-authored checklists + explicit verification

## References
- Anthropic: be clear, direct, and detailed — `https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/be-clear-and-direct`
- Anthropic: use XML tags — `https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/use-xml-tags`
- Anthropic: long context prompting tips — `https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/long-context-tips`
- OpenAI evaluation best practices — `https://platform.openai.com/docs/guides/evaluation-best-practices`
- Self-Refine — `https://arxiv.org/abs/2303.17651`
- Chain-of-Verification — `https://arxiv.org/abs/2309.11495`
- RubricBench — `https://arxiv.org/abs/2603.01562`
- Rubrics as an Attack Surface — `https://arxiv.org/abs/2602.13576`
- Re-Invoke — `https://research.google/blog/re-invoke-tool-invocation-rewriting-for-zero-shot-tool-retrieval/`
- REAR — `https://aclanthology.org/2024.emnlp-main.321/`
