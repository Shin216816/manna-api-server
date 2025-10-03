"""
Church Router for Church Admin Web App

Handles church admin endpoints for the web-based admin dashboard:
- Church authentication and profile management
- Church onboarding and KYC management
- Church dashboard and analytics
- Payout management and financial tracking
- Referral system and commission tracking
"""

from fastapi import APIRouter

# Import church sub-routers
from app.router.v1.church.auth import auth_router
from app.router.v1.church.profile import profile_router
from app.router.v1.church.kyc_compliance import router as kyc_compliance_router
from app.router.v1.church.onboarding import onboarding_router
from app.router.v1.church.dashboard import dashboard_router
from app.router.v1.church.analytics import router as analytics_router
from app.router.v1.church.advanced_analytics import router as advanced_analytics_router
from app.router.v1.church.payouts import payouts_router
from app.router.v1.church.referrals import router as referrals_router
from app.router.v1.church.members import members_router
from app.router.v1.church.donor_management import donor_management_router
from app.router.v1.church.roundups import router as roundups_router
from app.router.v1.church.google_oauth import router as google_oauth_router
from app.router.v1.church.impact_stories import impact_stories_router

# Create main church router
church_router = APIRouter()

# Include all church sub-routers
church_router.include_router(auth_router, prefix="/auth", tags=["Church Authentication"])
church_router.include_router(profile_router, prefix="/profile", tags=["Church Profile"])
church_router.include_router(kyc_compliance_router, prefix="/kyc", tags=["Church KYC"])
church_router.include_router(onboarding_router, prefix="/onboarding", tags=["Church Onboarding"])
church_router.include_router(dashboard_router, prefix="/dashboard", tags=["Church Dashboard"])
church_router.include_router(analytics_router, prefix="/analytics", tags=["Church Analytics"])
church_router.include_router(advanced_analytics_router, prefix="/advanced-analytics", tags=["Church Advanced Analytics"])
church_router.include_router(payouts_router, prefix="/payouts", tags=["Church Payouts"])
church_router.include_router(referrals_router, prefix="/referrals", tags=["Church Referrals"])
church_router.include_router(members_router, prefix="/members", tags=["Church Members"])
church_router.include_router(donor_management_router, prefix="/donors", tags=["Church Donor Management"])
church_router.include_router(roundups_router, prefix="/roundups", tags=["Church Round-ups"])
church_router.include_router(google_oauth_router, prefix="/google-oauth", tags=["Google OAuth"])
church_router.include_router(impact_stories_router, prefix="/impact-stories", tags=["Church Impact Stories"])

# Main exports
__all__ = [
    "church_router",
    "auth_router",
    "profile_router",
    "kyc_compliance_router",
    "onboarding_router",
    "dashboard_router",
    "analytics_router",
    "payouts_router",
    "referrals_router",
    "members_router",
    "donor_management_router",
    "roundups_router",
    "google_oauth_router",
    "impact_stories_router"
]
