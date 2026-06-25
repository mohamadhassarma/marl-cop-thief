# TODO — Task Tracking

**Version:** 1.00
**Date:** 2026-06-25

---

## Phase 1 — Scaffold & Docs ✅

- [x] Create project structure with uv
- [x] Write PRD.md
- [x] Write PLAN.md
- [x] Write TODO.md
- [x] Write PRD_game_engine.md
- [x] Write PRD_mcp_server.md
- [x] Write PRD_gmail_report.md
- [x] Write PRD_q_table.md
- [x] Create config/config.json
- [x] Create config/rate_limits.json
- [x] Create .env-example
- [x] Setup pyproject.toml with uv

---

## Phase 2 — Core Game Logic 🔲

- [ ] `shared/version.py` — version constant 1.00
- [ ] `shared/config.py` — ConfigManager class (loads config.json)
- [ ] `constants.py` — Direction enums, game constants
- [ ] `services/grid.py` — Grid class (positions, barriers, bounds)
- [ ] `services/game_engine.py` — GameEngine class (turns, scoring, win check)
- [ ] Tests for grid + engine (≥ 85% coverage)
- [ ] Sanity check: 2×2 grid runs without crashing

---

## Phase 3 — MCP Servers (Local) 🔲

- [ ] `shared/gatekeeper.py` — ApiGatekeeper class
- [ ] `services/cop_server.py` — Cop FastMCP server with move + barrier tools
- [ ] `services/thief_server.py` — Thief FastMCP server with move tool
- [ ] System prompts for each agent (prompt engineering log started)
- [ ] `sdk/sdk.py` — SDK class wrapping engine + MCP clients
- [ ] `main.py` — CLI entry point via SDK
- [ ] Local test: 2×2 sanity (both servers on localhost)
- [ ] Local test: 3×3 coordination check
- [ ] Local test: 4×4 partial observability check
- [ ] Local test: 5×5 full game (6 sub-games)

---

## Phase 4 — GUI & Visualization 🔲

- [ ] `services/visualizer.py` — ASCII or simple GUI grid display
- [ ] Score tracking display after each sub-game
- [ ] Sensitivity analysis: vary grid size, max_moves
- [ ] Generate graphs: score vs episodes, win rates
- [ ] Screenshots for README and docs

---

## Phase 5 — Gmail Reporting 🔲

- [ ] `services/reporter.py` — GmailReporter class
- [ ] OAuth setup (credentials.json + token flow)
- [ ] JSON-only email body (no free text)
- [ ] Test: send internal game report after 6 sub-games
- [ ] Validate JSON schema matches assignment spec

---

## Phase 6 — Cloud Deployment 🔲

- [ ] Deploy Cop MCP server to cloud (Prefect/ngrok)
- [ ] Deploy Thief MCP server to cloud
- [ ] Add Bearer token auth to both servers
- [ ] Update config with public URLs
- [ ] Test full pipeline end-to-end over cloud
- [ ] Add token revocation mechanism

---

## Phase 7 — Bonus Inter-Group Game 🔲

- [ ] Coordinate with partner group — share MCP URLs
- [ ] Agree on JSON schema for inter-group report
- [ ] Run 3 sub-games: our Cop vs their Thief
- [ ] Run 3 sub-games: their Cop vs our Thief
- [ ] Send inter-group JSON report email
- [ ] Verify both groups sent identical results
- [ ] Confirm mutual_agreement: true in both reports

---

## Phase 8 — Final Polish 🔲

- [ ] README.md complete (install, usage, examples, config)
- [ ] Prompt engineering log complete (docs/PROMPTS.md)
- [ ] Ruff: zero errors (`uv run ruff check .`)
- [ ] Coverage: ≥ 85% (`uv run pytest --cov`)
- [ ] All files ≤ 150 lines
- [ ] .gitignore covers .env, gmail_token.json, __pycache__
- [ ] uv.lock committed
- [ ] Final git tag: v1.00
