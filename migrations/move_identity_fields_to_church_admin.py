"""
Migration script to move identity fields from users to church_admins table
and remove fcm_token from users table.

This script:
1. Adds identity fields to church_admins table
2. Migrates existing identity data from users to church_admins
3. Removes identity fields and fcm_token from users table
"""

import logging
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.utils.database import engine


def migrate_identity_fields():
    """Migrate identity fields from users to church_admins table"""
    
    with engine.connect() as connection:
        try:
            # 1. Add identity fields to church_admins table
            logger.info("Adding identity fields to church_admins table...")
            
            # Add stripe_identity_session_id column
            connection.execute(text("""
                ALTER TABLE church_admins 
                ADD COLUMN IF NOT EXISTS stripe_identity_session_id VARCHAR(255) UNIQUE;
            """))
            
            # Add identity_verification_status column
            connection.execute(text("""
                ALTER TABLE church_admins 
                ADD COLUMN IF NOT EXISTS identity_verification_status VARCHAR(50) DEFAULT 'not_started';
            """))
            
            # Add identity_verification_date column
            connection.execute(text("""
                ALTER TABLE church_admins 
                ADD COLUMN IF NOT EXISTS identity_verification_date TIMESTAMP WITH TIME ZONE;
            """))
            
            connection.commit()
            logger.info("Successfully added identity fields to church_admins table")
            
            # 2. Migrate existing identity data from users to church_admins
            logger.info("Migrating identity data from users to church_admins...")
            
            # Get users with identity data who are church admins
            result = connection.execute(text("""
                SELECT u.id as user_id, u.stripe_identity_session_id, u.identity_verification_status, u.identity_verification_date
                FROM users u
                INNER JOIN church_admins ca ON u.id = ca.user_id
                WHERE u.stripe_identity_session_id IS NOT NULL 
                   OR u.identity_verification_status != 'not_started'
                   OR u.identity_verification_date IS NOT NULL;
            """))
            
            migrated_count = 0
            for row in result:
                user_id = row.user_id
                session_id = row.stripe_identity_session_id
                status = row.identity_verification_status
                date = row.identity_verification_date
                
                # Update church_admin record with identity data
                connection.execute(text("""
                    UPDATE church_admins 
                    SET stripe_identity_session_id = :session_id,
                        identity_verification_status = :status,
                        identity_verification_date = :date,
                        updated_at = NOW()
                    WHERE user_id = :user_id;
                """), {
                    "session_id": session_id,
                    "status": status,
                    "date": date,
                    "user_id": user_id
                })
                
                migrated_count += 1
                logger.info(f"Migrated identity data for user {user_id}")
            
            connection.commit()
            logger.info(f"Successfully migrated identity data for {migrated_count} users")
            
            # 3. Remove identity fields and fcm_token from users table
            logger.info("Removing identity fields and fcm_token from users table...")
            
            # Remove fcm_token column
            connection.execute(text("""
                ALTER TABLE users DROP COLUMN IF EXISTS fcm_token;
            """))
            
            # Remove stripe_identity_session_id column
            connection.execute(text("""
                ALTER TABLE users DROP COLUMN IF EXISTS stripe_identity_session_id;
            """))
            
            # Remove identity_verification_status column
            connection.execute(text("""
                ALTER TABLE users DROP COLUMN IF EXISTS identity_verification_status;
            """))
            
            # Remove identity_verification_date column
            connection.execute(text("""
                ALTER TABLE users DROP COLUMN IF EXISTS identity_verification_date;
            """))
            
            connection.commit()
            logger.info("Successfully removed identity fields and fcm_token from users table")
            
            # 4. Add indexes for performance
            logger.info("Adding indexes for identity fields...")
            
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_church_admins_identity_session 
                ON church_admins(stripe_identity_session_id) WHERE stripe_identity_session_id IS NOT NULL;
            """))
            
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_church_admins_identity_status 
                ON church_admins(identity_verification_status);
            """))
            
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_church_admins_identity_date 
                ON church_admins(identity_verification_date) WHERE identity_verification_date IS NOT NULL;
            """))
            
            connection.commit()
            logger.info("Successfully added indexes for identity fields")
            
        except Exception as e:
            logger.error(f"Error during migration: {str(e)}")
            connection.rollback()
            raise

def verify_migration():
    """Verify that the migration was successful"""
    
    with engine.connect() as connection:
        try:
            # Check that identity fields exist in church_admins
            result = connection.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'church_admins' 
                AND column_name IN ('stripe_identity_session_id', 'identity_verification_status', 'identity_verification_date');
            """))
            
            church_admin_columns = [row.column_name for row in result]
            logger.info(f"Identity columns in church_admins: {church_admin_columns}")
            
            # Check that identity fields are removed from users
            result = connection.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'users' 
                AND column_name IN ('fcm_token', 'stripe_identity_session_id', 'identity_verification_status', 'identity_verification_date');
            """))
            
            user_columns = [row.column_name for row in result]
            logger.info(f"Removed columns from users: {user_columns}")
            
            # Check migration count
            result = connection.execute(text("""
                SELECT COUNT(*) as count
                FROM church_admins 
                WHERE stripe_identity_session_id IS NOT NULL 
                   OR identity_verification_status != 'not_started'
                   OR identity_verification_date IS NOT NULL;
            """))
            
            migrated_count = result.scalar()
            logger.info(f"Total church_admins with identity data: {migrated_count}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error during verification: {str(e)}")
            return False

if __name__ == "__main__":
    logger.info("Starting migration to move identity fields to church_admins table...")
    
    try:
        migrate_identity_fields()
        
        if verify_migration():
            logger.info("Migration completed successfully!")
        else:
            logger.error("Migration verification failed!")
            
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        sys.exit(1)
