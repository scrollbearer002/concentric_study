from __future__ import annotations

import csv
import dataclasses
import html
import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parents[2]
CRE_DIR = ROOT / "cre"
ARTIFACTS_DIR = CRE_DIR / "artifacts"

RETRIEVED_DATE = "2026-03-04"

CURSOR_MCP_DOCS_URL = "https://cursor.com/docs/context/mcp"
CURSOR_PLUGINS_DOCS_URL = "https://cursor.com/docs/plugins"
CURSOR_CHANGELOG_URL = "https://cursor.com/changelog"
CURSOR_CHANGELOG_26_URL = "https://cursor.com/changelog/2-6"
CURSOR_25_BLOG_URL = "https://cursor.com/blog/cursor-2-5"
CURSOR_MARKETPLACE_URL = "https://cursor.com/marketplace"
MCP_APPS_OVERVIEW_URL = "https://modelcontextprotocol.io/extensions/apps/overview"

LOCAL_CURSOR_ENV_PATH = CRE_DIR / "artifacts" / "cursor_environment" / "latest.json"
LOCAL_TOOL_HEALTH_PATH = ROOT / "agent_infra" / "tool_health_catalog.json"
LOCAL_PHD_PRACTICE_PATH = CRE_DIR / "PHD_DECISION_PRACTICE.md"
LOCAL_WORKFLOW_VALUE_PATH = CRE_DIR / "MISSED_TOOL_WORKFLOW_VALUE_PHD.md"
LOCAL_ENV_BENEFITS_PATH = CRE_DIR / "PHASE_1_ENVIRONMENT_BENEFITS_PHD.md"
LOCAL_MASTER_TOOL_LIST_PATH = CRE_DIR / "MASTER_TOOL_LIST_PHD.md"


@dataclass(frozen=True)
class PrioritySpec:
    tier: str
    rank: int
    why_now: str
    gap_filled: str
    complements: str
    pilot_experiment: str
    risk_note: str
    feasibility_note: str
    workflow_classes: list[str]
    repo_fit: str
    upgrade_magnitude: str
    evidence_strength: str
    security_risk: str
    local_feasibility: str
    why_it_matters: str


def _fetch_text(url: str) -> str:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.text


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "candidate"


def _normalize_name(name: str) -> str:
    return re.sub(r"\s+", " ", name).strip()


def _normalize_description(value: str) -> str:
    value = html.unescape(value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def _version_tuple(version: str) -> tuple[int, ...]:
    numbers = [int(part) for part in re.findall(r"\d+", version)]
    return tuple(numbers or [0])


def _cursor_version_at_least(current_version: str, minimum_version: str) -> bool:
    current = list(_version_tuple(current_version))
    minimum = list(_version_tuple(minimum_version))
    width = max(len(current), len(minimum))
    current.extend([0] * (width - len(current)))
    minimum.extend([0] * (width - len(minimum)))
    return tuple(current) >= tuple(minimum)


def _extract_marketplace_plugins(page_html: str) -> list[dict[str, str]]:
    blocks = re.findall(
        r'<button type="button" class="ui-plugin-item ui-plugin-item--btn">(.*?)</button>',
        page_html,
        re.DOTALL,
    )
    seen: set[str] = set()
    items: list[dict[str, str]] = []
    for block in blocks:
        name_match = re.search(r'ui-plugin-item__name"[^>]*>(.*?)</span>', block)
        desc_match = re.search(r'data-color="secondary"[^>]*>(.*?)</span>', block)
        if not name_match:
            continue
        name = _normalize_name(re.sub(r"<.*?>", "", name_match.group(1)))
        desc = _normalize_description(re.sub(r"<.*?>", "", desc_match.group(1) if desc_match else ""))
        if name in seen:
            continue
        seen.add(name)
        items.append({"name": name, "description": desc})
    return items


def _extract_docs_servers(page_html: str) -> list[dict[str, Any]]:
    start = page_html.find('\\"maxItems\\":5,\\"servers\\":[')
    if start == -1:
        raise RuntimeError("Could not locate the Cursor docs MCP server inventory.")
    array_start = page_html.find("[", start)
    if array_start == -1:
        raise RuntimeError("Could not locate the start of the Cursor docs server array.")

    level = 0
    array_end = -1
    for idx in range(array_start, len(page_html)):
        char = page_html[idx]
        if char == "[":
            level += 1
        elif char == "]":
            level -= 1
            if level == 0:
                array_end = idx
                break
    if array_end == -1:
        raise RuntimeError("Could not locate the end of the Cursor docs server array.")

    encoded = page_html[array_start:array_end + 1]
    decoded = bytes(encoded, "utf-8").decode("unicode_escape")
    servers = json.loads(decoded)
    for item in servers:
        item["name"] = _normalize_name(item["name"])
        item["description"] = _normalize_description(item["description"])
    return servers


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _transport_list(raw_transport: list[str] | None) -> list[str]:
    if not raw_transport:
        return []
    normalized: list[str] = []
    for item in raw_transport:
        value = item.strip().lower()
        if value == "http":
            normalized.append("streamable_http")
        else:
            normalized.append(value)
    return normalized


def _auth_mode_from_docs_item(item: dict[str, Any]) -> list[str]:
    oauth = item.get("oauth")
    install = item.get("install") or {}
    if oauth is True:
        return ["oauth"]
    if isinstance(install, dict):
        if install.get("headers"):
            return ["api_key"]
        if install.get("env"):
            env_keys = " ".join(install["env"].keys()).lower()
            if any(token in env_keys for token in ["token", "key", "secret", "auth", "password"]):
                return ["api_key"]
    return ["none"]


def _auth_mode_from_plugin(name: str, description: str, matching_docs: dict[str, Any] | None) -> list[str]:
    if matching_docs:
        return _auth_mode_from_docs_item(matching_docs)
    haystack = f"{name} {description}".lower()
    if any(token in haystack for token in ["oauth", "authenticate"]):
        return ["oauth"]
    if any(token in haystack for token in ["secret", "auth", "token", "wallet", "credentials"]):
        return ["api_key"]
    return ["other"]


def _workflow_classes_for_text(name: str, description: str) -> list[str]:
    text = f"{name} {description}".lower()
    classes: list[str] = []

    if any(token in text for token in [
        "documentation", "docs", "research", "analysis", "search", "content extraction",
        "brief", "dashboard", "insights", "knowledge"
    ]):
        classes.append("research_intelligence")
    if any(token in text for token in [
        "repo", "repository", "code", "version control", "github", "gitlab", "components",
        "schema", "api/sdk", "code examples", "up-to-date code documentation"
    ]):
        classes.append("repo_retrieval")
    if any(token in text for token in [
        "browser", "automation", "deploy", "deployment", "database", "serverless",
        "cloud", "functions", "workers", "test", "testing", "cli", "model serving",
        "browserstack", "playwright", "device", "mobile apps", "wrangler", "iaс"
    ]):
        classes.append("execution_environment")
    if any(token in text for token in [
        "error", "tracing", "trace", "monitoring", "performance", "analytics", "logging",
        "audit", "insights", "debug", "observability", "langfuse", "sentry", "posthog"
    ]):
        classes.append("observability_forensics")
    if any(token in text for token in [
        "evaluation", "tests", "testing", "ci", "compiler", "review", "experiments",
        "feature flags", "quality", "smoke tests", "validation"
    ]):
        classes.append("verification_evaluation")
    if any(token in text for token in [
        "secret", "auth", "authentication", "security", "governance", "access",
        "audit", "protect", "policy", "wallet", "credentials", "1password"
    ]):
        classes.append("security_governance")
    if any(token in text for token in [
        "figma", "draw", "whiteboard", "diagram", "charts", "notebook", "briefs",
        "collaborate", "visually", "reports"
    ]):
        classes.append("artifact_generation")
    if any(token in text for token in [
        "slack", "linear", "jira", "confluence", "notion", "monday", "project management",
        "team", "workflow automation", "documents", "issues", "tasks", "code review", "shipping"
    ]):
        classes.append("coordination_orchestration")

    if not classes:
        classes.append("execution_environment")
    return sorted(set(classes))


def _repo_fit_from_classes(classes: list[str], name: str, description: str) -> str:
    score = 0
    weight = {
        "research_intelligence": 4,
        "repo_retrieval": 4,
        "execution_environment": 3,
        "observability_forensics": 4,
        "verification_evaluation": 4,
        "security_governance": 4,
        "artifact_generation": 2,
        "coordination_orchestration": 2,
    }
    for value in classes:
        score += weight[value]

    text = f"{name} {description}".lower()
    if any(token in text for token in ["browser", "trace", "evaluation", "docs", "research", "audit", "secret"]):
        score += 1

    if score >= 12:
        return "high"
    if score >= 9:
        return "medium_high"
    if score >= 6:
        return "medium"
    return "low"


def _upgrade_magnitude(repo_fit: str, classes: list[str], name: str) -> str:
    if "benchmark" in name.lower() or "trace" in name.lower():
        return "transformational"
    if repo_fit == "high":
        return "substantial"
    if repo_fit == "medium_high":
        return "moderate"
    return "minimal"


def _security_risk(name: str, description: str) -> str:
    text = f"{name} {description}".lower()
    if any(token in text for token in ["wallet", "swap", "sign", "secret management", "credentials"]):
        return "high"
    if any(token in text for token in [
        "deploy", "deployment", "browser", "automation", "database", "cloud", "auth",
        "security", "policy", "audit", "feature flags"
    ]):
        return "medium"
    return "low"


def _redundancy_with_repo(name: str, description: str) -> str:
    text = f"{name} {description}".lower()
    if any(token in text for token in [
        "tdd", "debugging", "collaboration patterns", "core skills library",
        "best practices"
    ]):
        return "high"
    if any(token in text for token in [
        "code review", "search", "browser", "evaluation", "monitoring", "docs"
    ]):
        return "partial"
    return "none"


def _local_feasibility(
    *,
    kind: str,
    name: str,
    description: str,
    current_cursor_version: str,
) -> str:
    text = f"{name} {description}".lower()
    if kind == "internal_opportunity":
        return "needs_setup"
    if any(token in text for token in ["figma", "tldraw", "amplitude", "interactive ui", "whiteboard", "charts"]):
        # These exist as plugins now, but their highest-value MCP Apps UX is a 2.6 feature.
        if not _cursor_version_at_least(current_cursor_version, "2.6.0"):
            return "blocked_by_cursor_version"
    if kind in {"cursor_plugin", "external_server"}:
        return "needs_setup"
    return "unclear"


def _evidence_strength(kind: str) -> str:
    if kind == "external_server":
        return "high"
    if kind == "cursor_plugin":
        return "medium_high"
    return "high"


def _recommended_experiment(name: str, classes: list[str]) -> str:
    if "research_intelligence" in classes and "repo_retrieval" in classes:
        return f"Use {name} on a live repo question with weak lexical overlap and compare retrieval quality against rg-only lookup."
    if "research_intelligence" in classes:
        return f"Run {name} on a current-docs research task and compare source freshness and citation quality against the current workflow."
    if "execution_environment" in classes:
        return f"Use {name} for a bounded browser or runtime task and compare setup friction, observability, and recovery against the existing local path."
    if "observability_forensics" in classes:
        return f"Use {name} after a failed run to see whether it shortens root-cause time relative to manual trace and screenshot inspection."
    if "verification_evaluation" in classes:
        return f"Use {name} on a regression-evaluation loop and compare signal quality versus current ad hoc checks."
    if "security_governance" in classes:
        return f"Run {name} in a safe sandbox and verify whether it improves secret handling, auditability, or approval clarity without expanding risk."
    if "artifact_generation" in classes:
        return f"Use {name} to generate a review artifact and compare whether it improves communication over diff-only or screenshot-only evidence."
    if "coordination_orchestration" in classes:
        return f"Use {name} in one multi-step coordination task and measure whether it reduces manual context handoff."
    return f"Run a focused pilot for {name} and record setup cost, signal quality, and overlap with existing tooling."


def _default_why_it_matters(name: str, description: str, classes: list[str]) -> str:
    class_phrase = ", ".join(classes)
    return (
        f"{name} is a credible Cursor MCP surface for {class_phrase}. "
        f"In this repo, that matters because the workflow depends on research, browser-state handling, verification, "
        f"and evidence-rich diagnostics rather than plain code generation alone."
    )


def _default_why_not_priority(repo_fit: str, redundancy: str, local_feasibility: str) -> str | None:
    reasons: list[str] = []
    if repo_fit in {"low", "medium"}:
        reasons.append(f"repo fit is only {repo_fit}")
    if redundancy != "none":
        reasons.append(f"overlap with current tooling is {redundancy}")
    if local_feasibility == "blocked_by_cursor_version":
        reasons.append("highest-value UX is blocked by the current local Cursor baseline")
    if not reasons:
        return None
    return "; ".join(reasons)


def _score_candidate(
    *,
    workflow_classes: list[str],
    repo_fit: str,
    upgrade_magnitude: str,
    evidence_strength: str,
    security_risk: str,
    local_feasibility: str,
    redundancy: str,
) -> dict[str, int]:
    mapping = {
        "low": 1,
        "medium": 2,
        "medium_high": 4,
        "high": 5,
        "minimal": 1,
        "moderate": 3,
        "substantial": 4,
        "transformational": 5,
        "ready": 5,
        "needs_setup": 3,
        "blocked_by_cursor_version": 1,
        "unclear": 2,
        "none": 5,
        "partial": 3,
        "high_redundancy": 1,
        "medium_high_evidence": 4,
    }
    workflow_lift = 1 + min(len(workflow_classes), 4)
    research_lift = 5 if "research_intelligence" in workflow_classes else 2
    operational_lift = 5 if "execution_environment" in workflow_classes or "observability_forensics" in workflow_classes else 2
    evaluation_lift = 5 if "verification_evaluation" in workflow_classes else 2
    security_compatibility = {"low": 5, "medium": 3, "high": 1}[security_risk]
    adoption_friction = {"ready": 5, "needs_setup": 3, "blocked_by_cursor_version": 1, "unclear": 2}[local_feasibility]
    evidence_quality = {"high": 5, "medium_high": 4, "medium": 3, "low": 1}[evidence_strength]
    local_readiness = {"ready": 5, "needs_setup": 3, "blocked_by_cursor_version": 1, "unclear": 2}[local_feasibility]

    priority_score = (
        workflow_lift * 2
        + research_lift * 2
        + operational_lift
        + evaluation_lift
        + evidence_quality * 2
        + local_readiness * 2
        + security_compatibility
        - (6 - adoption_friction)
    )
    phd_upgrade_score = (
        {"low": 1, "medium": 2, "medium_high": 4, "high": 5}[repo_fit]
        + {"minimal": 1, "moderate": 3, "substantial": 4, "transformational": 5}[upgrade_magnitude]
        + evidence_quality
    )
    time_to_value = {"ready": 5, "needs_setup": 3, "blocked_by_cursor_version": 1, "unclear": 2}[local_feasibility]
    if redundancy == "high":
        priority_score -= 4
    elif redundancy == "partial":
        priority_score -= 2

    return {
        "workflow_lift": workflow_lift,
        "research_lift": research_lift,
        "operational_lift": operational_lift,
        "evaluation_lift": evaluation_lift,
        "security_compatibility": security_compatibility,
        "adoption_friction": adoption_friction,
        "evidence_quality": evidence_quality,
        "local_readiness": local_readiness,
        "priority_score": priority_score,
        "phd_upgrade_score": phd_upgrade_score,
        "time_to_value": time_to_value,
    }


MANUAL_PRIORITY: dict[tuple[str, str], PrioritySpec] = {
    ("cursor_plugin", "Context7"): PrioritySpec(
        tier="Tier A",
        rank=1,
        why_now="This is the cleanest immediate upgrade for current-doc and API lookup inside Cursor.",
        gap_filled="Repo-scale and documentation-scale retrieval is still weaker than the project's research standard demands.",
        complements="ResearchAgent, SkillLibrary semantic retrieval, and rg-based repo exploration.",
        pilot_experiment="Use Context7 on 10 repo questions involving fast-moving libraries or APIs and compare answer freshness versus current shell-plus-web lookup.",
        risk_note="Low security risk; main risk is treating vendor-curated docs as complete.",
        feasibility_note="Plugin-era Cursor already exists locally, so the main cost is install/auth rather than version gating.",
        workflow_classes=["research_intelligence", "repo_retrieval"],
        repo_fit="high",
        upgrade_magnitude="substantial",
        evidence_strength="high",
        security_risk="low",
        local_feasibility="needs_setup",
        why_it_matters="Context7 directly upgrades one of the clearest repo needs: current, version-specific documentation retrieval for research-first implementation and codebase work.",
    ),
    ("cursor_plugin", "Parallel"): PrioritySpec(
        tier="Tier A",
        rank=2,
        why_now="The repo already emphasizes pre-execution research, and Parallel adds a strong external research surface inside Cursor.",
        gap_filled="Structured deep research and content extraction remain external to the main Cursor loop.",
        complements="ResearchAgent and the project's context-locked research prompts.",
        pilot_experiment="Run the same literature-and-docs task with Parallel and the existing manual web path, then compare source breadth, citation quality, and time-to-brief.",
        risk_note="Moderate risk of overcollection or noisy research results if not scoped tightly.",
        feasibility_note="Usable on the current local Cursor baseline, but requires external service setup.",
        workflow_classes=["research_intelligence"],
        repo_fit="high",
        upgrade_magnitude="substantial",
        evidence_strength="medium_high",
        security_risk="medium",
        local_feasibility="needs_setup",
        why_it_matters="Parallel is the strongest marketplace-native fit for the repo's PhD research workflow: deep research, content extraction, and data enrichment inside the IDE.",
    ),
    ("external_server", "Playwright"): PrioritySpec(
        tier="Tier A",
        rank=3,
        why_now="The project is a browser- and GUI-heavy agent runtime; Playwright is the highest-signal external MCP augmentation for browser execution and testing.",
        gap_filled="Current browser control is local-macOS-first and Safari-centric. A parallel browser automation surface would add controllable, testable browser execution.",
        complements="web_primitives.py, VerificationGate, VisualMonitor, and the universal-agent path.",
        pilot_experiment="Add a sandboxed Playwright MCP config and compare one site task against the current local web path on determinism, observability, and failure recovery.",
        risk_note="Medium security risk because browser automation expands reachable surface area and requires clear sandbox discipline.",
        feasibility_note="Current local Cursor can use stdio MCP servers; this is a setup question, not a 2.6 feature gate.",
        workflow_classes=["execution_environment", "verification_evaluation"],
        repo_fit="high",
        upgrade_magnitude="substantial",
        evidence_strength="high",
        security_risk="medium",
        local_feasibility="needs_setup",
        why_it_matters="Playwright is the clearest non-marketplace external MCP that could materially strengthen browser automation, reproducible testing, and bounded web experiments.",
    ),
    ("cursor_plugin", "Langfuse"): PrioritySpec(
        tier="Tier A",
        rank=4,
        why_now="The repo already invests heavily in traces, summaries, evaluation, and run forensics; Langfuse matches that center of gravity directly.",
        gap_filled="There is no Cursor-native external tracing and prompt/eval surface woven into the current workflow.",
        complements="TraceWriter, Summarizer, BenchmarkEvaluator, and diagnostic artifacts.",
        pilot_experiment="Instrument a small set of research or planning tasks with Langfuse and compare whether prompt/version/run visibility improves postmortem quality.",
        risk_note="Low-to-medium risk; the main concern is export of sensitive run context to an external service.",
        feasibility_note="Usable on the current local baseline with plugin setup and Langfuse access.",
        workflow_classes=["observability_forensics", "verification_evaluation"],
        repo_fit="high",
        upgrade_magnitude="substantial",
        evidence_strength="medium_high",
        security_risk="medium",
        local_feasibility="needs_setup",
        why_it_matters="Langfuse is the best marketplace fit for externalizing trace, prompt, and evaluation visibility without inventing a new observability stack from scratch.",
    ),
    ("cursor_plugin", "Runlayer"): PrioritySpec(
        tier="Tier A",
        rank=5,
        why_now="If this repo adopts more MCPs, governance becomes a first-order concern rather than a later cleanup step.",
        gap_filled="Current repo security is strong inside the Python runtime, but there is no dedicated Cursor-side MCP governance and audit surface.",
        complements="security/sanitizer.py, CredentialVault, HostToolHealth, and HITL patterns.",
        pilot_experiment="Install Runlayer in a disposable environment and test whether it materially improves MCP discovery, auditability, secret handling, and policy visibility.",
        risk_note="Medium risk because it becomes part of the MCP control plane; its own trust boundary must be reviewed carefully.",
        feasibility_note="Usable on current Cursor with setup; no 2.6-only dependency is required for core value.",
        workflow_classes=["security_governance", "observability_forensics"],
        repo_fit="high",
        upgrade_magnitude="substantial",
        evidence_strength="medium_high",
        security_risk="medium",
        local_feasibility="needs_setup",
        why_it_matters="Runlayer is the strongest marketplace-native answer to the repo's next likely bottleneck: governing a larger MCP surface safely.",
    ),
    ("internal_opportunity", "concentric-trace-mcp"): PrioritySpec(
        tier="Tier A",
        rank=6,
        why_now="The repo already has rich traces; exposing them cleanly to Cursor would convert latent research assets into interactive workflow power.",
        gap_filled="Trace inspection is currently script- or file-driven rather than native to Cursor's MCP tool loop.",
        complements="TraceWriter, DiagnosticReader, DecisionDependenceAnalyzer, and HealingOrchestrator.",
        pilot_experiment="Prototype read_run_manifest, list_recent_runs, and summarize_failure_chain as MCP tools and compare debugging speed against file-only inspection.",
        risk_note="Low risk if read-only; medium if any mutation or redaction boundaries are weak.",
        feasibility_note="No local Cursor version blocker; requires building and registering the MCP server.",
        workflow_classes=["observability_forensics", "verification_evaluation"],
        repo_fit="high",
        upgrade_magnitude="transformational",
        evidence_strength="high",
        security_risk="low",
        local_feasibility="needs_setup",
        why_it_matters="This is the highest-value internal MCP because it exposes one of the repo's strongest native advantages directly to Cursor.",
    ),
    ("internal_opportunity", "concentric-benchmark-mcp"): PrioritySpec(
        tier="Tier A",
        rank=7,
        why_now="The project already contains benchmark and claims-based evaluation machinery; Cursor should be able to query and compare runs directly.",
        gap_filled="Evaluation remains too file-centric for rapid iterative decision-making in Cursor.",
        complements="BenchmarkEvaluator, TaskClaim, and benchmark artifacts.",
        pilot_experiment="Prototype evaluate_run and compare_runs MCP tools, then use them during one regression-analysis cycle.",
        risk_note="Low risk if tools are read-only and scoped to repo-local data.",
        feasibility_note="Requires server implementation, not a Cursor upgrade.",
        workflow_classes=["verification_evaluation", "observability_forensics"],
        repo_fit="high",
        upgrade_magnitude="transformational",
        evidence_strength="high",
        security_risk="low",
        local_feasibility="needs_setup",
        why_it_matters="This turns the repo's evaluation science into an interactive Cursor surface instead of a passive artifact set.",
    ),
    ("internal_opportunity", "concentric-health-mcp"): PrioritySpec(
        tier="Tier A",
        rank=8,
        why_now="Environment drift and tool-health regressions are already first-order failure modes in this project.",
        gap_filled="Host readiness and baseline drift checks are not available as a native Cursor tool surface.",
        complements="HostToolHealth, tool_health_catalog.json, and cursor_environment snapshotting.",
        pilot_experiment="Prototype health_summary, check_tool_class, and compare_environment_baselines MCP tools and use them before live runs.",
        risk_note="Low risk; the main concern is leaking unnecessary host detail into prompts or logs.",
        feasibility_note="Requires internal MCP implementation only.",
        workflow_classes=["security_governance", "execution_environment", "observability_forensics"],
        repo_fit="high",
        upgrade_magnitude="substantial",
        evidence_strength="high",
        security_risk="low",
        local_feasibility="needs_setup",
        why_it_matters="A health MCP would let Cursor reason about this machine's readiness before work, which aligns directly with the repo's environment-discipline path.",
    ),
    ("internal_opportunity", "concentric-research-mcp"): PrioritySpec(
        tier="Tier A",
        rank=9,
        why_now="ResearchAgent is already a differentiated internal capability; surfacing it via MCP would make it reusable from inside Cursor without bespoke wrappers.",
        gap_filled="Research briefs and source registers are generated in the repo but not exposed as a reusable tool surface to Cursor.",
        complements="ResearchAgent, ResearchBrief artifacts, and context-locked research prompts.",
        pilot_experiment="Prototype run_research_brief and fetch_research_context MCP tools for one complex pre-execution task.",
        risk_note="Low-to-medium risk depending on web-search scope and prompt-budget control.",
        feasibility_note="Needs implementation, but no local version gate.",
        workflow_classes=["research_intelligence", "artifact_generation"],
        repo_fit="high",
        upgrade_magnitude="substantial",
        evidence_strength="high",
        security_risk="low",
        local_feasibility="needs_setup",
        why_it_matters="This makes the repo's research-first method directly callable from Cursor, which is a meaningful PhD-level workflow lift rather than a cosmetic integration.",
    ),
    ("cursor_plugin", "Sentry"): PrioritySpec(
        tier="Tier B",
        rank=1,
        why_now="Strong fit for debugging and failure forensics, but slightly less central than traces/eval already native to the repo.",
        gap_filled="External error tracking and incident review.",
        complements="DiagnosticReader and failure-analysis artifacts.",
        pilot_experiment="Use Sentry on one failing integration or runtime incident and compare time-to-root-cause against current methods.",
        risk_note="External telemetry boundary must be reviewed.",
        feasibility_note="Usable on the current local Cursor baseline with setup.",
        workflow_classes=["observability_forensics"],
        repo_fit="medium_high",
        upgrade_magnitude="substantial",
        evidence_strength="medium_high",
        security_risk="medium",
        local_feasibility="needs_setup",
        why_it_matters="Sentry is a high-signal debugging surface, but it is not as directly aligned as trace or benchmark exposure.",
    ),
    ("external_server", "GitHub"): PrioritySpec(
        tier="Tier B",
        rank=2,
        why_now="Useful for PR/issues/review workflows, but the repo already has strong git and shell access.",
        gap_filled="Structured GitHub workflow actions inside MCP.",
        complements="git CLI and future review-loop automation.",
        pilot_experiment="Use GitHub MCP for one issue-to-branch-to-review loop and compare the clarity versus shell-only flow.",
        risk_note="Repository mutation risk requires scoped tokens and repo boundaries.",
        feasibility_note="Usable on the current local Cursor baseline with Docker/token setup.",
        workflow_classes=["repo_retrieval", "coordination_orchestration"],
        repo_fit="medium_high",
        upgrade_magnitude="moderate",
        evidence_strength="high",
        security_risk="medium",
        local_feasibility="needs_setup",
        why_it_matters="GitHub MCP helps with review and issue context, but it does not attack the repo's highest current bottlenecks first.",
    ),
    ("external_server", "Browserbase"): PrioritySpec(
        tier="Tier B",
        rank=3,
        why_now="This is a credible browser-compute augmentation, but Playwright is the cleaner first browser MCP pilot.",
        gap_filled="Hosted browser sessions for agents.",
        complements="Playwright-style browser automation and web task experiments.",
        pilot_experiment="Compare one Browserbase MCP flow against a Playwright MCP flow for setup cost and useful observability.",
        risk_note="External browser execution broadens the data-handling boundary.",
        feasibility_note="Usable on the current version with setup.",
        workflow_classes=["execution_environment"],
        repo_fit="medium_high",
        upgrade_magnitude="moderate",
        evidence_strength="high",
        security_risk="medium",
        local_feasibility="needs_setup",
        why_it_matters="Browserbase is promising, but it is a second browser pilot after the simpler Playwright path.",
    ),
    ("cursor_plugin", "Cursor Team Kit"): PrioritySpec(
        tier="Tier B",
        rank=4,
        why_now="Strong dev-loop automation ideas, but more valuable after the core research, trace, and health surfaces are in place.",
        gap_filled="CI, code review, and shipping workflow automation inside Cursor.",
        complements="Future code-review automation and shipping workflows.",
        pilot_experiment="Use Cursor Team Kit on one small code-review or CI-fix loop in a disposable branch.",
        risk_note="Potential overlap with project-specific workflow needs.",
        feasibility_note="Plugin-era feature; requires setup, not a 2.6-only surface.",
        workflow_classes=["coordination_orchestration", "verification_evaluation"],
        repo_fit="medium_high",
        upgrade_magnitude="moderate",
        evidence_strength="medium_high",
        security_risk="medium",
        local_feasibility="needs_setup",
        why_it_matters="This is a strong reference workflow, but the repo should first expose its own native strengths rather than adopt a generic shipping kit.",
    ),
    ("cursor_plugin", "Figma"): PrioritySpec(
        tier="Tier B",
        rank=5,
        why_now="Relevant for artifact generation and visual review, but its highest-value MCP Apps path depends on whether the local Cursor build is already on 2.6+.",
        gap_filled="Visual artifact and diagram collaboration inside Cursor.",
        complements="Reference-board and review-artifact work.",
        pilot_experiment="If local Cursor is already on 2.6+, test Figma MCP Apps output in one artifact-review task; otherwise upgrade first and run the same comparison.",
        risk_note="Low risk; the main issue is whether the workflow actually benefits from in-chat visual UI.",
        feasibility_note="The plugin exists now; MCP Apps value depends on the local Cursor version.",
        workflow_classes=["artifact_generation"],
        repo_fit="medium_high",
        upgrade_magnitude="moderate",
        evidence_strength="medium_high",
        security_risk="low",
        local_feasibility="needs_setup",
        why_it_matters="Figma becomes more interesting once local Cursor catches up to the 2.6 MCP Apps surface.",
    ),
    ("cursor_plugin", "tldraw"): PrioritySpec(
        tier="Tier B",
        rank=6,
        why_now="Same story as Figma: promising visual collaboration, but the highest-value MCP Apps path depends on whether the local Cursor build is already on 2.6+.",
        gap_filled="In-chat whiteboarding and visual planning.",
        complements="Reference boards and plan visualization.",
        pilot_experiment="If local Cursor is already on 2.6+, use tldraw MCP Apps for one planning or debugging whiteboard experiment; otherwise upgrade first.",
        risk_note="Low risk; main concern is whether it adds signal over existing reference-board artifacts.",
        feasibility_note="Its best experience depends on whether the local Cursor build is already on 2.6+.",
        workflow_classes=["artifact_generation"],
        repo_fit="medium_high",
        upgrade_magnitude="moderate",
        evidence_strength="medium_high",
        security_risk="low",
        local_feasibility="needs_setup",
        why_it_matters="tldraw could become useful for visual planning and review once MCP Apps are locally available.",
    ),
    ("cursor_plugin", "Amplitude"): PrioritySpec(
        tier="Tier B",
        rank=7,
        why_now="Interesting for artifact-rich chart analysis, but not first-order for this repo's current bottlenecks.",
        gap_filled="Interactive chart and dashboard review inside Cursor.",
        complements="Benchmark and run-analysis reporting.",
        pilot_experiment="If local Cursor is already on 2.6+, test one Amplitude MCP Apps chart-review flow; otherwise upgrade first.",
        risk_note="Low risk; limited by local version and workflow fit.",
        feasibility_note="Best MCP Apps value depends on whether the local Cursor build is already on 2.6+.",
        workflow_classes=["artifact_generation", "research_intelligence"],
        repo_fit="medium",
        upgrade_magnitude="moderate",
        evidence_strength="medium_high",
        security_risk="low",
        local_feasibility="needs_setup",
        why_it_matters="Useful later for evidence review, but not immediate.",
    ),
    ("cursor_plugin", "Atlassian"): PrioritySpec(
        tier="Tier B",
        rank=8,
        why_now="Good coordination surface, but valuable only if the workflow starts leaning harder into Jira/Confluence-based planning and triage.",
        gap_filled="Structured backlog and documentation coordination.",
        complements="Future team workflows, not the current single-repo research bottleneck.",
        pilot_experiment="Try Atlassian on one planning/triage loop if Jira/Confluence becomes active in the workflow.",
        risk_note="Medium risk due to access scope and data boundary.",
        feasibility_note="Usable on the current version with OAuth setup.",
        workflow_classes=["coordination_orchestration"],
        repo_fit="medium_high",
        upgrade_magnitude="moderate",
        evidence_strength="medium_high",
        security_risk="medium",
        local_feasibility="needs_setup",
        why_it_matters="Strong if team coordination becomes central, but not first-order today.",
    ),
    ("internal_opportunity", "concentric-visual-monitor-mcp"): PrioritySpec(
        tier="Tier B",
        rank=9,
        why_now="Valuable, but secondary to trace, benchmark, and health surfaces.",
        gap_filled="Cursor-native access to screenshot timelines and drift deltas.",
        complements="VisualMonitor and VerificationGate.",
        pilot_experiment="Expose last_n_timeline and compare_against_reference tools for one failure-analysis workflow.",
        risk_note="Careful screenshot redaction boundaries are required.",
        feasibility_note="Needs internal implementation only.",
        workflow_classes=["observability_forensics"],
        repo_fit="high",
        upgrade_magnitude="substantial",
        evidence_strength="high",
        security_risk="medium",
        local_feasibility="needs_setup",
        why_it_matters="Very useful, but a second wave after trace and health.",
    ),
    ("internal_opportunity", "concentric-skill-mcp"): PrioritySpec(
        tier="Tier B",
        rank=10,
        why_now="Skill retrieval is valuable, but it sits behind stronger immediate needs like traces and health.",
        gap_filled="Expose semantic skill retrieval and maturity-gated reuse to Cursor.",
        complements="SkillLibrary and SemanticSkillIndex.",
        pilot_experiment="Prototype retrieve_skills and inspect_skill MCP tools and compare planning quality on repeated task families.",
        risk_note="Low risk; main concern is surfacing stale or overtrusted skills.",
        feasibility_note="Needs internal implementation only.",
        workflow_classes=["repo_retrieval", "coordination_orchestration"],
        repo_fit="medium_high",
        upgrade_magnitude="moderate",
        evidence_strength="high",
        security_risk="low",
        local_feasibility="needs_setup",
        why_it_matters="Useful for reuse, but not the first internal MCP to build.",
    ),
}


def _materialize_priority_spec(spec: PrioritySpec, name: str, current_cursor_version: str) -> PrioritySpec:
    if name not in {"Figma", "tldraw", "Amplitude"}:
        return spec
    if _cursor_version_at_least(current_cursor_version, "2.6.0"):
        ready_notes = {
            "Figma": {
                "why_now": "Relevant for artifact generation and visual review, and the local Cursor build is now new enough to test the MCP Apps path directly.",
                "pilot_experiment": f"Use Figma MCP Apps output in one artifact-review task on local Cursor {current_cursor_version} and compare it with the existing screenshot/reference-board workflow.",
                "feasibility_note": f"Local Cursor {current_cursor_version} is new enough to test both the plugin and MCP Apps experience; remaining work is setup and Figma-side enablement.",
                "why_it_matters": "Figma is now directly testable as both a plugin and an MCP Apps surface for artifact review and design-informed workflows.",
            },
            "tldraw": {
                "why_now": "The local Cursor build is now new enough to test MCP Apps whiteboarding directly instead of treating it as a future-only surface.",
                "pilot_experiment": f"Use tldraw MCP Apps on local Cursor {current_cursor_version} for one planning or debugging whiteboard experiment and compare it with the current reference-board path.",
                "feasibility_note": f"Local Cursor {current_cursor_version} is new enough to test the MCP Apps experience directly; remaining work is plugin setup and workflow validation.",
                "why_it_matters": "tldraw is now directly testable as a local MCP Apps surface for visual planning and review.",
            },
            "Amplitude": {
                "why_now": "The local Cursor build is now new enough to test MCP Apps chart review directly rather than treating it as version-blocked.",
                "pilot_experiment": f"Test one Amplitude MCP Apps chart-review flow on local Cursor {current_cursor_version} and see whether it improves evidence review over current artifacts.",
                "feasibility_note": f"Local Cursor {current_cursor_version} is new enough to test the MCP Apps path directly; remaining work is plugin setup and validating workflow fit.",
                "why_it_matters": "Amplitude is now directly testable as an MCP Apps evidence-review surface, though it remains secondary for this repo.",
            },
        }[name]
        return dataclasses.replace(
            spec,
            why_now=ready_notes["why_now"],
            pilot_experiment=ready_notes["pilot_experiment"],
            feasibility_note=ready_notes["feasibility_note"],
            why_it_matters=ready_notes["why_it_matters"],
            local_feasibility="needs_setup",
        )

    blocked_notes = {
        "Figma": {
            "why_now": "Relevant for artifact generation and visual review, but the highest-value interactive MCP Apps path is gated by local version mismatch.",
            "pilot_experiment": "Upgrade a local Cursor install to 2.6+, then test Figma MCP Apps output in one artifact-review task.",
            "feasibility_note": "The plugin exists, but the local Cursor baseline blocks the new 2.6 MCP Apps experience.",
            "why_it_matters": "Figma becomes more interesting once local Cursor catches up to the 2.6 MCP Apps surface.",
        },
        "tldraw": {
            "why_now": "Same story as Figma: promising visual collaboration, but a pre-2.6 local build reduces immediate value.",
            "pilot_experiment": "After a local Cursor upgrade to 2.6+, use tldraw MCP Apps for one planning or debugging whiteboard experiment.",
            "feasibility_note": "Blocked from its best experience by the current local Cursor baseline.",
            "why_it_matters": "tldraw could become useful for visual planning and review once MCP Apps are locally available.",
        },
        "Amplitude": {
            "why_now": "Interesting for artifact-rich chart analysis, but its best MCP Apps value is gated by the current local version.",
            "pilot_experiment": "After a local Cursor upgrade to 2.6+, test one Amplitude MCP Apps chart-review flow for whether it improves evidence review.",
            "feasibility_note": "Best MCP Apps value is blocked locally by the current version mismatch.",
            "why_it_matters": "Useful later for evidence review, but not immediate.",
        },
    }[name]
    return dataclasses.replace(
        spec,
        why_now=blocked_notes["why_now"],
        pilot_experiment=blocked_notes["pilot_experiment"],
        feasibility_note=blocked_notes["feasibility_note"],
        why_it_matters=blocked_notes["why_it_matters"],
        local_feasibility="blocked_by_cursor_version",
    )


INTERNAL_OPPORTUNITIES: list[dict[str, Any]] = [
    {
        "candidate_id": "INT-MCP-001",
        "name": "concentric-trace-mcp",
        "problem_filled": "Expose run manifests, traces, and causal failure summaries directly inside Cursor instead of requiring file-by-file inspection.",
        "repo_modules_exposed": [
            "operator/agent_infra/trace_writer.py",
            "operator/agent_infra/diagnostic_reader.py",
            "operator/agent_infra/decision_graph.py",
            "operator/agent_infra/healing_orchestrator.py",
        ],
        "tool_surface": [
            "list_recent_runs",
            "read_run_manifest",
            "full_diagnostic",
            "summarize_failure_chain",
        ],
        "target_user": "researcher",
        "expected_upgrade": "transformational",
        "build_complexity": "medium",
        "security_notes": "Keep the surface read-only by default and redact any credentials or sensitive payloads before tool return.",
        "why_cursor_mcp": "This converts one of the repo's strongest native assets into an interactive Cursor tool loop.",
        "prototype_priority": "immediate",
    },
    {
        "candidate_id": "INT-MCP-002",
        "name": "concentric-benchmark-mcp",
        "problem_filled": "Expose claims-based evaluation, run scoring, and regression comparison directly inside Cursor.",
        "repo_modules_exposed": [
            "operator/agent_infra/benchmark_evaluator.py",
        ],
        "tool_surface": [
            "evaluate_run",
            "compare_runs",
            "get_aggregate_report",
            "list_registered_claims",
        ],
        "target_user": "researcher",
        "expected_upgrade": "transformational",
        "build_complexity": "medium",
        "security_notes": "Read-only by default; keep any run metadata scoped to the repo and avoid leaking unrelated local paths.",
        "why_cursor_mcp": "The repo already has benchmark science; MCP would make it a live reasoning surface rather than a passive artifact.",
        "prototype_priority": "immediate",
    },
    {
        "candidate_id": "INT-MCP-003",
        "name": "concentric-research-mcp",
        "problem_filled": "Expose research briefs, source registers, and pre-execution method/tool mappings as reusable Cursor tools.",
        "repo_modules_exposed": [
            "operator/agent_infra/research_agent.py",
            "operator/agent_infra/summarizer.py",
        ],
        "tool_surface": [
            "run_research_brief",
            "get_research_context",
            "list_reference_images",
            "summarize_research_artifact",
        ],
        "target_user": "researcher",
        "expected_upgrade": "substantial",
        "build_complexity": "medium",
        "security_notes": "Scope outbound research carefully and keep prompt budgets explicit to avoid uncontrolled web retrieval.",
        "why_cursor_mcp": "This preserves the repo's research-first method inside Cursor instead of duplicating it manually.",
        "prototype_priority": "immediate",
    },
    {
        "candidate_id": "INT-MCP-004",
        "name": "concentric-health-mcp",
        "problem_filled": "Expose host-tool readiness, environment drift, and baseline status before live tasks begin.",
        "repo_modules_exposed": [
            "operator/agent_infra/host_tool_health.py",
            "operator/agent_infra/tool_health_catalog.json",
            "operator/cre/tools/cursor_environment_snapshot.py",
        ],
        "tool_surface": [
            "health_summary",
            "check_tool_class",
            "compare_environment_baselines",
            "explain_unhealthy_capability",
        ],
        "target_user": "operator",
        "expected_upgrade": "substantial",
        "build_complexity": "low",
        "security_notes": "Avoid exposing unnecessary host details; return readiness judgments and narrow diagnostics, not raw environment dumps by default.",
        "why_cursor_mcp": "This gives Cursor an explicit environment model for a project where environment readiness is a first-order concern.",
        "prototype_priority": "immediate",
    },
    {
        "candidate_id": "INT-MCP-005",
        "name": "concentric-skill-mcp",
        "problem_filled": "Expose semantic skill retrieval and maturity-gated reuse inside Cursor.",
        "repo_modules_exposed": [
            "operator/agent_infra/skill_library.py",
        ],
        "tool_surface": [
            "retrieve_skills",
            "get_skill_summary",
            "inspect_skill",
            "find_master_skills",
        ],
        "target_user": "operator",
        "expected_upgrade": "substantial",
        "build_complexity": "low",
        "security_notes": "Read-only exposure is safest; write-paths should remain opt-in and separately reviewed.",
        "why_cursor_mcp": "This turns the repo's episodic and semantic reuse layer into a native planning aid inside Cursor.",
        "prototype_priority": "high",
    },
    {
        "candidate_id": "INT-MCP-006",
        "name": "concentric-visual-monitor-mcp",
        "problem_filled": "Expose screenshot timelines, reference comparisons, and drift alerts to Cursor.",
        "repo_modules_exposed": [
            "operator/agent_infra/visual_monitor.py",
            "operator/agent_infra/verification_gate.py",
        ],
        "tool_surface": [
            "last_n_timeline",
            "compare_against_reference",
            "latest_snapshot_metadata",
            "describe_recent_drift",
        ],
        "target_user": "reviewer",
        "expected_upgrade": "substantial",
        "build_complexity": "medium",
        "security_notes": "Screenshots are sensitive; require explicit workspace scoping and make storage/retention visible.",
        "why_cursor_mcp": "The repo already has a temporal visual-memory subsystem that would become much more useful if Cursor could query it directly.",
        "prototype_priority": "high",
    },
]


PRIMARY_SOURCES: list[dict[str, Any]] = [
    {
        "source_id": "SRC-01",
        "title": "Model Context Protocol (MCP) | Cursor Docs",
        "url": CURSOR_MCP_DOCS_URL,
        "source_class": "official_docs_page",
        "published_date": None,
        "retrieved_date": RETRIEVED_DATE,
        "why_relevant": "Canonical Cursor source for MCP transport support, config locations, OAuth notes, MCP Apps, and the built-in MCP server directory.",
        "claims_supported": [
            "CAP-01", "CAP-02", "CAP-03", "CAP-04", "external:Playwright", "external:GitHub", "external:Context7",
        ],
    },
    {
        "source_id": "SRC-02",
        "title": "Plugins | Cursor Docs",
        "url": CURSOR_PLUGINS_DOCS_URL,
        "source_class": "official_docs_page",
        "published_date": None,
        "retrieved_date": RETRIEVED_DATE,
        "why_relevant": "Canonical Cursor source for plugin packaging, marketplace behavior, team marketplaces, and security review claims.",
        "claims_supported": [
            "CAP-05", "CAP-06", "plugin:Context7", "plugin:Runlayer", "plugin:Langfuse", "plugin:1Password",
        ],
    },
    {
        "source_id": "SRC-03",
        "title": "MCP Apps and Team Marketplaces for Plugins",
        "url": CURSOR_CHANGELOG_26_URL,
        "source_class": "official_changelog_entry",
        "published_date": "2026-03-03",
        "retrieved_date": RETRIEVED_DATE,
        "why_relevant": "Primary release note for Cursor 2.6 additions including MCP Apps and team marketplaces.",
        "claims_supported": ["CAP-06", "plugin:Figma", "plugin:tldraw", "plugin:Amplitude"],
    },
    {
        "source_id": "SRC-04",
        "title": "Cursor 2.5",
        "url": CURSOR_25_BLOG_URL,
        "source_class": "official_blog_post",
        "published_date": "2026-02-17",
        "retrieved_date": RETRIEVED_DATE,
        "why_relevant": "Primary source that plugins already existed before 2.6; critical for separating plugin support from newer 2.6-only surfaces.",
        "claims_supported": ["CAP-05", "LOCAL-01"],
    },
    {
        "source_id": "SRC-05",
        "title": "Cursor Marketplace",
        "url": CURSOR_MARKETPLACE_URL,
        "source_class": "official_marketplace",
        "published_date": None,
        "retrieved_date": RETRIEVED_DATE,
        "why_relevant": "Official Cursor directory for marketplace plugins and their current descriptions.",
        "claims_supported": [
            "plugin:Context7", "plugin:Parallel", "plugin:Runlayer", "plugin:Langfuse", "plugin:1Password",
            "plugin:Sentry", "plugin:Cursor Team Kit", "plugin:Figma", "plugin:tldraw", "plugin:Amplitude",
        ],
    },
    {
        "source_id": "SRC-06",
        "title": "MCP Apps extension overview",
        "url": MCP_APPS_OVERVIEW_URL,
        "source_class": "official_protocol_docs",
        "published_date": None,
        "retrieved_date": RETRIEVED_DATE,
        "why_relevant": "Protocol-level definition of MCP Apps that Cursor references for interactive UI support.",
        "claims_supported": ["CAP-06"],
    },
    {
        "source_id": "SRC-07",
        "title": "GitHub MCP Server",
        "url": "https://github.com/github/github-mcp-server",
        "source_class": "official_github_repo",
        "published_date": None,
        "retrieved_date": RETRIEVED_DATE,
        "why_relevant": "Canonical upstream repository for the GitHub MCP server referenced by Cursor docs.",
        "claims_supported": ["external:GitHub"],
    },
    {
        "source_id": "SRC-08",
        "title": "microsoft/playwright-mcp",
        "url": "https://github.com/microsoft/playwright-mcp",
        "source_class": "official_github_repo",
        "published_date": None,
        "retrieved_date": RETRIEVED_DATE,
        "why_relevant": "Canonical upstream repository for the Playwright MCP server used as the main browser-augmentation candidate.",
        "claims_supported": ["external:Playwright"],
    },
    {
        "source_id": "SRC-09",
        "title": "Langfuse Docs",
        "url": "https://langfuse.com/docs",
        "source_class": "official_provider_docs",
        "published_date": None,
        "retrieved_date": RETRIEVED_DATE,
        "why_relevant": "Canonical provider docs for Langfuse tracing and evaluation capabilities.",
        "claims_supported": ["plugin:Langfuse"],
    },
    {
        "source_id": "SRC-10",
        "title": "Parallel Docs",
        "url": "https://docs.parallel.ai/home",
        "source_class": "official_provider_docs",
        "published_date": None,
        "retrieved_date": RETRIEVED_DATE,
        "why_relevant": "Canonical provider docs for Parallel's research and extraction platform.",
        "claims_supported": ["plugin:Parallel"],
    },
    {
        "source_id": "SRC-11",
        "title": "Runlayer Docs",
        "url": "https://docs.runlayer.com/",
        "source_class": "official_provider_docs",
        "published_date": None,
        "retrieved_date": RETRIEVED_DATE,
        "why_relevant": "Canonical provider docs for Runlayer's MCP management and governance product.",
        "claims_supported": ["plugin:Runlayer"],
    },
    {
        "source_id": "SRC-12",
        "title": "Context7",
        "url": "https://context7.com/",
        "source_class": "official_provider_docs",
        "published_date": None,
        "retrieved_date": RETRIEVED_DATE,
        "why_relevant": "Canonical provider home for Context7, which Cursor exposes directly in both docs and marketplace surfaces.",
        "claims_supported": ["plugin:Context7", "external:Context7"],
    },
    {
        "source_id": "SRC-13",
        "title": "1Password Developer Docs",
        "url": "https://developer.1password.com/",
        "source_class": "official_provider_docs",
        "published_date": None,
        "retrieved_date": RETRIEVED_DATE,
        "why_relevant": "Canonical 1Password developer source for secret and auth tooling context.",
        "claims_supported": ["plugin:1Password"],
    },
    {
        "source_id": "SRC-14",
        "title": "Sentry Docs",
        "url": "https://docs.sentry.io/",
        "source_class": "official_provider_docs",
        "published_date": None,
        "retrieved_date": RETRIEVED_DATE,
        "why_relevant": "Canonical provider docs for Sentry error tracking and monitoring.",
        "claims_supported": ["plugin:Sentry", "external:Sentry"],
    },
]


def _candidate_key(kind: str, name: str) -> tuple[str, str]:
    return kind, _normalize_name(name)


def _build_docs_candidates(
    docs_servers: list[dict[str, Any]],
    current_cursor_version: str,
) -> list[dict[str, Any]]:
    catalog: list[dict[str, Any]] = []
    for idx, item in enumerate(docs_servers, start=1):
        name = item["name"]
        classes = _workflow_classes_for_text(name, item["description"])
        repo_fit = _repo_fit_from_classes(classes, name, item["description"])
        upgrade_magnitude = _upgrade_magnitude(repo_fit, classes, name)
        local_feasibility = _local_feasibility(
            kind="external_server",
            name=name,
            description=item["description"],
            current_cursor_version=current_cursor_version,
        )
        redundancy = _redundancy_with_repo(name, item["description"])
        entry = {
            "candidate_id": f"MCP-{idx:03d}",
            "name": name,
            "kind": "external_server",
            "provider": name,
            "canonical_url": item["docs"] if item.get("docs") not in {None, "$undefined"} else CURSOR_MCP_DOCS_URL,
            "repo_url": item["docs"] if isinstance(item.get("docs"), str) and "github.com" in item["docs"] else None,
            "cursor_install_path": "mcp_json",
            "cursor_support_basis": {"status": "verified", "sources": ["SRC-01"]},
            "transport": _transport_list(item.get("transport")),
            "auth_mode": _auth_mode_from_docs_item(item),
            "mcp_apps_support": "unknown",
            "team_shareability": "unknown",
            "workflow_classes": classes,
            "repo_fit": repo_fit,
            "upgrade_magnitude": upgrade_magnitude,
            "evidence_strength": _evidence_strength("external_server"),
            "local_feasibility": local_feasibility,
            "security_risk": _security_risk(name, item["description"]),
            "redundancy_with_repo": redundancy,
            "why_it_matters": _default_why_it_matters(name, item["description"], classes),
            "why_not_priority": _default_why_not_priority(repo_fit, redundancy, local_feasibility),
            "recommended_status": "catalog_only",
            "recommended_experiment": _recommended_experiment(name, classes),
            "raw_install": item.get("install"),
            "raw_docs_entry_index": item.get("index"),
        }
        scores = _score_candidate(
            workflow_classes=classes,
            repo_fit=repo_fit,
            upgrade_magnitude=upgrade_magnitude,
            evidence_strength=entry["evidence_strength"],
            security_risk=entry["security_risk"],
            local_feasibility=local_feasibility,
            redundancy=redundancy,
        )
        entry["scores"] = scores
        catalog.append(entry)
    return catalog


def _build_marketplace_candidates(
    plugins: list[dict[str, str]],
    docs_lookup: dict[str, dict[str, Any]],
    current_cursor_version: str,
    starting_index: int,
) -> list[dict[str, Any]]:
    catalog: list[dict[str, Any]] = []
    for offset, plugin in enumerate(plugins, start=starting_index):
        name = plugin["name"]
        matching_docs = docs_lookup.get(name)
        description = plugin["description"]
        classes = _workflow_classes_for_text(name, description)
        repo_fit = _repo_fit_from_classes(classes, name, description)
        upgrade_magnitude = _upgrade_magnitude(repo_fit, classes, name)
        local_feasibility = _local_feasibility(
            kind="cursor_plugin",
            name=name,
            description=description,
            current_cursor_version=current_cursor_version,
        )
        redundancy = _redundancy_with_repo(name, description)
        transport = _transport_list(matching_docs.get("transport")) if matching_docs else []
        entry = {
            "candidate_id": f"MCP-{offset:03d}",
            "name": name,
            "kind": "cursor_plugin",
            "provider": name,
            "canonical_url": CURSOR_MARKETPLACE_URL,
            "repo_url": matching_docs.get("docs") if matching_docs and isinstance(matching_docs.get("docs"), str) and "github.com" in matching_docs.get("docs") else None,
            "cursor_install_path": "marketplace",
            "cursor_support_basis": {"status": "verified", "sources": ["SRC-02", "SRC-05"]},
            "transport": transport,
            "auth_mode": _auth_mode_from_plugin(name, description, matching_docs),
            "mcp_apps_support": "yes" if name in {"Amplitude", "Figma", "tldraw"} else "unknown",
            "team_shareability": "yes",
            "workflow_classes": classes,
            "repo_fit": repo_fit,
            "upgrade_magnitude": upgrade_magnitude,
            "evidence_strength": _evidence_strength("cursor_plugin"),
            "local_feasibility": local_feasibility,
            "security_risk": _security_risk(name, description),
            "redundancy_with_repo": redundancy,
            "why_it_matters": _default_why_it_matters(name, description, classes),
            "why_not_priority": _default_why_not_priority(repo_fit, redundancy, local_feasibility),
            "recommended_status": "catalog_only",
            "recommended_experiment": _recommended_experiment(name, classes),
            "marketplace_description": description,
        }
        scores = _score_candidate(
            workflow_classes=classes,
            repo_fit=repo_fit,
            upgrade_magnitude=upgrade_magnitude,
            evidence_strength=entry["evidence_strength"],
            security_risk=entry["security_risk"],
            local_feasibility=local_feasibility,
            redundancy=redundancy,
        )
        entry["scores"] = scores
        catalog.append(entry)
    return catalog


def _build_internal_candidates(starting_index: int, current_cursor_version: str) -> list[dict[str, Any]]:
    catalog: list[dict[str, Any]] = []
    mapping = {
        "concentric-trace-mcp": ["observability_forensics", "verification_evaluation"],
        "concentric-benchmark-mcp": ["verification_evaluation", "observability_forensics"],
        "concentric-research-mcp": ["research_intelligence", "artifact_generation"],
        "concentric-health-mcp": ["execution_environment", "security_governance", "observability_forensics"],
        "concentric-skill-mcp": ["repo_retrieval", "coordination_orchestration"],
        "concentric-visual-monitor-mcp": ["observability_forensics"],
    }
    for offset, item in enumerate(INTERNAL_OPPORTUNITIES, start=starting_index):
        classes = mapping[item["name"]]
        repo_fit = "high" if item["expected_upgrade"] in {"substantial", "transformational"} else "medium_high"
        local_feasibility = _local_feasibility(
            kind="internal_opportunity",
            name=item["name"],
            description=item["problem_filled"],
            current_cursor_version=current_cursor_version,
        )
        entry = {
            "candidate_id": f"MCP-{offset:03d}",
            "name": item["name"],
            "kind": "internal_opportunity",
            "provider": "concentric_study",
            "canonical_url": str(CRE_DIR),
            "repo_url": None,
            "cursor_install_path": "mcp_json",
            "cursor_support_basis": {"status": "supported_but_inferred", "sources": ["SRC-01"]},
            "transport": ["stdio"],
            "auth_mode": ["none"],
            "mcp_apps_support": "no",
            "team_shareability": "yes",
            "workflow_classes": classes,
            "repo_fit": repo_fit,
            "upgrade_magnitude": item["expected_upgrade"],
            "evidence_strength": "high",
            "local_feasibility": local_feasibility,
            "security_risk": "low" if item["name"] != "concentric-visual-monitor-mcp" else "medium",
            "redundancy_with_repo": "none",
            "why_it_matters": item["why_cursor_mcp"],
            "why_not_priority": None,
            "recommended_status": "catalog_only",
            "recommended_experiment": f"Prototype {', '.join(item['tool_surface'][:2])} and compare usability against the current file/script path.",
            "internal_source": item["candidate_id"],
        }
        scores = _score_candidate(
            workflow_classes=classes,
            repo_fit=repo_fit,
            upgrade_magnitude=item["expected_upgrade"],
            evidence_strength="high",
            security_risk=entry["security_risk"],
            local_feasibility=local_feasibility,
            redundancy="none",
        )
        entry["scores"] = scores
        catalog.append(entry)
    return catalog


def _apply_manual_priority(
    catalog: list[dict[str, Any]],
    current_cursor_version: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    lookup = {_candidate_key(entry["kind"], entry["name"]): entry for entry in catalog}
    tier_a: list[dict[str, Any]] = []
    tier_b: list[dict[str, Any]] = []

    for key, base_spec in MANUAL_PRIORITY.items():
        entry = lookup[key]
        spec = _materialize_priority_spec(base_spec, entry["name"], current_cursor_version)
        entry["workflow_classes"] = spec.workflow_classes
        entry["repo_fit"] = spec.repo_fit
        entry["upgrade_magnitude"] = spec.upgrade_magnitude
        entry["evidence_strength"] = spec.evidence_strength
        entry["security_risk"] = spec.security_risk
        entry["local_feasibility"] = spec.local_feasibility
        entry["why_it_matters"] = spec.why_it_matters
        entry["why_not_priority"] = None
        entry["recommended_status"] = "priority" if spec.tier == "Tier A" else "pilot"
        entry["recommended_experiment"] = spec.pilot_experiment
        entry["priority_tier"] = spec.tier
        entry["priority_rank"] = spec.rank
        entry["priority_notes"] = {
            "why_now": spec.why_now,
            "gap_filled": spec.gap_filled,
            "complements_or_supersedes": spec.complements,
            "pilot_experiment": spec.pilot_experiment,
            "risk_note": spec.risk_note,
            "feasibility_note": spec.feasibility_note,
        }
        entry["scores"] = _score_candidate(
            workflow_classes=spec.workflow_classes,
            repo_fit=spec.repo_fit,
            upgrade_magnitude=spec.upgrade_magnitude,
            evidence_strength=spec.evidence_strength,
            security_risk=spec.security_risk,
            local_feasibility=spec.local_feasibility,
            redundancy=entry["redundancy_with_repo"],
        )
        if spec.tier == "Tier A":
            tier_a.append(entry)
        else:
            tier_b.append(entry)

    tier_a.sort(key=lambda item: item["priority_rank"])
    tier_b.sort(key=lambda item: item["priority_rank"])

    for entry in catalog:
        if "priority_tier" not in entry:
            if entry["kind"] == "internal_opportunity":
                entry["why_not_priority"] = entry["why_not_priority"] or "listed in the internal opportunity file but not promoted above stronger internal MCPs yet"
            elif entry["security_risk"] == "high":
                entry["recommended_status"] = "exclude"
                entry["why_not_priority"] = entry["why_not_priority"] or "security risk is too high for immediate adoption"
            else:
                entry["recommended_status"] = "catalog_only"
                entry["why_not_priority"] = entry["why_not_priority"] or "credible and Cursor-compatible, but outranked by higher-leverage candidates for this repo"

    tier_keys = {_candidate_key(item["kind"], item["name"]) for item in tier_a + tier_b}
    tier_c = [entry for entry in catalog if _candidate_key(entry["kind"], entry["name"]) not in tier_keys]
    tier_c.sort(key=lambda item: (-item["scores"]["priority_score"], item["name"]))
    return tier_a, tier_b, tier_c


def _build_workflow_gaps() -> list[dict[str, Any]]:
    return [
        {
            "gap_id": "GAP-01",
            "name": "Current documentation and repo retrieval inside Cursor",
            "why_it_exists": "The repo already values research-first implementation, but current repo and doc lookup still rely heavily on shell search plus manual browsing.",
            "local_evidence": [str(LOCAL_WORKFLOW_VALUE_PATH), str(LOCAL_PHD_PRACTICE_PATH)],
            "desired_workflow_classes": ["research_intelligence", "repo_retrieval"],
        },
        {
            "gap_id": "GAP-02",
            "name": "Browser augmentation beyond the local Safari/macOS path",
            "why_it_exists": "The runtime is strong on local macOS control, but a bounded external browser/testing surface could improve reproducibility and experiments.",
            "local_evidence": [str(LOCAL_ENV_BENEFITS_PATH), str(LOCAL_MASTER_TOOL_LIST_PATH)],
            "desired_workflow_classes": ["execution_environment", "verification_evaluation"],
        },
        {
            "gap_id": "GAP-03",
            "name": "Cursor-native observability and evaluation access",
            "why_it_exists": "The repo has strong traces and evaluation artifacts, but they are not exposed as native Cursor tools.",
            "local_evidence": [str(LOCAL_WORKFLOW_VALUE_PATH), str(LOCAL_MASTER_TOOL_LIST_PATH)],
            "desired_workflow_classes": ["observability_forensics", "verification_evaluation"],
        },
        {
            "gap_id": "GAP-04",
            "name": "MCP governance and secret discipline",
            "why_it_exists": "Adopting more MCPs introduces governance, audit, and secret-handling pressure not covered by install convenience alone.",
            "local_evidence": [str(LOCAL_ENV_BENEFITS_PATH), str(LOCAL_TOOL_HEALTH_PATH)],
            "desired_workflow_classes": ["security_governance", "observability_forensics"],
        },
        {
            "gap_id": "GAP-05",
            "name": "Visual artifact and review surfaces inside Cursor",
            "why_it_exists": "The repo values screenshots, reference boards, and visual evidence, but current Cursor integration is version-gated for MCP Apps.",
            "local_evidence": [str(LOCAL_WORKFLOW_VALUE_PATH)],
            "desired_workflow_classes": ["artifact_generation"],
        },
    ]


def _build_workflow_matrix(catalog: list[dict[str, Any]], gaps: list[dict[str, Any]]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for entry in catalog:
        matched_gaps = [
            gap["gap_id"]
            for gap in gaps
            if set(entry["workflow_classes"]) & set(gap["desired_workflow_classes"])
        ]
        rows.append({
            "candidate_id": entry["candidate_id"],
            "name": entry["name"],
            "kind": entry["kind"],
            "workflow_classes": entry["workflow_classes"],
            "matched_gaps": matched_gaps,
            "current_repo_assets": _repo_assets_for_candidate(entry),
            "scores": entry["scores"],
            "repo_fit": entry["repo_fit"],
            "upgrade_magnitude": entry["upgrade_magnitude"],
            "local_feasibility": entry["local_feasibility"],
            "recommended_status": entry["recommended_status"],
        })
    return {
        "retrieved_date": RETRIEVED_DATE,
        "current_repo_gaps": gaps,
        "candidate_rows": rows,
    }


def _repo_assets_for_candidate(entry: dict[str, Any]) -> list[str]:
    assets: list[str] = []
    classes = set(entry["workflow_classes"])
    if "research_intelligence" in classes:
        assets.append("ResearchAgent")
    if "repo_retrieval" in classes:
        assets.append("SkillLibrary / SemanticSkillIndex")
    if "execution_environment" in classes:
        assets.append("web_primitives.py / capability_router.py")
    if "observability_forensics" in classes:
        assets.append("TraceWriter / DiagnosticReader / VisualMonitor")
    if "verification_evaluation" in classes:
        assets.append("VerificationGate / BenchmarkEvaluator")
    if "security_governance" in classes:
        assets.append("InputSanitizer / CredentialVault / HostToolHealth")
    if "artifact_generation" in classes:
        assets.append("reference boards / run artifacts")
    if "coordination_orchestration" in classes:
        assets.append("OuterLoop / RulesStore / ReflectionJournal")
    return assets


def _build_prioritized_backlog(
    tier_a: list[dict[str, Any]],
    tier_b: list[dict[str, Any]],
    tier_c: list[dict[str, Any]],
) -> dict[str, Any]:
    def _entry_summary(entry: dict[str, Any]) -> dict[str, Any]:
        notes = entry.get("priority_notes", {})
        return {
            "candidate_id": entry["candidate_id"],
            "name": entry["name"],
            "kind": entry["kind"],
            "priority_rank": entry.get("priority_rank"),
            "why_now": notes.get("why_now"),
            "gap_filled": notes.get("gap_filled"),
            "complements_or_supersedes": notes.get("complements_or_supersedes"),
            "pilot_experiment": notes.get("pilot_experiment"),
            "risk_note": notes.get("risk_note"),
            "feasibility_note": notes.get("feasibility_note"),
            "workflow_classes": entry["workflow_classes"],
            "repo_fit": entry["repo_fit"],
            "upgrade_magnitude": entry["upgrade_magnitude"],
            "local_feasibility": entry["local_feasibility"],
        }

    return {
        "retrieved_date": RETRIEVED_DATE,
        "tier_a": [_entry_summary(entry) for entry in tier_a],
        "tier_b": [_entry_summary(entry) for entry in tier_b],
        "tier_c_summary": {
            "count": len(tier_c),
            "top_examples": [
                {
                    "candidate_id": entry["candidate_id"],
                    "name": entry["name"],
                    "kind": entry["kind"],
                    "recommended_status": entry["recommended_status"],
                    "why_not_priority": entry["why_not_priority"],
                }
                for entry in tier_c[:25]
            ],
        },
    }


def _build_local_feasibility(
    *,
    current_cursor_env: dict[str, Any],
    tier_a: list[dict[str, Any]],
) -> dict[str, Any]:
    current_cursor_version = current_cursor_env["app"]["version"]["value"]
    has_mcp_apps_locally = _cursor_version_at_least(current_cursor_version, "2.6.0")
    return {
        "retrieved_date": RETRIEVED_DATE,
        "local_cursor": {
            "version": current_cursor_version,
            "bundle_version": current_cursor_env["app"]["bundle_version"]["value"],
            "build_date": current_cursor_env["app"]["build_date"]["value"],
            "host_os": current_cursor_env["host"]["os"]["value"],
            "host_os_version": current_cursor_env["host"]["os_version"]["value"],
            "architecture": current_cursor_env["host"]["architecture"]["value"],
        },
        "platform_feature_gates": [
            {
                "feature": "Plugins",
                "platform_status": "verified in Cursor 2.5 official blog and current docs",
                "local_status": f"available on local Cursor {current_cursor_version}",
                "risk": "install/setup and auth, not version gating",
            },
            {
                "feature": "MCP Apps",
                "platform_status": "officially announced in Cursor 2.6 changelog on 2026-03-03",
                "local_status": (
                    f"available on local Cursor {current_cursor_version}"
                    if has_mcp_apps_locally
                    else f"blocked by local Cursor {current_cursor_version} unless the app is upgraded to 2.6+"
                ),
                "risk": "plugin can exist without full interactive UI value",
            },
            {
                "feature": "Team Marketplaces",
                "platform_status": "officially documented and announced for Teams/Enterprise",
                "local_status": (
                    f"local app is new enough on Cursor {current_cursor_version}, but still requires eligible plan/admin controls"
                    if has_mcp_apps_locally
                    else "requires both newer surface and eligible plan/admin controls"
                ),
                "risk": "not an immediate local single-user gain",
            },
            {
                "feature": "mcp.json server registration",
                "platform_status": "officially documented in current Cursor MCP docs",
                "local_status": "available now with setup",
                "risk": "local auth, tool trust, and policy review still required",
            },
        ],
        "tier_a_candidates": [
            {
                "candidate_id": entry["candidate_id"],
                "name": entry["name"],
                "kind": entry["kind"],
                "requires_cursor_2_6_plus": entry["local_feasibility"] == "blocked_by_cursor_version",
                "usable_on_local_cursor": entry["local_feasibility"] != "blocked_by_cursor_version",
                "blocked_pending_upgrade": entry["local_feasibility"] == "blocked_by_cursor_version",
                "requires_oauth": "oauth" in entry["auth_mode"],
                "needs_api_key_or_local_daemon": any(mode in entry["auth_mode"] for mode in ["api_key", "other"]),
                "requires_team_or_enterprise_surface": entry["name"] in {"Cursor Team Kit"},
                "security_risk": entry["security_risk"],
                "safe_default_mode": "read-only first" if entry["kind"] == "internal_opportunity" else "sandboxed pilot",
                "notes": entry.get("priority_notes", {}).get("feasibility_note", ""),
            }
            for entry in tier_a
        ],
    }


def _render_markdown(
    *,
    current_cursor_env: dict[str, Any],
    docs_candidates: list[dict[str, Any]],
    marketplace_candidates: list[dict[str, Any]],
    internal_candidates: list[dict[str, Any]],
    tier_a: list[dict[str, Any]],
    tier_b: list[dict[str, Any]],
    tier_c: list[dict[str, Any]],
) -> str:
    external_candidates = docs_candidates + marketplace_candidates
    current_cursor_version = current_cursor_env["app"]["version"]["value"]
    has_mcp_apps_locally = _cursor_version_at_least(current_cursor_version, "2.6.0")
    external_kind_counts = Counter(entry["kind"] for entry in external_candidates)
    workflow_counts = Counter()
    for entry in external_candidates + internal_candidates:
        workflow_counts.update(entry["workflow_classes"])

    lines: list[str] = [
        "# Cursor MCP Landscape (PhD)",
        "",
        "## 1. Executive Summary",
        "",
        f"This memo evaluates which MCPs are implementable in Cursor as of **{RETRIEVED_DATE}**, which of them materially improve the `concentric_study` workflow, and which internal MCPs should be built next.",
        "",
        "Main conclusions:",
        f"- The official Cursor MCP docs inventory currently exposes **{len(docs_candidates)}** server surfaces.",
        f"- The official Cursor marketplace currently exposes **{len(marketplace_candidates)}** unique plugin surfaces.",
        f"- Total external install surfaces cataloged: **{len(external_candidates)}**.",
        f"- Internal MCP opportunities cataloged: **{len(internal_candidates)}**.",
        "- The strongest immediate external upgrades are current-doc retrieval, deep research, browser augmentation, MCP governance, and trace/eval observability.",
        "- The strongest medium-term upgrades are internal MCPs that expose the repo's own trace, benchmark, health, and research machinery inside Cursor.",
        "",
        "## 2. Context and Exact Environment",
        "",
        f"- Repo method baseline: `{LOCAL_PHD_PRACTICE_PATH}`.",
        f"- Local Cursor baseline from `{LOCAL_CURSOR_ENV_PATH}`:",
        f"  - Version: `{current_cursor_env['app']['version']['value']}`",
        f"  - Build date: `{current_cursor_env['app']['build_date']['value']}`",
        f"  - Host: `{current_cursor_env['host']['os']['value']} {current_cursor_env['host']['os_version']['value']}` on `{current_cursor_env['host']['architecture']['value']}`",
        f"- Local tool-health basis: `{LOCAL_TOOL_HEALTH_PATH}`.",
        "- Workflow reality: this is not a generic IDE repo. It is a macOS visual-web-agent system with strong emphasis on research, browser execution, traces, security, verification, and evaluation.",
        "",
        "## 3. Official Cursor MCP Capability Baseline",
        "",
        f"- Cursor's MCP docs (`SRC-01`) document support for `stdio`, `SSE`, and `Streamable HTTP` transports via MCP.",
        f"- Cursor's MCP docs (`SRC-01`) document both project-level `.cursor/mcp.json` and global `~/.cursor/mcp.json` registration.",
        f"- Cursor's MCP docs (`SRC-01`) document one-click server installation from Cursor's collection plus OAuth-aware flows.",
        f"- Cursor's plugins docs (`SRC-02`) state that plugins package rules, skills, agents, commands, MCP servers, and hooks, and that they work across the IDE, CLI, and Cloud.",
        f"- Cursor's March 3, 2026 changelog (`SRC-03`) adds MCP Apps and team plugin marketplaces as explicit 2.6-era surfaces.",
        (
            f"- Local state: this machine is on Cursor `{current_cursor_version}`, so the 2.6-era MCP Apps surface is locally testable."
            if has_mcp_apps_locally
            else f"- Local caveat: this machine is on Cursor `{current_cursor_version}`, so the platform supports more than this machine currently exposes."
        ),
        "",
        "Interpretation:",
        "- Cursor-level MCP support is real and broad now.",
        (
            "- Local availability still depends on plan/admin controls and setup, but the app version no longer blocks 2.6-era MCP Apps testing."
            if has_mcp_apps_locally
            else "- Local availability is narrower than platform capability because the local app version lags the March 3, 2026 release surface."
        ),
        "",
        "## 4. Method and Source Policy",
        "",
        "Evidence ladder used:",
        "- Tier 1: official Cursor docs, official Cursor changelog, official Cursor blog, official Cursor marketplace, official provider docs, official upstream GitHub repos.",
        "- Tier 2: none relied on for priority recommendations unless the official source was incomplete.",
        "",
        "Collection method:",
        f"- Parse the official Cursor MCP docs inventory from `{CURSOR_MCP_DOCS_URL}`.",
        f"- Parse the official Cursor marketplace inventory from `{CURSOR_MARKETPLACE_URL}`.",
        "- Map candidates to repo workflow classes using the current repo's own PhD memos and tool inventory.",
        "- Keep marketplace plugins and direct MCP server entries separate when they represent materially different install surfaces.",
        "",
        "## 5. Exhaustive Catalog Overview",
        "",
        "Catalog counts by install surface:",
        f"- `external_server`: {external_kind_counts['external_server']}",
        f"- `cursor_plugin`: {external_kind_counts['cursor_plugin']}",
        f"- `internal_opportunity`: {len(internal_candidates)}",
        "",
        "Workflow coverage counts across the full catalog:",
    ]

    for key, value in sorted(workflow_counts.items()):
        lines.append(f"- `{key}`: {value}")

    lines.extend([
        "",
        "Interpretation:",
        "- Cursor's official ecosystem is already broad enough that the main problem is no longer discovery alone.",
        "- The real research question is selection: which MCPs strengthen this repo's actual workflow rather than merely adding surface area.",
        "",
        "## 6. Workflow-Fit Analysis for `concentric_study`",
        "",
        f"Current repo evidence from `{LOCAL_WORKFLOW_VALUE_PATH}`, `{LOCAL_ENV_BENEFITS_PATH}`, and `{LOCAL_MASTER_TOOL_LIST_PATH}` points to these highest-value upgrade zones:",
        "- current documentation and repository retrieval",
        "- bounded browser augmentation beyond the local Safari path",
        "- Cursor-native observability and evaluation access",
        "- MCP governance, audit, and secret discipline",
        (
            "- visual artifact/review surfaces, now that the local Cursor build includes the 2.6-era MCP Apps surface"
            if has_mcp_apps_locally
            else "- visual artifact/review surfaces once the local Cursor version catches up"
        ),
        "",
        "This means the most valuable MCPs are not generic productivity wrappers. The best fits are the ones that increase research quality, reduce diagnosis latency, or expose existing repo-native strengths inside Cursor.",
        "",
        "## 7. Highest-Upside External MCPs",
        "",
    ])

    for entry in tier_a:
        if entry["kind"] == "internal_opportunity":
            continue
        notes = entry["priority_notes"]
        lines.extend([
            f"### {entry['priority_rank']}. {entry['name']} ({entry['kind']})",
            f"- Why it matters: {entry['why_it_matters']}",
            f"- Why now: {notes['why_now']}",
            f"- Gap filled: {notes['gap_filled']}",
            f"- Complements/supersedes: {notes['complements_or_supersedes']}",
            f"- Pilot: {notes['pilot_experiment']}",
            f"- Risk: {notes['risk_note']}",
            f"- Local feasibility: {notes['feasibility_note']}",
            "",
        ])

    lines.extend([
        "## 8. Highest-Upside Internal MCPs",
        "",
    ])

    for entry in tier_a:
        if entry["kind"] != "internal_opportunity":
            continue
        notes = entry["priority_notes"]
        lines.extend([
            f"### {entry['priority_rank']}. {entry['name']}",
            f"- Why it matters: {entry['why_it_matters']}",
            f"- Why now: {notes['why_now']}",
            f"- Gap filled: {notes['gap_filled']}",
            f"- Complements/supersedes: {notes['complements_or_supersedes']}",
            f"- Pilot: {notes['pilot_experiment']}",
            f"- Risk: {notes['risk_note']}",
            f"- Local feasibility: {notes['feasibility_note']}",
            "",
        ])

    lines.extend([
        "## 9. Local Feasibility on This Machine",
        "",
        f"- Current local Cursor baseline: `{current_cursor_version}`.",
        (
            "- Immediate conclusion: both plugin-era MCP adoption and the 2.6 MCP Apps surface are locally testable now."
            if has_mcp_apps_locally
            else "- Immediate conclusion: plugin-era MCP adoption is plausible now, but the full 2.6 MCP Apps surface is not locally available until Cursor is upgraded."
        ),
        "",
        "Local gates:",
        "- `mcp.json` servers: available now with setup.",
        "- Marketplace plugins: available now.",
        (
            "- MCP Apps: platform-supported in 2.6 and locally available on this machine."
            if has_mcp_apps_locally
            else "- MCP Apps: platform-supported in 2.6, locally blocked until upgrade."
        ),
        "- Team marketplaces: also require plan/admin surfaces beyond a single local install.",
        "",
        "## 10. Risks, Limitations, and Unknowns",
        "",
        "- Cursor docs and marketplace pages are live product surfaces, not archived snapshots, so this memo captures a dated retrieval rather than a permanent historical freeze.",
        "- The marketplace exposes plugin descriptions cleanly but not all underlying transport/auth details; when available, those were filled from Cursor's MCP docs inventory.",
        (
            f"- Local feasibility is separated from platform support because even on Cursor {current_cursor_version}, plan/admin controls and per-server setup still matter."
            if has_mcp_apps_locally
            else f"- Local feasibility is separated from platform support because the machine is on Cursor {current_cursor_version} while the relevant changelog surface is already at 2.6."
        ),
        "- Some MCPs are credible but low-fit for this repo because they optimize shipping or SaaS operations rather than visual-agent research workflows.",
        "",
        "## 11. Recommended Adoption Order",
        "",
        "### Tier A — Highest-Upside Pilots",
    ])

    for entry in tier_a:
        lines.append(f"- `{entry['priority_rank']}`. `{entry['name']}` ({entry['kind']})")

    lines.extend([
        "",
        "### Tier B — Strong but Non-Immediate",
    ])
    for entry in tier_b:
        lines.append(f"- `{entry['priority_rank']}`. `{entry['name']}` ({entry['kind']})")

    lines.extend([
        "",
        "### Tier C — Real but Lower-Leverage for This Repo",
        f"- Count: `{len(tier_c)}`",
        "- These are worth cataloging for completeness, but they do not currently beat the Tier A/Tier B items on repo fit, upgrade magnitude, or local readiness.",
        "",
        "## 12. Appendix: Evidence and Inventory Snapshot",
        "",
        "Primary sources used:",
    ])

    for source in PRIMARY_SOURCES:
        published = source["published_date"] or "undated"
        lines.append(f"- `{source['source_id']}`: [{source['title']}]({source['url']}) — published `{published}`, retrieved `{source['retrieved_date']}`")

    lines.extend([
        "",
        "Top Tier C examples:",
    ])

    for entry in tier_c[:15]:
        lines.append(f"- `{entry['name']}` ({entry['kind']}): {entry['why_not_priority']}")

    lines.append("")
    return "\n".join(lines)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n")


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "candidate_id",
        "name",
        "kind",
        "provider",
        "canonical_url",
        "repo_url",
        "cursor_install_path",
        "transport",
        "auth_mode",
        "mcp_apps_support",
        "team_shareability",
        "workflow_classes",
        "repo_fit",
        "upgrade_magnitude",
        "evidence_strength",
        "local_feasibility",
        "security_risk",
        "redundancy_with_repo",
        "recommended_status",
        "priority_score",
        "phd_upgrade_score",
        "time_to_value",
        "why_it_matters",
        "why_not_priority",
        "recommended_experiment",
    ]
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            scores = row["scores"]
            writer.writerow({
                "candidate_id": row["candidate_id"],
                "name": row["name"],
                "kind": row["kind"],
                "provider": row["provider"],
                "canonical_url": row["canonical_url"],
                "repo_url": row["repo_url"],
                "cursor_install_path": row["cursor_install_path"],
                "transport": "|".join(row["transport"]),
                "auth_mode": "|".join(row["auth_mode"]),
                "mcp_apps_support": row["mcp_apps_support"],
                "team_shareability": row["team_shareability"],
                "workflow_classes": "|".join(row["workflow_classes"]),
                "repo_fit": row["repo_fit"],
                "upgrade_magnitude": row["upgrade_magnitude"],
                "evidence_strength": row["evidence_strength"],
                "local_feasibility": row["local_feasibility"],
                "security_risk": row["security_risk"],
                "redundancy_with_repo": row["redundancy_with_repo"],
                "recommended_status": row["recommended_status"],
                "priority_score": scores["priority_score"],
                "phd_upgrade_score": scores["phd_upgrade_score"],
                "time_to_value": scores["time_to_value"],
                "why_it_matters": row["why_it_matters"],
                "why_not_priority": row["why_not_priority"],
                "recommended_experiment": row["recommended_experiment"],
            })


def _validate_outputs(
    catalog: list[dict[str, Any]],
    tier_a: list[dict[str, Any]],
    memo_path: Path,
) -> None:
    if len(catalog) < 100:
        raise RuntimeError("Catalog is too small; expected a materially broad MCP surface.")
    if not tier_a:
        raise RuntimeError("Tier A is empty.")
    for entry in tier_a:
        if not entry["cursor_support_basis"]["sources"] and entry["kind"] != "internal_opportunity":
            raise RuntimeError(f"Prioritized candidate {entry['name']} has no source basis.")
    memo_text = memo_path.read_text()
    for phrase in [
        "Official Cursor MCP Capability Baseline",
        "Local Feasibility on This Machine",
        "Recommended Adoption Order",
    ]:
        if phrase not in memo_text:
            raise RuntimeError(f"Memo missing required section: {phrase}")


def main() -> int:
    current_cursor_env = _load_json(LOCAL_CURSOR_ENV_PATH)
    current_cursor_version = current_cursor_env["app"]["version"]["value"]

    docs_html = _fetch_text(CURSOR_MCP_DOCS_URL)
    marketplace_html = _fetch_text(CURSOR_MARKETPLACE_URL)

    docs_servers = _extract_docs_servers(docs_html)
    marketplace_plugins = _extract_marketplace_plugins(marketplace_html)
    docs_lookup = {item["name"]: item for item in docs_servers}

    docs_candidates = _build_docs_candidates(docs_servers, current_cursor_version)
    marketplace_candidates = _build_marketplace_candidates(
        marketplace_plugins,
        docs_lookup,
        current_cursor_version,
        starting_index=len(docs_candidates) + 1,
    )
    internal_candidates = _build_internal_candidates(
        starting_index=len(docs_candidates) + len(marketplace_candidates) + 1,
        current_cursor_version=current_cursor_version,
    )

    catalog = docs_candidates + marketplace_candidates + internal_candidates
    tier_a, tier_b, tier_c = _apply_manual_priority(catalog, current_cursor_version)

    workflow_matrix = _build_workflow_matrix(catalog, _build_workflow_gaps())
    prioritized_backlog = _build_prioritized_backlog(tier_a, tier_b, tier_c)
    local_feasibility = _build_local_feasibility(
        current_cursor_env=current_cursor_env,
        tier_a=tier_a,
    )

    sources_path = ARTIFACTS_DIR / "cursor_mcp_primary_sources.json"
    catalog_json_path = ARTIFACTS_DIR / "cursor_mcp_catalog.json"
    catalog_csv_path = ARTIFACTS_DIR / "cursor_mcp_catalog.csv"
    workflow_matrix_path = ARTIFACTS_DIR / "cursor_mcp_workflow_matrix.json"
    prioritized_backlog_path = ARTIFACTS_DIR / "cursor_mcp_prioritized_backlog.json"
    internal_opportunities_path = ARTIFACTS_DIR / "cursor_mcp_internal_opportunities.json"
    local_feasibility_path = ARTIFACTS_DIR / "cursor_mcp_local_feasibility.json"
    memo_path = CRE_DIR / "CURSOR_MCP_LANDSCAPE_PHD.md"

    _write_json(sources_path, PRIMARY_SOURCES)
    _write_json(catalog_json_path, catalog)
    _write_csv(catalog_csv_path, catalog)
    _write_json(workflow_matrix_path, workflow_matrix)
    _write_json(prioritized_backlog_path, prioritized_backlog)
    _write_json(internal_opportunities_path, INTERNAL_OPPORTUNITIES)
    _write_json(local_feasibility_path, local_feasibility)
    memo_path.write_text(_render_markdown(
        current_cursor_env=current_cursor_env,
        docs_candidates=docs_candidates,
        marketplace_candidates=marketplace_candidates,
        internal_candidates=internal_candidates,
        tier_a=tier_a,
        tier_b=tier_b,
        tier_c=tier_c,
    ))

    _validate_outputs(catalog, tier_a, memo_path)

    print(f"[cursor-mcp] docs_servers={len(docs_servers)} marketplace_plugins={len(marketplace_plugins)} total_catalog={len(catalog)}")
    print(f"[cursor-mcp] wrote={sources_path}")
    print(f"[cursor-mcp] wrote={catalog_json_path}")
    print(f"[cursor-mcp] wrote={catalog_csv_path}")
    print(f"[cursor-mcp] wrote={workflow_matrix_path}")
    print(f"[cursor-mcp] wrote={prioritized_backlog_path}")
    print(f"[cursor-mcp] wrote={internal_opportunities_path}")
    print(f"[cursor-mcp] wrote={local_feasibility_path}")
    print(f"[cursor-mcp] wrote={memo_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
