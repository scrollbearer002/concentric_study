# Cursor Environment Monitor (PhD)

## Purpose
This adds a repeatable, evidence-backed way to fingerprint the local Cursor installation and detect drift over time.

It exists because Cursor behavior, UI, runtime quirks, and research conclusions are only valid relative to the installed local environment.
If Cursor updates, the operating assumptions can change.

## What is captured
The snapshot tool records:
- Cursor app version
- VS Code base version
- commit SHA
- build date
- quality
- build type
- release track
- bundle identifier
- runtime versions: Electron, Chromium, Node.js, V8
- host OS version, build, kernel, architecture

## Provenance model
Each important field is stored with provenance.

Examples:
- `direct_product_json`
- `direct_bundle`
- `direct_runtime`
- `direct_sw_vers`
- `inferred_from_quality`
- `inferred_from_quality_and_absence_of_channel_metadata`

This matters because not every field shown in Cursor > About is exposed through one source.
The monitor distinguishes direct observations from narrow inferences.

## Files
- snapshot tool: `operator/cre/tools/cursor_environment_snapshot.py`
- launchd installer: `operator/cre/tools/install_cursor_env_daily_check.sh`
- latest snapshot: `operator/cre/artifacts/cursor_environment/latest.json`
- latest diff: `operator/cre/artifacts/cursor_environment/latest_diff.json`
- latest report: `operator/cre/artifacts/cursor_environment/latest_report.md`
- history: `operator/cre/artifacts/cursor_environment/history/`
- unattended daily snapshots: `~/Library/Application Support/ConcentricStudy/cursor_environment/`

## Daily automation
Install the daily check with:

```bash
cd /Users/christianpardo/Desktop/concentric_study
./operator/cre/tools/install_cursor_env_daily_check.sh
```

This installs a per-user LaunchAgent that runs daily at `09:00` and also runs once at install time.
The LaunchAgent writes to `~/Library/Application Support/ConcentricStudy/cursor_environment/`
instead of the Desktop repo path so it does not trip macOS Desktop privacy controls.

Implementation basis:
- `launchd.plist(5)` local man page
- `launchctl(1)` local man page

## Manual run
```bash
cd /Users/christianpardo/Desktop/concentric_study
python3 operator/cre/tools/cursor_environment_snapshot.py --print-report
```

Manual runs continue to write repo-local artifacts under `operator/cre/artifacts/cursor_environment/`.

## Why this helps
This gives a daily evidence trail for:
- Cursor upgrades
- commit changes
- runtime stack changes
- macOS drift

That improves:
- reproducibility
- debugging quality
- environment-locked research
- accurate product and tooling guidance

## Current limitation
`build_type` and `release_track` are inferred from local quality metadata unless Cursor exposes a more explicit local channel field in the app bundle.
