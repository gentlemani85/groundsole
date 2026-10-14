#!/usr/bin/env python3
"""
scripts/dreaming.py

Groundsole Dreaming – Biophysikalische Gedächtnis-Konsolidierung (Prinzip 14)
Konsolidierungs- und Audit-Zyklus im Ruhezustand (analog zum biologischen Träumen):
1. Zeitlicher Verfall (Temporal Decay): Markiert abgelaufene Termine/Fristen als [STATUS: EXPIRED].
2. Semantische FastEmbed-Clusterung: Erkennt thematisch verwandte Fakten über Key-Grenzen hinweg.
3. Widerspruchs- & Redundanz-Audit:
   - Hebt Fakt B Fakt A auf? -> [STATUS: DEPRECATED | Abgelöst am ...]
   - Wiederholt Fakt B Fakt A? -> [STATUS: DEPRECATED | Redundant zu ...]
4. Cognee Knowledge Graph Sync: Synchronisiert Entwertungen mit cognee_db.
5. DYNAMIC_STATE-Entschlackung: Bereinigt alte Meilensteine zur Token-Schonung.
6. Idempotentes Caching: Dauerhafte Sicherung geprüfter Paare in SQLite (0 wiederholte Kosten).
"""

import os
import sys
import re
import json
import sqlite3
import urllib.request
import urllib.error
import argparse
import time
import numpy as np
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEMORY_DIR = os.path.join(REPO_ROOT, "00_MEMORY")
LANGMEM_DB_PATH = os.path.join(MEMORY_DIR, "langmem_store.db")
COGNEE_DB_PATH = os.path.join(MEMORY_DIR, "cognee", "databases", "cognee_db")
DYNAMIC_STATE_PATH = os.path.join(MEMORY_DIR, "DYNAMIC_STATE.md")
HERMES_ENV_PATH = os.path.expanduser("~/.hermes/.env")
MODEL_NAME = "jinaai/jina-embeddings-v2-base-de"

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
        os.path.expanduser("~/.hermes/.env"),
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


def call_consolidation_check(fact_a: Dict[str, Any], fact_b: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Fragt das verfügbare Modell (Gemini, OpenRouter, OpenAI oder Ollama),
    ob Fakt B (neuer) Fakt A (älter) aufhebt oder wiederholt (Redundanz).
    """
    provider, key, url, model = get_inference_provider()
    if provider == "none" or not url:
        return None

    prompt = f"""Du bist der Kognitions-Konsolidierer für das lokale Gedächtnis (Groundsole Dreaming).
Prüfe zwei Einträge aus derselben Wissensdomäne auf zeitliche Widersprüche oder Redundanz:

[ÄLTERER EINTRAG A] ({fact_a['timestamp'][:10]}) - {fact_a['namespace']} / {fact_a['key']}:
"{fact_a['content']}"

[NEUERER EINTRAG B] ({fact_b['timestamp'][:10]}) - {fact_b['namespace']} / {fact_b['key']}:
"{fact_b['content']}"

FRAGE:
1. Widerspricht Fakt B Fakt A fundamental, oder löst er ihn ab? (-> action: "deprecate_older")
2. Sagt Fakt B im Kern dasselbe wie Fakt A (Redundanz / Doppelung), sodass der ältere Eintrag entbehrlich ist? (-> action: "merge_redundant")
3. Ergänzen sich beide sinnvoll oder behandeln unterschiedliche Aspekte? (-> action: "keep_both")

Antworte zwingend im folgenden JSON-Format:
{{
  "action": "deprecate_older" | "merge_redundant" | "keep_both",
  "reason": "Kurze, präzise Begründung in 1 Satz auf Deutsch."
}}
"""

    if provider == "gemini":
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.0, "responseMimeType": "application/json"}
        }
    else:
        headers = {"Content-Type": "application/json"}
        if key:
            headers["Authorization"] = f"Bearer {key}"
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0,
            "response_format": {"type": "json_object"}
        }

    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if provider == "gemini":
                raw_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            else:
                raw_text = data["choices"][0]["message"]["content"].strip()
            return json.loads(raw_text)
    except Exception as exc:
        print(f"⚠️ Konsolidierungs-Check ({provider}) fehlgeschlagen: {exc}", file=sys.stderr)
        return None



def audit_temporal_decay(conn: sqlite3.Connection, apply_changes: bool = False) -> List[Dict[str, Any]]:
    """
    Spürt situative Notizen, Termine und Fristen auf, die strikt in der Vergangenheit liegen.
    Schützt echte Erkenntnisse und Prinzipien vor versehentlichem Verfall.
    """
    c = conn.cursor()
    c.execute("""
        SELECT id, timestamp, namespace, key, content 
        FROM memories 
        WHERE content NOT LIKE '[STATUS: DEPRECATED%' 
          AND content NOT LIKE '[STATUS: EXPIRED%'
    """)
    rows = c.fetchall()

    today = datetime.now()
    expired_list = []

    for r in rows:
        m_id, ts, ns, key, content = r[0], r[1], r[2], r[3], r[4]
        # Nur wenn explizit terminlicher Charakter vorliegt
        is_termin_context = (
            ns in ("Termine", "Termin", "Fristen") or
            "termin" in key.lower() or
            "deadline" in key.lower() or
            "frist bis" in content.lower() or
            "termin am" in content.lower() or
            "vorregistrierung" in content.lower()
        )

        if not is_termin_context:
            continue

        # Datums-Parsing (DD.MM.YYYY)
        matches = re.finditer(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", content)
        for m in matches:
            d, m_num, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
            try:
                target_dt = datetime(y, m_num, d)
                if target_dt < today:
                    expired_list.append({
                        "id": m_id,
                        "key": key,
                        "date_str": target_dt.strftime("%d.%m.%Y"),
                        "content": content
                    })
                    break
            except ValueError:
                pass

    if apply_changes and expired_list:
        for item in expired_list:
            new_text = f"[STATUS: EXPIRED | Termin {item['date_str']} abgelaufen]: {item['content']}"
            c.execute("UPDATE memories SET content = ? WHERE id = ?", (new_text, item["id"]))
        conn.commit()

    return expired_list


def ensure_memory_embeddings(conn: sqlite3.Connection, active_records: List[Dict[str, Any]]):
    """
    Berechnet Embeddings für neue LangMem-Fakten und sichert sie dauerhaft in memory_embeddings.
    Dauert nur beim ersten Mal kurz; danach 0 Millisekunden.
    """
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS memory_embeddings (
            id INTEGER PRIMARY KEY,
            vector BLOB,
            updated_at TEXT
        )
    """)
    conn.commit()

    c.execute("SELECT id FROM memory_embeddings")
    existing_ids = {row[0] for row in c.fetchall()}

    missing_records = [r for r in active_records if r["id"] not in existing_ids]
    if not missing_records:
        return

    print(f"⚡ Vektoriere {len(missing_records)} neue LangMem-Fakten mit FastEmbed...")
    from fastembed import TextEmbedding
    model = TextEmbedding(model_name=MODEL_NAME)

    batch_size = 32
    for i in range(0, len(missing_records), batch_size):
        chunk = missing_records[i:i + batch_size]
        texts = [f"{r['namespace']} {r['key']}: {r['content'][:400]}" for r in chunk]
        embs = list(model.embed(texts, batch_size=batch_size))
        
        insert_rows = []
        now_str = datetime.now().isoformat()
        for rec, vec in zip(chunk, embs):
            vec_bytes = np.array(vec, dtype=np.float32).tobytes()
            insert_rows.append((rec["id"], vec_bytes, now_str))

        c.executemany("INSERT OR REPLACE INTO memory_embeddings (id, vector, updated_at) VALUES (?, ?, ?)", insert_rows)
        conn.commit()


def audit_semantic_clusters_and_conflicts(conn: sqlite3.Connection, apply_changes: bool = False, min_sim: float = 0.74) -> Dict[str, Any]:
    """
    Findet thematisch überlappende Fakten über Key-Grenzen hinweg mittels FastEmbed Cosine-Similarity
    und prüft sie mit Gemini auf Widersprüche und Redundanzen.
    """
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS dreaming_checked_pairs (
            pair_hash TEXT PRIMARY KEY,
            result TEXT,
            checked_at TEXT
        )
    """)
    conn.commit()

    c.execute("""
        SELECT id, timestamp, namespace, key, content 
        FROM memories 
        WHERE content NOT LIKE '[STATUS: DEPRECATED%' 
          AND content NOT LIKE '[STATUS: EXPIRED%'
        ORDER BY timestamp ASC
    """)
    rows = c.fetchall()

    records = [
        {"id": r[0], "timestamp": r[1], "namespace": r[2], "key": r[3], "content": r[4]}
        for r in rows
    ]

    if len(records) < 2:
        return {"total_scanned": len(records), "deprecations": [], "redundancies": []}

    ensure_memory_embeddings(conn, records)

    # Vektoren laden
    c.execute("SELECT id, vector FROM memory_embeddings")
    vector_map = {row[0]: np.frombuffer(row[1], dtype=np.float32) for row in c.fetchall()}

    valid_records = [r for r in records if r["id"] in vector_map]
    if not valid_records:
        return {"total_scanned": len(records), "deprecations": [], "redundancies": []}

    matrix = np.array([vector_map[r["id"]] for r in valid_records], dtype=np.float32)
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    matrix = matrix / np.maximum(norms, 1e-9)

    # 2 Millisekunden Matrix-Multiplikation
    sim_matrix = np.dot(matrix, matrix.T)

    c.execute("SELECT pair_hash, result FROM dreaming_checked_pairs")
    already_checked = {row[0]: row[1] for row in c.fetchall()}

    api_key = get_google_api_key()
    deprecations = []
    redundancies = []

    # Finde Kandidaten (entweder gleicher Key ODER Cosine-Similarity >= min_sim)
    candidate_pairs = []
    for i in range(len(valid_records)):
        for j in range(i + 1, len(valid_records)):
            older = valid_records[i]
            newer = valid_records[j]
            score = float(sim_matrix[i, j])

            same_key = (older["namespace"] == newer["namespace"] and older["key"] == newer["key"])
            if same_key or score >= min_sim:
                candidate_pairs.append((older, newer, score))

    # Sortiere nach höchster Relevanz / Ähnlichkeit
    candidate_pairs.sort(key=lambda x: x[2], reverse=True)

    # Max 25 ungescannte Checks pro Lauf zur Kosten- und Zeit-Kontrolle (~0,002 €)
    checks_performed = 0
    max_new_checks = 25

    for older, newer, score in candidate_pairs:
        pair_hash = f"{older['id']}::{newer['id']}"

        if pair_hash in already_checked:
            try:
                check = json.loads(already_checked[pair_hash])
            except Exception:
                check = None
        else:
            if not api_key or checks_performed >= max_new_checks:
                continue

            check = call_gemini_consolidation_check(api_key, older, newer)
            checks_performed += 1
            res_str = json.dumps(check or {})
            c.execute(
                "INSERT OR REPLACE INTO dreaming_checked_pairs (pair_hash, result, checked_at) VALUES (?, ?, ?)",
                (pair_hash, res_str, datetime.now().isoformat())
            )
            conn.commit()

        if not check:
            continue

        act = check.get("action")
        if act == "deprecate_older":
            deprecations.append({
                "target_id": older["id"],
                "older_key": older["key"],
                "newer_key": newer["key"],
                "score": score,
                "reason": check.get("reason", "Ablösung durch neueren Beschluss"),
                "older_content": older["content"],
                "newer_timestamp": newer["timestamp"][:10]
            })
        elif act == "merge_redundant":
            redundancies.append({
                "target_id": older["id"],
                "older_key": older["key"],
                "newer_key": newer["key"],
                "score": score,
                "reason": check.get("reason", "Redundante Doppelung"),
                "older_content": older["content"],
                "newer_timestamp": newer["timestamp"][:10]
            })

    # Änderungen anwenden
    if apply_changes:
        for d in deprecations:
            new_text = f"[STATUS: DEPRECATED | Abgelöst am {d['newer_timestamp']} durch '{d['newer_key']}']: {d['older_content']}"
            c.execute("UPDATE memories SET content = ? WHERE id = ?", (new_text, d["target_id"]))

        for r in redundancies:
            new_text = f"[STATUS: DEPRECATED | Redundant zu '{r['newer_key']}' ({r['newer_timestamp']})]: {r['older_content']}"
            c.execute("UPDATE memories SET content = ? WHERE id = ?", (new_text, r["target_id"]))

        conn.commit()

    return {
        "total_scanned": len(valid_records),
        "candidate_pairs": len(candidate_pairs),
        "new_checks_made": checks_performed,
        "deprecations": deprecations,
        "redundancies": redundancies
    }


def audit_cognee_graph(deprecated_keys: List[str] = None, apply_changes: bool = False) -> Dict[str, Any]:
    """
    Synchronisiert entwertete Fakten mit dem Cognee Wissensgraphen (cognee_db).
    """
    if not os.path.exists(COGNEE_DB_PATH):
        return {"status": "skipped", "message": "cognee_db existiert nicht."}

    conn = sqlite3.connect(COGNEE_DB_PATH)
    c = conn.cursor()

    c.execute("""
        SELECT e.id, n1.label, e.relationship_name, n2.label, e.attributes, e.created_at
        FROM edges e
        JOIN nodes n1 ON e.source_node_id = n1.id
        JOIN nodes n2 ON e.destination_node_id = n2.id
        ORDER BY e.created_at ASC
    """)
    edges = c.fetchall()

    deprecated_edges = 0
    updated_edges = 0

    for e in edges:
        attrs = {}
        if e[4]:
            try:
                attrs = json.loads(e[4])
            except Exception:
                pass
        if attrs.get("status") == "deprecated":
            deprecated_edges += 1

    if apply_changes and deprecated_keys:
        for k in deprecated_keys:
            c.execute("""
                SELECT e.id, e.attributes FROM edges e
                JOIN nodes n2 ON e.destination_node_id = n2.id
                WHERE n2.label LIKE ?
            """, (f"%{k}%",))
            for row in c.fetchall():
                eid, attr_str = row[0], row[1]
                attrs = {}
                if attr_str:
                    try:
                        attrs = json.loads(attr_str)
                    except Exception:
                        pass
                if attrs.get("status") != "deprecated":
                    attrs["status"] = "deprecated"
                    attrs["deprecated_at"] = datetime.now().isoformat()
                    c.execute("UPDATE edges SET attributes = ? WHERE id = ?", (json.dumps(attrs), eid))
                    updated_edges += 1
        conn.commit()

    conn.close()
    return {
        "total_edges": len(edges),
        "deprecated_edges": deprecated_edges,
        "updated_edges": updated_edges
    }


def prune_dynamic_state(apply_changes: bool = False) -> Dict[str, Any]:
    """
    Prüft DYNAMIC_STATE.md auf veraltete historische Einträge und hält die Kopf-Datei schlank.
    """
    if not os.path.exists(DYNAMIC_STATE_PATH):
        return {"status": "skipped", "message": "DYNAMIC_STATE.md nicht gefunden."}

    with open(DYNAMIC_STATE_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.splitlines()
    cleaned_lines = []
    removed_count = 0
    in_next_steps = False

    for line in lines:
        if line.startswith("## 2. Nächste geplante Schritte") or line.startswith("## 2. Letzte 10 kristallisierte Fakten"):
            in_next_steps = True

        if in_next_steps and "Abgeschlossen ✅" in line:
            date_match = re.search(r"\*\*(\d{1,2})\.\s+([A-Za-zä]+)\s+(\d{4})", line)
            if date_match:
                removed_count += 1
                continue

        cleaned_lines.append(line)

    if apply_changes and removed_count > 0:
        with open(DYNAMIC_STATE_PATH, "w", encoding="utf-8") as f:
            f.write("\n".join(cleaned_lines) + "\n")

    return {
        "pruned_milestones": removed_count,
        "applied": apply_changes
    }


def run_dreaming(apply_changes: bool = False) -> Dict[str, Any]:
    """Führt den vollen Groundsole Dreaming Konsolidierungs-Zyklus aus."""
    print("🌙 Starte Groundsole Deep Dreaming Konsolidierungs-Zyklus...")
    
    conn = sqlite3.connect(LANGMEM_DB_PATH)
    
    # 1. Zeitlicher Verfall (Expired State)
    expired = audit_temporal_decay(conn, apply_changes=apply_changes)

    # 2. Semantische FastEmbed-Clusterung, Widerspruchs- & Redundanz-Audit
    cluster_res = audit_semantic_clusters_and_conflicts(conn, apply_changes=apply_changes)
    conn.close()

    # 3. Cognee Graph Synchronisation
    dep_keys = [d["older_key"] for d in cluster_res.get("deprecations", [])] + [r["older_key"] for r in cluster_res.get("redundancies", [])]
    cognee_res = audit_cognee_graph(deprecated_keys=dep_keys, apply_changes=apply_changes)

    # 4. Kopf-Dateien Entschlackung
    dynamic_res = prune_dynamic_state(apply_changes=apply_changes)

    mode_str = "APPLY (Änderungen geschrieben)" if apply_changes else "DRY-RUN (Nur Analyse)"

    print("\n" + "="*65)
    print("📋 GROUNDSOLE DEEP DREAMING REPORT")
    print("="*65)
    print(f"Modus: {mode_str}")
    print(f"⏳ Zeitlicher Verfall: {len(expired)} abgelaufene Termine/Fristen erkannt [EXPIRED].")
    if expired:
        for ex in expired[:5]:
            print(f"  • Abgelaufen: '{ex['key']}' ({ex['date_str']})")

    print(f"\n🧠 LangMem Cluster-Audit: {cluster_res.get('total_scanned', 0)} Fakten | {cluster_res.get('candidate_pairs', 0)} thematische Paare.")
    print(f"  • Neue KI-Checks: {cluster_res.get('new_checks_made', 0)} | Widersprüche: {len(cluster_res.get('deprecations', []))} | Redundanzen: {len(cluster_res.get('redundancies', []))}")

    if cluster_res.get("deprecations"):
        print("\n⚡ Aufgespürte Widersprüche / Abgelöste Beschlüsse:")
        for d in cluster_res["deprecations"]:
            status_tag = "✅ Entwertet" if apply_changes else "⚠️ Veraltet"
            print(f"  • {status_tag}: '{d['older_key']}' (Sim: {d['score']:.2f}) -> Grund: {d['reason']}")

    if cluster_res.get("redundancies"):
        print("\n📦 Aufgespürte Redundanzen (Fakten-Synthese):")
        for r in cluster_res["redundancies"]:
            status_tag = "✅ Konsolidiert" if apply_changes else "⚠️ Redundant"
            print(f"  • {status_tag}: '{r['older_key']}' (Sim: {r['score']:.2f}) -> Grund: {r['reason']}")

    print(f"\n🕸️ Cognee Graph: {cognee_res.get('total_edges', 0)} Relationen überprüft ({cognee_res.get('updated_edges', 0)} Kanten synchronisiert).")
    print(f"📄 DYNAMIC_STATE: {dynamic_res.get('pruned_milestones', 0)} alte Meilensteine entschlackt.")
    print("="*65 + "\n")

    return {
        "timestamp": datetime.now().isoformat(),
        "mode": mode_str,
        "expired": len(expired),
        "deprecations": len(cluster_res.get("deprecations", [])),
        "redundancies": len(cluster_res.get("redundancies", [])),
        "cognee_updated": cognee_res.get("updated_edges", 0)
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Groundsole Deep Dreaming – Biophysikalische Gedächtnis-Konsolidierung")
    parser.add_argument("--apply", action="store_true", help="Wendet gefundene Entwertungen & Bereinigungen real an")
    parser.add_argument("--dry-run", action="store_true", help="Führt nur die semantische Analyse ohne Änderungen durch")
    args = parser.parse_args()

    apply_flag = args.apply and not args.dry_run
    run_dreaming(apply_changes=apply_flag)
