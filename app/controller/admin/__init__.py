"""
Admin Controller Package
Contains all admin-specific controller functions organized by feature.
"""

# Import admin auth controllers
from app.controller.admin.auth import (
    login_admin, logout_admin, get_admin_profile, refresh_admin_token, get_admin_permissions
)

# Import admin churches controllers
from app.controller.admin.churches import (
    get_all_churches, get_church_details, update_church_status, approve_church_kyc,
    get_church_analytics, get_church_members, get_church_donations
)

# Import admin users controllers
from app.controller.admin.users import (
    get_all_users, get_user_details, update_user_status, get_user_analytics,
    get_user_donations, get_user_church
)

# Import admin analytics controllers
from app.controller.admin.analytics import (
    get_platform_analytics, get_revenue_analytics, get_user_growth_analytics,
    get_church_growth_analytics, get_donation_analytics
)

# Import admin referrals controllers
from app.controller.admin.referrals import (
    get_referral_commissions, get_referral_statistics, get_referral_payouts
)

# Import admin system controllers
from app.controller.admin.system import (
    get_system_status, get_health_check, get_performance_metrics
)

# Import admin KYC controllers
from app.controller.admin.kyc import (
    get_kyc_list, get_kyc_details, approve_kyc, reject_kyc
)

__all__ = [
    # Admin Auth
    "login_admin", "logout_admin", "get_admin_profile", "refresh_admin_token", "get_admin_permissions",
    
    # Admin Churches
    "get_all_churches", "get_church_details", "update_church_status", "approve_church_kyc",
    "get_church_analytics", "get_church_members", "get_church_donations",
    
    # Admin Users
    "get_all_users", "get_user_details", "update_user_status", "get_user_analytics",
    "get_user_donations", "get_user_church",
    
    # Admin Analytics
    "get_platform_analytics", "get_revenue_analytics", "get_user_growth_analytics",
    "get_church_growth_analytics", "get_donation_analytics",
    
    # Admin Referrals
    "get_referral_commissions", "get_referral_statistics", "get_referral_payouts",
    
    # Admin System
    "get_system_status", "get_health_check", "get_performance_metrics",
    
    # Admin KYC
    "get_kyc_list", "get_kyc_details", "approve_kyc", "reject_kyc"
]
