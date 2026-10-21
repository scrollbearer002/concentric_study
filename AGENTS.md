# Concentric Study — Agent Instructions

This project is a general-purpose visual web agent on macOS, evolving from
single-site canvas automation toward cross-site autonomous web navigation.
It uses Gemini 2.5 Pro/Flash as vision-language models, Quartz HID events
for OS-level control, and a layered architecture with self-healing,
episodic memory, and security hardening.

## Infrastructure

The project has a shared infrastructure package at `operator/agent_infra/`:

| Module | Purpose |
|--------|---------|
| `trace_writer.py` | Writes structured JSONL execution traces and per-run manifests |
| `diagnostic_reader.py` | Reads traces with progressive disclosure (3 detail levels) |
| `healing_orchestrator.py` | Classifies failures and recommends corrective actions |
| `skill_library.py` | Stores verified successes as reusable skills with maturity gating, resolved_coords, and tool indexing |
| `outer_loop.py` | Dual-agent outer loop: Monitor → Diagnose → Adapt → Test. Includes ReflectionJournal and RulesStore |
| `action_trust.py` | Adaptive verification skip — tracks consecutive successes to skip costly VLM assertions |
| `summarizer.py` | Trajectory summarizer with folding and 500-token budget for VLM context injection |
| `research_agent.py` | Pre-execution 4-phase research pipeline: study subject, method, tools, then solve the equation |
| `host_tool_health.py` | Environment-readiness gate: host-tool health discovery and backend selection before capability activation |
| `visual_monitor.py` | Lightweight background screenshot monitor with ring buffer and pixel-diff comparison |
| `verification_gate.py` | Mandatory post-execution verification: constraint decomposition, screenshot capture, judge, pass/fail |
| `decision_graph.py` | Decision Dependence Graph analyzer: causal chain extraction, anomaly detection for trace-level root-cause analysis (MindGuard, arXiv:2508.20412) |
| `benchmark_evaluator.py` | MCP-Atlas-inspired benchmark evaluation: claims-based rubric, discovery precision, error recovery, plan optimality, NRP (arXiv:2602.00933) |

Additional modules at `operator/`:

| Module | Purpose |
|--------|---------|
| `a11y_engine.py` | macOS accessibility tree extraction (macapptree/pyax/AppleScript backends) |
| `element_map.py` | Unified Element Map — fuses SoM visual grounding with a11y tree data |
| `web_primitives.py` | Site-agnostic navigation primitives (click_element, type_into, scroll_to, etc.) |
| `inference_router.py` | Hybrid inference routing: Flash/Pro/Local model selection |
| `security/sanitizer.py` | Input sanitization against prompt injection attacks |
| `security/credential_vault.py` | macOS Keychain integration with HITL guards for sensitive actions |

Import with: `from agent_infra import TraceWriter, DiagnosticReader, SkillLibrary, OuterLoop, ActionTrustTracker, Summarizer, RulesStore, ResearchAgent, ResearchBrief, HostToolHealth, VisualMonitor, VerificationGate, DecisionDependenceAnalyzer, BenchmarkEvaluator, TaskClaim, SemanticSkillIndex`

For **related work and validation tiers** (implemented vs. proposed, Direct/Analogous/Novel), see **DUAL_AGENT_LOOP_PLAN.md** § Related Work and Validation Tiers.

For **evidence-first decision practice** (facts before each decision, PhD mindset), see **operator/cre/PHD_DECISION_PRACTICE.md**.

For **generating a single PDF for submission** from key docs (run locally), see **operator/cre/PLACEMENT_RESEARCH.md** § Submission PDF.

## Running Tests

```bash
cd operator
./venv/bin/python -m pytest cre/test_*.py -v --tb=short
```

To run the main GUI test:
```bash
cd operator
CONCENTRIC_TRIANGLES_CLEAN=1 ./venv/bin/python cre/test_excalidraw_covt.py
```

## Monitoring a Running Test

Each run produces a live trace at `operator/cre/runs/<run_id>/trace.jsonl`.
Steps are written as they complete. When `manifest.json` appears, the run is done.

Do NOT use `sleep` + `grep` to monitor. Read the trace file directly.

## Reading Results

```python
from agent_infra import DiagnosticReader
reader = DiagnosticReader("operator/cre/runs/<run_id>")
print(reader.full_diagnostic())
```

## Skill Library

```python
from agent_infra import SkillLibrary
lib = SkillLibrary("operator/cre")
print(lib.get_summary())
```

Skills progress: candidate (1 success) -> proven (3+) -> master (5+, 0 failures).
Only proven/master skills are trusted for autonomous reuse.

MASTER-tier skills now store `resolved_coords` in their action plans, enabling
coordinate cache replay that skips SoM + VLM calls entirely for known actions.

## Action Trust Tracker

The trust tracker (`action_trust.json`) persists success/failure counts per action key.
Verification is skipped only when the Beta-Binomial posterior lower bound exceeds
the configured reliability threshold at the configured confidence level.
Any failure resets the record, re-enabling verification.

```python
from agent_infra import ActionTrustTracker
tracker = ActionTrustTracker(persist_path="operator/cre/action_trust.json")
tracker.should_verify(("set_stroke_color", "black"))  # True initially, False only after sufficient posterior confidence
```

## Dual-Agent Outer Loop

The outer loop automates the full cycle: run test → read trace → classify failure → retry or escalate.

```bash
cd operator && ./venv/bin/python -m agent_infra.outer_loop --task CONCENTRIC_TRIANGLES_CLEAN
```

Or programmatically:
```python
from agent_infra import OuterLoop
loop = OuterLoop(
    task_id="CONCENTRIC_TRIANGLES_CLEAN",
    test_script="operator/cre/test_excalidraw_covt.py",
    runs_dir="operator/cre/runs",
)
result = loop.run()
```

Outcomes: `success`, `escalated` (ESCALATION.md written for code agent), `aborted`, `max_retries_exhausted`.

When `result.outcome == "escalated"`, read `result.escalation_path` for a structured diagnosis.

## Reflection Journal

The outer loop maintains episodic memory at `operator/cre/runs/reflection_journal.jsonl`.
Each cycle records a lesson learned. This prevents blind retries.

## Episodic Memory and Rules

The system learns from past runs:
- `reflection_journal.jsonl` stores verbal reflections after each cycle
- `rules.jsonl` stores explicit rules extracted from failure patterns (ExpeL-style)
- Before planning, the agent retrieves relevant past lessons and injects them into the VLM prompt

## Summarizer (Context Persistence)

The Summarizer compresses execution history into a 500-token budget for VLM context:
```python
from agent_infra import Summarizer
s = Summarizer(token_budget=500)
s.ingest_step(trace_step_dict)
context = s.get_context()  # inject into VLM prompt
```

## Research Agent (Pre-Execution Intelligence)

The ResearchAgent is integrated into the universal-agent path and can be run
before task execution to gather intelligence:

```python
from agent_infra import ResearchAgent
researcher = ResearchAgent(output_dir="operator/cre/runs/<run_id>")
brief = researcher.research(
    task="Draw two interlaced hands over a shattered glass sphere",
    site_url="https://www.canva.com/draw/",
)
print(brief.get_plan_summary())
```

Four-phase pipeline:
1. **Study Subject** — find reference images of what to build
2. **Study Method** — research how to build it (tutorials, techniques)
3. **Study Tools** — inventory available platform tools (integrates with SiteKnowledge)
4. **Solve Equation** — map method steps to tool capabilities → execution plan

Outputs a `ResearchBrief` saved as `research_brief.json` in the run directory.

Research basis: AppAgent Phase 1 (arXiv:2312.13771), SeeAct (arXiv:2401.01614),
GUI-explorer (ACL 2025), PG-Agent (arXiv:2509.03536).

## Host Tool Health (Environment-Readiness Gate)

The HostToolHealth layer makes the local substrate explicit before capability
activation begins:

```python
from agent_infra import HostToolHealth
checker = HostToolHealth()
payload = checker.evaluate(has_url=True)
print(payload["all_required_ready"])
print(payload["selected"])
```

It distinguishes:
- required substrate classes for the current task
- optional augmentation backends
- selected providers for each satisfied capability class

This prevents the universal-agent path from silently assuming that this machine
has the right Python runtime, AppleScript/System Events access, PyObjC native
stack, screenshot path, and browser target available.

## Visual Monitor (Continuous State Awareness)

Background screenshot service with comparison capability, wired into the
universal-agent path and selected demos/tests:

```python
from agent_infra import VisualMonitor
monitor = VisualMonitor(interval_seconds=5, buffer_size=50, output_dir="/tmp/monitor")
monitor.start()

# Execute task steps...

# Check current state against reference
result = monitor.compare("reference_image.png")
print(f"Similarity: {result.similarity_score}")  # 0.0 to 1.0
print(f"Assessment: {result.assessment}")

# Review timeline
for snap in monitor.timeline(last_n=5):
    print(f"[{snap.index}] {snap.iso_time}")

monitor.stop()
```

Features:
- Background daemon thread captures screenshots every N seconds (configurable)
- Ring buffer (default 50) prevents unbounded disk usage, auto-deletes oldest
- Pixel-diff comparison via PIL/numpy (no VLM needed, ~50ms per compare)
- Uses macOS `screencapture -x` (~100ms, silent, no focus change)
- Timeline retrieval for post-mortem review

Research basis: Peekaboo MCP (2025), ScreenAgent (IJCAI 2024), MIRA (arXiv:2511.21087).

## Verification Gate (Post-Execution Verification Layer)

The VerificationGate is implemented as a mandatory checkpoint in the
universal-agent path and selected demos/tests. It prevents the agent from
declaring success without looking at what it actually produced.

```python
from agent_infra import VerificationGate
gate = VerificationGate(
    task_description="Draw two hands interlaced over a shattered glass sphere",
    output_dir="/tmp/verification",
)
result = gate.verify()  # takes screenshot, decomposes constraints, judges each
if not result.passed:
    for d in result.deficiencies:
        print(f"FIX: {d}")
```

Features:
- Decomposes task into individually verifiable constraints (CRAFT pattern)
- Captures screenshot automatically (VISCO LOOKBACK)
- Judges via VLM (semantic, accurate) or pixel heuristics (fast, fallback)
- Returns structured VerificationResult with pass/fail per constraint
- `verify_loop(fix_fn, max_iterations)` automates the fix-reverify cycle
- All results saved as JSON for trace storage

Research basis: CRAFT (arXiv:2512.20362), GUI-Shepherd (2025), VISCO (CVPR 2025),
Maestro (arXiv:2509.10704), VisionDirector (arXiv:2512.19243).

## Decision Dependence Graph (Causal Trace Analysis)

The DDG analyzer builds causal dependency graphs from execution traces,
adapting MindGuard's attention-based DDG (arXiv:2508.20412) for offline
trace analysis using state-flow dependencies instead of attention weights.

```python
from agent_infra import DecisionDependenceAnalyzer
analyzer = DecisionDependenceAnalyzer()
analyzer.build_from_trace(trace_steps)  # list of step dicts
anomalies = analyzer.detect_anomalies()
chain = analyzer.get_causal_chain(failure_step_index)
context = analyzer.get_failure_context(failure_step_index)
```

Anomaly types detected:
- **orphaned_action**: Step with no causal predecessor (hallucinated step)
- **state_discontinuity**: Failed step with no incoming data-flow edges
- **repeated_failure_chain**: Same action type fails consecutively
- **thought_action_divergence**: Thought mentions different action than executed

The HealingOrchestrator integrates DDG via `analyze_run_with_ddg()`:
```python
from agent_infra import HealingOrchestrator
orch = HealingOrchestrator("operator/cre/runs")
classification = orch.analyze_run_with_ddg("operator/cre/runs/<run_id>")
# classification.details includes [DDG Analysis] causal chain info
```

Research basis: MindGuard (arXiv:2508.20412), AgentArmor (arXiv:2508.01249),
IPIGuard (arXiv:2508.15310, EMNLP 2025), Ferrante et al. (TOPLAS 1987).

## Benchmark Evaluator (MCP-Atlas Methodology)

The BenchmarkEvaluator provides multi-dimensional run evaluation using
the claims-based rubric from MCP-Atlas (arXiv:2602.00933).

```python
from agent_infra import BenchmarkEvaluator, TaskClaim
evaluator = BenchmarkEvaluator()
evaluator.register_claims("CONCENTRIC_TRIANGLES_CLEAN", [
    TaskClaim("Task completed successfully", "check_success"),
    TaskClaim("All steps succeeded", "check_all_steps_passed"),
    TaskClaim("Completed within 120 seconds", "check_duration_under"),
])
evaluator.register_optimal_steps("CONCENTRIC_TRIANGLES_CLEAN", 10)

result = evaluator.evaluate_run("operator/cre/runs/<run_id>")
print(f"Claims: {result.claims_score:.0%}")
print(f"Recovery: {result.recovery_rate:.0%}")

report = evaluator.get_aggregate_report()
```

Metrics computed:
- **Claims score**: Weighted fraction of verifiable claims satisfied (MCP-Atlas)
- **Discovery precision**: Fraction of actions that succeeded (MCP-Atlas)
- **Error recovery rate**: Failures followed by successful recovery (MCP-Atlas)
- **Plan optimality**: Ratio of optimal steps to actual steps (MCPToolBench++)
- **Net Resilient Performance**: PUA × (1-ASR) security metric (MSB, ICLR 2026)

Research basis: MCP-Atlas (arXiv:2602.00933), MCP-Bench (NeurIPS 2025),
MCPToolBench++ (arXiv:2508.07575), MSB (arXiv:2510.15994, ICLR 2026).

## Semantic Skill Retrieval (RAG-MCP Pattern)

The SkillLibrary now supports dual-layer semantic retrieval:

1. **Dense vector similarity** via sentence-transformers (when available)
2. **TF-IDF fallback** (zero dependencies, always available)

```python
from agent_infra import SkillLibrary
lib = SkillLibrary("operator/cre")
# Automatically uses semantic retrieval if sentence-transformers installed
results = lib.retrieve_by_similarity("draw nested triangles")
# Returns [(SkillRecord, similarity_score), ...]
```

The semantic layer bridges the lexical gap: "nested triangles" matches
"concentric triangle clean" because the embeddings capture semantic meaning,
not just shared tokens.

Research basis: RAG-MCP (arXiv:2505.03275), Sentence-BERT (arXiv:1908.10084,
EMNLP 2019), VOYAGER (NeurIPS 2023), CompactPrompt (arXiv:2510.18043).

## Perception Stack

- **SoM (Set-of-Mark)**: Pure-pixel visual grounding via grid overlay
- **A11y Engine**: macOS accessibility tree extraction for semantic labels
- **Unified Element Map**: Fuses SoM zones with a11y elements for hybrid perception
- **Parallel Scout Dispatch**: 4 simultaneous Gemini Flash queries for rapid page analysis

## Security

- **InputSanitizer**: Detects prompt injection, credential phishing, hidden instructions, plus MCP-specific tool poisoning defense (8 new patterns covering OWASP MCP Top 10)
- **MCP Tool Poisoning Defense**: `sanitize_tool_description()` for tool metadata, `sanitize_tool_response()` for tool outputs, `verify_schema_integrity()` for rug-pull detection (CVE-2025-54136)
- **CredentialVault**: macOS Keychain integration; credentials never appear in logs or VLM prompts
- **HITLGuard**: Pauses execution for human approval on password fields, form submissions, unknown domains

MCP-specific threat coverage (OWASP MCP Top 10 + MSB arXiv:2510.15994):
- Tool description override/poisoning (MCP03)
- Tool impersonation / out-of-scope parameters (MSB: 74.03% ASR)
- Cross-tool injection and tool-transfer attacks
- Privilege escalation via scope creep (MCP02)
- False-error escalation to trigger fallback paths
- Shadow tool detection (MCP09)
- User impersonation in tool responses
- Context injection / over-sharing (MCP10)
- Schema rug-pull detection (CVE-2025-54136, CVSS 7.2-8.8)

## Architecture-Critical Files

Do not modify without understanding the design:
- `operator/agent_infra/*.py` — shared infrastructure
- `operator/cre/test_excalidraw_covt.py` — main test with tracing, coord cache, trust tracker, summarizer
- `operator/a11y_engine.py` — accessibility tree extraction
- `operator/element_map.py` — unified element map (SoM + a11y fusion)
- `operator/web_primitives.py` — site-agnostic navigation primitives
- `operator/inference_router.py` — hybrid model routing
- `operator/security/` — sanitization and credential vault
- `operator/cre/skill_library.json` — persistent skill data
- `operator/cre/action_trust.json` — trust tracker persistence
- `operator/cre/runs/` — trace data, reflection journal, rules

## Agent Workflow: Two Complementary Protocols

| Protocol | Governs | Rule | When |
|----------|---------|------|------|
| **Facts Before Each Decision** | Design decisions (what/why) | Rule 12 | Any non-trivial design, placement, refactor, or policy choice |
| **Research-First Implementation** | Implementation tasks (how) | Rule 13 | Any non-trivial build, feature, or code change |
| **Decomposition Handbook** | Exhaustive topic trees (coordinator + workers) | Handbook | When the task is to take a system apart depth-first without overload |

Rule 13 follows: **Triage → Analyze → Strategize → Execute → Reflect**.
Trivial tasks (<3 lines, mechanical) skip to Execute.
Full method and research citations: `operator/cre/PHD_DECISION_PRACTICE.md` §4.
Coordinator+worker decomposition (budgets, funnel/refs, basement push): `operator/cre/DECOMPOSITION_HANDBOOK_PHD.md`. Master prompt: `operator/cre/artifacts/decomposition_handbook_master_prompt.txt`.
