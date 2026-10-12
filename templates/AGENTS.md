# Workspace Entry Anchor - Groundsole

This file is the canonical, tool-neutral entry point for any agentic harness (Antigravity, Hermes, Claude, Codex).

## 1. Minimal Core Triad (Session Startup)
Before performing any tasks, read silently and in sequence:
1. `00_MEMORY/STYLE_AND_GUARDRAILS.md` (Interaction standards, causality test, grounded communication)
2. `00_MEMORY/DYNAMIC_STATE.md` (Living operational state & active project focus)

Do NOT automatically load any other files (no legacy indices, no raw transcripts).

## 2. Memory & Information Retrieval (Token-Hygiene)
Follow the strict deterministic retrieval hierarchy:
1. **Primary: Semantic Vector Search & Structured Facts**
   Query first via vector search (`tools/scripts/memory_retriever.py`) or key-value fact store (`tools/scripts/memory.py`). This delivers precise facts and relationships with minimal token consumption.
2. **Secondary: Precise Line Citations in Transcripts**
   Only open a specific transcript in `00_MEMORY/transcripts/` if a vector search hit provides the exact line range. Never scan or dump entire Markdown files into context.
