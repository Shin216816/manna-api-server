"""
Database Backup Script for Manna Backend
========================================

This script creates a complete backup of the database before migration.
ALWAYS run this before executing any migration scripts.
"""

import os
import subprocess
from datetime import datetime
import logging

# Setup logging

def get_database_config():
    """Get database configuration from environment"""
    return {
        'host': os.getenv('DATABASE_HOST', 'localhost'),
        'port': os.getenv('DATABASE_PORT', '5432'),
        'user': os.getenv('DATABASE_USER', 'postgres'),
        'password': os.getenv('DATABASE_PASSWORD', '123123'),
        'name': os.getenv('DATABASE_NAME', 'manna_db')
    }

def create_backup():
    """Create a database backup"""
    
    logger.info("🔄 Starting database backup...")
    
    config = get_database_config()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"manna_db_backup_{timestamp}.sql"
    backup_path = os.path.join("migrations", "backups", backup_filename)
    
    # Create backups directory if it doesn't exist
    os.makedirs(os.path.dirname(backup_path), exist_ok=True)
    
    # Set password environment variable for pg_dump
    env = os.environ.copy()
    env['PGPASSWORD'] = config['password']
    
    try:
        # Run pg_dump command
        cmd = [
            'pg_dump',
            '-h', config['host'],
            '-p', config['port'],
            '-U', config['user'],
            '-d', config['name'],
            '--verbose',
            '--clean',
            '--if-exists',
            '--create',
            '--format=plain',
            '--file', backup_path
        ]
        
        logger.info(f"📦 Creating backup: {backup_filename}")
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"✅ Backup created successfully: {backup_path}")
            
            # Get backup file size
            size_mb = os.path.getsize(backup_path) / (1024 * 1024)
            logger.info(f"📊 Backup size: {size_mb:.2f} MB")
            
            return backup_path
        else:
            logger.error(f"❌ Backup failed: {result.stderr}")
            return None
            
    except FileNotFoundError:
        logger.error("❌ pg_dump not found. Please install PostgreSQL client tools.")
        return None
    except Exception as e:
        logger.error(f"❌ Backup failed: {e}")
        return None

def restore_backup(backup_path):
    """Restore database from backup"""
    
    logger.info(f"🔄 Restoring database from: {backup_path}")
    
    if not os.path.exists(backup_path):
        logger.error(f"❌ Backup file not found: {backup_path}")
        return False
    
    config = get_database_config()
    
    # Set password environment variable for psql
    env = os.environ.copy()
    env['PGPASSWORD'] = config['password']
    
    try:
        # Run psql command to restore
        cmd = [
            'psql',
            '-h', config['host'],
            '-p', config['port'],
            '-U', config['user'],
            '-d', 'postgres',  # Connect to postgres db first
            '--file', backup_path
        ]
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("✅ Database restored successfully!")
            return True
        else:
            logger.error(f"❌ Restore failed: {result.stderr}")
            return False
            
    except FileNotFoundError:
        logger.error("❌ psql not found. Please install PostgreSQL client tools.")
        return False
    except Exception as e:
        logger.error(f"❌ Restore failed: {e}")
        return False

def list_backups():
    """List all available backups"""
    
    backups_dir = os.path.join("migrations", "backups")
    if not os.path.exists(backups_dir):
        logger.info("📁 No backups directory found.")
        return []
    
    backups = []
    for file in os.listdir(backups_dir):
        if file.endswith('.sql'):
            file_path = os.path.join(backups_dir, file)
            size_mb = os.path.getsize(file_path) / (1024 * 1024)
            created = datetime.fromtimestamp(os.path.getctime(file_path))
            backups.append({
                'filename': file,
                'path': file_path,
                'size_mb': size_mb,
                'created': created
            })
    
    # Sort by creation time (newest first)
    backups.sort(key=lambda x: x['created'], reverse=True)
    
    logger.info("📦 Available backups:")
    for backup in backups:
        logger.info(f"   {backup['filename']} ({backup['size_mb']:.2f} MB) - {backup['created']}")
    
    return backups

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "restore":
            if len(sys.argv) > 2:
                backup_path = sys.argv[2]
                restore_backup(backup_path)
            else:
                logger.error("❌ Please provide backup file path for restore")
        elif sys.argv[1] == "list":
            list_backups()
        else:
            logger.error("❌ Unknown command. Use 'restore <path>' or 'list'")
    else:
        # Create backup
        backup_path = create_backup()
        if backup_path:
            logger.info("🎉 Backup completed successfully!")
            logger.info(f"💾 Backup saved to: {backup_path}")
            logger.info("🔧 To restore: python migrations/backup_database.py restore <backup_path>")
        else:
            logger.error("❌ Backup failed. Check logs for details.")
