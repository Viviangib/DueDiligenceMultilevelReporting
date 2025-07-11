"""add process_id to indicator model

Revision ID: 644b2973ff20
Revises: 05ad6b08e2c8
Create Date: 2025-07-10 15:41:34.394911

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '644b2973ff20'
down_revision: Union[str, Sequence[str], None] = '05ad6b08e2c8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
