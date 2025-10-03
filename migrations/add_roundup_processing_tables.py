"""
Add Roundup Processing Tables Migration

Adds tables for pending roundups, email verification, and Plaid transactions.
"""

from sqlalchemy import text
from app.utils.database import engine

def upgrade():
    """Add new tables for roundup processing"""
    
    # Create pending_roundups table
    engine.execute(text("""
        CREATE TABLE IF NOT EXISTS pending_roundups (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            transaction_id VARCHAR(255) NOT NULL,
            account_id VARCHAR(255) NOT NULL,
            payout_id INTEGER REFERENCES donor_payouts(id),
            original_amount DECIMAL(10,2) NOT NULL,
            roundup_amount DECIMAL(10,2) NOT NULL,
            merchant_name VARCHAR(255),
            category JSON,
            transaction_date TIMESTAMP WITH TIME ZONE NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            collected_at TIMESTAMP WITH TIME ZONE,
            status VARCHAR(20) DEFAULT 'pending',
            CONSTRAINT pending_roundups_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id),
            CONSTRAINT pending_roundups_payout_id_fkey FOREIGN KEY (payout_id) REFERENCES donor_payouts(id)
        );
    """))
    
    # Create indexes for pending_roundups
    engine.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_pending_roundups_user_id ON pending_roundups(user_id);
        CREATE INDEX IF NOT EXISTS idx_pending_roundups_transaction_id ON pending_roundups(transaction_id);
        CREATE INDEX IF NOT EXISTS idx_pending_roundups_status ON pending_roundups(status);
    """))
    
    # Create email_verifications table
    engine.execute(text("""
        CREATE TABLE IF NOT EXISTS email_verifications (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            token VARCHAR(255) UNIQUE NOT NULL,
            type VARCHAR(50) NOT NULL,
            status VARCHAR(20) DEFAULT 'pending',
            expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
            verified_at TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            CONSTRAINT email_verifications_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id)
        );
    """))
    
    # Create indexes for email_verifications
    engine.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_email_verifications_token ON email_verifications(token);
        CREATE INDEX IF NOT EXISTS idx_email_verifications_user_id ON email_verifications(user_id);
        CREATE INDEX IF NOT EXISTS idx_email_verifications_type ON email_verifications(type);
    """))
    
    # Create plaid_transactions table
    engine.execute(text("""
        CREATE TABLE IF NOT EXISTS plaid_transactions (
            id SERIAL PRIMARY KEY,
            plaid_item_id INTEGER NOT NULL REFERENCES plaid_items(id),
            transaction_id VARCHAR(255) UNIQUE NOT NULL,
            account_id VARCHAR(255) NOT NULL,
            amount DECIMAL(10,2) NOT NULL,
            merchant_name VARCHAR(255),
            category JSON,
            date TIMESTAMP WITH TIME ZONE NOT NULL,
            raw_data JSON,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            CONSTRAINT plaid_transactions_plaid_item_id_fkey FOREIGN KEY (plaid_item_id) REFERENCES plaid_items(id)
        );
    """))
    
    # Create indexes for plaid_transactions
    engine.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_plaid_transactions_plaid_item_id ON plaid_transactions(plaid_item_id);
        CREATE INDEX IF NOT EXISTS idx_plaid_transactions_transaction_id ON plaid_transactions(transaction_id);
        CREATE INDEX IF NOT EXISTS idx_plaid_transactions_date ON plaid_transactions(date);
    """))
    
    # Add stripe_payment_intent_id column to donor_payouts if it doesn't exist
    engine.execute(text("""
        ALTER TABLE donor_payouts 
        ADD COLUMN IF NOT EXISTS stripe_payment_intent_id VARCHAR(255);
    """))
    
    # Add stripe_default_payment_method_id column to users if it doesn't exist
    engine.execute(text("""
        ALTER TABLE users 
        ADD COLUMN IF NOT EXISTS stripe_default_payment_method_id VARCHAR(255);
    """))
    
    # Add stripe_connect_account_id column to churches if it doesn't exist
    engine.execute(text("""
        ALTER TABLE churches 
        ADD COLUMN IF NOT EXISTS stripe_connect_account_id VARCHAR(255);
    """))
    
    # Add stripe_transfer_id column to church_payouts if it doesn't exist
    engine.execute(text("""
        ALTER TABLE church_payouts 
        ADD COLUMN IF NOT EXISTS stripe_transfer_id VARCHAR(255);
    """))

def downgrade():
    """Remove the new tables"""
    
    # Drop tables in reverse order
    engine.execute(text("DROP TABLE IF EXISTS plaid_transactions CASCADE;"))
    engine.execute(text("DROP TABLE IF EXISTS email_verifications CASCADE;"))
    engine.execute(text("DROP TABLE IF EXISTS pending_roundups CASCADE;"))
    
    # Remove added columns
    engine.execute(text("ALTER TABLE donor_payouts DROP COLUMN IF EXISTS stripe_payment_intent_id;"))
    engine.execute(text("ALTER TABLE users DROP COLUMN IF EXISTS stripe_default_payment_method_id;"))
    engine.execute(text("ALTER TABLE churches DROP COLUMN IF EXISTS stripe_connect_account_id;"))
    engine.execute(text("ALTER TABLE church_payouts DROP COLUMN IF EXISTS stripe_transfer_id;"))

if __name__ == "__main__":
    upgrade()
    print("Migration completed successfully!")
