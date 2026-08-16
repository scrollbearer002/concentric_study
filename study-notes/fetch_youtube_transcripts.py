#!/usr/bin/env python3
"""Fetch full YouTube transcripts for the Surplus Funds study videos.

Works on a normal machine with internet (or a cloud agent once youtube.com
is allowlisted). Writes markdown transcripts under study-notes/transcripts/.

Usage:
  python3 study-notes/fetch_youtube_transcripts.py
  # or:
  python3 -m pip install -U youtube-transcript-api yt-dlp
  python3 study-notes/fetch_youtube_transcripts.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

VIDEOS = [
    {
        "id": "R8B06ovsDXI",
        "title": "How to start a Surplus Funds Business (45 min raw free game)",
        "channel": "Money Making Juggernaut",
    },
    {
        "id": "DMdtmrWAO6c",
        "title": "Surplus Funds Recovery Cold Calling - STEP-BY-STEP SCRIPT",
        "channel": "Money Making Juggernaut",
    },
    {
        "id": "AvPC7Lal-8U",
        "title": "How To Make Your Yearly Salary In The Next 30 Days",
        "channel": "Money Making Juggernaut",
    },
]

OUT_DIR = Path(__file__).resolve().parent / "transcripts"


def cues_to_markdown(meta: dict, cues: list[tuple[float, str]]) -> str:
    lines = [
        "# YouTube Video Transcript",
        "",
        f"**Video ID:** `{meta['id']}`",
        f"**Title:** {meta.get('title') or '(unknown)'}",
        f"**Channel:** {meta.get('channel') or '(unknown)'}",
        f"**Source:** https://www.youtube.com/watch?v={meta['id']}",
        f"**Cue count:** {len(cues)}",
        "",
        "---",
        "",
        "## Full transcript (readable)",
        "",
    ]
    buf: list[str] = []
    last: float | None = None
    for t, text in cues:
        if last is not None and t - last > 8 and buf:
            lines.append(" ".join(buf))
            lines.append("")
            buf = []
        buf.append(text)
        last = t
    if buf:
        lines.append(" ".join(buf))
        lines.append("")
    lines.append("## Timestamped lines")
    lines.append("")
    for t, text in cues:
        lines.append(f"[{int(t // 60):02d}:{int(t % 60):02d}] {text}")
    return "\n".join(lines) + "\n"


def fetch_via_youtube_transcript_api(video_id: str) -> list[tuple[float, str]]:
    from youtube_transcript_api import YouTubeTranscriptApi

    api = YouTubeTranscriptApi()
    fetched = api.fetch(video_id)
    cues: list[tuple[float, str]] = []
    # youtube-transcript-api >=1.0 returns FetchedTranscript with snippets
    snippets = getattr(fetched, "snippets", fetched)
    for snip in snippets:
        start = float(getattr(snip, "start", snip.get("start", 0)))  # type: ignore[union-attr]
        text = str(getattr(snip, "text", snip.get("text", ""))).replace("\n", " ").strip()  # type: ignore[union-attr]
        if text:
            cues.append((start, text))
    return cues


def fetch_via_ytdlp(video_id: str) -> list[tuple[float, str]]:
    import subprocess
    import tempfile

    url = f"https://www.youtube.com/watch?v={video_id}"
    with tempfile.TemporaryDirectory() as tmp:
        outtmpl = str(Path(tmp) / "subs")
        cmd = [
            sys.executable,
            "-m",
            "yt_dlp",
            "--skip-download",
            "--write-auto-subs",
            "--sub-langs",
            "en.*,en",
            "--sub-format",
            "vtt/json3/best",
            "-o",
            outtmpl,
            url,
        ]
        subprocess.check_call(cmd)
        files = list(Path(tmp).glob("*"))
        if not files:
            raise RuntimeError("yt-dlp wrote no subtitle files")
        # Prefer json3 / vtt
        path = sorted(files, key=lambda p: (p.suffix != ".json3", p.suffix != ".vtt", p.name))[0]
        raw = path.read_text(encoding="utf-8", errors="ignore")
        if path.suffix == ".json3" or raw.lstrip().startswith("{"):
            data = json.loads(raw)
            cues = []
            for ev in data.get("events", []):
                segs = ev.get("segs") or []
                text = "".join(s.get("utf8", "") for s in segs).replace("\n", " ").strip()
                if text:
                    cues.append((float(ev.get("tStartMs", 0)) / 1000.0, text))
            return cues
        # VTT parse
        cues = []
        blocks = re.split(r"\n\n+", raw)
        for block in blocks:
            m = re.search(
                r"(\d{2}):(\d{2}):(\d{2})\.(\d{3})\s-->\s",
                block,
            )
            if not m:
                continue
            h, mi, s, ms = map(int, m.groups())
            start = h * 3600 + mi * 60 + s + ms / 1000.0
            text_lines = [
                ln
                for ln in block.splitlines()
                if ln and "-->" not in ln and not ln.strip().isdigit() and not ln.startswith("WEBVTT")
            ]
            text = re.sub(r"<[^>]+>", "", " ".join(text_lines)).strip()
            if text:
                cues.append((start, text))
        return cues


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ok = 0
    for meta in VIDEOS:
        vid = meta["id"]
        print(f"== {vid}: {meta['title']}")
        cues: list[tuple[float, str]] = []
        errors: list[str] = []
        for name, fn in (
            ("youtube-transcript-api", fetch_via_youtube_transcript_api),
            ("yt-dlp", fetch_via_ytdlp),
        ):
            try:
                cues = fn(vid)
                if cues:
                    print(f"  OK via {name}: {len(cues)} cues")
                    break
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{name}: {exc}")
                print(f"  FAIL {name}: {exc}")
        if not cues:
            print(f"  ERROR: could not fetch transcript ({'; '.join(errors)})")
            continue
        path = OUT_DIR / f"{vid}_transcript.md"
        path.write_text(cues_to_markdown(meta, cues), encoding="utf-8")
        print(f"  wrote {path} ({path.stat().st_size} bytes)")
        ok += 1
    print(f"Done: {ok}/{len(VIDEOS)} transcripts")
    return 0 if ok == len(VIDEOS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
