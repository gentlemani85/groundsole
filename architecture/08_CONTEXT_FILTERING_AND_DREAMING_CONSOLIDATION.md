# 08 - Context Filtering & Dreaming Memory Consolidation

> **Status:** 2026-10-12  
> **Framework:** Groundsole v0.2.0  
> **Principles:** Principle 15 (Biophysical Memory Consolidation), Principle 16 (Deterministic Context Buffering)

---

## 1. The Twin Bottlenecks of Agentic Cognition

Modern LLM-powered harnesses operate under two fundamental physical constraints that inevitably degrade agentic performance over extended lifecycles:

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. Working RAM Vulnerability: Context Window Contamination                   │
│ • Heavy shell outputs, compiler traces, and verbose HTML flood prompt space │
│ • Displaces critical instructions, inflates latency, and skyrockets costs   │
│ ➔ Solution: Groundsole Context-Filter MCP Proxy                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                       ▲
                                       │ (Complementary Optimization)
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 2. Long-Term Memory Vulnerability: Cognitive Entropy & Fact Bloat           │
│ • Fast session capture accumulates obsolete decisions, expired dates & dupes│
│ • Contradictions between old and new facts confuse retrieval and inference   │
│ ➔ Solution: Groundsole Deep Dreaming Engine                                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. The Context-Filter MCP Proxy (Zero-Spill Terminal & Web Buffer)

### Problem: Context Contamination
When an agent runs commands like `npm test`, `git log`, `curl`, or deep file searches, hundreds or thousands of output lines dump straight into the conversation context. This produces:
1. **Attention Diffusion ("Lost in the Middle"):** Critical guardrails in the system prompt lose attention weight.
2. **Context Window Exhaustion:** Accelerates automatic conversation compaction, wiping out recent nuance.
3. **Severe Economic Waste:** Paying for thousands of tokens of boilerplate logs on every subsequent prompt.

### Architecture
The Groundsole Context-Filter runs as a standard **Model Context Protocol (MCP)** server over `stdio` (`tools/scripts/context_filter_mcp.py`):

```text
 Agent Turn ──▶ ctx_execute("pytest")
                      │
                      ▼
 ┌──────────────────────────────────────────────────────────┐
 │ Context-Filter MCP Server (context_filter_mcp.py)        │
 │ 1. Headless Execution: Subprocess runs silently          │
 │ 2. Ephemeral Storage: Full output saved to SQLite FTS5   │
 │    (/tmp/groundsole_ctx_cache.db)                        │
 │ 3. Signal Extraction: Scans for errors, exits & keywords │
 └────────────────────────────┬─────────────────────────────┘
                              │
                              ▼
 Agent Context ◀── Condensed Summary (Exit Code, 10 Signal Lines, Cache-ID)
                              │
                              ▼ (If deep inspection needed)
 Agent ──▶ ctx_inspect_lines(cache_id, start=42, end=55)
```

### Provided Tools
1. `ctx_execute`: Executes shell commands. Outputs under threshold (`max_lines=25`) are returned directly. Larger outputs are buffered in SQLite FTS5; only exit codes, signal lines (errors, exceptions), and preview snippets enter the prompt.
2. `ctx_inspect_lines`: Retrieves precise line ranges using a specific `cache_id`.
3. `ctx_search_output`: Executes SQLite FTS5 full-text regex/literal searches with surrounding context lines.
4. `ctx_read_url`: Fetches web pages headless, strips HTML tags/boilerplate, buffers the markdown in cache, and returns relevant sections matching a query.

---

## 3. The Deep Dreaming Engine (Biophysical Memory Consolidation)

### Problem: Cognitive Entropy in Long-Term Memory
In an active coprocessor relationship, facts, decisions, and system parameters are captured continuously across dozens of sessions. Over weeks and months, three forms of entropy arise:
1. **Temporal Decay:** Appointments, deadlines, and temporary workarounds become obsolete once their date passes.
2. **Decision Supersession:** A decision made in March (e.g. *Tool X selected*) is superseded by an architectural pivot in September (*Switched to Tool Y*). Without consolidation, retrieval surfaces both, confusing the model.
3. **Redundant Accumulation:** Similar facts formulated slightly differently across separate sessions bloat vector searches.

### The Biological Metaphor: Sleep & Dreaming
Groundsole separates knowledge acquisition from knowledge consolidation:
- **Waking State (Fast Acquisition):** During active dialogues, facts are recorded swiftly into `00_MEMORY/langmem_store.db` without slowing down the user.
- **Dreaming State (Consolidation & Pruning):** Periodically, during idle periods or via explicit invocation (`python3 scripts/dreaming.py --apply`), the Dreaming engine executes a multi-stage consolidation cycle.

```text
 ┌───────────────────────────────────────────────────────────────────────────┐
 │ 1. Temporal Decay Audit                                                   │
 │ Scans date patterns in time-bound namespaces ("Termine", "Deadlines").    │
 │ Marks passed dates deterministically: [STATUS: EXPIRED | Termin abgelaufen│
 └─────────────────────────────────────┬─────────────────────────────────────┘
                                       │
                                       ▼
 ┌───────────────────────────────────────────────────────────────────────────┐
 │ 2. Local Neural FastEmbed Clustering                                      │
 │ Generates dense embeddings (jina-embeddings-v2-base-de) in memory.        │
 │ Computes pairwise Cosine Similarity matrix in milliseconds (>= 0.74).     │
 └─────────────────────────────────────┬─────────────────────────────────────┘
                                       │
                                       ▼
 ┌───────────────────────────────────────────────────────────────────────────┐
 │ 3. Sub-Cent LLM Dispute Resolution (Gemini Flash)                         │
 │ Evaluates candidate pairs for contradiction or redundancy.                │
 │ Actions: deprecate_older | merge_redundant | keep_both                    │
 │ Result permanently cached in dreaming_checked_pairs (0 repeated cost).    │
 └─────────────────────────────────────┬─────────────────────────────────────┘
                                       │
                                       ▼
 ┌───────────────────────────────────────────────────────────────────────────┐
 │ 4. Knowledge Graph & State Synchronization                                │
 │ Marks superseded edges in graph.db / cognee_db as deprecated.             │
 │ Prunes completed milestones in DYNAMIC_STATE.md.                          │
 └─────────────────────────────────────┬─────────────────────────────────────┘
                                       │
                                       ▼
 ┌───────────────────────────────────────────────────────────────────────────┐
 │ 5. Safe Memory Gatekeeping                                                │
 │ memory.py search/list filters [STATUS: DEPRECATED] and [STATUS: EXPIRED]  │
 │ by default, ensuring clean retrieval while preserving immutable audit logs│
 └───────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Safe Gatekeeping & Non-Destructive Deprecation

Groundsole enforces an absolute safety guarantee: **Dreaming never hard-deletes memories.**

1. **Non-Destructive Annotation:**
   - Obsolete records are updated with explicit prefixes:
     `[STATUS: DEPRECATED | Abgelöst am 2026-10-12 durch 'key_b']: <Originaltext>`
     `[STATUS: EXPIRED | Termin 2026-10-06 abgelaufen]: <Originaltext>`
2. **Default Gatekeeper Filtering:**
   - Standard retrieval (`memory.py search <query>` and `memory.py list`) adds `WHERE content NOT LIKE '[STATUS: DEPRECATED%' AND content NOT LIKE '[STATUS: EXPIRED%'`.
   - The active agent only receives authoritative, currently valid facts.
3. **Full Auditability:**
   - Passing `--all` or `--include-deprecated` restores the complete historical evolution for compliance and audit requirements.
