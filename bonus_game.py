"""Bonus Game Runner — runs inter-group game calling opponent's MCP servers."""

import asyncio
import json
import logging
import random
from pathlib import Path

from fastmcp import Client

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Their server URLs and tokens
THEIR_COP_URL = "https://stated-prairie-fact-reviews.trycloudflare.com/mcp"
THEIR_THIEF_URL = "https://sorts-comparisons-aye-subsidiary.trycloudflare.com/mcp"
THEIR_COP_TOKEN = "e3ed46cc66064db59aa83795d2c985e2"
THEIR_THIEF_TOKEN = "d63c8ff4fa69e0702e7c8ae903b44bfe"

# Our server URLs
OUR_COP_URL = "https://coveting-elevator-municipal.ngrok-free.dev/mcp"
OUR_THIEF_URL = "https://traditions-phrase-beans-former.trycloudflare.com/mcp"

GRID_SIZE = 5
MAX_MOVES = 25
NUM_SUB_GAMES = 6
SEED = 0


def get_start_positions(sub_game_index: int) -> tuple:
    """Get seeded random start positions for a sub-game."""
    rng = random.Random(SEED + sub_game_index)
    all_cells = [(r, c) for r in range(GRID_SIZE) for c in range(GRID_SIZE)]
    cop = rng.choice(all_cells)
    remaining = [p for p in all_cells if p != cop]
    thief = rng.choice(remaining)
    return cop, thief


def build_observation(role: str, cop: tuple, thief: tuple,
                      barriers: list, turn: int) -> dict:
    """Build observation dict in their expected format."""
    return {
        "role": role,
        "grid": [GRID_SIZE, GRID_SIZE],
        "cop": [cop[0], cop[1]],
        "thief": [thief[0], thief[1]],
        "barriers": [[b[0], b[1]] for b in barriers] if barriers else [],
        "barriers_left": 5,
        "turn": turn,
    }


def parse_move(response_text: str) -> tuple:
    """Parse [INTENT: MOVE/BARRIER] response into action."""
    text = response_text.lower()
    action = "move"
    direction = (0, 0)

    compass_map = {
        "north-east": (-1, 1), "north-west": (-1, -1),
        "south-east": (1, 1), "south-west": (1, -1),
        "north": (-1, 0), "south": (1, 0),
        "east": (0, 1), "west": (0, -1),
    }

    for compass, delta in compass_map.items():
        if compass in text:
            direction = delta
            break

    return action, direction


def apply_move(pos: tuple, delta: tuple) -> tuple:
    """Apply a move delta to a position, clamping to grid bounds."""
    new_row = max(0, min(GRID_SIZE - 1, pos[0] + delta[0]))
    new_col = max(0, min(GRID_SIZE - 1, pos[1] + delta[1]))
    return (new_row, new_col)


async def call_agent(url: str, token: str, observation: dict) -> str:
    """Call an agent's request_move tool."""
    async with Client(url) as client:
        result = await client.call_tool(
            "request_move",
            {"observation": observation, "auth_token": token}
        )
        return result.content[0].text


async def run_sub_game(sub_game_index: int, we_are_cop: bool) -> dict:
    """Run a single sub-game."""
    cop_start, thief_start = get_start_positions(sub_game_index)
    cop_pos = cop_start
    thief_pos = thief_start
    barriers = []

    if we_are_cop:
        cop_url, cop_token = OUR_COP_URL, ""
        thief_url, thief_token = THEIR_THIEF_URL, THEIR_THIEF_TOKEN
    else:
        cop_url, cop_token = THEIR_COP_URL, THEIR_COP_TOKEN
        thief_url, thief_token = OUR_THIEF_URL, ""

    logger.info(f"Sub-game {sub_game_index + 1} | "
                f"{'We are COP' if we_are_cop else 'We are THIEF'} | "
                f"Cop:{cop_pos} Thief:{thief_pos}")

    result = "thief_win"
    moves_taken = 0

    for turn in range(MAX_MOVES):
        # Thief moves first
        obs = build_observation("thief", cop_pos, thief_pos, barriers, turn)
        try:
            thief_resp = await call_agent(thief_url, thief_token, obs)
            _, delta = parse_move(thief_resp)
            thief_pos = apply_move(thief_pos, delta)
        except Exception as e:
            logger.error(f"Thief agent error: {e}")

        moves_taken = turn + 1

        if cop_pos == thief_pos:
            result = "cop_win"
            break

        # Cop moves
        obs = build_observation("cop", cop_pos, thief_pos, barriers, turn)
        try:
            cop_resp = await call_agent(cop_url, cop_token, obs)
            _, delta = parse_move(cop_resp)
            cop_pos = apply_move(cop_pos, delta)
        except Exception as e:
            logger.error(f"Cop agent error: {e}")

        if cop_pos == thief_pos:
            result = "cop_win"
            moves_taken = turn + 1
            break

    logger.info(f"Sub-game {sub_game_index + 1} result: {result} in {moves_taken} moves")

    if result == "cop_win":
        cop_score, thief_score = 20, 5
    else:
        cop_score, thief_score = 5, 10

    return {
        "sub_game_index": sub_game_index,
        "result": result,
        "moves_taken": moves_taken,
        "we_are_cop": we_are_cop,
        "cop_score": cop_score,
        "thief_score": thief_score,
    }


async def run_bonus_game():
    """Run all 6 sub-games of the bonus game."""
    print("\n" + "="*60)
    print("  BONUS GAME — Mohamad-Salih vs NajAmjad")
    print("  Sub-games 1-3: They are Cop, We are Thief")
    print("  Sub-games 4-6: We are Cop, They are Thief")
    print("="*60 + "\n")

    sub_games = []
    our_total = 0
    their_total = 0

    for i in range(NUM_SUB_GAMES):
        we_are_cop = i >= 3  # They are Cop in 1-3, we are Cop in 4-6
        result = await run_sub_game(i, we_are_cop)
        sub_games.append(result)

        if we_are_cop:
            our_total += result["cop_score"]
            their_total += result["thief_score"]
        else:
            our_total += result["thief_score"]
            their_total += result["cop_score"]

        print(f"Sub-game {i+1}/6: {result['result']} in {result['moves_taken']} moves")

    print(f"\n{'='*60}")
    print(f"  FINAL: Us={our_total} | Them={their_total}")
    print(f"{'='*60}\n")

    report = {
        "report_type": "bonus_game",
        "groups": {"group_1": "NajAmjad", "group_2": "Mohamad-Salih"},
        "github_repo_group_1": "https://github.com/najikay/mcp-marl-cop-thief",
        "github_repo_group_2": "https://github.com/mohamadhassarma/marl-cop-thief",
        "mcp_url_group_1_cop": THEIR_COP_URL,
        "mcp_url_group_1_thief": THEIR_THIEF_URL,
        "mcp_url_group_2_cop": OUR_COP_URL,
        "mcp_url_group_2_thief": OUR_THIEF_URL,
        "timezone": "Asia/Jerusalem",
        "students_group_1": ["Amjad Abd El Rahim", "Naji Kayal"],
        "students_group_2": ["Mohamad Hassarma", "Salih Rabah"],
        "sub_games": sub_games,
        "totals_by_group": {
            "NajAmjad": their_total,
            "Mohamad-Salih": our_total,
        },
        "bonus_claim": {
            "NajAmjad": 10 if their_total > our_total else (7 if their_total < our_total else 5),
            "Mohamad-Salih": 10 if our_total > their_total else (7 if our_total < their_total else 5),
        },
        "mutual_agreement": None,
    }

    output_path = Path("results/bonus_game_results.json")
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"Results saved to {output_path}")
    print("\nBonus report JSON:")
    print(json.dumps(report, indent=2))

    return report


if __name__ == "__main__":
    asyncio.run(run_bonus_game())
