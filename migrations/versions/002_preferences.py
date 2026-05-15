"""empty message

Revision ID: 002
Revises: 001
Create Date: 2026-05-15
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("user_config", sa.Column("luggage", sa.String(20), server_default="carry_on"))
    op.add_column("user_config", sa.Column("adults", sa.Integer(), server_default="2"))
    op.add_column("user_config", sa.Column("max_budget", sa.Float(), nullable=True))
    op.add_column("user_config", sa.Column("non_stop_only", sa.Integer(), server_default="0"))
    op.add_column("price_history", sa.Column("booking_link", sa.String(500), nullable=True))
    op.add_column("price_history", sa.Column("luggage_match", sa.Integer(), server_default="0"))
    op.add_column("price_history", sa.Column("budget_match", sa.Integer(), server_default="0"))
    op.add_column("subscriptions", sa.Column("trial_ends_at", sa.DateTime(), nullable=True))
    op.add_column("subscriptions", sa.Column("api_requests_month", sa.Integer(), server_default="0"))
    op.add_column("subscriptions", sa.Column("api_requests_limit", sa.Integer(), server_default="10"))


def downgrade() -> None:
    op.drop_column("subscriptions", "api_requests_limit")
    op.drop_column("subscriptions", "api_requests_month")
    op.drop_column("subscriptions", "trial_ends_at")
    op.drop_column("price_history", "budget_match")
    op.drop_column("price_history", "luggage_match")
    op.drop_column("price_history", "booking_link")
    op.drop_column("user_config", "non_stop_only")
    op.drop_column("user_config", "max_budget")
    op.drop_column("user_config", "adults")
    op.drop_column("user_config", "luggage")
