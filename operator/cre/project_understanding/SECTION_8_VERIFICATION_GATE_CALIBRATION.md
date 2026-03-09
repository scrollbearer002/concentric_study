# Section 8: VerificationGate Calibration Against Human Judgment

## 1. Purpose

Section 7 closed the outcome-semantics ambiguity around accepted, rejected, and
final-verification outcomes. That makes the next empirical question sharper:

- does `VerificationGate` agree with humans often enough to be trusted as the
  repo's terminal acceptance signal?

This section records the current implementation path toward answering that
question with data rather than intuition.

## 2. Research Basis

The calibration requirement is not cosmetic.

- `Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena` established that
  model judges should be evaluated against humans rather than treated as
  self-validating.
- `Judge's Verdict` pushed the same point further: human agreement and
  task-conditioned calibration matter more than generic confidence claims.
- `Inter-Coder Agreement for Computational Linguistics` matters here because it
  makes chance-corrected agreement and explicit multi-annotator protocol part
  of the methodological baseline rather than an optional afterthought.
- `WebVoyager` showed that automatic web-agent evaluation can be useful, but
  only when its agreement with humans is explicitly measured.
- `Multimodal Auto Validation For Self-Refinement in Web Agents` strengthens
  the same lesson in a multimodal web-agent setting: visual validators are only
  persuasive when grounded against human decisions.

The method implied by that literature is:

1. export stable review packets from archived runs
2. collect blind human labels independently
3. adjudicate disagreements when needed
4. compute explicit human-human and gate-human agreement metrics
5. only then decide whether the gate is reliable enough to govern acceptance

## 3. Problem

Before this implementation sequence, the repo had:

- `VerificationGate` verdict artifacts in run directories
- trace and manifest data that already knew whether a run was accepted
- no stable dataset contract for human review
- no support for independent double rating or adjudication
- no repeatable agreement metrics for either human-human or gate-human
  comparison

That meant the project could say "calibrate the gate against humans" but had no
artifact path that would let a human or another agent actually do it with a
defensible review protocol.

## 4. Implementation

The calibration tool now lives at:

- `operator/cre/project_understanding/tools/build_verification_calibration.py`

It now does three jobs.

### 4.1 Candidate export

The tool scans archived run directories for `verification/verification_*.json`
artifacts and exports one human-review packet per artifact into:

- `artifacts/verification_calibration_candidates.jsonl`

Each record includes:

- `run_id`
- `task_id`
- `task_description`
- manifest `outcome`
- normalized `task_result`
- normalized `final_verification_status`
- gate verdict, score, deficiencies, and constraints
- screenshot and reference-image paths
- `human_review.labels` for independent raters
- `human_review.adjudicated_label` for resolved ground truth

This creates a durable review surface from already-executed runs.

### 4.2 Blinded review packets

The tool can now write review packets into:

- `artifacts/verification_review_packets/blind/`
- `artifacts/verification_review_packets/adjudication/`

The blind packet deliberately hides:

- gate pass/fail
- gate score
- gate deficiencies
- gate constraint outcomes

The adjudication packet reveals those artifacts only after independent labels
exist or disagreement requires resolution.

### 4.3 Agreement scoring

Once reviewers fill the human-review fields, the same tool computes:

- overall pass/fail agreement
- confusion matrix: `tp`, `tn`, `fp`, `fn`
- accuracy
- precision
- recall
- `F1`
- observed agreement
- `Cohen's kappa`
- human-human agreement from the first two completed human labels
- optional constraint-level agreement when human labels are provided per
  constraint description
- score separation between human-pass and human-fail subsets

The tool also distinguishes review states:

- `unlabeled`
- `single_rater`
- `multi_rater_consensus`
- `pending_adjudication`
- `adjudicated`

This is the minimum empirical surface needed to argue that the gate is or is
not calibrated enough for acceptance control.

## 5. Workflow

The intended workflow is now:

```bash
python3 operator/cre/project_understanding/tools/build_verification_calibration.py \
  --build-candidates \
  --write-review-packets
```

Two independent reviewers label the blinded packets by filling
`human_review.labels` in the dataset:

- `overall_passed`
- `overall_verdict`
- `notes`
- `rater_id`
- optional `constraint_labels`

If they disagree, an adjudicator fills:

- `human_review.adjudicated_label`
- `human_review.adjudication_notes`

Then score the annotated dataset:

```bash
python3 operator/cre/project_understanding/tools/build_verification_calibration.py \
  --dataset operator/cre/project_understanding/artifacts/verification_calibration_candidates.jsonl
```

The summary is written to:

- `artifacts/verification_calibration_report.json`

### 5.1 First run and bootstrap trust (AI jury)

The first session won't be trustworthy — and that's fine.

With only a few packets (e.g. six) you won't have enough data for a meaningful Kappa score. The CalibrationTracker will return `insufficient_data`. That's not a failure; it's the system being honest. What the first run gives you is something more valuable than a score: **the first real verdicts** to compare against your own judgment.

1. Run the AI jury (see command below).
2. Read the output yourself. Look at every case where the AI jury disagrees with the agent.
3. Ask: do I agree with the jury or the agent? That comparison — your judgment vs the jury's — is how you **bootstrap trust**.
4. After 15–20 packets you'll have real Kappa numbers. After 50 you'll know whether to trust the judge autonomously.

**Before running:** Check that `verification_calibration_candidates.jsonl` packets have the `screenshot_path` field populated with real paths. The jury without screenshots is still functional (it judges on task description and agent verdict alone) but is significantly weaker. Visual evidence is what separates reliable from guesswork. If screenshots aren't embedded in the packets yet, pass `--screenshot-dir cre/runs` (run directories must follow `run_id/screenshot_final.png`).

When ready, the single jury command is all it takes; the court is fully staffed.

#### Closing the gap: three steps before first run

1. **Drop the file.** Place `ai_jury.py` at `operator/ai_jury.py`. The docs are ahead of the code; once the file is there, the system is runnable.

2. **Environment variables.** The default two-judge pool needs both keys. Add to `.env` or your shell:
   ```bash
   export ANTHROPIC_API_KEY=your_key_here
   export OPENAI_API_KEY=your_key_here
   ```
   If you only have one key, run with a single judge: `--judges claude` or `--judges gpt4o`. It works; you lose cross-validation and the debate round.

3. **Dependencies.** From `operator/`:
   ```bash
   ./venv/bin/pip install anthropic openai
   ```
   Everything else used by the jury (`json`, `base64`, `pathlib`, `re`, `math`) is standard library.

#### First jury session

From `operator/`:

```bash
./venv/bin/python ai_jury.py \
  --calibration-file cre/project_understanding/artifacts/verification_calibration_candidates.jsonl \
  --screenshot-dir cre/runs \
  --output-dir parliament/jury_records
```

The six sealed dockets stay sealed until that command opens them.

#### Full picture: what exists before first run

The **operational system** — agent, handlers, survey office, planning ministry, verification gate, records, memory — is built and running. Conformance clean.

The **Parliament** (`parliament.py`) — proactive knowledge health authority, staleness detection, pre-mission review, post-mission recording, census sweep. Ready to drop into `operator/`.

The **AI Jury** (`ai_jury.py`) — rubric decomposition, heterogeneous judge pool, adversarial debate, Cohen's Kappa calibration tracker. Ready to drop into `operator/`.

The **host capabilities brief** (`.cursor/rules/host-capabilities.mdc`) — every model in Cursor knows what it can do without being told.

The **jury interface** (`jury.html`) — human fallback to seed calibration with your own judgments before or alongside the AI jury.

The **documentation** — SECTION_8, EXHAUSTIVE_TOOLS_AND_TIPS_MASTER, and related docs — is aligned with the code. What's left is not building; it's running. Drop the files, set the env vars, run the command. The six dockets open; the CalibrationTracker accumulates; Kappa climbs toward 0.6; the republic becomes self-governing.

## 6. Local Validation

Focused local regression coverage now exists in:

- `operator/cre/test_verification_calibration.py`

That test suite checks:

- candidate review packets are exported correctly from archived verification
  artifacts
- effective ground truth selection prefers adjudication, then consensus, then
  single-rater fallback
- overall agreement metrics are computed correctly
- human-human agreement is computed correctly
- constraint-level agreement is computed correctly
- blinded review packets do not leak gate verdicts
- unlabeled records do not break the calibration summary

## 7. Current State

This implementation still does not pretend calibration is complete. It now
establishes both the artifact contract and the human-review protocol so the next
human-review pass will produce a real report instead of a subjective narrative.

The first live candidate export from the current repo found:

- `6` archived verification artifacts
- `1` gate pass
- `5` gate failures
- `0` effective human labels so far

The immediate next empirical step is:

- label the six archived packets with two independent human ratings
- adjudicate any disagreements
- compute both human-human and gate-human agreement
- decide whether `VerificationGate` is strong enough as-is or needs prompt,
  criterion, or threshold changes

## 8. Why This Matters

After Section 7, the repo has a cleaner truth surface for run outcomes. Section
8 adds the missing evaluator-trust surface and the study protocol needed to
measure it.

Together, they make a stronger claim possible:

- not only can the repo state whether a run was accepted or rejected
- it can test whether the judge that made that decision agrees with humans
- it can also test whether the human review process itself is stable enough to
  treat as ground truth

That is the correct PhD-level next step for a system whose acceptance logic now
depends on a visual judge.

## 9. Deferred Follow-Up

Deferred on `2026-03-05` at user request:

- walk through one real verification review packet from this repo and show
  exactly how a human would label it, step by step

This item remains pending until explicitly resumed.
