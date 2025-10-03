"""
Advanced Donor Management Controller

Comprehensive donor management system for handling all donor-related activities:
- Donor segmentation and targeting
- Donor journey tracking and analytics
- Donor communication and campaigns
- Donor retention analysis and tools
- Donor support and ticketing system
- Donor reward/recognition programs
- Donor tax document management
- Donor preference management
- Donor churn prediction and prevention
- Bulk donor operations
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc, asc, case, text
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any, Tuple
import logging
from enum import Enum
from dataclasses import dataclass
import json
from collections import defaultdict

from app.model.m_user import User
from app.model.m_donation_batch import DonationBatch
from app.model.m_donation_preference import DonationPreference
from app.model.m_church import Church
from app.model.m_user_message import UserMessage
from app.model.m_audit_log import AuditLog
from app.core.responses import ResponseFactory
from app.core.admin_monitoring import admin_monitor, monitor_admin_endpoint, handle_admin_exception
from app.utils.email_service import EmailService
from app.utils.notification_service import NotificationService

logger = logging.getLogger(__name__)


class DonorSegment(Enum):
    """Donor segmentation categories"""
    HIGH_VALUE = "high_value"
    REGULAR = "regular"
    OCCASIONAL = "occasional"
    LAPSED = "lapsed"
    NEW = "new"
    AT_RISK = "at_risk"
    VIP = "vip"


class DonorLifecycleStage(Enum):
    """Donor lifecycle stages"""
    PROSPECT = "prospect"
    FIRST_TIME = "first_time"
    REPEAT = "repeat"
    LOYAL = "loyal"
    CHAMPION = "champion"
    INACTIVE = "inactive"
    CHURNED = "churned"


@dataclass
class DonorProfile:
    """Comprehensive donor profile"""
    user_id: int
    segment: DonorSegment
    lifecycle_stage: DonorLifecycleStage
    total_donated: float
    donation_count: int
    average_donation: float
    first_donation_date: Optional[datetime]
    last_donation_date: Optional[datetime]
    donation_frequency: str
    retention_probability: float
    churn_risk_score: int
    engagement_score: int
    ltv: float  # Lifetime Value
    preferences: Dict[str, Any]
    tags: List[str]


class DonorSegmentationManager:
    """Manages donor segmentation and targeting"""

    @staticmethod
    @monitor_admin_endpoint("segment_donors")
    async def segment_donors(
        admin_id: int,
        db: Session,
        church_id: Optional[int] = None,
        criteria: Optional[Dict[str, Any]] = None
    ) -> dict:
        """Segment donors based on behavior and characteristics"""
        try:
            # Base query for all donors
            query = db.query(User).join(DonationBatch).filter(
                DonationBatch.status == "completed"
            )

            if church_id:
                query = query.filter(User.church_id == church_id)

            donors = query.distinct().all()

            # Analyze each donor and assign segments
            segmented_donors = defaultdict(list)
            donor_profiles = []

            for donor in donors:
                profile = await DonorSegmentationManager._analyze_donor(donor.id, db)
                donor_profiles.append(profile)
                segmented_donors[profile.segment.value].append(profile)

            # Calculate segment statistics
            segment_stats = {}
            for segment, profiles in segmented_donors.items():
                segment_stats[segment] = {
                    "count": len(profiles),
                    "total_donated": sum(p.total_donated for p in profiles),
                    "average_ltv": sum(p.ltv for p in profiles) / len(profiles) if profiles else 0,
                    "average_engagement": sum(p.engagement_score for p in profiles) / len(profiles) if profiles else 0
                }

            return ResponseFactory.success(
                message="Donor segmentation completed successfully",
                data={
                    "total_donors": len(donor_profiles),
                    "segments": segment_stats,
                    "segmentation_criteria": criteria or "default",
                    "generated_at": datetime.now(timezone.utc).isoformat()
                }
            )

        except Exception as e:
            raise handle_admin_exception(e, "segment_donors", admin_id)

    @staticmethod
    async def _analyze_donor(user_id: int, db: Session) -> DonorProfile:
        """Analyze individual donor and create profile"""
        # Get donation history
        donations = db.query(DonationBatch).filter(
            DonationBatch.user_id == user_id,
            DonationBatch.status == "completed"
        ).order_by(DonationBatch.created_at).all()

        if not donations:
            # This shouldn't happen as we're only analyzing donors
            raise ValueError(f"No donations found for user {user_id}")

        # Calculate basic metrics
        total_donated = sum(float(d.total_amount) for d in donations)
        donation_count = len(donations)
        average_donation = total_donated / donation_count
        first_donation_date = donations[0].created_at
        last_donation_date = donations[-1].created_at

        # Calculate donation frequency
        days_between_first_last = (last_donation_date - first_donation_date).days
        frequency = "one-time" if donation_count == 1 else "regular" if days_between_first_last / donation_count < 45 else "occasional"

        # Determine lifecycle stage
        days_since_last = (datetime.now(timezone.utc) - last_donation_date).days
        lifecycle_stage = DonorSegmentationManager._determine_lifecycle_stage(
            donation_count, days_since_last, days_between_first_last
        )

        # Determine segment
        segment = DonorSegmentationManager._determine_segment(
            total_donated, donation_count, average_donation, days_since_last
        )

        # Calculate scores
        retention_probability = DonorSegmentationManager._calculate_retention_probability(
            donation_count, days_since_last, frequency, total_donated
        )
        churn_risk_score = DonorSegmentationManager._calculate_churn_risk(
            days_since_last, donation_count, frequency
        )
        engagement_score = DonorSegmentationManager._calculate_engagement_score(
            donation_count, days_since_last, total_donated
        )

        # Calculate LTV (simplified)
        ltv = DonorSegmentationManager._calculate_ltv(
            average_donation, donation_count, days_between_first_last
        )

        # Get current preferences
        preference = db.query(DonationPreference).filter_by(user_id=user_id).first()
        preferences = {
            "frequency": preference.frequency if preference else None,
            "amount": float(preference.amount) if preference and preference.amount else None,
            "is_paused": preference.pause if preference else False
        }

        return DonorProfile(
            user_id=user_id,
            segment=segment,
            lifecycle_stage=lifecycle_stage,
            total_donated=total_donated,
            donation_count=donation_count,
            average_donation=average_donation,
            first_donation_date=first_donation_date,
            last_donation_date=last_donation_date,
            donation_frequency=frequency,
            retention_probability=retention_probability,
            churn_risk_score=churn_risk_score,
            engagement_score=engagement_score,
            ltv=ltv,
            preferences=preferences,
            tags=[]
        )

    @staticmethod
    def _determine_lifecycle_stage(donation_count: int, days_since_last: int, total_days: int) -> DonorLifecycleStage:
        """Determine donor lifecycle stage"""
        if donation_count == 1:
            if days_since_last <= 30:
                return DonorLifecycleStage.FIRST_TIME
            else:
                return DonorLifecycleStage.PROSPECT
        elif donation_count <= 3:
            if days_since_last <= 60:
                return DonorLifecycleStage.REPEAT
            else:
                return DonorLifecycleStage.INACTIVE
        elif donation_count <= 10:
            if days_since_last <= 90:
                return DonorLifecycleStage.LOYAL
            else:
                return DonorLifecycleStage.INACTIVE
        else:
            if days_since_last <= 30:
                return DonorLifecycleStage.CHAMPION
            elif days_since_last <= 180:
                return DonorLifecycleStage.LOYAL
            else:
                return DonorLifecycleStage.CHURNED

    @staticmethod
    def _determine_segment(total_donated: float, donation_count: int, average_donation: float, days_since_last: int) -> DonorSegment:
        """Determine donor segment"""
        if total_donated >= 10000:
            return DonorSegment.VIP
        elif total_donated >= 5000 or average_donation >= 500:
            return DonorSegment.HIGH_VALUE
        elif donation_count >= 5 and days_since_last <= 90:
            return DonorSegment.REGULAR
        elif days_since_last > 180:
            return DonorSegment.LAPSED
        elif donation_count == 1 and days_since_last <= 30:
            return DonorSegment.NEW
        elif days_since_last > 90:
            return DonorSegment.AT_RISK
        else:
            return DonorSegment.OCCASIONAL

    @staticmethod
    def _calculate_retention_probability(donation_count: int, days_since_last: int, frequency: str, total_donated: float) -> float:
        """Calculate probability of donor retention"""
        base_score = min(donation_count * 10, 100)  # Base score from donation count

        # Adjust for recency
        if days_since_last <= 30:
            recency_modifier = 1.0
        elif days_since_last <= 90:
            recency_modifier = 0.8
        elif days_since_last <= 180:
            recency_modifier = 0.5
        else:
            recency_modifier = 0.2

        # Adjust for frequency
        frequency_modifier = 1.2 if frequency == "regular" else 1.0 if frequency == "occasional" else 0.8

        # Adjust for total donated
        value_modifier = min(1.0 + (total_donated / 10000), 1.5)

        score = base_score * recency_modifier * frequency_modifier * value_modifier
        return min(score / 100, 1.0)

    @staticmethod
    def _calculate_churn_risk(days_since_last: int, donation_count: int, frequency: str) -> int:
        """Calculate churn risk score (0-100)"""
        # Base risk from recency
        if days_since_last <= 30:
            base_risk = 10
        elif days_since_last <= 90:
            base_risk = 30
        elif days_since_last <= 180:
            base_risk = 60
        else:
            base_risk = 90

        # Adjust for donation history
        history_modifier = max(0.5, 1.0 - (donation_count * 0.05))

        # Adjust for frequency
        frequency_modifier = 0.8 if frequency == "regular" else 1.0 if frequency == "occasional" else 1.2

        risk_score = int(base_risk * history_modifier * frequency_modifier)
        return min(risk_score, 100)

    @staticmethod
    def _calculate_engagement_score(donation_count: int, days_since_last: int, total_donated: float) -> int:
        """Calculate engagement score (0-100)"""
        # Base score from activity
        activity_score = min(donation_count * 5, 50)

        # Recent activity bonus
        if days_since_last <= 30:
            recency_bonus = 30
        elif days_since_last <= 90:
            recency_bonus = 20
        elif days_since_last <= 180:
            recency_bonus = 10
        else:
            recency_bonus = 0

        # Value bonus
        value_bonus = min(total_donated / 100, 20)

        return min(int(activity_score + recency_bonus + value_bonus), 100)

    @staticmethod
    def _calculate_ltv(average_donation: float, donation_count: int, total_days: int) -> float:
        """Calculate estimated Lifetime Value"""
        if total_days <= 0:
            return average_donation

        # Estimate annual donation frequency
        annual_frequency = (donation_count / total_days) * 365 if total_days > 0 else 1

        # Estimate donor lifespan (conservative)
        estimated_lifespan_years = min(5, max(1, donation_count * 0.5))

        # Calculate LTV
        ltv = average_donation * annual_frequency * estimated_lifespan_years
        return round(ltv, 2)


class DonorJourneyTracker:
    """Tracks donor journey and touchpoints"""

    @staticmethod
    @monitor_admin_endpoint("get_donor_journey")
    async def get_donor_journey(
        user_id: int,
        admin_id: int,
        db: Session,
        include_predictions: bool = False
    ) -> dict:
        """Get comprehensive donor journey"""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail="Donor not found")

            # Get donor profile
            profile = await DonorSegmentationManager._analyze_donor(user_id, db)

            # Get donation timeline
            donations = db.query(DonationBatch).filter(
                DonationBatch.user_id == user_id,
                DonationBatch.status == "completed"
            ).order_by(DonationBatch.created_at).all()

            donation_timeline = [
                {
                    "id": d.id,
                    "amount": float(d.total_amount),
                    "date": d.created_at.isoformat() if d.created_at else None,
                    "frequency": d.frequency,
                    "church_id": d.church_id,
                    "milestone": DonorJourneyTracker._identify_milestone(d, donations)
                }
                for d in donations
            ]

            # Get communication history
            messages = db.query(UserMessage).filter(
                UserMessage.user_id == user_id
            ).order_by(desc(UserMessage.created_at)).limit(50).all()

            communication_timeline = [
                {
                    "id": msg.id,
                    "type": msg.message_type,
                    "title": msg.title,
                    "date": msg.created_at.isoformat() if msg.created_at else None,
                    "status": msg.status
                }
                for msg in messages
            ]

            # Calculate journey metrics
            journey_metrics = DonorJourneyTracker._calculate_journey_metrics(donations, profile)

            # Get touchpoints
            touchpoints = await DonorJourneyTracker._identify_touchpoints(user_id, db)

            result_data = {
                "donor_info": {
                    "id": user.id,
                    "name": f"{user.first_name} {user.last_name}",
                    "email": user.email,
                    "church_id": user.church_id,
                    "joined_date": user.created_at.isoformat() if user.created_at else None
                },
                "profile": {
                    "segment": profile.segment.value,
                    "lifecycle_stage": profile.lifecycle_stage.value,
                    "total_donated": profile.total_donated,
                    "donation_count": profile.donation_count,
                    "retention_probability": profile.retention_probability,
                    "churn_risk_score": profile.churn_risk_score,
                    "engagement_score": profile.engagement_score,
                    "ltv": profile.ltv
                },
                "journey_metrics": journey_metrics,
                "donation_timeline": donation_timeline,
                "communication_timeline": communication_timeline,
                "touchpoints": touchpoints
            }

            if include_predictions:
                predictions = await DonorJourneyTracker._generate_donor_predictions(profile, donations, db)
                result_data["predictions"] = predictions

            return ResponseFactory.success(
                message="Donor journey retrieved successfully",
                data=result_data
            )

        except Exception as e:
            raise handle_admin_exception(e, "get_donor_journey", admin_id)

    @staticmethod
    def _identify_milestone(donation: DonationBatch, all_donations: List[DonationBatch]) -> Optional[str]:
        """Identify if a donation represents a milestone"""
        donation_index = all_donations.index(donation)

        if donation_index == 0:
            return "first_donation"
        elif donation_index == 4:  # 5th donation
            return "loyal_donor"
        elif donation_index == 9:  # 10th donation
            return "champion_donor"

        # Check for amount milestones
        amount = float(donation.total_amount)
        if amount >= 1000:
            return "major_gift"
        elif amount >= 500:
            return "significant_gift"

        return None

    @staticmethod
    def _calculate_journey_metrics(donations: List[DonationBatch], profile: DonorProfile) -> dict:
        """Calculate journey-specific metrics"""
        if not donations:
            return {}

        # Time between donations
        donation_intervals = []
        for i in range(1, len(donations)):
            interval = (donations[i].created_at - donations[i-1].created_at).days
            donation_intervals.append(interval)

        avg_interval = sum(donation_intervals) / len(donation_intervals) if donation_intervals else 0

        # Donation progression
        amounts = [float(d.total_amount) for d in donations]
        is_increasing = len(amounts) > 1 and amounts[-1] > amounts[0]

        # Consistency score
        std_dev = 0
        if len(amounts) > 1:
            mean_amount = sum(amounts) / len(amounts)
            variance = sum((x - mean_amount) ** 2 for x in amounts) / len(amounts)
            std_dev = variance ** 0.5

        consistency_score = max(0, 100 - (std_dev / mean_amount * 100)) if amounts else 0

        return {
            "total_journey_days": (donations[-1].created_at - donations[0].created_at).days,
            "average_donation_interval_days": round(avg_interval, 1),
            "donation_trend": "increasing" if is_increasing else "stable",
            "consistency_score": round(consistency_score, 1),
            "milestones_achieved": len([d for d in donations if DonorJourneyTracker._identify_milestone(d, donations)])
        }

    @staticmethod
    async def _identify_touchpoints(user_id: int, db: Session) -> List[dict]:
        """Identify key touchpoints in donor journey"""
        # This would integrate with various systems to track touchpoints
        # For now, return a sample structure
        return [
            {
                "type": "website_visit",
                "date": "2024-01-15T10:30:00Z",
                "details": {"page": "/donate", "duration_seconds": 120}
            },
            {
                "type": "email_open",
                "date": "2024-01-10T14:20:00Z",
                "details": {"campaign": "monthly_update", "opened": True}
            },
            {
                "type": "app_login",
                "date": "2024-01-08T09:15:00Z",
                "details": {"platform": "mobile", "session_duration": 300}
            }
        ]

    @staticmethod
    async def _generate_donor_predictions(profile: DonorProfile, donations: List[DonationBatch], db: Session) -> dict:
        """Generate predictions for donor behavior"""
        # Simple prediction logic
        next_donation_probability = profile.retention_probability * 100

        # Predict next donation date
        if donations and len(donations) > 1:
            intervals = [(donations[i].created_at - donations[i-1].created_at).days for i in range(1, len(donations))]
            avg_interval = sum(intervals) / len(intervals)
            next_donation_date = donations[-1].created_at + timedelta(days=int(avg_interval))
        else:
            next_donation_date = datetime.now(timezone.utc) + timedelta(days=30)

        # Predict next donation amount
        amounts = [float(d.total_amount) for d in donations[-3:]]  # Last 3 donations
        predicted_amount = sum(amounts) / len(amounts) if amounts else profile.average_donation

        return {
            "next_donation": {
                "probability_percent": round(next_donation_probability, 1),
                "predicted_date": next_donation_date.isoformat(),
                "predicted_amount": round(predicted_amount, 2),
                "confidence": "medium"
            },
            "churn_risk": {
                "risk_level": "high" if profile.churn_risk_score > 70 else "medium" if profile.churn_risk_score > 40 else "low",
                "risk_score": profile.churn_risk_score,
                "key_factors": DonorJourneyTracker._identify_churn_factors(profile)
            },
            "ltv_projection": {
                "12_months": round(profile.ltv * 0.2, 2),
                "24_months": round(profile.ltv * 0.4, 2),
                "lifetime": profile.ltv
            }
        }

    @staticmethod
    def _identify_churn_factors(profile: DonorProfile) -> List[str]:
        """Identify key factors contributing to churn risk"""
        factors = []

        if profile.last_donation_date:
            days_since_last = (datetime.now(timezone.utc) - profile.last_donation_date).days
            if days_since_last > 180:
                factors.append("Long time since last donation")

        if profile.donation_count <= 2:
            factors.append("Low donation frequency")

        if profile.engagement_score < 30:
            factors.append("Low engagement score")

        if profile.preferences.get("is_paused"):
            factors.append("Donations currently paused")

        return factors[:3]  # Return top 3 factors


class DonorCampaignManager:
    """Manages donor communication campaigns"""

    @staticmethod
    @monitor_admin_endpoint("create_donor_campaign")
    async def create_targeted_campaign(
        admin_id: int,
        db: Session,
        campaign_data: dict
    ) -> dict:
        """Create targeted donor campaign"""
        try:
            # Validate campaign data
            required_fields = ["name", "message", "target_segments"]
            for field in required_fields:
                if field not in campaign_data:
                    raise HTTPException(status_code=400, detail=f"Missing required field: {field}")

            # Get target donors based on segments
            target_donors = await DonorCampaignManager._get_donors_by_segments(
                campaign_data["target_segments"],
                campaign_data.get("church_id"),
                campaign_data.get("additional_filters", {}),
                db
            )

            if not target_donors:
                raise HTTPException(status_code=400, detail="No donors found matching target criteria")

            # Create campaign record
            campaign_id = f"campaign_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # Send messages
            email_service = EmailService()
            notification_service = NotificationService()

            sent_count = 0
            failed_count = 0

            for donor in target_donors:
                try:
                    # Personalize message
                    personalized_message = DonorCampaignManager._personalize_message(
                        campaign_data["message"],
                        donor
                    )

                    # Send email
                    if campaign_data.get("send_email", True):
                        email_service.send_donor_campaign(
                            to_email=donor["email"],
                            donor_name=f"{donor['first_name']} {donor['last_name']}",
                            campaign_name=campaign_data["name"],
                            message=personalized_message
                        )

                    # Send push notification
                    if campaign_data.get("send_push", False):
                        notification_service.send_to_user(
                            user_id=donor["id"],
                            title=campaign_data["name"],
                            body=personalized_message[:100] + "..." if len(personalized_message) > 100 else personalized_message
                        )

                    sent_count += 1

                except Exception as e:
                    logger.error(f"Failed to send campaign message to donor {donor['id']}: {e}")
                    failed_count += 1

            # Log campaign
            AuditLog.create_log(
                db=db,
                user_id=admin_id,
                action="create_donor_campaign",
                resource_type="campaign",
                details={
                    "campaign_id": campaign_id,
                    "campaign_name": campaign_data["name"],
                    "target_segments": campaign_data["target_segments"],
                    "sent_count": sent_count,
                    "failed_count": failed_count
                }
            )

            return ResponseFactory.success(
                message="Donor campaign created and sent successfully",
                data={
                    "campaign_id": campaign_id,
                    "target_count": len(target_donors),
                    "sent_count": sent_count,
                    "failed_count": failed_count,
                    "success_rate": round((sent_count / len(target_donors) * 100), 1) if target_donors else 0
                }
            )

        except Exception as e:
            raise handle_admin_exception(e, "create_donor_campaign", admin_id)

    @staticmethod
    async def _get_donors_by_segments(
        target_segments: List[str],
        church_id: Optional[int],
        additional_filters: dict,
        db: Session
    ) -> List[dict]:
        """Get donors matching target segments"""
        # Get all donors first
        query = db.query(User).join(DonationBatch).filter(
            DonationBatch.status == "completed"
        )

        if church_id:
            query = query.filter(User.church_id == church_id)

        # Apply additional filters
        if additional_filters.get("min_total_donated"):
            # This would require a subquery to calculate total donated
            pass

        if additional_filters.get("last_donation_days"):
            days_ago = datetime.now(timezone.utc) - timedelta(days=additional_filters["last_donation_days"])
            query = query.filter(DonationBatch.created_at >= days_ago)

        donors = query.distinct().all()

        # Filter by segments
        filtered_donors = []
        for donor in donors:
            try:
                profile = await DonorSegmentationManager._analyze_donor(donor.id, db)
                if profile.segment.value in target_segments:
                    filtered_donors.append({
                        "id": donor.id,
                        "first_name": donor.first_name,
                        "last_name": donor.last_name,
                        "email": donor.email,
                        "segment": profile.segment.value,
                        "total_donated": profile.total_donated,
                        "donation_count": profile.donation_count
                    })
            except Exception as e:
                logger.error(f"Error analyzing donor {donor.id}: {e}")
                continue

        return filtered_donors

    @staticmethod
    def _personalize_message(template: str, donor: dict) -> str:
        """Personalize campaign message for donor"""
        # Simple template substitution
        personalized = template.replace("{donor_name}", f"{donor['first_name']} {donor['last_name']}")
        personalized = personalized.replace("{first_name}", donor['first_name'])
        personalized = personalized.replace("{total_donated}", f"${donor['total_donated']:.2f}")
        personalized = personalized.replace("{donation_count}", str(donor['donation_count']))

        return personalized


class DonorRetentionManager:
    """Manages donor retention and churn prevention"""

    @staticmethod
    @monitor_admin_endpoint("get_retention_analysis")
    async def get_retention_analysis(
        admin_id: int,
        db: Session,
        church_id: Optional[int] = None,
        period_days: int = 365
    ) -> dict:
        """Get comprehensive retention analysis"""
        try:
            # Get retention metrics
            retention_metrics = await DonorRetentionManager._calculate_retention_metrics(
                db, church_id, period_days
            )

            # Get churn analysis
            churn_analysis = await DonorRetentionManager._analyze_churn_patterns(
                db, church_id, period_days
            )

            # Get at-risk donors
            at_risk_donors = await DonorRetentionManager._identify_at_risk_donors(
                db, church_id
            )

            # Get retention recommendations
            recommendations = DonorRetentionManager._generate_retention_recommendations(
                retention_metrics, churn_analysis, at_risk_donors
            )

            return ResponseFactory.success(
                message="Donor retention analysis completed successfully",
                data={
                    "analysis_period_days": period_days,
                    "church_id": church_id,
                    "retention_metrics": retention_metrics,
                    "churn_analysis": churn_analysis,
                    "at_risk_donors": {
                        "count": len(at_risk_donors),
                        "total_value": sum(d["total_donated"] for d in at_risk_donors),
                        "details": at_risk_donors[:20]  # Limit to top 20
                    },
                    "recommendations": recommendations,
                    "generated_at": datetime.now(timezone.utc).isoformat()
                }
            )

        except Exception as e:
            raise handle_admin_exception(e, "get_retention_analysis", admin_id)

    @staticmethod
    async def _calculate_retention_metrics(
        db: Session,
        church_id: Optional[int],
        period_days: int
    ) -> dict:
        """Calculate retention metrics"""
        # Base query
        base_query = db.query(User).join(DonationBatch).filter(
            DonationBatch.status == "completed"
        )

        if church_id:
            base_query = base_query.filter(User.church_id == church_id)

        # Get donors from different periods
        now = datetime.now(timezone.utc)
        period_start = now - timedelta(days=period_days)

        # New donors in period
        new_donors = base_query.filter(
            func.min(DonationBatch.created_at) >= period_start
        ).distinct().count()

        # Donors who made their first donation before period but donated during period
        returning
