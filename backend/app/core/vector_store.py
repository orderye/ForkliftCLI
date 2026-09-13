from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from app.config import get_settings
from app.services.embedding_service import EMBED_DIM
from app.core.memory_vector_store import (
    ensure_collection as memory_ensure_collection,
    upsert_point as memory_upsert_point,
    search_similar as memory_search_similar,
    delete_by_document as memory_delete_by_document,
)

settings = get_settings()

COLLECTION = "forklift_multimodal"
USE_MEMORY_STORE = settings.USE_MEMORY_STORE  # 从配置读取设置

# uuid5 命名空间，保证同 prefix+db_id → 同 UUID，不同 id 不碰撞
_NS = __import__("uuid").uuid5(__import__("uuid").NAMESPACE_URL, "forklift-bao-vector-store")

# QdrantClient 单例，避免每次调用重建连接
_qdrant_client: QdrantClient | None = None


def get_qdrant() -> QdrantClient:
    global _qdrant_client
    if _qdrant_client is None:
        _qdrant_client = QdrantClient(url=settings.QDRANT_URL)
    return _qdrant_client


def ensure_collection(client: QdrantClient | None = None) -> None:
    if USE_MEMORY_STORE:
        memory_ensure_collection(COLLECTION)
        return

    client = client or get_qdrant()
    if not client.collection_exists(COLLECTION):
        client.create_collection(
            collection_name=COLLECTION,
            vectors_config=VectorParams(size=EMBED_DIM, distance=Distance.COSINE),
        )
        return

    size = client.get_collection(COLLECTION).config.params.vectors.size
    if size != EMBED_DIM:
        raise RuntimeError(
            f"Qdrant collection '{COLLECTION}' 向量维度 {size} 与 WEMM_EMBED_DIM={EMBED_DIM} 不一致，"
            "请重建 collection 或调整 WEMM_EMBED_DIM"
        )


def _to_point_id(raw: str | int) -> str:
    """Qdrant 只接受 unsigned int 或 UUID 字符串。

    把 'chunk-123' / 'fault-456' 等业务字符串通过 uuid5 映射成稳定 UUID，
    同一 prefix+db_id 永远产出同一个 UUID，不同 id 碰撞概率为零。
    """
    import uuid as _uuid
    if isinstance(raw, int):
        return str(_uuid.UUID(int=raw))
    return str(_uuid.uuid5(_NS, str(raw)))


def upsert_point(
    point_id: str | int,
    vector: list[float],
    payload: dict,
    client: QdrantClient | None = None,
) -> None:
    if USE_MEMORY_STORE:
        memory_upsert_point(point_id, vector, payload, COLLECTION)
        return
    
    client = client or get_qdrant()
    ensure_collection(client)
    client.upsert(
        collection_name=COLLECTION,
        points=[PointStruct(id=_to_point_id(point_id), vector=vector, payload=payload)],
    )


def _build_filter(forklift_model_id: int | None = None, engine_model_id: int | None = None) -> Filter | None:
    must = []
    if forklift_model_id is not None:
        must.append(FieldCondition(
            key="forklift_model_id",
            match=MatchValue(value=forklift_model_id),
        ))
    if engine_model_id is not None:
        must.append(FieldCondition(
            key="engine_model_id",
            match=MatchValue(value=engine_model_id),
        ))
    if not must:
        return None
    return Filter(must=must)


def delete_by_document(document_id: int, client: QdrantClient | None = None) -> int:
    """删除指定知识文档的全部向量点，返回实际删除数量。"""
    if USE_MEMORY_STORE:
        return memory_delete_by_document(document_id, COLLECTION)
    client = client or get_qdrant()
    if not client.collection_exists(COLLECTION):
        return 0
    must = [FieldCondition(key="doc_id", match=MatchValue(value=document_id))]
    deleted = client.count(
        COLLECTION,
        count_filter=Filter(must=must),
        exact=True,
    ).count
    if deleted:
        client.delete(
            collection_name=COLLECTION,
            points_selector=Filter(must=must),
        )
    return deleted


def search_similar(
    vector: list[float],
    top_k: int = 5,
    forklift_model_id: int | None = None,
    engine_model_id: int | None = None,
    client: QdrantClient | None = None,
) -> list[dict]:
    if USE_MEMORY_STORE:
        return memory_search_similar(vector, top_k, COLLECTION, forklift_model_id, engine_model_id)

    client = client or get_qdrant()
    if not client.collection_exists(COLLECTION):
        return []
    query_filter = _build_filter(forklift_model_id, engine_model_id)
    resp = client.query_points(
        collection_name=COLLECTION,
        query=vector,
        limit=top_k,
        query_filter=query_filter,
    )
    return [
        {"id": h.id, "score": h.score, "payload": h.payload}
        for h in resp.points
    ]
