# Doc Surface Governance (PhD)

Date: `2026-03-04`

## Context

### Local facts

- The top-level textual surface under `operator/cre/` currently contains more than one hundred files spanning:
  - current architecture and method memos
  - Cursor integration research
  - benchmark and site-specific case studies
  - historical execution/status reports
  - local setup and presentation notes
  - execution logs and byproducts
- The directory therefore mixes different evidence levels and different intended audiences in one flat namespace.
- That mixture increases onboarding cost and weakens source-of-truth discipline because a historical report can look just as authoritative as a current architecture memo.

### External research basis

This classification is not based only on local taste.

1. **Architecture documentation should be organized around concerns, stakeholders, and viewpoints.**
   - ISO/IEC/IEEE 42010 defines architecture descriptions in terms of concerns, stakeholders, viewpoints, views, and correspondences, not as one undifferentiated document heap.
   - Source: <https://www.iso-architecture.org/ieee-1471/>

2. **Relevant views should be selected deliberately rather than documenting everything at one level.**
   - SEI's Views and Beyond guidance treats views as the unit of architectural communication and argues that documentation should be packaged around what stakeholders need.
   - Sources:
     - <https://www.sei.cmu.edu/library/documenting-software-architectures-in-an-agile-world/>
     - <https://www.sei.cmu.edu/library/a-practical-method-for-documenting-software-architectures/>

3. **Architecture documentation that is not understandable or audience-shaped fails its purpose.**
   - SEI explicitly frames architecture documentation as something that must be understood, analyzed, and used by stakeholders; otherwise it does not deliver value.
   - Source:
     - <https://www.sei.cmu.edu/library/documenting-software-architectures-in-an-agile-world/>

4. **Cross-artifact traceability matters.**
   - CACM's requirements tracing article supports keeping explicit correspondences across artifacts instead of relying on implicit memory.
   - This is the basis for the machine-readable doc registry rather than an informal memo alone.
   - Source:
     - <https://cacm.acm.org/research/requirements-tracing/>

5. **Generated repository summaries are useful, but should be separated from canonical authored material.**
   - SEI's README study and current repository-summarization / architecture-reconstruction research both support machine-generated explanatory layers derived from source state.
   - That supports keeping rebuildable inventories and registries, but not treating every generated snapshot as canonical top-level documentation.
   - Sources:
     - <https://insights.sei.cmu.edu/blog/using-ai-to-augment-repository-readmes/>
     - <https://arxiv.org/abs/2406.09619>
     - <https://arxiv.org/abs/2508.10967>

6. **Decision records should keep context separate from decision and consequences.**
   - ADR practice supports a lightweight context -> decision -> consequences structure for documentation governance choices.
   - Source:
     - <https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions>

## Decision

`operator/cre/` should be governed as a **curated documentation surface**, not a flat memo dump.

The correct top-level policy is:

1. Keep a small **canonical core** at top level.
2. Keep a small set of **active snapshots** at top level when they are time-sensitive and still current.
3. Retain **supporting research** but de-emphasize it relative to the core reading path.
4. Classify **case studies**, **historical reports**, **local operational notes**, and **logs** separately so they are preserved without being mistaken for the current source of truth.
5. Maintain a **machine-readable registry** so the classification is inspectable and regenerable.

## Consequences

- Positive:
  - onboarding becomes faster because the current reading path is explicit
  - architecture and method docs are easier to cite correctly
  - historical provenance is preserved without dominating the top-level surface
  - future physical reorganization can happen with lower ambiguity

- Negative:
  - the project now has another governance document to maintain
  - some files that once looked equally important are explicitly downgraded to supporting or historical status
  - the registry classification will need periodic refresh as new memos are added

- Neutral:
  - no runtime code behavior changes
  - no historical material is deleted by this governance decision alone

## Current Implementation

- Human-facing index: [CANONICAL_RESEARCH_INDEX_PHD.md](/Users/christianpardo/Desktop/concentric_study/operator/cre/CANONICAL_RESEARCH_INDEX_PHD.md)
- Machine-readable registry: [cre_top_level_doc_registry.json](/Users/christianpardo/Desktop/concentric_study/operator/cre/artifacts/cre_top_level_doc_registry.json)
- Source register: [cre_doc_surface_primary_sources.json](/Users/christianpardo/Desktop/concentric_study/operator/cre/artifacts/cre_doc_surface_primary_sources.json)
- Builder: [build_cre_doc_registry.py](/Users/christianpardo/Desktop/concentric_study/operator/cre/tools/build_cre_doc_registry.py)
