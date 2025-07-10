"""refactor indicator model to use indicator_id and indicator columns

Revision ID: 05ad6b08e2c8
Revises: 6fb8efe060dd
Create Date: 2025-07-10 12:05:29.018800

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '05ad6b08e2c8'
down_revision: Union[str, Sequence[str], None] = '6fb8efe060dd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table('indicators')
    op.create_table(
        'indicators',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('indicator_id', sa.String, nullable=False),
        sa.Column('indicator', sa.String, nullable=False),
    )


def downgrade() -> None:
    op.drop_table('indicators')
    op.create_table(
        'indicators',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('indicator', sa.JSON, nullable=False),
    )
