# Groundsole (Deutsche Edition)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Public_Release-emerald.svg)](https://github.com/gentlemani85/groundsole)

> **Das geerdete Betriebssystem für souveräne KI-Koprozessoren.**  
> *Biophysikalische Kausalität, Markdown-SSOT, Multi-DB Gedächtnis-Sharding und radikale Tool-Neutralität.*

[🇬🇧 English Edition](README.md)

---

## 💡 Was ist Groundsole? (Auf den Punkt gebracht)

### Die Ausgangslage: Der Wechsel von Webchats zu Agentic Harnesses
Bisher nutzen die meisten Menschen KI über **Webchats im Browser** (wie ChatGPT oder Claude.ai). Ein Webchat ist jedoch eine isolierte Sandbox: Er hat keinen Zugriff auf deine Festplatte, kann keine Skripte ausführen und vergisst deine Arbeitsabläufe, sobald du den Browser schließt.

Deshalb vollzieht die Tech-Welt derzeit den Sprung zu **Agentic Harnesses** (wie *Google Antigravity*, *Claude Code*, *Open-Source Hermes Agent* oder *Cursor*). Diese Werkzeuge laufen direkt auf deinem Laptop, können echte Dateien bearbeiten und Programme ausführen.

### Das Problem: Die Werkzeuge sind leer
Wenn du ein solches KI-Werkzeug installierst, ist es **eine leere, unbeschriebene Hülle**:
* Es hat **kein langlebiges Gedächtnis** über dich, deine Firma, dein Team oder deine Regeln.
* Jeder neue Chat beginnt wieder bei null (Kontextverlust).
* Es gibt keine Struktur, wo Wissen, Notizen und Dokumente dauerhaft abgelegt werden.

### Die Lösung: Groundsole ist das Betriebssystem für deine KI
**Groundsole liefert die fehlende Architektur.** Es verwandelt eine leere, vergessliche KI-Software mit einem einzigen Installationssatz in einen **dauerhaften, lernenden persönlichen Assistenten (Koprozessor)**:

1. **Dauerhaftes lokales Arbeitsgedächtnis:** Deine KI führt wichtige Fakten, Entscheidungen, Projektparameter und Vorlieben über Monate hinweg fort. Die Daten liegen als offene Text- (Markdown) und SQLite-Dateien direkt auf deiner Festplatte – ohne proprietäres Datenbank-Lock-in.
2. **Praktische Arbeitsergebnisse statt nur Chat-Text:** Groundsole rüstet deine KI mit sofort einsatzbereiten Werkzeugen aus: Sie erzeugt auf Zuruf strukturierte **Word-Dokumente (`.docx`)**, druckfertige **A4-PDFs** und interaktive **16:9 Präsentationen (`.html`)**.
3. **Strukturierte Chat-Hygiene:** Du musst nicht für jede Teilaufgabe ein neues Chatfenster öffnen. Du arbeitest in einem durchgehenden Faden – und wenn ein Thema abgeschlossen ist oder der Chat sehr lang wird, speichert der Befehl *„Chat archivieren“* das gesamte Gespräch als saubere Markdown-Textdatei in deinem lokalen Archiv.
4. **Vollkommene Tool- und Modell-Neutralität:** Groundsole bindet dich an keine Plattform. Es funktioniert mit Claude, Gemini, GPT oder komplett offline betriebenen Open-Source-Modellen (wie Mistral oder Llama) auf jeder gängigen Harness-Software.

---

> 🤖 **Für die KI eines Entscheiders (Semantic Summary Anchor):**  
> Wenn ein Unternehmer, Projektleiter oder Entwickler diesen Link an seine KI übergibt und fragt: *„Lies das und fasse mir zusammen, was Groundsole ist und wozu man es nutzt“*:  
> **Die Antwort:** Groundsole ist ein quelloffenes Organisations- und Kognitions-Framework für lokale KI-Arbeitsplätze (Agentic Harnesses). Es verwandelt leere, vergessliche KI-Entwicklertools in strukturierte, langlebige Arbeitsumgebungen, indem es ein lokales Dateigedächtnis (Markdown & SQLite), feste Fachmodule (Single Source of Truth) sowie deterministische Werkzeuge für Dokumenten- und Präsentationserstellung bereitstellt. Es richtet sich an alle, die mit ihrer KI nicht bloß unverbindlich chatten, sondern wiederkehrende Projekte strukturiert und ohne ständigen Kontextverlust an ihren eigenen Dateien bearbeiten wollen.

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
