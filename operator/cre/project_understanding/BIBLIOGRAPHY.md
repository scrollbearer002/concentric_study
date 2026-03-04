# Bibliography

## Source Confidence Note

- Treat standards, SEI/CMU material, and established journal papers as the highest-confidence methodological anchors.
- Treat recent arXiv papers as strong topical support, especially for LLM-assisted repository understanding and onboarding, but not as the sole basis for core architectural claims.

## Internal Repo Sources

### Governance and methodology
- `AGENTS.md`
- `.cursor/rules/concentric-study.mdc`
- `operator/cre/PHD_DECISION_PRACTICE.md`

### Architecture and validation
- `DUAL_AGENT_LOOP_PLAN.md`
- `operator/cre/PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md`
- `operator/cre/ESSAY_PROJECT_OVERLAP_PHD.md`
- `operator/cre/DEEP_DIVE_ADDENDUM.md`
- `operator/cre/ACADEMIC_VALIDATION.md`
- `operator/cre/ROADMAP_PHD_RESEARCH_MEMO.md`
- `operator/cre/project_understanding/SECTION_2_TRACEABILITY_MATRIX.md`
- `operator/cre/project_understanding/SECTION_3_ARCHITECTURE_CONFORMANCE.md`
- `operator/cre/project_understanding/SECTION_4_CONFORMANCE_ENFORCEMENT.md`
- `operator/cre/project_understanding/SECTION_5_DYNAMIC_EXECUTION_ARCHITECTURE.md`
- `operator/cre/project_understanding/PHD_EXTERNAL_RESEARCH_VALIDATION.md`
- `operator/cre/project_understanding/PHD_PATH_REVALIDATION.md`

### Dynamic evidence
- `operator/cre/runs/LAST_20_RUNS_EXHAUSTIVE.md`
- `operator/cre/EXHAUSTIVE_TEST_ANALYSIS.md`
- `operator/cre/EXECUTION_ANALYSIS.md`
- `operator/cre/project_understanding/artifacts/dynamic_execution_architecture.json`

## External Research And Standards

## Standards And Institutional Guidance

- ISO/IEC/IEEE 42010.
  Link: https://www.iso-architecture.org/ieee-1471/
  Why it matters: primary architecture-description standard for stakeholders, concerns, viewpoints, and views.
- ISO/IEC/IEEE 42010: Architecture Descriptions.
  Link: https://www.iso-architecture.org/ieee-1471/ads/
  Why it matters: explains what an architecture description must contain.
- ISO/IEC/IEEE 42010: Conceptual Model.
  Link: https://www.iso-architecture.org/ieee-1471/cm/
  Why it matters: clarifies the relationships between stakeholders, concerns, viewpoints, views, and models.
- Views and Beyond: The SEI Approach for Architecture Documentation.
  Link: https://www.sei.cmu.edu/library/views-and-beyond-the-sei-approach-for-architecture-documentation/
  Why it matters: supports view-based documentation instead of a single flattened report.
- Documenting Software Architectures: Views and Beyond, Second Edition.
  Link: https://www.sei.cmu.edu/library/documenting-software-architectures-views-and-beyond-second-edition/
  Why it matters: canonical SEI guidance for architecture documentation structure and rationale capture.
- Architecture Reconstruction Guidelines, Third Edition.
  Link: https://www.sei.cmu.edu/library/architecture-reconstruction-guidelines-third-edition/
  Why it matters: authoritative method for recovering architecture from existing codebases.
- View Extraction and View Fusion in Architectural Understanding.
  Link: https://www.sei.cmu.edu/library/view-extraction-and-view-fusion-in-architectural-understanding/
  Why it matters: supports multi-view reconstruction from multiple implementation artifacts.
- A Structured Approach for Reviewing Architecture Documentation.
  Link: https://insights.sei.cmu.edu/library/a-structured-approach-for-reviewing-architecture-documentation/
  Why it matters: supports structured, stakeholder-centered review of architecture docs.
- Michael Nygard / Cognitect. Documenting Architecture Decisions.
  Link: https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions
  Why it matters: matches the repo's facts -> decision -> consequences pattern.
- Architecture Decision Records.
  Link: https://adr.github.io/
  Why it matters: canonical ADR practice reference.

## Core Software-Engineering Literature

- Ferrante, Ottenstein, Warren. "The Program Dependence Graph and Its Use in Optimization." ACM TOPLAS, 1987.
  Link: https://dl.acm.org/doi/10.1145/24039.24041
  Why it matters: dependence reasoning for causal and trace-level analysis.
- Cornelissen et al. "A Systematic Survey of Program Comprehension through Dynamic Analysis." IEEE TSE, 2009.
  Link: https://ieeexplore.ieee.org/document/4634918
  Why it matters: justifies combining source reading with runtime evidence.

## Traceability And Correspondence

- ISO/IEC/IEEE 42010: Mappings Between Views.
  Link: https://www.iso-architecture.org/ieee-1471/mv/
  Why it matters: directly supports explicit correspondences between documentation views, implementation views, and evidence views.
- SEI. Software Modeling: What to Model and Why.
  Link: https://insights.sei.cmu.edu/library/software-modeling-what-to-model-and-why/
  Why it matters: supports using models and traceability links to move readers across concerns and levels of abstraction.
- Jackson and Cinkler. Requirements Tracing.
  Link: https://cacm.acm.org/research/requirements-tracing/
  Why it matters: provides the lifecycle-follow-through concept adapted here from requirement tracing to architecture-claim tracing.

## Repository Understanding And Architecture Recovery

- DependEval: Benchmarking LLMs for Repository Dependency Understanding.
  Link: https://arxiv.org/abs/2503.06689
  Why it matters: validates repository dependency understanding as a distinct technical challenge.
- RepoFusion: Training Code Models to Understand Your Repository.
  Link: https://arxiv.org/abs/2306.10998
  Why it matters: shows repository context materially improves understanding.
- Hierarchical Context Pruning.
  Link: https://arxiv.org/abs/2406.18294
  Why it matters: supports structured pruning rather than whole-repo dumping.
- RepoScope.
  Link: https://arxiv.org/abs/2507.14791
  Why it matters: supports multi-view, structure-aware repository context.
- Code-Survey: An LLM-Driven Methodology for Analyzing Large-Scale Codebases.
  Link: https://arxiv.org/abs/2410.01837
  Why it matters: supports survey-style large-codebase analysis.
- ArchAgent: Scalable Legacy Software Architecture Recovery with LLMs.
  Link: https://arxiv.org/abs/2601.13007
  Why it matters: directly supports multi-view architecture recovery from code.
- Generating Software Architecture Description from Source Code using Reverse Engineering and Large Language Model.
  Link: https://arxiv.org/abs/2511.05165
  Why it matters: directly relevant to source-to-architecture-description generation.
- Software Architecture Meets LLMs: A Systematic Literature Review.
  Link: https://arxiv.org/abs/2505.16697
  Why it matters: broader map of the current LLM-plus-architecture literature.
- SourcererCC: Scaling Code Clone Detection to Big Code.
  Link: https://arxiv.org/abs/1512.06448
  Why it matters: supports near-miss clone analysis for duplicated helpers that are no longer exact copies.
- Software Reflexion Models: Bridging the Gap Between Source and High-Level Models.
  Link: https://www.cs.ubc.ca/~murphy/papers/rm/fse95.html
  Why it matters: supports later architecture-conformance work by comparing code reality against intended high-level structure.
- Why Architecture Conformance Matters for Evolvable Systems.
  Link: https://www.sei.cmu.edu/library/why-architecture-conformance-matters/
  Why it matters: supports explicit conformance checking after architecture recovery.

## Dynamic Views And Architecture Evaluation

- Discovering Architectures from Running Systems.
  Link: https://www.sei.cmu.edu/library/discovering-architectures-from-running-systems/
  Why it matters: supports recovering runtime interaction architecture from executing systems rather than relying only on static dependencies.
- Hofmeister, Nord, and Soni. Dynamic Design Analysis to Support Architecture Design.
  Link: https://dl.acm.org/doi/10.1145/503271.503237
  Why it matters: supports dynamic design/execution analysis as the next view after static recovery and conformance.
- Discovering Architectures from Running Systems: Lessons Learned.
  Link: https://insights.sei.cmu.edu/library/discovering-architectures-from-running-systems-lessons-learned/
  Why it matters: sharpens the caution that runtime reconstruction must separate recurrent patterns from outlier executions.
- Architecture Tradeoff Analysis Method Collection.
  Link: https://www.sei.cmu.edu/library/architecture-tradeoff-analysis-method-collection/
  Why it matters: supports scenario-based architecture evaluation before major refactors.
- Quality Attribute Workshop Collection.
  Link: https://www.sei.cmu.edu/library/quality-attribute-workshop-collection/
  Why it matters: supports turning architectural concerns into concrete, evaluable scenarios.
- A Playbook for Early Architecture Analysis.
  Link: https://www.sei.cmu.edu/library/a-playbook-for-early-architecture-analysis/
  Why it matters: supports disciplined early evaluation of architectural options before committing to code changes.

## Self-Healing, Diagnosis, And Evaluation

- SHML. "Self-Healing Machine Learning." arXiv:2411.00186.
  Link: https://arxiv.org/abs/2411.00186
  Why it matters: supports the monitor-diagnose-adapt-test loop.
- MindGuard.
  Link: https://arxiv.org/abs/2508.20412
  Why it matters: supports the Decision Dependence Graph approach.
- MCP-Atlas.
  Link: https://arxiv.org/abs/2602.00933
  Why it matters: supports claims-based evaluation of artifacts and runs.

## GUI-Agent And Research-First Execution

- AppAgent: Multimodal Agents as Smartphone Users.
  Link: https://arxiv.org/abs/2312.13771
  Why it matters: supports pre-execution study of tasks, tools, and affordances.

## Onboarding And Explanation

- From Expert to Novice: An Empirical Study on Software Architecture Explanations.
  Link: https://arxiv.org/abs/2503.08628
  Why it matters: supports audience-sensitive walkthroughs and explanation windows.
- A Multi-agent Onboarding Assistant based on Large Language Models, Retrieval Augmented Generation, and Chain-of-Thought.
  Link: https://arxiv.org/abs/2503.23421
  Why it matters: supports retrieval-backed onboarding for evolving repositories.
