# Environment Compliance Automation (PhD)

## Purpose
This adds the unattended review layer for the environment-justification audit system.

The repo already had:
- rules
- a checklist template
- a compliance logger
- a review script

This automation adds:
- automatic daily review via `launchd`
- Application Support storage so unattended jobs do not depend on Desktop privacy access
- log mirroring so manual repo-local entries are also visible to unattended review

## Environment Basis
System of interest:
- `concentric_study`

Local environment:
- macOS `26.3`
- user-space `launchd`
- Cursor and Safari workflow already tracked by the repo's environment monitor

Repo constraints:
- the audit layer must not interfere with the web-agent runtime
- the automation should reuse the existing Application Support pattern already used by the Cursor environment monitor

## Files
- installer: `operator/cre/tools/install_environment_compliance_daily_review.sh`
- repo-local logger: `operator/cre/tools/log_environment_compliance.py`
- repo-local reviewer: `operator/cre/tools/review_environment_compliance.py`
- repo-local log: `operator/cre/artifacts/environment_answer_compliance_log.jsonl`
- unattended mirror log: `~/Library/Application Support/ConcentricStudy/environment_compliance/environment_answer_compliance_log.jsonl`
- unattended review outputs:
  - `~/Library/Application Support/ConcentricStudy/environment_compliance/latest_review.json`
  - `~/Library/Application Support/ConcentricStudy/environment_compliance/latest_review.md`

## Design
### 1. Mirrored logging
The compliance logger now writes:
- repo-local JSONL log
- mirrored Application Support JSONL log

This preserves:
- repo-local evidence for manual inspection
- unattended review compatibility without Desktop access assumptions

### 2. Daily review
The LaunchAgent runs daily at `09:20` and also at install time.

It reviews the mirrored log and writes:
- JSON summary
- markdown summary

### 3. Seed-on-install
If the repo-local log exists and the automation log does not yet exist, the installer copies the repo log into the automation location so the first daily review starts with real history.

## Why this is safe
This automation is governance-only.
It does not touch:
- `operator/agent.py`
- `operator/agent_core.py`
- `operator/web_primitives.py`
- `ResearchAgent`
- `SiteKnowledge`
- live Safari automation

It only reads and writes audit artifacts.

## Installation
```bash
cd /Users/christianpardo/Desktop/concentric_study
./operator/cre/tools/install_environment_compliance_daily_review.sh
```

## Manual review
```bash
cd /Users/christianpardo/Desktop/concentric_study
python3 operator/cre/tools/review_environment_compliance.py --print-summary
```
