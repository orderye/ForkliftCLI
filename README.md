# 叉车宝 ForkliftCLI

智能叉车维修辅助系统 — 快速识别车型、查询配件、AI 故障诊断、3D/AR 模型查看。

## 技术架构

```
┌─────────────────────────────────────────────────┐
│           Flutter Mobile (Riverpod)             │
│  登录 · 铭牌OCR · 车型库 · 配件 · AI助手 · 3D/AR │
└──────────────────────┬──────────────────────────┘
                       │ REST API
┌──────────────────────▼──────────────────────────┐
│          FastAPI Backend (SQLAlchemy)            │
│  认证 · 车型 · 发动机 · 结构图 · 配件 · AI · 维修 │
└──────────────────────┬──────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
   PostgreSQL      Redis          Qdrant
   (主数据)       (缓存)       (向量检索 RAG)
```

## 项目结构

```
├── backend/                   # FastAPI 后端
│   ├── app/
│   │   ├── api/               # REST 路由
│   │   ├── models/            # SQLAlchemy 模型
│   │   ├── schemas/           # Pydantic 校验
│   │   ├── services/          # 业务逻辑
│   │   ├── core/              # 安全、数据库、异常处理
│   │   └── data/              # 种子数据
│   ├── alembic/               # 数据库迁移
│   └── requirements.txt
│
├── mobile/                    # Flutter 移动端
│   └── lib/
│       ├── app/               # 路由、主题
│       ├── features/          # 功能模块
│       │   ├── auth/          # 登录注册
│       │   ├── home/          # 首页
│       │   ├── ocr/           # 铭牌识别
│       │   ├── forklift/      # 车型库、我的叉车
│       │   ├── engine/        # 发动机资料
│       │   ├── diagram/       # 结构图
│       │   ├── parts/         # 配件查询
│       │   ├── ai_assistant/  # AI 维修助手
│       │   ├── maintenance/   # 维修记录、保养提醒
│       │   └── profile/       # 个人中心
│       └── core/              # 网络、模型、通用组件
│
├── unity/                     # Unity 3D/AR 项目
├── data/                      # 本地数据文件
└── docs/                      # 文档
```

## 快速开始

### 后端

```bash
cd backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 填写 AI_API_KEY 等

# 启动（默认 SQLite，自动建表）
uvicorn app.main:app --reload
```

API 文档：http://127.0.0.1:8000/docs

### 移动端

```bash
cd mobile

# 安装依赖
flutter pub get

# 运行
flutter run
```

## 核心功能

| 功能 | 说明 |
|------|------|
| 铭牌 OCR | 拍照识别叉车铭牌，自动匹配车型 |
| 车型库 | 50+ 叉车品牌/车型浏览与搜索 |
| 发动机资料 | 按车型查看发动机参数与维修要点 |
| 结构图 | 整车/发动机结构图，热点交互 |
| 配件查询 | OEM 编号搜索、替代件推荐 |
| AI 维修助手 | 文字/语音/图片输入，RAG 故障诊断 |
| 我的叉车 | 设备档案管理、维修记录、保养提醒 |
| 3D/AR 模型 | Unity 渲染，AR 实景叠加 |

## 关键技术

- **OCR**：PaddleOCR（开源，中文强）
- **AI**：OpenAI / 通义千问 API + Qdrant 向量库（RAG）
- **移动端**：Flutter + Riverpod + GoRouter
- **后端**：FastAPI + SQLAlchemy + Alembic
- **3D/AR**：Unity + AR Foundation

## 开发计划

详见 [MASTER_PLAN.md](MASTER_PLAN.md)

## 许可证

私有项目，未经授权禁止使用。
