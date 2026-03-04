# Last 3 Kleki Fix Program (PhD)

## Cross-Run Synthesis

- Preserve historical fixes for color grounding and clear-canvas recovery.
- Treat `2b70a9a006b0` as the main open-quality benchmark.
- Attack the open frontier in this order: render state, geometry primitive, plan synthesis, verification granularity, benchmark semantics.

## Waves

1. Render-state completeness: scatter, stabilizer, tool normalization.
2. Geometry primitive repair: structural segments instead of freehand structural draw_path use.
3. Plan-synthesis constraints: one-point scaffold and composition coverage enforced in normalization.
4. Step-level art verification: scaffold, facade, shading, and final-outline checkpoints.
5. Benchmark claim redesign: semantic art-quality claims, not only mechanical execution credit.

## Acceptance

- A rerun must pass recognizability, perspective, facade, shading, coverage, and line-discipline constraints.
- Historical failures must remain locked by regression tests.

## Artifacts

- `operator/cre/artifacts/last_3_kleki_defect_registry.json`
- `operator/cre/artifacts/last_3_kleki_cross_run_diff.json`
- `operator/cre/artifacts/last_3_kleki_quality_claims.json`
- `operator/cre/artifacts/last_3_kleki_step_matrix.csv`
