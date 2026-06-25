"""API Gatekeeper — centralized rate limiting for all LLM API calls."""

import time
import json
import logging
from collections import deque
from pathlib import Path
from typing import Callable, Any

logger = logging.getLogger(__name__)


class RateLimitConfig:
    """Loads rate limit settings from config file."""

    def __init__(self, config_path: str = "config/rate_limits.json") -> None:
        """Load rate limit config from JSON file.

        Args:
            config_path: Path to rate_limits.json.

        Raises:
            FileNotFoundError: If config file does not exist.
        """
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Rate limit config not found: {path}")
        with open(path) as f:
            data = json.load(f)
        provider = data.get("rate_limits", {})
        cfg = provider.get("anthropic", provider.get("default", {}))
        self.requests_per_minute: int = cfg.get("requests_per_minute", 30)
        self.requests_per_hour: int = cfg.get("requests_per_hour", 500)
        self.concurrent_max: int = cfg.get("concurrent_max", 5)
        self.retry_after_seconds: int = cfg.get("retry_after_seconds", 30)
        self.max_retries: int = cfg.get("max_retries", 3)
        self.max_queue_size: int = cfg.get("max_queue_size", 50)


class QueueStatus:
    """Status snapshot of the gatekeeper queue."""

    def __init__(self, depth: int, total_calls: int, total_retries: int) -> None:
        """Initialize queue status.

        Args:
            depth: Current number of queued requests.
            total_calls: Total API calls made.
            total_retries: Total retries performed.
        """
        self.depth = depth
        self.total_calls = total_calls
        self.total_retries = total_retries


class ApiGatekeeper:
    """Centralized API call manager with rate limiting and retry logic.

    All LLM API calls must go through execute() — never call the API directly.
    Enforces per-minute rate limits and handles transient failures with retries.
    """

    def __init__(self, config: RateLimitConfig) -> None:
        """Initialize gatekeeper with rate limit config.

        Args:
            config: Loaded RateLimitConfig instance.
        """
        self._config = config
        self._call_timestamps: deque[float] = deque()
        self._queue: deque = deque()
        self._total_calls: int = 0
        self._total_retries: int = 0

    def _clean_old_timestamps(self) -> None:
        """Remove timestamps older than 60 seconds from the window."""
        now = time.time()
        while self._call_timestamps and now - self._call_timestamps[0] > 60:
            self._call_timestamps.popleft()

    def _is_rate_limited(self) -> bool:
        """Return True if we have hit the per-minute rate limit."""
        self._clean_old_timestamps()
        return len(self._call_timestamps) >= self._config.requests_per_minute

    def _wait_for_slot(self) -> None:
        """Block until a rate limit slot is available."""
        while self._is_rate_limited():
            wait = self._config.retry_after_seconds
            logger.warning(f"Rate limit reached — waiting {wait}s")
            time.sleep(wait)
            self._clean_old_timestamps()

    def execute(self, api_call: Callable, *args: Any, **kwargs: Any) -> Any:
        """Execute an API call through the gatekeeper.

        Checks rate limits before execution, retries on transient failures,
        and logs all calls for monitoring.

        Args:
            api_call: Callable that makes the API request.
            *args: Positional arguments for the API call.
            **kwargs: Keyword arguments for the API call.

        Returns:
            API response from the callable.

        Raises:
            RuntimeError: If all retries are exhausted.
        """
        self._wait_for_slot()

        last_error: Exception | None = None
        for attempt in range(self._config.max_retries):
            try:
                self._call_timestamps.append(time.time())
                self._total_calls += 1
                logger.info(f"API call #{self._total_calls} (attempt {attempt + 1})")
                return api_call(*args, **kwargs)
            except Exception as e:
                last_error = e
                self._total_retries += 1
                logger.warning(f"API call failed (attempt {attempt + 1}): {e}")
                if attempt < self._config.max_retries - 1:
                    time.sleep(self._config.retry_after_seconds)

        raise RuntimeError(
            f"API call failed after {self._config.max_retries} retries: {last_error}"
        )

    def get_queue_status(self) -> QueueStatus:
        """Return current queue depth and call statistics."""
        return QueueStatus(
            depth=len(self._queue),
            total_calls=self._total_calls,
            total_retries=self._total_retries,
        )
