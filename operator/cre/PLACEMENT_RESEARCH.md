# PhD Placement Research: Trust+Routing Bridge & Related Work+Architecture

**Purpose:** Evidence-based recommendation for where to place (1) the **Trust + Routing Bridge** (code-level link between `action_trust.py` and `inference_router.py`) and (2) the **Related Work + Architecture** subsection (implemented vs. proposed, validation tiers), so they fit existing doc structure and support grading/submission.

---

## 1. Existing Documentation Map (Evidence)

| Document | Role | Evidence (location, content) |
|----------|------|------------------------------|
| **POTENTIAL_CHANGES.md** | Design rationale, tool-pairing audit, PhD citations | Pairing 4 (Beta-Binomial) L798–815; Pairing 10 (FrugalGPT) L938–955; runtime critical path L700 ("scipy (trust decision) → json"); module table L660 (action_trust, inference_router); Summary table L957–972. Already argues "We already have InferenceRouter … ActionTrustTracker" (L461). |
| **ACADEMIC_VALIDATION.md** | Evidence-based validation of specific CRE kernel decisions | Sections 1–3: Vision pipeline, Bezier, Zero-API. Pattern: *Problem → Academic Validation → Solution* with code/citations. No trust or routing section yet. |
| **DUAL_AGENT_LOOP_PLAN.md** | Architecture entry point, build plan, research foundation | 8-paper table L6–19; "What Exists Today" L52–60; loop diagram L22–48. Does not list action_trust or inference_router in diagram; no "Related Work" or "validation tiers" section. |
| **AGENTS.md** | Operator-facing: how to run, import, use | Infrastructure table lists action_trust, inference_router; no design or citation detail. |
| **evidence_concentric_clean/report.html** | Run evidence (steps + screenshots) | Step-wise PASS/fail only; not a home for theory or related work. |
| **PHD_REMEDIATION_PLAN.md** | Test oracle / remediation | Focused on oracle and clear-canvas; references Weyuker, Barr. Not the home for trust/routing or broad related work. |
| **COMPLEXITY_ANALYSIS_REPORT.md** | Radon complexity only | No related work or validation content. |

**Conclusion:** Trust+routing belongs in **POTENTIAL_CHANGES** (full bridge) and **ACADEMIC_VALIDATION** (short, citation-ready). Related Work + Architecture belongs in **DUAL_AGENT_LOOP_PLAN** (architecture entry point); **AGENTS.md** should only point to it.

---

## 2. Deliverable 1: Trust + Routing Bridge

### 2.1 Where it fits best (with evidence)

**Primary: POTENTIAL_CHANGES.md**

- **Exact placement:** Insert a new subsection **after** the Pairing 10 references block (after L955, before the "Summary: Evidence Strength by Tool Combination" table at L957).
- **Suggested title:** `### Verification and Efficiency Bridge: Trust and Routing in the Hot Path`
- **Evidence:**
  - L700: Runtime critical path explicitly lists "scipy (trust decision) → json (trace write)" and notes "inference_router" as next-generation. A bridge section completes the narrative: how trust (skip verification) and routing (which model) interact in one run.
  - L660: Both `action_trust.py` and (implicitly) inference_router appear in the module table; no other doc ties them in a single execution flow.
  - L943: "Our InferenceRouter already implements this for VLM calls (Flash → Pro → Local)." Pairing 10 is the right neighbor for a section that explains how routing and trust together reduce cost and verification load.
- **Content to add:** (1) Single execution flow: per action type, `should_verify(trust_key)` → if skip, no VLM assert; else assert → then `record_outcome` for router. (2) Code refs: `action_trust.py` (Beta posterior, `should_verify`, `record_success`/`record_failure`), `inference_router.py` (`route`, `record_outcome`, EMA updates, persistence). (3) Short pseudocode or flow diagram. (4) One sentence on how this bridges "verification reliability" (BetaConform-style) and "inference cost" (FrugalGPT-style).

**Secondary: ACADEMIC_VALIDATION.md**

- **Exact placement:** Add **Section 4** after Section 3 (Zero-API Navigation).
- **Suggested title:** `## 4. Verification Efficiency: Beta-Binomial Trust and Model-Tier Routing`
- **Evidence:** ACADEMIC_VALIDATION validates one kernel decision per section (vision, Bezier, navigation). Trust and routing are kernel-level decisions affecting every run; they are the next most cited in the audit (BetaConform, FrugalGPT). Keeping the same pattern (Problem → Academic Validation → Solution) preserves consistency and gives a short, citation-ready version.
- **Content to add:** (1) Problem: verification cost vs. reliability; need to skip asserts when statistically safe and to route cheap models when sufficient. (2) Academic validation: BetaConform (NeurIPS 2025), FrugalGPT (arXiv:2305.05176); one sentence each. (3) Solution: `action_trust.py` (Beta(1+s,1+f), lower bound vs. threshold); `inference_router.py` (task-type routing, EMAs, persist); 2–3 file:line references; one compact pseudocode block. (4) One line: "Full bridge and hot-path flow: POTENTIAL_CHANGES.md § Verification and Efficiency Bridge."

### 2.2 Why not elsewhere

- **DUAL_AGENT_LOOP_PLAN:** Focus is Monitor→Diagnose→Adapt→Test and outer loop; trust and routing are inner-loop. A pointer from DUAL_AGENT_LOOP to POTENTIAL_CHANGES § Bridge is enough.
- **AGENTS.md:** Ops-only; no space for pseudocode or citations. A single cross-reference is sufficient.
- **New standalone file:** Would duplicate material already in POTENTIAL_CHANGES (Pairings 4 and 10) and fragment the "evidence" narrative; one bridge section in POTENTIAL_CHANGES plus one section in ACADEMIC_VALIDATION keeps one long and one short version without a third location.

---

## 3. Deliverable 2: Related Work + Architecture Subsection

### 3.1 Where it fits best (with evidence)

**Primary: DUAL_AGENT_LOOP_PLAN.md**

- **Exact placement:** Insert a new section **after** "Research Foundation" (after the 8-paper table, L19) and **before** "Architecture Overview" (L22). So: Research Foundation → **Related Work and Validation Tiers** → Architecture Overview.
- **Suggested title:** `## Related Work and Validation Tiers`
- **Evidence:**
  - DUAL_AGENT_LOOP_PLAN is the architecture entry point: it opens with a research-foundation table and the loop diagram. Related Work belongs near the front for thesis/paper readers.
  - "What Exists Today" (L52–60) already distinguishes built vs. not; a subsection that states "implemented" vs. "proposed" and aligns with the audit’s validation tiers (Direct / Analogous / Novel) extends that distinction with evidence levels.
  - No other doc has both "architecture overview" and "research foundation" in one place; adding Related Work here gives a single place for "what we build, what exists, and how it’s validated."
- **Content to add:**  
  (1) **Implemented:** Bi-channel (a11y + SoM) fusion, trace-driven outer loop, Beta–Binomial verification gating, model-tier inference routing (Flash/Pro/Local), Pydantic/Gemini structured outputs, skill library with maturity and staleness.  
  (2) **Proposed:** Tri-channel (DOM + a11y + visual) fusion, modality-driven FrugalGPT perception cascade, asynchronous closed-loop observer (Quartz + Hammerspoon).  
  (3) **Validation tiers (compact table):** One row per pairing from the audit summary (e.g. SoM+VLM=Direct, pHash cache=Analogous, tri-channel=Novel), with one sentence per row.  
  (4) **Pointer:** "For pairing-level citations and tool-by-tool evidence, see POTENTIAL_CHANGES.md § PhD Evidence: Which Tool Combinations Have Proven Success Together."

**Secondary: AGENTS.md**

- **Exact placement:** At the end of the "Infrastructure" section (after the import line), or as a new short subsection before "Running Tests."
- **Content:** One line: `For related work and validation tiers (implemented vs. proposed, Direct/Analogous/Novel), see DUAL_AGENT_LOOP_PLAN.md § Related Work and Validation Tiers.`
- **Evidence:** AGENTS.md is the first doc many readers see; a single pointer keeps it operational and directs grading/review to the right place without duplicating content.

### 3.2 Why not elsewhere

- **POTENTIAL_CHANGES.md:** Already has the long "PhD Evidence" section and the Summary table (L957–972). Adding a full Related Work subsection here would duplicate the 8-paper table in DUAL_AGENT_LOOP_PLAN and blur the distinction between "tool-pairing evidence" and "architecture overview." DUAL_AGENT_LOOP_PLAN is the right home for the compact "implemented vs. proposed + validation tiers" summary; POTENTIAL_CHANGES remains the detailed evidence source.
- **ACADEMIC_VALIDATION.md:** Focuses on validating specific technical decisions (vision, Bezier, navigation, and now trust+routing). It is not the place for a broad Related Work + Architecture subsection that lists all pairings and tiers.
- **evidence_concentric_clean/report.html:** Run evidence only; no place for related work or architecture narrative.
- **New standalone (e.g. RELATED_WORK.md):** Would split "architecture + research foundation" across two files (DUAL_AGENT_LOOP_PLAN and RELATED_WORK). Keeping Related Work inside DUAL_AGENT_LOOP_PLAN preserves one entry point for architecture and validation.

---

## 4. Summary Table: Placement and Evidence

| Deliverable | Primary location | Exact placement | Secondary | Evidence in repo |
|-------------|------------------|------------------|-----------|-------------------|
| **Trust + Routing Bridge** | POTENTIAL_CHANGES.md | After Pairing 10 refs (before L957 Summary table) | ACADEMIC_VALIDATION.md §4 | L660, L700, L943, L798–815, L938–955 |
| **Related Work + Architecture** | DUAL_AGENT_LOOP_PLAN.md | After Research Foundation table (before L22 Architecture Overview) | AGENTS.md (one-line pointer) | L6–19 (8-paper table), L52–60 (What Exists Today), POTENTIAL_CHANGES L957–972 (Summary table) |

---

## 5. Implementation Checklist

- [ ] **POTENTIAL_CHANGES.md:** Insert `### Verification and Efficiency Bridge: Trust and Routing in the Hot Path` after L955; add execution flow, code refs, pseudocode, and one-sentence link to BetaConform/FrugalGPT.
- [ ] **ACADEMIC_VALIDATION.md:** Add `## 4. Verification Efficiency: Beta-Binomial Trust and Model-Tier Routing` with Problem → Academic Validation → Solution and pointer to POTENTIAL_CHANGES § Bridge.
- [ ] **DUAL_AGENT_LOOP_PLAN.md:** Insert `## Related Work and Validation Tiers` after L19; add implemented vs. proposed lists, compact validation table, and pointer to POTENTIAL_CHANGES § PhD Evidence.
- [ ] **AGENTS.md:** Add one-line pointer to DUAL_AGENT_LOOP_PLAN § Related Work and Validation Tiers under Infrastructure or before Running Tests.

This placement keeps a single long version of the trust+routing bridge in POTENTIAL_CHANGES, a short citation-ready version in ACADEMIC_VALIDATION, and a single architecture-facing Related Work + validation summary in DUAL_AGENT_LOOP_PLAN, with evidence traceable to existing sections and line numbers.

---

## Post-Validation Addendum (February 2026)

**Validation summary:** The placement strategy was reviewed and affirmed as robust, evidence-based, and aligned with best practices for AI agent documentation. It preserves modularity, minimizes duplication, and supports traceability for grading and peer review.

**Traceability for reproducibility (grading):** The doc hierarchy supports a clear path from operations to architecture to evidence:

- **AGENTS.md** (ops) → how to run, import, use; one-line pointer to Related Work.
- **DUAL_AGENT_LOOP_PLAN.md** (architecture) → Research Foundation, Related Work and Validation Tiers, loop diagram, What Exists Today.
- **POTENTIAL_CHANGES.md** (evidence) → tool pairings, Verification and Efficiency Bridge, Summary table, implementation priority.

Reviewers can follow: run instructions (AGENTS) → high-level architecture and validation tiers (DUAL_AGENT_LOOP_PLAN) → detailed evidence and code-level bridge (POTENTIAL_CHANGES, ACADEMIC_VALIDATION).

**Scalability caveat:** If the project grows, manual cross-references may become brittle. Consider a unified documentation framework (e.g. Sphinx, Docusaurus) for automated cross-linking and versioned builds. For current scope, manual pointers are sufficient.

**Suggestions captured:**

1. **Unified PDF export:** For submission, generate a single PDF from the key docs (e.g. `pandoc` or `mdbook build`). Not automated in-repo; run locally as needed.
2. **Diagrams:** Add a flow diagram (e.g. UML or Mermaid) in POTENTIAL_CHANGES § Verification and Efficiency Bridge to visualize trust gate → route → VLM → record_outcome. Optional follow-up.
3. **Evolving info:** If new modules (e.g. POMDP integrations) or governance standards (e.g. ISO/IEC 42001) appear, re-evaluate placements and pointers to avoid staleness.
4. **Further reading:** Clements et al. (2010), *Documenting Software Architectures: Views and Beyond* (SEI); NIST AI RMF (2023) for governance and risk in agent documentation.

**Optional follow-up status:**

- [x] **Diagrams:** Flow diagram added. Mermaid flowchart in **POTENTIAL_CHANGES.md** § Verification and Efficiency Bridge (trust gate → route → VLM → record_outcome). Implemented Feb 2026.
- [x] **Unified PDF export:** Documented below (§ Submission PDF). Run locally as needed; not automated in-repo.

**Decision: Best next step (evidence-first)**

| Aspect | Evidence |
|--------|----------|
| **Context** | Addendum above lists four suggestions; items 1 (PDF) and 2 (Diagrams) were actionable. Diagram was implemented but not recorded here → traceability gap for grading. PDF was "run locally as needed" with no recipe → submission not reproducible. Same addendum states: "Traceability for reproducibility (grading)" and "Reviewers can follow: run instructions → architecture → evidence." |
| **Decision** | Best next step is to **(1) record both follow-ups as done** (diagram implemented; PDF recipe documented) and **(2) add a minimal, reproducible PDF recipe** in this doc with a one-line pointer from AGENTS.md. Rationale: Recording closes the optional-item loop so reviewers see no pending ambiguity (explicit addendum items 1–2). A single pandoc command makes "run locally as needed" reproducible without adding in-repo automation, supporting submission and grading. Alternatives considered: (A) Only record diagram — leaves PDF suggestion unactionable for submitters. (B) Automate PDF in CI — addendum says "Not automated in-repo"; automation would contradict stated scope. (C) Do nothing — leaves traceability gap and no submission path. |
| **Consequences** | Positive: Optional follow-ups are tracked; graders see completion; submitters have one-command PDF. Negative: None. Recipe may need a one-line edit if key doc list changes. |

**Status:** Accepted.

**Submission PDF (run locally):** From repo root, generate one PDF from key docs for submission/grading:

```bash
pandoc AGENTS.md DUAL_AGENT_LOOP_PLAN.md operator/cre/PLACEMENT_RESEARCH.md operator/cre/ACADEMIC_VALIDATION.md -o submission_bundle.pdf --toc
```

Adjust the list of files as needed; install `pandoc` if missing (`brew install pandoc` on macOS). For a single combined document with TOC only, the above suffices. Alternatively use `mdbook build` if the project later adopts mdbook.

- [x] POTENTIAL_CHANGES.md: Bridge subsection added (after Pairing 10, before Summary table).
- [x] ACADEMIC_VALIDATION.md: Section 4 (Verification Efficiency) added; Executive Summary and Conclusion updated; sections renumbered (5–7).
- [x] DUAL_AGENT_LOOP_PLAN.md: "Related Work and Validation Tiers" section added (after Research Foundation, before Architecture Overview).
- [x] AGENTS.md: One-line pointer to DUAL_AGENT_LOOP_PLAN § Related Work and Validation Tiers added (after Import line, before Running Tests).
