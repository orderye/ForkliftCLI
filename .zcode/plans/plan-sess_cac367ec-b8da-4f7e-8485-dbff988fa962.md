# ForkliftCLI — MVP开发计划

## 一、技术架构

```
移动端 (Flutter + Riverpod)
    │  REST API
后端 (FastAPI + SQLAlchemy)
    │
PostgreSQL + Redis + 本地文件存储
```

## 二、项目目录结构

```
ForkliftCLI/
├── mobile/                    # Flutter 移动端
│   ├── lib/
│   │   ├── app/               # 路由、主题
│   │   ├── features/          # 按功能模块
│   │   │   ├── auth/          # 登录注册
│   │   │   ├── home/          # 首页
│   │   │   ├── ocr/           # 铭牌识别
│   │   │   ├── forklift/      # 车型库、我的叉车
│   │   │   ├── engine/        # 发动机资料
│   │   │   ├── diagram/       # 结构图
│   │   │   ├── parts/         # 配件查询
│   │   │   ├── ai_assistant/  # AI维修助手
│   │   │   ├── maintenance/   # 维修记录、保养
│   │   │   └── profile/       # 个人中心
│   │   └── core/              # 网络、模型、通用组件
│   └── pubspec.yaml
│
├── backend/                   # FastAPI 后端
│   ├── app/
│   │   ├── main.py
│   │   ├── models/            # SQLAlchemy 模型
│   │   ├── schemas/           # Pydantic 校验
│   │   ├── api/               # 路由
│   │   ├── services/          # 业务逻辑
│   │   ├── core/              # 安全、中间件、数据库
│   │   └── data/              # 种子数据
│   ├── alembic/
│   └── requirements.txt
│
├── data/                      # 本地数据文件
│   ├── brands/  models/  engines/  parts/  diagrams/  knowledge/
│
└── docs/
```

## 三、12周开发排期

### 第1-2周：基础搭建
- FastAPI项目初始化 + SQLAlchemy + Alembic + PostgreSQL
- 数据库Schema设计 + 迁移
- 用户系统：注册/登录/JWT鉴权
- Flutter项目初始化 + 路由 + 主题 + 网络层
- 登录注册页面

### 第3-4周：车型数据 + OCR
- 车型/发动机数据库API（CRUD）
- 50个种子车型数据导入
- OCR服务集成（PaddleOCR）
- 铭牌解析 + 车型模糊匹配
- App车型库浏览页 + OCR拍照识别页

### 第5-6周：结构图 + 配件
- 结构图API（按车型/系统分类）
- 配件API（OEM编号/替代件/搜索）
- 爆炸图数据结构
- App整车/发动机结构图查看
- App配件搜索 + 爆炸图交互

### 第7-8周：AI维修助手
- AI服务封装（LLM调用 + Prompt管理）
- RAG知识库构建（文档→切片→Embedding→向量检索）
- 故障树数据结构
- AI对话API + 故障诊断
- App AI聊天页（文字/语音/图片输入）

### 第9-10周：我的叉车 + 维修记录
- 设备档案API + 维修记录API + 保养提醒逻辑
- App我的叉车管理页
- App维修记录页 + 保养提醒页
- App个人中心

### 第11-12周：整合发布
- 端到端测试 + 性能优化
- UI打磨（动画/空状态/错误状态）
- App首页完善（六大入口 + 底部导航）
- 离线缓存
- 打包发布（Android APK + iOS TestFlight）

## 四、关键技术决策

- **OCR：** PaddleOCR（开源免费，中文强）
- **AI：** OpenAI/通义千问API + Qdrant向量库（RAG）
- **Flutter状态管理：** Riverpod
- **结构图：** 2D InteractiveViewer + 热点坐标点击

## 五、核心API端点

认证 | OCR | 车型库 | 发动机 | 结构图 | 配件 | AI对话 | 我的叉车 | 维修记录 | 保养提醒

共约30个API端点，覆盖全部MVP功能。

## 六、开发原则

1. 先跑通再优化 — 第一周前后端联通
2. 数据先行 — 车型/配件数据是核心资产
3. 模块解耦 — 每个功能独立开发测试
4. API优先 — 先写API，App后接
5. 渐进增强 — 先核心流程，再交互细节
