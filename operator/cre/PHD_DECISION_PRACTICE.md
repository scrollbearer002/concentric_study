# PhD Decision Practice: Facts Before Each Decision

**Purpose:** Codify an evidence-first decision habit so that non-trivial choices are grounded in observable facts and explicit context before a decision is stated or implemented. This reduces blind acceptance, blind reversal, and decision amnesia.

---

## 1. Research Basis

### Evidence-based decision making (cognitive science)

- **Epistemic then instrumental:** A rational decision first requires an accurate appraisal of reality ("what is true"), then choice of the option that best fits goals ("what to do"). *Stanovich (2016); Evans & Stanovich (2013); cognitive research on dual-process reasoning.*
- **Engagement before deciding:** Curiosity, cognitive flexibility, and open-mindedness predict better engagement with information and discernment of evidence quality when making decisions. *Eisenberg et al. (2019); evidence-based scientific thinking in everyday life — Cognitive Research: Principles and Implications (2024).*
- **Actively open-minded thinking:** Seek and fairly consider evidence that might contradict prior beliefs; this improves evidence evaluation and reduces susceptibility to misinformation. *Stenhouse et al. (2018); Pennycook & Rand (2019); Svedholm-Häkkinen & Lindeman (2018).*
- **Context in value-neutral language:** Describe forces and facts without advocacy so the decision is a response to context, not to persuasion. *ADR practice: Cognitect (2011), Nygard format.*

### Architecture Decision Records (ADR)

- **Context → Decision → Consequences:** Document the situation and forces first, then the decision, then all consequences (positive and negative). *Michael Nygard, "Documenting Architecture Decisions" (Cognitect, 2011); adr.github.io.*
- **Status:** Use "proposed" until there is agreement, then "accepted"; if superseded, mark and reference the replacement. This keeps decisions reviewable before implementation.
- **One to two pages:** Keep each record short so it is read and maintained. *Cognitect (2011).*

---

## 2. The Practice (Facts Before Each Decision)

For any **non-trivial** decision (design, placement, refactor, policy, or doc change):

1. **Facts / Context first**  
   - List observable facts, constraints, and forces (technical, project, social).  
   - Use value-neutral language; no advocacy in this section.  
   - Cite evidence where it exists (file:line, doc section, run outcome, paper).

2. **Decision second**  
   - State the chosen response in active voice ("We will …").  
   - Optionally mark **Status:** proposed | accepted | superseded.

3. **Consequences third**  
   - List resulting effects: positive, negative, and neutral.  
   - Acknowledge what becomes harder or riskier as well as what improves.

4. **Implementation / checklist (optional)**  
   - If the decision implies concrete tasks, add a short checklist and cross-references.

**Do not** state the decision or implement it before the context and evidence are written down. If context is missing, gather or document it first.

---

## 3. Lightweight Template

Use this for a single decision (e.g. in a design doc, ADR, or section of PLACEMENT_RESEARCH-style doc):

```markdown
## [Short title]

### Context (facts and forces)
- [Observable fact or constraint 1]
- [Observable fact or constraint 2]
- [Evidence: file/section/line or citation]

### Decision
We will [active-voice response to the context].

**Status:** proposed | accepted

### Consequences
- Positive: …
- Negative / trade-offs: …
- Neutral: …
```

For **placement or "where does X go"** decisions, the existing pattern in this repo is:

1. **Evidence table:** Document | Role | Evidence (location, content).  
2. **Primary placement:** Where it fits best, with exact location and evidence.  
3. **Why not elsewhere:** Short justification for each alternative.  
4. **Summary table + implementation checklist.**

See **operator/cre/PLACEMENT_RESEARCH.md** for a full example.

---

## 4. Companion: Research-First Implementation Protocol

The PhD decision practice governs **design decisions** (what and why).
For **implementation tasks** (how), see Rule 13 in `.cursor/rules/concentric-study.mdc`:

> Triage → Analyze → Strategize → Execute → Reflect

This five-step protocol is grounded in:
- **Dynamic Cognitive Orchestration** (OpenReview:1GoQe3r0Lv) — separating metacognitive planning from execution yields 89.2% on MATH, 89.5% on BIG-Bench Hard.
- **ICoT / RoutingGen** (arXiv:2512.14048, AAAI-2026) — difficulty-aware routing prevents overthinking on simple tasks while enforcing full analysis on complex ones. 46.37% token savings.
- **CodePlan** (arXiv:2409.12452) — pseudocode planning before code generation yields 25.1% improvement across 13 multi-step reasoning benchmarks.
- **CRISP** (arXiv:2507.08037) — explicit high-level plans enable smaller models to outperform larger models using few-shot prompting. Validates the project's goal of lower-tier model execution.

Together, Rules 12 and 13 form a complete PhD workflow: evidence-first decisions (Rule 12) + research-first implementation (Rule 13).

---

## 5. References (short)

| Source | What it supports |
|--------|-------------------|
| Stanovich (2016), Evans & Stanovich (2013) | Epistemic vs instrumental rationality; accurate appraisal before choosing. |
| Cognitive Research: Principles and Implications (2024), "Evidence-based scientific thinking and decision-making in everyday life" | Curiosity, flexibility, open-mindedness → better evidence engagement and discernment. |
| Stenhouse et al. (2018), Pennycook & Rand (2019) | Actively open-minded thinking and evidence evaluation. |
| Michael Nygard / Cognitect (2011), "Documenting Architecture Decisions" | Context (value-neutral) → Decision → Status → Consequences; lightweight ADRs. |
| adr.github.io, arc42 §9 | ADR formats and architecture decision documentation. |
| Dynamic Cognitive Orchestration (OpenReview:1GoQe3r0Lv, 2025) | Two-stage metacognitive planning → execution separation; SOTA on MATH, BIG-Bench Hard. |
| ICoT / RoutingGen (arXiv:2512.14048, AAAI-2026) | Difficulty-aware routing; intention abstraction before code generation. |
| CodePlan (arXiv:2409.12452, 2024) | Pseudocode-form planning yields 25.1% improvement on multi-step reasoning. |
| CRISP (arXiv:2507.08037, 2025) | Explicit high-level plans enable smaller models to outperform larger few-shot models. |
| Instruct-of-Reflection / IoRT (arXiv:2503.00902, 2025) | Dynamic meta-instructions for iterative reflection; 10.1% avg improvement. |
| PLACEMENT_RESEARCH.md (this repo) | Example: evidence table, placement with evidence, "why not elsewhere," checklist. |
