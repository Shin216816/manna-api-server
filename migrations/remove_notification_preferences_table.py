"""
Remove notification_preferences table migration

This migration removes the notification_preferences table since it's not used
in the current system. Notification preferences are handled via UserSettings model.
"""

import logging
import os
import sys
from sqlalchemy import text

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.database import engine

def upgrade():
    """Remove the notification_preferences table"""
    with engine.connect() as conn:
        # Drop the notification_preferences table
        conn.execute(text("DROP TABLE IF EXISTS notification_preferences CASCADE"))
        
        conn.commit()
    
    print("✅ notification_preferences table removed successfully")

def downgrade():
    """Recreate the notification_preferences table (if needed for rollback)"""
    with engine.connect() as conn:
        # Recreate the table
        conn.execute(text("""
            CREATE TABLE notification_preferences (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL UNIQUE,
                email_enabled BOOLEAN DEFAULT true,
                email_donations BOOLEAN DEFAULT true,
                email_roundups BOOLEAN DEFAULT true,
                email_kyc BOOLEAN DEFAULT true,
                email_system BOOLEAN DEFAULT true,
                email_marketing BOOLEAN DEFAULT false,
                sms_enabled BOOLEAN DEFAULT false,
                sms_donations BOOLEAN DEFAULT false,
                sms_roundups BOOLEAN DEFAULT false,
                sms_kyc BOOLEAN DEFAULT true,
                sms_system BOOLEAN DEFAULT true,
                push_enabled BOOLEAN DEFAULT true,
                push_donations BOOLEAN DEFAULT true,
                push_roundups BOOLEAN DEFAULT true,
                push_kyc BOOLEAN DEFAULT true,
                push_system BOOLEAN DEFAULT true,
                in_app_enabled BOOLEAN DEFAULT true,
                in_app_donations BOOLEAN DEFAULT true,
                in_app_roundups BOOLEAN DEFAULT true,
                in_app_kyc BOOLEAN DEFAULT true,
                in_app_system BOOLEAN DEFAULT true,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
                updated_at TIMESTAMP WITH TIME ZONE
            )
        """))
        
        # Create indexes
        conn.execute(text("CREATE INDEX ix_notification_preferences_id ON notification_preferences USING btree (id)"))
        conn.execute(text("CREATE INDEX ix_notification_preferences_user_id ON notification_preferences USING btree (user_id)"))
        
        conn.commit()
    
    print("✅ notification_preferences table recreated (rollback)")

if __name__ == "__main__":
    upgrade()
