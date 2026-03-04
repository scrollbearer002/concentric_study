# Quick Start Guide

## Current Status

✅ **Structure Verified**: All core files are in place
- `agent_core.py` - MacOSAgentCore (Quartz events)
- `visual_engine.py` - VisualGroundingEngine (Set-of-Mark)
- `codex_client.py` - CodexClient (fallback)
- `vlm_coordinator.py` - VLMCoordinator (fallback)
- `cre/test_excalidraw_covt.py` - Main test

## Setup (One-Time)

### 1. Create Virtual Environment

```bash
cd /Users/christianpardo/Desktop/concentric_study/operator
python3 -m venv venv
```

### 2. Install Dependencies

```bash
./venv/bin/pip install -r requirements-base.txt
```

This installs the primary current runtime:
- `pyobjc-framework-Cocoa` - macOS Cocoa framework
- `pyobjc-framework-Quartz` - Quartz event posting
- `google-genai` - Gemini API client
- `pydantic` - Data validation
- `Pillow` - Image processing

Optional enhancement packs:

```bash
./venv/bin/pip install -r requirements-optional.txt
./venv/bin/pip install -r requirements-legacy.txt
```

- `requirements-optional.txt` adds pHash, numpy/scipy math, semantic retrieval, and alternate a11y backends
- `requirements-legacy.txt` adds the older Hammerspoon/OpenAI path
- `requirements.txt` remains as a compatibility umbrella for older setup flows

### 3. Set API Key

```bash
export GEMINI_API_KEY='your-api-key-here'
# OR
export OPENAI_API_KEY='your-api-key-here'
```

## Running Tests

### Dry Run (Safe - No Mouse/Keyboard Control)

```bash
cd /Users/christianpardo/Desktop/concentric_study/operator
CONCENTRIC_DRY_RUN=1 PYTHONPATH=$(pwd) ./venv/bin/python cre/test_dry_run_flow.py
```

### Coordinate Math Test (No Dependencies)

```bash
cd /Users/christianpardo/Desktop/concentric_study/operator
./venv/bin/python cre/test_coordinate_math.py
```

### Full Test (Requires Safari + Excalidraw)

```bash
cd /Users/christianpardo/Desktop/concentric_study/operator
CONCENTRIC_TRIANGLES_CLEAN=1 PYTHONPATH=$(pwd) ./venv/bin/python cre/test_excalidraw_covt.py
```

**Note**: The full test will:
1. Open Safari to Excalidraw
2. Clear the canvas
3. Draw 4 concentric triangles
4. Take control of your mouse/keyboard

## Verification

Run the verification script from the project root:

```bash
cd /Users/christianpardo/Desktop/concentric_study
python3 verify_setup.py
```

Expected output after installing dependencies:
- ✅ All imports succeed
- ✅ Test file found
- ✅ Requirements found

## Study Files

The hot-path study file is at:
- `cre/study_concentric_logic.py` - Minimal 12-step flow
- `cre/INITIALIZATION_REPORT.md` - Full architectural audit

## Troubleshooting

### Import Errors
- Ensure `PYTHONPATH=$(pwd)` is set when running tests
- Verify virtual environment is activated or use `./venv/bin/python`

### Missing Dependencies
- Run `./venv/bin/pip install -r requirements-base.txt` again
- Add `requirements-optional.txt` or `requirements-legacy.txt` only if your path needs them
- Check the appropriate requirements file exists in `operator/`

### Quartz/AppKit Errors
- These are macOS-only frameworks
- Ensure you're on macOS
- Install via `pip install pyobjc-framework-Cocoa pyobjc-framework-Quartz`
