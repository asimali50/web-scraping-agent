"""Application constants and configuration values"""

# Time limits (seconds)
SOFT_TIME_LIMIT = 30
HARD_TIME_LIMIT = 45

# Retry configuration
MAX_RETRIES = 2
RETRY_BACKOFF_FACTOR = 2
INITIAL_RETRY_DELAY = 1

# Search configuration
MAX_GOOGLE_SEARCHES = 3
GOOGLE_SEARCH_DELAY = 2
MAX_GOOGLE_PAGES = 2

# Browser timeouts (milliseconds)
BROWSER_TIMEOUT_MS = 30000
AMAZON_TIMEOUT_MS = 8000
GOOGLE_TIMEOUT_MS = 15000
WEBSITE_TIMEOUT_MS = 5000

# Database configuration
DATABASE_CHECK_INTERVAL = 1
DATABASE_LOCK_TIMEOUT = 10

# Ignored domains (marketplace, social media, etc.)
IGNORED_DOMAINS = {
    "amazon.com",
    "amazon.co.uk",
    "facebook.com",
    "instagram.com",
    "linkedin.com",
    "pinterest.com",
    "youtube.com",
    "reddit.com",
    "wikipedia.org",
    "alibaba.com",
    "aliexpress.com",
    "walmart.com",
    "ebay.com",
    "temu.com",
}

# Status values
STATUS_FOUND = "found"
STATUS_NOT_FOUND = "not_found"
STATUS_NEEDS_REVIEW = "needs_review"
STATUS_AMAZON_FAILED = "amazon_failed"
STATUS_GOOGLE_FAILED = "google_failed"
STATUS_SKIPPED = "skipped"
STATUS_TIMEOUT = "timeout"

# Confidence thresholds
CONFIDENCE_AUTO_SAVE = 95
CONFIDENCE_REVIEW = 80
CONFIDENCE_NOT_FOUND = 80

# User agent string
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# API retry counts
CLAUDE_MAX_RETRIES = 3
SHEETS_MAX_RETRIES = 3

# Logging format
LOG_FORMAT = "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}"
