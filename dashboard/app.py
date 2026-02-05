"""
MAKE Reddit Scraper Dashboard - Main Entry Point
"""
import streamlit as st
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.connection import session_scope
from src.database.models import Post, Subreddit, Keyword

st.set_page_config(
    page_title="Dashboard | MAKE Scraper",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "MAKE Reddit Scraper - Find creator economy engagement opportunities"
    }
)

# MAKE Brand CSS - works in both light and dark mode
st.markdown("""
<style>
    /* MAKE Brand Colors - adaptive for dark/light mode */
    .make-header {
        display: flex;
        align-items: baseline;
        gap: 12px;
        margin-bottom: 8px;
    }

    .make-logo {
        font-size: 1.25rem;
        font-weight: 800;
        color: #5B5BF7;
        letter-spacing: -0.5px;
    }

    .make-title {
        font-size: 2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #5B5BF7 0%, #8B8BFF 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    .make-subtitle {
        font-size: 1rem;
        opacity: 0.7;
        margin-top: -8px;
        margin-bottom: 16px;
    }

    /* Mode toggle styling */
    .stRadio > div {
        gap: 1rem;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Accent color for links and highlights */
    a {
        color: #5B5BF7 !important;
    }
</style>
""", unsafe_allow_html=True)

# Header - works in dark and light mode
st.markdown("""
<div class="make-header">
    <span class="make-logo">MAKE</span>
    <span class="make-title">Reddit Scraper</span>
</div>
""", unsafe_allow_html=True)

st.markdown('<p class="make-subtitle">Find creator economy engagement opportunities</p>', unsafe_allow_html=True)

st.divider()

# Get database stats
with session_scope() as session:
    total_posts = session.query(Post).count()
    total_subreddits = session.query(Subreddit).filter(Subreddit.is_active == True).count()
    total_keywords = session.query(Keyword).filter(Keyword.is_active == True).count()

    # Posts from last 24h
    yesterday = datetime.utcnow() - timedelta(days=1)
    recent_posts = session.query(Post).filter(Post.collected_at >= yesterday).count()

    # High engagement posts (>5 comments)
    high_engagement = session.query(Post).filter(Post.num_comments >= 5).count()

    # Last scrape time
    last_post = session.query(Post).order_by(Post.collected_at.desc()).first()
    last_scrape = last_post.collected_at if last_post else None

# Metrics row
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Posts", total_posts, f"+{recent_posts} today")
with col2:
    st.metric("High Engagement", high_engagement, help="Posts with 5+ comments")
with col3:
    st.metric("Subreddits", total_subreddits)
with col4:
    st.metric("Keywords", total_keywords)

# Last updated
if last_scrape:
    time_diff = datetime.utcnow() - last_scrape
    if time_diff.days > 0:
        time_ago = f"{time_diff.days}d ago"
    elif time_diff.seconds > 3600:
        time_ago = f"{time_diff.seconds // 3600}h ago"
    else:
        time_ago = f"{time_diff.seconds // 60}m ago"
    st.caption(f"Last updated: {time_ago}")

st.divider()

# Mode selector - stored in session state
if "mode" not in st.session_state:
    st.session_state.mode = "Engagement"

mode = st.radio(
    "Mode",
    ["Engagement", "Research"],
    horizontal=True,
    help="Engagement: Fresh threads (hour/day/week) | Research: Historical data (month/year)",
    key="mode_selector"
)
st.session_state.mode = mode

# Define timeframes based on mode
if mode == "Engagement":
    timeframes = ["hour", "day", "week"]
    sort_order = Post.collected_at.desc()
    section_title = "Fresh Opportunities"
    section_desc = "Recent threads to engage with"
else:
    timeframes = ["month", "year"]
    sort_order = Post.num_comments.desc()
    section_title = "Research Insights"
    section_desc = "Historical patterns and trends"

st.divider()

# Recent opportunities based on mode
st.subheader(section_title)
st.caption(section_desc)

with session_scope() as session:
    # Filter by timeframe based on mode
    query = session.query(Post).filter(Post.search_timeframe.in_(timeframes))
    posts = query.order_by(sort_order).limit(10).all()

    if posts:
        for i, post in enumerate(posts):
            # Clean card layout
            with st.container():
                col1, col2 = st.columns([5, 1])

                with col1:
                    # Title with link
                    if post.permalink:
                        st.markdown(f"**[{post.title}]({post.permalink})**")
                    else:
                        st.markdown(f"**{post.title}**")

                    # Metadata row
                    meta_parts = [
                        f"r/{post.subreddit}",
                        f"Keyword: {post.search_keyword}",
                    ]
                    if post.created_utc:
                        meta_parts.append(f"Posted: {post.created_utc.strftime('%b %d')}")

                    st.caption(" · ".join(meta_parts))

                with col2:
                    # Engagement stats
                    st.markdown(f"**{post.num_comments}** comments")
                    st.caption(f"{post.upvotes} upvotes")

                st.divider()
    else:
        st.info(f"No posts found for {mode} mode. Run the scraper with appropriate timeframes.")
        if mode == "Engagement":
            st.code("python scripts/run_scraper.py --mode engagement")
        else:
            st.code("python scripts/run_scraper.py --mode research")

# Sidebar
with st.sidebar:
    st.markdown("### Quick Actions")

    if st.button("Refresh", use_container_width=True, type="primary"):
        st.rerun()

    st.divider()

    st.markdown("### Stats")
    st.markdown(f"**{total_posts}** posts collected")
    st.markdown(f"**{total_subreddits}** subreddits monitored")
    st.markdown(f"**{total_keywords}** keywords tracked")

    st.divider()

    st.markdown("### Run Scraper")
    st.code("python scripts/run_scraper.py", language="bash")
