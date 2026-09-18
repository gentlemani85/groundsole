# Memory Index

Last Updated: {{DATE}}

This directory represents the authoritative memory core for this workspace.
It is strictly tool-neutral: Claude, Codex, Gemini, Hermes, or any other agentic harness treat this directory as the Single Source of Truth (SSOT).

## Load Order
Adhere strictly to [LOAD_ORDER.md](LOAD_ORDER.md):
1. **Minimal Session Start:** Read only the 3 active runtime files (`index.md`, `STYLE_AND_GUARDRAILS.md`, `DYNAMIC_STATE.md`).
2. **On-Demand Domain Modules:** Modules in `modules/` are loaded exclusively when the current task touches their specific scope.
3. **Primary Historical Archives:** Past session logs in `transcripts/` serve as immutable historical evidence and are queried on-demand.

## Objective
These files prevent context fragmentation and token waste. They provide immediate calibration for the user's communication style, operational priorities, and red lines without re-reading the entire workspace history.
