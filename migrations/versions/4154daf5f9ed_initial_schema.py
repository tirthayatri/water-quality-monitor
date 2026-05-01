"""initial schema

Revision ID: 4154daf5f9ed
Revises: 
Create Date: 2026-05-01

"""
from alembic import op
import sqlalchemy as sa

revision = '4154daf5f9ed'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('monitor_points',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('thresholds',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('indicator', sa.String(length=50), nullable=False),
        sa.Column('min_val', sa.Float(), nullable=False),
        sa.Column('max_val', sa.Float(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('indicator')
    )

    op.create_table('water_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('point_id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.Column('chlorine', sa.Float(), nullable=False),
        sa.Column('conductivity', sa.Float(), nullable=False),
        sa.Column('ph', sa.Float(), nullable=False),
        sa.Column('orp', sa.Float(), nullable=False),
        sa.Column('turbidity', sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(['point_id'], ['monitor_points.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('alarm_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('record_id', sa.Integer(), nullable=False),
        sa.Column('indicator', sa.String(length=50), nullable=False),
        sa.Column('actual_val', sa.Float(), nullable=False),
        sa.Column('threshold_val', sa.Float(), nullable=False),
        sa.Column('alarm_type', sa.String(length=10), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['record_id'], ['water_records.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('alarm_logs')
    op.drop_table('water_records')
    op.drop_table('thresholds')
    op.drop_table('monitor_points')