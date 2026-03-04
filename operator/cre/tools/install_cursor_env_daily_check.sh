#!/bin/zsh
set -euo pipefail

REPO_ROOT="${1:-$HOME/Desktop/concentric_study}"
PYTHON_BIN="${2:-$(command -v python3)}"
SCRIPT_PATH="$REPO_ROOT/operator/cre/tools/cursor_environment_snapshot.py"
AUTOMATION_ROOT="$HOME/Library/Application Support/ConcentricStudy/cursor_environment"
AUTOMATION_SCRIPT_DIR="$HOME/Library/Application Support/ConcentricStudy/tools"
AUTOMATION_SCRIPT_PATH="$AUTOMATION_SCRIPT_DIR/cursor_environment_snapshot.py"
PLIST_PATH="$HOME/Library/LaunchAgents/com.concentricstudy.cursor-env-daily.plist"
LOG_DIR="$AUTOMATION_ROOT/logs"
mkdir -p "$LOG_DIR"
mkdir -p "$AUTOMATION_SCRIPT_DIR"

if [[ ! -f "$SCRIPT_PATH" ]]; then
  echo "snapshot script not found: $SCRIPT_PATH" >&2
  exit 1
fi

cp "$SCRIPT_PATH" "$AUTOMATION_SCRIPT_PATH"

cat > "$PLIST_PATH" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.concentricstudy.cursor-env-daily</string>
  <key>ProgramArguments</key>
  <array>
    <string>$PYTHON_BIN</string>
    <string>$AUTOMATION_SCRIPT_PATH</string>
    <string>--output-root</string>
    <string>$AUTOMATION_ROOT</string>
  </array>
  <key>WorkingDirectory</key>
  <string>$HOME</string>
  <key>StartCalendarInterval</key>
  <dict>
    <key>Hour</key>
    <integer>9</integer>
    <key>Minute</key>
    <integer>0</integer>
  </dict>
  <key>StandardOutPath</key>
  <string>$LOG_DIR/stdout.log</string>
  <key>StandardErrorPath</key>
  <string>$LOG_DIR/stderr.log</string>
  <key>RunAtLoad</key>
  <true/>
</dict>
</plist>
PLIST

launchctl bootout "gui/$(id -u)/com.concentricstudy.cursor-env-daily" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST_PATH"
launchctl kickstart -k "gui/$(id -u)/com.concentricstudy.cursor-env-daily"

echo "Installed daily Cursor environment check: $PLIST_PATH"
echo "Snapshots will be written under: $AUTOMATION_ROOT"
echo "Manual repo-local snapshots can still be written under: $REPO_ROOT/operator/cre/artifacts/cursor_environment"
