"""add repair manual metadata and chunk locators

Revision ID: 20260914_add_manual_metadata
Revises: 20260913_002_drop_users_email_unique

原先挂在 20260913_merge_all 上，与 20260913_002 并列形成了两个 head，
导致 `alembic upgrade head` 报 Multiple head revisions；改为顺序接在 002 之后。
"""
from alembic import op
import sqlalchemy as sa

revision = "20260914_add_manual_metadata"
down_revision = "20260913_002_drop_users_email_unique"
branch_labels = None
depends_on = None


def _add_column(table, column):
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if column.name not in {c["name"] for c in inspector.get_columns(table)}:
        op.add_column(table, column)


def upgrade():
    _add_column("knowledge_documents", sa.Column("category", sa.String(200), nullable=True, server_default=""))
    _add_column("knowledge_documents", sa.Column("file_type", sa.String(30), nullable=True, server_default="markdown"))
    _add_column("knowledge_documents", sa.Column("summary", sa.Text(), nullable=True, server_default=""))
    _add_column("knowledge_documents", sa.Column("page_count", sa.Integer(), nullable=True, server_default="0"))
    _add_column("knowledge_chunks", sa.Column("page_number", sa.Integer(), nullable=True))
    _add_column("knowledge_chunks", sa.Column("section_title", sa.String(500), nullable=True, server_default=""))
    _add_column("knowledge_chunks", sa.Column("source_locator", sa.String(500), nullable=True, server_default=""))


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    for table, names in {
        "knowledge_chunks": ("source_locator", "section_title", "page_number"),
        "knowledge_documents": ("page_count", "summary", "file_type", "category"),
    }.items():
        existing = {c["name"] for c in inspector.get_columns(table)}
        for name in names:
            if name in existing:
                op.drop_column(table, name)
