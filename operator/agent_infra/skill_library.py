"""Skill Library: verified success storage with maturity gating.

Implements the core skill library pattern from Voyager (Wang et al., NeurIPS 2023):
successful execution traces are stored as reusable, semantically indexed "skills"
that the agent can retrieve for future tasks. This eliminates plan regeneration
for known tasks and provides few-shot exemplars for novel tasks.

Design decisions backed by PhD research:
1. MATURITY GATING (ASG-SI, arXiv:2512.23760): Skills must accumulate N verified
   successes before being promoted to "proven" status. SkillsBench (arXiv:2602.12670)
   showed self-generated skills without verification can *hurt* performance — 16/84
   tasks degraded. We require evidence-backed promotion only.

2. SEMANTIC RETRIEVAL — dual-layer strategy:
   a) PRIMARY: Dense vector similarity via sentence-transformers when available.
      RAG-MCP (arXiv:2505.03275, Gan & Sun 2025) demonstrated that semantic
      retrieval reduces prompt tokens by 50% and improves tool selection accuracy
      from 13.62% to 43.13%. Sentence-BERT (arXiv:1908.10084, EMNLP 2019)
      outperforms TF-IDF by 11-15% Spearman on STS benchmark tasks.
   b) FALLBACK: TF-IDF + cosine similarity (AgentRec, arXiv:2501.13333 showed
      92.2% top-1 accuracy without GPU embeddings). Zero external dependencies.

3. POISONING PREVENTION (CRADLE security analysis, arXiv:2602.14211): 26.1% of
   community skills contain vulnerabilities. Our library only ingests skills from
   our own verified traces — no external skill marketplace. Each skill records
   its full provenance (run_id, timestamp, manifest hash) for auditability.

4. SKILL SCHEMA follows Voyager's (code, description, dependencies) pattern
   adapted for GUI agents: (action_plan, task_description, verification_evidence,
   performance_metrics).

Build-order: Phase 5 depends on Phase 1 (TraceWriter) for trace data and Phase 2
(DiagnosticReader) for reading trace contents. The Skill Library feeds into
Phase 6 (Automatic Curriculum) which uses skill mastery to determine difficulty
progression.
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
import re
import time
from collections import Counter
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class SkillRecord:
    """A single stored skill derived from a successful execution trace.

    Provenance fields enable full auditability: every skill can be traced
    back to the exact run that produced it, following ASG-SI's verifier-backed
    replay requirement.

    Memory decay fields (Gap 5):
    - last_validated_at: ISO timestamp of the most recent successful execution.
      Skills not re-validated within STALENESS_HOURS are demoted, following
      ACT-R's base-level activation decay (Anderson et al., 2004, Psychological
      Review, "An Integrated Theory of the Mind") and AriGraph's temporal
      validity windows (arXiv:2407.10457).
    - ui_fingerprint_hash: pHash of a representative UI region at the time of
      last validation. Detects distribution shift (Zauner, 2010; GUI-Actor,
      NeurIPS 2025, arXiv:2506.03143).
    """

    __slots__ = (
        "skill_id", "task_id", "task_description", "action_plan",
        "performance", "provenance", "maturity", "created_at", "updated_at",
        "last_validated_at", "ui_fingerprint_hash",
    )

    STALENESS_HOURS: float = 24.0

    def __init__(
        self,
        skill_id: str,
        task_id: str,
        task_description: str,
        action_plan: list[dict[str, Any]],
        performance: dict[str, Any],
        provenance: dict[str, Any],
    ) -> None:
        self.skill_id = skill_id
        self.task_id = task_id
        self.task_description = task_description
        self.action_plan = action_plan
        self.performance = performance
        self.provenance = provenance
        self.maturity = SkillMaturity()
        self.created_at = _iso_now()
        self.updated_at = self.created_at
        self.last_validated_at: str = self.created_at
        self.ui_fingerprint_hash: str | None = None

    def is_stale(self) -> bool:
        """Check if the skill needs revalidation.

        Uses a fixed staleness window (ACT-R base-level decay simplified
        to a step function). A more nuanced version would use the full
        B_i = ln(Σ t_j^{-d}) decay equation, but for a per-task library
        the step function is sufficient and interpretable.
        """
        try:
            import calendar
            validated_str = self.last_validated_at or self.updated_at
            parsed = time.strptime(validated_str[:19], "%Y-%m-%dT%H:%M:%S")
            validated_ts = calendar.timegm(parsed)  # UTC-aware conversion
            age_hours = (time.time() - validated_ts) / 3600
            return age_hours > self.STALENESS_HOURS
        except (ValueError, TypeError):
            return True  # unparseable timestamp → treat as stale

    def validate_fingerprint(self, current_hash: str | None, tolerance: float = 0.15) -> bool:
        """Check if the UI fingerprint matches the stored one.

        Returns True if:
        - No stored fingerprint (legacy skill — backward compatible)
        - No current hash provided (fingerprint unavailable)
        - pHash distance < tolerance

        Returns False if UI has drifted beyond tolerance (Zauner 2010).
        """
        if not self.ui_fingerprint_hash or not current_hash:
            return True
        try:
            import imagehash
            stored = imagehash.hex_to_hash(self.ui_fingerprint_hash)
            current = imagehash.hex_to_hash(current_hash)
            distance = (stored - current) / stored.hash.size
            return distance < tolerance
        except Exception:
            return True

    def touch_validation(self, ui_hash: str | None = None) -> None:
        """Mark the skill as freshly validated and optionally update the UI fingerprint."""
        self.last_validated_at = _iso_now()
        if ui_hash:
            self.ui_fingerprint_hash = ui_hash

    def to_dict(self) -> dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "task_id": self.task_id,
            "task_description": self.task_description,
            "action_plan": self.action_plan,
            "performance": self.performance,
            "provenance": self.provenance,
            "maturity": self.maturity.to_dict(),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_validated_at": self.last_validated_at,
            "ui_fingerprint_hash": self.ui_fingerprint_hash,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "SkillRecord":
        record = cls(
            skill_id=d["skill_id"],
            task_id=d["task_id"],
            task_description=d["task_description"],
            action_plan=d["action_plan"],
            performance=d["performance"],
            provenance=d["provenance"],
        )
        record.maturity = SkillMaturity.from_dict(d.get("maturity", {}))
        record.created_at = d.get("created_at", record.created_at)
        record.updated_at = d.get("updated_at", record.updated_at)
        record.last_validated_at = d.get("last_validated_at", record.updated_at)
        record.ui_fingerprint_hash = d.get("ui_fingerprint_hash")
        return record


class SkillMaturity:
    """Maturity tracking with evidence-backed promotion.

    Tier system (inspired by ASG-SI's gate-based promotion):
    - candidate: 1 verified success. Stored but not yet trusted for autonomous reuse.
    - proven:    N verified successes (default 3). Safe for autonomous retrieval.
    - master:    M verified successes (default 5) with no failures. Eligible for
                 teaching (few-shot exemplar for novel tasks).

    SkillsBench showed that premature skill reuse can degrade performance.
    The maturity threshold prevents this by requiring repeated verification.
    """

    TIERS = ("candidate", "proven", "master")
    PROVEN_THRESHOLD = 3
    MASTER_THRESHOLD = 5

    __slots__ = ("tier", "success_count", "failure_count", "evidence_run_ids")

    def __init__(self) -> None:
        self.tier: str = "candidate"
        self.success_count: int = 1
        self.failure_count: int = 0
        self.evidence_run_ids: list[str] = []

    def record_success(self, run_id: str) -> str:
        """Record a verified success and return the new tier."""
        self.success_count += 1
        if run_id not in self.evidence_run_ids:
            self.evidence_run_ids.append(run_id)
        return self._evaluate_tier()

    def record_failure(self, run_id: str) -> str:
        """Record a failure — demotes master back to proven."""
        self.failure_count += 1
        if self.tier == "master":
            self.tier = "proven"
        return self.tier

    def _evaluate_tier(self) -> str:
        if self.success_count >= self.MASTER_THRESHOLD and self.failure_count == 0:
            self.tier = "master"
        elif self.success_count >= self.PROVEN_THRESHOLD:
            self.tier = "proven"
        else:
            self.tier = "candidate"
        return self.tier

    def to_dict(self) -> dict[str, Any]:
        return {
            "tier": self.tier,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "evidence_run_ids": list(self.evidence_run_ids),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "SkillMaturity":
        m = cls()
        m.tier = d.get("tier", "candidate")
        m.success_count = d.get("success_count", 1)
        m.failure_count = d.get("failure_count", 0)
        m.evidence_run_ids = list(d.get("evidence_run_ids", []))
        return m


class SkillLibrary:
    """Persistent skill library with semantic retrieval and maturity gating.

    Storage: JSON file at `<output_dir>/skill_library.json`. Each skill is
    keyed by task_id for exact-match lookup and indexed by TF-IDF vectors
    for semantic similarity retrieval.

    Retrieval strategy (following AgentRec's lightweight approach):
    1. Exact match on task_id — O(1), perfect precision
    2. TF-IDF cosine similarity on task_description — O(n), no GPU required
    """

    def __init__(self, library_dir: str | Path) -> None:
        self._library_dir = Path(library_dir)
        self._library_dir.mkdir(parents=True, exist_ok=True)
        self._library_path = self._library_dir / "skill_library.json"
        self._skills: dict[str, SkillRecord] = {}
        self._semantic_index = SemanticSkillIndex()
        self._load()
        self._rebuild_semantic_index()

    @property
    def library_path(self) -> Path:
        return self._library_path

    def _load(self) -> None:
        if self._library_path.exists():
            try:
                with open(self._library_path, encoding="utf-8") as f:
                    data = json.load(f)
                for skill_dict in data.get("skills", []):
                    record = SkillRecord.from_dict(skill_dict)
                    self._skills[record.task_id] = record
            except (json.JSONDecodeError, KeyError):
                self._skills = {}

    def _save(self) -> None:
        data = {
            "version": 1,
            "updated_at": _iso_now(),
            "num_skills": len(self._skills),
            "skills": [s.to_dict() for s in self._skills.values()],
        }
        with open(self._library_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

    def ingest_from_trace(self, run_dir: str | Path) -> SkillRecord | None:
        """Ingest a successful run trace as a new or updated skill.

        Only ingests runs with outcome="success". Failed runs are rejected
        to prevent poisoning (CRADLE security principle).

        Returns the SkillRecord if ingested, None if rejected.
        """
        run_dir = Path(run_dir)
        manifest_path = run_dir / "manifest.json"
        trace_path = run_dir / "trace.jsonl"

        if not manifest_path.exists() or not trace_path.exists():
            return None

        with open(manifest_path, encoding="utf-8") as f:
            manifest = json.load(f)

        if manifest.get("outcome") != "success":
            return None

        task_id = manifest.get("task_id", "")
        if not task_id:
            return None

        action_plan = self._extract_action_plan(trace_path)
        performance = {
            "total_duration_ms": manifest.get("total_duration_ms", 0),
            "num_steps": manifest.get("num_steps", 0),
            "success_rate": 1.0,
        }
        provenance = {
            "run_id": manifest.get("run_id", ""),
            "timestamp": manifest.get("start_time", ""),
            "manifest_hash": _hash_file(manifest_path),
            "trace_hash": _hash_file(trace_path),
            "agent_config": manifest.get("agent_config", {}),
            "environment": manifest.get("environment", {}),
        }

        existing = self._skills.get(task_id)
        if existing:
            old_tier = existing.maturity.tier
            new_tier = existing.maturity.record_success(manifest.get("run_id", ""))

            old_has_coords = any(s.get("resolved_coords") for s in existing.action_plan)
            new_has_coords = any(s.get("resolved_coords") for s in action_plan)
            is_faster = performance["total_duration_ms"] < existing.performance.get("total_duration_ms", float("inf"))
            coords_upgrade = new_has_coords and not old_has_coords

            if is_faster or coords_upgrade:
                existing.action_plan = action_plan
                if is_faster:
                    existing.performance = performance
                    existing.provenance = provenance

            existing.updated_at = _iso_now()
            existing.touch_validation()
            self._save()
            return existing

        skill_id = _generate_skill_id(task_id)
        record = SkillRecord(
            skill_id=skill_id,
            task_id=task_id,
            task_description=manifest.get("task_description", ""),
            action_plan=action_plan,
            performance=performance,
            provenance=provenance,
        )
        record.maturity.evidence_run_ids.append(manifest.get("run_id", ""))

        self._skills[task_id] = record
        self._semantic_index.index_skill(
            task_id, manifest.get("task_description", "")
        )
        self._save()
        return record

    def record_failure(self, task_id: str, run_id: str) -> str | None:
        """Record a failed run against an existing skill. Returns new tier or None."""
        skill = self._skills.get(task_id)
        if not skill:
            return None
        new_tier = skill.maturity.record_failure(run_id)
        skill.updated_at = _iso_now()
        self._save()
        return new_tier

    def retrieve_exact(self, task_id: str) -> SkillRecord | None:
        """O(1) exact-match retrieval by task_id."""
        return self._skills.get(task_id)

    def retrieve_proven(self, task_id: str) -> SkillRecord | None:
        """Retrieve a skill only if it has reached 'proven' or 'master' tier.

        This is the primary retrieval method for autonomous reuse.
        Candidate-tier skills are not returned — they haven't been
        verified enough times (SkillsBench: premature reuse degrades performance).
        """
        skill = self._skills.get(task_id)
        if skill and skill.maturity.tier in ("proven", "master"):
            return skill
        return None

    def retrieve_by_similarity(self, query: str, top_k: int = 3, min_score: float = 0.1) -> list[tuple[SkillRecord, float]]:
        """Semantic similarity retrieval over task descriptions.

        Dual-layer strategy following RAG-MCP (arXiv:2505.03275):
        1. Try dense vector similarity via sentence-transformers
           (bridges the lexical gap: "nested triangles" ↔ "concentric shapes")
        2. Fall back to TF-IDF cosine similarity if embeddings unavailable
           (AgentRec: 92.2% top-1 accuracy, zero dependencies)
        """
        if not self._skills:
            return []

        # Layer 1: Dense semantic retrieval (RAG-MCP pattern)
        if self._semantic_index.available and self._semantic_index.indexed_count > 0:
            semantic_hits = self._semantic_index.query(
                query, top_k=top_k, min_score=min_score
            )
            results: list[tuple[SkillRecord, float]] = []
            for task_id, score in semantic_hits:
                skill = self._skills.get(task_id)
                if skill:
                    results.append((skill, score))
            if results:
                return results

        # Layer 2: TF-IDF fallback (AgentRec lightweight approach)
        return self._retrieve_by_tfidf(query, top_k=top_k, min_score=min_score)

    def _retrieve_by_tfidf(self, query: str, top_k: int = 3, min_score: float = 0.1) -> list[tuple[SkillRecord, float]]:
        """TF-IDF cosine similarity retrieval (fallback layer)."""
        corpus = []
        skill_list = []
        for skill in self._skills.values():
            corpus.append(skill.task_description)
            skill_list.append(skill)

        corpus.append(query)

        tfidf_matrix = _compute_tfidf(corpus)
        query_vec = tfidf_matrix[-1]

        scored: list[tuple[SkillRecord, float]] = []
        for i, skill in enumerate(skill_list):
            sim = _cosine_similarity(query_vec, tfidf_matrix[i])
            if sim >= min_score:
                scored.append((skill, sim))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    def _rebuild_semantic_index(self) -> None:
        """Populate the semantic index from all loaded skills."""
        if not self._semantic_index.available:
            return
        for skill in self._skills.values():
            if skill.task_description:
                self._semantic_index.index_skill(
                    skill.task_id, skill.task_description
                )

    def retrieve_by_tool(self, action_type: str) -> list[SkillRecord]:
        """Retrieve skills whose action plans use a specific action type.

        Enables Recon-Act-style tool archive (arXiv:2509.21072): skills
        are indexed by the tools they employ, enabling cross-task transfer.
        """
        results = []
        for skill in self._skills.values():
            for step_entry in skill.action_plan:
                action = step_entry.get("action", {})
                atype = action.get("type", "") if isinstance(action, dict) else str(action)
                if atype == action_type:
                    results.append(skill)
                    break
        return results

    def get_all_skills(self) -> list[SkillRecord]:
        return list(self._skills.values())

    def get_skill_count(self) -> int:
        return len(self._skills)

    def get_summary(self) -> str:
        """Human-readable summary of the skill library."""
        if not self._skills:
            return "Skill Library: empty (no skills stored)"

        lines = [
            f"=== SKILL LIBRARY ({len(self._skills)} skills) ===",
            "",
        ]
        for skill in self._skills.values():
            m = skill.maturity
            lines.append(
                f"  [{m.tier.upper():9s}] {skill.task_id}"
                f" | {m.success_count} successes, {m.failure_count} failures"
                f" | best time: {skill.performance.get('total_duration_ms', 0) / 1000:.1f}s"
                f" | {len(skill.action_plan)} steps"
            )
        return "\n".join(lines)

    def _extract_action_plan(self, trace_path: Path) -> list[dict[str, Any]]:
        """Extract the action sequence from a trace JSONL file.

        Stores essential fields for replay: action type, parameters, thought,
        and resolved_coords when available (for coordinate cache replay,
        following ViReSkill's skill memory pattern, arXiv:2509.24219).
        """
        plan: list[dict[str, Any]] = []
        with open(trace_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                step = json.loads(line)
                entry: dict[str, Any] = {
                    "step": step.get("step"),
                    "action": step.get("action", {}),
                    "thought": step.get("thought", ""),
                    "duration_ms": step.get("duration_ms", 0),
                }
                resolved = step.get("post_state", {}).get("resolved_coords")
                if resolved:
                    entry["resolved_coords"] = resolved
                plan.append(entry)
        return plan


# ---------------------------------------------------------------------------
# TF-IDF + Cosine Similarity (lightweight, no external dependencies)
# ---------------------------------------------------------------------------

def _tokenize(text: str) -> list[str]:
    """Simple whitespace + punctuation tokenizer with lowercasing."""
    return re.findall(r"[a-z0-9]+", text.lower())


def _compute_tfidf(corpus: list[str]) -> list[dict[str, float]]:
    """Compute TF-IDF vectors for a corpus of documents.

    Returns a list of {term: tfidf_weight} dicts, one per document.
    """
    n_docs = len(corpus)
    tokenized = [_tokenize(doc) for doc in corpus]

    df: Counter[str] = Counter()
    for tokens in tokenized:
        unique_terms = set(tokens)
        for term in unique_terms:
            df[term] += 1

    tfidf_matrix: list[dict[str, float]] = []
    for tokens in tokenized:
        tf: Counter[str] = Counter(tokens)
        total = len(tokens) if tokens else 1
        vec: dict[str, float] = {}
        for term, count in tf.items():
            idf = math.log((n_docs + 1) / (df[term] + 1)) + 1
            vec[term] = (count / total) * idf
        tfidf_matrix.append(vec)

    return tfidf_matrix


def _cosine_similarity(a: dict[str, float], b: dict[str, float]) -> float:
    """Cosine similarity between two sparse TF-IDF vectors."""
    all_terms = set(a) & set(b)
    if not all_terms:
        return 0.0

    dot = sum(a[t] * b[t] for t in all_terms)
    norm_a = math.sqrt(sum(v * v for v in a.values()))
    norm_b = math.sqrt(sum(v * v for v in b.values()))

    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


# ---------------------------------------------------------------------------
# Semantic Embedding Index (RAG-MCP pattern, arXiv:2505.03275)
# ---------------------------------------------------------------------------

class SemanticSkillIndex:
    """Dense vector embedding index for skill retrieval.

    Upgrades TF-IDF retrieval to dense vector similarity when the
    sentence-transformers library is available. Falls back gracefully
    to TF-IDF when it is not installed, preserving the zero-dependency
    guarantee for the core infrastructure.

    The index is built incrementally — each skill is embedded once on
    ingestion, not recomputed on every query. Embeddings persist in
    memory for the lifetime of the SkillLibrary instance.

    Research basis:
    - RAG-MCP (arXiv:2505.03275, Gan & Sun 2025): Semantic retrieval
      reduces prompt tokens 50% and improves selection accuracy from
      13.62% to 43.13% vs. including all tool schemas.
    - Sentence-BERT (Reimers & Gurevych, EMNLP 2019, arXiv:1908.10084):
      Dense embeddings outperform TF-IDF by 11-15% Spearman correlation
      on Semantic Textual Similarity benchmarks. Crucially bridges the
      lexical gap (e.g. "nested triangles" matches "concentric shapes").
    - VOYAGER (Wang et al., NeurIPS 2023): Skill library retrieval via
      embeddings enables lifelong learning in open-ended agents.
    - all-MiniLM-L6-v2: 384-dim, ~91 MB, CPU-only, 2-3s encode on
      desktop hardware. No GPU required.
    - CompactPrompt (arXiv:2510.18043): Self-information scoring for
      prompt compression achieves 60% token reduction with <5% accuracy
      loss, validating the retrieve-then-inject approach.

    Design principles:
    - ZERO mandatory dependencies: graceful ImportError fallback.
    - ZERO imports from agent_infra: preserves unidirectional chain.
    - Incremental indexing: O(1) per ingest, O(n) per query.
    - Normalized embeddings: dot product = cosine similarity.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        self._model: Any = None
        self._model_name = model_name
        self._embeddings: dict[str, list[float]] = {}
        self._available = False
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(model_name)
            self._available = True
            logger.info("SemanticSkillIndex: loaded %s", model_name)
        except ImportError:
            logger.debug(
                "sentence-transformers not installed; "
                "SemanticSkillIndex disabled (TF-IDF fallback active)"
            )

    @property
    def available(self) -> bool:
        return self._available

    @property
    def indexed_count(self) -> int:
        return len(self._embeddings)

    def index_skill(self, task_id: str, description: str) -> None:
        """Embed a skill description and store it in the index.

        Called once per skill on ingestion. The embedding is normalized
        so that dot product equals cosine similarity (Reimers &
        Gurevych, EMNLP 2019, §3.4).
        """
        if not self._model or not description:
            return
        try:
            embedding = self._model.encode(
                description, normalize_embeddings=True
            )
            self._embeddings[task_id] = embedding.tolist()
        except Exception as exc:
            logger.warning("SemanticSkillIndex.index_skill failed: %s", exc)

    def remove_skill(self, task_id: str) -> None:
        """Remove a skill from the index."""
        self._embeddings.pop(task_id, None)

    def query(
        self, query_text: str, top_k: int = 3, min_score: float = 0.1
    ) -> list[tuple[str, float]]:
        """Retrieve the top-K most semantically similar task_ids.

        Returns a list of (task_id, cosine_similarity) tuples sorted
        descending by score. Entries below min_score are excluded.

        Uses numpy dot product on normalized vectors. If numpy is not
        available, falls back to a pure-Python dot product.
        """
        if not self._model or not self._embeddings:
            return []
        try:
            q_emb = self._model.encode(
                query_text, normalize_embeddings=True
            )
            scored: list[tuple[str, float]] = []
            for task_id, emb in self._embeddings.items():
                sim = self._dot(q_emb, emb)
                if sim >= min_score:
                    scored.append((task_id, float(sim)))
            scored.sort(key=lambda x: x[1], reverse=True)
            return scored[:top_k]
        except Exception as exc:
            logger.warning("SemanticSkillIndex.query failed: %s", exc)
            return []

    @staticmethod
    def _dot(a: Any, b: Any) -> float:
        """Dot product between two vectors (numpy array or list)."""
        try:
            import numpy as np
            return float(np.dot(a, b))
        except ImportError:
            return sum(float(x) * float(y) for x, y in zip(a, b))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _iso_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()) + f".{int((time.time() % 1) * 1000):03d}Z"


def _hash_file(path: Path) -> str:
    """SHA-256 hash of a file for provenance verification."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def _generate_skill_id(task_id: str) -> str:
    """Deterministic skill ID from task_id for deduplication."""
    return hashlib.sha256(task_id.encode()).hexdigest()[:12]
