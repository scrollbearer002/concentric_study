# Visual Reasoning Enhancement Plan (PhD)

Environment basis: this plan is specific to the live `concentric_study` repo on `/Users/christianpardo/Desktop/concentric_study`, the actual FreeWWW IQ-test run recorded in `operator/cre/IQ_TEST_LIVE_RUN_LOG.md`, the saved visual puzzle artifacts under `operator/cre/iq_test_freewww_q*/`, and the current local visual stack in `operator/visual_engine.py`, `operator/element_map.py`, `operator/web_primitives.py`, `operator/agent_infra/research_agent.py`, `operator/agent_infra/site_knowledge.py`, `operator/agent_infra/verification_gate.py`, and `operator/agent_infra/benchmark_evaluator.py`.

## Executive Summary

The live score profile does **not** justify broad changes to the project. The score profile identifies two bounded weak spots:

- `Pattern Recognition`: `6/8`
- `Spatial Reasoning`: `6/8`

The repo is already strong at:

- logical/sequential reasoning
- mathematical transformation
- verbal classification
- mechanical browser control
- screenshot capture and grid grounding

The project is weaker at:

- **relation-heavy matrix completion**
- **2D/3D spatial transformation**
- **explicit visual hypothesis tracking**
- **confidence-aware revisit of uncertain visual items**

The correct enhancement is therefore **not** “make the whole agent smarter.” It is to add an **isolated visual-reasoning branch** above the current strong perception/execution stack.

## Local Evidence

### Live result

From `operator/cre/IQ_TEST_LIVE_RUN_LOG.md`:

- `IQ 135`
- `36/40 correct`
- `Pattern Recognition: 6/8`
- `Spatial Reasoning: 6/8`
- `Logical Reasoning: 8/8`
- `Mathematical Ability: 8/8`
- `Verbal Skills: 8/8`

This means the gain target is already sharply localized.

### Saved weak-family artifacts

The current repo already contains visual captures of the relevant weak item families:

- relation-heavy matrix completion:
  - `operator/cre/iq_test_freewww_q29/montage.png`
- 3D projection / top-view reasoning:
  - `operator/cre/iq_test_freewww_q32/montage.png`
- box-net folding:
  - `operator/cre/iq_test_freewww_q25/montage.png`
- shape-to-solid mapping:
  - `operator/cre/iq_test_freewww_q30/montage.png`

These are enough to seed a bounded local benchmark branch without another external dependency.

## Current Repo Strengths and Gaps

### What already exists

The repo already provides strong lower layers:

- screenshot and SoM grounding:
  - `operator/visual_engine.py:18`
  - `operator/visual_engine.py:115`
- fused element map:
  - `operator/element_map.py:71`
  - `operator/element_map.py:126`
- semantic web primitives:
  - `operator/web_primitives.py:68`
  - `operator/web_primitives.py:95`
  - `operator/web_primitives.py:120`
- research-time context construction:
  - `operator/agent_infra/research_agent.py:93`
  - `operator/agent_infra/site_knowledge.py:101`
- visual verification and claims evaluation:
  - `operator/agent_infra/verification_gate.py:88`
  - `operator/agent_infra/benchmark_evaluator.py:152`

### What is missing

The current repo lacks an explicit visual-reasoning layer for puzzles that require:

1. **family recognition**
   - matrix completion
   - rotation/reflection
   - counting progression
   - net folding
   - projection/top view

2. **visual scratchpad state**
   - what rule is being tested
   - what alternatives remain alive
   - why an option is rejected

3. **confidence-aware revisit**
   - the current protocol memo recommends this, but the runtime has no dedicated structure for it

4. **task-family benchmark claims**
   - current benchmark machinery is strong, but it has no dedicated IQ/visual-reasoning claim family

## What the strongest external research says

### 1. Matrix reasoning improves when rule induction is explicit

Carpenter, Just, and Shell’s cognitive account of Raven’s matrices argues that high performance depends on inducing and managing explicit transformation rules, not only pattern familiarity.

Reference:
- Carpenter, Just, & Shell (1990), *What one intelligence test measures: A theoretical account of the processing in the Raven Progressive Matrices Test.*
  - https://pubmed.ncbi.nlm.nih.gov/2394421/

Why it matters here:
- the repo should not treat matrix problems as raw image matching
- it should extract candidate transformation rules explicitly

### 2. Strategy choice affects matrix performance

Gonthier and Thomassin show that Raven-style performance depends strongly on the strategy used, especially analytic strategy use.

Reference:
- Gonthier & Thomassin (2015), *Strategy use fully mediates the relationship between working memory capacity and performance on Raven's matrices.*
  - https://pubmed.ncbi.nlm.nih.gov/25844240/

Why it matters here:
- the improvement lever is not “more compute”
- it is better **strategy structure**

### 3. Eye-movement work supports structured scan paths

Recent matrix-task work supports the value of deliberate visual scan structure rather than option-hunting first.

Reference:
- Laurence et al. (2025), matrix-task eye-movement work
  - https://pubmed.ncbi.nlm.nih.gov/40330965/

Why it matters here:
- the repo should add an explicit scan policy:
  - inspect matrix first
  - derive rule
  - only then compare options

### 4. Spatial skills are trainable

Uttal et al. show that spatial skills are malleable and training transfers across tasks more than older folklore assumed.

Reference:
- Uttal et al. (2013), *The malleability of spatial skills: A meta-analysis of training studies.*
  - https://pubmed.ncbi.nlm.nih.gov/23875923/

Why it matters here:
- weaker spatial categories are not fixed
- a bounded training branch is justified

### 5. Modern abstract visual reasoning benchmarks are relation-centric

The strongest AI-side evidence does not model these tasks as generic screenshot clicking. It models them as relation and rule inference problems.

References:
- Barrett et al. (2018), *Measuring Abstract Reasoning in Neural Networks*
  - https://arxiv.org/abs/1807.04225
- Zhang et al. (2019), *RAVEN: A Dataset for Relational and Analogical Visual REasoNing*
  - https://arxiv.org/abs/1903.02741
- Santoro et al. (2017), *A simple neural network module for relational reasoning*
  - https://arxiv.org/abs/1706.01427
- Chollet (2019), *On the Measure of Intelligence* / ARC framing
  - https://arxiv.org/abs/1911.01547

Why they matter here:
- the missing branch should emphasize:
  - relation extraction
  - rule families
  - option elimination by contradiction
- not just more pixel capture

## Repo-Safe Enhancement Direction

### Recommended branch name

`visual_reasoning_support`

### What this branch should do

Add a narrow layer with four responsibilities:

1. **Puzzle-family classification**
   - matrix progression
   - rotation/reflection
   - count/shape progression
   - net folding
   - projection/top-view

2. **Visual reasoning scratchpad**
   - predicted rule
   - candidate transformations
   - rejected options and reasons
   - confidence score

3. **Confidence-aware revisit**
   - revisit only low-confidence visual items once
   - preserve the current successful score-mode protocol

4. **Local visual benchmark fixtures**
   - reuse the saved `iq_test_freewww_q*/montage.png` artifacts
   - add a fixture dataset and a claims-based evaluator

## Exact implementation shape for this repo

### New isolated module

Recommended new module:

- `operator/agent_infra/visual_reasoning_support.py`

Why here:
- it sits above the current visual stack
- it does not replace `VisualGroundingEngine` or `WebPrimitives`
- it can remain optional and task-family-scoped

### New data structures

Recommended records:

- `PuzzleFamily`
- `VisualHypothesis`
- `OptionElimination`
- `VisualReasoningResult`

### New flow

For visual reasoning tasks only:

1. capture or load puzzle montage
2. classify puzzle family
3. apply family-specific reasoning template
4. produce option ranking
5. assign confidence
6. if confidence low and revisit is allowed, mark for one revisit pass

## What should NOT be changed

Do **not**:

- rewrite `operator/visual_engine.py`
- replace `element_map.py`
- weaken `web_primitives.py`
- merge this branch into every task family
- make strong universality claims yet

This should remain a bounded branch because the current runtime is already strong at the lower layers.

## Minimal first taxonomy

The first version should support only these families:

1. `matrix_progression`
2. `rotation_reflection`
3. `count_shape_progression`
4. `net_folding`
5. `projection_top_view`

This is enough to cover the actual weak items evidenced in the live run.

## Benchmark and verification implications

This repo already has benchmark and verification infrastructure. The bounded enhancement should use it.

Recommended additions:

- visual-reasoning task claims in `BenchmarkEvaluator`
- fixture-based acceptance checks
- confidence distribution logging
- low-confidence revisit rate

Suggested claim family:

- `check_visual_family_classified`
- `check_rule_hypothesis_generated`
- `check_option_elimination_logged`
- `check_confidence_recorded`
- `check_low_confidence_revisit_applied`

## Best next implementation order

### Phase 1
- add `PuzzleFamily` classifier
- add scratchpad schema
- add fixture loader for saved montages

### Phase 2
- add family-specific templates for:
  - matrix progression
  - net folding
  - projection/top view

### Phase 3
- integrate confidence/revisit protocol

### Phase 4
- run against the saved IQ artifacts, not live websites first

### Phase 5
- only then replay on a new external untimed IQ test

## Why this is the strongest move

This branch satisfies the current repo rules:

- it is evidence-backed by a real live run
- it targets a specific weakness
- it does not interfere with the strong current runtime
- it builds on existing artifact, verification, and benchmarking patterns

## Final Recommendation

For `concentric_study`, the strongest improvement path is:

1. keep the current score-mode protocol
2. preserve the strong existing runtime
3. add an isolated `visual_reasoning_support` branch
4. start with the exact weak families already evidenced by the live test
5. prove it locally on saved puzzle artifacts before any broader claims

That is the most scientifically coherent and project-safe way to improve the weak spots revealed by the IQ run.
