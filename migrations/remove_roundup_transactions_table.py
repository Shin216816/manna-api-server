#!/usr/bin/env python3
"""
Migration: Remove roundup_transactions table

This migration removes the redundant roundup_transactions table since:
1. DonationBatch table already stores all necessary roundup data
2. Individual transaction details are available from Plaid API
3. No need to duplicate data at different granularities

Date: 2024-12-19
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.database import engine
from sqlalchemy import text

def remove_roundup_transactions_table():
    """Remove the roundup_transactions table"""
    
    with engine.connect() as conn:
        try:
            # Drop the roundup_transactions table
            conn.execute(text("DROP TABLE IF EXISTS roundup_transactions"))
            conn.commit()
            print("✅ Successfully dropped roundup_transactions table")
            
        except Exception as e:
            print(f"❌ Error dropping roundup_transactions table: {e}")
            conn.rollback()
            raise

if __name__ == "__main__":
    print("🔄 Removing roundup_transactions table...")
    remove_roundup_transactions_table()
    print("✅ Migration completed successfully")
