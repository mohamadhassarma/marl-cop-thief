"""Agent Client — connects the game engine to Cop and Thief MCP servers."""

import json
import logging
import os
import asyncio
from cop_thief.services.grid import Position
from cop_thief.constants import ActionType, Direction, DIRECTION_DELTAS
from cop_thief.services.game_engine import Action

logger = logging.getLogger(__name__)

DEFAULT_COP_URL = "http://localhost:8001/mcp"
DEFAULT_THIEF_URL = "http://localhost:8002/mcp"
REQUEST_TIMEOUT = 30

# Map compass words to Direction enum values
COMPASS_TO_DIRECTION: dict[str, Direction] = {
    "north": Direction.UP,
    "south": Direction.DOWN,
    "west": Direction.LEFT,
    "east": Direction.RIGHT,
    "north-east": Direction.UP_RIGHT,
    "north-west": Direction.UP_LEFT,
    "south-east": Direction.DOWN_RIGHT,
    "south-west": Direction.DOWN_LEFT,
}


class AgentClient:
    """Client for communicating with Cop and Thief MCP servers."""

    def __init__(
        self,
        cop_url: str | None = None,
        thief_url: str | None = None,
    ) -> None:
        """Initialize client with server URLs from env or defaults."""
        self._cop_url = cop_url or os.environ.get("COP_MCP_URL", DEFAULT_COP_URL)
        self._thief_url = thief_url or os.environ.get("THIEF_MCP_URL", DEFAULT_THIEF_URL)
        if not self._cop_url.endswith("/mcp"):
            self._cop_url += "/mcp"
        if not self._thief_url.endswith("/mcp"):
            self._thief_url += "/mcp"

    async def _call_tool(self, url: str, observation: dict) -> dict:
        """Call decide_action tool on an MCP server asynchronously."""
        from fastmcp import Client
        try:
            async with Client(url) as client:
                result = await client.call_tool(
                    "decide_action",
                    {"observation_json": json.dumps(observation)}
                )
                content = result.content
                if content and hasattr(content[0], "text"):
                    return json.loads(content[0].text)
                return {}
        except Exception as e:
            logger.error(f"MCP tool call failed ({url}): {e}")
            raise RuntimeError(f"Agent server error: {e}")

    def _run(self, coro) -> dict:
        """Run async coroutine safely from sync context."""
        return asyncio.run(coro)

    def get_cop_action(self, observation: dict) -> Action:
        """Get Cop's next action from the Cop MCP server."""
        result = self._run(self._call_tool(self._cop_url, observation))
        return self._parse_action(result, role_is_cop=True)

    def get_thief_action(self, observation: dict) -> Action:
        """Get Thief's next action from the Thief MCP server."""
        result = self._run(self._call_tool(self._thief_url, observation))
        return self._parse_action(result, role_is_cop=False)

    def _parse_action(self, result: dict, role_is_cop: bool = True) -> Action:
        """Parse a server response dict into an Action object.

        Handles both compass word directions (north/south-east etc)
        and legacy direction strings.
        """
        from cop_thief.constants import Role
        role = Role.COP if role_is_cop else Role.THIEF
        action_type = result.get("action", ActionType.MOVE.value)

        if action_type == ActionType.PLACE_BARRIER.value and role_is_cop:
            pos = result.get("position", {"row": 0, "col": 0})
            return Action(
                agent=role,
                action_type=ActionType.PLACE_BARRIER,
                barrier_pos=Position(pos["row"], pos["col"]),
            )

        direction_str = result.get("direction", "south")
        direction = COMPASS_TO_DIRECTION.get(direction_str)
        if direction is None:
            logger.warning(f"Invalid direction '{direction_str}', defaulting to down")
            direction = Direction.DOWN

        return Action(agent=role, action_type=ActionType.MOVE, direction=direction)

    def health_check(self, role) -> bool:
        """Check if an agent server is reachable via FastMCP."""
        from cop_thief.constants import Role
        url = self._cop_url if role == Role.COP else self._thief_url

        async def _ping():
            from fastmcp import Client
            async with Client(url) as client:
                await client.ping()
            return True

        try:
            return asyncio.run(_ping())
        except Exception:
            return False
