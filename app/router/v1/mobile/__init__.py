"""
Mobile API Router

Handles mobile app endpoints for:
- Authentication
- Stripe payments
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from app.utils.database import get_db
from app.middleware.auth_middleware import jwt_auth
from app.core.responses import SuccessResponse, ResponseFactory
from typing import Optional, Dict, Any
import logging
from datetime import timedelta

# Import controllers
from app.controller.mobile.auth import (
    login, register, logout, change_mobile_password,
    forgot_password, reset_password, verify_otp, register_code_resend,
    register_code_confirm, refresh_token
)
from app.controller.mobile.stripe import (
    get_stripe_config, create_stripe_customer, get_stripe_customer, update_stripe_customer,
    create_payment_intent_handler, confirm_payment_intent_handler, get_payment_intent_handler,
    cancel_payment_intent_handler, create_setup_intent_handler, get_setup_intent_handler,
    attach_payment_method_handler, detach_payment_method_handler, list_payment_methods_handler, 
    update_payment_method_handler, create_charge_handler, create_connect_account_handler, 
    create_account_link_handler, get_connect_account_handler, create_refund_handler, 
    get_balance_handler, list_charges_handler, transfer_to_church_handler
)
from app.controller.mobile.bank import (
    create_mobile_link_token, exchange_mobile_public_token, get_mobile_transactions,
    get_mobile_bank_accounts, get_mobile_donation_history, get_mobile_donation_summary,
    ensure_stripe_customer, save_mobile_payment_method, delete_payment_method,
    set_default_payment_method, get_bank_dashboard, get_bank_preferences,
    update_bank_preferences, fetch_mobile_transactions
)
from app.controller.mobile.church import (
    search_churches, get_church_details, get_user_church, remove_user_from_church,
    select_church_for_user,
    refresh_user_data_after_church_selection,
    get_user_church_status
)
from app.controller.mobile.dashboard import get_mobile_dashboard
from app.controller.mobile.roundups import (
    get_mobile_pending_roundups, get_mobile_roundup_settings, 
    update_mobile_roundup_settings, get_mobile_impact_summary, quick_toggle_roundups
)
from app.controller.mobile.profile import (
    get_mobile_profile, update_mobile_profile, upload_mobile_profile_image,
    remove_mobile_profile_image, send_email_verification, confirm_email_verification,
    send_phone_verification, confirm_phone_verification
)
from app.controller.mobile.notifications import (
    get_mobile_notifications, mark_notification_read, mark_all_notifications_read,
    delete_notification, get_notification_preferences, update_notification_preferences
)
from app.controller.mobile.messages import (
    get_unread_message_count
)
from app.controller.mobile.identity import (
    start_identity_verification, get_identity_status,
    cancel_identity_verification, get_identity_info
)

# Import schemas
from app.schema.auth_schema import (
    AuthLoginRequest, AuthRegisterRequest, AuthChangePasswordRequest,
    AuthForgotPasswordRequest, AuthResetPasswordRequest, AuthVerifyOtpRequest,
    RefreshTokenRequest, AuthLogoutRequest, AuthRegisterCodeResendRequest,
    AuthRegisterConfirmRequest
)
from app.schema.stripe_schema import (
    CustomerCreateRequest, CustomerUpdateRequest, PaymentIntentCreateRequest,
    PaymentIntentConfirmRequest, SetupIntentCreateRequest, PaymentMethodAttachRequest,
    PaymentMethodUpdateRequest, ChargeCreateRequest, ConnectAccountCreateRequest,
    AccountLinkCreateRequest, RefundCreateRequest, TransferCreateRequest
)
from app.schema.bank_schema import (
    CreateLinkTokenRequest, ExchangePublicTokenRequest, GetTransactionsRequest
)

mobile_router = APIRouter(tags=["Mobile API"])

# Authentication Endpoints
@mobile_router.post("/auth/login", response_model=SuccessResponse)
async def login_route(login_data: AuthLoginRequest, db: Session = Depends(get_db)):
    """User login"""
    return login(login_data, db)

@mobile_router.post("/auth/register", response_model=SuccessResponse)
async def register_route(register_data: AuthRegisterRequest, db: Session = Depends(get_db)):
    """User registration"""
    return register(register_data, db)

@mobile_router.post("/auth/refresh", response_model=SuccessResponse)
async def refresh_token_route(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """Refresh access token"""
    return refresh_token(refresh_data, db)

@mobile_router.post("/auth/logout", response_model=SuccessResponse)
async def logout_route(
    logout_data: AuthLogoutRequest,
    db: Session = Depends(get_db)
):
    """User logout"""
    return logout(logout_data, db)

@mobile_router.post("/auth/change-password", response_model=SuccessResponse)
async def change_password_route(
    password_data: AuthChangePasswordRequest,
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Change user password"""
    return change_mobile_password(current_user["id"], password_data.old_password, password_data.new_password, db)

@mobile_router.post("/auth/forgot-password", response_model=SuccessResponse)
async def forgot_password_route(
    forgot_data: AuthForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    """Request password reset"""
    return forgot_password(forgot_data, db)

@mobile_router.post("/auth/reset-password", response_model=SuccessResponse)
async def reset_password_route(
    reset_data: AuthResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """Reset password with token"""
    return reset_password(reset_data, db)

@mobile_router.post("/auth/verify-otp", response_model=SuccessResponse)
async def verify_otp_route(
    verify_data: AuthVerifyOtpRequest,
    db: Session = Depends(get_db)
):
    """Verify OTP"""
    return verify_otp(verify_data, db)

@mobile_router.post("/auth/register/confirm", response_model=SuccessResponse)
async def register_confirm_route(
    confirm_data: AuthRegisterConfirmRequest,
    db: Session = Depends(get_db)
):
    """Confirm registration with verification code"""
    return register_code_confirm(confirm_data, db)

@mobile_router.post("/auth/register/resend-code", response_model=SuccessResponse)
async def resend_verification_route(
    resend_data: AuthRegisterCodeResendRequest,
    db: Session = Depends(get_db)
):
    """Resend verification code"""
    return register_code_resend(resend_data, db)

@mobile_router.post("/auth/google", response_model=SuccessResponse)
async def google_oauth_route(
    data: dict,
    db: Session = Depends(get_db)
):
    """Google OAuth login"""
    from app.controller.mobile.auth import google_oauth_login
    return google_oauth_login(data, db)

@mobile_router.post("/auth/apple", response_model=SuccessResponse)
async def apple_oauth_route(
    data: dict,
    db: Session = Depends(get_db)
):
    """Apple OAuth login"""
    from app.controller.mobile.auth import apple_oauth_login
    return apple_oauth_login(data, db)

# Stripe Configuration Endpoint
@mobile_router.get("/stripe/config", response_model=SuccessResponse)
async def get_stripe_config_route():
    """Get Stripe configuration for mobile app"""
    return get_stripe_config()

# Customer Management Endpoints
@mobile_router.post("/stripe/customers", response_model=SuccessResponse)
async def create_customer_route(
    customer_data: CustomerCreateRequest,
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Create a Stripe customer for the authenticated user"""
    return create_stripe_customer(current_user["id"], customer_data, db)

@mobile_router.get("/stripe/customers/me", response_model=SuccessResponse)
async def get_customer_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get Stripe customer information for the authenticated user"""
    return get_stripe_customer(current_user["id"], db)

@mobile_router.put("/stripe/customers/me", response_model=SuccessResponse)
async def update_customer_route(
    update_data: CustomerUpdateRequest,
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Update Stripe customer information for the authenticated user"""
    return update_stripe_customer(current_user["id"], update_data, db)

# Payment Intent Endpoints
@mobile_router.post("/stripe/payment-intents", response_model=SuccessResponse)
async def create_payment_intent_route(
    payment_data: PaymentIntentCreateRequest,
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Create a Payment Intent for processing payments"""
    return create_payment_intent_handler(current_user["id"], payment_data, db)

@mobile_router.post("/stripe/payment-intents/confirm", response_model=SuccessResponse)
async def confirm_payment_intent_route(
    payment_data: PaymentIntentConfirmRequest
):
    """Confirm a Payment Intent"""
    return confirm_payment_intent_handler(payment_data)

@mobile_router.get("/stripe/payment-intents/{payment_intent_id}", response_model=SuccessResponse)
async def get_payment_intent_route(payment_intent_id: str):
    """Get Payment Intent details"""
    return get_payment_intent_handler(payment_intent_id)

@mobile_router.post("/stripe/payment-intents/{payment_intent_id}/cancel", response_model=SuccessResponse)
async def cancel_payment_intent_route(payment_intent_id: str):
    """Cancel a Payment Intent"""
    return cancel_payment_intent_handler(payment_intent_id)

# Setup Intent Endpoints
@mobile_router.post("/stripe/setup-intents", response_model=SuccessResponse)
async def create_setup_intent_route(
    setup_data: SetupIntentCreateRequest,
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Create a Setup Intent for saving payment methods"""
    return create_setup_intent_handler(current_user["id"], setup_data, db)

@mobile_router.get("/stripe/setup-intents/{setup_intent_id}", response_model=SuccessResponse)
async def get_setup_intent_route(
    setup_intent_id: str,
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get Setup Intent details"""
    return get_setup_intent_handler(setup_intent_id, current_user["id"], db)

# Payment Method Endpoints
@mobile_router.post("/stripe/payment-methods/{payment_method_id}/attach", response_model=SuccessResponse)
async def attach_payment_method_route(
    payment_method_id: str,
    attach_data: PaymentMethodAttachRequest,
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Attach a payment method to the authenticated user's Stripe customer"""
    return attach_payment_method_handler(current_user["id"], attach_data, db)

@mobile_router.delete("/stripe/payment-methods/{payment_method_id}", response_model=SuccessResponse)
async def detach_payment_method_route(payment_method_id: str):
    """Detach a payment method from the authenticated user's Stripe customer"""
    return detach_payment_method_handler(payment_method_id)

@mobile_router.get("/stripe/payment-methods", response_model=SuccessResponse)
async def list_payment_methods_route(
    type: str = Query(default="card", description="Payment method type"),
    limit: int = Query(default=100, description="Number of payment methods to return"),
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """List payment methods for the authenticated user's Stripe customer"""
    return list_payment_methods_handler(current_user["id"], db, type, limit)

@mobile_router.put("/stripe/payment-methods/{payment_method_id}", response_model=SuccessResponse)
async def update_payment_method_route(
    payment_method_id: str,
    update_data: PaymentMethodUpdateRequest
):
    """Update a payment method"""
    return update_payment_method_handler(payment_method_id, update_data)

# Charge Endpoints
@mobile_router.post("/stripe/charges", response_model=SuccessResponse)
async def create_charge_route(
    charge_data: ChargeCreateRequest,
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Create a charge"""
    return create_charge_handler(current_user["id"], charge_data, db)

@mobile_router.get("/stripe/charges", response_model=SuccessResponse)
async def list_charges_route(
    limit: int = Query(default=100, description="Number of charges to return"),
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """List charges for the authenticated user"""
    return list_charges_handler(current_user["id"], db, limit)

# Connect Account Endpoints
@mobile_router.post("/stripe/connect/accounts", response_model=SuccessResponse)
async def create_connect_account_route(
    account_data: ConnectAccountCreateRequest,
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Create a Stripe Connect account"""
    return create_connect_account_handler(account_data, db)

@mobile_router.post("/stripe/connect/account-links", response_model=SuccessResponse)
async def create_account_link_route(
    link_data: AccountLinkCreateRequest
):
    """Create an account link for Stripe Connect onboarding"""
    return create_account_link_handler(link_data)

@mobile_router.get("/stripe/connect/accounts/{account_id}", response_model=SuccessResponse)
async def get_connect_account_route(account_id: str):
    """Get Stripe Connect account details"""
    return get_connect_account_handler(account_id)

# Refund Endpoints
@mobile_router.post("/stripe/refunds", response_model=SuccessResponse)
async def create_refund_route(
    refund_data: RefundCreateRequest
):
    """Create a refund"""
    return create_refund_handler(refund_data)

# Balance Endpoints
@mobile_router.get("/stripe/balance", response_model=SuccessResponse)
async def get_balance_route():
    """Get Stripe account balance"""
    return get_balance_handler()

# Transfer Endpoints
@mobile_router.post("/stripe/transfers", response_model=SuccessResponse)
async def transfer_to_church_route(
    transfer_data: TransferCreateRequest,
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Transfer funds to a church"""
    return transfer_to_church_handler(current_user["id"], transfer_data, db)

# User Profile Endpoints
@mobile_router.get("/auth/me", response_model=SuccessResponse)
async def get_current_user_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get current user profile with complete data"""
    # Return complete profile data (same as /profile endpoint)
    return get_mobile_profile(current_user["id"], db)

@mobile_router.get("/profile", response_model=SuccessResponse)
async def get_profile_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get user profile"""
    return get_mobile_profile(current_user["id"], db)

@mobile_router.put("/profile", response_model=SuccessResponse)
async def update_profile_route(
    profile_data: dict,
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Update user profile"""
    return update_mobile_profile(current_user["id"], profile_data, db)

@mobile_router.post("/profile/image", response_model=SuccessResponse)
async def upload_profile_image_route(
    file: UploadFile = File(...),
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Upload profile image"""
    from app.controller.mobile.profile import upload_mobile_profile_image
    return upload_mobile_profile_image(current_user["id"], file, db)

@mobile_router.delete("/profile/image", response_model=SuccessResponse)
async def delete_profile_image_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Delete profile image"""
    from app.controller.mobile.profile import delete_mobile_profile_image
    return delete_mobile_profile_image(current_user["id"], db)

@mobile_router.get("/profile/image", response_model=SuccessResponse)
async def get_profile_image_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get profile image URL"""
    from app.controller.mobile.profile import get_mobile_profile_image
    return get_mobile_profile_image(current_user["id"], db)

# Additional profile endpoints expected by Flutter app
@mobile_router.get("/auth/profile/stats", response_model=SuccessResponse)
async def get_profile_stats_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get profile statistics"""
    from app.controller.mobile.analytics import get_mobile_user_analytics
    return get_mobile_user_analytics(current_user["id"], db)

@mobile_router.get("/auth/profile/activity", response_model=SuccessResponse)
async def get_profile_activity_route(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    start_date: str = Query(default=None),
    end_date: str = Query(default=None),
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get profile activity history"""
    from app.controller.mobile.donations import get_mobile_donation_history
    return get_mobile_donation_history(current_user["id"], limit, db)

@mobile_router.put("/auth/profile/preferences", response_model=SuccessResponse)
async def update_profile_preferences_route(
    preferences_data: dict,
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Update profile preferences"""
    from app.controller.mobile.bank import update_bank_preferences
    return update_bank_preferences(current_user["id"], preferences_data, db)

@mobile_router.get("/auth/profile/preferences", response_model=SuccessResponse)
async def get_profile_preferences_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get profile preferences"""
    from app.controller.mobile.bank import get_bank_preferences
    return get_bank_preferences(current_user["id"], db)

# Bank Account Endpoints
@mobile_router.post("/bank/link-token", response_model=SuccessResponse)
async def create_link_token_route(
    data: CreateLinkTokenRequest,
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Create Plaid link token"""
    return create_mobile_link_token(data, current_user, db)

@mobile_router.post("/bank/exchange-token", response_model=SuccessResponse)
async def exchange_public_token_route(
    data: ExchangePublicTokenRequest,
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Exchange public token for access token"""
    return exchange_mobile_public_token(data, current_user, db)

@mobile_router.get("/bank/accounts", response_model=SuccessResponse)
async def get_bank_accounts_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get user's bank accounts"""
    return get_mobile_bank_accounts(current_user, db)

@mobile_router.post("/bank/transactions", response_model=SuccessResponse)
async def get_bank_transactions_route(
    data: GetTransactionsRequest,
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get bank transactions"""
    return fetch_mobile_transactions(data, current_user, db)

@mobile_router.get("/transactions", response_model=SuccessResponse)
async def get_transactions_route(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    start_date: str = Query(default=None),
    end_date: str = Query(default=None),
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get user transactions"""
    from app.controller.mobile.bank import get_user_transactions
    return get_user_transactions(current_user["id"], page, limit, start_date, end_date, db)

@mobile_router.get("/bank/donation-history", response_model=SuccessResponse)
async def get_bank_donation_history_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get bank donation history"""
    return get_mobile_donation_history(current_user, db)

@mobile_router.get("/bank/donation-summary", response_model=SuccessResponse)
async def get_donation_summary_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get donation summary"""
    return get_mobile_donation_summary(current_user, db)

@mobile_router.get("/bank/calculate-roundups", response_model=SuccessResponse)
async def calculate_roundups_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Calculate roundups for user"""
    from app.controller.mobile.donations import calculate_roundups
    return calculate_roundups(current_user["id"], db)

@mobile_router.get("/bank/dashboard", response_model=SuccessResponse)
async def get_bank_dashboard_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get bank dashboard"""
    return get_bank_dashboard(current_user["id"], db)

@mobile_router.get("/bank/preferences", response_model=SuccessResponse)
async def get_bank_preferences_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get bank preferences"""
    return get_bank_preferences(current_user["id"], db)

@mobile_router.put("/bank/preferences", response_model=SuccessResponse)
async def update_bank_preferences_route(
    preferences_data: dict,
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Update bank preferences"""
    return update_bank_preferences(current_user["id"], preferences_data, db)

@mobile_router.post("/bank/ensure-stripe-customer", response_model=SuccessResponse)
async def ensure_stripe_customer_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Ensure user has Stripe customer ID"""
    return ensure_stripe_customer(current_user["id"], db)

@mobile_router.post("/bank/payment-methods", response_model=SuccessResponse)
async def save_payment_method_route(
    payment_method_data: dict,
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Save payment method"""
    return save_mobile_payment_method(
        current_user["id"], 
        payment_method_data.get("payment_method_id"), 
        current_user, 
        db
    )

@mobile_router.get("/bank/payment-methods", response_model=SuccessResponse)
async def get_bank_payment_methods_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get user's payment methods"""
    from app.controller.mobile.bank import list_mobile_payment_methods
    return list_mobile_payment_methods(current_user, db)

@mobile_router.delete("/bank/payment-methods/{payment_method_id}", response_model=SuccessResponse)
async def delete_payment_method_route(
    payment_method_id: str,
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Delete payment method"""
    return delete_payment_method(payment_method_id, current_user["id"], db)

@mobile_router.put("/bank/payment-methods/{payment_method_id}/default", response_model=SuccessResponse)
async def set_default_payment_method_route(
    payment_method_id: str,
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Set default payment method"""
    return set_default_payment_method(payment_method_id, current_user["id"], db)

# Enhanced Roundup Endpoints
@mobile_router.get("/enhanced-roundup-status", response_model=SuccessResponse)
async def get_enhanced_roundup_status_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get enhanced roundup status"""
    return get_mobile_pending_roundups(current_user["id"], db)

# Church Messages Endpoints
@mobile_router.get("/church-messages", response_model=SuccessResponse)
async def get_church_messages_route(
    limit: int = Query(default=50, description="Number of messages to return"),
    offset: int = Query(default=0, description="Number of messages to skip"),
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get church messages"""
    return get_mobile_notifications(current_user["id"], db, limit, offset)

@mobile_router.get("/church-messages/unread-count", response_model=SuccessResponse)
async def get_church_messages_unread_count_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get unread church messages count"""
    return get_unread_message_count(current_user["id"], db)

# Pending Roundups Endpoints
@mobile_router.get("/pending-roundups", response_model=SuccessResponse)
async def get_pending_roundups_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get pending roundups"""
    return get_mobile_pending_roundups(current_user["id"], db)

# Church Search Endpoints
@mobile_router.get("/church/search", response_model=SuccessResponse)
async def search_churches_route(
    q: str = Query(..., description="Search query"),
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Search churches"""
    return search_churches(q, db)

@mobile_router.get("/church/{church_id}", response_model=SuccessResponse)
async def get_church_details_route(
    church_id: int,
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get church details"""
    return get_church_details(church_id, db)

@mobile_router.get("/church/user/me", response_model=SuccessResponse)
async def get_user_church_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get user's church"""
    return get_user_church(current_user["id"], db)

@mobile_router.delete("/church/user/me", response_model=SuccessResponse)
async def remove_user_church_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Remove user from church"""
    return remove_user_from_church(current_user["id"], db)

@mobile_router.post("/church/{church_id}/select", response_model=SuccessResponse)
async def select_church_route(
    church_id: int,
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Select church for user"""
    return select_church_for_user(current_user["id"], church_id, db)

@mobile_router.get("/refresh-user-data", response_model=SuccessResponse)
async def refresh_user_data_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Refresh all user data after church selection for mobile app caching"""
    return refresh_user_data_after_church_selection(current_user["id"], db)

@mobile_router.get("/auth/me/refresh", response_model=SuccessResponse)
async def force_refresh_profile_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Force refresh user profile (bypass any caching) - use after church selection"""
    return get_mobile_profile(current_user["id"], db)

@mobile_router.get("/church-status", response_model=SuccessResponse)
async def get_church_status_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get current user church status for debugging"""
    return get_user_church_status(current_user["id"], db)

# Roundup Settings Endpoints
@mobile_router.get("/roundup-settings", response_model=SuccessResponse)
async def get_roundup_settings_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get roundup settings"""
    return get_mobile_roundup_settings(current_user["id"], db)

@mobile_router.put("/roundup-settings", response_model=SuccessResponse)
async def update_roundup_settings_route(
    settings_data: dict,
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Update roundup settings"""
    return update_mobile_roundup_settings(current_user["id"], settings_data, db)

@mobile_router.post("/quick-toggle", response_model=SuccessResponse)
async def quick_toggle_roundups_route(
    pause: bool = Query(..., description="Pause roundups"),
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Quick toggle roundups"""
    return quick_toggle_roundups(current_user["id"], pause, db)

# Impact Summary Endpoints
@mobile_router.get("/impact-summary", response_model=SuccessResponse)
async def get_impact_summary_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get impact summary"""
    return get_mobile_impact_summary(current_user["id"], db)

# Analytics Endpoints
@mobile_router.get("/analytics/user", response_model=SuccessResponse)
async def get_user_analytics_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get user analytics data"""
    from app.controller.mobile.analytics import get_mobile_user_analytics
    return get_mobile_user_analytics(current_user["id"], db)

# Dashboard Endpoints
@mobile_router.get("/dashboard", response_model=SuccessResponse)
async def get_dashboard_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get dashboard data"""
    return get_mobile_dashboard(current_user["id"], db)

# Profile Endpoints
@mobile_router.get("/profile", response_model=SuccessResponse)
async def get_profile_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get user profile"""
    return get_mobile_profile(current_user["id"], db)

@mobile_router.put("/profile", response_model=SuccessResponse)
async def update_profile_route(
    profile_data: dict,
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Update user profile"""
    return update_mobile_profile(current_user["id"], profile_data, db)

@mobile_router.post("/profile/image", response_model=SuccessResponse)
async def upload_profile_image_route(
    image_file: UploadFile,
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Upload profile image"""
    return upload_mobile_profile_image(current_user["id"], image_file, db)

@mobile_router.delete("/profile/image", response_model=SuccessResponse)
async def remove_profile_image_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Remove profile image"""
    return remove_mobile_profile_image(current_user["id"], db)

@mobile_router.post("/profile/verify-email/send", response_model=SuccessResponse)
async def send_email_verification_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Send email verification"""
    return send_email_verification(current_user["id"], db)

@mobile_router.post("/profile/verify-email/confirm", response_model=SuccessResponse)
async def confirm_email_verification_route(
    verification_data: dict,
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Confirm email verification"""
    return confirm_email_verification(
        current_user["id"], 
        verification_data.get("access_code"), 
        verification_data.get("email"), 
        db
    )

@mobile_router.post("/profile/verify-phone/send", response_model=SuccessResponse)
async def send_phone_verification_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Send phone verification"""
    return send_phone_verification(current_user["id"], db)

@mobile_router.post("/profile/verify-phone/confirm", response_model=SuccessResponse)
async def confirm_phone_verification_route(
    verification_data: dict,
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Confirm phone verification"""
    return confirm_phone_verification(
        current_user["id"], 
        verification_data.get("access_code"), 
        verification_data.get("phone"), 
        db
    )

# Notification Endpoints
@mobile_router.get("/donor/notifications", response_model=SuccessResponse)
async def get_notifications_route(
    limit: int = Query(default=50, description="Number of notifications to return"),
    offset: int = Query(default=0, description="Number of notifications to skip"),
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get notifications"""
    return get_mobile_notifications(current_user["id"], db, limit, offset)

@mobile_router.post("/donor/notifications/{notification_id}/read", response_model=SuccessResponse)
async def mark_notification_read_route(
    notification_id: int,
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Mark notification as read"""
    return mark_notification_read(current_user["id"], notification_id, db)

@mobile_router.post("/donor/notifications/read-all", response_model=SuccessResponse)
async def mark_all_notifications_read_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Mark all notifications as read"""
    return mark_all_notifications_read(current_user["id"], db)

@mobile_router.delete("/donor/notifications/{notification_id}", response_model=SuccessResponse)
async def delete_notification_route(
    notification_id: int,
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Delete notification"""
    return delete_notification(current_user["id"], notification_id, db)

@mobile_router.get("/donor/notification-preferences", response_model=SuccessResponse)
async def get_notification_preferences_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get notification preferences"""
    return get_notification_preferences(current_user["id"], db)

@mobile_router.post("/donor/notification-preferences", response_model=SuccessResponse)
async def update_notification_preferences_route(
    preferences_data: dict,
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Update notification preferences"""
    return update_notification_preferences(current_user["id"], preferences_data, db)

# Identity Verification Endpoints
@mobile_router.post("/identity/verification-session", response_model=SuccessResponse)
async def create_verification_session_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Create a Stripe Identity verification session for the current user"""
    return create_verification_session(current_user["id"], db)

@mobile_router.get("/identity/verification-status", response_model=SuccessResponse)
async def get_verification_status_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Check the verification status of the current user's Stripe Identity session"""
    return check_verification_status(current_user["id"], db)

@mobile_router.post("/identity/verification-session/cancel", response_model=SuccessResponse)
async def cancel_verification_session_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Cancel the current user's verification session"""
    return cancel_verification_session(current_user["id"], db)

@mobile_router.get("/identity/verification-summary", response_model=SuccessResponse)
async def get_verification_summary_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get a summary of the current user's verification status"""
    return get_verification_summary(current_user["id"], db)
