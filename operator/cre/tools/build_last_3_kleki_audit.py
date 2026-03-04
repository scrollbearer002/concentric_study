#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
CRE = ROOT / 'operator' / 'cre'
RUNS = CRE / 'runs'
ARTIFACTS = CRE / 'artifacts'

RUN_IDS = ['2b70a9a006b0', 'f40e7d9ed9ab', '9d28b35cf1b0']
VALID_CLASSES = {
    'render_state', 'canvas_reset', 'color_grounding', 'window_capture_scope',
    'geometry_primitive', 'plan_synthesis', 'verification_granularity',
    'benchmark_claim_design', 'recovery_policy', 'historical_only',
    'open_quality_gap',
}
VALID_STATUS = {'historical_resolved', 'historical_regressed', 'still_open'}

RESEARCH_REFERENCES = [
    {
        'title': 'Kleki Help',
        'url': 'https://kleki.com/help/',
        'why': 'Documents Delete/Backspace clear-layer behavior, Shift drawing, shape tool shortcut, and browser recovery behavior.'
    },
    {
        'title': 'OSWorld',
        'url': 'https://arxiv.org/abs/2404.07972',
        'why': 'Primary benchmark showing GUI-agent failures cluster around grounding and operational control.'
    },
    {
        'title': 'UI-Hawk',
        'url': 'https://aclanthology.org/2025.emnlp-main.920/',
        'why': 'Supports temporal GUI evidence and screen-history-aware diagnostics.'
    },
    {
        'title': 'ShowUI',
        'url': 'https://arxiv.org/abs/2411.17465',
        'why': 'Supports tighter visual-action coupling for GUI tasks.'
    },
    {
        'title': 'ShowUI-pi',
        'url': 'https://showlab.github.io/showui-pi',
        'why': 'Supports continuous GUI dexterity primitives for line- and stroke-like operations.'
    },
    {
        'title': 'MCP-Atlas',
        'url': 'https://arxiv.org/abs/2602.00933',
        'why': 'Justifies claims-based partial-credit evaluation, but only when claims match task semantics.'
    },
    {
        'title': 'CRAFT',
        'url': 'https://arxiv.org/abs/2512.20362',
        'why': 'Supports decomposed multimodal verification instead of holistic pass/fail.'
    },
    {
        'title': 'University of Missouri One-Point Perspective',
        'url': 'https://arch.missouri.edu/architectural-studies-studio-student-work/drafting/project-one-point-perspective/',
        'why': 'Line quality, scale, and perspective accuracy are first-class acceptance criteria in architectural drawing.'
    },
    {
        'title': 'Julianna Kunstler One-Point Perspective',
        'url': 'https://juliannakunstler.com/1pt-perspective',
        'why': 'Codifies the relevant construction rules: verticals vertical, front horizontals horizontal, depth lines to one vanishing point.'
    },
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding='utf-8'))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def row(run_id: str, step: dict[str, Any], *, root_cause_class: str, root_cause_detail: str,
        status_now: str, required_fix: str, required_test: str, evidence_path: str | None = None) -> dict[str, Any]:
    if root_cause_class not in VALID_CLASSES:
        raise ValueError(root_cause_class)
    if status_now not in VALID_STATUS:
        raise ValueError(status_now)
    action = step.get('action', {}) or {}
    if not isinstance(action, dict):
        action = {'type': str(action)}
    action_result = step.get('action_result', {}) or {}
    evaluation = step.get('evaluation', {}) or {}
    expected = evaluation.get('expected') or action.get('type', 'action contract')
    actual = evaluation.get('actual') or action_result.get('error') or action_result.get('output') or str(action_result.get('success'))
    return {
        'run_id': run_id,
        'step': step.get('step'),
        'action_type': action.get('type', 'unknown'),
        'thought': step.get('thought', ''),
        'parameters': json.dumps(action.get('parameters', {}), ensure_ascii=False, sort_keys=True),
        'expected_contract': expected,
        'actual_outcome': actual,
        'evidence_path': evidence_path or '',
        'root_cause_class': root_cause_class,
        'root_cause_detail': root_cause_detail,
        'status_now': status_now,
        'required_fix': required_fix,
        'required_test': required_test,
    }


def classify_rows(run_id: str, manifest: dict[str, Any], steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for step in steps:
        sid = step.get('step')
        action_type = (step.get('action') or {}).get('type', 'unknown')
        evidence = ''
        detail = 'Context step retained for full line-by-line traceability.'
        fix = 'None beyond preserving current behavior.'
        test = 'No dedicated test beyond trace coverage.'
        klass = 'historical_only'
        status = 'historical_resolved'

        if run_id == '9d28b35cf1b0':
            if sid == 3:
                klass = 'color_grounding'
                detail = (
                    'Color selection contract failed: the system clicked the picker but could not prove the active swatch was black. '
                    'This exposed weak state-setting verification in the Kleki color picker.'
                )
                fix = 'Preserve the grayscale-anchor selection path and the color-effect contract; do not regress to generic panel clicks.'
                test = 'Regression test for grayscale-anchor coordinates and color contract resolution.'
                status = 'historical_resolved'
                evidence = 'operator/cre/runs/9d28b35cf1b0/trace.jsonl'
            elif sid == 1:
                detail = 'Leave-page dialog dismissal succeeded and is retained as a preflight dependency for later runs.'
                evidence = 'operator/cre/runs/9d28b35cf1b0/trace.jsonl'
            elif sid == 2:
                detail = 'Clear-canvas succeeded and became the baseline precondition before the color-setting failure.'
                evidence = 'operator/cre/runs/9d28b35cf1b0/trace.jsonl'

        elif run_id == 'f40e7d9ed9ab':
            if sid == 2:
                klass = 'recovery_policy'
                detail = (
                    'Clear-canvas failure was compounded by a recovery-policy defect: repeated diagnosis correctly identified persistent marks, '
                    'but recovery_action stayed none across attempts. The deeper bug was non-corrective retry logic, not only reset failure.'
                )
                fix = 'Preserve explicit clear-canvas contract repair and forbid none when diagnosis says canvas still contains marks.'
                test = 'Regression test for clear-canvas repair dispatch and historical checkpoint diagnosis.'
                status = 'historical_resolved'
                evidence = 'operator/cre/runs/f40e7d9ed9ab/visual_monitor/checkpoints.json'
            elif sid == 1:
                detail = 'Dialog dismissal succeeded; retained as part of Kleki session recovery handling.'
                evidence = 'operator/cre/runs/f40e7d9ed9ab/trace.jsonl'

        elif run_id == '2b70a9a006b0':
            if sid in {5, 6, 7, 8, 13, 14, 15, 16, 17, 18, 41}:
                klass = 'geometry_primitive'
                detail = (
                    'Structural building lines were executed as generic draw_path strokes. The completed output passed local stroke checks but '
                    'failed final architectural readability, indicating that straight structural primitives were not enforced.'
                )
                fix = 'Expose a first-class draw_segments structural action and route silhouette, mullions, roof edges, and final outline through it.'
                test = 'Unit test that structural Kleki plan steps normalize to draw_segments and preserve open independent strokes.'
                status = 'still_open'
                evidence = 'operator/cre/runs/2b70a9a006b0/trace.jsonl'
            elif sid in {10, 11, 19, 20, 21, 22, 23}:
                klass = 'plan_synthesis'
                detail = (
                    'Facade and floor-band geometry used simple horizontal strokes across the form without enforced one-point perspective shrinkage. '
                    'The final gate rejected perspective coherence and facade legibility.'
                )
                fix = 'Enforce one-point scaffold rules in planning and normalization: front horizontals horizontal, verticals vertical, depth lines coherent.'
                test = 'Plan-quality regression test for one-point scaffold, facade segmentation, and coverage constraints.'
                status = 'still_open'
                evidence = 'operator/cre/runs/2b70a9a006b0/trace.jsonl'
            elif sid in {25, 26, 27, 30, 33, 34, 35, 38, 39, 40}:
                klass = 'render_state'
                detail = (
                    'The run exercised color, brush size, and opacity, but the final image still showed noisy scatter contamination and unstable render-state normalization. '
                    'Scatter and stabilizer were not first-class controlled variables.'
                )
                fix = 'Add explicit Kleki render-state normalization: tool, scatter, stabilizer, opacity, and brush-size actions with contracts.'
                test = 'Unit tests for kleki_reset_render_state, kleki_set_scatter, kleki_set_stabilizer, and art render-state claims.'
                status = 'still_open'
                evidence = 'operator/cre/runs/2b70a9a006b0/verification/verify_01.png'
            elif sid in {28, 29, 31, 32, 36}:
                klass = 'open_quality_gap'
                detail = (
                    'Shading passes produced visible grayscale tone but not controlled architectural massing. Final critique explicitly called out sparse detail, weak subject identity, and noise-like tonal treatment.'
                )
                fix = 'Use broader, controlled tonal band segmentation and mid-run art assertions for shading quality and composition coverage.'
                test = 'Art-quality verification tests that catch sparse, noisy, or under-covered shading before the final gate.'
                status = 'still_open'
                evidence = 'operator/cre/runs/2b70a9a006b0/verification/verify_01.png'
            elif sid == 997:
                klass = 'verification_granularity'
                detail = (
                    'The final verification gate correctly rejected the output, but it was the first strong semantic quality check in the run. '
                    'That meant perspective, facade, coverage, and line-discipline defects survived until the end.'
                )
                fix = 'Add mandatory mid-run art visual assertions after scaffold, facade, shading, and final outline completion.'
                test = 'Verification-gate keyword tests plus step-level art checkpoint tests.'
                status = 'still_open'
                evidence = 'operator/cre/runs/2b70a9a006b0/trace.jsonl'
            elif sid == 996:
                klass = 'benchmark_claim_design'
                detail = (
                    'Benchmark scoring still gave partial credit despite severe architectural failure, proving the art claim surface remained too coarse.'
                )
                fix = 'Add claims for composition coverage, recognizability, perspective coherence, facade legibility, detail density, and render-state normalization.'
                test = 'Benchmark regression test distinguishing productive but poor art from valid architectural output.'
                status = 'still_open'
                evidence = 'operator/cre/runs/2b70a9a006b0/benchmark_result.json'

        out.append(row(run_id, step, root_cause_class=klass, root_cause_detail=detail,
                       status_now=status, required_fix=fix, required_test=test, evidence_path=evidence))
    return out


def build():
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    all_rows: list[dict[str, Any]] = []
    run_summaries: list[dict[str, Any]] = []
    for run_id in RUN_IDS:
        run_dir = RUNS / run_id
        manifest = load_json(run_dir / 'manifest.json')
        steps = load_jsonl(run_dir / 'trace.jsonl')
        bench = load_json(run_dir / 'benchmark_result.json') if (run_dir / 'benchmark_result.json').exists() else {}
        run_summaries.append({
            'run_id': run_id,
            'outcome': manifest.get('outcome'),
            'failure_step': manifest.get('failure_step'),
            'failure_category': manifest.get('failure_category'),
            'error_summary': manifest.get('error_summary'),
            'num_steps': manifest.get('num_steps'),
            'claims_score': bench.get('claims_score'),
            'discovery_precision': bench.get('discovery_precision'),
            'recovery_rate': bench.get('recovery_rate'),
        })
        all_rows.extend(classify_rows(run_id, manifest, steps))

    csv_path = ARTIFACTS / 'last_3_kleki_step_matrix.csv'
    fields = [
        'run_id','step','action_type','thought','parameters','expected_contract','actual_outcome','evidence_path',
        'root_cause_class','root_cause_detail','status_now','required_fix','required_test'
    ]
    with csv_path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(all_rows)

    open_backlog = [
        'composition coverage too small',
        'insufficient detail density',
        'weak subject recognizability',
        'poor facade structure',
        'broken one-point perspective',
        'linework reads as scribble/noise',
        'scatter noise contaminates shading',
    ]

    defect_registry = {
        'audited_runs': RUN_IDS,
        'run_summaries': run_summaries,
        'historical_resolved': {
            'color_grounding': {
                'primary_run': '9d28b35cf1b0',
                'current_state': 'Preserve the grayscale-anchor path and color-effect contract.',
            },
            'canvas_reset_plus_recovery_policy': {
                'primary_run': 'f40e7d9ed9ab',
                'current_state': 'Preserve explicit clear-canvas repair and regression coverage against recovery_action none.',
            },
            'window_capture_scope': {
                'primary_run': 'cd0862f1e3c4',
                'current_state': 'Remain regression-covered but not the main blocker in the chosen 3-run set.',
            },
        },
        'still_open': {
            'primary_run': '2b70a9a006b0',
            'classes': [
                'geometry_primitive', 'render_state', 'plan_synthesis',
                'verification_granularity', 'benchmark_claim_design', 'open_quality_gap',
            ],
            'quality_backlog': open_backlog,
        },
        'rows': all_rows,
        'references': RESEARCH_REFERENCES,
    }
    (ARTIFACTS / 'last_3_kleki_defect_registry.json').write_text(json.dumps(defect_registry, indent=2), encoding='utf-8')

    cross_run = {
        'runs': run_summaries,
        'fixed_frontiers': [
            {'run_id': '9d28b35cf1b0', 'class': 'color_grounding', 'status_now': 'historical_resolved'},
            {'run_id': 'f40e7d9ed9ab', 'class': 'canvas_reset', 'status_now': 'historical_resolved'},
            {'run_id': 'f40e7d9ed9ab', 'class': 'recovery_policy', 'status_now': 'historical_resolved'},
        ],
        'open_frontiers': [
            {'run_id': '2b70a9a006b0', 'class': 'geometry_primitive', 'status_now': 'still_open'},
            {'run_id': '2b70a9a006b0', 'class': 'render_state', 'status_now': 'still_open'},
            {'run_id': '2b70a9a006b0', 'class': 'plan_synthesis', 'status_now': 'still_open'},
            {'run_id': '2b70a9a006b0', 'class': 'verification_granularity', 'status_now': 'still_open'},
            {'run_id': '2b70a9a006b0', 'class': 'benchmark_claim_design', 'status_now': 'still_open'},
        ],
        'quality_backlog': open_backlog,
    }
    (ARTIFACTS / 'last_3_kleki_cross_run_diff.json').write_text(json.dumps(cross_run, indent=2), encoding='utf-8')

    quality_claims = {
        'task_family': 'kleki_architectural_art',
        'baseline_run': '2b70a9a006b0',
        'claims': [
            {'check': 'check_art_composition_coverage', 'description': 'Drawing fills a substantial portion of the canvas.', 'why': 'Final verification explicitly failed coverage.'},
            {'check': 'check_art_recognizable_subject', 'description': 'A recognizable tall skyscraper is present.', 'why': 'Final verification rejected subject recognizability.'},
            {'check': 'check_art_perspective_coherence', 'description': 'Major structural edges obey one-point perspective.', 'why': 'Final verification rejected perspective coherence.'},
            {'check': 'check_art_facade_legibility', 'description': 'Facade subdivisions are visible and coherent.', 'why': 'Final verification rejected facade structure.'},
            {'check': 'check_art_detail_density', 'description': 'Detail density is rich rather than sparse or patchy.', 'why': 'Final verification explicitly failed detail richness and exhaustiveness.'},
            {'check': 'check_art_render_state_normalized', 'description': 'Render state shows controlled brush settings without scatter contamination.', 'why': 'Final screenshot showed scatter-driven noise.'},
        ],
        'references': [r['url'] for r in RESEARCH_REFERENCES[:7]],
    }
    (ARTIFACTS / 'last_3_kleki_quality_claims.json').write_text(json.dumps(quality_claims, indent=2), encoding='utf-8')

    audit_md = []
    audit_md.append('# Last 3 Kleki Runs Line-by-Line Audit (PhD)')
    audit_md.append('')
    audit_md.append('Audited runs: `2b70a9a006b0`, `f40e7d9ed9ab`, `9d28b35cf1b0`.')
    audit_md.append('')
    audit_md.append('## Run Summaries')
    audit_md.append('')
    for summary in run_summaries:
        audit_md.append(f"- `{summary['run_id']}`: outcome=`{summary['outcome']}`, failure_step=`{summary['failure_step']}`, claims_score=`{summary['claims_score']}`")
    audit_md.append('')
    audit_md.append('## Required Conclusions')
    audit_md.append('')
    audit_md.append('- `9d28b35cf1b0` exposed the old color-setting contract defect and is now a historical regression case.')
    audit_md.append('- `f40e7d9ed9ab` exposed a real recovery-policy bug: diagnosis succeeded but corrective action was `none` twice.')
    audit_md.append('- `2b70a9a006b0` is the primary open-defect run because it crossed setup and failed on output quality at final verification.')
    audit_md.append('')
    audit_md.append('## Open Quality Backlog from `2b70a9a006b0`')
    audit_md.append('')
    for item in open_backlog:
        audit_md.append(f'- {item}')
    audit_md.append('')
    audit_md.append('## Step Matrix')
    audit_md.append('')
    audit_md.append('See `operator/cre/artifacts/last_3_kleki_step_matrix.csv` for the full row-level matrix.')
    audit_md.append('')
    for run_id in RUN_IDS:
        audit_md.append(f'### `{run_id}`')
        audit_md.append('')
        audit_md.append('| Step | Action | Root Cause | Status | Required Fix |')
        audit_md.append('|---|---|---|---|---|')
        for r in [r for r in all_rows if r['run_id'] == run_id]:
            audit_md.append(f"| {r['step']} | `{r['action_type']}` | `{r['root_cause_class']}` | `{r['status_now']}` | {r['required_fix']} |")
        audit_md.append('')
    audit_md.append('## Research Basis')
    audit_md.append('')
    for ref in RESEARCH_REFERENCES:
        audit_md.append(f"- [{ref['title']}]({ref['url']}): {ref['why']}")
    (CRE / 'LAST_3_KLEKI_RUNS_LINE_BY_LINE_AUDIT_PHD.md').write_text('\n'.join(audit_md) + '\n', encoding='utf-8')

    fix_md = []
    fix_md.append('# Last 3 Kleki Fix Program (PhD)')
    fix_md.append('')
    fix_md.append('## Cross-Run Synthesis')
    fix_md.append('')
    fix_md.append('- Preserve historical fixes for color grounding and clear-canvas recovery.')
    fix_md.append('- Treat `2b70a9a006b0` as the main open-quality benchmark.')
    fix_md.append('- Attack the open frontier in this order: render state, geometry primitive, plan synthesis, verification granularity, benchmark semantics.')
    fix_md.append('')
    fix_md.append('## Waves')
    fix_md.append('')
    fix_md.append('1. Render-state completeness: scatter, stabilizer, tool normalization.')
    fix_md.append('2. Geometry primitive repair: structural segments instead of freehand structural draw_path use.')
    fix_md.append('3. Plan-synthesis constraints: one-point scaffold and composition coverage enforced in normalization.')
    fix_md.append('4. Step-level art verification: scaffold, facade, shading, and final-outline checkpoints.')
    fix_md.append('5. Benchmark claim redesign: semantic art-quality claims, not only mechanical execution credit.')
    fix_md.append('')
    fix_md.append('## Acceptance')
    fix_md.append('')
    fix_md.append('- A rerun must pass recognizability, perspective, facade, shading, coverage, and line-discipline constraints.')
    fix_md.append('- Historical failures must remain locked by regression tests.')
    fix_md.append('')
    fix_md.append('## Artifacts')
    fix_md.append('')
    fix_md.append('- `operator/cre/artifacts/last_3_kleki_defect_registry.json`')
    fix_md.append('- `operator/cre/artifacts/last_3_kleki_cross_run_diff.json`')
    fix_md.append('- `operator/cre/artifacts/last_3_kleki_quality_claims.json`')
    fix_md.append('- `operator/cre/artifacts/last_3_kleki_step_matrix.csv`')
    (CRE / 'LAST_3_KLEKI_FIX_PROGRAM_PHD.md').write_text('\n'.join(fix_md) + '\n', encoding='utf-8')


if __name__ == '__main__':
    build()
