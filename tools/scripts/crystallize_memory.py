#!/usr/bin/env python3
"""
Sliding-Chunk-Crystallizer für Groundsole
Extrahiert autonom aus aufgelaufenen Puffer-Turns (alle N Turns oder bei --flush)
harte Fakten, Beschlüsse, Beträge und Beziehungen und überführt sie direkt nach
LangMem (langmem_store.db) und Cognee (cognee_db).

Multi-Provider: Unterstützt Gemini, OpenRouter, OpenAI, lokales Ollama oder Tier-1 In-Harness Modus.
"""


import os
import sys
import re
import json
import sqlite3
import urllib.request
import urllib.error
import argparse
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUFFER_DB_PATH = os.path.join(REPO_ROOT, "00_MEMORY", "emanuel_vectors", "memory_buffer.db")
HERMES_ENV_PATH = os.path.expanduser("~/.hermes/.env")

# Schnittstellen zu LangMem und Cognee importieren
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
try:
    from memory import add_memory
except ImportError:
    add_memory = None

try:
    from cognee_graph import add_edge
except ImportError:
    add_edge = None


def get_inference_provider() -> Tuple[str, Optional[str], Optional[str], Optional[str]]:
    """
    Ermittelt die verfügbare Inferenz-Quelle:
    - ("gemini", api_key, url, model)
    - ("openai", api_key, url, model)
    - ("ollama", None, url, model)
    - ("none", None, None, None)
    """
    k_google = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    candidate_files = [
        HERMES_ENV_PATH,
        os.path.expanduser("~/.config/groundsole/.env"),
        os.path.join(REPO_ROOT, ".env")
    ]
    if not k_google:
        for cfile in candidate_files:
            if os.path.exists(cfile):
                try:
                    with open(cfile, "r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if line.startswith("GOOGLE_API_KEY=") or line.startswith("GEMINI_API_KEY="):
                                k_google = line.split("=", 1)[1].strip().strip("'\"")
                                break
                except Exception:
                    pass
            if k_google:
                break

    if k_google:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={k_google}"
        return ("gemini", k_google, url, "gemini-2.5-flash")

    k_openrouter = os.environ.get("OPENROUTER_API_KEY")
    k_openai = os.environ.get("OPENAI_API_KEY")
    if not (k_openrouter or k_openai):
        for cfile in candidate_files:
            if os.path.exists(cfile):
                try:
                    with open(cfile, "r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if line.startswith("OPENROUTER_API_KEY="):
                                k_openrouter = line.split("=", 1)[1].strip().strip("'\"")
                            elif line.startswith("OPENAI_API_KEY="):
                                k_openai = line.split("=", 1)[1].strip().strip("'\"")
                except Exception:
                    pass

    if k_openrouter:
        return ("openai", k_openrouter, "https://openrouter.ai/api/v1/chat/completions", "google/gemini-2.5-flash")
    if k_openai:
        return ("openai", k_openai, "https://api.openai.com/v1/chat/completions", "gpt-4o-mini")

    try:
        req = urllib.request.Request("http://localhost:11434/api/tags")
        with urllib.request.urlopen(req, timeout=0.2) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            models = [m.get("name") for m in data.get("models", [])]
            if models:
                return ("ollama", None, "http://localhost:11434/v1/chat/completions", models[0])
    except Exception:
        pass

    return ("none", None, None, None)



def init_crystallizer_schema(conn: sqlite3.Connection):
    """Stellt sicher, dass die Cursor-Tabelle in memory_buffer.db existiert."""
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS crystallizer_state (
            filename TEXT PRIMARY KEY,
            last_chunk_id INTEGER NOT NULL,
            crystallized_turns_count INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT NOT NULL
        )
    """)
    conn.commit()


def get_latest_session_filename(conn: sqlite3.Connection) -> Optional[str]:
    """Findet den Dateinamen der neuesten aktiven Harness-Session im Puffer."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT filename FROM chunks 
        WHERE filename LIKE 'harness_%' 
        ORDER BY id DESC LIMIT 1
    """)
    row = cursor.fetchone()
    return row[0] if row else None


def fetch_pending_chunks(conn: sqlite3.Connection, filename: str) -> Tuple[List[Dict[str, Any]], int]:
    """Liest alle noch nicht kristallisierten Chunks einer Session aus."""
    cursor = conn.cursor()
    cursor.execute("SELECT last_chunk_id FROM crystallizer_state WHERE filename = ?", (filename,))
    row = cursor.fetchone()
    last_id = row[0] if row else 0

    cursor.execute("""
        SELECT id, speaker, turn_index, content 
        FROM chunks 
        WHERE filename = ? AND id > ?
        ORDER BY id ASC
    """, (filename, last_id))

    rows = cursor.fetchall()
    chunks = [
        {"id": r[0], "speaker": r[1], "turn_index": r[2], "content": r[3]}
        for r in rows
    ]
    return chunks, last_id


EXTRACTION_PROMPT = """Du bist der hochselektive Kognitions-Filter für das Groundsole Wissenssystem.
Deine oberste Pflicht ist SIGNAL ÜBER RAUSCHEN. LangMem und Cognee dürfen NIEMALS mit Kleinigkeiten, temporären Debugging-Details, Standard-Code oder trivialem Geplänkel gefüllt werden!

ANFORDERUNGEN:
1. MAXIMAL 1 BIS 3 FAKTEN für das GESAMTE Dokument! (Nur die absoluten Kronjuwelen: Richtungsentscheidungen, tragende Leitprinzipien oder echte Heureka-Durchbrüche).
2. Wenn das Gespräch lediglich routinemäßige Implementierung, CSS/UI-Polishing, Tippfehlerkorrekturen oder alltäglichen Arbeitsfortschritt behandelt: GIB LEERE LISTEN ZURÜCK ({"facts": [], "relations": []})!
3. Was zählt als Fakt / Erkenntnis?
   - Eine verbindliche Richtungsentscheidung (z.B. "Arbeitsweise X ab sofort verboten", "Tool Y ersetzt Tool Z").
   - Ein fundamental verstandener Systemmechanismus oder Kausalzusammenhang (z.B. Prefix-Caching, deterministische Kognition).
   - Ein Heureka-Moment mit starker Resonanz ("Krass!", "WOW!", "Das ist der Kern!").
4. Formuliere zeitlos, prägnant und als kausalen Lehrsatz. Keine Chat-Nacherzählungen ("Nutzer sagte...").
5. Maximal 1 bis 3 Relationen für Cognee (nur zwischen den Kernentitäten).


Antworte zwingend im folgenden JSON-Format:
{
  "facts": [
    {
      "namespace": "ERKENNTNIS | PRINZIP | SYSTEM | ENTSCHEIDUNG",
      "key": "praegnanter_schluessel",
      "content": "Kompakte, präzise Formulierung des Leitprinzips / Beschlusses."
    }
  ],
  "relations": [
    {
      "source": "Subjekt (z.B. Emanuel)",
      "relationship": "VERBINDUNG (z.B. ERKENNT, BESCHLIESST)",
      "target": "Objekt (z.B. Deterministische_Kognition)",
      "source_type": "Person | Konzept | System",
      "target_type": "Erkenntnis | Beschluss | System"
    }
  ]
}
"""


def call_extraction_llm(turns_text: str) -> Optional[Dict[str, Any]]:
    """Sendet den Textblock an das konfigurierte Modell (Gemini, OpenRouter, OpenAI oder Ollama)."""
    provider, key, url, model = get_inference_provider()
    if provider == "none" or not url:
        return None

    prompt = EXTRACTION_PROMPT + "\n\n### ZU ANALYSIERENDER GESPRÄCHSABSCHNITT:\n" + turns_text

    if provider == "gemini":
        models = [model, "gemini-3.5-flash-lite", "gemini-2.5-flash"]
        for m in models:
            m_url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={key}"
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt}
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.1,
                    "responseMimeType": "application/json"
                }
            }
            try:
                req = urllib.request.Request(
                    m_url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=30) as resp:
                    result = json.loads(resp.read().decode("utf-8"))
                    candidates = result.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts and "text" in parts[0]:
                            raw_json = parts[0]["text"]
                            return json.loads(raw_json)
            except urllib.error.HTTPError as e:
                err_msg = e.read().decode("utf-8", errors="ignore")
                if e.code == 404:
                    continue
                print(f"⚠️ Gemini API Fehler ({m}, HTTP {e.code}): {err_msg}", file=sys.stderr)
                break
            except Exception as exc:
                print(f"⚠️ Netzwerk-/Parsing-Fehler bei Modell {m}: {exc}", file=sys.stderr)
                break
        return None
    else:
        # OpenAI, OpenRouter oder Ollama
        headers = {"Content-Type": "application/json"}
        if key:
            headers["Authorization"] = f"Bearer {key}"
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "response_format": {"type": "json_object"}
        }
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                raw_text = data["choices"][0]["message"]["content"].strip()
                return json.loads(raw_text)
        except Exception as exc:
            print(f"⚠️ Extraktions-Fehler ({provider} - {model}): {exc}", file=sys.stderr)
            return None


def run_crystallization(
    threshold: int = 10,
    flush: bool = False,
    session_file: Optional[str] = None,
    dry_run: bool = False
) -> int:
    """
    Hauptfunktion: Prüft offene Chunks, ruft bei Bedarf die Extraktion auf
    und schreibt Fakten nach LangMem und Cognee.
    Gibt die Anzahl neu kristallisierter Fakten zurück.
    """
    if not os.path.exists(BUFFER_DB_PATH):
        print(f"ℹ️ Puffer-Datenbank existiert noch nicht: {BUFFER_DB_PATH}")
        return 0

    conn = sqlite3.connect(BUFFER_DB_PATH)
    try:
        init_crystallizer_schema(conn)

        if session_file:
            target_sessions = [session_file]
        else:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT filename FROM chunks WHERE filename LIKE 'harness_%' ORDER BY id DESC")
            target_sessions = [r[0] for r in cursor.fetchall()]

        if not target_sessions:
            print("ℹ️ Keine aktive Harness-Session in memory_buffer.db gefunden.")
            return 0

        total_saved_facts = 0

        for target_session in target_sessions:
            pending_chunks, last_id = fetch_pending_chunks(conn, target_session)
            count = len(pending_chunks)

            if count == 0:
                continue

            # Wenn weniger als Threshold und kein Flush -> überspringen
            if count < threshold and not flush:
                continue

            provider, key, url, model = get_inference_provider()
            if provider == "none":
                print("ℹ️ Kein externer API-Key (Gemini/OpenRouter/OpenAI/Ollama) konfiguriert.\n"
                      "   Tier-1 In-Harness Modus aktiv: Kronjuwelen-Fakten werden beim Archivieren direkt im Chat extrahiert.", file=sys.stderr)
                return total_saved_facts

            print(f"⚡ Kristallisiere {count} Turns aus {target_session} ({provider} - {model})...")

            # Textblock für LLM aufbereiten
            text_lines = []
            max_chunk_id = last_id
            for c in pending_chunks:
                speaker_tag = "Emanuel" if c["speaker"] == "user" else "Hermes"
                text_lines.append(f"[{speaker_tag} - Turn {c['turn_index']}]:\n{c['content']}\n")
                if c["id"] > max_chunk_id:
                    max_chunk_id = c["id"]

            combined_text = "\n---\n".join(text_lines)

            # Extraktions-Call via REST
            extracted = call_extraction_llm(combined_text)
            if not extracted:
                print(f"⚠️ Keine strukturierten Daten vom Modell ({provider}) erhalten.")
                continue

            facts = extracted.get("facts", [])
            relations = extracted.get("relations", [])

            print(f"💎 Extrahiert aus {target_session}: {len(facts)} Fakten, {len(relations)} Relationen.")

            if dry_run:
                print(f"\n[DRY RUN - {target_session}] Fakten:")
                print(json.dumps(facts, indent=2, ensure_ascii=False))
                print(f"\n[DRY RUN - {target_session}] Relationen:")
                print(json.dumps(relations, indent=2, ensure_ascii=False))
                total_saved_facts += len(facts)
                continue

            # In LangMem schreiben
            saved_facts = 0
            if add_memory and facts:
                for f in facts:
                    ns = f.get("namespace", "SYSTEM")
                    k = f.get("key", "notiz")
                    content = f.get("content", "")
                    if content:
                        try:
                            add_memory(namespace=ns, key=k, content=content)
                            saved_facts += 1
                        except Exception as exc:
                            print(f"⚠️ LangMem Speicherfehler: {exc}", file=sys.stderr)

            # In Cognee Wissensgraph schreiben
            saved_relations = 0
            if add_edge and relations:
                for r in relations:
                    src = r.get("source")
                    rel = r.get("relationship")
                    dst = r.get("target")
                    src_t = r.get("source_type", "Entity")
                    dst_t = r.get("target_type", "Entity")
                    if src and rel and dst:
                        try:
                            add_edge(source_label=src, relationship=rel, target_label=dst, source_type=src_t, target_type=dst_t)
                            saved_relations += 1
                        except Exception as exc:
                            print(f"⚠️ Cognee Speicherfehler: {exc}", file=sys.stderr)

            # Cursor aktualisieren
            cursor = conn.cursor()
            now_iso = datetime.now().isoformat()
            cursor.execute("""
                INSERT INTO crystallizer_state (filename, last_chunk_id, crystallized_turns_count, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(filename) DO UPDATE SET
                    last_chunk_id = excluded.last_chunk_id,
                    crystallized_turns_count = crystallized_turns_count + excluded.crystallized_turns_count,
                    updated_at = excluded.updated_at
            """, (target_session, max_chunk_id, count, now_iso))
            conn.commit()

            print(f"✅ Cursor für {target_session} aktualisiert (letzte Chunk-ID: {max_chunk_id}). LangMem: {saved_facts}, Cognee: {saved_relations}.")
            total_saved_facts += saved_facts

        return total_saved_facts

    finally:
        conn.close()


TRANSCRIPTS_STATE_FILE = os.path.join(REPO_ROOT, "00_MEMORY", "crystallized_transcripts.json")

def load_crystallized_transcripts() -> Dict[str, str]:
    if os.path.exists(TRANSCRIPTS_STATE_FILE):
        try:
            with open(TRANSCRIPTS_STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_crystallized_transcripts(data: Dict[str, str]):
    try:
        with open(TRANSCRIPTS_STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️ Fehler beim Speichern von {TRANSCRIPTS_STATE_FILE}: {e}", file=sys.stderr)


def crystallize_transcript(transcript_path: str, dry_run: bool = False) -> int:
    """Extrahiert Fakten und Cognee-Kanten direkt aus einem archivierten Transkript."""
    if not os.path.exists(transcript_path):
        print(f"❌ Transkript existiert nicht: {transcript_path}")
        return 0

    provider, key, url, model = get_inference_provider()
    if provider == "none":
        print("ℹ️ Kein externer API-Key (Gemini/OpenRouter/OpenAI/Ollama) konfiguriert.\n"
              "   Tier-1 In-Harness Modus aktiv: Kronjuwelen-Fakten werden beim Archivieren direkt im Chat extrahiert.", file=sys.stderr)
        return 0

    fname = os.path.basename(transcript_path)
    state = load_crystallized_transcripts()
    if fname in state and not dry_run:
        print(f"ℹ️ Transkript {fname} bereits kristallisiert am {state[fname]}.")
        return 0

    with open(transcript_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    # Für Transkripte: Gesamtschau statt 20 Mikro-Splitter (max. 40.000 Zeichen Überblick)
    if len(content) > 40000:
        # Repräsentativer Querschnitt: Anfang (Kontext/Ziel) + Ende (Ergebnisse/Beschlüsse)
        analyzed_text = content[:20000] + "\n\n[... MITTELTEIL ZUR VERDICHTUNG ÜBERSPRUNGEN ...]\n\n" + content[-20000:]
    else:
        analyzed_text = content

    print(f"💎 Kristallisiere archiviertes Transkript: {fname} ({provider} - {model})...")

    total_facts = 0
    total_relations = 0

    extracted = call_extraction_llm(analyzed_text)
    if not extracted:
        extracted = {"facts": [], "relations": []}

    facts = extracted.get("facts", [])[:3]
    relations = extracted.get("relations", [])[:3]

    if dry_run:
        print(f"[{fname}] Hochverdichtete Fakten ({len(facts)}): {json.dumps(facts, ensure_ascii=False, indent=2)}")
        print(f"[{fname}] Hochverdichtete Relationen ({len(relations)}): {json.dumps(relations, ensure_ascii=False, indent=2)}")
        return len(facts)

    if add_memory and facts:
        for fitem in facts:
            ns = fitem.get("namespace", "SYSTEM")
            k = fitem.get("key", "notiz")
            text = fitem.get("content", "")
            if text:
                try:
                    add_memory(namespace=ns, key=k, content=text)
                    total_facts += 1
                except Exception:
                    pass

    if add_edge and relations:
        for r in relations:
            src = r.get("source")
            rel = r.get("relationship")
            dst = r.get("target")
            if src and rel and dst:
                try:
                    add_edge(source_label=src, relationship=rel, target_label=dst)
                    total_relations += 1
                except Exception:
                    pass

    state[fname] = datetime.now().isoformat()
    save_crystallized_transcripts(state)
    print(f"✅ Transkript {fname} erfolgreich kristallisiert. LangMem: +{total_facts}, Cognee: +{total_relations}.")

    return total_facts


def update_dynamic_state_deterministic(force: bool = False) -> bool:
    """
    Aktualisiert DYNAMIC_STATE.md rein deterministisch (0 Tokens, 0 LLM-Kosten):
    1. Bewahrt den statischen Kopfbereich (Nordstern & Leitplanken).
    2. Prüft das Revisionsdatum (Weg A): Wenn überfällig, setzt es einen dezenten Hinweis-Banner.
    3. Liest die neuesten 10 Einträge aus langmem_store.db.
    4. Liest die echten Zähler aus SQLite & Transkripten.
    """
    dynamic_state_path = os.path.join(REPO_ROOT, "00_MEMORY", "DYNAMIC_STATE.md")
    langmem_db_path = os.path.join(REPO_ROOT, "00_MEMORY", "langmem_store.db")
    transcripts_dir = os.path.join(REPO_ROOT, "00_MEMORY", "transcripts")
    summaries_dir = os.path.join(REPO_ROOT, "00_MEMORY", "summaries")

    if not os.path.exists(dynamic_state_path):
        return False

    with open(dynamic_state_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Neueste 10 Fakten aus LangMem lesen
    recent_facts = []
    if os.path.exists(langmem_db_path):
        try:
            conn = sqlite3.connect(langmem_db_path)
            c = conn.cursor()
            c.execute("SELECT namespace, key, timestamp, content FROM memories ORDER BY id DESC LIMIT 10")
            for r in c.fetchall():
                ts = r[2].split("T")[0] if "T" in r[2] else r[2][:10]
                # Bereinige Inhalt auf eine Zeile
                clean_content = " ".join(r[3].splitlines()).strip()
                recent_facts.append(f"- **[{r[0]}:{r[1]}]** ({ts}): {clean_content}")
            conn.close()
        except Exception as exc:
            print(f"⚠️ Warnung beim Lesen von LangMem: {exc}", file=sys.stderr)

    # 2. Quellen-Zähler ermitteln
    total_files = 0
    first_date = "2023-09-07"
    last_date = datetime.now().strftime("%Y-%m-%d")
    total_mb = 0.0

    if os.path.exists(transcripts_dir):
        files = [f for f in os.listdir(transcripts_dir) if f.endswith(".md")]
        total_files = len(files)
        total_size = sum(os.path.getsize(os.path.join(transcripts_dir, f)) for f in files)
        total_mb = total_size / (1024 * 1024)
        dates = []
        for f in files:
            m = re.match(r"^(\d{4}-\d{2}-\d{2})", f)
            if m:
                dates.append(m.group(1))
        if dates:
            dates.sort()
            first_date = dates[0]
            last_date = dates[-1]

    # 3. Revisions-Prüfung (Weg A): Ist der Nordstern überfällig?
    today = datetime.now().date()
    # Standard: Nächste Rekalibrierung in 40 Tagen, falls noch nicht definiert
    rev_pattern = r"\*\*Nächste strategische Rekalibrierung:\*\*.*?(\d{4}-\d{2}-\d{2})"
    rev_match = re.search(rev_pattern, content)
    
    overdue_banner = ""
    target_rev_date_str = "2026-11-15"
    if rev_match:
        target_rev_date_str = rev_match.group(1)
        try:
            target_rev_date = datetime.strptime(target_rev_date_str, "%Y-%m-%d").date()
            if today >= target_rev_date:
                overdue_banner = f"> [!IMPORTANT]\n> **STRATEGISCHE REKALIBRIERUNG ÜBERFÄLLIG (Fälligkeit: {target_rev_date_str})!**\n> Bitte prüfe mit Emanuel beim Session-Start oder via Skill `meta-zoom`, ob der strategische Nordstern und die Projektachsen ein kurzes Update benötigen.\n\n"
        except Exception:
            pass

    # 4. Zusammenbau des deterministischen Abschnitts
    facts_block = "\n".join(recent_facts) if recent_facts else "- *Keine Einträge vorhanden.*"

    deterministic_section = (
        "## 2. Letzte 10 kristallisierte Fakten & Meilensteine (Auto-Sync)\n\n"
        f"{facts_block}\n\n"
        "## 3. Deterministische Datenquellen (SSOT)\n\n"
        "- **Vektorgedächtnis:** Multi-DB SQLite in `00_MEMORY/vectors/` (Archiv + Active + Memory-Buffer).\n"
        "- **Fakten- & Wissensgraph-Speicher:** Lokales LangMem (`00_MEMORY/langmem_store.db`) und Cognee (`00_MEMORY/cognee_db`).\n\n"
        "## Quellenlage\n\n"
        f"Primaerquellen: Rohchats in `00_MEMORY/transcripts/` ({total_files} Dateien im ISO-Format `YYYY-MM-DD`, Zeitraum von {first_date} bis {last_date}, ca. {total_mb:.1f} MB).\n"
    )

    # 5. Kopfbereich isolieren (bis zu '## 2.')
    head_pattern = r"^(.*?)(?=## 2\. Letzte 10|## 2\. Deterministische|$)"
    match = re.search(head_pattern, content, flags=re.DOTALL)
    head_content = match.group(1).strip() if match else content.strip()

    # Revisions-Zeile im Header sicherstellen
    if "**Nächste strategische Rekalibrierung:**" not in head_content:
        # Nach **Strategischer Fokus:** oder nach **Aktueller Stand:** einfügen
        head_content = re.sub(
            r"(\*\*Aktueller Stand:\*\*.*?\n)",
            r"\1**Nächste strategische Rekalibrierung:** ~ Mitte November 2026 (spätestens 2026-11-15)\n",
            head_content
        )

    # Banner oben einfügen oder aktualisieren
    head_clean = re.sub(r"> \[!IMPORTANT\]\n> \*\*STRATEGISCHE REKALIBRIERUNG ÜBERFÄLLIG.*?\n\n", "", head_content, flags=re.DOTALL)
    if overdue_banner:
        # Direkt nach H1 einfügen
        head_clean = re.sub(r"(# DYNAMIC STATE[^\n]*\n+)", r"\1" + overdue_banner, head_clean)

    # Alle trailing Trenner am Ende des Kopfbereichs strikt entfernen
    while head_clean.endswith("---") or head_clean.endswith("\n") or head_clean.endswith("-"):
        head_clean = re.sub(r"[\s\n-]*---\s*$", "", head_clean).strip()

    new_full_content = head_clean.strip() + "\n\n---\n\n" + deterministic_section

    with open(dynamic_state_path, "w", encoding="utf-8") as f:
        f.write(new_full_content)

    print(f"🎯 DYNAMIC_STATE.md erfolgreich deterministisch aktualisiert ({total_files} Transkripte, 10 Fakten).")
    return True


def scan_and_crystallize_transcripts(limit: int = 5, dry_run: bool = False) -> int:
    """Scannt 00_MEMORY/transcripts/ nach noch unkristallisierten Transkripten."""
    transcripts_dir = os.path.join(REPO_ROOT, "00_MEMORY", "transcripts")
    if not os.path.exists(transcripts_dir):
        return 0

    all_files = sorted(
        [os.path.join(transcripts_dir, f) for f in os.listdir(transcripts_dir) if f.endswith(".md")],
        reverse=True
    )

    state = load_crystallized_transcripts()
    pending = [f for f in all_files if os.path.basename(f) not in state][:limit]

    if not pending:
        print("✅ Alle archivierten Transkripte sind bereits in LangMem & Cognee kristallisiert.")
        update_dynamic_state_deterministic()
        return 0

    print(f"🔍 Gefunden: {len(pending)} unkristallisierte(s) Transkript(e). Starte Extraktion...")
    total = 0
    for p in pending:
        total += crystallize_transcript(p, dry_run=dry_run)
    
    update_dynamic_state_deterministic()
    return total


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sliding-Chunk- & Transkript-Crystallizer für LangMem & Cognee")
    parser.add_argument("--threshold", type=int, default=10, help="Mindestanzahl Turns vor Puffer-Extraktions-Call")
    parser.add_argument("--flush", action="store_true", help="Erzwingt Extraktion aller offenen Puffer-Turns")
    parser.add_argument("--session", type=str, default=None, help="Gezielte Puffer-Session (z. B. harness_hermes_123.md)")
    parser.add_argument("--transcript", type=str, default=None, help="Kristallisiert ein spezifisches archiviertes Transkript")
    parser.add_argument("--scan-transcripts", action="store_true", help="Scannt 00_MEMORY/transcripts/ nach neuen Sitzungen")
    parser.add_argument("--update-state", action="store_true", help="Aktualisiert DYNAMIC_STATE.md rein deterministisch (0 Tokens)")
    parser.add_argument("--dry-run", action="store_true", help="Gibt die Extraktion nur auf stdout aus")
    args = parser.parse_args()

    if args.update_state:
        update_dynamic_state_deterministic()
    elif args.transcript:
        crystallize_transcript(args.transcript, dry_run=args.dry_run)
        update_dynamic_state_deterministic()
    elif args.scan_transcripts:
        scan_and_crystallize_transcripts(dry_run=args.dry_run)
    else:
        run_crystallization(
            threshold=args.threshold,
            flush=args.flush,
            session_file=args.session,
            dry_run=args.dry_run
        )
        update_dynamic_state_deterministic()

