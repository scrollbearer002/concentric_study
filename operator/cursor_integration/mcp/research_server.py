from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from agent_infra.research_agent import ResearchBrief

from cursor_integration.mcp.base import CRE_ROOT, ToolSpec, ReadOnlyMCPServer, repo_relative, tokenize


class ResearchServer(ReadOnlyMCPServer):
    def __init__(self, runs_root: str | Path | None = None) -> None:
        super().__init__(server_name="concentric-research")
        self._runs_root = Path(runs_root) if runs_root else CRE_ROOT / "runs"
        self.register_tool(
            ToolSpec(
                name="get_research_brief",
                title="Get Research Brief",
                description="Return a saved research_brief.json by run_id, by task match, or by recency.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "run_id": {"type": "string"},
                        "task": {"type": "string"},
                    },
                },
                output_schema={"type": "object"},
                handler=self._handle_get_research_brief,
            )
        )
        self.register_tool(
            ToolSpec(
                name="search_research_notes",
                title="Search Research Notes",
                description="Search saved research briefs, notes, references, and tool summaries.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "limit": {"type": "integer", "minimum": 1, "maximum": 20},
                    },
                    "required": ["query"],
                },
                output_schema={"type": "object"},
                handler=self._handle_search_research_notes,
            )
        )
        self.register_tool(
            ToolSpec(
                name="method_tool_map",
                title="Method Tool Map",
                description="Return the best-matching research brief's method/tool mapping for a task description.",
                input_schema={
                    "type": "object",
                    "properties": {"task": {"type": "string"}},
                    "required": ["task"],
                },
                output_schema={"type": "object"},
                handler=self._handle_method_tool_map,
            )
        )

    def get_research_brief(self, run_id: str | None = None, task: str | None = None) -> dict[str, Any]:
        if run_id:
            run_dir = self._resolve_run_dir(run_id)
        elif task:
            match = self._best_match_for_task(task)
            if match is None:
                raise FileNotFoundError(f"No research brief matched task: {task}")
            run_dir = match
        else:
            run_dir = self._latest_research_run()
            if run_dir is None:
                raise FileNotFoundError("No research_brief.json files found.")
        brief = ResearchBrief.load(run_dir / "research_brief.json")
        return {
            "run_id": run_dir.name,
            "run_dir": repo_relative(run_dir),
            "brief": brief.to_dict(),
            "plan_summary": brief.get_plan_summary(),
        }

    def search_research_notes(self, query: str, limit: int = 5) -> dict[str, Any]:
        if not query.strip():
            raise ValueError("query must not be empty")
        if limit < 1 or limit > 20:
            raise ValueError("limit must be between 1 and 20")
        query_tokens = set(tokenize(query))
        matches: list[dict[str, Any]] = []
        for path in self._research_brief_paths():
            brief = ResearchBrief.load(path)
            haystack_parts = [
                brief.task_description,
                "\n".join(brief.quality_criteria),
                brief.get_plan_summary(),
            ]
            method_brief = brief.method_brief
            haystack_parts.extend(getattr(method_brief, "pitfalls", []) or [])
            for ref in getattr(method_brief, "references", []) or []:
                haystack_parts.append(f"{ref.title} {ref.relevance_note}")
            joined = "\n".join(haystack_parts)
            score = self._score_text(joined, query_tokens)
            if score <= 0:
                continue
            matches.append(
                {
                    "run_id": path.parent.name,
                    "path": repo_relative(path),
                    "score": score,
                    "task_description": brief.task_description,
                    "excerpt": joined[:800],
                }
            )
        ranked = sorted(matches, key=lambda row: row["score"], reverse=True)
        return {"query": query, "matches": ranked[:limit]}

    def method_tool_map(self, task: str) -> dict[str, Any]:
        match = self._best_match_for_task(task)
        if match is None:
            raise FileNotFoundError(f"No research brief matched task: {task}")
        brief = ResearchBrief.load(match / "research_brief.json")
        equation = brief.equation_solution
        mappings = getattr(equation, "mappings", []) or []
        return {
            "requested_task": task,
            "matched_run_id": match.name,
            "matched_run_path": repo_relative(match),
            "matched_task_description": brief.task_description,
            "execution_plan": brief.execution_plan,
            "quality_criteria": brief.quality_criteria,
            "tool_inventory_count": len(brief.tool_inventory),
            "mappings": [
                {
                    "method_step_id": mapping.method_step_id,
                    "tool_name": mapping.tool_name,
                    "action_type": mapping.action_type,
                    "why_this_mapping": mapping.why_this_mapping,
                    "verification_hint": mapping.verification_hint,
                }
                for mapping in mappings
            ],
        }

    def _research_brief_paths(self) -> list[Path]:
        return sorted(
            self._runs_root.glob("*/research_brief.json"),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )

    def _latest_research_run(self) -> Path | None:
        paths = self._research_brief_paths()
        return paths[0].parent if paths else None

    def _resolve_run_dir(self, run_id: str) -> Path:
        run_dir = self._runs_root / run_id
        if not (run_dir / "research_brief.json").exists():
            raise FileNotFoundError(f"research_brief.json missing for run: {run_id}")
        return run_dir

    def _best_match_for_task(self, task: str) -> Path | None:
        query_tokens = set(tokenize(task))
        best_path: Path | None = None
        best_score = -1
        for path in self._research_brief_paths():
            brief = ResearchBrief.load(path)
            joined = "\n".join(
                [
                    brief.task_description,
                    brief.get_plan_summary(),
                    "\n".join(brief.quality_criteria),
                ]
            )
            score = self._score_text(joined, query_tokens)
            if score > best_score:
                best_score = score
                best_path = path.parent
        return best_path if best_score > 0 else None

    def _score_text(self, text: str, query_tokens: set[str]) -> int:
        if not query_tokens:
            return 0
        text_tokens = tokenize(text)
        text_set = set(text_tokens)
        score = sum(3 for token in query_tokens if token in text_set)
        if " ".join(sorted(query_tokens)) in " ".join(sorted(text_set)):
            score += 2
        return score

    def _handle_get_research_brief(self, arguments: dict[str, Any]) -> dict[str, Any]:
        run_id = arguments.get("run_id")
        task = arguments.get("task")
        return self.get_research_brief(
            run_id=str(run_id) if run_id is not None else None,
            task=str(task) if task is not None else None,
        )

    def _handle_search_research_notes(self, arguments: dict[str, Any]) -> dict[str, Any]:
        return self.search_research_notes(
            str(arguments.get("query", "")),
            limit=int(arguments.get("limit", 5)),
        )

    def _handle_method_tool_map(self, arguments: dict[str, Any]) -> dict[str, Any]:
        return self.method_tool_map(str(arguments.get("task", "")))


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the concentric research MCP server.")
    parser.add_argument("--runs-root", default=str(CRE_ROOT / "runs"))
    args = parser.parse_args()
    server = ResearchServer(runs_root=args.runs_root)
    return server.serve_forever()


if __name__ == "__main__":
    raise SystemExit(main())
