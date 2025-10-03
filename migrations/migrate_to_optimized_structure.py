"""
Database Migration Script: Migrate to Optimized MVP Structure
============================================================

This script migrates the existing database to the new optimized structure
that aligns with MVP requirements for Manna's micro-donation platform.

Key Changes:
1. Unified User model for all user types
2. New ChurchMembership model for user-church relationships  
3. PlaidAccount model replacing BankAccount (encrypted access tokens only)
4. RoundupSettings model for user preferences
5. DonorPayout model for tracking money collected from donors
6. ChurchPayout model for tracking money sent to churches
7. Simplified payout tracking with direct relationships (PayoutAllocation removed)
8. Enhanced ChurchReferral and ReferralCommission models

IMPORTANT: This migration preserves existing data while adding new structure.
Run this AFTER backing up your database.
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from datetime import datetime, timezone
import logging

# Setup logging

def get_database_url():
    """Get database URL from environment"""
    host = os.getenv('DATABASE_HOST', 'localhost')
    port = os.getenv('DATABASE_PORT', '5432')
    user = os.getenv('DATABASE_USER', 'postgres')
    password = os.getenv('DATABASE_PASSWORD', '123123')
    name = os.getenv('DATABASE_NAME', 'manna_db')
    return f"postgresql://{user}:{password}@{host}:{port}/{name}"

def run_migration():
    """Execute the database migration"""
    
    logger.info("🚀 Starting database migration to optimized MVP structure...")
    
    # Create database connection
    engine = create_engine(get_database_url())
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # 1. Create new tables
        logger.info("📊 Creating new optimized tables...")
        
        # Create plaid_accounts table
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS plaid_accounts (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                plaid_item_id VARCHAR(100) UNIQUE NOT NULL,
                plaid_access_token_encrypted TEXT NOT NULL,
                account_id VARCHAR(100) NOT NULL,
                account_name VARCHAR(255),
                account_mask VARCHAR(10),
                account_type VARCHAR(20),
                institution_name VARCHAR(255),
                is_active BOOLEAN DEFAULT TRUE NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
                last_synced TIMESTAMP WITH TIME ZONE
            );
            CREATE INDEX IF NOT EXISTS idx_plaid_accounts_user_id ON plaid_accounts(user_id);
            CREATE INDEX IF NOT EXISTS idx_plaid_accounts_plaid_item_id ON plaid_accounts(plaid_item_id);
            CREATE INDEX IF NOT EXISTS idx_plaid_accounts_account_id ON plaid_accounts(account_id);
        """))
        
        # Create church_memberships table
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS church_memberships (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                church_id INTEGER NOT NULL REFERENCES churches(id),
                role VARCHAR(20) DEFAULT 'member' NOT NULL,
                is_active BOOLEAN DEFAULT TRUE NOT NULL,
                joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_church_memberships_user_id ON church_memberships(user_id);
            CREATE INDEX IF NOT EXISTS idx_church_memberships_church_id ON church_memberships(church_id);
            CREATE UNIQUE INDEX IF NOT EXISTS idx_church_memberships_user_church 
                ON church_memberships(user_id, church_id) WHERE is_active = TRUE;
        """))
        
        # Create roundup_settings table
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS roundup_settings (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                church_id INTEGER NOT NULL REFERENCES churches(id),
                collection_frequency VARCHAR(20) DEFAULT 'bi_weekly' NOT NULL,
                roundup_multiplier NUMERIC(3,1) DEFAULT 1.0 NOT NULL,
                monthly_cap NUMERIC(10,2),
                cover_processing_fees BOOLEAN DEFAULT FALSE NOT NULL,
                is_active BOOLEAN DEFAULT TRUE NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_roundup_settings_user_id ON roundup_settings(user_id);
            CREATE INDEX IF NOT EXISTS idx_roundup_settings_church_id ON roundup_settings(church_id);
            CREATE UNIQUE INDEX IF NOT EXISTS idx_roundup_settings_user_church 
                ON roundup_settings(user_id, church_id) WHERE is_active = TRUE;
        """))
        
        # Create donor_payouts table
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS donor_payouts (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                church_id INTEGER NOT NULL REFERENCES churches(id),
                stripe_charge_id VARCHAR(100) UNIQUE NOT NULL,
                amount_collected NUMERIC(10,2) NOT NULL,
                fees_covered_by_donor NUMERIC(10,2) DEFAULT 0.00 NOT NULL,
                net_amount NUMERIC(10,2) NOT NULL,
                collection_period_start TIMESTAMP WITH TIME ZONE NOT NULL,
                collection_period_end TIMESTAMP WITH TIME ZONE NOT NULL,
                transaction_count INTEGER DEFAULT 0 NOT NULL,
                roundup_multiplier_applied NUMERIC(3,1),
                monthly_cap_applied NUMERIC(10,2),
                status VARCHAR(20) DEFAULT 'pending' NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
                processed_at TIMESTAMP WITH TIME ZONE
            );
            CREATE INDEX IF NOT EXISTS idx_donor_payouts_user_id ON donor_payouts(user_id);
            CREATE INDEX IF NOT EXISTS idx_donor_payouts_church_id ON donor_payouts(church_id);
            CREATE INDEX IF NOT EXISTS idx_donor_payouts_stripe_charge_id ON donor_payouts(stripe_charge_id);
            CREATE INDEX IF NOT EXISTS idx_donor_payouts_status ON donor_payouts(status);
        """))
        
        # Create church_payouts table
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS church_payouts (
                id SERIAL PRIMARY KEY,
                church_id INTEGER NOT NULL REFERENCES churches(id),
                stripe_transfer_id VARCHAR(100) UNIQUE NOT NULL,
                amount_transferred NUMERIC(10,2) NOT NULL,
                manna_fees NUMERIC(10,2) DEFAULT 0.00 NOT NULL,
                net_amount NUMERIC(10,2) NOT NULL,
                payout_period_start TIMESTAMP WITH TIME ZONE NOT NULL,
                payout_period_end TIMESTAMP WITH TIME ZONE NOT NULL,
                donor_count INTEGER DEFAULT 0 NOT NULL,
                total_roundups_processed INTEGER DEFAULT 0 NOT NULL,
                status VARCHAR(20) DEFAULT 'pending' NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
                transferred_at TIMESTAMP WITH TIME ZONE
            );
            CREATE INDEX IF NOT EXISTS idx_church_payouts_church_id ON church_payouts(church_id);
            CREATE INDEX IF NOT EXISTS idx_church_payouts_stripe_transfer_id ON church_payouts(stripe_transfer_id);
            CREATE INDEX IF NOT EXISTS idx_church_payouts_status ON church_payouts(status);
        """))
        
        # payout_allocations table removed - overly complex junction table
        # Using direct church_id relationship and allocated_at timestamp instead
        
        # Add allocated_at column to donor_payouts for tracking allocation
        session.execute(text("""
            ALTER TABLE donor_payouts 
            ADD COLUMN IF NOT EXISTS allocated_at TIMESTAMP WITH TIME ZONE;
        """))
        
        session.commit()
        logger.info("✅ New tables created successfully!")
        
        # 2. Update existing tables with new columns
        logger.info("🔄 Adding new columns to existing tables...")
        
        # Add new fields to users table if they don't exist
        session.execute(text("""
            DO $$ 
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='password_hash') THEN
                    ALTER TABLE users ADD COLUMN password_hash TEXT;
                END IF;
                
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='last_login') THEN
                    ALTER TABLE users ADD COLUMN last_login TIMESTAMP WITH TIME ZONE;
                END IF;
            END $$;
        """))
        
        # Add new fields to churches table if they don't exist
        session.execute(text("""
            DO $$ 
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='churches' AND column_name='total_received') THEN
                    ALTER TABLE churches ADD COLUMN total_received NUMERIC(12,2) DEFAULT 0.00 NOT NULL;
                END IF;
                
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='churches' AND column_name='kyc_data') THEN
                    ALTER TABLE churches ADD COLUMN kyc_data JSON;
                END IF;
            END $$;
        """))
        
        # Update church_referrals table structure
        session.execute(text("""
            DO $$ 
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='church_referrals' AND column_name='commission_rate') THEN
                    ALTER TABLE church_referrals ADD COLUMN commission_rate NUMERIC(5,4) DEFAULT 0.10 NOT NULL;
                END IF;
                
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='church_referrals' AND column_name='total_commission_earned') THEN
                    ALTER TABLE church_referrals ADD COLUMN total_commission_earned NUMERIC(12,2) DEFAULT 0.00 NOT NULL;
                END IF;
                
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='church_referrals' AND column_name='commission_paid') THEN
                    ALTER TABLE church_referrals ADD COLUMN commission_paid BOOLEAN DEFAULT FALSE NOT NULL;
                END IF;
                
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='church_referrals' AND column_name='commission_period_months') THEN
                    ALTER TABLE church_referrals ADD COLUMN commission_period_months INTEGER DEFAULT 12 NOT NULL;
                END IF;
                
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='church_referrals' AND column_name='activated_at') THEN
                    ALTER TABLE church_referrals ADD COLUMN activated_at TIMESTAMP WITH TIME ZONE;
                END IF;
                
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='church_referrals' AND column_name='expires_at') THEN
                    ALTER TABLE church_referrals ADD COLUMN expires_at TIMESTAMP WITH TIME ZONE;
                END IF;
            END $$;
        """))
        
        # Update referral_commissions table structure
        session.execute(text("""
            DO $$ 
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='referral_commissions' AND column_name='church_referral_id') THEN
                    ALTER TABLE referral_commissions ADD COLUMN church_referral_id INTEGER REFERENCES church_referrals(id);
                END IF;
                
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='referral_commissions' AND column_name='church_payout_id') THEN
                    ALTER TABLE referral_commissions ADD COLUMN church_payout_id INTEGER REFERENCES church_payouts(id);
                END IF;
                
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='referral_commissions' AND column_name='commission_amount') THEN
                    ALTER TABLE referral_commissions ADD COLUMN commission_amount NUMERIC(10,2);
                END IF;
                
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='referral_commissions' AND column_name='period_start') THEN
                    ALTER TABLE referral_commissions ADD COLUMN period_start VARCHAR(20);
                END IF;
                
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='referral_commissions' AND column_name='period_end') THEN
                    ALTER TABLE referral_commissions ADD COLUMN period_end VARCHAR(20);
                END IF;
            END $$;
        """))
        
        session.commit()
        logger.info("✅ Table updates completed successfully!")
        
        # 3. Migrate existing data
        logger.info("📦 Migrating existing data...")
        
        # Migrate existing plaid items to plaid accounts
        session.execute(text("""
            INSERT INTO plaid_accounts (
                user_id, plaid_item_id, plaid_access_token_encrypted, 
                account_id, account_name, account_mask, account_type, 
                institution_name, is_active, created_at, updated_at
            )
            SELECT 
                user_id, 
                COALESCE(item_id, 'legacy_' || id::text) as plaid_item_id,
                access_token as plaid_access_token_encrypted,
                'legacy_account_' || id::text as account_id,
                'Legacy Account' as account_name,
                '****' as account_mask,
                'checking' as account_type,
                'Legacy Institution' as institution_name,
                CASE WHEN status = 'active' THEN TRUE ELSE FALSE END as is_active,
                COALESCE(created_at, NOW()) as created_at,
                COALESCE(created_at, NOW()) as updated_at
            FROM plaid_items 
            WHERE NOT EXISTS (
                SELECT 1 FROM plaid_accounts 
                WHERE plaid_accounts.user_id = plaid_items.user_id
            );
        """))
        
        # Create default church memberships for existing relationships
        # This attempts to infer church memberships from existing data
        session.execute(text("""
            INSERT INTO church_memberships (user_id, church_id, role, is_active, joined_at, created_at)
            SELECT DISTINCT 
                u.id as user_id,
                COALESCE(ca.church_id, (SELECT MIN(id) FROM churches)) as church_id,  -- Use first available church
                CASE
                    WHEN ca.id IS NOT NULL THEN 'admin'
                    ELSE 'member'
                END as role,
                TRUE as is_active,
                COALESCE(u.created_at, NOW()) as joined_at,
                NOW() as created_at
            FROM users u
            LEFT JOIN church_admins ca ON u.id = ca.user_id
            WHERE NOT EXISTS (
                SELECT 1 FROM church_memberships cm
                WHERE cm.user_id = u.id
            )
            AND EXISTS (SELECT 1 FROM churches LIMIT 1);  -- Only if churches exist
        """))
        
        # Create default roundup settings for users with plaid accounts
        session.execute(text("""
            INSERT INTO roundup_settings (user_id, church_id, collection_frequency, roundup_multiplier, is_active, created_at, updated_at)
            SELECT DISTINCT
                cm.user_id,
                cm.church_id,
                'bi_weekly' as collection_frequency,
                1.0 as roundup_multiplier,
                TRUE as is_active,
                NOW() as created_at,
                NOW() as updated_at
            FROM church_memberships cm
            INNER JOIN plaid_accounts pa ON cm.user_id = pa.user_id
            WHERE NOT EXISTS (
                SELECT 1 FROM roundup_settings rs 
                WHERE rs.user_id = cm.user_id AND rs.church_id = cm.church_id
            );
        """))
        
        session.commit()
        logger.info("✅ Data migration completed successfully!")
        
        # 4. Create indexes for performance
        logger.info("⚡ Creating performance indexes...")
        
        session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
            CREATE INDEX IF NOT EXISTS idx_users_email_verified ON users(is_email_verified);
            CREATE INDEX IF NOT EXISTS idx_churches_kyc_status ON churches(kyc_status);
            CREATE INDEX IF NOT EXISTS idx_churches_stripe_account ON churches(stripe_account_id);
        """))
        
        session.commit()
        logger.info("✅ Performance indexes created!")
        
        # 5. Update sequences
        logger.info("🔢 Updating database sequences...")
        
        sequences_to_update = [
            'plaid_accounts_id_seq',
            'church_memberships_id_seq', 
            'roundup_settings_id_seq',
            'donor_payouts_id_seq',
            'church_payouts_id_seq',
            # 'payout_allocations_id_seq' - removed with payout_allocations table
        ]
        
        for seq in sequences_to_update:
            try:
                session.execute(text(f"""
                    SELECT setval('{seq}', 
                        COALESCE((SELECT MAX(id) FROM {seq.replace('_id_seq', '')}), 1)
                    );
                """))
            except Exception as e:
                logger.warning(f"Could not update sequence {seq}: {e}")
        
        session.commit()
        logger.info("✅ Database sequences updated!")
        
        logger.info("🎉 Database migration completed successfully!")
        logger.info("📊 Migration Summary:")
        logger.info("   ✅ New optimized tables created")
        logger.info("   ✅ Existing data preserved and migrated")
        logger.info("   ✅ Performance indexes added")
        logger.info("   ✅ Database ready for MVP operations")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    success = run_migration()
    if success:
        print("🚀 Database migration completed successfully!")
        print("💡 Next steps:")
        print("   1. Test the new database structure")
        print("   2. Verify all API endpoints work correctly")
        print("   3. Run integration tests")
    else:
        print("❌ Migration failed. Check logs for details.")
