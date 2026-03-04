# Final Tool Coverage Audit (PhD)

## Scope
This is the final repo-wide pass over project-owned files, ordered by modification time from oldest to newest, to catch tooling that earlier architecture-only summaries missed.

Artifacts used:
- `operator/cre/artifacts/full_repo_files_by_mtime.json`
- `operator/cre/PROJECT_TOOLING_DEEP_AUDIT_PHD.md`
- `AGENTS.md`
- import and subprocess scans over `operator/**/*.py`

## Repo-wide file-pass result
- In-scope project-owned files scanned: `1145`
- The oldest files were early Hammerspoon/kernel and execution-demo artifacts.
- The newest files were the recent Cursor update memo and the tooling audit artifacts.

## Additional tools/components confirmed on the oldest-to-newest pass
These were either absent from the earlier short answer or only became obvious when scanning old files and operational scripts.

### Operational / shell tooling present in the repo
- `operator/cre/codex_kernel.lua`
- `operator/cre/showcase.sh`
- `operator/cre/verify_kernel.sh`
- `operator/cre/run_agent.sh`
- `operator/cre/run_ultimate_tests.sh`

### Legacy execution stack explicitly present
- Hammerspoon kernel
- `CodexClient`
- `VLMCoordinator`
- `VisualGroundingEngine`

### System commands/tools explicitly used
- `open`
- `osascript`
- `screencapture`
- `security` CLI for Keychain access

### Optional / research / support dependencies present in code or docs
- `imagehash`
- `numpy`
- `scipy`
- `sentence_transformers`
- `macapptree`
- `pyax`
- `openai`

## Important distinction: referenced vs present
A few historical docs reference tooling that is not present as a current repo file.

Confirmed referenced-but-absent example:
- `cursor_ocr_map.py`

That means it should not be counted as a current project tool, only as a historical/documented reference.

## Final delta relative to the earlier short answer
The earlier answer missed five categories:
1. capability/planning surface: `action_space.py`, `capability_router.py`, `window_capture.py`, `visual_engine.py`
2. episodic and site-knowledge surface: `SemanticSkillIndex`, `ReflectionJournal`, `RulesStore`, `SiteKnowledge`, `ExplorationLoop`, `ToolAffordance`, `InteractionRule`, `ButtonMapEntry`
3. legacy execution surface: `codex_kernel.lua`, Hammerspoon kernel, `CodexClient`, `VLMCoordinator`
4. optional but real dependency surface: `imagehash`, `numpy`, `scipy`, `sentence_transformers`, `macapptree`, `pyax`, `openai`
5. explicit system-tool surface: `open`, `osascript`, `screencapture`, `security`

## Final conclusion
After the full oldest-to-newest file pass, I did find additional real tools beyond the earlier answer.

The current project tool inventory should be treated as a layered set:
- canonical runtime/infrastructure tools
- optional live dependencies and backends
- legacy but still present execution tooling
- system commands and OS services the project depends on
- historical references that should not be mistaken for current code

The most important newly surfaced item from the oldest-file pass was the Hammerspoon operational layer centered on `operator/cre/codex_kernel.lua`, plus the fact that some docs still reference absent experimental utilities like `cursor_ocr_map.py`.
