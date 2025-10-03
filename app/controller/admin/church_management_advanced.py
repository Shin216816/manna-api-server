"""
Advanced Church Management Controller

Comprehensive church management system for handling all church-related activities:
- Church onboarding and setup
- Profile and settings management
- Member management and analytics
- Communication tools
- Event and calendar management
- Donation campaign management
- Document and compliance management
- Integration management
- Reporting and analytics
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc, asc
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
import logging

from app.model.m_church import Church
from app.model.m_church_admin import ChurchAdmin
from app.model.m_user import User
from app.model.m_donation_batch import DonationBatch
from app.model.m_donation_preference import DonationPreference
from app.model.m_church_message import ChurchMessage
from app.model.m_audit_log import AuditLog
from app.core.responses import ResponseFactory
from app.core.admin_monitoring import admin_monitor, monitor_admin_endpoint, handle_admin_exception
from app.utils.email_service import EmailService
from app.utils.notification_service import NotificationService

logger = logging.getLogger(__name__)


class ChurchOnboardingManager:
    """Manages church onboarding process"""

    @staticmethod
    @monitor_admin_endpoint("church_onboarding_start")
    async def start_onboarding(church_id: int, admin_id: int, db: Session) -> dict:
        """Initialize church onboarding process"""
        try:
            church = db.query(Church).filter(Church.id == church_id).first()
            if not church:
                raise HTTPException(status_code=404, detail="Church not found")

            # Create onboarding checklist
            checklist_items = [
                {"id": "basic_info", "name": "Basic Information", "completed": bool(church.name and church.email)},
                {"id": "contact_details", "name": "Contact Details", "completed": bool(church.phone and church.address)},
                {"id": "banking_info", "name": "Banking Information", "completed": church.stripe_account_id is not None},
                {"id": "kyc_documents", "name": "KYC Documents", "completed": church.kyc_status == "approved"},
                {"id": "admin_setup", "name": "Admin Setup", "completed": db.query(ChurchAdmin).filter_by(church_id=church_id).count() > 0},
                {"id": "donation_setup", "name": "Donation Setup", "completed": church.donation_enabled},
                {"id": "profile_completion", "name": "Profile Completion", "completed": bool(church.description and church.website)},
                {"id": "test_donation", "name": "Test Donation", "completed": False}  # To be implemented
            ]

            completion_rate = sum(1 for item in checklist_items if item["completed"]) / len(checklist_items) * 100

            return ResponseFactory.success(
                message="Onboarding status retrieved successfully",
                data={
                    "church_id": church_id,
                    "onboarding_status": "in_progress" if completion_rate < 100 else "completed",
                    "completion_rate": round(completion_rate, 1),
                    "checklist": checklist_items,
                    "next_steps": ChurchOnboardingManager._get_next_steps(checklist_items),
                    "estimated_time_remaining": ChurchOnboardingManager._estimate_completion_time(checklist_items)
                }
            )

        except Exception as e:
            raise handle_admin_exception(e, "church_onboarding_start", admin_id)

    @staticmethod
    def _get_next_steps(checklist_items: List[dict]) -> List[dict]:
        """Get recommended next steps for onboarding"""
        incomplete_items = [item for item in checklist_items if not item["completed"]]

        # Priority order for completion
        priority_order = ["basic_info", "contact_details", "admin_setup", "kyc_documents",
                         "banking_info", "donation_setup", "profile_completion", "test_donation"]

        next_steps = []
        for priority in priority_order:
            for item in incomplete_items:
                if item["id"] == priority:
                    next_steps.append({
                        "id": item["id"],
                        "name": item["name"],
                        "description": ChurchOnboardingManager._get_step_description(item["id"]),
                        "estimated_time": ChurchOnboardingManager._get_step_time(item["id"])
                    })
                    break
            if len(next_steps) >= 3:  # Limit to next 3 steps
                break

        return next_steps

    @staticmethod
    def _get_step_description(step_id: str) -> str:
        """Get description for onboarding step"""
        descriptions = {
            "basic_info": "Complete church name, email, and basic information",
            "contact_details": "Add phone number, address, and contact information",
            "admin_setup": "Add church administrators and assign roles",
            "kyc_documents": "Submit and complete KYC verification documents",
            "banking_info": "Set up Stripe account for donation processing",
            "donation_setup": "Configure donation settings and preferences",
            "profile_completion": "Add church description, website, and additional details",
            "test_donation": "Process a test donation to verify setup"
        }
        return descriptions.get(step_id, "Complete this step")

    @staticmethod
    def _get_step_time(step_id: str) -> str:
        """Get estimated time for onboarding step"""
        times = {
            "basic_info": "5 minutes",
            "contact_details": "3 minutes",
            "admin_setup": "10 minutes",
            "kyc_documents": "15 minutes",
            "banking_info": "20 minutes",
            "donation_setup": "10 minutes",
            "profile_completion": "15 minutes",
            "test_donation": "5 minutes"
        }
        return times.get(step_id, "10 minutes")

    @staticmethod
    def _estimate_completion_time(checklist_items: List[dict]) -> str:
        """Estimate total completion time"""
        incomplete_count = sum(1 for item in checklist_items if not item["completed"])

        if incomplete_count == 0:
            return "Completed"
        elif incomplete_count <= 2:
            return "15-30 minutes"
        elif incomplete_count <= 4:
            return "30-60 minutes"
        else:
            return "1-2 hours"


class ChurchProfileManager:
    """Manages church profile and settings"""

    @staticmethod
    @monitor_admin_endpoint("update_church_profile")
    async def update_profile(church_id: int, profile_data: dict, admin_id: int, db: Session) -> dict:
        """Update church profile information"""
        try:
            church = db.query(Church).filter(Church.id == church_id).first()
            if not church:
                raise HTTPException(status_code=404, detail="Church not found")

            # Store old values for audit
            old_values = {
                "name": church.name,
                "description": church.description,
                "website": church.website,
                "phone": church.phone,
                "address": church.address
            }

            # Update fields
            updatable_fields = ["name", "description", "website", "phone", "address",
                              "service_times", "denomination", "founding_year"]

            for field in updatable_fields:
                if field in profile_data:
                    setattr(church, field, profile_data[field])

            church.updated_at = datetime.now(timezone.utc)
            db.commit()

            # Log the update
            AuditLog.create_log(
                db=db,
                user_id=admin_id,
                action="update_church_profile",
                resource_type="church",
                resource_id=church_id,
                old_values=old_values,
                new_values=profile_data
            )

            return ResponseFactory.success(
                message="Church profile updated successfully",
                data=ChurchProfileManager._serialize_church_profile(church)
            )

        except Exception as e:
            raise handle_admin_exception(e, "update_church_profile", admin_id)

    @staticmethod
    def _serialize_church_profile(church: Church) -> dict:
        """Serialize church profile for API response"""
        return {
            "id": church.id,
            "name": church.name,
            "description": church.description,
            "email": church.email,
            "phone": church.phone,
            "website": church.website,
            "address": church.address,
            "service_times": church.service_times,
            "denomination": church.denomination,
            "founding_year": church.founding_year,
            "status": church.status,
            "is_active": church.is_active,
            "kyc_status": church.kyc_status,
            "donation_enabled": church.donation_enabled,
            "created_at": church.created_at.isoformat() if church.created_at else None,
            "updated_at": church.updated_at.isoformat() if church.updated_at else None
        }


class ChurchMemberManager:
    """Manages church members and analytics"""

    @staticmethod
    @monitor_admin_endpoint("get_church_members_advanced")
    async def get_members_with_analytics(
        church_id: int,
        admin_id: int,
        db: Session,
        page: int = 1,
        limit: int = 20,
        search: str = "",
        sort_by: str = "created_at",
        sort_order: str = "desc",
        status_filter: str = "all",
        donation_status: str = "all"
    ) -> dict:
        """Get church members with detailed analytics"""
        try:
            # Base query
            query = db.query(User).filter(User.church_id == church_id)

            # Apply filters
            if search:
                search_term = f"%{search}%"
                query = query.filter(
                    or_(
                        User.first_name.ilike(search_term),
                        User.last_name.ilike(search_term),
                        User.email.ilike(search_term)
                    )
                )

            if status_filter != "all":
                if status_filter == "active":
                    query = query.filter(User.is_active == True)
                elif status_filter == "inactive":
                    query = query.filter(User.is_active == False)

            # Donation status filter
            if donation_status == "active":
                query = query.join(DonationPreference).filter(DonationPreference.pause == False)
            elif donation_status == "paused":
                query = query.join(DonationPreference).filter(DonationPreference.pause == True)
            elif donation_status == "no_donations":
                query = query.outerjoin(DonationPreference).filter(DonationPreference.id == None)

            # Sorting
            sort_column = getattr(User, sort_by, User.created_at)
            if sort_order.lower() == "desc":
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(asc(sort_column))

            # Pagination
            total = query.count()
            offset = (page - 1) * limit
            members = query.offset(offset).limit(limit).all()

            # Get member analytics
            members_data = []
            for member in members:
                member_analytics = await ChurchMemberManager._get_member_analytics(member.id, db)
                members_data.append({
                    **ChurchMemberManager._serialize_member(member),
                    "analytics": member_analytics
                })

            # Get overall member statistics
            member_stats = await ChurchMemberManager._get_member_statistics(church_id, db)

            return ResponseFactory.success(
                message="Church members retrieved successfully",
                data={
                    "members": members_data,
                    "pagination": {
                        "page": page,
                        "limit": limit,
                        "total": total,
                        "pages": (total + limit - 1) // limit if limit > 0 else 1
                    },
                    "statistics": member_stats,
                    "filters_applied": {
                        "search": search,
                        "status_filter": status_filter,
                        "donation_status": donation_status,
                        "sort_by": sort_by,
                        "sort_order": sort_order
                    }
                }
            )

        except Exception as e:
            raise handle_admin_exception(e, "get_church_members_advanced", admin_id)

    @staticmethod
    async def _get_member_analytics(user_id: int, db: Session) -> dict:
        """Get analytics for a specific member"""
        # Total donations
        total_donations = db.query(func.sum(DonationBatch.total_amount)).filter(
            DonationBatch.user_id == user_id,
            DonationBatch.status == "completed"
        ).scalar() or 0

        # Donation count
        donation_count = db.query(func.count(DonationBatch.id)).filter(
            DonationBatch.user_id == user_id,
            DonationBatch.status == "completed"
        ).scalar() or 0

        # Average donation
        avg_donation = total_donations / donation_count if donation_count > 0 else 0

        # Last donation date
        last_donation = db.query(DonationBatch.created_at).filter(
            DonationBatch.user_id == user_id,
            DonationBatch.status == "completed"
        ).order_by(desc(DonationBatch.created_at)).first()

        # Current donation preference
        donation_pref = db.query(DonationPreference).filter_by(user_id=user_id).first()

        return {
            "total_donations": round(float(total_donations), 2),
            "donation_count": donation_count,
            "average_donation": round(float(avg_donation), 2),
            "last_donation_date": last_donation[0].isoformat() if last_donation else None,
            "has_active_donation": donation_pref is not None and not donation_pref.pause,
            "donation_frequency": donation_pref.frequency if donation_pref else None,
            "monthly_amount": float(donation_pref.amount) if donation_pref else 0
        }

    @staticmethod
    async def _get_member_statistics(church_id: int, db: Session) -> dict:
        """Get overall member statistics for the church"""
        # Total members
        total_members = db.query(func.count(User.id)).filter(User.church_id == church_id).scalar()

        # Active members
        active_members = db.query(func.count(User.id)).filter(
            User.church_id == church_id,
            User.is_active == True
        ).scalar()

        # Members with donations
        donors = db.query(func.count(func.distinct(User.id))).join(DonationPreference).filter(
            User.church_id == church_id
        ).scalar()

        # Active donors
        active_donors = db.query(func.count(func.distinct(User.id))).join(DonationPreference).filter(
            User.church_id == church_id,
            DonationPreference.pause == False
        ).scalar()

        # New members this month
        current_month = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        new_members_this_month = db.query(func.count(User.id)).filter(
            User.church_id == church_id,
            User.created_at >= current_month
        ).scalar()

        return {
            "total_members": total_members,
            "active_members": active_members,
            "inactive_members": total_members - active_members,
            "total_donors": donors,
            "active_donors": active_donors,
            "donor_conversion_rate": round((donors / total_members * 100) if total_members > 0 else 0, 1),
            "active_donor_rate": round((active_donors / total_members * 100) if total_members > 0 else 0, 1),
            "new_members_this_month": new_members_this_month
        }

    @staticmethod
    def _serialize_member(user: User) -> dict:
        """Serialize member data"""
        return {
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "phone": user.phone,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_login": user.last_login.isoformat() if user.last_login else None
        }


class ChurchCommunicationManager:
    """Manages church communication and messaging"""

    @staticmethod
    @monitor_admin_endpoint("send_church_message")
    async def send_message_to_members(
        church_id: int,
        admin_id: int,
        message_data: dict,
        db: Session
    ) -> dict:
        """Send message to church members"""
        try:
            # Validate church
            church = db.query(Church).filter(Church.id == church_id).first()
            if not church:
                raise HTTPException(status_code=404, detail="Church not found")

            # Get target members
            target_query = db.query(User).filter(User.church_id == church_id)

            # Apply filters if specified
            if message_data.get("target_filter") == "active_donors":
                target_query = target_query.join(DonationPreference).filter(
                    DonationPreference.pause == False
                )
            elif message_data.get("target_filter") == "inactive_members":
                target_query = target_query.filter(User.is_active == False)

            target_members = target_query.all()

            if not target_members:
                raise HTTPException(status_code=400, detail="No members found matching criteria")

            # Create message record
            church_message = ChurchMessage(
                church_id=church_id,
                sender_id=admin_id,
                title=message_data["title"],
                content=message_data["content"],
                message_type=message_data.get("type", "announcement"),
                target_filter=message_data.get("target_filter", "all"),
                scheduled_at=message_data.get("scheduled_at"),
                created_at=datetime.now(timezone.utc)
            )

            db.add(church_message)
            db.flush()  # Get the ID

            # Send messages
            email_service = EmailService()
            notification_service = NotificationService()

            sent_count = 0
            failed_count = 0

            for member in target_members:
                try:
                    # Send email
                    if message_data.get("send_email", True):
                        email_service.send_church_message(
                            to_email=member.email,
                            church_name=church.name,
                            title=message_data["title"],
                            content=message_data["content"]
                        )

                    # Send push notification
                    if message_data.get("send_push", False):
                        notification_service.send_to_user(
                            user_id=member.id,
                            title=message_data["title"],
                            body=message_data["content"][:100] + "..." if len(message_data["content"]) > 100 else message_data["content"]
                        )

                    sent_count += 1

                except Exception as e:
                    logger.error(f"Failed to send message to member {member.id}: {e}")
                    failed_count += 1

            # Update message record
            church_message.sent_count = sent_count
            church_message.failed_count = failed_count
            church_message.status = "sent"

            db.commit()

            return ResponseFactory.success(
                message="Message sent successfully",
                data={
                    "message_id": church_message.id,
                    "sent_count": sent_count,
                    "failed_count": failed_count,
                    "target_members": len(target_members),
                    "success_rate": round((sent_count / len(target_members) * 100), 1) if target_members else 0
                }
            )

        except Exception as e:
            raise handle_admin_exception(e, "send_church_message", admin_id)

    @staticmethod
    @monitor_admin_endpoint("get_church_messages")
    async def get_message_history(
        church_id: int,
        admin_id: int,
        db: Session,
        page: int = 1,
        limit: int = 20
    ) -> dict:
        """Get church message history"""
        try:
            query = db.query(ChurchMessage).filter(ChurchMessage.church_id == church_id)

            total = query.count()
            offset = (page - 1) * limit
            messages = query.order_by(desc(ChurchMessage.created_at)).offset(offset).limit(limit).all()

            messages_data = [
                {
                    "id": msg.id,
                    "title": msg.title,
                    "content": msg.content,
                    "message_type": msg.message_type,
                    "target_filter": msg.target_filter,
                    "sent_count": msg.sent_count,
                    "failed_count": msg.failed_count,
                    "status": msg.status,
                    "created_at": msg.created_at.isoformat() if msg.created_at else None,
                    "sender": {
                        "id": msg.sender.id if msg.sender else None,
                        "email": msg.sender.email if msg.sender else None
                    }
                }
                for msg in messages
            ]

            return ResponseFactory.success(
                message="Message history retrieved successfully",
                data={
                    "messages": messages_data,
                    "pagination": {
                        "page": page,
                        "limit": limit,
                        "total": total,
                        "pages": (total + limit - 1) // limit if limit > 0 else 1
                    }
                }
            )

        except Exception as e:
            raise handle_admin_exception(e, "get_church_messages", admin_id)


class ChurchAnalyticsManager:
    """Advanced analytics for church management"""

    @staticmethod
    @monitor_admin_endpoint("get_church_analytics_advanced")
    async def get_comprehensive_analytics(
        church_id: int,
        admin_id: int,
        db: Session,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        include_predictions: bool = False
    ) -> dict:
        """Get comprehensive church analytics"""
        try:
            # Parse dates
            if start_date:
                start_dt = datetime.fromisoformat(start_date)
            else:
                start_dt = datetime.now(timezone.utc) - timedelta(days=90)  # Default 90 days

            if end_date:
                end_dt = datetime.fromisoformat(end_date)
            else:
                end_dt = datetime.now(timezone.utc)

            # Get various analytics
            donation_analytics = await ChurchAnalyticsManager._get_donation_analytics(church_id, start_dt, end_dt, db)
            member_analytics = await ChurchAnalyticsManager._get_member_growth_analytics(church_id, start_dt, end_dt, db)
            engagement_analytics = await ChurchAnalyticsManager._get_engagement_analytics(church_id, start_dt, end_dt, db)
            financial_analytics = await ChurchAnalyticsManager._get_financial_analytics(church_id, start_dt, end_dt, db)

            result_data = {
                "period": {
                    "start_date": start_dt.isoformat(),
                    "end_date": end_dt.isoformat(),
                    "days": (end_dt - start_dt).days
                },
                "donation_analytics": donation_analytics,
                "member_analytics": member_analytics,
                "engagement_analytics": engagement_analytics,
                "financial_analytics": financial_analytics
            }

            # Add predictions if requested
            if include_predictions:
                predictions = await ChurchAnalyticsManager._generate_predictions(church_id, db)
                result_data["predictions"] = predictions

            return ResponseFactory.success(
                message="Church analytics retrieved successfully",
                data=result_data
            )

        except Exception as e:
            raise handle_admin_exception(e, "get_church_analytics_advanced", admin_id)

    @staticmethod
    async def _get_donation_analytics(church_id: int, start_dt: datetime, end_dt: datetime, db: Session) -> dict:
        """Get donation analytics"""
        # Total donations in period
        total_donations = db.query(func.sum(DonationBatch.total_amount)).filter(
            DonationBatch.church_id == church_id,
            DonationBatch.status == "completed",
            DonationBatch.created_at >= start_dt,
            DonationBatch.created_at <= end_dt
        ).scalar() or 0

        # Donation count
        donation_count = db.query(func.count(DonationBatch.id)).filter(
            DonationBatch.church_id == church_id,
            DonationBatch.status == "completed",
            DonationBatch.created_at >= start_dt,
            DonationBatch.created_at <= end_dt
        ).scalar() or 0

        # Average donation
        avg_donation = total_donations / donation_count if donation_count > 0 else 0

        # Monthly breakdown
        monthly_data = db.query(
            func.date_trunc('month', DonationBatch.created_at).label('month'),
            func.sum(DonationBatch.total_amount).label('total'),
            func.count(DonationBatch.id).label('count')
        ).filter(
            DonationBatch.church_id == church_id,
            DonationBatch.status == "completed",
            DonationBatch.created_at >= start_dt,
            DonationBatch.created_at <= end_dt
        ).group_by(
            func.date_trunc('month', DonationBatch.created_at)
        ).order_by('month').all()

        monthly_breakdown = [
            {
                "month": row.month.strftime('%Y-%m') if row.month else None,
                "total_amount": float(row.total or 0),
                "donation_count": row.count or 0,
                "average_donation": float(row.total or 0) / (row.count or 1)
            }
            for row in monthly_data
        ]

        return {
            "total_donations": round(float(total_donations), 2),
            "donation_count": donation_count,
            "average_donation": round(float(avg_donation), 2),
            "monthly_breakdown": monthly_breakdown
        }

    @staticmethod
    async def _get_member_growth_analytics(church_id: int, start_dt: datetime, end_dt: datetime, db: Session) -> dict:
        """Get member growth analytics"""
        # New members in period
        new_members = db.query(func.count(User.id)).filter(
            User.church_id == church_id,
            User.created_at >= start_dt,
            User.created_at <= end_dt
        ).scalar() or 0

        # Total members at start and end of period
        members_at_start = db.query(func.count(User.id)).filter(
            User.church_id == church_id,
            User.created_at <= start_dt
        ).scalar() or 0

        current_members = db.query(func.count(User.id)).filter(
            User.church_id == church_id,
            User.created_at <= end_dt
        ).scalar() or 0

        # Growth rate
        growth_rate = ((current_members - members_at_start) / members_at_start * 100) if members_at_start > 0 else 0

        # Monthly growth
        monthly_growth = db.query(
            func.date_trunc('month', User.created_at).label('month'),
            func.count(User.id).label('new_members')
        ).filter(
            User.church_id == church_id,
            User.created_at >= start_dt,
            User.created_at <= end_dt
        ).group_by(
            func.date_trunc('month', User.created_at)
        ).order_by('month').all()

        monthly_breakdown = [
            {
                "month": row.month.strftime('%Y-%m') if row.month else None,
                "new_members": row.new_members or 0
            }
            for row in monthly_growth
        ]

        return {
            "new_members": new_members,
            "members_at_start": members_at_start,
            "current_members": current_members,
            "growth_rate_percent": round(growth_rate, 2),
            "monthly_breakdown": monthly_breakdown
        }

    @staticmethod
    async def _get_engagement_analytics(church_id: int, start_dt: datetime, end_dt: datetime, db: Session) -> dict:
        """Get member engagement analytics"""
        # Active donors
        active_donors = db.query(func.count(func.distinct(User.id))).join(DonationPreference).filter(
            User.church_id == church_id,
            DonationPreference.pause == False
        ).scalar() or 0

        # Recent activity (donations in last 30 days)
        recent_activity = db.query(func.count(func.distinct(DonationBatch.user_id))).filter(
            DonationBatch.church_id == church_id,
            DonationBatch.status == "completed",
            DonationBatch.created_at >= datetime.now(timezone.utc) - timedelta(days=30)
        ).scalar() or 0

        total_members = db.query(func.count(User.id)).filter(User.church_id == church_id).scalar() or 0

        engagement_rate = (recent_activity / total_members * 100) if total_members > 0 else 0

        return {
            "active_donors": active_donors,
            "recent_active_members": recent_activity,
            "total_members": total_members,
            "engagement_rate_percent": round(engagement_rate, 2)
        }

    @staticmethod
    async def _get_financial_analytics(church_id: int, start_dt: datetime, end_dt: datetime, db: Session) -> dict:
        """Get financial analytics"""
        # Revenue analytics
        gross_revenue = db.query(func.sum(DonationBatch.total_amount)).filter(
            DonationBatch.church_id == church_id,
            DonationBatch.status == "completed",
            DonationBatch.created_at >= start_dt,
            DonationBatch.created_at <= end_dt
        ).scalar() or 0

        # Platform fees (assuming 5% + $0.30 per transaction)
        transaction_count = db.query(func.count(DonationBatch.id)).filter(
            DonationBatch.church_id == church_id,
            DonationBatch.status == "completed",
            DonationBatch.created_at >= start_dt,
            DonationBatch.created_at <= end_dt
        ).scalar() or 0

        platform_fees = (gross_revenue * 0.05) + (transaction_count * 0.30)
        net_revenue = gross_revenue - platform_fees

        # Monthly revenue breakdown
        monthly_revenue = db.query(
            func.date_trunc('month', DonationBatch.created_at).label('month'),
            func.sum(DonationBatch.total_amount).label('gross'),
            func.count(DonationBatch.id).label('transactions')
        ).filter(
            DonationBatch.church_id == church_id,
            DonationBatch.status == "completed",
            DonationBatch.created_at >= start_dt,
            DonationBatch.created_at <= end_dt
        ).group_by(
            func.date_trunc('month', DonationBatch.created_at)
        ).order_by('month').all()

        monthly_breakdown = [
            {
                "month": row.month.strftime('%Y-%m') if row.month else None,
                "gross_revenue": float(row.gross or 0),
                "transactions": row.transactions or 0,
                "platform_fees": (float(row.gross or 0) * 0.05) + ((row.transactions or 0) * 0.30),
                "net_revenue": float(row.gross or 0) - ((float(row.gross or 0) * 0.05) + ((row.transactions or 0) * 0.30))
            }
            for row in monthly_revenue
        ]

        return {
            "gross_revenue": round(float(gross_revenue), 2),
            "platform_fees": round(float(platform_fees), 2),
            "net_revenue": round(float(net_revenue), 2),
            "transaction_count": transaction_count,
            "average_transaction": round(float(gross_revenue) / transaction_count, 2) if transaction_count > 0 else 0,
            "monthly_breakdown": monthly_breakdown
        }

    @staticmethod
    async def _generate_predictions(church_id: int, db: Session) -> dict:
        """Generate simple predictions based on historical data"""
        # Get last 6 months of data for trend analysis
        six_months_ago = datetime.now(timezone.utc) - timedelta(days=180)

        # Donation trend
        monthly_donations = db.query(
            func.date_trunc('month', DonationBatch.created_at).label('month'),
            func.sum(DonationBatch.total_amount).label('total')
        ).filter(
            DonationBatch.church_id == church_id,
            DonationBatch.status == "completed",
            DonationBatch.created_at >= six_months_ago
        ).group_by(
            func.date_trunc('month', DonationBatch.created_at)
        ).order_by('month').all()

        # Simple linear trend prediction (very basic)
        if len(monthly_donations) >= 2:
            amounts = [float(row.total or 0) for row in monthly_donations]
            trend = (amounts[-1] - amounts[0]) / len(amounts) if len(amounts) > 1 else 0

            next_month_prediction = amounts[-1] + trend if amounts else 0
            growth_trend = "increasing" if trend > 0 else "decreasing" if trend < 0 else "stable"
        else:
            next_month_prediction = 0
            growth_trend = "insufficient_data"

        # Member growth trend
        monthly_members = db.query(
            func.date_trunc('month', User.created_at).label('month'),
            func.count(User.id).label('new_members')
        ).filter(
            User.church_id == church_id,
            User.created_at >= six_months_ago
        ).group_by(
            func.date_trunc('month', User.created_at)
        ).order_by('month').all()

        avg_monthly_growth = sum(row.new_members for row in monthly_members) / len(monthly_members) if monthly_members else 0

        return {
            "donation_predictions": {
                "next_month_estimate": round(float(next_month_prediction), 2),
                "trend": growth_trend,
                "confidence": "low"  # Since this is a simple prediction
            },
            "member_predictions": {
                "average_monthly_growth": round(avg_monthly_growth, 1),
                "projected_next_month": round(avg_monthly_growth, 0)
            },
            "disclaimer": "Predictions are based on simple trend analysis and should be used for guidance only."
        }


class ChurchDocumentManager:
    """Manages church documents and compliance"""

    @staticmethod
    @monitor_admin_endpoint("get_church_documents")
    async def get_document_library(church_id: int, admin_id: int, db: Session) -> dict:
        """Get church document library"""
        try:
            church = db.query(Church).filter(Church.id == church_id).first()
            if not church:
                raise HTTPException(status_code=404, detail="Church not found")

            # This would integrate with a document storage system
            # For now, return a structure showing what documents are available
            documents = {
                "kyc_documents": {
                    "status": church.kyc_status,
                    "documents": [
                        {"type": "registration_certificate", "status": "approved", "uploaded_at": "2024-01-15"},
                        {"type": "tax_exemption", "status": "pending", "uploaded_at": "2024-01-20"},
                        {"type": "bank_statement", "status": "approved", "uploaded_at": "2024-01-10"}
                    ]
                },
                "financial_documents": {
                    "monthly_statements": [],
                    "tax_documents": [],
                    "audit_reports": []
                },
                "operational_documents": {
                    "policies": [],
                    "procedures": [],
                    "insurance": []
                }
            }

            return ResponseFactory.success(
                message="Church documents retrieved successfully",
                data=documents
            )

        except Exception as e:
            raise handle_admin_exception(e, "get_church_documents", admin_id)


class ChurchReportingManager:
    """Manages church reporting and exports"""

    @staticmethod
    @monitor_admin_endpoint("generate_church_report")
    async def generate_comprehensive_report(
        church_id: int,
        admin_id: int,
        db: Session,
        report_type: str = "comprehensive",
        format: str = "json",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> dict:
        """Generate comprehensive church report"""
        try:
            church = db.query(Church).filter(Church.id == church_id).first()
            if not church:
                raise HTTPException(status_code=404, detail="Church not found")

            # Parse dates
            if start_date:
                start_dt = datetime.fromisoformat(start_date)
            else:
                start_dt = datetime.now(timezone.utc) - timedelta(days=90)

            if end_date:
                end_dt = datetime.fromisoformat(end_date)
            else:
                end_dt = datetime.now(timezone.utc)

            # Generate report data based on type
            if report_type == "comprehensive":
                report_data = await ChurchReportingManager._generate_comprehensive_report_data(
                    church_id, start_dt, end_dt, db
                )
            elif report_type == "financial":
                report_data = await ChurchReportingManager._generate_financial_report_data(
                    church_id, start_dt, end_dt, db
                )
            elif report_type == "members":
                report_data = await ChurchReportingManager._generate_members_report_data(
                    church_id, start_dt, end_dt, db
                )
            else:
                raise HTTPException(status_code=400, detail="Invalid report type")

            # Add metadata
            report_data["metadata"] = {
                "church_id": church_id,
                "church_name": church.name,
                "report_type": report_type,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "generated_by": admin_id,
                "period": {
                    "start_date": start_dt.isoformat(),
                    "end_date": end_dt.isoformat()
                },
                "format": format
            }

            return ResponseFactory.success(
                message="Church report generated successfully",
                data=report_data
            )

        except Exception as e:
            raise handle_admin_exception(e, "generate_church_report", admin_id)

    @staticmethod
    async def _generate_comprehensive_report_data(church_id: int, start_dt: datetime, end_dt: datetime, db: Session) -> dict:
        """Generate comprehensive report data"""
        # Get all analytics
        donation_analytics = await ChurchAnalyticsManager._get_donation_analytics(church_id, start_dt, end_dt, db)
        member_analytics = await ChurchAnalyticsManager._get_member_growth_analytics(church_id, start_dt, end_dt, db)
        engagement_analytics = await ChurchAnalyticsManager._get_engagement_analytics(church_id, start_dt, end_dt, db)
        financial_analytics = await ChurchAnalyticsManager._get_financial_analytics(church_id, start_dt, end_dt, db)

        # Get church basic info
        church = db.query(Church).filter(Church.id == church_id).first()

        return {
            "church_overview": ChurchProfileManager._serialize_church_profile(church),
            "summary": {
                "total_revenue": donation_analytics["total_donations"],
                "total_members": member_analytics["current_members"],
                "new_members": member_analytics["new_members"],
                "active_donors": engagement_analytics["active_donors"],
                "engagement_rate": engagement_analytics["engagement_rate_percent"]
            },
            "detailed_analytics": {
                "donations": donation_analytics,
                "members": member_analytics,
                "engagement": engagement_analytics,
                "financial": financial_analytics
            }
        }

    @staticmethod
    async def _generate_financial_report_data(church_id: int, start_dt: datetime, end_dt: datetime, db: Session) -> dict:
        """Generate financial report data"""
        financial_analytics = await ChurchAnalyticsManager._get_financial_analytics(church_id, start_dt, end_dt, db)
        donation_analytics = await ChurchAnalyticsManager._get_donation_analytics(church_id, start_dt, end_dt, db)

        # Get detailed transaction data
        transactions = db.query(DonationBatch).filter(
            DonationBatch.church_id == church_id,
            DonationBatch.status == "completed",
            DonationBatch.created_at >= start_dt,
            DonationBatch.created_at <= end_dt
        ).order_by(desc(DonationBatch.created_at)).all()

        transaction_details = [
            {
                "id": tx.id,
                "amount": float(tx.total_amount),
                "date": tx.created_at.isoformat() if tx.created_at else None,
                "donor_id": tx.user_id,
                "frequency": tx.frequency,
                "status": tx.status
            }
            for tx in transactions
        ]

        return {
            "financial_summary": financial_analytics,
            "donation_summary": donation_analytics,
            "transaction_details": transaction_details,
            "tax_summary": {
                "total_taxable_donations": financial_analytics["gross_revenue"],
                "platform_fees_deductible": financial_analytics["platform_fees"],
                "net_taxable_amount": financial_analytics["net_revenue"]
            }
        }

    @staticmethod
    async def _generate_members_report_data(church_id: int, start_dt: datetime, end_dt: datetime, db: Session) -> dict:
        """Generate members report data"""
        member_analytics = await ChurchAnalyticsManager._get_member_growth_analytics(church_id, start_dt, end_dt, db)

        # Get detailed member data
        members = db.query(User).filter(User.church_id == church_id).all()

        member_details = []
        for member in members:
            member_data = ChurchMemberManager._serialize_member(member)
            member_analytics_detail = await ChurchMemberManager._get_member_analytics(member.id, db)
            member_data["analytics"] = member_analytics_detail
            member_details.append(member_data)

        return {
            "member_summary": member_analytics,
            "member_details": member_details,
            "segmentation": {
                "active_donors": len([m for m in member_details if m["analytics"]["has_active_donation"]]),
                "inactive_donors": len([m for m in member_details if not m["analytics"]["has_active_donation"] and m["analytics"]["donation_count"] > 0]),
                "never_donated": len([m for m in member_details if m["analytics"]["donation_count"] == 0])
            }
        }


# Export all managers
__all__ = [
    "ChurchOnboardingManager",
    "ChurchProfileManager",
    "ChurchMemberManager",
    "ChurchCommunicationManager",
    "ChurchAnalyticsManager",
    "ChurchDocumentManager",
    "ChurchReportingManager"
]
