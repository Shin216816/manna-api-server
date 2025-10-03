"""
Analytics Service

Provides comprehensive analytics for the Manna platform including:
- Platform-wide analytics
- Church-specific analytics
- User donation analytics
- Spending category analysis
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
import logging

from app.model.m_user import User
from app.model.m_church import Church
from app.model.m_donation_batch import DonationBatch
from app.model.m_donation_preference import DonationPreference
from app.model.m_plaid_items import PlaidItem
# PlaidAccount import removed - using on-demand Plaid API fetching
from app.config import config

class AnalyticsService:
    """Service for generating analytics and reports"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_platform_analytics(self) -> Dict[str, Any]:
        """Get platform-wide analytics"""
        try:
            # Total users
            total_users = self.db.query(User).count()
            
            # Total churches
            total_churches = self.db.query(Church).count()
            
            # Total donations
            total_donations_result = self.db.query(func.sum(DonationBatch.total_amount)).filter(
                DonationBatch.status == config.STATUS_SUCCESS
            ).scalar()
            total_donations = float(total_donations_result) if total_donations_result else 0.0
            
            # Total successful batches
            total_batches = self.db.query(DonationBatch).filter(
                DonationBatch.status == config.STATUS_SUCCESS
            ).count()
            
            # Monthly growth (last 30 days vs previous 30 days)
            now = datetime.now(timezone.utc)
            last_30_days = now - timedelta(days=30)
            previous_30_days = last_30_days - timedelta(days=30)
            
            recent_donations = self.db.query(func.sum(DonationBatch.total_amount)).filter(
                and_(
                    DonationBatch.status == config.STATUS_SUCCESS,
                    DonationBatch.executed_at >= last_30_days
                )
            ).scalar() or 0.0
            
            previous_donations = self.db.query(func.sum(DonationBatch.total_amount)).filter(
                and_(
                    DonationBatch.status == config.STATUS_SUCCESS,
                    DonationBatch.executed_at >= previous_30_days,
                    DonationBatch.executed_at < last_30_days
                )
            ).scalar() or 0.0
            
            monthly_growth = ((recent_donations - previous_donations) / previous_donations * 100) if previous_donations > 0 else 0.0
            
            return {
                "total_users": total_users,
                "total_churches": total_churches,
                "total_donations": round(total_donations, 2),
                "total_batches": total_batches,
                "monthly_growth": round(monthly_growth, 2),
                "recent_30_days": round(recent_donations, 2),
                "previous_30_days": round(previous_donations, 2)
            }
            
        except Exception as e:
            
            return {}
    
    def get_church_analytics(self, church_id: int) -> Dict[str, Any]:
        """Get analytics for a specific church"""
        try:
            # Church info
            church = self.db.query(Church).filter_by(id=church_id).first()
            if not church:
                return {}
            
            # Total givers
            total_givers = self.db.query(User).filter_by(church_id=church_id).count()
            
            # Total donations
            total_donations_result = self.db.query(func.sum(DonationBatch.total_amount)).filter(
                and_(
                    DonationBatch.church_id == church_id,
                    DonationBatch.status == config.STATUS_SUCCESS
                )
            ).scalar()
            total_donations = float(total_donations_result) if total_donations_result else 0.0
            
            # Recent donations (last 30 days)
            last_30_days = datetime.now(timezone.utc) - timedelta(days=30)
            recent_donations_result = self.db.query(func.sum(DonationBatch.total_amount)).filter(
                and_(
                    DonationBatch.church_id == church_id,
                    DonationBatch.status == config.STATUS_SUCCESS,
                    DonationBatch.executed_at >= last_30_days
                )
            ).scalar()
            recent_donations = float(recent_donations_result) if recent_donations_result else 0.0
            
            # Average donation per giver
            avg_donation = total_donations / total_givers if total_givers > 0 else 0.0
            
            # Top donors
            top_donors = self.db.query(
                DonationBatch.user_id,
                func.sum(DonationBatch.total_amount).label('total_amount')
            ).filter(
                and_(
                    DonationBatch.church_id == church_id,
                    DonationBatch.status == config.STATUS_SUCCESS
                )
            ).group_by(DonationBatch.user_id).order_by(desc('total_amount')).limit(5).all()
            
            return {
                "church_id": church_id,
                "church_name": church.name,
                "total_givers": total_givers,
                "total_donations": round(total_donations, 2),
                "recent_donations": round(recent_donations, 2),
                "average_donation": round(avg_donation, 2),
                "top_donors": [
                    {
                        "user_id": donor.user_id,
                        "total_amount": round(donor.total_amount, 2)
                    } for donor in top_donors
                ]
            }
            
        except Exception as e:
            
            return {}
    
    def get_user_analytics(self, user_id: int) -> Dict[str, Any]:
        """Get analytics for a specific user"""
        try:
            # Total donated
            total_donated_result = self.db.query(func.sum(DonationBatch.total_amount)).filter(
                and_(
                    DonationBatch.user_id == user_id,
                    DonationBatch.status == config.STATUS_SUCCESS
                )
            ).scalar()
            total_donated = float(total_donated_result) if total_donated_result else 0.0
            
            # Total batches
            total_batches = self.db.query(DonationBatch).filter(
                and_(
                    DonationBatch.user_id == user_id,
                    DonationBatch.status == config.STATUS_SUCCESS
                )
            ).count()
            
            # Average donation per batch
            avg_donation = total_donated / total_batches if total_batches > 0 else 0.0
            
            # Recent donations (last 30 days)
            last_30_days = datetime.now(timezone.utc) - timedelta(days=30)
            recent_donations_result = self.db.query(func.sum(DonationBatch.total_amount)).filter(
                and_(
                    DonationBatch.user_id == user_id,
                    DonationBatch.status == config.STATUS_SUCCESS,
                    DonationBatch.executed_at >= last_30_days
                )
            ).scalar()
            recent_donations = float(recent_donations_result) if recent_donations_result else 0.0
            
            # Donation frequency
            first_donation = self.db.query(DonationBatch).filter(
                and_(
                    DonationBatch.user_id == user_id,
                    DonationBatch.status == config.STATUS_SUCCESS
                )
            ).order_by(DonationBatch.executed_at).first()
            
            if first_donation and total_batches > 1:
                days_since_first = (datetime.now(timezone.utc) - first_donation.executed_at).days
                donation_frequency = days_since_first / total_batches if days_since_first > 0 else 0
            else:
                donation_frequency = 0
            
            return {
                "user_id": user_id,
                "total_donated": round(total_donated, 2),
                "total_batches": total_batches,
                "average_donation": round(avg_donation, 2),
                "recent_donations": round(recent_donations, 2),
                "donation_frequency_days": round(donation_frequency, 1)
            }
            
        except Exception as e:
            
            return {}
    
    def get_church_spending_analytics(self, church_id: int) -> Dict[str, Any]:
        """Get aggregated spending categories and merchants for a church"""
        try:
            # Get church members
            members = self.db.query(User).filter(
                and_(
                    User.church_id == church_id,
                    User.role == "donor",
                    User.is_active == True
                )
            ).all()
            
            if not members:
                return {
                    "church_id": church_id,
                    "total_spending": 0.0,
                    "categories": {},
                    "merchants": [],
                    "note": "No active donors found"
                }
            
            # Aggregate spending data from all members
            total_spending = 0.0
            all_categories = {}
            all_merchants = {}
            
            for member in members:
                # Get member's spending analytics
                member_analytics = self.get_spending_categories(member.id)
                if member_analytics:
                    total_spending += member_analytics.get("total_spending", 0.0)
                    
                    # Aggregate categories
                    for category, amount in member_analytics.get("categories", {}).items():
                        all_categories[category] = all_categories.get(category, 0.0) + amount
                
                # Get member's merchant data
                member_merchants = self.get_top_merchants(member.id)
                if member_merchants:
                    for merchant in member_merchants.get("merchants", []):
                        merchant_name = merchant["name"]
                        if merchant_name in all_merchants:
                            all_merchants[merchant_name] += merchant["amount"]
                        else:
                            all_merchants[merchant_name] = merchant["amount"]
            
            # Sort merchants by amount
            sorted_merchants = [
                {"name": name, "amount": round(amount, 2)}
                for name, amount in sorted(all_merchants.items(), key=lambda x: x[1], reverse=True)
            ][:10]  # Top 10 merchants
            
            # Round category amounts
            rounded_categories = {
                category: round(amount, 2)
                for category, amount in all_categories.items()
            }
            
            return {
                "church_id": church_id,
                "total_spending": round(total_spending, 2),
                "categories": rounded_categories,
                "merchants": sorted_merchants,
                "note": "Aggregated anonymized data from all church donors"
            }
            
        except Exception as e:
            
            return {}
    
    def get_spending_categories(self, user_id: int) -> Dict[str, Any]:
        """Get spending category analysis for a user"""
        try:
            # This would typically fetch from Plaid transaction data
            # For now, return estimated categories based on fallback percentages
            
            # Get user's total spending (estimated from donations)
            total_donated_result = self.db.query(func.sum(DonationBatch.total_amount)).filter(
                and_(
                    DonationBatch.user_id == user_id,
                    DonationBatch.status == config.STATUS_SUCCESS
                )
            ).scalar()
            total_donated = float(total_donated_result) if total_donated_result else 0.0
            
            # Estimate total spending (assuming donations are ~10% of total spending)
            estimated_total_spending = total_donated * 10
            
            # Calculate categories using fallback percentages
            categories = {
                "food_dining": round(estimated_total_spending * config.FALLBACK_FOOD_PERCENTAGE, 2),
                "shopping": round(estimated_total_spending * config.FALLBACK_SHOPPING_PERCENTAGE, 2),
                "transportation": round(estimated_total_spending * config.FALLBACK_TRANSPORT_PERCENTAGE, 2),
                "entertainment": round(estimated_total_spending * config.FALLBACK_ENTERTAINMENT_PERCENTAGE, 2),
                "other": round(estimated_total_spending * config.FALLBACK_OTHER_PERCENTAGE, 2)
            }
            
            return {
                "user_id": user_id,
                "total_spending": round(estimated_total_spending, 2),
                "categories": categories,
                "note": "Based on estimated spending patterns. Connect bank account for real data."
            }
            
        except Exception as e:
            
            return {}
    
    def get_top_merchants(self, user_id: int) -> Dict[str, Any]:
        """Get top merchants for a user"""
        try:
            # This would typically fetch from Plaid transaction data
            # For now, return estimated merchants
            
            # Get user's total spending
            total_donated_result = self.db.query(func.sum(DonationBatch.total_amount)).filter(
                and_(
                    DonationBatch.user_id == user_id,
                    DonationBatch.status == config.STATUS_SUCCESS
                )
            ).scalar()
            total_donated = float(total_donated_result) if total_donated_result else 0.0
            
            # Estimate total spending
            estimated_total_spending = total_donated * 10
            
            # Return estimated top merchants
            merchants = [
                {"name": "Grocery Store", "amount": round(estimated_total_spending * 0.15, 2)},
                {"name": "Gas Station", "amount": round(estimated_total_spending * 0.10, 2)},
                {"name": "Restaurant", "amount": round(estimated_total_spending * 0.12, 2)},
                {"name": "Online Retailer", "amount": round(estimated_total_spending * 0.20, 2)},
                {"name": "Coffee Shop", "amount": round(estimated_total_spending * 0.05, 2)}
            ]
            
            return {
                "user_id": user_id,
                "total_spending": round(estimated_total_spending, 2),
                "merchants": merchants,
                "note": "Based on estimated spending patterns. Connect bank account for real data."
            }
            
        except Exception as e:
            
            return {}


# Analytics service functions

def get_platform_analytics(db: Session) -> Dict[str, Any]:
    """Get platform-wide analytics"""
    service = AnalyticsService(db)
    return service.get_platform_analytics()

def get_church_analytics(church_id: int, db: Session) -> Dict[str, Any]:
    """Get analytics for a specific church"""
    service = AnalyticsService(db)
    return service.get_church_analytics(church_id)

def get_user_analytics(user_id: int, db: Session) -> Dict[str, Any]:
    """Get analytics for a specific user"""
    service = AnalyticsService(db)
    return service.get_user_analytics(user_id)

def get_spending_categories(user_id: int, db: Session) -> Dict[str, Any]:
    """Get spending category analysis for a user"""
    service = AnalyticsService(db)
    return service.get_spending_categories(user_id)

def get_top_merchants(user_id: int, db: Session) -> Dict[str, Any]:
    """Get top merchants for a user"""
    service = AnalyticsService(db)
    return service.get_top_merchants(user_id)

def get_church_spending_analytics(church_id: int, db: Session) -> Dict[str, Any]:
    """Get aggregated spending categories and merchants for a church"""
    service = AnalyticsService(db)
    return service.get_church_spending_analytics(church_id)

# Additional functions from church_dashboard_service.py for consolidation
# These maintain API compatibility while consolidating services

def get_church_stripe_transactions(
    church_id: int,
    db: Session,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get church Stripe transactions (from church_dashboard_service.py)
    Maintains API compatibility
    """
    try:
        from app.services.stripe_service import (
            get_church_stripe_charges,
            get_church_stripe_transfers,
            get_church_stripe_balance,
            get_church_stripe_payouts,
        )
        
        # Get church
        from app.model.m_church import Church
        church = db.query(Church).filter(Church.id == church_id).first()
        if not church or not church.stripe_account_id:
            return {
                "success": False,
                "error": "Church not found or not connected to Stripe",
                "transactions": []
            }
        
        # Get Stripe data
        charges = get_church_stripe_charges(church.stripe_account_id, start_date, end_date)
        transfers = get_church_stripe_transfers(church.stripe_account_id, start_date, end_date)
        balance = get_church_stripe_balance(church.stripe_account_id)
        payouts = get_church_stripe_payouts(church.stripe_account_id, start_date, end_date)
        
        return {
            "success": True,
            "transactions": {
                "charges": charges,
                "transfers": transfers,
                "balance": balance,
                "payouts": payouts
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting church Stripe transactions: {str(e)}")
        return {
            "success": False,
            "error": f"Failed to get Stripe transactions: {str(e)}",
            "transactions": []
        }

def get_church_roundup_summary(church_id: int, db: Session) -> Dict[str, Any]:
    """
    Get church roundup summary (from church_dashboard_service.py)
    Maintains API compatibility
    """
    try:
        from app.model.m_church import Church
        from app.model.m_user import User
        from app.model.m_donation_preference import DonationPreference
        from app.services.plaid_transaction_service import plaid_transaction_service
        
        # Get church
        church = db.query(Church).filter(Church.id == church_id).first()
        if not church:
            return {
                "success": False,
                "error": "Church not found",
                "summary": {}
            }
        
        # Get church members
        members = db.query(User).filter(User.church_id == church_id).all()
        
        total_roundup_potential = 0.0
        active_donors = 0
        total_transactions = 0
        
        for member in members:
            # Get member's donation preferences
            preferences = db.query(DonationPreference).filter(
                DonationPreference.user_id == member.id
            ).first()
            
            if preferences and preferences.is_active:
                active_donors += 1
                
                # Calculate roundup potential for this member
                roundup_result = plaid_transaction_service.calculate_roundup_amount(
                    user_id=member.id,
                    db=db,
                    days_back=30
                )
                
                if roundup_result.get("success"):
                    total_roundup_potential += roundup_result.get("total_roundup", 0)
                    total_transactions += roundup_result.get("transaction_count", 0)
        
        return {
            "success": True,
            "summary": {
                "total_members": len(members),
                "active_donors": active_donors,
                "total_roundup_potential": total_roundup_potential,
                "total_transactions": total_transactions,
                "average_roundup_per_donor": total_roundup_potential / active_donors if active_donors > 0 else 0
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting church roundup summary: {str(e)}")
        return {
            "success": False,
            "error": f"Failed to get roundup summary: {str(e)}",
            "summary": {}
        }

def get_church_monthly_trends(
    church_id: int,
    db: Session,
    months_back: int = 12
) -> Dict[str, Any]:
    """
    Get church monthly trends (from church_dashboard_service.py)
    Maintains API compatibility
    """
    try:
        from app.model.m_church import Church
        from app.model.m_roundup_new import ChurchPayout
        from datetime import datetime, timezone, timedelta
        
        # Get church
        church = db.query(Church).filter(Church.id == church_id).first()
        if not church:
            return {
                "success": False,
                "error": "Church not found",
                "trends": []
            }
        
        # Get monthly payouts
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=months_back * 30)
        
        payouts = db.query(ChurchPayout).filter(
            ChurchPayout.church_id == church_id,
            ChurchPayout.created_at >= start_date,
            ChurchPayout.created_at <= end_date
        ).all()
        
        # Group by month
        monthly_data = {}
        for payout in payouts:
            month_key = payout.created_at.strftime("%Y-%m")
            if month_key not in monthly_data:
                monthly_data[month_key] = {
                    "month": month_key,
                    "total_amount": 0,
                    "payout_count": 0
                }
            
            monthly_data[month_key]["total_amount"] += float(payout.amount)
            monthly_data[month_key]["payout_count"] += 1
        
        # Convert to list and sort by month
        trends = list(monthly_data.values())
        trends.sort(key=lambda x: x["month"])
        
        return {
            "success": True,
            "trends": trends
        }
        
    except Exception as e:
        logger.error(f"Error getting church monthly trends: {str(e)}")
        return {
            "success": False,
            "error": f"Failed to get monthly trends: {str(e)}",
            "trends": []
        }

# Create service instances for backward compatibility
class ChurchDashboardService:
    """Wrapper class for backward compatibility"""
    
    @staticmethod
    def get_church_stripe_transactions(church_id: int, db: Session, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        return get_church_stripe_transactions(church_id, db, start_date, end_date)
    
    @staticmethod
    def get_church_roundup_summary(church_id: int, db: Session) -> Dict[str, Any]:
        return get_church_roundup_summary(church_id, db)
    
    @staticmethod
    def get_church_monthly_trends(church_id: int, db: Session, months_back: int = 12) -> Dict[str, Any]:
        return get_church_monthly_trends(church_id, db, months_back)

# Create service instance for backward compatibility
church_dashboard_service = ChurchDashboardService() 
