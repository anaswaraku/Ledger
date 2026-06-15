"""add budgets table

Revision ID: 8b1d9c72f10b
Revises: 910a8874560d
Create Date: 2026-06-14 10:44:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8b1d9c72f10b'
down_revision: Union[str, Sequence[str], None] = '910a8874560d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('budgets',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('journal_id', sa.Uuid(), nullable=False),
    sa.Column('account_id', sa.Uuid(), nullable=False),
    sa.Column('amount', sa.Numeric(precision=28, scale=10), nullable=False),
    sa.Column('period', sa.String(length=50), nullable=False),
    sa.Column('start_date', sa.Date(), nullable=False),
    sa.Column('end_date', sa.Date(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['journal_id'], ['journals.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_budgets_account_id'), 'budgets', ['account_id'], unique=False)
    op.create_index(op.f('ix_budgets_journal_id'), 'budgets', ['journal_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_budgets_journal_id'), table_name='budgets')
    op.drop_index(op.f('ix_budgets_account_id'), table_name='budgets')
    op.drop_table('budgets')
