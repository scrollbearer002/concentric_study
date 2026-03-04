# PhD External Research Validation

**Date of external research pass:** February 28, 2026

## Purpose

This memo answers a narrow question:

**Are the methods used in the project-understanding corpus actually aligned with
well-respected PhD-level sources in software architecture, program comprehension,
repository understanding, and onboarding?**

The answer is **yes, with an important qualification**:
- the foundational parts of the method are strongly supported by standards,
  SEI guidance, and long-standing software-engineering literature
- the LLM-specific and repository-scale synthesis parts are newer and should be
  treated as high-potential but still evolving research support

## Source Quality Model

### High confidence
- international standards
- SEI / CMU institutional architecture guidance
- established journal or conference papers

### Medium confidence
- recent arXiv papers with strong topical relevance but less maturity than standards or long-established literature

### Rule for use
- standards and SEI sources justify the **core method**
- newer LLM/repository papers justify the **tooling and scaling strategy**
- no major methodological claim in the corpus should depend on a single recent preprint alone

## Research Question 1: Should architecture be documented as multiple views instead of one giant description?

### Evidence
- ISO/IEC/IEEE 42010: architecture descriptions are organized around stakeholders,
  concerns, viewpoints, and views.
- SEI Views and Beyond: architecture documentation should be view-based, not a
  single flattened narrative.
- SEI Documenting Software Architectures, 2nd ed.: documents architecture through
  multiple coherent views plus rationale.

### Assessment
**High confidence.**

### Implication for this repo
The layered corpus is the correct choice:
- `FOLDER_ATLAS.md`
- `ARCHITECTURE_DIAGRAMS.md`
- `SUBSYSTEM_DEPENDENCY_REPORT.md`
- `RUNTIME_FLOWS.md`
- `EVIDENCE_AND_RUN_ARTIFACTS.md`
- `PHD_DEPTH_AUDIT.md`

This is more aligned with architecture standards than one monolithic repo essay.

## Research Question 2: Is it correct to recover architecture from code, dependencies, and runtime artifacts when the repo is large and mixed?

### Evidence
- SEI Architecture Reconstruction Guidelines, Third Edition
- SEI View Extraction and View Fusion in Architectural Understanding
- Cornelissen et al., dynamic-analysis program comprehension survey
- Ferrante et al., dependence-graph reasoning

### Assessment
**High confidence.**

### Implication for this repo
Using all of the following together is methodologically correct:
- static import graph
- folder inventory
- run artifacts (`trace.jsonl`, `manifest.json`, `ESCALATION.md`)
- long-form run analyses such as `operator/cre/runs/LAST_20_RUNS_EXHAUSTIVE.md`

This is exactly the kind of multi-evidence reconstruction that architecture-recovery
and program-comprehension literature recommends.

## Research Question 3: Is a generated subsystem dependency report derived from imports a valid architectural view?

### Evidence
- ISO 42010 allows architecture descriptions to use multiple models and correspondences.
- SEI reconstruction/view-fusion guidance explicitly supports extracted structural views.
- DependEval shows repository dependency understanding is a meaningful and non-trivial task.

### Assessment
**High confidence for use as one view, not the only view.**

### Implication for this repo
`import_graph.json` and `subsystem_dependency_report.json` are valid architectural inputs,
but they should not be treated as the whole architecture. That is why the corpus also
keeps runtime-flow and evidence views.

## Research Question 4: Is the 90-minute guided walkthrough a sound onboarding artifact?

### Evidence
- From Expert to Novice studies how architecture explanations must adapt to audience.
- Onboarding Buddy supports retrieval-backed onboarding assistance for evolving repos.
- Code-Survey supports systematic rather than ad hoc large-codebase analysis.

### Assessment
**Medium confidence.**

### Implication for this repo
The walkthrough is a justified artifact, especially because `operator/cre/` is mixed and
newcomers would otherwise be overwhelmed. The strongest support is not "90 minutes" as a
magic number, but the idea of staged, audience-sensitive onboarding over layered views.

## Research Question 5: Is it correct to use newer LLM/repository-understanding papers to justify the synthesis layer?

### Evidence
- RepoFusion: repository context matters materially for code understanding.
- Hierarchical Context Pruning: repository context should be structured and pruned,
  not dumped whole.
- RepoScope: multi-view repository context is better than flat retrieval.
- ArchAgent: scalable architecture recovery with LLMs uses multiple views and extraction.
- Generating Software Architecture Description from Source Code using Reverse Engineering and LLM: reverse engineering plus LLM synthesis is a valid architecture-document path.
- Software Architecture Meets LLMs SLR: the area is promising but still maturing.

### Assessment
**Medium confidence.**

### Implication for this repo
These sources support the generator, dependency report, diagrams, and audit synthesis,
but they should be presented as modern augmentation of the architecture method, not the
foundational reason the method is sound.

## Research Question 6: Is a doc-to-code traceability matrix a correct next layer after architecture recovery?

### Evidence
- ISO 42010's mapping-between-views guidance supports explicit correspondences between architectural representations.
- SEI's "Software Modeling: What to Model and Why" supports using models to help readers move across concerns and levels of detail.
- CACM's "Requirements Tracing" supports following a concern across representations rather than leaving it trapped in one artifact.
- Cornelissen et al. supports using runtime evidence as part of the traced correspondence, not only source code.

### Assessment
**High confidence.**

### Implication for this repo
`SECTION_2_TRACEABILITY_MATRIX.md` is the correct next layer after architecture recovery because this repo has multiple views that can drift independently:
- architecture docs
- runtime code
- persistent state and run artifacts
- evidence summaries

The traceability matrix is what turns those from parallel documents into a corresponding architecture description.

## What This Means For Confidence

For the strongest research-backed sequencing of the next work, see
`operator/cre/project_understanding/PHD_PATH_REVALIDATION.md`.

### Strongly supported parts of the current corpus
- layered documentation instead of a single flat report
- multi-view architecture description
- architecture reconstruction from implementation artifacts
- doc-to-code and doc-to-artifact correspondence via a traceability matrix
- source-vs-model architecture conformance checking against the recovered layering
- combining structural and dynamic evidence
- stakeholder-oriented audit and reading paths

### Supported but still emerging parts
- LLM-assisted architecture recovery
- repository-understanding synthesis over large codebases
- onboarding walkthroughs designed from retrieval and architecture-explanation research

## What Is Still Missing If We Want Even Higher Confidence

The current corpus is sound, but the literature still points to three remaining upgrades:

1. **Scenario-based architecture evaluation**
   Recovered structure and behavior should now be tested against quality scenarios, not only described.
2. **Runtime-conformance expectations**
   The dynamic execution families are now visible, but they are not yet enforced as runtime conformance rules.
3. **Repeated drift checks**
   Re-run traceability and dynamic reconstruction periodically so documentation does not silently lag stronger implementations.

## Bottom-Line Judgment

### Context
- The corpus currently uses layered views, import-derived subsystem modeling,
  runtime evidence, guided onboarding, explicit traceability correspondences,
  and architecture-conformance checks.
- Standards and SEI guidance support view-based architecture documentation and
  architecture reconstruction.
- Program-comprehension literature supports combining static and dynamic evidence.
- Recent LLM/repository papers support scaling these tasks to large mixed repos.

### Decision
We can be confident that the project-understanding method is **methodologically correct**
for this repo.

### Consequences
- Positive: the current corpus is defensible at a PhD level.
- Positive: the work is backed by respected architecture and software-engineering sources,
  not only recent LLM papers.
- Trade-off: some newer synthesis claims should still be framed as emerging support rather
  than settled consensus.
- Next step: add scenario-based architecture evaluation on top of the now-live conformance and execution views.

## External Sources Used

### Standards and institutional guidance
- ISO/IEC/IEEE 42010: https://www.iso-architecture.org/ieee-1471/
- ISO/IEC/IEEE 42010 Architecture Descriptions: https://www.iso-architecture.org/ieee-1471/ads/
- ISO/IEC/IEEE 42010 Conceptual Model: https://www.iso-architecture.org/ieee-1471/cm/
- ISO/IEC/IEEE 42010 Mappings Between Views: https://www.iso-architecture.org/ieee-1471/mv/
- Views and Beyond: https://www.sei.cmu.edu/library/views-and-beyond-the-sei-approach-for-architecture-documentation/
- Documenting Software Architectures, 2nd ed.: https://www.sei.cmu.edu/library/documenting-software-architectures-views-and-beyond-second-edition/
- Architecture Reconstruction Guidelines, Third Edition: https://www.sei.cmu.edu/library/architecture-reconstruction-guidelines-third-edition/
- View Extraction and View Fusion in Architectural Understanding: https://www.sei.cmu.edu/library/view-extraction-and-view-fusion-in-architectural-understanding/
- A Structured Approach for Reviewing Architecture Documentation: https://insights.sei.cmu.edu/library/a-structured-approach-for-reviewing-architecture-documentation/
- Software Modeling: What to Model and Why: https://insights.sei.cmu.edu/library/software-modeling-what-to-model-and-why/

### Core software-engineering literature
- Program Dependence Graph: https://dl.acm.org/doi/10.1145/24039.24041
- Dynamic-analysis program comprehension survey: https://ieeexplore.ieee.org/document/4634918
- Requirements Tracing: https://cacm.acm.org/research/requirements-tracing/

### Repository understanding and LLM-supported recovery
- DependEval: https://arxiv.org/abs/2503.06689
- RepoFusion: https://arxiv.org/abs/2306.10998
- Hierarchical Context Pruning: https://arxiv.org/abs/2406.18294
- RepoScope: https://arxiv.org/abs/2507.14791
- Code-Survey: https://arxiv.org/abs/2410.01837
- ArchAgent: https://arxiv.org/abs/2601.13007
- Generating Software Architecture Description from Source Code using Reverse Engineering and LLM: https://arxiv.org/abs/2511.05165
- Software Architecture Meets LLMs SLR: https://arxiv.org/abs/2505.16697

### Onboarding and explanation
- From Expert to Novice: https://arxiv.org/abs/2503.08628
- Onboarding Buddy: https://arxiv.org/abs/2503.23421
