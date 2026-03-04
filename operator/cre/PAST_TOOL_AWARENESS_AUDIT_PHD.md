# PhD Audit: Past Tool Awareness and Gaps

**Purpose:** Audit whether the prior tool memos were already reflected in my working model of this repo and this session, identify what I did not explicitly know soon enough, and explain why those gaps occurred.

**Primary evidence sources:**
- `AGENTS.md`
- `operator/cre/PHD_CHAT_TOOL_USE_RESEARCH.md`
- `operator/cre/TOOLS_USED_IN_CHAT_PHD_RESEARCH.md`
- `operator/cre/PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md`
- `operator/cre/PHD_DECISION_PRACTICE.md`

## 1. Core distinction I should have made earlier

The prior memos mix two different classes of "tools":

1. **Assistant/IDE tools**
   - `run_terminal_cmd`
   - `read_file`
   - `grep`
   - `codebase_search`
   - `glob_file_search`
   - `search_replace` / `StrReplace`
   - `TodoWrite`
   - `ReadLints`
   - `mcp_task`

2. **Project/runtime tools**
   - `TraceWriter`
   - `DiagnosticReader`
   - `HealingOrchestrator`
   - `SkillLibrary`
   - `OuterLoop`
   - `ActionTrustTracker`
   - `Summarizer`
   - `ResearchAgent`
   - `VisualMonitor`
   - `VerificationGate`
   - `DecisionDependenceAnalyzer`
   - `BenchmarkEvaluator`
   - `a11y_engine`
   - `element_map`
   - `web_primitives`
   - `InputSanitizer`
   - `CredentialVault`

This distinction matters because I am operating in a **Codex API tool environment**, not the historical Cursor tool environment. I knew most of the runtime tools from `AGENTS.md`, but I did not explicitly normalize all the older **assistant tool names** into the current tool surface early enough.

## 2. Tools I already knew were part of the project

These were already in my active model before this audit, because they are explicit in `AGENTS.md` and in the architecture corpus:

- `TraceWriter`
- `DiagnosticReader`
- `HealingOrchestrator`
- `SkillLibrary`
- `OuterLoop`
- `ActionTrustTracker`
- `Summarizer`
- `ResearchAgent`
- `VerificationGate`
- `DecisionDependenceAnalyzer`
- `BenchmarkEvaluator`
- `a11y_engine`
- `element_map`
- `web_primitives`
- `inference_router`
- `security/sanitizer.py`
- `security/credential_vault.py`

Evidence:
- `AGENTS.md`
- `operator/cre/PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md`
- `operator/cre/project_understanding/README.md`

## 3. Tools I did not explicitly map soon enough

These are the items I should have normalized earlier and did not:

### 3.1 Historical assistant-tool names

- `run_terminal_cmd`
- `read_file`
- `codebase_search`
- `glob_file_search`
- `search_replace` / `StrReplace`
- `TodoWrite`
- `ReadLints`
- `mcp_task`
- `SemanticSearch`

What I know now:
- These are **historical tool-interface names**, not repo modules.
- In the current session they map roughly to:
  - `run_terminal_cmd` -> `functions.exec_command`
  - `read_file` -> `functions.exec_command` with `sed`, `cat`, `nl`, `rg`
  - `grep` -> `rg`
  - `codebase_search` / `SemanticSearch` -> repo exploration via `rg`, targeted reads, and reasoning
  - `glob_file_search` -> `rg --files` / shell globbing
  - `search_replace` / `StrReplace` -> `functions.apply_patch`
  - `TodoWrite` -> `functions.update_plan`
  - `ReadLints` -> `python -m py_compile`, pytest, and any editor diagnostics we can reproduce locally
  - `mcp_task` -> no direct equivalent in this environment

### 3.2 Project/runtime tools I underused early in this session

- `ResearchAgent`
- `VisualMonitor`
- `BenchmarkEvaluator`

What I know now:
- I knew they existed from `AGENTS.md`, but I did not operationalize them early enough.
- The most consequential miss was `ResearchAgent`: I only wired it into the universal path after repeated live-task failures showed the planner lacked structured subject/method/tool intelligence.

## 4. Why I missed or delayed these mappings

### 4.1 Tool-name drift across environments

The largest source of error was **tool-name drift**:

- The memos describe prior work in Cursor-centric tool names.
- The current environment exposes Codex/API tools with different names and capabilities.
- I correctly reasoned about repo internals, but I did not early enough create a stable alias map between the old and current assistant tool surfaces.

### 4.2 I prioritized repo runtime architecture over historical chat tooling

My first passes focused on:

- repo structure
- imports
- runtime traces
- architectural conformance
- live Safari/Kleki execution

That was correct for understanding the codebase, but it meant I treated historical tool-use memos as **secondary provenance artifacts** rather than **first-class operational context**.

### 4.3 Some items are documented, not enforced

Several tools are clearly present in docs but not always present in the live hot path:

- `ResearchAgent`
- `VisualMonitor`
- `BenchmarkEvaluator`
- security hardening modules

Because they are not always invoked by default, I did not assume active use without evidence. That caution was defensible, but it still left a gap in my historical understanding of what had already been used in prior chats.

### 4.4 The memos compress unlike things under one label

The past memos use "tools" to refer to:

- assistant interface tools
- repo modules
- OS/system commands
- research methods

That compression made it easier to miss category boundaries until I audited them explicitly.

## 5. What I should have done earlier

1. Read `operator/cre/PHD_CHAT_TOOL_USE_RESEARCH.md` and `operator/cre/TOOLS_USED_IN_CHAT_PHD_RESEARCH.md` near the start of the repo-understanding work.
2. Build an explicit alias map from historical Cursor tool names to current Codex/API tools.
3. Separate:
   - assistant-tool history
   - repo runtime-tool history
   - currently wired hot-path tools
4. Treat `ResearchAgent` as a likely missing dependency in the universal drawing path earlier than I did.

## 6. Concrete corrections I have now made to my working model

I now treat the following as explicit facts:

- Older memos that mention `run_terminal_cmd`, `read_file`, `codebase_search`, `glob_file_search`, `StrReplace`, `TodoWrite`, and `ReadLints` are referring to a **prior assistant tool surface**, not missing repo modules.
- `AGENTS.md` is the canonical source for the **project/runtime tool inventory** in this repo.
- `ResearchAgent` is not optional background; for non-trivial drawing tasks it is a first-order capability that should be considered early.
- Historical memos under `operator/cre/` are part of the repo's operational memory and should be read as evidence, not merely as archival prose.

## 7. Bottom-line self-critique

I understood the repo's architectural modules better than I understood the repo's historical tool-provenance memos.

The main gap was not ignorance of core runtime components like `TraceWriter` or `VerificationGate`. The main gap was that I did not early enough normalize historical assistant-tool names and did not early enough elevate prior tool-use memos into the same evidence tier as `AGENTS.md`.

## 8. Operational rule going forward

Before substantial repo work, I should explicitly classify any cited "tool" into one of these buckets:

1. current assistant/API tool
2. historical assistant tool name
3. repo/runtime subsystem
4. OS/system utility
5. research method or evaluation protocol

That prevents the exact confusion this audit exposed.
