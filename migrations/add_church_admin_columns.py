"""
Migration script to add missing columns to church_admins table.

This migration adds all the columns that are expected by the ChurchAdmin model
but missing from the current database schema.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.config import config
import logging

# Configure logging

def add_church_admin_columns():
    """Add missing columns to church_admins table"""
    try:
        # Create database engine
        engine = create_engine(config.get_database_url)
        
        with engine.connect() as connection:
            # List of columns to add with their definitions
            columns_to_add = [
                ("admin_name", "VARCHAR(255)"),
                ("permissions", "JSON"),
                ("is_primary_admin", "BOOLEAN DEFAULT FALSE"),
                ("can_manage_finances", "BOOLEAN DEFAULT TRUE"),
                ("can_manage_members", "BOOLEAN DEFAULT TRUE"),
                ("can_manage_settings", "BOOLEAN DEFAULT TRUE"),
                ("contact_email", "VARCHAR(255)"),
                ("contact_phone", "VARCHAR(50)"),
                ("admin_notes", "TEXT"),
                ("admin_metadata", "JSON"),
                ("last_activity", "TIMESTAMP WITH TIME ZONE")
            ]
            
            # Check which columns already exist
            existing_columns_query = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'church_admins'
            """)
            
            result = connection.execute(existing_columns_query)
            existing_columns = {row[0] for row in result}
            
            logger.info(f"Existing columns: {existing_columns}")
            
            # Add missing columns
            for column_name, column_type in columns_to_add:
                if column_name not in existing_columns:
                    add_column_query = text(f"""
                        ALTER TABLE church_admins 
                        ADD COLUMN {column_name} {column_type}
                    """)
                    
                    connection.execute(add_column_query)
                    logger.info(f"Added column: {column_name}")
                else:
                    logger.info(f"Column {column_name} already exists")
            
            connection.commit()
            logger.info("Successfully updated church_admins table")
            
            # Update existing church admins with default values
            update_query = text("""
                UPDATE church_admins 
                SET 
                    is_primary_admin = CASE 
                        WHEN role = 'admin' OR role = 'pastor' THEN TRUE 
                        ELSE FALSE 
                    END,
                    can_manage_finances = TRUE,
                    can_manage_members = TRUE,
                    can_manage_settings = TRUE,
                    permissions = CASE 
                        WHEN role = 'admin' OR role = 'pastor' THEN '["church_management", "user_management", "finances", "settings"]'::json
                        WHEN role = 'moderator' THEN '["user_management", "settings"]'::json
                        WHEN role = 'treasurer' THEN '["finances"]'::json
                        ELSE '["basic"]'::json
                    END
                WHERE is_primary_admin IS NULL
            """)
            
            connection.execute(update_query)
            connection.commit()
            
            logger.info("Successfully updated existing church admins with default values")
            
    except Exception as e:
        logger.error(f"Error adding church admin columns: {e}")
        raise

if __name__ == "__main__":
    add_church_admin_columns()
