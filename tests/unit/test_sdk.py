"""Unit tests for CopThiefSDK."""

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from cop_thief.sdk.sdk import CopThiefSDK
from cop_thief.constants import SubGameResult, Role, ActionType, Direction
from cop_thief.services.game_engine import Action
from cop_thief.services.grid import Position


@pytest.fixture
def config_path(tmp_path) -> str:
    """Write valid config and return path."""
    data = {
        "version": "1.00",
        "grid": {"size": [3, 3]},
        "game": {"num_sub_games": 2, "max_moves_per_sub_game": 10},
        "cop": {"max_barriers_per_sub_game": 2},
        "scoring": {
            "cop_win": 20, "thief_win": 10,
            "cop_loss": 5, "thief_loss": 5
        },
        "reporting": {
            "target_email": "test@test.com",
            "group_name": "TestGroup",
            "timezone": "Asia/Jerusalem"
        },
        "llm": {"model": "claude-sonnet-4-6", "max_tokens": 1000}
    }
    f = tmp_path / "config.json"
    f.write_text(json.dumps(data))
    return str(f)


@pytest.fixture
def sdk(config_path) -> CopThiefSDK:
    """Return initialized SDK."""
    return CopThiefSDK(config_path=config_path)


def _mock_cop_action() -> Action:
    """Return a dummy cop move action."""
    return Action(agent=Role.COP, action_type=ActionType.MOVE, direction=Direction.DOWN)


def _mock_thief_action() -> Action:
    """Return a dummy thief move action."""
    return Action(agent=Role.THIEF, action_type=ActionType.MOVE, direction=Direction.UP)


class TestSDKInit:
    """Tests for SDK initialization."""

    def test_initializes(self, sdk):
        """SDK initializes without error."""
        assert sdk is not None

    def test_version(self, sdk):
        """SDK version is set."""
        assert sdk.version == "1.00"

    def test_config_loaded(self, sdk):
        """Config is accessible via property."""
        assert sdk.config.num_sub_games == 2


class TestSDKCheckServers:
    """Tests for server health checks."""

    def test_both_offline(self, sdk):
        """Returns False for both when servers are down."""
        with patch.object(sdk._client, "health_check", return_value=False):
            status = sdk.check_servers()
        assert status["cop"] is False
        assert status["thief"] is False

    def test_both_online(self, sdk):
        """Returns True for both when servers are up."""
        with patch.object(sdk._client, "health_check", return_value=True):
            status = sdk.check_servers()
        assert status["cop"] is True
        assert status["thief"] is True


class TestSDKRunSubGame:
    """Tests for run_sub_game method."""

    def test_run_sub_game_cop_wins(self, sdk):
        """Sub-game returns correct result when cop wins."""
        with patch.object(sdk._client, "get_thief_action", return_value=_mock_thief_action()), \
             patch.object(sdk._client, "get_cop_action", return_value=_mock_cop_action()):
            # Force cop onto thief position after first moves
            sdk._engine.reset_sub_game()
            sdk._engine._cop_pos = Position(1, 1)
            sdk._engine._thief_pos = Position(1, 1)
            sdk._engine._move_count = sdk._engine.max_moves
            result = sdk._engine.check_sub_game_over()
            assert result == SubGameResult.COP_WIN

    def test_run_sub_game_thief_wins(self, sdk):
        """Sub-game returns thief win when moves exhausted."""
        sdk._engine.reset_sub_game()
        sdk._engine._cop_pos = Position(0, 0)
        sdk._engine._thief_pos = Position(2, 2)
        sdk._engine._move_count = sdk._engine.max_moves
        result = sdk._engine.check_sub_game_over()
        assert result == SubGameResult.THIEF_WIN


class TestSDKRunFullGame:
    """Tests for run_full_game method."""

    def test_full_game_returns_summary(self, sdk):
        """run_full_game returns dict with expected keys."""
        with patch.object(sdk, "run_sub_game") as mock_sub:
            mock_sub.return_value = {
                "sub_game_index": 0,
                "result": "thief_win",
                "moves_taken": 10,
                "cop_score": 5,
                "thief_score": 10,
                "cop_start": {"row": 0, "col": 0},
                "thief_start": {"row": 2, "col": 2},
            }
            results = sdk.run_full_game()

        assert "sub_games" in results
        assert "totals" in results
        assert "group_name" in results
        assert len(results["sub_games"]) == 2

    def test_full_game_calls_correct_sub_game_count(self, sdk):
        """run_full_game runs exactly num_sub_games sub-games."""
        with patch.object(sdk, "run_sub_game") as mock_sub:
            mock_sub.return_value = {
                "sub_game_index": 0, "result": "cop_win",
                "moves_taken": 5, "cop_score": 20, "thief_score": 5,
                "cop_start": {"row": 0, "col": 0},
                "thief_start": {"row": 2, "col": 2},
            }
            sdk.run_full_game()
        assert mock_sub.call_count == sdk.config.num_sub_games


class TestSDKRenderBoard:
    """Tests for render_board method."""

    def test_render_returns_string(self, sdk):
        """render_board returns a non-empty string."""
        sdk._engine.reset_sub_game()
        output = sdk.render_board()
        assert isinstance(output, str)
        assert len(output) > 0
