"""
Trends Page - Analytics and trend visualization
"""
import streamlit as st

st.set_page_config(page_title="Trends | MAKE Scraper", page_icon="📈", layout="wide")

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from collections import Counter

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.database.connection import session_scope
from src.database.models import Post, Keyword
from dashboard.auth import check_password

if not check_password():
    st.stop()

st.title("📈 Trends & Analytics")
st.markdown("*Track keyword momentum and engagement patterns over time*")

st.divider()

# Get all posts for analysis
with session_scope() as session:
    posts = session.query(Post).all()

    if not posts:
        st.warning("No data to analyze yet. Run the scraper first!")
        st.code("python scripts/run_scraper.py")
        st.stop()

    # Convert to DataFrame
    df = pd.DataFrame([{
        "title": p.title,
        "subreddit": p.subreddit,
        "upvotes": p.upvotes,
        "comments": p.num_comments,
        "keyword": p.search_keyword,
        "collected_at": p.collected_at,
        "timeframe": p.search_timeframe
    } for p in posts])

# Overview metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Posts", len(df))
with col2:
    st.metric("Total Engagement", df['upvotes'].sum() + df['comments'].sum())
with col3:
    st.metric("Avg Comments", round(df['comments'].mean(), 1))
with col4:
    st.metric("Subreddits", df['subreddit'].nunique())

st.divider()

# Tabs for different views
tab1, tab2, tab3 = st.tabs(["📊 Keyword Analysis", "🏠 Subreddit Breakdown", "📈 Engagement Metrics"])

with tab1:
    st.subheader("Keyword Distribution")

    # Keyword counts
    keyword_counts = df['keyword'].value_counts().reset_index()
    keyword_counts.columns = ['Keyword', 'Count']

    fig = px.bar(
        keyword_counts,
        x='Keyword',
        y='Count',
        color='Count',
        color_continuous_scale='Oranges',
        title="Posts per Keyword"
    )
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    # Keyword engagement
    st.subheader("Keyword Engagement")
    keyword_engagement = df.groupby('keyword').agg({
        'upvotes': 'mean',
        'comments': 'mean'
    }).round(1).reset_index()
    keyword_engagement.columns = ['Keyword', 'Avg Upvotes', 'Avg Comments']

    st.dataframe(keyword_engagement, hide_index=True, use_container_width=True)

with tab2:
    st.subheader("Subreddit Distribution")

    # Subreddit pie chart
    sub_counts = df['subreddit'].value_counts().reset_index()
    sub_counts.columns = ['Subreddit', 'Posts']

    fig = px.pie(
        sub_counts,
        values='Posts',
        names='Subreddit',
        title="Posts by Subreddit"
    )
    st.plotly_chart(fig, use_container_width=True)

    # Subreddit engagement table
    st.subheader("Subreddit Engagement")
    sub_engagement = df.groupby('subreddit').agg({
        'upvotes': ['sum', 'mean'],
        'comments': ['sum', 'mean']
    }).round(1)
    sub_engagement.columns = ['Total Upvotes', 'Avg Upvotes', 'Total Comments', 'Avg Comments']
    sub_engagement = sub_engagement.reset_index()

    st.dataframe(sub_engagement, hide_index=True, use_container_width=True)

with tab3:
    st.subheader("Engagement Distribution")

    # Comments histogram
    fig = px.histogram(
        df,
        x='comments',
        nbins=20,
        title="Comment Distribution",
        color_discrete_sequence=['#FF4500']
    )
    fig.update_layout(xaxis_title="Number of Comments", yaxis_title="Number of Posts")
    st.plotly_chart(fig, use_container_width=True)

    # Upvotes vs Comments scatter
    st.subheader("Upvotes vs Comments")
    fig = px.scatter(
        df,
        x='upvotes',
        y='comments',
        color='subreddit',
        hover_data=['title'],
        title="Engagement Correlation"
    )
    st.plotly_chart(fig, use_container_width=True)

    # Top engaged posts
    st.subheader("🔥 Top Engaged Posts")
    top_posts = df.nlargest(10, 'comments')[['title', 'subreddit', 'upvotes', 'comments', 'keyword']]
    st.dataframe(top_posts, hide_index=True, use_container_width=True)

st.divider()

# Word cloud simulation (top words from titles)
st.subheader("🔤 Common Words in Titles")

# Simple word frequency
all_titles = ' '.join(df['title'].str.lower())
words = all_titles.split()
# Filter out common words
stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'is', 'it', 'my', 'i', 'me', 'you', 'your', 'this', 'that', 'with', 'from', 'as', 'be', 'have', 'has', 'was', 'were', 'been', 'are', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'can', 'may', 'might', 'must', 'shall'}
filtered_words = [w for w in words if w not in stop_words and len(w) > 2]
word_freq = Counter(filtered_words).most_common(20)

if word_freq:
    word_df = pd.DataFrame(word_freq, columns=['Word', 'Frequency'])
    fig = px.bar(
        word_df,
        x='Frequency',
        y='Word',
        orientation='h',
        color='Frequency',
        color_continuous_scale='Oranges',
        title="Most Common Words in Post Titles"
    )
    fig.update_layout(yaxis={'categoryorder': 'total ascending'})
    st.plotly_chart(fig, use_container_width=True)
