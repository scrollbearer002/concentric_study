# What Other People Use to Master the Visual Branch (PhD)

Environment basis: this memo is specific to the live `concentric_study` repo on `/Users/christianpardo/Desktop/concentric_study`, the current weak branch identified by the live IQ/art runs (`operator/cre/IQ_TEST_LIVE_RUN_LOG.md`, `operator/cre/jspaint_polo_bear_panther_final.png`, `operator/cre/jspaint_polo_bear_panther_canvas.png`), and the current local stack in `operator/visual_engine.py`, `operator/element_map.py`, `operator/web_primitives.py`, `operator/agent_infra/research_agent.py`, `operator/agent_infra/site_knowledge.py`, `operator/agent_infra/verification_gate.py`, and `operator/agent_infra/benchmark_evaluator.py`.

## Executive Summary

People who get genuinely strong at the part of this project that is currently weak do **not** rely on a single trick. The strongest patterns split into five categories:

1. **Reference organization tools** for drawing and visual planning
2. **Explicit rule-induction strategies** for matrix/pattern problems
3. **Benchmark corpora and replay harnesses** for visual reasoning
4. **Structured scan / think-aloud protocols** for hard visual tasks
5. **Targeted spatial-training drills** instead of broad “get smarter” work

For `concentric_study`, the strongest transferable items are:

- a **reference-board layer** before art generation
- a **constructive-matching visual scratchpad** before answer selection
- a **local visual benchmark harness** using saved montage artifacts
- a **confidence + revisit protocol** for weak visual items

The wrong move would be a broad rewrite of the strong browser/runtime core. The right move is a bounded enhancement branch above it.

## Local Problem Definition

### Direct local evidence
From `operator/cre/IQ_TEST_LIVE_RUN_LOG.md`:
- `Pattern Recognition: 6/8`
- `Spatial Reasoning: 6/8`
- `Logical Reasoning: 8/8`
- `Mathematical Ability: 8/8`
- `Verbal Skills: 8/8`

From the drawing branch:
- initial JSPaint failure came from geometry misuse and weak pre-draw surface understanding, not basic cursor control
- corrected via `operator/cre/art_geometry.py` and live canvas-fit normalization

This means the weak area is not broad reasoning. It is:
- visual relation extraction
- spatial transformation
- reference-grounded composition
- pre-action visual planning

## What Other People Actually Use

## 1. Reference boards and mood boards

### What people use
Artists and designers commonly use dedicated reference-board tools to keep subject references, anatomy, clothing cues, silhouette studies, and palette references visible while working. The clearest official example is PureRef.

Primary source:
- PureRef official site: <https://www.pureref.com/>
- PureRef handbook: <https://www.pureref.com/handbook/>

Why it matters:
- it externalizes visual memory
- it reduces drift from “concept memory” to “reference-grounded drawing”
- it supports side-by-side comparison instead of freehand imagination

Repo-specific implication:
- `concentric_study` should not treat drawing prompts like “Ralph Lauren polar bear in Black Panther Party clothing” as sufficient by themselves
- it should assemble a **reference board** inside the run directory before the first stroke

Recommended local analog:
- `reference_board.json`
- `reference_board.md`
- saved reference images under `operator/cre/runs/<run_id>/reference_images/`

## 2. Constructive matching and explicit rule induction

### What people use
Visual-reasoning researchers do not solve Raven-style problems by immediately scanning answer options. They first infer the structure or transformation inside the source matrix. This strategy is often called **constructive matching**.

Primary sources:
- Carpenter, Just, & Shell (1990), Raven processing model: <https://pubmed.ncbi.nlm.nih.gov/2394421/>
- Development of reasoning performance in Raven's matrices is grounded in effective strategy use (2023): <https://pubmed.ncbi.nlm.nih.gov/38059964/>
- Intraindividual strategy shifts in Raven's matrices (2019): <https://pubmed.ncbi.nlm.nih.gov/31318256/>

Why it matters:
- the user-level weak area in this repo is exactly matrix/pattern/spatial reasoning
- the strongest research consensus is: infer the rule first, compare options second

Repo-specific implication:
- the visual-reasoning branch should include a scratchpad for:
  - row/column rule hypothesis
  - transformation family
  - rejected options
  - confidence

Recommended local analog:
- `VisualHypothesis`
- `OptionElimination`
- `PuzzleFamily`

## 3. Think-aloud / explicit reasoning trace

### What people use
A surprising amount of improvement on matrix reasoning comes from explicitly verbalizing the strategy instead of silently guessing.

Primary source:
- Fox & Charness (2010), thinking aloud improves Raven performance: <https://pubmed.ncbi.nlm.nih.gov/19657761/>

Why it matters:
- this maps directly to the repo’s existing strength in trace logging and structured reasoning
- it suggests the system should not just click an option; it should write down the inferred rule before committing

Repo-specific implication:
- use the trace as a first-class reasoning surface for visual problems
- add a visual item protocol:
  - inspect
  - state rule
  - predict answer
  - compare choices
  - commit

Recommended local analog:
- a `reasoning_trace` field in visual benchmark runs

## 4. Benchmark corpora and replay harnesses

### What people use
Researchers master visual reasoning by working against benchmark corpora, not anecdotal one-off examples.

Primary sources:
- RAVEN benchmark paper: <https://arxiv.org/abs/1903.02741>
- RAVEN official GitHub: <https://github.com/WellyZhang/RAVEN>
- Barrett et al. (2018), PGM-style abstract reasoning: <https://arxiv.org/abs/1807.04225>
- ARC Prize official site: <https://arcprize.org/>
- ARC-AGI benchmarking harness: <https://docs.arcprize.org/benchmarking-agent>
- ARC benchmarking repo: <https://github.com/arcprize/arc-agi-benchmarking>

Why it matters:
- these communities do not treat “I solved one visual problem” as mastery
- they use:
  - repeatable fixtures
  - scored corpora
  - replay harnesses
  - regression comparisons

Repo-specific implication:
- our saved IQ artifacts should become a local mini-benchmark
- the repo should evaluate visual reasoning the way it already evaluates architecture and runs: with replayable evidence

Recommended local analog:
- `operator/cre/visual_reasoning_fixtures/`
- `operator/cre/test_visual_reasoning_support.py`
- claim-based benchmark scoring for matrix/spatial families

## 5. Structured visual search

### What people use
High-performing visual reasoners use structured scan behavior. Art experts and strong matrix solvers do not look randomly.

Primary sources:
- Tallon et al. (2021), art skills and visual search: <https://pubmed.ncbi.nlm.nih.gov/33584470/>
- Laurence et al. (2025), eye-movement work on matrix reasoning: <https://pubmed.ncbi.nlm.nih.gov/40330965/>

Why it matters:
- this supports the idea that the system should scan the source problem systematically before option hunting
- it also supports mid-pass art verification: silhouette, proportion, composition, then detail

Repo-specific implication:
- add scan-order guidance for visual tasks:
  - global silhouette / matrix structure first
  - local option comparison second

## 6. Spatial-skills training, not generic “more IQ”

### What people use
When spatial performance is weak, the research does not recommend vague intelligence training. It recommends targeted spatial training.

Primary sources:
- Uttal et al. (2013), spatial skills are malleable: <https://pubmed.ncbi.nlm.nih.gov/23875923/>
- Haptic perception and vision-based spatial ability (2023): <https://pubmed.ncbi.nlm.nih.gov/38108595/>
- Focused multisensory anatomy observation and drawing (2019): <https://pubmed.ncbi.nlm.nih.gov/31705741/>

Why it matters:
- the weak categories in the live run were pattern + spatial, not logic/math/verbal
- training should therefore target:
  - rotation
  - reflection
  - net folding
  - projection/top view
  - real-object part decomposition

Repo-specific implication:
- the best next branch is a **visual-reasoning support** layer, not more general planning logic

## 7. Drawing from observation improves recall and accuracy

### What people use
People who draw well tend to use observation and drawing itself as a memory/analysis tool.

Primary sources:
- Drawing your way to an A (2023): <https://pubmed.ncbi.nlm.nih.gov/37118527/>
- Visual free recall and recognition in art students and laypeople (2025): <https://pubmed.ncbi.nlm.nih.gov/39078592/>
- MIT Press, *Drawing Thought*: <https://mitpress.mit.edu/9780262544320/drawing-thought/>

Why it matters:
- drawing is not only output; it is a way of inspecting structure
- that supports multi-pass drawing instead of single-pass symbolic icon drawing

Repo-specific implication:
- art generation should follow:
  1. reference board
  2. silhouette pass
  3. anatomy/costume pass
  4. detail/color pass
  5. verification after each pass

## What fits this project best

### High-fit transfers
1. **Reference board first**
- strongest fit for art branches
- leverages existing `ResearchAgent` concept
- low risk to strong runtime

2. **Constructive matching scratchpad**
- strongest fit for pattern/spatial problems
- aligns with trace-first repo culture

3. **Local visual fixture benchmark**
- strongest fit for disciplined improvement
- matches repo’s artifact-first evaluation style

4. **Confidence + revisit**
- low implementation risk
- useful for both IQ tasks and drawing verification

### Medium-fit transfers
5. **Structured scan protocol**
- useful, but should likely begin as a protocol or trace field before becoming hard logic

6. **Multisensory / haptic training analogs**
- interesting theoretically, but less immediate for the macOS web-agent runtime

### Low-fit or out-of-scope transfers
7. **Full universal visual mutation/creation engine**
- too large for current evidence
- risks weakening the strong existing runtime

## Recommended repo build path

### Step 1
Add a reference-board branch to the art workflow:
- `reference_board.json`
- `subject_brief.json`
- `part_list.json`
- `composition_plan.json`

### Step 2
Add `visual_reasoning_support.py` with:
- `PuzzleFamily`
- `VisualHypothesis`
- `OptionElimination`
- `confidence`

### Step 3
Create a local benchmark set from:
- `operator/cre/iq_test_freewww_q25/`
- `operator/cre/iq_test_freewww_q29/`
- `operator/cre/iq_test_freewww_q30/`
- `operator/cre/iq_test_freewww_q32/`

### Step 4
Use the benchmark evaluator to score:
- correct family classification
- correct rule hypothesis
- correct option
- confidence calibration

### Step 5
Only after that, replay on external sites again.

## Final Recommendation

If the question is “what do other people use to master this part?”, the answer is:

- artists use **reference boards** and multi-pass observational drawing
- reasoning researchers use **constructive matching**, **think-aloud**, and **benchmark corpora**
- serious engineering teams use **fixture suites**, **replay harnesses**, and **scored regressions**

For `concentric_study`, the best synthesis is:

- **ReferenceBoard + VisualHypothesis + LocalBenchmarkHarness**

That is the strongest in-bounds upgrade path.
