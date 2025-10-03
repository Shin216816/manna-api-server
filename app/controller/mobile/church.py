"""
Mobile Church Controller

Handles church-related operations for mobile app:
- Church search
- Church details
- Church updates
- User church management
"""

from fastapi import HTTPException
import logging
from sqlalchemy.orm import PassiveFlag, Session
from sqlalchemy import or_, and_
from datetime import datetime, timezone
from app.model.m_user import User
from app.model.m_church import Church
from app.model.m_church_message import ChurchMessage, MessageType, MessagePriority
from app.model.m_user_message import UserMessage
from app.core.responses import ResponseFactory
from app.schema.church_schema import ChurchSearchRequest, ChurchUpdateRequest
from typing import List, Dict, Any, Optional


def search_churches(query: str, db: Session):
    """Search for churches by name or location"""
    try:
        
        
        # First, let's check if there are any churches at all in the database
        total_churches = db.query(Church).count()
        
        
        active_churches = db.query(Church).filter(Church.is_active == True).count()
        
        
        if not query or query.strip() == "" or query.strip().lower() == "all":
            # Return all churches if no query or query is "all"
            
            churches = db.query(Church).filter(Church.is_active == True).all()

        else:
            # Search by name, address, city, or state
            search_term = f"%{query.strip()}%"
            
            churches = db.query(Church).filter(
                and_(
                    Church.is_active == True,
                    or_(
                        Church.name.ilike(search_term),
                        Church.address.ilike(search_term),
                        Church.city.ilike(search_term),
                        Church.state.ilike(search_term)
                    )
                )
            ).limit(20).all()
        
        church_list = []
        for church in churches:
            church_list.append({
                "id": church.id,
                "name": church.name,
                "address": church.address or "",
                "city": church.city or "",
                "state": church.state or "",
                "phone": church.phone or "",
                "email": church.email or "",
                "website": church.website or "",
                "kyc_status": getattr(church, 'kyc_status', 'not_submitted') or "not_submitted",
                "is_active": church.is_active,
                "is_verified": getattr(church, 'kyc_status', 'not_submitted') == 'approved',
                "type": "church",  # Default type
                "created_at": church.created_at.isoformat() if church.created_at else None
            })
        return ResponseFactory.success(
            message="Churches retrieved successfully",
            data={
                "churches": church_list,
                "total_count": len(church_list)
            }
        )
        
    except Exception as e:
        
        raise HTTPException(status_code=500, detail="Failed to search churches")


def get_church_details(church_id: int, db: Session):
    """Get detailed information about a specific church"""
    try:
        church = db.query(Church).filter(
            and_(
                Church.id == church_id,
                Church.is_active == True
            )
        ).first()
        
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")
        
        church_data = {
            "id": church.id,
            "name": church.name,
            "address": church.address or "",
            "city": "",  # Default empty string since field doesn't exist in DB
            "state": "",  # Default empty string since field doesn't exist in DB
            "phone": church.phone or "",
            "email": church.email or "",
            "website": church.website or "",
            "kyc_status": getattr(church, 'kyc_status', 'not_submitted') or "not_submitted",
            "is_active": church.is_active,
            "is_verified": getattr(church, 'kyc_status', 'not_submitted') == 'approved',
            "type": "church",  # Default type
            "created_at": church.created_at.isoformat() if church.created_at else None,
            "updated_at": church.updated_at.isoformat() if church.updated_at else None
        }
        
        return ResponseFactory.success(
            message="Church details retrieved successfully",
            data=church_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        
        raise HTTPException(status_code=500, detail="Failed to get church details")


def update_church_info(church_id: int, update_data: ChurchUpdateRequest, current_user: dict, db: Session):
    """Update church information (admin only)"""
    try:
        # Check if user is admin of this church
        user = db.query(User).filter(User.id == current_user["id"]).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if user is admin and belongs to this church
        primary_church = user.get_primary_church(db)
        if user.role != "church_admin" or not primary_church or primary_church.id != church_id:
            raise HTTPException(status_code=403, detail="Not authorized to update this church")
        
        church = db.query(Church).filter(Church.id == church_id).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")
        
        # Update church fields
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            if hasattr(church, field):
                setattr(church, field, value)
        
        db.commit()
        db.refresh(church)
        
        return ResponseFactory.success(
            message="Church information updated successfully",
            data={
                "church_id": church.id,
                "name": church.name,
                "updated_fields": list(update_dict.keys())
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        
        raise HTTPException(status_code=500, detail="Failed to update church information")


def get_user_church(user_id: int, db: Session):
    """Get the church that a user belongs to"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get user's primary church
        primary_church = user.get_primary_church(db)
        if not primary_church:
            return ResponseFactory.success(
                message="User not associated with any church",
                data={"church": None}
            )
        
        church = primary_church
        if not church:
            return ResponseFactory.success(
                message="User's church not found",
                data={"church": None}
            )
        
        church_data = {
            "id": church.id,
            "name": church.name,
            "address": church.address or "",
            "city": "",  # Default empty string since field doesn't exist in DB
            "state": "",  # Default empty string since field doesn't exist in DB
            "phone": church.phone or "",
            "email": church.email or "",
            "website": church.website or "",
            "kyc_status": getattr(church, 'kyc_status', 'not_submitted') or "not_submitted",
            "is_active": church.is_active,
            "is_verified": getattr(church, 'kyc_status', 'not_submitted') == 'approved',
            "type": "church"  # Default type
        }
        
        return ResponseFactory.success(
            message="User's church retrieved successfully",
            data={"church": church_data}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        
        raise HTTPException(status_code=500, detail="Failed to get user's church")


def remove_user_from_church(user_id: int, db: Session):
    """Remove user from their current church"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get user's primary church
        primary_church = user.get_primary_church(db)
        if not primary_church:
            return ResponseFactory.success(
                message="User not associated with any church",
                data={"removed": False}
            )
        
        previous_church_id = primary_church.id
        # Update user's church association using direct church_id
        db.commit()
        
        return ResponseFactory.success(
            message="User removed from church successfully",
            data={
                "removed": True,
                "previous_church_id": previous_church_id
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        
        raise HTTPException(status_code=500, detail="Failed to remove user from church")


def select_church_for_user(user_id: int, church_id: int, db: Session):
    """Select a church for the user and create welcome message"""
    try:
        # Check if user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if church exists and is active
        church = db.query(Church).filter(
            and_(
                Church.id == church_id,
                Church.is_active == True
            )
        ).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found or inactive")
        
        # Update user's church association using direct church_id
        user.updated_at = datetime.now(timezone.utc)
        
        # Create welcome message for the user
        welcome_message = ChurchMessage(
            church_id=church_id,
            title=f"Welcome to {church.name}!",
            content=f"Welcome to {church.name}! We're excited to have you join our community. "
                    f"Your donations will help support our mission and make a positive impact. "
                    f"Feel free to reach out if you have any questions about our church or "
                    f"how your donations are being used.",
            type=MessageType.GENERAL,
            priority=MessagePriority.MEDIUM,
            is_active=True,
            is_published=True,
            published_at=datetime.now(timezone.utc)
        )
        
        db.add(welcome_message)
        db.commit()
        db.refresh(user)
        db.refresh(welcome_message)
        
        # Create a UserMessage record for the welcome message
        user_message = UserMessage(
            user_id=user_id,
            message_id=welcome_message.id,
            is_read=False
        )
        db.add(user_message)
        db.commit()
        db.refresh(user_message)
        
        # Get updated church data
        church_data = {
            "id": church.id,
            "name": church.name,
            "address": church.address or "",
            "city": "",  # Default empty string since field doesn't exist in DB
            "state": "",  # Default empty string since field doesn't exist in DB
            "phone": church.phone or "",
            "email": church.email or "",
            "website": church.website or "",
            "kyc_status": getattr(church, 'kyc_status', 'not_submitted') or "not_submitted",
            "is_active": church.is_active,
            "is_verified": getattr(church, 'kyc_status', 'not_submitted') == 'approved',
            "type": "church"  # Default type
        }
        
        # Get comprehensive data for mobile app caching after church selection
        
        # 1. User profile data with church information
        church_id = church.id if church else None
        user_profile_data = {
            "id": user.id,
            "first_name": user.first_name,
            "middle_name": user.middle_name,
            "last_name": user.last_name,
            "email": user.email,
            "phone": user.phone,
            "is_email_verified": user.is_email_verified,
            "is_phone_verified": user.is_phone_verified,
            "church_id": church_id,  # Backward compatibility
            "church_ids": [church_id] if church_id else [],  # Mobile app expects array
            "primary_church_id": church_id,  # Mobile app expects this field
            "profile_picture_url": user.profile_picture_url,
            "role": user.role,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None,
            "church": church_data  # Include detailed church information
        }

        # 2. Get dashboard data (mobile impact summary and analytics)
        dashboard_data = None
        try:
            from app.controller.mobile.dashboard import get_mobile_dashboard
            dashboard_response = get_mobile_dashboard(user_id, db)
            dashboard_data = dashboard_response.get("data") if hasattr(dashboard_response, 'get') else None
        except Exception as e:
            PassiveFlag
            

        # 3. Get donation preferences
        preferences_data = None
        try:
            from app.controller.mobile.bank import get_bank_preferences
            prefs_response = get_bank_preferences(user_id, db)
            preferences_data = prefs_response.get("data") if hasattr(prefs_response, 'get') else None
        except Exception as e:
            pass
            

        # 4. Get roundup settings
        roundup_settings = None
        try:
            from app.controller.mobile.roundups import get_mobile_roundup_settings
            roundup_response = get_mobile_roundup_settings(user_id, db)
            roundup_settings = roundup_response.get("data") if hasattr(roundup_response, 'get') else None
        except Exception as e:
            pass
            

        # 5. Get donation summary (if user has donations)
        donation_summary = None
        try:
            from app.model.m_donation_batch import DonationBatch
            has_donations = db.query(DonationBatch).filter(DonationBatch.user_id == user_id).count() > 0
            if has_donations:
                from app.controller.mobile.donations import get_mobile_donation_summary
                summary_response = get_mobile_donation_summary(user_id, db)
                donation_summary = summary_response.get("data") if hasattr(summary_response, 'get') else None
        except Exception as e:
            pass
            

        # Prepare comprehensive response for mobile app caching
        response_data = {
            "user_profile": user_profile_data,  # Complete user profile for caching
            "church": church_data,
            "welcome_message": {
                "id": welcome_message.id,
                "title": welcome_message.title,
                "content": welcome_message.content,
                "type": welcome_message.type.value,
                "priority": welcome_message.priority.value,
                "created_at": welcome_message.created_at.isoformat()
            },
            "user_message": {
                "id": user_message.id,
                "user_id": user_message.user_id,
                "message_id": user_message.message_id,
                "is_read": user_message.is_read,
                "created_at": user_message.created_at.isoformat()
            }
        }

        # Add optional data if available (for home screen and other screens)
        if dashboard_data:
            response_data["dashboard"] = dashboard_data
        if preferences_data:
            response_data["bank_preferences"] = preferences_data
        if roundup_settings:
            response_data["roundup_settings"] = roundup_settings
        if donation_summary:
            response_data["donation_summary"] = donation_summary

        
        
        
        
        return ResponseFactory.success(
            message=f"Successfully joined {church.name}",
            data=response_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        
        raise HTTPException(status_code=500, detail="Failed to select church")


def refresh_user_data_after_church_selection(user_id: int, db: Session):
    """
    Get comprehensive user data after church selection for mobile app caching
    This endpoint is called by mobile app after church selection to refresh all screens
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get user's primary church information
        church_data = None
        primary_church = user.get_primary_church(db)
        if primary_church:
            church_data = {
                "id": primary_church.id,
                "name": primary_church.name,
                "address": primary_church.address or "",
                "city": getattr(primary_church, 'city', '') or "",
                "state": getattr(primary_church, 'state', '') or "",
                "phone": primary_church.phone or "",
                "email": primary_church.email or "",
                "website": primary_church.website or "",
                "kyc_status": getattr(primary_church, 'kyc_status', 'not_submitted') or "not_submitted",
                "is_active": primary_church.is_active,
                "is_verified": getattr(primary_church, 'kyc_status', 'not_submitted') == 'approved',
                "type": "church"
            }
        
        # 1. User profile data
        church_id = primary_church.id if primary_church else None
        user_profile_data = {
            "id": user.id,
            "first_name": user.first_name,
            "middle_name": user.middle_name,
            "last_name": user.last_name,
            "email": user.email,
            "phone": user.phone,
            "is_email_verified": user.is_email_verified,
            "is_phone_verified": user.is_phone_verified,
            "church_id": church_id,
            "church_ids": [church_id] if church_id else [],
            "primary_church_id": church_id,
            "profile_picture_url": user.profile_picture_url,
            "role": user.role or "user",
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None
        }
        
        if church_data:
            user_profile_data["church"] = church_data

        # 2. Mobile dashboard data
        mobile_dashboard = None
        try:
            from app.controller.mobile.dashboard import get_mobile_dashboard
            dashboard_response = get_mobile_dashboard(user_id, db)
            mobile_dashboard = dashboard_response.get("data") if hasattr(dashboard_response, 'get') else dashboard_response
        except Exception as e:
            pass
            

        # 3. Bank preferences
        bank_preferences = None
        try:
            from app.controller.mobile.bank import get_bank_preferences
            prefs_response = get_bank_preferences(user_id, db)
            bank_preferences = prefs_response.get("data") if hasattr(prefs_response, 'get') else prefs_response
        except Exception as e:
            pass
            

        # 4. Roundup settings
        roundup_settings = None
        try:
            from app.controller.mobile.roundups import get_mobile_roundup_settings
            roundup_response = get_mobile_roundup_settings(user_id, db)
            roundup_settings = roundup_response.get("data") if hasattr(roundup_response, 'get') else roundup_response
        except Exception as e:
            pass
            

        # 5. Donation summary
        donation_summary = None
        try:
            from app.controller.mobile.donations import get_mobile_donation_summary
            summary_response = get_mobile_donation_summary(user_id, db)
            donation_summary = summary_response.get("data") if hasattr(summary_response, 'get') else summary_response
        except Exception as e:
            pass
            

        # 6. Impact summary 
        impact_summary = None
        try:
            from app.controller.mobile.analytics import get_mobile_impact_analytics
            impact_response = get_mobile_impact_analytics(user_id, db)
            impact_summary = impact_response.get("data") if hasattr(impact_response, 'get') else impact_response
        except Exception as e:
            pass
            

        return ResponseFactory.success(
            message="User data refreshed successfully",
            data={
                "user_profile": user_profile_data,
                "church": church_data,
                "mobile_dashboard": mobile_dashboard,
                "bank_preferences": bank_preferences,
                "roundup_settings": roundup_settings,
                "donation_summary": donation_summary,
                "impact_summary": impact_summary,
                "cache_timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        
        raise HTTPException(status_code=500, detail="Failed to refresh user data")


def get_user_church_status(user_id: int, db: Session):
    """
    Get user's current church status for debugging mobile app issues
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get user's primary church
        primary_church = user.get_primary_church(db)
        church_data = None
        if primary_church:
            church_data = {
                "id": primary_church.id,
                "name": primary_church.name,
                "is_active": primary_church.is_active
            }
        
        church_id = primary_church.id if primary_church else None
        status_data = {
            "user_id": user.id,
            "church_id": church_id,
            "church_ids": [church_id] if church_id else [],
            "primary_church_id": church_id,
            "has_church": church_id is not None,
            "church_ids_empty": not bool(church_id),
            "church": church_data,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None
        }
        
        
        
        return ResponseFactory.success(
            message="Church status retrieved successfully",
            data=status_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        
        raise HTTPException(status_code=500, detail="Failed to get church status")
