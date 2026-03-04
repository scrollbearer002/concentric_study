#!/usr/bin/env bash
# CRE Showcase: demonstrate Codex Runtime Environment capabilities for colleagues.
# Run: bash operator/cre/showcase.sh
# With Hammerspoon running and config reloaded, shows live kernel + latency + capabilities.

set -euo pipefail

PORT="${CRE_PORT:-9999}"
URL="http://127.0.0.1:${PORT}"
ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT_DIR"

echo ""
echo "=============================================="
echo "  Codex Runtime Environment (CRE) — Showcase"
echo "=============================================="
echo ""

# --- 1. Kernel liveness ---
echo "1. Kernel liveness"
echo "   URL: $URL"
if curl -s -m 2 "$URL" >/dev/null 2>&1; then
  GET_RESP=$(curl -s -m 2 "$URL")
  echo "   GET /        -> \"$GET_RESP\""
  PING_RESP=$(curl -s -m 2 -X POST "$URL" -H "Content-Type: application/json" -d '{"command":"ping"}' 2>/dev/null || echo "{}")
  if echo "$PING_RESP" | grep -q '"status":"ok"'; then
    echo "   POST ping    -> status: ok"
    KERNEL_UP=1
  else
    echo "   POST ping    -> (unexpected: $PING_RESP)"
    KERNEL_UP=0
  fi
else
  echo "   Kernel not running (nothing listening on $URL)"
  echo "   To start: open Hammerspoon -> Reload Config (or copy operator/cre/codex_kernel.lua to ~/.hammerspoon/init.lua and reload)"
  KERNEL_UP=0
fi
echo ""

if [[ "${KERNEL_UP:-0}" -eq 0 ]]; then
  echo "2. Capabilities (when kernel is running)"
  echo "   ping           - Health check"
  echo "   click          - High-speed click at (x,y) — replaces cliclick"
  echo "   screenshot     - In-memory capture, optional region — replaces screencapture"
  echo "   dump_state     - App/window state + Electron AX hydration — replaces osascript"
  echo "   wait_for_window - Poll for app window (non-blocking friendly)"
  echo ""
  echo "3. How to drive the kernel"
  echo "   curl:  curl -s -X POST $URL -H 'Content-Type: application/json' -d '{\"command\":\"ping\"}'"
  echo "   Python: CodexClient(port=$PORT).ping() / .click(x,y) / .screenshot() / .get_ui_tree()"
  echo "   Bridge: bash ai-bridge/cre_send_command.sh ping '{}'"
  echo ""
  echo "4. Full CRE test suite (run when kernel is up)"
  echo "   bash operator/tests/run_cre_tests.sh"
  echo ""
  exit 0
fi

# --- 2. Latency sample ---
echo "2. Latency (POST ping, 20 iterations)"
LATENCY_LOG="$ROOT_DIR/operator/.tmp/showcase_latency.log"
mkdir -p "$(dirname "$LATENCY_LOG")"
: > "$LATENCY_LOG"
for i in $(seq 1 20); do
  start=$(python3 -c 'import time; print(time.perf_counter())' 2>/dev/null || echo "0")
  curl -s -m 2 -X POST "$URL" -H "Content-Type: application/json" -d '{"command":"ping"}' >/dev/null
  end=$(python3 -c 'import time; print(time.perf_counter())' 2>/dev/null || echo "0")
  python3 -c "print(round(($end - $start) * 1000, 2))" 2>/dev/null >> "$LATENCY_LOG" || true
done
if [[ -s "$LATENCY_LOG" ]]; then
  AVG_MS=$(python3 -c "
import sys
with open('$LATENCY_LOG') as f:
    vals = [float(x) for x in f if x.strip()]
print(round(sum(vals)/len(vals), 2) if vals else 0)
" 2>/dev/null || echo "0")
  echo "   Average: ${AVG_MS} ms (target: <10 ms for HTTP kernel)"
else
  echo "   (could not compute)"
fi
echo ""

# --- 3. Screenshot (size + timing) ---
echo "3. Screenshot (in-memory, no disk)"
start=$(python3 -c 'import time; print(time.perf_counter())' 2>/dev/null || echo "0")
SCREENSHOT_JSON=$(curl -s -m 10 -X POST "$URL" -H "Content-Type: application/json" -d '{"command":"screenshot","args":{}}' 2>/dev/null || echo "{}")
end=$(python3 -c 'import time; print(time.perf_counter())' 2>/dev/null || echo "0")
if echo "$SCREENSHOT_JSON" | grep -q '"data":'; then
  BYTES_EST=$(echo "$SCREENSHOT_JSON" | python3 -c "
import sys, json, base64
d = json.load(sys.stdin)
b64 = d.get('data','').split(',')[-1]
print(len(base64.b64decode(b64)) if b64 else 0)
" 2>/dev/null || echo "0")
  ELAPSED_MS=$(python3 -c "print(round(($end - $start) * 1000, 1))" 2>/dev/null || echo "?")
  echo "   Captured in ~${ELAPSED_MS} ms, size ~$BYTES_EST bytes (base64 decoded)"
  echo "   (Replaces: screencapture -x /tmp/... + disk read; CRE keeps capture in RAM)"
else
  echo "   (screenshot call failed or timed out)"
fi
echo ""

# --- 4. Dump state (Cursor if running) ---
echo "4. State introspection (dump_state)"
STATE_RESP=$(curl -s -m 3 -X POST "$URL" -H "Content-Type: application/json" -d '{"command":"dump_state","args":{"app":"Cursor"}}' 2>/dev/null || echo "{}")
if echo "$STATE_RESP" | grep -q '"status":"ok"'; then
  echo "   Cursor: $(echo "$STATE_RESP" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print('title=%s window=%s' % (d.get('title','?'), d.get('window','?')))
" 2>/dev/null || echo "$STATE_RESP")"
  echo "   (Replaces: osascript UI queries; uses hs.axuielement + Electron AX hydration)"
else
  echo "   Cursor not running or dump_state failed: $STATE_RESP"
fi
echo ""

# --- 5. Commands available ---
echo "5. Commands available on kernel"
echo "   ping, click, screenshot, dump_state, wait_for_window"
echo ""

# --- 6. How to run full suite ---
echo "6. Full CRE test suite"
echo "   bash operator/tests/run_cre_tests.sh"
echo "   (Phases 0–7: benchmarks, kernel, vision, input, state, wait, bridge, validation)"
echo ""
