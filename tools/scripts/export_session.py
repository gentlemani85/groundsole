#!/usr/bin/env python3
"""
scripts/export_session.py

Harness-agnostischer, universeller Session-Exporter für Groundsole.
Unterstützt: Google Antigravity, Hermes Agent, Goose, Claude Code.

Erkennt automatisch die aktive Session der aktuell laufenden Harness
(oder via CLI-Argumente) und exportiert sie als bereinigtes, normiertes
Markdown-Transkript nach 00_MEMORY/transcripts/.
Stößt optional direkt die Kristallisierung in LangMem & Cognee an.
"""

import os
import sys
import re
import json
import sqlite3
import argparse
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Tuple

LOCAL_TZ = timezone(timedelta(hours=1))  # Default Winterzeit / lokal anpassbar

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRANSCRIPTS_DIR = os.path.join(REPO_ROOT, "00_MEMORY", "transcripts")


def clean_title(title: str) -> str:
    """Bereinigt Dateinamen von verbotenen Zeichen."""
    title = re.sub(r'[\\/*?:"<>|]', '', title)
    title = re.sub(r'\s+', ' ', title).strip()
    return title or "Session"


def format_iso_timestamp(ts) -> str:
    """Konvertiert UNIX Epoch oder ISO String in ein sauberes lokales ISO-Format."""
    if not ts:
        return datetime.now(LOCAL_TZ).strftime("%Y-%m-%dT%H:%M:%S%z")
    try:
        if isinstance(ts, (int, float)):
            dt = datetime.fromtimestamp(ts, tz=LOCAL_TZ)
            return dt.strftime("%Y-%m-%dT%H:%M:%S%z")
        # Text string
        iso_str = str(ts)
        if "T" in iso_str:
            dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
            return dt.astimezone(LOCAL_TZ).strftime("%Y-%m-%dT%H:%M:%S%z")
    except Exception:
        pass
    return str(ts)


def sanitize_text(text: str) -> str:
    """Entfernt technische System-Tags, Blobs, Tokens und UI-Elemente."""
    if not text:
        return ""
    # Resolve UI @[Quote] blocks from ADDITIONAL_METADATA before stripping
    meta_match = re.search(r'<ADDITIONAL_METADATA>([\s\S]*?)</ADDITIONAL_METADATA>', text)
    if meta_match:
        meta_content = meta_match.group(1)
        quotes = re.findall(r'@\[Quote\] is a \[Text Block\]:\s*\n?(.*?)(?=@\[Quote\] is a \[Text Block\]:|\Z)', meta_content, re.DOTALL)
        for q in [q.strip() for q in quotes if q.strip()]:
            text = text.replace('@[Quote]', f'> "{q}"\n', 1)

    text = re.sub(r'<USER_REQUEST>\s*', '', text)
    text = re.sub(r'</USER_REQUEST>\s*', '', text)
    text = re.sub(r'<ADDITIONAL_METADATA>[\s\S]*?</ADDITIONAL_METADATA>', '', text)
    text = re.sub(r'<CONTEXT_SUMMARY>[\s\S]*?</CONTEXT_SUMMARY>', '', text)
    text = re.sub(r'<USER_SETTINGS_CHANGE>[\s\S]*?</USER_SETTINGS_CHANGE>', '', text)
    text = re.sub(r'<SYSTEM_MESSAGE>[\s\S]*?</SYSTEM_MESSAGE>', '', text)
    text = re.sub(r'\[OUT-OF-BAND USER MESSAGE[^\]]*\]\s*', '', text)
    text = re.sub(r'\s*\[/OUT-OF-BAND USER MESSAGE\]', '', text)
    text = re.sub(r'<turn-context>[\s\S]*?</turn-context>', '', text)
    # Token- und Passworthygiene (Zero-Output für Secrets)
    text = re.sub(r'ghp_[A-Za-z0-9_]{36,}', '[IN_PASSBOLT_GESICHERT]', text)
    text = re.sub(r'AIzaSy[A-Za-z0-9_-]{33}', '[IN_PASSBOLT_GESICHERT]', text)
    text = re.sub(r'hf_[A-Za-z0-9]{30,}', '[IN_PASSBOLT_GESICHERT]', text)
    text = re.sub(r'rpa_[A-Za-z0-9]{20,}', '[IN_PASSBOLT_GESICHERT]', text)
    text = re.sub(r'sk-[A-Za-z0-9_-]{20,}', '[IN_PASSBOLT_GESICHERT]', text)
    return text.strip()


# ── Harness Readers ───────────────────────────────────────────────────────────

def read_antigravity_session(session_id: Optional[str] = None) -> Tuple[str, str, List[Dict]]:
    """Liest eine Antigravity Session aus transcript_full.jsonl."""
    brain_dir = os.path.expanduser("~/.gemini/antigravity/brain")
    if not os.path.isdir(brain_dir):
        raise FileNotFoundError("Antigravity Brain-Verzeichnis nicht gefunden.")

    # Wenn keine ID übergeben, nimm die zuletzt modifizierte
    if not session_id:
        cids = [d for d in os.listdir(brain_dir) if os.path.isdir(os.path.join(brain_dir, d)) and len(d) > 20]
        if not cids:
            raise ValueError("Keine Antigravity Sessions gefunden.")
        cids.sort(key=lambda d: os.path.getmtime(os.path.join(brain_dir, d)), reverse=True)
        session_id = cids[0]

    t_path = os.path.join(brain_dir, session_id, ".system_generated", "logs", "transcript_full.jsonl")
    if not os.path.exists(t_path):
        t_path = os.path.join(brain_dir, session_id, ".system_generated", "logs", "transcript.jsonl")
    if not os.path.exists(t_path):
        raise FileNotFoundError(f"Kein Transkript für Antigravity Session {session_id} gefunden.")

    with open(t_path, "r", encoding="utf-8", errors="replace") as f:
        steps = [json.loads(line) for line in f if line.strip()]

    turns = []
    first_date = datetime.now().strftime("%Y-%m-%d")
    user_indices = [idx for idx, s in enumerate(steps) if s.get("type") == "USER_INPUT"]

    for i, u_idx in enumerate(user_indices):
        u_step = steps[u_idx]
        next_u_idx = user_indices[i+1] if i + 1 < len(user_indices) else len(steps)

        u_cnt = sanitize_text(u_step.get("content", ""))
        u_ts = format_iso_timestamp(u_step.get("created_at"))
        if i == 0 and u_step.get("created_at"):
            first_date = str(u_step.get("created_at"))[:10]

        # Letzte Antwort für diesen Turn suchen
        a_step = None
        for j in range(next_u_idx - 1, u_idx, -1):
            s = steps[j]
            if s.get("type") == "PLANNER_RESPONSE" and s.get("content"):
                if not s.get("tool_calls"):
                    a_step = s
                    break
                elif not a_step:
                    a_step = s

        turns.append({"speaker": "Emanuel", "time": u_ts, "content": u_cnt})
        if a_step:
            a_cnt = sanitize_text(a_step.get("content", ""))
            a_ts = format_iso_timestamp(a_step.get("created_at"))
            if a_cnt:
                turns.append({"speaker": "Antigravity", "time": a_ts, "content": a_cnt})

    return (session_id, first_date, turns)


def read_hermes_session(session_id: Optional[str] = None) -> Tuple[str, str, List[Dict]]:
    """Liest eine Hermes Session aus state.db."""
    db_path = os.path.expanduser("~/.hermes/state.db")
    if not os.path.exists(db_path):
        raise FileNotFoundError("Hermes state.db nicht gefunden.")

    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=10)
    cur = conn.cursor()
    if session_id:
        cur.execute("SELECT id, started_at, title FROM sessions WHERE id = ?", (session_id,))
    else:
        cur.execute("SELECT id, started_at, title FROM sessions WHERE COALESCE(archived, 0) = 0 ORDER BY COALESCE(last_activity_at, started_at) DESC LIMIT 1")
    row = cur.fetchone()
    if not row:
        conn.close()
        raise ValueError("Keine Hermes Session gefunden.")

    sess_id, started_at, title = row
    first_date = datetime.fromtimestamp(started_at, tz=LOCAL_TZ).strftime("%Y-%m-%d")

    cur.execute(
        "SELECT role, content, timestamp FROM messages WHERE session_id = ? AND role IN ('user', 'assistant') ORDER BY id ASC",
        (sess_id,)
    )
    rows = cur.fetchall()
    conn.close()

    turns = []
    for role, content, ts in rows:
        cleaned = sanitize_text(content)
        if cleaned:
            speaker = "Emanuel" if role == "user" else "Hermes"
            turns.append({"speaker": speaker, "time": format_iso_timestamp(ts), "content": cleaned})

    return (str(sess_id), first_date, turns)


def read_goose_session(session_id: Optional[str] = None) -> Tuple[str, str, List[Dict]]:
    """Liest eine Goose Session aus sessions.db."""
    goose_db = os.path.expanduser("~/.local/share/goose/sessions/sessions.db")
    if not os.path.exists(goose_db):
        raise FileNotFoundError("Goose sessions.db nicht gefunden.")

    conn = sqlite3.connect(f"file:{goose_db}?mode=ro", uri=True, timeout=10)
    cur = conn.cursor()
    if session_id:
        cur.execute("SELECT id, created_at, description, name FROM sessions WHERE id = ?", (session_id,))
    else:
        cur.execute("SELECT id, created_at, description, name FROM sessions WHERE archived_at IS NULL ORDER BY updated_at DESC LIMIT 1")
    row = cur.fetchone()
    if not row:
        conn.close()
        raise ValueError("Keine Goose Session gefunden.")

    sess_id, created_at, desc, name = row
    first_date = str(created_at)[:10] if created_at else datetime.now().strftime("%Y-%m-%d")

    cur.execute(
        "SELECT role, content_json, timestamp FROM messages WHERE session_id = ? ORDER BY id ASC",
        (sess_id,)
    )
    rows = cur.fetchall()
    conn.close()

    turns = []
    for role, content_json, ts in rows:
        if not content_json:
            continue
        try:
            parsed = json.loads(content_json)
            parts = []
            if isinstance(parsed, list):
                for item in parsed:
                    if isinstance(item, dict) and item.get("type") == "text":
                        parts.append(item.get("text", ""))
            elif isinstance(parsed, dict) and parsed.get("type") == "text":
                parts.append(parsed.get("text", ""))
            text = "\n".join(parts).strip()
            cleaned = sanitize_text(text)
            if cleaned:
                speaker = "Emanuel" if role == "user" else "Goose"
                turns.append({"speaker": speaker, "time": format_iso_timestamp(ts), "content": cleaned})
        except Exception:
            continue

    return (str(sess_id), first_date, turns)


def auto_detect_active_harness() -> str:
    """Erkennt anhand von Prozesslisten und mtime-Checks die aktive Harness."""
    # 1. Antigravity Brain mtime
    ag_dir = os.path.expanduser("~/.gemini/antigravity/brain")
    hermes_db = os.path.expanduser("~/.hermes/state.db")
    goose_db = os.path.expanduser("~/.local/share/goose/sessions/sessions.db")

    scores = []
    if os.path.isdir(ag_dir):
        try:
            mtimes = [os.path.getmtime(os.path.join(ag_dir, d)) for d in os.listdir(ag_dir) if len(d) > 20]
            if mtimes:
                scores.append(("antigravity", max(mtimes)))
        except Exception:
            pass

    if os.path.exists(hermes_db):
        try:
            scores.append(("hermes", os.path.getmtime(hermes_db)))
        except Exception:
            pass

    if os.path.exists(goose_db):
        try:
            scores.append(("goose", os.path.getmtime(goose_db)))
        except Exception:
            pass

    if not scores:
        return "antigravity"

    scores.sort(key=lambda s: s[1], reverse=True)
    return scores[0][0]


# ── Universal Export Execution ────────────────────────────────────────────────

def export_session(
    harness: Optional[str] = None,
    session_id: Optional[str] = None,
    title: Optional[str] = None,
    output_path: Optional[str] = None,
    crystallize: bool = True
) -> str:
    """Führt den ganzheitlichen Session-Export deterministisch durch."""
    if not harness or harness == "auto":
        harness = auto_detect_active_harness()

    harness = harness.lower().strip()
    print(f"📦 Exportiere Session aus Harness: {harness.upper()}...")

    if harness == "antigravity":
        sess_id, date_str, turns = read_antigravity_session(session_id)
    elif harness == "hermes":
        sess_id, date_str, turns = read_hermes_session(session_id)
    elif harness == "goose":
        sess_id, date_str, turns = read_goose_session(session_id)
    else:
        raise ValueError(f"Unbekannte Harness: {harness}")

    if not turns:
        raise ValueError(f"Keine relevanten Turns in Session {sess_id} gefunden.")

    # Titel bestimmen
    final_title = title or f"Session_{sess_id[:8]}"
    final_title = clean_title(final_title)

    filename = f"{date_str} - {final_title}.md"
    if not output_path:
        os.makedirs(TRANSCRIPTS_DIR, exist_ok=True)
        output_path = os.path.join(TRANSCRIPTS_DIR, filename)

    # Markdown generieren
    md_lines = [f"# {final_title}\n"]
    for t in turns:
        md_lines.append(f"## {t['speaker']} ({t['time']})\n")
        md_lines.append(f"{t['content']}\n")

    full_md = "\n".join(md_lines).strip() + "\n"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(full_md)

    line_count = len(full_md.splitlines())
    byte_count = os.path.getsize(output_path)
    print(f"✅ Transkript erfolgreich exportiert:")
    print(f"   Harness:    {harness}")
    print(f"   Session-ID: {sess_id}")
    print(f"   Zielpfad:   {output_path}")
    print(f"   Umfang:     {len(turns)} Turns, {line_count} Zeilen, {byte_count:,} Bytes")

    # Optional: Sofortige Kristallisation
    if crystallize:
        cryst_script = os.path.join(REPO_ROOT, "scripts", "crystallize_memory.py")
        if not os.path.exists(cryst_script):
            cryst_script = os.path.join(REPO_ROOT, "tools", "scripts", "crystallize_memory.py")
        if os.path.exists(cryst_script):
            try:
                import subprocess
                venv_py = "/Users/emanuel/.local/venv/bin/python3"
                py_bin = venv_py if os.path.exists(venv_py) else sys.executable
                print("💎 Starte nachgelagerte Kristallisation...")
                subprocess.run([py_bin, cryst_script, "--transcript", output_path], check=True)
            except Exception as exc:
                print(f"⚠️ Kristallisation konnte nicht ausgeführt werden: {exc}")

    return output_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Universal Session Exporter for Groundsole")
    parser.add_argument("--harness", choices=["auto", "antigravity", "hermes", "goose"], default="auto", help="Harness-Auswahl")
    parser.add_argument("--session-id", help="Spezifische Session-ID (optional)")
    parser.add_argument("--title", help="Titel für das Transkript (ohne Datum)")
    parser.add_argument("--output", help="Individueller Ausgabepfad")
    parser.add_argument("--no-crystallize", action="store_true", help="Kristallisation überspringen")
    args = parser.parse_args()

    export_session(
        harness=args.harness,
        session_id=args.session_id,
        title=args.title,
        output_path=args.output,
        crystallize=(not args.no_crystallize)
    )
