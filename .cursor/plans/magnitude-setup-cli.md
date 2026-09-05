# Plan: Magnitude Setup CLI (inspired recreation)

## Objective
Recreate the Magnitude-style `setup` TUI shown in the reference screenshots:
profile this machine → rank local models → install → select agent harness.

## Classification
`isolated experimental branch to avoid weakening the core`

Does **not** modify `operator/agent_infra/*` or the Excalidraw hot path.
Lives under `operator/magnitude_setup/`.

## Environment basis
- System: Linux cloud agent VM (x86_64, ~16 GB RAM, 4 cores)
- Runtime: Python 3.12 + Textual + Rich + psutil
- Stakeholder goal: operational CLI demo matching screenshot UX
- Integration target: write harness config consumable by concentric local routing

## Scope (MVP that matches screenshots)
1. Hardware profile line (CPU / OS / cores / RAM / accel)
2. Preference slider: Fastest → Faster → Balanced → Smarter → Smartest
3. Recommended + On this computer lists
4. Detail pane with metadata + Unicode radar chart
5. Stepper: Choose model → Install model → Select harness
6. Progress bar during verify/install
7. Keyboard nav matching footer hints
8. Demo mode for headless verification (no real multi-GB downloads)

## Out of scope
- Full Magnitude inference server
- Real speculative-decoding engine
- Shipping as npm `@magnitudedev/cli` clone

## Pass / fail checkpoints
- `python -m magnitude_setup setup --demo --json` exits 0 and emits ranked models
- Unit tests for hardware, ranking, radar render
- Interactive TUI boots and screenshots/capture prove layout
- Config written after harness selection

## Stop / rollback
- If Textual cannot run in this terminal: keep `--demo` Rich renderer as strong path
- Do not merge into agent_infra until live non-regression evidence exists
