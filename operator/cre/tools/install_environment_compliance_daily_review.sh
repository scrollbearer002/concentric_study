#!/bin/zsh
set -euo pipefail

REPO_ROOT="${1:-$HOME/Desktop/concentric_study}"
PYTHON_BIN="${2:-$(command -v python3)}"
REVIEW_SCRIPT_PATH="$REPO_ROOT/operator/cre/tools/review_environment_compliance.py"
AUTOMATION_ROOT="$HOME/Library/Application Support/ConcentricStudy/environment_compliance"
AUTOMATION_SCRIPT_DIR="$HOME/Library/Application Support/ConcentricStudy/tools"
AUTOMATION_SCRIPT_PATH="$AUTOMATION_SCRIPT_DIR/review_environment_compliance.py"
PLIST_PATH="$HOME/Library/LaunchAgents/com.concentricstudy.environment-compliance-daily.plist"
LOG_DIR="$AUTOMATION_ROOT/logs"
REPO_LOG="$REPO_ROOT/operator/cre/artifacts/environment_answer_compliance_log.jsonl"
AUTOMATION_LOG="$AUTOMATION_ROOT/environment_answer_compliance_log.jsonl"
AUTOMATION_JSON="$AUTOMATION_ROOT/latest_review.json"
AUTOMATION_MD="$AUTOMATION_ROOT/latest_review.md"

mkdir -p "$LOG_DIR"
mkdir -p "$AUTOMATION_SCRIPT_DIR"

if [[ ! -f "$REVIEW_SCRIPT_PATH" ]]; then
  echo "review script not found: $REVIEW_SCRIPT_PATH" >&2
  exit 1
fi

cp "$REVIEW_SCRIPT_PATH" "$AUTOMATION_SCRIPT_PATH"

# Seed the automation log from the repo-local log on first install so daily review
# starts with real history without requiring Desktop access later.
if [[ -f "$REPO_LOG" && ! -f "$AUTOMATION_LOG" ]]; then
  cp "$REPO_LOG" "$AUTOMATION_LOG"
fi

cat > "$PLIST_PATH" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.concentricstudy.environment-compliance-daily</string>
  <key>ProgramArguments</key>
  <array>
    <string>$PYTHON_BIN</string>
    <string>$AUTOMATION_SCRIPT_PATH</string>
    <string>--log</string>
    <string>$AUTOMATION_LOG</string>
    <string>--json-out</string>
    <string>$AUTOMATION_JSON</string>
    <string>--md-out</string>
    <string>$AUTOMATION_MD</string>
  </array>
  <key>WorkingDirectory</key>
  <string>$HOME</string>
  <key>StartCalendarInterval</key>
  <dict>
    <key>Hour</key>
    <integer>9</integer>
    <key>Minute</key>
    <integer>20</integer>
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

launchctl bootout "gui/$(id -u)/com.concentricstudy.environment-compliance-daily" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST_PATH"
launchctl kickstart -k "gui/$(id -u)/com.concentricstudy.environment-compliance-daily"

echo "Installed daily environment compliance review: $PLIST_PATH"
echo "Automation root: $AUTOMATION_ROOT"
