"""add payments table

Revision ID: 20260910_add_payments
Revises: 20260910_merge_heads
Create Date: 2026-09-10

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "20260910_add_payments"
down_revision = "20260910_merge_heads"
branch_labels = None
depends_on = None


def _has_table(table_name: str) -> bool:
    return table_name in inspect(op.get_bind()).get_table_names()


def upgrade() -> None:
    if not _has_table("payments"):
        op.create_table(
            "payments",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("plan", sa.String(length=20), nullable=False),
            sa.Column("platform", sa.String(length=20), default="wechat"),
            sa.Column("amount", sa.Float(), nullable=False, default=0.0),
            sa.Column("status", sa.String(length=10), default="pending"),
            sa.Column("transaction_id", sa.String(length=100), default=""),
            sa.Column("payment_params", sa.Text(), default=""),
            sa.Column("created_at", sa.DateTime(), default=sa.text('CURRENT_TIMESTAMP')),
            sa.Column("updated_at", sa.DateTime(), default=sa.text('CURRENT_TIMESTAMP')),
        )
        with op.batch_alter_table("payments") as batch_op:
            batch_op.create_index("ix_payments_user_id", ["user_id"])
            batch_op.create_index("ix_payments_id", ["id"])


def downgrade() -> None:
    if _has_table("payments"):
        op.drop_table("payments")
