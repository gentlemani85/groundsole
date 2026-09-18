---
name: system-hygiene
description: "Workspace entropy reduction, cache sanitization, orphaned directory audits, and SSOT pointer verification."
version: 1.0.0
author: Emanuel Gössler
tags: [groundsole, hygiene, maintenance, entropy, cleanup, integrity]
---

# System Hygiene Skill

This skill performs periodic workspace audits to eliminate technical entropy, prevent cache pollution, and verify link integrity across all Markdown documents and skills.

---

## Trigger Conditions

Activate this skill when:
- The user requests: *"Run system hygiene"*, *"Clean up workspace"*, *"Check for dead links or duplicate files"*, or *"Run audit"*.
- After major architectural refactoring or bulk document migrations.

---

## 📋 Audit & Cleanup Protocol

When triggered, execute the following audit routine deterministically:

### 1. Ephemeral OS & Cache Cleanup
- Identify and remove `.DS_Store`, `Thumbs.db`, and temporary editor swap files (`*.swp`, `*~`).
- Clean ephemeral Python caches (`__pycache__/`, `*.pyc`).

### 2. Single Source of Truth (SSOT) & Link Integrity
- Inspect relative links and Markdown cross-pointers in `00_MEMORY/index.md`, `00_MEMORY/LOAD_ORDER.md`, and active domain modules.
- Ensure every referenced file actually exists on disk.
- Detect accidental data duplication across multiple modules.

### 3. Orphaned Directory Detection
- Scan for abandoned or shadowed configuration directories (e.g. nested duplicate skill folders).
- Verify that skills adhere to the single authoritative location.

### 4. Status Summary
Output a concise status report:
- 🟢 Cleaned files & reclaimed storage
- 🟢 Link integrity & SSOT pointer verification
- 🟢 Active registered skills
- 🟡 Identified open anomalies or unlinked files (if any)
