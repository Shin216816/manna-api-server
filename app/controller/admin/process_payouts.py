"""
Admin Payout Processing Controller

Allows administrators to manually trigger payouts and monitor payout status.
"""

from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from datetime import datetime, timezone, timedelta
import logging

from app.model.m_roundup_new import DonorPayout, ChurchPayout
from app.model.m_church import Church
from app.services.church_payout_service import ChurchPayoutService
from app.core.responses import ResponseFactory
from app.utils.audit import create_audit_log


def trigger_church_payout(church_id: int, current_admin: dict, db: Session):
    """Manually trigger payout for a specific church using correct workflow"""
    try:
        # Get church
        church = db.query(Church).filter_by(id=church_id).first()
        if not church:
            raise HTTPException(status_code=404, detail="Church not found")
        
        # Process payout using the correct service
        result = ChurchPayoutService.process_church_payout(db, church_id)
        
        if not result['success']:
            return ResponseFactory.success(
                message=result['message'],
                data={
                    "church_id": church_id,
                    "church_name": church.name,
                    "amount": result.get('amount', 0.0)
                }
            )
        
        # Create audit log
        create_audit_log(
            db=db,
            actor_type="admin",
            actor_id=current_admin.get("admin_id", 0),
            action="manual_payout",
            metadata={
                "resource_type": "church_payout",
                "church_id": church_id,
                "church_name": church.name,
                "church_payout_id": result['church_payout_id'],
                "stripe_transfer_id": result['stripe_transfer_id'],
                "gross_amount": result['gross_amount'],
                "system_fee": result['system_fee'],
                "net_amount": result['net_amount'],
                "donor_count": result['donor_count'],
                "donation_count": result['donation_count']
            }
        )
        
        return ResponseFactory.success(
            message=result['message'],
            data={
                "church_id": church_id,
                "church_name": church.name,
                "church_payout_id": result['church_payout_id'],
                "stripe_transfer_id": result['stripe_transfer_id'],
                "gross_amount": result['gross_amount'],
                "system_fee": result['system_fee'],
                "net_amount": result['net_amount'],
                "donor_count": result['donor_count'],
                "donation_count": result['donation_count']
            }
        )
        
    except Exception as e:
        
        raise HTTPException(status_code=500, detail=f"Failed to process payout: {str(e)}")


def get_pending_payouts(current_admin: dict, db: Session):
    """Get summary of all pending payouts using correct workflow"""
    try:
        # Get unallocated donor payouts grouped by church
        pending_payouts = db.query(
            DonorPayout.church_id,
            Church.name.label('church_name'),
            Church.stripe_account_id,
            func.sum(DonorPayout.donation_amount).label('total_amount'),
            func.count(DonorPayout.id).label('donation_count'),
            func.count(func.distinct(DonorPayout.user_id)).label('donor_count'),
            func.min(DonorPayout.processed_at).label('oldest_donation'),
            func.max(DonorPayout.processed_at).label('newest_donation')
        ).join(
            Church, DonorPayout.church_id == Church.id
        ).filter(
            and_(
                DonorPayout.status == "completed",  # Successfully processed
                DonorPayout.allocated_at.is_(None),  # Not yet allocated to church payout
                Church.status == "active",
                Church.kyc_status == "verified"
            )
        ).group_by(
            DonorPayout.church_id, Church.name, Church.stripe_account_id
        ).all()
        
        # Format results
        pending_data = []
        total_pending_amount = 0.0
        
        for payout in pending_payouts:
            # Calculate days since oldest donation
            days_pending = (datetime.now(timezone.utc) - payout.oldest_donation).days if payout.oldest_donation else 0
            
            # Calculate system fee and net amount
            gross_amount = float(payout.total_amount)
            system_fee = gross_amount * 0.05  # 5% system fee
            net_amount = gross_amount - system_fee
            
            payout_info = {
                "church_id": payout.church_id,
                "church_name": payout.church_name,
                "gross_amount": round(gross_amount, 2),
                "system_fee": round(system_fee, 2),
                "net_amount": round(net_amount, 2),
                "donation_count": payout.donation_count,
                "donor_count": payout.donor_count,
                "oldest_donation": payout.oldest_donation.isoformat() if payout.oldest_donation else None,
                "newest_donation": payout.newest_donation.isoformat() if payout.newest_donation else None,
                "days_pending": days_pending,
                "has_stripe_account": bool(payout.stripe_account_id),
                "ready_for_payout": bool(payout.stripe_account_id) and days_pending >= 7 and net_amount >= 1.00
            }
            
            pending_data.append(payout_info)
            total_pending_amount += net_amount
        
        return ResponseFactory.success(
            message="Pending payouts retrieved successfully",
            data={
                "pending_payouts": pending_data,
                "total_pending_amount": round(total_pending_amount, 2),
                "total_churches": len(pending_data)
            }
        )
        
    except Exception as e:
        
        raise HTTPException(status_code=500, detail="Failed to get pending payouts")


def retry_failed_payout(payout_id: int, current_admin: dict, db: Session):
    """Manually retry a failed church payout"""
    try:
        # Get the failed payout
        payout = db.query(ChurchPayout).filter_by(id=payout_id).first()
        if not payout:
            raise HTTPException(status_code=404, detail="Church payout not found")
        
        if payout.status not in ["failed", "reversed"]:
            raise HTTPException(status_code=400, detail="Payout is not in a failed state")
        
        # Note: Since ChurchPayouts are only created after successful transfers,
        # a "retry" would actually mean processing a new payout for the church
        # The original failed transfer would need to be handled separately
        
        # Process a new payout for this church
        result = ChurchPayoutService.process_church_payout(db, payout.church_id)
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['message'])
        
        # Create audit log
        create_audit_log(
            db=db,
            actor_type="admin",
            actor_id=current_admin.get("admin_id", 0),
            action="retry_payout",
            metadata={
                "resource_type": "church_payout",
                "original_payout_id": payout_id,
                "new_payout_id": result['church_payout_id'],
                "church_id": payout.church_id,
                "net_amount": result['net_amount']
            }
        )
        
        return ResponseFactory.success(
            message="New payout processed successfully",
            data={
                "original_payout_id": payout_id,
                "new_payout_id": result['church_payout_id'],
                "stripe_transfer_id": result['stripe_transfer_id'],
                "net_amount": result['net_amount']
            }
        )
        
    except Exception as e:
        
        raise HTTPException(status_code=500, detail=f"Failed to retry payout: {str(e)}")


def get_payout_analytics(current_admin: dict, db: Session, days: int = 30):
    """Get payout analytics for the admin dashboard using correct workflow"""
    try:
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Get church payout statistics
        payout_stats = db.query(
            ChurchPayout.status,
            func.sum(ChurchPayout.net_payout_amount).label('total_amount'),
            func.count(ChurchPayout.id).label('count')
        ).filter(
            ChurchPayout.created_at >= cutoff_date
        ).group_by(ChurchPayout.status).all()
        
        # Format statistics
        stats_data = {}
        total_amount = 0.0
        total_count = 0
        
        for stat in payout_stats:
            amount = float(stat.total_amount) if stat.total_amount else 0.0
            stats_data[stat.status] = {
                "amount": round(amount, 2),
                "count": stat.count
            }
            total_amount += amount
            total_count += stat.count
        
        # Get pending donation amount (unallocated donor payouts)
        pending_donations = db.query(func.sum(DonorPayout.donation_amount)).filter(
            and_(
                DonorPayout.status == "completed",
                DonorPayout.allocated_at.is_(None)
            )
        ).scalar()
        
        pending_gross = float(pending_donations) if pending_donations else 0.0
        pending_net = pending_gross * 0.95  # After 5% system fee
        
        return ResponseFactory.success(
            message="Payout analytics retrieved successfully",
            data={
                "period_days": days,
                "payout_stats": stats_data,
                "total_processed": {
                    "amount": round(total_amount, 2),
                    "count": total_count
                },
                "pending_gross_amount": round(pending_gross, 2),
                "pending_net_amount": round(pending_net, 2),
                "success_rate": round((stats_data.get("completed", {}).get("count", 0) / total_count * 100), 2) if total_count > 0 else 0.0
            }
        )
        
    except Exception as e:
        
        raise HTTPException(status_code=500, detail="Failed to get payout analytics")


def get_payout_by_id(payout_id: int, db: Session):
    """Get a specific payout by ID with full breakdown data"""
    try:
        payout = db.query(ChurchPayout).join(Church).filter(ChurchPayout.id == payout_id).first()
        
        if not payout:
            raise HTTPException(status_code=404, detail="Payout not found")
        
        payout_data = {
            "id": payout.id,
            "church_id": payout.church_id,
            "church_name": payout.church.name,
            "gross_donation_amount": float(payout.gross_donation_amount),
            "system_fee_amount": float(payout.system_fee_amount),
            "system_fee_percentage": float(payout.system_fee_percentage),
            "net_payout_amount": float(payout.net_payout_amount),
            "donor_count": payout.donor_count,
            "donation_count": payout.donation_count,
            "period_start": payout.period_start,
            "period_end": payout.period_end,
            "status": payout.status,
            "stripe_transfer_id": payout.stripe_transfer_id,
            "failure_reason": payout.failure_reason,
            "payout_breakdown": payout.payout_breakdown,  # Include breakdown data
            "created_at": payout.created_at.isoformat() if payout.created_at else None,
            "processed_at": payout.processed_at.isoformat() if payout.processed_at else None,
            "failed_at": payout.failed_at.isoformat() if payout.failed_at else None,
        }
        
        return ResponseFactory.success(
            message="Payout retrieved successfully",
            data=payout_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to retrieve payout")


def get_all_payouts(page: int = 1, limit: int = 20, status_filter: str | None = None, db: Session | None = None):
    """Get all church payouts with pagination and filtering"""
    if db is None:
        raise HTTPException(status_code=500, detail="Database session required")
    try:
        query = db.query(ChurchPayout).join(Church)
        
        if status_filter and status_filter != "all":
            query = query.filter(ChurchPayout.status == status_filter)
        
        total = query.count()
        offset = (page - 1) * limit
        payouts = query.order_by(ChurchPayout.created_at.desc()).offset(offset).limit(limit).all()
        
        payouts_data = []
        for payout in payouts:
            payouts_data.append({
                "id": payout.id,
                "church_id": payout.church_id,
                "church_name": payout.church.name,
                "gross_donation_amount": float(payout.gross_donation_amount),
                "system_fee_amount": float(payout.system_fee_amount),
                "system_fee_percentage": float(payout.system_fee_percentage),
                "net_payout_amount": float(payout.net_payout_amount),
                "donor_count": payout.donor_count,
                "donation_count": payout.donation_count,
                "period_start": payout.period_start,
                "period_end": payout.period_end,
                "status": payout.status,
                "stripe_transfer_id": payout.stripe_transfer_id,
                "failure_reason": payout.failure_reason,
                "payout_breakdown": payout.payout_breakdown,  # Include breakdown data
                "created_at": payout.created_at.isoformat() if payout.created_at else None,
                "processed_at": payout.processed_at.isoformat() if payout.processed_at else None,
                "failed_at": payout.failed_at.isoformat() if payout.failed_at else None,
            })
        
        return ResponseFactory.success(
            message="Church payouts retrieved successfully",
            data={
                "payouts": payouts_data,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": total,
                    "pages": (total + limit - 1) // limit if limit > 0 else 1
                }
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to retrieve payouts")
