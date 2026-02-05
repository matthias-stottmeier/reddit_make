"""
Opportunities Page - High-intent threads to engage with
"""
import streamlit as st

st.set_page_config(page_title="Opportunities | MAKE Scraper", page_icon="🎯", layout="wide")

import pandas as pd
from datetime import datetime, timedelta, timezone

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.database.connection import session_scope
from src.database.models import Post, Subreddit, Keyword
from dashboard.auth import check_password

if not check_password():
    st.stop()

# Status options for action tracking
STATUS_OPTIONS = ["NEW", "IN_PROGRESS", "DONE", "SKIPPED"]
STATUS_COLORS = {
    "NEW": "🔵",
    "IN_PROGRESS": "🟡",
    "DONE": "🟢",
    "SKIPPED": "⚫"
}
STATUS_LABELS = {
    "NEW": "New",
    "IN_PROGRESS": "In Progress",
    "DONE": "Done",
    "SKIPPED": "Skipped"
}

# Helper function to update post status
def update_post_status(post_id, new_status):
    with session_scope() as session:
        post = session.query(Post).filter(Post.id == post_id).first()
        if post:
            post.action_status = new_status
            post.action_updated_at = datetime.now(timezone.utc)
            session.commit()

# Helper function to update post notes
def update_post_notes(post_id, notes):
    with session_scope() as session:
        post = session.query(Post).filter(Post.id == post_id).first()
        if post:
            post.action_notes = notes
            post.action_updated_at = datetime.now(timezone.utc)
            session.commit()

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

# Filters - Row 1
col1, col2, col3, col4, col5 = st.columns([1.5, 1, 1.5, 1.5, 1.5])

with col1:
    time_filter = st.selectbox(
        "Time Range",
        ["Last 24 hours", "Last 7 days", "Last 30 days", "All time"],
        index=1
    )

with col2:
    min_comments = st.number_input("Min Comments", min_value=0, value=0)

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

with col5:
    status_filter = st.selectbox(
        "Action Status",
        ["All", "NEW", "IN_PROGRESS", "DONE", "SKIPPED"],
        index=0,
        format_func=lambda x: f"{STATUS_COLORS.get(x, '📋')} {STATUS_LABELS.get(x, x)}" if x != "All" else "📋 All Statuses"
    )

st.divider()

# Build query and load posts into a list (to avoid session issues)
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
        category_keywords = session.query(Keyword.keyword).filter(Keyword.category == keyword_filter).all()
        keyword_list = [k[0] for k in category_keywords]
        if keyword_list:
            query = query.filter(Post.search_keyword.in_(keyword_list))

    # Status filter
    if status_filter != "All":
        query = query.filter(Post.action_status == status_filter)

    # Min comments
    query = query.filter(Post.num_comments >= min_comments)

    # Order by: NEW first, then by comments
    posts_raw = query.order_by(
        Post.action_status == "NEW",  # NEW posts first
        Post.num_comments.desc(),
        Post.collected_at.desc()
    ).limit(50).all()

    # Convert to dict to avoid session detachment issues
    posts = [{
        "id": p.id,
        "title": p.title,
        "subreddit": p.subreddit,
        "permalink": p.permalink,
        "search_keyword": p.search_keyword,
        "num_comments": p.num_comments,
        "upvotes": p.upvotes,
        "action_status": p.action_status or "NEW",
        "action_notes": p.action_notes or "",
        "collected_at": p.collected_at
    } for p in posts_raw]

# Stats summary
col1, col2, col3, col4 = st.columns(4)
with col1:
    new_count = len([p for p in posts if p["action_status"] == "NEW"])
    st.metric("🔵 New", new_count)
with col2:
    in_progress_count = len([p for p in posts if p["action_status"] == "IN_PROGRESS"])
    st.metric("🟡 In Progress", in_progress_count)
with col3:
    done_count = len([p for p in posts if p["action_status"] == "DONE"])
    st.metric("🟢 Done", done_count)
with col4:
    st.metric("📊 Total Shown", len(posts))

st.divider()

# Display results
st.subheader(f"Found {len(posts)} opportunities")

if posts:
    for i, post in enumerate(posts):
        status_icon = STATUS_COLORS.get(post["action_status"], "🔵")

        with st.container():
            # Header row with title and status
            header_col, status_col = st.columns([4, 1])

            with header_col:
                st.markdown(f"### {status_icon} {post['title']}")
                st.markdown(f"**r/{post['subreddit']}** • Matched: `{post['search_keyword']}` • 💬 {post['num_comments']} comments • ⬆️ {post['upvotes']} upvotes")

            with status_col:
                # Status dropdown
                current_status_idx = STATUS_OPTIONS.index(post["action_status"]) if post["action_status"] in STATUS_OPTIONS else 0
                new_status = st.selectbox(
                    "Status",
                    STATUS_OPTIONS,
                    index=current_status_idx,
                    key=f"status_{post['id']}",
                    format_func=lambda x: f"{STATUS_COLORS.get(x, '🔵')} {STATUS_LABELS.get(x, x)}",
                    label_visibility="collapsed"
                )

                # Update status if changed
                if new_status != post["action_status"]:
                    update_post_status(post["id"], new_status)
                    st.rerun()

            # Action row
            action_col1, action_col2, notes_col = st.columns([1, 1, 3])

            with action_col1:
                if post["permalink"]:
                    st.link_button("🔗 Open Thread", post["permalink"], use_container_width=True)

            with action_col2:
                # Quick actions
                if post["action_status"] == "NEW":
                    if st.button("▶️ Start", key=f"start_{post['id']}", use_container_width=True):
                        update_post_status(post["id"], "IN_PROGRESS")
                        st.rerun()
                elif post["action_status"] == "IN_PROGRESS":
                    if st.button("✅ Done", key=f"done_{post['id']}", use_container_width=True):
                        update_post_status(post["id"], "DONE")
                        st.rerun()

            with notes_col:
                # Notes input
                notes = st.text_input(
                    "Notes",
                    value=post["action_notes"],
                    key=f"notes_{post['id']}",
                    placeholder="Add notes about your engagement...",
                    label_visibility="collapsed"
                )

                # Save notes if changed
                if notes != post["action_notes"]:
                    update_post_notes(post["id"], notes)

            st.divider()
else:
    st.info("No opportunities found matching your filters. Try adjusting the criteria or run the scraper.")

# Export option
st.divider()
if posts:
    if st.button("📥 Export to CSV"):
        df = pd.DataFrame([{
            "Title": p["title"],
            "Subreddit": p["subreddit"],
            "Upvotes": p["upvotes"],
            "Comments": p["num_comments"],
            "Keyword": p["search_keyword"],
            "Status": p["action_status"],
            "Notes": p["action_notes"],
            "URL": p["permalink"],
            "Collected": p["collected_at"]
        } for p in posts])

        csv = df.to_csv(index=False)
        st.download_button(
            "Download CSV",
            csv,
            "opportunities.csv",
            "text/csv"
        )
