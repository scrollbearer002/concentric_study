#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from agent import _generate_fallback_plan, _normalize_plan_for_site, _run_benchmark_evaluation


class _FakeTraceWriter:
    def __init__(self, run_dir: Path) -> None:
        self.run_dir = run_dir
        self.manifest_path = run_dir / 'manifest.json'



def test_kleki_skyscraper_fallback_includes_render_reset_segments_and_checkpoints() -> None:
    plan = _generate_fallback_plan(
        'Draw a skyscraper with exhaustive facade detail and grayscale shading.',
        'https://kleki.com',
        720,
        450,
    )
    actions = [step.get('action') for step in plan]

    assert actions[0] == 'kleki_clear_canvas'
    assert actions[1] == 'kleki_reset_render_state'
    assert 'draw_segments' in actions
    assert 'visual_assert' in actions
    assert any(step.get('action') == 'kleki_set_scatter' for step in plan)



def test_kleki_normalization_injects_render_reset_and_art_checkpoints() -> None:
    plan = [
        {'action': 'clear_canvas', 'args': {}, 'description': 'Clear canvas'},
        {'action': 'draw_path', 'args': {'vertices': [[850, 1550], [1250, 400]]}, 'description': 'Draw the front face left vertical edge of the skyscraper'},
        {'action': 'draw_path', 'args': {'vertices': [[1050, 1500], [1450, 1500], [1050, 1410], [1450, 1410]]}, 'description': 'Draw horizontal lines for the facade grid'},
    ]
    normalized = _normalize_plan_for_site(plan, 'https://kleki.com', 'Draw a skyscraper with exhaustive facade detail and profuse grayscale shading.')
    actions = [step.get('action') for step in normalized]
    assert actions[0] == 'kleki_clear_canvas'
    assert actions[1] == 'kleki_reset_render_state'
    assert actions[2] == 'draw_segments'
    assert actions[3] == 'visual_assert'
    assert 'visual_assert' in actions



def test_run_benchmark_evaluation_art_claims_penalize_bad_architectural_output(tmp_path: Path) -> None:
    run_dir = tmp_path / 'runs' / 'art_quality_001'
    run_dir.mkdir(parents=True)

    manifest = {
        'run_id': 'art_quality_001',
        'task_id': 'DRAW_SKYSCRAPER_ARCH',
        'task_description': 'Draw a tall modern skyscraper in one-point perspective with exhaustive facade detail and profuse grayscale shading.',
        'outcome': 'failure',
        'total_duration_ms': 123000,
        'agent_config': {'url': 'https://kleki.com'},
    }
    (run_dir / 'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')

    trace_lines = [
        {'step': 1, 'action': {'type': 'kleki_reset_render_state', 'parameters': {}}, 'action_result': {'success': True}},
        {'step': 2, 'action': {'type': 'kleki_set_scatter', 'parameters': {}}, 'action_result': {'success': True}},
        {'step': 3, 'action': {'type': 'draw_segments', 'parameters': {}}, 'action_result': {'success': True}},
        {'step': 4, 'action': {'type': 'draw_path', 'parameters': {}}, 'action_result': {'success': True}},
        {'step': 997, 'action': {'type': 'final_verification_gate', 'parameters': {}}, 'action_result': {'success': False}, 'post_state': {
            'constraints': [
                {'description': 'Canvas is not empty — visible drawing/content present', 'category': 'existence', 'satisfied': True},
                {'description': 'Drawing fills a substantial portion of the canvas (>30%)', 'category': 'composition', 'satisfied': False, 'critique': 'Coverage too small.'},
                {'description': 'A recognizable tall skyscraper or high-rise building is clearly present', 'category': 'subject', 'satisfied': False, 'critique': 'Not recognizable.'},
                {'description': 'Facade structure such as windows, panel lines, or architectural subdivisions is visible', 'category': 'subject', 'satisfied': False, 'critique': 'Facade not legible.'},
                {'description': 'The structure follows a coherent perspective rather than random line directions', 'category': 'subject', 'satisfied': False, 'critique': 'Perspective broken.'},
                {'description': 'Rich, abundant detail throughout', 'category': 'subject', 'satisfied': False, 'critique': 'Too sparse.'},
                {'description': 'No obvious scatter-noise contamination breaks up the intended tonal passes', 'category': 'subject', 'satisfied': False, 'critique': 'Scatter noise visible.'},
            ],
            'deficiencies': ['Coverage too small.', 'Not recognizable.', 'Facade not legible.', 'Perspective broken.', 'Too sparse.', 'Scatter noise visible.'],
        }},
    ]
    with open(run_dir / 'trace.jsonl', 'w', encoding='utf-8') as f:
        for line in trace_lines:
            f.write(json.dumps(line) + '\n')

    payload = _run_benchmark_evaluation(
        _FakeTraceWriter(run_dir),
        plan=[{'action': 'kleki_reset_render_state'}, {'action': 'draw_segments'}, {'action': 'draw_path'}],
    )
    assert payload is not None
    detail = {item['description']: item for item in payload['claims_detail']}
    assert payload['claims_total'] == 13
    assert detail['Art output is a recognizable subject']['satisfied'] is False
    assert detail['Art output maintains perspective coherence']['satisfied'] is False
    assert detail['Art facade or structural subdivisions remain legible']['satisfied'] is False
    assert detail['Art detail density matches the requested fidelity']['satisfied'] is False
    assert detail['Art render state remained normalized and controlled']['satisfied'] is False
