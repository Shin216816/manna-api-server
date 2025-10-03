"""
External service integrations for the Manna Backend API.

This package contains all external service integrations:
- Plaid banking API integration
- Stripe payment processing
- Referral system management
- Analytics services
- Roundup services
- Payment method services
"""

# External service clients
from app.services.plaid_client import plaid_client
from app.services.stripe_service import transfer_to_church

# Unified services
from app.services.analytics_service import get_platform_analytics, get_church_analytics, get_user_analytics
from app.services.roundup_service import roundup_service
from app.services.stripe_service import (
    create_payment_method_for_user as create_payment_method,
    list_payment_methods_for_user as list_payment_methods,
    update_payment_method_for_user as update_payment_method,
    delete_payment_method_for_user as delete_payment_method,
    set_default_payment_method_for_user as set_default_payment_method,
    get_default_payment_method_for_customer as get_default_payment_method,
    validate_payment_method_for_user as validate_payment_method
)
from app.services.referral import (
    calculate_referral_commission,
    get_referral_summary,
    track_referral_donation,
    get_referral_stats
)

# New services
from app.services.plaid_webhook_service import plaid_webhook_service

# Main exports
__all__ = [
    # Plaid client
    "plaid_client",
    "create_link_token",
    "exchange_public_token",
    "get_accounts",
    "get_balances",
    "get_transactions",
    "get_transactions_with_options",
    "get_institution_by_id",
    
    # Stripe service
    "transfer_to_church",
    
    # Unified analytics service
    "get_platform_analytics",
    "get_church_analytics", 
    "get_user_analytics",
    
    # Unified roundup service
    "roundup_service",
    
    # Payment method services
    "create_payment_method",
    "list_payment_methods",
    "update_payment_method",
    "delete_payment_method",
    "set_default_payment_method",
    "get_default_payment_method",
    "validate_payment_method",
    
    # Referral service
    "calculate_referral_commission",
    "get_referral_summary",
    "track_referral_donation",
    "get_referral_stats",
    
    # Plaid webhook service
    "plaid_webhook_service"
] 
