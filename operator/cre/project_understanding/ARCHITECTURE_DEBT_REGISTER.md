# Architecture Debt Register

This register tracks architecture debt that is intentionally tolerated but
explicitly bounded. A debt entry is not a generic warning. It is a named,
owned, reviewable contract.

## AC006

- `status`: `monitored_debt`
- `owner`: `repo maintainer`
- `issue`: `operator/cre/project_understanding/SECTION_4_CONFORMANCE_ENFORCEMENT.md`
- `review_by`: `2026-04-03`
- `rationale`: Root-level compatibility shims are still used by a bounded set of
  tests and harnesses while canonical `agent_infra.*` imports remain the target
  surface. Growth is blocked; migration can proceed incrementally.
- `scope`: Only the caller set frozen in `ALLOWED_SHIM_IMPORTS` is tolerated.
  Any new shim-import edge outside that frozen set is a hard conformance
  regression.
- `exit_condition`: All remaining shim callers are migrated to canonical
  `agent_infra.*` imports and the shim surface reaches zero live callers.
