# Architecture Conformance Next Hardening (PhD)

## Environment Basis
- Repo: `concentric_study`
- Machine: local macOS arm64 development environment
- Active subsystem: `operator/cre/project_understanding/tools/build_architecture_conformance.py`
- Scope: architecture-governance tooling, not the Safari/web-agent runtime

## Local Repo Facts
1. There is currently no checked-in CI workflow directory (`.github/workflows/`) in this repo.
2. `build_architecture_conformance.py` currently has one public mode split only by `--enforce`:
   - it always rebuilds the live import graph
   - it always rewrites `artifacts/import_graph.json`
   - it always rewrites `artifacts/architecture_conformance.json`
   - it always rewrites `artifacts/architecture_conformance.csv`
3. After the recent hardening, the import graph is deterministic by construction for a fixed repo state:
   - sorted file enumeration
   - sorted Python path input
   - sorted edge output
4. A focused regression test now proves input-order invariance:
   - `operator/cre/test_architecture_conformance.py`

## Proposal Analysis

### 1. Split conformance into `--regen-graph` vs `--check`
**Verdict:** Yes, strongly recommended for this project.

**Why it fits this repo:**
- Right now `load_graph()` mutates repo artifacts even when the caller only wants verification.
- That is acceptable for local rebuilding, but it is the wrong default shape for CI because it mixes:
  - graph regeneration
  - enforcement
  - artifact mutation
- This repo already values evidence separation. A clean split would align with that pattern.

**Direct local evidence:**
- `operator/cre/project_understanding/tools/build_architecture_conformance.py:147`
- `operator/cre/project_understanding/tools/build_architecture_conformance.py:380`
- `operator/cre/project_understanding/tools/build_architecture_conformance.py:462`

**External evidence:**
- Bazel hermeticity docs say writing to the source tree during build/test is a source of non-hermeticity.
  - https://docs.bazel.build/versions/master/hermeticity.html
- Bazel’s write-to-sources pattern explicitly separates:
  - `bazel test` / `bazel build` for checking
  - `bazel run` for source mutation/update
  - https://registry.bazel.build/docs/bazel_lib
  - https://dev.to/bazel/bazel-can-write-to-the-source-folder-b9b

**Repo-specific interpretation:**
- For `concentric_study`, the right shape is:
  - `--regen-graph` or `--write-artifacts`: mutating update path
  - `--check`: pure verification against already-generated artifacts or an in-memory live graph without writing
- This is especially important once CI exists.

### 2. Pin the graph digest in CI output and store it as an artifact
**Verdict:** Yes, good future hardening; medium priority because CI is not checked in yet.

**Why it fits this repo:**
- The project is already artifact-heavy and evidence-first.
- A graph digest makes the conformance input auditable over time.
- It is most useful once a CI workflow exists.

**Direct local evidence:**
- No checked-in CI workflow currently exists.
- The import graph is already materialized at:
  - `operator/cre/project_understanding/artifacts/import_graph.json`

**External evidence:**
- GitHub Actions artifacts are immutable in v4 and expose digest outputs.
  - https://docs.github.com/actions/using-workflows/storing-workflow-data-as-artifacts
  - https://github.com/marketplace/actions/upload-a-build-artifact
- GitHub artifact attestations bind subject + digest + predicate.
  - https://github.com/actions/attest
- SLSA provenance emphasizes verifiable information about how artifacts were produced.
  - https://slsa.dev/spec/v1.2-rc2/build-provenance

**Repo-specific interpretation:**
- This is a strong fit for a future CI layer, not an urgent local-runtime need.
- Recommended once `.github/workflows/` is introduced.

### 3. Add a two-run determinism test in the same process
**Verdict:** Yes, and this repo now effectively has the right first version of it.

**Why it fits this repo:**
- The main nondeterminism risk here was ordering.
- We already added a stronger practical variant:
  - same process
  - reversed input order
  - full graph equality
- That catches a meaningful class of hidden instability.

**Direct local evidence:**
- `operator/cre/test_architecture_conformance.py:59`
- local digest check on this machine produced identical digests for forward vs reverse path order

**External evidence:**
- Bazel hermeticity guidance recommends null sequential builds and comparing hashes to detect non-reproducibility.
  - https://docs.bazel.build/versions/master/hermeticity.html
- Reproducible Builds guidance emphasizes running reproducibility tests in varying environments and comparing outputs.
  - https://reproducible-builds.org/docs/why/

**Repo-specific interpretation:**
- This is a direct fit and should stay.
- A second same-process identical-order digest assertion could be added, but it is lower value than the reversed-order equality test already present.

### 4. Define AC006 as monitored debt with expiry
**Verdict:** Yes, strongly recommended.

**Why it fits this repo:**
- `AC006` is currently `drift`, but the meaning of that drift is underspecified in enforcement output.
- For this repo, ambiguous long-lived drift is bad because docs and governance are now trying to be scientifically precise.
- If it is accepted debt, it should be named as such with:
  - owner
  - issue link
  - review date or expiry condition

**Direct local evidence:**
- `operator/cre/project_understanding/tools/build_architecture_conformance.py:447`
- current `--enforce` output still reports `AC006: drift`
- no explicit owner/expiry metadata is present in the rule record schema

**External evidence:**
- SEI recommends keeping technical debt current and trackable in accessible registries/dashboards.
  - https://www.sei.cmu.edu/blog/experiences-documenting-and-remediating-enterprise-technical-debt/
  - https://www.sei.cmu.edu/library/got-technical-debt-surfacing-elusive-technical-debt-in-issue-trackers-2/
- FixMe shows value in linking debt to external issue state and notifying when it is ready to be addressed.
  - https://arxiv.org/abs/2109.02878

**Repo-specific interpretation:**
- “monitored debt with expiry” is not directly specified by those sources as a phrase.
- It is an engineering inference from technical-debt tracking literature and fits this repo well.
- This is a high-value governance improvement.

### 5. Cross-environment probe on multiple Python versions / one non-macOS runner
**Verdict:** Yes, but only for the conformance tooling layer, not as a project-wide runtime claim.

**Why it fits this repo:**
- The import-graph and conformance tooling is mostly pure Python and path/AST based.
- It does not depend on Safari or Quartz in the hot path.
- So cross-environment validation is reasonable for this subtool.

**Direct local evidence:**
- `build_understanding_artifacts.py` import-graph code uses `pathlib`, `ast`, and sorting logic only.
- No macOS GUI APIs are used in the graph-building path.
- There is currently no checked-in CI matrix for Python/OS in this repo.

**External evidence:**
- GitHub recommends matrix testing across Python versions and OSes to make behavior explicit.
  - https://docs.github.com/actions/guides/building-and-testing-python
- Reproducible Builds stresses testing in varying environments to catch hidden build differences.
  - https://reproducible-builds.org/docs/why/

**Repo-specific interpretation:**
- This is valid for the conformance tool claim:
  - “stable function of repo state”
- It is **not** evidence that the full `concentric_study` runtime is cross-platform. The runtime is still macOS-specific.
- So this should be framed narrowly.

## Final Ranking for This Repo
1. **Do now:** split mutating regeneration from pure check
2. **Do now:** define AC006 as monitored debt with owner/expiry metadata
3. **Keep as-is / maybe strengthen later:** determinism test (already good enough to keep)
4. **Do when CI exists:** print/store graph digest as CI artifact
5. **Do when CI exists:** cross-environment probe for the conformance tool only

## Bottom Line
The strongest next hardening for `concentric_study` is not more runtime work.
It is making the conformance tool obey the same discipline it enforces:
- pure checks should be non-mutating
- accepted debt should be explicit and reviewable
- reproducibility claims should be bounded to the subtool that was actually tested
