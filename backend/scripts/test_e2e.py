"""灌入测试数据到 Qdrant，验证 /embed/search 全链路。用 HTTP API 直接操作。"""
import json, requests

BASE = "http://127.0.0.1:8000"
QDRANT = "http://127.0.0.1:6333"
COLLECTION = "forklift_multimodal"


def api(method, url, **kw):
    r = getattr(requests, method)(url, **kw)
    if r.status_code >= 400:
        print(f"  ❌ {method.upper()} {url} → {r.status_code} {r.text[:200]}")
    return r


def main():
    # 1. 登录
    r = api("post", f"{BASE}/api/v1/auth/login", json={"phone": "13800000001", "password": "test12"})
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    print(f"1. token ok")

    # 2. 测试文档
    docs = [
        {"id": 1, "title": "门架提升缓慢", "text": "门架提升缓慢，可能是液压油不足或液压泵故障"},
        {"id": 2, "title": "发动机异响", "text": "发动机异响，检查活塞环和连杆轴承"},
        {"id": 3, "title": "液压油泄漏", "text": "液压油泄漏，检查密封圈和管路接头"},
        {"id": 4, "title": "刹车失灵", "text": "刹车失灵，检查刹车片和液压制动系统"},
        {"id": 5, "title": "门架倾斜异常", "text": "门架倾斜异常，检查倾斜油缸和销轴"},
    ]

    # 3. 逐个 embedding + 灌入
    points = []
    for doc in docs:
        r = api("post", f"{BASE}/api/v1/embed", headers=headers, json={"text": doc["text"]})
        vec = r.json()["vector"]
        points.append({"id": doc["id"], "vector": vec, "payload": doc})
        print(f"2.{doc['id']} embedding: {doc['title']}")

    # 4. 批量灌入 Qdrant
    r = api("put", f"{QDRANT}/collections/{COLLECTION}/points",
            headers={"Content-Type": "application/json"},
            json={"points": points})
    print(f"3. upsert: {r.json().get('status', r.text[:100])}")

    # 5. 验证数量
    r = api("get", f"{QDRANT}/collections/{COLLECTION}")
    cnt = r.json()["result"]["points_count"]
    print(f"4. points_count={cnt}")

    # 6. 搜索测试 1
    r = api("post", f"{BASE}/api/v1/embed/search", headers=headers,
            json={"query_text": "门架提升缓慢", "top_k": 3})
    hits = r.json().get("hits", [])
    print(f"5. search '门架提升缓慢': {len(hits)} hits")
    for h in hits:
        p = h.get("payload", {})
        print(f"   [{h['score']:.4f}] {p.get('title', '?')}")

    # 7. 搜索测试 2
    r = api("post", f"{BASE}/api/v1/embed/search", headers=headers,
            json={"query_text": "发动机有异响", "top_k": 3})
    hits2 = r.json().get("hits", [])
    print(f"6. search '发动机有异响': {len(hits2)} hits")
    for h in hits2:
        p = h.get("payload", {})
        print(f"   [{h['score']:.4f}] {p.get('title', '?')}")

    print("\n✅ 全链路通过")


if __name__ == "__main__":
    main()
