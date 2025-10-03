from fastapi import HTTPException
import logging
import traceback
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from sqlalchemy import func
from typing import Optional
from app.model.m_church import Church
from app.model.m_user import User
from app.model.m_donation_batch import DonationBatch
from app.model.m_audit_log import AuditLog
from app.core.responses import ResponseFactory


def get_church_members(
    church_id: int, page: int = 1, limit: int = 20, anonymized: bool = True, db: Optional[Session] = None
):
    """Get church members list with optional anonymization"""
    if db is None:
        raise HTTPException(status_code=500, detail="Database session required")
    
    # Validate parameters
    if page < 1:
        raise HTTPException(status_code=400, detail="Page must be greater than 0")
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 100")
    if church_id < 1:
        raise HTTPException(status_code=400, detail="Invalid church ID")
    
    try:
        church = db.query(Church).filter(Church.id == church_id).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")

        offset = (page - 1) * limit

        # Get users associated with this church
        members = (
            db.query(User)
            .filter(User.church_id == church_id)
            .order_by(User.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        total_count = (
            db.query(func.count(User.id)).filter(User.church_id == church_id).scalar()
        )

        members_data = []
        for member in members:
            # Get member's donation summary
            total_donated = (
                db.query(func.sum(DonationBatch.total_amount))
                .filter(
                    DonationBatch.user_id == member.id,
                    DonationBatch.church_id == church_id,
                    DonationBatch.status == "completed",
                )
                .scalar()
                or 0.0
            )

            donation_count = (
                db.query(func.count(DonationBatch.id))
                .filter(
                    DonationBatch.user_id == member.id,
                    DonationBatch.church_id == church_id,
                    DonationBatch.status == "completed",
                )
                .scalar()
                or 0
            )

            if anonymized:
                # Anonymized data for general church admin viewing
                members_data.append(
                    {
                        "id": f"donor_{member.id}",  # Anonymized ID
                        "donor_id": member.id,  # Keep for internal reference
                        "name": f"{member.first_name[0]}{'*' * (len(member.first_name) - 1)} {member.last_name[0]}{'*' * (len(member.last_name) - 1)}",  # Anonymized name
                        "email": f"{member.email.split('@')[0][:2]}{'*' * (len(member.email.split('@')[0]) - 2)}@{member.email.split('@')[1]}" if member.email else None,  # Anonymized email
                        "phone": f"***-***-{member.phone[-4:]}" if member.phone else None,  # Anonymized phone
                        "is_email_verified": member.is_email_verified,
                        "is_phone_verified": member.is_phone_verified,
                        "joined_date": member.created_at.strftime("%Y-%m") if member.created_at else None,  # Only month/year
                        "total_donated": float(total_donated),
                        "donation_count": donation_count,
                        "donation_frequency": "Regular" if donation_count > 5 else "Occasional" if donation_count > 0 else "New",
                        "last_donation_month": None,  # Will be populated if needed
                    }
                )
            else:
                # Detailed data for support/troubleshooting purposes
                members_data.append(
                    {
                        "id": member.id,
                        "first_name": member.first_name,
                        "last_name": member.last_name,
                        "email": member.email,
                        "phone": member.phone,
                        "is_email_verified": member.is_email_verified,
                        "is_phone_verified": member.is_phone_verified,
                        "created_at": member.created_at,
                        "total_donated": float(total_donated),
                        "donation_count": donation_count,
                    }
                )

        return ResponseFactory.success(
            message="Church members retrieved successfully",
            data={
                "members": members_data,
                "view_type": "anonymized" if anonymized else "detailed",
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total_count": total_count,
                    "total_pages": (total_count + limit - 1) // limit,
                },
            },
        )

    except HTTPException:
        raise
    except Exception as e:

        raise HTTPException(status_code=500, detail="Failed to get members")


def get_member_details(member_id: int, church_id: int, db: Session):
    """Get specific member details"""
    try:
        church = db.query(Church).filter(Church.id == church_id).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")

        member = (
            db.query(User)
            .filter(User.id == member_id, User.church_id == church_id)
            .first()
        )

        if not member:
            raise HTTPException(status_code=404, detail="Member not found")

        # Get member's donation statistics
        total_donated = (
            db.query(func.sum(DonationBatch.total_amount))
            .filter(
                DonationBatch.user_id == member.id,
                DonationBatch.church_id == church_id,
                DonationBatch.status == "completed",
            )
            .scalar()
            or 0.0
        )

        donation_count = (
            db.query(func.count(DonationBatch.id))
            .filter(
                DonationBatch.user_id == member.id,
                DonationBatch.church_id == church_id,
                DonationBatch.status == "completed",
            )
            .scalar()
            or 0
        )

        avg_donation = total_donated / donation_count if donation_count > 0 else 0.0

        # Get recent donations
        recent_donations = (
            db.query(DonationBatch)
            .filter(
                DonationBatch.user_id == member.id,
                DonationBatch.church_id == church_id,
                DonationBatch.status == "completed",
            )
            .order_by(DonationBatch.created_at.desc())
            .limit(5)
            .all()
        )

        recent_donations_data = []
        for donation in recent_donations:
            recent_donations_data.append(
                {
                    "id": donation.id,
                    "amount": float(donation.total_amount),
                    "created_at": donation.created_at,
                    "status": donation.status,
                }
            )

        return ResponseFactory.success(
            message="Member details retrieved successfully",
            data={
                "member": {
                    "id": member.id,
                    "first_name": member.first_name,
                    "last_name": member.last_name,
                    "email": member.email,
                    "phone": member.phone,
                    "is_email_verified": member.is_email_verified,
                    "is_phone_verified": member.is_phone_verified,
                    "created_at": member.created_at,
                    "updated_at": member.updated_at,
                },
                "donation_stats": {
                    "total_donated": float(total_donated),
                    "donation_count": donation_count,
                    "average_donation": round(avg_donation, 2),
                },
                "recent_donations": recent_donations_data,
            },
        )

    except HTTPException:
        raise
    except Exception as e:

        raise HTTPException(status_code=500, detail="Failed to get member details")


def get_member_giving_history(
    member_id: int,
    church_id: int,
    page: int = 1,
    limit: int = 20,
    db: Optional[Session] = None,
):
    """Get member's giving history"""
    if db is None:
        raise HTTPException(status_code=500, detail="Database session required")
    try:
        church = db.query(Church).filter(Church.id == church_id).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")

        member = (
            db.query(User)
            .filter(User.id == member_id, User.church_id == church_id)
            .first()
        )

        if not member:
            raise HTTPException(status_code=404, detail="Member not found")

        offset = (page - 1) * limit

        donations = (
            db.query(DonationBatch)
            .filter(
                DonationBatch.user_id == member_id,
                DonationBatch.church_id == church_id,
                DonationBatch.status == "completed",
            )
            .order_by(DonationBatch.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        total_count = (
            db.query(func.count(DonationBatch.id))
            .filter(
                DonationBatch.user_id == member_id,
                DonationBatch.church_id == church_id,
                DonationBatch.status == "completed",
            )
            .scalar()
        )

        donations_data = []
        for donation in donations:
            donations_data.append(
                {
                    "id": donation.id,
                    "amount": float(donation.total_amount),
                    "created_at": donation.created_at,
                    "status": donation.status,
                }
            )

        return ResponseFactory.success(
            message="Member giving history retrieved successfully",
            data={
                "donations": donations_data,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total_count": total_count,
                    "total_pages": (total_count + limit - 1) // limit,
                },
            },
        )

    except HTTPException:
        raise
    except Exception as e:

        raise HTTPException(status_code=500, detail="Failed to get giving history")


def search_members(
    church_id: int,
    search_term: str,
    page: int = 1,
    limit: int = 20,
    anonymized: bool = True,
    db: Optional[Session] = None,
):
    """Search church members with optional anonymization"""
    if db is None:
        raise HTTPException(status_code=500, detail="Database session required")
    try:
        church = db.query(Church).filter(Church.id == church_id).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")

        offset = (page - 1) * limit

        # Search members by name or email
        members = (
            db.query(User)
            .filter(
                User.church_id == church_id,
                (
                    User.first_name.ilike(f"%{search_term}%")
                    | User.last_name.ilike(f"%{search_term}%")
                    | User.email.ilike(f"%{search_term}%")
                ),
            )
            .order_by(User.first_name, User.last_name)
            .offset(offset)
            .limit(limit)
            .all()
        )

        total_count = (
            db.query(func.count(User.id))
            .filter(
                User.church_id == church_id,
                (
                    User.first_name.ilike(f"%{search_term}%")
                    | User.last_name.ilike(f"%{search_term}%")
                    | User.email.ilike(f"%{search_term}%")
                ),
            )
            .scalar()
        )

        members_data = []
        for member in members:
            # Get member's donation summary
            total_donated = (
                db.query(func.sum(DonationBatch.total_amount))
                .filter(
                    DonationBatch.user_id == member.id,
                    DonationBatch.church_id == church_id,
                    DonationBatch.status == "completed",
                )
                .scalar()
                or 0.0
            )

            donation_count = (
                db.query(func.count(DonationBatch.id))
                .filter(
                    DonationBatch.user_id == member.id,
                    DonationBatch.church_id == church_id,
                    DonationBatch.status == "completed",
                )
                .scalar()
                or 0
            )

            if anonymized:
                # Anonymized data for general church admin viewing
                members_data.append(
                    {
                        "id": f"donor_{member.id}",  # Anonymized ID
                        "donor_id": member.id,  # Keep for internal reference
                        "name": f"{member.first_name[0]}{'*' * (len(member.first_name) - 1)} {member.last_name[0]}{'*' * (len(member.last_name) - 1)}",  # Anonymized name
                        "email": f"{member.email.split('@')[0][:2]}{'*' * (len(member.email.split('@')[0]) - 2)}@{member.email.split('@')[1]}" if member.email else None,  # Anonymized email
                        "phone": f"***-***-{member.phone[-4:]}" if member.phone else None,  # Anonymized phone
                        "is_email_verified": member.is_email_verified,
                        "is_phone_verified": member.is_phone_verified,
                        "joined_date": member.created_at.strftime("%Y-%m") if member.created_at else None,  # Only month/year
                        "total_donated": float(total_donated),
                        "donation_count": donation_count,
                        "donation_frequency": "Regular" if donation_count > 5 else "Occasional" if donation_count > 0 else "New",
                    }
                )
            else:
                # Detailed data for support/troubleshooting purposes
                members_data.append(
                    {
                        "id": member.id,
                        "first_name": member.first_name,
                        "last_name": member.last_name,
                        "email": member.email,
                        "phone": member.phone,
                        "is_email_verified": member.is_email_verified,
                        "is_phone_verified": member.is_phone_verified,
                        "created_at": member.created_at,
                        "total_donated": float(total_donated),
                        "donation_count": donation_count,
                    }
                )

        return ResponseFactory.success(
            message="Member search completed successfully",
            data={
                "members": members_data,
                "search_term": search_term,
                "view_type": "anonymized" if anonymized else "detailed",
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total_count": total_count,
                    "total_pages": (total_count + limit - 1) // limit,
                },
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to search members")


def update_member_status(
    member_id: int,
    church_id: int,
    status: str,
    admin_id: int,
    notes: Optional[str] = None,
    db: Optional[Session] = None,
):
    """Update member status (active/inactive/blocked)"""
    if db is None:
        raise HTTPException(status_code=500, detail="Database session required")
    try:
        church = db.query(Church).filter(Church.id == church_id).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")

        member = (
            db.query(User)
            .filter(User.id == member_id, User.church_id == church_id)
            .first()
        )

        if not member:
            raise HTTPException(status_code=404, detail="Member not found")

        valid_statuses = ["active", "inactive", "blocked"]
        if status not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {valid_statuses}",
            )

        old_status = "active" if member.is_active else "inactive"

        if status == "active":
            member.is_active = True
        elif status == "inactive":
            member.is_active = False
        elif status == "blocked":
            member.is_active = False

        member.updated_at = datetime.now(timezone.utc)

        audit_log = AuditLog(
            actor_type="church_admin",
            actor_id=admin_id,
            church_id=church_id,
            action="MEMBER_STATUS_UPDATED",
            details_json={
                "member_id": member_id,
                "member_email": member.email,
                "old_status": old_status,
                "new_status": status,
                "notes": notes,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        db.add(audit_log)
        db.commit()

        return ResponseFactory.success(
            message=f"Member status updated to {status}",
            data={
                "member_id": member.id,
                "email": member.email,
                "name": f"{member.first_name} {member.last_name}",
                "status": status,
                "is_active": member.is_active,
                "updated_at": member.updated_at.isoformat(),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to update member status")


def add_member_note(
    member_id: int,
    church_id: int,
    note: str,
    admin_id: int,
    db: Optional[Session] = None,
):
    """Add a note about a member"""
    if db is None:
        raise HTTPException(status_code=500, detail="Database session required")
    try:
        church = db.query(Church).filter(Church.id == church_id).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")

        member = (
            db.query(User)
            .filter(User.id == member_id, User.church_id == church_id)
            .first()
        )

        if not member:
            raise HTTPException(status_code=404, detail="Member not found")

        audit_log = AuditLog(
            actor_type="church_admin",
            actor_id=admin_id,
            church_id=church_id,
            action="MEMBER_NOTE_ADDED",
            details_json={
                "member_id": member_id,
                "member_email": member.email,
                "note": note,
                "added_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        db.add(audit_log)
        db.commit()

        return ResponseFactory.success(
            message="Note added successfully",
            data={
                "member_id": member.id,
                "note": note,
                "added_at": datetime.now(timezone.utc).isoformat(),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to add member note")


def get_member_notes(member_id: int, church_id: int, db: Optional[Session] = None):
    """Get all notes for a member"""
    if db is None:
        raise HTTPException(status_code=500, detail="Database session required")
    try:
        church = db.query(Church).filter(Church.id == church_id).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")

        member = (
            db.query(User)
            .filter(User.id == member_id, User.church_id == church_id)
            .first()
        )

        if not member:
            raise HTTPException(status_code=404, detail="Member not found")

        notes = (
            db.query(AuditLog)
            .filter(
                AuditLog.church_id == church_id,
                AuditLog.action == "MEMBER_NOTE_ADDED",
                AuditLog.details_json.contains({"member_id": member_id}),
            )
            .order_by(AuditLog.created_at.desc())
            .all()
        )

        notes_data = []
        for note in notes:
            try:
                details = (
                    note.details_json if isinstance(note.details_json, dict) else {}
                )
                notes_data.append(
                    {
                        "id": note.id,
                        "note": details.get("note", ""),
                        "added_at": note.created_at.isoformat(),
                        "added_by": note.actor_id,
                    }
                )
            except Exception:
                continue

        return ResponseFactory.success(
            message="Member notes retrieved successfully",
            data={
                "member_id": member.id,
                "notes": notes_data,
                "total_notes": len(notes_data),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get member notes")


def export_members(
    church_id: int, format_type: str = "csv", db: Optional[Session] = None
):
    """Export church members data"""
    if db is None:
        raise HTTPException(status_code=500, detail="Database session required")
    try:
        church = db.query(Church).filter(Church.id == church_id).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")

        if format_type not in ["csv", "json"]:
            raise HTTPException(
                status_code=400, detail="Format must be 'csv' or 'json'"
            )

        members = db.query(User).filter(User.church_id == church_id).all()

        export_data = []
        for member in members:
            total_donated = (
                db.query(func.sum(DonationBatch.total_amount))
                .filter(
                    DonationBatch.user_id == member.id,
                    DonationBatch.church_id == church_id,
                    DonationBatch.status == "completed",
                )
                .scalar()
                or 0.0
            )

            donation_count = (
                db.query(func.count(DonationBatch.id))
                .filter(
                    DonationBatch.user_id == member.id,
                    DonationBatch.church_id == church_id,
                    DonationBatch.status == "completed",
                )
                .scalar()
                or 0
            )

            export_data.append(
                {
                    "id": member.id,
                    "first_name": member.first_name,
                    "last_name": member.last_name,
                    "email": member.email,
                    "phone": member.phone,
                    "is_active": member.is_active,
                    "total_donated": float(total_donated),
                    "donation_count": donation_count,
                    "joined_date": (
                        member.created_at.strftime("%Y-%m-%d")
                        if member.created_at
                        else ""
                    ),
                    "last_donation": None,
                }
            )

        return ResponseFactory.success(
            message=f"Members exported in {format_type} format",
            data={
                "format": format_type,
                "total_members": len(export_data),
                "members": export_data,
                "exported_at": datetime.now(timezone.utc).isoformat(),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to export members")
