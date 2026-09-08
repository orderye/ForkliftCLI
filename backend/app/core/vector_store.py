from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from app.config import get_settings
from app.services.embedding_service import EMBED_DIM

settings = get_settings()

COLLECTION = "forklift_multimodal"

# uuid5 命名空间，保证同 prefix+db_id → 同 UUID，不同 id 不碰撞
_NS = __import__("uuid").uuid5(__import__("uuid").NAMESPACE_URL, "forklift-bao-vector-store")


def get_qdrant() -> QdrantClient:
    return QdrantClient(url=settings.QDRANT_URL)


def ensure_collection(client: QdrantClient | None = None) -> None:
    client = client or get_qdrant()
    if not client.collection_exists(COLLECTION):
        client.create_collection(
            collection_name=COLLECTION,
            vectors_config=VectorParams(size=EMBED_DIM, distance=Distance.COSINE),
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


def search_similar(
    vector: list[float],
    top_k: int = 5,
    forklift_model_id: int | None = None,
    engine_model_id: int | None = None,
    client: QdrantClient | None = None,
) -> list[dict]:
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
