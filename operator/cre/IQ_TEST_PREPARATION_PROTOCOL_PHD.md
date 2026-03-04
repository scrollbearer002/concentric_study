# IQ Test Preparation Protocol (PhD)

## Environment Basis
This protocol is specific to the live `concentric_study` repo on `/Users/christianpardo/Desktop/concentric_study`, this machine's Safari workflow, and the actual prior IQ-test artifacts in `operator/cre/IQ_TEST_LIVE_RUN_LOG.md`. It is not a generic study guide. It is a bounded performance protocol for the next live IQ-test run so the system improves its mistakes without degrading the current strong runtime.

## Executive Summary
The strongest conclusion from the evidence is that the prior poor automated IQ-test results were driven less by lack of raw reasoning capacity and more by the wrong operating mode:

1. the Mensa run optimized completion, not reasoning
2. the 123test cursor-guided run optimized visible demonstration, not correctness
3. the repo had no explicit per-item reasoning protocol, confidence tracking, or revisit discipline

For the next IQ test, the system should use a reasoning-first, evidence-logged, untimed-or-low-time-pressure protocol built around:
- constructive matching before option hunting
- explicit self-explanation of the rule
- confidence labeling
- revisit of uncertain items
- accuracy over speed when time pressure is absent

## Local Evidence From Prior Runs
### Run 1: Mensa Norway
Evidence: `operator/cre/IQ_TEST_LIVE_RUN_LOG.md`

Observed:
- rapid page progression through many items
- no recorded per-item reasoning trace
- final result: `Your score is below 100`
- the site itself warns browser/plugin conditions can distort scoring

Interpretation:
- the run was a browser-task completion success, not a valid reasoning-quality benchmark
- the operating mode was effectively "answer and advance" rather than "reason, verify, commit"

### Run 2: Zolly Darko untimed branch
Evidence: `operator/cre/IQ_TEST_LIVE_RUN_LOG.md`

Observed:
- explicit untimed site selection
- answers were filled and submitted
- raw result recorded separately in chat, but the repo log still lacks item-level reasoning evidence

Interpretation:
- this was directionally better than the timed Mensa run because time pressure was reduced
- but the protocol still lacked explicit reasoning capture and uncertainty management

### Run 3: 123test cursor-guided branch
Evidence: `operator/cre/IQ_TEST_LIVE_RUN_LOG.md`

Observed:
- the primary goal shifted toward visible cursor demonstration
- eight question answers were clicked through successfully
- the flow reached a demographic/results shell rather than a clean score capture

Interpretation:
- the run tested visible control more than psychometric performance
- correctness was subordinated to demonstration constraints

## Directly Supported Repo Diagnosis
The main mistakes were:
1. **completion over reasoning**
2. **no explicit per-question rule extraction**
3. **no structured confidence calibration**
4. **no revisit discipline**
5. **score-demonstration tradeoff left implicit**

These are operational mistakes, not proof of low reasoning capacity.

## External Research and What It Means Here
### 1. Intelligence matters, but it is not the dominant controllable lever
- Roth et al. (2015), meta-analysis of intelligence and school grades:
  https://www.sciencedirect.com/science/article/pii/S0160289615001269
- Lozano-Blasco et al. (2022), systematic review/meta-analysis:
  https://pubmed.ncbi.nlm.nih.gov/36547510/

Why it matters here:
- raw reasoning ability helps
- but the repo can actually improve faster by fixing process variables than by arguing about IQ labels

### 2. Self-regulation and conscientiousness are major predictors of performance
- Zimmerman (2002), self-regulated learning:
  https://doi.org/10.1207/S15430421TIP4102_2
- Poropat (2009), conscientiousness and academic performance:
  https://pubmed.ncbi.nlm.nih.gov/19254083/
- Mammadov (2022), Big Five and performance:
  https://pubmed.ncbi.nlm.nih.gov/34265097/

Why it matters here:
- the best immediate gain is to force planning, monitoring, and revision into the test run itself

### 3. Retrieval and self-explanation improve learning and reasoning quality
- Roediger & Karpicke (2006), test-enhanced learning:
  https://pubmed.ncbi.nlm.nih.gov/16507066/
- Dunlosky et al. (2013), effective learning techniques:
  https://pubmed.ncbi.nlm.nih.gov/26173288/

Why it matters here:
- before choosing an answer, the system should articulate the transformation rule from memory/current observation instead of jumping to options

### 4. Active learning and high-quality feedback matter
- Freeman et al. (2014), active learning meta-analysis:
  https://pubmed.ncbi.nlm.nih.gov/24821756/
- Wisniewski, Zierer, & Hattie (2020), feedback:
  https://pubmed.ncbi.nlm.nih.gov/32038429/

Why it matters here:
- the next test should generate item-level evidence that can be reviewed afterward, not just a final score screenshot

### 5. Matrix reasoning benefits from constructive matching and strategic visual search
- Gonthier & Thomassin (2015), strategy use on Raven's matrices:
  https://pubmed.ncbi.nlm.nih.gov/25844240/
- Vigneau et al. (2006), cognitive/response strategy in matrix reasoning:
  https://pubmed.ncbi.nlm.nih.gov/16750606/
- Laurence et al. (2025), eye-movement dynamics on visual matrices:
  https://pubmed.ncbi.nlm.nih.gov/40330965/

Why it matters here:
- for matrix-style IQ items, the system should inspect the matrix first, infer the rule, and only then inspect answer options
- this is a concrete correction to the prior click-first behavior

### 6. Speed-accuracy tradeoff should be handled explicitly
- classic speed-accuracy tradeoff literature and decision science support this principle; in this repo the actionable implication is simple:
  - if the test is untimed or low-pressure, optimize for accuracy, not rapid completion

Why it matters here:
- the Mensa run implicitly chose speed
- the next run should only do that if the site enforces strong time pressure and there is no revisit path

### 7. Sleep/attention affect performance enough to matter operationally
- Chan et al. (2023), sleep and academic performance:
  https://pubmed.ncbi.nlm.nih.gov/37079951/

Why it matters here:
- the next IQ run should not be treated as a casual filler task if the goal is score quality
- cognitive state is part of the environment

## Mistake-to-Countermeasure Map
### Mistake 1: Completion was prioritized over reasoning
Countermeasure:
- introduce a hard pre-answer reasoning step
- no answer click until a candidate rule is stated

### Mistake 2: Option selection happened before matrix structure was understood
Countermeasure:
- use constructive matching:
  1. inspect row/column/shape rule
  2. predict missing pattern
  3. only then compare options

### Mistake 3: No uncertainty tracking
Countermeasure:
- each item gets a confidence label:
  - high
  - medium
  - low
- if revisit is available, low-confidence items are revisited once after the first pass

### Mistake 4: No score-vs-demo distinction
Countermeasure:
- define the run mode before starting:
  - `score_mode`
  - `demo_mode`
- if `score_mode`, visible cursor flourish is subordinate to correctness
- if `demo_mode`, the result is not interpreted as an ability estimate

### Mistake 5: No item-level evidence for postmortem review
Countermeasure:
- per question, log:
  - prompt type
  - inferred rule
  - selected answer
  - confidence
  - reason for elimination of alternatives (brief)

## Next-Test Operating Protocol
### Mode Declaration
Before the test starts, explicitly declare one:
- `score_mode`: maximize correctness
- `demo_mode`: maximize visible cursor demo while keeping reasonable correctness

Default for the next IQ test should be:
- `score_mode`

### Preflight
1. Prefer untimed or weakly timed test
2. Safari full screen
3. Stable session and page load
4. No parallel task switching
5. Start the item ledger

### Per-Question Loop
For each question:
1. Inspect the problem before the answers
2. State a candidate rule or transformation
3. Predict the missing output
4. Compare answer options against the prediction
5. Select answer only after rule-to-option mapping exists
6. Assign confidence: high / medium / low
7. Log the result

### Revisit Rule
If the test allows review:
- revisit all `low` confidence items once
- do not churn endlessly
- one clean revisit pass only

### Stop Rule
Stop and log a special event if:
- the site prevents stable rendering
- interaction mode changes unexpectedly
- the system is forced into demo behavior that compromises score validity

## Minimal Repo-Safe Implementation Recommendation
This should be implemented as a **run protocol**, not a runtime rewrite.

Recommended near-term additions:
1. a per-item IQ reasoning ledger template
2. explicit `score_mode` vs `demo_mode` declaration in the run log
3. a question-loop checklist for matrix tests
4. optional confidence summary at end of run

This is safer than changing core interaction code just to chase a better IQ score.

## What This Does Not Claim
This protocol does **not** claim:
- that IQ tests are a full measure of intelligence
- that one retest will produce a "true" score
- that better protocol eliminates all browser or site artifacts
- that this repo should be optimized around psychometric benchmarking

It claims only:
- the previous runs made identifiable process mistakes
- those mistakes are correctable
- the strongest evidence-backed improvement is a reasoning-first protocol for the next run

## References
1. Roth, B. et al. (2015). Intelligence and school grades: A meta-analysis. Intelligence.
   https://www.sciencedirect.com/science/article/pii/S0160289615001269
2. Lozano-Blasco, R. et al. (2022). Types of Intelligence and Academic Performance: A Systematic Review and Meta-Analysis.
   https://pubmed.ncbi.nlm.nih.gov/36547510/
3. Zimmerman, B. J. (2002). Becoming a Self-Regulated Learner.
   https://doi.org/10.1207/S15430421TIP4102_2
4. Poropat, A. E. (2009). Personality and academic performance.
   https://pubmed.ncbi.nlm.nih.gov/19254083/
5. Mammadov, S. (2022). Big Five personality traits and academic performance.
   https://pubmed.ncbi.nlm.nih.gov/34265097/
6. Roediger, H. L., & Karpicke, J. D. (2006). Test-enhanced learning.
   https://pubmed.ncbi.nlm.nih.gov/16507066/
7. Dunlosky, J. et al. (2013). Effective learning techniques.
   https://pubmed.ncbi.nlm.nih.gov/26173288/
8. Freeman, S. et al. (2014). Active learning increases student performance.
   https://pubmed.ncbi.nlm.nih.gov/24821756/
9. Wisniewski, B., Zierer, K., & Hattie, J. (2020). The Power of Feedback Revisited.
   https://pubmed.ncbi.nlm.nih.gov/32038429/
10. Gonthier, C., & Thomassin, N. (2015). Strategy use and fluid intelligence.
   https://pubmed.ncbi.nlm.nih.gov/25844240/
11. Vigneau, F. et al. (2006). Strategy and matrix reasoning performance.
   https://pubmed.ncbi.nlm.nih.gov/16750606/
12. Laurence, P. G. et al. (2025). Eye movement patterns in visual matrix tasks.
   https://pubmed.ncbi.nlm.nih.gov/40330965/
13. Chan, N. Y. et al. (2023). Sleep and academic performance.
   https://pubmed.ncbi.nlm.nih.gov/37079951/
