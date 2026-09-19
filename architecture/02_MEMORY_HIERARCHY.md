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
            ┌──────────────────┴──────────────────┐
            ▼                                     ▼
┌──────────────────────────────┐    ┌──────────────────────────────┐
│ 3. Dense Signatures          │    │ 4. Long-Term Retrieval       │
│ • 00_MEMORY/summaries/       │    │ • Semantic Vector Shards     │
│ • Fast topological routing   │    │ • Knowledge Graph Relations  │
│ • First mentions & clusters  │    │ • Cross-year semantic search │
└──────────────────────────────┘    └──────────────────────────────┘
```

> [!IMPORTANT]
> **The Memory Crystallization Rule:**  
> **Long-term memory is NOT written while a session is actively running.**  
> Persistent recall crystallizes only when a session or major milestone is explicitly processed through the `stream-archive` lifecycle. Until that moment, memories exist only in temporary working context.

---

## 2. The Three Runtime Layers (Token Conservation)

To avoid "Lost in the Middle" degradation and ballooning token consumption, Groundsole divides files into three access tiers:

1. **Layer 1: Active Runtime Core (Minimal Session Start)**  
   - `00_MEMORY/index.md` (authoritative index & source priorities)
   - `00_MEMORY/STYLE_AND_GUARDRAILS.md` (peer coprocessor tone & causality test)
   - `00_MEMORY/DYNAMIC_STATE.md` (immediate focus, active blockers, open tasks)  
   *-> Loaded silently upon every session initialization.*

2. **Layer 2: On-Demand Domain Modules (Deterministic Domain State)**  
   - `00_MEMORY/modules/OPERATIONS_AND_PROJECTS.md`
   - `00_MEMORY/modules/RESOURCES_AND_FINANCE.md`
   - `00_MEMORY/modules/INFRASTRUCTURE_AND_ASSETS.md`
   - `00_MEMORY/modules/LEARNING_AND_SKILLS.md`  
   *-> Loaded ONLY when the user's inquiry explicitly touches that domain.*

3. **Layer 3: Immutable Archive & Secondary Indices**  
   - `00_MEMORY/transcripts/*.md` (raw primary dialogues)
   - `00_MEMORY/summaries/*.md` (routing signatures)  
   *-> Queried on demand via semantic vector search or ripgrep.*

---

## 3. Subagent Token Protection

When subagents or background tasks are spawned, they halt their load order immediately after reading `index.md`. They bypass all domain modules and style guides, reserving 100% of their context budget for their specialized task.

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

### Causal State & Fact Extraction Protocol (LangMem)
Facts, parameters, and binding decisions do not wait for vector consolidation. At the end of every dialog turn, the coprocessor autonomously checks if a durable fact was established:
- **Decisions & Directional Shifts:** Tool choices, approved roadmaps, canceled plans.
- **Counterpart & Project Facts:** Quotes, commitments, deadlines, rates.
- **Infrastructure & Numerical State:** Measured values, consumption, hardware specs.
- **Universal Catch-All:** Any information whose absence in future sessions would cause friction, repetition, or false assumptions.

