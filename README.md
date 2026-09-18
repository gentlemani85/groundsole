# Groundsole

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Public_Release-emerald.svg)](https://github.com/gentlemani85/groundsole)

> **The grounded operating framework for sovereign AI coprocessors.**  
> *Biophysical causality, plaintext SSOT, multi-DB memory sharding, and radical tool neutrality.*

[🇩🇪 Deutsche Version / German Edition](README_DE.md)

---

## 1. How to Initialize a Workspace (For Any User)

You do not need complex installation scripts. Whether using Google Antigravity, Open-Source Hermes Agent, Claude Code, or Codex:

### Method 1: The One-Prompt Setup (Easiest)
Create a new, empty folder (e.g. `~/Documents/COCKPIT`), open your AI agent in that folder, and prompt:
> **"Read https://raw.githubusercontent.com/gentlemani85/groundsole/main/templates/bootstrap.md and set up my system."**

The agent fetches the blueprint, asks you which profile you want (or decides autonomously if you prefer), installs the isolated Python environment outside your cloud storage, and provisions all tools.

### Method 2: Manual Download
1. Download [bootstrap.md](https://raw.githubusercontent.com/gentlemani85/groundsole/main/templates/bootstrap.md) into your workspace directory.
2. Tell your AI: **"Read bootstrap.md and set up my system."**

### Method 3: CLI Scaffolding (Power Users)
```bash
git clone https://github.com/gentlemani85/groundsole.git
cd groundsole

# Scaffold a tailored instance:
python3 tools/init_instance.py --target ~/Documents/STUDENT_COCKPIT --profile school --user "Alex"
```

---

## 2. Directory Structure

```text
groundsole/
├── LICENSE                            # MIT License (2026 Emanuel Gössler)
├── README.md                          # Framework overview & manifest (English)
├── README_DE.md                       # German edition
├── version.json                       # Upstream release tracking
├── architecture/                      # Foundational architectural principles
│   ├── 01_CORE_PRINCIPLES_AND_SSOT.md # Ground test, causality & As-Is truthfulness
│   ├── 02_MEMORY_HIERARCHY.md         # RAM vs. Long-term memory, 3-tier loading strategy
│   ├── 03_ROLLOUT_AND_INSTANCES.md    # Decoupled Hub-and-Spoke model
│   └── 04_SCALABLE_STORAGE_AND_SHARDING.md # Multi-DB sharding & cloud-sync resilience
├── templates/                         # Clean boilerplate templates
│   ├── AGENTS.md                      # Universal agent entry point
│   ├── index.md                       # Authoritative memory index
│   ├── LOAD_ORDER.md                  # Minimal runtime load order
│   ├── STYLE_AND_GUARDRAILS.md        # Coprocessor tone & causality checks
│   ├── DYNAMIC_STATE.md               # Active operational focus
│   ├── bootstrap.md                   # Self-Executing Master Bootstrap Prompt
│   └── modules/                       # Universal domain state modules
│       ├── OPERATIONS_AND_PROJECTS.md # Deliverables & milestones (personal / team)
│       ├── RESOURCES_AND_FINANCE.md   # Liquidity, budgets & commitments
│       ├── INFRASTRUCTURE_AND_ASSETS.md# Workstations, environments & tooling
│       └── LEARNING_AND_SKILLS.md     # Academic curricula & skill mastery
├── skills/                            # Pre-configured Groundsole skills
│   ├── stream-archive/                # Sanitizes, signs, and freezes sessions into transcripts
│   ├── memory-recall/                 # Unified search across vectors, graph, facts & plaintext
│   ├── document-export/               # Exports Markdown to Word (.docx) and A4 PDF (.pdf)
│   ├── mail-manager/                  # Checks and sends emails via IMAP/SMTP (Gmail, Outlook)
│   ├── system-hygiene/                # Entropy reduction, cache cleanup & link audit
│   └── inbox-triage/                  # Deterministic ingestion of raw files from Inbox/
└── tools/                             # Automation & Execution Engines
    ├── init_instance.py               # Instance generator tool
    ├── check_update.py                # Decentralized upstream update checker
    └── scripts/                       # Core Python Utility & Memory Engines
        ├── memory.py                  # Key-value fact store with cloud conflict resolution
        ├── memory_indexer.py          # FastEmbed Jina ONNX transcript vector indexer
        ├── memory_retriever.py        # Multi-DB federated semantic search engine
        ├── knowledge_graph.py         # Zero-API relational knowledge graph (SQLite)
        ├── document_exporter.py       # Word (.docx) and print-ready PDF generator
        └── mail_helper.py             # Zero-dependency IMAP/SMTP email assistant
```

---

## 3. The 4-Tier Memory Architecture

Groundsole models persistent cognition across four complementary layers:

1. **Plaintext Markdown SSOT (`00_MEMORY/`):** Human-readable, Git-versioned state.
2. **Key-Value Fact Store (`memory.py`):** Lightning-fast personal facts and preferences with automatic cloud-sync conflict resolution.
3. **Semantic Vector Shards (`memory_indexer.py` & `memory_retriever.py`):** FastEmbed neural embeddings (`jinaai/jina-embeddings-v2-base-de`) partitioned into sealed historical archives and active shards.
4. **Relational Knowledge Graph (`knowledge_graph.py`):** Zero-API entity topology mapping relationships without cloud lock-in.

---

## 4. Capability Tiers (Selected during Bootstrap)

When running `bootstrap.md`, the user or agent chooses their footprint:
- **Full Sovereign Core:** All 4 memory layers + complete skill set.
- **Academic / Student Cockpit:** Curricula tracking, vector recall, fact store, and `stream-archive`.
- **Lightweight Plaintext:** Markdown SSOT + SQLite fact store (zero neural dependencies).
- **Autonomous Setup:** The agent evaluates user intent and configures the optimal tier automatically.

---

## 5. License & Philosophy

Groundsole is open source under the MIT License. It serves as an uncompromised foundation for cognitive sovereignty—proving that agentic AI requires neither vendor lock-in nor cloud dependency.
