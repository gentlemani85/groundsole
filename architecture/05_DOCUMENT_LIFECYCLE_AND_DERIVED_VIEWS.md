# 05 - Document Lifecycle, Quality Assurance & Derived Views

> **Status:** 2026-09-22  
> **Framework:** Groundsole  
> **Architecture Pattern:** 3-Tier Document Lifecycle & CQRS Materialized Views

---

## 1. Context & Motivation

In any organization scaling its AI integration, documentation and communication rapidly face two failure modes:
1. **The Drift of Unchecked Edits:** AI agents modify authoritative records (e.g. security audits, license matrices), but stale approvals remain displayed, rendering quality seals meaningless.
2. **Consultant Puffery & Hallucinated Metrics:** AI systems tend to invent grandiose marketing claims or extrapolate trivial adjustments into inflated annual "cost-savings" figures that damage professional credibility.
3. **Hardcoded Presentation Silos:** Summary dashboards often maintain parallel hardcoded HTML/code tables rather than rendering directly from the underlying data source, leading to conflicting truths.

To eliminate these vulnerabilities, Groundsole establishes a formal **3-Tier Document Lifecycle** and **Materialized Projection Architecture**.

---

## 2. The 3-Tier Document Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│  Tier 1: Working / Raw Artifacts (Ungelenkte Arbeitsdaten)  │
│  • Scratchpads, raw scans, transcripts, exploratory notes   │
│  • High velocity, fluid edits, 0% formal review overhead    │
└──────────────────────────────┬──────────────────────────────┘
                               │ Structured & Curated into
                               ▼
┌─────────────────────────────────────────────────────────────┐
│  Tier 2: Authoritative Master Records (Gelenkte SSOT)       │
│  • Reversible, versioned source of truth in Git             │
│  • Machine-readable YAML Front-Matter governance            │
│  • Strict Human-in-the-Loop Quality Management (QM) seal    │
└──────────────────────────────┬──────────────────────────────┘
                               │ Compiled / Projected into
                               ▼
┌─────────────────────────────────────────────────────────────┐
│  Tier 3: Derived Views (Abgeleitete / Materialisierte Sicht)│
│  • Executive dashboards, management cockpits, slide decks   │
│  • 100% deterministically generated from Tier 2             │
│  • Strictly read-only: Manual edits are strictly forbidden  │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Tier 2 Governance & The Invalidation Law

Authoritative documents (Tier 2) must include standardized YAML Front-Matter metadata at the very beginning of the plaintext file:

```yaml
---
title: System Architecture & Security Audit
tier: 2
version: 1.2
status: in_review       # draft | in_review | approved
author: Emanuel Gössler
reviewed_by: Emanuel Gössler
reviewed_at: 2026-09-22 15:00
---
```

### The Invalidation Law
* **Automatic Seal Revocation:** Whenever an AI agent or human modifies the content of a Tier 2 document, the status **must immediately revert to `in_review`** (or `draft`).
* **No Retrospective False Seals:** A document must never display an "Approved" seal if any data inside was modified after the recorded timestamp.
* **Human-in-the-Loop Sovereign:** Only an explicit verification by the designated human reviewer restores the status to `approved`.

---

## 4. Tier 3: The Materialized View Principle

Dashboards (web frontends, status monitors, executive summaries) are **projections**, not databases.
* **No Parallel Truths:** It is strictly prohibited to hardcode numbers, metrics, or tables in PHP, HTML, or JavaScript templates.
* **Passive Parsers:** All UI views must either directly parse the Tier 2 Markdown files via lightweight deterministc renderers or consume an automated compile-step (e.g. `MANAGEMENT_COCKPIT.md`).
* If a metric changes in Tier 2, the Tier 3 dashboard updates automatically on the next page load.

---

## 5. The Anti-Puffery Rule (Grounded Metrics)

Groundsole strictly bans inflated consultant jargon:
* **No Artificial Extrapolations:** Never calculate fictitious annual savings (e.g. *"Saves €468/year!"*) from minor operational housekeeping tasks.
* **Bare Technical Facts:** Metrics must be stated soberly and verifiably (e.g. *"7 unused accounts consolidated into shared mailboxes"*).
* **Respect Real Business Context:** For an enterprise, trivial recurring software costs are operational background noise; framing them as strategic triumphs demonstrates cognitive detachment.
