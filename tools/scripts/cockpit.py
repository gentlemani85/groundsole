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
import plistlib
import urllib.request
import urllib.error
from pathlib import Path
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

def get_inference_info() -> Dict[str, Any]:
    """
    Ermittelt die aktive Inferenzquelle für Groundsole:
    - Gemini API Key
    - OpenRouter API Key
    - OpenAI API Key
    - Lokales Ollama
    - Tier-1 In-Harness (Zero API / Abo-Modus)
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
        return {
            "provider": "gemini",
            "label": "Gemini 2.5 Flash",
            "desc": "Cloud-API über Google Key",
            "mode": "api"
        }

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
        return {
            "provider": "openrouter",
            "label": "OpenRouter",
            "desc": "Multi-Provider Router",
            "mode": "api"
        }
    if k_openai:
        return {
            "provider": "openai",
            "label": "OpenAI GPT-4o-mini",
            "desc": "Cloud-API über OpenAI Key",
            "mode": "api"
        }

    try:
        req = urllib.request.Request("http://localhost:11434/api/tags")
        with urllib.request.urlopen(req, timeout=0.2) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            models = [m.get("name") for m in data.get("models", [])]
            if models:
                return {
                    "provider": "ollama",
                    "label": f"Ollama ({models[0]})",
                    "desc": "100% lokales Modell",
                    "mode": "local"
                }
    except Exception:
        pass

    return {
        "provider": "inharness",
        "label": "In-Harness Modus (Tier 1)",
        "desc": "Zero-API · Inferenz über aktiven Chat-Agenten",
        "mode": "chat"
    }


def get_managed_daemons() -> List[Dict[str, Any]]:
    """
    Liest alle registrierten Launchd-Dienste dynamisch aus ~/Library/LaunchAgents/ aus.
    Erkennt Intervalle, Kalender-Zeiten und den aktuellen Aktivierungsstatus (launchctl).
    """
    agents_dir = os.path.expanduser("~/Library/LaunchAgents")
    if not os.path.exists(agents_dir):
        return []

    plist_files = sorted(glob.glob(os.path.join(agents_dir, "*.plist")))
    results = []

    def read_log_info(path: Optional[str]) -> str:
        if not path or not os.path.exists(path):
            return "Bereit"
        try:
            mtime = os.path.getmtime(path)
            dt = datetime.fromtimestamp(mtime).strftime("%d.%m. %H:%M")
            with open(path, "r", encoding="utf-8", errors="ignore") as fp:
                lines = [l.strip() for l in fp if l.strip()]
                last = lines[-1] if lines else "OK"
                if len(last) > 65:
                    last = last[:65] + "..."
            return f"{dt} Uhr · {last}"
        except Exception as e:
            return f"Info: {e}"

    for pfile in plist_files:
        try:
            with open(pfile, "rb") as f:
                p = plistlib.load(f)
            args = p.get("ProgramArguments", [])
            args_str = " ".join(args)

            # Nur Groundsole / Workspace bezogene Dienste
            title = None
            desc = None
            log_path = p.get("StandardOutPath")
            d_id = None

            if "memory_indexer.py" in args_str:
                d_id = "memory-buffer-sync"
                title = "⚡ Vektorpuffer-Sync (Heartbeat)"
                desc = "Liest neue ungespeicherte Turns leise in memory_buffer.db für alle Chat-Harnesses ein."
                if not log_path:
                    log_path = os.path.expanduser("~/Library/Logs/groundsole_memory_sync.log")
            elif "system_hygiene.py" in args_str:
                d_id = "system-hygiene"
                title = "🛡️ Automatische System-Hygiene"
                desc = "Bereinigt verwaiste Cache-Dateien, temporäre Telemetrie und prüft SSOT-Pfade im Workspace."
                if not log_path:
                    log_path = os.path.expanduser("~/Library/Logs/groundsole_system_hygiene.log")
            elif "backup_manager.py" in args_str:
                if "antigravity" in args_str:
                    d_id = "backup-antigravity"
                    title = "💾 Antigravity-Sicherheitsbackup"
                    desc = "Tägliche Snapshot-Sicherung der Antigravity-Konfiguration."
                else:
                    d_id = "workspace-backup"
                    title = "💾 Workspace- & Cloud-Backup"
                    desc = "Wöchentliche komprimierte Snapshot-Sicherung des Workspace."
            else:
                continue

            label = p.get("Label", os.path.basename(pfile).replace(".plist", ""))

            # launchctl Status prüfen
            is_active = False
            try:
                res = subprocess.run(["launchctl", "list", label], capture_output=True, text=True)
                is_active = (res.returncode == 0)
            except Exception:
                pass

            # Zeitplan ermitteln
            interval_sec = p.get("StartInterval")
            cal_interval = p.get("StartCalendarInterval")

            schedule_type = "interval" if interval_sec else "calendar"
            interval_min = 30
            cal_hour = 9
            cal_minute = 0
            cal_weekday = None
            schedule_display = "Nicht konfiguriert"

            if interval_sec:
                schedule_type = "interval"
                interval_min = int(interval_sec // 60)
                if interval_min >= 60 and interval_min % 60 == 0:
                    hours = interval_min // 60
                    schedule_display = f"Alle {hours} Std. ({interval_min} Min.)"
                else:
                    schedule_display = f"Alle {interval_min} Minuten"
            elif cal_interval:
                schedule_type = "calendar"
                if isinstance(cal_interval, dict):
                    cal_hour = cal_interval.get("Hour", 0)
                    cal_minute = cal_interval.get("Minute", 0)
                    cal_weekday = cal_interval.get("Weekday")
                elif isinstance(cal_interval, list) and cal_interval:
                    cal_hour = cal_interval[0].get("Hour", 0)
                    cal_minute = cal_interval[0].get("Minute", 0)
                    cal_weekday = cal_interval[0].get("Weekday")

                time_str = f"{cal_hour:02d}:{cal_minute:02d} Uhr"
                weekday_names = {1: "Montag", 2: "Dienstag", 3: "Mittwoch", 4: "Donnerstag", 5: "Freitag", 6: "Samstag", 7: "Sonntag", 0: "Sonntag"}
                if cal_weekday is not None and cal_weekday in weekday_names:
                    schedule_display = f"Jeden {weekday_names[cal_weekday]} um {time_str}"
                else:
                    schedule_display = f"Täglich um {time_str}"

            results.append({
                "id": d_id,
                "title": title,
                "desc": desc,
                "plist_path": pfile,
                "label": label,
                "is_active": is_active,
                "schedule_type": schedule_type,
                "interval_minutes": interval_min,
                "calendar_hour": cal_hour,
                "calendar_minute": cal_minute,
                "calendar_weekday": cal_weekday,
                "schedule_display": schedule_display,
                "status_text": read_log_info(log_path)
            })
        except Exception:
            continue

    return results


def get_stats() -> Dict[str, Any]:
    """Sammelt Live-Metriken über das Wissensfundament, Inferenz und Systemdienste."""
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

    daemons = get_managed_daemons()
    inference = get_inference_info()

    return {
        "transcripts": t_count,
        "langmem_active": f_active,
        "langmem_total": f_total,
        "vectors": v_count,
        "inference": inference,
        "daemons": daemons,
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
    .badges-group {
      display: flex;
      flex-direction: column;
      align-items: flex-end;
      gap: 6px;
    }
    .badge-row {
      display: flex;
      gap: 8px;
      align-items: center;
    }
    .badge {
      display: inline-block;
      font-size: 11px;
      font-weight: 700;
      padding: 4px 10px;
      border-radius: 9999px;
      background: var(--success-bg);
      color: var(--success-text);
      letter-spacing: 0.3px;
    }
    .badge-inference {
      background: #EFF6FF;
      color: #1D4ED8;
      border: 1px solid #BFDBFE;
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
      border-radius: 10px;
      padding: 14px 16px;
      margin-bottom: 12px;
    }
    .daemon-top {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 6px;
    }
    .daemon-title-area {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .daemon-title {
      font-size: 14px;
      font-weight: 700;
      color: var(--text-main);
    }
    .daemon-id {
      font-family: var(--font-mono);
      font-size: 10px;
      color: var(--text-faint);
    }
    .daemon-desc {
      font-size: 12px;
      color: var(--text-muted);
      margin-bottom: 10px;
    }
    .daemon-meta {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 10px;
    }
    .status-badge {
      font-size: 11px;
      font-weight: 700;
      padding: 3px 8px;
      border-radius: 4px;
      display: inline-flex;
      align-items: center;
      gap: 4px;
    }
    .status-active {
      background: var(--success-bg);
      color: var(--success-text);
      border: 1px solid #BBF7D0;
    }
    .status-paused {
      background: #F1F5F9;
      color: #64748B;
      border: 1px solid #CBD5E1;
    }
    .schedule-badge {
      font-size: 11px;
      font-weight: 600;
      color: #334155;
      background: #FFFFFF;
      padding: 3px 8px;
      border-radius: 4px;
      border: 1px solid var(--border);
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }
    .btn-edit-sched {
      background: transparent;
      border: none;
      color: var(--primary);
      font-size: 11px;
      font-weight: 600;
      cursor: pointer;
      text-decoration: underline;
      padding: 0 4px;
    }
    .daemon-log {
      font-size: 11px;
      color: var(--text-muted);
      margin-left: auto;
    }

    /* SWITCH TOGGLE */
    .switch-container {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .switch-label {
      font-size: 11px;
      font-weight: 700;
      color: var(--text-muted);
    }
    .switch {
      position: relative;
      display: inline-block;
      width: 44px;
      height: 24px;
    }
    .switch input { 
      opacity: 0;
      width: 0;
      height: 0;
    }
    .slider {
      position: absolute;
      cursor: pointer;
      top: 0; left: 0; right: 0; bottom: 0;
      background-color: #CBD5E1;
      transition: .2s;
      border-radius: 24px;
    }
    .slider:before {
      position: absolute;
      content: "";
      height: 18px;
      width: 18px;
      left: 3px;
      bottom: 3px;
      background-color: white;
      transition: .2s;
      border-radius: 50%;
      box-shadow: 0 1px 3px rgba(0,0,0,0.15);
    }
    input:checked + .slider {
      background-color: #10B981;
    }
    input:checked + .slider:before {
      transform: translateX(20px);
    }

    /* INLINE SCHEDULER DRAWER */
    .schedule-editor {
      margin-top: 10px;
      padding: 10px 14px;
      background: #FFFFFF;
      border: 1px solid var(--border);
      border-radius: 6px;
      display: none;
      align-items: center;
      gap: 10px;
      font-size: 12px;
    }
    .schedule-editor select, .schedule-editor input {
      padding: 4px 8px;
      border: 1px solid var(--border-strong);
      border-radius: 4px;
      font-size: 12px;
      font-family: inherit;
    }
    .btn-sm {
      padding: 4px 10px;
      font-size: 11px;
      font-weight: 700;
      border-radius: 4px;
      cursor: pointer;
      border: 1px solid var(--border-strong);
      background: #FFFFFF;
    }
    .btn-sm-primary {
      background: #1E293B;
      color: #FFFFFF;
      border-color: #0F172A;
    }

    /* ACTIONS GRID */
    .actions-grid {
      display: grid;
      grid-template-columns: 1fr;
      gap: 14px;
    }
    .action-card {
      background: var(--surface-subtle);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 10px;
      transition: border-color 0.15s, box-shadow 0.15s;
    }
    .action-card:hover {
      border-color: var(--border-strong);
      box-shadow: 0 2px 4px rgba(0,0,0,0.04);
    }
    .action-top {
      display: flex;
      align-items: center;
      gap: 16px;
    }
    .btn {
      appearance: none;
      border: 1px solid var(--border-strong);
      background: #FFFFFF;
      color: var(--text-main);
      font-family: var(--font-sans);
      font-size: 12px;
      font-weight: 700;
      padding: 10px 16px;
      border-radius: 6px;
      cursor: pointer;
      white-space: nowrap;
      min-width: 170px;
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
      font-size: 13px;
      font-weight: 700;
    }
    .action-info p {
      font-size: 12px;
      color: var(--text-muted);
      margin-top: 1px;
    }
    .auto-note {
      font-size: 11px;
      color: var(--text-muted);
      background: #FFFFFF;
      border: 1px solid var(--border);
      border-left: 3px solid var(--primary);
      padding: 6px 12px;
      border-radius: 4px;
      line-height: 1.45;
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
      height: 260px;
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
      <p>Autonome Schaltzentrale auf deiner SSD · Plattformneutral für alle Agenten & Chat-Harnesses</p>
    </div>
    <div class="badges-group">
      <div class="badge-row">
        <span class="badge badge-inference" id="inference-badge">🤖 Inferenz: Wird ermittelt...</span>
        <span class="badge" id="live-badge">100% LOKAL & AKTIV</span>
      </div>
      <div style="font-size: 10px; color: var(--text-faint);" id="last-update">Aktualisiert: ...</div>
    </div>
  </header>

  <!-- 1. WISSENSFUNDAMENT -->
  <div class="card">
    <div class="card-header">
      <h2>🧠 Das Wissensfundament (SSOT auf Festplatte)</h2>
      <p>Alle Agenten (Claude Code, Antigravity, Hermes, Cursor, OpenWebUI) greifen deterministisch auf diesen lokalen Datenbestand zu.</p>
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
      <p>Laufen deterministisch auf Betriebssystem-Ebene im Hintergrund. Zeitpläne und Schalter können hier direkt angepasst werden.</p>
    </div>

    <div id="daemons-container">
      <div style="font-size: 12px; color: var(--text-muted); padding: 8px;">Dienste werden geladen...</div>
    </div>
  </div>

  <!-- 3. SOFORT-AKTIONEN -->
  <div class="card">
    <div class="card-header">
      <h2>🚀 Sofort-Aktionen (Manuell auslösen)</h2>
      <p>Prozesse sofort gezielt starten, ohne auf die Zeitautomatik oder ein Chat-Kommando zu warten.</p>
    </div>

    <div class="actions-grid">
      <!-- 1. DREAMING -->
      <div class="action-card">
        <div class="action-top">
          <button class="btn btn-primary" onclick="runAction('dreaming')">🌙 Dreaming starten</button>
          <div class="action-info">
            <h3>Groundsole Dreaming</h3>
            <p>Biophysikalische Konsolidierung (Prinzip 15): Verfall, Vektor-Clusterung & Widerspruchs-Audit.</p>
          </div>
        </div>
        <div class="auto-note">
          ℹ️ <strong>Läuft vollautomatisch:</strong> Wird im Hintergrund nachts oder nach Session-Archivierung ausgeführt. Manueller Klick nur für sofortigen Vorab-Durchlauf nötig.
        </div>
      </div>

      <!-- 2. PUFFER SYNC -->
      <div class="action-card">
        <div class="action-top">
          <button class="btn" onclick="runAction('sync')">⚡ Puffer syncen</button>
          <div class="action-info">
            <h3>Vektorpuffer Sync</h3>
            <p>Scannt ungespeicherte Turns aller aktiven Harnesses sofort in die Such-Vektoren ein.</p>
          </div>
        </div>
        <div class="auto-note">
          ℹ️ <strong>Läuft vollautomatisch:</strong> Heartbeat-Hintergrunddienst liest alle 30 Min. ungespeicherte Zeilen ein. Manueller Klick nur für sofortigen Zwischenstand nötig.
        </div>
      </div>

      <!-- 3. HEALTH CHECK & HYGIENE -->
      <div class="action-card">
        <div class="action-top">
          <button class="btn" onclick="runAction('health')">🛡️ Check starten</button>
          <div class="action-info">
            <h3>System-Gesundheitscheck & Hygiene</h3>
            <p>Prüft Pfade, SSOT-Verweise, Markdown-Links und bereinigt temporäre Caches.</p>
          </div>
        </div>
        <div class="auto-note">
          ℹ️ <strong>Läuft vollautomatisch:</strong> Tägliche System-Hygiene scannt den Workspace morgens. Manueller Klick nur nach großen Refactorings nötig.
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
    let currentDaemons = [];

    async function loadStats() {
      try {
        const res = await fetch('/api/stats');
        const data = await res.json();
        document.getElementById('val-transcripts').textContent = `${data.transcripts} Sitzungen`;
        document.getElementById('val-langmem').textContent = `${data.langmem_active} Fakten`;
        document.getElementById('sub-langmem').textContent = `${data.langmem_total} gesamt (inkl. entwerteter Audit-Historie)`;
        document.getElementById('val-vectors').textContent = `${data.vectors.toLocaleString()} Chunks`;

        if (data.inference) {
          const infBadge = document.getElementById('inference-badge');
          infBadge.textContent = `🤖 Inferenz: ${data.inference.label}`;
          infBadge.title = `${data.inference.desc} (${data.inference.mode})`;
        }

        currentDaemons = data.daemons || [];
        renderDaemons();
        document.getElementById('last-update').textContent = `Aktualisiert: ${data.updated_at}`;
      } catch (e) {
        console.warn('Fehler beim Laden der Statistiken:', e);
      }
    }

    function renderDaemons() {
      const container = document.getElementById('daemons-container');
      if (!currentDaemons || currentDaemons.length === 0) {
        container.innerHTML = `
          <div style="font-size: 12px; color: var(--text-muted); padding: 8px;">
            Aktuell sind keine Hintergrunddienste eingerichtet. Alle Aktionen können manuell ausgeführt werden.
          </div>`;
        return;
      }

      container.innerHTML = currentDaemons.map((d, idx) => `
        <div class="daemon-row" id="daemon-row-${d.id}">
          <div class="daemon-top">
            <div class="daemon-title-area">
              <span class="daemon-title">${d.title}</span>
              <span class="daemon-id">${d.label}</span>
            </div>
            <div class="switch-container">
              <span class="switch-label">${d.is_active ? 'EIN' : 'AUS'}</span>
              <label class="switch">
                <input type="checkbox" ${d.is_active ? 'checked' : ''} onchange="toggleDaemon('${d.id}', this.checked)">
                <span class="slider"></span>
              </label>
            </div>
          </div>
          <div class="daemon-desc">${d.desc}</div>
          <div class="daemon-meta">
            <span class="status-badge ${d.is_active ? 'status-active' : 'status-paused'}">
              ${d.is_active ? '● AKTIV' : '○ PAUSIERT'}
            </span>
            <span class="schedule-badge">
              <span>${d.schedule_type === 'interval' ? '⏱️' : '⏰'} ${d.schedule_display}</span>
              <button class="btn-edit-sched" onclick="toggleEditSched('${d.id}')">Ändern</button>
            </span>
            <span class="daemon-log">${d.status_text}</span>
          </div>

          <!-- Inline Schedule Editor -->
          <div class="schedule-editor" id="sched-editor-${d.id}">
            ${d.schedule_type === 'interval' ? `
              <span>Intervall:</span>
              <select id="sel-min-${d.id}">
                <option value="15" ${d.interval_minutes == 15 ? 'selected' : ''}>Alle 15 Minuten</option>
                <option value="30" ${d.interval_minutes == 30 ? 'selected' : ''}>Alle 30 Minuten (Standard)</option>
                <option value="60" ${d.interval_minutes == 60 ? 'selected' : ''}>Alle 60 Minuten (1 Std.)</option>
                <option value="120" ${d.interval_minutes == 120 ? 'selected' : ''}>Alle 120 Minuten (2 Std.)</option>
              </select>
              <button class="btn-sm btn-sm-primary" onclick="saveIntervalSched('${d.id}')">Speichern</button>
              <button class="btn-sm" onclick="toggleEditSched('${d.id}')">Abbrechen</button>
            ` : `
              <span>Uhrzeit:</span>
              <input type="time" id="inp-time-${d.id}" value="${String(d.calendar_hour).padStart(2,'0')}:${String(d.calendar_minute).padStart(2,'0')}">
              <span>Wochentag:</span>
              <select id="sel-day-${d.id}">
                <option value="daily" ${d.calendar_weekday === null ? 'selected' : ''}>Täglich</option>
                <option value="1" ${d.calendar_weekday == 1 ? 'selected' : ''}>Montags</option>
                <option value="2" ${d.calendar_weekday == 2 ? 'selected' : ''}>Dienstags</option>
                <option value="3" ${d.calendar_weekday == 3 ? 'selected' : ''}>Mittwochs</option>
                <option value="4" ${d.calendar_weekday == 4 ? 'selected' : ''}>Donnerstags</option>
                <option value="5" ${d.calendar_weekday == 5 ? 'selected' : ''}>Freitags</option>
                <option value="6" ${d.calendar_weekday == 6 ? 'selected' : ''}>Samstags</option>
                <option value="7" ${d.calendar_weekday == 7 ? 'selected' : ''}>Sonntags</option>
              </select>
              <button class="btn-sm btn-sm-primary" onclick="saveCalendarSched('${d.id}')">Speichern</button>
              <button class="btn-sm" onclick="toggleEditSched('${d.id}')">Abbrechen</button>
            `}
          </div>
        </div>
      `).join('');
    }

    function toggleEditSched(daemonId) {
      const el = document.getElementById(`sched-editor-${daemonId}`);
      if (el) {
        el.style.display = (el.style.display === 'flex' ? 'none' : 'flex');
      }
    }

    async function toggleDaemon(daemonId, enable) {
      try {
        const res = await fetch('/api/daemons/toggle', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({id: daemonId, enable: enable})
        });
        const data = await res.json();
        if (data.status === 'ok') {
          loadStats();
        } else {
          alert('Fehler beim Ändern des Dienstes: ' + (data.error || 'Unbekannt'));
        }
      } catch (err) {
        alert('Netzwerkfehler: ' + err.message);
      }
    }

    async function saveIntervalSched(daemonId) {
      const sel = document.getElementById(`sel-min-${daemonId}`);
      const minutes = parseInt(sel.value, 10);
      try {
        const res = await fetch('/api/daemons/schedule', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({id: daemonId, type: 'interval', minutes: minutes})
        });
        const data = await res.json();
        if (data.status === 'ok') {
          toggleEditSched(daemonId);
          loadStats();
        } else {
          alert('Fehler beim Speichern: ' + (data.error || 'Unbekannt'));
        }
      } catch (err) {
        alert('Netzwerkfehler: ' + err.message);
      }
    }

    async function saveCalendarSched(daemonId) {
      const timeVal = document.getElementById(`inp-time-${daemonId}`).value || '09:00';
      const [h, m] = timeVal.split(':').map(v => parseInt(v, 10));
      const dayVal = document.getElementById(`sel-day-${daemonId}`).value;
      const weekday = (dayVal === 'daily' ? null : parseInt(dayVal, 10));

      try {
        const res = await fetch('/api/daemons/schedule', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({id: daemonId, type: 'calendar', hour: h, minute: m, weekday: weekday})
        });
        const data = await res.json();
        if (data.status === 'ok') {
          toggleEditSched(daemonId);
          loadStats();
        } else {
          alert('Fehler beim Speichern: ' + (data.error || 'Unbekannt'));
        }
      } catch (err) {
        alert('Netzwerkfehler: ' + err.message);
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
        if self.path == "/api/daemons/toggle":
            content_length = int(self.headers.get("Content-Length", 0))
            raw_body = self.rfile.read(content_length)
            try:
                data = json.loads(raw_body.decode("utf-8"))
                d_id = data.get("id")
                enable = bool(data.get("enable"))
            except Exception:
                d_id, enable = None, False

            daemons = get_managed_daemons()
            target = next((d for d in daemons if d["id"] == d_id), None)
            if not target:
                self.send_response(404)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Daemon nicht gefunden"}).encode("utf-8"))
                return

            plist_path = target["plist_path"]
            if enable:
                res = subprocess.run(["launchctl", "load", plist_path], capture_output=True, text=True)
            else:
                res = subprocess.run(["launchctl", "unload", plist_path], capture_output=True, text=True)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "is_active": enable, "out": res.stdout, "err": res.stderr}).encode("utf-8"))
            return

        elif self.path == "/api/daemons/schedule":
            content_length = int(self.headers.get("Content-Length", 0))
            raw_body = self.rfile.read(content_length)
            try:
                data = json.loads(raw_body.decode("utf-8"))
                d_id = data.get("id")
                sched_type = data.get("type", "interval")
            except Exception:
                d_id, sched_type = None, "interval"

            daemons = get_managed_daemons()
            target = next((d for d in daemons if d["id"] == d_id), None)
            if not target:
                self.send_response(404)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Daemon nicht gefunden"}).encode("utf-8"))
                return

            plist_path = target["plist_path"]
            try:
                with open(plist_path, "rb") as f:
                    p = plistlib.load(f)

                schedule_display = ""
                if sched_type == "interval":
                    minutes = int(data.get("minutes", 30))
                    if minutes < 1:
                        minutes = 1
                    p["StartInterval"] = minutes * 60
                    p.pop("StartCalendarInterval", None)
                    schedule_display = f"Alle {minutes} Minuten"
                elif sched_type == "calendar":
                    hour = int(data.get("hour", 9))
                    minute = int(data.get("minute", 0))
                    weekday = data.get("weekday")
                    cal_dict = {"Hour": hour, "Minute": minute}
                    if weekday is not None and str(weekday).isdigit():
                        cal_dict["Weekday"] = int(weekday)
                    p["StartCalendarInterval"] = cal_dict
                    p.pop("StartInterval", None)
                    time_str = f"{hour:02d}:{minute:02d} Uhr"
                    weekday_names = {1: "Montag", 2: "Dienstag", 3: "Mittwoch", 4: "Donnerstag", 5: "Freitag", 6: "Samstag", 7: "Sonntag", 0: "Sonntag"}
                    if "Weekday" in cal_dict and cal_dict["Weekday"] in weekday_names:
                        schedule_display = f"Jeden {weekday_names[cal_dict['Weekday']]} um {time_str}"
                    else:
                        schedule_display = f"Täglich um {time_str}"

                with open(plist_path, "wb") as f:
                    plistlib.dump(p, f)

                # Bei aktiven Diensten sofort reloaden
                if target["is_active"]:
                    subprocess.run(["launchctl", "unload", plist_path], capture_output=True)
                    subprocess.run(["launchctl", "load", plist_path], capture_output=True)

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "ok", "schedule_display": schedule_display}).encode("utf-8"))
                return
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
                return

        elif self.path == "/api/run":
            content_length = int(self.headers.get("Content-Length", 0))
            raw_body = self.rfile.read(content_length)
            try:
                data = json.loads(raw_body.decode("utf-8"))
                action = data.get("action", "")
            except Exception:
                action = ""

            cmds = []
            if action == "dreaming":
                cmds = [([VENV_PYTHON, os.path.join(SCRIPTS_DIR, "dreaming.py"), "--apply"], "🌙 Starte Groundsole Dreaming...")]
            elif action == "sync":
                cmds = [([VENV_PYTHON, os.path.join(SCRIPTS_DIR, "memory_indexer.py"), "--scan-harness"], "⚡ Starte Vektorpuffer-Sync...")]
            elif action == "health":
                cmds = [
                    ([VENV_PYTHON, os.path.join(SCRIPTS_DIR, "check_integrity.py")], "🔍 Prüfe Workspace- & Markdown-Integrität..."),
                    ([VENV_PYTHON, os.path.join(SCRIPTS_DIR, "system_hygiene.py")], "\n🧹 Starte System-Hygiene & Cache-Bereinigung...")
                ]
            else:
                self.send_response(400)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.end_headers()
                self.wfile.write(f"Unbekannte Aktion: {action}\n".encode("utf-8"))
                return

            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.end_headers()

            try:
                for cmd, banner in cmds:
                    self.wfile.write(f"{banner}\n".encode("utf-8"))
                    self.wfile.flush()
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
