"""Initial migration

Revision ID: ebe7a8507680
Revises: 
Create Date: 2025-07-19 14:24:41.709047

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ebe7a8507680'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('analysis',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('status', sa.String(), nullable=True),
    sa.Column('output_file', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_analysis_id'), 'analysis', ['id'], unique=False)
    op.create_table('indicator_statuses',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('status', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('file', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_indicator_statuses_id'), 'indicator_statuses', ['id'], unique=False)
    op.create_table('indicators',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('indicator_id', sa.String(), nullable=False),
    sa.Column('indicator', sa.String(), nullable=False),
    sa.Column('process_id', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_indicators_id'), 'indicators', ['id'], unique=False)
    op.create_index(op.f('ix_indicators_process_id'), 'indicators', ['process_id'], unique=False)
    op.create_table('regulations',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('file_type', sa.String(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('embedding_status', sa.String(), nullable=True),
    sa.Column('pinecone_namespace', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_regulations_id'), 'regulations', ['id'], unique=False)
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(), nullable=False),
    sa.Column('email', sa.String(), nullable=False),
    sa.Column('hashed_password', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    op.drop_index(op.f('ix_regulations_id'), table_name='regulations')
    op.drop_table('regulations')
    op.drop_index(op.f('ix_indicators_process_id'), table_name='indicators')
    op.drop_index(op.f('ix_indicators_id'), table_name='indicators')
    op.drop_table('indicators')
    op.drop_index(op.f('ix_indicator_statuses_id'), table_name='indicator_statuses')
    op.drop_table('indicator_statuses')
    op.drop_index(op.f('ix_analysis_id'), table_name='analysis')
    op.drop_table('analysis')
    # ### end Alembic commands ###
