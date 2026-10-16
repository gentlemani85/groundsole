---
name: youtube-transcript
description: "Deterministischer Abruf und Volltext-Analyse von YouTube-Videos via Wortlaut-Transkription (yt-dlp / youtube-transcript-api). Garantiert 100% Faktenabdeckung und verhindert oberflächliche Halluzinationen aus Web-Snippets."
version: 1.0.0
author: Emanuel Gössler
tags: [groundsole, youtube, transcript, audio, video, research]
---

# YouTube Transcript Skill

Dieser Skill ermöglicht dem AI-Koprozessor den deterministischen, vollständigen Abruf des gesprochenen Wortlauts aus YouTube-Videos. Er stellt sicher, dass Analysen, Zusammenfassungen und technische Prüfungen niemals auf oberflächlichen Suchmaschinen-Snippets oder Video-Metadaten beruhen, sondern auf 100 % des tatsächlich gesprochenen Textes.

---

## 🎯 Trigger Conditions

Aktiviere diesen Skill automatisch, sobald:
- Der Benutzer eine YouTube-URL (`youtube.com/watch?v=...`, `youtu.be/...`) oder eine 11-stellige Video-ID im Chat übergibt.
- Der Benutzer auffordert: *"Prüf den Inhalt des Videos"*, *"Fass das Video zusammen"*, *"Was sagt der Sprecher zu X?"*, *"Analysiere das Video"*.

---

## 🛠️ Ausführung & Workflow

### 1. Transkript deterministisch abrufen
Vor jeder inhaltlichen Antwort oder Zusammenfassung führt der Agent das zentrale Skript aus:

```bash
/Users/emanuel/.local/venv/bin/python3 scripts/youtube_transcript.py "<YOUTUBE_URL_ODER_ID>"
```

*Das Skript prüft automatisch Untertitel und automatische Transkripte in Deutsch und Englisch via `yt-dlp` und gibt den bereinigten Volltext samt Metadaten (Titel, Kanal, Dauer) aus.*

### 2. Inferenz & Analyse auf Primärquelle stützen
- **Wortlaut als SSOT:** Alle Behauptungen, Zitate, Benchmarks und Zeitstempel müssen direkt aus dem abgerufenen Transkripttext belegt werden.
- **Verbot von Suchschnipsel-Raten:** Wenn Untertitel deaktiviert sind oder kein Transkript existiert, meldet der Agent dies wahrheitsgemäß, anstatt den Inhalt anhand von Websuchen oder Videotiteln zu erraten.
- **Wichtige Kernaussagen strukturieren:** Technische Daten (Modelle, RAM, Latenzen, Kosten) präzise herausarbeiten und direkt mit dem Projektkontext verknüpfen.
