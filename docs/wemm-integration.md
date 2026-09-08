# WeMM-Embedding 集成说明

## 接口

### `POST /api/v1/embed` (需登录)
输入:
- `text`: 文本
- `image_base64`: 图片 base64（支持 `data:image/...;base64,` 前缀）

输出:
- `vector`: 归一化向量

### `POST /api/v1/embed/search` (需登录)
输入:
- `query_text`: 文本查询
- `query_image_base64`: 图片查询
- `top_k`: 返回条数（默认 5）

输出:
- `hits[]`
  - `id`: UUID（由 `uuid5` 从 `chunk-<id>` / `fault-<id>` 稳定转换）
  - `score`: 余弦相似度
  - `payload.title`: 文档/故障标题
  - `payload.text`: 片段内容
  - `payload.url`: 来源链接

## 后端流程

- 移动端只拍照/输入
- FastAPI 负责 embedding（WeMM `model.embedding()` + Matryoshka 截断 → L2 归一化）
- Qdrant 存向量（Cosine 距离，collection 名 `forklift_multimodal`）
- AI 服务先召回（`/embed/search`），再让 LLM 生成
- OCR 仍用 PaddleOCR，负责识字；向量检索不替代 OCR/字段提取

## 关键文件

| 文件 | 作用 |
|------|------|
| `backend/app/services/embedding_service.py` | 加载 WeMM、文本/图片向量化 |
| `backend/app/core/vector_store.py` | Qdrant 客户端、collection 创建、upsert/search |
| `backend/app/api/embed.py` | `/embed`、`/embed/search` 路由 |
| `backend/app/schemas/embed.py` | 请求/响应 schema |
| `backend/app/services/ai_service.py` | `chat`/`diagnose` 注入 `_retrieve_context` |
| `backend/scripts/ingest_knowledge.py` | 把 `knowledge_chunks` + `fault_trees` 灌进 Qdrant |
| `backend/scripts/smoke_embedding.py` | 轻量自检（维度/归一/路由可导入） |
| `backend/tests/test_embedding.py` | pytest，heavy 用例靠环境变量开启 |
| `backend/tests/conftest.py` | pytest 路径注入 |
| `mobile/lib/features/embed/embed_search_page.dart` | Flutter 文本/图片检索页 |
| `mobile/lib/core/api/api_client.dart` | `searchEmbed()` 客户端方法 |

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `QDRANT_URL` | `http://localhost:6333` | Qdrant 地址 |
| `WEMM_MODEL_NAME` | `tencent/WeMM-Embedding-2B` | HF 模型 ID |
| `WEMM_EMBED_DIM` | `1024` | 向量维度 |

## 运行

```bash
# 1. 安装依赖
cd backend && pip install -r requirements.txt

# 2. 启动 Qdrant
docker run -d -p 6333:6333 qdrant/qdrant

# 3. 初始化数据库 + 种子
python scripts/seed_db.py

# 4. 启动 FastAPI
uvicorn app.main:app --reload

# 5. 灌知识库到 Qdrant
python scripts/ingest_knowledge.py

# 6. 轻量自检（不加载模型）
python scripts/smoke_embedding.py

# 7. 全量测试（可选）
WEMM_RUN_HEAVY=1 QDRANT_RUN_HEAVY=1 pytest tests/
```