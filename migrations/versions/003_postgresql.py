"""Add PostgreSQL compatibility

Revision ID: 003
Revises: 002
Create Date: 2026-05-16
"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "postgresql":
        op.alter_column("price_history", "price", type_=sa.Numeric(12, 2), existing_type=sa.Float())
        op.alter_column("subscriptions", "trial_ends_at", type_=sa.DateTime(timezone=True), existing_type=sa.DateTime())
        op.create_index("ix_price_history_checked_at", "price_history", ["checked_at"], postgresql_using="brin")
        op.create_index("ix_alert_log_sent_at", "alert_log", ["sent_at"], postgresql_using="brin")


def downgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "postgresql":
        op.drop_index("ix_alert_log_sent_at", table_name="alert_log")
        op.drop_index("ix_price_history_checked_at", table_name="price_history")
