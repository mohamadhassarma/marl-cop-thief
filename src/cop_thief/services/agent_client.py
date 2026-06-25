"""Agent Client — connects the game engine to Cop and Thief MCP servers."""

import json
import logging
import os
import httpx
from cop_thief.services.grid import Position
from cop_thief.constants import ActionType, Direction, Role
from cop_thief.services.game_engine import Action

logger = logging.getLogger(__name__)

DEFAULT_COP_URL = "http://localhost:8001"
DEFAULT_THIEF_URL = "http://localhost:8002"
REQUEST_TIMEOUT = 30


class AgentClient:
    """HTTP client for communicating with Cop and Thief MCP servers.

    Sends observation dicts as JSON to each server's decide_action tool
    and parses the returned action for the game engine to apply.
    """

    def __init__(
        self,
        cop_url: str | None = None,
        thief_url: str | None = None,
    ) -> None:
        """Initialize client with server URLs from env or defaults.

        Args:
            cop_url: URL of Cop MCP server (overrides env).
            thief_url: URL of Thief MCP server (overrides env).
        """
        self._cop_url = cop_url or os.environ.get("COP_MCP_URL", DEFAULT_COP_URL)
        self._thief_url = thief_url or os.environ.get("THIEF_MCP_URL", DEFAULT_THIEF_URL)
        self._token = os.environ.get("COP_MCP_TOKEN", "")

    def _headers(self) -> dict:
        """Return auth headers if token is set."""
        if self._token:
            return {"Authorization": f"Bearer {self._token}"}
        return {}

    def _call_server(self, url: str, observation: dict) -> dict:
        """Send observation to an MCP server and get action back.

        Args:
            url: Base URL of the MCP server.
            observation: Agent observation dict.

        Returns:
            Parsed action dict with 'action' and optional 'direction'/'position'.

        Raises:
            RuntimeError: If server returns error or invalid response.
        """
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "decide_action",
                "arguments": {"observation_json": json.dumps(observation)}
            },
            "id": 1
        }
        try:
            response = httpx.post(
                f"{url}/mcp",
                json=payload,
                headers=self._headers(),
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            data = response.json()
            result = data.get("result", {})
            content = result.get("content", [{}])
            text = content[0].get("text", "{}")
            return json.loads(text)
        except Exception as e:
            logger.error(f"Server call failed ({url}): {e}")
            raise RuntimeError(f"Agent server error: {e}")

    def get_cop_action(self, observation: dict) -> Action:
        """Get Cop's next action from the Cop MCP server.

        Args:
            observation: Cop's game observation dict.

        Returns:
            Action object ready for the game engine.
        """
        result = self._call_server(self._cop_url, observation)
        return self._parse_action(result, Role.COP)

    def get_thief_action(self, observation: dict) -> Action:
        """Get Thief's next action from the Thief MCP server.

        Args:
            observation: Thief's game observation dict.

        Returns:
            Action object ready for the game engine.
        """
        result = self._call_server(self._thief_url, observation)
        return self._parse_action(result, Role.THIEF)

    def _parse_action(self, result: dict, role: Role) -> Action:
        """Parse a server response dict into an Action object.

        Args:
            result: Response dict from MCP server.
            role: Which agent this action belongs to.

        Returns:
            Validated Action object.
        """
        action_type = result.get("action", ActionType.MOVE.value)

        if action_type == ActionType.PLACE_BARRIER.value and role == Role.COP:
            pos = result.get("position", {"row": 0, "col": 0})
            return Action(
                agent=role,
                action_type=ActionType.PLACE_BARRIER,
                barrier_pos=Position(pos["row"], pos["col"]),
            )

        direction_str = result.get("direction", "down")
        try:
            direction = Direction(direction_str)
        except ValueError:
            logger.warning(f"Invalid direction '{direction_str}', defaulting to down")
            direction = Direction.DOWN

        return Action(agent=role, action_type=ActionType.MOVE, direction=direction)

    def health_check(self, role: Role) -> bool:
        """Check if an agent server is reachable.

        Args:
            role: Which server to check (COP or THIEF).

        Returns:
            True if server responds, False otherwise.
        """
        url = self._cop_url if role == Role.COP else self._thief_url
        try:
            response = httpx.get(f"{url}/health", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
