"""
Mobile Controller Package
Contains all mobile-specific controller functions organized by feature.
"""

# Import auth controllers
from app.controller.mobile.auth import (
    register, register_code_resend, register_code_confirm,
    login, logout, forgot_password, verify_otp, reset_password,
    google_oauth_login, biometric_login, refresh_token, apple_oauth_login
)

# Import profile controllers
from app.controller.mobile.profile import (
    get_mobile_profile, update_mobile_profile, upload_mobile_profile_image, remove_mobile_profile_image,
    send_email_verification, confirm_email_verification,
    send_phone_verification, confirm_phone_verification
)

# Import bank controllers
from app.controller.mobile.bank import (
    create_mobile_link_token, exchange_mobile_public_token, get_mobile_transactions,
    get_mobile_bank_accounts, get_mobile_donation_history, get_mobile_donation_summary,
    get_mobile_impact_analytics, list_mobile_payment_methods, delete_mobile_payment_method,
    save_mobile_payment_method
)

# Import roundups controllers
from app.controller.mobile.roundups import (
    get_mobile_roundup_settings, update_mobile_roundup_settings,
    get_mobile_pending_roundups, quick_toggle_roundups,
    get_mobile_impact_summary
)

# Import notifications controllers
from app.controller.mobile.notifications import (
    get_mobile_notifications, mark_notification_read, mark_all_notifications_read,
    delete_notification, get_notification_preferences, update_notification_preferences
)

# Import dashboard controllers
from app.controller.mobile.dashboard import (
    get_mobile_dashboard
)

__all__ = [
    # Auth
    "register", "register_code_resend", "register_code_confirm",
    "login", "logout", "forgot_password", "verify_otp", "reset_password",
    "google_oauth_login", "biometric_login", "refresh_token", "apple_oauth_login",

    # Profile
    "get_mobile_profile", "update_mobile_profile", "upload_mobile_profile_image", "remove_mobile_profile_image",
    "send_email_verification", "confirm_email_verification",
    "send_phone_verification", "confirm_phone_verification",

    # Bank
    "create_mobile_link_token", "exchange_mobile_public_token", "get_mobile_transactions",
    "get_mobile_bank_accounts", "get_mobile_donation_history", "get_mobile_donation_summary",
    "get_mobile_impact_analytics", "list_mobile_payment_methods", "delete_mobile_payment_method",
    "save_mobile_payment_method",

    # Roundups
    "get_mobile_roundup_settings", "update_mobile_roundup_settings",
    "get_mobile_pending_roundups", "quick_toggle_roundups",
    "get_mobile_impact_summary",

    # Notifications
    "get_mobile_notifications", "mark_notification_read", "mark_all_notifications_read",
    "delete_notification", "get_notification_preferences", "update_notification_preferences",

    # Dashboard
    "get_mobile_dashboard",
]
