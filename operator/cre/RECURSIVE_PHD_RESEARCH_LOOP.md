# Recursive PhD Research Loop

## Purpose
This protocol forces the agent to treat its **first answer as a draft**, not a final answer. The agent must recursively re-evaluate its own output against stronger evidence until it reaches an explicit stopping condition.

This is the right method when you want:
- stronger primary-source grounding
- fewer early-answer omissions
- explicit separation of fact, inference, and unknowns
- a defensible stopping rule instead of endless vague "more research"

## Core Principle
The loop is not:
- "answer once"
- then maybe improve if the user asks again

The loop is:
1. answer
2. critique the answer
3. research what could invalidate or strengthen it
4. revise the answer
5. test whether the revision materially improved it
6. repeat until the evidence no longer changes the result

## Research Basis
### 1. Iterative self-refinement improves output quality
Self-Refine shows that a model can improve outputs by iteratively generating feedback and refining its own draft.
Source:
- Self-Refine (2023): https://arxiv.org/abs/2303.17651

### 2. Verification should be independent of the initial draft
Chain-of-Verification shows that after drafting, the system should plan verification questions and answer them independently before producing the final response.
Source:
- Chain-of-Verification (2023): https://arxiv.org/abs/2309.11495

### 3. Multiple reasoning paths reduce premature commitment
Self-Consistency shows that better answers often emerge when multiple reasoning paths are considered rather than committing to the first path.
Source:
- Self-Consistency Improves Chain of Thought Reasoning (2022): https://arxiv.org/abs/2203.11171

### 4. Reflection and episodic memory improve future decisions
Reflexion shows that explicit verbal reflection over prior attempts improves subsequent performance.
Source:
- Reflexion (NeurIPS 2023): https://openreview.net/forum?id=vAElhFcKW6

### 5. The loop still needs a stopping rule
Qualitative research uses saturation and sufficiency: stop when new passes no longer produce materially new analytical information.
Sources:
- Practical guidance to qualitative research: saturation/sufficiency: https://pmc.ncbi.nlm.nih.gov/articles/PMC5774281/
- Beyond the Guise of Saturation: Rigor and Qualitative Interview Data: https://pmc.ncbi.nlm.nih.gov/articles/PMC8527935/

## The Protocol
Use this exact sequence for any non-trivial research or planning task.

### Pass 0: Initial draft
- Answer the question using the best current evidence.
- Mark every claim as one of:
  - `directly_supported`
  - `inferred`
  - `unknown`
- Record the primary sources used.

### Pass 1: Adversarial self-critique
The agent must ask itself:
- What in my answer depends on weak or secondary sources?
- What could be outdated?
- What did I assume without proving?
- What are the strongest counterexamples or missing boundaries?
- What would an advanced reviewer challenge immediately?

Output of Pass 1:
- a defect list
- a missing-source list
- a claim-strength map

### Pass 2: Targeted re-research
Research only the defects found in Pass 1.
For each weak claim:
- look for stronger primary sources
- look for contradictory evidence
- look for scope/availability limits
- look for operational details that change the recommendation

### Pass 3: Revised answer
Revise the answer.
Every revision must state:
- what changed
- why it changed
- which stronger source caused the change

### Pass 4: Saturation check
Ask:
- Did this pass add any stronger primary sources?
- Did any claim status change?
- Did any recommendation change?
- Did any new non-trivial risk, exclusion, or dependency appear?

If **yes**, run another loop.
If **no**, stop.

## Stopping Rule
Stop only when a full critique-and-reresearch pass produces **all** of the following:

1. no stronger primary source replaces an existing source
2. no claim changes status
3. no recommendation changes materially
4. no new boundary, risk, or exclusion is discovered
5. no new practical experiment or implementation step is required

This is the correct operational meaning of "it cannot be enhanced further with the current evidence set."

## Hard Limits
To avoid fake certainty, the loop must also admit these realities:
- It can never prove global optimality.
- It can only prove **current evidence saturation** under the available source set and time budget.
- If new sources, new product state, or new user constraints appear, the loop reopens.

## Required Output Format
For any final answer produced under this loop, include:

### 1. Answer
The best current answer.

### 2. What changed after recursive review
A short list of corrections, upgrades, or tightened constraints.

### 3. Stopping rationale
A statement such as:
- "A second critique-and-reresearch pass did not change any claim status, recommendation, or primary source ranking, so the answer is currently evidence-saturated."

### 4. Reopen conditions
State what new information would justify another pass.

## Recommended Pass Budget
Default budget for non-trivial work:
- minimum: `2` full passes
- standard: `3` full passes
- high-stakes: loop until saturation, but require explicit evidence that the last pass made no material difference

## Prompt Template
Use this exact instruction block when you want this behavior:

```text
Use a Recursive PhD Research Loop.

Treat your first answer as a draft, not a final answer.
After producing the first draft:
1. Critique it aggressively for weak claims, missing primary sources, unsupported inferences, stale assumptions, and missing boundaries.
2. Re-research only those weaknesses using stronger primary sources.
3. Revise the answer.
4. Repeat this loop until a full critique-and-reresearch pass produces no material improvement.

Stop only when:
- no stronger primary source replaces an existing one
- no claim changes status
- no recommendation changes materially
- no new major risk, boundary, exclusion, or implementation step is discovered

In the final output, include:
- the final answer
- what changed after recursive review
- why you stopped
- what new information would reopen the loop

Do not present the first answer as final.
Do not stop just because you have one plausible answer.
Stop only at evidence saturation.
```

## Repo-Compatible Version
For this repository specifically, combine it with `operator/cre/PHD_DECISION_PRACTICE.md`:
- Facts / Context first
- Decision second
- Consequences third
- Then run the recursive critique-and-reresearch loop over that draft until saturation

## Bottom Line
What you want is not "ask again manually." What you want is a **recursive evidence-saturation protocol**.

That is the professional way to force stronger answers from the same system before it speaks as if it is done.
