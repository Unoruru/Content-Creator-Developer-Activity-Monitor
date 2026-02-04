"""Monitor module for web page change detection."""

import hashlib
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from .config import Config


class MonitorError(Exception):
    """Raised when monitoring operations fail."""
    pass


def fetch_page_content(url: str, timeout: int = 30) -> str:
    """Fetch the content of a web page.

    Args:
        url: The URL to fetch.
        timeout: Request timeout in seconds.

    Returns:
        The page content as a string.

    Raises:
        MonitorError: If the request fails.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }

    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response.text
    except requests.exceptions.Timeout:
        raise MonitorError(f"Request timed out after {timeout} seconds")
    except requests.exceptions.HTTPError as e:
        raise MonitorError(f"HTTP error {e.response.status_code}: {e.response.reason}")
    except requests.exceptions.ConnectionError:
        raise MonitorError(f"Failed to connect to {url}")
    except requests.exceptions.RequestException as e:
        raise MonitorError(f"Request failed: {e}")


def extract_content(html: str, selector: str | None = None) -> str:
    """Extract and clean content from HTML.

    Args:
        html: The raw HTML content.
        selector: Optional CSS selector to extract specific element.

    Returns:
        Cleaned content string.

    Raises:
        MonitorError: If selector doesn't match any element.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Remove dynamic elements that change on every load
    for tag in soup.find_all(["script", "style", "noscript", "iframe"]):
        tag.decompose()

    # Remove elements commonly used for tracking/ads
    for tag in soup.find_all(attrs={"class": re.compile(r"ad|tracking|analytics", re.I)}):
        tag.decompose()

    # Remove elements with dynamic attributes
    for tag in soup.find_all(attrs={"data-timestamp": True}):
        tag.decompose()
    for tag in soup.find_all(attrs={"data-nonce": True}):
        tag.decompose()

    # If selector provided, extract specific element
    if selector:
        element = soup.select_one(selector)
        if element is None:
            raise MonitorError(f"Selector '{selector}' did not match any element")
        content = element.get_text(separator=" ", strip=True)
    else:
        content = soup.get_text(separator=" ", strip=True)

    # Normalize whitespace
    content = re.sub(r"\s+", " ", content).strip()

    return content


def compute_hash(content: str) -> str:
    """Compute SHA256 hash of content.

    Args:
        content: The content to hash.

    Returns:
        Hexadecimal hash string.
    """
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def load_previous_hash(path: str) -> str | None:
    """Load the previous hash from file.

    Args:
        path: Path to the hash file.

    Returns:
        The previous hash, or None if file doesn't exist.
    """
    try:
        hash_path = Path(path)
        if hash_path.exists():
            return hash_path.read_text().strip()
        return None
    except (IOError, OSError):
        return None


def save_hash(path: str, hash_value: str) -> None:
    """Save hash to file.

    Args:
        path: Path to the hash file.
        hash_value: The hash to save.
    """
    hash_path = Path(path)
    hash_path.parent.mkdir(parents=True, exist_ok=True)
    hash_path.write_text(hash_value)


def check_for_changes(config: Config) -> tuple[bool, str]:
    """Check if the monitored page has changed.

    Args:
        config: The application configuration.

    Returns:
        Tuple of (has_changed, message).
        - has_changed: True if page content changed.
        - message: Description of what happened (for logging).

    Raises:
        MonitorError: If monitoring fails.
    """
    # Fetch and process page content
    html = fetch_page_content(config.monitor_url)
    content = extract_content(html, config.check_selector)
    current_hash = compute_hash(content)

    # Compare with previous hash
    previous_hash = load_previous_hash(config.hash_storage_path)

    if previous_hash is None:
        # First run - save hash and report no change
        save_hash(config.hash_storage_path, current_hash)
        return False, "First run - baseline hash saved"

    if current_hash == previous_hash:
        return False, "No changes detected"

    # Change detected - save new hash
    save_hash(config.hash_storage_path, current_hash)
    return True, "Change detected on monitored page"
