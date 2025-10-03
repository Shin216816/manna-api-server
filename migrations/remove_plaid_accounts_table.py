#!/usr/bin/env python3
"""
Remove plaid_accounts table migration

This migration removes the plaid_accounts table since the system
now uses on-demand Plaid API fetching instead of database storage.
"""

import sys
import os
import logging
from sqlalchemy import text

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.database import engine

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def upgrade():
    """Remove plaid_accounts table and related objects"""
    try:
        with engine.connect() as conn:
            # Drop the plaid_accounts table
            logger.info("Dropping plaid_accounts table...")
            conn.execute(text("DROP TABLE IF EXISTS plaid_accounts CASCADE"))
            logger.info("✅ plaid_accounts table dropped successfully")
            
            # Drop the sequence if it exists
            logger.info("Dropping plaid_accounts sequence...")
            conn.execute(text("DROP SEQUENCE IF EXISTS plaid_accounts_id_seq CASCADE"))
            logger.info("✅ plaid_accounts sequence dropped successfully")
            
            conn.commit()
            logger.info("✅ Migration completed successfully")
            
    except Exception as e:
        logger.error(f"❌ Error during migration: {e}")
        raise

def downgrade():
    """Recreate plaid_accounts table (for rollback)"""
    try:
        with engine.connect() as conn:
            # Recreate the plaid_accounts table
            logger.info("Recreating plaid_accounts table...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS plaid_accounts (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    plaid_item_id INTEGER NOT NULL,
                    account_id VARCHAR(255) UNIQUE NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    official_name VARCHAR(255),
                    type VARCHAR(50) NOT NULL,
                    subtype VARCHAR(50),
                    mask VARCHAR(10),
                    available_balance NUMERIC(12, 2),
                    current_balance NUMERIC(12, 2),
                    iso_currency_code VARCHAR(3) DEFAULT 'USD' NOT NULL,
                    status VARCHAR(20) DEFAULT 'active' NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL,
                    CONSTRAINT plaid_accounts_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id),
                    CONSTRAINT plaid_accounts_plaid_item_id_fkey FOREIGN KEY (plaid_item_id) REFERENCES plaid_items(id)
                )
            """))
            
            # Create indexes
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_plaid_accounts_user_id ON plaid_accounts(user_id);
                CREATE INDEX IF NOT EXISTS idx_plaid_accounts_plaid_item_id ON plaid_accounts(plaid_item_id);
                CREATE INDEX IF NOT EXISTS idx_plaid_accounts_account_id ON plaid_accounts(account_id);
            """))
            
            conn.commit()
            logger.info("✅ plaid_accounts table recreated successfully")
            
    except Exception as e:
        logger.error(f"❌ Error during rollback: {e}")
        raise

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Remove plaid_accounts table migration")
    parser.add_argument("--rollback", action="store_true", help="Rollback the migration")
    
    args = parser.parse_args()
    
    if args.rollback:
        logger.info("🔄 Rolling back plaid_accounts table removal...")
        downgrade()
    else:
        logger.info("🚀 Running plaid_accounts table removal migration...")
        upgrade()
