# PRD — Game Engine

**Version:** 1.00
**Component:** `services/game_engine.py`

---

## 1. Description

The Game Engine manages all game state: grid, agent positions, barriers,
turn order, win condition checking, and score accumulation across sub-games.
It is the single source of truth for game state.

## 2. Input / Output

### Input
- `config`: loaded ConfigManager instance
- Per-turn: agent action (move direction or barrier position) as structured data

### Output
- Per-turn: updated grid state, partial observation for each agent
- Per-sub-game: winner, scores awarded
- Per-game: full score totals for Cop and Thief

### Setup Parameters (from config.json)
| Parameter | Type | Default | Description |
|---|---|---|---|
| grid.size | [int, int] | [5, 5] | Grid dimensions |
| game.num_sub_games | int | 6 | Sub-games per full game |
| game.max_moves_per_sub_game | int | 25 | Move limit per sub-game |
| cop.max_barriers_per_sub_game | int | 5 | Max barriers Cop can place |

## 3. Game Rules

- Cop and Thief start at positions set by engine (random or configured)
- Turns alternate: Thief moves first, then Cop
- Each turn: agent chooses move (N/S/E/W) or Cop places barrier
- Barriers block movement; placed cell becomes impassable for Thief
- Barrier counts as Cop's action for that turn (no move)
- Cop wins sub-game: lands on exact Thief cell (capture)
- Thief wins sub-game: survives all 25 moves
- Agents cannot move outside grid bounds

## 4. Scoring

| Event | Cop Points | Thief Points |
|---|---|---|
| Cop captures Thief | +20 | +5 |
| Thief escapes (25 moves) | +5 | +10 |

## 5. Partial Observation

Each agent receives only:
- Its own current position
- Last known position of opponent (updated only when in same row/column)
- Positions of all barriers

## 6. Win/Loss Conditions

- Sub-game ends immediately when Cop lands on Thief's cell
- Sub-game ends after move 25 if no capture
- Full game ends after all 6 sub-games regardless of scores

## 7. Success Criteria

- [ ] Engine correctly applies all movement rules
- [ ] Barrier placement blocked correctly
- [ ] Win detection triggers on exact position match
- [ ] Scores accumulate correctly across 6 sub-games
- [ ] Partial observation hides correct information from each agent
- [ ] All edge cases documented and tested (grid boundary, barrier on occupied cell)
