"""
Add profile_picture_url column to users table

This migration adds the profile_picture_url field to the users table
to support profile image uploads for all user types.
"""

import logging
from sqlalchemy import text
from app.utils.database import get_db

def run_migration():
    """Add profile_picture_url column to users table"""
    
    db = next(get_db())
    
    try:
        # Check if column already exists
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'profile_picture_url'
        """))
        
        if result.fetchone():
            print("Column 'profile_picture_url' already exists in users table")
            return
        
        # Add the profile_picture_url column
        db.execute(text("""
            ALTER TABLE users 
            ADD COLUMN profile_picture_url VARCHAR(500)
        """))
        
        db.commit()
        print("Successfully added profile_picture_url column to users table")
        
    except Exception as e:
        db.rollback()
        print(f"Error adding profile_picture_url column: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    run_migration()
