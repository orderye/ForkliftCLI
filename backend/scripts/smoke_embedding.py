"""轻量自检：向量维度 / 模块结构 / 路由可导入。

不启动模型，仅校验常量和模块结构是否正确。
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def main() -> None:
    from app.services.embedding_service import EMBED_DIM
    import numpy as np

    assert isinstance(EMBED_DIM, int) and EMBED_DIM > 0, f"bad EMBED_DIM: {EMBED_DIM}"

    # 验证 L2 归一化逻辑（内联复现）
    x = np.random.rand(1, EMBED_DIM).astype(np.float32)
    norm = np.linalg.norm(x, axis=-1, keepdims=True)
    y = x / np.clip(norm, 1e-12, None)
    assert abs(float(np.linalg.norm(y[0])) - 1.0) < 1e-3

    from app.api.embed import router
    from app.core.vector_store import COLLECTION, _to_point_id

    assert COLLECTION, "collection name must not be empty"

    # 验证 uuid5 点 ID 转换：同输入同输出，不同输入不同输出
    id_a = _to_point_id("chunk-1")
    id_b = _to_point_id("chunk-1")
    id_c = _to_point_id("chunk-2")
    assert id_a == id_b, "same input should produce same uuid"
    assert id_a != id_c, "different input should produce different uuid"

    print(f"smoke ok: dim={EMBED_DIM} collection={COLLECTION} routes={len(router.routes)}")


if __name__ == "__main__":
    main()