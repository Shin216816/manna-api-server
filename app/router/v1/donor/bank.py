from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.utils.database import get_db
from app.middleware.auth_middleware import jwt_auth
from app.controller.donor.bank import (
    create_link_token, exchange_public_token, get_linked_accounts,
    unlink_account, sync_accounts, get_account_balance, get_transactions
)
from app.schema.donor_schema import (
    DonorLinkTokenRequest, DonorPublicTokenRequest
)

router = APIRouter()

@router.post("/link-token")
def donor_create_link_token(data: DonorLinkTokenRequest, current_user: dict = Depends(jwt_auth), db: Session = Depends(get_db)):
    """Create Plaid link token for donor"""
    return create_link_token(data, current_user, db)

@router.post("/exchange-token")
def donor_exchange_public_token(data: DonorPublicTokenRequest, current_user: dict = Depends(jwt_auth), db: Session = Depends(get_db)):
    """Exchange public token for access token"""
    return exchange_public_token(data, current_user, db)

@router.get("/accounts")
def donor_get_linked_accounts(current_user: dict = Depends(jwt_auth), db: Session = Depends(get_db)):
    """Get donor linked bank accounts"""
    return get_linked_accounts(current_user, db)



@router.delete("/accounts/{account_id}")
def donor_unlink_account(account_id: str, current_user: dict = Depends(jwt_auth), db: Session = Depends(get_db)):
    """Unlink donor bank account"""
    return unlink_account(account_id, current_user, db)

@router.post("/sync")
def donor_sync_accounts(current_user: dict = Depends(jwt_auth), db: Session = Depends(get_db)):
    """Sync donor bank accounts"""
    return sync_accounts(current_user, db)

@router.get("/balance/{account_id}")
def donor_get_account_balance(account_id: str, current_user: dict = Depends(jwt_auth), db: Session = Depends(get_db)):
    """Get donor account balance"""
    return get_account_balance(account_id, current_user, db)

@router.post("/transactions")
def donor_get_transactions(data: dict, current_user: dict = Depends(jwt_auth), db: Session = Depends(get_db)):
    """Get donor bank transactions"""
    return get_transactions(data, current_user, db)
