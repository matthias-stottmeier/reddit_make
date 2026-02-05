"""
All Posts Page - Browse and filter all collected posts
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.database.connection import session_scope
from src.database.models import Post, Subreddit

st.set_page_config(page_title="All Posts | MAKE Scraper", page_icon="📋", layout="wide")

st.title("📋 All Collected Posts")
st.markdown("*Browse and filter all posts from your monitored subreddits*")

st.divider()

# Filters in expander
with st.expander("🔍 Filters", expanded=True):
    col1, col2, col3 = st.columns(3)

    with col1:
        search_term = st.text_input("Search titles", placeholder="e.g., Paxum, payout")

    with col2:
        with session_scope() as session:
            subreddits = session.query(Post.subreddit).distinct().all()
            subreddit_list = ["All"] + [s[0] for s in subreddits]
        subreddit_filter = st.selectbox("Subreddit", subreddit_list)

    with col3:
        sort_by = st.selectbox("Sort by", ["Newest", "Most Comments", "Most Upvotes"])

    col4, col5 = st.columns(2)
    with col4:
        min_upvotes = st.slider("Min Upvotes", 0, 100, 0)
    with col5:
        min_comments = st.slider("Min Comments", 0, 50, 0)

# Build query and get data
with session_scope() as session:
    query = session.query(Post)

    # Apply filters
    if search_term:
        query = query.filter(Post.title.ilike(f"%{search_term}%"))

    if subreddit_filter != "All":
        query = query.filter(Post.subreddit == subreddit_filter)

    query = query.filter(Post.upvotes >= min_upvotes)
    query = query.filter(Post.num_comments >= min_comments)

    # Apply sort
    if sort_by == "Newest":
        query = query.order_by(Post.collected_at.desc())
    elif sort_by == "Most Comments":
        query = query.order_by(Post.num_comments.desc())
    else:
        query = query.order_by(Post.upvotes.desc())

    posts = query.limit(100).all()

    # Convert to DataFrame for display
    if posts:
        df = pd.DataFrame([{
            "Title": p.title[:60] + "..." if len(p.title) > 60 else p.title,
            "Subreddit": f"r/{p.subreddit}",
            "⬆️": p.upvotes,
            "💬": p.num_comments,
            "Keyword": p.search_keyword,
            "Collected": p.collected_at.strftime("%Y-%m-%d %H:%M") if p.collected_at else "",
            "URL": p.permalink
        } for p in posts])

        st.subheader(f"Showing {len(posts)} posts")

        # Display as table with clickable links
        st.dataframe(
            df,
            column_config={
                "URL": st.column_config.LinkColumn("Link", display_text="Open"),
                "⬆️": st.column_config.NumberColumn("Upvotes"),
                "💬": st.column_config.NumberColumn("Comments"),
            },
            hide_index=True,
            use_container_width=True
        )

        # Export
        st.divider()
        csv = df.to_csv(index=False)
        st.download_button(
            "📥 Export to CSV",
            csv,
            "all_posts.csv",
            "text/csv"
        )
    else:
        st.info("No posts found. Run the scraper to collect data!")
        st.code("python scripts/run_scraper.py")
