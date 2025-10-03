"""
Optimize donor payment flow migration

This migration restructures the donor payment flow to eliminate redundancy:

1. Removes payment_transactions table (redundant with donor_payouts)
2. Updates donation_batches to store church-level aggregated totals only
3. Updates donor_payouts to store individual donor donation records with business logic
4. Stripe transaction details fetched via API instead of stored locally

WORKFLOW OPTIMIZATION:
- Individual donations: stored in donor_payouts with roundup multiplier and business context
- Church totals: aggregated in donation_batches for payout processing
- Stripe details: fetched via stripe_payment_intent_id when needed (not stored)

This eliminates duplicate fields and follows the principle:
Store business logic locally, fetch payment details from Stripe API
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from datetime import datetime, timezone

def get_database_url():
    """Get database URL from environment variables"""
    # Try DATABASE_URL first (full connection string)
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        return database_url
    
    # Fallback to individual components
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    db_name = os.getenv('DB_NAME', 'manna_db')
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD', '')
    
    return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

def optimize_donor_payment_flow():
    """Optimize donor payment flow by removing redundant tables and fields"""
    
    # Load environment variables from .env file if it exists
    env_file = os.path.join(os.path.dirname(__file__), '..', '.env')
    if os.path.exists(env_file):
        print(f"Loading environment from {env_file}")
        with open(env_file, 'r') as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
    else:
        print("No .env file found, using environment variables or defaults")
    
    # Create database connection
    database_url = get_database_url()
    print(f"Connecting to database: {database_url.split('@')[0]}@***")
    
    try:
        engine = create_engine(database_url)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        
        print("Starting donor payment flow optimization...")
        
        # Step 1: Update donation_batches table structure
        print("Step 1: Updating donation_batches table structure...")
        
        # Check if old columns exist
        result = session.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'donation_batches' 
            AND column_name IN ('user_id', 'total_amount', 'processing_fees', 'multiplier_applied')
        """))
        old_columns = [row[0] for row in result.fetchall()]
        
        if old_columns:
            print(f"Found old donation_batches columns: {old_columns}")
            
            # Add new columns if they don't exist
            session.execute(text("""
                ALTER TABLE donation_batches 
                ADD COLUMN IF NOT EXISTS total_gross_amount NUMERIC(12,2),
                ADD COLUMN IF NOT EXISTS total_processing_fees NUMERIC(10,2) DEFAULT 0.00,
                ADD COLUMN IF NOT EXISTS total_net_amount NUMERIC(12,2),
                ADD COLUMN IF NOT EXISTS donor_count INTEGER DEFAULT 0,
                ADD COLUMN IF NOT EXISTS total_donations INTEGER DEFAULT 0,
                ADD COLUMN IF NOT EXISTS batch_period VARCHAR(50),
                ADD COLUMN IF NOT EXISTS church_payout_id INTEGER REFERENCES church_payouts(id)
            """))
            
            # Remove user_id constraint and column (donation_batches should be church-level)
            session.execute(text("""
                ALTER TABLE donation_batches DROP COLUMN IF EXISTS user_id CASCADE
            """))
            
            # Remove redundant columns
            session.execute(text("""
                ALTER TABLE donation_batches 
                DROP COLUMN IF EXISTS total_amount,
                DROP COLUMN IF EXISTS processing_fees,
                DROP COLUMN IF EXISTS multiplier_applied,
                DROP COLUMN IF EXISTS roundup_count,
                DROP COLUMN IF EXISTS collection_date,
                DROP COLUMN IF EXISTS stripe_payment_intent_id,
                DROP COLUMN IF EXISTS retry_attempts,
                DROP COLUMN IF EXISTS last_retry_at
            """))
            
            print("Updated donation_batches table structure")
        
        # Step 2: Update donor_payouts table structure
        print("Step 2: Updating donor_payouts table structure...")
        
        # Check if old columns exist
        result = session.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'donor_payouts' 
            AND column_name IN ('gross_amount', 'processing_fees', 'net_amount')
        """))
        old_donor_columns = [row[0] for row in result.fetchall()]
        
        if old_donor_columns:
            print(f"Found old donor_payouts columns: {old_donor_columns}")
            
            # Add new columns
            session.execute(text("""
                ALTER TABLE donor_payouts 
                ADD COLUMN IF NOT EXISTS donation_amount NUMERIC(10,2),
                ADD COLUMN IF NOT EXISTS roundup_multiplier NUMERIC(3,1) DEFAULT 2.0,
                ADD COLUMN IF NOT EXISTS base_roundup_amount NUMERIC(10,2),
                ADD COLUMN IF NOT EXISTS plaid_transaction_count INTEGER DEFAULT 0,
                ADD COLUMN IF NOT EXISTS donation_type VARCHAR(20) DEFAULT 'roundup',
                ADD COLUMN IF NOT EXISTS donation_summary JSONB
            """))
            
            # Migrate data from old columns to new columns (only if old columns exist)
            result = session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'donor_payouts' 
                AND column_name = 'gross_amount'
            """))
            
            if result.fetchone():
                session.execute(text("""
                    UPDATE donor_payouts 
                    SET donation_amount = gross_amount,
                        base_roundup_amount = COALESCE(gross_amount / 2.0, 0),
                        plaid_transaction_count = COALESCE(transaction_count, 0)
                    WHERE donation_amount IS NULL
                """))
                print("Migrated data from old columns to new columns")
            else:
                print("Old columns don't exist, skipping data migration")
            
            # Remove redundant columns
            session.execute(text("""
                ALTER TABLE donor_payouts 
                DROP COLUMN IF EXISTS gross_amount,
                DROP COLUMN IF EXISTS processing_fees,
                DROP COLUMN IF EXISTS net_amount,
                DROP COLUMN IF EXISTS transaction_count,
                DROP COLUMN IF EXISTS stripe_charge_id,
                DROP COLUMN IF EXISTS roundup_summary
            """))
            
            # Check if collection_period column exists (it should already exist)
            result = session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'donor_payouts' 
                AND column_name = 'collection_period'
            """))
            
            if not result.fetchone():
                # Add collection_period if it doesn't exist
                session.execute(text("""
                    ALTER TABLE donor_payouts 
                    ADD COLUMN collection_period VARCHAR(50)
                """))
                print("Added missing collection_period column")
            else:
                print("collection_period column already exists")
            
            print("Updated donor_payouts table structure")
        
        # Step 3: Drop payment_transactions table (redundant)
        print("Step 3: Removing redundant payment_transactions table...")
        
        result = session.execute(text("""
            SELECT COUNT(*) as count 
            FROM information_schema.tables 
            WHERE table_name = 'payment_transactions'
        """))
        table_exists = result.fetchone()[0] > 0
        
        if table_exists:
            # Get row count before dropping
            result = session.execute(text("SELECT COUNT(*) FROM payment_transactions"))
            row_count = result.fetchone()[0]
            print(f"Found payment_transactions table with {row_count} rows")
            
            # Drop the table
            session.execute(text("DROP TABLE IF EXISTS payment_transactions CASCADE"))
            print(f"Dropped payment_transactions table ({row_count} rows removed)")
        else:
            print("payment_transactions table does not exist")
        
        session.commit()
        print("Donor payment flow optimization completed successfully!")
        print("")
        print("OPTIMIZED WORKFLOW:")
        print("1. Individual donations → donor_payouts (business logic + stripe_payment_intent_id)")
        print("2. Church totals → donation_batches (aggregated amounts for payouts)")
        print("3. Stripe details → Fetched via API when needed (not stored locally)")
        print("4. Eliminated redundant payment_transactions table")
        
    except Exception as e:
        if 'session' in locals():
            session.rollback()
            session.close()
        print(f"Error during migration: {e}")
        print("This might be due to:")
        print("1. Database not running")
        print("2. Missing .env file with database credentials")
        print("3. Incorrect database connection parameters")
        print("4. Foreign key constraints")
        return False
    
    return True

if __name__ == "__main__":
    optimize_donor_payment_flow()
