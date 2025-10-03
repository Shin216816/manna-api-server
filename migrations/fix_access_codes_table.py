"""
Migration to fix access_codes table for OTP-based registration
Adds missing columns: email, phone, is_used, user_data, code_type
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.config import config as settings
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    """Add missing columns to access_codes table"""
    try:
        # Create engine
        engine = create_engine(settings.DATABASE_URL)
        
        with engine.connect() as conn:
            # Start transaction
            trans = conn.begin()
            
            try:
                logger.info("Starting access_codes table migration...")
                
                # Add missing columns
                migrations = [
                    "ALTER TABLE access_codes ADD COLUMN IF NOT EXISTS email VARCHAR(255)",
                    "ALTER TABLE access_codes ADD COLUMN IF NOT EXISTS phone VARCHAR(20)",
                    "ALTER TABLE access_codes ADD COLUMN IF NOT EXISTS is_used BOOLEAN DEFAULT FALSE NOT NULL",
                    "ALTER TABLE access_codes ADD COLUMN IF NOT EXISTS user_data JSON",
                    "ALTER TABLE access_codes ADD COLUMN IF NOT EXISTS code_type VARCHAR(50) DEFAULT 'registration' NOT NULL",
                    "ALTER TABLE access_codes ALTER COLUMN user_id DROP NOT NULL",
                    "CREATE INDEX IF NOT EXISTS idx_access_codes_email ON access_codes(email)",
                    "CREATE INDEX IF NOT EXISTS idx_access_codes_phone ON access_codes(phone)",
                    "CREATE INDEX IF NOT EXISTS idx_access_codes_is_used ON access_codes(is_used)",
                    "CREATE INDEX IF NOT EXISTS idx_access_codes_code_type ON access_codes(code_type)"
                ]
                
                for migration in migrations:
                    logger.info(f"Executing: {migration}")
                    conn.execute(text(migration))
                
                # Commit transaction
                trans.commit()
                logger.info("✅ Access codes table migration completed successfully!")
                
            except Exception as e:
                trans.rollback()
                logger.error(f"❌ Migration failed: {str(e)}")
                raise
                
    except Exception as e:
        logger.error(f"❌ Database connection failed: {str(e)}")
        raise

if __name__ == "__main__":
    run_migration()
