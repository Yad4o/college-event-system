"""add club_join_requests table

Revision ID: a1b2c3d4e5f6
Revises: 
Create Date: 2025-01-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "a1b2c3d4e5f6"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "club_join_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("club_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.Enum("pending", "approved", "rejected", name="clubapplicationstatus"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["club_id"], ["clubs.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "club_id", name="uq_join_request"),
    )
    op.create_index("ix_club_join_requests_club_id", "club_join_requests", ["club_id"])
    op.create_index("ix_club_join_requests_user_id", "club_join_requests", ["user_id"])
    op.create_index("ix_club_join_requests_id", "club_join_requests", ["id"])

    # Add unique constraint to club_memberships if not present
    try:
        op.create_unique_constraint("uq_membership", "club_memberships", ["user_id", "club_id"])
    except Exception:
        pass


def downgrade() -> None:
    op.drop_table("club_join_requests")
