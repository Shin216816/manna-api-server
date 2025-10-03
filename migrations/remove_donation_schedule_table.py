"""
Remove donation_schedule table migration

This migration removes the donation_schedule table as it's not needed for the roundup-only donation system.
Roundup donations are triggered automatically by Plaid transactions, not by scheduled donations.
All donation settings are handled by the donation_preferences table.
"""

import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import logging

# Load environment variables
load_dotenv()

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Configure logging

def get_database_url():
    """Get database URL from environment variables"""
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD', '123123')
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    db_name = os.getenv('DB_NAME', 'manna_db')
    
    return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

def remove_donation_schedule_table():
    """Remove the donation_schedule table and related indexes"""
    
    database_url = get_database_url()
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        logger.info("Starting donation_schedule table removal...")
        
        # Check if table exists
        result = session.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'donation_schedules'
            );
        """))
        table_exists = result.scalar()
        
        if not table_exists:
            logger.info("donation_schedules table does not exist - nothing to remove")
            return
        
        # Check if there's any data in the table
        result = session.execute(text("SELECT COUNT(*) FROM donation_schedules"))
        row_count = result.scalar()
        logger.info(f"Found {row_count} rows in donation_schedules table")
        
        if row_count > 0:
            logger.warning(f"Table contains {row_count} rows - these will be lost!")
            response = input("Continue with deletion? (yes/no): ")
            if response.lower() != 'yes':
                logger.info("Migration cancelled by user")
                return
        
        # Drop the table (this will also drop associated indexes and constraints)
        logger.info("Dropping donation_schedules table...")
        session.execute(text("DROP TABLE IF EXISTS donation_schedules CASCADE"))
        session.commit()
        
        logger.info("✅ donation_schedules table removed successfully")
        logger.info("✅ All associated indexes and constraints removed")
        
        # Verify table is gone
        result = session.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'donation_schedules'
            );
        """))
        table_still_exists = result.scalar()
        
        if not table_still_exists:
            logger.info("✅ Verification: donation_schedules table successfully removed")
        else:
            logger.error("❌ Error: Table still exists after drop command")
            
    except Exception as e:
        logger.error(f"❌ Error during migration: {e}")
        session.rollback()
        raise
    finally:
        session.close()

def main():
    """Main migration function"""
    try:
        logger.info("=" * 60)
        logger.info("DONATION SCHEDULE TABLE REMOVAL MIGRATION")
        logger.info("=" * 60)
        
        remove_donation_schedule_table()
        
        logger.info("=" * 60)
        logger.info("MIGRATION COMPLETED SUCCESSFULLY")
        logger.info("=" * 60)
        logger.info("")
        logger.info("Summary of changes:")
        logger.info("- Removed donation_schedules table")
        logger.info("- Removed all associated indexes and constraints")
        logger.info("- System now uses only donation_preferences for roundup settings")
        logger.info("")
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
