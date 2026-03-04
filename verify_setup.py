#!/usr/bin/env python3
"""Quick verification that all required files are present and importable."""

import sys
import subprocess
from pathlib import Path

operator_dir = Path(__file__).parent / "operator"
venv_python = operator_dir / "venv" / "bin" / "python"

print("Checking setup...")

# Check if venv exists and use it, otherwise use system Python
if venv_python.exists():
    print("✅ Virtual environment found")
    python_cmd = str(venv_python)
else:
    print("⚠️  Virtual environment not found, using system Python")
    python_cmd = sys.executable
    # Add operator to path for system Python
    sys.path.insert(0, str(operator_dir))

print("\nChecking imports...")

# Check core files using the appropriate Python
import_cmd = f"""
import sys
sys.path.insert(0, '{operator_dir}')
try:
    from agent_core import MacOSAgentCore
    print('✅ agent_core.py')
except ImportError as e:
    print(f'❌ agent_core.py: {{e}}')

try:
    from visual_engine import VisualGroundingEngine
    print('✅ visual_engine.py')
except ImportError as e:
    print(f'❌ visual_engine.py: {{e}}')

try:
    from codex_client import CodexClient
    print('✅ codex_client.py')
except ImportError as e:
    print(f'❌ codex_client.py: {{e}}')

try:
    from vlm_coordinator import VLMCoordinator
    print('✅ vlm_coordinator.py')
except ImportError as e:
    print(f'❌ vlm_coordinator.py: {{e}}')
"""

result = subprocess.run([python_cmd, "-c", import_cmd], capture_output=True, text=True, cwd=str(operator_dir))
print(result.stdout)
if result.stderr:
    print(result.stderr, file=sys.stderr)

# Check test file
test_path = operator_dir / "cre" / "test_excalidraw_covt.py"
if test_path.exists():
    print(f"✅ Test file: {test_path}")
else:
    print(f"❌ Test file missing: {test_path}")

# Check requirements
req_path = operator_dir / "requirements.txt"
if req_path.exists():
    print(f"✅ Requirements: {req_path}")
else:
    print(f"❌ Requirements missing: {req_path}")

print("\n" + "="*60)
print("Setup verification complete!")
print("="*60)

if venv_python.exists():
    print("\n✅ Dependencies installed!")
    print("\nNext steps:")
    print("1. Set API key: export GEMINI_API_KEY='your-key'")
    print("2. Run test:")
    print("   cd operator")
    print("   CONCENTRIC_TRIANGLES_CLEAN=1 PYTHONPATH=$(pwd) ./venv/bin/python cre/test_excalidraw_covt.py")
else:
    print("\n⚠️  Virtual environment not found!")
    print("\nNext steps:")
    print("1. Install dependencies: cd operator && python3 -m venv venv && ./venv/bin/pip install -r requirements.txt")
    print("2. Set API key: export GEMINI_API_KEY='your-key'")
    print("3. Run test: CONCENTRIC_TRIANGLES_CLEAN=1 PYTHONPATH=$(pwd) ./venv/bin/python cre/test_excalidraw_covt.py")
