from fastapi import HTTPException
import logging
import traceback
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone, timedelta
from typing import Optional

from app.model.m_user import User
from app.model.m_church import Church
from app.model.m_donation_batch import DonationBatch
from app.model.m_donation_preference import DonationPreference
from app.core.responses import ResponseFactory


def get_all_users(
    page: int = 1,
    limit: int = 20,
    search: str = "",
    church_id: Optional[int] = None,
    role: Optional[str] = None,
    db: Optional[Session] = None,
):
    """Get all users with pagination and filtering"""
    try:
        if db is None:
            raise HTTPException(status_code=500, detail="Database session required")
        
        query = db.query(User)

        # Filter by role - default to only donor users for users page
        if role:
            query = query.filter(User.role == role)
        else:
            # Default: exclude church_admin and manna_admin users
            query = query.filter(User.role.in_(["donor", "congregant", "user"]))

        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                (User.email.ilike(search_filter))
                | (User.first_name.ilike(search_filter))
                | (User.last_name.ilike(search_filter))
            )
        if church_id and church_id > 0:
            # Note: This filter needs to be updated to use ChurchMembership relationship
            # For now, we'll skip this filter as User.church_id doesn't exist
            pass

        total = query.count()
        users = query.offset((page - 1) * limit).limit(limit).all()

        users_data = []
        for user in users:
            try:
                # Get user's primary church
                primary_church = user.get_primary_church(db)
                church = primary_church

                # Get user's total donations
                total_donations = (
                    db.query(func.sum(DonationBatch.amount))
                    .filter(
                        DonationBatch.user_id == user.id,
                        DonationBatch.status == "completed",
                    )
                    .scalar()
                    or 0.0
                )

                # Get user's donation count
                donation_count = (
                    db.query(func.count(DonationBatch.id))
                    .filter(
                        DonationBatch.user_id == user.id,
                        DonationBatch.status == "completed",
                    )
                    .scalar()
                    or 0
                )

                users_data.append(
                    {
                        "id": user.id,
                        "email": user.email,
                        "phone": user.phone,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "is_active": user.is_active,
                        "is_email_verified": user.is_email_verified,
                        "is_phone_verified": user.is_phone_verified,
                        "church_id": church.id if church else None,
                        "church_name": church.name if church else None,
                        "created_at": (
                            user.created_at.isoformat() if user.created_at else None
                        ),
                        "last_login": (
                            user.last_login.isoformat() if user.last_login else None
                        ),
                        "stats": {
                            "total_donations": round(float(total_donations or 0), 2),
                            "donation_count": donation_count,
                        },
                    }
                )
                
            except Exception as user_error:
                # Log error but continue with next user
                print(f"Error processing user {user.email}: {user_error}")
                continue
        
        return ResponseFactory.success(
            message="Users retrieved successfully",
            data={
                "users": users_data,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": total,
                    "pages": (total + limit - 1) // limit,
                },
            },
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to retrieve users")


def get_user_details(user_id: int, db: Session):
    """Get detailed user information"""
    try:
        if db is None:
            raise HTTPException(status_code=500, detail="Database session required")
        user = db.query(User).filter_by(id=user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Get user's primary church (only for church_id reference)
        primary_church = user.get_primary_church(db)

        # Get user's total donations
        total_donations = (
            db.query(func.sum(DonationBatch.amount))
            .filter(
                DonationBatch.user_id == user.id, DonationBatch.status == "completed"
            )
            .scalar()
            or 0.0
        )

        # Get user's donation count
        donation_count = (
            db.query(func.count(DonationBatch.id))
            .filter(
                DonationBatch.user_id == user.id, DonationBatch.status == "completed"
            )
            .scalar()
            or 0
        )

        # Get this month's donations
        current_month = datetime.now(timezone.utc).replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        this_month_donations = (
            db.query(func.sum(DonationBatch.amount))
            .filter(
                DonationBatch.user_id == user.id,
                DonationBatch.status == "completed",
                DonationBatch.created_at >= current_month,
            )
            .scalar()
            or 0.0
        )

        # Get donation preferences
        preferences = db.query(DonationPreference).filter(DonationPreference.user_id == user.id).first()
        
        # For admin view, if no preferences exist, we don't create defaults
        # This allows admins to see that the user hasn't set up preferences yet

        return ResponseFactory.success(
            message="User details retrieved successfully",
            data={
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "phone": user.phone,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "middle_name": user.middle_name,
                    "is_active": user.is_active,
                    "is_email_verified": user.is_email_verified,
                    "is_phone_verified": user.is_phone_verified,
                    "church_id": primary_church.id if primary_church else None,
                    "google_id": user.google_id,
                    "apple_id": user.apple_id,
                    "profile_picture_url": user.profile_picture_url,
                    "created_at": (
                        user.created_at.isoformat() if user.created_at else None
                    ),
                    "updated_at": (
                        user.updated_at.isoformat() if user.updated_at else None
                    ),
                    "last_login": (
                        user.last_login.isoformat() if user.last_login else None
                    ),
                    "role": user.role,
                    "stats": {
                        "total_donations": round(float(total_donations or 0), 2),
                        "donation_count": donation_count,
                        "this_month_donations": round(float(this_month_donations), 2),
                    },
                    "preferences": {
                        "frequency": preferences.frequency if preferences else None,
                        "multiplier": preferences.multiplier if preferences else None,
                        "pause": preferences.pause if preferences else None,
                        "cover_processing_fees": (
                            preferences.cover_processing_fees if preferences else None
                        ),
                        "roundups_enabled": (
                            preferences.roundups_enabled if preferences else None
                        ),
                        "minimum_roundup": (
                            float(preferences.minimum_roundup) if preferences and preferences.minimum_roundup is not None else None
                        ),
                        "monthly_cap": (
                            float(preferences.monthly_cap) if preferences and preferences.monthly_cap is not None else None
                        ),
                        "exclude_categories": (
                            preferences.exclude_categories if preferences else None
                        ),
                        "target_church_id": (
                            preferences.target_church_id if preferences else None
                        ),
                        "created_at": (
                            preferences.created_at.isoformat() if preferences and preferences.created_at else None
                        ),
                        "updated_at": (
                            preferences.updated_at.isoformat() if preferences and preferences.updated_at else None
                        ),
                    },
                }
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to retrieve user details")


def update_user_status(user_id: int, is_active: bool, db: Session):
    """Update user status"""
    try:
        user = db.query(User).filter_by(id=user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user.is_active = is_active
        user.updated_at = datetime.now(timezone.utc)
        db.commit()

        return ResponseFactory.success(
            message="User status updated successfully",
            data={
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "is_active": user.is_active,
                    "updated_at": user.updated_at.isoformat(),
                }
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to update user status")


def get_user_analytics(
    user_id: int,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Optional[Session] = None,
):
    """Get user analytics with proper date validation and comprehensive data"""
    try:
        if db is None:
            raise HTTPException(status_code=500, detail="Database session required")
        
        user = db.query(User).filter_by(id=user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Validate and parse dates
        start_date_obj = None
        end_date_obj = None
        
        if start_date:
            try:
                start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start_date format. Use YYYY-MM-DD")
        
        if end_date:
            try:
                end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end_date format. Use YYYY-MM-DD")

        # Build query for donations - only completed donations
        query = db.query(DonationBatch).filter(
            DonationBatch.user_id == user_id, 
            DonationBatch.status == "completed"
        )

        # Apply date filters
        if start_date_obj:
            query = query.filter(DonationBatch.created_at >= start_date_obj)
        if end_date_obj:
            query = query.filter(DonationBatch.created_at <= end_date_obj)

        donations = query.order_by(DonationBatch.created_at.desc()).all()

        # Calculate analytics
        total_amount = sum(float(d.amount) for d in donations)
        donation_count = len(donations)
        avg_donation = total_amount / donation_count if donation_count > 0 else 0.0

        # Get first and last donation dates
        first_donation = donations[-1] if donations else None
        last_donation = donations[0] if donations else None

        # Monthly breakdown - group by month
        monthly_data = {}
        for donation in donations:
            month_key = donation.created_at.strftime("%Y-%m")
            if month_key not in monthly_data:
                monthly_data[month_key] = {"amount": 0.0, "count": 0}
            monthly_data[month_key]["amount"] += float(donation.amount)
            monthly_data[month_key]["count"] += 1

        # Sort monthly data by month
        sorted_monthly = sorted(monthly_data.items(), key=lambda x: x[0])

        # Calculate additional metrics
        total_donations_all_time = db.query(func.count(DonationBatch.id)).filter(
            DonationBatch.user_id == user_id,
            DonationBatch.status == "completed"
        ).scalar() or 0

        total_amount_all_time = db.query(func.sum(DonationBatch.amount)).filter(
            DonationBatch.user_id == user_id,
            DonationBatch.status == "completed"
        ).scalar() or 0.0

        return ResponseFactory.success(
            message="User analytics retrieved successfully",
            data={
                "user_id": user_id,
                "user_name": f"{user.first_name} {user.last_name}",
                "analytics": {
                    "total_amount": round(float(total_amount), 2),
                    "donation_count": donation_count,
                    "average_donation": round(float(avg_donation), 2),
                    "first_donation_date": first_donation.created_at.isoformat() if first_donation else None,
                    "last_donation_date": last_donation.created_at.isoformat() if last_donation else None,
                    "total_donations_all_time": total_donations_all_time,
                    "total_amount_all_time": round(float(total_amount_all_time), 2),
                },
                "monthly_breakdown": [
                    {
                        "month": month,
                        "amount": round(data["amount"], 2),
                        "count": data["count"],
                    }
                    for month, data in sorted_monthly
                ],
                "date_range": {
                    "start_date": start_date, 
                    "end_date": end_date,
                    "period_days": (end_date_obj - start_date_obj).days if start_date_obj and end_date_obj else None
                },
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to retrieve user analytics")


def get_user_donations(
    user_id: int, page: int = 1, limit: int = 20, db: Optional[Session] = None
):
    """Get user donations"""
    try:
        if db is None:
            raise HTTPException(status_code=500, detail="Database session required")
        user = db.query(User).filter_by(id=user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        query = db.query(DonationBatch).filter(
            DonationBatch.user_id == user_id, DonationBatch.status == "completed"
        )
        total = query.count()
        donations = (
            query.order_by(DonationBatch.created_at.desc())
            .offset((page - 1) * limit)
            .limit(limit)
            .all()
        )

        donations_data = []
        for donation in donations:
            donations_data.append(
                {
                    "id": donation.id,
                    "total_amount": float(donation.amount),
                    "transaction_count": donation.transaction_count,
                    "status": donation.status,
                    "created_at": donation.created_at.isoformat(),
                    "processed_at": (
                        donation.payout_date.isoformat()
                        if donation.payout_date
                        else None
                    ),
                }
            )

        return ResponseFactory.success(
            message="User donations retrieved successfully",
            data={
                "donations": donations_data,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": total,
                    "pages": (total + limit - 1) // limit,
                },
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to retrieve user donations")


def get_user_church(user_id: int, db: Optional[Session] = None):
    """Get user's church information"""
    try:
        if db is None:
            raise HTTPException(status_code=500, detail="Database session required")
        user = db.query(User).filter_by(id=user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Get user's primary church
        primary_church = user.get_primary_church(db)
        if not primary_church:
            return ResponseFactory.success(
                message="User has no church", data={"church": None}
            )

        church = primary_church
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")

        return ResponseFactory.success(
            message="User church retrieved successfully",
            data={
                "church": {
                    "id": church.id,
                    "name": church.name,
                    "email": church.email,
                    "phone": church.phone,
                    "website": church.website,
                    "status": church.status,
                    "is_active": church.is_active,
                    "kyc_status": church.kyc_status,
                }
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to retrieve user church")


def get_user_activity(user_id: int, db: Optional[Session] = None):
    """Get comprehensive user activity for admin management"""
    try:
        if db is None:
            raise HTTPException(status_code=500, detail="Database session required")
        
        user = db.query(User).filter_by(id=user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Import required models
        from app.model.m_audit_log import AuditLog
        from app.model.m_donation_batch import DonationBatch
        from app.model.m_donation_preference import DonationPreference
        from app.services.session_service import session_manager

        # Get login activity
        login_activity = {
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "account_created": user.created_at.isoformat() if user.created_at else None,
            "last_updated": user.updated_at.isoformat() if user.updated_at else None,
            "is_active": user.is_active,
            "email_verified": user.is_email_verified,
            "phone_verified": user.is_phone_verified,
        }

        # Get active sessions
        active_sessions = session_manager.get_user_sessions(user_id)
        session_activity = []
        for session in active_sessions:
            session_activity.append({
                "session_id": session.session_id,
                "device_info": session.device_info,
                "ip_address": session.ip_address,
                "user_agent": session.user_agent,
                "created_at": session.created_at.isoformat() if session.created_at else None,
                "last_activity": session.last_activity.isoformat() if session.last_activity else None,
                "is_active": session.is_active,
            })

        # Get donation activity
        donation_batches = db.query(DonationBatch).filter(
            DonationBatch.user_id == user_id
        ).order_by(DonationBatch.created_at.desc()).limit(10).all()

        donation_activity = []
        for batch in donation_batches:
            donation_activity.append({
                "id": batch.id,
                "amount": float(batch.amount),
                "status": batch.status,
                "transaction_count": batch.transaction_count,
                "created_at": batch.created_at.isoformat() if batch.created_at else None,
                "collection_date": batch.collection_date.isoformat() if batch.collection_date else None,
                "payout_date": batch.payout_date.isoformat() if batch.payout_date else None,
                "processing_fee": float(batch.processing_fee) if batch.processing_fee else 0.0,
                "net_amount": float(batch.net_amount) if batch.net_amount else 0.0,
            })

        # Get donation statistics
        total_donated = db.query(func.sum(DonationBatch.amount)).filter(
            DonationBatch.user_id == user_id,
            DonationBatch.status == "completed"
        ).scalar() or 0.0

        donation_count = db.query(func.count(DonationBatch.id)).filter(
            DonationBatch.user_id == user_id,
            DonationBatch.status == "completed"
        ).scalar() or 0

        # Get preference changes (from audit logs)
        preference_changes = db.query(AuditLog).filter(
            AuditLog.actor_type == "user",
            AuditLog.actor_id == user_id,
            AuditLog.action.like("%PREFERENCE%")
        ).order_by(AuditLog.created_at.desc()).limit(5).all()

        preference_activity = []
        for change in preference_changes:
            preference_activity.append({
                "action": change.action,
                "created_at": change.created_at.isoformat() if change.created_at else None,
                "additional_data": change.additional_data,
                "ip_address": change.ip_address,
            })

        # Get account activity (profile changes, etc.)
        account_activity = []
        
        # Add account creation
        account_activity.append({
            "action": "ACCOUNT_CREATED",
            "description": "User account created",
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "details": {
                "email": user.email,
                "role": user.role,
            }
        })

        # Add email verification if verified
        if user.is_email_verified and user.updated_at:
            account_activity.append({
                "action": "EMAIL_VERIFIED",
                "description": "Email address verified",
                "created_at": user.updated_at.isoformat(),
                "details": {
                    "email": user.email,
                }
            })

        # Add phone verification if verified
        if user.is_phone_verified and user.updated_at:
            account_activity.append({
                "action": "PHONE_VERIFIED",
                "description": "Phone number verified",
                "created_at": user.updated_at.isoformat(),
                "details": {
                    "phone": user.phone,
                }
            })

        # Get recent audit logs for this user
        recent_audit_logs = db.query(AuditLog).filter(
            AuditLog.actor_type == "user",
            AuditLog.actor_id == user_id
        ).order_by(AuditLog.created_at.desc()).limit(10).all()

        audit_activity = []
        for log in recent_audit_logs:
            audit_activity.append({
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "created_at": log.created_at.isoformat() if log.created_at else None,
                "ip_address": log.ip_address,
                "user_agent": log.user_agent,
                "additional_data": log.additional_data,
            })

        # Get church activity
        church_activity = []
        if user.church_id:
            church_activity.append({
                "action": "CHURCH_JOINED",
                "description": f"Joined church (ID: {user.church_id})",
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "details": {
                    "church_id": user.church_id,
                }
            })

        # Calculate activity summary
        activity_summary = {
            "total_donations": donation_count,
            "total_donated": round(float(total_donated), 2),
            "active_sessions": len(active_sessions),
            "last_activity": user.last_login.isoformat() if user.last_login else None,
            "account_age_days": (datetime.now(timezone.utc) - user.created_at).days if user.created_at else 0,
        }

        return ResponseFactory.success(
            message="User activity retrieved successfully",
            data={
                "user_id": user_id,
                "activity_summary": activity_summary,
                "login_activity": login_activity,
                "session_activity": session_activity,
                "donation_activity": donation_activity,
                "preference_activity": preference_activity,
                "account_activity": account_activity,
                "audit_activity": audit_activity,
                "church_activity": church_activity,
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to retrieve user activity")
