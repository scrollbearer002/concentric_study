#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import plistlib
import platform
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

APP_PATH = Path('/Applications/Cursor.app')
INFO_PLIST = APP_PATH / 'Contents' / 'Info.plist'
PRODUCT_JSON = APP_PATH / 'Contents' / 'Resources' / 'app' / 'product.json'
PACKAGE_JSON = APP_PATH / 'Contents' / 'Resources' / 'app' / 'package.json'
BINARY_PATH = APP_PATH / 'Contents' / 'MacOS' / 'Cursor'
ARTIFACT_ROOT = Path('operator/cre/artifacts/cursor_environment')
DIFF_IGNORED_KEYS = {'captured_at_utc'}


@dataclass
class SnapshotResult:
    snapshot: dict[str, Any]
    previous: dict[str, Any] | None
    diff: dict[str, Any]
    paths: dict[str, str]


def _run(cmd: list[str], timeout: float = 5.0) -> str:
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=True)
    return proc.stdout.strip()


def _safe_run(cmd: list[str], timeout: float = 5.0) -> str | None:
    try:
        return _run(cmd, timeout=timeout)
    except Exception:
        return None


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _load_plist(path: Path) -> dict[str, Any]:
    with path.open('rb') as f:
        return plistlib.load(f)


def _get_runtime_versions() -> dict[str, Any]:
    expr = 'JSON.stringify({node:process.versions.node,electron:process.versions.electron,chromium:process.versions.chrome,v8:process.versions.v8})'
    output = _safe_run([str(BINARY_PATH), '-p', expr], timeout=8.0)
    if not output:
        return {
            'node_js': {'value': None, 'provenance': 'unavailable'},
            'electron': {'value': None, 'provenance': 'unavailable'},
            'chromium': {'value': None, 'provenance': 'unavailable'},
            'v8': {'value': None, 'provenance': 'unavailable'},
        }
    data = json.loads(output)
    return {
        'node_js': {'value': data.get('node'), 'provenance': 'direct_runtime'},
        'electron': {'value': data.get('electron'), 'provenance': 'direct_runtime'},
        'chromium': {'value': data.get('chromium'), 'provenance': 'direct_runtime'},
        'v8': {'value': data.get('v8'), 'provenance': 'direct_runtime'},
    }


def collect_snapshot() -> dict[str, Any]:
    if not APP_PATH.exists():
        raise FileNotFoundError(f'Cursor app not found at {APP_PATH}')

    info = _load_plist(INFO_PLIST)
    product = _load_json(PRODUCT_JSON)
    package = _load_json(PACKAGE_JSON)
    runtime = _get_runtime_versions()

    sw_vers = {
        'product_name': _safe_run(['sw_vers', '-productName']),
        'product_version': _safe_run(['sw_vers', '-productVersion']),
        'build_version': _safe_run(['sw_vers', '-buildVersion']),
    }
    uname = platform.uname()

    quality = product.get('quality')
    build_type = quality.capitalize() if isinstance(quality, str) else None
    release_track = 'Default' if quality == 'stable' else quality.capitalize() if isinstance(quality, str) else None

    snapshot = {
        'captured_at_utc': datetime.now(timezone.utc).isoformat(),
        'app': {
            'path': str(APP_PATH),
            'name': {'value': info.get('CFBundleName') or product.get('nameLong'), 'provenance': 'direct_bundle'},
            'bundle_identifier': {'value': info.get('CFBundleIdentifier') or product.get('darwinBundleIdentifier'), 'provenance': 'direct_bundle'},
            'version': {'value': product.get('version') or info.get('CFBundleShortVersionString'), 'provenance': 'direct_product_json'},
            'bundle_version': {'value': info.get('CFBundleVersion'), 'provenance': 'direct_bundle'},
            'vscode_version': {'value': product.get('vscodeVersion'), 'provenance': 'direct_product_json'},
            'commit': {'value': product.get('commit'), 'provenance': 'direct_product_json'},
            'build_date': {'value': product.get('date'), 'provenance': 'direct_product_json'},
            'quality': {'value': quality, 'provenance': 'direct_product_json'},
            'build_type': {'value': build_type, 'provenance': 'inferred_from_quality'},
            'release_track': {'value': release_track, 'provenance': 'inferred_from_quality_and_absence_of_channel_metadata'},
            'author': {'value': (package.get('author') or {}).get('name'), 'provenance': 'direct_package_json'},
            'release_notes_url': {'value': product.get('releaseNotesUrl'), 'provenance': 'direct_product_json'},
        },
        'runtime': runtime,
        'host': {
            'os': {'value': sw_vers['product_name'], 'provenance': 'direct_sw_vers'},
            'os_version': {'value': sw_vers['product_version'], 'provenance': 'direct_sw_vers'},
            'os_build': {'value': sw_vers['build_version'], 'provenance': 'direct_sw_vers'},
            'kernel': {'value': uname.release, 'provenance': 'direct_platform'},
            'architecture': {'value': uname.machine, 'provenance': 'direct_platform'},
            'shell': {'value': os.environ.get('SHELL'), 'provenance': 'direct_environment'},
        },
    }
    return snapshot


def _flatten(prefix: str, obj: Any, out: dict[str, Any]) -> None:
    if isinstance(obj, dict):
        if set(obj.keys()) == {'value', 'provenance'}:
            out[prefix] = obj.get('value')
            return
        for k, v in obj.items():
            next_prefix = f'{prefix}.{k}' if prefix else k
            _flatten(next_prefix, v, out)
    else:
        out[prefix] = obj


def diff_snapshots(previous: dict[str, Any] | None, current: dict[str, Any]) -> dict[str, Any]:
    prev_flat: dict[str, Any] = {}
    curr_flat: dict[str, Any] = {}
    if previous:
        _flatten('', previous, prev_flat)
    _flatten('', current, curr_flat)

    added: dict[str, Any] = {}
    removed: dict[str, Any] = {}
    changed: dict[str, dict[str, Any]] = {}

    for key, value in curr_flat.items():
        if key in DIFF_IGNORED_KEYS:
            continue
        if key not in prev_flat:
            added[key] = value
        elif prev_flat[key] != value:
            changed[key] = {'before': prev_flat[key], 'after': value}
    for key, value in prev_flat.items():
        if key in DIFF_IGNORED_KEYS:
            continue
        if key not in curr_flat:
            removed[key] = value

    return {
        'has_changes': bool(added or removed or changed),
        'added': added,
        'removed': removed,
        'changed': changed,
    }


def _write_json(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + '\n')


def _build_report(snapshot: dict[str, Any], diff: dict[str, Any], previous_path: str | None) -> str:
    lines = [
        '# Cursor Environment Daily Report',
        '',
        f"Captured: `{snapshot['captured_at_utc']}`",
        '',
        '## Current Fingerprint',
        f"- Cursor version: `{snapshot['app']['version']['value']}`",
        f"- VS Code base: `{snapshot['app']['vscode_version']['value']}`",
        f"- Commit: `{snapshot['app']['commit']['value']}`",
        f"- Build date: `{snapshot['app']['build_date']['value']}`",
        f"- Quality: `{snapshot['app']['quality']['value']}`",
        f"- Build type: `{snapshot['app']['build_type']['value']}` ({snapshot['app']['build_type']['provenance']})",
        f"- Release track: `{snapshot['app']['release_track']['value']}` ({snapshot['app']['release_track']['provenance']})",
        f"- Electron: `{snapshot['runtime']['electron']['value']}`",
        f"- Chromium: `{snapshot['runtime']['chromium']['value']}`",
        f"- Node.js: `{snapshot['runtime']['node_js']['value']}`",
        f"- V8: `{snapshot['runtime']['v8']['value']}`",
        f"- macOS: `{snapshot['host']['os']['value']} {snapshot['host']['os_version']['value']}` build `{snapshot['host']['os_build']['value']}`",
        f"- Architecture: `{snapshot['host']['architecture']['value']}`",
        '',
        '## Drift Summary',
    ]
    if not previous_path:
        lines.append('- No previous snapshot found. This is the baseline.')
    elif not diff['has_changes']:
        lines.append(f'- No environment drift detected relative to `{previous_path}`.')
    else:
        lines.append(f'- Changes detected relative to `{previous_path}`.')
        if diff['changed']:
            lines.append('')
            lines.append('### Changed Fields')
            for key, payload in sorted(diff['changed'].items()):
                lines.append(f"- `{key}`: `{payload['before']}` -> `{payload['after']}`")
        if diff['added']:
            lines.append('')
            lines.append('### Added Fields')
            for key, value in sorted(diff['added'].items()):
                lines.append(f"- `{key}`: `{value}`")
        if diff['removed']:
            lines.append('')
            lines.append('### Removed Fields')
            for key, value in sorted(diff['removed'].items()):
                lines.append(f"- `{key}`: `{value}`")
    lines.extend([
        '',
        '## Notes',
        '- `build_type` and `release_track` are inferred from `product.json` quality metadata unless Cursor exposes more explicit channel metadata locally.',
        '- This report is intended to mirror the information shown in Cursor > About, but gathered automatically from the installed app bundle and runtime.',
    ])
    return '\n'.join(lines) + '\n'


def snapshot_to_paths(output_root: Path, snapshot: dict[str, Any]) -> dict[str, Path]:
    ts = snapshot['captured_at_utc'].replace(':', '').replace('-', '').replace('+00:00', 'Z')
    history_dir = output_root / 'history'
    latest_path = output_root / 'latest.json'
    history_path = history_dir / f'{ts}.json'
    diff_path = output_root / 'latest_diff.json'
    report_path = output_root / 'latest_report.md'
    return {
        'latest': latest_path,
        'history': history_path,
        'diff': diff_path,
        'report': report_path,
    }


def run_snapshot(output_root: Path) -> SnapshotResult:
    snapshot = collect_snapshot()
    paths = snapshot_to_paths(output_root, snapshot)
    previous = None
    previous_path = None
    if paths['latest'].exists():
        previous = json.loads(paths['latest'].read_text())
        previous_path = str(paths['latest'])
    diff = diff_snapshots(previous, snapshot)
    _write_json(paths['history'], snapshot)
    _write_json(paths['latest'], snapshot)
    _write_json(paths['diff'], diff)
    paths['report'].parent.mkdir(parents=True, exist_ok=True)
    paths['report'].write_text(_build_report(snapshot, diff, previous_path))
    return SnapshotResult(snapshot=snapshot, previous=previous, diff=diff, paths={k: str(v) for k, v in paths.items()})


def main() -> int:
    parser = argparse.ArgumentParser(description='Capture and diff the local Cursor environment fingerprint.')
    parser.add_argument('--output-root', default=str(ARTIFACT_ROOT), help='Directory where snapshots and reports will be written.')
    parser.add_argument('--print-json', action='store_true', help='Print the current snapshot JSON to stdout.')
    parser.add_argument('--print-report', action='store_true', help='Print the latest markdown report to stdout.')
    args = parser.parse_args()

    result = run_snapshot(Path(args.output_root))
    if args.print_json:
        print(json.dumps(result.snapshot, indent=2, sort_keys=True))
    if args.print_report:
        print(Path(result.paths['report']).read_text())
    if not args.print_json and not args.print_report:
        print(json.dumps({'paths': result.paths, 'has_changes': result.diff['has_changes']}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
