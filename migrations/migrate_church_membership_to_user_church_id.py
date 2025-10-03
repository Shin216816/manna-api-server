#!/usr/bin/env python3
"""
Migration script to replace church_membership table with direct church_id on users table.

This migration:
1. Adds church_id column to users table
2. Populates church_id from existing church_memberships data
3. Drops the church_memberships table
4. Updates any remaining references

Run this script after updating the models and controllers.
"""

import sys
import os
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text, MetaData, Table, Column, Integer, ForeignKey
from sqlalchemy.orm import sessionmaker
from app.config import config

def run_migration():
    """Execute the migration"""
    engine = create_engine(config.get_database_url)
    
    with engine.connect() as connection:
        # Start transaction
        trans = connection.begin()
        
        try:
            print("Starting church_membership to user.church_id migration...")
            
            # Step 1: Add church_id column to users table if it doesn't exist
            print("Step 1: Adding church_id column to users table...")
            try:
                connection.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN church_id INTEGER REFERENCES churches(id)
                """))
                print("+ Added church_id column to users table")
            except Exception as e:
                if "already exists" in str(e) or "duplicate column" in str(e).lower():
                    print("+ church_id column already exists")
                    # Rollback and start a new transaction
                    trans.rollback()
                    trans = connection.begin()
                else:
                    raise e
            
            # Step 2: Create index on church_id for performance
            print("Step 2: Creating index on users.church_id...")
            try:
                connection.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_users_church_id ON users(church_id)
                """))
                print("+ Created index on users.church_id")
            except Exception as e:
                print(f"Index creation warning: {e}")
            
            # Step 3: Populate church_id from church_memberships
            print("Step 3: Populating users.church_id from church_memberships...")
            
            # Get active memberships and update users
            result = connection.execute(text("""
                UPDATE users 
                SET church_id = cm.church_id
                FROM church_memberships cm
                WHERE users.id = cm.user_id 
                AND cm.is_active = true
                AND users.church_id IS NULL
            """))
            
            rows_updated = result.rowcount
            print(f"+ Updated {rows_updated} users with church_id from memberships")
            
            # Step 4: Handle users with multiple active memberships (take the first one)
            print("Step 4: Handling users with multiple memberships...")
            result = connection.execute(text("""
                WITH first_membership AS (
                    SELECT DISTINCT ON (user_id) user_id, church_id
                    FROM church_memberships 
                    WHERE is_active = true
                    ORDER BY user_id, created_at ASC
                )
                UPDATE users 
                SET church_id = fm.church_id
                FROM first_membership fm
                WHERE users.id = fm.user_id 
                AND users.church_id IS NULL
            """))
            
            additional_updates = result.rowcount
            print(f"+ Updated {additional_updates} additional users with multiple memberships")
            
            # Step 5: Update user roles based on church_membership roles
            print("Step 5: Updating user roles...")
            
            # Update church admins
            result = connection.execute(text("""
                UPDATE users 
                SET role = 'church_admin'
                FROM church_memberships cm
                WHERE users.id = cm.user_id 
                AND cm.is_active = true
                AND cm.role IN ('admin', 'primary_admin')
                AND users.role != 'manna_admin'
            """))
            
            admin_updates = result.rowcount
            print(f"+ Updated {admin_updates} users to church_admin role")
            
            # Update donors
            result = connection.execute(text("""
                UPDATE users 
                SET role = 'donor'
                FROM church_memberships cm
                WHERE users.id = cm.user_id 
                AND cm.is_active = true
                AND cm.role = 'member'
                AND users.role NOT IN ('church_admin', 'manna_admin')
            """))
            
            member_updates = result.rowcount
            print(f"+ Updated {member_updates} users to donor role")
            
            # Step 6: Verify data integrity
            print("Step 6: Verifying data integrity...")
            
            # Check for users without church_id (excluding manna_admins)
            result = connection.execute(text("""
                SELECT COUNT(*) as orphaned_users
                FROM users 
                WHERE church_id IS NULL 
                AND role != 'manna_admin'
                AND is_active = true
            """))
            
            orphaned_count = result.fetchone()[0]
            if orphaned_count > 0:
                print(f"! Warning: {orphaned_count} active users without church_id (excluding manna_admins)")
            else:
                print("+ All active users have church_id assigned")
            
            # Step 7: Drop church_memberships table
            print("Step 7: Dropping church_memberships table...")
            
            # First, drop any foreign key constraints that reference church_memberships
            try:
                connection.execute(text("DROP TABLE IF EXISTS church_memberships CASCADE"))
                print("+ Dropped church_memberships table")
            except Exception as e:
                print(f"Warning dropping table: {e}")
            
            # Step 8: Final verification
            print("Step 8: Final verification...")
            
            # Count users with church associations
            result = connection.execute(text("""
                SELECT 
                    COUNT(*) as total_users,
                    COUNT(church_id) as users_with_church,
                    COUNT(CASE WHEN role = 'donor' THEN 1 END) as donors,
                    COUNT(CASE WHEN role = 'church_admin' THEN 1 END) as church_admins,
                    COUNT(CASE WHEN role = 'manna_admin' THEN 1 END) as manna_admins
                FROM users 
                WHERE is_active = true
            """))
            
            stats = result.fetchone()
            print(f"+ Migration completed successfully!")
            print(f"  - Total active users: {stats[0]}")
            print(f"  - Users with church: {stats[1]}")
            print(f"  - Donors: {stats[2]}")
            print(f"  - Church admins: {stats[3]}")
            print(f"  - Manna admins: {stats[4]}")
            
            # Commit the transaction
            trans.commit()
            print("\n*** Migration completed successfully! ***")
            
        except Exception as e:
            # Rollback on error
            trans.rollback()
            print(f"\n*** Migration failed: {e} ***")
            raise e

def rollback_migration():
    """Rollback the migration (recreate church_memberships table)"""
    engine = create_engine(config.get_database_url)
    
    with engine.connect() as connection:
        trans = connection.begin()
        
        try:
            print("Starting rollback of church_membership migration...")
            
            # Recreate church_memberships table
            print("Step 1: Recreating church_memberships table...")
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS church_memberships (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    church_id INTEGER NOT NULL REFERENCES churches(id),
                    role VARCHAR(20) NOT NULL DEFAULT 'member',
                    is_active BOOLEAN NOT NULL DEFAULT true,
                    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """))
            
            # Recreate indexes
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_church_memberships_user_id ON church_memberships(user_id);
                CREATE INDEX IF NOT EXISTS idx_church_memberships_church_id ON church_memberships(church_id);
                CREATE INDEX IF NOT EXISTS idx_church_memberships_active ON church_memberships(is_active);
            """))
            
            # Populate from users table
            print("Step 2: Populating church_memberships from users...")
            connection.execute(text("""
                INSERT INTO church_memberships (user_id, church_id, role, is_active, joined_at, created_at)
                SELECT 
                    id as user_id,
                    church_id,
                    CASE 
                        WHEN role = 'church_admin' THEN 'admin'
                        WHEN role = 'congregant' THEN 'member'
                        ELSE 'member'
                    END as role,
                    true as is_active,
                    created_at as joined_at,
                    created_at
                FROM users 
                WHERE church_id IS NOT NULL
                AND is_active = true
            """))
            
            print("Step 3: Removing church_id column from users...")
            connection.execute(text("ALTER TABLE users DROP COLUMN IF EXISTS church_id"))
            
            trans.commit()
            print("+ Rollback completed successfully!")
            
        except Exception as e:
            trans.rollback()
            print(f"*** Rollback failed: {e} ***")
            raise e

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate church_membership table to user.church_id")
    parser.add_argument("--rollback", action="store_true", help="Rollback the migration")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without executing")
    
    args = parser.parse_args()
    
    if args.dry_run:
        print("DRY RUN MODE - No changes will be made")
        print("This migration would:")
        print("1. Add church_id column to users table")
        print("2. Populate church_id from church_memberships")
        print("3. Update user roles based on membership roles")
        print("4. Drop church_memberships table")
        print("\nRun without --dry-run to execute the migration")
    elif args.rollback:
        rollback_migration()
    else:
        run_migration()
