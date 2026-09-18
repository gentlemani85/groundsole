# 04 - Scalable Multi-DB Sharding & Storage Architecture

> **Status:** 2026-09-18  
> **Framework:** Groundsole

---

## 1. The Real-World Failure of Monolithic Databases

Most RAG tutorials recommend storing all embeddings in a single monolithic vector database (e.g. a single `vectors.db` or Chroma/Pinecone instance). 

In long-running production environments operating across multiple devices synchronized via cloud storage (iCloud, OneDrive, SharePoint, Google Drive), monolithic databases suffer from fatal physical bottlenecks:

1. **Bandwidth Churn:** When a 200 MB+ database file changes by even a single chunk, the entire file must be re-uploaded by the cloud sync daemon.
2. **File Lock Collisions:** Asynchronous cloud sync clients frequently lock the database file during upload, causing `sqlite3.OperationalError: database is locked`.
3. **Database Corruption:** Concurrent writes across two unsynchronized laptops result in corrupted database states or "conflicted copy" files.

---

## 2. Multi-DB Sharding: Production Reality vs. Target Concept

To prevent cloud-sync thrashing, Groundsole establishes a log-structured multi-database architecture.

```text
vectors/
├── [archive_001.db]       <-- SEALED HISTORICAL EPOCH (Read-Only)
│                              • Synced to cloud ONCE. Never modified again.
│                              • Zero bandwidth churn, zero lock conflicts.
│
└── [user_active.db]       <-- ACTIVE WORKING SHARD (Current Sessions)
                               • High-speed incremental writes.
                               • Rapid, low-overhead sync across devices.
```

### Current Production State (IST-Stand):
* **Manual Shard Separation:** The historical archive (thousands of past sessions) is isolated into an immutable, read-only shard (`archive_001.db`). New session transcripts are indexed into an active working shard (`user_active.db`).
* **Federated Multi-DB Discovery:** The retrieval script discovers all matching `*.db` files in the vector folder and queries them concurrently, aggregating and ranking results in a single response stream.

### Conceptual Roadmap (KONZEPT - NOCH NICHT IMPLEMENTIERT):
* **Automated Threshold Auto-Sealing:** An automated routine that monitors `user_active.db` and automatically freezes/rotates it into a new numbered archive shard once a specific chunk or megabyte threshold is crossed.  
  *(Status: Architectural concept. Must be developed and tested in production before deployment into the core toolkit.)*

---

## 3. Multi-Tenant & Collaborative Federation (IST-Stand)

In shared workspaces (e.g. family environments, research teams, or corporate divisions), database files are partitioned by identity while remaining federated:

```text
PARTNERSHIP_SPACE / TEAM_SPACE
├── vectors/
│   ├── user_archive_001.db     (User sealed historical archive)
│   ├── user_active.db          (User active working memory)
│   ├── partner_archive_001.db  (Partner sealed archive)
│   ├── partner_active.db       (Partner active memory)
│   └── team_shared.db          (Shared organizational knowledge)
```

### Scoped Retrieval
The retriever dynamically queries target databases based on the requested scope:
- `scope="me"`: Queries only user-owned databases.
- `scope="partner"`: Queries only partner-owned databases.
- `scope="all"`: Queries all discovered databases in the folder.

---

## 4. The Multi-Model Cognitive Triad

Groundsole balances memory across three complementary representations:

| Memory Layer | Storage Mechanism | Best Used For |
| :--- | :--- | :--- |
| **Plaintext Markdown** | UTF-8 Files (`00_MEMORY/`) | Authoritative Single Source of Truth (SSOT), human inspection, Git tracking |
| **Semantic Vector Shards** | Multi-DB SQLite (`vectors/*.db`) | Associative recall, fuzzy matching, historical trajectory searches across years |
| **Knowledge Graph** | Relational Graph (`cognee_db`) | Rigid entity topologies, family trees, infrastructure graphs, hardware specs |
| **Key-Value Fact Store** | Structured KV (`langmem_store.db`)| Fast user preferences, operational constraints, live counters |
