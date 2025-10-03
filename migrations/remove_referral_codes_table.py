#!/usr/bin/env python3
"""
Migration: Remove referral_codes table

This migration removes the unused referral_codes table since:
1. The table is completely unused (no queries, no imports, no exports)
2. ChurchReferral table already handles all referral functionality
3. No data is stored in referral_codes table
4. Removing unused tables improves database performance

Date: 2024-12-19
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.database import engine
from sqlalchemy import text

def remove_referral_codes_table():
    """Remove the referral_codes table"""
    
    with engine.connect() as conn:
        try:
            # Drop the referral_codes table
            conn.execute(text("DROP TABLE IF EXISTS referral_codes"))
            conn.commit()
            print("✅ Successfully dropped referral_codes table")
            
        except Exception as e:
            print(f"❌ Error dropping referral_codes table: {e}")
            conn.rollback()
            raise

if __name__ == "__main__":
    print("🔄 Removing referral_codes table...")
    remove_referral_codes_table()
    print("✅ Migration completed successfully")
