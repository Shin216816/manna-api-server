"""
Comprehensive Backup and Recovery Service

Implements:
- Automated database backups
- Point-in-time recovery
- Data export functionality
- Backup verification
- Disaster recovery procedures
- Backup retention policies
"""

import os
import json
import logging
import subprocess
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.utils.database import get_db
from app.config import config

logger = logging.getLogger(__name__)

@dataclass
class BackupInfo:
    """Backup information"""
    id: str
    filename: str
    size_bytes: int
    created_at: datetime
    backup_type: str
    status: str
    checksum: str
    metadata: Dict[str, Any]

class BackupService:
    """Comprehensive backup and recovery service"""
    
    def __init__(self):
        self.backup_dir = Path(config.BACKUP_DIR) if hasattr(config, 'BACKUP_DIR') else Path('/tmp/backups')
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Backup retention policies
        self.retention_policies = {
            'daily': 30,    # Keep daily backups for 30 days
            'weekly': 12,   # Keep weekly backups for 12 weeks
            'monthly': 12   # Keep monthly backups for 12 months
        }
    
    def create_database_backup(self, backup_type: str = 'manual') -> BackupInfo:
        """Create database backup"""
        try:
            timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
            filename = f"manna_db_backup_{timestamp}.sql"
            filepath = self.backup_dir / filename
            
            # Get database connection string
            db_url = config.DATABASE_URL
            
            # Create backup using pg_dump
            cmd = [
                'pg_dump',
                '--verbose',
                '--clean',
                '--no-owner',
                '--no-privileges',
                '--format=custom',
                '--file', str(filepath),
                db_url
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                raise Exception(f"Backup failed: {result.stderr}")
            
            # Get file size
            file_size = filepath.stat().st_size
            
            # Calculate checksum
            checksum = self._calculate_checksum(filepath)
            
            # Create backup info
            backup_info = BackupInfo(
                id=f"backup_{timestamp}",
                filename=filename,
                size_bytes=file_size,
                created_at=datetime.now(timezone.utc),
                backup_type=backup_type,
                status='completed',
                checksum=checksum,
                metadata={
                    'database_url': db_url,
                    'backup_command': ' '.join(cmd),
                    'pg_dump_version': self._get_pg_dump_version()
                }
            )
            
            # Save backup metadata
            self._save_backup_metadata(backup_info)
            
            logger.info(f"Database backup created: {filename} ({file_size} bytes)")
            return backup_info
            
        except Exception as e:
            logger.error(f"Error creating database backup: {e}")
            raise
    
    def restore_database_backup(self, backup_id: str, target_database: str = None) -> bool:
        """Restore database from backup"""
        try:
            # Get backup info
            backup_info = self._get_backup_info(backup_id)
            if not backup_info:
                raise Exception(f"Backup {backup_id} not found")
            
            filepath = self.backup_dir / backup_info.filename
            
            if not filepath.exists():
                raise Exception(f"Backup file not found: {filepath}")
            
            # Verify backup integrity
            if not self._verify_backup_integrity(filepath, backup_info.checksum):
                raise Exception("Backup integrity check failed")
            
            # Get database connection string
            db_url = config.DATABASE_URL
            if target_database:
                # Replace database name in URL
                db_url = db_url.rsplit('/', 1)[0] + f'/{target_database}'
            
            # Restore backup using pg_restore
            cmd = [
                'pg_restore',
                '--verbose',
                '--clean',
                '--no-owner',
                '--no-privileges',
                '--dbname', db_url,
                str(filepath)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode != 0:
                raise Exception(f"Restore failed: {result.stderr}")
            
            logger.info(f"Database restored from backup: {backup_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error restoring database backup: {e}")
            raise
    
    def export_user_data(self, user_id: int, db: Session) -> Dict[str, Any]:
        """Export user data for GDPR compliance"""
        try:
            # Get user data
            user_data = self._get_user_data(user_id, db)
            
            # Get related data
            related_data = self._get_user_related_data(user_id, db)
            
            export_data = {
                'user_id': user_id,
                'exported_at': datetime.now(timezone.utc).isoformat(),
                'user_data': user_data,
                'related_data': related_data
            }
            
            # Save export file
            timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
            filename = f"user_export_{user_id}_{timestamp}.json"
            filepath = self.backup_dir / filename
            
            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            logger.info(f"User data exported: {filename}")
            return export_data
            
        except Exception as e:
            logger.error(f"Error exporting user data: {e}")
            raise
    
    def cleanup_old_backups(self) -> Dict[str, int]:
        """Clean up old backups based on retention policies"""
        try:
            cleanup_stats = {
                'daily_removed': 0,
                'weekly_removed': 0,
                'monthly_removed': 0,
                'total_removed': 0
            }
            
            # Get all backup files
            backup_files = list(self.backup_dir.glob('manna_db_backup_*.sql'))
            
            # Group by type and age
            now = datetime.now(timezone.utc)
            
            for filepath in backup_files:
                try:
                    # Parse timestamp from filename
                    timestamp_str = filepath.stem.split('_')[-2] + '_' + filepath.stem.split('_')[-1]
                    file_time = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S').replace(tzinfo=timezone.utc)
                    
                    age_days = (now - file_time).days
                    
                    # Determine backup type and retention
                    if age_days < 7:
                        # Daily backup
                        if age_days > self.retention_policies['daily']:
                            filepath.unlink()
                            cleanup_stats['daily_removed'] += 1
                    elif age_days < 30:
                        # Weekly backup
                        if age_days > self.retention_policies['weekly'] * 7:
                            filepath.unlink()
                            cleanup_stats['weekly_removed'] += 1
                    else:
                        # Monthly backup
                        if age_days > self.retention_policies['monthly'] * 30:
                            filepath.unlink()
                            cleanup_stats['monthly_removed'] += 1
                            
                except Exception as e:
                    logger.warning(f"Error processing backup file {filepath}: {e}")
                    continue
            
            cleanup_stats['total_removed'] = (
                cleanup_stats['daily_removed'] + 
                cleanup_stats['weekly_removed'] + 
                cleanup_stats['monthly_removed']
            )
            
            logger.info(f"Backup cleanup completed: {cleanup_stats}")
            return cleanup_stats
            
        except Exception as e:
            logger.error(f"Error cleaning up old backups: {e}")
            raise
    
    def list_backups(self) -> List[BackupInfo]:
        """List all available backups"""
        try:
            backups = []
            
            # Get backup files
            backup_files = list(self.backup_dir.glob('manna_db_backup_*.sql'))
            
            for filepath in backup_files:
                try:
                    # Parse timestamp from filename
                    timestamp_str = filepath.stem.split('_')[-2] + '_' + filepath.stem.split('_')[-1]
                    file_time = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S').replace(tzinfo=timezone.utc)
                    
                    # Get file size
                    file_size = filepath.stat().st_size
                    
                    # Calculate checksum
                    checksum = self._calculate_checksum(filepath)
                    
                    backup_info = BackupInfo(
                        id=f"backup_{timestamp_str}",
                        filename=filepath.name,
                        size_bytes=file_size,
                        created_at=file_time,
                        backup_type='scheduled',
                        status='completed',
                        checksum=checksum,
                        metadata={}
                    )
                    
                    backups.append(backup_info)
                    
                except Exception as e:
                    logger.warning(f"Error processing backup file {filepath}: {e}")
                    continue
            
            # Sort by creation time (newest first)
            backups.sort(key=lambda x: x.created_at, reverse=True)
            
            return backups
            
        except Exception as e:
            logger.error(f"Error listing backups: {e}")
            raise
    
    def verify_backup_integrity(self, backup_id: str) -> bool:
        """Verify backup integrity"""
        try:
            backup_info = self._get_backup_info(backup_id)
            if not backup_info:
                return False
            
            filepath = self.backup_dir / backup_info.filename
            if not filepath.exists():
                return False
            
            return self._verify_backup_integrity(filepath, backup_info.checksum)
            
        except Exception as e:
            logger.error(f"Error verifying backup integrity: {e}")
            return False
    
    def _calculate_checksum(self, filepath: Path) -> str:
        """Calculate file checksum"""
        import hashlib
        
        hash_md5 = hashlib.md5()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        
        return hash_md5.hexdigest()
    
    def _verify_backup_integrity(self, filepath: Path, expected_checksum: str) -> bool:
        """Verify backup file integrity"""
        try:
            actual_checksum = self._calculate_checksum(filepath)
            return actual_checksum == expected_checksum
        except Exception as e:
            logger.error(f"Error verifying backup integrity: {e}")
            return False
    
    def _get_pg_dump_version(self) -> str:
        """Get pg_dump version"""
        try:
            result = subprocess.run(['pg_dump', '--version'], capture_output=True, text=True)
            return result.stdout.strip()
        except Exception:
            return "Unknown"
    
    def _save_backup_metadata(self, backup_info: BackupInfo):
        """Save backup metadata to file"""
        try:
            metadata_file = self.backup_dir / f"{backup_info.id}_metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump({
                    'id': backup_info.id,
                    'filename': backup_info.filename,
                    'size_bytes': backup_info.size_bytes,
                    'created_at': backup_info.created_at.isoformat(),
                    'backup_type': backup_info.backup_type,
                    'status': backup_info.status,
                    'checksum': backup_info.checksum,
                    'metadata': backup_info.metadata
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving backup metadata: {e}")
    
    def _get_backup_info(self, backup_id: str) -> Optional[BackupInfo]:
        """Get backup info from metadata file"""
        try:
            metadata_file = self.backup_dir / f"{backup_id}_metadata.json"
            if not metadata_file.exists():
                return None
            
            with open(metadata_file, 'r') as f:
                data = json.load(f)
            
            return BackupInfo(
                id=data['id'],
                filename=data['filename'],
                size_bytes=data['size_bytes'],
                created_at=datetime.fromisoformat(data['created_at']),
                backup_type=data['backup_type'],
                status=data['status'],
                checksum=data['checksum'],
                metadata=data['metadata']
            )
        except Exception as e:
            logger.error(f"Error getting backup info: {e}")
            return None
    
    def _get_user_data(self, user_id: int, db: Session) -> Dict[str, Any]:
        """Get user data for export"""
        from app.model.m_user import User
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {}
        
        return {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'phone': user.phone,
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'last_login': user.last_login.isoformat() if user.last_login else None,
            'is_active': user.is_active,
            'role': user.role
        }
    
    def _get_user_related_data(self, user_id: int, db: Session) -> Dict[str, Any]:
        """Get user related data for export"""
        from app.model.m_donation_preference import DonationPreference
        from app.model.m_roundup_new import DonorPayout
        
        # Get donation preferences
        preferences = db.query(DonationPreference).filter(
            DonationPreference.user_id == user_id
        ).first()
        
        # Get donation history
        donations = db.query(DonorPayout).filter(
            DonorPayout.user_id == user_id
        ).all()
        
        return {
            'donation_preferences': {
                'frequency': preferences.frequency if preferences else None,
                'multiplier': preferences.multiplier if preferences else None,
                'pause': preferences.pause if preferences else None,
                'cover_processing_fees': preferences.cover_processing_fees if preferences else None,
                'monthly_cap': float(preferences.monthly_cap) if preferences and preferences.monthly_cap else None
            },
            'donations': [
                {
                    'id': d.id,
                    'amount': float(d.donation_amount),
                    'type': d.donation_type,
                    'status': d.status,
                    'created_at': d.created_at.isoformat() if d.created_at else None
                }
                for d in donations
            ]
        }


# Global backup service instance
backup_service = BackupService()


def get_backup_service() -> BackupService:
    """Get backup service instance"""
    return backup_service
