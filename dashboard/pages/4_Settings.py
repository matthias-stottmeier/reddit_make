"""
Settings Page - Manage subreddits, keywords, and scraping configuration
"""
import streamlit as st

# MUST be first Streamlit command
st.set_page_config(page_title="Settings | MAKE Scraper", page_icon="⚙️", layout="wide")

import pandas as pd
from datetime import datetime
import requests
import os

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.database.connection import session_scope
from src.database.models import Subreddit, Keyword

# GitHub repository info for triggering scraper
# Try Streamlit secrets first, then fall back to environment variables
try:
    GITHUB_REPO = st.secrets.get("GITHUB_REPO", os.getenv("GITHUB_REPO", ""))
    GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN", os.getenv("GITHUB_TOKEN", ""))
except Exception:
    GITHUB_REPO = os.getenv("GITHUB_REPO", "")
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

st.title("⚙️ Settings")
st.markdown("*Manage your subreddits, keywords, and scraping configuration*")

st.divider()

# Helper function to toggle subreddit status
def toggle_subreddit(sub_id):
    with session_scope() as session:
        sub = session.query(Subreddit).filter(Subreddit.id == sub_id).first()
        if sub:
            sub.is_active = not sub.is_active
            session.commit()

# Helper function to toggle keyword status
def toggle_keyword(kw_id):
    with session_scope() as session:
        kw = session.query(Keyword).filter(Keyword.id == kw_id).first()
        if kw:
            kw.is_active = not kw.is_active
            session.commit()

# Tabs for different settings
tab1, tab2, tab3, tab4 = st.tabs(["📁 Subreddits", "🔑 Keywords", "⏱️ Scraping", "🗃️ Database"])

# ============================================
# TAB 1: SUBREDDITS
# ============================================
with tab1:
    st.subheader("Monitored Subreddits")

    # First, load subreddit data into a list (outside session)
    with session_scope() as session:
        subreddits_data = [
            {"id": s.id, "name": s.name, "tier": s.tier, "is_active": s.is_active}
            for s in session.query(Subreddit).order_by(Subreddit.tier, Subreddit.name).all()
        ]

    # Display as editable table
    if subreddits_data:
        # Tier 1
        st.markdown("### Tier 1 (High Signal)")
        tier1 = [s for s in subreddits_data if s["tier"] == 1]
        for sub in tier1:
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.markdown(f"**r/{sub['name']}**")
            with col2:
                status = "✅ Active" if sub["is_active"] else "❌ Inactive"
                st.write(status)
            with col3:
                if st.button("Toggle", key=f"toggle_sub_{sub['id']}"):
                    toggle_subreddit(sub["id"])
                    st.rerun()

        st.divider()

        # Tier 2
        st.markdown("### Tier 2 (Platform-Specific)")
        tier2 = [s for s in subreddits_data if s["tier"] == 2]
        for sub in tier2:
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.markdown(f"**r/{sub['name']}**")
            with col2:
                status = "✅ Active" if sub["is_active"] else "❌ Inactive"
                st.write(status)
            with col3:
                if st.button("Toggle", key=f"toggle_sub_{sub['id']}"):
                    toggle_subreddit(sub["id"])
                    st.rerun()

    st.divider()

    # Add new subreddit
    st.subheader("Add New Subreddit")
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        new_sub_name = st.text_input("Subreddit name (without r/)", placeholder="newsubreddit")
    with col2:
        new_sub_tier = st.selectbox("Tier", [1, 2])
    with col3:
        if st.button("➕ Add Subreddit"):
            if new_sub_name:
                with session_scope() as session:
                    existing = session.query(Subreddit).filter(Subreddit.name == new_sub_name).first()
                    if existing:
                        st.error(f"r/{new_sub_name} already exists!")
                    else:
                        new_sub = Subreddit(name=new_sub_name, tier=new_sub_tier, is_active=True)
                        session.add(new_sub)
                        session.commit()
                        st.success(f"Added r/{new_sub_name}!")
                        st.rerun()

# ============================================
# TAB 2: KEYWORDS
# ============================================
with tab2:
    st.subheader("Keyword Categories")

    with session_scope() as session:
        keywords = session.query(Keyword).order_by(Keyword.category, Keyword.keyword).all()

        if keywords:
            # Group by category
            categories = {}
            for kw in keywords:
                if kw.category not in categories:
                    categories[kw.category] = []
                categories[kw.category].append(kw)

            # Display each category
            for category, kws in categories.items():
                with st.expander(f"**{category.upper()}** ({len(kws)} keywords)", expanded=False):
                    # Show as pills/tags
                    active_kws = [k for k in kws if k.is_active]
                    inactive_kws = [k for k in kws if not k.is_active]

                    if active_kws:
                        st.markdown("**Active:**")
                        st.write(" • ".join([f"`{k.keyword}`" for k in active_kws]))

                    if inactive_kws:
                        st.markdown("**Inactive:**")
                        st.write(" • ".join([f"~~{k.keyword}~~" for k in inactive_kws]))

    st.divider()

    # Add new keyword
    st.subheader("Add New Keyword")
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        new_kw = st.text_input("Keyword", placeholder="new keyword")
    with col2:
        new_kw_category = st.selectbox("Category", ["pain", "compliance", "switch", "fee", "banking", "platform"])
    with col3:
        if st.button("➕ Add Keyword"):
            if new_kw:
                with session_scope() as session:
                    existing = session.query(Keyword).filter(Keyword.keyword == new_kw).first()
                    if existing:
                        st.error(f"'{new_kw}' already exists!")
                    else:
                        new_keyword = Keyword(keyword=new_kw, category=new_kw_category, is_active=True, weight=2.0)
                        session.add(new_keyword)
                        session.commit()
                        st.success(f"Added '{new_kw}'!")
                        st.rerun()

# ============================================
# TAB 3: SCRAPING SETTINGS
# ============================================
with tab3:
    st.subheader("Scraping Configuration")

    # ---- TRIGGER SCRAPER SECTION ----
    st.markdown("### 🚀 Trigger Scraper")

    col1, col2 = st.columns([2, 1])

    with col1:
        scrape_mode = st.selectbox(
            "Scraping Mode",
            ["all", "engagement", "research"],
            help="All = full scrape (all timeframes), Engagement = hour/day/week, Research = month/year"
        )

    with col2:
        st.write("")  # Spacer
        st.write("")  # Spacer
        trigger_btn = st.button("🔄 Run Scraper Now", type="primary", use_container_width=True)

    if trigger_btn:
        if GITHUB_REPO and GITHUB_TOKEN:
            # Trigger GitHub Actions via repository dispatch
            try:
                response = requests.post(
                    f"https://api.github.com/repos/{GITHUB_REPO}/dispatches",
                    headers={
                        "Authorization": f"token {GITHUB_TOKEN}",
                        "Accept": "application/vnd.github.v3+json"
                    },
                    json={
                        "event_type": "trigger-scrape",
                        "client_payload": {"mode": scrape_mode}
                    }
                )
                if response.status_code == 204:
                    st.success("✅ Scraper triggered! Check GitHub Actions for progress.")
                    st.info(f"View progress: https://github.com/{GITHUB_REPO}/actions")
                else:
                    st.error(f"Failed to trigger scraper: {response.status_code} - {response.text}")
            except Exception as e:
                st.error(f"Error triggering scraper: {e}")
        else:
            st.warning("⚠️ GitHub integration not configured. Set GITHUB_REPO and GITHUB_TOKEN in Streamlit secrets.")
            st.info("The scraper runs automatically twice daily via GitHub Actions.")

    # Show last scrape info
    with session_scope() as session:
        from src.database.models import Post
        last_post = session.query(Post).order_by(Post.collected_at.desc()).first()
        if last_post:
            st.caption(f"📅 Last data collected: {last_post.collected_at.strftime('%Y-%m-%d %H:%M UTC')}")

    st.divider()

    st.markdown("### ⏰ Automatic Schedule")
    st.info("""
    The scraper runs automatically via GitHub Actions:
    - **6:00 AM UTC** - Daily full scrape (all keywords, all timeframes)

    Data is saved directly to Supabase. Existing posts have their stats updated
    (upvotes, comments) while preserving your action status and notes.
    """)

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Time Windows")
        st.markdown("""
        - **hour**: Fresh threads (engagement opportunities)
        - **day**: Today's hot topics
        - **week**: This week's trends
        - **month**: Established patterns
        - **year**: Historical/evergreen issues
        """)

    with col2:
        st.markdown("### Scraping Delays")
        st.markdown("""
        - **Min delay**: 2 seconds
        - **Max delay**: 5 seconds
        - *Polite scraping to avoid rate limits*
        """)

    st.divider()

    with st.expander("📝 Local Development Commands"):
        st.code("""
# Quick test (1 subreddit, 2 keywords)
python scripts/run_scraper.py --limit 1 --keywords payout banking

# Engagement mode (hour/day/week)
python scripts/run_scraper.py --mode engagement

# Research mode (month/year)
python scripts/run_scraper.py --mode research

# Full scrape (all subreddits, all keywords, all timeframes)
python scripts/run_scraper.py
        """, language="bash")

# ============================================
# TAB 4: DATABASE
# ============================================
with tab4:
    st.subheader("Database Statistics")

    with session_scope() as session:
        from src.database.models import Post, Comment

        post_count = session.query(Post).count()
        sub_count = session.query(Subreddit).count()
        kw_count = session.query(Keyword).count()

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Posts", post_count)
        with col2:
            st.metric("Subreddits", sub_count)
        with col3:
            st.metric("Keywords", kw_count)

    st.divider()

    st.subheader("Database Location")
    db_path = Path(__file__).parent.parent.parent / "data" / "reddit_scraper.db"
    st.code(str(db_path))

    st.divider()

    st.subheader("⚠️ Danger Zone")
    with st.expander("Database Operations", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Clear All Posts", type="secondary"):
                st.warning("This will delete all collected posts. Are you sure?")
                if st.button("Yes, delete all posts", key="confirm_delete"):
                    with session_scope() as session:
                        session.query(Post).delete()
                        session.commit()
                    st.success("All posts deleted!")
                    st.rerun()

        with col2:
            if st.button("🔄 Reinitialize Database", type="secondary"):
                st.warning("This will reset the entire database!")
