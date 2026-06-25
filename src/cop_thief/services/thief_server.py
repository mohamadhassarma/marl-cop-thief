"""Thief MCP Server — FastMCP server for the Thief agent (inter-group compatible)."""

import os
import json
import logging
from pathlib import Path
from dotenv import load_dotenv
from fastmcp import FastMCP
from cop_thief.services.strategy import thief_best_move, is_trapped, observation_to_positions
from cop_thief.services.grid import Grid, Position
from cop_thief.shared.config import ConfigManager
from cop_thief.constants import ActionType, COMPASS_WORDS

load_dotenv()
logger = logging.getLogger(__name__)

mcp = FastMCP("thief-agent")

_root = Path(__file__).resolve().parents[3]
_config = ConfigManager(str(_root / "config" / "config.json"))
_auth_token = os.environ.get("THIEF_MCP_TOKEN", "")


def _build_observation(obs: dict) -> dict:
    """Normalize observation from either internal or inter-group format."""
    if "cop" in obs and "thief" in obs:
        return {
            "my_position": obs["thief"],
            "cop_last_known": obs["cop"],
            "barriers": obs.get("barriers", []),
            "moves_remaining": 25 - obs.get("turn", 0),
        }
    return obs


@mcp.tool()
def request_move(observation: dict, auth_token: str = "") -> str:
    """Decide Thief's next action — inter-group compatible tool.

    Uses max-distance evasion with 8-way movement.
    Returns [INTENT: MOVE] prose with compass direction.

    Args:
        observation: Game state dict.
        auth_token: Bearer token for authentication.

    Returns:
        Natural language string starting with [INTENT: MOVE].
    """
    if _auth_token and auth_token != _auth_token:
        return "[INTENT: HOLD] Access denied."

    try:
        obs = _build_observation(observation)
        rows, cols = _config.grid_size
        grid = Grid(rows, cols)

        for b in obs.get("barriers", []):
            grid.add_barrier(Position(b["row"], b["col"]))

        my_pos, cop_pos = observation_to_positions(obs)

        if is_trapped(grid, my_pos):
            return "[INTENT: HOLD] I am trapped with no valid moves."

        best_dir = thief_best_move(grid, my_pos, cop_pos)
        if best_dir:
            compass = COMPASS_WORDS[best_dir]
            logger.info(f"Thief evade → {compass} | pos:{my_pos} cop:{cop_pos}")
            return (
                f"[INTENT: MOVE] Evading {compass} to maximize distance from cop. "
                f"My position {my_pos}, cop at {cop_pos}."
            )

        return "[INTENT: HOLD] No safe move available."

    except Exception as e:
        logger.error(f"Thief decision error: {e}")
        return "[INTENT: MOVE] Moving north as fallback."


@mcp.tool()
def decide_action(observation_json: str) -> str:
    """Legacy internal tool for backward compatibility.

    Args:
        observation_json: JSON string of thief observation dict.

    Returns:
        JSON string with action type and direction.
    """
    try:
        observation = json.loads(observation_json)
        result = request_move(observation, _auth_token)
        if "north-east" in result:
            direction = "north-east"
        elif "north-west" in result:
            direction = "north-west"
        elif "south-east" in result:
            direction = "south-east"
        elif "south-west" in result:
            direction = "south-west"
        elif "north" in result:
            direction = "north"
        elif "south" in result:
            direction = "south"
        elif "east" in result:
            direction = "east"
        elif "west" in result:
            direction = "west"
        else:
            direction = "north"
        return json.dumps({"action": ActionType.MOVE.value, "direction": direction})
    except Exception as e:
        logger.error(f"Legacy thief error: {e}")
        return json.dumps({"action": ActionType.MOVE.value, "direction": "north"})


def run_thief_server(port: int = 8002) -> None:
    """Start the Thief MCP server."""
    logger.info(f"Starting Thief MCP server on port {port}")
    mcp.run(transport="streamable-http", host="0.0.0.0", port=port)
