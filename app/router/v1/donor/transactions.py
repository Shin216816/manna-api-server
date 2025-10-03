from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.controller.donor.transactions import (
    get_donor_transactions,
    get_transaction_details,
    calculate_roundup_for_transaction,
    sync_transactions
)
from app.utils.database import get_db
from app.middleware.auth_middleware import jwt_auth
from app.core.responses import SuccessResponse

router = APIRouter(tags=["Donor"])

@router.get("/", response_model=SuccessResponse)
def get_transactions_route(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    start_date: str = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(None, description="End date (YYYY-MM-DD)"),
    category: str = Query(None, description="Transaction category filter"),
    search: str = Query(None, description="Search term for transactions"),
    status: str = Query(None, description="Transaction status filter"),
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """
    Get donor transactions
    
    Retrieves donor's bank transactions (Plaid) and payment transactions (Stripe) 
    with roundup calculations. Supports pagination, date filtering, and search.
    """
    # Extract user_id from JWT auth
    user_id = current_user.get('user_id') or current_user.get('id')
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID not found in token")
    
    return get_donor_transactions(
        user_id, 
        page, 
        limit, 
        start_date, 
        end_date, 
        category,
        search,
        status,
        db
    )

@router.get("/{transaction_id}", response_model=SuccessResponse)
def get_transaction_details_route(
    transaction_id: str,
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """
    Get transaction details
    
    Retrieves detailed information about a specific transaction
    including roundup calculations and metadata.
    """
    # Extract user_id from JWT auth
    user_id = current_user.get('user_id') or current_user.get('id')
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID not found in token")
    
    return get_transaction_details(transaction_id, user_id, db)

@router.post("/{transaction_id}/calculate-roundup", response_model=SuccessResponse)
def calculate_roundup_route(
    transaction_id: str,
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """
    Calculate roundup amount
    
    Calculates the roundup amount for a specific transaction
    based on current donor settings and preferences.
    """
    # Extract user_id from JWT auth
    user_id = current_user.get('user_id') or current_user.get('id')
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID not found in token")
    
    return calculate_roundup_for_transaction(transaction_id, user_id, db)

@router.post("/sync", response_model=SuccessResponse)
def sync_transactions_route(
    current_user: dict = Depends(jwt_auth),
    db: Session = Depends(get_db)
):
    """
    Sync transactions
    
    Synchronizes bank transactions from Plaid for the current user.
    This updates the transaction database with the latest data.
    """
    # Extract user_id from JWT auth
    user_id = current_user.get('user_id') or current_user.get('id')
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID not found in token")
    
    return sync_transactions(user_id, db)