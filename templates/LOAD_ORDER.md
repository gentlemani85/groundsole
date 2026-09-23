# Load Order

## Minimal Session Start
Any AI agent operating within this workspace reads **only these 3 files** by default:
1. `00_MEMORY/index.md`
2. `00_MEMORY/STYLE_AND_GUARDRAILS.md`
3. `00_MEMORY/DYNAMIC_STATE.md`

## On-Demand Domain Modules (Load ONLY when explicitly required)
- `00_MEMORY/modules/OPERATIONS_AND_PROJECTS.md`
- `00_MEMORY/modules/RESOURCES_AND_FINANCE.md`
- `00_MEMORY/modules/INFRASTRUCTURE_AND_ASSETS.md`
- `00_MEMORY/modules/LEARNING_AND_SKILLS.md`
- Session logs in `00_MEMORY/transcripts/`

## ⚡ Context Strategy & Token Hygiene (Vectors First)
When answering questions regarding past topics, historical patterns, or specifications:
1. **Always query the primary vector database first** (`python3 tools/scripts/memory_retriever.py --query "<term>"`). Local CPU-based vector search consumes 0 context tokens and returns pinpointed verbatim chunks.
2. **Never scan raw markdown transcripts on suspicion.** Raw full-text transcripts must only be loaded if a vector hit explicitly identifies the exact line range needed for further context.

---

## 🧠 Autonomous Fact & Decision Memory Protocol
At the conclusion of every turn, regardless of harness (Hermes, Antigravity, Claude, Codex), silently evaluate if a permanent fact, binding decision, deadline, milestone, or status shift occurred.

### 🚨 Emotion as Smoke Detector & Turn Checklist:
- **Emotion as Milestone Sensor:** Strong user emotions (pride, relief, frustration, excitement) are smoke detectors signaling real-world breakthroughs or critical friction. Reflexively identify the underlying technical/status cause and persist it!
- **Input Chunking Check:** If a user prompt contains a retrospective/milestone followed by a new task, never allow the first part to be lost in the execution of the second. Extract and persist facts first!
- **Turn-End Checklist:** Before rendering the final response, silently verify:
  1. Did a milestone, decision, or state shift occur?
  2. Is it persisted in memory?
  If yes, execute `python3 scripts/memory.py add "<Namespace>" "<Key>" "<Content>"`.

### Categories:
- **Decisions & Status Shifts:** Choices, milestones, direction changes -> Namespace: `Decisions` or `<ProjectID>`
- **Entity Facts & Dates:** External commitments, client facts -> Namespace: `<ProjectID>` or `<Contact>`
- **Infrastructure & Assets:** System parameters, paths, credentials -> Namespace: `Infrastructure`
- **Universal Catch-All:** Any fact whose absence in future chats would cause friction or repeated questions.
