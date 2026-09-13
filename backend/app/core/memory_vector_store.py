"""内存向量存储 - 用于测试和开发环境"""
import uuid
import time
from typing import Dict, List, Optional, Any
import math

# 与 vector_store.py 保持同一 uuid5 命名空间，保证 memory / Qdrant 双模式点 ID 一致
_NS = uuid.uuid5(uuid.NAMESPACE_URL, "forklift-bao-vector-store")


class MemoryVectorStore:
    """内存向量存储实现"""

    def __init__(self):
        self.collections: Dict[str, Dict] = {}
        self.points: Dict[str, List[Dict]] = {}

    def ensure_collection(self, collection_name: str) -> None:
        """确保集合存在"""
        if collection_name not in self.collections:
            self.collections[collection_name] = {
                "name": collection_name,
                "vectors_count": 0,
                "created_at": time.time(),
            }
            self.points[collection_name] = []

    def _to_point_id(self, raw: str | int) -> str:
        """生成稳定的点ID，与 vector_store._to_point_id 逻辑完全一致。"""
        if isinstance(raw, int):
            return str(uuid.UUID(int=raw))
        return str(uuid.uuid5(_NS, str(raw)))
    
    def upsert_point(
        self,
        point_id: str | int,
        vector: List[float],
        payload: Dict,
        collection_name: str = "forklift_multimodal"
    ) -> None:
        """插入或更新点"""
        self.ensure_collection(collection_name)
        
        point_id_str = self._to_point_id(point_id)
        
        # 查找是否已存在
        existing_idx = None
        for i, point in enumerate(self.points[collection_name]):
            if point["id"] == point_id_str:
                existing_idx = i
                break
        
        if existing_idx is not None:
            # 更新现有点
            self.points[collection_name][existing_idx] = {
                "id": point_id_str,
                "vector": vector,
                "payload": payload,
                "created_at": point["created_at"],
                "updated_at": time.time()
            }
        else:
            # 插入新点
            self.points[collection_name].append({
                "id": point_id_str,
                "vector": vector,
                "payload": payload,
                "created_at": time.time(),
                "updated_at": time.time()
            })
        
        self.collections[collection_name]["vectors_count"] = len(self.points[collection_name])
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        if len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def search_similar(
        self,
        vector: List[float],
        top_k: int = 5,
        collection_name: str = "forklift_multimodal",
        forklift_model_id: Optional[int] = None,
        engine_model_id: Optional[int] = None
    ) -> List[Dict]:
        """搜索相似向量"""
        if collection_name not in self.points:
            return []
        
        # 计算相似度
        candidates = []
        for point in self.points[collection_name]:
            # 过滤条件
            if forklift_model_id is not None:
                if point["payload"].get("forklift_model_id") != forklift_model_id:
                    continue
            
            if engine_model_id is not None:
                if point["payload"].get("engine_model_id") != engine_model_id:
                    continue
            
            similarity = self.cosine_similarity(vector, point["vector"])
            candidates.append({
                "id": point["id"],
                "score": similarity,
                "payload": point["payload"]
            })
        
        # 按相似度排序
        candidates.sort(key=lambda x: x["score"], reverse=True)
        
        # 返回前top_k个结果
        return candidates[:top_k]
    
    def get_collection_info(self, collection_name: str) -> Dict:
        """获取集合信息"""
        if collection_name not in self.collections:
            return None
        
        return {
            "name": self.collections[collection_name]["name"],
            "vectors_count": self.collections[collection_name]["vectors_count"],
            "created_at": self.collections[collection_name]["created_at"]
        }
    
    def list_collections(self) -> List[str]:
        """列出所有集合"""
        return list(self.collections.keys())

# 全局实例
_memory_store = None

def get_memory_store() -> MemoryVectorStore:
    """获取内存存储实例"""
    global _memory_store
    if _memory_store is None:
        _memory_store = MemoryVectorStore()
    return _memory_store

def ensure_collection(collection_name: str = "forklift_multimodal") -> None:
    """确保集合存在"""
    get_memory_store().ensure_collection(collection_name)

def upsert_point(
    point_id: str | int,
    vector: List[float],
    payload: Dict,
    collection_name: str = "forklift_multimodal"
) -> None:
    """插入或更新点"""
    get_memory_store().upsert_point(point_id, vector, payload, collection_name)

def delete_by_document(document_id: int, collection_name: str = "forklift_multimodal") -> int:
    """删除指定知识文档的全部向量点。"""
    store = get_memory_store()
    if collection_name not in store.points:
        return 0
    before = len(store.points[collection_name])
    store.points[collection_name] = [
        point for point in store.points[collection_name]
        if point["payload"].get("doc_id") != document_id
    ]
    store.collections[collection_name]["vectors_count"] = len(store.points[collection_name])
    return before - len(store.points[collection_name])

def clear_collection(collection_name: str = "forklift_multimodal") -> None:
    """清空集合中的全部点（保留集合本身），用于缓存失效后全量重建。"""
    store = get_memory_store()
    if collection_name in store.points:
        store.points[collection_name] = []
    if collection_name in store.collections:
        store.collections[collection_name]["vectors_count"] = 0

def search_similar(
    vector: List[float],
    top_k: int = 5,
    collection_name: str = "forklift_multimodal",
    forklift_model_id: Optional[int] = None,
    engine_model_id: Optional[int] = None,
) -> List[Dict]:
    """内存模式的相似检索入口，返回结构与 Qdrant 分支一致。

    vector_store.py 从本模块转发该函数；此前只有类方法、没有模块级函数，
    导致 `from app.core.memory_vector_store import search_similar` 失败，整个 app 无法导入。
    """
    return get_memory_store().search_similar(
        vector, top_k, collection_name, forklift_model_id, engine_model_id
    )
