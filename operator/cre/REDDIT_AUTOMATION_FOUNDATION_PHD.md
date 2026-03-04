# Reddit Automation Foundation (PhD)

## Summary
This pass established the foundation for a separate Reddit automation product.

We did two things:
1. Verified the current official Reddit policy and product boundary at a high level.
2. Performed a live signed-in Safari reconnaissance pass against Reddit's home surface and submit surface using the current Concentric Study instrumentation stack.

This is enough to say the following with confidence:
- The current project can already instrument Reddit as a live browser target.
- It can capture the page, build Set-of-Mark overlays, record a visual monitor timeline, and preserve evidence artifacts.
- A production-grade Reddit posting system should not be designed as uncontrolled GUI spam automation.
- The correct product direction is policy-aware, approval-gated, evidence-logged automation, ideally using official Reddit developer surfaces where feasible and GUI automation only where necessary.

## Official Constraint Surface
Primary source classes used:
- Reddit Content Policy
- Reddit User Agreement
- Reddit developer / platform documentation and official product pages where available

Operational reading:
- Reddit treats spam, manipulation, and inauthentic platform abuse as policy problems.
- Any company-posting workflow must include explicit rate limits, subreddit-fit checks, human review, and transparency about the account identity.
- The system should default to drafting plus approval, not blind auto-posting.

PhD-level design implication:
- The separate project should be built as a **policy-constrained publishing agent**, not just a browser bot.
- The minimum viable safe architecture is: source ingestion -> draft generation -> subreddit selection -> rule check -> human approval -> post execution -> evidence capture.

## Live Reconnaissance Performed
Live pages inspected:
- `https://www.reddit.com/`
- `https://www.reddit.com/submit`

Artifacts created under:
- `operator/cre/reddit_research_demo/`

Observed outputs:
- front-window screenshots for both pages
- Set-of-Mark overlays for both pages
- a short VisualMonitor timeline spanning the live navigation
- machine-readable summary JSON

Current live evidence says:
- Safari navigation to Reddit worked.
- Signed-in Reddit surfaces were reachable.
- Screenshot capture worked.
- Set-of-Mark grounding worked, yielding `144` zones on both captured Reddit surfaces.
- Visual monitoring worked, yielding `12` timeline entries.
- Accessibility extraction worked only at a shallow AppleScript fallback level on the captured Reddit surfaces.

This means the current project can already support a first-stage Reddit product prototype centered on:
- page observation
- page-state evidence capture
- UI surface mapping
- future action planning against post-composer screens

## Tools Used In This Pass
### Web / research tools
- Official-source web research to check Reddit policy and automation constraints.

### Browser / OS tools
- `Safari`
- `open`
- `osascript`
- `screencapture`

### Current project tools
- `window_capture.capture_front_window`
- `VisualGroundingEngine.generate_som_overlay`
- `A11yEngine.extract`
- `VisualMonitor`

### Artifacts written
- `operator/cre/reddit_research_demo/home.png`
- `operator/cre/reddit_research_demo/home_som.png`
- `operator/cre/reddit_research_demo/submit.png`
- `operator/cre/reddit_research_demo/submit_som.png`
- `operator/cre/reddit_research_demo/reddit_demo_summary.json`
- `operator/cre/reddit_research_demo/visual_monitor/*.png`

## What The Separate Product Should Be
If the goal is "post about what a company is doing," the serious product is not just "make Reddit posts."

It should have these layers:
1. **Source ingestion**
   - ingest company updates from inventory, product feed, blog, changelog, or internal event stream
2. **Content framing**
   - determine what is announcement-worthy versus spammy or low-value
3. **Subreddit selection**
   - select only subreddits whose norms and rules fit the content
4. **Policy and rule check**
   - enforce subreddit rules, account constraints, and self-promotion limits
5. **Draft generation**
   - generate title, body, links, disclosures, and tone variants
6. **Human approval**
   - require review before posting in public environments
7. **Execution**
   - use official API/platform surfaces where possible; GUI automation only where needed
8. **Evidence and logging**
   - save screenshots, post IDs, timestamps, and exact drafted content
9. **Feedback loop**
   - track engagement, removals, moderator actions, and future posting fitness

## What This Project Already Gives You For That Future Product
Concentric Study already contributes major reusable pieces:
- browser navigation and observation
- evidence capture
- visual grounding
- recovery scaffolding
- trace logging
- benchmark evaluation
- security and approval boundaries
- site knowledge structure

That means the next repo does not start from zero. It can inherit the architecture patterns directly.

## Current Gap To Close Before Real Reddit Posting
The current Reddit pass was reconnaissance only.

Not yet built in this repo for Reddit specifically:
- subreddit rule modeling
- Reddit-specific site knowledge
- post-composer action contracts
- anti-spam policy guardrails tailored to Reddit
- approval-gated publishing loop
- post-success verification tied to a real Reddit submission

## Recommended Next Build Order
1. Create a new Desktop project folder for the Reddit showcase product.
2. Copy over the architectural patterns, not the whole repo blindly.
3. Start with a `research + draft + approval + evidence` workflow.
4. Add Reddit site knowledge and composer mapping before attempting autonomous posting.
5. Keep public posting behind explicit approval until policy and subreddit behavior are well modeled.

## Bottom Line
The current project is already good enough to serve as the research and systems foundation for a Reddit-focused publishing agent.

What we proved today is not "it can already post safely at scale."
What we proved is more important:
- it can observe Reddit live
- it can preserve evidence
- it can structure the interaction surface
- it has the architectural pieces needed to evolve into a serious, policy-aware Reddit automation product
