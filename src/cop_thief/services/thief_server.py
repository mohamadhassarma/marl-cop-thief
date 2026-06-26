"""Thief MCP Server — FastMCP server for the Thief agent (inter-group compatible)."""

import json
import logging
import os
import random
from pathlib import Path

from dotenv import load_dotenv
from fastmcp import FastMCP

from cop_thief.constants import COMPASS_WORDS, DIRECTION_DELTAS, ActionType
from cop_thief.services.grid import Grid, Position
from cop_thief.services.strategy import is_trapped, observation_to_positions
from cop_thief.shared.config import ConfigManager

load_dotenv()
logger = logging.getLogger(__name__)

mcp = FastMCP("thief-agent")

_root = Path(__file__).resolve().parents[3]
_config = ConfigManager(str(_root / "config" / "config.json"))
_auth_token = os.environ.get("THIEF_MCP_TOKEN", "")


def _extract_position(pos) -> dict:
    """Extract row/col from various position formats."""
    if isinstance(pos, dict):
        return {"row": pos.get("row", 0), "col": pos.get("col", 0)}
    if isinstance(pos, (list, tuple)) and len(pos) >= 2:
        return {"row": pos[0], "col": pos[1]}
    return {"row": 0, "col": 0}


def _extract_barriers(barriers) -> list:
    """Extract barriers from various formats."""
    if not barriers:
        return []
    result = []
    for b in barriers:
        if isinstance(b, dict):
            result.append({"row": b.get("row", 0), "col": b.get("col", 0)})
        elif isinstance(b, (list, tuple)) and len(b) >= 2:
            result.append({"row": b[0], "col": b[1]})
    return result


def _build_observation(obs: dict) -> dict:
    """Normalize observation from any format to internal format."""
    if not isinstance(obs, dict):
        return {
            "my_position": {"row": 4, "col": 4},
            "cop_last_known": {"row": 0, "col": 0},
            "barriers": [],
            "moves_remaining": 25,
        }
    thief_pos = _extract_position(obs.get("thief", {"row": 4, "col": 4}))
    cop_pos = _extract_position(obs.get("cop", {"row": 0, "col": 0}))
    barriers = _extract_barriers(obs.get("barriers", []))
    turn = obs.get("turn", 0)
    return {
        "my_position": thief_pos,
        "cop_last_known": cop_pos,
        "barriers": barriers,
        "moves_remaining": 25 - turn,
    }


def _scored_moves(grid: Grid, thief_pos: Position, cop_pos: Position) -> list:
    """Return all valid moves sorted by distance from cop (ascending = worse)."""
    moves = []
    for direction, (dr, dc) in DIRECTION_DELTAS.items():
        neighbor = Position(thief_pos.row + dr, thief_pos.col + dc)
        if not grid.is_valid(neighbor) or grid.is_barrier(neighbor):
            continue
        dist = max(
            abs(neighbor.row - cop_pos.row),
            abs(neighbor.col - cop_pos.col)
        )
        moves.append((dist, direction))
    moves.sort(key=lambda x: x[0], reverse=True)
    return moves


@mcp.tool()
def request_move(observation: dict, auth_token: str = "") -> str:
    """Decide Thief's next action — inter-group compatible tool.

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

        moves = _scored_moves(grid, my_pos, cop_pos)
        if not moves:
            return "[INTENT: HOLD] No valid moves available."


        chosen = moves[1][1] if len(moves) > 1 and random.random() < 0.4 else moves[0][1]

        compass = COMPASS_WORDS[chosen]
        logger.info(f"Thief evade → {compass}")
        return (
            f"[INTENT: MOVE] Evading {compass} to avoid the cop. "
            f"My position {my_pos}, cop at {cop_pos}."
        )

    except Exception as e:
        logger.error(f"Thief decision error: {e}", exc_info=True)
        return "[INTENT: MOVE] Moving north as fallback."


@mcp.tool()
def decide_action(observation_json: str) -> str:
    """Legacy internal tool for backward compatibility."""
    try:
        observation = json.loads(observation_json)
        result = request_move(observation, _auth_token)
        for compass in ["north-east", "north-west", "south-east", "south-west",
                        "north", "south", "east", "west"]:
            if compass in result:
                return json.dumps({"action": ActionType.MOVE.value, "direction": compass})
        return json.dumps({"action": ActionType.MOVE.value, "direction": "north"})
    except Exception as e:
        logger.error(f"Legacy thief error: {e}")
        return json.dumps({"action": ActionType.MOVE.value, "direction": "north"})


def run_thief_server(port: int = 8002) -> None:
    """Start the Thief MCP server."""
    logger.info(f"Starting Thief MCP server on port {port}")
    mcp.run(transport="streamable-http", host="0.0.0.0", port=port)
