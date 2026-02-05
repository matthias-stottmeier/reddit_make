"""
Opportunities Page - High-intent threads to engage with
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.database.connection import session_scope
from src.database.models import Post, Subreddit, Keyword

st.set_page_config(page_title="Opportunities | MAKE Scraper", page_icon="🎯", layout="wide")

st.title("🎯 Engagement Opportunities")
st.markdown("*High-intent threads where creators are asking for help with payments/banking*")

st.divider()

# Load filter options from database
with session_scope() as session:
    # Get active subreddits from database
    db_subreddits = session.query(Subreddit).filter(Subreddit.is_active == True).order_by(Subreddit.name).all()
    subreddit_options = ["All"] + [s.name for s in db_subreddits]

    # Get unique keyword categories from database
    db_keywords = session.query(Keyword.category).distinct().all()
    keyword_categories = ["All"] + sorted([k[0] for k in db_keywords if k[0]])

# Filters
col1, col2, col3, col4 = st.columns(4)

with col1:
    time_filter = st.selectbox(
        "Time Range",
        ["Last 24 hours", "Last 7 days", "Last 30 days", "All time"],
        index=1
    )

with col2:
    min_comments = st.number_input("Min Comments", min_value=0, value=1)

with col3:
    subreddit_filter = st.selectbox(
        "Subreddit",
        subreddit_options
    )

with col4:
    keyword_filter = st.selectbox(
        "Keyword Category",
        keyword_categories
    )

st.divider()

# Build query
with session_scope() as session:
    query = session.query(Post)

    # Time filter
    if time_filter == "Last 24 hours":
        query = query.filter(Post.collected_at >= datetime.utcnow() - timedelta(days=1))
    elif time_filter == "Last 7 days":
        query = query.filter(Post.collected_at >= datetime.utcnow() - timedelta(days=7))
    elif time_filter == "Last 30 days":
        query = query.filter(Post.collected_at >= datetime.utcnow() - timedelta(days=30))

    # Subreddit filter
    if subreddit_filter != "All":
        query = query.filter(Post.subreddit == subreddit_filter)

    # Keyword filter - filter by category
    if keyword_filter != "All":
        # Get all keywords in this category
        category_keywords = session.query(Keyword.keyword).filter(Keyword.category == keyword_filter).all()
        keyword_list = [k[0] for k in category_keywords]
        if keyword_list:
            query = query.filter(Post.search_keyword.in_(keyword_list))

    # Min comments
    query = query.filter(Post.num_comments >= min_comments)

    # Order by engagement potential (comments are key for engagement)
    posts = query.order_by(Post.num_comments.desc(), Post.collected_at.desc()).limit(50).all()

    # Display results
    st.subheader(f"Found {len(posts)} opportunities")

    if posts:
        for i, post in enumerate(posts):
            # Determine intent signal
            intent_color = "🟢" if post.num_comments >= 5 else "🟡" if post.num_comments >= 2 else "⚪"

            with st.container():
                col1, col2 = st.columns([4, 1])

                with col1:
                    st.markdown(f"### {intent_color} {post.title}")
                    st.markdown(f"**r/{post.subreddit}** • Matched: `{post.search_keyword}`")

                    # Action buttons
                    btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 2])
                    with btn_col1:
                        if post.permalink:
                            st.link_button("🔗 Open Thread", post.permalink)
                    with btn_col2:
                        st.button(f"📌 Save", key=f"save_{i}")

                with col2:
                    st.metric("💬 Comments", post.num_comments)
                    st.metric("⬆️ Upvotes", post.upvotes)

                st.divider()
    else:
        st.info("No opportunities found matching your filters. Try adjusting the criteria or run the scraper.")

# Export option
st.divider()
if posts:
    if st.button("📥 Export to CSV"):
        df = pd.DataFrame([{
            "Title": p.title,
            "Subreddit": p.subreddit,
            "Upvotes": p.upvotes,
            "Comments": p.num_comments,
            "Keyword": p.search_keyword,
            "URL": p.permalink,
            "Collected": p.collected_at
        } for p in posts])

        csv = df.to_csv(index=False)
        st.download_button(
            "Download CSV",
            csv,
            "opportunities.csv",
            "text/csv"
        )
