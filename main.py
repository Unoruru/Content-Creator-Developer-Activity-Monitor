#!/usr/bin/env python3
"""Developer Activity Monitor - Main entry point.

Monitors a web page for changes and sends email notifications when detected.
"""

import sys
from datetime import datetime

from src.config import Config, ConfigError, load_config, validate_config
from src.monitor import MonitorError, check_for_changes
from src.notifier import notify_change


def log(message: str) -> None:
    """Print a timestamped log message."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")


def main() -> int:
    """Run the monitoring workflow.

    Returns:
        Exit code: 0 for success, 1 for error.
    """
    log("Starting Developer Activity Monitor")

    # Load and validate configuration
    try:
        config = load_config()
        validate_config(config)
        log(f"Monitoring URL: {config.monitor_url}")
    except ConfigError as e:
        log(f"Configuration error: {e}")
        return 1

    # Check for changes
    try:
        has_changed, message = check_for_changes(config)
        log(message)
    except MonitorError as e:
        log(f"Monitor error: {e}")
        return 1

    # Send notification if changes detected
    if has_changed:
        log("Sending notification email...")
        if notify_change(config, config.monitor_url):
            log("Notification sent successfully")
        else:
            log("Failed to send notification")
            return 1
    else:
        log("No notification needed")

    log("Monitor completed successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
