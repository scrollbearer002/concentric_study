# Master Diagram: How the Republic Connects

## Purpose of This Chapter

This chapter is the single place where the full story of Concentric is turned into one explicit systems diagram. It answers five questions in order:

1. **System overview** — What is the republic, and what two loops hold it together?
2. **Ministry dependency chain** — Which institutions process a mission, and in what order, and why?
3. **Law-to-ministry matrix** — Which constitutional laws constrain which ministries?
4. **Feedback-loop map** — What loops turn one run into future state?
5. **Legitimacy-loop map** — What loop sits above the runtime and judges the judge?

The goal is to show how everything in the story connects: the city Christian founded, the ministries he built, the amendments he enacted, and the trial the republic now awaits. Nothing here is invented; every connection is anchored to the real code and artifacts in the repo.

---

## 1. System Overview

Concentric is a republic for converting **human intent** into **audited, learnable, and eventually legitimate action**.

It does not only “do tasks.” It qualifies what is being asked, staffs the right institutions, builds a world model, turns that model into lawful action, survives failure, judges the result, records the truth of that result, learns from it, and—in the highest loop—prepares to subject even its own final judge to human review.

### What enters the system

Every mission enters as a bundle of state, not a single string:

| Input class | Meaning | Where it is gated or supplied |
|-------------|---------|------------------------------|
| Human intent | Task description, target state, desired artifact | Executive (agent.py) |
| Target context | URL, app, site, or frontmost GUI state | Survey Office, window_capture |
| Host substrate | What this machine can support (Python, a11y, browser, etc.) | host_tool_health.py |
| Persistent civic memory | Skills, trust, site knowledge, rules, reflections | skill_library, action_trust, site_knowledge |
| Current frontier | What the system can perceive right now | a11y_engine, visual_engine, element_map |

The republic does not begin with action. It begins with **state qualification**: what is being asked, whether the machine can act, and what it already knows.

### The two loops that hold everything together

All of the story—Books I through VI—can be read as the emergence of two interlocking loops.

**Operational loop** (the day-to-day life of a mission):

```
see → understand → plan → act → recover → verify → record → learn
```

**Constitutional loop** (the life of the state across time):

```
describe the state → constrain the state → audit the state → judge the judge → reform the state
```

The operational loop is *how* a single mission runs. The constitutional loop is *how* the republic became more truthful, more aligned, and finally ready for the trial of its Supreme Inspectorate.

### One-sentence reading

The Executive receives a mission; the staffing layer decides which ministries are active; the Survey Office builds a world model; the Planning Ministry turns desire into doctrine; the Legislature provides the public action code; the Ministry of Interior and the Machinery Depot dispatch those actions; the Emergency Authority handles failure; the Supreme Inspectorate judges the final result; the Ministry of Records preserves what happened; the auditors and memory institutions interpret and learn from it; and the legitimacy loop waits above all of this to judge the judge.

That is the system in one breath.

---

## 2. Ministry Dependency Chain

The runtime is a **chain of ministries**. Each ministry exists because the previous one, by itself, is insufficient. Order is dependency order: you cannot plan without perception, cannot dispatch without law, cannot judge without execution.

| # | Ministry | Primary file(s) | Why it comes next |
|---|----------|-----------------|-------------------|
| 1 | **Executive Office** | agent.py (line 2627) | The republic needs a sovereign reading of the task before it can know which institutions to activate. |
| 2 | **Civil Service Commission** | capability_router.py (line 132) | The mission must be framed before staffing; the executive defines the problem, this layer defines the active apparatus. |
| 3 | **Survey Office** | a11y_engine.py (74), visual_engine.py (18), element_map.py (71), window_capture.py (104) | The republic cannot plan over a world it has not observed. This is the first anti-fantasy institution. |
| 4 | **Planning Ministry** | research_agent.py (394) | Planning must be grounded in observed territory; raw perception is not yet strategy. |
| 5 | **Legislature** | action_space.py (43) | Planning needs a lawful grammar; without it, plans remain prose, not state-sanctioned action. |
| 6 | **Ministry of Interior and Public Works** | action_handlers.py (3558) | Laws must become dispatch; this is where public action names become concrete operations. |
| 7 | **State Machinery Depot** | agent_core.py (183) | Handlers define operational semantics; the depot makes them physically true (clicks, keys, screenshots). |
| 8 | **Emergency Authority** | recovery.py (662), healing_orchestrator.py, decision_graph.py, outer_loop.py | Foreign territory is unstable; failure must be institutionalized, not treated as a surprise. |
| 9 | **Supreme Inspectorate** | verification_gate.py (88) | Successful motion is not identical to accepted result; the republic needs a final office that says whether the task truly counts as done. |
| 10 | **Ministry of Records** | trace_writer.py (164) | An unrecorded mission cannot become evidence or institutional knowledge. |
| 11 | **Inspector General & Treasury** | diagnostic_reader.py (57), benchmark_evaluator.py (377) | Archives must become intelligible diagnosis and comparable judgment. |
| 12 | **National Memory Archive & Risk Office** | skill_library.py (244), site_knowledge.py (101), action_trust.py (60), outer_loop.py (247) | The republic is supposed to learn across runs, not only repeat. |

### Why each connection exists (anti-failure design)

- **Executive → Capability Router** — Prevents mobilizing wrong or missing institutions.
- **Capability Router → Survey** — Prevents acting without a current world model.
- **Survey → Planning** — Prevents strategy detached from the actual page or screen.
- **Planning → Legislature** — Prevents free-form plans with no lawful execution vocabulary.
- **Legislature → Interior** — Prevents semantic plans that cannot be dispatched.
- **Interior → Machinery** — Prevents “implemented” actions without real machine control.
- **Execution → Recovery** — Prevents brittle one-shot failure in dynamic environments.
- **Recovery → Verification** — Prevents mistaking completed motion for successful task completion.
- **Verification → Records** — Prevents losing the final truth of what happened.
- **Records → Diagnostics/Benchmarks** — Prevents archives that cannot drive understanding or measurement.
- **Diagnostics/Benchmarks → Memory** — Prevents repeated ignorance across runs.

The architecture is a **chain of anti-failure institutions**.

---

## 3. Law-to-Ministry Matrix

The runtime is governed by **constitutional laws** that were added to prevent specific kinds of state falsehood. Each law constrains one or more ministries and is anchored in specific files.

| Law | Primary file(s) | Ministries constrained | What it prevents |
|-----|-----------------|------------------------|-------------------|
| **Truthful Lawbook Act** | action_space.py (53) | Legislature | Legal overstatement of capability; planner-visible law must be checkable against live dispatch. |
| **Executive Dispatchability Act** | action_handlers.py (3560) | Legislature, Ministry of Interior | Public verbs that exist only on paper; planner-visible verbs must have live handler support. |
| **Emergency Powers Validity Act** | research_agent.py (258) | Planning Ministry | Imaginary contingency plans; fallback action types must be as lawful as primary. |
| **Boundary Discipline Act** | action_handlers.py (32), agent.py (2779), research_agent.py (394) | Interior, Executive, Planning | Hidden cross-layer coupling; ministries must communicate through ports and injected interfaces. |
| **Unified Civil Registry Act** | trace_writer.py (223) | Ministry of Records | Fragmented sovereignty over mission truth; task result, execution result, verification, step outcomes must be separate but coherent. |
| **Auditor Alignment Act** | diagnostic_reader.py (64), benchmark_evaluator.py (377) | Inspector General, Treasury | Archives and evaluators speaking different languages about the same run; both must use normalized outcome semantics. |
| **Inspectorate Accountability Act** | build_verification_calibration.py (469), SECTION_8_VERIFICATION_GATE_CALIBRATION.md | Supreme Inspectorate (indirectly: the court that judges it) | Permanent unreviewable authority; the final judge must be calibratable against blinded human review. |

### Flow of law through the chain

- **Legislature** is constrained by the Truthful Lawbook and Dispatchability acts (what can be said and what must be executable).
- **Planning Ministry** is constrained by Emergency Powers Validity (fallbacks must be real).
- **Interior and Executive** are constrained by Boundary Discipline (no private tunnels).
- **Ministry of Records** is constrained by the Unified Civil Registry (one sovereign truth).
- **Inspector General and Treasury** are constrained by Auditor Alignment (same truth contract).
- **Supreme Inspectorate** is not “constrained” by a law inside the runtime but is **subject to** the Inspectorate Accountability Act via the calibration court: its verdicts can be compared to human judgment.

---

## 4. Feedback-Loop Map

Concentric is defined as much by its **loops** as by its layers. Four major feedback loops turn one run into future state.

### 4.1 Tactical execution loop

**Sequence:** `plan → execute → verify local effect → recover if needed → continue`

**Primary file:** recovery.py (662)

**Purpose:** Keep the mission alive inside unstable territory. Single-run resilience.

---

### 4.2 Archive and diagnosis loop

**Sequence:** `run → trace → manifest → diagnostic reading → benchmark evaluation`

**Primary files:** trace_writer.py (164), diagnostic_reader.py (57), benchmark_evaluator.py (377)

**Purpose:** Convert action history into state-readable evidence. This is how the republic *knows* what happened and how it compares to other runs.

---

### 4.3 Memory and policy loop

**Sequence:** `successful traces and repeated outcomes → skill / trust / site knowledge / rules → future planning and execution bias`

**Primary files:** skill_library.py (244), action_trust.py (60), site_knowledge.py (101), outer_loop.py (247)

**Purpose:** Make the republic stateful across missions. Past success and failure change future behavior.

---

### 4.4 Failure-to-reform loop

**Sequence:** `failure → classification → causal analysis → reflection → retry, rule, or escalation`

**Primary files:** healing_orchestrator.py, decision_graph.py (162), outer_loop.py (247)

**Purpose:** Ensure failure becomes civic knowledge rather than isolated pain. Lessons and rules persist; escalation can hand off to a code agent when the republic cannot heal itself.

---

### Summary diagram (feedback loops)

```
Tactical:     [ plan → execute → verify effect → recover ] → (continue)
Archive:      [ run → trace → manifest → diagnose → benchmark ]
Memory:       [ success/failure → skills/trust/site knowledge/rules ] → (future runs)
Failure-reform: [ failure → classify → analyze → reflect ] → (retry | rule | escalate)
```

---

## 5. Legitimacy-Loop Map

The **legitimacy loop** sits **above** the runtime. It does not make missions run; it makes the republic’s final judge **auditable**.

### Sequence

1. **VerificationGate** produces verdict artifacts during or after missions (pass/fail, deficiencies).
2. Archived verification records are **exported** as calibration candidates.
3. **Blind review packets** are created so human raters do not see the gate’s own verdict first (Law of Blindness).
4. **Two independent human raters** label the same packets.
5. If they disagree, **adjudication** resolves disagreement into effective ground truth.
6. **Agreement metrics** compare the machine judge to human civic judgment (human–human and gate–human).

### Primary files and artifacts

| Role | Location |
|------|----------|
| Export and packet build | build_verification_calibration.py (469, 501) |
| Calibration report and index | verification_calibration_report.json, INDEX.md (project_understanding artifacts) |
| Procedure and rationale | SECTION_8_VERIFICATION_GATE_CALIBRATION.md |

### Why this loop is higher than the runtime

The runtime can be **internally coherent** and still not yet **deserve trust**. The legitimacy loop is the mechanism by which the republic tests whether its Supreme Inspectorate should remain authoritative. Until human jurors have opened the six sealed dockets, the loop is **prepared** but not **completed**. That is why Book III is written in the future tense: the court is built, the republic waits for speech.

---

## 6. How Everything Works Together in One Sentence

Concentric works by taking a human mission, staffing the right institutions, building a world model, turning that model into lawful executable action, surviving failure, judging the result, preserving the truth of that result, learning from it, and eventually subjecting even its own judge to outside review.

---

## 7. The Three Binding Principles

What holds the whole system together can be stated in three principles:

1. **Coherence** — Planners, handlers, records, and evaluators must speak about the same state (truthful lawbook, unified registry, auditor alignment).
2. **Recoverability** — The city assumes failure and designs around it (recovery, healing, outer loop, reflection).
3. **Legitimacy** — Success must mean more than “the system says it succeeded” (verification gate, calibration court, human review).

That is the master diagram: system overview, ministry chain, law-to-ministry matrix, feedback-loop map, and legitimacy-loop map, in one chapter.
