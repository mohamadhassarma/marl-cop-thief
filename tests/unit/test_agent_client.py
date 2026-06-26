"""Unit tests for AgentClient."""

import json
import pytest
from unittest.mock import patch, MagicMock
from cop_thief.services.agent_client import AgentClient
from cop_thief.services.grid import Position
from cop_thief.constants import Role, ActionType, Direction


@pytest.fixture
def client() -> AgentClient:
    """Return AgentClient with local test URLs."""
    return AgentClient(
        cop_url="http://localhost:8001",
        thief_url="http://localhost:8002",
    )


@pytest.fixture
def cop_observation() -> dict:
    """Sample Cop observation."""
    return {
        "role": "cop",
        "my_position": {"row": 0, "col": 0},
        "opponent_position": {"row": 4, "col": 4},
        "barriers": [],
        "moves_taken": 0,
        "moves_remaining": 25,
        "barriers_placed": 0,
        "barriers_remaining": 5,
        "grid_size": [5, 5],
    }


@pytest.fixture
def thief_observation() -> dict:
    """Sample Thief observation."""
    return {
        "role": "thief",
        "my_position": {"row": 4, "col": 4},
        "cop_last_known": {"row": 0, "col": 0},
        "barriers": [],
        "moves_taken": 0,
        "moves_remaining": 25,
        "grid_size": [5, 5],
    }


class TestParseAction:
    """Tests for _parse_action method."""

    def test_parse_move_action(self, client):
        """Parses move action correctly."""
        result = {"action": "move", "direction": "east"}
        action = client._parse_action(result, role_is_cop=True)
        assert action.action_type == ActionType.MOVE
        assert action.direction == Direction.RIGHT

    def test_parse_barrier_action(self, client):
        """Parses barrier action correctly."""
        result = {"action": "place_barrier", "position": {"row": 2, "col": 3}}
        action = client._parse_action(result, role_is_cop=True)
        assert action.action_type == ActionType.PLACE_BARRIER
        assert action.barrier_pos == Position(2, 3)

    def test_invalid_direction_defaults(self, client):
        """Invalid direction defaults to DOWN."""
        result = {"action": "move", "direction": "diagonal"}
        action = client._parse_action(result, role_is_cop=False)
        assert action.direction == Direction.DOWN

    def test_thief_cannot_get_barrier_action(self, client):
        """Thief barrier action falls back to move."""
        result = {"action": "place_barrier", "position": {"row": 1, "col": 1}}
        action = client._parse_action(result, role_is_cop=False)
        assert action.action_type == ActionType.MOVE


class TestGetCopAction:
    """Tests for get_cop_action with mocked FastMCP client."""

    def test_get_cop_move(self, client, cop_observation):
        """Returns move action from server response."""
        with patch.object(client, "_run", return_value={"action": "move", "direction": "east"}):
            action = client.get_cop_action(cop_observation)
        assert action.action_type == ActionType.MOVE
        assert action.direction == Direction.RIGHT

    def test_get_cop_barrier(self, client, cop_observation):
        """Returns barrier action from server response."""
        with patch.object(client, "_run", return_value={
            "action": "place_barrier", "position": {"row": 3, "col": 3}
        }):
            action = client.get_cop_action(cop_observation)
        assert action.action_type == ActionType.PLACE_BARRIER
        assert action.barrier_pos == Position(3, 3)

    def test_server_error_raises(self, client, cop_observation):
        """RuntimeError raised when server is unreachable."""
        with patch.object(client, "_run", side_effect=RuntimeError("Connection refused")):
            with pytest.raises(RuntimeError):
                client.get_cop_action(cop_observation)


class TestGetThiefAction:
    """Tests for get_thief_action with mocked FastMCP client."""

    def test_get_thief_move(self, client, thief_observation):
        """Returns move action from server response."""
        with patch.object(client, "_run", return_value={"action": "move", "direction": "north"}):
            action = client.get_thief_action(thief_observation)
        assert action.action_type == ActionType.MOVE
        assert action.direction == Direction.UP


class TestHealthCheck:
    """Tests for health_check method."""

    def test_healthy_server(self, client):
        """Returns True when server responds."""
        with patch("asyncio.run", return_value=True):
            assert client.health_check(Role.COP) is True

    def test_unhealthy_server(self, client):
        """Returns False when server is unreachable."""
        with patch("asyncio.run", side_effect=Exception("refused")):
            assert client.health_check(Role.THIEF) is False
            