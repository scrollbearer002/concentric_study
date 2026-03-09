#!/bin/zsh
set -euo pipefail

REPO_ROOT="${1:-$HOME/Desktop/concentric_study}"
PYTHON_BIN="${2:-$(command -v python3)}"
SCRIPT_PATH="$REPO_ROOT/operator/cre/tools/verification_packet_walkthrough_reminder.py"
AUTOMATION_ROOT="$HOME/Library/Application Support/ConcentricStudy/verification_packet_walkthrough_reminder"
AUTOMATION_SCRIPT_DIR="$HOME/Library/Application Support/ConcentricStudy/tools"
AUTOMATION_SCRIPT_PATH="$AUTOMATION_SCRIPT_DIR/verification_packet_walkthrough_reminder.py"
PLIST_PATH="$HOME/Library/LaunchAgents/com.concentricstudy.verification-packet-walkthrough-reminder.plist"
LOG_DIR="$AUTOMATION_ROOT/logs"

mkdir -p "$LOG_DIR"
mkdir -p "$AUTOMATION_SCRIPT_DIR"

if [[ ! -f "$SCRIPT_PATH" ]]; then
  echo "reminder script not found: $SCRIPT_PATH" >&2
  exit 1
fi

cp "$SCRIPT_PATH" "$AUTOMATION_SCRIPT_PATH"

cat > "$PLIST_PATH" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.concentricstudy.verification-packet-walkthrough-reminder</string>
  <key>ProgramArguments</key>
  <array>
    <string>$PYTHON_BIN</string>
    <string>$AUTOMATION_SCRIPT_PATH</string>
    <string>--output-root</string>
    <string>$AUTOMATION_ROOT</string>
  </array>
  <key>WorkingDirectory</key>
  <string>$HOME</string>
  <key>StartInterval</key>
  <integer>86400</integer>
  <key>StandardOutPath</key>
  <string>$LOG_DIR/stdout.log</string>
  <key>StandardErrorPath</key>
  <string>$LOG_DIR/stderr.log</string>
</dict>
</plist>
PLIST

launchctl bootout "gui/$(id -u)/com.concentricstudy.verification-packet-walkthrough-reminder" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST_PATH"

echo "Installed 24-hour verification packet walkthrough reminder: $PLIST_PATH"
echo "Reminder logs will be written under: $AUTOMATION_ROOT"
echo "First reminder will arrive on the next 24-hour interval after load."
