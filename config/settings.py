"""
Configuration settings for Reddit Scraper
"""
import os
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATABASE_PATH = DATA_DIR / "reddit_scraper.db"

# Ensure data directory exists (may fail on read-only filesystems like Streamlit Cloud)
try:
    DATA_DIR.mkdir(exist_ok=True)
except OSError:
    pass  # Directory might already exist or be read-only

# Database URL
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# Scraping settings
SCRAPE_DELAY_MIN = 2  # seconds between requests
SCRAPE_DELAY_MAX = 5  # random delay up to this

# Reddit URL patterns
REDDIT_SEARCH_URL = "https://www.reddit.com/r/{subreddit}/search/"
REDDIT_SEARCH_PARAMS = "?q={keyword}&type=posts&sort=top&t={timeframe}"

# Time windows for scraping
TIME_WINDOWS = {
    "hour": "Fresh threads (engagement opportunities)",
    "day": "Today's hot topics",
    "week": "This week's trends",
    "month": "Established patterns",
    "year": "Historical/evergreen issues"
}

# Engagement time windows (for finding threads to respond to)
ENGAGEMENT_WINDOWS = ["hour", "day", "week"]

# Research time windows (for trend analysis)
RESEARCH_WINDOWS = ["month", "year"]

# User agents for rotation
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
]

# Subreddit tiers
TIER_1_SUBREDDITS = [
    "onlyfansadvice",
    "Fansly_Advice",
    "onlyfansgirls",
    "onlyfansmodels",
    "onlyfanspromotions",
    "CreatorsAdvice",
    "ContentCreators",
    "AdultContentCreators",
    "NSFWCreators",
    "NSFWbusiness"
]

TIER_2_SUBREDDITS = [
    "ManyVids",
    "ManyvidsCreators",
    "Streamate",
    "Stripchat",
    "Chaturbate",
    "MyFreeCams",
    "Flirt4Free",
    "LoyalFans",
    "Fanvue",
    "Fanfix",
    "JustForFans",
    "Passes",
    "Fansly",
    "Uncove"
]

ALL_SUBREDDITS = TIER_1_SUBREDDITS + TIER_2_SUBREDDITS
