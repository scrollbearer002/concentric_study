from __future__ import annotations

import json
from pathlib import Path

from cursor_integration.mcp.trace_server import TraceServer


def _write_run(root: Path, run_id: str) -> Path:
    run_dir = root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "run_id": run_id,
        "task_id": "TEST_TRACE_TASK",
        "task_description": "Test trace task",
        "outcome": "failure",
        "num_steps": 3,
        "total_duration_ms": 3210,
        "failure_step": 2,
        "failure_category": "grounding_error",
        "error_summary": "Element not found",
        "timestamp": "2026-03-04T00:00:00Z",
        "agent_config": {"mode": "test"},
        "steps_summary": ["1: click ok", "2: click failed", "3: verify skipped"],
    }
    steps = [
        {
            "step": 1,
            "thought": "Open the page and click the toolbar button.",
            "action": {"type": "click", "parameters": {"target": "toolbar"}},
            "pre_state": {"focused_app": "Safari"},
            "post_state": {"toolbar_open": True},
            "action_result": {"success": True},
            "duration_ms": 100,
        },
        {
            "step": 2,
            "thought": "Click after the toolbar opened in step 1.",
            "action": {"type": "click", "parameters": {"target": "canvas"}},
            "pre_state": {"toolbar_open": True},
            "post_state": {"canvas_changed": False},
            "action_result": {"success": False, "error": "Element not found"},
            "evaluation": {"expected": "drawn", "actual": "not found", "match": False},
            "duration_ms": 120,
        },
        {
            "step": 3,
            "thought": "Verify if drawing is present after step 2.",
            "action": {"type": "assert_visual", "parameters": {"target": "drawing"}},
            "pre_state": {"canvas_changed": False},
            "post_state": {"verified": False},
            "action_result": {"success": True},
            "duration_ms": 90,
        },
    ]
    (run_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (run_dir / "trace.jsonl").write_text(
        "\n".join(json.dumps(step) for step in steps) + "\n",
        encoding="utf-8",
    )
    (run_dir / "benchmark_result.json").write_text(
        json.dumps({"run_id": run_id, "claims_score": 0.75}),
        encoding="utf-8",
    )
    return run_dir


def test_trace_server_exposes_run_tools(tmp_path: Path) -> None:
    _write_run(tmp_path, "run-a")
    server = TraceServer(runs_root=tmp_path)

    listing = server.list_recent_runs(limit=5)
    assert listing["runs"][0]["run_id"] == "run-a"
    assert listing["runs"][0]["has_benchmark_result"] is True

    manifest = server.get_run_manifest("run-a")
    assert manifest["manifest"]["task_id"] == "TEST_TRACE_TASK"

    summary = server.get_run_summary("run-a", detail_level=2)
    assert "RUN SUMMARY" in summary["summary"]
    assert "FAILURE WINDOW" in summary["summary"]

    failure = server.summarize_failure_chain("run-a")
    assert failure["classification"]["category"] in {"grounding", "execution", "logic"}
    assert "Element not found" in failure["error_summary"]

    artifacts = server.list_run_artifacts("run-a")
    assert any(item["path"].endswith("manifest.json") for item in artifacts["artifacts"])


def test_trace_server_handles_mcp_requests(tmp_path: Path) -> None:
    _write_run(tmp_path, "run-b")
    server = TraceServer(runs_root=tmp_path)

    initialize = server.handle_message(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "test"}},
        }
    )
    assert initialize["result"]["serverInfo"]["name"] == "concentric-trace"

    tools = server.handle_message({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    tool_names = {tool["name"] for tool in tools["result"]["tools"]}
    assert "list_recent_runs" in tool_names
    assert "summarize_failure_chain" in tool_names

    call = server.handle_message(
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "get_run_manifest", "arguments": {"run_id": "run-b"}},
        }
    )
    assert call["result"]["structuredContent"]["manifest"]["run_id"] == "run-b"
