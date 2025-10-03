"""
Migration to add donor-specific models and tables
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    # Create invites table
    op.create_table(
        'invites',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('church_id', sa.Integer(), nullable=False),
        sa.Column('token_hash', sa.String(length=255), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('consumed_by_user_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['church_id'], ['churches.id'], ),
        sa.ForeignKeyConstraint(['consumed_by_user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_invites_id'), 'invites', ['id'], unique=False)
    op.create_index(op.f('ix_invites_token_hash'), 'invites', ['token_hash'], unique=True)

    # Create roundup_ledger table
    op.create_table(
        'roundup_ledger',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('transaction_id', sa.Integer(), nullable=False),
        sa.Column('roundup_cents', sa.Integer(), nullable=False),
        sa.Column('computed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(['transaction_id'], ['bank_transactions.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_roundup_ledger_id'), 'roundup_ledger', ['id'], unique=False)

    # Create period_totals table
    op.create_table(
        'period_totals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('period_key', sa.String(length=50), nullable=False),
        sa.Column('subtotal_cents', sa.Integer(), nullable=False),
        sa.Column('multiplier_applied', sa.Integer(), nullable=True),
        sa.Column('fees_applied', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_period_totals_id'), 'period_totals', ['id'], unique=False)
    op.create_index(op.f('ix_period_totals_period_key'), 'period_totals', ['period_key'], unique=False)

    # Create payments table
    op.create_table(
        'payments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('stripe_reference_id', sa.String(length=255), nullable=False),
        sa.Column('period_key', sa.String(length=50), nullable=False),
        sa.Column('amount_cents', sa.Integer(), nullable=False),
        sa.Column('method_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_payments_id'), 'payments', ['id'], unique=False)
    op.create_index(op.f('ix_payments_stripe_reference_id'), 'payments', ['stripe_reference_id'], unique=True)

    # Create consents table
    op.create_table(
        'consents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('version', sa.String(length=50), nullable=False),
        sa.Column('accepted_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('ip', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('text_snapshot', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_consents_id'), 'consents', ['id'], unique=False)

    # Create plaid_items table
    op.create_table(
        'plaid_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('item_id', sa.String(length=255), nullable=False),
        sa.Column('access_token', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_plaid_items_id'), 'plaid_items', ['id'], unique=False)
    op.create_index(op.f('ix_plaid_items_item_id'), 'plaid_items', ['item_id'], unique=True)

    # Add stripe_customer_id to users table if it doesn't exist
    op.add_column('users', sa.Column('stripe_customer_id', sa.String(length=255), nullable=True))

def downgrade():
    # Remove stripe_customer_id from users table
    op.drop_column('users', 'stripe_customer_id')
    
    # Drop tables in reverse order
    op.drop_index(op.f('ix_plaid_items_item_id'), table_name='plaid_items')
    op.drop_index(op.f('ix_plaid_items_id'), table_name='plaid_items')
    op.drop_table('plaid_items')
    
    op.drop_index(op.f('ix_consents_id'), table_name='consents')
    op.drop_table('consents')
    
    op.drop_index(op.f('ix_payments_stripe_reference_id'), table_name='payments')
    op.drop_index(op.f('ix_payments_id'), table_name='payments')
    op.drop_table('payments')
    
    op.drop_index(op.f('ix_period_totals_period_key'), table_name='period_totals')
    op.drop_index(op.f('ix_period_totals_id'), table_name='period_totals')
    op.drop_table('period_totals')
    
    op.drop_index(op.f('ix_roundup_ledger_id'), table_name='roundup_ledger')
    op.drop_table('roundup_ledger')
    
    op.drop_index(op.f('ix_invites_token_hash'), table_name='invites')
    op.drop_index(op.f('ix_invites_id'), table_name='invites')
    op.drop_table('invites')
