from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, JSON
from app.core.database import Base
from app.models.copyright_mixin import CopyrightMixin


class KnowledgeDocument(CopyrightMixin, Base):
    __tablename__ = "knowledge_documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    content = Column(Text, default="")
    source = Column(String(500), default="")
    doc_type = Column(String(50), default="manual")  # manual | fault | case | parameter
    category = Column(String(200), default="")
    file_type = Column(String(30), default="markdown")
    summary = Column(Text, default="")
    page_count = Column(Integer, default=0)
    forklift_model_id = Column(Integer, ForeignKey("forklift_models.id"), nullable=True)
    engine_model_id = Column(Integer, ForeignKey("engine_models.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("knowledge_documents.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    chunk_text = Column(Text, nullable=False)
    embedding_id = Column(String(100), default="")
    page_number = Column(Integer, nullable=True)
    section_title = Column(String(500), default="")
    source_locator = Column(String(500), default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class FaultCode(Base):
    __tablename__ = "fault_codes"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String(20), default="medium")  # low | medium | high | critical
    category = Column(String(50), default="")  # engine | hydraulic | electrical | brake | etc.


class FaultTree(Base):
    __tablename__ = "fault_trees"

    id = Column(Integer, primary_key=True, index=True)
    fault_code_id = Column(Integer, ForeignKey("fault_codes.id"), nullable=True)
    forklift_model_id = Column(Integer, ForeignKey("forklift_models.id"), nullable=True)
    engine_model_id = Column(Integer, ForeignKey("engine_models.id"), nullable=True)
    symptom = Column(Text, nullable=False)
    causes_json = Column(JSON, default=list)
    solutions_json = Column(JSON, default=list)
    probability_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
