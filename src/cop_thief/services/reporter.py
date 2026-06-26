"""Reporter — sends automated JSON game report via Gmail API."""

import base64
import json
import logging
import os
from email.mime.text import MIMEText
from pathlib import Path

logger = logging.getLogger(__name__)


class GmailReporter:
    """Sends game results as JSON-only email via Gmail OAuth API.

    Requires pre-generated OAuth token at GMAIL_TOKEN_PATH.
    Email body contains only valid JSON — no free text.
    """

    def __init__(self) -> None:
        """Initialize reporter with OAuth credentials from env."""
        self._token_path = os.environ.get(
            "GMAIL_TOKEN_PATH", "config/gmail_token.json"
        )
        self._credentials_path = os.environ.get(
            "GMAIL_CREDENTIALS_PATH", "config/gmail_credentials.json"
        )
        self._target = os.environ.get(
            "REPORT_EMAIL", "rmisegal+uoh26b@gmail.com"
        )

    def _get_service(self):
        """Build and return authenticated Gmail API service.

        Returns:
            Authenticated Gmail API resource.

        Raises:
            FileNotFoundError: If token file does not exist.
            RuntimeError: If authentication fails.
        """
        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build

            if not Path(self._token_path).exists():
                raise FileNotFoundError(
                    f"Gmail token not found at {self._token_path}. "
                    "Run OAuth flow first."
                )
            creds = Credentials.from_authorized_user_file(
                self._token_path,
                ["https://www.googleapis.com/auth/gmail.send"]
            )
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
                with open(self._token_path, "w") as f:
                    f.write(creds.to_json())

            return build("gmail", "v1", credentials=creds)
        except ImportError as e:
            raise RuntimeError(
                "Google API libraries not installed. "
                "Run: uv add google-auth google-auth-httplib2 google-api-python-client"
            ) from e

    def _build_message(self, subject: str, body: str) -> dict:
        """Build a base64-encoded email message.

        Args:
            subject: Email subject line.
            body: JSON string for email body.

        Returns:
            Dict with 'raw' key containing encoded message.
        """
        message = MIMEText(body, "plain")
        message["to"] = self._target
        message["subject"] = subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        return {"raw": raw}

    def send_game_report(self, game_results: dict) -> bool:
        """Send internal game report email.

        Args:
            game_results: Full game result dict from SDK.run_full_game().

        Returns:
            True if email sent successfully, False otherwise.
        """
        try:
            service = self._get_service()
            group = game_results.get("group_name", "unknown")
            subject = f"EX06 Game Report — {group}"
            body = json.dumps(game_results, indent=2)
            message = self._build_message(subject, body)
            service.users().messages().send(
                userId="me", body=message
            ).execute()
            logger.info(f"Game report sent to {self._target}")
            return True
        except Exception as e:
            logger.error(f"Failed to send game report: {e}")
            return False

    def send_bonus_report(self, bonus_results: dict) -> bool:
        """Send inter-group bonus game report email.

        Args:
            bonus_results: Bonus game result dict with report_type field.

        Returns:
            True if email sent successfully, False otherwise.
        """
        try:
            service = self._get_service()
            g1 = bonus_results.get("groups", {}).get("group_1", "unknown")
            g2 = bonus_results.get("groups", {}).get("group_2", "unknown")
            subject = f"EX06 Bonus Report — {g1} vs {g2}"
            body = json.dumps(bonus_results, indent=2)
            message = self._build_message(subject, body)
            service.users().messages().send(
                userId="me", body=message
            ).execute()
            logger.info(f"Bonus report sent to {self._target}")
            return True
        except Exception as e:
            logger.error(f"Failed to send bonus report: {e}")
            return False

    def validate_report_json(self, report: dict) -> bool:
        """Validate that report dict is JSON-serializable.

        Args:
            report: Report dict to validate.

        Returns:
            True if valid JSON, False otherwise.
        """
        try:
            json.dumps(report)
            return True
        except (TypeError, ValueError):
            return False
