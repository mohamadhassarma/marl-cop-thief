"""Cop MCP Server — FastMCP server for the Cop agent."""

import json
import logging
from pathlib import Path

from dotenv import load_dotenv
from fastmcp import FastMCP

from cop_thief.constants import ActionType
from cop_thief.services.grid import Grid, Position
from cop_thief.services.strategy import cop_best_barrier, cop_best_move, observation_to_positions
from cop_thief.shared.config import ConfigManager
from cop_thief.shared.gatekeeper import ApiGatekeeper, RateLimitConfig

load_dotenv()
logger = logging.getLogger(__name__)

mcp = FastMCP("cop-agent")

# Resolve config paths relative to project root
_root = Path(__file__).resolve().parents[3]
_config = ConfigManager(str(_root / "config" / "config.json"))
_gatekeeper = ApiGatekeeper(RateLimitConfig(str(_root / "config" / "rate_limits.json")))


@mcp.tool()
def decide_action(observation_json: str) -> str:
    """Decide Cop's next action given current game state.

    Uses BFS pathfinding as primary strategy — always takes shortest
    path to Thief. Falls back to barrier placement if path is blocked.

    Args:
        observation_json: JSON string of cop observation dict.

    Returns:
        JSON string with action type and parameters.
    """
    try:
        observation = json.loads(observation_json)
        rows, cols = _config.grid_size
        grid = Grid(rows, cols)

        for b in observation.get("barriers", []):
            grid.add_barrier(Position(b["row"], b["col"]))

        my_pos, opp_pos = observation_to_positions(observation)
        barriers_remaining = observation.get("barriers_remaining", 0)
        moves_remaining = observation.get("moves_remaining", 25)

        # BFS: always move toward thief on shortest path
        best_move = cop_best_move(grid, my_pos, opp_pos)
        if best_move:
            logger.info(f"Cop BFS → {best_move.value} | pos:{my_pos} thief:{opp_pos}")
            return json.dumps({
                "action": ActionType.MOVE.value,
                "direction": best_move.value
            })

        # Barrier: only if early in game and thief is blocked
        if barriers_remaining > 0 and moves_remaining > 15:
            barrier = cop_best_barrier(grid, my_pos, opp_pos, barriers_remaining)
            if barrier:
                logger.info(f"Cop barrier → {barrier}")
                return json.dumps({
                    "action": ActionType.PLACE_BARRIER.value,
                    "position": {"row": barrier.row, "col": barrier.col}
                })

        # Fallback: move down
        logger.warning("Cop fallback move")
        return json.dumps({"action": ActionType.MOVE.value, "direction": "down"})

    except Exception as e:
        logger.error(f"Cop decision error: {e}")
        return json.dumps({"action": ActionType.MOVE.value, "direction": "down"})


def run_cop_server(port: int = 8001) -> None:
    """Start the Cop MCP server.

    Args:
        port: Port to listen on (default 8001).
    """
    logger.info(f"Starting Cop MCP server on port {port}")
    mcp.run(transport="streamable-http", host="0.0.0.0", port=port)
