"""Configuration module for the Developer Activity Monitor."""

import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv


@dataclass
class Config:
    """Configuration settings for the monitor."""

    # Required settings
    monitor_url: str
    email_from: str
    email_to: str
    email_password: str

    # Optional settings with defaults
    check_selector: str | None = None
    email_smtp_host: str = "smtp.gmail.com"
    email_smtp_port: int = 465
    hash_storage_path: str = "last_hash.txt"


class ConfigError(Exception):
    """Raised when configuration is invalid or missing."""
    pass


def load_config() -> Config:
    """Load configuration from environment variables.

    Returns:
        Config: The loaded configuration.

    Raises:
        ConfigError: If required environment variables are missing.
    """
    # Load .env file if it exists
    load_dotenv()

    # Required variables
    required_vars = ["MONITOR_URL", "EMAIL_FROM", "EMAIL_TO", "EMAIL_PASSWORD"]
    missing = [var for var in required_vars if not os.getenv(var)]

    if missing:
        raise ConfigError(
            f"Missing required environment variables: {', '.join(missing)}"
        )

    # Parse optional selector (empty string means None)
    check_selector = os.getenv("CHECK_SELECTOR", "").strip() or None

    # Parse SMTP port with validation
    smtp_port_str = os.getenv("EMAIL_SMTP_PORT", "465")
    try:
        smtp_port = int(smtp_port_str)
    except ValueError:
        raise ConfigError(f"Invalid EMAIL_SMTP_PORT value: {smtp_port_str}")

    return Config(
        monitor_url=os.getenv("MONITOR_URL", ""),
        email_from=os.getenv("EMAIL_FROM", ""),
        email_to=os.getenv("EMAIL_TO", ""),
        email_password=os.getenv("EMAIL_PASSWORD", ""),
        check_selector=check_selector,
        email_smtp_host=os.getenv("EMAIL_SMTP_HOST", "smtp.gmail.com"),
        email_smtp_port=smtp_port,
        hash_storage_path=os.getenv("HASH_STORAGE_PATH", "last_hash.txt"),
    )


def validate_config(config: Config) -> None:
    """Validate the configuration values.

    Args:
        config: The configuration to validate.

    Raises:
        ConfigError: If any configuration value is invalid.
    """
    # Validate URL format (basic check)
    if not config.monitor_url.startswith(("http://", "https://")):
        raise ConfigError(
            f"Invalid MONITOR_URL: must start with http:// or https://"
        )

    # Validate email addresses (basic check)
    if "@" not in config.email_from:
        raise ConfigError(f"Invalid EMAIL_FROM: must be a valid email address")

    if "@" not in config.email_to:
        raise ConfigError(f"Invalid EMAIL_TO: must be a valid email address")

    # Validate SMTP port range
    if not (1 <= config.email_smtp_port <= 65535):
        raise ConfigError(
            f"Invalid EMAIL_SMTP_PORT: must be between 1 and 65535"
        )
