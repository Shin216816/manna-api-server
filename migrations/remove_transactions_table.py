#!/usr/bin/env python3
"""
Migration: Remove transactions table

This migration removes the redundant transactions table since:
1. All transaction data is fetched directly from external APIs (Stripe/Plaid)
2. DonationBatch table already stores business logic data
3. No need to duplicate external data locally

Date: 2024-12-19
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.database import engine
from sqlalchemy import text

def remove_transactions_table():
    """Remove the transactions table"""
    
    with engine.connect() as conn:
        try:
            # Drop the transactions table
            conn.execute(text("DROP TABLE IF EXISTS transactions"))
            conn.commit()
            print("✅ Successfully dropped transactions table")
            
        except Exception as e:
            print(f"❌ Error dropping transactions table: {e}")
            conn.rollback()
            raise

if __name__ == "__main__":
    print("🔄 Removing transactions table...")
    remove_transactions_table()
    print("✅ Migration completed successfully")
