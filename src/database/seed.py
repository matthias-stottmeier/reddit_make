"""
Seed the database with initial keywords and subreddits
"""
from datetime import datetime, timezone

import sys
sys.path.insert(0, str(__file__).rsplit('/', 3)[0])

from src.database.connection import session_scope
from src.database.models import Keyword, Subreddit, Settings
from config.keywords import (
    PAIN_KEYWORDS, COMPLIANCE_KEYWORDS, SWITCH_KEYWORDS, FEE_KEYWORDS,
    PAYMENT_PROVIDERS, MAINSTREAM_BANKS, WALLETS, PLATFORMS,
    KEYWORD_WEIGHTS
)
from config.settings import TIER_1_SUBREDDITS, TIER_2_SUBREDDITS


def seed_initial_data():
    """Seed the database with initial configuration"""
    with session_scope() as session:
        # Check if already seeded
        existing = session.query(Keyword).first()
        if existing:
            print("Database already seeded, skipping...")
            return

        print("Seeding database with initial data...")

        # Seed keywords
        _seed_keywords(session)

        # Seed subreddits
        _seed_subreddits(session)

        # Seed default settings
        _seed_settings(session)

        print("Seeding complete!")


def _seed_keywords(session):
    """Seed keyword data"""
    keywords_to_add = []

    # Pain keywords
    for kw in PAIN_KEYWORDS:
        keywords_to_add.append(Keyword(
            keyword=kw,
            category="pain",
            weight=KEYWORD_WEIGHTS["pain"],
            is_active=True
        ))

    # Compliance keywords
    for kw in COMPLIANCE_KEYWORDS:
        keywords_to_add.append(Keyword(
            keyword=kw,
            category="compliance",
            weight=KEYWORD_WEIGHTS["compliance"],
            is_active=True
        ))

    # Switch keywords
    for kw in SWITCH_KEYWORDS:
        keywords_to_add.append(Keyword(
            keyword=kw,
            category="switch",
            weight=KEYWORD_WEIGHTS["switch"],
            is_active=True
        ))

    # Fee keywords
    for kw in FEE_KEYWORDS:
        keywords_to_add.append(Keyword(
            keyword=kw,
            category="fee",
            weight=KEYWORD_WEIGHTS["fee"],
            is_active=True
        ))

    # Payment providers
    for kw in PAYMENT_PROVIDERS:
        keywords_to_add.append(Keyword(
            keyword=kw,
            category="banking",
            subcategory="payment_provider",
            weight=KEYWORD_WEIGHTS["banking"],
            is_active=True
        ))

    # Banks
    for kw in MAINSTREAM_BANKS:
        keywords_to_add.append(Keyword(
            keyword=kw,
            category="banking",
            subcategory="bank",
            weight=KEYWORD_WEIGHTS["banking"],
            is_active=True
        ))

    # Wallets
    for kw in WALLETS:
        keywords_to_add.append(Keyword(
            keyword=kw,
            category="banking",
            subcategory="wallet",
            weight=KEYWORD_WEIGHTS["banking"],
            is_active=True
        ))

    # Platforms
    for kw in PLATFORMS:
        keywords_to_add.append(Keyword(
            keyword=kw,
            category="platform",
            platform_name=kw,
            weight=KEYWORD_WEIGHTS["platform"],
            is_active=True
        ))

    session.add_all(keywords_to_add)
    print(f"  Added {len(keywords_to_add)} keywords")


def _seed_subreddits(session):
    """Seed subreddit data"""
    subreddits_to_add = []

    # Tier 1 subreddits
    for sub in TIER_1_SUBREDDITS:
        subreddits_to_add.append(Subreddit(
            name=sub,
            tier=1,
            description="Direct creator monetization (high signal)",
            is_active=True
        ))

    # Tier 2 subreddits
    for sub in TIER_2_SUBREDDITS:
        subreddits_to_add.append(Subreddit(
            name=sub,
            tier=2,
            description="Platform-specific & camming",
            is_active=True
        ))

    session.add_all(subreddits_to_add)
    print(f"  Added {len(subreddits_to_add)} subreddits")


def _seed_settings(session):
    """Seed default settings"""
    default_settings = [
        Settings(
            key="scrape_delay_min",
            value=2,
            description="Minimum delay between scrape requests (seconds)"
        ),
        Settings(
            key="scrape_delay_max",
            value=5,
            description="Maximum delay between scrape requests (seconds)"
        ),
        Settings(
            key="engagement_schedule_hours",
            value=4,
            description="Hours between engagement window scrapes (hour/day/week)"
        ),
        Settings(
            key="research_schedule_hours",
            value=24,
            description="Hours between research window scrapes (month/year)"
        ),
        Settings(
            key="max_posts_per_search",
            value=25,
            description="Maximum posts to collect per search query"
        ),
        Settings(
            key="pain_score_threshold",
            value=5.0,
            description="Pain score threshold for highlighting posts"
        ),
        Settings(
            key="switch_intent_threshold",
            value=3.0,
            description="Switch intent threshold for opportunities"
        ),
    ]

    session.add_all(default_settings)
    print(f"  Added {len(default_settings)} default settings")


if __name__ == "__main__":
    seed_initial_data()
