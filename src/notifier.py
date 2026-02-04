"""Notifier module for sending email notifications."""

import smtplib
import ssl
from datetime import datetime
from email.message import EmailMessage

from .config import Config


class NotifierError(Exception):
    """Raised when notification operations fail."""
    pass


def send_email(config: Config, subject: str, body: str) -> bool:
    """Send an email notification.

    Args:
        config: The application configuration.
        subject: Email subject line.
        body: Email body text.

    Returns:
        True if email sent successfully, False otherwise.
    """
    msg = EmailMessage()
    msg["From"] = config.email_from
    msg["To"] = config.email_to
    msg["Subject"] = subject
    msg.set_content(body)

    context = ssl.create_default_context()

    try:
        with smtplib.SMTP_SSL(
            config.email_smtp_host,
            config.email_smtp_port,
            context=context
        ) as server:
            server.login(config.email_from, config.email_password)
            server.send_message(msg)
        return True
    except smtplib.SMTPAuthenticationError:
        print("ERROR: SMTP authentication failed. Check your email and password.")
        print("       If using Gmail, ensure you're using an App Password.")
        return False
    except smtplib.SMTPException as e:
        print(f"ERROR: Failed to send email: {e}")
        return False
    except Exception as e:
        print(f"ERROR: Unexpected error sending email: {e}")
        return False


def notify_change(config: Config, url: str) -> bool:
    """Send a change notification email.

    Args:
        config: The application configuration.
        url: The URL that changed.

    Returns:
        True if notification sent successfully, False otherwise.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    subject = "🔔 Developer Update Detected"

    body = f"""A change has been detected on the monitored page.

URL: {url}
Detected at: {timestamp}

Visit the page to see what's new!
"""

    return send_email(config, subject, body)
