# Context7 Pilot (PhD)

**Status:** proposed and locally configured on **March 4, 2026**. Live server handshake is still blocked until `CONTEXT7_API_KEY` is present in the shell environment that launches Cursor.

## 1. Context

### Local facts
- This machine is now on Cursor `2.6.11` according to [latest_report.md](/Users/christianpardo/Desktop/concentric_study/operator/cre/artifacts/cursor_environment/latest_report.md).
- The repo already concluded that the strongest first external MCP is `Context7` because the current workflow needs better current-doc retrieval for fast-moving libraries and APIs. See [CURSOR_MCP_LANDSCAPE_PHD.md](/Users/christianpardo/Desktop/concentric_study/operator/cre/CURSOR_MCP_LANDSCAPE_PHD.md).
- The repo's own workflow memos identify documentation retrieval, environment discipline, and high-evidence implementation as the highest-value upgrade zones. See [MISSED_TOOL_WORKFLOW_VALUE_PHD.md](/Users/christianpardo/Desktop/concentric_study/operator/cre/MISSED_TOOL_WORKFLOW_VALUE_PHD.md) and [PHASE_1_ENVIRONMENT_BENEFITS_PHD.md](/Users/christianpardo/Desktop/concentric_study/operator/cre/PHASE_1_ENVIRONMENT_BENEFITS_PHD.md).
- This repo actively uses external packages where stale model memory can cause real implementation errors:
  - `google-genai` in [agent_core.py](/Users/christianpardo/Desktop/concentric_study/operator/agent_core.py)
  - `google.genai.types.GoogleSearch` grounding in [site_knowledge.py](/Users/christianpardo/Desktop/concentric_study/operator/agent_infra/site_knowledge.py)
  - `pydantic` structured models in [agent_core.py](/Users/christianpardo/Desktop/concentric_study/operator/agent_core.py)
  - `Pillow` and `numpy` image logic in [verification_gate.py](/Users/christianpardo/Desktop/concentric_study/operator/agent_infra/verification_gate.py) and [visual_monitor.py](/Users/christianpardo/Desktop/concentric_study/operator/agent_infra/visual_monitor.py)
  - `pytest` integration-test gating in [conftest.py](/Users/christianpardo/Desktop/concentric_study/operator/cre/conftest.py)

### External facts
- Cursor's MCP docs support project-local `.cursor/mcp.json`, remote MCP servers, request headers, and environment-variable interpolation.
- Context7's official installation docs recommend the remote Cursor MCP connection and explicitly say a rule can be used to auto-invoke it for doc-sensitive prompts.
- MCP-Atlas (`arXiv:2602.00933`) supports claims-based partial-credit evaluation plus diagnostics on discovery, parameterization, error recovery, and efficiency. That is a better fit for an MCP pilot than binary pass/fail only.

### Forces
- The first pilot should maximize signal and minimize risk.
- The pilot must separate two different questions:
  - Does Cursor invoke Context7 on the right prompts and avoid it on the wrong ones?
  - When Context7 is used, does answer quality improve enough to justify keeping the rule always on?
- This is a single-user, single-repo pilot. The correct design is a bounded within-subject evaluation, not a broad rollout.

## 2. Decision

We will run a two-phase Context7 pilot:

1. **Selective invocation phase**
   Test whether the rule engages Context7 on external-package prompts and stays off repo-local or Cursor-product prompts.

2. **Paired value phase**
   For the positive-control prompts only, compare answer quality and latency with Context7 disabled versus enabled, using fresh chats and a fixed counterbalanced order.

This design keeps the pilot honest. A tool that produces good answers but triggers on the wrong prompts is still a bad always-on rule. A tool that triggers correctly but adds no answer-quality lift is also not worth default adoption.

## 3. Implemented Setup

Project-local Context7 MCP registration is now present at [mcp.json](/Users/christianpardo/Desktop/concentric_study/.cursor/mcp.json).

The config uses the official remote server pattern, but stores the key via environment interpolation rather than a literal secret:

```json
{
  "mcpServers": {
    "context7": {
      "url": "https://mcp.context7.com/mcp",
      "headers": {
        "CONTEXT7_API_KEY": "${env:CONTEXT7_API_KEY}"
      }
    }
  }
}
```

The project-local rule is at [context7-docs.mdc](/Users/christianpardo/Desktop/concentric_study/.cursor/rules/context7-docs.mdc). Its scope is intentionally narrow:
- use Context7 for current third-party library, SDK, framework, and migration questions
- do not use it for repo-local facts, host facts, or Cursor-product facts

## 4. Preflight

Before any scoring run:

1. Export `CONTEXT7_API_KEY` in the shell that launches Cursor.
2. Relaunch Cursor from that shell.
3. Open the repo in Cursor.
4. Confirm the `context7` MCP server appears as connected.
5. Pin one Cursor model for the full pilot. Do not change models between arms.
6. Keep all other MCP servers off for the pilot if possible.

Current blocker:
- `CONTEXT7_API_KEY` was not present in the shell environment during setup, so live connectivity was not validated yet.

## 5. Pilot Design

### Phase A: selective invocation

Purpose:
- verify routing discipline
- catch false-positive tool use

Design:
- Use the 10-question bank in [context7_pilot_rubric.json](/Users/christianpardo/Desktop/concentric_study/operator/cre/artifacts/context7_pilot_rubric.json).
- Ask each question in a fresh chat with Context7 enabled and the rule active.
- Do not append `use context7`.
- Record:
  - whether Context7 was invoked
  - whether the invocation was appropriate
  - whether the answer cited the right source type

Interpretation:
- Positive controls should usually invoke Context7.
- Negative controls should not invoke Context7.

### Phase B: paired value comparison

Purpose:
- measure actual answer-quality lift, not just tool visibility

Design:
- Run only the 8 positive controls.
- Use two fresh chats per prompt:
  - `A`: Context7 disabled in Cursor MCP settings
  - `B`: Context7 enabled with the rule active
- Use the fixed order schedule from the rubric JSON to counterbalance order effects.
- Keep the prompt text identical across arms.
- If `B` does not auto-invoke Context7, optionally run a third diagnostic retry with `use context7` appended. Record it as `rescue`, not as the primary treatment score.

Why this design:
- Within-subject pairing reduces variance because each question serves as its own control.
- Counterbalancing reduces order bias.
- Fresh chats reduce contamination from prior turns.
- A rescue run distinguishes routing failure from content failure.

## 6. Scoring

### Positive-control scoring (`0-10`)
- `0-4` factual correctness of claims and API names
- `0-2` version sensitivity or migration correctness
- `0-2` code usefulness for this repo's actual tasks
- `0-1` source traceability
- `0-1` uncertainty discipline and no overreach

Severe hallucination rule:
- Any answer that invents a package API, migration rule, or source support gets a severe-hallucination flag.
- A severe hallucination caps the score at `4`, even if other parts look polished.

### Negative-control scoring (`0-10`)
- `0-4` correct source routing and non-use of Context7 when out of scope
- `0-3` factual correctness from the proper source
- `0-2` traceability to local files or official Cursor sources
- `0-1` explicit statement that external package docs are not the right basis

### Operational metrics
- latency in seconds
- auto-invoked or not
- severe hallucination or not
- answer required manual correction or not

## 7. Acceptance Thresholds

Keep the rule always on only if all of the following hold:

- Phase A:
  - Context7 auto-invokes on at least `6/8` positive controls
  - Context7 stays off on both negative controls
- Phase B:
  - mean positive-control score with Context7 is at least `8.0/10`
  - mean score improvement over baseline is at least `+1.0`
  - Context7 wins at least `6/8` paired positive controls
  - median latency is not more than `25%` slower than baseline
  - zero severe hallucination incidents

Decision rule:
- **Pass:** keep the rule always on
- **Mixed:** keep the server installed, but use Context7 selectively or by explicit prompt suffix
- **Fail:** disable the rule and keep Context7 only as an occasional manual tool

## 8. Question-Bank Logic

The bank is deliberately not generic.

Positive controls target packages this repo actually uses:
- `google-genai`
- `pydantic`
- `requests`
- `Pillow`
- `numpy`
- `pytest`

Negative controls target questions that should come from:
- local repo files
- official Cursor product sources

This is important because the adoption decision is not "is Context7 good in general?"
The real decision is "does Context7 improve this repo's actual work without degrading tool discipline?"

## 9. Adjudication Guidance

- Score from copied outputs, not from memory.
- If possible, remove arm labels before scoring to reduce expectation bias.
- Do not over-interpret p-values with only 8 paired positives. Use practical thresholds, wins count, and clear failure modes.
- Preserve answer transcripts in the results template so later disagreement can be audited.

## 10. Sources

- Cursor MCP docs: <https://cursor.com/docs/context/mcp>
- Context7 official install docs / repo README: <https://github.com/upstash/context7#installation>
- MCP-Atlas abstract: <https://arxiv.org/abs/2602.00933>
