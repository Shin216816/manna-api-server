"""
Remove payment_methods table migration

This migration removes the payment_methods table since we're now using Stripe API directly
for payment method management instead of storing them locally.
"""

import logging
import os
import sys
from sqlalchemy import text

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.database import engine

def upgrade():
    """Remove the payment_methods table"""
    with engine.connect() as conn:
        # Drop the payment_methods table
        conn.execute(text("DROP TABLE IF EXISTS payment_methods CASCADE"))
        
        # Drop the sequence
        conn.execute(text("DROP SEQUENCE IF EXISTS payment_methods_id_seq CASCADE"))
        
        conn.commit()
    
    print("✅ payment_methods table and related objects removed successfully")

def downgrade():
    """Recreate the payment_methods table (if needed for rollback)"""
    with engine.connect() as conn:
        # Recreate the sequence
        conn.execute(text("""
            CREATE SEQUENCE payment_methods_id_seq
                START WITH 1
                INCREMENT BY 1
                NO MINVALUE
                NO MAXVALUE
                CACHE 1
        """))
        
        # Recreate the table
        conn.execute(text("""
            CREATE TABLE payment_methods (
                id INTEGER NOT NULL DEFAULT nextval('payment_methods_id_seq'::regclass),
                user_id INTEGER NOT NULL,
                stripe_payment_method_id VARCHAR(255) NOT NULL,
                type VARCHAR(50) NOT NULL,
                status VARCHAR(50) DEFAULT 'pending',
                is_default BOOLEAN DEFAULT false,
                card_brand VARCHAR(50),
                card_last4 VARCHAR(4),
                card_exp_month INTEGER,
                card_exp_year INTEGER,
                bank_name VARCHAR(255),
                bank_account_type VARCHAR(50),
                bank_account_last4 VARCHAR(4),
                wallet_type VARCHAR(50),
                payment_metadata TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
                updated_at TIMESTAMP WITH TIME ZONE,
                PRIMARY KEY (id),
                FOREIGN KEY(user_id) REFERENCES users (id),
                UNIQUE (stripe_payment_method_id)
            )
        """))
        
        # Create indexes
        conn.execute(text("CREATE INDEX ix_payment_methods_id ON payment_methods USING btree (id)"))
        conn.execute(text("CREATE INDEX ix_payment_methods_user_id ON payment_methods USING btree (user_id)"))
        
        conn.commit()
    
    print("✅ payment_methods table recreated (rollback)")

if __name__ == "__main__":
    upgrade()
