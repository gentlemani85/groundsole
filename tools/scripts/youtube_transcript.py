#!/usr/bin/env python3
"""
00_FRAMEWORK/tools/scripts/youtube_transcript.py
scripts/youtube_transcript.py
Deterministischer Abruf des vollständigen Wortlaut-Transkripts eines YouTube-Videos
via youtube-transcript-api (primär) und yt-dlp (Fallback & Metadaten).
"""

import sys
import json
import urllib.request
import re

try:
    import yt_dlp
except ImportError:
    yt_dlp = None

def extract_video_id(url_or_id: str) -> str:
    m = re.search(r"(?:v=|\/|youtu\.be\/)([0-9A-Za-z_-]{11})", url_or_id)
    if m:
        return m.group(1)
    return url_or_id.strip()

def get_transcript(url_or_id: str) -> str:
    vid = extract_video_id(url_or_id)
    url = f"https://www.youtube.com/watch?v={vid}" if len(vid) == 11 else url_or_id

    title = "YouTube Video"
    channel = "Unbekannt"
    duration = 0
    subs = {}

    if yt_dlp:
        ydl_opts = {
            "skip_download": True,
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": ["de", "en", "en-orig"],
            "quiet": True,
            "no_warnings": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                title = info.get("title", title)
                channel = info.get("uploader", channel)
                duration = info.get("duration", 0)
                subs = info.get("subtitles") or info.get("automatic_captions") or {}
            except Exception:
                pass

    # Versuche zuerst youtube_transcript_api (äußerst stabil, kein 429-Block)
    text = ""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        ytt = YouTubeTranscriptApi()
        fetched = ytt.fetch(vid, languages=['de', 'en', 'en-US', 'en-GB'])
        lines = [entry.text.strip() for entry in fetched if entry.text.strip()]
        text = " ".join(lines)
    except Exception:
        text = ""

    # Fallback auf yt-dlp Untertitel-Download falls nötig
    if not text and subs:
        target_lang = None
        for lang in ["de", "en", "en-orig"]:
            if lang in subs:
                target_lang = lang
                break
        if not target_lang:
            target_lang = list(subs.keys())[0]

        formats = subs[target_lang]
        sub_url = None
        for fmt in formats:
            if fmt.get("ext") == "json3" or "json" in fmt.get("ext", ""):
                sub_url = fmt.get("url")
                break
        if not sub_url and formats:
            sub_url = formats[0].get("url")

        if sub_url:
            try:
                req = urllib.request.Request(sub_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
                with urllib.request.urlopen(req) as resp:
                    raw_data = resp.read().decode("utf-8")
                data = json.loads(raw_data)
                lines = []
                for event in data.get("events", []):
                    if "segs" in event:
                        line = "".join(seg.get("utf8", "") for seg in event["segs"]).strip()
                        if line and line != "\n":
                            lines.append(line)
                text = " ".join(lines)
            except Exception as e:
                return f"Fehler beim Laden des Transkripts: {e}"

    if not text:
        return f"Titel: {title}\nKanal: {channel}\nKein Transkript oder Untertitel verfügbar."

    minutes = duration // 60
    seconds = duration % 60
    header = f"# Video: {title}\n- **Kanal:** {channel}\n- **Dauer:** {minutes}m {seconds}s\n\n---\n\n"
    return header + text

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Verwendung: python3 scripts/youtube_transcript.py <YouTube-URL oder ID>")
        sys.exit(1)

    url = sys.argv[1]
    print(get_transcript(url))
