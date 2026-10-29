# 02 - Memory Hierarchy & Cognitive Lifecycle

> **Status:** 2026-09-18  
> **Framework:** Groundsole

---

## 1. Ephemeral Working RAM vs. Durable Long-Term Memory

A critical misconception in agentic AI is assuming that an ongoing conversation automatically integrates into persistent long-term memory. 

In Groundsole, the operational boundary is clear:

```text
┌──────────────────────────────────────────────────────────────┐
│ 1. Active Working Session (Volatile Cognitive RAM)          │
│ • Uncommitted dialogue, temporary drafts, immediate thoughts │
│ • Lives ONLY inside the active prompt context window        │
│ • Susceptible to context window compression / truncation     │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               │ ⚠️ Archiving Event (stream-archive)
                               ▼
┌──────────────────────────────────────────────────────────────┐
│ 2. Immutable Transcripts (Frozen Primary Historical Evidence)│
│ • 00_MEMORY/transcripts/YYYY-MM-DD - Title.md               │
│ • Stripped of telemetry, system XML, and compiler dumps      │
│ • Authoritative, unchangeable historical truth               │
└──────────────────────────────┬───────────────────────────────┘
                                │
                                ▼
                ┌──────────────────────────────┐
                │ 3. Long-Term Retrieval       │
                │ • Semantic Vector Shards     │
                │ • Key-Value Facts (LangMem)  │
                │ • Knowledge Graph Relations  │
                │ • Cross-year semantic search │
                └──────────────────────────────┘
```

> [!IMPORTANT]
> **The Memory Crystallization Rule:**  
> **Long-term memory is NOT written while a session is actively running.**  
> Persistent recall crystallizes only when a session or major milestone is explicitly processed through the `stream-archive` lifecycle. Until that moment, memories exist only in temporary working context.

---

## 2. The Three Runtime Layers (Token Conservation)

To avoid "Lost in the Middle" degradation and ballooning token consumption, Groundsole divides files into three access tiers:

1. **Layer 1: Active Runtime Core (Minimal Session Start)**  
   - `AGENTS.md` (root anchor & entry pointer)
   - `00_MEMORY/STYLE_AND_GUARDRAILS.md` (peer coprocessor tone & causality test)
   - `00_MEMORY/DYNAMIC_STATE.md` (immediate focus, active blockers, open tasks)  
   *-> Loaded silently upon every session initialization.*

2. **Layer 2: On-Demand Domain Modules (Deterministic Domain State)**  
   - `00_MEMORY/modules/OPERATIONS_AND_PROJECTS.md`
   - `00_MEMORY/modules/RESOURCES_AND_FINANCE.md`
   - `00_MEMORY/modules/INFRASTRUCTURE_AND_ASSETS.md`
   - `00_MEMORY/modules/LEARNING_AND_SKILLS.md`  
   *-> Loaded ONLY when the user's inquiry explicitly touches that domain.*

3. **Layer 3: Immutable Archive & Deterministic Retrieval**  
   - `00_MEMORY/transcripts/*.md` (raw primary dialogues)
   - `00_MEMORY/vectors/*.db` & `00_MEMORY/langmem_store.db` (semantic & key-value facts)  
   *-> Queried on demand via semantic vector search or memory_retriever.py.*

---

## 3. Subagent Token Protection

When subagents or background tasks are spawned, they halt their load order immediately after reading `AGENTS.md`. They bypass all domain modules and style guides, reserving 100% of their context budget for their specialized task.

---

## 4. The Three-Tier Vector & Fact Storage Architecture

Groundsole prevents context rot and database contamination through strict physical separation:

```text
┌─────────────────────────────────────────────────────────────┐
│ Tier 1: Volatile Session Buffer (memory_buffer.db)          │
│ • Mirrors active, uncommitted sessions across local harness │
│ • Delta-indexing runs asynchronously in < 1 second           │
│ • Serves as safety net / backup against accidental deletion │
│ • Pruned during cleanup routines without polluting active   │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               │ Explicit Archiving Event
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ Tier 2: Curated Active Memory (memory_active.db)            │
│ • Pure sink for verified Markdown files in transcripts/     │
│ • Guaranteed idempotent via UNIQUE(content_hash)            │
│ • Zero ephemeral noise, zero zombie vectors                 │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               │ Epoched at capacity (~40k chunks)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ Tier 3: Sealed Epoch Archives (memory_archive_001.db ...)   │
│ • Immutable, read-only cold storage                         │
└─────────────────────────────────────────────────────────────┘
```

### Causal State & Fact Extraction Protocol (Post-Archival Crystallization)
Facts, parameters, and binding decisions are not extracted randomly during active conversation. Following **Principle 14 (Deterministic Downstream)**, fact and graph crystallization is strictly tied to the archiving event:
- **Decoupled from Chat Loop:** The agent does not run background extraction prompts during active dialogue turns. This preserves working memory and prevents context fragmentation.
- **Post-Archival Processing (`crystallize_memory.py`):** When a session transcript is finalized and indexed, an isolated downstream processor analyses the cohesive conversation context.
- **Strict Signal-Over-Noise Filter:** Extraction enforces a hard ceiling of **1 to 3 fundamental breakthrough facts or binding decisions** per session. Incremental code edits, trivial chatter, or styling adjustments yield empty results.
- **Deterministic Key Consolidation:** Extracted facts are strictly mapped to normalized namespaces (`ERKENNTNIS`, `ENTSCHEIDUNG`, `PRINZIP`, `SYSTEM`), continuously overwriting previous states rather than accumulating duplicate fragments.

---

## 5. Dual-Channel Context Architecture & Delta Synchronization

### Dual-Channel Context (RAM Context Window vs. Disk Vector Buffer)
Every dialogue turn exists simultaneously across two independent layers:
1. **Channel 1: Volatile In-Memory RAM (Context Window):**
   Handles fast, direct conversational flow. When context boundaries are reached due to extensive tool calls or long dialogue history, the platform server may compact previous turns into `<CONTEXT_SUMMARY>`.
2. **Channel 2: Persistent On-Disk Vector Buffer (`memory_buffer.db`):**
   Stores raw turns as hashed vector embeddings. This provides 100% loss-resistance: even if the in-memory window is compacted or an active chat is closed, all raw verbatim excerpts and technical figures remain instantly searchable.

### Autonomous Delta Synchronization
Buffer indexing never requires manual intervention:
- **Startup Trigger:** Executed in the background during session initialization (`python3 scripts/memory_indexer.py --scan-harness &`), ensuring the buffer is always up to date with zero user wait time.
- **Just-In-Time (JIT) Retriever Sync:** Before executing any search query, `memory_retriever.py` checks active harness logs for new turns. Unchanged sessions evaluate in ~0.02s; new turns are vectorized incrementally in 1–3s before returning search results.
- **Digital Hygiene & Thought Clearance:** Compaction warnings are treated calmly. Since all data is preserved in Tier 1, archiving via `stream-archive` is conducted deliberately as a hygiene step when a cohesive milestone is completed, resetting working memory for maximum model precision.

---

## 6. Dormant Memory Consolidation & Gatekeeping (Groundsole Dreaming)

To prevent cognitive entropy, stale deadlines, and contradictory decisions from accumulating across historical tiers:
- **Dormant Consolidation (`dreaming.py`):** Runs offline to evaluate temporal decay, compute dense semantic clusters via local FastEmbed, and resolve contradictions with sub-cent LLM verification.
- **Safe Non-Destructive Gatekeeping (`memory.py`):** Deprecated and expired records are marked with `[STATUS: DEPRECATED]` or `[STATUS: EXPIRED]` and filtered automatically from standard search/list queries, maintaining high-precision recall while guaranteeing an immutable audit trail.
*(-> Full architecture in [08_CONTEXT_FILTERING_AND_DREAMING_CONSOLIDATION.md](08_CONTEXT_FILTERING_AND_DREAMING_CONSOLIDATION.md))*



