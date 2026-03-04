# Evidence-Driven Execution: PhD-Level Interpretation, Spec, and Plan

## Part 1 — What You Are Saying (PhD-Level Interpretation)

You are making four intertwined claims:

**1. Full-screen Safari is an observability choice.**  
We made Safari full screen not only to avoid other windows obscuring the canvas but to **fix the coordinate system**. When the window is full screen, the screenshot we take has known dimensions. The **geometric center** of that image, (width/2, height/2), is then a **deterministic “true middle”**—no VLM guess. So full-screen is the precondition for *knowing* where the middle is with high confidence (e.g. ~95%+). We should treat it that way: use screenshot center as the canonical center for drawing, not a model’s interpretation.

**2. We are sprinting instead of walking.**  
Right now the test runs a sequence of actions and only checks a few high-level outcomes (e.g. “canvas empty?”, “four triangles?”). We are **not** using the screenshots we take to **gate** each step. So we’re “sprinting toward the finish line”: we assume each action worked and move on. You want a **slower, evidence-gated pace**: at each step we **verify** that the world looks right before we proceed. That is “walking or jogging”—deliberate, observable progress, not rushing.

**3. We are skipping steps in the sense of skipping verification.**  
“Skipping steps” here means: we execute an action and then **immediately** go to the next one without confirming the **observable outcome** of the current one. So we’re not skipping actions in the plan; we’re skipping **the verification of each action’s effect**. You want **no step to be considered done** until the evidence (the screenshot) shows that the expected state has been achieved. In other words: **evidence gates progression**. We only leave step N when the screenshot (and any simple checks we can do on it) says we’re in the right state for step N+1.

**4. The evidence blocks (screenshots) should drive the test, not just document it.**  
The screenshots we take should not only be “evidence logs” for a report at the end. They should be **the primary mechanism** for checking that we’re moving in the right direction **at every step**. So: use each screenshot to (a) **verify** that the current step achieved its goal, and (b) where possible, **adapt** (e.g. “triangle is off-center → apply offset next time”). Evidence is not just for proof after the fact; it’s the **feedback loop** that keeps the test on track.

In one sentence: you want **evidence-driven, state-verified execution**—full-screen for a known “true middle,” and at every step use screenshots to verify and, when possible, correct before moving on, so we’re never sprinting past unverified steps.

---

## Part 2 — Enhanced Specification: What the Project Should Do (Exhaustive Detail)

### 2.1 Coordinate system and “true middle”

- **Precondition:** Safari is full screen so the screenshot is the full viewport with stable dimensions.
- **Definition of center:** The drawing center used for “middle of the screen” is **always** the geometric center of the screenshot:  
  `center_x = screenshot_width / 2`, `center_y = screenshot_height / 2`.  
  No VLM is required for this. Optionally, a VLM can later be used to refine “center of the *canvas*” if the canvas is not full-frame, but the **default and primary** reference is screenshot center.
- **Use:** All drawing coordinates (e.g. triangle vertices) are computed **relative to this center**. No separate “canvas center” from the VLM unless we explicitly add a refinement step that compares VLM center to screenshot center and we document why we’re overriding.

### 2.2 Per-step verification (evidence gates)

- **After every action** (or after every logical group of actions that produce one visible state change), the test must:
  1. **Capture** a screenshot (the “evidence block” for this step).
  2. **Verify** that the observable state matches what we expect after this step. Verification can be:
     - **Deterministic:** e.g. “screenshot center pixel is roughly the center of the largest drawn shape” (if we add simple image logic), or “dialog is not present” (e.g. no clear-canvas modal).
     - **VLM-based:** e.g. “Is the Excalidraw canvas empty?” or “Is the black swatch selected?” or “Are there four nested black triangles in the center?”
  3. **Decide:**  
     - If the check **passes:** log the step as verified, store the screenshot, and **only then** proceed to the next step.  
     - If the check **fails:** do **not** proceed as if the step succeeded. Log a failure, optionally retry or correct (see 2.3), and only move on when the evidence shows success or we explicitly abort/skip with a reason.
- **No “sprinting”:** The test must not assume success. It must **wait for evidence** that the state is correct before transitioning. So the pace is “walk or jog”: each step is small and verified.

### 2.3 Use of evidence to adapt (closed-loop correction)

- Where it is feasible, use the **same screenshots** not only to verify but to **correct**:
  - **Position:** After drawing (e.g. first triangle), we can ask the VLM or use heuristics: “Where is the center of the drawn shape?” or “Is the shape centered?” If it’s off, compute an offset (e.g. delta from desired center to observed center) and **use that offset** for the next drawing action (or for the next run). So we close the loop: observe → compare to desired → adapt.
  - **Color/tool:** If “set stroke black” is verified by “Is black selected?” and it fails, we could retry the click (e.g. different target) or try an alternative action.
- The **minimum** is: verify every step. The **enhancement** is: when verification fails or is “almost right,” use the evidence to adapt (offset, retry, or documented fallback).

### 2.4 Evidence blocks as the source of truth

- Every screenshot is an **evidence block**: it is stored, labeled with step number and expected state, and linked to the verification result (pass/fail and, if applicable, correction applied).
- The **report** (e.g. HTML) should show not only “we did step N” but “after step N, we verified: [expected state], result: [pass/fail], screenshot: [image].” So the report is an **audit trail** of verified states, not just a list of actions.
- No step is marked **PASS** in the log or report unless the **verification for that step** (using the evidence block) has passed. So “PASS” means “evidence shows we achieved the expected state,” not “we executed the action.”

### 2.5 Pace and clarity

- **Pace:** The test is designed for **correctness and observability first**, not raw speed. Delays between actions, and between action and screenshot, are acceptable so that (a) the UI has time to update and (b) we have a clear, stable screenshot for verification.
- **Clarity:** Each step has a **single, clear expected state** (e.g. “canvas empty,” “pen selected,” “one triangle visible and centered”). The verification question and the evidence block are aligned to that state. No step tries to verify three things at once unless we explicitly define a composite “state” and document it.

---

## Part 3 — Plan: How to Get This Done (Patience and Clarity, Most Productive)

### Phase 1 — True middle from screenshot (no VLM for center)

- **Goal:** Stop using VLM-reported “canvas center” as the primary drawing center. Use the geometric center of the screenshot instead.
- **Tasks:**  
  1. After capturing the full-screen screenshot, get its dimensions (e.g. from the image file or from the capture API).  
  2. Set `center_x = width / 2`, `center_y = height / 2` and use this for all drawing math.  
  3. Remove or clearly demote reliance on `analyze_ui` for canvas center in the CONCENTRIC_TRIANGLES_CLEAN (and similar) flows.  
  4. Document in the code and in this spec that “true middle” is screenshot center when Safari is full screen.

**Exit criterion:** Drawing uses (width/2, height/2) as center; behavior is reproducible and documented.

---

### Phase 2 — Evidence gate at every step

- **Goal:** No step is considered complete until we have taken a screenshot and verified the expected state for that step.
- **Tasks:**  
  1. For each action in the CONCENTRIC_TRIANGLES_CLEAN plan, define **one** expected state (e.g. “canvas empty,” “pen selected,” “stroke black selected,” “one triangle visible,” “four triangles visible and centered”).  
  2. After each action (or logical group): (a) take a screenshot, (b) run the verification for that step (deterministic or VLM), (c) if pass → store evidence block, log PASS, proceed; if fail → log FAIL, do not mark step as PASS, optionally retry or abort with a clear reason.  
  3. Ensure the test **does not** proceed to the next step until the current step’s verification passes (or we explicitly implement a “skip with reason” path).  
  4. Update the pass log and report so that “PASS” is only written when the verification for that step has passed.

**Exit criterion:** Every step has a verification and an evidence block; progression is gated by verification; report reflects verified states.

---

### Phase 3 — Use evidence to adapt (closed-loop correction)

- **Goal:** When verification shows “almost right” or “wrong in a fixable way,” use the evidence to correct (e.g. position offset).
- **Tasks:**  
  1. After the first drawing step (e.g. first triangle), add a verification: “Is there one triangle visible and roughly centered?” If we have a VLM or heuristic that can return “center of shape” or “offset from image center,” compute an offset.  
  2. Apply that offset to the center used for **subsequent** drawing (or store it for the next run).  
  3. Optionally: after “set stroke black,” if verification fails, retry with a different target (e.g. different SoM box) or a fallback.  
  4. Document which steps have corrective feedback and how (offset, retry, etc.).

**Exit criterion:** At least one closed-loop correction is implemented (e.g. center offset from first shape); behavior is documented and visible in the report.

---

### Phase 4 — Evidence-block audit trail and report

- **Goal:** The report is an exhaustive, step-by-step audit trail: for each step, we see the expected state, the verification result, and the screenshot that was used to decide.
- **Tasks:**  
  1. Store for each step: step index, action name, expected state, verification question (if VLM), result (pass/fail), screenshot path, and any correction applied.  
  2. Generate the HTML (or other) report from this structure: for each step, show expected state, result, and the evidence block (screenshot).  
  3. Ensure no step is marked PASS in the report without a passing verification for that step.

**Exit criterion:** Opening the report shows a clear, step-by-step verified story with evidence blocks; “PASS” is only shown where verification passed.

---

### Order and dependencies

- **Phase 1** can be done first and is independent.  
- **Phase 2** depends on having a clear list of steps and expected states; it can start once Phase 1 is done (or in parallel if center is already computed from screenshot elsewhere).  
- **Phase 3** builds on Phase 2 (we need verification in place to know when to correct).  
- **Phase 4** is a refinement of how we store and display what Phase 2 and 3 already produce; it can be done in tandem with Phase 2 and 3.

**Principle throughout:** Patience and clarity. One phase at a time, with a clear exit criterion, so we’re always “walking or jogging” toward a test that uses evidence at every step and, where possible, adapts from that evidence instead of sprinting toward the finish line.
