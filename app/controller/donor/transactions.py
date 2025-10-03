import logging
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from sqlalchemy import desc, and_, or_
from typing import Optional

# Set up logger for this module
logger = logging.getLogger(__name__)

# PlaidTransaction import removed - using on-demand Plaid API fetching
# RoundupTransaction removed - using DonationBatch data instead
from app.model.m_donation_preference import DonationPreference
from app.model.m_plaid_items import PlaidItem
from app.model.m_user import User
from app.core.responses import ResponseFactory
from app.core.exceptions import UserNotFoundError, ValidationError
from app.utils.error_handler import handle_controller_errors
from app.services.plaid_client import get_transactions, get_transactions_sync
from app.services.stripe_service import get_customer_transactions
from fastapi import HTTPException

@handle_controller_errors
def get_donor_transactions(
    user_id: int,
    page: int = 1,
    limit: int = 20,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = None
):
    """Get donor transactions combining Plaid and Stripe transactions"""
    
    logger.info(f"Starting transaction fetch for user {user_id} with filters: page={page}, limit={limit}, start_date={start_date}, end_date={end_date}, category={category}, search={search}, status={status}")
    
    # Get user to check for Stripe customer ID
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        logger.warning(f"User {user_id} not found")
        raise HTTPException(status_code=404, detail="User not found")
    
    all_transactions = []
    
    # 1. Get Plaid transactions on-demand using sync endpoint
    plaid_items = db.query(PlaidItem).filter(
        PlaidItem.user_id == user_id,
        PlaidItem.status == "active"
    ).all()
    
    for item in plaid_items:
        try:
            # Fetch transactions using the new sync endpoint
            transactions_data = get_transactions(
                access_token=item.access_token,
                days_back=30  # Fetch last 30 days by default
            )
            
            if transactions_data and 'transactions' in transactions_data:
                for transaction in transactions_data['transactions']:
                    # Parse date safely - handle both ISO format and simple date strings
                    try:
                        if 'T' in transaction['date'] or 'Z' in transaction['date']:
                            # ISO format with timezone
                            transaction_date = datetime.fromisoformat(transaction['date'].replace('Z', '+00:00'))
                        else:
                            # Simple date format (YYYY-MM-DD)
                            transaction_date = datetime.fromisoformat(transaction['date']).replace(tzinfo=timezone.utc)
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Invalid date format for transaction {transaction.get('transaction_id', 'unknown')}: {transaction.get('date', 'unknown')}")
                        # Use current date as fallback instead of skipping
                        transaction_date = datetime.now(timezone.utc)
                    
                    # Apply date filters only if provided
                    if start_date:
                        try:
                            start_dt = datetime.fromisoformat(start_date).replace(tzinfo=timezone.utc)
                            if transaction_date < start_dt:
                                continue
                        except ValueError:
                            logger.warning(f"Invalid start_date format: {start_date}")
                    
                    if end_date:
                        try:
                            end_dt = datetime.fromisoformat(end_date).replace(tzinfo=timezone.utc)
                            if transaction_date > end_dt:
                                continue
                        except ValueError:
                            logger.warning(f"Invalid end_date format: {end_date}")
                    
                    # Apply category filter - handle None categories safely
                    transaction_category = transaction.get('category')
                    if category and transaction_category:
                        if not any(cat.lower() == category.lower() for cat in transaction_category):
                            continue
                    
                    # Convert to unified format with safe category handling
                    unified_transaction = {
                        "id": f"plaid_{transaction['transaction_id']}",
                        "type": "plaid",
                        "amount": float(transaction['amount']),
                        "date": transaction_date.isoformat(),  # Convert to ISO string
                        "merchant_name": transaction.get('merchant_name') or transaction.get('name') or "Unknown Merchant",
                        "category": transaction_category[0] if transaction_category and len(transaction_category) > 0 else "other",
                        "subcategory": transaction_category[1] if transaction_category and len(transaction_category) > 1 else None,
                        "description": transaction.get('name') or "Bank Transaction",
                        "status": "completed" if not transaction.get('pending', False) else "pending",
                        "account_id": transaction['account_id'],
                        "created_at": transaction_date.isoformat(),  # Convert to ISO string
                        "original_id": transaction['transaction_id'],
                        "is_pending": transaction.get('pending', False),
                        "location": transaction.get('location'),
                        "payment_meta": transaction.get('payment_meta')
                    }
                    all_transactions.append(unified_transaction)
                    
        except Exception as e:
            logging.error(f"Error fetching Plaid transactions for item {item.id}: {str(e)}")
            continue
    
    # 2. Get Stripe transactions if user has Stripe customer ID
    if user.stripe_customer_id:
        try:
            stripe_transactions = get_customer_transactions(user.stripe_customer_id, limit=1000)
            
            # Convert Stripe transactions to unified format
            for transaction in stripe_transactions:
                # Apply date filters to Stripe transactions
                if start_date:
                    start_dt = datetime.fromisoformat(start_date).replace(tzinfo=timezone.utc)
                    if transaction['date'] < start_dt:
                        continue
                
                if end_date:
                    end_dt = datetime.fromisoformat(end_date).replace(tzinfo=timezone.utc)
                    if transaction['date'] > end_dt:
                        continue
                
                unified_transaction = {
                    "id": f"stripe_{transaction['id']}",
                    "type": "stripe",
                    "amount": transaction['amount'],
                    "date": transaction['date'],
                    "merchant_name": transaction['merchant_name'],
                    "category": "payment",
                    "subcategory": "stripe",
                    "description": transaction['description'],
                    "status": transaction['status'],
                    "account_id": user.stripe_customer_id,
                    "created_at": transaction['created_at'],
                    "original_id": transaction['id'],
                    "payment_intent_id": transaction.get('payment_intent_id'),
                    "is_pending": transaction['status'] == 'pending'
                }
                all_transactions.append(unified_transaction)
                
        except Exception as e:
            logging.error(f"Failed to fetch Stripe transactions for user {user_id}: {str(e)}")
            # Continue without Stripe transactions if there's an error
    
    # 3. Store total unfiltered count before applying filters
    total_unfiltered_count = len(all_transactions)
    
    # 4. Apply additional filters
    filtered_transactions = all_transactions.copy()  # Work with a copy to preserve original
    
    if search:
        search_lower = search.lower()
        filtered_transactions = [
            t for t in filtered_transactions
            if (search_lower in (t.get('description', '') or '').lower() or
                search_lower in (t.get('merchant_name', '') or '').lower() or
                search_lower in str(t.get('amount', '')).lower())
        ]
    
    if status and status != 'all':
        filtered_transactions = [t for t in filtered_transactions if t['status'] == status]
    
    # 5. Sort filtered transactions by date (newest first)
    filtered_transactions.sort(key=lambda x: x['date'], reverse=True)
    
    # 6. Apply pagination to filtered results
    filtered_count = len(filtered_transactions)
    start_index = (page - 1) * limit
    end_index = start_index + limit
    paginated_transactions = filtered_transactions[start_index:end_index]
    
    # 7. Get user's donation preferences for round-up calculations
    donation_prefs = db.query(DonationPreference).filter(
        DonationPreference.user_id == user_id
    ).first()
    
    multiplier = 1.0
    if donation_prefs and donation_prefs.multiplier:
        multiplier = float(donation_prefs.multiplier.replace('x', ''))
    
    # 8. Process transactions and calculate round-ups
    processed_transactions = []
    
    for transaction in paginated_transactions:
        # Calculate round-up amount (only for Plaid transactions)
        roundup_amount = 0.0
        if transaction['type'] == 'plaid':
            roundup_amount = calculate_roundup_amount(transaction['amount'], multiplier)
        
        processed_transaction = {
            "id": transaction['id'],
            "type": transaction['type'],
            "amount": float(transaction['amount']),  # Ensure amount is float
            "date": transaction['date'],  # Already converted to ISO string
            "merchant_name": transaction['merchant_name'],
            "category": transaction['category'],
            "subcategory": transaction['subcategory'],
            "description": transaction['description'],
            "status": transaction['status'],
            "account_id": transaction['account_id'],
            "roundup_amount": round(roundup_amount, 2),  # Round to 2 decimal places
            "is_roundup_eligible": roundup_amount > 0,
            "created_at": transaction['created_at'],  # Already converted to ISO string
            "is_pending": transaction.get('is_pending', False)
        }
        
        # Add Stripe-specific fields
        if transaction['type'] == 'stripe':
            processed_transaction['payment_intent_id'] = transaction.get('payment_intent_id')
        
        processed_transactions.append(processed_transaction)
    
    # 9. Calculate pagination info based on filtered results
    total_pages = (filtered_count + limit - 1) // limit if filtered_count > 0 else 1
    has_next = page < total_pages
    has_prev = page > 1
    
    # Determine if filters are active
    has_active_filters = any([
        search and search.strip(),
        status and status != 'all',
        start_date,
        end_date,
        category
    ])
    
    return ResponseFactory.success(
        message="Transactions retrieved successfully",
        data={
            "transactions": processed_transactions,
            "pagination": {
                "page": page,
                "limit": limit,
                "filtered_count": filtered_count,
                "total_count": total_unfiltered_count,
                "total_pages": total_pages,
                "has_next": has_next,
                "has_prev": has_prev
            },
            "filters": {
                "start_date": start_date,
                "end_date": end_date,
                "category": category,
                "search": search,
                "status": status,
                "has_active_filters": has_active_filters
            }
        }
    )

@handle_controller_errors
def get_transaction_details(transaction_id: str, user_id: int, db: Session):
    """Get detailed transaction information"""
    
    # Extract the actual Plaid transaction ID from the formatted ID
    if not transaction_id.startswith('plaid_'):
        raise HTTPException(status_code=400, detail="Invalid transaction ID format")
    
    plaid_transaction_id = transaction_id.replace('plaid_', '')
    
    # Get user's Plaid items to find the transaction
    plaid_items = db.query(PlaidItem).filter(
        PlaidItem.user_id == user_id,
        PlaidItem.status == "active"
    ).all()
    
    transaction_details = None
    
    for item in plaid_items:
        try:
            # Fetch transactions using the new sync endpoint
            transactions_data = get_transactions(
                access_token=item.access_token,
                days_back=30
            )
            
            if transactions_data and 'transactions' in transactions_data:
                for transaction in transactions_data['transactions']:
                    if transaction['transaction_id'] == plaid_transaction_id:
                        transaction_details = transaction
                        break
                        
        except Exception as e:
            logging.error(f"Error fetching transactions for item {item.id}: {str(e)}")
            continue
    
    if not transaction_details:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Get user's donation preferences
    donation_prefs = db.query(DonationPreference).filter(
        DonationPreference.user_id == user_id
    ).first()
    
    multiplier = 1.0
    if donation_prefs and donation_prefs.multiplier:
        multiplier = float(donation_prefs.multiplier.replace('x', ''))
    
    # Calculate round-up amount
    roundup_amount = calculate_roundup_amount(float(transaction_details['amount']), multiplier)
    
    # RoundupTransaction removed - roundup data is now in DonationBatch
    # For detailed roundup info, we would need to query DonationBatch
    # For now, we'll calculate roundup amount on-the-fly
    
    # Handle date parsing safely
    try:
        if 'T' in transaction_details['date'] or 'Z' in transaction_details['date']:
            # ISO format with timezone
            transaction_date = datetime.fromisoformat(transaction_details['date'].replace('Z', '+00:00'))
        else:
            # Simple date format (YYYY-MM-DD)
            transaction_date = datetime.fromisoformat(transaction_details['date']).replace(tzinfo=timezone.utc)
    except (ValueError, TypeError) as e:
        logger.warning(f"Invalid date format for transaction {transaction_details.get('transaction_id', 'unknown')}: {transaction_details.get('date', 'unknown')}")
        raise HTTPException(status_code=400, detail="Invalid transaction date format")
    
    # Handle category safely
    transaction_category = transaction_details.get('category')
    
    result = {
        "id": f"plaid_{transaction_details['transaction_id']}",
        "account_id": transaction_details['account_id'],
        "amount": float(transaction_details['amount']),
        "date": transaction_date.isoformat(),
        "merchant_name": transaction_details.get('merchant_name') or transaction_details.get('name') or "Unknown Merchant",
        "category": transaction_category[0] if transaction_category and len(transaction_category) > 0 else "other",
        "subcategory": transaction_category[1] if transaction_category and len(transaction_category) > 1 else None,
        "description": transaction_details.get('name') or "Bank Transaction",
        "roundup_amount": roundup_amount,
        "is_roundup_eligible": roundup_amount > 0,
        "roundup_status": roundup_transaction.status if roundup_transaction else "pending",
        "roundup_collected_at": roundup_transaction.collected_at.isoformat() if roundup_transaction and roundup_transaction.collected_at else None,
        "created_at": transaction_date.isoformat(),
        "is_pending": transaction_details.get('pending', False),
        "location": transaction_details.get('location'),
        "payment_meta": transaction_details.get('payment_meta'),
        "iso_currency_code": transaction_details.get('iso_currency_code', 'USD')
    }
    
    return ResponseFactory.success(
        message="Transaction details retrieved successfully",
        data=result
    )

@handle_controller_errors
def calculate_roundup_for_transaction(transaction_id: str, user_id: int, db: Session):
    """Calculate round-up amount for a specific transaction"""
    
    # Extract the actual Plaid transaction ID from the formatted ID
    if not transaction_id.startswith('plaid_'):
        raise HTTPException(status_code=400, detail="Invalid transaction ID format")
    
    plaid_transaction_id = transaction_id.replace('plaid_', '')
    
    # Get user's Plaid items to find the transaction
    plaid_items = db.query(PlaidItem).filter(
        PlaidItem.user_id == user_id,
        PlaidItem.status == "active"
    ).all()
    
    transaction_details = None
    
    for item in plaid_items:
        try:
            # Fetch transactions using the new sync endpoint
            transactions_data = get_transactions(
                access_token=item.access_token,
                days_back=30
            )
            
            if transactions_data and 'transactions' in transactions_data:
                for transaction in transactions_data['transactions']:
                    if transaction['transaction_id'] == plaid_transaction_id:
                        transaction_details = transaction
                        break
                        
        except Exception as e:
            logging.error(f"Error fetching transactions for item {item.id}: {str(e)}")
            continue
    
    if not transaction_details:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Get user's donation preferences
    donation_prefs = db.query(DonationPreference).filter(
        DonationPreference.user_id == user_id
    ).first()
    
    multiplier = 1.0
    if donation_prefs and donation_prefs.multiplier:
        multiplier = float(donation_prefs.multiplier.replace('x', ''))
    
    # Calculate round-up amount
    roundup_amount = calculate_roundup_amount(float(transaction_details['amount']), multiplier)
    
    return ResponseFactory.success(
        message="Round-up calculated successfully",
        data={
            "transaction_id": transaction_id,
            "original_amount": float(transaction_details['amount']),
            "roundup_amount": roundup_amount,
            "multiplier": multiplier,
            "is_eligible": roundup_amount > 0
        }
    )

def calculate_roundup_amount(amount: float, multiplier: float = 1.0) -> float:
    """Calculate round-up amount for a given transaction amount"""
    
    # Only calculate round-ups for positive amounts (debits)
    # In Plaid, positive amounts are typically debits (money going out)
    if amount <= 0:
        return 0.0
    
    # Calculate the round-up (ceiling - original amount)
    rounded_amount = float(amount).__ceil__()
    roundup = rounded_amount - amount
    
    # Apply multiplier
    final_roundup = roundup * multiplier
    
    # Round to 2 decimal places
    return round(final_roundup, 2)

@handle_controller_errors
def sync_transactions(user_id: int, db: Session):
    """Sync transactions from Plaid for the current user using the new sync endpoint"""
    try:
        # Get user's Plaid items
        plaid_items = db.query(PlaidItem).filter(
            PlaidItem.user_id == user_id,
            PlaidItem.status == "active"
        ).all()
        
        if not plaid_items:
            return ResponseFactory.error("No active Plaid accounts found", "404")
        
        total_transactions = 0
        items_processed = 0
        
        for item in plaid_items:
            try:
                # Use the new sync endpoint to get transactions
                # This will fetch all available transactions using cursor-based pagination
                all_transactions = []
                cursor = None
                has_more = True
                page_count = 0
                
                logging.info(f"Starting sync for item {item.item_id} (access_token: {item.access_token[:10]}...)")
                
                while has_more:
                    page_count += 1
                    logging.debug(f"Fetching page {page_count} for item {item.item_id}, cursor: {cursor}")
                    
                    sync_response = get_transactions_sync(
                        access_token=item.access_token,
                        cursor=cursor,
                        count=500
                    )
                    
                    page_transactions = sync_response['transactions']
                    all_transactions.extend(page_transactions)
                    cursor = sync_response['next_cursor']
                    has_more = sync_response['has_more']
                    
                    logging.debug(f"Page {page_count}: {len(page_transactions)} transactions, has_more: {has_more}")
                
                total_transactions += len(all_transactions)
                items_processed += 1
                
                logging.info(f"Completed sync for item {item.item_id}: {len(all_transactions)} total transactions across {page_count} pages")
                
            except Exception as e:
                logging.error(f"Error syncing transactions for item {item.id}: {str(e)}")
                continue
        
        # Log summary of transaction types
        logging.info(f"Sync completed: {total_transactions} total transactions from {items_processed} active accounts")
        
        return ResponseFactory.success(
            message=f"Successfully fetched {total_transactions} transactions from {items_processed} active accounts",
            data={
                "total_transactions": total_transactions,
                "items_processed": items_processed,
                "note": "Transactions are now fetched on-demand and not stored in database for better performance"
            }
        )
        
    except Exception as e:
        logging.error(f"Error syncing transactions for user {user_id}: {str(e)}")
        return ResponseFactory.error("Failed to sync transactions", "500")
