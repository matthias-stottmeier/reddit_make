"""
SQLAlchemy Database Models for Reddit Scraper
"""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text, JSON,
    ForeignKey, Index, create_engine
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Post(Base):
    """Reddit posts with engagement data"""
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Reddit identification
    platform_id = Column(String(100), unique=True, nullable=False, index=True)
    subreddit = Column(String(100), nullable=False, index=True)
    subreddit_tier = Column(Integer, default=1)  # 1 or 2

    # Content
    title = Column(Text, nullable=False)
    body = Column(Text, default="")
    author = Column(String(100), default="[deleted]")
    permalink = Column(String(500), default="")
    url = Column(String(500), default="")
    flair = Column(String(200), default="")

    # Engagement metrics
    upvotes = Column(Integer, default=0)
    downvotes = Column(Integer, default=0)
    score = Column(Integer, default=0)
    num_comments = Column(Integer, default=0)
    upvote_ratio = Column(Float, default=0.0)
    awards_count = Column(Integer, default=0)

    # Calculated scores
    engagement_score = Column(Float, default=0.0)
    pain_score = Column(Float, default=0.0)
    switch_intent_score = Column(Float, default=0.0)

    # Sentiment analysis
    sentiment_score = Column(Float, default=0.0)  # -1.0 to 1.0
    sentiment_label = Column(String(20), default="neutral")  # positive, negative, neutral
    subjectivity_score = Column(Float, default=0.5)

    # Keyword matching
    matched_keywords = Column(JSON, default=list)  # List of matched keywords
    keyword_categories = Column(JSON, default=list)  # List of categories matched
    primary_category = Column(String(50), default="other")  # Main category

    # Search context
    search_keyword = Column(String(200), default="")  # Keyword used to find this
    search_timeframe = Column(String(20), default="month")  # hour, day, week, month, year

    # Author trust signals
    author_karma = Column(Integer, default=0)
    author_account_age_days = Column(Integer, default=0)
    author_is_verified = Column(Boolean, default=False)

    # Post flags
    is_self_post = Column(Boolean, default=True)
    is_nsfw = Column(Boolean, default=False)
    has_outcome_edit = Column(Boolean, default=False)  # User updated with resolution
    is_archived = Column(Boolean, default=False)

    # Timestamps
    created_utc = Column(DateTime, nullable=True)
    collected_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_updated = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")

    # Indexes for common queries
    __table_args__ = (
        Index('idx_subreddit_created', 'subreddit', 'created_utc'),
        Index('idx_engagement_score', 'engagement_score'),
        Index('idx_pain_score', 'pain_score'),
        Index('idx_switch_intent', 'switch_intent_score'),
        Index('idx_category', 'primary_category'),
        Index('idx_timeframe', 'search_timeframe'),
    )

    def __repr__(self):
        return f"<Post(id={self.id}, subreddit='{self.subreddit}', title='{self.title[:30]}...')>"


class Comment(Base):
    """Top comments for context"""
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False, index=True)
    comment_id = Column(String(100), unique=True, nullable=False)
    parent_id = Column(String(100), default="")  # For nested comments

    # Content
    author = Column(String(100), default="[deleted]")
    body = Column(Text, default="")
    score = Column(Integer, default=0)

    # Sentiment
    sentiment_score = Column(Float, default=0.0)
    sentiment_label = Column(String(20), default="neutral")

    # Author info
    author_karma = Column(Integer, default=0)
    author_account_age_days = Column(Integer, default=0)
    is_op_reply = Column(Boolean, default=False)

    # Timestamps
    created_utc = Column(DateTime, nullable=True)
    collected_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationship
    post = relationship("Post", back_populates="comments")

    def __repr__(self):
        return f"<Comment(id={self.id}, post_id={self.post_id}, score={self.score})>"


class Keyword(Base):
    """Keyword tracking"""
    __tablename__ = "keywords"

    id = Column(Integer, primary_key=True, autoincrement=True)
    keyword = Column(String(200), unique=True, nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)  # pain, compliance, switch, fee, platform, banking
    subcategory = Column(String(50), default="")

    # Platform-specific
    platform_name = Column(String(100), default="")  # If this is a platform-specific keyword

    # Stats
    mention_count = Column(Integer, default=0)
    avg_sentiment = Column(Float, default=0.0)
    last_seen = Column(DateTime, nullable=True)

    # Status
    is_active = Column(Boolean, default=True)
    weight = Column(Float, default=1.0)  # Scoring weight

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Keyword(keyword='{self.keyword}', category='{self.category}')>"


class Subreddit(Base):
    """Subreddit configuration"""
    __tablename__ = "subreddits"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    tier = Column(Integer, default=1)  # 1 = high signal, 2 = platform-specific
    description = Column(Text, default="")

    # Stats
    subscriber_count = Column(Integer, default=0)
    post_count_scraped = Column(Integer, default=0)
    last_scraped = Column(DateTime, nullable=True)

    # Status
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Subreddit(name='{self.name}', tier={self.tier})>"


class Trend(Base):
    """Aggregated metrics over time"""
    __tablename__ = "trends"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, nullable=False, index=True)
    hour = Column(Integer, nullable=True)  # NULL for daily aggregates

    # Scope
    subreddit = Column(String(100), nullable=True, index=True)  # NULL for global trends
    keyword = Column(String(200), nullable=True, index=True)  # NULL for subreddit-wide trends
    category = Column(String(50), nullable=True)

    # Metrics
    post_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    total_score = Column(Integer, default=0)
    avg_engagement_score = Column(Float, default=0.0)
    avg_pain_score = Column(Float, default=0.0)
    avg_sentiment = Column(Float, default=0.0)

    # Calculated
    momentum_score = Column(Float, default=0.0)  # Change vs previous period

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index('idx_trend_date_subreddit', 'date', 'subreddit'),
        Index('idx_trend_date_keyword', 'date', 'keyword'),
    )

    def __repr__(self):
        return f"<Trend(date={self.date}, subreddit='{self.subreddit}', keyword='{self.keyword}')>"


class ManualThread(Base):
    """Manually entered X/Twitter threads"""
    __tablename__ = "manual_threads"

    id = Column(Integer, primary_key=True, autoincrement=True)
    platform = Column(String(50), default="twitter")  # twitter, x, other
    url = Column(String(500), unique=True, nullable=False)

    # Content
    author = Column(String(100), default="")
    content = Column(Text, default="")
    notes = Column(Text, default="")  # User notes

    # Category
    category = Column(String(50), default="")  # User-defined category
    matched_keywords = Column(JSON, default=list)

    # Metrics (manual entry)
    likes = Column(Integer, default=0)
    retweets = Column(Integer, default=0)
    replies = Column(Integer, default=0)
    views = Column(Integer, default=0)

    # Sentiment
    sentiment_score = Column(Float, default=0.0)
    sentiment_label = Column(String(20), default="neutral")

    # Timestamps
    posted_at = Column(DateTime, nullable=True)
    added_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    added_by = Column(String(100), default="user")

    def __repr__(self):
        return f"<ManualThread(platform='{self.platform}', url='{self.url[:50]}...')>"


class SavedSearch(Base):
    """Saved search configurations"""
    __tablename__ = "saved_searches"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, default="")

    # Search parameters (stored as JSON)
    subreddits = Column(JSON, default=list)  # List of subreddit names
    include_keywords = Column(JSON, default=list)
    exclude_keywords = Column(JSON, default=list)
    categories = Column(JSON, default=list)  # Filter by keyword categories
    min_score = Column(Integer, default=0)
    min_comments = Column(Integer, default=0)
    min_pain_score = Column(Float, default=0.0)
    timeframes = Column(JSON, default=list)  # hour, day, week, month, year

    # Alert configuration
    alert_enabled = Column(Boolean, default=False)
    alert_threshold_engagement = Column(Float, default=50.0)
    alert_threshold_pain = Column(Float, default=5.0)
    alert_email = Column(String(200), default="")

    # Status
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_run = Column(DateTime, nullable=True)
    run_count = Column(Integer, default=0)

    def __repr__(self):
        return f"<SavedSearch(name='{self.name}')>"


class Alert(Base):
    """Alerts generated by the system"""
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    search_id = Column(Integer, ForeignKey("saved_searches.id"), nullable=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=True)

    # Alert info
    alert_type = Column(String(50), nullable=False)  # high_engagement, pain_spike, switch_intent
    message = Column(Text, nullable=False)
    severity = Column(String(20), default="info")  # info, warning, critical

    # Status
    is_read = Column(Boolean, default=False)
    is_dismissed = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    read_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<Alert(type='{self.alert_type}', is_read={self.is_read})>"


class Settings(Base):
    """Application settings stored in database"""
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(JSON, nullable=True)
    description = Column(Text, default="")

    # Timestamps
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Settings(key='{self.key}')>"
