from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.controller.mobile.bank import (
    create_mobile_link_token, exchange_mobile_public_token, get_mobile_transactions,
    get_mobile_bank_accounts, get_mobile_donation_history, get_mobile_donation_summary,
    get_mobile_impact_analytics, list_mobile_payment_methods, delete_mobile_payment_method,
    save_mobile_payment_method
)
from app.schema.bank_schema import (
    CreateLinkTokenRequest, ExchangePublicTokenRequest, GetTransactionsRequest,
    PaymentMethodRequest
)
from app.utils.database import get_db
from app.middleware.auth_middleware import jwt_auth
from app.core.responses import SuccessResponse

bank_router = APIRouter(tags=["Mobile Banking"])

@bank_router.post("/link-token", response_model=SuccessResponse)
async def create_link_token_route(
    data: CreateLinkTokenRequest,
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Create Plaid link token for mobile"""
    return create_mobile_link_token(data, current_user, db)

@bank_router.post("/exchange-token", response_model=SuccessResponse)
async def exchange_public_token_route(
    data: ExchangePublicTokenRequest,
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Exchange public token for access token"""
    return exchange_mobile_public_token(data, current_user, db)

@bank_router.post("/transactions", response_model=SuccessResponse)
async def get_transactions_route(
    data: GetTransactionsRequest,
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get user transactions from linked accounts"""
    return get_mobile_transactions(data, current_user, db)

@bank_router.get("/accounts", response_model=SuccessResponse)
async def get_bank_accounts_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get user's linked bank accounts"""
    return get_mobile_bank_accounts(current_user, db)

@bank_router.get("/donations/history", response_model=SuccessResponse)
async def get_donation_history_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get user's donation history"""
    return get_mobile_donation_history(current_user, db)

@bank_router.get("/donations/summary", response_model=SuccessResponse)
async def get_donation_summary_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get user's donation summary"""
    return get_mobile_donation_summary(current_user, db)

@bank_router.get("/donations/impact", response_model=SuccessResponse)
async def get_impact_analytics_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Get user's impact analytics"""
    return get_mobile_impact_analytics(current_user, db)

@bank_router.get("/payment-methods", response_model=SuccessResponse)
async def list_payment_methods_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """List user's saved payment methods"""
    return list_mobile_payment_methods(current_user, db)

@bank_router.delete("/payment-methods/{payment_method_id}", response_model=SuccessResponse)
async def delete_payment_method_route(
    payment_method_id: str,
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Delete a payment method"""
    return delete_mobile_payment_method(payment_method_id, current_user, db)

@bank_router.post("/payment-methods", response_model=SuccessResponse)
async def save_payment_method_route(
    data: PaymentMethodRequest,
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """Save a payment method"""
    return save_mobile_payment_method(current_user["id"], data.payment_method_id, current_user, db)
