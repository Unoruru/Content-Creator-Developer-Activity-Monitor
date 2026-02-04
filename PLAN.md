# Project Plan: Developer Activity Monitor

## Project Overview

A Python-based web monitoring tool that tracks a developer's page on a community website and sends email notifications when changes are detected. Designed to run automatically via GitHub Actions.

---

## Directory Structure

```
developer-monitor/
├── .github/
│   └── workflows/
│       └── monitor.yml
├── src/
│   ├── __init__.py
│   ├── monitor.py
│   ├── notifier.py
│   └── config.py
├── tests/
│   ├── __init__.py
│   ├── test_monitor.py
│   └── test_notifier.py
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
└── main.py
```

---

## Implementation Tasks

### Task 1: Project Setup

- Initialize the project structure
- Create `requirements.txt` with dependencies:
  - `requests`
  - `beautifulsoup4`
  - `python-dotenv`
  - `pytest`
- Create `.gitignore` for Python projects:
  - `.env`
  - `__pycache__/`
  - `*.pyc`
  - `last_hash.txt`
  - `.pytest_cache/`
  - `venv/`
- Create `.env.example` as a template for required environment variables

---

### Task 2: Configuration Module (`src/config.py`)

**Purpose:** Centralize all configuration and environment variable handling.

**Required Environment Variables:**

| Variable | Description | Default |
|----------|-------------|---------|
| `MONITOR_URL` | The developer's page URL to watch | (required) |
| `CHECK_SELECTOR` | CSS selector to monitor specific content | `None` (full page) |
| `EMAIL_SMTP_HOST` | SMTP server hostname | `smtp.gmail.com` |
| `EMAIL_SMTP_PORT` | SMTP server port | `465` |
| `EMAIL_FROM` | Sender email address | (required) |
| `EMAIL_TO` | Recipient email address | (required) |
| `EMAIL_PASSWORD` | SMTP password or app password | (required) |
| `HASH_STORAGE_PATH` | Path to store the hash file | `last_hash.txt` |

**Implementation Details:**

- Load environment variables using `python-dotenv`
- Create a `Config` class or dataclass to hold all settings
- Add validation function to ensure all required variables are set
- Raise clear error messages for missing configuration

---

### Task 3: Monitor Module (`src/monitor.py`)

**Purpose:** Handle all web scraping and change detection logic.

**Functions to Implement:**

#### `fetch_page_content(url: str) -> str`
- Make HTTP GET request with proper headers (User-Agent to avoid blocks)
- Set reasonable timeout (30 seconds)
- Handle common HTTP errors gracefully (404, 500, timeout)
- Return page content as string
- Raise custom exception on failure

#### `extract_content(html: str, selector: str | None) -> str`
- If selector is provided, use BeautifulSoup to extract specific element
- If no selector, return full HTML
- Strip dynamic elements that change on every load:
  - Script tags
  - Nonce/CSRF tokens
  - Timestamps
  - Ads/tracking elements
- Return cleaned content string

#### `compute_hash(content: str) -> str`
- Use SHA256 for hash computation
- Return hexadecimal string representation

#### `load_previous_hash(path: str) -> str | None`
- Read hash from file at given path
- Return `None` if file doesn't exist
- Handle file read errors gracefully

#### `save_hash(path: str, hash_value: str) -> None`
- Write hash to file at given path
- Create parent directories if needed

#### `check_for_changes(config: Config) -> tuple[bool, str]`
- Orchestrate the above functions
- Return tuple: `(has_changed: bool, message: str)`
- Message should describe what happened (for logging)

---

### Task 4: Notifier Module (`src/notifier.py`)

**Purpose:** Handle all notification delivery.

**Functions to Implement:**

#### `send_email(config: Config, subject: str, body: str) -> bool`
- Use `smtplib.SMTP_SSL` for secure connection
- Format email using `email.message.EmailMessage`
- Include proper headers (From, To, Subject, Date)
- Return `True` on success, `False` on failure
- Log errors with details (but not sensitive info)

#### `notify_change(config: Config, url: str) -> bool`
- Compose user-friendly email:
  - Subject: `🔔 Developer Update Detected`
  - Body template:
    ```
    A change has been detected on the monitored page.
    
    URL: {url}
    Detected at: {timestamp}
    
    Visit the page to see what's new!
    ```
- Call `send_email` and return result

---

### Task 5: Main Entry Point (`main.py`)

**Purpose:** Orchestrate the monitoring workflow.

**Implementation:**

```python
def main():
    # 1. Load and validate configuration
    # 2. Run change detection
    # 3. If changes detected, send notification
    # 4. Log results to stdout (for GitHub Actions visibility)
    # 5. Exit with appropriate code:
    #    - 0: Success (no change or change notified)
    #    - 1: Error (fetch failed, notification failed, etc.)
```

**Logging Output:**
- Print timestamps and status messages
- Make it clear in logs whether:
  - First run (no previous hash)
  - No changes detected
  - Changes detected and notification sent
  - Any errors occurred

---

### Task 6: GitHub Actions Workflow

**File:** `.github/workflows/monitor.yml`

```yaml
name: Monitor Developer Page

on:
  schedule:
    # Run every 4 hours
    - cron: '0 */4 * * *'
  workflow_dispatch:
    # Allow manual trigger from GitHub UI

jobs:
  monitor:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Restore previous hash
        uses: actions/cache@v4
        with:
          path: last_hash.txt
          key: page-hash-${{ github.run_id }}
          restore-keys: page-hash-
      
      - name: Run monitor
        env:
          MONITOR_URL: ${{ secrets.MONITOR_URL }}
          EMAIL_FROM: ${{ secrets.EMAIL_FROM }}
          EMAIL_TO: ${{ secrets.EMAIL_TO }}
          EMAIL_PASSWORD: ${{ secrets.EMAIL_PASSWORD }}
        run: python main.py
      
      - name: Save hash for next run
        if: always()
        uses: actions/cache/save@v4
        with:
          path: last_hash.txt
          key: page-hash-${{ github.run_id }}
```

**Notes:**
- Cache is used to persist hash between workflow runs
- `restore-keys: page-hash-` ensures we get the most recent hash
- `if: always()` ensures hash is saved even if notification fails

---

### Task 7: Tests

**File:** `tests/test_monitor.py`

Test cases:
- `test_compute_hash_consistency`: Same input produces same hash
- `test_compute_hash_different_input`: Different input produces different hash
- `test_extract_content_with_selector`: Correctly extracts element by CSS selector
- `test_extract_content_full_page`: Returns cleaned HTML when no selector
- `test_load_previous_hash_file_exists`: Reads hash from existing file
- `test_load_previous_hash_file_missing`: Returns None for missing file
- `test_save_hash`: Correctly writes hash to file

**File:** `tests/test_notifier.py`

Test cases:
- `test_email_formatting`: Email has correct structure
- `test_notify_change_message`: Notification contains URL and timestamp
- Mock SMTP to avoid sending real emails in tests

---

### Task 8: Documentation (`README.md`)

**Sections to Include:**

#### Overview
Brief description of what the project does.

#### Features
- Monitors any web page for changes
- Email notifications when changes detected
- Runs automatically via GitHub Actions
- Optional CSS selector for targeted monitoring
- Zero cost (uses GitHub Actions free tier)

#### Quick Start
1. Fork/clone the repository
2. Set up GitHub Secrets
3. Enable GitHub Actions
4. (Optional) Adjust cron schedule

#### GitHub Secrets Configuration

| Secret | Description | How to Get |
|--------|-------------|------------|
| `MONITOR_URL` | URL to monitor | Copy from browser |
| `EMAIL_FROM` | Gmail address | Your Gmail |
| `EMAIL_TO` | Notification recipient | Your email |
| `EMAIL_PASSWORD` | Gmail App Password | See instructions below |

**Getting a Gmail App Password:**
1. Enable 2-Factor Authentication on your Google account
2. Go to Google Account → Security → App passwords
3. Generate a new app password for "Mail"
4. Use this 16-character password (not your regular password)

#### Customization

**Change check frequency:**
Edit the cron expression in `.github/workflows/monitor.yml`:
- `0 */4 * * *` = Every 4 hours
- `0 */1 * * *` = Every hour
- `0 9,18 * * *` = At 9 AM and 6 PM

**Monitor specific element:**
Add `CHECK_SELECTOR` to your secrets with a CSS selector:
- `#releases` = Element with id "releases"
- `.activity-feed` = Element with class "activity-feed"

#### Local Development

```bash
# Clone the repository
git clone https://github.com/yourusername/developer-monitor.git
cd developer-monitor

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your values

# Run locally
python main.py

# Run tests
pytest
```

#### Troubleshooting

**"Authentication failed" email error:**
- Make sure you're using an App Password, not your regular password
- Verify 2FA is enabled on your Google account

**No notifications received:**
- Check GitHub Actions logs for errors
- Verify the MONITOR_URL is accessible
- Check spam folder

**Too many notifications:**
- The page may have dynamic content that changes frequently
- Use `CHECK_SELECTOR` to monitor only the relevant section

---

## GitHub Secrets Summary

| Secret Name | Required | Description |
|-------------|----------|-------------|
| `MONITOR_URL` | Yes | Full URL of the developer's profile/page |
| `EMAIL_FROM` | Yes | Your Gmail address for sending |
| `EMAIL_TO` | Yes | Email address to receive notifications |
| `EMAIL_PASSWORD` | Yes | Gmail App Password |
| `CHECK_SELECTOR` | No | CSS selector for specific element |

---

## Optional Enhancements (Future)

These features can be added later to extend functionality:

- [ ] **Discord/Slack notifications**: Add webhook support as alternative to email
- [ ] **Diff reporting**: Show what specifically changed on the page
- [ ] **Multiple page support**: Monitor several developers/pages
- [ ] **Retry logic**: Add exponential backoff for transient failures
- [ ] **Rate limiting**: Respect target site's robots.txt and rate limits
- [ ] **Content filtering**: Ignore certain types of changes (e.g., view counts)
- [ ] **Telegram bot**: Send notifications via Telegram
- [ ] **Dashboard**: Simple web UI to view monitoring history

---

## Development Workflow with Claude CLI

When implementing this project with Claude CLI, work through the tasks in order:

```bash
# Start in the project directory
cd developer-monitor

# Task 1: Setup
claude "Create the project structure and initial files based on PLAN.md Task 1"

# Task 2: Config
claude "Implement src/config.py based on PLAN.md Task 2"

# Task 3: Monitor
claude "Implement src/monitor.py based on PLAN.md Task 3"

# Task 4: Notifier
claude "Implement src/notifier.py based on PLAN.md Task 4"

# Task 5: Main
claude "Implement main.py based on PLAN.md Task 5"

# Task 6: GitHub Actions
claude "Create the GitHub Actions workflow based on PLAN.md Task 6"

# Task 7: Tests
claude "Write tests based on PLAN.md Task 7"

# Task 8: Documentation
claude "Create README.md based on PLAN.md Task 8"
```

---

## License

MIT License (or your preferred license)
