#!/usr/bin/env python3
"""
Groundsole Context-Filter MCP Server (Prinzip 16)
Standardisiertes JSON-RPC 2.0 Interface über stdio.
Fängt schwere Tool-Ausgaben (Terminal-Logs, Tests, Webabrufe) ab, puffert sie lokal
in einer temporären SQLite-FTS5-Datenbank (groundsole_ctx_cache.db) und gibt
dem Modell nur relevante Signale und Treffer zurück.

Inspiriert durch das Architektur-Muster von mksglu/context-mode (MIT License),
eigenständig und autark implementiert für Groundsole.
"""

import sys
import os
import json
import sqlite3
import subprocess
import uuid
import re
import urllib.request
import urllib.error
import time
import tempfile

PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = "context-filter"
SERVER_VERSION = "1.0.0"

CACHE_DB_PATH = os.path.join(tempfile.gettempdir(), "groundsole_ctx_cache.db")
DEFAULT_MAX_LINES = 25

def get_db():
    """Initialisiert oder öffnet die lokale SQLite FTS5 Cache-Datenbank."""
    conn = sqlite3.connect(CACHE_DB_PATH)
    conn.execute("PRAGMA journal_mode = WAL;")
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS executions (
                cache_id TEXT PRIMARY KEY,
                command TEXT,
                cwd TEXT,
                exit_code INTEGER,
                total_lines INTEGER,
                created_at REAL
            )
        """)
        conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS execution_lines USING fts5(
                cache_id UNINDEXED,
                line_no UNINDEXED,
                content
            )
        """)
    return conn

def send_response(response_dict):
    """Schreibt eine JSON-RPC Antwort auf stdout."""
    raw = json.dumps(response_dict, ensure_ascii=False)
    sys.stdout.write(raw + "\n")
    sys.stdout.flush()

def handle_initialize(msg_id, params):
    return {
        "jsonrpc": "2.0",
        "id": msg_id,
        "result": {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": SERVER_NAME,
                "version": SERVER_VERSION
            }
        }
    }

def handle_tools_list(msg_id):
    tools = [
        {
            "name": "ctx_execute",
            "description": (
                "Führt einen Shell-Befehl aus und schützt das Kontextfenster vor Token-Überlauf. "
                "Ausgaben unter dem Zeilenlimit werden direkt zurückgegeben. Große Ausgaben werden "
                "in einer lokalen SQLite-FTS5-Tabelle gepuffert und auf Signalzeilen (Errors, Fails, Exit-Code) "
                "oder optionale Suchbegriffe (query) verdichtet."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Der auszuführende Shell-Befehl."
                    },
                    "cwd": {
                        "type": "string",
                        "description": "Optionales Arbeitsverzeichnis für die Ausführung."
                    },
                    "query": {
                        "type": "string",
                        "description": "Optionaler Suchbegriff, nach dem die Ausgabe gefiltert werden soll."
                    },
                    "max_lines": {
                        "type": "integer",
                        "description": "Maximal ungefiltert erlaubte Zeilen (Standard: 25)."
                    }
                },
                "required": ["command"]
            }
        },
        {
            "name": "ctx_inspect_lines",
            "description": (
                "Ruft exakte Zeilenbereiche eines zuvor gepufferten Befehlsergebnisses ab. "
                "Verwendet die cache_id aus ctx_execute."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "cache_id": {
                        "type": "string",
                        "description": "Die Cache-ID des Befehlslaufs."
                    },
                    "start_line": {
                        "type": "integer",
                        "description": "Erste abzurufende Zeilennummer (1-basiert)."
                    },
                    "end_line": {
                        "type": "integer",
                        "description": "Letzte abzurufende Zeilennummer (1-basiert, inklusive)."
                    }
                },
                "required": ["cache_id", "start_line", "end_line"]
            }
        },
        {
            "name": "ctx_search_output",
            "description": (
                "Durchsucht einen zuvor gepufferten Befehlsausstoß mittels SQLite FTS5 Volltextsuche "
                "und liefert relevante Treffer inklusive Kontextzeilen davor und danach zurück."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "cache_id": {
                        "type": "string",
                        "description": "Die Cache-ID des Laufs."
                    },
                    "query": {
                        "type": "string",
                        "description": "Der Suchbegriff oder die Suchphrase."
                    },
                    "window": {
                        "type": "integer",
                        "description": "Anzahl der Kontextzeilen vor und nach jedem Treffer (Standard: 2)."
                    }
                },
                "required": ["cache_id", "query"]
            }
        },
        {
            "name": "ctx_read_url",
            "description": (
                "Liest eine URL ein, filtert HTML-Tags/Boilerplate deterministisch heraus und liefert "
                "bei großen Seiten nur Abschnitte zurück, die zu einem Suchbegriff passen."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "Die abzurufende HTTP/HTTPS-URL."
                    },
                    "query": {
                        "type": "string",
                        "description": "Optionaler Filterbegriff für den relevanten Textabschnitt."
                    },
                    "max_lines": {
                        "type": "integer",
                        "description": "Maximale Zeilenanzahl vor Filterung (Standard: 30)."
                    }
                },
                "required": ["url"]
            }
        }
    ]
    return {
        "jsonrpc": "2.0",
        "id": msg_id,
        "result": {"tools": tools}
    }

def execute_command_filtered(command, cwd=None, query=None, max_lines=DEFAULT_MAX_LINES):
    """Führt einen Befehl aus und filtert die Ausgabe deterministisch."""
    if not cwd:
        cwd = os.getcwd()
    max_lines = int(max_lines or DEFAULT_MAX_LINES)

    try:
        proc = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            errors="replace"
        )
        output = proc.stdout or ""
        exit_code = proc.returncode
    except Exception as e:
        return {
            "exit_code": -1,
            "error": f"Ausführungsfehler: {str(e)}",
            "output": ""
        }

    lines = output.splitlines()
    total_lines = len(lines)

    # Wenn der Output kurz genug ist und keine spezielle Query gefordert wurde, direkt durchreichen
    if total_lines <= max_lines and not query:
        return {
            "exit_code": exit_code,
            "total_lines": total_lines,
            "filtered": False,
            "output": "\n".join(lines) if lines else "(Keine Ausgabe)"
        }

    # Bei großem Output: In SQLite FTS5 Datenbank sichern
    cache_id = str(uuid.uuid4())[:8]
    conn = get_db()
    with conn:
        conn.execute(
            "INSERT INTO executions (cache_id, command, cwd, exit_code, total_lines, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (cache_id, command, cwd, exit_code, total_lines, time.time())
        )
        conn.executemany(
            "INSERT INTO execution_lines (cache_id, line_no, content) VALUES (?, ?, ?)",
            [(cache_id, idx + 1, line) for idx, line in enumerate(lines)]
        )

    # Signal-Zeilen oder Query-Treffer extrahieren
    matched_lines = []
    signal_pattern = re.compile(r"(error|fatal|fail|exception|warning|traceback|syntaxerror|panic|denied)", re.IGNORECASE)

    if query:
        # FTS5 Match
        cur = conn.cursor()
        safe_query = query.replace('"', '""')
        try:
            cur.execute(
                "SELECT line_no, content FROM execution_lines WHERE cache_id = ? AND content MATCH ? ORDER BY line_no LIMIT 50",
                (cache_id, f'"{safe_query}"')
            )
            rows = cur.fetchall()
            for r in rows:
                matched_lines.append((r[0], r[1]))
        except Exception:
            # Fallback auf Python-Suche, falls FTS-Syntax fehlschlägt
            for idx, line in enumerate(lines):
                if query.lower() in line.lower():
                    matched_lines.append((idx + 1, line))
    else:
        # Automatische Signalsuche nach Fehlern/Warnungen
        for idx, line in enumerate(lines):
            if signal_pattern.search(line):
                matched_lines.append((idx + 1, line))

    # Strukturierte Rückmeldung bauen
    header = (
        f"🛡️ [Groundsole Context-Filter | Cache-ID: {cache_id}]\n"
        f"Befehl: `{command}` (Exit-Code: {exit_code}, Gesamtzeilen: {total_lines})\n"
        f"Die vollständige Ausgabe wurde gepuffert, um das Kontextfenster zu schonen."
    )

    if query:
        header += f" Filter: '{query}' ({len(matched_lines)} Treffer)\n"
    else:
        header += f" Erkannte Signale/Fehler: {len(matched_lines)}\n"

    body_parts = []
    if matched_lines:
        body_parts.append("\n--- Relevante Auszüge / Signale ---")
        for line_no, content in matched_lines[:30]:
            body_parts.append(f"Z.{line_no}: {content}")
        if len(matched_lines) > 30:
            body_parts.append(f"... (+ {len(matched_lines) - 30} weitere Treffer)")
    else:
        body_parts.append("\n(Keine Fehler- oder Signal-Muster im Output gefunden. Die ersten 5 und letzten 5 Zeilen:)")
        head_lines = lines[:5]
        tail_lines = lines[-5:] if total_lines > 5 else []
        for idx, l in enumerate(head_lines):
            body_parts.append(f"Z.{idx + 1}: {l}")
        if total_lines > 10:
            body_parts.append("...")
        for idx, l in enumerate(tail_lines):
            line_idx = total_lines - len(tail_lines) + idx + 1
            if line_idx > len(head_lines):
                body_parts.append(f"Z.{line_idx}: {l}")

    footer = (
        f"\n👉 Für Detailansicht: `ctx_inspect_lines` mit cache_id='{cache_id}' (z. B. Start/Endzeile) "
        f"oder `ctx_search_output` für Volltextsuche."
    )

    return {
        "cache_id": cache_id,
        "exit_code": exit_code,
        "total_lines": total_lines,
        "filtered": True,
        "output": header + "\n" + "\n".join(body_parts) + "\n" + footer
    }

def inspect_lines(cache_id, start_line, end_line):
    """Liest gezielt Zeilen aus einer gepufferten Ausführung."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT command, total_lines FROM executions WHERE cache_id = ?", (cache_id,))
    row = cur.fetchone()
    if not row:
        return {"error": f"Kein Eintrag für Cache-ID '{cache_id}' gefunden."}

    cmd, total_lines = row[0], row[1]
    start = max(1, int(start_line))
    end = min(total_lines, int(end_line))

    if start > end:
        return {"error": f"Ungültiger Zeilenbereich: start_line ({start}) > end_line ({end})."}

    cur.execute(
        "SELECT line_no, content FROM execution_lines WHERE cache_id = ? AND line_no >= ? AND line_no <= ? ORDER BY line_no",
        (cache_id, start, end)
    )
    lines = cur.fetchall()

    result = [f"--- Cache-ID: {cache_id} | Zeilen {start} bis {end} von {total_lines} ---"]
    for l_no, text in lines:
        result.append(f"{l_no:5d} | {text}")

    return {
        "cache_id": cache_id,
        "start_line": start,
        "end_line": end,
        "output": "\n".join(result)
    }

def search_output(cache_id, query, window=2):
    """Sucht in gepuffertem Output mit Kontextfenster vor und nach Treffern."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT command, total_lines FROM executions WHERE cache_id = ?", (cache_id,))
    exec_row = cur.fetchone()
    if not exec_row:
        return {"error": f"Kein Eintrag für Cache-ID '{cache_id}' gefunden."}

    total_lines = exec_row[1]
    window = max(0, int(window))

    # Treffer-Zeilen ermitteln
    safe_query = query.replace('"', '""')
    matched_line_nos = []
    try:
        cur.execute(
            "SELECT line_no FROM execution_lines WHERE cache_id = ? AND content MATCH ? ORDER BY line_no LIMIT 50",
            (cache_id, f'"{safe_query}"')
        )
        matched_line_nos = [r[0] for r in cur.fetchall()]
    except Exception:
        cur.execute("SELECT line_no, content FROM execution_lines WHERE cache_id = ?", (cache_id,))
        for l_no, cnt in cur.fetchall():
            if query.lower() in cnt.lower():
                matched_line_nos.append(l_no)
                if len(matched_line_nos) >= 50:
                    break

    if not matched_line_nos:
        return {
            "cache_id": cache_id,
            "query": query,
            "matches": 0,
            "output": f"Keine Treffer für '{query}' in Cache-ID '{cache_id}' (Gesamt: {total_lines} Zeilen)."
        }

    # Zeilenbereiche zusammenführen
    ranges = []
    for l_no in matched_line_nos:
        r_start = max(1, l_no - window)
        r_end = min(total_lines, l_no + window)
        if ranges and ranges[-1][1] >= r_start - 1:
            ranges[-1] = (ranges[-1][0], max(ranges[-1][1], r_end))
        else:
            ranges.append((r_start, r_end))

    output_lines = [f"--- Cache-ID: {cache_id} | {len(matched_line_nos)} Treffer für '{query}' ---"]
    for r_start, r_end in ranges:
        cur.execute(
            "SELECT line_no, content FROM execution_lines WHERE cache_id = ? AND line_no >= ? AND line_no <= ? ORDER BY line_no",
            (cache_id, r_start, r_end)
        )
        output_lines.append(f"\n[Zeilen {r_start}-{r_end}]")
        for l_no, text in cur.fetchall():
            marker = ">>" if l_no in matched_line_nos else "  "
            output_lines.append(f"{marker} {l_no:5d} | {text}")

    return {
        "cache_id": cache_id,
        "query": query,
        "matches": len(matched_line_nos),
        "output": "\n".join(output_lines)
    }

def clean_html(html_text):
    """Entfernt Tags, Skripte und Styles aus HTML deterministisch."""
    text = re.sub(r"<script.*?</script>", " ", html_text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style.*?</style>", " ", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<noscript.*?</noscript>", " ", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    text = re.sub(r"[ \t]+", " ", text)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)

def read_url_filtered(url, query=None, max_lines=30):
    """Holt Webinhalte headless ab und filtert Token-Müll vorab heraus."""
    max_lines = int(max_lines or 30)
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Groundsole-Context-Filter/1.0 (+https://github.com/gentlemani85/groundsole)"}
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw_data = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        return {"error": f"URL-Abruffehler: {str(e)}"}

    cleaned_text = clean_html(raw_data)
    lines = cleaned_text.splitlines()
    total_lines = len(lines)

    if total_lines <= max_lines and not query:
        return {
            "url": url,
            "total_lines": total_lines,
            "filtered": False,
            "output": cleaned_text
        }

    # Bei großen Texten puffern
    cache_id = str(uuid.uuid4())[:8]
    conn = get_db()
    with conn:
        conn.execute(
            "INSERT INTO executions (cache_id, command, cwd, exit_code, total_lines, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (cache_id, f"read_url: {url}", os.getcwd(), 0, total_lines, time.time())
        )
        conn.executemany(
            "INSERT INTO execution_lines (cache_id, line_no, content) VALUES (?, ?, ?)",
            [(cache_id, idx + 1, line) for idx, line in enumerate(lines)]
        )

    matched_lines = []
    if query:
        for idx, line in enumerate(lines):
            if query.lower() in line.lower():
                matched_lines.append((idx + 1, line))

    header = (
        f"🌐 [Groundsole Web-Filter | Cache-ID: {cache_id}]\n"
        f"URL: {url} (Extrahierte Textzeilen: {total_lines})\n"
    )

    body_parts = []
    if query:
        header += f"Filter: '{query}' ({len(matched_lines)} Treffer)\n"
        for line_no, content in matched_lines[:30]:
            body_parts.append(f"Z.{line_no}: {content}")
    else:
        header += f"Vorschau (erste {max_lines} Zeilen):\n"
        for idx, l in enumerate(lines[:max_lines]):
            body_parts.append(f"Z.{idx + 1}: {l}")
        if total_lines > max_lines:
            body_parts.append(f"... (+ {total_lines - max_lines} weitere Zeilen gepuffert)")

    footer = f"\n👉 Für gezielten Abruf: `ctx_inspect_lines` oder `ctx_search_output` mit cache_id='{cache_id}'."
    return {
        "cache_id": cache_id,
        "url": url,
        "total_lines": total_lines,
        "filtered": True,
        "output": header + "\n" + "\n".join(body_parts) + "\n" + footer
    }

def handle_tool_call(msg_id, tool_name, args):
    """Dispatched Werkzeugaufrufe an die passenden Handler."""
    try:
        if tool_name == "ctx_execute":
            res = execute_command_filtered(
                command=args.get("command", ""),
                cwd=args.get("cwd"),
                query=args.get("query"),
                max_lines=args.get("max_lines", DEFAULT_MAX_LINES)
            )
            text_out = res.get("output") or res.get("error", "Unbekannter Fehler")
        elif tool_name == "ctx_inspect_lines":
            res = inspect_lines(
                cache_id=args.get("cache_id", ""),
                start_line=args.get("start_line", 1),
                end_line=args.get("end_line", 20)
            )
            text_out = res.get("output") or res.get("error", "Unbekannter Fehler")
        elif tool_name == "ctx_search_output":
            res = search_output(
                cache_id=args.get("cache_id", ""),
                query=args.get("query", ""),
                window=args.get("window", 2)
            )
            text_out = res.get("output") or res.get("error", "Unbekannter Fehler")
        elif tool_name == "ctx_read_url":
            res = read_url_filtered(
                url=args.get("url", ""),
                query=args.get("query"),
                max_lines=args.get("max_lines", 30)
            )
            text_out = res.get("output") or res.get("error", "Unbekannter Fehler")
        else:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32601, "message": f"Tool '{tool_name}' nicht gefunden."}
            }

        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": text_out
                    }
                ]
            }
        }
    except Exception as e:
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {"code": -32000, "message": f"Interner Tool-Fehler: {str(e)}"}
        }

def main():
    """MCP JSON-RPC Loop über stdin/stdout."""
    sys.stdin.reconfigure(encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")

    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            line = line.strip()
            if not line:
                continue

            msg = json.loads(line)
            msg_id = msg.get("id")
            method = msg.get("method")
            params = msg.get("params", {})

            if method == "initialize":
                resp = handle_initialize(msg_id, params)
                send_response(resp)
            elif method == "notifications/initialized":
                pass
            elif method == "tools/list":
                resp = handle_tools_list(msg_id)
                send_response(resp)
            elif method == "tools/call":
                tool_name = params.get("name")
                args = params.get("arguments", {})
                resp = handle_tool_call(msg_id, tool_name, args)
                send_response(resp)
            elif method == "ping":
                send_response({"jsonrpc": "2.0", "id": msg_id, "result": {}})
            else:
                if msg_id is not None:
                    send_response({
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "error": {"code": -32601, "message": f"Method not found: {method}"}
                    })
        except Exception as e:
            sys.stderr.write(f"[Context-Filter MCP Error] {e}\n")
            sys.stderr.flush()

if __name__ == "__main__":
    main()
