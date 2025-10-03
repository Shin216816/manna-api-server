"""
Church Payout Service

Implements the CORRECT church payout workflow:
1. Calculate church earnings from donor_payouts (minus system fees)
2. Execute Stripe transfer to church
3. If transfer succeeds, create ChurchPayout record with stripe_transfer_id
4. Mark donor_payouts as allocated

This ensures ChurchPayout records are only created AFTER successful transfers.
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import logging
from typing import List, Optional, Dict, Any

from app.model.m_roundup_new import DonorPayout, ChurchPayout
from app.model.m_church import Church
from app.services.stripe_service import transfer_to_church
from app.core.constants import get_business_constant


class ChurchPayoutService:
    """Service for processing church payouts with correct workflow"""
    
    @staticmethod
    def calculate_church_earnings(donor_payouts: List[DonorPayout], 
                                system_fee_percentage: float = 0.05) -> Dict[str, Any]:
        """
        Calculate church earnings from donor payouts
        
        Args:
            donor_payouts: List of DonorPayout records
            system_fee_percentage: Platform fee percentage (default 5%)
            
        Returns:
            Dict with gross_amount, system_fee, net_amount, donor_count, donation_count
        """
        if not donor_payouts:
            return {
                'gross_amount': Decimal('0.00'),
                'system_fee': Decimal('0.00'),
                'net_amount': Decimal('0.00'),
                'donor_count': 0,
                'donation_count': 0
            }
        
        # Calculate totals
        gross_amount = sum(Decimal(str(dp.donation_amount)) for dp in donor_payouts)
        system_fee = gross_amount * Decimal(str(system_fee_percentage))
        net_amount = gross_amount - system_fee
        
        # Count unique donors and total donations
        unique_donors = set(dp.user_id for dp in donor_payouts)
        
        return {
            'gross_amount': gross_amount,
            'system_fee': system_fee,
            'net_amount': net_amount,
            'donor_count': len(unique_donors),
            'donation_count': len(donor_payouts)
        }
    
    @staticmethod
    def get_pending_donor_payouts_for_church(db: Session, church_id: int) -> List[DonorPayout]:
        """
        Get all pending (unallocated) donor payouts for a church
        
        Args:
            db: Database session
            church_id: Church ID
            
        Returns:
            List of DonorPayout records ready for payout
        """
        return db.query(DonorPayout).filter(
            and_(
                DonorPayout.church_id == church_id,
                DonorPayout.status == "completed",  # Only successful donations
                DonorPayout.allocated_at.is_(None)  # Not yet allocated to a church payout
            )
        ).order_by(DonorPayout.processed_at.asc()).all()
    
    @staticmethod
    def process_church_payout(db: Session, church_id: int, 
                            system_fee_percentage: Optional[float] = None) -> Dict[str, Any]:
        """
        Process church payout following the correct workflow
        
        WORKFLOW:
        1. Get pending donor payouts for church
        2. Calculate church earnings (minus system fees)
        3. Execute Stripe transfer to church
        4. If transfer succeeds, create ChurchPayout record
        5. Mark donor payouts as allocated
        
        Args:
            db: Database session
            church_id: Church ID to process payout for
            system_fee_percentage: Override default system fee percentage
            
        Returns:
            Dict with payout result details
        """
        try:
            # Get church details
            church = db.query(Church).filter_by(id=church_id).first()
            if not church:
                raise ValueError(f"Church {church_id} not found")
            
            if not church.stripe_account_id:
                raise ValueError(f"Church {church.name} does not have Stripe Connect account")
            
            # Get pending donor payouts
            pending_payouts = ChurchPayoutService.get_pending_donor_payouts_for_church(db, church_id)
            
            if not pending_payouts:
                return {
                    'success': False,
                    'message': f"No pending donations found for church {church.name}",
                    'church_id': church_id,
                    'amount': 0.00
                }
            
            # Get system fee percentage
            if system_fee_percentage is None:
                system_fee_percentage = float(get_business_constant("SYSTEM_FEE_PERCENTAGE", 0.05) or 0.05)
            
            # Calculate earnings
            earnings = ChurchPayoutService.calculate_church_earnings(pending_payouts, system_fee_percentage)
            
            # Check minimum payout amount
            min_payout = float(get_business_constant("MIN_PAYOUT_AMOUNT", 1.00) or 1.00)
            if float(earnings['net_amount']) < min_payout:
                return {
                    'success': False,
                    'message': f"Payout amount ${earnings['net_amount']:.2f} is below minimum ${min_payout:.2f}",
                    'church_id': church_id,
                    'amount': float(earnings['net_amount'])
                }
            
            logging.info(f"[CHURCH PAYOUT] Processing payout for {church.name}: "
                        f"${earnings['gross_amount']:.2f} gross, ${earnings['system_fee']:.2f} fee, "
                        f"${earnings['net_amount']:.2f} net")
            
            # STEP 1: Execute Stripe transfer FIRST
            transfer = transfer_to_church(
                amount_cents=int(float(earnings['net_amount']) * 100),  # Convert to cents
                destination_account_id=church.stripe_account_id,
                metadata={
                    'church_id': str(church_id),
                    'church_name': church.name,
                    'gross_amount': str(earnings['gross_amount']),
                    'system_fee': str(earnings['system_fee']),
                    'net_amount': str(earnings['net_amount']),
                    'donor_count': str(earnings['donor_count']),
                    'donation_count': str(earnings['donation_count']),
                    'flow_type': 'correct_workflow'
                }
            )
            
            
            
            # STEP 2: Create ChurchPayout record AFTER successful transfer
            church_payout = ChurchPayout.create_after_successful_transfer(
                db=db,
                church_id=church_id,
                donor_payouts=pending_payouts,
                stripe_transfer_id=transfer.id,
                system_fee_percentage=system_fee_percentage
            )
            
            
            
            return {
                'success': True,
                'message': f"Payout processed successfully for {church.name}",
                'church_id': church_id,
                'church_payout_id': church_payout.id,
                'stripe_transfer_id': transfer.id,
                'gross_amount': float(earnings['gross_amount']),
                'system_fee': float(earnings['system_fee']),
                'net_amount': float(earnings['net_amount']),
                'donor_count': earnings['donor_count'],
                'donation_count': earnings['donation_count']
            }
            
        except Exception as e:
            
            db.rollback()
            raise e
    
    @staticmethod
    def process_all_pending_church_payouts(db: Session) -> Dict[str, Any]:
        """
        Process payouts for all churches with pending donor payouts
        
        Args:
            db: Database session
            
        Returns:
            Dict with summary of processed payouts
        """
        try:
            # Get all churches with pending donor payouts
            churches_with_pending = db.query(
                DonorPayout.church_id,
                Church.name.label('church_name'),
                Church.stripe_account_id,
                func.count(DonorPayout.id).label('pending_count'),
                func.sum(DonorPayout.donation_amount).label('total_amount')
            ).join(
                Church, DonorPayout.church_id == Church.id
            ).filter(
                and_(
                    DonorPayout.status == "completed",
                    DonorPayout.allocated_at.is_(None),
                    Church.status == "active",
                    Church.kyc_status == "verified",
                    Church.stripe_account_id.isnot(None)
                )
            ).group_by(
                DonorPayout.church_id, Church.name, Church.stripe_account_id
            ).all()
            
            results = []
            total_processed = 0
            total_amount = Decimal('0.00')
            
            
            for church_data in churches_with_pending:
                try:
                    result = ChurchPayoutService.process_church_payout(db, church_data.church_id)
                    results.append(result)
                    
                    if result['success']:
                        total_processed += 1
                        total_amount += Decimal(str(result['net_amount']))
                        
                except Exception as e:
                    
                    results.append({
                        'success': False,
                        'church_id': church_data.church_id,
                        'message': f"Error: {str(e)}"
                    })
                    continue
            
            return {
                'success': True,
                'message': f"Processed {total_processed} church payouts",
                'total_churches': len(churches_with_pending),
                'successful_payouts': total_processed,
                'total_amount': float(total_amount),
                'results': results
            }
            
        except Exception as e:
            
            raise e
    
    @staticmethod
    def get_church_payout_summary(db: Session, church_id: int, 
                                 days: int = 30) -> Dict[str, Any]:
        """
        Get payout summary for a church
        
        Args:
            db: Database session
            church_id: Church ID
            days: Number of days to look back
            
        Returns:
            Dict with payout summary
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Get recent payouts
        recent_payouts = db.query(ChurchPayout).filter(
            and_(
                ChurchPayout.church_id == church_id,
                ChurchPayout.created_at >= cutoff_date
            )
        ).order_by(ChurchPayout.created_at.desc()).all()
        
        # Get pending amount
        pending_payouts = ChurchPayoutService.get_pending_donor_payouts_for_church(db, church_id)
        pending_amount = sum(Decimal(str(dp.donation_amount)) for dp in pending_payouts)
        
        # Calculate totals
        total_paid = sum(Decimal(str(cp.net_payout_amount)) for cp in recent_payouts)
        
        return {
            'church_id': church_id,
            'period_days': days,
            'recent_payouts': len(recent_payouts),
            'total_paid': float(total_paid),
            'pending_donations': len(pending_payouts),
            'pending_amount': float(pending_amount),
            'payouts': [cp.to_dict() for cp in recent_payouts]
        }
