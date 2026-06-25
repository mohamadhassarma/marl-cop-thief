# PLAN — Architecture & Technical Design

**Version:** 1.00
**Date:** 2026-06-25

---

## 1. System Architecture (C4 — Container Level)

```
┌─────────────────────────────────────────────────────────┐
│                    Game Orchestrator                     │
│                   (MCP Client / Engine)                  │
│                                                         │
│  ┌─────────────┐   natural language   ┌──────────────┐ │
│  │  Game Loop  │──────────────────────│  SDK Layer   │ │
│  │  (6 games)  │                      │  (sdk.py)    │ │
│  └─────────────┘                      └──────┬───────┘ │
│                                              │          │
│                                    ┌─────────┴────────┐ │
│                                    │  API Gatekeeper  │ │
│                                    └─────────┬────────┘ │
└──────────────────────────────────────────────┼──────────┘
                                               │
                    ┌──────────────────────────┼──────────────────────────┐
                    │                          │                          │
                    ▼                          ▼                          ▼
          ┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
          │  Cop MCP Server  │      │ Thief MCP Server │      │   Gmail Service  │
          │  (FastMCP)       │      │  (FastMCP)       │      │  (OAuth Report)  │
          │  Port: 8001      │      │  Port: 8002      │      └──────────────────┘
          │                  │      │                  │
          │  Tools:          │      │  Tools:          │
          │  - move()        │      │  - move()        │
          │  - place_barrier │      │                  │
          │                  │      │                  │
          │  LLM inside:     │      │  LLM inside:     │
          │  Anthropic API   │      │  Anthropic API   │
          └──────────────────┘      └──────────────────┘
```

---

## 2. Component Design

### Game Engine (`services/game_engine.py`)
- Manages grid state, turn order, move validation
- Applies barriers, checks win conditions after each move
- Passes partial observations to each agent (not full state)
- Accumulates scores across 6 sub-games

### MCP Servers (`services/cop_server.py`, `services/thief_server.py`)
- Built with FastMCP
- Each exposes tool(s) the engine can call
- Internally calls LLM with game state as natural language prompt
- LLM response is parsed into a structured tool call

### SDK Layer (`sdk/sdk.py`)
- Single entry point for all business logic
- Wraps game engine, MCP clients, reporter
- Used by `main.py`, CLI, and tests

### API Gatekeeper (`shared/gatekeeper.py`)
- All LLM API calls route through here
- Enforces rate limits from `config/rate_limits.json`
- Handles retries and queuing

### Config Manager (`shared/config.py`)
- Loads `config/config.json` at startup
- Validates all required fields
- Single source of truth for all parameters

---

## 3. Data Flow — One Turn

```
Engine → "You are the Cop at (2,2). Thief was last seen near (4,4).
          Barriers at: [(1,1)]. It's your turn. Move or place barrier."
      ↓
Cop MCP Server receives message
      ↓
LLM processes → decides action
      ↓
Tool call returned: move(direction="right") OR place_barrier(position=(3,2))
      ↓
Engine validates + applies action
      ↓
Grid state updated → next turn
```

---

## 4. Partial Observability (Dec-POMDP)

Formal tuple: `⟨n, S, {Aᵢ}, P, R, {Ωᵢ}, O, γ⟩`

- **n = 2** agents (Cop, Thief)
- **S** = grid positions of both agents + barrier positions
- **Aᵢ** = {move_up, move_down, move_left, move_right} for Thief;
         + {place_barrier} for Cop
- **Ωᵢ** = each agent sees only its own position + limited radius info
- **γ** = 0.9 (discount factor for Q-learning if used)

---

## 5. Deployment Architecture

### Phase 1 — Local
```
localhost:8001  →  Cop MCP Server
localhost:8002  →  Thief MCP Server
```

### Phase 2 — Cloud (Prefect or equivalent)
```
https://cop-mcp-<group>.prefect.run   →  Cop MCP Server
https://thief-mcp-<group>.prefect.run →  Thief MCP Server
```
Auth: Bearer token required on all requests (revocable).

---

## 6. Key Technical Decisions (ADRs)

| Decision | Choice | Rationale |
|---|---|---|
| MCP framework | FastMCP | Simplest FastMCP integration, good Python support |
| LLM provider | Anthropic (Claude) | Already have API key, reliable tool-use |
| Agent strategy | Heuristic first, Q-table optional | Ensures working baseline fast |
| Deployment | Prefect Cloud | Free tier, easy FastMCP hosting |
| Auth | Bearer token | Simple, revocable, no password exposure |
| Report | Gmail OAuth | Required by assignment, token > password |
