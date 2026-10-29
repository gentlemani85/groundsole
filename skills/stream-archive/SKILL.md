---
name: stream-archive
description: "Automated session transcript archiving, telemetry sanitization, and long-term memory crystallization."
version: 1.0.0
author: Emanuel Gössler
tags: [groundsole, archive, indexing, memory, automation]
---

# Stream Archive Skill

This skill governs the foundational transition of cognitive data in Groundsole: **moving from volatile conversation memory into immutable, indexed long-term storage.**

---

## 🧠 Fundamental Principle: RAM vs. Long-Term Storage

> [!IMPORTANT]
> **To the User and Agent:**  
> An active chat session is ephemeral cognitive working RAM. **The AI does NOT possess durable, cross-session recall of ongoing thoughts until the session is explicitly archived.**
> 
> Archiving is the crystallization event that:
> 1. Freezes the raw dialogue as an immutable primary source in `00_MEMORY/transcripts/`.
> 2. Filters out raw telemetry, system tokens, and noise.
> 3. Triggers incremental ingestion into the active semantic vector database shard.
> 4. Crystallizes permanent facts into LangMem and Cognee.

---

## Trigger Conditions

Activate this skill when:
- The user requests: *"Archive this session"*, *"Export and archive chat"*, *"Sync transcripts"*, or *"Process new chats"*.
- A conversation reaches major milestone breakthroughs or nears the context token ceiling.

---

## 📝 Formatting & Sanitization Standards

Every session transcript saved to `00_MEMORY/transcripts/` must strictly adhere to these formatting rules:

1. **Heading Hierarchy (H1 vs H2 vs H3) & Sprecher-Identität:**
   - **H1 (`#`)**: Solely the main title at the very top (e.g., `# 2026-09-18 - Groundsole Core Architecture`).
   - **H2 (`##`)**: Solely the speaker headings with timestamps:
     - `## <User_Name> (YYYY-MM-DDTHH:MM:SS+02:00)`. **Das generische Label „User“ ist strengstens verboten! Verwende immer den konkreten Benutzernamen.**
     - `## Antigravity (YYYY-MM-DDTHH:MM:SS+02:00)` (or Claude / Hermes / etc.)
   - **H3 (`###`) and below**: All section headings *within* responses.

2. **Telemetry Sanitization & Anti-Noise:**
   - **System XML Tags:** Completely strip all system wrapper tags: `<ADDITIONAL_METADATA>`, `<CONTEXT_SUMMARY>`, `<USER_REQUEST>`, `<SYSTEM_MESSAGE>`, `<USER_SETTINGS_CHANGE>`.
   - **Client Telemetry & Tool-Dumps:** Strip tool JSON schemas, voluminous compiler dumps, raw terminal outputs, unformatted stack traces, and base64 strings.
   - **Universal Zero-Leak Secret-Sanitizer:** Alle API-Keys (auch Fragmente wie `AQ.`, `sk-`), Tokens, Passwörter, Router-Keys und Secrets ausnahmslos durch `[IN_PASSWORT_MANAGER_GESICHERT]` ersetzen.
   - **Rationale:** Only genuine reasoning, decisions, and factual dialogue belong in the transcript. Telemetry noise degrades semantic vector embeddings.

3. **Direct H1-to-H2 Transition (No Metadata Header):**
   - Directly after H1, the first speaker H2 **must follow immediately** (`# Title \n\n ## <User_Name> (...)`).
   - Do **not** inject metadata lines (`Date:`, `Participants:`, `Status:`) into the transcript.


4. **Archivierungs-Triage & Zero-Leak-Sanitizing:**
   - **Standard-Pfad (Persönlich & Philosophie):**
     - Transkript: `00_MEMORY/transcripts/YYYY-MM-DD - [Titel].md`
     - Vektordatenbank: `00_MEMORY/vectors/active.db`
   - **Isolierter Mandanten-/Team-Pfad (Optionale Firmen-Vektorisierung):**
     - Bei getrennten Mandanten- oder Firmenthemen strikte Vektortrennung sicherstellen.
     - **Prüfung 1 (Strikter Privacy & Anti-Leak Check):** Es dürfen niemals private Identifikatoren (persönliche Finanzen, Gesundheit, Familie) in geteilte Wissensspeicher fließen.
     - **Prüfung 2 (Zero-Leak Secret-Sanitizer):** Alle Secrets und Passwörter durch `[IN_PASSWORT_MANAGER_GESICHERT]` ersetzen.

---

## 📋 Step-by-Step Archival Lifecycle

1. **Triage & Classification:**
   Prüfe, ob Standard-Pfad oder ein isolierter Mandanten-/Team-Pfad vorliegt. Bei Team-Pfaden Datenschutz-Check durchführen.

2. **Harness-Erkennung & Transkript-Generierung:**
   - **In Hermes Agent (0-Token-Extraktion):**
     Der Agent führt das universelle, harness-agnostische Extraktions-Skript aus:
     ```bash
     python tools/scripts/export_session.py --title "Titel des Chats"
     ```
     Dies erkennt die aktive Harness (Antigravity, Hermes, Goose, Claude Code) automatisch, bereinigt Telemetrie und Passwörter und exportiert den Dialog direkt nach `00_MEMORY/transcripts/`.
   - **In Antigravity:**  
     Chatverlauf auslesen, von Telemetrie/System-Tags säubern, Passwörter durch `[IN_PASSWORT_MANAGER_GESICHERT]` ersetzen und nach `00_MEMORY/transcripts/YYYY-MM-DD - [Descriptive_Title].md` schreiben.

3. **Incremental Vector Ingestion:**  
   Index the new transcript into the appropriate database shard using `python tools/scripts/memory_indexer.py --file "00_MEMORY/transcripts/<Dateiname.md>"`.

4. **Kristallisierung & DYNAMIC_STATE (Deterministisch via Skript oder In-Harness):**  
   - **Tier 1 (In-Harness Modus / Zero-API Default):**  
     Falls keine externen API-Keys konfiguriert sind (Abo-Modelle wie Claude Pro, ChatGPT Plus, Antigravity), extrahiert der aktive Chat-Agent 1 bis 3 Kronjuwelen-Fakten (Signal über Rauschen: Kernbeschlüsse, Heureka-Erkenntnisse) direkt während des Archivierens und trägt sie ein via:  
     `python scripts/memory.py add <Namespace> <Key> "<Inhalt>"`
   - **Tier 2 (Multi-Provider Hintergrund-Pipeline):**  
     Wenn API-Keys (Gemini, OpenRouter, OpenAI) oder ein lokales Ollama aktiv sind, führt der Agent aus:  
     `python tools/scripts/crystallize_memory.py --scan-transcripts`  
     Dies überträgt Kronjuwelen-Fakten nach LangMem/Cognee und aktualisiert `DYNAMIC_STATE.md` (inkl. 10 Fakten & Quellenlage) vollautomatisch.

5. **Mandatory Post-Archiving Quality Control (QC) & Report:**  
   Immediately and autonomously perform the following verification checklist and present the results in a structured QC report:
   - **Sprecher-Integrität:** Verify that all human speaker headers strictly use `## <User_Name> (...)`. The generic label `## User` must occur exactly **0 times**.
   - **Chronologie & Vollständigkeit:** Verify that the transcript starts with the exact first prompt of the active session (e.g. from the start date) and runs chronologically without prepending foreign sessions or truncating early history.
   - **Header Hierarchy:** Verify H1 title immediately followed by H2 first speaker (no metadata block in transcript).
   - **Hygiene & Sanitization:** Confirm total removal of `<CONTEXT_SUMMARY>`, `<USER_REQUEST>`, `<USER_SETTINGS_CHANGE>`, raw tool telemetry, and complete replacement of all secrets/passwords with `[IN_PASSWORT_MANAGER_GESICHERT]`.
   - **Vector Routing:** Confirm embeddings written strictly to the target vector shard.
   - **Dynamic State & Fakten:** Confirm synchronization in `00_MEMORY/DYNAMIC_STATE.md`.

