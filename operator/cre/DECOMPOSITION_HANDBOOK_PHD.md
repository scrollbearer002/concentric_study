# The Decomposition Handbook (PhD)

**Repo placement:** `operator/cre/DECOMPOSITION_HANDBOOK_PHD.md`  
**Master prompt stub:** `operator/cre/artifacts/decomposition_handbook_master_prompt.txt`  
**Protocol metadata:** `operator/cre/artifacts/decomposition_handbook_protocol.json`  
**Classification:** isolated experimental method protocol (docs + prompt stub only — not wired into `agent_infra`)  
**Invoke:** `Run the decomposition protocol on {TOPIC}. Depth {N}.`

**Environment basis:** Landed in `concentric_study` for coordinator+worker topic decomposition. Does not modify the OuterLoop / TraceWriter runtime path. Odyssey worked-example numbers below are handbook claims from the executed run; full tree files are not stored in this workspace.

---

### How to take any topic apart with a team of AI agents — from system to screws to elements — without overloading

*Version 1.1 — written after a complete run on a 2015 Honda Odyssey EX-L (base tree → depth-9 recursion → full periodic-table push). Everything below was executed, not theorized. Fact-checked 2026-10-21 against PMI, NASA, INCOSE, and the multi-agent research literature — see §14 for verdicts, including the two places where this method runs ahead of the evidence.*

---

## 0. What this is

A reproducible method for turning any topic into an exhaustively deep, strictly structured tree using a coordinator + worker agent team. The method has four phases:

1. **Base tree** — coordinator + workers build a depth-6 tree of the topic.
2. **Recursive deepening** — each branch gets its own worker, pushing 3+ levels deeper.
3. **Basement push** — every terminal node is resolved to the topic's fundamental layer (for physical objects: the periodic table).
4. **Presentation** — merged master inventory + an interactive artifact.

The Odyssey run produced: ~750 nodes at depth 9, 19 shared structural refs, then 48 of 118 chemical elements mapped across 5 branches — with zero duplicated expansions and no runaway breadth. The machinery that made that possible is the actual subject of this document.

## 1. The idea in 60 seconds

Any complex system can be decomposed into a tree where **every child is a genuine interface boundary** — a place where the material, the engineering discipline, or the failure mode changes. A piston ring is a boundary (steel → coated steel → combustion gas). A "miscellaneous parts" node is not.

Three rules keep the tree from exploding:

- **Budgets.** Depth and breadth are rationed like money. Default: 6 levels deep, 8 children wide. "Deeper" means +2 levels, never unbounded.
- **The funnel rule.** When branches converge (every chip → die → transistor; every motor → copper + steel + magnets), expand once, assign a ref ID, point everyone at it. This is the single most important mechanism in the handbook.
- **The leaf rule.** Stop subdividing when no new interface boundary appears. Depth stops where insight stops, not where the budget runs out.

One coordinator owns the tree, the budgets, and the final merge. Workers own one branch at a time and can never spawn workers — all recursion is gated through the coordinator.

## 2. Core concepts (learn these before anything else)

**Interface boundary.** The test every proposed child node must pass: does it differ from its parent/siblings in material, in the profession that designs it, or in how it fails? A transistor passes (new material stack, new physics, new failure modes). "Left half of the piston" fails. If a node fails this test, it is filler — cut it.

**Node schema.** Every node carries exactly this, no more:
- `name` — what it is
- `scale` — physical size, or scope for non-physical topics
- `function` — one line: what it does
- `children` — its sub-components
- `up` — what it depends on from the level above (context/resources flow down)
- `down` — what it depends on from the level below (function flows up)
- `status` — `branch` | `leaf` | `ref`

**Ref (the funnel).** A node with `status: ref` is expanded exactly once, given an ID (`REF-motor`), and every other branch points at it instead of re-expanding. The coordinator maintains the **dedup registry**: the list of all ref IDs. Before any worker expands any node, it checks the registry. This is what converts exponential blowup into linear work.

**Counted group.** When a node has dozens of near-identical children (500 resistors, 4,500 spot welds, 1,700 socket pins), do not list them. Write `Resistor ×~500 → [one expanded exemplar]` and expand the exemplar once. The count is preserved; the combinatorics die.

**Logical branches.** After the physical tree, identify the cross-cutting distribution trees that run *through* the system — for a motherboard: power, clock, data; for a van: 12V power, CAN data, thermal loops. Name each, trace its path top to bottom in 3–5 lines. This step routinely surfaces the single most interesting insight of the whole exercise (for the van: "no central brain, just a CAN committee").

**Merge pass.** After workers return, the coordinator — and only the coordinator — assembles the final tree, unifies ref IDs across workers (two workers will both invent `REF-bolt`; merge them), verifies every branch terminates in a leaf or ref, and writes the footer: depth reached, node count, refs used, what was grouped or cut. The footer is not decoration; it is the honesty mechanism. Nothing hidden.

**Lineage (fact-checked, see §14).** The exhaustive/no-filler rule is PMI's **100% rule** — children sum to exactly 100% of the parent, no more, no less. It is related to but distinct from Minto's MECE, and note carefully: the funnel rule technically *violates* MECE's strict mutual exclusivity, since a ref'd subtree belongs to several parents. This handbook therefore claims the 100% rule plus explicit ref accounting, not MECE. Interface-boundary decomposition descends from Parnas (1972, decompose around hidden design decisions) and Baldwin & Clark's *Design Rules* (visible design rules vs hidden module parameters). The funnel rule is memoization applied to knowledge work: naively expanding duplicated subtrees is exponential; solving each once and referencing it is not.

---

## 3. Team anatomy

### The coordinator (1)

Owns: the tree, the depth/breadth budgets, the dedup registry, worker assignments, the merge pass, and the final output. The coordinator never expands nodes itself during worker phases — it plans, rations, and merges.

Coordinator's first message in every run states: **topic, depth budget, breadth budget, worker count, branch assignments.** Then it dispatches.

### Workers (3–5)

Each worker owns **one branch at a time**. A worker:
- receives its branch + the node schema + the decomposition rules + the current dedup registry,
- returns a subtree in the output format, plus any new refs it created, plus a footer,
- then goes idle until reassigned.

**Workers never spawn workers.** If a worker wants to go one level deeper than its assignment, it requests it; the coordinator approves only against remaining depth budget. This **recursion gate** is the second most important mechanism in the handbook. Un-gated recursion is how agent teams melt down. *(Honesty flag: the gate is an unvalidated heuristic. No published study isolates it, and multi-agent research shows coordination structure can hurt as well as help depending on task type — see §14. Keep it because runaway recursion is a real observed failure mode, not because the literature blesses it.)*

### Simulation mode (single-agent fallback)

If the executing AI cannot spawn real subagents, it simulates the team: one coordinator planning pass (budgets + branch list), then one worker pass per branch in strict sequence, then a merge pass. All rules apply unchanged. The output is identical in structure; only the wall-clock time differs.

### Sizing the team

- **3 workers:** slower, tighter, easier merge. Best for unfamiliar topics where the coordinator needs control.
- **5 workers:** faster, needs a stricter merge pass. Best for well-understood physical systems with clean branch boundaries.
- More than 5 is almost never worth it — merge-pass cost grows faster than worker parallelism.

---

## 4. The master prompt (copy-paste to start any run)

Copy from `operator/cre/artifacts/decomposition_handbook_master_prompt.txt`, or:

```
You are the COORDINATOR of a decomposition team. Take {TOPIC} and break it
into a complete structured tree, {DEPTH} levels deep, without overloading
the team.

TEAM STRUCTURE
- 1 Coordinator (you). You own the tree, the budgets, and the final merge.
- 3–5 Workers. Each owns ONE branch at a time. Workers never spawn
  workers — all recursion goes through you.
- If you cannot spawn real subagents, simulate the team: one Coordinator
  planning pass, then one Worker pass per branch in sequence, then a merge
  pass. All rules below still apply.

NODE SCHEMA — every node carries:
- name, scale/scope, function (one line: what it does)
- children: its sub-components
- up: what it depends on from the level above (context/resources)
- down: what it depends on from the level below (components/function)
- status: branch | leaf | ref
  (ref = "expanded once elsewhere — see NODE-ID")

DECOMPOSITION RULES
1. Break each node into its REAL parts. Every child must be a genuine
   interface boundary: different materials, different discipline, or
   different failure mode. No filler nodes.
2. Breadth cap: max {BREADTH, default 8} children per node. Beyond that,
   group them and note the grouping. Never list 200 identical children.
3. Depth cap: max {DEPTH, default 6}. "Deeper" = +2 per request. Never
   unbounded.
4. FUNNEL RULE: when branches converge on the same subtree (every chip →
   die → transistor), expand it ONCE, assign a ref ID, and point all other
   branches at it. Check the registry before expanding anything.
5. Leaf rule: stop when subdividing adds no new interface boundary.
   Never pad depth with trivia.
6. Counted groups: near-identical explosions collapse to
   "Resistor ×~500 → [one expanded exemplar]".
7. Logical branches: after the physical tree, add the cross-cutting trees
   running through the system (power, clock, data). Name each, trace it
   top to bottom.

LOAD MANAGEMENT
- One branch per worker at a time; return the subtree before taking another.
- Recursion gate: workers request deeper levels; you approve only against
  remaining depth budget.
- Dedup registry: no subtree expanded twice.
- Merge pass: you assemble the final tree, resolve refs, verify every
  branch terminates in a leaf or ref.

OUTPUT
1. Tree in indented notation (├─ └─ │), scale on major nodes.
2. "Convergence" section: each ref subtree expanded once, in full.
3. "Logical branches" section.
4. Footer: depth reached, total nodes, refs used, what was grouped or cut.

Begin by stating the topic, budgets, and top-level branch assignments.
Then execute.
```

Invoke it as: `Run the decomposition protocol on {TOPIC}. Depth {N}.`

---

## 5. Phase 1 — Base tree (the procedure)

**Goal:** a complete, correct tree at depth ~6 covering the entire topic, with the first set of refs established.

1. **Coordinator plans.** Read the topic. Identify the top-level branches — the largest genuine interface boundaries. For a van: powertrain / chassis / electrical / interior / exterior. For a motherboard: substrate / compute / power / firmware / connectors. Aim for 3–6 branches; each becomes one worker assignment. State depth (default 6), breadth (default 8).
2. **Dispatch workers.** Each worker prompt contains: its branch name, the node schema, the 7 decomposition rules, the (initially empty or seeded) dedup registry, the output format, and the instruction to return new refs + a footer. Workers work in parallel.
3. **Workers return subtrees.** Each returns: tree fragment in `├─ └─ │` notation, new ref definitions, footer (deepest level, node count, refs used, grouped/cut).
4. **Coordinator merges.** Unify ref IDs (see §8), assemble the full tree, add the logical-branches section, write the global footer. Verify: every branch terminates in leaf or ref; no subtree expanded twice; breadth cap respected (counted groups noted).

**What "done" looks like:** the Odyssey base tree was ~120 nodes at depth 6, 3 refs (motor, ecu, sensor), 5 logical-branch trees identified. One screen of coordinator preamble + one tree + convergence + logical branches + footer.

**Choosing branches well matters more than anything else in this phase.** Good branches are *disjoint by discipline*: the powertrain worker and the electrical worker should rarely need the same knowledge. If two workers keep colliding on the same nodes, the branch boundary is wrong — redraw it and reassign. (In the Odyssey run, harnesses belonged to W3 and glass bonding to W5; the coordinator enforced this in the merge rather than letting both expand them.)

---

## 6. Phase 2 — Recursive deepening (the procedure)

**Goal:** take every branch N levels deeper (Odyssey: +3, to depth 9) without the tree exploding.

1. **Coordinator re-dispatches** — one worker per Phase-1 branch, each instructed: "expand *every* node in your branch 3 levels deeper; follow the same rules; here is the current dedup registry — check it before expanding anything; reuse parent refs, don't redefine them."
2. **Workers expand.** The critical worker behaviors at depth:
   - *Exemplar expansion:* for repeated assemblies (6 pistons, 4 brake corners, 2 sliding doors), expand **one exemplar** fully and mark the rest as counted mirrors (`×2 mirrored, not duplicated`).
   - *Cross-branch references:* when a node belongs to another worker's branch (W5's door sub-harnesses belong to W3), **reference it, don't expand it** — note `→ W3 territory`.
   - *New refs:* workers will discover new shared subassemblies at depth (bolts, bearings, bushings, welds, clips, seals). Each gets a ref ID local to the worker; the coordinator unifies them in the merge.
3. **Coordinator merges again.** This merge is heavier than Phase 1's:
   - Unify ref IDs across workers (W1's `REF-bolt` and W2's `REF-bolt` become one global ref).
   - Resolve cross-branch pointers into a consistent scheme.
   - Re-verify termination and the leaf rule at the new depth.
   - Update the footer with new totals.

**What "done" looks like:** Odyssey Phase 2 was ~750 nodes at depth 9, 19 unified refs. The deepest chain: mirrors → LaneWatch camera → lens stack → element → optical surfaces → AR coating → TiO₂/SiO₂ quarter-wave films. Note where it stopped: below thin-film layers is materials science, not van anatomy — the leaf rule held.

**The depth-9 pattern.** Across all five branches, depth 9 consistently meant: system → branch → subsystem → assembly → component → sub-component → piece → material → coating/layer. If your topic's depth-9 doesn't bottom out in something this regular, your branches are uneven — rebalance them.

---

## 7. Phase 3 — The basement push (the procedure)

**Goal:** resolve every terminal node to the topic's fundamental layer.

**First, the coordinator chooses the basement.** The basement is the layer below which subdivision stops being *about the topic*:

| Topic type | Basement | Example terminal chain |
|---|---|---|
| Physical artifact | Periodic table (elements) | AR coating → TiO₂/SiO₂ films → Ti, Si, O |
| Electronic system | Atoms → transistor physics | gate oxide → SiO₂ molecules → Si, O |
| Software | Bytes / instructions / syscalls | TLS handshake → AES rounds → S-box lookups |
| Organization | Individual roles | approvals → signatory → named human |
| Biological | Molecules / cells | hemoglobin → heme + globin → Fe, C, H, O, N |
| Legal/financial | Named instruments/parties | settlement → payor → account |

For physical topics (the fully worked case), the worker procedure is:

1. **Map every material**, stated or clearly implied: component → material → compound → ELEMENTS (name + symbol). Example: *brake pad → semi-metallic composite → steel fiber (Fe) + graphite (C) + barite filler (Ba, S, O) + phenolic binder (C, H, O).*
2. **Tag each element MAJOR or TRACE.** Major = bulk/structural somewhere in the branch (Fe in steel, C in polymers). Trace = additive, coating, dopant, plating, pigment (Ir in spark plugs, Au on connectors). This tag is what makes the final inventory readable — without it, 48 elements is noise.
3. **Expand implied materials** (e.g. "rubber bushing" → natural rubber/SBR → C, H + sulfur crosslinks + ZnO activator + carbon black), but **never invent components** not in the tree.
4. **Mark uncertainty explicitly** with `(uncertain)` or `(inferred)` — e.g. LED semiconductor composition, glass tint formulation. The merge preserves these marks; they are honesty, not weakness.
5. **Return:** subsystem-grouped mappings + a deduplicated element rollup per branch (one line per element: symbol, name, major/trace, 2–4 components it appears in).

**Coordinator merge:** union all branch rollups into the **master inventory** — one row per element: symbol, name, tier, branches present, key uses. Dedupe ruthlessly; keep the uncertainty marks. Write branch summaries (one paragraph each: what the branch *is*, elementally) and merge notes (mass leaders, notable absences, deepest chain).

**What "done" looks like:** Odyssey Phase 3 was 48 of 118 elements. Seven (Fe, Al, Cu, C, H, O, Si) carry ~99% of mass; 41 exist in grams. Notable absences recorded: no lithium-ion (lead-acid → Pb), no rare-earth magnets (ferrite won), no mercury, no cadmium.

---

## 8. Phase 4 — Presentation

The tree is not the deliverable; *understanding* is. Phase 4 turns the merged inventory into something a human can explore:

1. **Master inventory document** — the element table (Phase 3 output), branch summaries, merge notes. This is the reference artifact.
2. **Interactive artifact** — for the Odyssey: a periodic table with the 48 present elements highlighted (major vs trace color-coded), branch filter buttons (W1–W5 isolate each system's elements), and tap-for-detail (branches + uses per element). Build whatever interactive form fits the topic; the requirements are: filterable by branch, tier-labeled (major/trace), and honest about uncertainty.
3. **Narrative** — the one-paragraph truth the whole exercise revealed. Odyssey's: *"~35 electric motors and ~15 computers wearing 350 kg of welded steel, gossiping over CAN, drinking 12V and gasoline — and elementally, 7 elements wearing 41 accessories."* If Phase 4 can't produce this sentence, the decomposition missed something.

**Repo note:** Interactive Odyssey artifacts are not checked into this workspace. Produce them per-run under `operator/cre/runs/<run_id>/` when a decomposition is executed here.

---

## 9. Anti-overload machinery (all of it, in one place)

1. **Depth budget** — hard cap, +2 per "deeper" request, never unbounded.
2. **Breadth budget** — 8 children max per node before grouping.
3. **Recursion gate** — workers can't freelance deeper; coordinator rations depth.
4. **Dedup registry + funnel rule** — expand once, reference everywhere. (Odyssey: kept ~750 nodes from becoming ~2,000.)
5. **Counted groups + exemplar expansion** — `×~500 → [one exemplar]`.
6. **Leaf rule** — stop where interface boundaries stop.
7. **Cross-branch references** — reference, never re-expand, another worker's territory.
8. **One-branch-at-a-time** — a worker returns its subtree before taking another.
9. **Merge pass** — single owner deduplicates, unifies refs, verifies termination.
10. **Footer honesty** — depth, node count, refs, grouped/cut items stated every phase.

Mechanisms 4 and 5 do ~80% of the work. If you only remember two, remember those.

*Honesty note: mechanisms 4–7, 9, and 10 are grounded in established practice (PMI 100% rule, memoization, WBS discipline). The specific numbers in mechanisms 1–2 (depth 6, breadth 8) and the recursion gate in mechanism 3 are judgment calls without validating research behind the exact values — PMI and NASA actually prescribe adaptive depth ("as far as necessary to manage"), not fixed caps. The caps work as scope discipline; do not cite them as science. See §14.*

---

## 10. Failure modes and recoveries

- **Two workers invent the same ref.** Expected. The merge pass unifies them; workers must *not* try to coordinate refs peer-to-peer.
- **A worker redefines a parent ref** instead of reusing it. Catch in merge: parent refs are read-only for workers. State this in the worker prompt.
- **Breadth explosion mid-branch** (e.g. "every wire in the harness"). The worker should have used a counted group. Coordinator sends it back with: "collapse to counted group + one exemplar."
- **A worker goes too deep** (past the leaf rule into trivia). Merge cuts it; note the cut in the footer. If it keeps happening, the worker prompt needs a sharper leaf-rule example for that topic.
- **Branch boundary collision** (two workers expanding the same subsystem). Redraw the boundary, assign sole ownership, make the other reference it.
- **Worker pads depth** with filler nodes to hit the depth target. Depth is a *cap*, not a quota — the leaf rule outranks it. Say this explicitly in worker prompts.
- **Uncertainty creep** — too many `(uncertain)` marks means the worker is guessing beyond the tree. Rule: uncertain marks are for *industry-standard inference* (LED chemistry, glass tint), never for invented components.

---

## 11. Worked example: 2015 Honda Odyssey EX-L (full trace)

| Phase | Instruction given | Result |
|---|---|---|
| 1 — Base | "Run the decomposition protocol on a 2015 Honda Odyssey EX-L. Depth 6." | ~120 nodes, depth 6, 3 refs (motor, ecu, sensor), 5 branches, logical trees: power / data / thermal |
| 2 — Deepen | 5 workers, one per branch, "+3 levels, exemplar expansion, check registry, reference don't re-expand" | ~750 nodes, depth 9, 19 unified refs, deepest chain ends in thin-film physics |
| 3 — Basement | 5 workers, "every material → compound → elements, major/trace tags, mark uncertainty" | 48/118 elements; 7 carry ~99% mass; absences recorded (no Li-ion, no rare-earths, no Hg/Cd) |
| 4 — Present | Master inventory doc + interactive periodic table (branch filters, tier colors, tap-for-detail) | Reference doc + widget + the one-paragraph truth |

Total agent calls: 1 coordinator + 5 + 5 + 5 workers across the run, 4 merge passes. No worker ever spawned a worker. No phase exceeded its budget.

**Corrections (fact-check 2026-10-21):** engine code is **J35Z8** (not J35Y6); EX-L wheels are **17-inch** (18-inch is Touring-only); the "48 elements" census is a **floor, not an assay** (Kirchain et al., MIT, *Environ. Sci. Technol.* 2021 found 76 elements in modern automobiles).

---

## 12. Adapting to new topics

- **Pick the basement first.** Before Phase 1, the coordinator should be able to name the terminal layer (§7 table). If you can't name it, the topic may be too abstract for full-depth treatment — do Phases 1–2 only.
- **Non-physical topics skip Phase 3's chemistry** but keep its *shape*: every terminal node still resolves to *something* atomic (a named person, a single instruction, a single cell). The discipline — "no node left un-grounded" — is the point, not the periodic table.
- **"Deeper on {branch}"** spends extra depth budget on one branch instead of spreading thin. Use when the user cares about one subsystem (Odyssey run: could have gone depth 11 on powertrain alone).
- **Breadth 8 is a default, not a law.** Dense technical topics (a CPU) tolerate 10; narrative topics (a legal case) want 5–6.

## 13. Checklists

**Coordinator, every phase:** ☐ topic + budgets + branches stated ☐ workers dispatched with registry ☐ recursion gate enforced ☐ merge pass done ☐ refs unified ☐ termination verified ☐ footer written (depth, nodes, refs, grouped/cut).

**Worker, every assignment:** ☐ interface-boundary test per child ☐ breadth cap / counted groups ☐ registry checked before expanding ☐ parent refs reused, not redefined ☐ other branches referenced, not expanded ☐ leaf rule respected (cap, not quota) ☐ footer returned (depth, nodes, new refs, grouped/cut).

**Merge pass:** ☐ duplicate refs unified ☐ cross-branch pointers consistent ☐ every branch terminates (leaf/ref) ☐ uncertainty marks preserved ☐ footer honest about cuts ☐ narrative sentence writable.

---

*The method's thesis: depth is cheap when shared subtrees are expanded once, and structure is what makes depth affordable. Everything else is bookkeeping.*

---

## 14. Fact-check appendix (added 2026-10-21)

This method was audited against top trusted sources. Verdicts, kept honest:

**Supported by established sources**
- *Tree decomposition* — PMI Practice Standard for WBS; NASA Systems Engineering Handbook; INCOSE SE Handbook. Limits in the sources themselves: depth should be adaptive and non-uniform, and a WBS validates scope, not anatomy.
- *Exhaustive children* — PMI's 100% rule (see the Lineage note in §2 — not MECE, and the funnel rule breaks strict MECE exclusivity).
- *Interface boundaries* — Parnas (1972); Baldwin & Clark, *Design Rules*; Stevens/Myers/Constantine (1974). This handbook's exact boundary markers (material / discipline / failure-mode changes) are a consistent gloss on those classics, not a quotation from them.
- *Funnel rule* — exactly memoization/dynamic programming: naive expansion of duplicated subtrees is exponential (Θ(2ⁿ)); expanding each shared subtree once over a DAG collapses it. Caveat: no research quantifies the savings for LLM-agent decomposition specifically, and a DAG breaks naive 100% roll-up accounting unless refs are tracked explicitly (this method tracks them).

**Partially supported / unvalidated — the two heuristics**
- *Coordinator-gated workers* — the orchestrator-worker pattern is real in production systems (Anthropic's research system: large gains on breadth-first research, ~15× token cost). But Kim et al., "Towards a Science of Scaling Agent Systems" (arXiv:2512.08296), found centralized coordination *hurts* sequential planning and that gains saturate once single-agent baselines are strong; Cemri et al., MAST (arXiv:2503.13657), found multi-agent gains often minimal, with organizational failure modes (specification, inter-agent misalignment, verification) dominating. **No study validates the specific rule "workers never spawn workers."** It is retained as a guard against an observed failure mode (runaway recursion), labeled heuristic.
- *Specific budget numbers (depth 6, breadth 8)* — consistent with PMI/NASA adaptive stopping rules and with human working-memory limits (Cowan 2010: 3–5 items), but no source prescribes these numbers, and human cognitive-load evidence does not transfer directly to LLM agents, whose real constraint is token/context economics. Labeled heuristic.

**Corrections to the worked example** (found by the same audit): the Odyssey's engine code is **J35Z8**, not J35Y6 (the Y6 is a direct-injected 280 hp engine from a later model — it contradicts the tree's own port-injection claim); the EX-L rides on **17-inch** wheels (18-inch is Touring-only); and the "48 elements" census is a **floor, not an assay** — Kirchain et al. (MIT, *Environ. Sci. Technol.* 2021) found 76 elements in modern automobiles. All three are corrected in the Odyssey documents.

*Rule for future editors of this handbook: when the method and the evidence disagree, the evidence wins and this appendix grows.*
