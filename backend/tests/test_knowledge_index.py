"""知识库索引同步与多模态输入边界测试。

conftest 已设置 USE_MEMORY_STORE=true 与 WEMM_FAKE_EMBEDDING=true：
全程离线、不加载真实 WeMM 模型。
"""
import base64
import io
from datetime import datetime, timedelta

import pytest
from fastapi import HTTPException
from pydantic import ValidationError


# ── Schema 边界 ────────────────────────────────────────────────────
def test_embed_request_requires_exactly_one_input():
    from app.schemas.embed import EmbedRequest

    with pytest.raises(ValidationError):
        EmbedRequest()
    with pytest.raises(ValidationError):
        EmbedRequest(text="a", image_base64="x")
    assert EmbedRequest(text="液压油更换周期").text
    assert EmbedRequest(image_base64="x").image_base64


def test_embed_request_rejects_blank_text():
    from app.schemas.embed import EmbedRequest

    with pytest.raises(ValidationError):
        EmbedRequest(text="   ")


def test_search_request_top_k_and_id_bounds():
    from app.schemas.embed import SearchRequest

    with pytest.raises(ValidationError):
        SearchRequest(query_text="q", top_k=0)
    with pytest.raises(ValidationError):
        SearchRequest(query_text="q", top_k=51)
    with pytest.raises(ValidationError):
        SearchRequest(query_text="q", forklift_model_id=0)
    assert SearchRequest(query_text="q", top_k=50).top_k == 50


# ── 图片解码边界 ──────────────────────────────────────────────────────
def _png_b64(size=(4, 4)) -> str:
    from PIL import Image as PILImage

    buf = io.BytesIO()
    PILImage.new("RGB", size, color=(10, 20, 30)).save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def test_decode_image_rejects_garbage():
    from app.api.embed import _decode_image

    raw = base64.b64encode(b"not an image").decode()
    with pytest.raises(HTTPException) as exc:
        _decode_image(raw)
    assert exc.value.status_code == 400


def test_decode_image_rejects_oversize_pixels():
    from PIL import Image as PILImage

    from app.api.embed import _decode_image

    buf = io.BytesIO()
    PILImage.new("L", (6000, 4000), color=0).save(buf, format="PNG")  # 2400 万像素
    with pytest.raises(HTTPException) as exc:
        _decode_image(base64.b64encode(buf.getvalue()).decode())
    assert exc.value.status_code == 413


def test_decode_image_accepts_valid_png():
    from app.api.embed import _decode_image

    assert _decode_image(_png_b64()).size == (4, 4)


# ── 索引同步 ────────────────────────────────────────────────────────
def _doc_points(document_id: int) -> int:
    from app.core.memory_vector_store import get_memory_store

    store = get_memory_store()
    return sum(
        1
        for p in store.points.get("forklift_multimodal", [])
        if p["payload"].get("doc_id") == document_id
    )


def _create_doc(db, **overrides):
    from app.models.ai import KnowledgeDocument

    fields = {
        "title": "索引同步测试手册",
        "content": "门架提升缓慢。优先检查液压油位与溢流阀压力。",
        "doc_type": "manual",
    }
    fields.update(overrides)
    doc = KnowledgeDocument(**fields)
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def test_sync_document_index_rebuilds_and_deletes(db_session, catalog):
    from app.services.knowledge_index_service import (
        delete_document_index,
        sync_document_index,
    )

    doc = _create_doc(
        db_session,
        forklift_model_id=catalog["model_id"],
        engine_model_id=catalog["engine_model_id"],
    )
    try:
        count = sync_document_index(db_session, doc.id, rebuild_chunks=True)
        assert count >= 2
        assert _doc_points(doc.id) == count

        # 不重建分块的增量同步，点数保持一致（先删后写）
        assert sync_document_index(db_session, doc.id) == count
        assert _doc_points(doc.id) == count
    finally:
        delete_document_index(doc.id)
    assert _doc_points(doc.id) == 0


def test_sync_skips_license_expired_document(db_session):
    from app.services.knowledge_index_service import (
        delete_document_index,
        sync_document_index,
    )

    doc = _create_doc(
        db_session,
        license_expire=datetime.utcnow() - timedelta(days=1),
    )
    try:
        assert sync_document_index(db_session, doc.id, rebuild_chunks=True) == 0
        assert _doc_points(doc.id) == 0
    finally:
        delete_document_index(doc.id)


def test_hybrid_invalidate_clears_stale_minilm_points():
    from app.core import hybrid_retriever
    from app.core.memory_vector_store import (
        get_memory_store,
        upsert_point as mem_upsert,
    )
    from app.core.minilm_retriever import COLLECTION

    mem_upsert("stale-point", [0.1] * 384, {"chunk_id": 1}, COLLECTION)
    store = get_memory_store()
    assert len(store.points.get(COLLECTION, [])) >= 1

    hybrid_retriever.invalidate()
    assert store.points.get(COLLECTION, []) == []
