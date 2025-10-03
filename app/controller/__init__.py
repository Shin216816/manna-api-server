"""
Controller Package
Contains all controller functions organized by user type and functionality.
"""

# Import mobile controllers
from app.controller.mobile.auth import (
    register, login, logout, forgot_password, verify_otp, reset_password,
    google_oauth_login, apple_oauth_login, refresh_token, biometric_login,
    register_code_confirm, register_code_resend
)

from app.controller.mobile.profile import (
    get_mobile_profile, update_mobile_profile, upload_mobile_profile_image, remove_mobile_profile_image,
    send_email_verification, confirm_email_verification,
    send_phone_verification, confirm_phone_verification
)

from app.controller.mobile.bank import (
    create_mobile_link_token, exchange_mobile_public_token, get_mobile_transactions,
    get_mobile_bank_accounts, get_mobile_donation_history, get_mobile_donation_summary,
    get_mobile_impact_analytics, list_mobile_payment_methods, delete_mobile_payment_method,
    save_mobile_payment_method
)

from app.controller.mobile.roundups import (
    get_mobile_roundup_settings, update_mobile_roundup_settings,
    get_mobile_pending_roundups, quick_toggle_roundups,
    get_mobile_impact_summary
)

from app.controller.mobile.notifications import (
    get_mobile_notifications, mark_notification_read, mark_all_notifications_read,
    delete_notification, get_notification_preferences, update_notification_preferences
)

from app.controller.mobile.dashboard import (
    get_mobile_dashboard
)

# Import church controllers
from app.controller.church.auth import (
    register_church_admin, login_church_admin, logout_church, refresh_church_token
)

from app.controller.church.dashboard import (
    get_church_dashboard, get_church_analytics, get_church_members, get_church_donations
)

from app.controller.church.analytics import (
    get_church_analytics, get_donor_analytics, get_revenue_analytics, get_giving_patterns, get_performance_metrics
)

from app.controller.church.profile import (
    get_church_profile, update_church_profile, upload_church_logo, remove_church_logo,
    get_church_logo, get_church_contact, update_church_contact, get_church_branding, update_church_branding
)

from app.controller.church.kyc import (
    init_kyc, generate_kyc_link, get_kyc_status, get_payouts_status
)

from app.controller.church.members import (
    get_church_members, get_member_details, get_member_giving_history, search_members
)

# Import admin controllers
from app.controller.admin.auth import (
    login_admin, logout_admin, refresh_admin_token, get_admin_profile
)

from app.controller.admin.churches import (
    get_all_churches, get_church_details, update_church_status, get_church_analytics
)

from app.controller.admin.users import (
    get_all_users, get_user_details, update_user_status, get_user_analytics
)

from app.controller.admin.analytics import (
    get_platform_analytics, get_revenue_analytics, get_user_growth_analytics, get_church_growth_analytics, get_donation_analytics
)

from app.controller.admin.system import (
    get_system_status, get_health_check, get_performance_metrics
)

from app.controller.admin.kyc import (
    get_kyc_list, get_kyc_details, approve_kyc, reject_kyc
)

from app.controller.admin.referrals import (
    get_referral_commissions, get_referral_statistics, get_referral_payouts
)

# Import shared controllers
from app.controller.shared.health import (
    health_check, detailed_health_check
)

from app.controller.shared.webhooks import (
    handle_stripe_webhook, handle_plaid_webhook
)

from app.controller.shared.stripe import (
    create_payment_intent, confirm_payment, get_payment_status
)

from app.controller.shared.files import (
    upload_file_controller, delete_file_controller, get_file_url_controller
)

__all__ = [
    # Mobile controllers
    "register", "login", "logout", "forgot_password", "verify_otp", "reset_password",
    "google_oauth_login", "apple_oauth_login", "refresh_token", "biometric_login",
    "register_code_confirm", "register_code_resend",
    "get_mobile_profile", "update_mobile_profile", "upload_mobile_profile_image", "remove_mobile_profile_image",
    "send_email_verification", "confirm_email_verification",
    "send_phone_verification", "confirm_phone_verification",
    "create_mobile_link_token", "exchange_mobile_public_token", "get_mobile_transactions",
    "get_mobile_bank_accounts", "get_mobile_donation_history", "get_mobile_donation_summary",
    "get_mobile_impact_analytics", "list_mobile_payment_methods", "delete_mobile_payment_method",
    "save_mobile_payment_method", "get_mobile_roundup_settings", "update_mobile_roundup_settings",
    "get_mobile_pending_roundups", "quick_toggle_roundups", "get_mobile_impact_summary",
    "get_mobile_notifications", "mark_notification_read", "mark_all_notifications_read",
    "delete_notification", "get_notification_preferences", "update_notification_preferences",
    "get_mobile_dashboard",
    
    # Church controllers
    "register_church_admin", "login_church_admin", "logout_church", "refresh_church_token",
    "get_church_dashboard", "get_church_analytics", "get_church_members", "get_church_donations",
    "get_church_analytics", "get_donor_analytics", "get_revenue_analytics", "get_giving_patterns", "get_performance_metrics",
    "get_church_profile", "update_church_profile", "upload_church_logo", "remove_church_logo",
    "get_church_logo", "get_church_contact", "update_church_contact", "get_church_branding", "update_church_branding",
    "init_kyc", "generate_kyc_link", "get_kyc_status", "get_payouts_status",
    "get_church_members", "get_member_details", "get_member_giving_history", "search_members",
    
    # Admin controllers
    "login_admin", "logout_admin", "refresh_admin_token", "get_admin_profile",
    "get_all_churches", "get_church_details", "update_church_status", "get_church_analytics",
    "get_all_users", "get_user_details", "update_user_status", "get_user_analytics",
    "get_platform_analytics", "get_revenue_analytics", "get_user_growth_analytics", "get_church_growth_analytics", "get_donation_analytics",
    "get_system_status", "get_health_check", "get_performance_metrics",
    "get_kyc_list", "get_kyc_details", "approve_kyc", "reject_kyc",
    "get_referral_commissions", "get_referral_statistics", "get_referral_payouts",
    
    # Shared controllers
    "health_check", "detailed_health_check",
    "handle_stripe_webhook", "handle_plaid_webhook",
    "create_payment_intent", "confirm_payment", "get_payment_status",
    "upload_file_controller", "delete_file_controller", "get_file_url_controller"
]
