"""
Remove bank_accounts table migration

This migration removes the bank_accounts table since we're now using
the Plaid items and accounts tables for all bank account data.
"""

from sqlalchemy import text
from app.utils.database import engine


def upgrade():
    """Remove bank_accounts table"""
    with engine.connect() as conn:
        # Drop the bank_accounts table
        conn.execute(text("DROP TABLE IF EXISTS bank_accounts CASCADE"))
        conn.commit()
        print("✅ Dropped bank_accounts table")


def downgrade():
    """Recreate bank_accounts table (if needed for rollback)"""
    with engine.connect() as conn:
        # Recreate the bank_accounts table structure
        conn.execute(text("""
            CREATE TABLE bank_accounts (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                account_id VARCHAR NOT NULL,
                name VARCHAR,
                mask VARCHAR,
                subtype VARCHAR,
                type VARCHAR,
                institution VARCHAR,
                access_token TEXT NOT NULL,
                is_active TEXT DEFAULT 'active',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """))
        conn.commit()
        print("✅ Recreated bank_accounts table")


if __name__ == "__main__":
    upgrade()
