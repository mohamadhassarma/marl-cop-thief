"""Unit tests for GmailReporter."""

from unittest.mock import MagicMock, patch

import pytest

from cop_thief.services.reporter import GmailReporter


@pytest.fixture
def reporter() -> GmailReporter:
    """Return a GmailReporter instance."""
    return GmailReporter()


@pytest.fixture
def game_results() -> dict:
    """Sample game results dict."""
    return {
        "group_name": "TestGroup",
        "cop_mcp_url": "http://localhost:8001",
        "thief_mcp_url": "http://localhost:8002",
        "timezone": "Asia/Jerusalem",
        "sub_games": [
            {
                "sub_game_index": 0,
                "result": "cop_win",
                "moves_taken": 10,
                "cop_score": 20,
                "thief_score": 5,
            }
        ],
        "totals": {"cop": 20, "thief": 5}
    }


@pytest.fixture
def bonus_results() -> dict:
    """Sample bonus game results dict."""
    return {
        "report_type": "bonus_game",
        "groups": {"group_1": "Alpha", "group_2": "Beta"},
        "sub_games": [],
        "totals_by_group": {"Alpha": 60, "Beta": 40},
        "bonus_claim": {"Alpha": 10, "Beta": 7},
        "mutual_agreement": True
    }


class TestValidateReportJson:
    """Tests for JSON validation."""

    def test_valid_dict(self, reporter, game_results):
        """Valid dict passes JSON validation."""
        assert reporter.validate_report_json(game_results) is True

    def test_empty_dict(self, reporter):
        """Empty dict is valid JSON."""
        assert reporter.validate_report_json({}) is True

    def test_non_serializable(self, reporter):
        """Dict with non-serializable value fails validation."""
        assert reporter.validate_report_json({"key": object()}) is False


class TestBuildMessage:
    """Tests for email message building."""

    def test_builds_message(self, reporter):
        """Message dict contains raw key."""
        msg = reporter._build_message("Test Subject", '{"key": "value"}')
        assert "raw" in msg
        assert isinstance(msg["raw"], str)

    def test_message_is_base64(self, reporter):
        """Raw message is valid base64."""
        import base64
        msg = reporter._build_message("Subject", "body")
        decoded = base64.urlsafe_b64decode(msg["raw"])
        assert len(decoded) > 0


class TestSendGameReport:
    """Tests for send_game_report method."""

    def test_returns_false_on_missing_token(self, reporter, game_results):
        """Returns False when token file is missing."""
        with patch.object(reporter, "_get_service",
                          side_effect=FileNotFoundError("No token")):
            result = reporter.send_game_report(game_results)
        assert result is False

    def test_returns_true_on_success(self, reporter, game_results):
        """Returns True when email is sent successfully."""
        mock_service = MagicMock()
        mock_service.users().messages().send().execute.return_value = {"id": "123"}
        with patch.object(reporter, "_get_service", return_value=mock_service):
            result = reporter.send_game_report(game_results)
        assert result is True


class TestSendBonusReport:
    """Tests for send_bonus_report method."""

    def test_returns_false_on_error(self, reporter, bonus_results):
        """Returns False when sending fails."""
        with patch.object(reporter, "_get_service",
                          side_effect=RuntimeError("API error")):
            result = reporter.send_bonus_report(bonus_results)
        assert result is False

    def test_returns_true_on_success(self, reporter, bonus_results):
        """Returns True when bonus report is sent."""
        mock_service = MagicMock()
        mock_service.users().messages().send().execute.return_value = {"id": "456"}
        with patch.object(reporter, "_get_service", return_value=mock_service):
            result = reporter.send_bonus_report(bonus_results)
        assert result is True
