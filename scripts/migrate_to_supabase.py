"""
Migration script: Move data from SQLite to Supabase (PostgreSQL)

Usage:
    export SUPABASE_URL="postgresql://postgres:PASSWORD@db.PROJECT.supabase.co:5432/postgres"
    python scripts/migrate_to_supabase.py
"""
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# SQLite source
SQLITE_PATH = Path(__file__).parent.parent / "data" / "reddit_scraper.db"
SQLITE_URL = f"sqlite:///{SQLITE_PATH}"

# PostgreSQL target (Supabase)
SUPABASE_URL = os.getenv("SUPABASE_URL")

if not SUPABASE_URL:
    print("❌ Error: SUPABASE_URL environment variable not set!")
    print("\nSet it with:")
    print('  export SUPABASE_URL="postgresql://postgres:PASSWORD@db.PROJECT.supabase.co:5432/postgres"')
    sys.exit(1)

print("=" * 60)
print("Migration: SQLite → Supabase (PostgreSQL)")
print("=" * 60)

# Create engines
print("\n📁 Connecting to SQLite...")
sqlite_engine = create_engine(SQLITE_URL)
SqliteSession = sessionmaker(bind=sqlite_engine)

print("🌐 Connecting to Supabase...")
pg_engine = create_engine(SUPABASE_URL)
PgSession = sessionmaker(bind=pg_engine)

# Import models and create tables in PostgreSQL
print("\n📦 Creating tables in Supabase...")
from src.database.models import Base, Post, Subreddit, Keyword, Comment, Trend, Settings

Base.metadata.create_all(bind=pg_engine)
print("✅ Tables created!")

# Migrate data
def migrate_table(model, name):
    """Migrate a single table from SQLite to PostgreSQL"""
    sqlite_session = SqliteSession()
    pg_session = PgSession()

    try:
        # Count existing records in PostgreSQL
        existing_count = pg_session.query(model).count()
        if existing_count > 0:
            print(f"  ⚠️  {name}: {existing_count} records already exist, skipping...")
            return existing_count

        # Get all records from SQLite
        records = sqlite_session.query(model).all()
        count = len(records)

        if count == 0:
            print(f"  ➖ {name}: No records to migrate")
            return 0

        print(f"  📤 {name}: Migrating {count} records...")

        # Detach from SQLite session and add to PostgreSQL
        for record in records:
            sqlite_session.expunge(record)
            # Create a new instance with the same data
            data = {c.name: getattr(record, c.name) for c in record.__table__.columns}
            new_record = model(**data)
            pg_session.merge(new_record)

        pg_session.commit()
        print(f"  ✅ {name}: {count} records migrated!")
        return count

    except Exception as e:
        pg_session.rollback()
        print(f"  ❌ {name}: Error - {e}")
        return 0
    finally:
        sqlite_session.close()
        pg_session.close()

# Migrate in order (respecting foreign keys)
print("\n🚀 Starting migration...")
total = 0
total += migrate_table(Subreddit, "Subreddits")
total += migrate_table(Keyword, "Keywords")
total += migrate_table(Settings, "Settings")
total += migrate_table(Post, "Posts")
total += migrate_table(Comment, "Comments")
total += migrate_table(Trend, "Trends")

print(f"\n🎉 Migration complete! Total records: {total}")
print("\nNext steps:")
print("1. Add SUPABASE_URL to Streamlit Cloud secrets")
print("2. Add SUPABASE_URL to GitHub Actions secrets")
print("3. Push the code changes to GitHub")
