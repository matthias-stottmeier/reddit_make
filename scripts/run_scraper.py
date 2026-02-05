#!/usr/bin/env python3
"""
Run the Reddit scraper to collect posts
"""
import sys
import asyncio
import argparse
from pathlib import Path
from datetime import datetime, timezone

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.collectors.reddit_scraper import RedditScraper
from src.database.connection import session_scope
from src.database.models import Post, Subreddit, Keyword
from config.settings import TIME_WINDOWS, ENGAGEMENT_WINDOWS, RESEARCH_WINDOWS
from config.keywords import PRIORITY_SEARCH_KEYWORDS


async def run_scraper(
    subreddits: list[str] = None,
    keywords: list[str] = None,
    timeframes: list[str] = None,
    mode: str = "all",
    headless: bool = True,
    limit: int = None
):
    """
    Run the scraper for specified subreddits, keywords, and timeframes

    Args:
        subreddits: List of subreddits to scrape (None = all active)
        keywords: List of keywords to search (None = priority keywords)
        timeframes: List of timeframes (None = based on mode)
        mode: 'engagement', 'research', or 'all'
        headless: Run browser without GUI
        limit: Limit number of subreddits to process (for testing)
    """
    # Get active subreddits from database
    with session_scope() as session:
        if subreddits:
            db_subreddits = session.query(Subreddit).filter(
                Subreddit.name.in_(subreddits),
                Subreddit.is_active == True
            ).all()
        else:
            db_subreddits = session.query(Subreddit).filter(
                Subreddit.is_active == True
            ).all()

        subreddit_names = [s.name for s in db_subreddits]

    if limit:
        subreddit_names = subreddit_names[:limit]

    # Set keywords
    if keywords is None:
        keywords = PRIORITY_SEARCH_KEYWORDS

    # Set timeframes based on mode
    if timeframes is None:
        if mode == "engagement":
            timeframes = ENGAGEMENT_WINDOWS
        elif mode == "research":
            timeframes = RESEARCH_WINDOWS
        else:
            timeframes = list(TIME_WINDOWS.keys())

    print(f"\n{'='*60}")
    print(f"REDDIT SCRAPER - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    print(f"Mode: {mode}")
    print(f"Subreddits: {len(subreddit_names)}")
    print(f"Keywords: {len(keywords)}")
    print(f"Timeframes: {timeframes}")
    print(f"Headless: {headless}")
    print(f"{'='*60}\n")

    total_posts = 0
    new_posts = 0
    updated_posts = 0

    async with RedditScraper(headless=headless) as scraper:
        for subreddit in subreddit_names:
            print(f"\n[{subreddit}]")

            for keyword in keywords:
                for timeframe in timeframes:
                    # Scrape posts
                    posts = await scraper.scrape_search_results(
                        subreddit=subreddit,
                        keyword=keyword,
                        timeframe=timeframe
                    )

                    # Save to database
                    saved, updated = save_posts(posts)
                    new_posts += saved
                    updated_posts += updated
                    total_posts += len(posts)

                    # Delay between requests
                    await scraper.random_delay()

            # Update subreddit last_scraped
            with session_scope() as session:
                sub = session.query(Subreddit).filter(Subreddit.name == subreddit).first()
                if sub:
                    sub.last_scraped = datetime.now(timezone.utc)

    print(f"\n{'='*60}")
    print(f"SCRAPING COMPLETE")
    print(f"{'='*60}")
    print(f"Total posts found: {total_posts}")
    print(f"New posts saved: {new_posts}")
    print(f"Posts updated: {updated_posts}")
    print(f"{'='*60}\n")


def save_posts(posts: list[dict]) -> tuple[int, int]:
    """
    Save posts to database, handling duplicates

    Args:
        posts: List of post dictionaries

    Returns:
        Tuple of (new_posts_count, updated_posts_count)
    """
    new_count = 0
    updated_count = 0

    with session_scope() as session:
        for post_data in posts:
            platform_id = post_data.get("platform_id")
            if not platform_id:
                continue

            # Check if post exists
            existing = session.query(Post).filter(Post.platform_id == platform_id).first()

            if existing:
                # Update metrics
                existing.upvotes = post_data.get("upvotes", existing.upvotes)
                existing.num_comments = post_data.get("num_comments", existing.num_comments)
                existing.last_updated = datetime.now(timezone.utc)
                updated_count += 1
            else:
                # Create new post
                new_post = Post(
                    platform_id=platform_id,
                    subreddit=post_data.get("subreddit", ""),
                    title=post_data.get("title", ""),
                    author=post_data.get("author", "[deleted]"),
                    permalink=post_data.get("permalink", ""),
                    upvotes=post_data.get("upvotes", 0),
                    num_comments=post_data.get("num_comments", 0),
                    flair=post_data.get("flair", ""),
                    search_keyword=post_data.get("search_keyword", ""),
                    search_timeframe=post_data.get("search_timeframe", "month"),
                    collected_at=datetime.now(timezone.utc),
                )

                # Parse created_utc if available
                created_str = post_data.get("created_utc")
                if created_str:
                    try:
                        new_post.created_utc = datetime.fromisoformat(created_str.replace('Z', '+00:00'))
                    except:
                        pass

                session.add(new_post)
                new_count += 1

    return new_count, updated_count


def main():
    parser = argparse.ArgumentParser(description="Run Reddit Scraper")
    parser.add_argument(
        "--mode", "-m",
        choices=["engagement", "research", "all"],
        default="all",
        help="Scraping mode: engagement (hour/day/week), research (month/year), or all"
    )
    parser.add_argument(
        "--subreddits", "-s",
        nargs="+",
        help="Specific subreddits to scrape"
    )
    parser.add_argument(
        "--keywords", "-k",
        nargs="+",
        help="Specific keywords to search"
    )
    parser.add_argument(
        "--timeframes", "-t",
        nargs="+",
        choices=list(TIME_WINDOWS.keys()),
        help="Specific timeframes to use"
    )
    parser.add_argument(
        "--no-headless",
        action="store_true",
        help="Run browser with GUI (visible)"
    )
    parser.add_argument(
        "--limit", "-l",
        type=int,
        help="Limit number of subreddits (for testing)"
    )

    args = parser.parse_args()

    # Run the async scraper
    asyncio.run(run_scraper(
        subreddits=args.subreddits,
        keywords=args.keywords,
        timeframes=args.timeframes,
        mode=args.mode,
        headless=not args.no_headless,
        limit=args.limit
    ))


if __name__ == "__main__":
    main()
