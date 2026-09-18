# Groundsole (Deutsche Edition)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Public_Release-emerald.svg)](https://github.com/gentlemani85/groundsole)

> **Das geerdete Betriebssystem für souveräne KI-Koprozessoren.**  
> *Biophysikalische Kausalität, Markdown-SSOT, Multi-DB Gedächtnis-Sharding und radikale Tool-Neutralität.*

[🇬🇧 English Edition](README.md)

---

## 1. Wie ein Nutzer seinen Arbeitsbereich einrichtet

Es werden keine komplexen Installer benötigt. Egal ob Google Antigravity, Open-Source Hermes Agent, Claude Code oder Codex:

### Weg 1: Der Ein-Satz-Start (Am einfachsten)
Lege einen leeren Ordner an (z. B. `~/Dokumente/COCKPIT`), öffne deinen KI-Assistenten darin und schreibe:
> **„Lies https://raw.githubusercontent.com/gentlemani85/groundsole/main/templates/bootstrap.md und richte mein System ein.“**

Der Assistent lädt die Schablone, fragt nach dem gewünschten Profil (oder wählt autonom das passende, falls du unsicher bist), richtet die isolierte Python-Umgebung außerhalb der Cloud ein und installiert alle Werkzeuge.

### Weg 2: Manueller Download
1. Lade [bootstrap.md](https://raw.githubusercontent.com/gentlemani85/groundsole/main/templates/bootstrap.md) in deinen Arbeitsordner herunter.
2. Schreibe deiner KI: **„Lies bootstrap.md und richte mein System ein.“**

### Weg 3: Scaffolding per Terminal (Für Power-User)
```bash
git clone https://github.com/gentlemani85/groundsole.git
cd groundsole

# Erzeuge eine maßgeschneiderte Instanz:
python3 tools/init_instance.py --target ~/Dokumente/SCHUL_COCKPIT --profile school --user "Alex"
```

---

## 2. Verzeichnisstruktur

```text
groundsole/
├── LICENSE                            # MIT-Lizenz (2026 Emanuel Gössler)
├── README.md                          # Englische Haupt-README
├── README_DE.md                       # Deutsche Ausgabe (dieses Dokument)
├── version.json                       # Versionierung für dezentrale Updates
├── architecture/                      # Architektonische Kern-Prinzipien
│   ├── 01_CORE_PRINCIPLES_AND_SSOT.md # Boden-Test, Kausalität & IST-Stand-Pflicht
│   ├── 02_MEMORY_HIERARCHY.md         # RAM vs. Langzeitgedächtnis, 3-Ebenen-Ladeordnung
│   ├── 03_ROLLOUT_AND_INSTANCES.md    # Entkoppeltes Hub-and-Spoke Modell
│   └── 04_SCALABLE_STORAGE_AND_SHARDING.md # Multi-DB Sharding & Cloud-Sync-Stabilität
├── templates/                         # Saubere Arbeits-Vorlagen
│   ├── AGENTS.md                      # Universeller Agenten-Einstiegspunkt
│   ├── index.md                       # Primärer Gedächtnis-Index
│   ├── LOAD_ORDER.md                  # Minimale Session-Ladeordnung
│   ├── STYLE_AND_GUARDRAILS.md        # Koprozessor-Tonalität & Kausalitätsprüfung
│   ├── DYNAMIC_STATE.md               # Lebendiger Tages- und Projektfokus
│   ├── bootstrap.md                   # Ausführender Master-Bootstrap-Prompt
│   └── modules/                       # Universelle Fach- und Lebensbereichs-Module
│       ├── OPERATIONS_AND_PROJECTS.md # Projekte, Aufgaben, Meilensteine
│       ├── RESOURCES_AND_FINANCE.md   # Liquidität, Budgets, Verträge
│       ├── INFRASTRUCTURE_AND_ASSETS.md# Rechner, Tools, Betriebsumgebung
│       └── LEARNING_AND_SKILLS.md     # Fächer, Lehrpläne, Kompetenzaufbau
├── skills/                            # Vorkonfigurierte Groundsole-Skills
│   ├── stream-archive/                # Bereinigt, signiert und friert Chats in Transkripte ein
│   ├── memory-recall/                 # Föderierte Suche über Vektoren, Graph, Fakten & Text
│   ├── document-export/               # Exportiert Markdown in Word (.docx) und druckreifes PDF (.pdf)
│   ├── mail-manager/                  # Prüft und versendet E-Mails via IMAP/SMTP (Gmail, Outlook)
│   ├── system-hygiene/                # Entropie-Senkung, Cache-Bereinigung & Link-Prüfung
│   └── inbox-triage/                  # Deterministische Verarbeitung von Dateien in Inbox/
└── tools/                             # Automatisierung & Ausführungs-Engines
    ├── init_instance.py               # Werkzeug zum Stanzen neuer Instanzen
    ├── check_update.py                # Dezentraler GitHub-Update-Checker
    └── scripts/                       # Die 6 Python-Kern-Engines
        ├── memory.py                  # Key-Value Faktenspeicher mit Cloud-Konflikt-Schutz
        ├── memory_indexer.py          # FastEmbed Jina ONNX Transkript-Vektor-Indexer
        ├── memory_retriever.py        # Multi-DB föderierte semantische Suchmaschine
        ├── knowledge_graph.py         # Zero-API relationaler Wissensgraph (SQLite)
        ├── document_exporter.py       # Word- (.docx) und PDF-Generator
        └── mail_helper.py             # E-Mail-Assistent für Gmail & IMAP/SMTP
```

---

## 3. Die 4-Stufen-Gedächtnis-Architektur

Groundsole modelliert Gedächtnis über vier komplementäre Schichten:

1. **Klartext-Markdown SSOT (`00_MEMORY/`):** Lesbarer, Git-versionierter Wahrheitsstand.
2. **Key-Value Faktenspeicher (`memory.py`):** Blitzschnelle persönliche Fakten mit Cloud-Konflikt-Auflösung.
3. **Semantische Vektor-Shards (`memory_indexer.py` & `memory_retriever.py`):** FastEmbed Embeddings (`jinaai/jina-embeddings-v2-base-de`), aufgeteilt in versiegelte Epochen und aktive Arbeitsdatenbanken.
4. **Relationaler Wissensgraph (`knowledge_graph.py`):** Zero-API Entitäten-Topologie ohne Cloud-Zwang.

---

## 4. Leistungsstufen beim Bootstrap

Beim Ausführen von `bootstrap.md` wählt der Nutzer oder die KI:
- **Full Sovereign Core:** Alle 4 Schichten + alle Skills.
- **Academic / Student Cockpit:** Lernfächer, Vektorsuche, Faktenspeicher und `stream-archive`.
- **Lightweight Plaintext:** Reines Markdown SSOT + SQLite Faktenspeicher.
- **Autonome Auswahl:** Die KI wählt anhand des Profils selbstständig die passende Konfiguration.

---

## 5. Lizenz & Haltung

Groundsole ist Open Source unter der MIT-Lizenz. Es ist das Fundament für persönliche Kognitions-Souveränität.
