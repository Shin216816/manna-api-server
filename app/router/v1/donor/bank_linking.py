"""
Bank Linking Router

Handles bank account linking endpoints using Plaid integration.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.controller.donor.bank_linking import (
    create_link_token,
    exchange_public_token,
    get_linked_accounts,
    unlink_account,
    validate_plaid_connection
)
from app.core.responses import ResponseFactory
from app.middleware.auth_middleware import get_current_user
from app.utils.database import get_db

# Important: Do not set a prefix here; aggregator mounts at /donor/bank-linking
router = APIRouter(tags=["Bank Linking"])


@router.post("/link-token", response_model=None)
async def create_bank_link_token(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a Plaid link token for bank account connection
    """
    user_id = current_user["id"]
    return create_link_token(user_id, db)


@router.post("/exchange-token", response_model=None)
async def exchange_bank_token(
    public_token: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Exchange public token for access token and link bank account
    """
    user_id = current_user["id"]
    return exchange_public_token(user_id, public_token, db)


@router.get("/accounts", response_model=None)
async def get_bank_accounts(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all linked bank accounts for the current user
    """
    user_id = current_user["id"]
    return get_linked_accounts(user_id, db)


@router.delete("/accounts/{account_id}", response_model=None)
async def unlink_bank_account(
    account_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Unlink a specific bank account
    """
    user_id = current_user["id"]
    return unlink_account(user_id, account_id, db)


@router.post("/sync-transactions", response_model=None)
async def sync_bank_transactions(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Validate Plaid connection and return account status
    """
    user_id = current_user["id"]
    return validate_plaid_connection(user_id, db)
