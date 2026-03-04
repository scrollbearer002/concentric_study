# Context-Locked Research Filter (PhD)

## Purpose
This protocol prevents a research loop from improving an answer with **credible but irrelevant** information.

It exists because stronger sources are not sufficient by themselves. For a source to improve an answer, it must be both:
1. **credible**
2. **in-bounds for the current environment, domain, task, and success criteria**

This is the missing layer above a normal recursive research loop.

## Core Problem
Without a context lock, a model can drift into adjacent domains and still sound intelligent.

Example:
- user environment: `soccer team`
- task: `how to become the best player on this team`
- drifted research: basketball team dynamics, spelling bee practice, generic leadership advice

That is not low-quality information in general. It is **low-value evidence for the current system-of-interest**.

## Main Conclusion
The correct way to prevent this is to run a **Context-Locked Research Filter** before and during recursive research.

The filter should force the model to explicitly define:
- the system-of-interest
- the domain
- the environment
- the target user/stakeholder
- the task objective
- the success criteria
- the excluded adjacent domains

Then every source and every claim must be tested against that frame before it is allowed to influence the answer.

## Research Basis
### 1. Good prompting requires explicit contextual information
Anthropic's prompt engineering guidance explicitly states that models perform better when given contextual information such as the workflow, end goal, audience, and what success looks like.

Implication here:
- the model must be told not only the question, but also the environment in which the answer must operate.

Source:
- Anthropic, Be clear, direct, and detailed: https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/be-clear-and-direct

### 2. Structured context improves correctness
Anthropic recommends structured prompts with explicit tagged sections for context, instructions, and other task components.

Implication here:
- context should not be implicit in a paragraph of prose; it should be encoded as a formal research frame.

Source:
- Anthropic, Use XML tags to structure your prompts: https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/use-xml-tags

### 3. Long-context quality depends on organizing documents and grounding answers in the right evidence
Anthropic's long-context guidance recommends clear document structure and grounding responses in the relevant quoted material.

Implication here:
- large context alone is not enough; the system must distinguish relevant context from surrounding noise.

Source:
- Anthropic, Long context prompting tips: https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/long-context-tips

### 4. Retrieval quality depends on intent extraction and removal of irrelevant background context
Google's Re-Invoke work explicitly highlights online intent extraction that filters irrelevant background context during tool retrieval.

Implication here:
- before retrieval or research, the system should strip away background material that is not part of the core task intent.

Source:
- Google Research blog, Re-Invoke: Tool invocation rewriting for zero-shot tool retrieval: https://research.google/blog/re-invoke-tool-invocation-rewriting-for-zero-shot-tool-retrieval/

### 5. Query generation improves when search intent is explicit and task-adaptive
Task-adaptive retrieval research shows that explicit search intent improves retrieval quality across non-trivial task types.

Implication here:
- the research loop should not search only from the user's surface wording; it should first compile the request into task-adaptive search intent.

Source:
- Disentangling Questions from Query Generation for Task-Adaptive Retrieval (2024): https://arxiv.org/abs/2409.16570

### 6. Relevance must be assessed, not assumed
Relevance-aware RAG research shows that retrieved context can mislead if the system cannot assess whether it is actually relevant and useful.

Implication here:
- every candidate source should be scored not just for authority, but for direct relevance to the defined environment and task.

Source:
- REAR: A Relevance-Aware Retrieval-Augmented Framework for Open-Domain Question Answering (EMNLP 2024): https://aclanthology.org/2024.emnlp-main.321/

### 7. Sufficient context matters more than merely related context
Google Research's sufficient-context work shows that relevant context is not the same thing as sufficient context.

Implication here:
- a source can be on-topic yet still be insufficient for the current task. The loop should detect and reject this case.

Sources:
- Google Research blog, sufficient context: https://research.google/blog/deeper-insights-into-retrieval-augmented-generation-the-role-of-sufficient-context/
- Google Research publication page: https://research.google/pubs/sufficient-context-a-new-lens-on-retrieval-augmented-generation-systems-2/

### 8. Domain adaptation matters because methods do not transfer cleanly across environments
Retrieval and ranking work repeatedly shows that models and retrieval methods degrade when moved to out-of-domain settings.

Implication here:
- evidence from adjacent domains should be treated as analogical support at best, not direct evidence, unless the transfer case is justified.

Sources:
- Domain Adaptation for Dense Retrieval and Conversational Dense Retrieval through Self-Supervision by Meticulous Pseudo-Relevance Labeling (LREC-COLING 2024): https://aclanthology.org/2024.lrec-main.467/
- Relevance-aware Diverse Query Generation for Out-of-domain Text Ranking (RepL4NLP 2024): https://aclanthology.org/2024.repl4nlp-1.3/
- BERM: Training the Balanced and Extractable Representation for Matching to Improve Generalization Ability of Dense Retrieval (2023): https://arxiv.org/abs/2305.11052

### 9. Retrieval should not be invoked indiscriminately
Recent agentic context work argues that indiscriminate retrieval saturates context with irrelevant noise.

Implication here:
- the research loop should retrieve selectively and refine only where a context gap exists.

Source:
- To Retrieve or To Think? An Agentic Approach for Context Evolution (2026): https://arxiv.org/abs/2601.08747

## The Protocol
This filter runs **before** and **during** the Recursive PhD Research Loop.

### Phase 0: Define the Research Frame
Before any research, explicitly fill these fields:

- `system_of_interest`
- `domain`
- `environment`
- `task`
- `stakeholder`
- `success_criteria`
- `allowed_source_domains`
- `excluded_adjacent_domains`
- `transfer_rules`

Example:
- `system_of_interest`: Reddit publishing product
- `domain`: Reddit workflows, Reddit policy, software productization
- `environment`: customer-facing Reddit automation product
- `task`: define product boundary and delivery model
- `stakeholder`: software-buying engineering team
- `success_criteria`: professional Reddit-only product package
- `excluded_adjacent_domains`: generic social media growth hacks, unrelated browser bots

### Phase 1: Compile the question into search intent
Rewrite the user request into a narrow search-intent object.

Required fields:
- `core_intent`
- `must_have_terms`
- `must_not_drift_into`
- `primary_source_types`
- `scope_limits`

This prevents the system from researching broad neighbors of the problem instead of the problem.

### Phase 2: Source admissibility filter
A source is admissible only if it passes all three checks:

1. **Credibility**
- primary source, official docs, standards body, or strong peer-reviewed research when appropriate

2. **Relevance**
- directly informs the current domain/environment/task

3. **Usefulness**
- changes or constrains the answer in a meaningful way

If a source is credible but irrelevant, reject it.
If a source is relevant but weak, mark it low-confidence.

### Phase 3: Claim-level tagging
Every claim in the answer must be tagged as one of:
- `direct_in_domain_support`
- `direct_environment_support`
- `analogical_support`
- `background_only`
- `out_of_bounds`

Rules:
- `direct_in_domain_support`: evidence from the same task/domain
- `direct_environment_support`: evidence from the actual operating environment
- `analogical_support`: adjacent-domain evidence used only as analogy
- `background_only`: useful framing, not operational proof
- `out_of_bounds`: should not influence the answer

### Phase 4: Drift check during recursive review
After each revision pass, ask:
- Did I introduce a source outside the defined domain?
- Did I let adjacent-domain evidence act like direct proof?
- Did I strengthen the answer with information that does not help the system-of-interest?
- Did I answer the general version of the question instead of the situated version?

If yes, remove or demote that evidence.

### Phase 5: Context-saturation stopping rule
The research loop stops only when both conditions are true:

1. **Evidence saturation**
- no stronger source changes the answer

2. **Context fidelity**
- no additional in-bounds source materially improves the answer within the defined environment and task frame

This is stricter than ordinary saturation.

## Transfer Rules
Transfer from adjacent domains is allowed only when explicitly justified.

Use this hierarchy:
1. same system and same task
2. same domain and similar task
3. adjacent domain with explicit transfer reasoning
4. remote domain only as weak analogy

Never let level 3 or 4 evidence override level 1 or 2 evidence.

## Prompt Template
Use this when you want context-locked recursive research:

```text
Use a Context-Locked Recursive PhD Research Loop.

First define the research frame:
- system_of_interest
- domain
- environment
- task
- stakeholder
- success_criteria
- excluded_adjacent_domains
- transfer_rules

Then answer the question using only in-bounds sources.
Treat your first answer as a draft.
After the first draft:
1. Critique it for weak claims, unsupported inferences, stale assumptions, and domain drift.
2. Re-research only the weak or drift-prone parts using stronger in-bounds primary sources.
3. Revise the answer.
4. Repeat until a full pass produces no material improvement from stronger in-bounds evidence.

For every important claim, mark whether it is:
- direct_in_domain_support
- direct_environment_support
- analogical_support
- background_only
- out_of_bounds

Do not let adjacent-domain evidence act as direct proof.
Do not optimize for generic correctness; optimize for correctness within the defined environment and task.

Stop only when:
- no stronger in-bounds primary source changes the answer
- no claim status changes
- no recommendation changes materially
- no new in-bounds risk, boundary, or implementation step is discovered

In the final output include:
- the final answer
- the research frame
- what changed after recursive review
- why you stopped
- what would reopen the loop
```

## Best Practice for This Repo
In `concentric_study`, combine this with `operator/cre/PHD_DECISION_PRACTICE.md` and `operator/cre/RECURSIVE_PHD_RESEARCH_LOOP.md`.

Order:
1. define context and system-of-interest
2. write facts/context first
3. make the draft answer
4. critique for evidence weakness and context drift
5. re-research only in-bounds gaps
6. stop at context-aware evidence saturation

## Bottom Line
What you want is **situated research**, not generic research.

The best answer is not the answer supported by the most impressive pile of sources.
It is the answer supported by the strongest **relevant** sources for the exact environment, system, and objective you care about.
