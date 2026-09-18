---
name: stream-archive
description: "Automated session transcript archiving, telemetry sanitization, signature generation, and long-term memory crystallization."
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
> 3. Extracts a structured, dense signature into `00_MEMORY/summaries/`.
> 4. Triggers incremental ingestion into the active semantic vector database shard.

---

## Trigger Conditions

Activate this skill when:
- The user requests: *"Archive this session"*, *"Export and archive chat"*, *"Sync transcripts"*, or *"Process new chats"*.
- A conversation reaches major milestone breakthroughs or nears the context token ceiling.

---

## 📝 Formatting & Sanitization Standards

Every session transcript saved to `00_MEMORY/transcripts/` must strictly adhere to these formatting rules:

1. **Heading Hierarchy (H1 vs H2 vs H3):**
   - **H1 (`#`)**: Solely the main title at the very top (e.g., `# 2026-09-18 - Groundsole Core Architecture`).
   - **H2 (`##`)**: Solely the speaker headings with timestamps:
     - `## User (YYYY-MM-DDTHH:MM:SS+02:00)`
     - `## Antigravity (YYYY-MM-DDTHH:MM:SS+02:00)` (or Claude / Hermes / etc.)
   - **H3 (`###`) and below**: All section headings *within* responses.

2. **Telemetry Sanitization & Anti-Noise:**
   - **System XML Tags:** Completely strip all system wrapper tags: `<ADDITIONAL_METADATA>`, `<CONTEXT_SUMMARY>`, `<USER_REQUEST>`, `<SYSTEM_MESSAGE>`.
   - **Client Telemetry:** Strip tool JSON schemas, voluminous compiler dumps, unformatted stack traces, and base64 strings.
   - **Rationale:** Only genuine reasoning, decisions, and factual dialogue belong in the transcript. Telemetry noise degrades semantic vector embeddings.

3. **Direct H1-to-H2 Transition (No Metadata Header):**
   - Directly after H1, the first speaker H2 **must follow immediately** (`# Title \n\n ## User (...)`).
   - Do **not** inject metadata lines (`Date:`, `Participants:`, `Status:`) into the transcript. All metadata belongs exclusively in the signature file (`00_MEMORY/summaries/`).

---

## 📋 Step-by-Step Archival Lifecycle

1. **Inspect & Sanitize:**  
   Read the raw export, ensure proper H1/H2 formatting, and remove all telemetry junk.
2. **Save Transcript:**  
   Write the sanitized file to `00_MEMORY/transcripts/YYYY-MM-DD - [Descriptive_Title].md`.
3. **Generate Signature Block:**  
   Create `00_MEMORY/summaries/YYYY-MM-DD - [Descriptive_Title]_signature.md` with:
   ```markdown
   # FILE: [filename without extension]
   DATE: [YYYY-MM-DD]
   SIZE: [Size in KB]
   DOMAINS: [Relevant domain clusters, e.g. Architecture, Operations, Strategy]
   ORGANISM_STATE: [1-2 sentences on state and context at the time of session]
   CORE_INSIGHTS: [2-3 sentences summarizing genuine breakthroughs and decisions]
   FIRST_MENTIONS: [New concepts, terms, or entity names introduced here]
   REFERENCES: [Linked files, external URLs, or entity references]
   ```
4. **Update Dynamic State:**  
   Update `00_MEMORY/DYNAMIC_STATE.md` with current archive counts and operational focus.
5. **Incremental Vector Ingestion:**  
   Index the new transcript into the local active database shard (`active.db`).
