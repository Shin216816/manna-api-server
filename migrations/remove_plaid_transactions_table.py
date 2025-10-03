#!/usr/bin/env python3
"""
Remove plaid_transactions table migration

This migration removes the plaid_transactions table since the system
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
    """Remove plaid_transactions table and related objects"""
    try:
        with engine.connect() as conn:
            # Drop the plaid_transactions table
            logger.info("Dropping plaid_transactions table...")
            conn.execute(text("DROP TABLE IF EXISTS plaid_transactions CASCADE"))
            logger.info("✅ plaid_transactions table dropped successfully")
            
            # Drop the sequence if it exists
            logger.info("Dropping plaid_transactions sequence...")
            conn.execute(text("DROP SEQUENCE IF EXISTS plaid_transactions_id_seq CASCADE"))
            logger.info("✅ plaid_transactions sequence dropped successfully")
            
            conn.commit()
            logger.info("✅ Migration completed successfully")
            
    except Exception as e:
        logger.error(f"❌ Error during migration: {e}")
        raise

def downgrade():
    """Recreate plaid_transactions table (for rollback)"""
    try:
        with engine.connect() as conn:
            # Recreate the plaid_transactions table
            logger.info("Recreating plaid_transactions table...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS plaid_transactions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    plaid_transaction_id VARCHAR(255) UNIQUE NOT NULL,
                    plaid_account_id VARCHAR(255) NOT NULL,
                    amount NUMERIC(12, 2) NOT NULL,
                    roundup_amount NUMERIC(12, 2) DEFAULT 0.00,
                    date TIMESTAMP NOT NULL,
                    merchant_name VARCHAR(255),
                    category VARCHAR(100),
                    subcategory VARCHAR(100),
                    description TEXT,
                    is_pending BOOLEAN DEFAULT FALSE NOT NULL,
                    account_owner VARCHAR(255),
                    payment_meta TEXT,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL,
                    CONSTRAINT plaid_transactions_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """))
            
            # Create indexes
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_plaid_transactions_user_id ON plaid_transactions(user_id);
                CREATE INDEX IF NOT EXISTS idx_plaid_transactions_plaid_transaction_id ON plaid_transactions(plaid_transaction_id);
                CREATE INDEX IF NOT EXISTS idx_plaid_transactions_date ON plaid_transactions(date);
                CREATE INDEX IF NOT EXISTS idx_plaid_transactions_roundup_amount ON plaid_transactions(roundup_amount);
            """))
            
            conn.commit()
            logger.info("✅ plaid_transactions table recreated successfully")
            
    except Exception as e:
        logger.error(f"❌ Error during rollback: {e}")
        raise

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Remove plaid_transactions table migration")
    parser.add_argument("--rollback", action="store_true", help="Rollback the migration")
    
    args = parser.parse_args()
    
    if args.rollback:
        logger.info("🔄 Rolling back plaid_transactions table removal...")
        downgrade()
    else:
        logger.info("🚀 Running plaid_transactions table removal migration...")
        upgrade()
