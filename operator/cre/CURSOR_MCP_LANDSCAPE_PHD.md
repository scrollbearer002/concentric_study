# Cursor MCP Landscape (PhD)

## 1. Executive Summary

This memo evaluates which MCPs are implementable in Cursor as of **2026-03-04**, which of them materially improve the `concentric_study` workflow, and which internal MCPs should be built next.

Main conclusions:
- The official Cursor MCP docs inventory currently exposes **153** server surfaces.
- The official Cursor marketplace currently exposes **39** unique plugin surfaces.
- Total external install surfaces cataloged: **192**.
- Internal MCP opportunities cataloged: **6**.
- The strongest immediate external upgrades are current-doc retrieval, deep research, browser augmentation, MCP governance, and trace/eval observability.
- The strongest medium-term upgrades are internal MCPs that expose the repo's own trace, benchmark, health, and research machinery inside Cursor.

## 2. Context and Exact Environment

- Repo method baseline: `/Users/christianpardo/Desktop/concentric_study/operator/cre/PHD_DECISION_PRACTICE.md`.
- Local Cursor baseline from `/Users/christianpardo/Desktop/concentric_study/operator/cre/artifacts/cursor_environment/latest.json`:
  - Version: `2.6.11`
  - Build date: `2026-03-03T18:57:48.001Z`
  - Host: `macOS 26.3` on `arm64`
- Local tool-health basis: `/Users/christianpardo/Desktop/concentric_study/operator/agent_infra/tool_health_catalog.json`.
- Workflow reality: this is not a generic IDE repo. It is a macOS visual-web-agent system with strong emphasis on research, browser execution, traces, security, verification, and evaluation.

## 3. Official Cursor MCP Capability Baseline

- Cursor's MCP docs (`SRC-01`) document support for `stdio`, `SSE`, and `Streamable HTTP` transports via MCP.
- Cursor's MCP docs (`SRC-01`) document both project-level `.cursor/mcp.json` and global `~/.cursor/mcp.json` registration.
- Cursor's MCP docs (`SRC-01`) document one-click server installation from Cursor's collection plus OAuth-aware flows.
- Cursor's plugins docs (`SRC-02`) state that plugins package rules, skills, agents, commands, MCP servers, and hooks, and that they work across the IDE, CLI, and Cloud.
- Cursor's March 3, 2026 changelog (`SRC-03`) adds MCP Apps and team plugin marketplaces as explicit 2.6-era surfaces.
- Local state: this machine is on Cursor `2.6.11`, so the 2.6-era MCP Apps surface is locally testable.

Interpretation:
- Cursor-level MCP support is real and broad now.
- Local availability still depends on plan/admin controls and setup, but the app version no longer blocks 2.6-era MCP Apps testing.

## 4. Method and Source Policy

Evidence ladder used:
- Tier 1: official Cursor docs, official Cursor changelog, official Cursor blog, official Cursor marketplace, official provider docs, official upstream GitHub repos.
- Tier 2: none relied on for priority recommendations unless the official source was incomplete.

Collection method:
- Parse the official Cursor MCP docs inventory from `https://cursor.com/docs/context/mcp`.
- Parse the official Cursor marketplace inventory from `https://cursor.com/marketplace`.
- Map candidates to repo workflow classes using the current repo's own PhD memos and tool inventory.
- Keep marketplace plugins and direct MCP server entries separate when they represent materially different install surfaces.

## 5. Exhaustive Catalog Overview

Catalog counts by install surface:
- `external_server`: 153
- `cursor_plugin`: 39
- `internal_opportunity`: 6

Workflow coverage counts across the full catalog:
- `artifact_generation`: 7
- `coordination_orchestration`: 22
- `execution_environment`: 78
- `observability_forensics`: 43
- `repo_retrieval`: 22
- `research_intelligence`: 53
- `security_governance`: 38
- `verification_evaluation`: 38

Interpretation:
- Cursor's official ecosystem is already broad enough that the main problem is no longer discovery alone.
- The real research question is selection: which MCPs strengthen this repo's actual workflow rather than merely adding surface area.

## 6. Workflow-Fit Analysis for `concentric_study`

Current repo evidence from `/Users/christianpardo/Desktop/concentric_study/operator/cre/MISSED_TOOL_WORKFLOW_VALUE_PHD.md`, `/Users/christianpardo/Desktop/concentric_study/operator/cre/PHASE_1_ENVIRONMENT_BENEFITS_PHD.md`, and `/Users/christianpardo/Desktop/concentric_study/operator/cre/MASTER_TOOL_LIST_PHD.md` points to these highest-value upgrade zones:
- current documentation and repository retrieval
- bounded browser augmentation beyond the local Safari path
- Cursor-native observability and evaluation access
- MCP governance, audit, and secret discipline
- visual artifact/review surfaces, now that the local Cursor build includes the 2.6-era MCP Apps surface

This means the most valuable MCPs are not generic productivity wrappers. The best fits are the ones that increase research quality, reduce diagnosis latency, or expose existing repo-native strengths inside Cursor.

## 7. Highest-Upside External MCPs

### 1. Context7 (cursor_plugin)
- Why it matters: Context7 directly upgrades one of the clearest repo needs: current, version-specific documentation retrieval for research-first implementation and codebase work.
- Why now: This is the cleanest immediate upgrade for current-doc and API lookup inside Cursor.
- Gap filled: Repo-scale and documentation-scale retrieval is still weaker than the project's research standard demands.
- Complements/supersedes: ResearchAgent, SkillLibrary semantic retrieval, and rg-based repo exploration.
- Pilot: Use Context7 on 10 repo questions involving fast-moving libraries or APIs and compare answer freshness versus current shell-plus-web lookup.
- Risk: Low security risk; main risk is treating vendor-curated docs as complete.
- Local feasibility: Plugin-era Cursor already exists locally, so the main cost is install/auth rather than version gating.

### 2. Parallel (cursor_plugin)
- Why it matters: Parallel is the strongest marketplace-native fit for the repo's PhD research workflow: deep research, content extraction, and data enrichment inside the IDE.
- Why now: The repo already emphasizes pre-execution research, and Parallel adds a strong external research surface inside Cursor.
- Gap filled: Structured deep research and content extraction remain external to the main Cursor loop.
- Complements/supersedes: ResearchAgent and the project's context-locked research prompts.
- Pilot: Run the same literature-and-docs task with Parallel and the existing manual web path, then compare source breadth, citation quality, and time-to-brief.
- Risk: Moderate risk of overcollection or noisy research results if not scoped tightly.
- Local feasibility: Usable on the current local Cursor baseline, but requires external service setup.

### 3. Playwright (external_server)
- Why it matters: Playwright is the clearest non-marketplace external MCP that could materially strengthen browser automation, reproducible testing, and bounded web experiments.
- Why now: The project is a browser- and GUI-heavy agent runtime; Playwright is the highest-signal external MCP augmentation for browser execution and testing.
- Gap filled: Current browser control is local-macOS-first and Safari-centric. A parallel browser automation surface would add controllable, testable browser execution.
- Complements/supersedes: web_primitives.py, VerificationGate, VisualMonitor, and the universal-agent path.
- Pilot: Add a sandboxed Playwright MCP config and compare one site task against the current local web path on determinism, observability, and failure recovery.
- Risk: Medium security risk because browser automation expands reachable surface area and requires clear sandbox discipline.
- Local feasibility: Current local Cursor can use stdio MCP servers; this is a setup question, not a 2.6 feature gate.

### 4. Langfuse (cursor_plugin)
- Why it matters: Langfuse is the best marketplace fit for externalizing trace, prompt, and evaluation visibility without inventing a new observability stack from scratch.
- Why now: The repo already invests heavily in traces, summaries, evaluation, and run forensics; Langfuse matches that center of gravity directly.
- Gap filled: There is no Cursor-native external tracing and prompt/eval surface woven into the current workflow.
- Complements/supersedes: TraceWriter, Summarizer, BenchmarkEvaluator, and diagnostic artifacts.
- Pilot: Instrument a small set of research or planning tasks with Langfuse and compare whether prompt/version/run visibility improves postmortem quality.
- Risk: Low-to-medium risk; the main concern is export of sensitive run context to an external service.
- Local feasibility: Usable on the current local baseline with plugin setup and Langfuse access.

### 5. Runlayer (cursor_plugin)
- Why it matters: Runlayer is the strongest marketplace-native answer to the repo's next likely bottleneck: governing a larger MCP surface safely.
- Why now: If this repo adopts more MCPs, governance becomes a first-order concern rather than a later cleanup step.
- Gap filled: Current repo security is strong inside the Python runtime, but there is no dedicated Cursor-side MCP governance and audit surface.
- Complements/supersedes: security/sanitizer.py, CredentialVault, HostToolHealth, and HITL patterns.
- Pilot: Install Runlayer in a disposable environment and test whether it materially improves MCP discovery, auditability, secret handling, and policy visibility.
- Risk: Medium risk because it becomes part of the MCP control plane; its own trust boundary must be reviewed carefully.
- Local feasibility: Usable on current Cursor with setup; no 2.6-only dependency is required for core value.

## 8. Highest-Upside Internal MCPs

### 6. concentric-trace-mcp
- Why it matters: This is the highest-value internal MCP because it exposes one of the repo's strongest native advantages directly to Cursor.
- Why now: The repo already has rich traces; exposing them cleanly to Cursor would convert latent research assets into interactive workflow power.
- Gap filled: Trace inspection is currently script- or file-driven rather than native to Cursor's MCP tool loop.
- Complements/supersedes: TraceWriter, DiagnosticReader, DecisionDependenceAnalyzer, and HealingOrchestrator.
- Pilot: Prototype read_run_manifest, list_recent_runs, and summarize_failure_chain as MCP tools and compare debugging speed against file-only inspection.
- Risk: Low risk if read-only; medium if any mutation or redaction boundaries are weak.
- Local feasibility: No local Cursor version blocker; requires building and registering the MCP server.

### 7. concentric-benchmark-mcp
- Why it matters: This turns the repo's evaluation science into an interactive Cursor surface instead of a passive artifact set.
- Why now: The project already contains benchmark and claims-based evaluation machinery; Cursor should be able to query and compare runs directly.
- Gap filled: Evaluation remains too file-centric for rapid iterative decision-making in Cursor.
- Complements/supersedes: BenchmarkEvaluator, TaskClaim, and benchmark artifacts.
- Pilot: Prototype evaluate_run and compare_runs MCP tools, then use them during one regression-analysis cycle.
- Risk: Low risk if tools are read-only and scoped to repo-local data.
- Local feasibility: Requires server implementation, not a Cursor upgrade.

### 8. concentric-health-mcp
- Why it matters: A health MCP would let Cursor reason about this machine's readiness before work, which aligns directly with the repo's environment-discipline path.
- Why now: Environment drift and tool-health regressions are already first-order failure modes in this project.
- Gap filled: Host readiness and baseline drift checks are not available as a native Cursor tool surface.
- Complements/supersedes: HostToolHealth, tool_health_catalog.json, and cursor_environment snapshotting.
- Pilot: Prototype health_summary, check_tool_class, and compare_environment_baselines MCP tools and use them before live runs.
- Risk: Low risk; the main concern is leaking unnecessary host detail into prompts or logs.
- Local feasibility: Requires internal MCP implementation only.

### 9. concentric-research-mcp
- Why it matters: This makes the repo's research-first method directly callable from Cursor, which is a meaningful PhD-level workflow lift rather than a cosmetic integration.
- Why now: ResearchAgent is already a differentiated internal capability; surfacing it via MCP would make it reusable from inside Cursor without bespoke wrappers.
- Gap filled: Research briefs and source registers are generated in the repo but not exposed as a reusable tool surface to Cursor.
- Complements/supersedes: ResearchAgent, ResearchBrief artifacts, and context-locked research prompts.
- Pilot: Prototype run_research_brief and fetch_research_context MCP tools for one complex pre-execution task.
- Risk: Low-to-medium risk depending on web-search scope and prompt-budget control.
- Local feasibility: Needs implementation, but no local version gate.

## 9. Local Feasibility on This Machine

- Current local Cursor baseline: `2.6.11`.
- Immediate conclusion: both plugin-era MCP adoption and the 2.6 MCP Apps surface are locally testable now.

Local gates:
- `mcp.json` servers: available now with setup.
- Marketplace plugins: available now.
- MCP Apps: platform-supported in 2.6 and locally available on this machine.
- Team marketplaces: also require plan/admin surfaces beyond a single local install.

## 10. Risks, Limitations, and Unknowns

- Cursor docs and marketplace pages are live product surfaces, not archived snapshots, so this memo captures a dated retrieval rather than a permanent historical freeze.
- The marketplace exposes plugin descriptions cleanly but not all underlying transport/auth details; when available, those were filled from Cursor's MCP docs inventory.
- Local feasibility is separated from platform support because even on Cursor 2.6.11, plan/admin controls and per-server setup still matter.
- Some MCPs are credible but low-fit for this repo because they optimize shipping or SaaS operations rather than visual-agent research workflows.

## 11. Recommended Adoption Order

### Tier A — Highest-Upside Pilots
- `1`. `Context7` (cursor_plugin)
- `2`. `Parallel` (cursor_plugin)
- `3`. `Playwright` (external_server)
- `4`. `Langfuse` (cursor_plugin)
- `5`. `Runlayer` (cursor_plugin)
- `6`. `concentric-trace-mcp` (internal_opportunity)
- `7`. `concentric-benchmark-mcp` (internal_opportunity)
- `8`. `concentric-health-mcp` (internal_opportunity)
- `9`. `concentric-research-mcp` (internal_opportunity)

### Tier B — Strong but Non-Immediate
- `1`. `Sentry` (cursor_plugin)
- `2`. `GitHub` (external_server)
- `3`. `Browserbase` (external_server)
- `4`. `Cursor Team Kit` (cursor_plugin)
- `5`. `Figma` (cursor_plugin)
- `6`. `tldraw` (cursor_plugin)
- `7`. `Amplitude` (cursor_plugin)
- `8`. `Atlassian` (cursor_plugin)
- `9`. `concentric-visual-monitor-mcp` (internal_opportunity)
- `10`. `concentric-skill-mcp` (internal_opportunity)

### Tier C — Real but Lower-Leverage for This Repo
- Count: `179`
- These are worth cataloging for completeness, but they do not currently beat the Tier A/Tier B items on repo fit, upgrade magnitude, or local readiness.

## 12. Appendix: Evidence and Inventory Snapshot

Primary sources used:
- `SRC-01`: [Model Context Protocol (MCP) | Cursor Docs](https://cursor.com/docs/context/mcp) — published `undated`, retrieved `2026-03-04`
- `SRC-02`: [Plugins | Cursor Docs](https://cursor.com/docs/plugins) — published `undated`, retrieved `2026-03-04`
- `SRC-03`: [MCP Apps and Team Marketplaces for Plugins](https://cursor.com/changelog/2-6) — published `2026-03-03`, retrieved `2026-03-04`
- `SRC-04`: [Cursor 2.5](https://cursor.com/blog/cursor-2-5) — published `2026-02-17`, retrieved `2026-03-04`
- `SRC-05`: [Cursor Marketplace](https://cursor.com/marketplace) — published `undated`, retrieved `2026-03-04`
- `SRC-06`: [MCP Apps extension overview](https://modelcontextprotocol.io/extensions/apps/overview) — published `undated`, retrieved `2026-03-04`
- `SRC-07`: [GitHub MCP Server](https://github.com/github/github-mcp-server) — published `undated`, retrieved `2026-03-04`
- `SRC-08`: [microsoft/playwright-mcp](https://github.com/microsoft/playwright-mcp) — published `undated`, retrieved `2026-03-04`
- `SRC-09`: [Langfuse Docs](https://langfuse.com/docs) — published `undated`, retrieved `2026-03-04`
- `SRC-10`: [Parallel Docs](https://docs.parallel.ai/home) — published `undated`, retrieved `2026-03-04`
- `SRC-11`: [Runlayer Docs](https://docs.runlayer.com/) — published `undated`, retrieved `2026-03-04`
- `SRC-12`: [Context7](https://context7.com/) — published `undated`, retrieved `2026-03-04`
- `SRC-13`: [1Password Developer Docs](https://developer.1password.com/) — published `undated`, retrieved `2026-03-04`
- `SRC-14`: [Sentry Docs](https://docs.sentry.io/) — published `undated`, retrieved `2026-03-04`

Top Tier C examples:
- `PostHog` (cursor_plugin): credible and Cursor-compatible, but outranked by higher-leverage candidates for this repo
- `Braintrust` (external_server): credible and Cursor-compatible, but outranked by higher-leverage candidates for this repo
- `CodeScene` (external_server): credible and Cursor-compatible, but outranked by higher-leverage candidates for this repo
- `CodeSherlock` (external_server): credible and Cursor-compatible, but outranked by higher-leverage candidates for this repo
- `Endor Labs` (external_server): credible and Cursor-compatible, but outranked by higher-leverage candidates for this repo
- `Luciq` (external_server): credible and Cursor-compatible, but outranked by higher-leverage candidates for this repo
- `Amplitude` (external_server): repo fit is only medium
- `Astro docs server` (external_server): overlap with current tooling is partial
- `Browser Use` (external_server): overlap with current tooling is partial
- `DryRun Security` (external_server): credible and Cursor-compatible, but outranked by higher-leverage candidates for this repo
- `Glean` (cursor_plugin): overlap with current tooling is partial
- `Hex` (external_server): repo fit is only medium
- `Pendo` (external_server): repo fit is only medium
- `PlanetScale` (cursor_plugin): credible and Cursor-compatible, but outranked by higher-leverage candidates for this repo
- `Vantage` (external_server): credible and Cursor-compatible, but outranked by higher-leverage candidates for this repo
