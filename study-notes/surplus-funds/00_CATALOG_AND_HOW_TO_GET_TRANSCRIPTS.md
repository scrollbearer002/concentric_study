# Surplus Funds Videos — Catalog (transcripts pending network access)

Channel: **Money Making Juggernaut** (Eric Richardson)

These three videos are the study set. Full ASR transcripts exist on YouTube, but this cloud environment cannot download caption timedtext until `youtube.com` is allowlisted (InnerTube metadata works; caption/`get_transcript` does not).

| # | Video ID | Title | URL |
|---|---|---|---|
| 1 | `R8B06ovsDXI` | How to start a Surplus Funds Business (45 min raw free game) | https://www.youtube.com/watch?v=R8B06ovsDXI |
| 2 | `DMdtmrWAO6c` | Surplus Funds Recovery Cold Calling - STEP-BY-STEP SCRIPT | https://www.youtube.com/watch?v=DMdtmrWAO6c |
| 3 | `AvPC7Lal-8U` | How To Make Your Yearly Salary In The Next 30 Days | https://www.youtube.com/watch?v=AvPC7Lal-8U |

## How to get the full transcripts

### Option A — one command (recommended)
```bash
python3 -m pip install -U youtube-transcript-api yt-dlp
python3 study-notes/fetch_youtube_transcripts.py
```
Writes:
- `study-notes/transcripts/R8B06ovsDXI_transcript.md`
- `study-notes/transcripts/DMdtmrWAO6c_transcript.md`
- `study-notes/transcripts/AvPC7Lal-8U_transcript.md`

### Option B — manual YouTube copy
For each video: Open → ⋯ → Show transcript → copy all → paste into the matching file above.

### Option C — allowlist in this cloud agent
Approve egress for `youtube.com` (and ideally `googlevideo.com`), then ask me to rerun the fetcher.

## What already works here
- Titles + channel via `youtubei.googleapis.com` (allowlisted)
- Confirmation that searchable transcript panels exist for all three videos
- Fetcher script ready to dump full timestamped transcripts

## Next step after transcripts land
Build the organized study-notes pack (master notes + cheat sheet + practice playbook) for the surplus-funds subject.
