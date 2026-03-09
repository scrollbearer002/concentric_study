# CRE Research Surface

`operator/cre/` is the repo's mixed research, evaluation, experiment, and
legacy-operations layer. It is not a single subsystem. It contains:

- PhD memos about architecture, tooling, environment, and Cursor integration
- test entrypoints and evaluation harnesses
- curated evidence bundles and benchmark outputs
- legacy setup notes and local operational remnants

The top-level surface is intentionally not flat in meaning. Use the curated
index below instead of treating every file in this directory as equally current.

## Start Here

- [CANONICAL_RESEARCH_INDEX_PHD.md](CANONICAL_RESEARCH_INDEX_PHD.md)
- [DOC_SURFACE_GOVERNANCE_PHD.md](DOC_SURFACE_GOVERNANCE_PHD.md)
- [PHD_DECISION_PRACTICE.md](PHD_DECISION_PRACTICE.md)
- [PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md](PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md)
- [CURRENT_ARCHITECTURE_SURFACE_PHD.md](CURRENT_ARCHITECTURE_SURFACE_PHD.md)

## Machine-Readable Index

- [artifacts/cre_top_level_doc_registry.json](artifacts/cre_top_level_doc_registry.json)

## Regenerate The Index

```bash
python3 operator/cre/tools/build_cre_doc_registry.py
```

## Legacy Kernel Note

Older CRE-kernel files remain in this directory for provenance:

- `codex_kernel.lua`
- `verify_kernel.sh`
- `SHOWCASE.md`

They are not the primary documentation entrypoint for the current
`concentric_study` architecture.
