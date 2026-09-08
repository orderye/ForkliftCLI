import os
import pytest

pytestmark = pytest.mark.embedding


def test_embed_dim_constant():
    from app.services.embedding_service import EMBED_DIM
    assert isinstance(EMBED_DIM, int) and EMBED_DIM > 0


def test_point_id_stability():
    from app.core.vector_store import _to_point_id
    a1 = _to_point_id("chunk-1")
    a2 = _to_point_id("chunk-1")
    b = _to_point_id("chunk-2")
    assert a1 == a2
    assert a1 != b


@pytest.mark.skipif(
    os.environ.get("WEMM_RUN_HEAVY") != "1",
    reason="set WEMM_RUN_HEAVY=1 to actually load WeMM",
)
def test_text_embedding_shape():
    from app.services.embedding_service import get_text_embedding, EMBED_DIM
    vec = get_text_embedding("门架提升缓慢")
    assert isinstance(vec, list)
    assert len(vec) == EMBED_DIM
    n = sum(x * x for x in vec) ** 0.5
    assert 0.99 < n < 1.01  # L2-normalized


@pytest.mark.skipif(
    os.environ.get("QDRANT_RUN_HEAVY") != "1",
    reason="set QDRANT_RUN_HEAVY=1 to exercise Qdrant",
)
def test_upsert_and_search_roundtrip():
    from app.core.vector_store import upsert_point, search_similar, ensure_collection
    from app.services.embedding_service import get_text_embedding

    ensure_collection()
    vec = get_text_embedding("叉车液压系统")
    upsert_point("smoke-1", vec, {"title": "smoke", "text": "叉车液压"})
    hits = search_similar(vec, top_k=3)
    assert any(h.get("payload", {}).get("title") == "smoke" for h in hits)