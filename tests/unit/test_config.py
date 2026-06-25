"""Unit tests for ConfigManager."""

import json
import pytest
from pathlib import Path
from cop_thief.shared.config import ConfigManager


@pytest.fixture
def valid_config(tmp_path) -> Path:
    """Write a valid config.json to a temp directory."""
    data = {
        "version": "1.00",
        "grid": {"size": [5, 5]},
        "game": {"num_sub_games": 6, "max_moves_per_sub_game": 25},
        "cop": {"max_barriers_per_sub_game": 5},
        "scoring": {
            "cop_win": 20, "thief_win": 10,
            "cop_loss": 5, "thief_loss": 5
        },
        "reporting": {
            "target_email": "test@test.com",
            "group_name": "TestGroup",
            "timezone": "Asia/Jerusalem"
        },
        "llm": {"model": "claude-sonnet-4-6", "max_tokens": 1000}
    }
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps(data))
    return config_file


@pytest.fixture
def config(valid_config) -> ConfigManager:
    """Return a loaded ConfigManager from valid config."""
    return ConfigManager(str(valid_config))


class TestConfigManagerLoad:
    """Tests for config loading."""

    def test_loads_valid_config(self, config):
        """ConfigManager loads without error on valid config."""
        assert config is not None

    def test_file_not_found(self):
        """Raises FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            ConfigManager("nonexistent/path/config.json")

    def test_missing_required_key(self, tmp_path):
        """Raises ValueError if required key is missing."""
        data = {"version": "1.00"}  # missing all other keys
        f = tmp_path / "config.json"
        f.write_text(json.dumps(data))
        with pytest.raises(ValueError):
            ConfigManager(str(f))


class TestConfigManagerProperties:
    """Tests for config property accessors."""

    def test_grid_size(self, config):
        """grid_size returns correct tuple."""
        assert config.grid_size == (5, 5)

    def test_num_sub_games(self, config):
        """num_sub_games returns correct value."""
        assert config.num_sub_games == 6

    def test_max_moves(self, config):
        """max_moves returns correct value."""
        assert config.max_moves == 25

    def test_max_barriers(self, config):
        """max_barriers returns correct value."""
        assert config.max_barriers == 5

    def test_version(self, config):
        """version returns correct string."""
        assert config.version == "1.00"

    def test_scoring(self, config):
        """scoring returns dict with expected keys."""
        s = config.scoring
        assert s["cop_win"] == 20
        assert s["thief_win"] == 10

    def test_llm(self, config):
        """llm returns dict with model key."""
        assert config.llm["model"] == "claude-sonnet-4-6"

    def test_get_existing_key(self, config):
        """get() returns value for existing key."""
        assert config.get("version") == "1.00"

    def test_get_missing_key_default(self, config):
        """get() returns default for missing key."""
        assert config.get("nonexistent", "fallback") == "fallback"
