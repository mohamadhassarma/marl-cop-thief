"""Unit tests for GameEngine."""

import json
import pytest
from pathlib import Path
from cop_thief.services.game_engine import GameEngine, Action
from cop_thief.services.grid import Position
from cop_thief.constants import Direction, Role, SubGameResult, ActionType
from cop_thief.shared.config import ConfigManager


@pytest.fixture
def config(tmp_path) -> ConfigManager:
    """Create a minimal config for testing."""
    data = {
        "version": "1.00",
        "grid": {"size": [5, 5]},
        "game": {"num_sub_games": 6, "max_moves_per_sub_game": 25},
        "cop": {"max_barriers_per_sub_game": 5},
        "scoring": {
            "cop_win": 20, "thief_win": 10,
            "cop_loss": 5, "thief_loss": 5
        },
        "reporting": {
            "target_email": "test@test.com",
            "group_name": "Test",
            "timezone": "Asia/Jerusalem"
        },
        "llm": {"model": "claude-sonnet-4-6", "max_tokens": 1000}
    }
    f = tmp_path / "config.json"
    f.write_text(json.dumps(data))
    return ConfigManager(str(f))


@pytest.fixture
def engine(config) -> GameEngine:
    """Create a fresh GameEngine."""
    return GameEngine(config)


class TestGameEngineInit:
    """Tests for engine initialization."""

    def test_initializes(self, engine):
        """Engine initializes without error."""
        assert engine is not None

    def test_game_state_empty(self, engine):
        """Game state starts with no sub-games."""
        assert len(engine.game_state.sub_games) == 0
        assert engine.game_state.total_cop_score == 0
        assert engine.game_state.total_thief_score == 0


class TestResetSubGame:
    """Tests for sub-game reset."""

    def test_reset_clears_barriers(self, engine):
        """Reset removes all barriers."""
        engine.reset_sub_game()
        engine.grid.add_barrier(Position(1, 1))
        engine.reset_sub_game()
        assert engine.grid.barrier_count() == 0

    def test_reset_sets_positions(self, engine):
        """Reset assigns valid start positions."""
        engine.reset_sub_game()
        assert engine.grid.is_valid(engine._cop_pos)
        assert engine.grid.is_valid(engine._thief_pos)

    def test_reset_positions_differ(self, engine):
        """Cop and Thief start on different cells."""
        engine.reset_sub_game()
        assert engine._cop_pos != engine._thief_pos

    def test_reset_move_count(self, engine):
        """Reset sets move count to zero."""
        engine.reset_sub_game()
        assert engine._move_count == 0


class TestObservations:
    """Tests for agent observation methods."""

    def setup_method(self):
        """Reset engine before each test."""

    def test_cop_observation_keys(self, engine):
        """Cop observation contains required keys."""
        engine.reset_sub_game()
        obs = engine.get_cop_observation()
        assert "my_position" in obs
        assert "opponent_position" in obs
        assert "barriers_remaining" in obs
        assert "moves_remaining" in obs

    def test_thief_observation_keys(self, engine):
        """Thief observation contains required keys."""
        engine.reset_sub_game()
        obs = engine.get_thief_observation()
        assert "my_position" in obs
        assert "cop_last_known" in obs
        assert "moves_remaining" in obs

    def test_cop_observation_role(self, engine):
        """Cop observation has correct role."""
        engine.reset_sub_game()
        assert engine.get_cop_observation()["role"] == "cop"

    def test_thief_observation_role(self, engine):
        """Thief observation has correct role."""
        engine.reset_sub_game()
        assert engine.get_thief_observation()["role"] == "thief"


class TestApplyAction:
    """Tests for action application."""

    def test_cop_move(self, engine):
        """Cop move updates cop position."""
        engine.reset_sub_game()
        engine._cop_pos = Position(2, 2)
        action = Action(Role.COP, ActionType.MOVE, direction=Direction.DOWN)
        engine.apply_action(action)
        assert engine._cop_pos == Position(3, 2)

    def test_thief_move(self, engine):
        """Thief move updates thief position."""
        engine.reset_sub_game()
        engine._thief_pos = Position(2, 2)
        action = Action(Role.THIEF, ActionType.MOVE, direction=Direction.RIGHT)
        engine.apply_action(action)
        assert engine._thief_pos == Position(2, 3)

    def test_place_barrier(self, engine):
        """Cop can place a barrier."""
        engine.reset_sub_game()
        pos = Position(1, 1)
        action = Action(Role.COP, ActionType.PLACE_BARRIER, barrier_pos=pos)
        engine.apply_action(action)
        assert engine.grid.is_barrier(pos)
        assert engine._barrier_count == 1

    def test_thief_cannot_place_barrier(self, engine):
        """Thief placing barrier raises ValueError."""
        engine.reset_sub_game()
        action = Action(Role.THIEF, ActionType.PLACE_BARRIER, barrier_pos=Position(1, 1))
        with pytest.raises(ValueError):
            engine.apply_action(action)

    def test_max_barriers_exceeded(self, engine):
        """Exceeding max barriers raises ValueError."""
        engine.reset_sub_game()
        for i in range(engine.max_barriers):
            action = Action(Role.COP, ActionType.PLACE_BARRIER, barrier_pos=Position(0, i))
            engine.apply_action(action)
        with pytest.raises(ValueError):
            action = Action(Role.COP, ActionType.PLACE_BARRIER, barrier_pos=Position(1, 0))
            engine.apply_action(action)

    def test_move_increments_count(self, engine):
        """Each action increments move count."""
        engine.reset_sub_game()
        engine._cop_pos = Position(2, 2)
        action = Action(Role.COP, ActionType.MOVE, direction=Direction.UP)
        engine.apply_action(action)
        assert engine._move_count == 1


class TestWinConditions:
    """Tests for sub-game win detection."""

    def test_cop_wins_on_capture(self, engine):
        """Cop wins when on same cell as Thief."""
        engine.reset_sub_game()
        engine._cop_pos = Position(2, 2)
        engine._thief_pos = Position(2, 2)
        assert engine.check_sub_game_over() == SubGameResult.COP_WIN

    def test_thief_wins_on_max_moves(self, engine):
        """Thief wins when move limit is reached."""
        engine.reset_sub_game()
        engine._cop_pos = Position(0, 0)
        engine._thief_pos = Position(4, 4)
        engine._move_count = engine.max_moves
        assert engine.check_sub_game_over() == SubGameResult.THIEF_WIN

    def test_no_result_mid_game(self, engine):
        """No result returned when game is still ongoing."""
        engine.reset_sub_game()
        engine._cop_pos = Position(0, 0)
        engine._thief_pos = Position(4, 4)
        engine._move_count = 5
        assert engine.check_sub_game_over() is None


class TestScoring:
    """Tests for score calculation."""

    def test_cop_win_scoring(self, engine):
        """Cop win gives correct scores."""
        cop, thief = engine.score_sub_game(SubGameResult.COP_WIN)
        assert cop == 20
        assert thief == 5

    def test_thief_win_scoring(self, engine):
        """Thief win gives correct scores."""
        cop, thief = engine.score_sub_game(SubGameResult.THIEF_WIN)
        assert cop == 5
        assert thief == 10

    def test_record_sub_game_accumulates(self, engine):
        """Recording sub-games accumulates total scores."""
        engine.reset_sub_game()
        engine.record_sub_game(0, SubGameResult.COP_WIN, Position(0, 0), Position(4, 4))
        engine.record_sub_game(1, SubGameResult.THIEF_WIN, Position(0, 0), Position(4, 4))
        assert engine.game_state.total_cop_score == 25
        assert engine.game_state.total_thief_score == 15
        assert len(engine.game_state.sub_games) == 2
