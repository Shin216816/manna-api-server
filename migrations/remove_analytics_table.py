"""
Remove analytics table migration

This migration removes the analytics and metrics tables since they are not used
in the current system. All analytics are calculated real-time from source data.
"""

from sqlalchemy import text
from app.utils.database import engine


def upgrade():
    """Remove analytics and metrics tables"""
    with engine.connect() as conn:
        # Drop the analytics and metrics tables
        conn.execute(text("DROP TABLE IF EXISTS analytics CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS metrics CASCADE"))
        conn.commit()
        print("✅ Dropped analytics and metrics tables")


def downgrade():
    """Recreate analytics and metrics tables (if needed for rollback)"""
    with engine.connect() as conn:
        # Recreate the analytics table structure
        conn.execute(text("""
            CREATE TABLE analytics (
                id SERIAL PRIMARY KEY,
                analytics_type VARCHAR(50) NOT NULL,
                scope_id INTEGER,
                scope_type VARCHAR(50),
                analytics_date TIMESTAMP WITH TIME ZONE NOT NULL,
                period_start TIMESTAMP WITH TIME ZONE,
                period_end TIMESTAMP WITH TIME ZONE,
                total_amount FLOAT DEFAULT 0.0,
                total_amount_cents INTEGER DEFAULT 0,
                currency VARCHAR(3) DEFAULT 'USD',
                total_count INTEGER DEFAULT 0,
                success_count INTEGER DEFAULT 0,
                failure_count INTEGER DEFAULT 0,
                growth_rate FLOAT DEFAULT 0.0,
                growth_percentage FLOAT DEFAULT 0.0,
                total_users INTEGER DEFAULT 0,
                active_users INTEGER DEFAULT 0,
                new_users INTEGER DEFAULT 0,
                total_churches INTEGER DEFAULT 0,
                active_churches INTEGER DEFAULT 0,
                new_churches INTEGER DEFAULT 0,
                total_transactions INTEGER DEFAULT 0,
                successful_transactions INTEGER DEFAULT 0,
                failed_transactions INTEGER DEFAULT 0,
                average_transaction_value FLOAT DEFAULT 0.0,
                custom_metrics JSON,
                description TEXT,
                tags JSON,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                legacy_model VARCHAR(50),
                legacy_id INTEGER
            )
        """))
        
        # Recreate the metrics table structure
        conn.execute(text("""
            CREATE TABLE metrics (
                id SERIAL PRIMARY KEY,
                metric_name VARCHAR(100) NOT NULL,
                metric_key VARCHAR(100) NOT NULL UNIQUE,
                metric_value FLOAT NOT NULL,
                metric_unit VARCHAR(50),
                metric_type VARCHAR(50) NOT NULL,
                metric_category VARCHAR(50),
                scope_id INTEGER,
                scope_type VARCHAR(50),
                period_start TIMESTAMP WITH TIME ZONE NOT NULL,
                period_end TIMESTAMP WITH TIME ZONE NOT NULL,
                context_data JSON,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """))
        conn.commit()
        print("✅ Recreated analytics and metrics tables")


if __name__ == "__main__":
    upgrade()
