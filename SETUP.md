# Concentric Study Setup Guide

## What's Missing

Your Desktop copy needs the core implementation files that the test imports. Here's what was copied:

### Core Files (in `operator/`)
- `agent_core.py` - MacOSAgentCore (Quartz events, Gemini File API)
- `visual_engine.py` - VisualGroundingEngine (Set-of-Mark overlay)
- `codex_client.py` - CodexClient (fallback for Hammerspoon kernel)
- `vlm_coordinator.py` - VLMCoordinator (fallback VLM wrapper)
- `requirements.txt` - Python dependencies

### Test Files (in `operator/cre/`)
- `test_excalidraw_covt.py` - Main test with CONCENTRIC_TRIANGLES_CLEAN flow
- `study_concentric_logic.py` - Study file with hot-path functions
- All other cre/ files (evidence, specs, etc.)

## Setup Steps

### 1. Install Dependencies

```bash
cd /Users/christianpardo/Desktop/concentric_study/operator
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
```

### 2. Set API Key

```bash
export GEMINI_API_KEY='your-key'
# OR
export OPENAI_API_KEY='your-key'
```

### 3. Run the Test

```bash
cd /Users/christianpardo/Desktop/concentric_study/operator
CONCENTRIC_TRIANGLES_CLEAN=1 PYTHONPATH=$(pwd) ./venv/bin/python cre/test_excalidraw_covt.py
```

## Why It Didn't Work Before

The test file uses:
```python
sys.path.insert(0, str(Path(__file__).parent.parent))
```

This expects `cre/` to be inside an `operator/` directory with the core files (`agent_core.py`, `visual_engine.py`, etc.) as siblings.

The Desktop copy now has the correct structure:
```
concentric_study/
└── operator/
    ├── agent_core.py
    ├── visual_engine.py
    ├── codex_client.py
    ├── vlm_coordinator.py
    ├── requirements.txt
    └── cre/
        ├── test_excalidraw_covt.py
        ├── study_concentric_logic.py
        └── ... (other files)
```

## What the Test Does

When `CONCENTRIC_TRIANGLES_CLEAN=1` is set, it:
1. Clears the Excalidraw canvas (Cmd+Backspace + Enter)
2. Verifies canvas is empty (Gemini oracle)
3. Re-captures screenshot and gets true center (width/2, height/2)
4. Selects pen tool ('p')
5. Opens stroke color picker ('S')
6. Clicks black swatch (SoM + VLM extraction)
7. Draws 4 concentric triangles at center
8. Verifies final state (Gemini oracle)

## Enterprise Mode vs Legacy Mode

- **Enterprise Mode** (preferred): Uses `MacOSAgentCore` + `VisualGroundingEngine` (no Hammerspoon kernel needed)
- **Legacy Mode**: Falls back to `VLMCoordinator` + `CodexClient` (requires Hammerspoon kernel)

Enterprise mode activates when:
- `agent_core.py` and `visual_engine.py` are importable
- `GEMINI_API_KEY` or `OPENAI_API_KEY` is set
