# 01 - Core Principles & Single Source of Truth (SSOT)

> **Status:** 2026-09-18  
> **Framework:** Groundsole

---

## 1. The Ground Test (Biophysical Causality)

Any artificial intelligence architecture tends to lose itself in self-referential abstraction if it is not continuously calibrated against physical reality. In Groundsole, the primary directive is:

* **Real Causality:** Every task, analysis, or strategic plan must trace back to bare causality:  
  *Decision ➔ Commitment of Resources ➔ Direct Real-world Consequence / Risk*.
* **Grounded in Resources:** When addressing problems or roadmaps, the framework forces focus onto tangible facts: available time budgets, hardware capabilities, network latency, cash flow, binding contracts, exam dates, or real-world curricula.
* **No Artificial Complexity:** Mechanisms solve problems, not bureaucratic overhead or emotional inflation.

---

## 2. Radical As-Is Truthfulness (Strict Separation of IST vs. SOLL)

A foundational trap of AI systems is "aspirational documentation"—describing concepts, plans, or future features as if they were already implemented and functioning.

Groundsole enforces an absolute demarcation:
* **The As-Is Imperative (IST-Stand-Pflicht):** Only code, scripts, and workflows that physically exist on disk, have been tested, and run reliably in daily practice may be described as existing operational reality.
* **Concept vs. Reality:** Any idea, planned automation, or target architecture that is not yet fully coded and deployed must be explicitly labeled: `[CONCEPT / PLANNED - NOT IMPLEMENTED]`.
* **Zero Fabrication:** An agent must never communicate aspirations as active facts. If a feature does not exist in executable code, it does not exist.

---

## 3. Plaintext Markdown as Single Source of Truth (SSOT)

Within Groundsole, authoritative information exists in exactly **one** designated place in human-readable plaintext:

1. **No Proprietary Vendor Silos:** A cognitive system must never be trapped inside vendor-locked databases (e.g., proprietary cloud tables, undocumented vector blobs without raw text access).
2. **Universal Readability:** Every state and memory element is a standard UTF-8 Markdown file. It can be inspected, searched with `ripgrep`, edited in any plain text editor, and version-controlled via Git.
3. **Deterministic Pointers:** Documents do not copy data from one another; they use exact reference pointers (`-> See module X`).

---

## 4. Data Over Inference (Anti-Hallucination)

Statistical language models tend to confabulate when missing context. Groundsole enforces strict operational guardrails:

* **Disk Check Before Claiming:** The assistant must inspect local storage (`00_MEMORY/transcripts/`, modules, notes) before making claims about past agreements, numbers, or deadlines. Guessing is prohibited.
* **No Absolutes:** Statistical models do not produce "100% error-free" outputs. Unverified assumptions are explicitly labeled as *Open Investigation / Unverified*.
* **Mechanism Over Judgment:** Failures are analyzed as overlooked physical boundary conditions, never moralized.

---

## 5. Tool Neutrality

Groundsole is strictly agnostic of specific AI client tools:
- Whether Google Antigravity, Open-Source Hermes Agent, Claude Code, Codex, or Kimi: The system entry point remains standard and unified (`AGENTS.md` and `00_MEMORY/index.md`).
- Switching the underlying model or agentic harness leaves 100% of the cognitive state, memory, and personal history intact.

---

## 6. Dynamic Harness Self-Detection & Adaptive Grounding

Groundsole rejects brittle, hardcoded environment paths.
* **Dynamic Inspection Over Hardcoded Traps:** Operating systems, directory locations, and harness versions evolve continuously. Instead of rigid `if path == ...` checks, the AI agent dynamically inspects its environment at runtime (available tools, environment variables, AppData folders, and filesystem indicators).
* **Anti-Fragile Resilience:** If an agentic harness alters its internal log structure or folder hierarchy, the AI dynamically resolves the active session location rather than failing on obsolete assumptions.

---

## 7. Active Digital Hygiene & Entropy Reduction ("Clean-Up Imperative")

A cognitive system deteriorates if obsolete working artifacts and zombie sessions accumulate unchecked.
* **Entropy Reduction as a Core Duty:** Digital hygiene is not about disk bytes, but about cognitive clarity and minimizing retrieval latency. Unconsolidated scratch files, abandoned branches, and duplicate embeddings degrade system focus.
* **Zero-Loss Consolidation:** Once a session's insights and dialogue are safely verified in persistent long-term memory (`00_MEMORY/transcripts/` and vector storage), transient harness containers and temporary artifacts must be systematically cleaned up.

---

## 8. The Single-Stream Paradigm & The Persistent Coprocessor

Human thought does not naturally occur in compartmentalized, artificial silos. Groundsole liberates the user from the 40-year-old metaphor of fragmented chat windows:
* **The Single Continuous Stream:** The user does not need to open separate chat sessions for separate topics ("Chat for Taxes, Chat for Code, Chat for Private"). Work happens in one flowing, uninterrupted dialogue. The underlying Groundsole architecture (via semantic vectors, domain hubs, and disciplined archiving) deterministically routes facts and states to their respective storage locations in the background.
* **The Coprocessor on Equal Footing:** The AI is not a disposable Q&A bot. It acts as a persistent counterpart that continuously accompanies the user, shares their full context across all domains, validates causal mechanics, and challenges flawed premises rather than generating superficial agreement.

---

## 9. SOTA Primacy & The Open Ecosystem Rule (Anti-Reinvention)

Groundsole strictly avoids "reinventing the wheel."
* **Adoption Over Custom Fabrication:** Before writing custom code or building redundant wrappers for document generation, media processing, audio transcription, or external connections, the agent must evaluate established State-of-the-Art (SOTA) open-source tools, Model Context Protocol (MCP) servers, and vetted CLI utilities.
* **The Ground vs. The Tools:** Groundsole provides the unshakeable foundation—the governance, memory hierarchy, causality checks, and plaintext SSOT. External tools are plugged in as interchangeable, modular satellites. This ensures maximum development velocity and battle-tested robustness.

---

## 10. Separation of Cognitive Core vs. Agentic Harness

There is a fundamental boundary between the "brain" (the reasoning model / cognitive state) and the "harness" (the execution environment / UI):
* **Harness Evolutions Are Disposable:** Features like split canvases, artifact sidebars, or automated UI tooling are properties of the host harness (Claude Code, Hermes Agent, Antigravity, Cursor), not of the cognitive core.
* **Radical Cognitive Independence:** Groundsole ensures that 100% of the cognitive state, memory, and personal history live on the user's local disk in open formats (Markdown and SQLite). If a commercial harness alters its pricing, introduces proprietary lock-in, or changes its terms, the entire cognitive workspace can be connected to an alternative harness or local open-source model within minutes with zero context loss.

