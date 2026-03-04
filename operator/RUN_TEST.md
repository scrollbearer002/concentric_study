# Running the Concentric Triangles Test

## Fully Automated Flow

The test **automatically handles everything** - you don't need to:
- ❌ Open Safari manually
- ❌ Navigate to Excalidraw
- ❌ Clear the canvas
- ❌ Select tools
- ❌ Position the window

The test does all of this for you.

## What the Test Does Automatically

1. **Opens Safari**: `open -a Safari https://excalidraw.com`
2. **Waits 10 seconds** for page load
3. **Maximizes Safari window** (full screen)
4. **Clears canvas**: Cmd+Backspace → Enter → Verification
5. **Re-captures screenshot** and calculates true center (width/2, height/2)
6. **Selects pen tool**: Presses 'p'
7. **Opens stroke picker**: Presses 'S'
8. **Clicks black swatch**: Uses Set-of-Mark + VLM to find and click
9. **Draws 4 concentric triangles**: Sizes 220, 160, 100, 50
10. **Verifies final result**: Gemini oracle checks for 4 triangles

## Prerequisites

### 1. Install Dependencies

```bash
cd /Users/christianpardo/Desktop/concentric_study/operator
./venv/bin/pip install -r requirements-base.txt
```

Optional packs:

```bash
./venv/bin/pip install -r requirements-optional.txt
./venv/bin/pip install -r requirements-legacy.txt
```

Use `requirements-optional.txt` for extra perception/retrieval features and
`requirements-legacy.txt` only for the older Hammerspoon/OpenAI stack.

### 2. Set API Key

```bash
export GEMINI_API_KEY='your-api-key-here'
# OR
export OPENAI_API_KEY='your-api-key-here'
```

**Note**: The API key is required for:
- Visual state verification (oracle checks)
- Set-of-Mark coordinate extraction
- UI analysis

## Running the Test

### Full Automated Test

```bash
cd /Users/christianpardo/Desktop/concentric_study/operator
export GEMINI_API_KEY='your-api-key-here'
CONCENTRIC_TRIANGLES_CLEAN=1 PYTHONPATH=$(pwd) ./venv/bin/python cre/test_excalidraw_covt.py
```

### What Happens

1. **Test starts** → Logs initialization
2. **Safari opens** → Navigates to Excalidraw
3. **10-second wait** → Page loads
4. **Window maximizes** → Full screen
5. **Canvas cleared** → Cmd+Backspace + Enter
6. **Verification** → Gemini checks: "Is canvas empty?"
7. **Screenshot captured** → Center calculated: (1440, 900) for 2880×1800
8. **Pen selected** → 'p' keypress
9. **Stroke picker** → 'S' keypress  
10. **Black swatch clicked** → SoM + VLM extraction
11. **Triangles drawn** → 4 concentric triangles at center
12. **Final verification** → Gemini checks: "Are there 4 triangles?"

### Evidence Generated

The test creates evidence screenshots:
- `cre/step_01.png` through `cre/step_12.png`
- `cre/evidence_concentric_clean/report.html`
- `cre/concentric_triangles_clean_pass_log.txt`

## Safety Notes

⚠️ **The test will take control of your mouse and keyboard**

- Make sure no other windows need focus
- Close any important unsaved work
- The test runs for ~30-60 seconds
- You can interrupt with Ctrl+C

### Dry Run Mode (Safe)

To test the logic without actual control:

```bash
cd /Users/christianpardo/Desktop/concentric_study/operator
CONCENTRIC_DRY_RUN=1 PYTHONPATH=$(pwd) ./venv/bin/python cre/test_dry_run_flow.py
```

This logs what would happen without posting Quartz events.

## Troubleshooting

### Safari Doesn't Open
- Check macOS permissions for terminal/Python
- Try manually: `open -a Safari https://excalidraw.com`

### Canvas Not Clearing
- Ensure Safari is in focus
- Check that Excalidraw loaded fully (wait longer)

### API Errors
- Verify `GEMINI_API_KEY` is set correctly
- Check API quota/limits
- Test with: `echo $GEMINI_API_KEY`

### Import Errors
- Ensure `PYTHONPATH=$(pwd)` is set
- Verify dependencies installed: `./venv/bin/pip list`
- Run verification: `python3 ../verify_setup.py`

## Expected Output

```
[2026-02-21 HH:MM:SS] run_start | test_excalidraw_covt.py
[2026-02-21 HH:MM:SS] mode | Enterprise
[2026-02-21 HH:MM:SS] init | MacOSAgentCore + VisualGroundingEngine
[2026-02-21 HH:MM:SS] phase | PHASE 1: PAGE LOAD & INITIAL OBSERVATION
[2026-02-21 HH:MM:SS] safari_open | ok
[2026-02-21 HH:MM:SS] wait_start | 10 seconds
...
[2026-02-21 HH:MM:SS] PASS | clear_canvas
[2026-02-21 HH:MM:SS] PASS | triangle_1_of_4 | size=220
[2026-02-21 HH:MM:SS] PASS | triangle_4_of_4 | size=50
[2026-02-21 HH:MM:SS] PASS | draw_concentric_triangles
```

## Study Mode

The minimal hot-path version (without full test infrastructure):

```bash
cd /Users/christianpardo/Desktop/concentric_study/operator
CONCENTRIC_DRY_RUN=1 PYTHONPATH=$(pwd) ./venv/bin/python cre/study_concentric_logic.py
```

This shows the 12-step flow logic without executing.
