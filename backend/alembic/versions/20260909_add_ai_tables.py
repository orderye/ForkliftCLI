"""add ai tables (knowledge docs, chunks, fault codes, fault trees)

Revision ID: 20260909_add_ai_tables
Revises: 20240908_add_model3d_version_fields
Create Date: 2026-09-09

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine import reflection


revision = '20260909_add_ai_tables'
down_revision = '20240908_add_model3d_version_fields'
branch_labels = None
depends_on = None


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = reflection.Inspector.from_engine(bind)
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    # knowledge_documents - no unique constraint on title (model doesn't have it)
    if not _table_exists('knowledge_documents'):
        op.create_table(
            'knowledge_documents',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('title', sa.String(length=500), nullable=False),
            sa.Column('content', sa.Text(), default=''),
            sa.Column('source', sa.String(length=500), default=''),
            sa.Column('doc_type', sa.String(length=50), default='manual'),
            sa.Column('forklift_model_id', sa.Integer(), sa.ForeignKey('forklift_models.id'), nullable=True),
            sa.Column('engine_model_id', sa.Integer(), sa.ForeignKey('engine_models.id'), nullable=True),
            sa.Column('created_at', sa.DateTime(), default=sa.func.datetime('now')),
        )
        op.create_index('ix_knowledge_documents_id', 'knowledge_documents', ['id'])

    # knowledge_chunks - no unique constraint on (document_id, chunk_index)
    if not _table_exists('knowledge_chunks'):
        op.create_table(
            'knowledge_chunks',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('document_id', sa.Integer(), sa.ForeignKey('knowledge_documents.id'), nullable=False),
            sa.Column('chunk_index', sa.Integer(), nullable=False),
            sa.Column('chunk_text', sa.Text(), nullable=False),
            sa.Column('embedding_id', sa.String(length=100), default=''),
            sa.Column('created_at', sa.DateTime(), default=sa.func.datetime('now')),
        )
        op.create_index('ix_knowledge_chunks_id', 'knowledge_chunks', ['id'])

    # fault_codes - code is unique (model has unique=True)
    if not _table_exists('fault_codes'):
        op.create_table(
            'fault_codes',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('code', sa.String(length=50), unique=True, nullable=False),
            sa.Column('description', sa.Text(), nullable=False),
            sa.Column('severity', sa.String(length=20), default='medium'),
            sa.Column('category', sa.String(length=50), default=''),
        )
        op.create_index('ix_fault_codes_id', 'fault_codes', ['id'])

    # fault_trees - JSON defaults match model (list for causes/solutions, dict for probability)
    if not _table_exists('fault_trees'):
        op.create_table(
            'fault_trees',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('fault_code_id', sa.Integer(), sa.ForeignKey('fault_codes.id'), nullable=True),
            sa.Column('forklift_model_id', sa.Integer(), sa.ForeignKey('forklift_models.id'), nullable=True),
            sa.Column('engine_model_id', sa.Integer(), sa.ForeignKey('engine_models.id'), nullable=True),
            sa.Column('symptom', sa.Text(), nullable=False),
            sa.Column('causes_json', sa.JSON(), default=list),
            sa.Column('solutions_json', sa.JSON(), default=list),
            sa.Column('probability_json', sa.JSON(), default=dict),
            sa.Column('created_at', sa.DateTime(), default=sa.func.datetime('now')),
        )
        op.create_index('ix_fault_trees_id', 'fault_trees', ['id'])


def downgrade() -> None:
    op.drop_index('ix_fault_trees_id', table_name='fault_trees')
    op.drop_table('fault_trees')

    op.drop_index('ix_fault_codes_id', table_name='fault_codes')
    op.drop_table('fault_codes')

    op.drop_index('ix_knowledge_chunks_id', table_name='knowledge_chunks')
    op.drop_table('knowledge_chunks')

    op.drop_index('ix_knowledge_documents_id', table_name='knowledge_documents')
    op.drop_table('knowledge_documents')