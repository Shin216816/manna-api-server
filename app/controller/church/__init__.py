"""
Church admin controllers for church management functionality.
"""

from app.controller.church.auth import (
    register_church_admin,
    login_church_admin,
    refresh_church_token,
    logout_church
)

from app.controller.church.profile import (
    get_church_profile,
    update_church_profile,
    upload_church_logo,
    update_church_contact,
    update_church_branding
)

from app.controller.church.kyc import (
    init_kyc,
    generate_kyc_link,
    get_kyc_status,
    get_payouts_status
)

from app.controller.church.dashboard import (
    get_church_dashboard,
    get_church_analytics,
    get_church_members,
    get_church_donations
)

from app.controller.church.analytics import (
    get_church_analytics,
    get_donor_analytics,
    get_revenue_analytics,
    get_giving_patterns
)

from app.controller.church.payouts import (
    get_payout_history,
    get_payout_details,
    get_payout_status
)

from app.controller.church.referrals import (
    generate_referral_code,
    get_referral_info,
    get_referral_commissions,
    calculate_referral_commissions
)

from app.controller.church.members import (
    get_church_members,
    get_member_details,
    get_member_giving_history,
    search_members
)

__all__ = [
    # Auth
    "register_church_admin",
    "login_church_admin",
    "refresh_church_token",
    "logout_church",
    
    # Profile
    "get_church_profile",
    "update_church_profile",
    "upload_church_logo",
    "update_church_contact",
    "update_church_branding",
    
    # KYC
    "init_kyc",
    "generate_kyc_link",
    "get_kyc_status",
    "get_payouts_status",
    
    # Dashboard
    "get_church_dashboard",
    "get_church_analytics",
    "get_church_members",
    "get_church_donations",
    
    # Analytics
    "get_church_analytics",
    "get_donor_analytics",
    "get_revenue_analytics",
    "get_giving_patterns",
    
    # Payouts
    "get_payout_history",
    "get_payout_details",
    "get_payout_status",
    
    # Referrals
    "get_referral_code",
    "get_referral_list",
    "get_referral_commissions",
    "get_referral_statistics",
    
    # Members
    "get_church_members",
    "get_member_details",
    "get_member_giving_history",
    "search_members"
] 
