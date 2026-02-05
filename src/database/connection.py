"""
Database connection and session management
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager

import sys
sys.path.insert(0, str(__file__).rsplit('/', 3)[0])

from config.settings import DATABASE_URL, DATABASE_TYPE
from src.database.models import Base


# Create engine with appropriate settings for database type
if DATABASE_TYPE == "postgresql":
    # PostgreSQL (Supabase) settings
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        poolclass=QueuePool,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,  # Check connection health
    )
else:
    # SQLite settings (local development)
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False}
    )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)
    print(f"Database tables created at: {DATABASE_URL}")


def drop_tables():
    """Drop all database tables (use with caution!)"""
    Base.metadata.drop_all(bind=engine)
    print("All database tables dropped")


def get_session() -> Session:
    """Get a new database session"""
    return SessionLocal()


@contextmanager
def session_scope():
    """
    Provide a transactional scope around a series of operations.

    Usage:
        with session_scope() as session:
            session.add(post)
            session.commit()
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_database():
    """Initialize database with tables and seed data"""
    from src.database.seed import seed_initial_data

    create_tables()
    seed_initial_data()
    print("Database initialized successfully!")


if __name__ == "__main__":
    create_tables()
