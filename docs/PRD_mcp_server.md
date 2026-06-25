# PRD — MCP Agent Servers

**Version:** 1.00
**Components:** `services/cop_server.py`, `services/thief_server.py`

---

## 1. Description

Two independent FastMCP servers — one for the Cop agent, one for the Thief.
Each server receives a natural language message describing the game state,
uses an LLM to decide an action, and returns a structured tool call.
Servers have no shared state and no direct connection to each other.

## 2. Input / Output

### Input
- Natural language message from game engine describing:
  - Agent's current position
  - Last known opponent position
  - Barrier positions
  - Turn number and moves remaining
  - Available actions

### Output
- Structured tool call: `move(direction)` or `place_barrier(row, col)`
- No free text output — only tool call

### Setup Parameters (from config.json)
| Parameter | Type | Default | Description |
|---|---|---|---|
| llm.model | str | claude-sonnet-4-6 | LLM model to use |
| llm.max_tokens | int | 1000 | Max tokens per response |
| llm.provider | str | anthropic | API provider |
| cop_mcp_url | str | localhost:8001 | Cop server URL |
| thief_mcp_url | str | localhost:8002 | Thief server URL |

## 3. Tools Exposed

### Cop Server Tools
```
move(direction: str) -> str
  direction: one of "up", "down", "left", "right"

place_barrier(row: int, col: int) -> str
  row, col: target cell coordinates (0-indexed)
```

### Thief Server Tools
```
move(direction: str) -> str
  direction: one of "up", "down", "left", "right"
```

## 4. LLM Integration

- Each server calls LLM via ApiGatekeeper (rate limited)
- System prompt defines agent role, rules, and output format
- LLM must always respond with a tool call — never plain text
- If LLM returns plain text, server retries up to max_retries

## 5. Auth (Cloud Deployment)

- Bearer token required on all requests
- Token set via environment variable, never hardcoded
- Tokens are revocable independently per server

## 6. Success Criteria

- [ ] Cop server starts and responds on configured port
- [ ] Thief server starts and responds on configured port
- [ ] Both servers return valid tool calls for any valid natural language input
- [ ] Rate limiting enforced via Gatekeeper
- [ ] Retry logic handles LLM timeouts gracefully
- [ ] Bearer token auth blocks unauthorized requests
- [ ] Servers deployable independently to cloud
