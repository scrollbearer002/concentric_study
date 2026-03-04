# Cursor 2.6 Operating Protocol (PhD)

Date: `2026-03-04`

## Purpose

This protocol defines how Cursor 2.6 should be used inside
`concentric_study` so the repo gains leverage without adding context noise or
tool sprawl.

## Default Mode Selection

Use `/plan` when:
- the task is non-trivial
- the task spans multiple files
- the task mixes research and implementation
- the task involves rollout, debugging, or design choices

Use `/ask` when:
- the goal is exploration only
- you need codebase understanding without edits
- you are disambiguating architecture before choosing a plan

Use direct build mode only when:
- the task is bounded and already well-understood
- the path does not require a design branch

## Conversation Hygiene

- start a fresh chat when changing objectives
- start a fresh chat if the agent begins mixing repo-local and external-doc
  reasoning
- pin only live, still-active long-running threads
- use `@Past Chats` or plan artifacts instead of dragging old chat noise into a
  new objective

## MCP Operating Rules

- keep the active MCP set minimal
- name the MCP explicitly when ambiguity is likely
- use `context7` only for current third-party docs
- use `concentric-health` for environment facts
- use `concentric-trace` for run forensics
- do not use external-doc MCPs for repo-local or Cursor-product questions

## Failure Capture SOP

When Cursor, MCP, or browser behavior fails:
1. capture the Request ID
2. capture the exact prompt or action that triggered the failure
3. if UI is involved, capture a screenshot or browser state
4. if the failure looks Cursor-level, open DevTools console
5. record whether the failure is:
   - repo code
   - MCP routing or server behavior
   - sandbox or network policy
   - Cursor product behavior

## Browser Workflow SOP

For browser or visual work:
- inspect the current page state before acting
- use the integrated browser to collect screenshots and DOM evidence
- verify the actual target surface before assuming control is wired correctly
- treat screenshots as measurement, not decoration

## Decision Tree

```mermaid
flowchart TD
    A[New task] --> B{Need edits?}
    B -- No --> C[/ask]
    B -- Yes --> D{Non-trivial or branching?}
    D -- Yes --> E[/plan and save artifact]
    D -- No --> F[Build directly]
    E --> G{Need current external docs?}
    G -- Yes --> H[Use Context7]
    G -- No --> I[Stay repo-local]
    H --> J[Implement smallest justified change]
    I --> J
    J --> K{Failure?}
    K -- No --> L[Verify and close]
    K -- Yes --> M[Capture Request ID, evidence, failure class]
```

## Cursor-Level Diagnostics

Use DevTools console only when the issue appears to be in Cursor itself, such
as:
- tool list not rendering
- MCP connected state disagreeing with behavior
- browser sidebar or embedded UI failures
- suspicious extension or workbench issues

For repo failures, prefer local trace artifacts first.

## Non-Goals

This protocol does not assume:
- team marketplace access
- cloud-agent availability
- Bugbot availability
- enterprise admin controls

Those are separate, contingent tracks.
