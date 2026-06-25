"""Cop MCP Server — FastMCP server for the Cop agent."""

import os
import json
import logging
from dotenv import load_dotenv
from fastmcp import FastMCP
from cop_thief.services.strategy import cop_best_move, cop_best_barrier, observation_to_positions
from cop_thief.services.grid import Grid, Position
from cop_thief.shared.gatekeeper import ApiGatekeeper, RateLimitConfig
from cop_thief.shared.config import ConfigManager
from cop_thief.constants import Direction, ActionType

load_dotenv()
logger = logging.getLogger(__name__)

mcp = FastMCP("cop-agent")
_config = ConfigManager()
_gatekeeper = ApiGatekeeper(RateLimitConfig())


def _build_cop_prompt(observation: dict) -> str:
    """Build a strategic system prompt for the Cop agent.

    Args:
        observation: Cop's current game observation dict.

    Returns:
        Formatted prompt string for the LLM.
    """
    rows, cols = _config.grid_size
    return f"""You are the COP agent in a pursuit game on a {rows}x{cols} grid.
Your goal: catch the THIEF by moving to their exact position.

Current state:
- Your position: {observation['my_position']}
- Thief position: {observation['opponent_position']}
- Barriers: {observation['barriers']}
- Moves taken: {observation['moves_taken']}/{observation['moves_taken'] + observation['moves_remaining']}
- Barriers placed: {observation['barriers_placed']}/{observation['barriers_placed'] + observation['barriers_remaining']}

Strategy rules (follow in order):
1. If you can capture the Thief in 1 move, DO IT — call move() immediately.
2. If the Thief has an obvious escape route and you have barriers left, call place_barrier()
   to block their most likely escape direction.
3. Otherwise, move toward the Thief using the shortest path.
4. NEVER stay still — always call either move() or place_barrier().

You MUST respond by calling exactly one tool: move() or place_barrier().
Do not explain your reasoning. Just call the tool."""


def _build_thief_prompt_for_cop(observation: dict) -> str:
    """Unused here but kept for symmetry."""
    return ""


def _call_llm(prompt: str, tools: list) -> dict:
    """Call the Anthropic API via gatekeeper and return the tool call.

    Args:
        prompt: System + user prompt for the LLM.
        tools: List of tool definitions.

    Returns:
        Parsed tool call dict with 'name' and 'input' keys.

    Raises:
        RuntimeError: If LLM returns no tool call after retries.
    """
    import anthropic
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    def _api_call():
        return client.messages.create(
            model=_config.llm["model"],
            max_tokens=_config.llm["max_tokens"],
            tools=tools,
            messages=[{"role": "user", "content": prompt}],
        )

    response = _gatekeeper.execute(_api_call)
    for block in response.content:
        if block.type == "tool_use":
            return {"name": block.name, "input": block.input}
    raise RuntimeError("LLM returned no tool call")


@mcp.tool()
def move(direction: str) -> str:
    """Move the Cop in a direction.

    Args:
        direction: One of 'up', 'down', 'left', 'right'.

    Returns:
        Confirmation string with the direction moved.
    """
    valid = [d.value for d in Direction]
    if direction not in valid:
        return f"Invalid direction '{direction}'. Must be one of {valid}"
    return json.dumps({"action": ActionType.MOVE.value, "direction": direction})


@mcp.tool()
def place_barrier(row: int, col: int) -> str:
    """Place a barrier at the given grid position.

    Args:
        row: Target row (0-indexed).
        col: Target column (0-indexed).

    Returns:
        Confirmation string with barrier position.
    """
    return json.dumps({
        "action": ActionType.PLACE_BARRIER.value,
        "position": {"row": row, "col": col}
    })


@mcp.tool()
def decide_action(observation_json: str) -> str:
    """Main decision tool — given game state, decide Cop's next action.

    Uses BFS strategy as primary decision maker, falls back to LLM
    for complex situations. Always returns a valid action.

    Args:
        observation_json: JSON string of cop observation dict.

    Returns:
        JSON string with action type and parameters.
    """
    try:
        observation = json.loads(observation_json)
        rows, cols = _config.grid_size
        grid = Grid(rows, cols)

        # Rebuild grid state from observation
        for b in observation.get("barriers", []):
            grid.add_barrier(Position(b["row"], b["col"]))

        my_pos, opp_pos = observation_to_positions(observation)
        barriers_remaining = observation.get("barriers_remaining", 0)

        # BFS-first strategy: use pathfinding directly
        best_move = cop_best_move(grid, my_pos, opp_pos)
        if best_move:
            logger.info(f"Cop BFS move: {best_move.value}")
            return json.dumps({
                "action": ActionType.MOVE.value,
                "direction": best_move.value
            })

        # Fallback: place barrier if BFS has no path
        barrier = cop_best_barrier(grid, my_pos, opp_pos, barriers_remaining)
        if barrier:
            return json.dumps({
                "action": ActionType.PLACE_BARRIER.value,
                "position": {"row": barrier.row, "col": barrier.col}
            })

        # Last resort: LLM decides
        prompt = _build_cop_prompt(observation)
        tools = [
            {"name": "move", "description": "Move cop", "input_schema": {
                "type": "object",
                "properties": {"direction": {"type": "string"}},
                "required": ["direction"]
            }},
            {"name": "place_barrier", "description": "Place barrier", "input_schema": {
                "type": "object",
                "properties": {"row": {"type": "integer"}, "col": {"type": "integer"}},
                "required": ["row", "col"]
            }},
        ]
        result = _call_llm(prompt, tools)
        return json.dumps(result)

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
