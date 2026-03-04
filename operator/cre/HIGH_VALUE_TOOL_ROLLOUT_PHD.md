# PhD Rollout Memo: High-Value Tool Integration

**Purpose:** Move from the research verdict in `operator/cre/MISSED_TOOL_WORKFLOW_VALUE_PHD.md` into a concrete, evidence-backed integration order for the main universal agent path.

## 1. Decision

The first runtime tools to wire into `operator/agent.py` should be:

1. `VisualMonitor`
2. `BenchmarkEvaluator`

`ResearchAgent` was already partially wired and therefore was not the highest-gap item anymore.

## 2. Local evidence

### 2.1 `ResearchAgent` was already in the hot path

- `operator/agent.py:643`
- `operator/agent.py:1918`

This means the repo had already moved beyond the older state documented in `operator/cre/SUBJECT_LOOKUP_FOR_DRAWING.md:85`.

### 2.2 `VisualMonitor` existed but was not in the universal agent path

- runtime module exists: `operator/agent_infra/visual_monitor.py:66`
- ad hoc usage existed in a test script, not the universal agent:
  - `operator/cre/test_canva_draw.py:267`

This is a workflow gap, not a missing component.

### 2.3 `BenchmarkEvaluator` existed but was not invoked from `agent.py`

- runtime module exists: `operator/agent_infra/benchmark_evaluator.py:152`
- test-only usage existed:
  - `operator/cre/test_phd_enhancements.py:336`

This meant runs were producing traces and manifests but not consistently producing claims-based evaluation.

## 3. Research basis

### 3.1 Why `VisualMonitor` first

GUI agents fail on temporal drift, not only current-state interpretation.

- `ScreenAgent` frames GUI operation as a screenshot-driven loop rather than a one-shot state read.
  - Source: https://arxiv.org/abs/2402.07945
- `UI-Hawk` argues that screen-stream understanding is necessary because current-frame-only observation misses crucial temporal context.
  - Source: https://aclanthology.org/2025.emnlp-main.920/
- SEI running-systems guidance supports recovering and validating architecture from actual runtime behavior rather than intended design alone.
  - Source: https://www.sei.cmu.edu/library/discovering-architectures-from-running-systems/

### 3.2 Why `BenchmarkEvaluator` second

Once runs are observable, they need repeatable scoring.

- `MCP-Atlas` supports claims-based partial-credit evaluation and diagnostic metrics over binary success alone.
  - Source: https://arxiv.org/abs/2602.00933
- `AutoGenBench` emphasizes repetition and controlled evaluation because single-run agent outcomes are noisy.
  - Source: https://microsoft.github.io/autogen/0.2/blog/2024/01/25/AutoGenBench/

## 4. Implementation completed in this pass

### 4.1 Visual monitor integration

- start helper added in `operator/agent.py:1738`
- stop-and-persist helper added in `operator/agent.py:1769`
- run wiring added in `operator/agent.py:1979`
- stop/finalize wiring added in `operator/agent.py:2166`

Outputs now persist into each run directory under:

- `operator/cre/runs/<run_id>/visual_monitor/status.json`
- `operator/cre/runs/<run_id>/visual_monitor/timeline.json`

### 4.2 Benchmark evaluation integration

- default evaluator builder added in `operator/agent.py:1808`
- post-finalize evaluator runner added in `operator/agent.py:1847`
- finalize wiring added in `operator/agent.py:1640`

Completed runs now automatically produce:

- `operator/cre/runs/<run_id>/benchmark_result.json`

### 4.3 Regression coverage

- `operator/cre/test_runtime_tool_integration.py`

This validates:

1. visual monitor artifacts are persisted
2. default benchmark claims are registered and saved

## 5. Why this order is methodologically correct

This order follows a strong architecture/evaluation sequence:

1. improve runtime observability
2. improve repeatable evaluation
3. only then expand behavioral control policies

That sequence is stronger than jumping directly into more recovery logic, because it improves the measurement substrate first.

## 6. Next steps

1. add `VisualMonitor.capture_now()` checkpoints after high-risk recovery actions
2. enrich benchmark claims with task-family-specific checks instead of only generic claims
3. fold benchmark summaries into the project-understanding corpus so architectural drift and task quality can be compared from the same run data
