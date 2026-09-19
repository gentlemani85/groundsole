#!/usr/bin/env python3
"""
Groundsole Vector Indexer (FastEmbed / Jina ONNX)
Increments and indexes session transcripts into 00_MEMORY/vectors/active.db.
Supports incremental hashing so only new or modified transcripts are processed.
"""

import os
import re
import sys
import glob
import sqlite3
import hashlib
import json
import argparse
from datetime import datetime
from typing import List, Dict, Tuple, Optional
import numpy as np

def find_workspace_root():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_root = os.path.dirname(os.path.dirname(script_dir))
    if os.path.exists(os.path.join(workspace_root, "00_MEMORY")):
        return workspace_root
    if os.path.exists(os.path.join(os.getcwd(), "00_MEMORY")):
        return os.getcwd()
    return workspace_root

WORKSPACE_DIR = find_workspace_root()
RAW_CHATS_DIR = os.path.join(WORKSPACE_DIR, "00_MEMORY", "transcripts")
VECTORS_DIR = os.path.join(WORKSPACE_DIR, "00_MEMORY", "vectors")
os.makedirs(VECTORS_DIR, exist_ok=True)
DB_PATH = os.path.join(VECTORS_DIR, "memory_active.db")
BUFFER_DB_PATH = os.path.join(VECTORS_DIR, "memory_buffer.db")

MODEL_NAME = "jinaai/jina-embeddings-v2-base-de"

def init_db(db_path: str = DB_PATH):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS indexed_files (
            filename TEXT PRIMARY KEY,
            file_hash TEXT NOT NULL,
            indexed_at TEXT NOT NULL,
            chunk_count INTEGER NOT NULL,
            title TEXT,
            date_str TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            chunk_index INTEGER NOT NULL,
            speaker TEXT,
            timestamp_str TEXT,
            header_context TEXT,
            content TEXT NOT NULL,
            token_count INTEGER,
            content_hash TEXT,
            embedding BLOB,
            FOREIGN KEY (filename) REFERENCES indexed_files(filename) ON DELETE CASCADE
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_file ON chunks(filename)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_speaker ON chunks(speaker)")
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_chunks_content_hash ON chunks(content_hash)")
    conn.commit()
    conn.close()

def get_file_hash(filepath: str) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

def parse_transcript(filepath: str) -> Tuple[Dict, List[Dict]]:
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    fname = os.path.basename(filepath)
    title_match = re.match(r"^#\s+(.+)$", content, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else fname.replace(".md", "")
    date_match = re.search(r"(\d{4}-\d{2}-\d{2})", fname)
    date_str = date_match.group(1) if date_match else "unknown"

    meta = {"filename": fname, "title": title, "date_str": date_str}

    h2_pattern = re.compile(r"^##\s+([^\n]+)", re.MULTILINE)
    sections = []
    matches = list(h2_pattern.finditer(content))

    for i, m in enumerate(matches):
        h2_text = m.group(1).strip()
        start_pos = m.end()
        end_pos = matches[i+1].start() if i+1 < len(matches) else len(content)
        sec_body = content[start_pos:end_pos].strip()

        speaker = "Assistant" if any(w in h2_text.lower() for w in ["assistant", "gemini", "antigravity", "claude", "hermes", "ai", "bot"]) else "User"
        ts_match = re.search(r"\(([^)]+)\)", h2_text)
        ts_str = ts_match.group(1) if ts_match else ""

        sections.append({
            "speaker": speaker,
            "timestamp_str": ts_str,
            "header": h2_text,
            "content": sec_body
        })

    # Chunking
    chunks = []
    for s in sections:
        body = s["content"]
        if not body:
            continue
        max_chunk_chars = 1500
        paragraphs = body.split("\n\n")
        current_chunk = []
        current_len = 0

        for p in paragraphs:
            p_strip = p.strip()
            if not p_strip:
                continue
            if current_len + len(p_strip) > max_chunk_chars and current_chunk:
                chunks.append({
                    "speaker": s["speaker"],
                    "timestamp_str": s["timestamp_str"],
                    "header_context": s["header"],
                    "content": "\n\n".join(current_chunk),
                    "token_count": int(current_len / 4)
                })
                current_chunk = [p_strip]
                current_len = len(p_strip)
            else:
                current_chunk.append(p_strip)
                current_len += len(p_strip)

        if current_chunk:
            chunks.append({
                "speaker": s["speaker"],
                "timestamp_str": s["timestamp_str"],
                "header_context": s["header"],
                "content": "\n\n".join(current_chunk),
                "token_count": int(current_len / 4)
            })

    return meta, chunks

def index_file(filepath: str, embedding_model, db_path: str = DB_PATH) -> int:
    init_db(db_path)
    meta, chunks = parse_transcript(filepath)
    if not chunks:
        return 0

    texts_to_embed = [c["content"] for c in chunks]
    embeddings = list(embedding_model.embed(texts_to_embed))

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("DELETE FROM chunks WHERE filename=?", (meta["filename"],))
    c.execute("DELETE FROM indexed_files WHERE filename=?", (meta["filename"],))

    fhash = get_file_hash(filepath)
    now = datetime.now().isoformat()
    c.execute(
        "INSERT INTO indexed_files (filename, file_hash, indexed_at, chunk_count, title, date_str) VALUES (?, ?, ?, ?, ?, ?)",
        (meta["filename"], fhash, now, len(chunks), meta["title"], meta["date_str"])
    )

    for idx, (chunk, emb) in enumerate(zip(chunks, embeddings)):
        emb_blob = np.array(emb, dtype=np.float32).tobytes()
        chash = hashlib.md5(chunk["content"].encode("utf-8")).hexdigest()
        c.execute("""
            INSERT OR IGNORE INTO chunks (filename, chunk_index, speaker, timestamp_str, header_context, content, token_count, content_hash, embedding)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (meta["filename"], idx, chunk["speaker"], chunk["timestamp_str"], chunk["header_context"], chunk["content"], chunk["token_count"], chash, emb_blob))

    conn.commit()
    conn.close()
    return len(chunks)

def main():
    parser = argparse.ArgumentParser(description="Groundsole Vector Indexer")
    parser.add_argument("--file", help="Specific transcript file to index")
    parser.add_argument("--all", action="store_true", help="Scan and index all unindexed transcripts")
    args = parser.parse_args()

    try:
        from fastembed import TextEmbedding
    except ImportError:
        print("❌ fastembed is not installed. Please install it in your venv: pip install fastembed numpy")
        sys.exit(1)

    print(f"Loading embedding model: {MODEL_NAME}...")
    model = TextEmbedding(model_name=MODEL_NAME)

    if args.file:
        fpath = os.path.abspath(args.file)
        print(f"Indexing single file: {fpath}")
        count = index_file(fpath, model)
        print(f"✅ Indexed {count} chunks for {os.path.basename(fpath)}")
    else:
        files = sorted(glob.glob(os.path.join(RAW_CHATS_DIR, "*.md")))
        print(f"Found {len(files)} transcripts in {RAW_CHATS_DIR}")
        init_db(DB_PATH)
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        indexed = {row[0]: row[1] for row in c.execute("SELECT filename, file_hash FROM indexed_files").fetchall()}
        conn.close()

        updated_count = 0
        for f in files:
            fname = os.path.basename(f)
            curr_hash = get_file_hash(f)
            if fname not in indexed or indexed[fname] != curr_hash:
                print(f"Processing: {fname}")
                c_count = index_file(f, model)
                updated_count += 1

        print(f"✅ Processing complete. {updated_count} files indexed/updated.")

if __name__ == "__main__":
    main()
