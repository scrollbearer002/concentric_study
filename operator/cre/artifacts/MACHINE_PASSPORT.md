# Machine Passport

Captured locally on Christian's MacBook Air on 2026-07-30 at approximately 13:20 PDT. This is a facts-only snapshot, not a desired-state specification. Serial number, hardware UUID, provisioning UDID, usernames in command output, and credentials are intentionally omitted.

## Identity and hardware

- Host class: MacBook Air
- Model identifier: `MacBookAir10,1`
- Model number: `MGN63LL/A`
- Chip: Apple M1 (`arm64`)
- CPU: 8 cores (4 performance, 4 efficiency)
- Memory: 8 GB (8,589,934,592 bytes)
- Activation Lock: enabled
- Rosetta 2: not installed/reported false by Homebrew

## Operating system

- macOS: 26.5.1
- Build: `25F80`
- Darwin kernel: 25.5.0, `RELEASE_ARM64_T8103`
- Command Line Tools: 26.5
- Full Xcode: not installed
- Root APFS view at capture: 228 GiB total, 34 GiB available

## Cursor

- `/Applications/Cursor.app`: present
- Version: 3.13.25
- Commit: `31e8d61c448c7472e371505838a0fe34083dad50`
- Architecture: `arm64`
- Bundle identifier: `com.todesktop.230313mzl4w4u92`
- Embedded `cursor` launcher: present
- Standalone `agent` CLI on `PATH`: absent
- Installed Cursor extensions:
  - `anysphere.cursorpyright`
  - `anysphere.remote-ssh`
  - `eamodio.gitlens`
  - `github.vscode-github-actions`
  - `ms-azuretools.vscode-containers`
  - `ms-azuretools.vscode-docker`
  - `ms-python.debugpy`
  - `ms-python.python`
  - `openai.chatgpt`

## Homebrew and developer runtimes

- Homebrew prefix: `/opt/homebrew`
- Homebrew version after the live inventory: 6.0.13
- Installed formulae: 164
- Installed casks: 4 (`hammerspoon`, `min`, `obs`, `xcodes-app`)
- The inventory check reported 104 outdated formulae and 3 outdated casks.
- Homebrew warned that the `mobile-dev-inc/tap`, `wix/brew`, and `xcodesorg/made` taps were not trusted.
- Python resolution:
  1. `/opt/homebrew/bin/python3`
  2. `/usr/bin/python3`
- Active Python: 3.14.3
- Active pip: 26.0
- Git: 2.50.1 (Apple Git-155)
- GitHub CLI: 2.86.0
- Node.js: 22.21.1
- npm: 10.9.4
- Deno: 2.7.10
- uv: 0.10.12
- Docker CLI: 29.2.0

Notable installed formulae relevant to this repository include `cliclick`, `cocoapods`, `d2`, `deno`, `direnv`, `ffmpeg`, `gh`, `git-lfs`, `graphviz`, `node`, `nmap`, `pandoc`, `python@3.14`, `ripgrep`, `semgrep`, `tesseract`, `uv`, `watchman`, `whisper-cpp`, `xcodegen`, and `yt-dlp`.

## Hammerspoon and macOS permissions

- `/Applications/Hammerspoon.app`: present
- Version: 1.1.1
- Bundle identifier: `org.hammerspoon.Hammerspoon`

Direct read-only inspection of the user and system TCC databases succeeded. In TCC, `auth_value = 2` is an allow record and `auth_value = 0` is a deny record.

Cursor has allow records for Accessibility, Developer Tool, Input Monitoring/listen events, posting events, Screen Recording, and Full Disk Access. It also has allowed Apple Events records for Safari, Terminal, TextEdit, Finder, Freeform, Mail, Reminders, System Events, and Min. Cursor has a deny record for QuickTime Player automation, plus deny/limited records for some user-data scopes (including Documents and Media Library). This is not equivalent to unrestricted access to every app or data class.

Hammerspoon has allow records for Accessibility, Developer Tool, Input Monitoring/listen events, Screen Recording, Full Disk Access, Bluetooth, and app-bundle access.

No TCC setting was changed during capture.

## Repository HostToolHealth

The package-style invocation:

`PYTHONPATH=operator python3 -m agent_infra.host_tool_health`

did not reach the health check because importing `agent_infra` transitively required Pillow, which is missing from the active Python 3.14 environment (`ModuleNotFoundError: PIL`).

Running the checker directly:

`python3 operator/agent_infra/host_tool_health.py`

completed and returned a non-zero status with this summary:

- Required classes: `runtime_python_selected`, `macos_ui_automation`, `native_event_backend`, `screen_capture`
- Selected browser target: `safari_bundle`
- Selected credential backend: `security_cli`
- Selected macOS UI automation: `osascript_system_events`
- Selected screen capture: `screencapture_cli`
- Missing required classes: `native_event_backend`, `runtime_python_selected`
- `all_required_ready`: false

This machine is therefore locally capable but not currently green according to the repository's own readiness gate.

## Follow-up HostToolHealth (project venv)

Re-run with `operator/venv/bin/python` on 2026-07-30 (local laptop agent follow-up):

- `native_event_backend` → `pyobjc_native_stack` (AppKit/Quartz OK in project venv)
- `macos_ui_automation` → `osascript_system_events`
- `screen_capture` → `screencapture_cli`
- `browser_target` → `safari_bundle`
- `credential_backend` → `security_cli` (optional)
- Missing required: `runtime_python_selected` — venv exists, but `venv_core_imports` timed out after 5s (`pydantic`, `requests`, `PIL`, `google.genai`, `numpy`)
- `all_required_ready`: false

Interpretation: substrate is mostly present; the remaining red gate looks like a cold-import timeout on an 8 GB M1 under a hard 5s subprocess limit, not a missing PyObjC stack.

## Installed application sample

Relevant applications observed in `/Applications` include Cursor, Docker, Hammerspoon, Min, OBS, Obsidian, ProtonVPN, Safari, Xcodes, and Zotero.

## Capture notes

- The configured workspace path `/Users/christianpardo/Desktop/concentric_study_strong_v2` did not exist.
- The active repository copy used for this capture resolved to `/Users/christianpardo/Desktop/Desktop - Christian’s MacBook Air/concentric_study_strong_v2`.
- No application, package, permission, or repository content was uninstalled or wiped.
- Homebrew's standard outdated-package query auto-updated Homebrew itself and repository metadata before the auto-update was stopped; the version above is the post-check live value.
