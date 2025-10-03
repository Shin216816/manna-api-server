import os
import time
import random
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from plaid.api import plaid_api
from plaid.configuration import Configuration
from plaid.api_client import ApiClient
from plaid.api.plaid_api import (
    ItemPublicTokenExchangeRequest,
    AccountsGetRequest,
    AccountsBalanceGetRequest,
    TransactionsGetRequest, 
    TransactionsSyncRequest,
    InstitutionsGetByIdRequest
)
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from plaid.exceptions import ApiException

from app.config import config
from app.core.constants import (
    PLAID_RATE_LIMIT_DELAY,
    PLAID_MAX_RETRIES,
    PLAID_BACKOFF_MULTIPLIER,
    PLAID_CACHE_TTL,
    PLAID_TIMEOUT,
    PLAID_CONNECT_TIMEOUT,
    PLAID_READ_TIMEOUT
)
import logging

# Set up logger for this module
logger = logging.getLogger(__name__)

# Log the PLAID_CLIENT_ID being used


# Environment mapping for SDK v9+
env_map = {
    "sandbox": "https://sandbox.plaid.com",
    "development": "https://development.plaid.com",
    "production": "https://production.plaid.com"
}
base_url = env_map.get(config.PLAID_ENV.lower(), "https://sandbox.plaid.com")

# Initialize configuration
configuration = Configuration(
    host=base_url,
    api_key={
        "clientId": config.PLAID_CLIENT_ID,
        "secret": config.PLAID_SECRET,
    }
)

# Create client
api_client = ApiClient(configuration)
plaid_client = plaid_api.PlaidApi(api_client)

# Rate limiting configuration
RATE_LIMIT_DELAY = PLAID_RATE_LIMIT_DELAY
MAX_RETRIES = PLAID_MAX_RETRIES
BACKOFF_MULTIPLIER = PLAID_BACKOFF_MULTIPLIER

# Simple cache for transactions (in production, use Redis)
_transaction_cache = {}
CACHE_TTL = PLAID_CACHE_TTL  # 5 minutes cache TTL

def _get_cache_key(access_token: str, days_back: int) -> str:
    """Generate cache key for transactions"""
    return f"transactions:{access_token}:{days_back}"

def _is_cache_valid(cache_entry: dict) -> bool:
    """Check if cache entry is still valid"""
    if not cache_entry:
        return False
    return time.time() - cache_entry.get('timestamp', 0) < CACHE_TTL

class TimeoutError(Exception):
    """Custom timeout exception"""
    pass

def _execute_with_timeout(func, timeout_seconds=PLAID_TIMEOUT, *args, **kwargs):
    """Execute function with timeout using threading"""
    result: List[Any] = [None]
    exception: List[Any] = [None]
    
    def target():
        try:
            result[0] = func(*args, **kwargs)
        except Exception as e:
            exception[0] = e
    
    thread = threading.Thread(target=target)
    thread.daemon = True
    thread.start()
    thread.join(timeout_seconds)
    
    if thread.is_alive():
        
        raise TimeoutError(f"Request timed out after {timeout_seconds} seconds")
    
    if exception[0]:
        raise exception[0]
    
    return result[0]

def _handle_plaid_rate_limit(max_retries: int = MAX_RETRIES) -> Callable:
    """Decorator to handle Plaid rate limiting with exponential backoff and timeout"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    # Add jitter to prevent thundering herd
                    jitter = random.uniform(0, 0.1)
                    time.sleep(RATE_LIMIT_DELAY + jitter)
                    
                    # Execute with timeout
                    return _execute_with_timeout(func, PLAID_TIMEOUT, *args, **kwargs)
                    
                except ApiException as e:
                    last_exception = e
                    
                    # Check if it's a rate limit error
                    if hasattr(e, 'status') and e.status == 429:
                        
                        
                        if attempt < max_retries - 1:
                            # Exponential backoff with jitter
                            delay = RATE_LIMIT_DELAY * (BACKOFF_MULTIPLIER ** attempt)
                            jitter = random.uniform(0, delay * 0.1)
                            time.sleep(delay + jitter)
                            continue
                    
                    # Re-raise non-rate-limit errors immediately
                    raise e
                    
                except TimeoutError as e:
                    last_exception = e
                    
                    if attempt < max_retries - 1:
                        # Wait before retry
                        time.sleep(2 ** attempt)
                        continue
                    raise e
                    
                except Exception as e:
                    last_exception = e
                    
                    raise e
            
            # If we've exhausted all retries, raise the last exception
            if last_exception:
                raise last_exception
                
        return wrapper
    return decorator

def create_link_token(user_id: str, client_name: str, country_codes: list, language: str, products: list) -> dict:
    """Create a Plaid link token"""
    try:
        user = LinkTokenCreateRequestUser(client_user_id=user_id)
        
        request = LinkTokenCreateRequest(
            user=user,
            client_name=client_name,
            country_codes=country_codes,
            language=language,
            products=products
        )
        
        response = plaid_client.link_token_create(request)
        return {
            "link_token": response.link_token,
            "expiration": response.expiration.isoformat(),
            "request_id": response.request_id
        }
    except ApiException as e:
        
        raise Exception(f"Failed to create link token: {e.body}")

def exchange_public_token(public_token: str) -> dict:
    """Exchange public token for access token"""
    try:
        request = ItemPublicTokenExchangeRequest(public_token=public_token)
        response = plaid_client.item_public_token_exchange(request)
        
        return {
            "access_token": response.access_token,
            "item_id": response.item_id
        }
    except ApiException as e:
        
        raise Exception(f"Failed to exchange public token: {e.body}")

def get_accounts(access_token: str) -> dict:
    """Get accounts for a Plaid item"""
    try:
        request = AccountsGetRequest(access_token=access_token)
        response = plaid_client.accounts_get(request)
        
        accounts = []
        for account in response.accounts:
            accounts.append({
                "account_id": account.account_id,
                "name": account.name,
                "official_name": getattr(account, 'official_name', None),
                "type": account.type,
                "subtype": account.subtype,
                "mask": account.mask,
                "available_balance": float(account.balances.available) if account.balances.available is not None else None,
                "current_balance": float(account.balances.current) if account.balances.current is not None else None,
                "iso_currency_code": account.balances.iso_currency_code or "USD",
                "status": "active",  # Plaid API only returns active accounts
                "balances": {
                    "available": account.balances.available,
                    "current": account.balances.current,
                    "limit": account.balances.limit
                }
            })
        
        # Get institution information
        institution_name = "Unknown Bank"
        try:
            institution_request = InstitutionsGetByIdRequest(
                institution_id=response.item.institution_id,
                country_codes=[CountryCode("US")]
            )
            institution_response = plaid_client.institutions_get_by_id(institution_request)
            institution_name = institution_response.institution.name
        except Exception as e:
            logging.warning(f"Could not fetch institution name: {str(e)}")
        
        return {
            "accounts": accounts,
            "item": {
                "item_id": response.item.item_id,
                "institution_id": response.item.institution_id
            },
            "institution": {
                "institution_id": response.item.institution_id,
                "name": institution_name
            }
        }
    except ApiException as e:
        raise Exception(f"Failed to get accounts: {e.body}")

def get_transactions_by_date(access_token: str, start_date: str, end_date: str) -> dict:
    """Get transactions for a Plaid item"""
    try:
        request = TransactionsGetRequest(
            access_token=access_token,
            start_date=start_date,
            end_date=end_date
        )
        
        response = plaid_client.transactions_get(request)
        
        transactions = []
        for transaction in response.transactions:
            transactions.append({
                "transaction_id": transaction.transaction_id,
                "account_id": transaction.account_id,
                "amount": transaction.amount,
                "date": transaction.date,
                "name": transaction.name,
                "merchant_name": transaction.merchant_name,
                "category": transaction.category,
                "category_id": transaction.category_id,
                "pending": transaction.pending
            })
        
        return {
            "transactions": transactions,
            "accounts": [
                {
                    "account_id": account.account_id,
                    "name": account.name,
                    "type": account.type,
                    "subtype": account.subtype,
                    "mask": account.mask
                }
                for account in response.accounts
            ],
            "total_transactions": response.total_transactions
        }
    except ApiException as e:
        
        raise Exception(f"Failed to get transactions: {e.body}")

# Get balances with timeout handling
@_handle_plaid_rate_limit()
def get_balances(access_token: str):
    try:
        request = AccountsBalanceGetRequest(access_token=access_token)
        response = plaid_client.accounts_balance_get(request)
        return response
    except Exception as e:
        raise e

# Get transactions using the recommended /transactions/sync endpoint
@_handle_plaid_rate_limit()
def get_transactions_sync(access_token: str, cursor: str = None, count: int = 100):
    """
    Get transactions using the recommended /transactions/sync endpoint
    
    Args:
        access_token: Plaid access token
        cursor: Cursor for pagination (None for initial request)
        count: Number of transactions to fetch (1-500)
    
    Returns:
        Dict with transactions, next_cursor, and has_more flag
    """
    try:
        # Create sync request - in Plaid SDK 9.0.0, options are passed directly
        # Handle None cursor by omitting it from the request
        request_kwargs = {
            'access_token': access_token,
            'count': count
        }
        
        # Only add cursor if it's not None
        if cursor is not None:
            request_kwargs['cursor'] = cursor
            
        request = TransactionsSyncRequest(**request_kwargs)
        
        response = plaid_client.transactions_sync(request)
        
        # Debug logging for transaction types
        logging.info(f"Plaid sync response - Added: {len(response.added)}, Modified: {len(response.modified)}, Removed: {len(response.removed)}")
        
        # Convert response to dict format
        transactions = []
        for transaction in response.added:
            transactions.append({
                "transaction_id": transaction.transaction_id,
                "account_id": transaction.account_id,
                "amount": transaction.amount,
                "date": transaction.date.isoformat() if hasattr(transaction.date, 'isoformat') else str(transaction.date),
                "name": transaction.name,
                "merchant_name": transaction.merchant_name,
                "category": transaction.category,
                "category_id": transaction.category_id,
                "pending": transaction.pending,
                "iso_currency_code": transaction.iso_currency_code,
                "unofficial_currency_code": transaction.unofficial_currency_code,
                "location": {
                    "address": transaction.location.address if transaction.location else None,
                    "city": transaction.location.city if transaction.location else None,
                    "region": transaction.location.region if transaction.location else None,
                    "postal_code": transaction.location.postal_code if transaction.location else None,
                    "country": transaction.location.country if transaction.location else None,
                    "lat": transaction.location.lat if transaction.location else None,
                    "lon": transaction.location.lon if transaction.location else None,
                } if transaction.location else None,
                "payment_meta": {
                    "reference_number": transaction.payment_meta.reference_number if transaction.payment_meta else None,
                    "ppd_id": transaction.payment_meta.ppd_id if transaction.payment_meta else None,
                    "payment_method": transaction.payment_meta.payment_method if transaction.payment_meta else None,
                    "payment_processor": transaction.payment_meta.payment_processor if transaction.payment_meta else None,
                } if transaction.payment_meta else None,
            })
        
        return {
            "transactions": transactions,
            "next_cursor": response.next_cursor,
            "has_more": response.has_more,
            "request_id": response.request_id
        }
        
    except Exception as e:
        raise e

# Legacy function for backward compatibility - now uses sync endpoint
@_handle_plaid_rate_limit()
def get_transactions(access_token: str, days_back: int = 30):
    """
    Legacy function that uses /transactions/sync for backward compatibility
    This function fetches all transactions from the last N days
    """
    try:
        # Check cache first
        cache_key = _get_cache_key(access_token, days_back)
        cached_data = _transaction_cache.get(cache_key)
        
        if cached_data and _is_cache_valid(cached_data):
            return cached_data['data']
        
        # Fetch all transactions using sync endpoint
        all_transactions = []
        cursor = None
        has_more = True
        
        while has_more:
            sync_response = get_transactions_sync(access_token, cursor=cursor, count=500)
            all_transactions.extend(sync_response['transactions'])
            cursor = sync_response['next_cursor']
            has_more = sync_response['has_more']
        
        # Return all transactions without date filtering for now
        # This ensures we get all available transactions from Plaid
        filtered_transactions = all_transactions
        
        # Cache the response
        _transaction_cache[cache_key] = {
            'data': {
                'transactions': filtered_transactions,
                'total_transactions': len(filtered_transactions)
            },
            'timestamp': time.time()
        }
        
        return {
            'transactions': filtered_transactions,
            'total_transactions': len(filtered_transactions)
        }
        
    except Exception as e:
        raise e

# Get transactions with options and timeout handling
@_handle_plaid_rate_limit()
def get_transactions_with_options(access_token: str, days_back: int = 30, options: Optional[dict] = None):
    try:
        today = datetime.today().date()
        start_date = today - timedelta(days=days_back)
        
        # In Plaid SDK 9.0.0, options are passed directly to the request
        request_kwargs = {
            'access_token': access_token,
            'start_date': start_date,
            'end_date': today
        }
        
        if options:
            if 'include_personal_finance_category' in options:
                request_kwargs['include_personal_finance_category'] = options['include_personal_finance_category']
            if 'include_original_description' in options:
                request_kwargs['include_original_description'] = options['include_original_description']
        
        request = TransactionsGetRequest(**request_kwargs)
        response = plaid_client.transactions_get(request)
        return response
    except Exception as e:
        raise e

# Get institution by ID with timeout handling
@_handle_plaid_rate_limit()
def get_institution_by_id(institution_id: str, options: Optional[dict] = None):
    try:
        # In Plaid SDK 9.0.0, options are passed directly to the request
        request_kwargs = {
            'institution_id': institution_id,
            'country_codes': ['US']
        }
        
        if options:
            if 'include_optional_metadata' in options:
                request_kwargs['include_optional_metadata'] = options['include_optional_metadata']
        
        request = InstitutionsGetByIdRequest(**request_kwargs)
        response = plaid_client.institutions_get_by_id(request)
        return {
            "institution": {
                "institution_id": response.institution.institution_id,
                "name": response.institution.name,
                "type": response.institution.type,
                "country_codes": response.institution.country_codes
            }
        }
    except Exception as e:
        raise e

def get_plaid_client():
    return plaid_client
