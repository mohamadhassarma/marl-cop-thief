"""Thief MCP Server — FastMCP server for the Thief agent."""

import os
import json
import logging
from pathlib import Path
from dotenv import load_dotenv
from fastmcp import FastMCP
from cop_thief.services.strategy import thief_best_move, observation_to_positions
from cop_thief.services.grid import Grid, Position
from cop_thief.shared.config import ConfigManager
from cop_thief.constants import ActionType

load_dotenv()
logger = logging.getLogger(__name__)

mcp = FastMCP("thief-agent")

_root = Path(__file__).resolve().parents[3]
_config = ConfigManager(str(_root / "config" / "config.json"))


@mcp.tool()
def decide_action(observation_json: str) -> str:
    """Decide Thief's next action given current game state.

    Uses max-distance evasion — always moves to maximize distance
    from Cop while avoiding dead ends.

    Args:
        observation_json: JSON string of thief observation dict.

    Returns:
        JSON string with action type and direction.
    """
    try:
        observation = json.loads(observation_json)
        rows, cols = _config.grid_size
        grid = Grid(rows, cols)

        for b in observation.get("barriers", []):
            grid.add_barrier(Position(b["row"], b["col"]))

        my_pos, cop_pos = observation_to_positions(observation)

        best_dir = thief_best_move(grid, my_pos, cop_pos)
        if best_dir:
            logger.info(f"Thief evade → {best_dir.value} | pos:{my_pos} cop:{cop_pos}")
            return json.dumps({
                "action": ActionType.MOVE.value,
                "direction": best_dir.value
            })

        logger.warning("Thief fallback move")
        return json.dumps({"action": ActionType.MOVE.value, "direction": "up"})

    except Exception as e:
        logger.error(f"Thief decision error: {e}")
        return json.dumps({"action": ActionType.MOVE.value, "direction": "up"})


def run_thief_server(port: int = 8002) -> None:
    """Start the Thief MCP server.

    Args:
        port: Port to listen on (default 8002).
    """
    logger.info(f"Starting Thief MCP server on port {port}")
    mcp.run(transport="streamable-http", host="0.0.0.0", port=port)
