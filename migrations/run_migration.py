"""
Migration Runner for Manna Backend Database Optimization
========================================================

This script orchestrates the complete database migration process:
1. Creates a backup of the current database
2. Runs the migration to the optimized MVP structure  
3. Validates the migration with comprehensive tests
4. Provides rollback capability if needed

Usage:
    python migrations/run_migration.py [--backup-only] [--test-only] [--force]
    
Options:
    --backup-only    Only create a backup, don't run migration
    --test-only      Only run tests on existing database  
    --force          Skip confirmation prompts
"""

import argparse
import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging

def main():
    parser = argparse.ArgumentParser(description="Run Manna database migration")
    parser.add_argument('--backup-only', action='store_true', help='Only create backup')
    parser.add_argument('--test-only', action='store_true', help='Only run tests')
    parser.add_argument('--force', action='store_true', help='Skip confirmation prompts')
    
    args = parser.parse_args()
    
    logger.info("🚀 Manna Database Migration Runner")
    logger.info("=" * 50)
    
    # Step 1: Create backup
    if not args.test_only:
        logger.info("📦 Step 1: Creating database backup...")
        
        try:
            from migrations.backup_database import create_backup
            backup_path = create_backup()
            
            if not backup_path:
                logger.error("❌ Backup failed! Aborting migration.")
                return False
                
            logger.info(f"✅ Backup created: {backup_path}")
            
            if args.backup_only:
                logger.info("🎉 Backup completed successfully!")
                return True
                
        except ImportError as e:
            logger.error(f"❌ Could not import backup module: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Backup failed: {e}")
            return False
    
    # Confirmation prompt
    if not args.force and not args.test_only:
        print("\n⚠️  WARNING: This will modify your database structure!")
        print("Make sure you have:")
        print("  ✓ Created a backup (done above)")
        print("  ✓ Stopped all running API servers")
        print("  ✓ Informed team members about the migration")
        
        response = input("\nProceed with migration? (yes/no): ").lower().strip()
        if response not in ['yes', 'y']:
            logger.info("❌ Migration cancelled by user")
            return False
    
    # Step 2: Run migration
    if not args.test_only:
        logger.info("🔄 Step 2: Running database migration...")
        
        try:
            from migrations.migrate_to_optimized_structure import run_migration
            migration_success = run_migration()
            
            if not migration_success:
                logger.error("❌ Migration failed! Check logs for details.")
                return False
                
            logger.info("✅ Migration completed successfully!")
            
        except ImportError as e:
            logger.error(f"❌ Could not import migration module: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            return False
    
    # Step 3: Run validation tests
    logger.info("🧪 Step 3: Running validation tests...")
    
    try:
        from migrations.test_migration import main as test_main
        test_success = test_main()
        
        if not test_success:
            logger.error("❌ Migration validation failed!")
            if not args.test_only:
                print("\n🚨 MIGRATION VALIDATION FAILED!")
                print("The migration completed but validation tests failed.")
                print("You may want to:")
                print("  1. Review the test failures above")
                print("  2. Fix any issues manually") 
                print("  3. Re-run tests with: python migrations/run_migration.py --test-only")
                print("  4. Or rollback with your backup if needed")
            return False
            
        logger.info("✅ Validation tests passed!")
        
    except ImportError as e:
        logger.error(f"❌ Could not import test module: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Validation tests failed: {e}")
        return False
    
    # Success!
    if args.test_only:
        logger.info("🎉 Database validation completed successfully!")
    else:
        logger.info("🎉 Database migration completed successfully!")
        logger.info("")
        logger.info("📊 Migration Summary:")
        logger.info("   ✅ Database backup created")
        logger.info("   ✅ Migration executed successfully")
        logger.info("   ✅ Validation tests passed")
        logger.info("   ✅ Database ready for MVP operations")
        logger.info("")
        logger.info("🚀 Next Steps:")
        logger.info("   1. Update your application servers")
        logger.info("   2. Test API endpoints manually")
        logger.info("   3. Monitor application logs for issues")
        logger.info("   4. Remove old migration files when confident")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n❌ Migration cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 Migration runner failed: {e}")
        sys.exit(1)
