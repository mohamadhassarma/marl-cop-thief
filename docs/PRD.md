# PRD — MARL Cop & Thief via MCP Servers

**Version:** 1.00
**Date:** 2026-06-25
**Author:** Mohamad Hassarma

---

## 1. Project Overview

### Problem Statement
Design and implement a multi-agent reinforcement learning (MARL) system where two
autonomous AI agents — a Cop and a Thief — play a pursuit game on a 2D grid.
Agents communicate exclusively via natural language through MCP (Model Context Protocol)
servers, with no hardcoded protocol between them.

### Target Audience
- Course staff (Dr. Yoram Segal, University of Haifa)
- Peer reviewers (inter-group bonus competition)

### Vision
Demonstrate that two independent LLM-powered agents can coordinate a structured
game using only free natural language, deployed as autonomous MCP microservices.

---

## 2. Goals & Success Metrics

### Goals
- Implement a fully autonomous Cop vs. Thief pursuit game over 6 sub-games
- Each agent runs as an independent MCP server powered by an LLM
- Game engine orchestrates both agents without hardcoded move protocols
- Automated JSON report emailed after every full game

### KPIs
| Metric | Target |
|---|---|
| Sub-games per full game | 6 |
| Max moves per sub-game | 25 |
| Test coverage | ≥ 85% |
| Ruff lint errors | 0 |
| File size | ≤ 150 lines each |

### Acceptance Criteria
- [ ] Both MCP servers start independently and respond to natural language
- [ ] Game engine runs all 6 sub-games without manual intervention
- [ ] Correct scoring applied after each sub-game
- [ ] JSON report emailed automatically to rmisegal+uoh26b@gmail.com
- [ ] Cloud deployment with token-based auth working
- [ ] Bonus: inter-group game completes with matching JSON from both groups

---

## 3. Functional Requirements

### User Stories
- As the game engine, I can send a natural language message to the Cop MCP server
  and receive a valid move or barrier placement as a tool call response.
- As the game engine, I can send a natural language message to the Thief MCP server
  and receive a valid move as a tool call response.
- As an observer, I can see the grid state after every move via the GUI/CLI.
- As course staff, I receive a JSON-only email report after the game completes.

### Features
- 2D grid game engine (configurable size, default 5×5)
- Cop agent: can move (4 directions) or place a barrier each turn
- Thief agent: can move (4 directions) each turn
- Partial observability: each agent receives only its own position + limited info
- 6 sub-games played sequentially, scores accumulated
- Automated Gmail report via OAuth token

### Non-Functional Requirements
- All config values loaded from `config/config.json` — nothing hardcoded
- All LLM calls go through the centralized API Gatekeeper
- Agents must be independently deployable (no shared process)
- Response latency per turn: < 10 seconds
- System must handle LLM timeouts gracefully with retry logic

---

## 4. Assumptions & Constraints

### Assumptions
- LLM (Anthropic Claude) reliably returns a tool call on every turn given correct prompting
- Both MCP servers are reachable at configured URLs during a game
- Gmail OAuth token is pre-generated before game runs

### Constraints
- Files ≤ 150 lines (excluding comments/blanks)
- Package manager: `uv` only
- Python ≥ 3.10
- No secrets committed to git

### Out of Scope
- Web-based multiplayer UI
- Training deep neural networks
- Supporting game grids larger than 10×10

---

## 5. Timeline & Milestones

| Phase | Milestone | Status |
|---|---|---|
| 1 | Scaffold + docs complete | ✅ Done |
| 2 | Game engine + grid logic | 🔲 TODO |
| 3 | MCP servers (local, 2×2 sanity) | 🔲 TODO |
| 4 | Full pipeline local (5×5) | 🔲 TODO |
| 5 | Cloud deployment + auth | 🔲 TODO |
| 6 | Gmail reporting | 🔲 TODO |
| 7 | Bonus inter-group game | 🔲 TODO |
