from __future__ import annotations

import csv
import json
from pathlib import Path
from textwrap import dedent

ROOT = Path(__file__).resolve().parents[2]
CRE_DIR = ROOT / "cre"
ARTIFACTS_DIR = CRE_DIR / "artifacts"
TRANSCRIPT_PATH = CRE_DIR / "transcripts" / "cursor_official_software_is_changing_2026-02-26.txt"
RETRIEVED_DATE = "2026-02-28"


PRIMARY_SOURCES = [
    {
        "source_id": "SRC-01",
        "title": "Software is changing",
        "url": "https://www.youtube.com/watch?v=2SkrTnGMsr0",
        "source_class": "official_video",
        "published_date": "2026-02-26",
        "retrieved_date": RETRIEVED_DATE,
        "why_relevant": "Canonical transcript source for the claims under analysis.",
        "claims_supported": ["C01", "C02", "C03", "C04", "C05", "C06", "C07", "C08"],
    },
    {
        "source_id": "SRC-02",
        "title": "Cloud Agents with Computer Use",
        "url": "https://cursor.com/changelog/02-24-26/",
        "source_class": "official_changelog_entry",
        "published_date": "2026-02-24",
        "retrieved_date": RETRIEVED_DATE,
        "why_relevant": "Release ledger for Cursor 2.6, including cloud agents with computer use, agent plans, and cloud activity surfaces.",
        "claims_supported": ["C03", "C04", "C05", "C06"],
    },
    {
        "source_id": "SRC-03",
        "title": "Cursor agents can now control their own computers",
        "url": "https://cursor.com/blog/cloud-agents-computer-use",
        "source_class": "official_blog_post",
        "published_date": "2026-02-24",
        "retrieved_date": RETRIEVED_DATE,
        "why_relevant": "Primary explanation of remote browser, terminal, and code-editing capability for cloud agents.",
        "claims_supported": ["C03", "C04", "C05", "C06"],
    },
    {
        "source_id": "SRC-04",
        "title": "A computer for every agent",
        "url": "https://www.youtube.com/watch?v=6Nru5OQq9O4",
        "source_class": "official_video",
        "published_date": "2026-02-24",
        "retrieved_date": RETRIEVED_DATE,
        "why_relevant": "Official video framing that directly supports the 'own computers' part of the transcript.",
        "claims_supported": ["C04"],
    },
    {
        "source_id": "SRC-05",
        "title": "Cursor now shows you demos, not diffs",
        "url": "https://www.youtube.com/watch?v=XbZvC4KTH68",
        "source_class": "official_video",
        "published_date": "2026-02-24",
        "retrieved_date": RETRIEVED_DATE,
        "why_relevant": "Direct official support for the idea that review increasingly includes demo artifacts rather than only textual diffs.",
        "claims_supported": ["C06", "C07"],
    },
    {
        "source_id": "SRC-06",
        "title": "Bugbot Autofix",
        "url": "https://cursor.com/changelog/02-26-26/",
        "source_class": "official_changelog_entry",
        "published_date": "2026-02-26",
        "retrieved_date": RETRIEVED_DATE,
        "why_relevant": "Release ledger for automatic PR issue fixing and review-loop automation.",
        "claims_supported": ["C06", "C07"],
    },
    {
        "source_id": "SRC-07",
        "title": "Closing the code review loop with Bugbot Autofix",
        "url": "https://cursor.com/blog/bugbot-autofix",
        "source_class": "official_blog_post",
        "published_date": "2026-02-26",
        "retrieved_date": RETRIEVED_DATE,
        "why_relevant": "Operational explanation of Bugbot Autofix spawning cloud agents to test changes and fix PR issues automatically.",
        "claims_supported": ["C06", "C07"],
    },
    {
        "source_id": "SRC-08",
        "title": "Expanding our long-running agents research preview",
        "url": "https://cursor.com/blog/long-running-agents",
        "source_class": "official_blog_post",
        "published_date": "2026-02-12",
        "retrieved_date": RETRIEVED_DATE,
        "why_relevant": "Primary evidence for reduced micromanagement over longer-running tasks and explicit rollout scope.",
        "claims_supported": ["C02", "C03", "C04"],
    },
    {
        "source_id": "SRC-09",
        "title": "The third era of AI software development",
        "url": "https://cursor.com/blog/third-era",
        "source_class": "official_blog_post",
        "published_date": "2026-02-26",
        "retrieved_date": RETRIEVED_DATE,
        "why_relevant": "Product-direction framing for autonomous cloud agents taking on larger tasks over longer timescales.",
        "claims_supported": ["C01", "C02", "C03", "C05"],
    },
    {
        "source_id": "SRC-10",
        "title": "Towards self-driving codebases",
        "url": "https://cursor.com/blog/self-driving-codebases",
        "source_class": "official_blog_post",
        "published_date": "2026-02-05",
        "retrieved_date": RETRIEVED_DATE,
        "why_relevant": "Earlier research-preview framing for a multi-agent harness that pushes work beyond synchronous chat-style coding.",
        "claims_supported": ["C01", "C02", "C03"],
    },
    {
        "source_id": "SRC-11",
        "title": "Cursor 2.5",
        "url": "https://cursor.com/blog/cursor-2-5",
        "source_class": "official_blog_post",
        "published_date": "2026-02-17",
        "retrieved_date": RETRIEVED_DATE,
        "why_relevant": "Supporting infrastructure source for plugins, async subagents, and network controls that make broader agent autonomy more plausible.",
        "claims_supported": ["C03", "C05"],
    },
]


CLAIMS = [
    {
        "claim_id": "C01",
        "claim_text": "Building software has historically required developers to manually break ideas into explicit logic the computer can execute.",
        "claim_family": "vision_statement",
        "transcript_excerpt": "To build software, you've always had to break down your ideas into small bits of logic a computer could understand.",
        "source_type": "official_video_transcript",
        "verification_status": "not_verified",
        "confidence": "low",
        "official_sources": ["SRC-01", "SRC-09", "SRC-10"],
        "supporting_quotes_or_paraphrases": [
            "The official February 2026 strategy posts argue that a new era is emerging, but they do not attempt to verify the transcript's historical claim literally.",
            "This line functions as framing, not as a dated product update."
        ],
        "practical_user_change": "None directly. This is rhetorical context for the autonomy features announced elsewhere.",
        "limitations": [
            "The statement is historical and philosophical rather than product-specific.",
            "Official sources do not present this as something users can verify in-product."
        ],
        "open_questions": [
            "Whether Cursor intends this line as a product thesis or simply as marketing framing."
        ],
        "recommended_local_experiment": "No direct product experiment. Treat as framing only and verify downstream autonomy claims instead.",
    },
    {
        "claim_id": "C02",
        "claim_text": "Current code-writing agents still often require close user attention and the product direction is to reduce that micromanagement burden.",
        "claim_family": "workflow_claim",
        "transcript_excerpt": "Even today, as agents write code for you, your constant attention is required. Micromanagement is not the future of software engineering.",
        "source_type": "official_video_transcript",
        "verification_status": "supported_but_inferred",
        "confidence": "high",
        "official_sources": ["SRC-01", "SRC-08", "SRC-09", "SRC-10"],
        "supporting_quotes_or_paraphrases": [
            "The long-running agents post says the preview exists to let agents work over longer horizons in the web app rather than only in short synchronous bursts.",
            "The 'third era' post frames autonomous cloud agents as taking on larger tasks over longer timescales.",
            "The self-driving codebases post says part of Cursor's multi-agent research harness is available in preview."
        ],
        "practical_user_change": "Users gained product surfaces aimed at reducing hand-holding: long-running web agents, agent plans, and cloud execution. The practical change is less frequent intervention on some classes of work, not zero oversight.",
        "limitations": [
            "The transcript overstates current trust if read literally; official sources present previews, planning, and cloud execution, not universal unattended autonomy.",
            "Long-running agents were explicitly preview-scoped as of February 12, 2026."
        ],
        "open_questions": [
            "How often agents still require human clarification during long tasks.",
            "Which task classes truly benefit from lower micromanagement today versus only in research preview."
        ],
        "recommended_local_experiment": "Give a long-running agent a multi-file refactor or investigation in the web app, record the number of user interventions required, and compare it to a synchronous editor-only agent session.",
    },
    {
        "claim_id": "C03",
        "claim_text": "Users should increasingly be able to hand an idea to agents and let them pursue it over longer horizons with less step-by-step decomposition.",
        "claim_family": "capability_claim",
        "transcript_excerpt": "What if you could trust agents to take an idea and run with it?",
        "source_type": "official_video_transcript",
        "verification_status": "partially_supported",
        "confidence": "medium",
        "official_sources": ["SRC-01", "SRC-02", "SRC-03", "SRC-08", "SRC-09", "SRC-10", "SRC-11"],
        "supporting_quotes_or_paraphrases": [
            "Cursor 2.6 introduced agent plans and cloud agents with computer use.",
            "The long-running agents preview made longer-horizon execution available in the web app for Ultra, Teams, and Enterprise users.",
            "The third-era and self-driving posts position the product around more autonomous cloud work, but they stop short of a blanket trust guarantee."
        ],
        "practical_user_change": "Some users can now delegate bigger tasks to long-running or cloud agents, inspect plans, and review outcomes after broader exploration than earlier chat-style coding allowed.",
        "limitations": [
            "Trust remains scoped: preview features, rollout constraints, and review expectations still apply.",
            "Official sources do not promise that any idea can be handed off successfully without supervision."
        ],
        "open_questions": [
            "Exact approval-gate semantics across plans and org types.",
            "How much autonomy differs between local editor agents and cloud agents."
        ],
        "recommended_local_experiment": "Start the same medium-complexity feature task in the editor and in the web/cloud flow. Compare how much task decomposition you must provide up front and how many follow-up interventions each path requires.",
    },
    {
        "claim_id": "C04",
        "claim_text": "Cursor agents can explore and try things in remote computers rather than only operating inside the local editor.",
        "claim_family": "capability_claim",
        "transcript_excerpt": "if they were free to explore and try things in their own computers.",
        "source_type": "official_video_transcript",
        "verification_status": "verified_directly",
        "confidence": "high",
        "official_sources": ["SRC-01", "SRC-02", "SRC-03", "SRC-04", "SRC-08"],
        "supporting_quotes_or_paraphrases": [
            "The February 24 changelog says cloud agents with computer use can use tools in remote environments and provide desktop preview.",
            "The February 24 blog says Cursor agents can control their own computers.",
            "The official companion video is titled 'A computer for every agent'."
        ],
        "practical_user_change": "Agents can run in remote environments with browser, terminal, and code-editing capability, and users can observe or review what happened through activity surfaces and previews instead of relying only on local editor actions.",
        "limitations": [
            "This is cloud/remote execution, not a guarantee that every local editor task now runs on a separate machine by default.",
            "Rollout details vary by feature surface and plan."
        ],
        "open_questions": [
            "Whether all plan tiers get the same computer-use depth and quota.",
            "What exact isolation, sandbox, and network defaults apply across organizations."
        ],
        "recommended_local_experiment": "Launch a cloud agent task that must open a browser, edit code, and run a terminal command. Verify that desktop preview or equivalent cloud-activity artifacts appear and that the execution is clearly remote rather than local-editor-only.",
    },
    {
        "claim_id": "C05",
        "claim_text": "Cursor is shifting from code-only output toward returning more fully realized working results, including live features or operational artifacts.",
        "claim_family": "workflow_claim",
        "transcript_excerpt": "What if your ideas came back as live features",
        "source_type": "official_video_transcript",
        "verification_status": "supported_but_inferred",
        "confidence": "high",
        "official_sources": ["SRC-01", "SRC-02", "SRC-03", "SRC-05", "SRC-09", "SRC-11"],
        "supporting_quotes_or_paraphrases": [
            "Cloud agents with computer use add browser and terminal actions that support feature-level execution instead of only diff generation.",
            "The official video 'Cursor now shows you demos, not diffs' directly reinforces artifact-based output and review.",
            "Cursor 2.5 added supporting agent infrastructure such as plugins and async subagents, which makes more complete task execution plausible."
        ],
        "practical_user_change": "Users should expect more runs that culminate in working previews, demos, or tested changes rather than only a raw patch to read line-by-line. In practice, this means reviewing artifacts and outcomes in addition to code.",
        "limitations": [
            "The transcript's 'live features' phrasing is broader than the formal product docs.",
            "Official sources support a shift toward richer outputs, but they do not claim all tasks now return working features automatically."
        ],
        "open_questions": [
            "What qualifies as a 'live feature' artifact across product surfaces.",
            "Whether demo-style review is standard or only available in certain cloud-agent flows."
        ],
        "recommended_local_experiment": "Ask a cloud agent to implement a small UI change, then check whether the review surface includes runnable preview artifacts, screenshots, or demo links in addition to a code diff or PR.",
    },
    {
        "claim_id": "C06",
        "claim_text": "Review is increasingly shifting from pure diff inspection toward demo or artifact inspection.",
        "claim_family": "workflow_claim",
        "transcript_excerpt": "reviewing changes",
        "source_type": "official_video_transcript",
        "verification_status": "verified_directly",
        "confidence": "high",
        "official_sources": ["SRC-01", "SRC-02", "SRC-03", "SRC-05", "SRC-06", "SRC-07"],
        "supporting_quotes_or_paraphrases": [
            "The official February 24 video is titled 'Cursor now shows you demos, not diffs'.",
            "Cloud agents with computer use ship with desktop preview and activity tracking.",
            "Bugbot Autofix closes more of the review loop by finding and fixing PR issues using cloud agents."
        ],
        "practical_user_change": "Users reviewing agent work should expect evidence beyond textual diffs: previews, cloud-activity artifacts, and auto-generated fixes in PR workflows. The center of gravity moves closer to outcome review.",
        "limitations": [
            "This does not eliminate code review; regulated or high-risk codebases will still inspect diffs closely.",
            "The strongest direct support comes from official videos and blog/changelog framing rather than a formal operational spec."
        ],
        "open_questions": [
            "Which artifact surfaces are available in the editor, web, and PR flows respectively.",
            "How long those artifacts persist and whether organizations can audit them later."
        ],
        "recommended_local_experiment": "Run a cloud-agent or Bugbot workflow on a PR and record whether the reviewer receives only diff/comment output or also preview, demo, screenshot, or replay artifacts. Treat missing artifacts as falsification.",
    },
    {
        "claim_id": "C07",
        "claim_text": "Bugbot Autofix materially changes review practice by letting review issues be fixed automatically through spawned cloud agents.",
        "claim_family": "direct_product_claim",
        "transcript_excerpt": "reviewing changes",
        "source_type": "official_video_transcript",
        "verification_status": "verified_directly",
        "confidence": "high",
        "official_sources": ["SRC-06", "SRC-07"],
        "supporting_quotes_or_paraphrases": [
            "The February 26 changelog announced Bugbot Autofix.",
            "The February 26 blog says Bugbot Autofix can find and automatically fix PR issues by spawning cloud agents to test changes."
        ],
        "practical_user_change": "PR review is no longer limited to human comments followed by manual patching. Cursor now offers a path where identified review issues can be turned into automatically tested fixes.",
        "limitations": [
            "This is specific to the Bugbot review flow, not a universal review mechanism across all Cursor agent work.",
            "The available org tiers, repo constraints, and admin controls still need verification in-product."
        ],
        "open_questions": [
            "Exactly which plans and repository setups can use Autofix today.",
            "Whether Autofix opens new branches, commits directly, or requires manual confirmation at each step."
        ],
        "recommended_local_experiment": "Create a PR with a known, review-detectable issue and run Bugbot Autofix. Verify whether it spawns cloud execution, posts a fix artifact, and proposes or applies a concrete code change.",
    },
    {
        "claim_id": "C08",
        "claim_text": "The phrase 'reviewing changes was as easy as hitting I' names a concrete interaction shortcut or UI action.",
        "claim_family": "direct_product_claim",
        "transcript_excerpt": "was as easy as hitting I",
        "source_type": "official_video_transcript",
        "verification_status": "not_verified",
        "confidence": "low",
        "official_sources": ["SRC-01", "SRC-05", "SRC-06", "SRC-07"],
        "supporting_quotes_or_paraphrases": [
            "The transcript appears truncated or mistranscribed at the end of the sentence.",
            "No official current primary source found in this verification pass maps a February 2026 Cursor update to a specific 'hitting I' interaction."
        ],
        "practical_user_change": "None established. This line should not be operationalized until the interaction is confirmed from the original video or another official source.",
        "limitations": [
            "The transcript fragment is incomplete and may be inaccurate.",
            "Treating it as a verified shortcut would overstate the evidence."
        ],
        "open_questions": [
            "Was the intended phrase 'hitting play', 'hitting run', or another UI action rather than the letter I?",
            "Does the original video visual track reveal the intended interaction?"
        ],
        "recommended_local_experiment": "Re-watch the official video frame by frame at the final sentence and confirm whether a concrete keyboard shortcut or button press is actually shown. If nothing clear appears, leave the claim unresolved.",
    },
]


EVIDENCE_ROWS = [
    {
        "claim_id": "C02",
        "claim_text": CLAIMS[1]["claim_text"],
        "verification_status": "supported_but_inferred",
        "confidence": "high",
        "primary_source_title": "Expanding our long-running agents research preview",
        "primary_source_url": "https://cursor.com/blog/long-running-agents",
        "primary_source_date": "2026-02-12",
        "evidence_kind": "official_blog_post",
        "user_scope": "Ultra, Teams, Enterprise",
        "rollout_scope": "web app, research preview",
        "notes": "Longer-running agent execution supports the transcript's anti-micromanagement claim, but does not prove fully unattended trust."
    },
    {
        "claim_id": "C02",
        "claim_text": CLAIMS[1]["claim_text"],
        "verification_status": "supported_but_inferred",
        "confidence": "high",
        "primary_source_title": "The third era of AI software development",
        "primary_source_url": "https://cursor.com/blog/third-era",
        "primary_source_date": "2026-02-26",
        "evidence_kind": "official_blog_post",
        "user_scope": "strategy framing",
        "rollout_scope": "product direction",
        "notes": "Frames autonomous cloud agents as taking on larger tasks over longer timescales."
    },
    {
        "claim_id": "C03",
        "claim_text": CLAIMS[2]["claim_text"],
        "verification_status": "partially_supported",
        "confidence": "medium",
        "primary_source_title": "Cloud Agents with Computer Use",
        "primary_source_url": "https://cursor.com/changelog/02-24-26/",
        "primary_source_date": "2026-02-24",
        "evidence_kind": "official_changelog_entry",
        "user_scope": "Cursor users with access to cloud agents",
        "rollout_scope": "Cursor 2.6 surfaces",
        "notes": "Agent plans and computer-use capability support greater delegation, but the transcript's trust framing is broader than the release note."
    },
    {
        "claim_id": "C03",
        "claim_text": CLAIMS[2]["claim_text"],
        "verification_status": "partially_supported",
        "confidence": "medium",
        "primary_source_title": "Expanding our long-running agents research preview",
        "primary_source_url": "https://cursor.com/blog/long-running-agents",
        "primary_source_date": "2026-02-12",
        "evidence_kind": "official_blog_post",
        "user_scope": "Ultra, Teams, Enterprise",
        "rollout_scope": "web app, research preview",
        "notes": "Confirms longer-horizon execution, but keeps rollout and trust explicitly scoped."
    },
    {
        "claim_id": "C04",
        "claim_text": CLAIMS[3]["claim_text"],
        "verification_status": "verified_directly",
        "confidence": "high",
        "primary_source_title": "Cloud Agents with Computer Use",
        "primary_source_url": "https://cursor.com/blog/cloud-agents-computer-use",
        "primary_source_date": "2026-02-24",
        "evidence_kind": "official_blog_post",
        "user_scope": "cloud-agent users",
        "rollout_scope": "remote environments and desktop preview",
        "notes": "Directly states that Cursor agents can use tools in remote environments, including browser, terminal, and code editing."
    },
    {
        "claim_id": "C04",
        "claim_text": CLAIMS[3]["claim_text"],
        "verification_status": "verified_directly",
        "confidence": "high",
        "primary_source_title": "A computer for every agent",
        "primary_source_url": "https://www.youtube.com/watch?v=6Nru5OQq9O4",
        "primary_source_date": "2026-02-24",
        "evidence_kind": "official_video",
        "user_scope": "official product messaging",
        "rollout_scope": "companion launch framing",
        "notes": "Reinforces the 'own computers' phrasing from the transcript with an official companion video title."
    },
    {
        "claim_id": "C05",
        "claim_text": CLAIMS[4]["claim_text"],
        "verification_status": "supported_but_inferred",
        "confidence": "high",
        "primary_source_title": "Cursor now shows you demos, not diffs",
        "primary_source_url": "https://www.youtube.com/watch?v=XbZvC4KTH68",
        "primary_source_date": "2026-02-24",
        "evidence_kind": "official_video",
        "user_scope": "official workflow messaging",
        "rollout_scope": "demo/review framing",
        "notes": "Directly supports the move toward richer artifacts, though the transcript's 'live features' language remains broader than the video title alone."
    },
    {
        "claim_id": "C05",
        "claim_text": CLAIMS[4]["claim_text"],
        "verification_status": "supported_but_inferred",
        "confidence": "high",
        "primary_source_title": "Cloud Agents with Computer Use",
        "primary_source_url": "https://cursor.com/changelog/02-24-26/",
        "primary_source_date": "2026-02-24",
        "evidence_kind": "official_changelog_entry",
        "user_scope": "cloud-agent users",
        "rollout_scope": "remote computer use and activity views",
        "notes": "Operationally supports feature-level artifact generation rather than only diff output."
    },
    {
        "claim_id": "C06",
        "claim_text": CLAIMS[5]["claim_text"],
        "verification_status": "verified_directly",
        "confidence": "high",
        "primary_source_title": "Cursor now shows you demos, not diffs",
        "primary_source_url": "https://www.youtube.com/watch?v=XbZvC4KTH68",
        "primary_source_date": "2026-02-24",
        "evidence_kind": "official_video",
        "user_scope": "official review-workflow messaging",
        "rollout_scope": "product positioning",
        "notes": "This is the cleanest direct source for the artifact-review shift."
    },
    {
        "claim_id": "C06",
        "claim_text": CLAIMS[5]["claim_text"],
        "verification_status": "verified_directly",
        "confidence": "high",
        "primary_source_title": "Closing the code review loop with Bugbot Autofix",
        "primary_source_url": "https://cursor.com/blog/bugbot-autofix",
        "primary_source_date": "2026-02-26",
        "evidence_kind": "official_blog_post",
        "user_scope": "PR review users",
        "rollout_scope": "Bugbot Autofix review flow",
        "notes": "Adds a concrete PR-review automation surface on top of the demos/artifacts narrative."
    },
    {
        "claim_id": "C07",
        "claim_text": CLAIMS[6]["claim_text"],
        "verification_status": "verified_directly",
        "confidence": "high",
        "primary_source_title": "Bugbot Autofix",
        "primary_source_url": "https://cursor.com/changelog/02-26-26/",
        "primary_source_date": "2026-02-26",
        "evidence_kind": "official_changelog_entry",
        "user_scope": "Bugbot users",
        "rollout_scope": "release entry",
        "notes": "Release note for review-loop automation."
    },
    {
        "claim_id": "C07",
        "claim_text": CLAIMS[6]["claim_text"],
        "verification_status": "verified_directly",
        "confidence": "high",
        "primary_source_title": "Closing the code review loop with Bugbot Autofix",
        "primary_source_url": "https://cursor.com/blog/bugbot-autofix",
        "primary_source_date": "2026-02-26",
        "evidence_kind": "official_blog_post",
        "user_scope": "PR review users",
        "rollout_scope": "spawned cloud agents, test your changes",
        "notes": "Strongest operational source for the mechanics of Autofix."
    },
    {
        "claim_id": "C08",
        "claim_text": CLAIMS[7]["claim_text"],
        "verification_status": "not_verified",
        "confidence": "low",
        "primary_source_title": "Software is changing",
        "primary_source_url": "https://www.youtube.com/watch?v=2SkrTnGMsr0",
        "primary_source_date": "2026-02-26",
        "evidence_kind": "official_video",
        "user_scope": "n/a",
        "rollout_scope": "transcript fragment only",
        "notes": "No corroborating primary source matched a specific 'hitting I' interaction during the verification pass."
    },
]


VERIFICATION_CHECKLIST = [
    {
        "experiment_id": "EXP-01",
        "claim_id": "C04",
        "experiment_name": "Cloud agent artifact review",
        "environment": "Current Cursor cloud-agent surface",
        "preconditions": [
            "Account with access to cloud agents",
            "Repository that can be safely modified in a disposable branch",
        ],
        "steps": [
            "Launch a cloud agent task that requires browser interaction, terminal use, and code edits.",
            "Observe whether the task runs in a remote environment rather than purely inside the local editor.",
            "Inspect the resulting activity view for preview artifacts such as screenshots, desktop preview, logs, or execution trace.",
        ],
        "expected_result": "The run clearly exposes remote computer-use evidence rather than only a final patch.",
        "falsification_condition": "If the agent cannot use remote browser or terminal surfaces, or produces no remote-execution artifacts, the 'own computers' claim is overstated for the tested surface.",
    },
    {
        "experiment_id": "EXP-02",
        "claim_id": "C07",
        "experiment_name": "Bugbot Autofix workflow",
        "environment": "Repository with PR integration and Bugbot enabled",
        "preconditions": [
            "A test PR with an issue Bugbot can plausibly flag",
            "Access to the Bugbot review surface",
        ],
        "steps": [
            "Open the PR and trigger Bugbot Autofix if the UI allows it.",
            "Record whether a cloud agent is spawned.",
            "Record whether Bugbot proposes a fix artifact, branch change, or patch for review.",
        ],
        "expected_result": "Bugbot identifies an issue and offers or applies an automatically tested fix path rather than only a plain comment.",
        "falsification_condition": "If Bugbot only comments without any fix-generation or cloud-agent behavior, the Autofix claim is not operationally present in the tested setup.",
    },
    {
        "experiment_id": "EXP-03",
        "claim_id": "C02",
        "experiment_name": "Long-running agent planning and intervention count",
        "environment": "Cursor web app with long-running agents access",
        "preconditions": [
            "Ultra, Teams, or Enterprise seat with long-running agent access",
            "A task large enough to require multiple substeps",
        ],
        "steps": [
            "Assign a moderately complex task in the web app.",
            "Measure how many clarifications or nudges are required before the agent reaches a reviewable result.",
            "Compare against a synchronous editor session on the same task.",
        ],
        "expected_result": "The long-running path requires materially fewer interventions than the synchronous path.",
        "falsification_condition": "If intervention count is unchanged or higher, the reduced-micromanagement implication is weak for the tested workload.",
    },
    {
        "experiment_id": "EXP-04",
        "claim_id": "C03",
        "experiment_name": "Delegation depth across local and cloud flows",
        "environment": "Editor agent and cloud-agent surfaces",
        "preconditions": [
            "Same repository accessible in both flows",
            "A feature request that spans search, edits, and execution",
        ],
        "steps": [
            "Run the task in the local editor flow.",
            "Run the same task in the cloud-agent or long-running flow.",
            "Compare amount of up-front decomposition, approval frequency, and completion quality.",
        ],
        "expected_result": "The cloud or long-running path accepts broader intent and performs more end-to-end execution before asking for help.",
        "falsification_condition": "If both flows require the same amount of step-by-step decomposition, the 'take an idea and run with it' claim is not operationally strong.",
    },
    {
        "experiment_id": "EXP-05",
        "claim_id": "C05",
        "experiment_name": "Live-feature versus diff-only output",
        "environment": "Cloud-agent feature implementation task",
        "preconditions": [
            "Task with a visible UI or runtime result",
            "Access to any preview or activity surface",
        ],
        "steps": [
            "Ask the agent to implement a small, visible feature.",
            "Inspect the review surface for runnable preview, screenshot, or demo artifacts.",
            "Record whether the output is richer than a diff alone.",
        ],
        "expected_result": "The agent returns demonstrable feature-level artifacts in addition to code changes.",
        "falsification_condition": "If only a diff or PR appears with no preview-style evidence, the 'live features' claim remains aspirational for the tested path.",
    },
    {
        "experiment_id": "EXP-06",
        "claim_id": "C06",
        "experiment_name": "Demo-based review surface validation",
        "environment": "Official Cursor review flow that claims demo/artifact support",
        "preconditions": [
            "Task or PR suitable for review",
            "Access to the latest review UI",
        ],
        "steps": [
            "Complete an agent run or PR review flow.",
            "Record all review artifacts shown to the user.",
            "Classify them as diff-only, demo/artifact-enhanced, or hybrid.",
        ],
        "expected_result": "The flow exposes at least one artifact beyond plain diff text.",
        "falsification_condition": "If review remains diff-only across the tested flow, the 'demos, not diffs' claim is overgeneralized.",
    },
    {
        "experiment_id": "EXP-07",
        "claim_id": "C08",
        "experiment_name": "Transcript fragment verification",
        "environment": "Original official video playback",
        "preconditions": [
            "Access to the original YouTube video",
        ],
        "steps": [
            "Re-watch the final seconds of the video slowly.",
            "Check whether the phrase 'hitting I' is accurate or a transcription artifact.",
            "Capture the actual UI action or conclude that none is clear.",
        ],
        "expected_result": "Either a concrete UI action is identified or the transcript fragment is confirmed as too ambiguous to operationalize.",
        "falsification_condition": "If no clear interaction can be confirmed, the claim must remain unresolved.",
    },
]


def build_markdown(transcript_text: str) -> str:
    verified = [c for c in CLAIMS if c["verification_status"] == "verified_directly"]
    inferred = [c for c in CLAIMS if c["verification_status"] in {"supported_but_inferred", "partially_supported"}]
    unresolved = [c for c in CLAIMS if c["verification_status"] in {"not_verified", "contradicted"}]

    def bullet_list(items):
        return "\n".join(f"- {item}" for item in items)

    source_lines = []
    for src in PRIMARY_SOURCES:
        source_lines.append(
            f"- `{src['source_id']}`: [{src['title']}]({src['url']}) — {src['published_date']} — {src['source_class'].replace('_', ' ')}. {src['why_relevant']}"
        )

    claim_rows = []
    for claim in CLAIMS:
        claim_rows.append(
            f"| {claim['claim_id']} | {claim['claim_family']} | {claim['verification_status']} | {claim['confidence']} | {claim['claim_text']} |"
        )

    verified_sections = []
    for claim in verified:
        verified_sections.append(dedent(f"""
        ### {claim['claim_id']} — {claim['claim_text']}
        - Status: `{claim['verification_status']}`
        - Confidence: `{claim['confidence']}`
        - User impact: {claim['practical_user_change']}
        - Limitations:
{bullet_list(claim['limitations'])}
        - Official sources: {', '.join(f"`{sid}`" for sid in claim['official_sources'])}
        """).strip())

    inferred_sections = []
    for claim in inferred:
        inferred_sections.append(dedent(f"""
        ### {claim['claim_id']} — {claim['claim_text']}
        - Status: `{claim['verification_status']}`
        - Confidence: `{claim['confidence']}`
        - Why this is not treated as direct fact: {' '.join(claim['limitations'][:1])}
        - Practical change: {claim['practical_user_change']}
        - Open questions:
{bullet_list(claim['open_questions'])}
        - Official sources: {', '.join(f"`{sid}`" for sid in claim['official_sources'])}
        """).strip())

    unresolved_sections = []
    for claim in unresolved:
        unresolved_sections.append(dedent(f"""
        ### {claim['claim_id']} — {claim['claim_text']}
        - Status: `{claim['verification_status']}`
        - Confidence: `{claim['confidence']}`
        - Why unresolved: {' '.join(claim['limitations'])}
        - Open questions:
{bullet_list(claim['open_questions'])}
        """).strip())

    appendix_rows = []
    for row in EVIDENCE_ROWS:
        appendix_rows.append(
            f"| {row['claim_id']} | {row['primary_source_title']} | {row['primary_source_date']} | {row['verification_status']} | {row['user_scope']} | {row['notes']} |"
        )

    experiments = []
    for exp in VERIFICATION_CHECKLIST:
        experiments.append(dedent(f"""
        ### {exp['experiment_id']} — {exp['experiment_name']}
        - Claim: `{exp['claim_id']}`
        - Environment: {exp['environment']}
        - Preconditions:
{bullet_list(exp['preconditions'])}
        - Steps:
{bullet_list(exp['steps'])}
        - Expected result: {exp['expected_result']}
        - Falsification condition: {exp['falsification_condition']}
        """).strip())

    text = dedent(f"""
    # Cursor Official Updates 2026 PhD Research

    ## Executive Summary
    This memo treats the official Cursor video [`Software is changing`](https://www.youtube.com/watch?v=2SkrTnGMsr0) (published February 26, 2026) as a hypothesis set rather than as ground truth. The video is strategically aligned with official February 2026 Cursor releases around cloud agents with computer use, long-running agents, and review-loop automation, but it is more aspirational than operational.

    Main conclusion:
    - The strongest directly verified shift is that Cursor now supports cloud agents that can act in remote computers and that official review surfaces are moving toward artifact/demo-based review.
    - The strongest directly verified review update is Bugbot Autofix on February 26, 2026.
    - The strongest supported inference is that Cursor is reducing micromanagement for some tasks through long-running and cloud execution, but not yet guaranteeing universally trustworthy end-to-end autonomy.
    - The least reliable transcript fragment is `as easy as hitting I`; that line remains unresolved and should not be operationalized.

    ## Primary Source Set
    {chr(10).join(source_lines)}

    Transcript used in this research:

    ```text
    {transcript_text.strip()}
    ```

    ## Transcript Claim Inventory
    | Claim ID | Family | Verification | Confidence | Claim |
    | --- | --- | --- | --- | --- |
    {chr(10).join(claim_rows)}

    ## Verified Product Updates
    {chr(10).join(verified_sections)}

    ## Likely Implications / Inferences
    {chr(10).join(inferred_sections)}

    ## Open Questions and Unverifiable Claims
    {chr(10).join(unresolved_sections)}

    ## What Changed for Users in Practice
    - Cursor users gained official cloud-agent capability that can use browser, terminal, and code-editing tools in remote environments rather than operating only inside the local editor.
    - Review surfaces are increasingly framed around evidence artifacts, previews, and demo-like outputs instead of only a textual diff.
    - PR review workflows changed materially with Bugbot Autofix, which officially closes more of the loop by spawning cloud agents to test and fix issues.
    - Longer-horizon agent work expanded in the web app, but rollout remained explicitly scoped to Ultra, Teams, and Enterprise users at the time of the long-running agents announcement.
    - Supporting infrastructure such as plugins, async subagents, and network controls strengthens the autonomy story, but those items are supporting enablers rather than the core claims of the video.

    ## Risks, Limitations, and Unknowns
    - The video is a strategy-layer artifact, not a release note. Over-reading it would inflate what is actually shipped.
    - Some supporting evidence comes from official video titles and official blog framing, which are primary but still more marketing-oriented than docs.
    - The docs path for Bugbot did not resolve to a stable feature-specific page during this pass, so the memo relies on official changelog and blog evidence instead.
    - The transcript is short and the final sentence appears truncated, so the claim count is intentionally conservative.
    - Cloud-agent, long-running, and review features do not obviously apply identically across editor, web app, dashboard, and enterprise-admin surfaces.

    ## Recommended Local Verification Experiments
    {chr(10).join(experiments)}

    ## Appendix: Claim-by-Claim Evidence Table
    | Claim ID | Source | Date | Verification | User Scope | Notes |
    | --- | --- | --- | --- | --- | --- |
    {chr(10).join(appendix_rows)}
    """).strip() + "\n"
    normalized_lines = []
    in_code_block = False
    for line in text.splitlines():
        if line.startswith("```"):
            in_code_block = not in_code_block
            normalized_lines.append(line)
            continue
        if in_code_block:
            normalized_lines.append(line)
        else:
            normalized_lines.append(line.lstrip())
    return "\n".join(normalized_lines) + "\n"


def main() -> None:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    transcript_text = TRANSCRIPT_PATH.read_text(encoding="utf-8") if TRANSCRIPT_PATH.exists() else ""

    memo_path = CRE_DIR / "CURSOR_OFFICIAL_UPDATES_2026_PHD_RESEARCH.md"
    memo_path.write_text(build_markdown(transcript_text), encoding="utf-8")

    claim_registry_path = ARTIFACTS_DIR / "cursor_official_updates_2026_claim_registry.json"
    claim_registry_path.write_text(json.dumps(CLAIMS, indent=2), encoding="utf-8")

    evidence_matrix_path = ARTIFACTS_DIR / "cursor_official_updates_2026_evidence_matrix.csv"
    with evidence_matrix_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "claim_id",
                "claim_text",
                "verification_status",
                "confidence",
                "primary_source_title",
                "primary_source_url",
                "primary_source_date",
                "evidence_kind",
                "user_scope",
                "rollout_scope",
                "notes",
            ],
        )
        writer.writeheader()
        writer.writerows(EVIDENCE_ROWS)

    primary_sources_path = ARTIFACTS_DIR / "cursor_official_updates_2026_primary_sources.json"
    primary_sources_path.write_text(json.dumps(PRIMARY_SOURCES, indent=2), encoding="utf-8")

    verification_checklist_path = ARTIFACTS_DIR / "cursor_official_updates_2026_verification_checklist.json"
    verification_checklist_path.write_text(json.dumps(VERIFICATION_CHECKLIST, indent=2), encoding="utf-8")

    print(memo_path)
    print(claim_registry_path)
    print(evidence_matrix_path)
    print(primary_sources_path)
    print(verification_checklist_path)


if __name__ == "__main__":
    main()
