# PhD Memo: Event-Triggered Recovery Checkpoints

**Purpose:** Document why the recovery loop now forces `VisualMonitor.capture_now()` checkpoints around high-risk repairs, and why that is the correct next move for this repo.

## 1. Decision

Add event-triggered monitor checkpoints around:

1. diagnosed failure
2. before recovery action
3. after recovery action
4. before precondition repair
5. after precondition repair
6. after contract repair
7. recovery postcondition pass/fail

This was implemented in:

- `operator/agent_infra/recovery.py`
- `operator/agent.py`

## 2. Local evidence

Before this change:

- the monitor existed and captured on a fixed interval:
  - `operator/agent_infra/visual_monitor.py:115`
  - `operator/agent_infra/visual_monitor.py:137`
- the universal agent started and stopped the monitor:
  - `operator/agent.py:1738`
  - `operator/agent.py:1769`
- the recovery loop diagnosed failures and executed repairs:
  - `operator/agent_infra/recovery.py:146`
  - `operator/agent_infra/recovery.py:174`
  - `operator/agent_infra/recovery.py:430`
  - `operator/agent_infra/recovery.py:534`

But there was still a temporal observability gap:

- periodic capture can miss short-lived dialogs and transient UI states
- recovery logic knew *when* it attempted a repair, but the monitor timeline did not explicitly mark those moments

That gap was visible in the Kleki failure sequence, where modal interference and state drift mattered more than static end-state inspection.

## 3. Research basis

### 3.1 Screen history matters, not just the current frame

`UI-Hawk` shows that GUI agents relying only on the current screen and text history miss crucial temporal information and that screen-stream understanding is essential for GUI tasks.

Source:
- https://aclanthology.org/2025.emnlp-main.920/

### 3.2 History-aware reasoning improves long-horizon GUI behavior

`History-Aware Reasoning for GUI Agents` argues that long-horizon GUI execution requires explicit short-term memory of previous interactions rather than treating each screen independently.

Source:
- https://arxiv.org/abs/2511.09127

### 3.3 Temporal redundancy only helps if salient frames are retained

`GUI-KV` shows that GUI workloads contain temporal redundancy, but also that semantically important frames must be preserved rather than uniformly discarded.

Source:
- https://arxiv.org/abs/2510.00536

**Inference from source:** event-triggered checkpoints are a practical way to preserve semantically important recovery frames inside a long run.

### 3.4 Closed-loop refinement benefits from checkpointed visual verification

`VisionDirector` uses staged edits with semantic verification and rollback after each edit step.

Source:
- https://arxiv.org/abs/2512.19243

**Inference from source:** the same principle applies here. Recovery actions are not ordinary steps; they are intervention points that deserve dedicated visual evidence.

### 3.5 Runtime evidence should be mapped to higher-level control events

SEI’s running-systems work shows that runtime observations become more useful when low-level events are mapped onto meaningful architectural operations.

Source:
- https://www.sei.cmu.edu/library/discovering-architectures-from-running-systems-lessons-learned/

**Inference from source:** raw periodic screenshots are weaker than screenshots labeled with recovery phases such as `before_recovery_action` or `recovery_postcondition_failed`.

## 4. What changed

### 4.1 Recovery checkpoints are now explicit

Added checkpoint forcing in:

- `operator/agent_infra/recovery.py:62`
- `operator/agent_infra/recovery.py:194`
- `operator/agent_infra/recovery.py:242`
- `operator/agent_infra/recovery.py:506`

The helper records:

- phase label
- file path
- step index
- attempt index
- action type
- diagnosis summary

### 4.2 Checkpoints are now persisted with the run

The run-level monitor artifact now includes checkpoint metadata in:

- `operator/agent.py:1769`

New persisted artifact:

- `operator/cre/runs/<run_id>/visual_monitor/checkpoints.json`

## 5. Why this is the right level of intervention

This is a narrow runtime-observability improvement, not a broad redesign.

It does **not**:

- change planner semantics
- change the action space
- change final verification criteria

It **does**:

- increase temporal evidence density exactly where failures branch
- make recovery post-mortems more defensible
- support better benchmark interpretation later

## 6. Validation

Regression coverage:

- `operator/cre/test_runtime_tool_integration.py`

Validated:

1. run-level checkpoint persistence
2. forced checkpoint recording from the recovery helper

## 7. Next steps

1. use the new checkpoints to compare a fresh live art run against `operator/cre/runs/0b64930f0c59` and `operator/cre/runs/9d28b35cf1b0`
2. add task-family benchmark claims so checkpoint-rich runs are judged against task semantics, not only generic success
