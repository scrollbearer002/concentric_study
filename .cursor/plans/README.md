# Cursor Plans

This directory stores durable Cursor plans for recurring repo workflows.

Use these plans when:
- the task is non-trivial or cross-file
- the task mixes research and implementation
- a browser/debugging loop needs explicit evidence capture
- an MCP rollout or integration change needs a bounded path

Plan discipline:
- start with `/plan` for non-trivial work
- keep one plan per objective
- preserve the exact decision question, not just the steps
- include a Mermaid block when sequence or branching matters
- update the plan when the branch meaningfully changes
- include explicit pass/fail and stop/rollback criteria

Suggested template:
- `evidence-gated-task-template.md`

Current plans:
- `context7-pilot.md`
- `debug-runtime-regression.md`
- `add-internal-mcp.md`
- `research-before-runtime.md`
- `browser-task-triage.md`
- `cursor-intelligence-bootstrap.md`
- `cursor-intelligence-activation-2026-03-05.md`
- `live-visual-control-demo-2026-03-05.md`
