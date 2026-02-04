# Developer Activity Monitor

A Python-based web monitoring tool that tracks a developer's page and sends email notifications when changes are detected. Designed to run automatically via GitHub Actions.

## Features

- Monitors any web page for content changes
- Email notifications when changes detected
- Runs automatically via GitHub Actions (every 4 hours)
- Optional CSS selector for targeted monitoring
- Zero cost (uses GitHub Actions free tier)

## Quick Start

1. **Fork or clone this repository**

2. **Set up GitHub Secrets** (Settings → Secrets and variables → Actions):
   - `MONITOR_URL` - The URL to monitor
   - `EMAIL_FROM` - Your Gmail address
   - `EMAIL_TO` - Notification recipient email
   - `EMAIL_PASSWORD` - Gmail App Password (see below)

3. **Enable GitHub Actions** (Actions tab → Enable workflows)

4. **Trigger manually** or wait for scheduled run

## GitHub Secrets Configuration

| Secret | Required | Description |
|--------|----------|-------------|
| `MONITOR_URL` | Yes | Full URL of the page to monitor |
| `EMAIL_FROM` | Yes | Gmail address for sending notifications |
| `EMAIL_TO` | Yes | Email address to receive notifications |
| `EMAIL_PASSWORD` | Yes | Gmail App Password |
| `CHECK_SELECTOR` | No | CSS selector to monitor specific element |
| `EMAIL_SMTP_HOST` | No | SMTP server (default: smtp.gmail.com) |
| `EMAIL_SMTP_PORT` | No | SMTP port (default: 465) |

## Getting a Gmail App Password

Regular Gmail passwords won't work with SMTP. You need an App Password:

1. Enable 2-Factor Authentication on your Google account
2. Go to [Google Account](https://myaccount.google.com/) → Security → 2-Step Verification
3. Scroll down and click "App passwords"
4. Generate a new app password for "Mail"
5. Use the 16-character password (without spaces) as `EMAIL_PASSWORD`

## Customization

### Change Check Frequency

Edit the cron expression in `.github/workflows/monitor.yml`:

```yaml
schedule:
  - cron: '0 */4 * * *'  # Every 4 hours (default)
  # - cron: '0 */1 * * *'  # Every hour
  # - cron: '0 9,18 * * *' # At 9 AM and 6 PM
  # - cron: '*/30 * * * *' # Every 30 minutes
```

### Monitor Specific Element

Add `CHECK_SELECTOR` secret with a CSS selector:

- `#releases` - Element with id "releases"
- `.activity-feed` - Element with class "activity-feed"
- `div.content > p` - First paragraph in content div

This is useful to ignore dynamic parts of the page (ads, timestamps, etc.).

## Local Development

```bash
# Clone the repository
git clone https://github.com/yourusername/developer-monitor.git
cd developer-monitor

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your values

# Run locally
python main.py

# Run tests
pytest
```

## Project Structure

```
developer-monitor/
├── .github/workflows/
│   └── monitor.yml       # GitHub Actions workflow
├── src/
│   ├── __init__.py
│   ├── config.py         # Configuration handling
│   ├── monitor.py        # Page monitoring logic
│   └── notifier.py       # Email notifications
├── tests/
│   ├── __init__.py
│   ├── test_monitor.py   # Monitor tests
│   └── test_notifier.py  # Notifier tests
├── .env.example          # Environment template
├── .gitignore
├── main.py               # Entry point
├── README.md
└── requirements.txt
```

## Troubleshooting

### "Authentication failed" email error

- Make sure you're using an App Password, not your regular password
- Verify 2FA is enabled on your Google account
- Check that `EMAIL_FROM` matches the Google account used to generate the App Password

### No notifications received

- Check GitHub Actions logs for errors (Actions tab → Select workflow run)
- Verify `MONITOR_URL` is accessible (try opening in browser)
- Check your spam folder
- Ensure all required secrets are set

### Too many notifications

The page may have dynamic content that changes frequently (timestamps, ads, view counts). Use `CHECK_SELECTOR` to monitor only the relevant section of the page.

### First run doesn't send notification

This is expected behavior. The first run establishes a baseline hash. Subsequent runs will compare against this baseline and notify only when changes occur.

## How It Works

1. **Fetch** - Downloads the web page content
2. **Extract** - Removes dynamic elements (scripts, styles, tracking)
3. **Hash** - Computes SHA256 hash of the cleaned content
4. **Compare** - Checks against previously stored hash
5. **Notify** - Sends email if hash changed
6. **Store** - Saves current hash for next comparison

The hash is persisted between GitHub Actions runs using the cache action.

## License

MIT License
