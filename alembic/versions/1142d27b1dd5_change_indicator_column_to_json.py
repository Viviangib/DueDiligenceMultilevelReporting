"""Change indicator column to JSON

Revision ID: 1142d27b1dd5
Revises: a7bf37ee2ee7
Create Date: 2025-07-04 12:14:28.441155

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '1142d27b1dd5'
down_revision: Union[str, Sequence[str], None] = 'a7bf37ee2ee7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        'indicators',
        'indicator',
        existing_type=sa.TEXT(),
        type_=sa.JSON(),
        existing_nullable=False,
        postgresql_using='indicator::json'
    )

def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        'indicators',
        'indicator',
        existing_type=sa.JSON(),
        type_=sa.TEXT(),
        existing_nullable=False
    )
