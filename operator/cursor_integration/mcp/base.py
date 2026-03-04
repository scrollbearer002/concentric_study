from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


REPO_ROOT = Path(__file__).resolve().parents[3]
OPERATOR_ROOT = REPO_ROOT / "operator"
CRE_ROOT = OPERATOR_ROOT / "cre"

_SENSITIVE_KEY_PATTERN = re.compile(
    r"(api[_-]?key|token|secret|password|authorization|credential)",
    re.IGNORECASE,
)
_CTX7_PATTERN = re.compile(r"ctx7sk-[A-Za-z0-9-]+")
_GOOGLE_KEY_PATTERN = re.compile(r"AIza[0-9A-Za-z\-_]{20,}")


@dataclass(frozen=True)
class ToolSpec:
    name: str
    title: str
    description: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    handler: Callable[[dict[str, Any]], Any]


def repo_relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path.resolve())


def load_json(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def sanitize_text(text: str, *, max_chars: int = 4000) -> str:
    redacted = _CTX7_PATTERN.sub("[REDACTED_CONTEXT7_KEY]", text)
    redacted = _GOOGLE_KEY_PATTERN.sub("[REDACTED_GOOGLE_KEY]", redacted)
    if len(redacted) <= max_chars:
        return redacted
    return redacted[: max_chars - 17] + "...[TRUNCATED]"


def sanitize_value(
    value: Any,
    *,
    max_depth: int = 6,
    max_list_items: int = 25,
    max_chars: int = 4000,
) -> Any:
    if max_depth <= 0:
        return "[TRUNCATED_DEPTH]"

    if isinstance(value, dict):
        items = list(value.items())
        sanitized: dict[str, Any] = {}
        for index, (key, item) in enumerate(items):
            if index >= max_list_items:
                sanitized["__truncated_keys__"] = len(items) - max_list_items
                break
            if _SENSITIVE_KEY_PATTERN.search(str(key)):
                sanitized[str(key)] = "[REDACTED]"
            else:
                sanitized[str(key)] = sanitize_value(
                    item,
                    max_depth=max_depth - 1,
                    max_list_items=max_list_items,
                    max_chars=max_chars,
                )
        return sanitized

    if isinstance(value, list):
        sliced = value[:max_list_items]
        out = [
            sanitize_value(
                item,
                max_depth=max_depth - 1,
                max_list_items=max_list_items,
                max_chars=max_chars,
            )
            for item in sliced
        ]
        if len(value) > max_list_items:
            out.append(f"[TRUNCATED_ITEMS:{len(value) - max_list_items}]")
        return out

    if isinstance(value, str):
        return sanitize_text(value, max_chars=max_chars)

    return value


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9_]+", text.lower())


def make_text_result(payload: Any) -> dict[str, Any]:
    safe_payload = sanitize_value(payload)
    text = json.dumps(safe_payload, indent=2, sort_keys=True)
    return {
        "content": [{"type": "text", "text": sanitize_text(text)}],
        "structuredContent": safe_payload,
    }


class ReadOnlyMCPServer:
    """Small stdio MCP server with read-only tool annotations.

    This is intentionally lightweight so the repo can expose internal data
    without adding another dependency chain just to speak MCP.
    """

    protocol_version = "2025-06-18"

    def __init__(self, *, server_name: str, version: str = "0.1.0") -> None:
        self.server_name = server_name
        self.version = version
        self._tools: dict[str, ToolSpec] = {}

    def register_tool(self, spec: ToolSpec) -> None:
        self._tools[spec.name] = spec

    def tool_definitions(self) -> list[dict[str, Any]]:
        return [
            {
                "name": spec.name,
                "title": spec.title,
                "description": spec.description,
                "inputSchema": spec.input_schema,
                "outputSchema": spec.output_schema,
                "annotations": {
                    "title": spec.title,
                    "readOnlyHint": True,
                    "destructiveHint": False,
                    "idempotentHint": True,
                    "openWorldHint": False,
                },
            }
            for spec in self._tools.values()
        ]

    def handle_message(self, message: Any) -> Any:
        if isinstance(message, list):
            responses = [self._handle_single(item) for item in message]
            return [resp for resp in responses if resp is not None]
        return self._handle_single(message)

    def _handle_single(self, message: Any) -> dict[str, Any] | None:
        if not isinstance(message, dict):
            return self._error(None, -32600, "Invalid Request")

        method = message.get("method")
        request_id = message.get("id")
        params = message.get("params", {}) or {}

        if method == "notifications/initialized":
            return None
        if method == "ping":
            return self._result(request_id, {})
        if method == "initialize":
            return self._result(
                request_id,
                {
                    "protocolVersion": self.protocol_version,
                    "capabilities": {"tools": {}},
                    "serverInfo": {
                        "name": self.server_name,
                        "title": self.server_name,
                        "version": self.version,
                    },
                },
            )
        if method == "tools/list":
            return self._result(request_id, {"tools": self.tool_definitions()})
        if method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {}) or {}
            spec = self._tools.get(str(tool_name))
            if spec is None:
                return self._error(request_id, -32601, f"Unknown tool: {tool_name}")
            try:
                payload = spec.handler(arguments)
            except FileNotFoundError as exc:
                return self._error(request_id, -32001, str(exc))
            except ValueError as exc:
                return self._error(request_id, -32602, str(exc))
            except Exception as exc:
                return self._error(request_id, -32603, f"Tool execution failed: {exc}")
            return self._result(request_id, make_text_result(payload))

        return self._error(request_id, -32601, f"Method not found: {method}")

    def serve_forever(self) -> int:
        for raw in sys.stdin:
            raw = raw.strip()
            if not raw:
                continue
            try:
                message = json.loads(raw)
            except json.JSONDecodeError as exc:
                response = self._error(None, -32700, f"Parse error: {exc}")
                sys.stdout.write(json.dumps(response, separators=(",", ":")) + "\n")
                sys.stdout.flush()
                continue
            response = self.handle_message(message)
            if response is None:
                continue
            sys.stdout.write(json.dumps(response, separators=(",", ":")) + "\n")
            sys.stdout.flush()
        return 0

    def _result(self, request_id: Any, result: dict[str, Any]) -> dict[str, Any]:
        return {"jsonrpc": "2.0", "id": request_id, "result": result}

    def _error(
        self,
        request_id: Any,
        code: int,
        message: str,
        *,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        error: dict[str, Any] = {"code": code, "message": message}
        if data is not None:
            error["data"] = sanitize_value(data)
        return {"jsonrpc": "2.0", "id": request_id, "error": error}
