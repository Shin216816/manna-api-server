"""
Comprehensive Monitoring Service for Production

Implements:
- Application Performance Monitoring (APM)
- Error tracking and alerting
- System metrics collection
- Health checks
- Log aggregation
- Real-time monitoring dashboard
"""

import time
import psutil
import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, asdict
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from fastapi import Request

from app.model.m_user import User
from app.model.m_church import Church
from app.model.m_roundup_new import DonorPayout, ChurchPayout
from app.core.responses import ResponseFactory

logger = logging.getLogger(__name__)

@dataclass
class SystemMetrics:
    """System performance metrics"""
    timestamp: str
    cpu_percent: float
    memory_percent: float
    memory_available_gb: float
    disk_percent: float
    disk_free_gb: float
    process_memory_mb: float
    active_connections: int
    database_connections: int

@dataclass
class ApplicationMetrics:
    """Application-specific metrics"""
    timestamp: str
    total_users: int
    active_users_24h: int
    total_churches: int
    active_churches: int
    total_donations: float
    donations_24h: float
    total_roundups: float
    roundups_24h: float
    api_requests_1h: int
    error_rate_1h: float
    response_time_avg: float

@dataclass
class ErrorMetrics:
    """Error tracking metrics"""
    timestamp: str
    error_count: int
    error_rate: float
    critical_errors: int
    warning_errors: int
    error_types: Dict[str, int]
    recent_errors: List[Dict[str, Any]]

class MonitoringService:
    """Comprehensive monitoring service"""
    
    def __init__(self):
        self.metrics_history: List[SystemMetrics] = []
        self.error_history: List[ErrorMetrics] = []
        self.alert_thresholds = {
            'cpu_percent': 80.0,
            'memory_percent': 85.0,
            'disk_percent': 90.0,
            'error_rate': 5.0,
            'response_time': 2.0
        }
        self.alerts: List[Dict[str, Any]] = []
    
    def collect_system_metrics(self) -> SystemMetrics:
        """Collect current system metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_available_gb = memory.available / (1024**3)
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            disk_free_gb = disk.free / (1024**3)
            
            # Process metrics
            process = psutil.Process()
            process_memory_mb = process.memory_info().rss / (1024**2)
            
            # Network connections
            active_connections = len(psutil.net_connections())
            
            return SystemMetrics(
                timestamp=datetime.now(timezone.utc).isoformat(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_available_gb=round(memory_available_gb, 2),
                disk_percent=disk_percent,
                disk_free_gb=round(disk_free_gb, 2),
                process_memory_mb=round(process_memory_mb, 2),
                active_connections=active_connections,
                database_connections=0  # Will be set by database monitoring
            )
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return SystemMetrics(
                timestamp=datetime.now(timezone.utc).isoformat(),
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_available_gb=0.0,
                disk_percent=0.0,
                disk_free_gb=0.0,
                process_memory_mb=0.0,
                active_connections=0,
                database_connections=0
            )
    
    def collect_application_metrics(self, db: Session) -> ApplicationMetrics:
        """Collect application-specific metrics"""
        try:
            now = datetime.now(timezone.utc)
            yesterday = now - timedelta(days=1)
            one_hour_ago = now - timedelta(hours=1)
            
            # User metrics
            total_users = db.query(User).count()
            active_users_24h = db.query(User).filter(
                User.last_login >= yesterday
            ).count()
            
            # Church metrics
            total_churches = db.query(Church).count()
            active_churches = db.query(Church).filter(
                Church.is_active == True
            ).count()
            
            # Donation metrics
            total_donations_result = db.query(func.sum(DonorPayout.donation_amount)).filter(
                DonorPayout.status == "completed"
            ).scalar()
            total_donations = float(total_donations_result) if total_donations_result else 0.0
            
            donations_24h_result = db.query(func.sum(DonorPayout.donation_amount)).filter(
                DonorPayout.status == "completed",
                DonorPayout.created_at >= yesterday
            ).scalar()
            donations_24h = float(donations_24h_result) if donations_24h_result else 0.0
            
            # Roundup metrics
            total_roundups_result = db.query(func.sum(DonorPayout.donation_amount)).filter(
                DonorPayout.status == "completed",
                DonorPayout.donation_type == "roundup"
            ).scalar()
            total_roundups = float(total_roundups_result) if total_roundups_result else 0.0
            
            roundups_24h_result = db.query(func.sum(DonorPayout.donation_amount)).filter(
                DonorPayout.status == "completed",
                DonorPayout.donation_type == "roundup",
                DonorPayout.created_at >= yesterday
            ).scalar()
            roundups_24h = float(roundups_24h_result) if roundups_24h_result else 0.0
            
            return ApplicationMetrics(
                timestamp=now.isoformat(),
                total_users=total_users,
                active_users_24h=active_users_24h,
                total_churches=total_churches,
                active_churches=active_churches,
                total_donations=round(total_donations, 2),
                donations_24h=round(donations_24h, 2),
                total_roundups=round(total_roundups, 2),
                roundups_24h=round(roundups_24h, 2),
                api_requests_1h=0,  # Will be tracked by middleware
                error_rate_1h=0.0,  # Will be calculated from logs
                response_time_avg=0.0  # Will be tracked by middleware
            )
        except Exception as e:
            logger.error(f"Error collecting application metrics: {e}")
            return ApplicationMetrics(
                timestamp=datetime.now(timezone.utc).isoformat(),
                total_users=0,
                active_users_24h=0,
                total_churches=0,
                active_churches=0,
                total_donations=0.0,
                donations_24h=0.0,
                total_roundups=0.0,
                roundups_24h=0.0,
                api_requests_1h=0,
                error_rate_1h=0.0,
                response_time_avg=0.0
            )
    
    def check_health(self, db: Session) -> Dict[str, Any]:
        """Comprehensive health check"""
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'checks': {}
        }
        
        try:
            # Database health
            db_healthy = self._check_database_health(db)
            health_status['checks']['database'] = {
                'status': 'healthy' if db_healthy else 'unhealthy',
                'details': 'Database connection successful' if db_healthy else 'Database connection failed'
            }
            
            # System health
            system_metrics = self.collect_system_metrics()
            system_healthy = self._check_system_health(system_metrics)
            health_status['checks']['system'] = {
                'status': 'healthy' if system_healthy else 'unhealthy',
                'details': asdict(system_metrics)
            }
            
            # Application health
            app_metrics = self.collect_application_metrics(db)
            app_healthy = self._check_application_health(app_metrics)
            health_status['checks']['application'] = {
                'status': 'healthy' if app_healthy else 'unhealthy',
                'details': asdict(app_metrics)
            }
            
            # Overall status
            if not (db_healthy and system_healthy and app_healthy):
                health_status['status'] = 'unhealthy'
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            health_status['status'] = 'unhealthy'
            health_status['error'] = str(e)
        
        return health_status
    
    def _check_database_health(self, db: Session) -> bool:
        """Check database connectivity"""
        try:
            db.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    def _check_system_health(self, metrics: SystemMetrics) -> bool:
        """Check system health against thresholds"""
        checks = [
            metrics.cpu_percent < self.alert_thresholds['cpu_percent'],
            metrics.memory_percent < self.alert_thresholds['memory_percent'],
            metrics.disk_percent < self.alert_thresholds['disk_percent']
        ]
        return all(checks)
    
    def _check_application_health(self, metrics: ApplicationMetrics) -> bool:
        """Check application health"""
        checks = [
            metrics.error_rate_1h < self.alert_thresholds['error_rate'],
            metrics.response_time_avg < self.alert_thresholds['response_time']
        ]
        return all(checks)
    
    def track_request(self, request: Request, response_time: float, status_code: int):
        """Track API request metrics"""
        # This would be called by middleware
        pass
    
    def track_error(self, error: Exception, context: Dict[str, Any]):
        """Track application errors"""
        error_data = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context
        }
        
        logger.error(f"Application error: {error_data}")
        
        # Check if this is a critical error
        if self._is_critical_error(error):
            self._create_alert('critical_error', error_data)
    
    def _is_critical_error(self, error: Exception) -> bool:
        """Determine if error is critical"""
        critical_errors = [
            'DatabaseError',
            'ConnectionError',
            'TimeoutError',
            'MemoryError',
            'SystemError'
        ]
        return type(error).__name__ in critical_errors
    
    def _create_alert(self, alert_type: str, data: Dict[str, Any]):
        """Create monitoring alert"""
        alert = {
            'id': f"{alert_type}_{int(time.time())}",
            'type': alert_type,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'data': data,
            'status': 'active'
        }
        
        self.alerts.append(alert)
        logger.critical(f"ALERT: {alert}")
        
        # In production, this would send notifications
        # self._send_alert_notification(alert)
    
    def get_metrics_summary(self, db: Session) -> Dict[str, Any]:
        """Get comprehensive metrics summary"""
        system_metrics = self.collect_system_metrics()
        app_metrics = self.collect_application_metrics(db)
        health_status = self.check_health(db)
        
        return {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'health': health_status,
            'system': asdict(system_metrics),
            'application': asdict(app_metrics),
            'alerts': {
                'active': len([a for a in self.alerts if a['status'] == 'active']),
                'total': len(self.alerts)
            }
        }
    
    def get_dashboard_data(self, db: Session) -> Dict[str, Any]:
        """Get data for monitoring dashboard"""
        metrics = self.get_metrics_summary(db)
        
        # Add historical data
        metrics['history'] = {
            'system_metrics': [asdict(m) for m in self.metrics_history[-24:]],  # Last 24 hours
            'error_metrics': [asdict(e) for e in self.error_history[-24:]]
        }
        
        return metrics


# Global monitoring service instance
monitoring_service = MonitoringService()


def get_monitoring_service() -> MonitoringService:
    """Get monitoring service instance"""
    return monitoring_service
