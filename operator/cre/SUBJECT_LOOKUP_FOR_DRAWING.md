# Looking up in detail what to draw — PhD-style subject research

**Purpose:** When you ask to draw something (e.g. "a realistic 1991 BMW M3 E30"), the system can look up **in detail** what that subject looks like so the planner generates accurate shapes, proportions, and placement instead of guessing.

---

## 1. Why it matters

Without subject lookup, the planner only sees:
- The goal string: "Draw a realistic 1991 BMW M3 E30"
- The SoM screenshot (current UI)
- Site knowledge (tools, rules)

It has **no** explicit reference for:
- Proportions (wheelbase, hood length, roofline angle)
- Silhouette (side view: hood, windshield, roof, trunk, sill, wheel arches)
- Distinctive features (E30 M3: box flares, rear spoiler, grille, window shape)

So the VLM may produce generic "car" geometry. With a **subject brief** (key visual details from web search or reference images), the planner can generate draw_path steps that match the real subject.

---

## 2. Two mechanisms

### A. Lightweight subject brief (wired in agent.py)

**When:** For any drawing task, before VLM plan generation.

**How:**
1. If the goal looks like a drawing goal (e.g. "draw" in goal, or `needs_drawing` from task classification), call **subject lookup** once.
2. **Subject lookup** = one Gemini 2.5 Pro call **with Google Search grounding**. Prompt: ask for a concise visual description of the subject suitable for a realistic drawing — key proportions, silhouette (e.g. side view), distinctive features, and any ratios or landmarks.
3. The response is a short paragraph (3–6 sentences).
4. Inject that into the planner prompt as: **"Reference for what to draw:\n{paragraph}\n"**
5. The VLM that generates the action plan now sees both the SoM screenshot and this reference, so it can plan draw_path vertices and tool steps that match the subject.

**Pros:** Single API call, no screenshots of reference images, works with existing Gemini client.  
**Cons:** Text-only (no reference image in the planner context).

**Code:** `_get_subject_brief(agent, goal)` in agent.py; result passed into `_generate_plan_vlm(..., subject_brief=...)`.

---

### B. Full ResearchAgent pipeline (optional, pre-execution)

**When:** Optional pre-step before running the main agent (e.g. from OuterLoop or a separate "research then run" script).

**How:**
1. **ResearchAgent.research(task, site_url, search_fn, screenshot_fn, vlm_fn, site_knowledge)** runs:
   - **Phase 1 — Study subject:** Extract visual subjects from task (e.g. "car", "1991 BMW M3 E30"); search for reference images; capture screenshots of those images → `reference_images/` in run dir.
   - **Phase 2 — Study method:** Search "how to draw {subject} step by step"; optionally VLM to get JSON steps/pitfalls → `method_brief`.
   - **Phase 3 — Study tools:** Use SiteKnowledge + optional screenshot to get tool inventory.
   - **Phase 4 — Solve equation:** Map method steps to tools → `execution_plan` + `quality_criteria`.
2. **ResearchBrief** is saved (`research_brief.json`); it contains `reference_images` (paths), `method_brief`, `tool_inventory`, `execution_plan`, `quality_criteria`.
3. The executor (or agent) can then:
   - Load the brief; use **reference image paths** as visual context (e.g. show reference + canvas to VLM), or
   - Use **method_brief** and **execution_plan** to drive steps instead of/in addition to dynamic VLM planning.

**Pros:** Reference images on disk; full method research; execution plan.  
**Cons:** Requires `search_fn` and `screenshot_fn` (web search + ability to capture URLs); integrated into the universal-agent path but not yet a universal guarantee across every entrypoint or drawing harness.

**Code:** `agent_infra/research_agent.py` — `ResearchAgent`, `ResearchBrief`; see RESEARCH_AGENT_DESIGN.md.

---

## 3. Magma-specific: Reference panel

Magma has a **Reference/View** panel (right toolbar, book/stacked-papers icon). You can:

- **Load a reference image** (e.g. a BMW E30 side profile) into that panel.
- The canvas screenshot then shows **both** the canvas and the reference.
- The planner VLM sees the reference next to the canvas and can plan strokes that match the reference.

To use this with subject lookup:

1. **Lightweight path:** Run subject brief (text) as above; optionally add a plan step: "Open Reference panel, load image from [URL or path]." That requires the agent to have a way to load an image (e.g. URL from search, or a path from ResearchAgent’s `reference_images/`).
2. **ResearchAgent path:** After Phase 1, reference images are in `runs/<id>/reference_images/`. A separate step could "import reference into Magma" if Magma supports file/open; or the planner could be given the reference image path and the SoM could include a screenshot where the reference is already visible (e.g. user loaded it once).

---

## 4. Summary

| Question | Answer |
|----------|--------|
| How do you look up in detail what I ask you to draw? | **(1) Lightweight:** One Gemini + Google Search call → short "subject brief" (proportions, silhouette, features) → injected into planner prompt. **(2) Full:** ResearchAgent studies subject (reference images), method (tutorials), tools → ResearchBrief with reference_images + method_brief + execution_plan. |
| Is it wired? | Lightweight subject brief: yes, in `agent.py` for drawing tasks. ResearchAgent: integrated in the universal-agent path; not a universal guarantee across every entrypoint/test harness. |
| For PhD realism? | Subject brief improves plan quality by grounding the VLM in real visual facts. Combine with Magma tool workflow (Brush, Color, Brush Settings, Zoom) and, if available, reference image in Magma’s Reference panel. |

This file is the single place that describes how we look up, in detail, what you ask to draw.
