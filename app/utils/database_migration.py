"""
Database Migration Utility

This module handles the migration from old redundant models to new unified models.
It ensures data integrity during the transition period.
"""

import logging
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Dict, Any
from datetime import datetime, timezone



class DatabaseMigration:
    """Handles database migrations from old to new models"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def migrate_transactions(self) -> Dict[str, int]:
        """
        Migrate data from old transaction models to new unified Transaction model
        
        Returns:
            Dict with migration counts for each model
        """
        migration_counts = {
            'payment_transactions': 0,
            'payouts': 0,
            'roundups': 0,
            'donation_batches': 0,
            'payments': 0,
            'period_totals': 0
        }
        
        try:
            # Check if new transactions table exists
            result = self.db.execute(text("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_name = 'transactions'
            """))
            
            if result.scalar() == 0:
                logger.info("Transactions table doesn't exist yet. Skipping migration.")
                return migration_counts
            
            # Migrate from payment_transactions
            try:
                result = self.db.execute(text("""
                    INSERT INTO transactions (
                        type, category, status, amount_cents, currency, user_id, church_id,
                        payment_method_id, stripe_payment_intent_id, stripe_charge_id,
                        description, created_at, updated_at, legacy_model, legacy_id
                    )
                    SELECT 
                        'payment' as type,
                        CASE 
                            WHEN type = 'ROUNDUP' THEN 'roundup'
                            WHEN type = 'MANUAL' THEN 'manual'
                            WHEN type = 'RECURRING' THEN 'recurring'
                            ELSE 'manual'
                        END as category,
                        CASE 
                            WHEN status = 'PENDING' THEN 'pending'
                            WHEN status = 'PROCESSING' THEN 'processing'
                            WHEN status = 'SUCCEEDED' THEN 'succeeded'
                            WHEN status = 'FAILED' THEN 'failed'
                            WHEN status = 'CANCELLED' THEN 'cancelled'
                            WHEN status = 'REFUNDED' THEN 'refunded'
                            ELSE 'pending'
                        END as status,
                        amount_cents,
                        COALESCE(currency, 'USD') as currency,
                        user_id,
                        church_id,
                        payment_method_id,
                        stripe_payment_intent_id,
                        stripe_charge_id,
                        description,
                        created_at,
                        updated_at,
                        'payment_transactions' as legacy_model,
                        id as legacy_id
                    FROM payment_transactions
                    WHERE id NOT IN (
                        SELECT legacy_id FROM transactions 
                        WHERE legacy_model = 'payment_transactions'
                    )
                """))
                
                migration_counts['payment_transactions'] = result.rowcount
                logger.info(f"Migrated {result.rowcount} payment transactions")
                
            except Exception as e:
                logger.warning(f"Could not migrate payment_transactions: {e}")
            
            # Migrate from payouts
            try:
                result = self.db.execute(text("""
                    INSERT INTO transactions (
                        type, category, status, amount_cents, currency, church_id,
                        stripe_transfer_id, description, created_at, updated_at,
                        legacy_model, legacy_id
                    )
                    SELECT 
                        'payout' as type,
                        'payout' as category,
                        CASE 
                            WHEN status = 'pending' THEN 'pending'
                            WHEN status = 'processing' THEN 'processing'
                            WHEN status = 'completed' THEN 'succeeded'
                            WHEN status = 'failed' THEN 'failed'
                            ELSE 'pending'
                        END as status,
                        CAST(amount * 100 AS INTEGER) as amount_cents,
                        COALESCE(currency, 'USD') as currency,
                        church_id,
                        stripe_transfer_id,
                        description,
                        created_at,
                        updated_at,
                        'payouts' as legacy_model,
                        id as legacy_id
                    FROM payouts
                    WHERE id NOT IN (
                        SELECT legacy_id FROM transactions 
                        WHERE legacy_model = 'payouts'
                    )
                """))
                
                migration_counts['payouts'] = result.rowcount
                logger.info(f"Migrated {result.rowcount} payouts")
                
            except Exception as e:
                logger.warning(f"Could not migrate payouts: {e}")
            
            # Commit all migrations
            self.db.commit()
            logger.info("Transaction migration completed successfully")
            
        except Exception as e:
            logger.error(f"Error during transaction migration: {e}")
            self.db.rollback()
            raise
        
        return migration_counts
    
    def migrate_analytics(self) -> Dict[str, int]:
        """
        Migrate data from old analytics models to new unified Analytics model
        
        Returns:
            Dict with migration counts for each model
        """
        migration_counts = {
            'platform_analytics': 0,
            'platform_metrics': 0,
            'period_totals': 0
        }
        
        try:
            # Check if new analytics table exists
            result = self.db.execute(text("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_name = 'analytics'
            """))
            
            if result.scalar() == 0:
                logger.info("Analytics table doesn't exist yet. Skipping migration.")
                return migration_counts
            
            # Migrate from platform_analytics
            try:
                result = self.db.execute(text("""
                    INSERT INTO analytics (
                        analytics_type, scope_type, analytics_date,
                        total_amount, total_amount_cents, currency,
                        total_users, active_users, new_users,
                        total_churches, active_churches, new_churches,
                        total_transactions, successful_transactions, failed_transactions,
                        average_transaction_value, custom_metrics, created_at, updated_at,
                        legacy_model, legacy_id
                    )
                    SELECT 
                        'platform' as analytics_type,
                        'platform' as scope_type,
                        COALESCE(analytics_date, created_at) as analytics_date,
                        total_gmv as total_amount,
                        CAST(total_gmv * 100 AS INTEGER) as total_amount_cents,
                        'USD' as currency,
                        total_users,
                        active_users,
                        new_users_today + new_users_this_month as new_users,
                        total_churches,
                        active_churches,
                        new_churches_this_month as new_churches,
                        total_transactions,
                        successful_transactions,
                        failed_transactions,
                        average_transaction_value,
                        json_build_object(
                            'gmv', total_gmv,
                            'monthly_gmv', monthly_gmv,
                            'daily_gmv', daily_gmv,
                            'revenue', total_revenue,
                            'monthly_revenue', monthly_revenue,
                            'daily_revenue', daily_revenue,
                            'user_growth_rate', user_growth_rate,
                            'revenue_growth_rate', revenue_growth_rate,
                            'gmv_growth_rate', gmv_growth_rate,
                            'top_churches', top_churches,
                            'geographic_distribution', geographic_distribution
                        ) as custom_metrics,
                        created_at,
                        updated_at,
                        'platform_analytics' as legacy_model,
                        id as legacy_id
                    FROM platform_analytics
                    WHERE id NOT IN (
                        SELECT legacy_id FROM analytics 
                        WHERE legacy_model = 'platform_analytics'
                    )
                """))
                
                migration_counts['platform_analytics'] = result.rowcount
                logger.info(f"Migrated {result.rowcount} platform analytics records")
                
            except Exception as e:
                logger.warning(f"Could not migrate platform_analytics: {e}")
            
            # Commit all migrations
            self.db.commit()
            logger.info("Analytics migration completed successfully")
            
        except Exception as e:
            logger.error(f"Error during analytics migration: {e}")
            self.db.rollback()
            raise
        
        return migration_counts
    
    def cleanup_legacy_tables(self) -> List[str]:
        """
        Clean up legacy tables after successful migration
        
        Returns:
            List of cleaned up table names
        """
        cleaned_tables = []
        
        try:
            # List of tables to clean up (only after confirming migration success)
            legacy_tables = [
                'payment_transactions',
                'payouts', 
                'roundups',
                'donation_batches',
                'payments',
                'period_totals',
                'platform_analytics',
                'platform_metrics'
            ]
            
            for table in legacy_tables:
                try:
                    # Check if table exists and has no data
                    result = self.db.execute(text(f"""
                        SELECT COUNT(*) FROM {table}
                    """))
                    
                    if result.scalar() == 0:
                        # Drop empty table
                        self.db.execute(text(f"DROP TABLE IF EXISTS {table}"))
                        cleaned_tables.append(table)
                        logger.info(f"Cleaned up empty table: {table}")
                    
                except Exception as e:
                    logger.warning(f"Could not clean up table {table}: {e}")
            
            self.db.commit()
            logger.info("Legacy table cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during legacy table cleanup: {e}")
            self.db.rollback()
            raise
        
        return cleaned_tables
    
    def run_full_migration(self) -> Dict[str, Any]:
        """
        Run the complete migration process
        
        Returns:
            Dict with migration results
        """
        logger.info("Starting database migration process...")
        
        results = {
            'transactions': {},
            'analytics': {},
            'cleaned_tables': [],
            'success': True,
            'errors': []
        }
        
        try:
            # Step 1: Migrate transactions
            results['transactions'] = self.migrate_transactions()
            
            # Step 2: Migrate analytics
            results['analytics'] = self.migrate_analytics()
            
            # Step 3: Clean up legacy tables (only after successful migration)
            if results['transactions'] and results['analytics']:
                results['cleaned_tables'] = self.cleanup_legacy_tables()
            
            logger.info("Database migration completed successfully")
            
        except Exception as e:
            results['success'] = False
            results['errors'].append(str(e))
            logger.error(f"Migration failed: {e}")
        
        return results


def run_migration(db: Session) -> Dict[str, Any]:
    """
    Convenience function to run migration
    
    Args:
        db: Database session
        
    Returns:
        Migration results
    """
    migrator = DatabaseMigration(db)
    return migrator.run_full_migration()
