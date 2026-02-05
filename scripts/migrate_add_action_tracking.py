"""
Migration script: Add action tracking columns to posts table
Run this once to update existing databases with the new columns.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from src.database.connection import engine

def migrate():
    """Add action_status, action_notes, and action_updated_at columns to posts table"""

    with engine.connect() as conn:
        # Check if columns already exist
        result = conn.execute(text("PRAGMA table_info(posts)"))
        columns = [row[1] for row in result.fetchall()]

        migrations_needed = []

        if 'action_status' not in columns:
            migrations_needed.append(
                "ALTER TABLE posts ADD COLUMN action_status VARCHAR(20) DEFAULT 'NEW'"
            )
            print("Will add: action_status column")

        if 'action_notes' not in columns:
            migrations_needed.append(
                "ALTER TABLE posts ADD COLUMN action_notes TEXT DEFAULT ''"
            )
            print("Will add: action_notes column")

        if 'action_updated_at' not in columns:
            migrations_needed.append(
                "ALTER TABLE posts ADD COLUMN action_updated_at DATETIME"
            )
            print("Will add: action_updated_at column")

        if not migrations_needed:
            print("✅ All action tracking columns already exist. No migration needed.")
            return

        # Run migrations
        for sql in migrations_needed:
            conn.execute(text(sql))
            print(f"✅ Executed: {sql}")

        conn.commit()

        # Create index on action_status
        try:
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_action_status ON posts(action_status)"))
            conn.commit()
            print("✅ Created index on action_status")
        except Exception as e:
            print(f"Index may already exist: {e}")

        print("\n🎉 Migration complete!")

if __name__ == "__main__":
    print("=" * 50)
    print("Migration: Add Action Tracking to Posts")
    print("=" * 50)
    migrate()
