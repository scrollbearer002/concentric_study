# Option C — Cloud pilot upload

## Status
- Landing dir ready: `/workspace/wc_pilot/inbox/`
- VM free disk: ~229 GB
- `wc_pilot/` is gitignored — case files must never be committed to `concentric_study`

## User action required (blocker)
Get **one** pilot ZIP into the VM. Prefer in this order:
1. `Master Legal File.zip` (~43 MB)
2. Else one `Legal Case Files N.zip` (~72 MB)

### Transfer methods
A. **Private temporary download link** (best): Dropbox / Google Drive / iCloud share with link access → paste URL in chat → agent `curl`/`wget` into `wc_pilot/inbox/`.
B. **Chat attach**: if the Cursor Agents UI accepts the ZIP as an attachment, attach it and say “file is attached”.
C. **Free ~80 MB on Mac**, download one ZIP from iCloud, upload via whichever attach/link path works.

Do **not** git-commit or push legal ZIPs to GitHub.

## After file lands (agent executes)
1. Verify checksum + size in `inbox/`
2. Unzip to `wc_pilot/unzips/<name>/`
3. Build inner `inventory.json`
4. Near-dup member hash map
5. Chunk + line-coverage pilot on that archive only
6. Produce coverage ledger + first findings draft

## Pass/fail
- [ ] ZIP present under `wc_pilot/inbox/`
- [ ] Unzip succeeds
- [ ] Inventory of inner files written
- [ ] Line coverage started on pilot only
