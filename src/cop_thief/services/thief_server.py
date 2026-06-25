"""Thief MCP Server — FastMCP server for the Thief agent."""

import os
import json
import logging
from dotenv import load_dotenv
from fastmcp import FastMCP
from cop_thief.services.strategy import thief_best_move, observation_to_positions
from cop_thief.services.grid import Grid, Position
from cop_thief.shared.gatekeeper import ApiGatekeeper, RateLimitConfig
from cop_thief.shared.config import ConfigManager
from cop_thief.constants import Direction, ActionType

load_dotenv()
logger = logging.getLogger(__name__)

mcp = FastMCP("thief-agent")
_config = ConfigManager()
_gatekeeper = ApiGatekeeper(RateLimitConfig())


def _build_thief_prompt(observation: dict) -> str:
    """Build a strategic evasion prompt for the Thief agent.

    Args:
        observation: Thief's current game observation dict.

    Returns:
        Formatted prompt string for the LLM.
    """
    rows, cols = _config.grid_size
    return f"""You are the THIEF agent in a pursuit game on a {rows}x{cols} grid.
Your goal: SURVIVE all {observation['moves_taken'] + observation['moves_remaining']} moves
without being caught by the COP.

Current state:
- Your position: {observation['my_position']}
- Cop last known position: {observation['cop_last_known']}
- Barriers (impassable): {observation['barriers']}
- Moves remaining: {observation['moves_remaining']}

Survival rules (follow in order):
1. NEVER move onto or adjacent to the Cop's position if avoidable.
2. Prefer moves that maximize your distance from the Cop.
3. Prefer open areas over corners — avoid getting trapped.
4. If all directions lead closer to the Cop, pick the one with the most escape options.
5. NEVER stay still — always call move().

You MUST respond by calling exactly one tool: move().
Do not explain your reasoning. Just call the tool."""


def _call_llm(prompt: str) -> dict:
    """Call the Anthropic API via gatekeeper for Thief decisions.

    Args:
        prompt: User prompt describing game state.

    Returns:
        Parsed tool call dict with direction.

    Raises:
        RuntimeError: If LLM returns no tool call after retries.
    """
    import anthropic
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    tools = [
        {"name": "move", "description": "Move thief", "input_schema": {
            "type": "object",
            "properties": {"direction": {"type": "string",
                "enum": ["up", "down", "left", "right"]}},
            "required": ["direction"]
        }}
    ]

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
    """Move the Thief in a direction.

    Args:
        direction: One of 'up', 'down', 'left', 'right'.

    Returns:
        JSON string confirming the move action.
    """
    valid = [d.value for d in Direction]
    if direction not in valid:
        return f"Invalid direction '{direction}'. Must be one of {valid}"
    return json.dumps({"action": ActionType.MOVE.value, "direction": direction})


@mcp.tool()
def decide_action(observation_json: str) -> str:
    """Main decision tool — given game state, decide Thief's next action.

    Uses max-distance evasion strategy as primary decision maker,
    falls back to LLM for complex situations. Always returns a valid move.

    Args:
        observation_json: JSON string of thief observation dict.

    Returns:
        JSON string with action type and direction.
    """
    try:
        observation = json.loads(observation_json)
        rows, cols = _config.grid_size
        grid = Grid(rows, cols)

        # Rebuild grid state from observation
        for b in observation.get("barriers", []):
            grid.add_barrier(Position(b["row"], b["col"]))

        my_pos, cop_pos = observation_to_positions(observation)

        # Evasion-first strategy: maximize distance from Cop
        best_dir = thief_best_move(grid, my_pos, cop_pos)
        if best_dir:
            logger.info(f"Thief evasion move: {best_dir.value}")
            return json.dumps({
                "action": ActionType.MOVE.value,
                "direction": best_dir.value
            })

        # Fallback: LLM decides when evasion has no clear move
        prompt = _build_thief_prompt(observation)
        result = _call_llm(prompt)
        direction = result.get("input", {}).get("direction", "down")
        return json.dumps({"action": ActionType.MOVE.value, "direction": direction})

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
