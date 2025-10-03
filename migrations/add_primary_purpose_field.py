"""Migration to add primary_purpose field to churches table"""

from alembic import op
import sqlalchemy as sa

def upgrade():
    # Add primary_purpose column to churches table
    op.add_column('churches', sa.Column('primary_purpose', sa.Text(), nullable=True))

def downgrade():
    # Remove primary_purpose column from churches table
    op.drop_column('churches', 'primary_purpose')
