# PhD Path Revalidation

**Date:** February 28, 2026

## 0. Status Note

The sequence in this memo has partially completed:

- Step A was implemented in `operator/cre/project_understanding/SECTION_4_CONFORMANCE_ENFORCEMENT.md`
- Step B was implemented in `operator/cre/project_understanding/SECTION_5_DYNAMIC_EXECUTION_ARCHITECTURE.md`

The active next step is now Step C: scenario-based architecture evaluation.

## 1. Purpose

This memo answers a narrower question than the earlier external-validation memo:

**Given the corpus already built, are we moving along the strongest research-backed
path for repository understanding and architecture work, or should the next steps
be reordered?**

This is a sequencing memo, not just a bibliography memo.
Its job is to stop the project-understanding work from drifting into “more artifacts”
when the stronger literature would point to a different next move.

## 2. Source Quality Model

### Highest-confidence sources
- ISO/IEC/IEEE 42010
- SEI/CMU architecture documentation, reconstruction, and evaluation material
- established architecture/program-comprehension papers

### Medium-confidence sources
- recent repository-understanding and LLM-for-architecture papers
- useful for scale and synthesis, but not the sole basis for the core method

## 3. What The Current Corpus Already Did Correctly

### 3.1 Layered architecture documentation
**Assessment:** High confidence.

Supported by:
- ISO/IEC/IEEE 42010
- SEI Views and Beyond
- SEI Documenting Software Architectures, 2nd ed.

Why this matters here:
- the repo is too mixed for a single monograph to remain usable
- the current multi-view corpus is the correct response, not over-documentation

### 3.2 Architecture recovery from code plus runtime artifacts
**Assessment:** High confidence.

Supported by:
- SEI Architecture Reconstruction Guidelines
- SEI View Extraction and View Fusion in Architectural Understanding
- Cornelissen et al. on dynamic-analysis-based comprehension

Why this matters here:
- `concentric_study` is not a pure source-code repo
- its run artifacts are first-class architectural evidence

### 3.3 Traceability and correspondence
**Assessment:** High confidence.

Supported by:
- ISO 42010 mappings between views
- SEI Software Modeling: What to Model and Why
- CACM Requirements Tracing

Why this matters here:
- the repo has multiple views that can drift independently
- the traceability matrix was the correct step after recovery

### 3.4 Architecture conformance checking
**Assessment:** High confidence.

Supported by:
- Software Reflexion Models
- SEI Why Architecture Conformance Matters for Evolvable Systems

Why this matters here:
- the corpus now compares intended architecture to actual imports instead of only describing structure
- this was the right move before any serious refactoring recommendations

## 4. What The Literature Says We Should Not Do Next

### 4.1 Do not jump straight to broad refactoring
Why not:
- conformance literature argues that once erosion is measured, the next step is to
  make erosion observable and prevent recurrence, not immediately perform large changes
- otherwise the repo can regress while the refactor is still underway

### 4.2 Do not keep adding only static views
Why not:
- dynamic-architecture literature shows that running-system evidence reveals
  interaction structures that import graphs cannot capture
- another static-only pass would now be lower-value than adding execution views

### 4.3 Do not treat LLM synthesis as the strongest remaining method layer
Why not:
- the strongest remaining gaps are now in dynamic structure and architecture evaluation
- those areas have older, stronger foundations than another round of purely synthetic summarization

## 5. Strongest Research-Backed Path Forward

## 5.1 Step A: Turn conformance into regression enforcement
**Priority:** first
**Confidence:** high

Research basis:
- Software Reflexion Models
- Why Architecture Conformance Matters for Evolvable Systems
- ISO 42010 correspondences

Reasoning:
- we now have an intended model and measured live drift
- the strongest next move is to keep the model live by preventing known drift from growing
- in this repo, that means at minimum:
  - fail or flag new shim imports
  - preserve the narrow scope of runtime imports inside `operator/agent_infra/startup.py` and `operator/agent_infra/recovery.py`
  - track facade-import concentration explicitly

## 5.2 Step B: Add a dynamic execution architecture view
**Priority:** second
**Confidence:** high

Research basis:
- Discovering Architectures from Running Systems (SEI)
- Dynamic Design Analysis to Support Architecture Design (ESEC/FSE 2001)
- Cornelissen et al. dynamic-analysis survey

Reasoning:
- the current corpus has strong static structure and run-artifact evidence
- what it still lacks is a recovered interaction view from actual execution behavior
- for this repo, that means deriving an execution/call-flow architecture from:
  - `trace.jsonl`
  - `manifest.json`
  - outer-loop escalation artifacts
  - canonical entrypoints

This is now a stronger next step than another static dependency report.

## 5.3 Step C: Run scenario-based architecture evaluation before large code changes
**Priority:** third
**Confidence:** high

Research basis:
- Architecture Tradeoff Analysis Method Collection (SEI)
- Quality Attribute Workshop Collection (SEI)
- ARID and the SEI playbook for early architecture analysis

Reasoning:
- once conformance is enforced and dynamic behavior is visible, the next best move is not blind cleanup
- it is to evaluate the architecture against concrete quality scenarios such as:
  - recoverability under repeated GUI obstruction
  - observability of failure root cause
  - changeability of shared execution helpers
  - security boundary clarity during credentialed workflows
  - performance/cost tradeoffs in verification and routing

This is the strongest basis for deciding which refactors are worth doing.

## 5.4 Step D: Only then prioritize code-structure changes
**Priority:** fourth
**Confidence:** high

Examples that should follow, not precede, Steps A-C:
- shim retirement
- facade slimming
- extraction of boundary adapters
- entrypoint de-duplication work that crosses module boundaries

## 6. Implications For The Work Already Done

### Strongly validated
- layered corpus
- architecture diagrams and subsystem report
- 90-minute walkthrough as an onboarding artifact
- Section 1 duplication audit
- Section 2 traceability matrix
- Section 3 architecture conformance checks

### Still missing for research-grade completeness
- scenario-based quality-attribute evaluation
- runtime-conformance expectations over execution families, not only static imports
- repeated drift checks so new run corpora and new docs stay aligned with the recovered views

## 7. Decision

### Context
- the corpus already has recovery, traceability, and conformance layers
- the remaining high-value uncertainty is in runtime interaction structure and architecture tradeoffs, not folder inventory or additional static description

### Decision
The most solid PhD path from here is:
1. keep conformance regression enforcement live
2. keep the dynamic execution view refreshed as the run corpus evolves
3. scenario-based architecture evaluation
4. only then code-structure changes

### Consequences
- Positive: this path is more conservative and methodologically stronger than jumping directly into refactors or more prose synthesis
- Positive: it aligns the next work with stronger institutional and classical architecture sources
- Trade-off: progress will look slower, but the resulting decisions will be substantially better grounded

## 8. Primary Sources

- ISO/IEC/IEEE 42010: https://www.iso-architecture.org/ieee-1471/
- ISO/IEC/IEEE 42010 Mappings Between Views: https://www.iso-architecture.org/ieee-1471/mv/
- Views and Beyond: https://www.sei.cmu.edu/library/views-and-beyond-the-sei-approach-for-architecture-documentation/
- Documenting Software Architectures, 2nd ed.: https://www.sei.cmu.edu/library/documenting-software-architectures-views-and-beyond-second-edition/
- Architecture Reconstruction Guidelines, Third Edition: https://www.sei.cmu.edu/library/architecture-reconstruction-guidelines-third-edition/
- View Extraction and View Fusion in Architectural Understanding: https://www.sei.cmu.edu/library/view-extraction-and-view-fusion-in-architectural-understanding/
- Software Modeling: What to Model and Why: https://insights.sei.cmu.edu/library/software-modeling-what-to-model-and-why/
- Requirements Tracing: https://cacm.acm.org/research/requirements-tracing/
- A Systematic Survey of Program Comprehension through Dynamic Analysis: https://ieeexplore.ieee.org/document/4634918
- Software Reflexion Models: https://www.cs.ubc.ca/~murphy/papers/rm/fse95.html
- Why Architecture Conformance Matters for Evolvable Systems: https://www.sei.cmu.edu/library/why-architecture-conformance-matters/
- Discovering Architectures from Running Systems: https://www.sei.cmu.edu/library/discovering-architectures-from-running-systems/
- Dynamic Design Analysis to Support Architecture Design: https://dl.acm.org/doi/10.1145/503271.503237
- Architecture Tradeoff Analysis Method Collection: https://www.sei.cmu.edu/library/architecture-tradeoff-analysis-method-collection/
- Quality Attribute Workshop Collection: https://www.sei.cmu.edu/library/quality-attribute-workshop-collection/
- A Playbook for Early Architecture Analysis: https://www.sei.cmu.edu/library/a-playbook-for-early-architecture-analysis/
