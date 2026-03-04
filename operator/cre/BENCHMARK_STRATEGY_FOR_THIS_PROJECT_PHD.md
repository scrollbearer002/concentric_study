# Benchmark Strategy For This Project (PhD)

## Environment basis
This strategy is for the live `concentric_study` repo on `/Users/christianpardo/Desktop/concentric_study`, running on this Mac with:
- full test baseline: `193 passed`, `3 skipped`, `5 warnings`
- pure architecture conformance: `enforcement_passed: true`
- host-tool health: `all_required_ready: true`
- current strong path: macOS + Safari + Quartz/PyObjC + screenshot/SoM/a11y + verification

This is not a generic browser-agent recommendation. It is a repo-specific testing strategy.

## Short answer
From the candidate list, the best tests for this project fall into three tiers:

1. **Immediate operational tests on the real current runtime**
   - `wikipedia.org`
   - `news.ycombinator.com`
   - carefully bounded `maps.google.com` tasks
2. **Separate benchmark branch for repeatable browser-agent evaluation**
   - `WebArena`
   - `VisualWebArena`
   - `BrowserGym` as a harness if we choose to integrate benchmarks systematically
3. **Offline generalization/evaluation datasets**
   - `Mind2Web`

`Surf.new` is low-value for scientific evaluation in this repo. It may be useful for inspiration, but not as a core benchmark.

## What tests we can do from the list

### A. WebArena
What it is:
- self-hostable browser benchmark with realistic site replicas and long-horizon tasks
- official site: `https://webarena.dev/`
- official repo: `https://github.com/web-arena-x/webarena`
- paper: `https://arxiv.org/abs/2307.13854`

What tests we can do for this repo:
- shopping flow tests
- forum posting/commenting tests
- GitLab-style issue/wiki/repo tasks
- CMS/content editing tasks
- long-horizon multi-step navigation and recovery tests

How to use it to our advantage:
- **not** by replacing the current Safari runtime
- use it as a **separate benchmark branch** to measure:
  - task completion rate
  - recovery rate
  - step efficiency
  - action drift
  - cross-task planning quality
- useful for proving whether our planning/recovery architecture generalizes beyond the specific live sites we currently use

Why it is a good fit:
- repeatable
- lower anti-bot interference than real sites
- aligns with long-horizon browser-agent evaluation research

Why it is not the first thing to wire into the core path:
- our current strong path is macOS + Safari + Quartz + live site instrumentation
- WebArena is a browser benchmark environment, not a direct drop-in replacement for our current OS-native runtime

Verdict for this repo:
- **high value**
- **separate benchmark/evaluation branch**
- **not core runtime replacement**

### B. VisualWebArena
What it is:
- vision-oriented extension of the WebArena family
- especially relevant to screenshot-based or multimodal agents
- already cited locally in `operator/agent_core.py`

What tests we can do:
- screenshot-grounded web task completion
- compare performance of:
  - vision-first
  - DOM/HTML-first
  - hybrid approaches
- test whether our SoM + screenshot + a11y fusion actually helps on benchmark tasks

How to use it to our advantage:
- this repo is already vision-heavy
- VisualWebArena is the better benchmark family than plain WebArena for our current architecture
- it lets us evaluate the actual project strengths instead of testing only HTML-driven agents

Verdict for this repo:
- **very high value**
- likely better than plain WebArena once we build the benchmark branch

### C. BrowserGym
What it is:
- a browser-task benchmarking harness ecosystem used to run/evaluate browser benchmarks systematically
- official docs: `https://browsergym.readthedocs.io/`

What tests we can do:
- repeated benchmark execution
- standardized evaluation loops
- multi-benchmark orchestration once WebArena/VisualWebArena are added

How to use it to our advantage:
- useful if we want a dedicated **evaluation harness** instead of ad hoc benchmark scripts
- strongest value comes **after** we decide to support WebArena/VisualWebArena systematically

Verdict for this repo:
- **medium-high value**
- infrastructure for a benchmark branch, not an immediate operational test target

### D. Mind2Web
What it is:
- real-web task dataset with HTML/screenshot annotations and generalization splits
- official site: `https://osu-nlp-group.github.io/Mind2Web/`
- paper: `https://arxiv.org/abs/2306.06070`

What tests we can do:
- offline generalization evaluation
- compare whether our planners and action abstractions overfit to a few site types
- evaluate prompt/planning quality against a broader real-site task distribution

How to use it to our advantage:
- not as a direct Safari runtime demo
- use it as a **research/evaluation dataset** to stress-test generalization claims
- especially useful for:
  - plan generation quality
  - task decomposition quality
  - hybrid perception justification

Why it is not a first operational target:
- it is primarily a dataset/benchmark surface
- it does not directly exercise the exact current macOS Safari runtime in the same way as live smoke sites

Verdict for this repo:
- **high value for offline evaluation**
- **not the first live integration target**

### E. Surf.new
What it is:
- lightweight playground for trying web agents quickly

What tests we can do:
- informal exploratory demos
- quick agent behavior inspection

How to use it to our advantage:
- low-friction inspiration or quick comparisons
- not strong enough as a scientific benchmark for this repo

Verdict for this repo:
- **low scientific value**
- optional inspiration only

### F. Wikipedia
What it is:
- stable, low-risk, text-heavy live site

What tests we can do right now on the strong runtime:
- page search/navigation
- section targeting
- extraction and summarization
- citation lookup
- multi-step navigation chains

How to use it to our advantage:
- best live smoke site for current Safari runtime
- good for testing:
  - navigation
  - reading/extraction
  - wrong-surface detection
  - verification quality
- low risk of anti-bot friction compared with commercial sites

Verdict for this repo:
- **very high immediate value**
- best live test site from the list for current workflow improvement

### G. Hacker News (`news.ycombinator.com`)
What it is:
- simple, text-heavy live site with minimal JS complexity

What tests we can do right now:
- thread navigation
n- reading and extraction
- story ranking checks
- bounded posting/reply reconnaissance if authenticated and explicitly intended

How to use it to our advantage:
- ideal for clean navigation and DOM/a11y/screenshot agreement tests
- good intermediate complexity between Wikipedia and dynamic app sites

Verdict for this repo:
- **high immediate value**
- very good live smoke/integration target

### H. Google Maps
What it is:
- real, dynamic, JavaScript-heavy live site

What tests we can do:
- search for locations
- route lookup
- hours/address extraction
- bounded multi-step route tasks

How to use it to our advantage:
- stronger dynamic-site stress test after Wikipedia/HN
- useful for validating whether the current runtime handles modern, reactive web UIs

Why to use cautiously:
- more dynamic behavior
- more layout volatility
- higher risk than Wikipedia/HN

Verdict for this repo:
- **good later-stage live test**
- not the first benchmark from the list to prioritize

## What “enhance” should mean in this project
For `concentric_study`, **enhance** should not mean “add more stuff.”

It should mean a change that **measurably improves** one or more of:
- task completion rate
- recovery rate
- verification accuracy
- cross-site generalization
- artifact truthfulness
- debugging speed
- evidence quality

And it must do that **without weakening**:
- host-tool health
- architecture conformance
- pre-click confirmation
- final verification
- strong Safari/macOS runtime behavior

So in this repo, enhancement means:

> a measurable reliability or generalization gain, proven by live runs, tests, or benchmark artifacts, without degrading the strong current core.

That definition is consistent with the repo rules and with the current architecture state.

## Best workflow use of these benchmarks/sites

### Tier 1 — Current-runtime live smoke tests
Use now:
- Wikipedia
- Hacker News
- later Google Maps

Purpose:
- improve the actual Safari/macOS path we already have
- validate navigation, extraction, surface control, recovery, and verification on real sites

### Tier 2 — Separate benchmark branch
Use next:
- WebArena
- VisualWebArena
- optionally BrowserGym as the harness

Purpose:
- create repeatable, paper-grade evaluation of browser-task performance
- compare plan quality, recovery, and task completion under controlled conditions
- measure progress without relying only on ad hoc demos

### Tier 3 — Offline generalization branch
Use after Tier 2:
- Mind2Web

Purpose:
- evaluate how well the project generalizes across broader web task distributions
- stress-test whether our abstractions overfit a few known websites

## Why this ordering is correct for this repo
Because the current architecture is strongest at:
- macOS-native execution
- Safari/full-screen surface control
- screenshot/SoM/a11y fusion
- trace/recovery/verification

The immediate leverage comes from exercising that path on simple, real live sites.

Benchmark suites help next, but only if kept in a bounded evaluation branch so they do not distort the current strong runtime path.

## Facts from the live repo that support this strategy
- current local test baseline: `193 passed`, `3 skipped`, `5 warnings`
- pure architecture conformance: passes, with `AC006` as monitored debt
- host-tool health: all required substrate classes ready
- current benchmark-family references in repo are mostly citation-level, not integrated harnesses:
  - `operator/a11y_engine.py`
  - `operator/element_map.py`
  - `operator/agent_core.py`
  - `operator/cre/ACADEMIC_VALIDATION.md`
- there is currently no checked-in CI workflow directory, so CI-heavy benchmark automation is not the first move

## Best immediate next tests from the list
If the goal is to enhance the current workflow right now, the best order is:

1. Wikipedia live smoke tasks
2. Hacker News live smoke tasks
3. Google Maps bounded dynamic tasks
4. VisualWebArena branch design
5. WebArena/BrowserGym integration branch
6. Mind2Web offline evaluation branch

## Final recommendation
Use the list like this:
- **Wikipedia + HN** to improve the current real runtime
- **VisualWebArena/WebArena** to build a scientific benchmark branch
- **Mind2Web** to test generalization claims later
- **Surf.new** only if you want quick inspiration, not evidence

That is the strongest evidence-backed use of these environments for `concentric_study`.
