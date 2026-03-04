# Cursor Integration

This package contains the optional Cursor-facing integration layer for
`concentric_study`.

Design constraints:
- isolated from core `agent_infra`
- read-only by default
- repo-local only
- deterministic where possible
- minimal MCP stdio transport without extra SDK dependencies

Current servers:
- `cursor_integration.mcp.trace_server`
- `cursor_integration.mcp.health_server`
- `cursor_integration.mcp.benchmark_server`
- `cursor_integration.mcp.research_server`

Example local Cursor MCP registration once you want to enable one:

```json
{
  "mcpServers": {
    "concentric-trace": {
      "command": "operator/venv/bin/python",
      "args": ["-m", "cursor_integration.mcp.trace_server"]
    }
  }
}
```

Recommended enablement order:
1. `concentric-trace`
2. `concentric-health`
3. `concentric-benchmark`
4. `concentric-research`

Current project registration state:
- active in `.cursor/mcp.json`: `context7`, `concentric-health`, `concentric-trace`
- implemented but intentionally not active by default: `concentric-benchmark`,
  `concentric-research`

This keeps the default tool surface small while still exposing the two
highest-signal repo-local read-only servers first.
