# 07 - Team Federation, Shared Hubs & Brownfield Ingestion

> **Status:** 2026-10-12  
> **Framework:** Groundsole  
> **Pattern:** Two-Tier Hub-and-Spoke Federation & Retroactive Workspace Ingestion

---

## 1. The Dilemma of Organizational AI Rollouts

When companies, public authorities, and small teams deploy agentic AI harnesses (such as Hermes Agent, Antigravity, or Claude Code), they typically fall into one of two systemic traps:

1. **The Shared-Workspace Trap (Monolithic Chaos):**  
   Forcing the entire team into a single shared AI conversation environment destroys psychological safety. Team members hesitate to explore raw ideas, draft messy arguments, or expose iterative queries when colleagues and managers share the same chat log. Furthermore, context windows overflow with conflicting requests from across the organization.
2. **The Naked Isolation Trap (Fragmented Silos):**  
   Giving each team member a "naked" personal installation without a shared architectural memory leads to immediate knowledge fragmentation. Every employee must independently explain the company’s infrastructure, corporate tone, legal boundaries, and project facts to their agent from scratch. When key insights or system fixes occur, they remain locked in one person's ephemeral chat history.

Groundsole resolves this tension through **Two-Tier Hub-and-Spoke Federation**, cleanly decoupling private thought spaces from collective organizational truths.

---

## 2. The Two-Tier Architecture: Home Port + Shared Hub

```text
┌────────────────────────────────────────────────────────────────────────┐
│ THE SHARED TEAM HUB (SharePoint / Nextcloud / Shared Drive: TEAM_HUB/) │
│ Synchronized across all team members & workstations.                   │
│                                                                        │
│ ├── AGENTS.md                 <-- Organization-wide tone & guardrails  │
│ ├── TEAM_FEED.md              <-- Real-time team news, updates & tips  │
│ ├── dossiers/                 <-- Curated SSOT Knowledge Dossiers      │
│ │   ├── 01_ORGANIZATION_PROFILE.md   (Business model & services)       │
│ │   ├── 02_INFRASTRUCTURE_AND_TOOLS.md (Network, servers, software)    │
│ │   └── 03_SECURITY_AND_COMPLIANCE.md  (GDPR, CDPA, keys in vault)     │
│ └── templates/                <-- Shared templates (memos, protocols)  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                  Referenced by root AGENTS.md at startup
                                    │
         ┌──────────────────────────┴──────────────────────────┐
         ▼                                                     ▼
┌─────────────────────────────────┐   ┌─────────────────────────────────┐
│ PERSONAL HOME PORT (Member A)   │   │ PERSONAL HOME PORT (Member B)   │
│ Workstation / Personal Drive    │   │ Workstation / Personal Drive    │
│                                 │   │                                 │
│ ├── AGENTS.md (Minimal Triad)   │   │ ├── AGENTS.md (Minimal Triad)   │
│ │   • Points to TEAM_HUB/       │   │ │   • Points to TEAM_HUB/       │
│ ├── 00_MEMORY/                  │   │ ├── 00_MEMORY/                  │
│ │   ├── transcripts/ (Private)  │   │ │   ├── transcripts/ (Private)  │
│ │   └── DYNAMIC_STATE.md        │   │ │   └── DYNAMIC_STATE.md        │
│ └── scripts/ (Local Engines)    │   │ └── scripts/ (Local Engines)    │
└─────────────────────────────────┘   └─────────────────────────────────┘
```

### Tier 1: The Personal Home Port (Der Persönliche Heimathafen)
- **Zero Exposure:** The daily launch workspace for the harness (e.g. `ISN-AI/` in personal OneDrive or local SSD).
- **Private Working Memory:** Raw session transcripts (`00_MEMORY/transcripts/`), scratchpads, and personal todo lists remain 100% private to the user.
- **Root Entry Point:** The local `AGENTS.md` implements the Minimal Core Triad and defines an immutable pointer to the shared team hub.

### Tier 2: The Shared Team Hub (Der Geteilte Team-Hub)
- **Centralized Single Source of Truth (SSOT):** Hosted on an existing corporate cloud mount (Microsoft SharePoint, Nextcloud, Google Workspace).
- **Read-on-Start:** When any member's agent initializes, it reads the team hub's `AGENTS.md`, checks `TEAM_FEED.md` for recent company-wide developments, and indexes the curated `dossiers/`.
- **Zero Duplication:** General infrastructure documentation, security policies, and service portfolios exist in exactly one authoritative location.

---

## 3. Two-Way Knowledge Routing & Selective Crystallization

When a team member finishes a working session, information is partitioned deterministically:

1. **Default Local Archiving:**  
   The entire verbatim transcript is exported locally to `00_MEMORY/transcripts/` via `export_hermes_session.py` or `export_antigravity_session.py`. It is vectorized locally into the user's active database.
2. **Selective Upstream Crystallization:**  
   If an interaction generated a binding organizational decision, a new standard procedure, or a system bugfix, the user or agent explicitly promotes the insight to the Shared Hub:
   > *"Kristallisiere diese Entscheidung in das Infrastruktur-Dossier am SharePoint."*
   The coprocessor uses `replace_file_content` to surgically patch the target markdown dossier in `TEAM_HUB/dossiers/` and logs a concise entry in `TEAM_FEED.md`.

---

## 4. The Brownfield Ingestion Pattern (Nachträgliche Einführung)

In enterprise reality, teams rarely start on a clean slate ("greenfield"). Team members often operate their harness (e.g. Hermes Agent) for **weeks or months nakedly** before Groundsole is introduced.

A rigid framework that demands an empty directory or discards pre-existing history will face severe user resistance. Groundsole solves this via the **Brownfield Ingestion Protocol**:

```text
┌─────────────────────────────────────────────────────────────┐
│ 1. Non-Destructive Docking (init_instance.py)               │
│ • Targets an already populated directory without data loss  │
│ • Existing notes & drafts are preserved untouched           │
│ • Groundsole core (00_MEMORY/, scripts/, AGENTS.md) is docked│
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Zero-Token Historical Harvest (export_*_session --all)   │
│ • Inspects harness database (e.g. ~/.hermes/state.db)       │
│ • Detects all unarchived historical sessions                │
│ • Generates verbatim 1:1 Markdown transcripts in seconds    │
│ • Zero LLM token consumption, zero lossy summarization      │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Retroactive Memory Consolidation                         │
│ • FastEmbed ONNX batches embeddings across all transcripts  │
│ • Post-archival crystallizer extracts durable breakthroughs │
│ • The agent immediately inherits full historical context    │
└─────────────────────────────────────────────────────────────┘
```

### Operational Guarantees for Brownfield Workstations:
1. **Historical Parity:** All past conversations are preserved word-for-word in standard Markdown format (`YYYY-MM-DD - [Title].md`).
2. **Immediate Cognitive Recall:** A newly docked Groundsole coprocessor can immediately answer questions about tasks and decisions from three weeks prior via `memory_retriever.py`.
3. **Zero Configuration Friction:** Scaffolding with `--profile team_spoke --hub-path "<path>" --retro-sync-hermes` completes the entire migration autonomously in under 30 seconds.
