"""empty message

Revision ID: 001
Revises:
Create Date: 2026-05-15
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_config",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("chat_id", sa.String(length=20), nullable=False),
        sa.Column("onboarded", sa.Integer(), nullable=True),
        sa.Column("origins", sa.String(length=200), nullable=True),
        sa.Column("destinations", sa.String(length=200), nullable=True),
        sa.Column("active", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("chat_id"),
    )
    op.create_table(
        "subscriptions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("chat_id", sa.String(length=20), nullable=False),
        sa.Column("plan", sa.String(length=20), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("chat_id"),
    )
    op.create_table(
        "price_history",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("chat_id", sa.String(length=20), nullable=False),
        sa.Column("route", sa.String(length=20), nullable=False),
        sa.Column("origin", sa.String(length=5), nullable=False),
        sa.Column("destination", sa.String(length=5), nullable=False),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("airline", sa.String(length=50), nullable=False),
        sa.Column("checked_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "alert_log",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("chat_id", sa.String(length=20), nullable=False),
        sa.Column("route", sa.String(length=20), nullable=False),
        sa.Column("alert_type", sa.String(length=20), nullable=False),
        sa.Column("difference", sa.Float(), nullable=True),
        sa.Column("sent_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("alert_log")
    op.drop_table("price_history")
    op.drop_table("subscriptions")
    op.drop_table("user_config")
