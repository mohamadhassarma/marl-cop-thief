# Prompt Engineering Log

**Version:** 1.00
**Project:** MARL Cop & Thief via MCP Servers
**Date:** 2026-06-25

---

## Overview

This document logs the key prompts used during AI-assisted development of this project,
including the context, goal, output quality, and lessons learned from each interaction.

---

## Prompt 1 — Project Scaffold and Documentation

**Context:** Starting the project from scratch, needed to establish the full folder
structure and mandatory documentation before writing any code.

**Prompt:**
```
I have a new AI assignment. The assignment requires two autonomous AI agents (Cop and
Thief) to play a pursuit game on a 2D grid via MCP servers communicating in natural
language. Generate the full project scaffold with all mandatory docs: PRD.md, PLAN.md,
TODO.md, and per-component PRDs for game engine, MCP server, Gmail reporter, and Q-table.
Follow the software guidelines requiring uv package manager, 150-line file limit, and
SDK architecture.
```

**Output:** Complete project scaffold with 7 documentation files, config files,
.gitignore, .env-example, and README.md.

**Quality:** High — all mandatory docs generated correctly on first attempt.

**Lesson:** Starting with documentation before code forced clear thinking about
architecture and prevented wasted implementation effort.

---

## Prompt 2 — Game Engine Design

**Context:** Needed core game logic for a 5x5 grid pursuit game with specific
win conditions and scoring rules.

**Prompt:**
```
Implement a GameEngine class for the Cop vs Thief pursuit game. Rules:
- 5x5 grid (configurable), max 25 moves per sub-game, 6 sub-games total
- Cop wins by landing on Thief's exact cell
- Thief wins by surviving all 25 moves
- Cop can place up to 5 barriers per sub-game
- Scoring: Cop capture = 20pts Cop + 5pts Thief; Thief escape = 10pts Thief + 5pts Cop
- Partial observability: each agent sees only its own position and limited info
All config from config.json, never hardcoded. Follow SDK architecture with all logic
through the SDK layer.
```

**Output:** GameEngine class with full turn management, scoring, win detection,
barrier placement, and partial observation generation.

**Quality:** High — 96% test coverage achieved. Minor fix needed for dataclass field
initialization.

**Lesson:** Detailed spec with exact scoring values and rules produced accurate
implementation on first attempt.

---

## Prompt 3 — BFS Pathfinding Strategy

**Context:** Needed intelligent agent strategies to make the game competitive.
Cop needed to catch Thief efficiently; Thief needed to evade effectively.

**Prompt:**
```
Implement a strategy module with:
1. BFS shortest path finding for the Cop (8-way King moves, respects barriers)
2. Chebyshev max-distance evasion for the Thief
3. Dead-end avoidance for the Thief (count future free neighbors before moving)
4. Barrier placement strategy for Cop (block Thief escape routes)
5. Trap detection (is_trapped function)
The goal is for the Cop to catch the Thief in as few moves as possible.
```

**Output:** strategy.py with BFS, evasion, barrier placement, trap detection,
and observation parsing utilities.

**Quality:** High — BFS catches Thief in 2-4 moves when starting close.
Evasion keeps Thief alive for 25 moves consistently.

**Lesson:** Combining algorithmic (BFS) with heuristic (max-distance) approaches
produced better results than pure LLM decision-making.

---

## Prompt 4 — FastMCP Server Implementation

**Context:** The assignment required MCP servers that receive natural language,
decide an action, and return a structured response.

**Prompt:**
```
Implement two FastMCP servers (cop_server.py and thief_server.py) that:
1. Expose a request_move(observation: dict, auth_token: str) tool
2. Accept observation in inter-group format: {role, grid, cop, thief, barriers, turn}
3. Use BFS strategy as primary decision maker (not LLM)
4. Return [INTENT: MOVE] prose with compass direction (north, south-east, etc.)
5. Handle any observation format (dict positions or list positions)
6. Include Bearer token authentication
```

**Output:** Two FastMCP servers with robust observation parsing, strategy-based
decisions, and inter-group protocol compliance.

**Quality:** Medium initially — required 3 iterations to handle different observation
formats from the other group's engine. Final version handles all formats.

**Lesson:** Inter-group integration requires defensive parsing. Always handle
multiple input formats when dealing with external systems.

---

## Prompt 5 — Inter-Group Protocol Adaptation

**Context:** The other group used a more advanced spec (8-way movement, specific
observation format, request_move tool name) that differed from the default assignment.

**Prompt:**
```
Update the system to support 8-way King movement (north, south, east, west,
north-east, north-west, south-east, south-west). Update constants.py with 8
direction enums and DIRECTION_DELTAS. Update strategy.py BFS for 8-way movement.
Update cop_server and thief_server to accept the inter-group observation format:
{role, grid: [5,5], cop: [row, col], thief: [row, col], barriers: [[r,c],...],
barriers_left, turn}
```

**Output:** Full 8-way movement system with updated constants, strategy, and servers.

**Quality:** High — BFS with 8-way movement catches Thief faster (diagonal shortcuts).
Observation format handles both dict and list position formats.

**Lesson:** 8-way movement actually strengthens the Cop — diagonal moves reduce
path length significantly on a 5x5 grid.

---

## Prompt 6 — Bonus Game Runner

**Context:** Needed a standalone script to run the inter-group bonus game,
calling both our servers and their servers.

**Prompt:**
```
Create bonus_game.py that runs 6 sub-games between our group and NajAmjad:
- Sub-games 1-3: They are Cop (their server), We are Thief (our server)
- Sub-games 4-6: We are Cop (our server), They are Thief (their server)
- Use seeded random starting positions (seed + sub_game_index)
- Build observation in their format: {role, grid:[5,5], cop:[r,c], thief:[r,c], ...}
- Save results to results/bonus_game_results.json
- Generate complete bonus report JSON matching assignment §9.2 schema
```

**Output:** Complete bonus game runner with async MCP client calls,
position parsing, and JSON report generation.

**Quality:** Required 4 iterations to fix observation format issues
(grid format, position format, variant field removal).

**Lesson:** Always test inter-group communication with actual server calls
before the official run. Format mismatches are the most common issue.

---

## Prompt 7 — Gmail OAuth Setup

**Context:** Assignment requires automated email reporting via Gmail API.

**Prompt:**
```
Set up Gmail OAuth for automated JSON report sending. The GmailReporter class
should authenticate via OAuth token stored in config/gmail_token.json, send
email to rmisegal+uoh26b@gmail.com with subject containing group name and
body containing only valid JSON (no free text).
```

**Output:** GmailReporter class with OAuth flow, token refresh, and JSON-only
email body.

**Quality:** Medium — OAuth setup required manual browser authorization flow.
Token saving and refresh worked correctly.

**Lesson:** Gmail OAuth requires one-time manual browser authorization.
After that, the token refreshes automatically.

---

## Best Practices Discovered

1. **Docs before code** — Writing PRD and PLAN first prevented architecture mistakes
2. **Strategy over LLM** — BFS pathfinding outperforms LLM decisions for deterministic games
3. **Defensive parsing** — Always handle multiple input formats for inter-group integration
4. **Test-first approach** — Writing tests before implementation caught bugs early
5. **Config externalization** — All parameters in config.json made tuning easy
6. **Iterative debugging** — Each format error fixed incrementally with targeted prompts

---

## Token Usage Estimate

| Phase | Approx. Tokens | Cost Estimate |
|---|---|---|
| Documentation generation | ~15,000 | ~$0.15 |
| Core game logic | ~20,000 | ~$0.20 |
| MCP server implementation | ~25,000 | ~$0.25 |
| Debugging and fixes | ~30,000 | ~$0.30 |
| Bonus game integration | ~20,000 | ~$0.20 |
| **Total** | **~110,000** | **~$1.10** |
