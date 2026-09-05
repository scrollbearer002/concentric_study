# Magnitude Setup (inspired recreation)
#
# Isolated experimental package under operator/magnitude_setup/.
# Profiles this machine, ranks local models, and walks through
# Choose model → Install model → Select harness.
#
# Inspired by Magnitude (https://magnitude.dev/, Apache-2.0).
# This is NOT the official @magnitudedev/cli.

## Quick start

```bash
cd operator
pip install textual rich psutil pytest
PYTHONPATH=. python -m magnitude_setup setup --rich-demo
PYTHONPATH=. python -m magnitude_setup setup --json --demo
PYTHONPATH=. python -m magnitude_setup rank --preference Smarter
```

Interactive Textual TUI (requires a real TTY):

```bash
PYTHONPATH=. python -m magnitude_setup setup --demo
```

## What it writes

Default output directory: `operator/cre/runs/magnitude_setup_demo/`

- `local_model_setup.json` — selected model, scores, harness, endpoint hint
- `local_model.env` — `CONCENTRIC_LOCAL_MODEL` / `CONCENTRIC_ENABLE_LOCAL` for operator tooling

## Classification

`isolated experimental branch to avoid weakening the core`

Does not modify `agent_infra/` or the Excalidraw hot path.
