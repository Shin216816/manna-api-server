"""
Real-time Monitoring Controller

Provides real-time system and business monitoring:
- System health metrics
- Business metrics monitoring
- Performance tracking
- Alert management
- Real-time dashboards
"""

from fastapi import HTTPException
import logging
import traceback
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
import time

# Try to import psutil, fallback to mock if not available
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    # Mock psutil for development
    class MockPsutil:
        @staticmethod
        def cpu_percent(interval=1):
            return 45.0
        
        @staticmethod
        def virtual_memory():
            class MockMemory:
                percent = 67.8
                available = 8 * 1024**3  # 8GB
            return MockMemory()
        
        @staticmethod
        def disk_usage(path):
            class MockDisk:
                percent = 23.1
                free = 100 * 1024**3  # 100GB
            return MockDisk()
    
    psutil = MockPsutil()

from app.model.m_user import User
from app.model.m_church import Church
from app.model.m_donation_batch import DonationBatch
from app.model.m_donation_preference import DonationPreference
from app.core.responses import ResponseFactory


def get_system_alerts(db: Session):
    """Get system alerts and notifications"""
    try:
        alerts = []
        
        # Check for high error rates
        error_rate = get_error_rate_metrics()
        if error_rate > 5.0:  # 5% error rate threshold
            alerts.append({
                "id": 1,
                "type": "error",
                "title": "High Error Rate",
                "message": f"Error rate is {error_rate}%, above normal threshold",
                "severity": "high",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "acknowledged": False
            })

        # Check for pending KYC applications
        pending_kyc = db.query(func.count(Church.id)).filter(
            Church.kyc_status == "pending"
        ).scalar()
        
        if pending_kyc > 10:  # More than 10 pending KYC
            alerts.append({
                "id": 2,
                "type": "kyc",
                "title": "High KYC Pending Count",
                "message": f"{pending_kyc} KYC applications pending review",
                "severity": "medium",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "acknowledged": False
            })

        # Check for failed payouts
        failed_payouts = db.query(func.count(DonationBatch.id)).filter(
            DonationBatch.status == "failed"
        ).scalar()
        
        if failed_payouts > 0:
            alerts.append({
                "id": 3,
                "type": "payout",
                "title": "Failed Payouts",
                "message": f"{failed_payouts} payouts have failed and need attention",
                "severity": "high",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "acknowledged": False
            })

        # Check for system resource usage
        system_health = get_realtime_system_health(db)
        if system_health.data['cpu_usage'] > 80:
            alerts.append({
                "id": 4,
                "type": "system",
                "title": "High CPU Usage",
                "message": f"CPU usage is {system_health.data['cpu_usage']}%, above recommended threshold",
                "severity": "medium",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "acknowledged": False
            })

        return ResponseFactory.success(
            message="System alerts retrieved successfully",
            data={
                "alerts": alerts,
                "total_count": len(alerts),
                "unacknowledged_count": len([a for a in alerts if not a.get('acknowledged', False)])
            }
        )
        
    except Exception as e:
        logging.error(f"Error getting system alerts: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve system alerts")


def acknowledge_alert(alert_id: int, admin_user_id: int, db: Session):
    """Acknowledge a system alert"""
    try:
        # In a real implementation, you would have an alerts table
        # For now, we'll just return success
        # TODO: Implement proper alert acknowledgment with database storage
        
        return ResponseFactory.success(
            message="Alert acknowledged successfully",
            data={
                "alert_id": alert_id,
                "acknowledged_by": admin_user_id,
                "acknowledged_at": datetime.now(timezone.utc).isoformat()
            }
        )
        
    except Exception as e:
        logging.error(f"Error acknowledging alert: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to acknowledge alert")


def get_realtime_system_health(db: Session):
    """Get real-time system health metrics"""
    try:
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Database health check
        db_start_time = time.time()
        try:
            db.execute(text("SELECT 1"))
            db_response_time = (time.time() - db_start_time) * 1000  # Convert to ms
            db_status = "healthy"
        except Exception as e:
            db_response_time = 0
            db_status = "unhealthy"
            logging.error(f"Database health check failed: {str(e)}")

        # Calculate health score (0-100)
        health_score = calculate_system_health_score(
            cpu_percent, memory.percent, disk.percent, db_response_time
        )

        # Determine overall status
        if health_score >= 90:
            overall_status = "excellent"
        elif health_score >= 75:
            overall_status = "good"
        elif health_score >= 50:
            overall_status = "warning"
        else:
            overall_status = "critical"

        return ResponseFactory.success(
            message="Real-time system health retrieved successfully",
            data={
                "overall_status": overall_status,
                "health_score": health_score,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "system_metrics": {
                    "cpu_usage": round(cpu_percent, 2),
                    "memory_usage": round(memory.percent, 2),
                    "memory_available": round(memory.available / (1024**3), 2),  # GB
                    "disk_usage": round(disk.percent, 2),
                    "disk_free": round(disk.free / (1024**3), 2),  # GB
                },
                "database": {
                    "status": db_status,
                    "response_time_ms": round(db_response_time, 2),
                },
                "alerts": get_system_alerts(cpu_percent, memory.percent, disk.percent, db_response_time),
            },
        )

    except Exception as e:
        logging.error(f"Error getting real-time system health: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve system health")


def get_realtime_business_metrics(db: Session):
    """Get real-time business metrics"""
    try:
        now = datetime.now(timezone.utc)
        last_hour = now - timedelta(hours=1)
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)

        # Real-time donation metrics
        donations_last_hour = db.query(func.count(DonationBatch.id)).filter(
            DonationBatch.created_at >= last_hour,
            DonationBatch.status == "completed"
        ).scalar()

        revenue_last_hour = db.query(func.sum(DonationBatch.amount)).filter(
            DonationBatch.created_at >= last_hour,
            DonationBatch.status == "completed"
        ).scalar() or 0.0

        # 24-hour metrics
        donations_24h = db.query(func.count(DonationBatch.id)).filter(
            DonationBatch.created_at >= last_24h,
            DonationBatch.status == "completed"
        ).scalar()

        revenue_24h = db.query(func.sum(DonationBatch.amount)).filter(
            DonationBatch.created_at >= last_24h,
            DonationBatch.status == "completed"
        ).scalar() or 0.0

        # 7-day metrics
        donations_7d = db.query(func.count(DonationBatch.id)).filter(
            DonationBatch.created_at >= last_7d,
            DonationBatch.status == "completed"
        ).scalar()

        revenue_7d = db.query(func.sum(DonationBatch.amount)).filter(
            DonationBatch.created_at >= last_7d,
            DonationBatch.status == "completed"
        ).scalar() or 0.0

        # Active users (logged in within last hour)
        active_users = db.query(func.count(User.id)).filter(
            User.last_login >= last_hour
        ).scalar()

        # New registrations
        new_users_24h = db.query(func.count(User.id)).filter(
            User.created_at >= last_24h
        ).scalar()

        new_churches_24h = db.query(func.count(Church.id)).filter(
            Church.created_at >= last_24h
        ).scalar()

        # Calculate trends
        hour_ago = now - timedelta(hours=1)
        two_hours_ago = now - timedelta(hours=2)
        
        donations_previous_hour = db.query(func.count(DonationBatch.id)).filter(
            DonationBatch.created_at >= two_hours_ago,
            DonationBatch.created_at < hour_ago,
            DonationBatch.status == "completed"
        ).scalar()

        revenue_previous_hour = db.query(func.sum(DonationBatch.amount)).filter(
            DonationBatch.created_at >= two_hours_ago,
            DonationBatch.created_at < hour_ago,
            DonationBatch.status == "completed"
        ).scalar() or 0.0

        # Calculate growth rates
        donation_growth = calculate_growth_rate(donations_last_hour, donations_previous_hour)
        revenue_growth = calculate_growth_rate(revenue_last_hour, revenue_previous_hour)

        return ResponseFactory.success(
            message="Real-time business metrics retrieved successfully",
            data={
                "timestamp": now.isoformat(),
                "last_hour": {
                    "donations": donations_last_hour,
                    "revenue": round(float(revenue_last_hour), 2),
                    "donation_growth": round(donation_growth, 2),
                    "revenue_growth": round(revenue_growth, 2),
                },
                "last_24h": {
                    "donations": donations_24h,
                    "revenue": round(float(revenue_24h), 2),
                    "new_users": new_users_24h,
                    "new_churches": new_churches_24h,
                },
                "last_7d": {
                    "donations": donations_7d,
                    "revenue": round(float(revenue_7d), 2),
                },
                "active_users": active_users,
                "alerts": get_business_alerts(
                    donations_last_hour, revenue_last_hour, 
                    donation_growth, revenue_growth
                ),
            },
        )

    except Exception as e:
        logging.error(f"Error getting real-time business metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve business metrics")


def get_performance_metrics(db: Session):
    """Get detailed performance metrics"""
    try:
        now = datetime.now(timezone.utc)
        
        # API response times (placeholder - would integrate with monitoring)
        avg_response_time = get_avg_response_time()
        p95_response_time = get_p95_response_time()
        p99_response_time = get_p99_response_time()

        # Database performance
        db_start_time = time.time()
        db.execute(text("SELECT COUNT(*) FROM users"))
        db_query_time = (time.time() - db_start_time) * 1000

        # Cache performance (placeholder)
        cache_hit_rate = get_cache_hit_rate()
        cache_miss_rate = 100 - cache_hit_rate

        # Error rates
        error_rate_24h = get_error_rate_24h()
        error_rate_7d = get_error_rate_7d()

        # Throughput
        requests_per_minute = get_requests_per_minute()
        requests_per_hour = get_requests_per_hour()

        return ResponseFactory.success(
            message="Performance metrics retrieved successfully",
            data={
                "timestamp": now.isoformat(),
                "response_times": {
                    "average_ms": avg_response_time,
                    "p95_ms": p95_response_time,
                    "p99_ms": p99_response_time,
                },
                "database": {
                    "query_time_ms": round(db_query_time, 2),
                    "connections": get_db_connections(),
                },
                "cache": {
                    "hit_rate_percent": cache_hit_rate,
                    "miss_rate_percent": cache_miss_rate,
                },
                "errors": {
                    "rate_24h_percent": error_rate_24h,
                    "rate_7d_percent": error_rate_7d,
                },
                "throughput": {
                    "requests_per_minute": requests_per_minute,
                    "requests_per_hour": requests_per_hour,
                },
            },
        )

    except Exception as e:
        logging.error(f"Error getting performance metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve performance metrics")


def get_system_alerts(
    cpu_percent: float,
    memory_percent: float,
    disk_percent: float,
    db_response_time: float
) -> List[Dict[str, Any]]:
    """Generate system alerts based on metrics"""
    alerts = []

    if cpu_percent > 90:
        alerts.append({
            "type": "cpu",
            "severity": "critical",
            "message": f"High CPU usage: {cpu_percent}%",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    elif cpu_percent > 80:
        alerts.append({
            "type": "cpu",
            "severity": "warning",
            "message": f"Elevated CPU usage: {cpu_percent}%",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    if memory_percent > 90:
        alerts.append({
            "type": "memory",
            "severity": "critical",
            "message": f"High memory usage: {memory_percent}%",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    elif memory_percent > 80:
        alerts.append({
            "type": "memory",
            "severity": "warning",
            "message": f"Elevated memory usage: {memory_percent}%",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    if disk_percent > 90:
        alerts.append({
            "type": "disk",
            "severity": "critical",
            "message": f"High disk usage: {disk_percent}%",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    elif disk_percent > 80:
        alerts.append({
            "type": "disk",
            "severity": "warning",
            "message": f"Elevated disk usage: {disk_percent}%",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    if db_response_time > 1000:  # 1 second
        alerts.append({
            "type": "database",
            "severity": "critical",
            "message": f"Slow database response: {db_response_time}ms",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    elif db_response_time > 500:  # 500ms
        alerts.append({
            "type": "database",
            "severity": "warning",
            "message": f"Elevated database response time: {db_response_time}ms",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    return alerts


def get_business_alerts(
    donations_last_hour: int,
    revenue_last_hour: float,
    donation_growth: float,
    revenue_growth: float
) -> List[Dict[str, Any]]:
    """Generate business alerts based on metrics"""
    alerts = []

    # Check for unusual activity drops
    if donations_last_hour == 0:
        alerts.append({
            "type": "business",
            "severity": "warning",
            "message": "No donations in the last hour",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    # Check for significant growth/decline
    if donation_growth < -50:
        alerts.append({
            "type": "business",
            "severity": "warning",
            "message": f"Significant drop in donations: {donation_growth}%",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    elif donation_growth > 200:
        alerts.append({
            "type": "business",
            "severity": "info",
            "message": f"Significant increase in donations: {donation_growth}%",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    if revenue_growth < -50:
        alerts.append({
            "type": "business",
            "severity": "warning",
            "message": f"Significant drop in revenue: {revenue_growth}%",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    return alerts


def calculate_system_health_score(
    cpu_percent: float,
    memory_percent: float,
    disk_percent: float,
    db_response_time: float
) -> int:
    """Calculate overall system health score (0-100)"""
    score = 100

    # CPU penalty
    if cpu_percent > 90:
        score -= 30
    elif cpu_percent > 80:
        score -= 20
    elif cpu_percent > 70:
        score -= 10

    # Memory penalty
    if memory_percent > 90:
        score -= 30
    elif memory_percent > 80:
        score -= 20
    elif memory_percent > 70:
        score -= 10

    # Disk penalty
    if disk_percent > 90:
        score -= 20
    elif disk_percent > 80:
        score -= 10

    # Database penalty
    if db_response_time > 1000:
        score -= 20
    elif db_response_time > 500:
        score -= 10
    elif db_response_time > 200:
        score -= 5

    return max(score, 0)


def calculate_growth_rate(current: float, previous: float) -> float:
    """Calculate growth rate percentage"""
    if previous == 0:
        return 100.0 if current > 0 else 0.0
    return ((current - previous) / previous) * 100


# Placeholder functions for monitoring integration
def get_avg_response_time() -> float:
    """Get average API response time (placeholder)"""
    return 150.0  # Would integrate with actual monitoring


def get_p95_response_time() -> float:
    """Get P95 API response time (placeholder)"""
    return 300.0


def get_p99_response_time() -> float:
    """Get P99 API response time (placeholder)"""
    return 500.0


def get_cache_hit_rate() -> float:
    """Get cache hit rate (placeholder)"""
    return 85.0


def get_error_rate_24h() -> float:
    """Get 24-hour error rate (placeholder)"""
    return 0.5


def get_error_rate_7d() -> float:
    """Get 7-day error rate (placeholder)"""
    return 0.3


def get_requests_per_minute() -> int:
    """Get requests per minute (placeholder)"""
    return 120


def get_requests_per_hour() -> int:
    """Get requests per hour (placeholder)"""
    return 7200


def get_db_connections() -> int:
    """Get active database connections (placeholder)"""
    return 15
