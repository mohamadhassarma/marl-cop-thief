"""SDK — single entry point for all game logic.

All external consumers (CLI, GUI, tests) must go through this class.
No business logic should be called directly outside of the SDK.
"""

import logging

from cop_thief.constants import Role
from cop_thief.services.agent_client import AgentClient
from cop_thief.services.game_engine import GameEngine
from cop_thief.services.grid import Position
from cop_thief.shared.config import ConfigManager
from cop_thief.shared.version import VERSION

logger = logging.getLogger(__name__)


class CopThiefSDK:
    """Main SDK for the MARL Cop & Thief game.

    Orchestrates the full game pipeline:
    - Initializes engine, agent clients, and reporter
    - Runs sub-games sequentially
    - Collects results and triggers reporting

    Usage:
        sdk = CopThiefSDK()
        results = sdk.run_full_game()
    """

    def __init__(self, config_path: str = "config/config.json") -> None:
        """Initialize SDK with config and all dependencies.

        Args:
            config_path: Path to config.json file.
        """
        self._config = ConfigManager(config_path)
        self._engine = GameEngine(self._config)
        self._client = AgentClient()
        self._version = VERSION
        logger.info(f"CopThiefSDK v{self._version} initialized")

    @property
    def config(self) -> ConfigManager:
        """Return the loaded config manager."""
        return self._config

    @property
    def version(self) -> str:
        """Return SDK version string."""
        return self._version

    def run_sub_game(self, index: int) -> dict:
        """Run a single sub-game from start to finish.

        Resets the grid, alternates turns between Thief and Cop,
        checks win conditions after each turn, and records the result.

        Args:
            index: Sub-game index (0-based).

        Returns:
            Dict with sub-game result, scores, and move count.
        """
        self._engine.reset_sub_game()
        cop_start = Position(
            self._engine._cop_pos.row,
            self._engine._cop_pos.col
        )
        thief_start = Position(
            self._engine._thief_pos.row,
            self._engine._thief_pos.col
        )

        logger.info(f"Sub-game {index + 1} start — "
                    f"Cop:{cop_start} Thief:{thief_start}")

        while True:
            # Thief moves first
            thief_obs = self._engine.get_thief_observation()
            try:
                thief_action = self._client.get_thief_action(thief_obs)
                self._engine.apply_action(thief_action)
            except Exception as e:
                logger.error(f"Thief action failed: {e}")

            result = self._engine.check_sub_game_over()
            if result:
                break

            # Cop moves second
            cop_obs = self._engine.get_cop_observation()
            try:
                cop_action = self._client.get_cop_action(cop_obs)
                self._engine.apply_action(cop_action)
            except Exception as e:
                logger.error(f"Cop action failed: {e}")

            result = self._engine.check_sub_game_over()
            if result:
                break

        state = self._engine.record_sub_game(index, result, cop_start, thief_start)
        logger.info(f"Sub-game {index + 1} result: {result.value} "
                    f"in {state.moves_taken} moves")
        return {
            "sub_game_index": index,
            "result": result.value,
            "moves_taken": state.moves_taken,
            "cop_score": state.cop_score,
            "thief_score": state.thief_score,
            "cop_start": {"row": cop_start.row, "col": cop_start.col},
            "thief_start": {"row": thief_start.row, "col": thief_start.col},
        }

    def run_full_game(self) -> dict:
        """Run all sub-games and return complete game results.

        Returns:
            Dict with all sub-game results and total scores.
        """
        num = self._config.num_sub_games
        logger.info(f"Starting full game: {num} sub-games")
        sub_games = []

        for i in range(num):
            result = self.run_sub_game(i)
            sub_games.append(result)
            print(f"Sub-game {i + 1}/{num}: {result['result']} "
                  f"(Cop +{result['cop_score']}, Thief +{result['thief_score']})")

        totals = self._engine.game_state
        summary = {
            "group_name": self._config.reporting["group_name"],
            "cop_mcp_url": "",
            "thief_mcp_url": "",
            "timezone": self._config.reporting["timezone"],
            "sub_games": sub_games,
            "totals": {
                "cop": totals.total_cop_score,
                "thief": totals.total_thief_score,
            }
        }
        logger.info(f"Game complete — Cop:{totals.total_cop_score} "
                    f"Thief:{totals.total_thief_score}")
        return summary

    def check_servers(self) -> dict:
        """Check if both MCP servers are reachable.

        Returns:
            Dict with health status for each server.
        """
        return {
            "cop": self._client.health_check(Role.COP),
            "thief": self._client.health_check(Role.THIEF),
        }

    def render_board(self) -> str:
        """Return ASCII representation of the current board state."""
        return self._engine.render()
