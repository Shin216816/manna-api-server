"""
Donor Management Controller for Church Admins

Provides comprehensive donor management functionality:
- Active donor tracking
- Donor analytics
- Donor communication
- Donor status management
"""

from fastapi import HTTPException
import logging
import traceback
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc, case, text
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from app.model.m_church import Church
from app.model.m_user import User
from app.model.m_roundup_new import DonorPayout
from app.model.m_donation_preference import DonationPreference
from app.model.m_audit_log import AuditLog
# TransactionStatus and TransactionType enums removed - using DonationBatch status instead
from app.model.m_donation_preference import DonationPreference
from app.core.responses import ResponseFactory


def get_active_donors(
    church_id: int, page: int = 1, limit: int = 20, search: Optional[str] = None, status: Optional[str] = None, db: Optional[Session] = None
):
    """Get active donors with detailed analytics"""
    if db is None:
        raise HTTPException(status_code=500, detail="Database session required")

    try:
        # Check if church exists
        church = db.query(Church).filter_by(id=church_id).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")

        # Build base filter for counting
        count_filter = and_(
            User.church_id == church_id,
            User.is_active == True,
            User.role.in_(["donor", "congregant", "user"])  # Include multiple possible roles
        )
        
        # Add search filter to count if provided
        if search:
            search_filter = or_(
                User.first_name.ilike(f"%{search}%"),
                User.last_name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%"),
                func.concat(User.first_name, " ", User.last_name).ilike(f"%{search}%")
            )
            count_filter = and_(count_filter, search_filter)
        
        # Get total count for pagination - include all active users in the church, not just donors
        # This ensures we capture users who might not have the role set correctly
        total_count = (
            db.query(func.count(User.id))
            .filter(count_filter)
            .scalar()
            or 0
        )

        # Get church members with their donation stats (excluding admins)
        offset = (page - 1) * limit
        
        # Build base query
        base_filter = and_(
            User.church_id == church_id,
            User.is_active == True,
            User.role.in_(["donor", "congregant", "user"])  # Include multiple possible roles
        )
        
        # Add search filter if provided
        if search:
            search_filter = or_(
                User.first_name.ilike(f"%{search}%"),
                User.last_name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%"),
                func.concat(User.first_name, " ", User.last_name).ilike(f"%{search}%")
            )
            base_filter = and_(base_filter, search_filter)
        
        members_query = (
            db.query(
                User.id,
                User.first_name,
                User.last_name,
                User.email,
                User.phone,
                User.created_at,
                User.last_login,
                User.role,
                func.coalesce(func.sum(DonorPayout.donation_amount), 0).label(
                    "total_donated"
                ),
                func.coalesce(func.count(DonorPayout.id), 0).label("donation_count"),
                func.max(DonorPayout.processed_at).label("last_donation_date"),
            )
            .outerjoin(
                DonorPayout,
                and_(
                    User.id == DonorPayout.user_id,
                    DonorPayout.church_id == church_id,
                    DonorPayout.status == "completed",
                ),
            )
            .filter(base_filter)
            .group_by(User.id, User.role)
            .order_by(desc("total_donated"))
            .offset(offset)
            .limit(limit)
        )

        members = members_query.all()

        # If no members found with donations, try to get all active church members
        if not members and total_count > 0:
            # Fallback query to get all active church members
            fallback_query = (
                db.query(
                    User.id,
                    User.first_name,
                    User.last_name,
                    User.email,
                    User.phone,
                    User.created_at,
                    User.last_login,
                    User.role,
                )
                .filter(base_filter)  # Use the same base filter with search
                .order_by(User.created_at.desc())
                .offset(offset)
                .limit(limit)
            )
            members = fallback_query.all()

        # Process member data
        donors_data = []
        for member in members:
            preferences = (
                db.query(DonationPreference).filter_by(user_id=member.id).first()
            )

            # Handle both regular query (with donations) and fallback query (without donations)
            if hasattr(member, 'total_donated'):
                total_donated_dollars = (
                    float(member.total_donated) if member.total_donated else 0.0
                )
                donation_count = member.donation_count or 0
                last_donation_date = member.last_donation_date
            else:
                # Fallback query - get donation data separately
                donation_stats = (
                    db.query(
                        func.coalesce(func.sum(DonorPayout.donation_amount), 0).label("total_donated"),
                        func.coalesce(func.count(DonorPayout.id), 0).label("donation_count"),
                        func.max(DonorPayout.processed_at).label("last_donation_date"),
                    )
                    .filter(
                        DonorPayout.user_id == member.id,
                        DonorPayout.church_id == church_id,
                        DonorPayout.status == "completed",
                    )
                    .first()
                )
                total_donated_dollars = float(donation_stats.total_donated) if donation_stats else 0.0
                donation_count = donation_stats.donation_count if donation_stats else 0
                last_donation_date = donation_stats.last_donation_date if donation_stats else None

            avg_donation = (
                total_donated_dollars / donation_count
                if donation_count > 0
                else 0.0
            )

            # Determine status based on activity and role
            status = "active"
            if last_donation_date:
                days_since_last_donation = (
                    datetime.now(timezone.utc) - last_donation_date
                ).days
                if days_since_last_donation > 90:
                    status = "inactive"
                elif days_since_last_donation > 30:
                    status = "moderate"
            elif preferences and not preferences.pause:
                status = "active"
            elif member.role in ["donor", "congregant", "user"]:
                # If user is a member of the church but hasn't donated yet, mark as active
                status = "active"
            else:
                status = "inactive"

            # Create full name for display
            full_name = f"{member.first_name or ''} {member.last_name or ''}".strip()
            if not full_name:
                full_name = member.email or f"User {member.id}"

            donors_data.append(
                {
                    "id": member.id,
                    "first_name": member.first_name,
                    "last_name": member.last_name,
                    "full_name": full_name,
                    "name": full_name,  # For compatibility with frontend
                    "email": member.email,
                    "phone": member.phone,
                    "role": member.role,
                    "joined_date": (
                        member.created_at.isoformat() if member.created_at else None
                    ),
                    "last_login": (
                        member.last_login.isoformat() if member.last_login else None
                    ),
                    "last_donation": (
                        last_donation_date.isoformat()
                        if last_donation_date
                        else None
                    ),
                    "total_donated": round(total_donated_dollars, 2),
                    "donation_count": donation_count,
                    "average_donation": round(avg_donation, 2),
                    "avg_donation": round(avg_donation, 2),  # For compatibility
                    "donation_preferences": (
                        {
                            "roundup_enabled": (
                                not preferences.pause if preferences else False
                            ),
                            "frequency": preferences.frequency if preferences else None,
                            "multiplier": (
                                preferences.multiplier if preferences else None
                            ),
                            "cover_processing_fees": (
                                preferences.cover_processing_fees
                                if preferences
                                else False
                            ),
                        }
                        if preferences
                        else None
                    ),
                    "status": status,
                }
            )

        return ResponseFactory.success(
            message="Active donors retrieved successfully",
            data={
                "donors": donors_data,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": total_count,
                    "pages": (total_count + limit - 1) // limit,
                },
                "summary": {
                    "total_active_donors": total_count,
                    "total_donations": sum(d["total_donated"] for d in donors_data),
                    "average_donation": (
                        sum(d["total_donated"] for d in donors_data) / len(donors_data)
                        if donors_data
                        else 0
                    ),
                },
            },
        )

    except HTTPException:
        raise
    except Exception as e:

        raise HTTPException(status_code=500, detail="Failed to retrieve active donors")


def get_donor_analytics(church_id: int, donor_id: int, db: Optional[Session] = None):
    """Get comprehensive analytics for a specific donor"""
    if db is None:
        raise HTTPException(status_code=500, detail="Database session required")

    try:
        church = db.query(Church).filter_by(id=church_id).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")

        donor = (
            db.query(User)
            .filter(
                User.id == donor_id,
                User.church_id == church_id,
                User.role == "donor",
                User.is_active == True,
            )
            .first()
        )

        if not donor:
            raise HTTPException(status_code=404, detail="Donor not found")

        donations = (
            db.query(DonorPayout)
            .filter(
                DonorPayout.user_id == donor_id,
                DonorPayout.church_id == church_id,
                DonorPayout.status == "completed",
            )
            .order_by(DonorPayout.processed_at.desc())
            .all()
        )

        total_donated = sum(float(d.donation_amount) for d in donations)
        donation_count = len(donations)
        avg_donation = total_donated / donation_count if donation_count > 0 else 0.0

        preferences = db.query(DonationPreference).filter_by(user_id=donor_id).first()

        return ResponseFactory.success(
            message="Donor analytics retrieved successfully",
            data={
                "donor": {
                    "id": donor.id,
                    "name": f"{donor.first_name} {donor.last_name}",
                    "email": donor.email,
                    "phone": donor.phone,
                    "joined_date": (
                        donor.created_at.isoformat() if donor.created_at else None
                    ),
                    "last_login": (
                        donor.last_login.isoformat() if donor.last_login else None
                    ),
                },
                "giving_stats": {
                    "total_donated": round(float(total_donated), 2),
                    "donation_count": donation_count,
                    "average_donation": round(float(avg_donation), 2),
                },
                "preferences": (
                    {
                        "roundup_enabled": (
                            not preferences.pause if preferences else False
                        ),
                        "frequency": preferences.frequency if preferences else None,
                        "multiplier": preferences.multiplier if preferences else None,
                        "pause": preferences.pause if preferences else False,
                    }
                    if preferences
                    else None
                ),
            },
        )

    except HTTPException:
        raise
    except Exception as e:

        raise HTTPException(
            status_code=500, detail="Failed to retrieve donor analytics"
        )


def get_donor_communication_preferences(
    church_id: int, donor_id: int, db: Optional[Session] = None
):
    """Get donor communication preferences and history"""
    if db is None:
        raise HTTPException(status_code=500, detail="Database session required")

    try:
        church = db.query(Church).filter_by(id=church_id).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")

        donor = (
            db.query(User)
            .filter(
                User.id == donor_id,
                User.church_id == church_id,
                User.role == "donor",
                User.is_active == True,
            )
            .first()
        )

        if not donor:
            raise HTTPException(status_code=404, detail="Donor not found")

        communication_prefs = {
            "email_notifications": True,
            "sms_notifications": donor.phone is not None,
            "push_notifications": True,
            "marketing_emails": True,
            "frequency": "weekly",
        }

        return ResponseFactory.success(
            message="Donor communication preferences retrieved successfully",
            data={
                "donor_id": donor_id,
                "preferences": communication_prefs,
                "contact_info": {
                    "email": donor.email,
                    "phone": donor.phone,
                    "is_email_verified": donor.is_email_verified,
                    "is_phone_verified": donor.is_phone_verified,
                },
            },
        )

    except HTTPException:
        raise
    except Exception as e:

        raise HTTPException(
            status_code=500, detail="Failed to retrieve communication preferences"
        )


def update_donor_communication_preferences(
    church_id: int,
    donor_id: int,
    preferences: Dict[str, Any],
    admin_id: int,
    db: Optional[Session] = None,
):
    """Update donor communication preferences"""
    if db is None:
        raise HTTPException(status_code=500, detail="Database session required")

    try:
        church = db.query(Church).filter_by(id=church_id).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")

        donor = (
            db.query(User)
            .filter(
                User.id == donor_id,
                User.church_id == church_id,
                User.role == "donor",
                User.is_active == True,
            )
            .first()
        )

        if not donor:
            raise HTTPException(status_code=404, detail="Donor not found")

        audit_log = AuditLog(
            actor_type="church_admin",
            actor_id=admin_id,
            church_id=church_id,
            action="DONOR_COMMUNICATION_PREFERENCES_UPDATED",
            details_json={
                "donor_id": donor_id,
                "donor_email": donor.email,
                "old_preferences": {},
                "new_preferences": preferences,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        db.add(audit_log)
        db.commit()

        return ResponseFactory.success(
            message="Donor communication preferences updated successfully",
            data={
                "donor_id": donor_id,
                "preferences": preferences,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            },
        )

    except HTTPException:
        raise
    except Exception as e:

        raise HTTPException(
            status_code=500, detail="Failed to update communication preferences"
        )


def get_donor_retention_metrics(church_id: int, db: Optional[Session] = None):
    """Get donor retention metrics and insights"""
    if db is None:
        raise HTTPException(status_code=500, detail="Database session required")

    try:
        church = db.query(Church).filter_by(id=church_id).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")

        now = datetime.now(timezone.utc)

        all_donors = (
            db.query(func.distinct(DonorPayout.user_id))
            .filter(
                DonorPayout.church_id == church_id, DonorPayout.status == "completed"
            )
            .all()
        )

        total_donors = len(all_donors)
        if total_donors == 0:
            return ResponseFactory.success(
                message="No donor data available", data={"retention_metrics": {}}
            )

        retention_metrics = {}

        for period in [30, 60, 90, 180, 365]:
            period_days_ago = now - timedelta(days=period)

            recent_donors = (
                db.query(func.distinct(DonorPayout.user_id))
                .filter(
                    DonorPayout.church_id == church_id,
                    DonorPayout.status == "completed",
                    DonorPayout.processed_at >= period_days_ago,
                )
                .all()
            )

            retention_rate = (
                (len(recent_donors) / total_donors) * 100 if total_donors > 0 else 0
            )
            retention_metrics[f"{period}_day_retention"] = round(
                float(retention_rate), 1
            )

        return ResponseFactory.success(
            message="Donor retention metrics retrieved successfully",
            data={"retention_metrics": retention_metrics, "total_donors": total_donors},
        )

    except HTTPException:
        raise
    except Exception as e:

        raise HTTPException(
            status_code=500, detail="Failed to retrieve retention metrics"
        )


def export_donor_data(
    church_id: int,
    format_type: str = "csv",
    filters: Optional[Dict[str, Any]] = None,
    db: Optional[Session] = None,
):
    """Export donor data with optional filtering"""
    if db is None:
        raise HTTPException(status_code=500, detail="Database session required")

    try:
        church = db.query(Church).filter_by(id=church_id).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")

        if format_type not in ["csv", "json"]:
            raise HTTPException(
                status_code=400, detail="Format must be 'csv' or 'json'"
            )

        query = (
            db.query(
                User.id,
                User.first_name,
                User.last_name,
                User.email,
                User.phone,
                User.created_at,
                User.last_login,
                func.sum(DonorPayout.donation_amount).label("total_donated"),
                func.count(DonorPayout.id).label("donation_count"),
            )
            .join(
                DonorPayout,
                and_(
                    User.id == DonorPayout.user_id,
                    DonorPayout.church_id == church_id,
                    DonorPayout.status == "completed",
                ),
            )
            .filter(User.church_id == church_id, User.is_active == True)
            .group_by(User.id)
        )

        if filters:
            if filters.get("min_donations"):
                query = query.having(
                    func.count(DonorPayout.id) >= filters["min_donations"]
                )
            if filters.get("min_amount"):
                query = query.having(
                    func.sum(DonorPayout.donation_amount) >= filters["min_amount"]
                )

        donors = query.all()

        export_data = []
        for donor in donors:
            total_donated_dollars = (
                float(donor.total_donated) if donor.total_donated else 0.0
            )

            export_data.append(
                {
                    "id": donor.id,
                    "first_name": donor.first_name,
                    "last_name": donor.last_name,
                    "email": donor.email,
                    "phone": donor.phone,
                    "joined_date": (
                        donor.created_at.strftime("%Y-%m-%d")
                        if donor.created_at
                        else ""
                    ),
                    "last_login": (
                        donor.last_login.strftime("%Y-%m-%d")
                        if donor.last_login
                        else ""
                    ),
                    "total_donated": round(total_donated_dollars, 2),
                    "donation_count": donor.donation_count,
                    "average_donation": (
                        round(total_donated_dollars / donor.donation_count, 2)
                        if donor.donation_count > 0
                        else 0.0
                    ),
                }
            )

        return ResponseFactory.success(
            message=f"Donor data exported in {format_type} format",
            data={
                "format": format_type,
                "total_donors": len(export_data),
                "donors": export_data,
                "exported_at": datetime.now(timezone.utc).isoformat(),
                "filters_applied": filters or {},
            },
        )

    except HTTPException:
        raise
    except Exception as e:

        raise HTTPException(status_code=500, detail="Failed to export donor data")
