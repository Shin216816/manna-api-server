"""
Admin Router for Manna Internal Admin Web App

Handles admin endpoints for platform management and oversight:
- KYC review and approval workflow
- Church management and monitoring
- User management and support
- Platform analytics and reporting
- Referral commission management
- Enhanced real-time monitoring
- Advanced analytics and insights
"""

from fastapi import APIRouter

# Import admin sub-routers
from app.router.v1.admin.auth import auth_router
from app.router.v1.admin.churches import churches_router
from app.router.v1.admin.users import users_router
from app.router.v1.admin.analytics import analytics_router
from app.router.v1.admin.kyc import kyc_router
from app.router.v1.admin.kyc_review import router as kyc_review_router
from app.router.v1.admin.payouts import payout_router
from app.router.v1.admin.referrals import referrals_router
from app.router.v1.admin.system import system_router
from app.router.v1.admin.dashboard import router as dashboard_router

# Create main admin router
admin_router = APIRouter()

# Include all admin sub-routers
admin_router.include_router(auth_router, tags=["Admin Authentication"])
admin_router.include_router(churches_router, prefix="/churches", tags=["Admin Churches"])
admin_router.include_router(users_router, prefix="/users", tags=["Admin Users"])
admin_router.include_router(analytics_router, prefix="/analytics", tags=["Admin Analytics"])
admin_router.include_router(kyc_router, prefix="/kyc", tags=["Admin KYC"])
admin_router.include_router(kyc_review_router, prefix="/kyc-review", tags=["Admin KYC Review"])
admin_router.include_router(payout_router, prefix="/payouts", tags=["Admin Payouts"])
admin_router.include_router(referrals_router, prefix="/referrals", tags=["Admin Referrals"])
admin_router.include_router(system_router, prefix="/system", tags=["Admin System"])
admin_router.include_router(dashboard_router, prefix="/dashboard", tags=["Admin Dashboard"])

# Main exports
__all__ = [
    "admin_router",
    "auth_router",
    "churches_router",
    "users_router",
    "analytics_router",
    "kyc_router",
    "kyc_review_router",
    "payouts_router",
    "referrals_router",
    "system_router",
    "dashboard_router"
]