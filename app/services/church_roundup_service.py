import logging
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from app.model.m_church import Church
from app.model.m_user import User
from app.model.m_plaid_items import PlaidItem
# PlaidAccount import removed - using on-demand Plaid API fetching
from app.model.m_donation_batch import DonationBatch
from app.model.m_donation_preference import DonationPreference
from app.model.m_audit_log import AuditLog
from app.core.exceptions import RoundupError
from app.services.plaid_transaction_service import plaid_transaction_service


class ChurchRoundupService:
    """Service for church admins to manage round-ups and transactions using on-demand fetching"""
    
    @staticmethod
    def get_church_roundup_summary(church_id: int, db: Session) -> Dict[str, Any]:
        """Get round-up summary for a church using on-demand transaction fetching"""
        try:
            # Get church
            church = db.query(Church).filter(Church.id == church_id).first()
            if not church:
                raise RoundupError(f"Church {church_id} not found")
            
            # Get round-up settings
            settings = db.query(DonationPreference).filter(DonationPreference.church_id == church_id).first()
            
            # Get active users for this church
            active_users = db.query(User).filter(
                User.church_id == church_id,
                User.is_active == True
            ).all()
            
            # Calculate roundup totals for all users
            total_pending = 0.0
            users_with_roundups = 0
            
            for user in active_users:
                try:
                    # Calculate roundup for this user
                    roundup_result = plaid_transaction_service.calculate_roundup_amount(
                        user_id=user.id,
                        db=db,
                        days_back=7,
                        multiplier=1.0  # Default multiplier
                    )
                    
                    if roundup_result["success"] and roundup_result["roundup_amount"] > 0:
                        total_pending += roundup_result["roundup_amount"]
                        users_with_roundups += 1
                        
                except Exception as e:
                    continue
            
            # Get recent batches
            recent_batches = db.query(DonationBatch).filter(
                DonationBatch.church_id == church_id,
                DonationBatch.batch_type == "roundup"
            ).order_by(DonationBatch.created_at.desc()).limit(5).all()
            
            # Calculate total collected
            total_collected = db.query(func.sum(DonationBatch.total_amount)).filter(
                DonationBatch.church_id == church_id,
                DonationBatch.batch_type == "roundup",
                DonationBatch.status == "success"
            ).scalar() or 0
            
            return {
                "church_name": church.name,
                "settings": {
                    "roundups_enabled": settings.roundups_enabled if settings else True,
                    "collection_frequency": settings.frequency if settings else "monthly",
                    "multiplier": settings.multiplier if settings else "2x",
                    "monthly_cap": float(settings.monthly_cap) if settings and settings.monthly_cap else None
                },
                "summary": {
                    "total_pending": round(total_pending, 2),
                    "total_collected": float(total_collected),
                    "pending_count": users_with_roundups,
                    "active_users": len(active_users),
                    "users_with_roundups": users_with_roundups
                },
                "recent_batches": [
                    {
                        "id": batch.id,
                        "total_amount": float(batch.total_amount),
                        "roundup_count": batch.roundup_count,
                        "status": batch.status,
                        "collection_date": batch.collection_date.isoformat() if batch.collection_date else None,
                        "created_at": batch.created_at.isoformat()
                    }
                    for batch in recent_batches
                ]
            }
            
        except Exception as e:
            raise RoundupError(f"Failed to get church roundup summary: {str(e)}")
    
    @staticmethod
    def get_church_transactions(
        church_id: int, 
        db: Session,
        page: int = 1, 
        limit: int = 20,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get transactions for church members using on-demand fetching"""
        try:
            # Get active users for this church
            active_users = db.query(User).filter(
                User.church_id == church_id,
                User.is_active == True
            ).all()
            
            all_transactions = []
            total_count = 0
            
            for user in active_users:
                try:
                    # Get transactions for this user
                    result = plaid_transaction_service.get_user_transactions(
                        user_id=user.id,
                        db=db,
                        days_back=30
                    )
                    
                    if result["success"]:
                        transactions = result["transactions"]
                        total_count += len(transactions)
                        
                        # Add user info to each transaction
                        for transaction in transactions:
                            transaction["user_id"] = user.id
                            transaction["user_name"] = f"{user.first_name} {user.last_name}".strip()
                            all_transactions.append(transaction)
                            
                except Exception as e:
                    continue
            
            # Sort by date (newest first)
            all_transactions.sort(key=lambda x: x.get('date', ''), reverse=True)
            
            # Apply pagination
            start_idx = (page - 1) * limit
            end_idx = start_idx + limit
            paginated_transactions = all_transactions[start_idx:end_idx]
            
            return {
                "transactions": paginated_transactions,
                "total_count": total_count,
                "page": page,
                "limit": limit,
                "total_pages": (total_count + limit - 1) // limit
            }
            
        except Exception as e:
            raise RoundupError(f"Failed to get church transactions: {str(e)}")
    
    @staticmethod
    def get_user_roundup_details(
        church_id: int,
        user_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """Get detailed roundup information for a specific user"""
        try:
            # Verify user belongs to church
            user = db.query(User).filter(
                User.id == user_id,
                User.church_id == church_id,
                User.is_active == True
            ).first()
            
            if not user:
                raise RoundupError(f"User {user_id} not found or not active in church {church_id}")
            
            # Get roundup summary for this user
            roundup_result = plaid_transaction_service.calculate_roundup_amount(
                user_id=user_id,
                db=db,
                days_back=7,
                multiplier=1.0
            )
            
            if not roundup_result["success"]:
                return {
                    "user_id": user_id,
                    "user_name": f"{user.first_name} {user.last_name}".strip(),
                    "roundup_amount": 0.0,
                    "transaction_count": 0,
                    "error": roundup_result.get("error", "Failed to calculate roundup")
                }
            
            return {
                "user_id": user_id,
                "user_name": f"{user.first_name} {user.last_name}".strip(),
                "roundup_amount": roundup_result["roundup_amount"],
                "transaction_count": roundup_result["transaction_count"],
                "period_days": roundup_result["period_days"]
            }
            
        except Exception as e:
            raise RoundupError(f"Failed to get user roundup details: {str(e)}")
    
    @staticmethod
    def process_church_roundups(church_id: int, db: Session) -> Dict[str, Any]:
        """Process roundups for all active users in a church"""
        try:
            # Get active users for this church
            active_users = db.query(User).filter(
                User.church_id == church_id,
                User.is_active == True
            ).all()
            
            total_roundup_amount = 0.0
            users_processed = 0
            users_with_roundups = 0
            
            for user in active_users:
                try:
                    # Calculate roundup for this user
                    roundup_result = plaid_transaction_service.calculate_roundup_amount(
                        user_id=user.id,
                        db=db,
                        days_back=7,
                        multiplier=1.0
                    )
                    
                    if roundup_result["success"]:
                        total_roundup_amount += roundup_result["roundup_amount"]
                        users_processed += 1
                        
                        if roundup_result["roundup_amount"] > 0:
                            users_with_roundups += 1
                            
                except Exception as e:
                    continue
            
            return {
                "church_id": church_id,
                "total_roundup_amount": round(total_roundup_amount, 2),
                "users_processed": users_processed,
                "users_with_roundups": users_with_roundups,
                "period_days": 7
            }
            
        except Exception as e:
            raise RoundupError(f"Failed to process church roundups: {str(e)}")
