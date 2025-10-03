"""
Migration script to add missing permissions column to users table.

This migration adds the permissions column that is expected by the User model
but missing from the current database schema.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.config import config
import logging

# Configure logging

def add_user_permissions_column():
    """Add permissions column to users table"""
    try:
        # Create database engine
        engine = create_engine(config.get_database_url)
        
        with engine.connect() as connection:
            # Check if the column already exists
            check_query = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'permissions'
            """)
            
            result = connection.execute(check_query)
            if result.fetchone():
                logger.info("Column 'permissions' already exists in users table")
                return
            
            # Add the permissions column
            add_column_query = text("""
                ALTER TABLE users 
                ADD COLUMN permissions TEXT
            """)
            
            connection.execute(add_column_query)
            connection.commit()
            
            logger.info("Successfully added 'permissions' column to users table")
            
            # Update existing users with default permissions based on their role
            update_query = text("""
                UPDATE users 
                SET permissions = CASE 
                    WHEN role = 'super_admin' THEN '["admin", "church_management", "user_management", "analytics", "system_admin"]'
                    WHEN role = 'admin' THEN '["admin", "church_management", "user_management", "analytics"]'
                    WHEN role = 'church_admin' THEN '["church_management", "user_management", "analytics"]'
                    ELSE '["user"]'
                END
                WHERE permissions IS NULL
            """)
            
            connection.execute(update_query)
            connection.commit()
            
            logger.info("Successfully updated existing users with default permissions")
            
    except Exception as e:
        logger.error(f"Error adding permissions column: {e}")
        raise

if __name__ == "__main__":
    add_user_permissions_column()
