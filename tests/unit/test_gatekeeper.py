"""Unit tests for ApiGatekeeper."""

import json

import pytest

from cop_thief.shared.gatekeeper import ApiGatekeeper, RateLimitConfig


@pytest.fixture
def rate_config(tmp_path) -> RateLimitConfig:
    """Create a test rate limit config."""
    data = {
        "version": "1.00",
        "rate_limits": {
            "default": {
                "requests_per_minute": 60,
                "requests_per_hour": 500,
                "concurrent_max": 5,
                "retry_after_seconds": 1,
                "max_retries": 3,
                "max_queue_size": 50
            }
        }
    }
    f = tmp_path / "rate_limits.json"
    f.write_text(json.dumps(data))
    return RateLimitConfig(str(f))


@pytest.fixture
def gatekeeper(rate_config) -> ApiGatekeeper:
    """Return a fresh ApiGatekeeper."""
    return ApiGatekeeper(rate_config)


class TestRateLimitConfig:
    """Tests for RateLimitConfig loading."""

    def test_loads_correctly(self, rate_config):
        """Config loads with correct values."""
        assert rate_config.requests_per_minute == 60
        assert rate_config.max_retries == 3

    def test_file_not_found(self):
        """Raises FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            RateLimitConfig("nonexistent.json")


class TestApiGatekeeperExecute:
    """Tests for execute() method."""

    def test_executes_successfully(self, gatekeeper):
        """Gatekeeper executes a simple callable."""
        result = gatekeeper.execute(lambda: 42)
        assert result == 42

    def test_passes_args(self, gatekeeper):
        """Gatekeeper passes args and kwargs correctly."""
        result = gatekeeper.execute(lambda x, y: x + y, 3, 7)
        assert result == 10

    def test_increments_call_count(self, gatekeeper):
        """Total calls incremented after each execute."""
        gatekeeper.execute(lambda: None)
        gatekeeper.execute(lambda: None)
        assert gatekeeper.get_queue_status().total_calls == 2

    def test_retries_on_failure(self, gatekeeper):
        """Gatekeeper retries on exception."""
        call_count = {"n": 0}

        def flaky():
            call_count["n"] += 1
            if call_count["n"] < 2:
                raise ConnectionError("Transient error")
            return "ok"

        result = gatekeeper.execute(flaky)
        assert result == "ok"
        assert gatekeeper.get_queue_status().total_retries == 1

    def test_raises_after_max_retries(self, gatekeeper):
        """Raises RuntimeError after all retries exhausted."""
        def always_fails():
            raise ConnectionError("Always fails")

        with pytest.raises(RuntimeError):
            gatekeeper.execute(always_fails)


class TestQueueStatus:
    """Tests for queue status reporting."""

    def test_initial_status(self, gatekeeper):
        """Initial queue status has zero counts."""
        status = gatekeeper.get_queue_status()
        assert status.total_calls == 0
        assert status.total_retries == 0
        assert status.depth == 0

    def test_status_after_calls(self, gatekeeper):
        """Status reflects calls made."""
        gatekeeper.execute(lambda: None)
        gatekeeper.execute(lambda: None)
        status = gatekeeper.get_queue_status()
        assert status.total_calls == 2
