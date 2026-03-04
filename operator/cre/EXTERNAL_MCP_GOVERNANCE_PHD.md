# External MCP Governance (PhD)

Date: `2026-03-04`

## Executive Decision

External MCP adoption in `concentric_study` must remain narrow, evidence-backed,
and reversible.

Default rule:
- prefer repo-local files first
- prefer read-only internal MCPs second
- add an external MCP only when it closes a real workflow gap that local tools
  do not already cover well

## Rollout Order

1. `Context7`
2. `Parallel`
3. `Playwright`
4. `Langfuse`
5. `Runlayer`

This order follows the repo's MCP landscape memo and keeps the first pilots on
high-signal retrieval, research, and observability surfaces.

## Governance Rules

- one new external MCP at a time
- define the exact task class it is allowed to own
- define the security boundary before enabling it
- define negative controls before the first real pilot
- do not enable another external MCP until the current one has a pass, mixed,
  or fail verdict

## Tool-Count Policy

Tool overload is treated as a real failure mode. If the active MCP set expands,
tool routing quality can degrade and context budget gets wasted.

Policy:
- keep the always-on MCP set minimal
- disable MCPs that are not actively being evaluated
- prefer explicit tool naming in prompts when similar tool classes coexist

## Security Boundary

For each external MCP, record:
- domains contacted
- whether OAuth or API key auth is required
- whether outputs may contain sensitive data
- whether the tool can write or only read
- whether the MCP can indirectly expand browser or network reach

No MCP with write scope should be adopted by default without a separate review.

## Sandbox Policy

When external MCP evaluation requires networked commands, use an explicit domain
allowlist rather than broad access.

Minimum first-wave domains:
- `mcp.context7.com`
- `context7.com`
- `docs.parallel.ai`
- `parallel.ai`
- `langfuse.com`
- `docs.runlayer.com`
- `runlayer.com`

Special case:
- `Playwright` is not governed by a single vendor domain. Allow target domains
  only for the specific pilot under test.

## Negative Controls

Use these to prove an external MCP is not overfiring:
- repo-local code question should not use `Context7`
- environment question should not use `Context7`
- Cursor product question should not use `Context7`
- run-forensics question should use `concentric-trace`, not a SaaS MCP

## Stop Conditions

Disable or roll back an external MCP when any of the following occurs:
- severe hallucination on a task it should own
- false-positive invocation on repo-local or host-local work
- unacceptable latency for the observed quality lift
- secret or policy boundary concerns
- tool overload or prompt-routing confusion

## Operating Pattern

The correct default pattern is:
1. local files
2. internal MCP if repo-native evidence exists
3. external MCP only for the gap that remains

This keeps Cursor aligned with the repo's bounded-growth rule.
