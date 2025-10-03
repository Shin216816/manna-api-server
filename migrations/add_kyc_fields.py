"""
Migration script to add new KYC fields to the churches table
"""

from sqlalchemy import create_engine, text
from app.config import config
import logging

def run_migration():
    """Run the migration to add new KYC fields"""
    try:
        # Create database engine
        engine = create_engine(config.DATABASE_URL)
        
        with engine.connect() as conn:
            # Add new KYC state machine fields
            conn.execute(text("""
                ALTER TABLE churches 
                ADD COLUMN IF NOT EXISTS kyc_state VARCHAR(50) DEFAULT 'UNREGISTERED',
                ADD COLUMN IF NOT EXISTS charges_enabled BOOLEAN DEFAULT FALSE,
                ADD COLUMN IF NOT EXISTS payouts_enabled BOOLEAN DEFAULT FALSE,
                ADD COLUMN IF NOT EXISTS disabled_reason TEXT,
                ADD COLUMN IF NOT EXISTS requirements_json JSONB,
                ADD COLUMN IF NOT EXISTS verified_at TIMESTAMPTZ
            """))
            
            # Create church_users table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS church_users (
                    id SERIAL PRIMARY KEY,
                    church_id INTEGER REFERENCES churches(id),
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    role VARCHAR(20) NOT NULL CHECK (role IN ('owner', 'admin', 'finance', 'viewer')),
                    mfa_enabled BOOLEAN DEFAULT FALSE,
                    last_login_at TIMESTAMPTZ,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                )
            """))
            
            # Update audit_logs table
            conn.execute(text("""
                ALTER TABLE audit_logs 
                ADD COLUMN IF NOT EXISTS church_id INTEGER REFERENCES churches(id),
                ADD COLUMN IF NOT EXISTS details_json JSONB,
                ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW()
            """))
            
            # Update existing churches to have REGISTERED state if they have basic info
            conn.execute(text("""
                UPDATE churches 
                SET kyc_state = 'REGISTERED' 
                WHERE kyc_state = 'UNREGISTERED' 
                AND name IS NOT NULL 
                AND email IS NOT NULL
            """))
            
            # Commit the changes
            conn.commit()
            
            
            
    except Exception as e:
        }")
        raise

if __name__ == "__main__":
    run_migration()
