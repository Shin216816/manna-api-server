from apscheduler.schedulers.background import BackgroundScheduler
from app.tasks.cleanup_blacklisted_tokens import clean_expired_blacklist
from app.tasks.process_church_payouts import process_pending_church_payouts, retry_failed_payouts, create_monthly_church_payouts
from app.tasks.referral_commission_scheduler import process_referral_commissions, calculate_pending_commissions, retry_failed_commission_payouts
from app.utils.database import SessionLocal
from app.model.m_user import User
from app.model.m_donation_preference import DonationPreference
from app.controller.admin.execute_donation_batch import execute_donation_batch
from app.tasks.retry_failed_batches import retry_failed_donations
from app.services.donor_schedule_service import DonorScheduleService
from datetime import datetime, timezone, timedelta
from app.model.m_donation_batch import DonationBatch
import logging

# Set up logging



def run_scheduled_roundups():
    """
    Main scheduler function that processes individual donor payouts based on their schedules
    """
    db = SessionLocal()
    try:
        logging.info("[SCHEDULER] Starting scheduled donor payout processing...")
        
        # Get donors due for donation today
        due_donors = DonorScheduleService.get_donors_due_for_donation(db)
        
        logging.info(f"[SCHEDULER] Found {len(due_donors)} donors due for donation today")
        
        processed_count = 0
        failed_count = 0
        
        for donor in due_donors:
            try:
                logging.info(f"[SCHEDULER] Processing donation for {donor['name']} (User ID: {donor['user_id']})")
                
                # Process the donor payout
                result = DonorScheduleService.process_donor_payout(donor['user_id'], db)
                
                if result['success']:
                    processed_count += 1
                    logging.info(f"[SCHEDULER] Successfully processed donation for {donor['name']}: ${result['amount']}")
                else:
                    failed_count += 1
                    logging.error(f"[SCHEDULER] Failed to process donation for {donor['name']}: {result['error']}")
                    
            except Exception as e:
                failed_count += 1
                logging.error(f"[SCHEDULER] Error processing donation for {donor['name']}: {str(e)}")
                continue
        
        logging.info(f"[SCHEDULER] Completed donor payout processing: {processed_count} successful, {failed_count} failed")
                
    except Exception as e:
        logging.error(f"[SCHEDULER] Error in scheduled donor payout processing: {str(e)}")
    finally:
        db.close()


def should_process_roundups(preference, current_time, db):
    """
    Determine if roundups should be processed for a user based on their frequency preference
    """
    # Get the last successful batch for this user
    last_batch = db.query(DonationBatch).filter(
        DonationBatch.user_id == preference.user_id,
        DonationBatch.status == "success"
    ).order_by(DonationBatch.executed_at.desc()).first()
    
    if not last_batch:
        # First time processing for this user
        return True
    
    # Calculate time since last batch
    time_since_last = current_time - last_batch.executed_at
    
    if preference.frequency == "biweekly":
        # Process every 2 weeks
        return time_since_last >= timedelta(weeks=2)
    elif preference.frequency == "monthly":
        # Process every month (approximately 30 days)
        return time_since_last >= timedelta(days=30)
    
    return False


def retry_failed_roundups():
    """
    Retry failed roundup batches
    """
    retry_failed_donations()


def cleanup_expired_tokens():
    """
    Clean up expired blacklisted tokens
    """
    clean_expired_blacklist()


def process_church_payouts():
    """
    Process pending church payouts
    """
    process_pending_church_payouts()


def retry_church_payouts():
    """
    Retry failed church payouts
    """
    retry_failed_payouts()


# Initialize scheduler
scheduler = BackgroundScheduler()

# Add jobs (but don't start yet)
def add_scheduler_jobs():
    """Add all scheduled jobs to the scheduler"""
    scheduler.add_job(
        run_scheduled_roundups,
        'cron',
        hour=9,  # 9 AM UTC daily
        minute=0,
        id='scheduled_roundups',
        name='Process scheduled donor payouts'
    )

    scheduler.add_job(
        retry_failed_roundups,
        'interval',
        hours=12,  # Retry failed batches every 12 hours
        id='retry_failed_roundups',
        name='Retry failed roundup batches'
    )

    scheduler.add_job(
        cleanup_expired_tokens,
        'interval',
        hours=24,  # Clean up tokens daily
        id='cleanup_tokens',
        name='Clean up expired tokens'
    )

    scheduler.add_job(
        process_church_payouts,
        'cron',
        day_of_week=4,  # Friday
        hour=14,  # 2 PM UTC
        minute=0,
        id='process_church_payouts',
        name='Process pending church payouts'
    )

    scheduler.add_job(
        create_monthly_church_payouts,
        'cron',
        day=1,  # Run on the 1st of each month
        hour=2,  # At 2 AM UTC
        id='create_monthly_payouts',
        name='Create monthly church payouts'
    )

    scheduler.add_job(
        retry_church_payouts,
        'interval',
        hours=12,  # Retry failed payouts every 12 hours
        id='retry_church_payouts',
        name='Retry failed church payouts'
    )

    # Add referral commission jobs
    scheduler.add_job(
        process_referral_commissions,
        'interval',
        hours=24,  # Process commissions daily
        id='process_referral_commissions',
        name='Process referral commissions'
    )

    scheduler.add_job(
        calculate_pending_commissions,
        'interval',
        hours=6,  # Calculate commissions every 6 hours
        id='calculate_pending_commissions',
        name='Calculate pending commissions'
    )

    scheduler.add_job(
        retry_failed_commission_payouts,
        'interval',
        hours=12,  # Retry failed commission payouts every 12 hours
        id='retry_failed_commission_payouts',
        name='Retry failed commission payouts'
    )


def start_scheduler():
    """Start the background scheduler"""
    try:
        # Add jobs first
        add_scheduler_jobs()
        # Then start the scheduler
        scheduler.start()
        info("[SCHEDULER] Background scheduler started successfully")
    except Exception as e:
        error(f"[SCHEDULER] Failed to start scheduler: {e}")


def stop_scheduler():
    """Stop the background scheduler"""
    try:
        scheduler.shutdown()
        info("[SCHEDULER] Background scheduler stopped")
    except Exception as e:
        error(f"[SCHEDULER] Error stopping scheduler: {e}")
