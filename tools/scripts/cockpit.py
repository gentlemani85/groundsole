#!/usr/bin/env python3
"""
scripts/cockpit.py

Groundsole Cockpit – Plattformunabhängige lokale Web-Zentrale (v2.6)
Funktioniert 100 % lokal ohne Cloud- oder externe CDN-Abhängigkeiten.
- HTTP-Server auf http://127.0.0.1:8765 (Standardbibliothek http.server)
- Dynamische Browser-Erkennung (Chrome, Edge, Brave, Chromium für --app Modus; Fallback auf Standardbrowser)
- Live-Streaming von Skriptausgaben (ReadableStream)
- Echtzeit-Metriken (Transkripte, LangMem-Fakten, Vektoren, System-Logs)
"""

import os
import sys
import json
import sqlite3
import subprocess
import glob
import time
import urllib.request
import urllib.error
from datetime import datetime
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from typing import Optional, Tuple, List, Dict, Any


PORT = 8765
HOST = "127.0.0.1"

def find_workspace_root() -> str:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_root = os.path.dirname(script_dir)
    if os.path.exists(os.path.join(workspace_root, "00_MEMORY")):
        return workspace_root
    workspace_root_framework = os.path.dirname(workspace_root)
    if os.path.exists(os.path.join(workspace_root_framework, "00_MEMORY")):
        return workspace_root_framework
    if os.path.exists(os.path.join(os.getcwd(), "00_MEMORY")):
        return os.getcwd()
    return workspace_root

REPO_ROOT = find_workspace_root()
SCRIPTS_DIR = os.path.join(REPO_ROOT, "scripts")
if not os.path.exists(SCRIPTS_DIR):
    SCRIPTS_DIR = os.path.join(REPO_ROOT, "tools", "scripts")

MEMORY_DIR = os.path.join(REPO_ROOT, "00_MEMORY")
LANGMEM_DB_PATH = os.path.join(MEMORY_DIR, "langmem_store.db")

VENV_PYTHON = os.path.expanduser("~/.local/venv/bin/python3")
if not os.path.exists(VENV_PYTHON):
    VENV_PYTHON = sys.executable

# Bekannte Log-Pfade (mit graceful Fallback)
SYNC_LOG = os.path.expanduser("~/Library/Logs/groundsole_memory_sync.log")
WORKSPACE_BACKUP_LOG = os.path.expanduser("~/.gemini/backups/launchd_backup.log")
if not os.path.exists(WORKSPACE_BACKUP_LOG) and os.path.exists(os.path.expanduser("~/.gemini/backups/launchd_siddhanta.log")):
    WORKSPACE_BACKUP_LOG = os.path.expanduser("~/.gemini/backups/launchd_siddhanta.log")

ANTIGRAVITY_BACKUP_LOG = os.path.expanduser("~/.gemini/backups/launchd_antigravity.log")
HYGIENE_LOG = os.path.expanduser("~/Library/Logs/groundsole_system_hygiene.log")


def get_stats() -> Dict[str, Any]:
    """Sammelt Live-Metriken über das Wissensfundament und Systemdienste."""
    t_dir = os.path.join(MEMORY_DIR, "transcripts")
    t_count = len(glob.glob(os.path.join(t_dir, "*.md"))) if os.path.exists(t_dir) else 0

    f_active, f_total = 0, 0
    if os.path.exists(LANGMEM_DB_PATH):
        try:
            conn = sqlite3.connect(LANGMEM_DB_PATH)
            f_total = conn.execute("SELECT count(*) FROM memories").fetchone()[0]
            f_active = conn.execute(
                "SELECT count(*) FROM memories WHERE content NOT LIKE '[STATUS: DEPRECATED%' AND content NOT LIKE '[STATUS: EXPIRED%'"
            ).fetchone()[0]
            conn.close()
        except Exception:
            pass

    v_count = 0
    v_dirs = glob.glob(os.path.join(MEMORY_DIR, "*vector*"))
    for vd in v_dirs:
        if os.path.isdir(vd):
            for db_f in glob.glob(os.path.join(vd, "*.db")):
                try:
                    conn = sqlite3.connect(db_f)
                    cnt = conn.execute("SELECT count(*) FROM chunks").fetchone()[0]
                    v_count += cnt
                    conn.close()
                except Exception:
                    pass
        elif vd.endswith(".db"):
            try:
                conn = sqlite3.connect(vd)
                cnt = conn.execute("SELECT count(*) FROM chunks").fetchone()[0]
                v_count += cnt
                conn.close()
            except Exception:
                pass

    def read_last_log_info(path: str) -> str:
        if not os.path.exists(path):
            return "Bereit"
        try:
            mtime = os.path.getmtime(path)
            dt = datetime.fromtimestamp(mtime).strftime("%d.%m. %H:%M")
            with open(path, "r", encoding="utf-8", errors="ignore") as fp:
                lines = [l.strip() for l in fp if l.strip()]
                last = lines[-1] if lines else "Aktiv"
                if len(last) > 70:
                    last = last[:70] + "..."
            return f"{dt} Uhr · {last}"
        except Exception as e:
            return f"Info: {e}"

    return {
        "transcripts": t_count,
        "langmem_active": f_active,
        "langmem_total": f_total,
        "vectors": v_count,
        "sync_log": read_last_log_info(SYNC_LOG),
        "workspace_backup_log": read_last_log_info(WORKSPACE_BACKUP_LOG),
        "antigravity_backup_log": read_last_log_info(ANTIGRAVITY_BACKUP_LOG),

        "hygiene_log": read_last_log_info(HYGIENE_LOG),
        "updated_at": datetime.now().strftime("%H:%M:%S")
    }

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Groundsole Cockpit</title>
  <style>
    :root {
      --bg: #F8FAFC;
      --surface: #FFFFFF;
      --surface-subtle: #F1F5F9;
      --border: #E2E8F0;
      --border-strong: #CBD5E1;
      --text-main: #0F172A;
      --text-muted: #475569;
      --text-faint: #94A3B8;
      --primary: #2563EB;
      --primary-hover: #1D4ED8;
      --success-bg: #DCFCE7;
      --success-text: #166534;
      --warning-bg: #FEF3C7;
      --warning-text: #92400E;
      --terminal-bg: #0B1120;
      --terminal-text: #E2E8F0;
      --font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      --font-mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: var(--font-sans);
      background-color: var(--bg);
      color: var(--text-main);
      line-height: 1.5;
      padding: 24px;
      max-width: 1100px;
      margin: 0 auto;
    }

    /* HEADER */
    header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 24px;
      border-bottom: 1px solid var(--border);
      padding-bottom: 16px;
    }
    .header-title h1 {
      font-size: 24px;
      font-weight: 800;
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .header-title p {
      font-size: 13px;
      color: var(--text-muted);
      margin-top: 4px;
    }
    .badge {
      display: inline-block;
      font-size: 11px;
      font-weight: 700;
      padding: 4px 10px;
      border-radius: 9999px;
      background: var(--success-bg);
      color: var(--success-text);
      letter-spacing: 0.5px;
    }

    /* CARDS */
    .card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 20px;
      margin-bottom: 20px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    }
    .card-header {
      margin-bottom: 16px;
    }
    .card-header h2 {
      font-size: 16px;
      font-weight: 700;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .card-header p {
      font-size: 12px;
      color: var(--text-muted);
      margin-top: 2px;
    }

    /* STATS GRID */
    .stats-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 14px;
    }
    .stat-box {
      background: var(--surface-subtle);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 14px 16px;
    }
    .stat-val {
      font-size: 22px;
      font-weight: 800;
      color: var(--primary);
    }
    .stat-label {
      font-size: 12px;
      font-weight: 600;
      color: var(--text-main);
      margin-top: 2px;
    }
    .stat-sub {
      font-size: 11px;
      color: var(--text-muted);
    }

    /* DAEMONS */
    .daemon-row {
      background: var(--surface-subtle);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 12px 16px;
      margin-bottom: 10px;
    }
    .daemon-top {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 4px;
    }
    .daemon-title {
      font-size: 13px;
      font-weight: 700;
    }
    .daemon-id {
      font-family: var(--font-mono);
      font-size: 10px;
      color: var(--text-faint);
    }
    .daemon-desc {
      font-size: 11px;
      color: var(--text-muted);
      margin-bottom: 6px;
    }
    .daemon-status {
      font-size: 11px;
      font-weight: 600;
      color: var(--primary);
      background: #FFFFFF;
      padding: 4px 8px;
      border-radius: 4px;
      border: 1px solid var(--border);
      display: inline-block;
    }

    /* ACTIONS GRID */
    .actions-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
      gap: 12px;
    }
    .action-card {
      background: var(--surface-subtle);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 12px 14px;
      display: flex;
      align-items: center;
      gap: 14px;
      transition: border-color 0.15s, box-shadow 0.15s;
    }
    .action-card:hover {
      border-color: var(--border-strong);
      box-shadow: 0 2px 4px rgba(0,0,0,0.04);
    }
    .btn {
      appearance: none;
      border: 1px solid var(--border-strong);
      background: #FFFFFF;
      color: var(--text-main);
      font-family: var(--font-sans);
      font-size: 12px;
      font-weight: 700;
      padding: 8px 14px;
      border-radius: 6px;
      cursor: pointer;
      white-space: nowrap;
      min-width: 150px;
      text-align: center;
      transition: all 0.15s ease;
    }
    .btn:hover:not(:disabled) {
      background: var(--surface-subtle);
      border-color: var(--primary);
      color: var(--primary);
    }
    .btn:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
    .btn-primary {
      background: #1E293B;
      color: #FFFFFF;
      border-color: #0F172A;
    }
    .btn-primary:hover:not(:disabled) {
      background: var(--primary);
      border-color: var(--primary);
      color: #FFFFFF;
    }
    .action-info {
      flex: 1;
    }
    .action-info h3 {
      font-size: 12px;
      font-weight: 700;
    }
    .action-info p {
      font-size: 11px;
      color: var(--text-muted);
      margin-top: 1px;
    }

    /* TERMINAL */
    .terminal-container {
      background: var(--terminal-bg);
      border-radius: 8px;
      border: 1px solid #1E293B;
      overflow: hidden;
    }
    .terminal-header {
      background: #0F172A;
      padding: 8px 14px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid #1E293B;
    }
    .terminal-title {
      font-family: var(--font-mono);
      font-size: 11px;
      font-weight: 600;
      color: #94A3B8;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .terminal-status {
      font-size: 11px;
      font-weight: 600;
      color: #38BDF8;
    }
    .terminal-clear {
      background: transparent;
      border: 1px solid #334155;
      color: #94A3B8;
      font-size: 10px;
      padding: 2px 8px;
      border-radius: 4px;
      cursor: pointer;
    }
    .terminal-clear:hover {
      color: #FFFFFF;
      border-color: #64748B;
    }
    pre#terminal-output {
      font-family: var(--font-mono);
      font-size: 11px;
      color: var(--terminal-text);
      padding: 14px;
      height: 280px;
      overflow-y: auto;
      white-space: pre-wrap;
      word-break: break-all;
      line-height: 1.45;
    }
    .spinner {
      display: inline-block;
      width: 10px;
      height: 10px;
      border: 2px solid rgba(255,255,255,0.3);
      border-radius: 50%;
      border-top-color: #38BDF8;
      animation: spin 0.8s linear infinite;
    }
    @keyframes spin { to { transform: rotate(360deg); } }
  </style>
</head>
<body>

  <header>
    <div class="header-title">
      <h1>⚡ Groundsole Cockpit</h1>
      <p>Autonome Schaltzentrale auf deiner SSD · Plattformneutral & unabhängig von Chat-Fenstern</p>
    </div>
    <div style="text-align: right;">
      <span class="badge" id="live-badge">100% LOKAL & AKTIV</span>
      <div style="font-size: 10px; color: var(--text-faint); margin-top: 4px;" id="last-update">Aktualisiert: ...</div>
    </div>
  </header>

  <!-- 1. WISSENSFUNDAMENT -->
  <div class="card">
    <div class="card-header">
      <h2>🧠 Das Wissensfundament (SSOT auf Festplatte)</h2>
      <p>Alle Agenten (Antigravity, Hermes, OpenWebUI) greifen deterministisch auf diesen lokalen Datenbestand zu.</p>
    </div>
    <div class="stats-grid">
      <div class="stat-box">
        <div class="stat-val" id="val-transcripts">-</div>
        <div class="stat-label">Archivierte Sitzungen</div>
        <div class="stat-sub">Roh-Transkripte in 00_MEMORY/transcripts/</div>
      </div>
      <div class="stat-box">
        <div class="stat-val" id="val-langmem">-</div>
        <div class="stat-label">Persistente Fakten</div>
        <div class="stat-sub" id="sub-langmem">Gefiltert in langmem_store.db</div>
      </div>
      <div class="stat-box">
        <div class="stat-val" id="val-vectors">-</div>
        <div class="stat-label">Such-Vektoren</div>
        <div class="stat-sub">FastEmbed Chunks in Vektordatenbanken</div>
      </div>
    </div>
  </div>

  <!-- 2. HINTERGRUND-DIENSTE -->
  <div class="card">
    <div class="card-header">
      <h2>🛡️ Autonome System-Hintergrunddienste</h2>
      <p>Laufen deterministisch auf Betriebssystem-Ebene, völlig unabhängig von geöffneten Chat-Fenstern.</p>
    </div>

    <div class="daemon-row">
      <div class="daemon-top">
        <span class="daemon-title">1. Vektorpuffer-Sync (Heartbeat)</span>
        <span class="daemon-id">groundsole_memory_sync</span>
      </div>
      <div class="daemon-desc">Liest neue ungespeicherte Turns leise in memory_buffer.db für Antigravity und Hermes ein.</div>
      <div class="daemon-status" id="log-sync">Lädt...</div>
    </div>

    <div class="daemon-row">
      <div class="daemon-top">
        <span class="daemon-title">2. Automatische System-Hygiene</span>
        <span class="daemon-id">groundsole_system_hygiene</span>
      </div>
      <div class="daemon-desc">Bereinigt verwaiste Cache-Dateien, temporäre Telemetrie und prüft SSOT-Pfade im Workspace.</div>
      <div class="daemon-status" id="log-hygiene">Lädt...</div>
    </div>

    <div class="daemon-row">
      <div class="daemon-top">
        <span class="daemon-title">3. Lokales & Cloud-Sicherheits-Backup</span>
        <span class="daemon-id">workspace-backup</span>
      </div>
      <div class="daemon-desc">Automatisierte Snapshot-Sicherung nach Google Drive / externen Speicher.</div>
      <div class="daemon-status" id="log-backup">Lädt...</div>
    </div>
  </div>

  <!-- 3. SOFORT-AKTIONEN -->
  <div class="card">
    <div class="card-header">
      <h2>🚀 Sofort-Aktionen (Manuell auslösen)</h2>
      <p>Prozesse sofort gezielt starten, ohne auf die Zeitautomatik oder ein Chat-Kommando zu warten.</p>
    </div>

    <div class="actions-grid">
      <div class="action-card">
        <button class="btn btn-primary" onclick="runAction('dreaming')">🌙 Dreaming starten</button>
        <div class="action-info">
          <h3>Groundsole Dreaming</h3>
          <p>Biophysikalische Konsolidierung (Prinzip 15): Verfall, Vektor-Clusterung & Widerspruchs-Audit.</p>
        </div>
      </div>

      <div class="action-card">
        <button class="btn" onclick="runAction('sync')">⚡ Puffer syncen</button>
        <div class="action-info">
          <h3>Vektorpuffer Sync</h3>
          <p>Aktualisiert memory_buffer.db sofort mit neuen Chat-Zeilen aller aktiven Harnesses.</p>
        </div>
      </div>

      <div class="action-card">
        <button class="btn" onclick="runAction('crystallize')">💎 Kristallisieren</button>
        <div class="action-info">
          <h3>Fakten kristallisieren</h3>
          <p>Extrahiert anstehende Fakten & Relationen nach LangMem und Cognee via Gemini Flash Lite.</p>
        </div>
      </div>

      <div class="action-card">
        <button class="btn" onclick="runAction('integrity')">🔍 Integrität prüfen</button>
        <div class="action-info">
          <h3>Integritäts-Check</h3>
          <p>Scannt Pfade, SSOT-Verweise und Markdown-Links auf formale Konsistenz.</p>
        </div>
      </div>

      <div class="action-card">
        <button class="btn" onclick="runAction('hermes_export')">📥 Hermes retten</button>
        <div class="action-info">
          <h3>Letzte Hermes-Session</h3>
          <p>Notfall-Export: Rettet die letzte Sitzung verlustfrei (0 Tokens) direkt in ein Transkript.</p>
        </div>
      </div>

      <div class="action-card">
        <button class="btn" onclick="runAction('hygiene')">🧹 System-Hygiene</button>
        <div class="action-info">
          <h3>Cache & Entropie</h3>
          <p>Bereinigt alte temporäre Daten und prüft Zeiger auf Festplatte.</p>
        </div>
      </div>
    </div>
  </div>

  <!-- 4. LIVE TERMINAL -->
  <div class="card" style="padding: 0; overflow: hidden;">
    <div class="terminal-container">
      <div class="terminal-header">
        <div class="terminal-title">
          <span>🖥️ Live-Protokoll & Prozessausgabe</span>
          <span id="terminal-spinner" style="display: none;" class="spinner"></span>
        </div>
        <div style="display: flex; gap: 10px; align-items: center;">
          <span class="terminal-status" id="terminal-status">Bereit</span>
          <button class="terminal-clear" onclick="clearTerminal()">Löschen</button>
        </div>
      </div>
      <pre id="terminal-output">// Willkommen im Groundsole Cockpit. Klicke oben auf eine Aktion, um den Prozess live zu verfolgen.</pre>
    </div>
  </div>

  <script>
    async function loadStats() {
      try {
        const res = await fetch('/api/stats');
        const data = await res.json();
        document.getElementById('val-transcripts').textContent = `${data.transcripts} Sitzungen`;
        document.getElementById('val-langmem').textContent = `${data.langmem_active} Fakten`;
        document.getElementById('sub-langmem').textContent = `${data.langmem_total} gesamt (inkl. entwerteter Audit-Historie)`;
        document.getElementById('val-vectors').textContent = `${data.vectors.toLocaleString()} Chunks`;

        document.getElementById('log-sync').textContent = data.sync_log;
        document.getElementById('log-hygiene').textContent = data.hygiene_log;
        document.getElementById('log-backup').textContent = data.workspace_backup_log;
        document.getElementById('last-update').textContent = `Aktualisiert: ${data.updated_at}`;
      } catch (e) {
        console.warn('Fehler beim Laden der Statistiken:', e);
      }
    }


    function clearTerminal() {
      document.getElementById('terminal-output').textContent = '// Konsole geleert.\\n';
    }

    async function runAction(actionName) {
      const buttons = document.querySelectorAll('.btn');
      buttons.forEach(b => b.disabled = true);

      const statusEl = document.getElementById('terminal-status');
      const spinnerEl = document.getElementById('terminal-spinner');
      const outEl = document.getElementById('terminal-output');

      statusEl.textContent = `Führe aus: ${actionName}...`;
      statusEl.style.color = '#38BDF8';
      spinnerEl.style.display = 'inline-block';
      outEl.textContent = `▶ Starte Aktion: [${actionName}]\\n----------------------------------------------------\\n`;

      try {
        const response = await fetch('/api/run', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({action: actionName})
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder('utf-8');

        while (true) {
          const {value, done} = await reader.read();
          if (done) break;
          const chunk = decoder.decode(value, {stream: true});
          outEl.textContent += chunk;
          outEl.scrollTop = outEl.scrollHeight;
        }

        statusEl.textContent = 'Abgeschlossen ✅';
        statusEl.style.color = '#4ADE80';
      } catch (err) {
        outEl.textContent += `\\n❌ Verbindungsfehler: ${err.message}\\n`;
        statusEl.textContent = 'Fehler ❌';
        statusEl.style.color = '#F87171';
      } finally {
        spinnerEl.style.display = 'none';
        buttons.forEach(b => b.disabled = false);
        loadStats();
      }
    }

    // Initiales Laden und 10s Intervall
    loadStats();
    setInterval(loadStats, 10000);
  </script>
</body>
</html>
"""

class CockpitHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Ruhige Konsole im Hintergrund
        pass

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode("utf-8"))
        elif self.path == "/api/ping":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "version": "2.6.0"}).encode("utf-8"))
        elif self.path == "/api/stats":
            stats = get_stats()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(stats).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/api/run":
            content_length = int(self.headers.get("Content-Length", 0))
            raw_body = self.rfile.read(content_length)
            try:
                data = json.loads(raw_body.decode("utf-8"))
                action = data.get("action", "")
            except Exception:
                action = ""

            action_cmds = {
                "dreaming": [VENV_PYTHON, os.path.join(SCRIPTS_DIR, "dreaming.py"), "--apply"],
                "sync": [VENV_PYTHON, os.path.join(SCRIPTS_DIR, "memory_indexer.py"), "--scan-harness"],
                "crystallize": [VENV_PYTHON, os.path.join(SCRIPTS_DIR, "crystallize_memory.py"), "--flush"],
                "integrity": [VENV_PYTHON, os.path.join(SCRIPTS_DIR, "check_integrity.py")],
                "hermes_export": [VENV_PYTHON, os.path.join(SCRIPTS_DIR, "export_hermes_session.py")],
                "hygiene": [VENV_PYTHON, os.path.join(SCRIPTS_DIR, "system_hygiene.py")]
            }

            cmd = action_cmds.get(action)
            if not cmd or not os.path.exists(cmd[1]):
                self.send_response(400)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.end_headers()
                self.wfile.write(f"Unbekannte Aktion oder Skript nicht gefunden: {action}\n".encode("utf-8"))
                return

            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.end_headers()

            try:
                proc = subprocess.Popen(
                    cmd,
                    cwd=REPO_ROOT,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )
                for line in iter(proc.stdout.readline, ""):
                    self.wfile.write(line.encode("utf-8"))
                    self.wfile.flush()
                proc.stdout.close()
                proc.wait()
                self.wfile.write(f"\n[Exit-Code: {proc.returncode}]\n".encode("utf-8"))
                self.wfile.flush()
            except Exception as e:
                self.wfile.write(f"\nFehler bei der Ausführung: {str(e)}\n".encode("utf-8"))
                self.wfile.flush()
        else:
            self.send_response(404)
            self.end_headers()


def is_server_running(url: str = f"http://{HOST}:{PORT}") -> bool:
    """Prüft, ob der Server bereits auf dem Port antwortet."""
    try:
        req = urllib.request.Request(f"{url}/api/ping")
        with urllib.request.urlopen(req, timeout=0.5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("status") == "ok"
    except Exception:
        return False


def find_app_mode_browser() -> Optional[Tuple[str, List[str]]]:
    """
    Spürt dynamisch einen Chromium-basierten Browser auf, der den rahmenlosen
    App-Modus (--app=URL) nativ unterstützt (Chrome, Edge, Brave, Chromium).
    Funktioniert herstellerneutral auf macOS, Windows und Linux.
    """
    # 1. macOS
    if sys.platform == "darwin":
        candidates = [
            ("Google Chrome", "/Applications/Google Chrome.app", ["open", "-na", "Google Chrome", "--args"]),
            ("Microsoft Edge", "/Applications/Microsoft Edge.app", ["open", "-na", "Microsoft Edge", "--args"]),
            ("Brave Browser", "/Applications/Brave Browser.app", ["open", "-na", "Brave Browser", "--args"]),
            ("Chromium", "/Applications/Chromium.app", ["open", "-na", "Chromium", "--args"]),
        ]
        for name, path, cmd in candidates:
            if os.path.exists(path):
                return (name, cmd)

    # 2. Windows
    elif sys.platform == "win32":
        import shutil
        candidates = [
            ("msedge", ["cmd.exe", "/c", "start", "msedge", "--app="]),
            ("chrome", ["cmd.exe", "/c", "start", "chrome", "--app="]),
            ("brave", ["cmd.exe", "/c", "start", "brave", "--app="]),
        ]
        for name, cmd in candidates:
            if shutil.which(name):
                return (name, cmd)

    # 3. Linux
    elif sys.platform.startswith("linux"):
        import shutil
        for bin_name in ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "brave-browser", "microsoft-edge"]:
            if shutil.which(bin_name):
                return (bin_name, [bin_name])

    return None


def open_cockpit_window(url: str):
    """
    Öffnet die Cockpit-URL im rahmenlosen App-Fenster (Weg 3).
    Falls kein Chromium-Browser installiert ist, eleganter Fallback auf Standard-Browser.
    """
    browser = find_app_mode_browser()
    if browser:
        name, cmd_prefix = browser
        try:
            if sys.platform == "darwin":
                full_cmd = cmd_prefix + [f"--app={url}"]
                subprocess.Popen(full_cmd)
                return
            elif sys.platform == "win32":
                full_cmd = cmd_prefix[:-1] + [f"--app={url}"]
                subprocess.Popen(full_cmd, shell=True)
                return
            elif sys.platform.startswith("linux"):
                full_cmd = cmd_prefix + [f"--app={url}"]
                subprocess.Popen(full_cmd)
                return
        except Exception:
            pass

    # Graceful Fallback: System-Standardbrowser (Safari, Firefox, etc.)
    import webbrowser
    webbrowser.open(url)


def run_server():
    server = ThreadingHTTPServer((HOST, PORT), CockpitHandler)
    print(f"🚀 Groundsole Cockpit läuft auf http://{HOST}:{PORT}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Groundsole Cockpit beendet.")
        server.server_close()


def main():
    target_url = f"http://{HOST}:{PORT}"

    # Modus 1: Reiner Server-Start (z. B. im Hintergrund oder via Daemon)
    if "--server" in sys.argv:
        run_server()
        return

    # Modus 2: 1-Klick-Starter (Weg 1 + Weg 3)
    if not is_server_running(target_url):
        # Server lautlos im Hintergrund starten
        log_file = os.path.join(os.path.expanduser("~"), ".gemini", "cockpit_server.log")
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        with open(log_file, "a") as f_out:
            subprocess.Popen(
                [VENV_PYTHON, os.path.abspath(__file__), "--server"],
                stdout=f_out,
                stderr=f_out,
                start_new_session=True
            )


        # Warte kurz auf Server-Bereitschaft (max. 2 Sekunden)
        for _ in range(20):
            if is_server_running(target_url):
                break
            time.sleep(0.1)

    # Browser im App-Fenster öffnen
    open_cockpit_window(target_url)


if __name__ == "__main__":
    main()
