"""add currency columns

Revision ID: f3c38b2847a9
Revises: 8b1d9c72f10b
Create Date: 2026-06-16 19:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f3c38b2847a9'
down_revision: Union[str, Sequence[str], None] = '8b1d9c72f10b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'journals',
        sa.Column('base_currency', sa.String(length=10), nullable=False, server_default='USD')
    )
    op.add_column(
        'transaction_entries',
        sa.Column('cost_amount', sa.Numeric(precision=28, scale=10), nullable=True)
    )
    op.add_column(
        'transaction_entries',
        sa.Column('cost_commodity', sa.String(length=20), nullable=True)
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('transaction_entries', 'cost_commodity')
    op.drop_column('transaction_entries', 'cost_amount')
    op.drop_column('journals', 'base_currency')
