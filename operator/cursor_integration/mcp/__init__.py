"""Read-only MCP servers for Cursor.

Avoid eager imports here so `python -m cursor_integration.mcp.<server>` starts
cleanly without package-level side effects.
"""

__all__ = [
    "benchmark_server",
    "health_server",
    "research_server",
    "trace_server",
]
