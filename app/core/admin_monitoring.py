"""
Admin Monitoring and Error Handling System

Provides comprehensive monitoring, error handling, and alerting for admin operations:
- Real-time system monitoring
- Error tracking and alerting
- Performance metrics
- Health checks
- Automated incident response
- Admin dashboard metrics
"""

import logging
import time
import traceback
import psutil
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Callable
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from sqlalchemy.orm import Session
from sqlalchemy import func, text
from fastapi import HTTPException, status

from app.model.m_admin_audit_log import AdminAuditLog
from app.model.m_church import Church
from app.model.m_user import User
from app.model.m_donation_batch import DonationBatch
from app.config import config

# Configure logging
logger = logging.getLogger(__name__)

class AlertLevel(Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class SystemStatus(Enum):
    """System status levels"""
    HEALTHY = "healthy"
    WARNING = "warning"
    DEGRADED = "degraded"
    DOWN = "down"

@dataclass
class MetricPoint:
    """Single metric data point"""
    timestamp: datetime
    value: float
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Alert:
    """System alert"""
    id: str
    level: AlertLevel
    title: str
    message: str
    timestamp: datetime
    resolved: bool = False
    resolution_time: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class MetricsCollector:
    """Collects and stores system metrics"""

    def __init__(self, max_points: int = 1440):  # 24 hours of minute-by-minute data
        self.max_points = max_points
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_points))
        self.last_collection = datetime.now(timezone.utc)

    def record_metric(self, name: str, value: float, metadata: Dict[str, Any] = None):
        """Record a metric value"""
        point = MetricPoint(
            timestamp=datetime.now(timezone.utc),
            value=value,
            metadata=metadata or {}
        )
        self.metrics[name].append(point)

    def get_metric_history(self, name: str, hours: int = 1) -> List[MetricPoint]:
        """Get metric history for the last N hours"""
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        return [
            point for point in self.metrics[name]
            if point.timestamp >= since
        ]

    def get_metric_average(self, name: str, hours: int = 1) -> float:
        """Get average metric value over the last N hours"""
        history = self.get_metric_history(name, hours)
        if not history:
            return 0.0
        return sum(point.value for point in history) / len(history)

    def get_metric_latest(self, name: str) -> Optional[float]:
        """Get the latest value for a metric"""
        if name in self.metrics and self.metrics[name]:
            return self.metrics[name][-1].value
        return None

class HealthChecker:
    """System health monitoring"""

    def __init__(self):
        self.last_check = datetime.now(timezone.utc)
        self.status = SystemStatus.HEALTHY

    def check_database_health(self, db: Session) -> Dict[str, Any]:
        """Check database connectivity and performance"""
        try:
            start_time = time.time()

            # Test basic connectivity
            result = db.execute(text("SELECT 1")).scalar()
            connection_time = (time.time() - start_time) * 1000

            if connection_time > 1000:  # > 1 second
                status = "warning"
            elif connection_time > 5000:  # > 5 seconds
                status = "critical"
            else:
                status = "healthy"

            # Get connection pool stats
            pool_stats = {}
            if hasattr(db.bind.pool, 'size'):
                pool_stats = {
                    'pool_size': db.bind.pool.size(),
                    'checked_in': db.bind.pool.checkedin(),
                    'checked_out': db.bind.pool.checkedout(),
                    'overflow': db.bind.pool.overflow(),
                    'invalid': db.bind.pool.invalid()
                }

            return {
                'status': status,
                'connection_time_ms': round(connection_time, 2),
                'pool_stats': pool_stats,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                'status': 'critical',
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

    def check_system_resources(self) -> Dict[str, Any]:
        """Check system resource usage"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)

            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent

            # Network stats
            network = psutil.net_io_counters()

            # Determine overall status
            status = "healthy"
            if cpu_percent > 80 or memory_percent > 80 or disk_percent > 85:
                status = "warning"
            if cpu_percent > 90 or memory_percent > 90 or disk_percent > 95:
                status = "critical"

            return {
                'status': status,
                'cpu_percent': cpu_percent,
                'memory_percent': memory_percent,
                'memory_total_gb': round(memory.total / 1024**3, 2),
                'memory_available_gb': round(memory.available / 1024**3, 2),
                'disk_percent': disk_percent,
                'disk_total_gb': round(disk.total / 1024**3, 2),
                'disk_free_gb': round(disk.free / 1024**3, 2),
                'network_bytes_sent': network.bytes_sent,
                'network_bytes_recv': network.bytes_recv,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            logger.error(f"System resource check failed: {e}")
            return {
                'status': 'critical',
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

    def check_application_health(self, db: Session) -> Dict[str, Any]:
        """Check application-specific health metrics"""
        try:
            # Recent error rate
            one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
            recent_errors = db.query(AdminAuditLog).filter(
                AdminAuditLog.success == False,
                AdminAuditLog.timestamp >= one_hour_ago
            ).count()

            total_requests = db.query(AdminAuditLog).filter(
                AdminAuditLog.timestamp >= one_hour_ago
            ).count()

            error_rate = (recent_errors / total_requests * 100) if total_requests > 0 else 0

            # Active sessions
            active_admins = db.query(func.count(func.distinct(AdminAuditLog.admin_id))).filter(
                AdminAuditLog.timestamp >= datetime.now(timezone.utc) - timedelta(minutes=30)
            ).scalar() or 0

            # Recent activity
            recent_activity = db.query(AdminAuditLog).filter(
                AdminAuditLog.timestamp >= datetime.now(timezone.utc) - timedelta(minutes=5)
            ).count()

            # Determine status
            status = "healthy"
            if error_rate > 10:  # > 10% error rate
                status = "warning"
            if error_rate > 25:  # > 25% error rate
                status = "critical"

            return {
                'status': status,
                'error_rate_percent': round(error_rate, 2),
                'recent_errors': recent_errors,
                'total_requests_1h': total_requests,
                'active_admin_sessions': active_admins,
                'recent_activity_5m': recent_activity,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            logger.error(f"Application health check failed: {e}")
            return {
                'status': 'critical',
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

class AlertManager:
    """Manages system alerts and notifications"""

    def __init__(self):
        self.alerts: Dict[str, Alert] = {}
        self.alert_handlers: Dict[AlertLevel, List[Callable]] = defaultdict(list)
        self.email_config = self._get_email_config()

    def _get_email_config(self) -> Dict[str, str]:
        """Get email configuration from settings"""
        return {
            'smtp_server': getattr(config, 'SMTP_SERVER', 'localhost'),
            'smtp_port': getattr(config, 'SMTP_PORT', 587),
            'smtp_username': getattr(config, 'SMTP_USERNAME', ''),
            'smtp_password': getattr(config, 'SMTP_PASSWORD', ''),
            'from_email': getattr(config, 'ALERT_FROM_EMAIL', 'alerts@manna.com'),
            'admin_emails': getattr(config, 'ADMIN_ALERT_EMAILS', '').split(',')
        }

    def create_alert(self, alert_id: str, level: AlertLevel, title: str,
                    message: str, metadata: Dict[str, Any] = None) -> Alert:
        """Create a new alert"""
        alert = Alert(
            id=alert_id,
            level=level,
            title=title,
            message=message,
            timestamp=datetime.now(timezone.utc),
            metadata=metadata or {}
        )

        self.alerts[alert_id] = alert

        # Trigger alert handlers
        for handler in self.alert_handlers[level]:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Alert handler failed: {e}")

        return alert

    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert"""
        if alert_id in self.alerts:
            self.alerts[alert_id].resolved = True
            self.alerts[alert_id].resolution_time = datetime.now(timezone.utc)
            return True
        return False

    def get_active_alerts(self, level: Optional[AlertLevel] = None) -> List[Alert]:
        """Get all active alerts, optionally filtered by level"""
        alerts = [alert for alert in self.alerts.values() if not alert.resolved]
        if level:
            alerts = [alert for alert in alerts if alert.level == level]
        return sorted(alerts, key=lambda x: x.timestamp, reverse=True)

    def send_email_alert(self, alert: Alert):
        """Send email notification for alert"""
        if not self.email_config['admin_emails'] or not self.email_config['admin_emails'][0]:
            return

        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_config['from_email']
            msg['To'] = ', '.join(self.email_config['admin_emails'])
            msg['Subject'] = f"[MANNA ALERT - {alert.level.value.upper()}] {alert.title}"

            body = f"""
Alert Details:
- Level: {alert.level.value.upper()}
- Title: {alert.title}
- Message: {alert.message}
- Timestamp: {alert.timestamp.isoformat()}
- Alert ID: {alert.id}

Metadata:
{json.dumps(alert.metadata, indent=2)}

This is an automated alert from the Manna Admin System.
"""

            msg.attach(MIMEText(body, 'plain'))

            server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
            server.starttls()
            if self.email_config['smtp_username']:
                server.login(self.email_config['smtp_username'], self.email_config['smtp_password'])

            server.send_message(msg)
            server.quit()

            logger.info(f"Email alert sent for {alert.id}")

        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")

    def register_handler(self, level: AlertLevel, handler: Callable[[Alert], None]):
        """Register an alert handler"""
        self.alert_handlers[level].append(handler)

class AdminMonitor:
    """Main monitoring system for admin operations"""

    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.health_checker = HealthChecker()
        self.alert_manager = AlertManager()
        self.last_health_check = datetime.now(timezone.utc)

        # Register default alert handlers
        self.alert_manager.register_handler(AlertLevel.HIGH, self.alert_manager.send_email_alert)
        self.alert_manager.register_handler(AlertLevel.CRITICAL, self.alert_manager.send_email_alert)

    async def collect_metrics(self, db: Session):
        """Collect system metrics"""
        try:
            # Database metrics
            db_health = self.health_checker.check_database_health(db)
            if 'connection_time_ms' in db_health:
                self.metrics_collector.record_metric('db_connection_time_ms', db_health['connection_time_ms'])

            # System resource metrics
            system_health = self.health_checker.check_system_resources()
            self.metrics_collector.record_metric('cpu_percent', system_health.get('cpu_percent', 0))
            self.metrics_collector.record_metric('memory_percent', system_health.get('memory_percent', 0))
            self.metrics_collector.record_metric('disk_percent', system_health.get('disk_percent', 0))

            # Application metrics
            app_health = self.health_checker.check_application_health(db)
            self.metrics_collector.record_metric('error_rate_percent', app_health.get('error_rate_percent', 0))
            self.metrics_collector.record_metric('active_admin_sessions', app_health.get('active_admin_sessions', 0))

            # Business metrics
            total_churches = db.query(Church).count()
            active_churches = db.query(Church).filter(Church.is_active == True).count()
            total_users = db.query(User).count()

            self.metrics_collector.record_metric('total_churches', total_churches)
            self.metrics_collector.record_metric('active_churches', active_churches)
            self.metrics_collector.record_metric('total_users', total_users)

            # Check for alerts
            await self._check_for_alerts(db_health, system_health, app_health)

        except Exception as e:
            logger.error(f"Metrics collection failed: {e}")
            self.alert_manager.create_alert(
                'metrics_collection_failed',
                AlertLevel.HIGH,
                'Metrics Collection Failed',
                f'Failed to collect system metrics: {str(e)}'
            )

    async def _check_for_alerts(self, db_health: Dict, system_health: Dict, app_health: Dict):
        """Check for alert conditions"""

        # Database alerts
        if db_health.get('status') == 'critical':
            self.alert_manager.create_alert(
                'database_critical',
                AlertLevel.CRITICAL,
                'Database Critical',
                'Database is experiencing critical issues',
                db_health
            )
        elif db_health.get('status') == 'warning':
            self.alert_manager.create_alert(
                'database_warning',
                AlertLevel.MEDIUM,
                'Database Warning',
                'Database performance degraded',
                db_health
            )
        else:
            self.alert_manager.resolve_alert('database_critical')
            self.alert_manager.resolve_alert('database_warning')

        # System resource alerts
        cpu = system_health.get('cpu_percent', 0)
        memory = system_health.get('memory_percent', 0)
        disk = system_health.get('disk_percent', 0)

        if cpu > 90 or memory > 90 or disk > 95:
            self.alert_manager.create_alert(
                'system_resources_critical',
                AlertLevel.CRITICAL,
                'System Resources Critical',
                f'Critical resource usage - CPU: {cpu}%, Memory: {memory}%, Disk: {disk}%',
                system_health
            )
        elif cpu > 80 or memory > 80 or disk > 85:
            self.alert_manager.create_alert(
                'system_resources_warning',
                AlertLevel.MEDIUM,
                'System Resources Warning',
                f'High resource usage - CPU: {cpu}%, Memory: {memory}%, Disk: {disk}%',
                system_health
            )
        else:
            self.alert_manager.resolve_alert('system_resources_critical')
            self.alert_manager.resolve_alert('system_resources_warning')

        # Application alerts
        error_rate = app_health.get('error_rate_percent', 0)
        if error_rate > 25:
            self.alert_manager.create_alert(
                'high_error_rate',
                AlertLevel.CRITICAL,
                'High Error Rate',
                f'Error rate is {error_rate}% in the last hour',
                app_health
            )
        elif error_rate > 10:
            self.alert_manager.create_alert(
                'elevated_error_rate',
                AlertLevel.MEDIUM,
                'Elevated Error Rate',
                f'Error rate is {error_rate}% in the last hour',
                app_health
            )
        else:
            self.alert_manager.resolve_alert('high_error_rate')
            self.alert_manager.resolve_alert('elevated_error_rate')

    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        active_alerts = self.alert_manager.get_active_alerts()

        # Determine overall status
        if any(alert.level == AlertLevel.CRITICAL for alert in active_alerts):
            overall_status = SystemStatus.DOWN
        elif any(alert.level == AlertLevel.HIGH for alert in active_alerts):
            overall_status = SystemStatus.DEGRADED
        elif any(alert.level == AlertLevel.MEDIUM for alert in active_alerts):
            overall_status = SystemStatus.WARNING
        else:
            overall_status = SystemStatus.HEALTHY

        return {
            'status': overall_status.value,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'active_alerts': len(active_alerts),
            'critical_alerts': len([a for a in active_alerts if a.level == AlertLevel.CRITICAL]),
            'high_alerts': len([a for a in active_alerts if a.level == AlertLevel.HIGH]),
            'medium_alerts': len([a for a in active_alerts if a.level == AlertLevel.MEDIUM]),
            'low_alerts': len([a for a in active_alerts if a.level == AlertLevel.LOW]),
            'uptime_hours': self._get_uptime_hours(),
            'last_health_check': self.last_health_check.isoformat()
        }

    def _get_uptime_hours(self) -> float:
        """Get system uptime in hours (simplified)"""
        try:
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot_time
            return uptime.total_seconds() / 3600
        except:
            return 0.0

    def get_dashboard_metrics(self) -> Dict[str, Any]:
        """Get metrics for admin dashboard"""
        return {
            'system_status': self.get_system_status(),
            'recent_metrics': {
                'cpu_percent': self.metrics_collector.get_metric_latest('cpu_percent'),
                'memory_percent': self.metrics_collector.get_metric_latest('memory_percent'),
                'disk_percent': self.metrics_collector.get_metric_latest('disk_percent'),
                'error_rate_percent': self.metrics_collector.get_metric_latest('error_rate_percent'),
                'db_connection_time_ms': self.metrics_collector.get_metric_latest('db_connection_time_ms'),
                'active_admin_sessions': self.metrics_collector.get_metric_latest('active_admin_sessions'),
                'total_churches': self.metrics_collector.get_metric_latest('total_churches'),
                'active_churches': self.metrics_collector.get_metric_latest('active_churches'),
                'total_users': self.metrics_collector.get_metric_latest('total_users')
            },
            'metric_history': {
                'cpu_percent': [
                    {'timestamp': p.timestamp.isoformat(), 'value': p.value}
                    for p in self.metrics_collector.get_metric_history('cpu_percent', 1)
                ],
                'error_rate_percent': [
                    {'timestamp': p.timestamp.isoformat(), 'value': p.value}
                    for p in self.metrics_collector.get_metric_history('error_rate_percent', 1)
                ]
            },
            'active_alerts': [
                {
                    'id': alert.id,
                    'level': alert.level.value,
                    'title': alert.title,
                    'message': alert.message,
                    'timestamp': alert.timestamp.isoformat()
                }
                for alert in self.alert_manager.get_active_alerts()[:10]  # Latest 10 alerts
            ]
        }

# Global monitor instance
admin_monitor = AdminMonitor()

def get_admin_monitor() -> AdminMonitor:
    """Get the global admin monitor instance"""
    return admin_monitor

# Decorator for monitoring admin endpoints
def monitor_admin_endpoint(endpoint_name: str):
    """Decorator to monitor admin endpoint performance"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            error_message = None

            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                error_message = str(e)
                raise
            finally:
                duration_ms = (time.time() - start_time) * 1000

                # Record metrics
                admin_monitor.metrics_collector.record_metric(
                    f'{endpoint_name}_duration_ms',
                    duration_ms
                )
                admin_monitor.metrics_collector.record_metric(
                    f'{endpoint_name}_requests_total',
                    1
                )

                if not success:
                    admin_monitor.metrics_collector.record_metric(
                        f'{endpoint_name}_errors_total',
                        1
                    )

                    # Create alert for repeated failures
                    recent_errors = len([
                        p for p in admin_monitor.metrics_collector.get_metric_history(
                            f'{endpoint_name}_errors_total', 0.25  # Last 15 minutes
                        )
                    ])

                    if recent_errors >= 5:  # 5 errors in 15 minutes
                        admin_monitor.alert_manager.create_alert(
                            f'{endpoint_name}_repeated_failures',
                            AlertLevel.HIGH,
                            f'{endpoint_name} Repeated Failures',
                            f'{endpoint_name} has failed {recent_errors} times in the last 15 minutes',
                            {'endpoint': endpoint_name, 'error_count': recent_errors}
                        )

        return wrapper
    return decorator

# Exception handler for admin endpoints
def handle_admin_exception(e: Exception, endpoint: str, admin_id: Optional[int] = None) -> HTTPException:
    """Standardized exception handling for admin endpoints"""

    # Log the error
    logger.error(f"Admin endpoint error in {endpoint}: {str(e)}\n{traceback.format_exc()}")

    # Record metrics
    admin_monitor.metrics_collector.record_metric(f'{endpoint}_errors_total', 1)

    # Determine appropriate HTTP status and message
    if isinstance(e, HTTPException):
        return e
    elif isinstance(e, ValueError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    elif isinstance(e, PermissionError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    else:
        # Generic server error
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred. The incident has been logged."
        )
