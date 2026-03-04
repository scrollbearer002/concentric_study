#!/bin/bash
# Enterprise GUI Agent - Execution wrapper
# Handles virtual env, secure API key, cleanup, and Python agent invocation.

set -e

echo "========================================"
echo "  Enterprise GUI Agent Initializing"
echo "========================================"

# 1. Activate virtual environment if present
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "[✓] Virtual environment activated."
elif [ -d "../venv" ]; then
    source ../venv/bin/activate
    echo "[✓] Virtual environment activated."
else
    echo "[!] No 'venv' found. Using system Python."
fi

# 2. Secure API key handling
if [ -z "$GEMINI_API_KEY" ] && [ -z "$OPENAI_API_KEY" ]; then
    echo -n "Enter your Gemini API Key: "
    read -s API_KEY_INPUT
    echo ""
    export GEMINI_API_KEY="$API_KEY_INPUT"
    echo "[✓] API Key exported to environment."
else
    echo "[✓] API Key detected in environment."
fi

# 3. Clean up old state files before running
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
rm -f "$SCRIPT_DIR/current_state.png" "$SCRIPT_DIR/som_overlay.png" "$SCRIPT_DIR/som_red.png" "$SCRIPT_DIR/color_menu_state.png"

# 4. Run from operator directory so imports resolve
OPERATOR_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$OPERATOR_DIR"
export PYTHONPATH="$OPERATOR_DIR:$PYTHONPATH"
echo "[✓] PYTHONPATH=$PYTHONPATH"
echo "----------------------------------------"
python3 "$SCRIPT_DIR/test_excalidraw_enterprise.py"

# 5. Deactivate on exit
if [ -n "$VIRTUAL_ENV" ]; then
    deactivate 2>/dev/null || true
fi
