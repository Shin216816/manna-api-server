"""
Admin User Management Controller

Handles admin user management functionality:
- List all users
- Get user details
- Search users
- User support and troubleshooting
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func, or_
from app.model.m_user import User
from app.model.m_church import Church
from app.model.m_donation_batch import DonationBatch
from app.model.m_donation_preference import DonationPreference
from app.model.m_plaid_items import PlaidItem
# PlaidAccount import removed - using on-demand Plaid API fetching
from app.core.responses import ResponseFactory
from datetime import datetime, timezone
import logging


def list_users(search: str, limit: int, offset: int, db: Session):
    """List all users with search functionality"""
    try:
        query = db.query(User)
        
        # Apply search filter
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    User.first_name.ilike(search_term),
                    User.last_name.ilike(search_term),
                    User.email.ilike(search_term)
                )
            )
        
        # Get total count
        total_count = query.count()
        
        # Get users with pagination
        users = query.order_by(desc(User.created_at)).offset(offset).limit(limit).all()
        
        user_data = []
        for user in users:
            # Get user's primary church name
            church_name = None
            primary_church = user.get_primary_church(db)
            if primary_church:
                church_name = primary_church.name
            
            # Get total donated amount
            total_donated_result = db.query(func.sum(DonationBatch.amount)).filter(
                and_(
                    DonationBatch.user_id == user.id,
                    DonationBatch.status == "completed"
                )
            ).scalar()
            total_donated = float(total_donated_result) if total_donated_result else 0.0
            
            # Get last active date (last donation or login)
            last_donation = db.query(DonationBatch).filter(
                and_(
                    DonationBatch.user_id == user.id,
                    DonationBatch.status == "completed"
                )
            ).order_by(desc(DonationBatch.created_at)).first()
            
            last_active = None
            if last_donation and last_donation.created_at:
                last_active = last_donation.created_at
            elif user.last_login:
                last_active = user.last_login
            
            user_data.append({
                "id": user.id,
                "name": f"{user.first_name} {user.last_name}",
                "email": user.email,
                "church_name": church_name,
                "total_donated": round(total_donated, 2),
                "last_active": last_active.isoformat() if last_active else None,
                "status": "active" if user.is_active else "inactive",
                "role": user.role
            })
        
        return ResponseFactory.success(
            message="Users retrieved successfully",
            data={
                "users": user_data,
                "total_count": total_count,
                "limit": limit,
                "offset": offset
            }
        )
        
    except Exception as e:
        
        return ResponseFactory.error("Error retrieving users", "500")


def get_user_details(user_id: int, db: Session):
    """Get detailed user information"""
    try:
        user = db.query(User).filter_by(id=user_id).first()
        if not user:
            return ResponseFactory.error("User not found", "404")
        
        # Get user's primary church
        church_name = None
        primary_church = user.get_primary_church(db)
        if primary_church:
            church_name = primary_church.name
        
        # Get donation history
        donations = db.query(DonationBatch).filter(
            and_(
                DonationBatch.user_id == user.id,
                DonationBatch.status == "completed"
            )
        ).order_by(desc(DonationBatch.created_at)).limit(10).all()
        
        donation_history = []
        for donation in donations:
            donation_history.append({
                "id": donation.id,
                "amount": donation.amount,
                "date": donation.created_at.isoformat() if donation.created_at else None,
                "status": donation.status,
                "stripe_transfer_id": donation.stripe_transfer_id
            })
        
        # Get bank accounts (masked for privacy) from Plaid API
        from app.services.plaid_account_service import plaid_account_service
        accounts_result = plaid_account_service.get_user_accounts(user.id, db)
        masked_accounts = []
        if accounts_result["success"]:
            for account in accounts_result["accounts"]:
                masked_accounts.append({
                    "id": account["account_id"],
                    "account_name": account["name"],
                    "mask": f"****{account['mask'][-4:]}" if account.get("mask") else "****",
                    "type": account["type"],
                    "is_active": account.get("status", "active") == "active"
                })
        
        # Get donation preferences
        preferences = db.query(DonationPreference).filter_by(user_id=user.id).first()
        user_preferences = None
        if preferences:
            user_preferences = {
                "frequency": preferences.frequency,
                "multiplier": preferences.multiplier,
                "pause": preferences.pause,
                "cover_processing_fees": preferences.cover_processing_fees,
                "church_id": preferences.church_id
            }
        
        # Get total donated
        total_donated_result = db.query(func.sum(DonationBatch.amount)).filter(
            and_(
                DonationBatch.user_id == user.id,
                DonationBatch.status == "completed"
            )
        ).scalar()
        total_donated = float(total_donated_result) if total_donated_result else 0.0
        
        user_details = {
            "id": user.id,
            "name": f"{user.first_name} {user.last_name}",
            "email": user.email,
            "phone": user.phone,
            "church_name": church_name,
            "church_id": primary_church.id if primary_church else None,
            "donation_history": donation_history,
            "bank_accounts": masked_accounts,
            "preferences": user_preferences,
            "total_donated": round(total_donated, 2),
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "status": "active" if user.is_active else "inactive",
            "role": user.role
        }
        
        return ResponseFactory.success(
            message="User details retrieved successfully",
            data={
                "user": user_details
            }
        )
        
    except Exception as e:
        
        return ResponseFactory.error("Error retrieving user details", "500")


def search_users(search_term: str, limit: int, offset: int, db: Session):
    """Search users by name or email"""
    try:
        search_filter = f"%{search_term}%"
        
        users = db.query(User).filter(
            or_(
                User.first_name.ilike(search_filter),
                User.last_name.ilike(search_filter),
                User.email.ilike(search_filter)
            )
        ).order_by(desc(User.created_at)).offset(offset).limit(limit).all()
        
        user_data = []
        for user in users:
            # Get user's primary church name
            church_name = None
            primary_church = user.get_primary_church(db)
            if primary_church:
                church_name = primary_church.name
            
            # Get total donated
            total_donated_result = db.query(func.sum(DonationBatch.amount)).filter(
                and_(
                    DonationBatch.user_id == user.id,
                    DonationBatch.status == "completed"
                )
            ).scalar()
            total_donated = float(total_donated_result) if total_donated_result else 0.0
            
            user_data.append({
                "id": user.id,
                "name": f"{user.first_name} {user.last_name}",
                "email": user.email,
                "church_name": church_name,
                "total_donated": round(total_donated, 2),
                "status": "active" if user.is_active else "inactive"
            })
        
        return ResponseFactory.success(
            message="User search completed",
            data={
                "users": user_data,
                "search_term": search_term,
                "limit": limit,
                "offset": offset
            }
        )
        
    except Exception as e:
        
        return ResponseFactory.error("Error searching users", "500") 
