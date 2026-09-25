# 03 - Rollout & Instance Architecture

> **Status:** 2026-09-18  
> **Framework:** Groundsole

---

## 1. Hub & Spoke Without Cloud Lock-in

A personal AI coprocessor must be strictly private and tailored to the individual. At the same time, improvements to foundational architecture, new skills, or updated guardrails should not require tedious manual copying across machines.

Groundsole resolves this via a decoupled Hub-and-Spoke model:

* **The Hub (Groundsole Core on GitHub):**  
  Contains exclusively neutral blueprints, standard tooling (`tools/`), verified skills (`skills/teach/`), and architecture documentation. **Zero private data, zero raw transcripts, zero credentials.**
* **The Spoke Instance (e.g., Student Cockpit, Company Team Workstation):**  
  An autonomous local workspace on the user's machine. It inherits the core structural blueprints while holding its own private notes, modules, and transcripts.

---

## 2. Instance Lifecycle

```text
┌─────────────────────────────────┐
│ Groundsole Core (GitHub)        │
│ (Templates, Skills, Tooling)    │
└────────────────┬────────────────┘
                 │
                 │ 1. init_instance.py (One-time Scaffolding)
                 ▼
┌─────────────────────────────────┐
│ New Instance (e.g. Student Cockpit)   │
│ • AGENTS.md & 00_MEMORY/        │
│ • skills/teach                  │
│ • version.json (v0.1.0)         │
└────────────────┬────────────────┘
                 │
                 │ 2. check_update.py (Ongoing Verification)
                 ▼
     Query against upstream GitHub:
     "💡 Core update available: Groundsole v0.2.0.
      Apply update? [Yes/No]"
```

---

## 3. The Ironclad Data Protection Rule

When updating an instance, the **Rule of Local Sovereignty** applies:
1. **Allowed:** Updating universal skills (e.g., `skills/teach/SKILL.md`) and core utility scripts.
2. **Strictly Forbidden:** Overwriting `00_MEMORY/transcripts/`, customized domain modules, or user-maintained `DYNAMIC_STATE.md` files.
