# Reddit Live Demo For Brian (PhD)

## What was demonstrated live
A signed-in Reddit Safari session was used to demonstrate that the current Concentric Study stack can:
- navigate between live Reddit surfaces
- move backward and forward through browser history
- open the Reddit submit composer
- inspect the live composer DOM instead of guessing the UI
- write a real draft into the body field
- write a title into the title component state
- capture evidence artifacts of the live session

## Live navigation performed
Sequence executed:
1. `https://www.reddit.com/`
2. `https://www.reddit.com/r/popular/`
3. `https://www.reddit.com/r/technology/`
4. browser back
5. browser forward
6. `https://www.reddit.com/submit`

## Live draft created
Title intent:
- `What I learned while instrumenting Reddit with a macOS web agent`

Body draft inserted into the live composer:
- starts with: `Hello, my name is Concentric Study, made by Christian.`
- explains the Reddit exploration and what was observed
- frames the accomplishment as evidence-driven browser instrumentation, not blind spam posting
- includes a direct nod to Brian and the possibility space of the system

## What was verified
Verified from live Safari DOM after insertion:
- body field contained the inserted draft text
- title component stored the intended title as its value attribute

## Tools used
### System/browser tools
- `Safari`
- `open`
- `osascript`
- `screencapture`

### Project tools
- `window_capture.capture_front_window`
- `VisualGroundingEngine.generate_som_overlay`
- `A11yEngine.extract`
- `VisualMonitor`

### Browser-side instrumentation used during the demo
- DOM inspection via Safari JavaScript execution
- live query of editable fields, buttons, and title/body components
- component-aware filling of Reddit's current submit composer

## Evidence artifacts
- `operator/cre/reddit_research_demo/home.png`
- `operator/cre/reddit_research_demo/home_som.png`
- `operator/cre/reddit_research_demo/submit.png`
- `operator/cre/reddit_research_demo/submit_som.png`
- `operator/cre/reddit_research_demo/draft_filled.png`
- `operator/cre/reddit_research_demo/draft_filled_final.png`
- `operator/cre/reddit_research_demo/reddit_demo_summary.json`
- `operator/cre/reddit_research_demo/visual_monitor/`

## Why the demo stopped before public posting
The system reached the real Reddit composer and prepared a live draft, but it did not submit a public post automatically.

Reason:
- public posting from a signed-in personal account is a real-world external action with reputational and policy consequences
- the current submit surface also still required a clean posting target / community selection boundary, which should not be guessed in a public demo

PhD-level interpretation:
- this is the correct stopping point for a safe demonstration
- the hard part is not filling text; it is making posting policy-aware, target-aware, and approval-gated

## Bottom line for Brian
The project already has the technical primitives needed for a serious Reddit automation product:
- navigation
- observation
- grounding
- monitoring
- DOM inspection
- draft composition
- evidence logging

What remains is product discipline:
- subreddit rule modeling
- approval workflow
- safe posting boundary
- post-success verification
