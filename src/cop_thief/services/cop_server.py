"""Cop MCP Server — FastMCP server for the Cop agent (inter-group compatible)."""

import os
import json
import logging
from pathlib import Path
from dotenv import load_dotenv
from fastmcp import FastMCP
from cop_thief.services.strategy import cop_best_move, is_trapped, observation_to_positions
from cop_thief.services.grid import Grid, Position
from cop_thief.shared.config import ConfigManager
from cop_thief.constants import ActionType, COMPASS_WORDS

load_dotenv()
logger = logging.getLogger(__name__)

mcp = FastMCP("cop-agent")

_root = Path(__file__).resolve().parents[3]
_config = ConfigManager(str(_root / "config" / "config.json"))
_auth_token = os.environ.get("COP_MCP_TOKEN", "")


def _build_observation(obs: dict) -> dict:
    """Normalize observation from either internal or inter-group format."""
    if "cop" in obs and "thief" in obs:
        return {
            "my_position": obs["cop"],
            "opponent_position": obs["thief"],
            "barriers": obs.get("barriers", []),
            "barriers_remaining": obs.get("barriers_left", 5),
            "moves_remaining": 25 - obs.get("turn", 0),
        }
    return obs


@mcp.tool()
def request_move(observation: dict, auth_token: str = "") -> str:
    """Decide Cop's next action — inter-group compatible tool.

    Uses BFS pathfinding. Returns [INTENT: MOVE/BARRIER] prose message
    with compass direction as required by inter-group protocol.

    Args:
        observation: Game state dict.
        auth_token: Bearer token for authentication.

    Returns:
        Natural language string starting with [INTENT: ...].
    """
    if _auth_token and auth_token != _auth_token:
        return "[INTENT: HOLD] Access denied."

    try:
        obs = _build_observation(observation)
        rows, cols = _config.grid_size
        grid = Grid(rows, cols)

        for b in obs.get("barriers", []):
            grid.add_barrier(Position(b["row"], b["col"]))

        my_pos, opp_pos = observation_to_positions(obs)
        barriers_remaining = obs.get("barriers_remaining", 5)

        if is_trapped(grid, my_pos):
            return "[INTENT: HOLD] I am trapped with no valid moves."

        best_move = cop_best_move(grid, my_pos, opp_pos)
        if best_move:
            compass = COMPASS_WORDS[best_move]
            logger.info(f"Cop BFS → {compass} | pos:{my_pos} thief:{opp_pos}")
            return (
                f"[INTENT: MOVE] Moving {compass} to close in on the thief. "
                f"Current position {my_pos}, thief at {opp_pos}."
            )

        return "[INTENT: HOLD] No clear path to thief, holding position."

    except Exception as e:
        logger.error(f"Cop decision error: {e}")
        return "[INTENT: MOVE] Moving south as fallback."


@mcp.tool()
def decide_action(observation_json: str) -> str:
    """Legacy internal tool for backward compatibility.

    Args:
        observation_json: JSON string of cop observation dict.

    Returns:
        JSON string with action type and parameters.
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
            direction = "south"
        return json.dumps({"action": ActionType.MOVE.value, "direction": direction})
    except Exception as e:
        logger.error(f"Legacy cop error: {e}")
        return json.dumps({"action": ActionType.MOVE.value, "direction": "south"})


def run_cop_server(port: int = 8001) -> None:
    """Start the Cop MCP server."""
    logger.info(f"Starting Cop MCP server on port {port}")
    mcp.run(transport="streamable-http", host="0.0.0.0", port=port)
