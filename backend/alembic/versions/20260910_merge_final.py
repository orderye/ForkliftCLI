"""merge copyright fields, payments, and ingest knowledge docs branches

Revision ID: 20260910_merge_final
Revises: ('20260910_add_copyright_fields', '20260910_add_payments', '20260910_ingest_knowledge_docs')
Create Date: 2026-09-10

"""
from alembic import op

revision = '20260910_merge_final'
down_revision = ('20260910_add_copyright_fields', '20260910_add_payments', '20260910_ingest_knowledge_docs')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass