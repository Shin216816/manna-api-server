"""
Database models for the Manna Backend API.

This package contains all SQLAlchemy models for:
- User management
- Church management
- Banking integration
- Donation processing
- Audit logging
- Authentication tokens
- Messaging system
- User settings
- KYC management
- Payout management
- Referral management
"""

# Core models - essential for functionality
from .m_user import User
from .m_church import Church
from .m_church_admin import ChurchAdmin
from .m_access_codes import AccessCode
from .m_impact_story import ImpactStory
from .m_contact_message import ContactMessage, ContactCategory, ContactPriority

# Payment transaction models - DEPRECATED (PaymentTransaction removed due to redundancy)
# TransactionType and TransactionStatus enums removed - using DonationBatch status instead

# Payment and banking models
# PaymentMethod model removed - using Stripe API directly

# Legacy models - kept for migration purposes (imported only when needed)
from .m_beneficial_owner import BeneficialOwner
from .m_donation_preference import DonationPreference
# # from .m_donation_schedule import DonationSchedule  # Removed - not needed for roundup-only system
# from .m_notification_log import NotificationLog
from .m_audit_log import AuditLog
# from .m_refresh_token import RefreshToken
# from .m_blacklisted_token import BlacklistedToken
# from .m_church_message import ChurchMessage
# from .m_church_referral import ChurchReferral
# from .m_referral_commission import ReferralCommission  # Removed - redundant with church_referrals functionality
# from .m_admin_user import AdminUser
# Removed redundant tables - using real-time calculations instead:
# from .m_roundup_ledger import RoundupLedger  # Use Plaid API real-time calculations
# from .m_period_totals import PeriodTotal      # Use live aggregation from DonorPayout/ChurchPayout
# from .m_payments import Payment  # File not found - may have been removed
from .m_consents import Consent
from .m_plaid_items import PlaidItem
# PlaidAccount model removed - using on-demand Plaid API fetching
# PlaidTransaction model removed - using on-demand Plaid API fetching
from .m_roundup_new import DonorPayout, ChurchPayout
from .m_pending_roundup import PendingRoundup
# RoundupTransaction removed - using DonationBatch instead
from .m_donation_batch import DonationBatch
from .m_referral import ReferralCommission
from .m_donor_settings import DonorSettings

# Main exports - core models and payment transaction models
__all__ = [
    # Core models
    "User",
    "Church", 
    "ChurchAdmin",
    "AccessCode",
    "ImpactStory",
    "ContactMessage",
    "ContactCategory", 
    "ContactPriority",
    
    # Payment transaction models - REMOVED (using DonationBatch status instead)
    
    # Payment models
    # PaymentMethod exports removed - using Stripe API directly
    
    
    # Audit models
    "AuditLog",
    
    # Banking and roundup models
    "PlaidItem",
    # PlaidAccount removed - using on-demand Plaid API fetching
    # PlaidTransaction removed - using on-demand Plaid API fetching
    "DonorPayout",
    "ChurchPayout",
    "PendingRoundup",
    "DonationBatch",
    
    # Legacy models
    "BeneficialOwner",
    "DonationPreference",
    
    # New models - RoundupTransaction removed
    "ReferralCommission",
    "DonorSettings"
]
