# 05 - Document Lifecycle, Plaintext SSOT & Derived Views

> **Framework:** Groundsole  
> **Architecture Pattern:** 3-Tier Document Hierarchy & Pure Materialized Projections

---

## 1. Context & Motivation

In a personal cognitive workspace powered by local and cloud AI agents, files quickly face two failure modes:
1. **The Trap of Parallel Copies:** Summary dashboards or slide decks maintain hardcoded text copies instead of reading directly from the underlying markdown source, creating conflicting truths.
2. **Loss of Epistemic Integrity:** Ephemeral chat working thoughts or speculative drafts get conflated with immutable personal facts and verified decisions.

To maintain perfect mental clarity, Groundsole establishes a clean **3-Tier Document Hierarchy**.

---

## 2. The 3-Tier Document Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│  Tier 1: Working / Raw Artifacts (Ephemere Arbeitsdaten)     │
│  • Scratchpads, raw scans, active session logs, drafts      │
│  • High velocity, fluid edits, cognitive RAM                │
└──────────────────────────────┬──────────────────────────────┘
                               │ Crystallized & Curated into
                               ▼
┌─────────────────────────────────────────────────────────────┐
│  Tier 2: Authoritative Master Records (Autoritative SSOT)   │
│  • Durable knowledge modules (Markdown) and local SQLite    │
│  • Git-versioned single source of truth                     │
│  • Grounded facts, verified contracts, core principles      │
└──────────────────────────────┬──────────────────────────────┘
                               │ Compiled / Projected into
                               ▼
┌─────────────────────────────────────────────────────────────┐
│  Tier 3: Derived Views (Abgeleitete / Materialisierte Sicht)│
│  • Personal cockpits, interactive HTML decks, PDF exports   │
│  • 100% deterministically generated from Tier 2             │
│  • Strictly read-only: Manual edits in Tier 3 are forbidden │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Tier 2: The Plaintext Source of Truth (SSOT)

Every durable decision, life parameter, and project state lives in **exactly one canonical Markdown file** or the local fact database (`langmem_store.db`).
* **Surgical Edits Only:** AI agents must never overwrite full files with blind dumps. Edits are applied surgically (`replace_file_content`) to preserve human manual edits.
* **Deterministic Traceability:** Every change is locally tracked in Git, ensuring 100% reversibility and autonomy.

---

## 4. Tier 3: The Materialized View Principle

Presentations, visual cockpits, and web dashboards are **pure projections**, never independent storage locations:
* **No Hardcoded Data:** Never hardcode metrics, facts, or tables into HTML or presentation templates.
* **Direct Markdown Binding:** Tools must parse the Tier 2 Markdown files directly or rebuild deterministically from source markdown notes.
* When Tier 2 updates, Tier 3 updates on reload.

---

## 5. The Anti-Puffery Rule (Grounded Facts)

Groundsole strictly enforces sober, biophysical communication:
* **No Artificial Hype:** Never invent hypothetical savings or consulting buzzwords.
* **Naked Biophysical Facts:** Parameters are stated soberly: real costs, measured latency, hardware wattage, timestamps, and contract terms.
