from app.model.m_donation_batch import DonationBatch
from app.controller.admin.execute_donation_batch import execute_donation_batch
from app.utils.database import SessionLocal
from datetime import datetime, timedelta, timezone

def retry_failed_donations():
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        batches = db.query(DonationBatch).filter(
            DonationBatch.status == "failed",
            DonationBatch.retry_attempts < 3
        ).all()

        for b in batches:
            try:
                print(f"[RETRY] Retrying batch #{b.id} (attempt {b.retry_attempts + 1})")
                b.retry_attempts += 1
                b.last_retry_at = now
                db.commit()

                execute_donation_batch(b.id, {"id": b.user_id}, db)
            except Exception as e:
                print(f"[RETRY ERROR] Batch #{b.id} still failed: {e}")
    finally:
        db.close()
