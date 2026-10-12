# 06 - Cross-Harness Entry Architecture & The Triad

> **Status:** 2026-10-04  
> **Framework:** Groundsole  
> **Pattern:** Tool-Neutral Session Initialization & The Minimal Core Triad

---

## 1. Context & Motivation

Agentic AI tools and harnesses evolve rapidly. Proprietary interfaces (Google Antigravity, Claude Code, OpenAI Codex) and open-source autonomous agent runners (Hermes Agent, OpenWebUI) introduce differing configuration conventions:
- Some inject global machine-wide instructions (`~/.gemini/config/AGENTS.md`).
- Some look for root-level identity files (`SOUL.md`).
- Others rely on repository-level entry pointers (`AGENTS.md`).

When systems attempt to maintain separate, siloed configurations across each tool, they inevitably suffer from **synchronization drift, fragmented truths, and ballooning startup latency**.

Groundsole establishes a strictly tool-neutral, unified entry point that decouples the cognitive core from the host harness.

---

## 2. The Unified Entry Invariant: `AGENTS.md` as the Root Anchor

Every Groundsole-compliant workspace defines exactly **one** primary entry anchor at its filesystem root:
`./AGENTS.md`

### Harness-Specific Bridging Rules:
1. **Host-Agnostic Runners (e.g. Hermes Agent):**
   Host-specific identity files (such as `SOUL.md`) must intentionally remain empty or act solely as a minimal symlink/pointer back to the workspace root (`./AGENTS.md`). No operational logic or personal context may reside inside harness-specific state directories.
2. **Platform-Level Dispatchers (e.g. Antigravity Global Rule):**
   Global machine configurations (`~/.gemini/config/AGENTS.md`) serve exclusively as **dispatchers and physical guardrails** (e.g. checking paths, protecting cloud-synced folders, enforcing the central virtual environment). They do not store cognitive memories. Once the workspace path is confirmed, the dispatcher delegates 100% of the cognitive execution to the local workspace root.

---

## 3. The Minimal Core Triad (Token-Optimized Session Start)

Earlier multi-step initialization cascades (loading index files, load orders, relation maps, and legacy states sequentially) wasted thousands of tokens before addressing user requests.

Under Groundsole's streamlined architecture, session initialization across **all harnesses** is reduced to the **Minimal Core Triad** (exactly three plaintext Markdown files):

```text
┌─────────────────────────────────────────────────────────────┐
│ 1. Root Entry Anchor (AGENTS.md)                            │
│ • Canonical entry pointer for any agentic harness            │
│ • Declares workspace boundaries and source hierarchy         │
└──────────────────────────────┬──────────────────────────────┘
                               │ Directly references
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Interaction & Causality Core (STYLE_AND_GUARDRAILS.md)   │
│ • Peer-coprocessor interaction guidelines (no preachiness)  │
│ • Biophysical causality test & evidence imperatives          │
│ • Grounded communication standards                           │
└──────────────────────────────┬──────────────────────────────┘
                               │ Directly references
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Living Operational State (DYNAMIC_STATE.md)              │
│ • Real-time project trajectory & active focal initiatives   │
│ • Recent milestone completions & open commitments           │
│ • Hardware, network, and environment parameters              │
└─────────────────────────────────────────────────────────────┘
```

### Key Architectural Benefits:
* **Zero Cascade Latency:** An agent reads only what is immediately necessary to calibrate tone, boundaries, and current trajectory.
* **Radical Context Preservation:** Over 80% of startup token overhead is eliminated, leaving maximal attention window capacity for deep reasoning.
* **On-Demand Deep Dives:** All historical archives, domain modules, and secondary indices remain on disk, queried exclusively via semantic vector retrieval or precise file links when explicitly needed.
