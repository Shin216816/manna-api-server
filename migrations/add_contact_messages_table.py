"""
Migration to add contact_messages table for visitor contact form submissions
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    # Create contact_messages table
    op.create_table(
        'contact_messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('subject', sa.String(length=500), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('category', sa.Enum('GENERAL', 'SUPPORT', 'PARTNERSHIP', 'TECHNICAL', 'FEEDBACK', name='contactcategory'), nullable=True),
        sa.Column('priority', sa.Enum('LOW', 'MEDIUM', 'HIGH', 'URGENT', name='contactpriority'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_contact_messages_id'), 'contact_messages', ['id'], unique=False)
    op.create_index('ix_contact_messages_email', 'contact_messages', ['email'], unique=False)
    op.create_index('ix_contact_messages_category', 'contact_messages', ['category'], unique=False)
    op.create_index('ix_contact_messages_created_at', 'contact_messages', ['created_at'], unique=False)

def downgrade():
    # Drop indexes first
    op.drop_index('ix_contact_messages_created_at', table_name='contact_messages')
    op.drop_index('ix_contact_messages_category', table_name='contact_messages')
    op.drop_index('ix_contact_messages_email', table_name='contact_messages')
    op.drop_index(op.f('ix_contact_messages_id'), table_name='contact_messages')
    
    # Drop table
    op.drop_table('contact_messages')
    
    # Drop enum types
    op.execute('DROP TYPE IF EXISTS contactpriority')
    op.execute('DROP TYPE IF EXISTS contactcategory')
