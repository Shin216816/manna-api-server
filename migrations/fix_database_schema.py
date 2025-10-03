"""
Database Schema Fix Migration

This migration fixes database schema inconsistencies and adds missing fields
for the MVP implementation.
"""

import logging
from sqlalchemy import text
from app.utils.database import get_db
from app.model.base import Base
from app.model.m_user import User
from app.model.m_church import Church
from app.model.m_plaid_transaction import PlaidTransaction
from app.model.m_payment_methods import PaymentMethod

logger = logging.getLogger(__name__)

def fix_database_schema():
    """Fix database schema inconsistencies"""
    db = next(get_db())
    
    try:
        # Add missing fields to users table
        logger.info("Adding missing fields to users table...")
        
        # Add stripe_default_payment_method_id if it doesn't exist
        try:
            db.execute(text("""
                ALTER TABLE users 
                ADD COLUMN stripe_default_payment_method_id VARCHAR(100)
            """))
            logger.info("Added stripe_default_payment_method_id to users table")
        except Exception as e:
            if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                logger.info("stripe_default_payment_method_id already exists in users table")
            else:
                logger.error(f"Error adding stripe_default_payment_method_id: {e}")
        
        # Add missing fields to plaid_transactions table
        logger.info("Adding missing fields to plaid_transactions table...")
        
        # Add roundup_amount if it doesn't exist
        try:
            db.execute(text("""
                ALTER TABLE plaid_transactions 
                ADD COLUMN roundup_amount DECIMAL(12,2) DEFAULT 0.00
            """))
            logger.info("Added roundup_amount to plaid_transactions table")
        except Exception as e:
            if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                logger.info("roundup_amount already exists in plaid_transactions table")
            else:
                logger.error(f"Error adding roundup_amount: {e}")
        
        # Add missing fields to churches table
        logger.info("Adding missing fields to churches table...")
        
        # Add kyc_state if it doesn't exist
        try:
            db.execute(text("""
                ALTER TABLE churches 
                ADD COLUMN kyc_state VARCHAR(20)
            """))
            logger.info("Added kyc_state to churches table")
        except Exception as e:
            if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                logger.info("kyc_state already exists in churches table")
            else:
                logger.error(f"Error adding kyc_state: {e}")
        
        # Add kyc_submitted_at if it doesn't exist
        try:
            db.execute(text("""
                ALTER TABLE churches 
                ADD COLUMN kyc_submitted_at TIMESTAMP WITH TIME ZONE
            """))
            logger.info("Added kyc_submitted_at to churches table")
        except Exception as e:
            if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                logger.info("kyc_submitted_at already exists in churches table")
            else:
                logger.error(f"Error adding kyc_submitted_at: {e}")
        
        # Add stripe_account_id if it doesn't exist
        try:
            db.execute(text("""
                ALTER TABLE churches 
                ADD COLUMN stripe_account_id VARCHAR(100) UNIQUE
            """))
            logger.info("Added stripe_account_id to churches table")
        except Exception as e:
            if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                logger.info("stripe_account_id already exists in churches table")
            else:
                logger.error(f"Error adding stripe_account_id: {e}")
        
        # Add charges_enabled if it doesn't exist
        try:
            db.execute(text("""
                ALTER TABLE churches 
                ADD COLUMN charges_enabled BOOLEAN DEFAULT FALSE
            """))
            logger.info("Added charges_enabled to churches table")
        except Exception as e:
            if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                logger.info("charges_enabled already exists in churches table")
            else:
                logger.error(f"Error adding charges_enabled: {e}")
        
        # Add payouts_enabled if it doesn't exist
        try:
            db.execute(text("""
                ALTER TABLE churches 
                ADD COLUMN payouts_enabled BOOLEAN DEFAULT FALSE
            """))
            logger.info("Added payouts_enabled to churches table")
        except Exception as e:
            if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                logger.info("payouts_enabled already exists in churches table")
            else:
                logger.error(f"Error adding payouts_enabled: {e}")
        
        # Create indexes for better performance
        logger.info("Creating indexes for better performance...")
        
        try:
            db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_users_stripe_customer_id 
                ON users(stripe_customer_id)
            """))
            logger.info("Created index on users.stripe_customer_id")
        except Exception as e:
            logger.error(f"Error creating index on users.stripe_customer_id: {e}")
        
        try:
            db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_churches_stripe_account_id 
                ON churches(stripe_account_id)
            """))
            logger.info("Created index on churches.stripe_account_id")
        except Exception as e:
            logger.error(f"Error creating index on churches.stripe_account_id: {e}")
        
        try:
            db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_churches_kyc_status 
                ON churches(kyc_status)
            """))
            logger.info("Created index on churches.kyc_status")
        except Exception as e:
            logger.error(f"Error creating index on churches.kyc_status: {e}")
        
        try:
            db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_plaid_transactions_roundup_amount 
                ON plaid_transactions(roundup_amount)
            """))
            logger.info("Created index on plaid_transactions.roundup_amount")
        except Exception as e:
            logger.error(f"Error creating index on plaid_transactions.roundup_amount: {e}")
        
        # Commit all changes
        db.commit()
        logger.info("Database schema fixes completed successfully")
        
    except Exception as e:
        logger.error(f"Error fixing database schema: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    fix_database_schema()
