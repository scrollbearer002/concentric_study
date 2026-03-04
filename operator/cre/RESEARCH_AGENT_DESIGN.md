# Research Agent + Visual Monitor — Architecture Design

**Status note:** This document describes the original architecture design and
target integration pattern for `ResearchAgent` and `VisualMonitor`. Parts of
this design are now implemented in the universal-agent path, while other parts
remain design intent or selected-demo/test integrations. Treat present-tense
"always" or "before any task execution" language below as design intent unless
the current universal-agent path and tests show universal enforcement.

## 1. Problem Statement

The current system executes tasks *without first studying what it's building or how to build it*. When asked to "create X on website Y," the agent immediately begins clicking UI elements without:
- Finding reference images of X to know what the target looks like
- Studying how to render X (anatomy, composition, technique)
- Exploring what tools Y provides
- Defining a visual standard to compare against during/after execution

This produces blind execution — equivalent to a surgeon operating without imaging.

## 2. Research Basis

### 2.1 Pre-Task Research (Study Before Execution)

| Framework | Key Principle | Citation |
|-----------|--------------|----------|
| **AppAgent Phase 1** | Autonomous exploration before deployment; agent learns affordances then uses them | Yang et al., 2023, arXiv:2312.13771 |
| **GUI-explorer** | Transition-aware knowledge extraction: (observation, action, outcome) triples | ACL 2025, arXiv:2505.16827 |
| **SeeAct** | Grounding VLM actions in external documentation reduces hallucination 30-40% | Zheng et al., 2024, arXiv:2401.01614 |
| **PG-Agent** | Retrieval-Augmented perception guidelines from page graphs | 2025, arXiv:2509.03536 |

### 2.2 Iterative Visual Refinement (Compare and Correct)

| Framework | Key Principle | Citation |
|-----------|--------------|----------|
| **MIRA** | Perception-reasoning-action loop: atomic edits driven by visual feedback | 2025, arXiv:2511.21087 |
| **VisionDirector** | Closed-loop refinement with semantic verification and rollback after each edit | 2025, arXiv:2512.19243 |
| **RefineEdit-Agent** | LVLM-driven feedback loop for iterative refinement against target | 2025, arXiv:2508.17435 |
| **COCO BRP** | Bidirectional reflection for stable convergence | 2025, arXiv:2508.13815 |

### 2.3 Lightweight Visual Monitoring (Periodic Screenshots)

| Tool/Framework | Key Principle | Source |
|----------------|--------------|--------|
| **Peekaboo MCP** | ScreenCaptureKit for zero-focus-change captures; 3 tools (image, list, analyze) | steipete.me, 2025 |
| **Screeny MCP** | Privacy-first background window capture without focus change | github.com/rohanrav/screeny |
| **ScreenAgent** | Plan-action-reflection cycle with real screenshot observation | IJCAI 2024 |
| **macOS screencapture** | Native CLI, -x flag suppresses sound, ~800ms per capture | Built-in |

## 3. Architecture Design

### 3.1 New Module: `agent_infra/research_agent.py`

A pre-execution intelligence gatherer designed to run before execution in the
universal-agent path.

```
Dependency: standalone (no infra imports)
Position in chain: TraceWriter level (foundational, no dependencies)
```

**Three-phase pipeline:**

1. **STUDY_SUBJECT** — Find and capture reference images of what to build
   - Web search for reference images matching the task description
   - Screenshot/capture references as ground truth targets
   - Store as `reference_images/` in the run directory

2. **STUDY_METHOD** — Research how to build it
   - Search for tutorials, guides, techniques relevant to the subject
   - Produce a structured "method brief" (steps, techniques, pitfalls)
   - Store as `method_brief.json` in the run directory

3. **STUDY_TOOLS** — Explore what tools are available on the target platform
   - Leverages existing `SiteKnowledge` + `ExplorationLoop`
   - Maps every tool, shortcut, and interaction pattern
   - Produces a capabilities inventory

4. **SOLVE_EQUATION** — Find the optimal intersection
   - Given: (subject requirements) + (method knowledge) + (tool capabilities)
   - Output: an execution plan that maps method steps to available tools
   - Store as `execution_plan.json`

**Key data structures:**

```python
@dataclass
class ResearchBrief:
    task_description: str
    reference_images: list[str]       # paths to captured reference images
    method_brief: dict[str, Any]      # techniques, steps, pitfalls
    tool_inventory: dict[str, Any]    # available tools + capabilities
    execution_plan: list[dict]        # ordered steps mapping method to tools
    quality_criteria: list[str]       # what "done" looks like
```

### 3.2 New Module: `agent_infra/visual_monitor.py`

A lightweight background screenshot service that provides continuous visual state awareness.

```
Dependency: standalone (no infra imports)
Position in chain: TraceWriter level (foundational, no dependencies)
```

**Core concept: a background thread takes periodic screenshots and stores them in a ring buffer.**

```python
class VisualMonitor:
    def __init__(self, interval_seconds=5, buffer_size=50, output_dir=None):
        # Configurable interval (default 5s, adjustable 1-30s)
        # Ring buffer prevents unbounded disk usage
        # Output directory for persistent snapshots

    def start(self) -> None:
        # Launch background daemon thread
        # Uses screencapture -x (native, ~100ms, no focus change)

    def stop(self) -> None:
        # Stop the background thread, flush final snapshot

    def latest(self) -> str | None:
        # Return path to most recent screenshot

    def compare(self, reference_path: str) -> dict:
        # Pixel-level diff between current state and reference
        # Returns: similarity_score, diff_image_path, changed_regions

    def timeline(self, last_n: int = 10) -> list[str]:
        # Return paths to last N screenshots for review
```

**Implementation approach:**
- Uses `screencapture -x` (macOS native, ~100ms, silent, no focus change)
- Background `threading.Timer` with configurable interval
- Ring buffer (deque) with max size to prevent disk bloat
- Each capture: `{output_dir}/monitor/{timestamp}.png`
- Optional: pixel-diff comparison using PIL/numpy (lightweight, no ML model needed)

**Why not Peekaboo MCP?**
Peekaboo requires Node.js 20+, ScreenCaptureKit (macOS 14+), and adds MCP protocol overhead. Our system already uses `screencapture -x` successfully throughout the codebase. Adding a dependency for equivalent functionality violates YAGNI. The native approach is simpler, faster, and already proven in our pipeline.

### 3.3 Integration with Existing Infrastructure

```
                    ┌──────────────────┐
                    │  ResearchAgent   │  ← NEW (pre-execution)
                    │  study → plan    │
                    └────────┬─────────┘
                             │ execution_plan + references
                             ▼
┌──────────────┐    ┌──────────────────┐    ┌──────────────┐
│ SiteKnowledge│◄───│   TraceWriter    │───►│VisualMonitor │ ← NEW
│ (existing)   │    │   (existing)     │    │ (background) │
└──────────────┘    └────────┬─────────┘    └──────┬───────┘
                             │                      │
                     ┌───────▼───────┐      ┌──────▼───────┐
                     │ DiagnosticRdr │      │ compare() to │
                     │ (existing)    │      │ reference    │
                     └───────┬───────┘      └──────────────┘
                             │
                     ┌───────▼───────┐
                     │ HealingOrch   │
                     │ (existing)    │
                     └───────┬───────┘
                             │
                     ┌───────▼───────┐
                     │  OuterLoop    │  ← Enhanced with research + monitor
                     │ (existing)    │
                     └───────────────┘
```

**Dependency chain preserved:**
- `ResearchAgent` has NO imports from agent_infra (standalone)
- `VisualMonitor` has NO imports from agent_infra (standalone)
- OuterLoop gains optional integration with both

### 3.4 Enhanced Outer Loop Cycle

Current: `Monitor → Diagnose → Adapt → Test`

New: `Research → Execute(Monitor) → Compare → Refine → Done`

```
1. RESEARCH (pre-execution)
   research_agent.study(task_description)
   → reference_images, method_brief, tool_inventory, execution_plan

2. EXECUTE (with live monitoring)
   visual_monitor.start(interval=5)
   trace_writer.begin(...)
   ... execute plan steps ...
   trace_writer.end(...)

3. COMPARE (post-step verification)
   After each major step:
   visual_monitor.compare(reference_image)
   → similarity_score, diff_regions

4. REFINE (iterative correction)
   If similarity < threshold:
     Identify what's wrong from diff
     Adjust, erase, redo
     Re-compare
   Loop until satisfied or max_iterations

5. DONE (final verification)
   visual_monitor.compare(reference_image) → final_score
   Store result + all monitor snapshots in trace
```

## 4. Files to Create/Modify

### New files:
- `operator/agent_infra/research_agent.py` — Pre-execution research pipeline
- `operator/agent_infra/visual_monitor.py` — Background screenshot monitor

### Modified files:
- `operator/agent_infra/__init__.py` — Export new modules
- `.cursor/rules/concentric-study.mdc` — Add Rule 15 (research-first universal workflow)
- `AGENTS.md` — Document new modules and workflow

### NOT modified:
- `trace_writer.py` — no schema changes needed
- `outer_loop.py` — integration is optional, not forced
- `skill_library.py` — unchanged
- Any existing test files

## 5. Quality Criteria for This Implementation

- [ ] Both new modules have zero imports from agent_infra (unidirectional chain preserved)
- [ ] VisualMonitor's background thread is a daemon (dies with main process)
- [ ] Ring buffer prevents unbounded disk usage
- [ ] ResearchBrief is JSON-serializable for trace storage
- [ ] Existing tests still pass
- [ ] Rule 15 captures the universal workflow in concentric-study.mdc
