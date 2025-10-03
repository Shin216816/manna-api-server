"""
Enhanced Church Management Controller

Provides advanced church management functionality:
- Bulk operations (approve/reject multiple churches)
- Advanced filtering and search
- Church performance metrics
- Communication tools
- Workflow management
"""

from fastapi import HTTPException
import logging
import traceback
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

from app.model.m_church import Church
from app.model.m_church_admin import ChurchAdmin
from app.model.m_user import User
from app.model.m_donation_batch import DonationBatch
from app.model.m_donation_preference import DonationPreference
from app.core.responses import ResponseFactory


class BulkChurchActionRequest(BaseModel):
    church_ids: List[int]
    action: str  # 'approve', 'reject', 'activate', 'deactivate', 'send_communication'
    notes: Optional[str] = None
    reason: Optional[str] = None


class ChurchSearchRequest(BaseModel):
    search_term: Optional[str] = None
    status_filter: Optional[str] = None
    kyc_status_filter: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    revenue_min: Optional[float] = None
    revenue_max: Optional[float] = None
    member_count_min: Optional[int] = None
    member_count_max: Optional[int] = None
    sort_by: Optional[str] = "created_at"
    sort_order: Optional[str] = "desc"
    page: int = 1
    limit: int = 20


def get_enhanced_church_list(
    search_request: ChurchSearchRequest,
    db: Optional[Session] = None,
):
    """Get enhanced church list with advanced filtering and search"""
    try:
        if db is None:
            raise HTTPException(status_code=500, detail="Database session required")

        # Build base query
        query = db.query(Church)

        # Apply filters
        if search_request.search_term:
            search_filter = f"%{search_request.search_term}%"
            query = query.filter(
                or_(
                    Church.name.ilike(search_filter),
                    Church.email.ilike(search_filter),
                    Church.phone.ilike(search_filter),
                    Church.city.ilike(search_filter),
                    Church.state.ilike(search_filter)
                )
            )

        if search_request.status_filter and search_request.status_filter != "all":
            query = query.filter(Church.status == search_request.status_filter)

        if search_request.kyc_status_filter and search_request.kyc_status_filter != "all":
            query = query.filter(Church.kyc_status == search_request.kyc_status_filter)

        if search_request.date_from:
            date_from = parse_date(search_request.date_from)
            query = query.filter(Church.created_at >= date_from)

        if search_request.date_to:
            date_to = parse_date(search_request.date_to)
            query = query.filter(Church.created_at <= date_to)

        # Apply sorting
        if search_request.sort_by == "name":
            sort_column = Church.name
        elif search_request.sort_by == "created_at":
            sort_column = Church.created_at
        elif search_request.sort_by == "status":
            sort_column = Church.status
        elif search_request.sort_by == "kyc_status":
            sort_column = Church.kyc_status
        else:
            sort_column = Church.created_at

        if search_request.sort_order == "asc":
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (search_request.page - 1) * search_request.limit
        churches = query.offset(offset).limit(search_request.limit).all()

        # Build enhanced church data
        churches_data = []
        for church in churches:
            # Get church admin
            admin = db.query(ChurchAdmin).filter(ChurchAdmin.church_id == church.id).first()
            admin_user = None
            if admin:
                admin_user = db.query(User).filter(User.id == admin.user_id).first()

            # Get member count
            member_count = db.query(func.count(User.id)).filter(User.church_id == church.id).scalar()

            # Get revenue metrics
            total_revenue = db.query(func.sum(DonationBatch.amount)).filter(
                DonationBatch.church_id == church.id,
                DonationBatch.status == "completed"
            ).scalar() or 0.0

            # Get this month's revenue
            current_month = datetime.now(timezone.utc).replace(
                day=1, hour=0, minute=0, second=0, microsecond=0
            )
            this_month_revenue = db.query(func.sum(DonationBatch.amount)).filter(
                DonationBatch.church_id == church.id,
                DonationBatch.status == "completed",
                DonationBatch.created_at >= current_month
            ).scalar() or 0.0

            # Get active donors
            active_donors = db.query(func.count(User.id.distinct())).join(DonationPreference, User.id == DonationPreference.user_id).filter(
                User.church_id == church.id,
                DonationPreference.pause == False
            ).scalar()

            # Get donation count
            donation_count = db.query(func.count(DonationBatch.id)).filter(
                DonationBatch.church_id == church.id,
                DonationBatch.status == "completed"
            ).scalar()

            # Calculate performance score (0-100)
            performance_score = calculate_church_performance_score(
                total_revenue, donation_count, member_count, active_donors
            )

            churches_data.append({
                "id": church.id,
                "name": church.name,
                "email": church.email,
                "phone": church.phone,
                "website": church.website,
                "address": church.address,
                "city": church.city,
                "state": church.state,
                "zip_code": church.zip_code,
                "status": church.status,
                "is_active": church.is_active,
                "kyc_status": church.kyc_status,
                "stripe_account_id": church.stripe_account_id,
                "referral_code": church.referral_code,
                "created_at": church.created_at.isoformat() if church.created_at else None,
                "updated_at": church.updated_at.isoformat() if church.updated_at else None,
                "admin": {
                    "id": admin.id if admin else None,
                    "email": admin_user.email if admin_user else None,
                    "name": f"{admin_user.first_name} {admin_user.last_name}" if admin_user else None,
                },
                "metrics": {
                    "member_count": member_count,
                    "active_donors": active_donors,
                    "total_revenue": round(float(total_revenue), 2),
                    "this_month_revenue": round(float(this_month_revenue), 2),
                    "donation_count": donation_count,
                    "performance_score": performance_score,
                },
            })

        # Apply revenue filters after data collection
        if search_request.revenue_min is not None:
            churches_data = [c for c in churches_data if c["metrics"]["total_revenue"] >= search_request.revenue_min]
        
        if search_request.revenue_max is not None:
            churches_data = [c for c in churches_data if c["metrics"]["total_revenue"] <= search_request.revenue_max]

        if search_request.member_count_min is not None:
            churches_data = [c for c in churches_data if c["metrics"]["member_count"] >= search_request.member_count_min]
        
        if search_request.member_count_max is not None:
            churches_data = [c for c in churches_data if c["metrics"]["member_count"] <= search_request.member_count_max]

        return ResponseFactory.success(
            message="Enhanced church list retrieved successfully",
            data={
                "churches": churches_data,
                "pagination": {
                    "page": search_request.page,
                    "limit": search_request.limit,
                    "total": len(churches_data),  # After filtering
                    "pages": (len(churches_data) + search_request.limit - 1) // search_request.limit,
                },
                "filters_applied": {
                    "search_term": search_request.search_term,
                    "status_filter": search_request.status_filter,
                    "kyc_status_filter": search_request.kyc_status_filter,
                    "date_from": search_request.date_from,
                    "date_to": search_request.date_to,
                    "revenue_min": search_request.revenue_min,
                    "revenue_max": search_request.revenue_max,
                    "member_count_min": search_request.member_count_min,
                    "member_count_max": search_request.member_count_max,
                },
            },
        )

    except Exception as e:
        logging.error(f"Error getting enhanced church list: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve enhanced church list")


def bulk_church_action(
    action_request: BulkChurchActionRequest,
    db: Optional[Session] = None,
):
    """Perform bulk actions on multiple churches"""
    try:
        if db is None:
            raise HTTPException(status_code=500, detail="Database session required")

        if not action_request.church_ids:
            raise HTTPException(status_code=400, detail="No church IDs provided")

        # Validate church IDs exist
        existing_churches = db.query(Church).filter(Church.id.in_(action_request.church_ids)).all()
        existing_ids = [c.id for c in existing_churches]
        missing_ids = [id for id in action_request.church_ids if id not in existing_ids]

        if missing_ids:
            raise HTTPException(
                status_code=400, 
                detail=f"Churches not found: {missing_ids}"
            )

        results = []
        now = datetime.now(timezone.utc)

        for church in existing_churches:
            try:
                if action_request.action == "approve":
                    church.kyc_status = "approved"
                    church.status = "active"
                    church.is_active = True
                    church.updated_at = now
                    result = "approved"

                elif action_request.action == "reject":
                    church.kyc_status = "rejected"
                    church.updated_at = now
                    result = "rejected"

                elif action_request.action == "activate":
                    church.is_active = True
                    church.updated_at = now
                    result = "activated"

                elif action_request.action == "deactivate":
                    church.is_active = False
                    church.updated_at = now
                    result = "deactivated"

                else:
                    result = "unknown_action"

                results.append({
                    "church_id": church.id,
                    "church_name": church.name,
                    "action": action_request.action,
                    "result": result,
                    "success": result != "unknown_action"
                })

            except Exception as e:
                results.append({
                    "church_id": church.id,
                    "church_name": church.name,
                    "action": action_request.action,
                    "result": "error",
                    "error": str(e),
                    "success": False
                })

        # Commit changes
        db.commit()

        # Log the bulk action
        log_bulk_action(action_request, results, db)

        return ResponseFactory.success(
            message=f"Bulk {action_request.action} action completed",
            data={
                "action": action_request.action,
                "total_churches": len(action_request.church_ids),
                "successful": len([r for r in results if r["success"]]),
                "failed": len([r for r in results if not r["success"]]),
                "results": results,
            },
        )

    except Exception as e:
        logging.error(f"Error performing bulk church action: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to perform bulk church action")


def get_church_performance_metrics(
    church_id: int,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Optional[Session] = None,
):
    """Get comprehensive church performance metrics"""
    try:
        if db is None:
            raise HTTPException(status_code=500, detail="Database session required")

        church = db.query(Church).filter(Church.id == church_id).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")

        start_dt = parse_date(start_date) if start_date else None
        end_dt = parse_date(end_date) if end_date else None

        # Revenue metrics
        revenue_query = db.query(DonationBatch).filter(
            DonationBatch.church_id == church_id,
            DonationBatch.status == "completed"
        )

        if start_dt:
            revenue_query = revenue_query.filter(DonationBatch.created_at >= start_dt)
        if end_dt:
            revenue_query = revenue_query.filter(DonationBatch.created_at <= end_dt)

        donations = revenue_query.all()
        total_revenue = sum(float(d.amount) for d in donations)
        avg_donation = total_revenue / len(donations) if donations else 0

        # Member metrics
        total_members = db.query(func.count(User.id)).filter(User.church_id == church_id).scalar()
        active_donors = db.query(func.count(User.id.distinct())).join(DonationPreference, User.id == DonationPreference.user_id).filter(
            User.church_id == church_id,
            DonationPreference.pause == False
        ).scalar()

        # Growth metrics
        current_month = datetime.now(timezone.utc).replace(day=1)
        last_month = (current_month - timedelta(days=1)).replace(day=1)
        
        this_month_revenue = db.query(func.sum(DonationBatch.amount)).filter(
            DonationBatch.church_id == church_id,
            DonationBatch.status == "completed",
            DonationBatch.created_at >= current_month
        ).scalar() or 0.0

        last_month_revenue = db.query(func.sum(DonationBatch.amount)).filter(
            DonationBatch.church_id == church_id,
            DonationBatch.status == "completed",
            DonationBatch.created_at >= last_month,
            DonationBatch.created_at < current_month
        ).scalar() or 0.0

        revenue_growth = calculate_growth_rate(this_month_revenue, last_month_revenue)

        # Engagement metrics
        recent_activity = db.query(func.count(DonationBatch.id)).filter(
            DonationBatch.church_id == church_id,
            DonationBatch.status == "completed",
            DonationBatch.created_at >= datetime.now(timezone.utc) - timedelta(days=7)
        ).scalar()

        # Performance score
        performance_score = calculate_church_performance_score(
            total_revenue, len(donations), total_members, active_donors
        )

        return ResponseFactory.success(
            message="Church performance metrics retrieved successfully",
            data={
                "church_id": church_id,
                "church_name": church.name,
                "revenue_metrics": {
                    "total_revenue": round(float(total_revenue), 2),
                    "average_donation": round(float(avg_donation), 2),
                    "donation_count": len(donations),
                    "this_month_revenue": round(float(this_month_revenue), 2),
                    "revenue_growth": round(revenue_growth, 2),
                },
                "member_metrics": {
                    "total_members": total_members,
                    "active_donors": active_donors,
                    "donor_engagement_rate": round((active_donors / total_members * 100) if total_members > 0 else 0, 2),
                },
                "engagement_metrics": {
                    "recent_activity": recent_activity,
                    "performance_score": performance_score,
                },
                "date_range": {
                    "start_date": start_date,
                    "end_date": end_date,
                },
            },
        )

    except Exception as e:
        logging.error(f"Error getting church performance metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve church performance metrics")


def send_church_communication(
    church_id: int,
    communication_type: str,
    subject: str,
    message: str,
    db: Optional[Session] = None,
):
    """Send communication to church"""
    try:
        if db is None:
            raise HTTPException(status_code=500, detail="Database session required")

        church = db.query(Church).filter(Church.id == church_id).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")

        # Get church admin for communication
        admin = db.query(ChurchAdmin).filter(ChurchAdmin.church_id == church_id).first()
        if not admin:
            raise HTTPException(status_code=400, detail="Church admin not found")
        
        # Get the user associated with the admin
        admin_user = db.query(User).filter(User.id == admin.user_id).first()
        if not admin_user:
            raise HTTPException(status_code=400, detail="Church admin user not found")

        # Log communication (placeholder - would integrate with email service)
        communication_log = {
            "church_id": church_id,
            "church_name": church.name,
            "admin_email": admin_user.email,
            "communication_type": communication_type,
            "subject": subject,
            "message": message,
            "sent_at": datetime.now(timezone.utc).isoformat(),
            "status": "sent"  # Would be updated based on actual sending
        }

        # TODO: Integrate with actual email service
        # send_email(admin_user.email, subject, message)

        return ResponseFactory.success(
            message="Communication sent successfully",
            data=communication_log,
        )

    except Exception as e:
        logging.error(f"Error sending church communication: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to send communication")


def calculate_church_performance_score(
    total_revenue: float,
    donation_count: int,
    member_count: int,
    active_donors: int
) -> int:
    """Calculate church performance score (0-100)"""
    score = 0

    # Revenue score (40 points max)
    if total_revenue > 10000:
        score += 40
    elif total_revenue > 5000:
        score += 30
    elif total_revenue > 1000:
        score += 20
    elif total_revenue > 100:
        score += 10

    # Activity score (30 points max)
    if donation_count > 100:
        score += 30
    elif donation_count > 50:
        score += 20
    elif donation_count > 10:
        score += 10
    elif donation_count > 0:
        score += 5

    # Engagement score (30 points max)
    if member_count > 0:
        engagement_rate = active_donors / member_count
        if engagement_rate > 0.5:
            score += 30
        elif engagement_rate > 0.3:
            score += 20
        elif engagement_rate > 0.1:
            score += 10
        elif engagement_rate > 0:
            score += 5

    return min(score, 100)


def log_bulk_action(
    action_request: BulkChurchActionRequest,
    results: List[Dict[str, Any]],
    db: Session,
):
    """Log bulk action for audit purposes"""
    # TODO: Implement proper audit logging
    logging.info(f"Bulk action performed: {action_request.action} on {len(action_request.church_ids)} churches")


def parse_date(date_str: str) -> datetime:
    """Parse date string to datetime object"""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")


def calculate_growth_rate(current: float, previous: float) -> float:
    """Calculate growth rate percentage"""
    if previous == 0:
        return 100.0 if current > 0 else 0.0
    return ((current - previous) / previous) * 100
