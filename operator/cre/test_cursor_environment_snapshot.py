from pathlib import Path
import importlib.util
import sys

MODULE_PATH = Path(__file__).resolve().parent / 'tools' / 'cursor_environment_snapshot.py'
spec = importlib.util.spec_from_file_location('cursor_environment_snapshot', MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


def test_diff_snapshots_detects_changes():
    previous = {
        'app': {'version': {'value': '2.5.25', 'provenance': 'direct_product_json'}},
        'runtime': {'electron': {'value': '39.4.0', 'provenance': 'direct_runtime'}},
    }
    current = {
        'app': {'version': {'value': '2.5.26', 'provenance': 'direct_product_json'}},
        'runtime': {'electron': {'value': '39.4.0', 'provenance': 'direct_runtime'}},
    }
    diff = mod.diff_snapshots(previous, current)
    assert diff['has_changes'] is True
    assert diff['changed']['app.version']['before'] == '2.5.25'
    assert diff['changed']['app.version']['after'] == '2.5.26'


def test_diff_snapshots_no_changes_when_values_match():
    current = {
        'app': {'version': {'value': '2.5.26', 'provenance': 'direct_product_json'}},
        'runtime': {'electron': {'value': '39.4.0', 'provenance': 'direct_runtime'}},
    }
    diff = mod.diff_snapshots(current, current)
    assert diff['has_changes'] is False
    assert diff['changed'] == {}
    assert diff['added'] == {}
    assert diff['removed'] == {}
