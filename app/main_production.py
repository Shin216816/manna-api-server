"""
Production-Ready Main Application

Integrates all production features:
- Security middleware
- Rate limiting
- Monitoring
- Caching
- Notifications
- Backup services
- Health checks
- Error handling
"""

import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

# Import all production middleware and services
from app.middleware.security_middleware import setup_security_middleware
from app.middleware.rate_limiter import setup_rate_limiting
from app.middleware.monitoring_middleware import setup_monitoring_middleware
from app.middleware.exception_handler import setup_global_exception_handler
from app.services.cache_service import setup_cache_service
from app.services.monitoring_service import get_monitoring_service
from app.services.notification_service import get_notification_service
from app.services.backup_service import get_backup_service

# Import routers
from app.router.v1.donor import auth as donor_auth
from app.router.v1.donor import dashboard as donor_dashboard
from app.router.v1.donor import settings as donor_settings
from app.router.v1.donor import roundups as donor_roundups
from app.router.v1.donor import transactions as donor_transactions
from app.router.v1.donor import bank_linking as donor_bank
from app.router.v1.donor import donations as donor_donations

from app.router.v1.church import auth as church_auth
from app.router.v1.church import dashboard as church_dashboard
from app.router.v1.church import onboarding as church_onboarding
from app.router.v1.church import kyc_compliance as church_kyc
from app.router.v1.church import payouts as church_payouts
from app.router.v1.church import referrals as church_referrals

from app.router.v1.admin import auth as admin_auth
from app.router.v1.admin import churches as admin_churches
from app.router.v1.admin import users as admin_users
from app.router.v1.admin import analytics as admin_analytics
from app.router.v1.admin import enhanced as admin_enhanced

from app.router.v1.shared.health import health_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting Manna Production Application")
    
    # Initialize services
    monitoring_service = get_monitoring_service()
    notification_service = get_notification_service()
    backup_service = get_backup_service()
    
    # Setup cache service
    setup_cache_service()
    
    # Perform initial health check
    try:
        health_status = monitoring_service.check_health(None)
        if health_status['status'] == 'healthy':
            logger.info("Application started successfully")
        else:
            logger.warning(f"Application started with warnings: {health_status}")
    except Exception as e:
        logger.error(f"Health check failed during startup: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Manna Production Application")

# Create FastAPI application
app = FastAPI(
    title="Manna - Micro-Donation Platform",
    description="Production-ready micro-donation platform for churches and donors",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs" if True else None,  # Disable docs in production
    redoc_url="/redoc" if True else None,  # Disable redoc in production
)

# Security middleware (must be first)
setup_security_middleware(app)

# Rate limiting
setup_rate_limiting(app)

# Monitoring middleware
setup_monitoring_middleware(app)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://manna-frontend.vercel.app", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)

# Trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["manna-api-server.onrender.com", "localhost", "127.0.0.1"]
)

# Global exception handler
setup_global_exception_handler(app)

# Include routers
app.include_router(health_router, prefix="/health", tags=["Health"])

# Donor routes
app.include_router(donor_auth.router, prefix="/api/v1/donor", tags=["Donor Auth"])
app.include_router(donor_dashboard.router, prefix="/api/v1/donor", tags=["Donor Dashboard"])
app.include_router(donor_settings.router, prefix="/api/v1/donor", tags=["Donor Settings"])
app.include_router(donor_roundups.router, prefix="/api/v1/donor", tags=["Donor Roundups"])
app.include_router(donor_transactions.router, prefix="/api/v1/donor", tags=["Donor Transactions"])
app.include_router(donor_bank.router, prefix="/api/v1/donor", tags=["Donor Bank"])
app.include_router(donor_donations.router, prefix="/api/v1/donor", tags=["Donor Donations"])

# Church routes
app.include_router(church_auth.auth_router, prefix="/api/v1/church", tags=["Church Auth"])
app.include_router(church_dashboard.dashboard_router, prefix="/api/v1/church", tags=["Church Dashboard"])
app.include_router(church_onboarding.onboarding_router, prefix="/api/v1/church", tags=["Church Onboarding"])
app.include_router(church_kyc.router, prefix="/api/v1/church", tags=["Church KYC"])
app.include_router(church_payouts.payouts_router, prefix="/api/v1/church", tags=["Church Payouts"])
app.include_router(church_referrals.router, prefix="/api/v1/church", tags=["Church Referrals"])

# Admin routes
app.include_router(admin_auth.auth_router, prefix="/api/v1/admin", tags=["Admin Auth"])
app.include_router(admin_churches.churches_router, prefix="/api/v1/admin", tags=["Admin Churches"])
app.include_router(admin_users.users_router, prefix="/api/v1/admin", tags=["Admin Users"])
app.include_router(admin_analytics.analytics_router, prefix="/api/v1/admin", tags=["Admin Analytics"])
app.include_router(admin_enhanced.router, prefix="/api/v1/admin", tags=["Enhanced Admin"])

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with basic information"""
    return {
        "message": "Manna - Micro-Donation Platform API",
        "version": "2.0.0",
        "status": "operational",
        "environment": "production"
    }

# Health check endpoints
@app.get("/health")
async def health_check():
    """Basic health check"""
    monitoring_service = get_monitoring_service()
    return monitoring_service.check_health(None)

@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with metrics"""
    monitoring_service = get_monitoring_service()
    return monitoring_service.get_metrics_summary(None)

# Metrics endpoint for monitoring
@app.get("/metrics")
async def get_metrics():
    """Get application metrics for monitoring systems"""
    monitoring_service = get_monitoring_service()
    return monitoring_service.get_dashboard_data(None)

# Cache statistics endpoint
@app.get("/cache/stats")
async def get_cache_stats():
    """Get cache statistics"""
    from app.services.cache_service import get_cache_service
    cache_service = get_cache_service()
    return cache_service.get_stats()

# Notification history endpoint
@app.get("/notifications/history/{user_id}")
async def get_notification_history(user_id: int, limit: int = 50, offset: int = 0):
    """Get notification history for user"""
    notification_service = get_notification_service()
    return notification_service.get_notification_history(user_id, limit, offset, None)

# Backup management endpoints
@app.post("/admin/backup/create")
async def create_backup():
    """Create database backup"""
    backup_service = get_backup_service()
    try:
        backup_info = backup_service.create_database_backup("manual")
        return {
            "success": True,
            "message": "Backup created successfully",
            "data": {
                "backup_id": backup_info.id,
                "filename": backup_info.filename,
                "size_bytes": backup_info.size_bytes,
                "created_at": backup_info.created_at.isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Backup creation failed: {e}")
        return {
            "success": False,
            "message": f"Backup creation failed: {str(e)}"
        }

@app.get("/admin/backup/list")
async def list_backups():
    """List available backups"""
    backup_service = get_backup_service()
    try:
        backups = backup_service.list_backups()
        return {
            "success": True,
            "data": [
                {
                    "id": backup.id,
                    "filename": backup.filename,
                    "size_bytes": backup.size_bytes,
                    "created_at": backup.created_at.isoformat(),
                    "backup_type": backup.backup_type,
                    "status": backup.status
                }
                for backup in backups
            ]
        }
    except Exception as e:
        logger.error(f"Backup listing failed: {e}")
        return {
            "success": False,
            "message": f"Backup listing failed: {str(e)}"
        }

@app.post("/admin/backup/cleanup")
async def cleanup_backups():
    """Clean up old backups"""
    backup_service = get_backup_service()
    try:
        cleanup_stats = backup_service.cleanup_old_backups()
        return {
            "success": True,
            "message": "Backup cleanup completed",
            "data": cleanup_stats
        }
    except Exception as e:
        logger.error(f"Backup cleanup failed: {e}")
        return {
            "success": False,
            "message": f"Backup cleanup failed: {str(e)}"
        }

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Handle 404 errors"""
    return JSONResponse(
        status_code=200,
        content={
            "success": False,
            "message": "Resource not found",
            "error_code": "NOT_FOUND",
            "request_id": getattr(request.state, 'request_id', None)
        }
    )

@app.exception_handler(405)
async def method_not_allowed_handler(request: Request, exc):
    """Handle 405 errors"""
    return JSONResponse(
        status_code=200,
        content={
            "success": False,
            "message": "Method not allowed",
            "error_code": "METHOD_NOT_ALLOWED",
            "request_id": getattr(request.state, 'request_id', None)
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main_production:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
        access_log=True
    )
