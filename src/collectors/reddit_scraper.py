"""
Reddit Web Scraper using Playwright
Scrapes Reddit search results without needing API access
"""
import asyncio
import json
import random
import re
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import quote_plus

from playwright.async_api import async_playwright, Page, Browser
from bs4 import BeautifulSoup

import sys
sys.path.insert(0, str(__file__).rsplit('/', 3)[0])

from config.settings import (
    REDDIT_SEARCH_URL,
    REDDIT_SEARCH_PARAMS,
    SCRAPE_DELAY_MIN,
    SCRAPE_DELAY_MAX,
    USER_AGENTS,
    TIME_WINDOWS,
)


class RedditScraper:
    """
    Scrapes Reddit search results using Playwright for JS rendering
    """

    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self._playwright = None

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def start(self):
        """Initialize the browser"""
        self._playwright = await async_playwright().start()
        self.browser = await self._playwright.chromium.launch(headless=self.headless)
        context = await self.browser.new_context(
            user_agent=random.choice(USER_AGENTS),
            viewport={"width": 1920, "height": 1080},
        )
        self.page = await context.new_page()

    async def close(self):
        """Close the browser"""
        if self.browser:
            await self.browser.close()
        if self._playwright:
            await self._playwright.stop()

    def build_search_url(self, subreddit: str, keyword: str, timeframe: str = "month") -> str:
        """
        Build Reddit search URL

        Args:
            subreddit: Subreddit name (without r/)
            keyword: Search keyword
            timeframe: hour, day, week, month, year

        Returns:
            Full search URL
        """
        base = REDDIT_SEARCH_URL.format(subreddit=subreddit)
        params = REDDIT_SEARCH_PARAMS.format(
            keyword=quote_plus(keyword),
            timeframe=timeframe
        )
        return base + params

    async def scrape_search_results(
        self,
        subreddit: str,
        keyword: str,
        timeframe: str = "month",
        max_posts: int = 25
    ) -> list[dict]:
        """
        Scrape search results for a subreddit + keyword combination

        Args:
            subreddit: Subreddit to search in
            keyword: Keyword to search for
            timeframe: Time filter (hour, day, week, month, year)
            max_posts: Maximum number of posts to collect

        Returns:
            List of post dictionaries
        """
        url = self.build_search_url(subreddit, keyword, timeframe)
        print(f"  Scraping: r/{subreddit} | '{keyword}' | {timeframe}")

        try:
            # Navigate to search page
            await self.page.goto(url, wait_until="domcontentloaded", timeout=30000)

            # Wait for content to load
            await asyncio.sleep(3)

            # Handle cookie consent if present
            try:
                cookie_button = await self.page.query_selector('button:has-text("Accept")')
                if cookie_button:
                    await cookie_button.click()
                    await asyncio.sleep(1)
            except:
                pass

            # Scroll to load more posts
            for _ in range(2):
                await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(1)

            # Get page content
            html = await self.page.content()
            posts = self._parse_search_results(html, subreddit, keyword, timeframe)

            print(f"    Found {len(posts)} posts")
            return posts[:max_posts]

        except Exception as e:
            print(f"    Error scraping r/{subreddit}: {e}")
            return []

    def _parse_search_results(
        self,
        html: str,
        subreddit: str,
        keyword: str,
        timeframe: str
    ) -> list[dict]:
        """
        Parse HTML to extract post data from search-telemetry-tracker elements

        Args:
            html: Page HTML content
            subreddit: Source subreddit
            keyword: Search keyword used
            timeframe: Time filter used

        Returns:
            List of post dictionaries
        """
        soup = BeautifulSoup(html, 'lxml')
        posts = []
        seen_ids = set()

        # Find all search-telemetry-tracker elements with post data
        trackers = soup.find_all('search-telemetry-tracker', attrs={'data-faceplate-tracking-context': True})

        for tracker in trackers:
            try:
                # Parse the JSON data from the attribute
                context_str = tracker.get('data-faceplate-tracking-context', '{}')
                context = json.loads(context_str)

                # Check if this is a post tracker (has post data)
                post_data = context.get('post')
                if not post_data:
                    continue

                post_id = post_data.get('id', '')
                if not post_id or post_id in seen_ids:
                    continue

                seen_ids.add(post_id)

                # Extract subreddit info
                sub_data = context.get('subreddit', {})

                # Find the corresponding post element for additional data
                post_element = tracker.find_parent('search-telemetry-tracker', attrs={'data-thingid': True})
                if not post_element:
                    post_element = tracker

                # Extract votes and comments from the DOM
                upvotes = 0
                num_comments = 0
                timestamp = None
                permalink = ""

                # Look for vote/comment counts
                counter_row = tracker.find(attrs={'data-testid': 'search-counter-row'})
                if counter_row:
                    counter_text = counter_row.get_text()
                    # Parse "5 votes · 9 comments"
                    vote_match = re.search(r'(\d+)\s*votes?', counter_text)
                    comment_match = re.search(r'(\d+)\s*comments?', counter_text)
                    if vote_match:
                        upvotes = int(vote_match.group(1))
                    if comment_match:
                        num_comments = int(comment_match.group(1))

                # Look for timestamp
                time_elem = tracker.find('faceplate-timeago')
                if time_elem:
                    timestamp = time_elem.get('ts')

                # Look for permalink
                title_link = tracker.find('a', attrs={'data-testid': 'post-title-text'})
                if title_link:
                    permalink = title_link.get('href', '')
                else:
                    title_link = tracker.find('a', attrs={'data-testid': 'post-title'})
                    if title_link:
                        permalink = title_link.get('href', '')

                if permalink and not permalink.startswith('http'):
                    permalink = f"https://www.reddit.com{permalink}"

                # Build the post object
                post = {
                    "platform_id": f"reddit_{post_id.replace('t3_', '')}",
                    "subreddit": sub_data.get('name', subreddit),
                    "title": post_data.get('title', ''),
                    "author": "",  # Not in tracking data
                    "permalink": permalink,
                    "upvotes": upvotes,
                    "num_comments": num_comments,
                    "flair": "",
                    "is_nsfw": post_data.get('nsfw', False),
                    "search_keyword": keyword,
                    "search_timeframe": timeframe,
                    "created_utc": timestamp,
                    "collected_at": datetime.now(timezone.utc).isoformat(),
                }

                posts.append(post)

            except json.JSONDecodeError:
                continue
            except Exception as e:
                continue

        return posts

    def _parse_score(self, score_text: str) -> int:
        """Parse score text like '1.2k' to integer"""
        if not score_text:
            return 0

        score_text = score_text.strip().lower()

        # Handle 'k' suffix (1.2k -> 1200)
        if 'k' in score_text:
            try:
                num = float(score_text.replace('k', ''))
                return int(num * 1000)
            except:
                pass

        # Handle 'm' suffix (1.2m -> 1200000)
        if 'm' in score_text:
            try:
                num = float(score_text.replace('m', ''))
                return int(num * 1000000)
            except:
                pass

        # Try direct integer parse
        try:
            return int(re.sub(r'[^\d-]', '', score_text))
        except:
            return 0

    async def random_delay(self):
        """Add random delay between requests"""
        delay = random.uniform(SCRAPE_DELAY_MIN, SCRAPE_DELAY_MAX)
        await asyncio.sleep(delay)


async def scrape_subreddit_keywords(
    subreddit: str,
    keywords: list[str],
    timeframes: list[str] = None,
    headless: bool = True
) -> list[dict]:
    """
    Convenience function to scrape a subreddit for multiple keywords

    Args:
        subreddit: Subreddit to scrape
        keywords: List of keywords to search
        timeframes: List of timeframes (defaults to all)
        headless: Run browser in headless mode

    Returns:
        List of all posts found
    """
    if timeframes is None:
        timeframes = list(TIME_WINDOWS.keys())

    all_posts = []

    async with RedditScraper(headless=headless) as scraper:
        for keyword in keywords:
            for timeframe in timeframes:
                posts = await scraper.scrape_search_results(
                    subreddit=subreddit,
                    keyword=keyword,
                    timeframe=timeframe
                )
                all_posts.extend(posts)
                await scraper.random_delay()

    return all_posts


# For testing
if __name__ == "__main__":
    async def test():
        print("Testing Reddit Scraper...")
        posts = await scrape_subreddit_keywords(
            subreddit="onlyfansadvice",
            keywords=["payout", "banking"],
            timeframes=["month"],
            headless=True
        )
        print(f"\nFound {len(posts)} posts")
        for post in posts[:5]:
            print(f"\n- {post['title'][:60]}...")
            print(f"  Score: {post['upvotes']} | Comments: {post['num_comments']}")
            print(f"  URL: {post['permalink']}")

    asyncio.run(test())
