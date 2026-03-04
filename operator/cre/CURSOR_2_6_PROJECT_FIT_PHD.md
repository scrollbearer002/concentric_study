# Cursor 2.6 Project Fit (PhD)

Date: `2026-03-04`

## Executive Summary

The best Cursor 2.6 implementation path for `concentric_study` is a local,
evidence-first operating layer plus a small read-only internal MCP surface.

What should be implemented now:
- durable `.cursor/plans/` artifacts
- split rules for planning, browser evidence, MCP governance, and runtime debug
- read-only internal MCP servers for repo-native health and trace access first
- explicit external MCP governance, with Context7 as the first validated pattern

What should not be treated as first-wave repo work:
- cloud agents
- Bugbot Autofix
- team marketplaces
- enterprise analytics surfaces
- plugin packaging
- MCP Apps

These are real Cursor 2.4-2.6 capabilities, but they are not the strongest
first implementation move for this repo because they depend on external product
surfaces, account controls, or still-unstable packaging layers.

## Local Environment

- Cursor version: `2.6.11`
- Cursor environment artifact:
  `/Users/christianpardo/Desktop/concentric_study/operator/cre/artifacts/cursor_environment/latest.json`
- Repo method baseline:
  `/Users/christianpardo/Desktop/concentric_study/operator/cre/PHD_DECISION_PRACTICE.md`

Interpretation:
- project-local `.cursor/mcp.json` is locally usable now
- 2.6-era surfaces like MCP Apps are platform-supported, but they remain a
  poor first move for this repo compared with read-only internal MCP exposure

## Official Cursor Basis

Primary product facts used in this memo:
- MCP docs: Cursor supports `stdio`, `SSE`, and `Streamable HTTP`, plus
  project-level `.cursor/mcp.json` and global `~/.cursor/mcp.json`
  registration: <https://docs.cursor.com/advanced/model-context-protocol>
- MCP extension API: Cursor can also register MCPs programmatically through the
  extension API: <https://docs.cursor.com/en/context/mcp-extension-api>
- Cursor 2.6 changelog: MCP Apps and team marketplaces were introduced on
  March 3, 2026: <https://cursor.com/changelog/2-6>
- Cursor 2.5 changelog: plugins package skills, subagents, MCP servers, hooks,
  and rules; sandbox network controls and async subagents shipped on February
  17, 2026: <https://cursor.com/changelog/2-5>
- Cursor 2.4 changelog: subagents, skills, image generation, and clarification
  questions shipped on January 22, 2026: <https://cursor.com/changelog/2-4>
- CLI changelog: `/plan`, `/ask`, cloud handoff, one-click MCP auth, and
  interactive MCP management are official 2026 CLI surfaces:
  <https://cursor.com/changelog/cli-jan-16-2026>

## Repo-Fit Analysis

This repo is not a generic editor workflow. It is a macOS visual web-agent
system with strong existing infrastructure for:
- traces and manifests
- environment readiness
- benchmark evaluation
- research briefs
- verification and visual monitoring

That means the highest-value Cursor integration is not more general-purpose AI
surface area. It is Cursor-native access to repo-native evidence.

## Implemented Now

This integration pass adds:
- `.cursor/plans/` durable plan library
- four focused Cursor rules
- two project-registered read-only internal MCP servers:
  - `concentric-health`
  - `concentric-trace`
- two additional implemented but not yet active read-only MCP servers:
  - `concentric-benchmark`
  - `concentric-research`
- governance and operating memos for external MCP rollout and Cursor workflow

## Decision

Implementation order for this repo:
1. Cursor operating layer
2. read-only internal MCP servers
3. guarded external MCP rollout
4. plugin packaging preparation only after stability
5. MCP Apps only after internal MCP data surfaces are stable
6. cloud and team features as contingent tracks

## Rationale For Deferral

### Plugin packaging

Deferred because:
- the repo is not currently a git worktree
- the plugin surface should package stable primitives, not exploratory ones
- the official plugin manifest/schema should be re-verified at packaging time

### MCP Apps

Deferred because the internal data surfaces should exist first. The repo's real
strength is traces, evaluation, and environment drift, so those should become
Cursor tools before they become embedded UIs.

### Cloud and team features

Deferred because they are account-, admin-, or product-surface gated and do not
represent the strongest repo-local leverage move.

## Immediate Next Steps

1. Validate `concentric-health` and `concentric-trace` inside Cursor.
2. Complete the Context7 pilot using the saved rubric.
3. If the active tool surface remains disciplined, enable
   `concentric-benchmark`.
4. Keep plugin and app work deferred until the above layers are stable.
