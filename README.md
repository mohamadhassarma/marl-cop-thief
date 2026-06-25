# MARL Cop & Thief via MCP Servers

**EX06 — Dual AI Agent Race via MCP Servers**
University of Haifa | Dr. Yoram Segal | 2026

Two autonomous LLM-powered agents (Cop and Thief) play a pursuit game on a
configurable 2D grid. They communicate only through natural language via
independent MCP servers, with no hardcoded protocol between them.

---

## System Requirements

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) package manager
- Anthropic API key (or other supported LLM provider)

---

## Installation

```bash
# Clone the repo
git clone https://github.com/mohamadhassarma/marl-cop-thief.git
cd marl-cop-thief

# Install dependencies
uv sync

# Copy environment template and fill in your values
cp .env-example .env
```

Edit `.env` with your API keys and MCP server URLs.

---

## Configuration

All game parameters live in `config/config.json` — nothing is hardcoded.

Key settings:
| Parameter | Default | Description |
|---|---|---|
| `grid.size` | `[5, 5]` | Grid dimensions |
| `game.num_sub_games` | `6` | Sub-games per full game |
| `game.max_moves_per_sub_game` | `25` | Move limit per sub-game |
| `cop.max_barriers_per_sub_game` | `5` | Max barriers Cop can place |
| `llm.model` | `claude-sonnet-4-6` | LLM model |

Rate limits are in `config/rate_limits.json`.

---

## Running the Game

```bash
# Start Cop MCP server (terminal 1)
uv run python src/main.py --role cop --port 8001

# Start Thief MCP server (terminal 2)
uv run python src/main.py --role thief --port 8002

# Run the game engine (terminal 3)
uv run python src/main.py --mode game
```

### Sanity Checks (run in order)

```bash
# 2x2 grid — basic logic
uv run python src/main.py --mode game --grid 2 2

# 3x3 grid — coordination check
uv run python src/main.py --mode game --grid 3 3

# 5x5 grid — full game
uv run python src/main.py --mode game
```

---

## Running Tests

```bash
# Run all tests with coverage
uv run pytest tests/ --cov=src --cov-report=term-missing

# Lint check
uv run ruff check .
```

---

## Project Structure

```
marl-cop-thief/
├── src/
│   ├── cop_thief/
│   │   ├── sdk/sdk.py          # Single entry point for all logic
│   │   ├── services/           # Game engine, MCP servers, reporter
│   │   ├── shared/             # Config, gatekeeper, version
│   │   └── constants.py        # Enums and immutable constants
│   └── main.py                 # CLI entry point
├── tests/
│   ├── unit/                   # Unit tests mirroring src/
│   └── integration/            # End-to-end pipeline tests
├── docs/                       # PRD, PLAN, TODO, per-component PRDs
├── config/                     # config.json, rate_limits.json
├── results/                    # Experiment outputs, graphs
├── assets/                     # Screenshots, diagrams
├── notebooks/                  # Analysis notebooks
├── README.md
├── pyproject.toml
└── uv.lock
```

---

## Contributing

- Follow the guidelines in `docs/PRD.md` and `docs/PLAN.md`
- All files must stay ≤ 150 lines
- Run `uv run ruff check .` before committing
- Tests must maintain ≥ 85% coverage

---

## License

Academic project — University of Haifa, 2026.
All rights reserved. Not for redistribution.
