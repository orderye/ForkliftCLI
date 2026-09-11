"""merge payments and account system integration

Revision ID: 20260913_merge_all
Revises: ('20260910_add_payments', '20260913_001_integrate_account_system')
Create Date: 2026-09-13

注：原先的上游 20260910_merge_final 已删除。它唯一作用是合并 payments 与
ingest_knowledge_docs 两个分支；数据播种迁移已移到链尾，因此直接在此合并。
"""
revision = '20260913_merge_all'
down_revision = ('20260910_add_payments', '20260913_001_integrate_account_system')
branch_labels = None
depends_on = None

def upgrade() -> None:
    pass

def downgrade() -> None:
    pass