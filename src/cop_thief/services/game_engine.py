"""Game Engine — manages turns, scoring, and win conditions."""

import random
from dataclasses import dataclass, field
from cop_thief.services.grid import Grid, Position
from cop_thief.constants import Direction, Role, SubGameResult, ActionType
from cop_thief.shared.config import ConfigManager


@dataclass
class Action:
    """An action taken by an agent during their turn."""

    agent: Role
    action_type: ActionType
    direction: Direction | None = None
    barrier_pos: Position | None = None


@dataclass
class SubGameState:
    """Snapshot of a completed sub-game."""

    sub_game_index: int
    result: SubGameResult
    moves_taken: int
    cop_score: int
    thief_score: int
    cop_start: Position
    thief_start: Position


@dataclass
class GameState:
    """Full game state across all sub-games."""

    sub_games: list[SubGameState] = field(default_factory=list)
    total_cop_score: int = 0
    total_thief_score: int = 0


class GameEngine:
    """Manages the full game: grid, turns, scoring, and win detection.

    Runs num_sub_games sequential sub-games, accumulating scores.
    Each sub-game resets positions and barriers but keeps score totals.
    """

    def __init__(self, config: ConfigManager) -> None:
        """Initialize engine from config.

        Args:
            config: Loaded ConfigManager instance.
        """
        rows, cols = config.grid_size
        self.grid = Grid(rows, cols)
        self.config = config
        self.scoring = config.scoring
        self.max_moves = config.max_moves
        self.max_barriers = config.max_barriers
        self.num_sub_games = config.num_sub_games
        self.game_state = GameState()
        self._cop_pos: Position = Position(0, 0)
        self._thief_pos: Position = Position(0, 0)
        self._move_count: int = 0
        self._barrier_count: int = 0

    def _random_start_positions(self) -> tuple[Position, Position]:
        """Generate non-overlapping random start positions."""
        rows, cols = self.config.grid_size
        all_cells = [Position(r, c) for r in range(rows) for c in range(cols)]
        cop_pos = random.choice(all_cells)
        remaining = [p for p in all_cells if p != cop_pos]
        thief_pos = random.choice(remaining)
        return cop_pos, thief_pos

    def reset_sub_game(self) -> None:
        """Reset grid and positions for a new sub-game."""
        self.grid.reset_barriers()
        self._cop_pos, self._thief_pos = self._random_start_positions()
        self._move_count = 0
        self._barrier_count = 0

    def get_cop_observation(self) -> dict:
        """Return partial observation for the Cop agent."""
        return {
            "role": "cop",
            "my_position": {"row": self._cop_pos.row, "col": self._cop_pos.col},
            "opponent_position": {"row": self._thief_pos.row, "col": self._thief_pos.col},
            "barriers": [{"row": b.row, "col": b.col} for b in self.grid.get_barriers()],
            "moves_taken": self._move_count,
            "moves_remaining": self.max_moves - self._move_count,
            "barriers_placed": self._barrier_count,
            "barriers_remaining": self.max_barriers - self._barrier_count,
            "grid_size": list(self.config.grid_size),
        }

    def get_thief_observation(self) -> dict:
        """Return partial observation for the Thief agent."""
        return {
            "role": "thief",
            "my_position": {"row": self._thief_pos.row, "col": self._thief_pos.col},
            "cop_last_known": {"row": self._cop_pos.row, "col": self._cop_pos.col},
            "barriers": [{"row": b.row, "col": b.col} for b in self.grid.get_barriers()],
            "moves_taken": self._move_count,
            "moves_remaining": self.max_moves - self._move_count,
            "grid_size": list(self.config.grid_size),
        }

    def apply_action(self, action: Action) -> None:
        """Apply a validated agent action to the game state.

        Args:
            action: The action to apply.

        Raises:
            ValueError: If action is invalid (e.g. too many barriers).
        """
        if action.action_type == ActionType.MOVE:
            if action.direction is None:
                raise ValueError("Move action requires a direction")
            if action.agent == Role.COP:
                self._cop_pos = self.grid.apply_move(self._cop_pos, action.direction)
            else:
                self._thief_pos = self.grid.apply_move(self._thief_pos, action.direction)

        elif action.action_type == ActionType.PLACE_BARRIER:
            if action.agent != Role.COP:
                raise ValueError("Only Cop can place barriers")
            if self._barrier_count >= self.max_barriers:
                raise ValueError("Max barriers reached")
            if action.barrier_pos is None:
                raise ValueError("Barrier action requires a position")
            self.grid.add_barrier(action.barrier_pos)
            self._barrier_count += 1

        self._move_count += 1

    def check_sub_game_over(self) -> SubGameResult | None:
        """Check if the current sub-game has ended.

        Returns:
            SubGameResult if game is over, None if still ongoing.
        """
        if self._cop_pos == self._thief_pos:
            return SubGameResult.COP_WIN
        if self._move_count >= self.max_moves:
            return SubGameResult.THIEF_WIN
        return None

    def score_sub_game(self, result: SubGameResult) -> tuple[int, int]:
        """Return (cop_score, thief_score) for a sub-game result."""
        if result == SubGameResult.COP_WIN:
            return self.scoring["cop_win"], self.scoring["thief_loss"]
        return self.scoring["cop_loss"], self.scoring["thief_win"]

    def record_sub_game(
        self, index: int, result: SubGameResult,
        cop_start: Position, thief_start: Position
    ) -> SubGameState:
        """Record a completed sub-game and update totals.

        Args:
            index: Sub-game index (0-based).
            result: Outcome of the sub-game.
            cop_start: Cop's starting position.
            thief_start: Thief's starting position.

        Returns:
            The completed SubGameState.
        """
        cop_score, thief_score = self.score_sub_game(result)
        self.game_state.total_cop_score += cop_score
        self.game_state.total_thief_score += thief_score
        state = SubGameState(
            sub_game_index=index,
            result=result,
            moves_taken=self._move_count,
            cop_score=cop_score,
            thief_score=thief_score,
            cop_start=cop_start,
            thief_start=thief_start,
        )
        self.game_state.sub_games.append(state)
        return state

    def render(self) -> str:
        """Return current grid as ASCII string."""
        return self.grid.render(self._cop_pos, self._thief_pos)
