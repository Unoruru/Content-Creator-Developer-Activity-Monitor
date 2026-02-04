"""Tests for the notifier module."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from src.config import Config
from src.notifier import notify_change, send_email


@pytest.fixture
def mock_config():
    """Create a mock configuration for testing."""
    return Config(
        monitor_url="https://example.com/developer",
        email_from="sender@example.com",
        email_to="recipient@example.com",
        email_password="test_password",
        email_smtp_host="smtp.example.com",
        email_smtp_port=465,
    )


class TestSendEmail:
    """Tests for send_email function."""

    @patch("src.notifier.smtplib.SMTP_SSL")
    def test_successful_send(self, mock_smtp_class, mock_config):
        """Should return True on successful send."""
        mock_server = MagicMock()
        mock_smtp_class.return_value.__enter__.return_value = mock_server

        result = send_email(mock_config, "Test Subject", "Test Body")

        assert result is True
        mock_server.login.assert_called_once_with(
            mock_config.email_from, mock_config.email_password
        )
        mock_server.send_message.assert_called_once()

    @patch("src.notifier.smtplib.SMTP_SSL")
    def test_authentication_error(self, mock_smtp_class, mock_config, capsys):
        """Should return False and log error on auth failure."""
        import smtplib

        mock_smtp_class.return_value.__enter__.side_effect = (
            smtplib.SMTPAuthenticationError(535, b"Auth failed")
        )

        result = send_email(mock_config, "Test Subject", "Test Body")

        assert result is False
        captured = capsys.readouterr()
        assert "authentication failed" in captured.out.lower()

    @patch("src.notifier.smtplib.SMTP_SSL")
    def test_smtp_error(self, mock_smtp_class, mock_config, capsys):
        """Should return False and log error on SMTP failure."""
        import smtplib

        mock_smtp_class.return_value.__enter__.side_effect = (
            smtplib.SMTPException("Connection refused")
        )

        result = send_email(mock_config, "Test Subject", "Test Body")

        assert result is False
        captured = capsys.readouterr()
        assert "error" in captured.out.lower()

    @patch("src.notifier.smtplib.SMTP_SSL")
    def test_email_structure(self, mock_smtp_class, mock_config):
        """Should create email with correct structure."""
        mock_server = MagicMock()
        mock_smtp_class.return_value.__enter__.return_value = mock_server

        send_email(mock_config, "Test Subject", "Test Body")

        # Get the message that was sent
        call_args = mock_server.send_message.call_args
        msg = call_args[0][0]

        assert msg["From"] == mock_config.email_from
        assert msg["To"] == mock_config.email_to
        assert msg["Subject"] == "Test Subject"
        assert "Test Body" in msg.get_content()


class TestNotifyChange:
    """Tests for notify_change function."""

    @patch("src.notifier.send_email")
    def test_calls_send_email(self, mock_send_email, mock_config):
        """Should call send_email with correct parameters."""
        mock_send_email.return_value = True

        result = notify_change(mock_config, "https://example.com/page")

        assert result is True
        mock_send_email.assert_called_once()

        # Check the call arguments
        call_args = mock_send_email.call_args
        config_arg = call_args[0][0]
        subject_arg = call_args[0][1]
        body_arg = call_args[0][2]

        assert config_arg == mock_config
        assert "Update Detected" in subject_arg
        assert "https://example.com/page" in body_arg

    @patch("src.notifier.send_email")
    def test_includes_timestamp(self, mock_send_email, mock_config):
        """Should include timestamp in notification body."""
        mock_send_email.return_value = True

        notify_change(mock_config, "https://example.com/page")

        body_arg = mock_send_email.call_args[0][2]
        # Should contain a date-like pattern
        assert "Detected at:" in body_arg

    @patch("src.notifier.send_email")
    def test_returns_send_email_result(self, mock_send_email, mock_config):
        """Should return whatever send_email returns."""
        mock_send_email.return_value = False

        result = notify_change(mock_config, "https://example.com/page")

        assert result is False
