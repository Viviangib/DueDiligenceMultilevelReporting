"""add process_id to indicator model

Revision ID: 6305049a3ef4
Revises: 644b2973ff20
Create Date: 2025-07-10 15:46:13.291688

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6305049a3ef4'
down_revision: Union[str, Sequence[str], None] = '644b2973ff20'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table('indicators')
    op.create_table(
        'indicators',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('indicator_id', sa.String, nullable=False),
        sa.Column('indicator', sa.String, nullable=False),
        sa.Column('process_id', sa.String, nullable=False, index=True),
    )


def downgrade() -> None:
    op.drop_table('indicators')
    op.create_table(
        'indicators',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('indicator_id', sa.String, nullable=False),
        sa.Column('indicator', sa.String, nullable=False),
    )
