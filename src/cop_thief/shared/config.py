"""Configuration manager — loads and validates config/config.json."""

import json
from pathlib import Path


class ConfigManager:
    """Loads game configuration from a JSON file.

    All game parameters are read from config/config.json.
    No values are hardcoded — this is the single source of truth.
    """

    def __init__(self, config_path: str = "config/config.json") -> None:
        """Initialize and load config from the given path.

        Args:
            config_path: Path to the JSON config file.

        Raises:
            FileNotFoundError: If config file does not exist.
            ValueError: If required fields are missing.
        """
        self._path = Path(config_path)
        self._data = self._load()
        self._validate()

    def _load(self) -> dict:
        """Load JSON config from disk."""
        if not self._path.exists():
            raise FileNotFoundError(f"Config file not found: {self._path}")
        with open(self._path) as f:
            return json.load(f)

    def _validate(self) -> None:
        """Ensure all required top-level keys are present."""
        required = ["version", "grid", "game", "cop", "scoring", "reporting", "llm"]
        missing = [k for k in required if k not in self._data]
        if missing:
            raise ValueError(f"Missing required config keys: {missing}")

    def get(self, key: str, default=None):
        """Get a top-level config value by key."""
        return self._data.get(key, default)

    @property
    def grid_size(self) -> tuple[int, int]:
        """Return grid dimensions as (rows, cols)."""
        size = self._data["grid"]["size"]
        return (size[0], size[1])

    @property
    def num_sub_games(self) -> int:
        """Return number of sub-games per full game."""
        return self._data["game"]["num_sub_games"]

    @property
    def max_moves(self) -> int:
        """Return max moves allowed per sub-game."""
        return self._data["game"]["max_moves_per_sub_game"]

    @property
    def max_barriers(self) -> int:
        """Return max barriers the Cop can place per sub-game."""
        return self._data["cop"]["max_barriers_per_sub_game"]

    @property
    def scoring(self) -> dict:
        """Return scoring configuration dict."""
        return self._data["scoring"]

    @property
    def llm(self) -> dict:
        """Return LLM configuration dict."""
        return self._data["llm"]

    @property
    def reporting(self) -> dict:
        """Return reporting configuration dict."""
        return self._data["reporting"]

    @property
    def version(self) -> str:
        """Return config version string."""
        return self._data["version"]
