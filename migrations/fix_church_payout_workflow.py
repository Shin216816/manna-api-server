"""
Fix Church Payout Workflow Migration

This migration updates the ChurchPayout model to reflect the correct workflow:
1. Calculate church earnings from donor_payouts (minus system fees)
2. Execute Stripe transfer to church
3. If transfer succeeds, create ChurchPayout record with stripe_transfer_id
4. Mark donor_payouts as allocated

Changes:
- Rename gross_amount -> gross_donation_amount (clearer naming)
- Rename manna_fee_amount -> system_fee_amount (clearer naming) 
- Rename manna_fee_percentage -> system_fee_percentage (clearer naming)
- Rename net_amount -> net_payout_amount (clearer naming)
- Rename total_transactions -> donation_count (clearer naming)
- Make stripe_transfer_id NOT NULL (required - proves transfer succeeded)
- Update default status to 'completed' (payouts only created after successful transfer)
"""

import os
import sys
from datetime import datetime, timezone
from sqlalchemy import create_engine, text, MetaData, Table, Column, Integer, String, Numeric, DateTime, Boolean, Text, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import sessionmaker

# Add the parent directory to the path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_database_url():
    """Get database URL from environment variables"""
    import os
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    # Get database credentials
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    db_name = os.getenv('DB_NAME', 'manna_db')
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD', '')
    
    return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

def migrate_church_payout_structure():
    """Update ChurchPayout table structure for correct workflow"""
    
    # Create database connection
    database_url = get_database_url()
    engine = create_engine(database_url)
    
    print(f"[MIGRATION] Connecting to database...")
    
    with engine.connect() as connection:
        # Start transaction
        trans = connection.begin()
        
        try:
            print("[MIGRATION] Starting ChurchPayout structure migration...")
            
            # Check if church_payouts table exists
            result = connection.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'church_payouts'
                );
            """))
            
            table_exists = result.scalar()
            
            if not table_exists:
                print("[MIGRATION] church_payouts table does not exist. Creating new table with correct structure...")
                
                # Create new table with correct structure
                connection.execute(text("""
                    CREATE TABLE church_payouts (
                        id SERIAL PRIMARY KEY,
                        church_id INTEGER NOT NULL REFERENCES churches(id),
                        gross_donation_amount NUMERIC(12,2) NOT NULL,
                        system_fee_amount NUMERIC(10,2) NOT NULL DEFAULT 0.00,
                        system_fee_percentage NUMERIC(5,4) NOT NULL DEFAULT 0.05,
                        net_payout_amount NUMERIC(12,2) NOT NULL,
                        donor_count INTEGER NOT NULL DEFAULT 0,
                        donation_count INTEGER NOT NULL DEFAULT 0,
                        period_start VARCHAR(20) NOT NULL,
                        period_end VARCHAR(20) NOT NULL,
                        stripe_transfer_id VARCHAR(100) NOT NULL UNIQUE,
                        status VARCHAR(20) NOT NULL DEFAULT 'completed',
                        failure_reason TEXT,
                        payout_breakdown JSON,
                        created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                        processed_at TIMESTAMP WITH TIME ZONE,
                        failed_at TIMESTAMP WITH TIME ZONE
                    );
                """))
                
                # Create indexes
                connection.execute(text("""
                    CREATE INDEX idx_church_payouts_church_id ON church_payouts(church_id);
                    CREATE INDEX idx_church_payouts_stripe_transfer_id ON church_payouts(stripe_transfer_id);
                    CREATE INDEX idx_church_payouts_created_at ON church_payouts(created_at);
                """))
                
                print("[MIGRATION] Created new church_payouts table with correct structure")
                
            else:
                print("[MIGRATION] church_payouts table exists. Updating structure...")
                
                # Check current columns
                result = connection.execute(text("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_name = 'church_payouts' 
                    AND table_schema = 'public'
                    ORDER BY ordinal_position;
                """))
                
                existing_columns = {row[0]: row for row in result.fetchall()}
                print(f"[MIGRATION] Found existing columns: {list(existing_columns.keys())}")
                
                # Map existing columns to new structure based on actual schema
                # Current columns: amount_transferred, manna_fees, net_amount, payout_period_start, payout_period_end, total_roundups_processed
                column_mappings = [
                    ('amount_transferred', 'gross_donation_amount'),
                    ('manna_fees', 'system_fee_amount'), 
                    ('payout_period_start', 'period_start'),
                    ('payout_period_end', 'period_end'),
                    ('total_roundups_processed', 'donation_count')
                ]
                
                for old_name, new_name in column_mappings:
                    if old_name in existing_columns and new_name not in existing_columns:
                        print(f"[MIGRATION] Renaming column {old_name} -> {new_name}")
                        connection.execute(text(f"""
                            ALTER TABLE church_payouts 
                            RENAME COLUMN {old_name} TO {new_name};
                        """))
                
                # Add missing columns
                missing_columns = [
                    ('system_fee_percentage', 'NUMERIC(5,4) NOT NULL DEFAULT 0.05'),
                    ('net_payout_amount', 'NUMERIC(12,2) NOT NULL DEFAULT 0.00'),
                    ('failure_reason', 'TEXT'),
                    ('payout_breakdown', 'JSON'),
                    ('processed_at', 'TIMESTAMP WITH TIME ZONE'),
                    ('failed_at', 'TIMESTAMP WITH TIME ZONE')
                ]
                
                # Refresh existing columns after renames
                result = connection.execute(text("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'church_payouts' AND table_schema = 'public';
                """))
                current_columns = {row[0] for row in result.fetchall()}
                
                for col_name, col_definition in missing_columns:
                    if col_name not in current_columns:
                        print(f"[MIGRATION] Adding column {col_name}")
                        connection.execute(text(f"""
                            ALTER TABLE church_payouts 
                            ADD COLUMN {col_name} {col_definition};
                        """))
                
                # Calculate net_payout_amount from existing data if it's empty
                print("[MIGRATION] Calculating net_payout_amount from existing data")
                connection.execute(text("""
                    UPDATE church_payouts 
                    SET net_payout_amount = COALESCE(net_amount, 0.00)
                    WHERE net_payout_amount = 0.00 OR net_payout_amount IS NULL;
                """))
                
                # Update stripe_transfer_id to be NOT NULL if it's currently nullable
                # But first, we need to handle existing NULL values
                if 'stripe_transfer_id' in existing_columns:
                    # Check for NULL values
                    result = connection.execute(text("""
                        SELECT COUNT(*) FROM church_payouts 
                        WHERE stripe_transfer_id IS NULL;
                    """))
                    null_count = result.scalar()
                    
                    if null_count > 0:
                        print(f"[MIGRATION] Found {null_count} records with NULL stripe_transfer_id")
                        print("[MIGRATION] Setting placeholder values for existing NULL stripe_transfer_ids")
                        
                        # Set placeholder values for NULL stripe_transfer_ids
                        connection.execute(text("""
                            UPDATE church_payouts 
                            SET stripe_transfer_id = 'LEGACY_' || id::text || '_' || EXTRACT(EPOCH FROM created_at)::text
                            WHERE stripe_transfer_id IS NULL;
                        """))
                    
                    # Now make the column NOT NULL
                    print("[MIGRATION] Making stripe_transfer_id NOT NULL")
                    connection.execute(text("""
                        ALTER TABLE church_payouts 
                        ALTER COLUMN stripe_transfer_id SET NOT NULL;
                    """))
                
                # Update default status if needed
                print("[MIGRATION] Updating default status to 'completed'")
                connection.execute(text("""
                    ALTER TABLE church_payouts 
                    ALTER COLUMN status SET DEFAULT 'completed';
                """))
                
                # Update existing 'pending' status records to 'completed' since they exist
                result = connection.execute(text("""
                    UPDATE church_payouts 
                    SET status = 'completed' 
                    WHERE status = 'pending' AND stripe_transfer_id IS NOT NULL;
                """))
                
                updated_count = result.rowcount
                if updated_count > 0:
                    print(f"[MIGRATION] Updated {updated_count} pending payouts to completed status")
            
            # Commit transaction
            trans.commit()
            print("[MIGRATION] ChurchPayout structure migration completed successfully!")
            
        except Exception as e:
            # Rollback on error
            trans.rollback()
            print(f"[MIGRATION ERROR] Failed to migrate ChurchPayout structure: {e}")
            raise e

def main():
    """Run the migration"""
    try:
        migrate_church_payout_structure()
        print("\n[SUCCESS] ChurchPayout workflow migration completed!")
        
    except Exception as e:
        print(f"\n[ERROR] Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
