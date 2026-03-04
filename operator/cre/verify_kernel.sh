#!/usr/bin/env bash
# Verify Codex kernel is reachable without relying on the hs CLI (IPC).
# Usage: bash operator/cre/verify_kernel.sh
# After reloading Hammerspoon: GET and POST ping must succeed.

set -euo pipefail

PORT="${CRE_PORT:-9999}"
URL="http://127.0.0.1:${PORT}"

get_resp=$(curl -s -m 2 "$URL" 2>/dev/null || true)
if [[ -z "$get_resp" ]] || [[ "$get_resp" != *"Codex Kernel Active"* ]]; then
  echo "FAIL  Kernel not reachable at $URL (GET did not return 'Codex Kernel Active')"
  exit 1
fi

ping_resp=$(curl -s -m 2 -X POST "$URL" -H "Content-Type: application/json" -d '{"command":"ping"}' 2>/dev/null || true)
if [[ "$ping_resp" != *"\"status\":\"ok\""* ]] && [[ "$ping_resp" != *'"status":"ok"'* ]]; then
  echo "FAIL  POST ping did not return status ok (got: ${ping_resp:0:120})"
  exit 1
fi

echo "OK    Codex Kernel at $URL (GET and ping ok)"
exit 0
