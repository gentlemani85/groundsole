# Workspace Entry Anchor - Groundsole

This file is the canonical, tool-neutral entry point for any agentic harness (Antigravity, Hermes, Goose, Claude Code, Codex).

## 1. Minimal Core Triad (Session Startup)
Before performing any tasks, read silently and in sequence:
1. `00_MEMORY/STYLE_AND_GUARDRAILS.md` (Interaction standards, causality test, grounded communication)
2. `00_MEMORY/DYNAMIC_STATE.md` (Living operational state & active focus)

Do NOT automatically load any other files (no legacy indices, no raw transcripts).

## 2. Memory & Information Retrieval (Token-Hygiene)
Follow the strict deterministic retrieval hierarchy (Fastest & Leanest to Deepest):
1. **Primary: Structured Facts (LangMem)**  
   Query first via `python tools/scripts/memory.py search "<Topic>"` (sub-millisecond SQLite/FTS5 lookup, 0 context tokens). Delivers atomic parameters, milestones, and decisions directly.
2. **Secondary: Relational Knowledge Graph (Cognee)**  
   Query via `python tools/scripts/cognee_graph.py query "<Topic>"` for entity relationships and conceptual connections.
3. **Tertiary: Deep Semantic Vector Search (Tiefengedächtnis)**  
   Query via `python tools/scripts/memory_retriever.py -q "<Topic>"` for historical trajectories, exact phrasing, and voice context across transcripts.
4. **Quaternary: Precise Line Citations in Transcripts**  
   Only open a specific transcript in `00_MEMORY/transcripts/` if a vector search hit provides the exact line range. Never scan or dump entire Markdown files into context.
