# Cursor Cloud And Team Surfaces (PhD)

Date: `2026-03-04`

## Purpose

Classify the major Cursor 2.4-2.6 cloud, team, and enterprise surfaces so they
do not get mixed into first-wave repo implementation work.

## Classification

### `account_gated`

- Cloud agents with computer use
  - Reason: requires access to Cursor cloud-agent surfaces and is not a
    repo-local implementation path by itself.
- Bugbot Autofix
  - Reason: requires PR workflow plus Bugbot access.
- Shared transcripts
  - Reason: depends on account-level sharing surfaces.

### `admin_gated`

- Team marketplaces
  - Reason: requires Teams or Enterprise admin controls.
- Conversation insights
  - Reason: enterprise-admin surface.
- Billing groups
  - Reason: enterprise/account governance surface.
- Service accounts
  - Reason: admin and org-level automation feature.
- team rules distribution
  - Reason: requires dashboard-level admin control.

### `monitor_only`

- Cursor Blame
  - Reason: real enterprise capability, but not a repo implementation target.
- cloud review artifacts and demos
  - Reason: worth monitoring as a future review surface, but not a local repo
    integration task.

### `not_repo_work`

- org-wide spend analytics
- private marketplace operations
- cross-team billing and dashboard administration

These are real Cursor surfaces, but they are not code or repo integration work
for `concentric_study`.

## Local Ready But Deferred

- MCP Apps
  - Platform-ready on Cursor `2.6.11`, but still deferred until internal data
    surfaces stabilize.
- plugin packaging
  - technically local once schema is verified, but deferred until internal
    rules and MCPs are stable and the repo is in a real git worktree.

## Decision

Do not treat cloud, team, or enterprise surfaces as part of the first-wave
implementation program. Track them separately and revisit only after the local
Cursor operating layer and read-only internal MCPs are stable.
