#!/usr/bin/env bash
# Idempotent Cloud Agent bootstrap for the concentric_study repo.
#
# This project is a macOS GUI-automation agent, but its shared infrastructure
# package (operator/agent_infra) and the bulk of the cre/ pytest suite are pure
# Python and run on the Linux Cloud Agent substrate. This script provisions the
# Linux development/test environment. The macOS-only GUI path (pyobjc/Quartz +
# live Safari) cannot run here and is not installed.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT/operator"

# Ensure the venv module is available. On Debian/Ubuntu it ships separately as
# python3-venv, which minimal base images may omit.
ensure_venv_pkg() {
  if command -v sudo >/dev/null 2>&1; then
    sudo apt-get update -y
    sudo apt-get install -y python3-venv
  else
    apt-get update -y
    apt-get install -y python3-venv
  fi
}

if [ ! -x venv/bin/python ]; then
  if ! python3 -m venv venv 2>/dev/null; then
    echo "python3 -m venv failed; installing python3-venv and retrying..."
    ensure_venv_pkg
    rm -rf venv
    python3 -m venv venv
  fi
fi

./venv/bin/python -m pip install --upgrade pip
./venv/bin/pip install -r requirements-dev.txt

echo "-----------------------------------------------------------------------"
echo "concentric_study Linux dev environment ready."
echo "Run the test suite with:"
echo "  cd operator && ./venv/bin/python -m pytest cre/test_*.py -v --tb=short"
echo "(macOS-only GUI test modules are skipped/uncollectable on Linux.)"
echo "-----------------------------------------------------------------------"
