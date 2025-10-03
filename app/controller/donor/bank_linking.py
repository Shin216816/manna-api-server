"""
Bank Linking Controller

Handles Plaid integration for secure bank account connection:
- Create Plaid link tokens
- Exchange public tokens for access tokens
- Retrieve account information
- Handle bank account verification
"""

import logging
import plaid
from plaid.api import plaid_api
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.accounts_get_request import AccountsGetRequest
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.transactions_get_request_options import TransactionsGetRequestOptions
from plaid.model.country_code import CountryCode
from plaid.model.products import Products
# from plaid.model.link_token_create_request_webhook import LinkTokenCreateRequestWebhook  # This import doesn't exist
# from plaid.model.transactions_get_request_options_account_ids import TransactionsGetRequestOptionsAccountIds
# from plaid.model.transactions_get_request_options_date_range import TransactionsGetRequestOptionsDateRange
# from plaid.model.transactions_get_request_options_date_range_start_date import TransactionsGetRequestOptionsDateRangeStartDate
# from plaid.model.transactions_get_request_options_date_range_end_date import TransactionsGetRequestOptionsDateRangeEndDate
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.model.m_user import User
from app.model.m_plaid_items import PlaidItem
# PlaidAccount import removed - using on-demand Plaid API fetching
# PlaidTransaction import removed - using on-demand Plaid API fetching
from app.core.responses import ResponseFactory
from app.core.exceptions import UserNotFoundError, ValidationError
from app.utils.error_handler import handle_controller_errors
from app.config import config as settings
from fastapi import HTTPException

# Initialize Plaid client
plaid_client = plaid.ApiClient(plaid.Configuration(
    host=plaid.Environment.Sandbox,  # Change to production in production
    api_key={
        'clientId': settings.PLAID_CLIENT_ID,
        'secret': settings.PLAID_SECRET
    }
))
plaid_api_instance = plaid_api.PlaidApi(plaid_client)


@handle_controller_errors
def create_link_token(user_id: int, db: Session) -> ResponseFactory:
    """Create a Plaid link token for bank account connection with enhanced error handling"""
    try:
        # Verify user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise UserNotFoundError("User not found")

        # Check if user already has active bank accounts
        existing_items = db.query(PlaidItem).filter(
            PlaidItem.user_id == user_id,
            PlaidItem.status == "active"
        ).count()

        # Create link token request with enhanced configuration
        request = LinkTokenCreateRequest(
            products=[Products('transactions')],
            client_name="Manna - Micro-Donation Platform",
            country_codes=[CountryCode('US')],
            language='en',
            # webhook=LinkTokenCreateRequestWebhook(
            #     url=f"{settings.BASE_URL}/webhooks/plaid"
            # ),  # Webhook configuration removed due to import issues
            user=LinkTokenCreateRequestUser(
                client_user_id=str(user_id)
            ),
            # Add additional configuration for better UX
            redirect_uri=f"{settings.FRONTEND_URL}/donor/bank-linking/success",
            update_mode="update" if existing_items > 0 else "create"
        )

        # Create link token
        response = plaid_api_instance.link_token_create(request)
        
        return ResponseFactory.success(
            message="Link token created successfully",
            data={
                "link_token": response['link_token'],
                "expiration": response['expiration'],
                "request_id": response['request_id'],
                "has_existing_accounts": existing_items > 0,
                "expires_in": 1800  # 30 minutes
            }
        )

    except plaid.ApiException as e:
        logging.error(f"Plaid API error creating link token: {e}")
        error_detail = "Failed to create link token"
        if hasattr(e, 'body') and e.body:
            try:
                import json
                error_body = json.loads(e.body)
                error_detail = error_body.get('error_message', error_detail)
            except:
                error_detail = str(e.body)
        
        raise HTTPException(status_code=400, detail=error_detail)
    except Exception as e:
        logging.error(f"Error creating link token: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create link token")


@handle_controller_errors
def exchange_public_token(
    user_id: int, 
    public_token: str, 
    db: Session
) -> ResponseFactory:
    """Exchange public token for access token and store item with enhanced validation"""
    try:
        # Verify user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise UserNotFoundError("User not found")

        # Validate public token
        if not public_token or len(public_token.strip()) == 0:
            raise ValidationError("Public token is required")

        # Exchange public token for access token
        request = ItemPublicTokenExchangeRequest(
            public_token=public_token
        )
        
        response = plaid_api_instance.item_public_token_exchange(request)
        access_token = response['access_token']
        item_id = response['item_id']

        # Check if item already exists
        existing_item = db.query(PlaidItem).filter(
            PlaidItem.item_id == item_id
        ).first()

        if existing_item:
            # Update existing item
            existing_item.access_token = access_token
            existing_item.status = "active"
            existing_item.updated_at = datetime.now(timezone.utc)
            plaid_item = existing_item
        else:
            # Create new Plaid item
            plaid_item = PlaidItem(
                user_id=user_id,
                item_id=item_id,
                access_token=access_token,
                institution_id=response.get('institution_id'),
                status="active",
                created_at=datetime.now(timezone.utc)
            )
            db.add(plaid_item)
        
        db.commit()
        db.refresh(plaid_item)

        # Validate account access
        try:
            validate_accounts_access(user_id, access_token, db)
        except Exception as e:
            logging.error(f"Error validating account access after token exchange: {str(e)}")
            # Don't fail the entire operation if account validation fails

        return ResponseFactory.success(
            message="Bank account linked successfully",
            data={
                "item_id": item_id,
                "institution_id": response.get('institution_id'),
                "linked_at": plaid_item.created_at.isoformat(),
                "is_update": existing_item is not None
            }
        )

    except plaid.ApiException as e:
        logging.error(f"Plaid API error exchanging token: {e}")
        error_detail = "Failed to link bank account"
        if hasattr(e, 'body') and e.body:
            try:
                import json
                error_body = json.loads(e.body)
                error_detail = error_body.get('error_message', error_detail)
            except:
                error_detail = str(e.body)
        
        raise HTTPException(status_code=400, detail=error_detail)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(f"Error exchanging public token: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to link bank account")


@handle_controller_errors
def validate_accounts_access(
    user_id: int, 
    access_token: str, 
    db: Session
) -> None:
    """Validate that accounts can be accessed from Plaid API"""
    try:
        # Test account access
        request = AccountsGetRequest(access_token=access_token)
        response = plaid_api_instance.accounts_get(request)
        
        accounts = response['accounts']
        logging.info(f"Successfully validated access to {len(accounts)} accounts for user {user_id}")

    except plaid.ApiException as e:
        logging.error(f"Plaid API error validating accounts: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to validate account access: {e.body}")
    except Exception as e:
        logging.error(f"Error validating account access: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to validate account access")


@handle_controller_errors
def get_linked_accounts(user_id: int, db: Session) -> ResponseFactory:
    """Get all linked bank accounts for the user from Plaid API"""
    try:
        from app.services.plaid_account_service import plaid_account_service
        
        # Get accounts from Plaid API
        result = plaid_account_service.get_user_accounts(user_id, db)
        
        if not result["success"]:
            return ResponseFactory.success(
                message="No linked accounts found",
                data={
                    "accounts": [],
                    "total_accounts": 0
                }
            )

        # Format accounts for response
        all_accounts = []
        for account in result["accounts"]:
            all_accounts.append({
                "id": account["account_id"],  # Use account_id as ID since we don't have DB ID
                "account_id": account["account_id"],
                "name": account["name"],
                "official_name": account.get("official_name"),
                "type": account["type"],
                "subtype": account["subtype"],
                "mask": account["mask"],
                "available_balance": account.get("available_balance"),
                "current_balance": account.get("current_balance"),
                "currency": account.get("iso_currency_code", "USD"),
                "institution_name": account.get("institution_name", "Unknown Bank"),
                "linked_at": account.get("linked_at")
            })

        return ResponseFactory.success(
            message="Linked accounts retrieved successfully",
            data={
                "accounts": all_accounts,
                "total_accounts": len(all_accounts)
            }
        )

    except Exception as e:
        logging.error(f"Error getting linked accounts: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get linked accounts")


@handle_controller_errors
def unlink_account(user_id: int, account_id: str, db: Session) -> ResponseFactory:
    """Unlink a bank account by deactivating the Plaid item"""
    try:
        from app.services.plaid_account_service import plaid_account_service
        
        # First verify the account exists for this user
        account_result = plaid_account_service.get_account_by_id(user_id, account_id, db)
        
        if not account_result["success"]:
            raise ValidationError("Account not found")

        # Get the Plaid item that contains this account
        plaid_item = db.query(PlaidItem).filter(
            PlaidItem.user_id == user_id,
            PlaidItem.id == account_result["account"]["plaid_item_id"]
        ).first()

        if not plaid_item:
            raise ValidationError("Plaid item not found")

        # Deactivate the entire Plaid item (which contains all accounts)
        plaid_item.status = "inactive"
        plaid_item.updated_at = datetime.now(timezone.utc)

        db.commit()

        return ResponseFactory.success(
            message="Account unlinked successfully",
            data={
                "account_id": account_id,
                "unlinked_at": datetime.now(timezone.utc).isoformat()
            }
        )

    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(f"Error unlinking account: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to unlink account")


@handle_controller_errors
def validate_plaid_connection(user_id: int, db: Session) -> ResponseFactory:
    """Validate Plaid connection and return account status"""
    try:
        # Get active Plaid items
        plaid_items = db.query(PlaidItem).filter(
            PlaidItem.user_id == user_id,
            PlaidItem.status == "active"
        ).all()

        if not plaid_items:
            return ResponseFactory.success(
                message="No active bank accounts found",
                data={"active_accounts": 0}
            )

        active_accounts = 0
        account_details = []
        
        for item in plaid_items:
            try:
                # Test connection by getting account info
                request = AccountsGetRequest(access_token=item.access_token)
                response = plaid_api_instance.accounts_get(request)
                
                if response and 'accounts' in response:
                    active_accounts += len(response['accounts'])
                    account_details.append({
                        "item_id": item.item_id,
                        "institution_id": item.institution_id,
                        "accounts_count": len(response['accounts']),
                        "status": "active"
                    })
                    
            except Exception as e:
                logging.warning(f"Failed to validate connection for item {item.item_id}: {e}")
                account_details.append({
                    "item_id": item.item_id,
                    "institution_id": item.institution_id,
                    "accounts_count": 0,
                    "status": "error"
                })

        return ResponseFactory.success(
            message="Plaid connection validated",
            data={
                "active_accounts": active_accounts,
                "total_items": len(plaid_items),
                "validated_at": datetime.now(timezone.utc).isoformat(),
                "account_details": account_details
            }
        )

    except plaid.ApiException as e:
        logging.error(f"Plaid API error validating connection: {e}")
        error_detail = "Failed to validate Plaid connection"
        if hasattr(e, 'body') and e.body:
            try:
                import json
                error_body = json.loads(e.body)
                error_detail = error_body.get('error_message', error_detail)
            except:
                error_detail = str(e.body)
        
        raise HTTPException(status_code=400, detail=error_detail)
    except Exception as e:
        logging.error(f"Error validating Plaid connection: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to validate Plaid connection")


@handle_controller_errors
def get_recent_transactions(user_id: int, days: int = 30, db: Session = None) -> ResponseFactory:
    """Get recent transactions for the user with roundup calculations"""
    try:
        # Get user's linked accounts
        plaid_items = db.query(PlaidItem).filter(
            PlaidItem.user_id == user_id,
            PlaidItem.status == "active"
        ).all()

        if not plaid_items:
            return ResponseFactory.success(
                message="No linked accounts found",
                data={
                    "transactions": [],
                    "total_transactions": 0,
                    "total_roundup_amount": 0.0
                }
            )

        # Get transactions from the last N days
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        
        all_transactions = []
        total_roundup_amount = 0.0

        for item in plaid_items:
            try:
                request = TransactionsGetRequest(
                    access_token=item.access_token,
                    start_date=start_date.date(),
                    end_date=end_date.date(),
                    options=TransactionsGetRequestOptions(
                        count=500,
                        offset=0
                    )
                )
                
                response = plaid_api_instance.transactions_get(request)
                transactions = response['transactions']
                
                for transaction_data in transactions:
                    # Calculate roundup amount
                    amount = abs(float(transaction_data['amount']))
                    roundup_amount = 0.0
                    
                    if amount > 0:
                        # Calculate roundup (round up to next dollar)
                        rounded_amount = int(amount) + 1
                        roundup_amount = rounded_amount - amount
                        total_roundup_amount += roundup_amount
                    
                    all_transactions.append({
                        "id": transaction_data['transaction_id'],
                        "account_id": transaction_data['account_id'],
                        "amount": amount,
                        "roundup_amount": roundup_amount,
                        "date": transaction_data['date'],
                        "merchant_name": transaction_data.get('merchant_name'),
                        "description": transaction_data.get('name'),
                        "category": transaction_data.get('category', [None])[0] if transaction_data.get('category') else None,
                        "is_pending": transaction_data.get('pending', False),
                        "institution_id": item.institution_id
                    })
                    
            except plaid.ApiException as e:
                logging.error(f"Error getting transactions for item {item.item_id}: {e}")
                continue

        # Sort transactions by date (newest first)
        all_transactions.sort(key=lambda x: x['date'], reverse=True)

        return ResponseFactory.success(
            message="Recent transactions retrieved successfully",
            data={
                "transactions": all_transactions,
                "total_transactions": len(all_transactions),
                "total_roundup_amount": round(total_roundup_amount, 2),
                "date_range": {
                    "start_date": start_date.date().isoformat(),
                    "end_date": end_date.date().isoformat(),
                    "days": days
                }
            }
        )

    except Exception as e:
        logging.error(f"Error getting recent transactions: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get recent transactions")


@handle_controller_errors
def get_account_balance(user_id: int, account_id: str, db: Session) -> ResponseFactory:
    """Get current balance for a specific account from Plaid API"""
    try:
        from app.services.plaid_account_service import plaid_account_service
        
        # Get account from Plaid API
        account_result = plaid_account_service.get_account_by_id(user_id, account_id, db)
        
        if not account_result["success"]:
            raise ValidationError("Account not found")

        account_data = account_result["account"]

        return ResponseFactory.success(
            message="Account balance retrieved successfully",
            data={
                "account_id": account_id,
                "account_name": account_data["name"],
                "available_balance": account_data.get("available_balance", 0.0),
                "current_balance": account_data.get("current_balance", 0.0),
                "currency": account_data.get("iso_currency_code", "USD"),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        )

    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except plaid.ApiException as e:
        logging.error(f"Plaid API error getting account balance: {e}")
        raise HTTPException(status_code=400, detail="Failed to get account balance")
    except Exception as e:
        logging.error(f"Error getting account balance: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get account balance")
