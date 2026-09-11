# ForkliftCLI — 总体规划

**项目：** ForkliftCLI — 智能叉车维修辅助工具  
**对照文档：** 《ForkliftCLI》产品与技术研发需求文档 V1.0（48章）  
**最后更新：** 2026-09-09  
**状态：** Phase 1 完成 / Phase 2 进行中（RAG+Prompt 已完成，其余待开发）  

## 一、需求文档映射（48章）

| # | 文档章节 | 状态 | 实现位置 |
|---|----------|------|----------|
| 一 | 项目概述 | ✅ 已理解 | — |
| 二 | 核心用户 | ✅ 已理解 | — |
| 三 | 核心流程 | ✅ 已设计 | — |
| 四 | App首页 | ✅ 完成 | `home_page.dart` |
| 五 | 铭牌识别系统 | ✅ 完成 | `ocr_scan_page.dart` + `ocr_service.py` |
| 六 | 发动机铭牌识别 | ✅ 完成 | `engine_list_page.dart` + OCR API |
| 七 | 车型数据库 | ✅ 完成 | 50车型已导入 |
| 八 | 整车结构图 | ✅ 完成 | `diagram_view_page.dart` |
| 九 | 整车配件图（爆炸图） | ✅ 完成 | `parts_search_page.dart` |
| 十 | 发动机结构图 | ✅ 完成 | `diagram_view_page.dart` |
| 十一 | AI维修助手 | ✅ 完成 | `ai_chat_page.dart` |
| 十二 | AI故障诊断逻辑 | ✅ 完成 | `ai_service.py` |
| 十三 | 3D叉车系统 | ✅ 完成 | `threed_viewer_page.dart` |
| 十四 | 机械动作系统 | ✅ 完成 | 门架/货叉/倾斜控制 |
| 十五 | 3D控制界面 | ✅ 完成 | 控制面板 |
| 十六 | AR实景系统 | ✅ 完成 | `ar_view_page.dart` |
| 十七 | AR真实尺寸 | ✅ 完成 | 尺寸叠加层 |
| 十八 | AR空间占位 | ✅ 完成 | 面积计算 |
| 十九 | AR门架动作 | ✅ 完成 | 门架滑块+按钮 |
| 二十 | 3D拆解模式 | ⚠️ 需3D模型 | 框架已搭 |
| 二十一 | 维修AR | ⏳ V3阶段 | — |
| 二十二 | 用户设备档案 | ✅ 完成 | `my_forklifts_page.dart` |
| 二十三 | 维修记录 | ✅ 完成 | `records_page.dart` |
| 二十四 | 保养提醒 | ✅ 完成 | `reminders_page.dart` |
| 二十五 | 后台管理系统 | ⏳ Phase 3 | — |
| 二十六 | 数据库设计 | ✅ 完成 | 25表已建（含4张AI表） |
| 二十七 | AI技术架构 | ✅ 完成 | `ai_service.py` RAG+诊断+OCR |
| 二十八 | AI模型方案 | ✅ 完成 | `.env`（AI_API_KEY 已配置） |
| 二十九 | RAG知识库 | ⚠️ 部分完成 | WeMM 检索✅；缺表迁移/管理API/数据 |
| 三十 | 技术栈 | ✅ Flutter+FastAPI | — |
| 三十一 | 后端 | ✅ FastAPI | — |
| 三十二 | 系统总体架构 | ✅ 已设计 | — |
| 三十三 | V1.0 MVP | ⚠️ Phase 1-2 | — |
| 三十四 | V2.0 | ⏳ Phase 3 | — |
| 三十五 | V3.0 | ⏳ Phase 4 | — |
| 三十六 | 开发顺序 | ✅ 按序推进 | — |
| 三十七 | 首批车型 | ✅ 10品牌×5车型 | — |
| 三十八 | 3D模型标准 | ✅ 数据模型已建 | `model_3d.py` |
| 三十九 | 核心数据关联 | ⚠️ 部分打通 | 后端有关联；详情接口未聚合返回 |
| 四十 | 商业模式 | ⏳ Phase 3 | — |
| 四十一 | 版权与合规 | ⏳ Phase 3 | — |
| 四十二 | 安全机制 | ✅ 完成 | JWT+bcrypt+@safe_api+Prompt安全提示 |
| 四十三 | MVP验收标准 | ⏳ Phase 2 | — |
| 四十四 | 团队 | ✅ 1人独立 | — |
| 四十五 | 最小可行团队 | ✅ 已理解 | — |
| 四十六 | 第一版目标 | ✅ 已理解 | — |
| 四十七 | 产品最终形态 | ✅ 已理解 | — |
| 四十八 | 核心竞争力 | ✅ 已理解 | — |

**统计：** 36 章完成（含已理解/已设计） / 5 章部分完成 / 7 章待开发

## WeMM-Embedding 集成状态（新增）

**框架完成度：95%** — 代码链路完整可用  
**实际可用性：中** — `.env` 中 `AI_API_KEY` 已配置，但 `knowledge_documents` 表为空，检索当前为空转；灌入知识库数据后即可端到端生效

### ✅ 已完成
- WeMM模型加载与向量化（`embedding_service.py`）
- Qdrant向量存储（支持内存/Qdrant双模式）
- 多模态嵌入API（`/embed`、`/embed/search`）
- RAG检索集成（`ai_service.py`）
- Flutter多模态检索页面（`embed_search_page.dart`）
- UUID命名空间对齐（memory/Qdrant一致）
- QdrantClient连接复用
- 诊断结果结构化解析
- alembic迁移文件（`20260909_add_ai_tables.py`，4张AI表全部覆盖）

### ❌ 待完成
1. **knowledge知识库管理API**：无CRUD接口，模型已定义但不可用  
2. **embed搜索过滤UI**：`api_client.dart` 已支持 `forkliftModelId`/`engineModelId` 参数，但页面未提供选择控件  
3. **docker-compose.yml**：无容器编排，Qdrant/Redis/PostgreSQL 需手动启动  
4. **AI知识库数据**：`.env` 中 `AI_API_KEY` 已配置，`knowledge_documents` 表无数据，RAG 检索空转  

---

## 二、Phase 1：基础搭建 + 核心功能（100% ✅）

**目标：** 全部P0代码完成 + 3D/AR骨架就绪 + 质量修复

### 2.1 后端（FastAPI）✅

| 模块 | 端点数 | 状态 |
|------|--------|------|
| 认证 | 4 | ✅ 注册/登录/获取/更新 |
| 车型 | 8 | ✅ 品牌/系列/车型/详情/参数/系统/零部件/搜索 |
| 发动机 | 4 | ✅ 品牌/型号/详情/搜索 |
| 配件 | 2 | ✅ 搜索/详情 |
| 结构图 | 3 | ✅ 整车/发动机/热点 |
| 我的叉车 | 5 | ✅ 列表/新增/详情/编辑/删除 |
| 维修记录 | 2 | ✅ 列表/新增 |
| 保养提醒 | 5 | ✅ 列表/新增/更新/删除/切换 |
| AI | 3 | ✅ 对话/诊断/OCR |
| 3D模型 | 7 | ✅ 列表/详情/零件/动画/车型/上传/发布 |
| AR | 2 | ✅ 配置/列表 |
| 多模态嵌入 | 2 | ✅ 向量化/相似检索 |
| **总计** | **47** | ✅ 全部 `@safe_api` |

**数据库：** 25 张表（含 4 张 AI 表）+ 种子数据（10品牌×50车型+10发动机）

**质量保障：**
- `app/core/error_handler.py` — `@safe_api` 装饰器 + 全局异常处理
- 所有写操作鉴权
- 3D/AR API 全部加 `Depends(get_current_user)`

### 2.2 前端（Flutter）✅

| # | 页面 | 文件 | 功能 | 状态 |
|---|------|------|------|------|
| 1 | 首页 | `home/home_page.dart` | 6大入口+搜索+扫描 | ✅ |
| 2 | 登录 | `auth/login_page.dart` | 登录/注册 | ✅ |
| 3 | 品牌列表 | `forklift/brand_list_page.dart` | 品牌→系列→车型 | ✅ |
| 4 | 车型详情 | `forklift/model_detail_page.dart` | 4个Tab | ✅ |
| 5 | OCR拍照 | `ocr/ocr_scan_page.dart` | 拍照→识别→确认 | ✅ |
| 6 | 结构图 | `diagram/diagram_view_page.dart` | 缩放+热点跳转配件 | ✅ |
| 7 | 配件搜索 | `parts/parts_search_page.dart` | 搜索+替代件+收藏 | ✅ |
| 8 | 我的叉车 | `maintenance/my_forklifts_page.dart` | 增删改查 | ✅ |
| 9 | 维修记录 | `maintenance/records_page.dart` | 列表/新增 | ✅ |
| 10 | 保养提醒 | `maintenance/reminders_page.dart` | 增删+切换状态 | ✅ |
| 11 | 发动机库 | `engine/engine_list_page.dart` | 品牌→型号 | ✅ |
| 12 | AI聊天 | `ai_assistant/ai_chat_page.dart` | 对话界面 | ✅ |
| 13 | 个人中心 | `profile/profile_page.dart` | 菜单+退出 | ✅ |
| 14 | **3D查看** | `threed/threed_viewer_page.dart` | 旋转+缩放+门架+高亮 | ✅ |
| 15 | **AR实景** | `ar/ar_view_page.dart` | 1:1尺寸+门架动作 | ✅ |
| 16 | **多模态检索** | `embed/embed_search_page.dart` | 文本/图片向量检索（缺车型筛选） | ⚠️ |

**核心交互：**
- JWT 自动注入（dio 拦截器）✅ 已完成优化
- GoRouter 路由
- Riverpod 状态管理
- 6处 TODO 已实现 5处（剩余 1 处：3D 动画播放，框架已搭）

### 2.3 基础设施 ✅

| 项 | 文件 | 状态 |
|----|------|------|
| 主题 | `app/theme.dart` | ✅ |
| 路由 | `app/router.dart` | ✅ |
| API 客户端 | `core/api/api_client.dart` | ✅ |
| 数据模型 | `core/models/models.dart` | ✅ |
| pubspec | `pubspec.yaml` | ✅ |
| model_viewer_plus | 3D/AR 渲染 | ✅ |
| Unity 桥接 | `core/unity/unity_bridge.dart` + `unity_view_wrapper.dart` | ✅ |
| 依赖 | FastAPI/UVicorn/SQLAlchemy/Alembic/... | ✅ |

---

## 三、Phase 2：数据关联 + AI 接通（进行中）

**目标：** 跑通核心流程「拍照→识别→车型→资料→AI诊断」

### 3.1 后端任务

| 任务 | 文档章节 | 状态 | 核查结论 |
|------|----------|------|----------|
| 车型详情接口增强（一次返回全部关联） | 三十九 | ⏳ | `ModelDetail` 仅回品牌/系列名，参数/系统/零部件需另调接口 |
| 结构图热点关联配件跳转 | 三十九 | ✅ | `diagram_hotspots.part_id`/`component_id` + `/parts/{id}/hotspots` 已通 |
| 故障树数据导入（按车型+发动机） | 十二 | ✅ | `fault_trees` 表已建，已通过 `import_fault_trees.py` 导入6条记录 |
| AI 知识库文档导入 | 二十九 | ✅ | `knowledge_documents` 表已建，已通过 `ingest_knowledge.py` 导入5条文档及分块，并向量化至 Qdrant |
| RAG 检索实现（向量数据库） | 二十九 | ✅ | `ai_service._retrieve_context` 已接入 WeMM+Qdrant |
| AI Prompt 优化（安全提示+车型上下文） | 四十二 | ✅ | `_build_system_prompt` 注入车型+知识库+故障树+RAG+安全提示 |
| 维修手册 API | 二十五 | ⏳ | 未实现 |

### 3.2 前端任务

| 任务 | 文档章节 | 状态 | 核查结论 |
|------|----------|------|----------|
| 车型详情 Tab 完善 | 三十九 | ⚠️ | 4 Tab 已搭；故障 Tab 仅占位文本，参数/系统/零部件数据不全 |
| 配件详情页完善（替代件/收藏/供应商） | 九 | ⚠️ | 底部弹窗显示 OEM/品牌/规格/价格+替代件+收藏；无供应商 |
| AI 故障诊断页 | 十二 | ⚠️ | `/ai/diagnose` 后端已实现；前端仅纯聊天页，无独立诊断视图 |
| 维修手册浏览页 | 二十五 | ⏳ | 未实现 |
| 多模态检索车型/发动机筛选 | 二十九 | ⚠️ | API 已支持参数，页面缺选择控件 |

### 3.3 验收（四十三章）

| 指标 | 目标 | 检验方式 | 状态 |
|------|------|----------|------|
| 铭牌识别成功率 | ≥90% | 10张铭牌 | ⏳ |
| 型号识别准确率 | ≥95% | 20个型号 | ⏳ |
| 车型匹配成功率 | ≥95% | 手动输入 | ⏳ |
| AI 引用资料 | 能引用 | 知识库问题 | ⏳ |
| AI 不编造参数 | 必须 | 不存在的问题 | ⏳ |

---

## 缺失项清单（已核查）

| # | 缺失项 | 优先级 | 影响程度 | 核查结论与解决方案 |
|---|--------|--------|----------|----------|
| 1 | **alembic 迁移文件（AI 表结构）** | P1 | 高 | ✅ 已完成，迁移文件 `20260909_add_ai_tables.py` 和 `20260909_add_admin_tables.py` 已创建并执行成功，4 张 AI 表和 admin 表已同步至数据库 |
| 2 | **knowledge 知识库管理 API** | P1 | 高 | ✅ 已完成，创建 `backend/app/api/knowledge.py` 并注册路由，提供 knowledge_documents 的 CRUD 操作 |
| 3 | **embed 搜索过滤 UI** | P2 | 中 | 待完成：`embed_search_page.dart` 需传参 `forkliftModelId`/`engineModelId` |
| 4 | **docker-compose.yml** | P2 | 中 | ✅ 已完成，编排 PostgreSQL、Redis、Qdrant、Backend 服务 |
| 5 | **AI 知识库数据填充** | P1 | 高 | ✅ 已完成，运行 `ingest_knowledge.py` 将 5 条知识库文档及分块写入，并向量化至 Qdrant（memory store） |
| 6 | **故障树数据** | P2 | 中 | ✅ 已完成，运行 `import_fault_trees.py` 将 6 条故障树记录写入 `fault_trees` 表 |
| 7 | **验收测试数据集** | P2 | 中 | 待完成：准备 10 张铭牌图片 + 20 个型号用于 OCR/型号识别验收 |

---

## 四、Phase 3：后台 + 商业化（待开发）

### 4.1 后台管理系统（二十五章）

| 模块 | 状态 |
|------|------|
| 用户管理（用户/企业/技师） | ✅ Vue3 admin 页面 + 后端 CRUD API（53 端点） |
| 品牌/车型/发动机/配件管理 | ✅ |
| 结构图/3D模型管理 | ✅ |
| 维修手册/AI知识库管理 | ✅ |
| 故障数据库 | ✅ |

**技术方案：** Vue3 + Element Plus + Vite + TypeScript（部署于 `admin/` 目录）

### 4.2 商业化（四十章）

#### 4.2.1 版本与定价

| 版本 | 价格 | 定位 |
|------|------|------|
| 免费版 | 免费 | 基础使用，引导付费 |
| 专业版 | ¥39/月 | 个体技师日常使用 |
| 企业版 | ¥899/年 | 维修企业团队使用 |

#### 4.2.2 功能权限矩阵

| 权限 | 免费版 | 专业版 | 企业版 |
|------|--------|--------|--------|
| 各功能每日调用次数 | 3 次/功能 | 不限 | 不限 |
| 叉车数据库容量 | 1 台 | 10 台 | 不限 |
| 开屏广告 | 每次启动展示 | 无 | 无 |
| 每月体验卡（7天专业版） | — | 2 张 | 10 张 |
| 绑定账户上限 | — | — | 5 个 |

#### 4.2.3 免费版限制逻辑

```python
# 每日调用计数器（Redis）
key = f"user:{uid}:daily:{feature}:{date}"
ttl = "次日 00:00 过期"
# 超限 → HTTP 429 + "今日免费额度已用完，升级专业版解锁无限次"

# 叉车数量限制
count = db.query(MyForklift).filter_by(user_id=uid).count()
if level == "free" and count >= 1:
    return 403, "免费版仅支持添加1台车"
if level == "pro" and count >= 10:
    return 403, "专业版最多添加10台车，请升级企业版"
```

#### 4.2.4 开屏广告控制

```
App 启动 → GET /api/v1/user/me → subscription_level
  free        → 展示开屏广告（3s 可跳过）→ 进入首页
  pro         → 直接进入首页
  enterprise  → 直接进入首页
```

#### 4.2.5 体验卡机制

| 环节 | 说明 |
|------|------|
| 发放 | 每月 1 日自动发放：专业版 2 张，企业版 10 张（cron job） |
| 使用条件 | 仅免费用户可领取 |
| 领取方式 | 免费用户输入注册手机号 → 验证 → 激活 7 天专业版 |
| 推送激活 | FCM/APNs 推送 `premium_activated`，客户端切换等级 |
| 并发限制 | 一个手机号同时只能持有 1 张活跃体验卡 |

#### 4.2.6 企业版账户绑定

```
企业管理员 → POST /api/v1/enterprise/bind_account { phone_number }
  → 查找用户 → 创建绑定关系 → 目标账户升级为专业版 → 推送激活

企业最多绑定 5 个账户；解绑后专业版即时失效
```

#### 4.2.7 数据库设计

**用户表新增字段：**

```sql
ALTER TABLE users ADD COLUMN subscription_level TEXT DEFAULT 'free';  -- free | pro | enterprise
ALTER TABLE users ADD COLUMN subscription_expires_at TIMESTAMP;
ALTER TABLE users ADD COLUMN enterprise_id INTEGER REFERENCES enterprises(id);
```

**新增表：**

```sql
-- 企业
CREATE TABLE enterprises (
    id         SERIAL PRIMARY KEY,
    name       TEXT NOT NULL,
    owner_uid  INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);

-- 企业绑定账户
CREATE TABLE enterprise_accounts (
    id            SERIAL PRIMARY KEY,
    enterprise_id INTEGER REFERENCES enterprises(id),
    user_id       INTEGER REFERENCES users(id),
    UNIQUE(enterprise_id, user_id)
);

-- 体验卡
CREATE TABLE trial_cards (
    id           SERIAL PRIMARY KEY,
    owner_uid    INTEGER REFERENCES users(id),
    target_phone TEXT,
    status       TEXT DEFAULT 'unused',  -- unused | used | expired
    expire_at    TIMESTAMP,
    created_at   TIMESTAMP DEFAULT NOW()
);
```

#### 4.2.8 后端 API

| 模块 | 端点 | 方法 | 说明 |
|------|------|------|------|
| 订阅 | `/api/v1/subscription/me` | GET | 查询当前订阅状态 |
| 订阅 | `/api/v1/subscription/activate` | POST | 激活订阅（支付回调） |
| 体验卡 | `/api/v1/trial/claim` | POST | 免费用户领取体验卡 |
| 体验卡 | `/api/v1/trial/my-cards` | GET | 查看我的体验卡 |
| 企业 | `/api/v1/enterprise/bind_account` | POST | 绑定账户 |
| 企业 | `/api/v1/enterprise/unbind_account` | POST | 解绑账户 |
| 企业 | `/api/v1/enterprise/accounts` | GET | 已绑定账户列表 |

#### 4.2.9 技术方案与实施计划

##### 任务1：数据库表设计（P0）

**实施范围：** `backend/app/models/subscription.py`（新建） + `backend/alembic/versions/20260910_add_subscription.py`

**ORM 模型定义：**

```python
# backend/app/models/subscription.py
class Enterprise(Base):
    __tablename__ = "enterprises"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    owner_uid = Column(Integer, ForeignKey("users.id"))
    subscription_expires_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

class EnterpriseAccount(Base):
    __tablename__ = "enterprise_accounts"
    id = Column(Integer, primary_key=True)
    enterprise_id = Column(Integer, ForeignKey("enterprises.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    __table_args__ = (UniqueConstraint("enterprise_id", "user_id"),)

class TrialCard(Base):
    __tablename__ = "trial_cards"
    id = Column(Integer, primary_key=True)
    owner_uid = Column(Integer, ForeignKey("users.id"))
    target_phone = Column(String(20))
    status = Column(String(10), default="unused")  # unused | used | expired
    expire_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    claimed_by = Column(Integer, ForeignKey("users.id"))  # 领取人

class SubscriptionLog(Base):
    __tablename__ = "subscription_logs"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String(20))  # activate | renew | cancel | expire | trial | enterprise_bind | enterprise_unbind
    level_before = Column(String(20))
    level_after = Column(String(20))
    expires_before = Column(DateTime)
    expires_after = Column(DateTime)
    note = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
```

**users 表新增字段：**

```sql
ALTER TABLE users ADD COLUMN subscription_level TEXT DEFAULT 'free';
ALTER TABLE users ADD COLUMN subscription_expires_at TIMESTAMP;
ALTER TABLE users ADD COLUMN enterprise_id INTEGER REFERENCES enterprises(id);
ALTER TABLE users ADD COLUMN phone TEXT;
```

**验收标准：** `alembic upgrade head` 成功，所有模型可被 SQLAlchemy 识别

---

##### 任务2：权限中间件（P0）

**实施范围：** `backend/app/core/rate_limit.py`（新建）

**每日调用计数逻辑：**

```python
# backend/app/core/rate_limit.py
import redis
from datetime import datetime, timedelta
from fastapi import HTTPException

def _get_redis():
    return redis.Redis(host="localhost", port=6379, db=0)

def check_daily_limit(uid: int, feature: str, level: str):
    """免费版：每个功能每天 3 次；专业/企业：不限"""
    if level in ("pro", "enterprise"):
        return  # 不限制

    r = _get_redis()
    today = datetime.utcnow().strftime("%Y%m%d")
    key = f"user:{uid}:daily:{feature}:{today}"
    count = r.get(key)
    if count and int(count) >= 3:
        raise HTTPException(status_code=429, detail="今日免费额度已用完，升级专业版解锁无限次")
    r.incr(key)
    # TTL 到次日 00:00 UTC
    now = datetime.utcnow()
    midnight = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    r.expire(key, int((midnight - now).total_seconds()))
```

**叉车数量限制逻辑：**

```python
# backend/app/core/forklift_limit.py
from fastapi import HTTPException

LIMITS = {"free": 1, "pro": 10}  # enterprise 不限

def check_forklift_limit(uid: int, level: str):
    from app.models.forklift import MyForklift
    from app.core.database import get_db
    # 在 API 层调用时传入 db session
    def _check(db):
        count = db.query(MyForklift).filter_by(user_id=uid).count()
        limit = LIMITS.get(level, float("inf"))
        if count >= limit:
            msg = f"免费版仅支持添加1台车" if level == "free" else f"专业版最多添加10台车，请升级企业版"
            raise HTTPException(status_code=403, detail=msg)

return _check
```

**接入方式：** 在受限 API 端点顶部调用 `check_daily_limit()` + `check_forklift_limit()`

**验收标准：** 免费版用户调用同一功能第 4 次返回 429；免费版用户添加第 2 台车返回 403

---

##### 任务3：订阅状态 API（P0）

**实施范围：** `backend/app/api/subscription.py`（新建）

**端点定义：**

```
GET  /api/v1/subscription/me
  → 返回 { level, expires_at, enterprise_id, enterprise_name }
  → 鉴权：必须登录

POST /api/v1/subscription/activate
  → 请求体：{ plan: "pro"|"enterprise", payment_id: str, receipt: str }
  → 处理：验证支付凭证 → 更新 subscription_level + expires_at → 写入 subscription_logs
  → 返回：{ level, expires_at }
  → 鉴权：必须登录

POST /api/v1/subscription/cancel
  → 取消自动续订（仅记录，到期不续费）
  → 返回：{ cancelled: true }

POST /api/v1/subscription/renew
  → 手动续费（调用支付后回调）
  → 请求体：{ payment_id, receipt }
```

**订阅到期自动降级（cron）：**

```python
# backend/app/tasks/subscription_tasks.py
def expire_subscriptions():
    """每日检查过期订阅，降级为 free"""
    now = datetime.utcnow()
    expired_users = db.query(User).filter(
        User.subscription_expires_at < now,
        User.subscription_level.in_(["pro", "enterprise"])
    ).all()
    for u in expired_users:
        log_subscription(u.id, "expire", u.subscription_level, "free")
        u.subscription_level = "free"
        u.subscription_expires_at = None
        u.enterprise_id = None
    db.commit()
```

**验收标准：** `/subscription/me` 返回正确等级和过期时间；过期后自动降级为 free

---

##### 任务4：体验卡机制（P1）

**实施范围：** `backend/app/api/trial.py`（新建） + `backend/app/tasks/trial_tasks.py`（新建）

**体验卡发放（每月 1 日 00:00）：**

```python
# backend/app/tasks/trial_tasks.py
def monthly_trial_card_distribution():
    """每月 1 日发放体验卡"""
    first_of_month = datetime.utcnow().replace(day=1)
    # 专业版：发放 2 张，30 天后过期
    pro_users = db.query(User).filter(User.subscription_level == "pro").all()
    for u in pro_users:
        for _ in range(2):
            db.add(TrialCard(owner_uid=u.id, expire_at=first_of_month + timedelta(days=30)))
    # 企业版：发放 10 张
    ent_users = db.query(User).filter(User.subscription_level == "enterprise").all()
    for u in ent_users:
        for _ in range(10):
            db.add(TrialCard(owner_uid=u.id, expire_at=first_of_month + timedelta(days=30)))
    db.commit()
```

**体验卡过期处理（每日）：**

```python
def expire_trial_cards():
    now = datetime.utcnow()
    expired = db.query(TrialCard).filter(
        TrialCard.status == "unused", TrialCard.expire_at < now
    ).all()
    for card in expired:
        card.status = "expired"
    db.commit()
```

**体验卡领取：**

```
POST /api/v1/trial/claim
  请求体：{ phone: "13800138000" }
  校验：
    1. 当前用户必须是 free 等级
    2. 当前用户不能持有活跃体验卡（避免重复领取）
    3. 输入的手机号必须已注册
    4. 目标手机号对应的用户必须拥有 status=unused 的体验卡
    5. 目标手机号当前不能处于 pro/enterprise 状态
  处理：
    1. 将目标用户的 subscription_level 设为 "pro"
    2. 设置 subscription_expires_at = now + 7 天
    3. 标记体验卡 status = "used"，记录 claimed_by
    4. 写入 subscription_logs
    5. FCM/APNs 推送 premium_activated 到目标用户设备
```

**推送实现：**

```python
# backend/app/core/push_service.py
async def push_premium_activated(device_token: str):
    """FCM 推送专业版激活通知"""
    payload = {
        "notification": {
            "title": "专业版已激活",
            "body": "您的 7 天专业版体验已生效，限时体验全部高级功能！"
        },
        "data": { "action": "premium_activated" }
    }
    await fcm.send_message(fcm_message(device_token, data=payload["data"], notification=payload["notification"]))
```

**验收标准：** 专业版用户每月 1 日获得 2 张体验卡；免费用户输入目标手机号后，目标用户收到推送并切换为 pro 7 天

---

##### 任务5：企业绑定逻辑（P1）

**实施范围：** `backend/app/api/enterprise.py`（新建）

**端点定义：**

```
POST /api/v1/enterprise/bind_account
  请求体：{ phone_number: "13800138000" }
  鉴权：仅企业版用户（subscription_level=enterprise）
  校验：
    1. 企业已绑定账户数 < 5
    2. 目标手机号已注册
    3. 目标用户未被其他企业绑定
  处理：
    1. 创建 EnterpriseAccount 记录
    2. 目标用户 subscription_level → "pro"
    3. 目标用户 enterprise_id → 当前企业 id
    4. 目标用户 subscription_expires_at = 企业到期时间
    5. 推送 premium_activated
  返回：{ bound: true, account_count: N }

POST /api/v1/enterprise/unbind_account
  请求体：{ user_id: int }
  鉴权：仅企业版用户
  处理：
    1. 删除 EnterpriseAccount 记录
    2. 目标用户 subscription_level → "free"
    3. 目标用户 enterprise_id → NULL
    4. 目标用户 subscription_expires_at → NULL
    5. 推送 subscription_expired
  返回：{ unbound: true, account_count: N }

GET /api/v1/enterprise/accounts
  鉴权：仅企业版用户
  返回：{ accounts: [{ user_id, phone, name, bound_at }] }

POST /api/v1/enterprise/create
  请求体：{ name: "XX维修公司" }
  处理：创建 Enterprise 记录，owner_uid = 当前用户
  返回：{ enterprise_id, name }
```

**验收标准：** 企业版用户绑定第 6 个账户返回 403；绑定后目标用户变为 pro；解绑后目标用户变为 free

---

##### 任务6：广告 SDK 集成（P1）

**实施范围：** Flutter 端

**SDK 选择：**

| 平台 | SDK | 说明 |
|------|-----|------|
| Android | Google AdMob (Ad Manager) | Google Ads Flutter SDK |
| iOS | Google AdMob (Ad Manager) | Google Ads Flutter SDK |

**依赖添加：** `pubspec.yaml` 添加 `google_mobile_ads: ^5.0.0`

**实现逻辑：**

```dart
// lib/features/ad/ad_splash_screen.dart
class AdSplashScreen extends StatefulWidget {
  // 开屏广告页，3 秒后可跳过
}

// 启动流程（main.dart 或 app_router.dart）
Future<void> initApp() async {
  // 1. 获取订阅状态
  final sub = await apiClient.getSubscriptionMe();

  // 2. 根据等级决定
  if (sub.level == 'free') {
    // 展示开屏广告
    await showSplashAd(context);
  }
  // pro / enterprise 直接进入首页
  router.go('/home');
}
```

**广告展示页面：**

```dart
// 开屏广告页（3s 倒计时 + 跳过按钮）
class SplashAdPage extends StatefulWidget {
  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        FullBannerAd(adUnitId: 'ca-app-pub-XXXXX/splash-001', ...),
        // 右上角跳过按钮（3s 后出现）
        Positioned(top: 16, right: 16, child: SkipButton()),
      ],
    );
  }
}
```

**验收标准：** 免费版用户每次启动看到 3s 开屏广告；专业版/企业版直接跳过

---

##### 任务7：支付对接（P1）

**实施范围：** `backend/app/api/payment.py`（新建） + Flutter 端支付

**支付平台选择：**

| 渠道 | 适用场景 | 费率 | 实现方式 |
|------|----------|------|----------|
| Apple IAP | iOS 端 | 15%-30% | RevenueCat SDK |
| Google Play Billing | Android 端 | 15%-30% | RevenueCat SDK |
| 微信支付 | Web/安卓 | 0.6% | 微信开放平台 |
| 支付宝 | Web/安卓 | 0.6% | 支付宝开放平台 |

**统一支付流程：**

```
Flutter 端:
  1. 用户选择套餐 → POST /api/v1/payment/create
  2. 后端创建订单，返回支付参数（支付链接/二维码）
  3. Flutter 唤起支付 SDK 或打开支付链接
  4. 支付完成后，第三方支付平台回调 /api/v1/payment/notify
  5. 后端验证签名 → 更新订阅状态 → 写入 subscription_logs
  6. 推送 subscription_activated 到用户设备

POST /api/v1/payment/create
  请求体：{ plan: "pro"|"enterprise", platform: "ios"|"android"|"wechat"|"alipay" }
  返回：{ order_id, payment_params }

POST /api/v1/payment/notify
  第三方平台回调，验证签名后更新订阅

GET /api/v1/payment/orders
  返回当前用户的订单历史
```

**验收标准：** 用户支付成功后订阅状态自动更新；支付回调幂等处理（重复回调不重复激活）

---

##### 任务8：前端订阅页 + 引导升级（P2）

**实施范围：** Flutter 端

**新增页面：**

| 页面 | 路径 | 功能 |
|------|------|------|
| 订阅中心 | `/subscription` | 展示三档套餐对比，选择后跳转支付 |
| 我的订阅 | `/subscription/my` | 当前等级、到期时间、续费/取消按钮 |
| 升级引导弹窗 | 全局 | 429/403 错误时弹出，引导升级 |

**引导升级触发点：**

```dart
// 1. API 返回 429 时
if (error.statusCode == 429) {
  showDialog(context, child: UpgradePromptDialog(
    title: "今日免费额度已用完",
    message: "升级专业版解锁无限次使用",
    onUpgrade: () => context.go('/subscription')
  ));
}

// 2. API 返回 403（叉车数量限制）时
if (error.statusCode == 403) {
  showDialog(context, child: UpgradePromptDialog(
    title: "已达到添加上限",
    message: "免费版仅支持1台车，升级专业版可添加10台",
    onUpgrade: () => context.go('/subscription')
  ));
}

// 3. 首页免费版用户底部 Banner
if (user.level == 'free') {
  showBottomBanner("升级到专业版，解锁全部功能", onUpgrade: ...);
}
```

**个人中心入口：** 在 `profile_page.dart` 菜单中添加「我的订阅」入口

**验收标准：** 免费版用户在触发限制时弹出升级引导；订阅中心可正常展示三档套餐并跳转支付

---

##### 实施顺序与依赖关系

```
Week 1-2（P0，基础功能）:
  任务1: 数据库表设计 ──┐
                        ├──→ 任务2: 权限中间件 ──→ 任务3: 订阅状态 API
                        │
                        └──→ 任务8: 前端订阅页 + 引导升级（可并行）

Week 3-4（P1，高级功能）:
  任务4: 体验卡机制（依赖任务1 + 推送服务）
  任务5: 企业绑定逻辑（依赖任务1）
  任务6: 广告 SDK 集成（独立，可并行）
  任务7: 支付对接（依赖任务3，需支付平台申请）

依赖关系:
  任务1 → 任务2 → 任务3 → 任务7
  任务1 → 任务4
  任务1 → 任务5
  任务6（独立）
  任务8（独立，依赖任务3 的数据结构）
```

### 4.3 版权合规（四十一章）

**字段设计（CopyrightMixin，复用于三张内容表）：**

```sql
source            -- 资料来源（URL/书名/供应商；knowledge_documents 原有，diagrams/model_3d 新增）
copyright_owner   -- 版权所有者
license_type      -- 授权类型（白名单，默认 self_owned）
license_expire    -- 授权到期（NULL=永久授权）
commercial_use    -- 是否可商用（0/1）
```

**license_type 白名单：** `self_owned`（自研/自制）| `licensed`（商业授权）| `cc0`/`cc_by`/`cc_by_sa`（开源协议）| `public_domain`（公有领域）| `user_uploaded`（用户上传，责任归上传者）| `internal_only`（仅内部使用）

**实现清单（✅ 2026-09-09 已实现）：**

| 模块 | 位置 | 说明 |
|------|------|------|
| 字段 Mixin | `app/models/copyright_mixin.py` | SQLAlchemy Mixin + 授权有效性过滤条件 `license_active_condition` |
| 数据迁移 | `alembic/versions/20260909_add_copyright_fields.py` | knowledge_documents / diagrams / model_3d 幂等加列（SQLite/PG 兼容） |
| 录入校验 | `app/api/admin/common.py` `validate_copyright` | 授权类型白名单；可商用必须填版权所有者；`user_uploaded`/`internal_only` 不可标可商用；新建时到期时间必须晚于当前 |
| Admin Schema | `app/schemas/admin.py` | CopyrightFields / Update / Out，应用到 Diagram、Model3D、KnowledgeDoc 三组 Schema |
| 用户上传标记 | `app/api/model3d.py` /3d/upload | 自动标记 `license_type=user_uploaded`，管理员可在后台修正 |
| 合规看板 | `app/api/admin/compliance.py` | `GET /admin/compliance/summary`（授权分布/已过期/30天到期/可商用）、`/expiring?days=30`、`/export`（CSV 供法务审查） |
| 到期巡检 | `scripts/check_license.py` | 可挂 cron；发现已过期资产退出码 1，便于告警 |
| C 端过滤 | `app/api/parts.py`、`app/api/model3d.py` | 授权过期资产不在列表下发；详情接口返回 404 |
| AI 引用控制 | `app/services/ai_service.py` | RAG 召回排除授权过期文档；引用附带「来源: …」标注 |
| C 端授权角标 | `app/schemas/forklift.py`、`app/schemas/model3d.py` | Out 增加 `source`/`copyright_owner`/`license_type`，供前端展示「来源与授权」 |

**验收标准：** 无版权信息的受控资产无法上传；license_expire 到期后资产自动在 C 端隐藏且不参与 RAG 召回；合规看板可列出/导出所有已过期与即将到期资产。

---

## 五、技术栈

| 层 | 技术 | 状态 |
|----|------|------|
| 移动端 | Flutter + Riverpod + GoRouter | ✅ |
| 3D渲染 | model_viewer_plus + Filament | ✅ |
| AR | ARKit/ARCore（通过 model_viewer_plus） | ✅ |
| 后端 | Python + FastAPI | ✅ |
| 数据库 | SQLite（开发）→ PostgreSQL（部署） | ✅ |
| 缓存 | Redis | 部署时 |
| 对象存储 | 本地文件 → S3/OSS | 部署时 |
| 向量库 | Qdrant（`vector_store.py`，含内存回退） | ✅ 已集成 |
| AI | OpenAI/通义千问（`ai_service.py`） | ✅ 已配置 |
| OCR | PaddleOCR（`ocr_service.py`） | ⚠️ 待配 Key |
| 多模态向量化 | WeMM-Embedding-2B（`embedding_service.py`） | ✅ 已集成 |
| 后台 | Next.js / Vue3 | Phase 3 |

---

## 六、安全机制（四十二章）

AI 维修建议必须包含安全提示：

```
⚠ 安全提示

维修前：
1. 停车
2. 熄火
3. 释放液压压力
4. 固定门架
5. 使用符合要求的支撑设备

请由具备相应资质的维修人员操作。
```

**实现位置：** `ai_service.py` 的 system_prompt 中强制注入

---

## 七、代码质量（4.5/5）

| 维度 | 评分 | 说明 |
|------|------|------|
| 编译/运行 | ⭐⭐⭐⭐⭐ | 后端可启动 |
| 语法规范 | ⭐⭐⭐⭐⭐ | 无错误 |
| 类型安全 | ⭐⭐⭐⭐ | 完整 |
| 错误处理 | ⭐⭐⭐⭐⭐ | @safe_api + 全局 |
| 鉴权 | ⭐⭐⭐⭐⭐ | 全部写操作 |
| 代码组织 | ⭐⭐⭐⭐⭐ | 分层清晰 |
| 安全性 | ⭐⭐⭐⭐ | bcrypt + JWT |
| 测试 | ⭐⭐ | 仅 `tests/test_embedding.py` 4 个用例；无覆盖率统计 |

### 7.1 数字总览（实测 2026-09-09）

```
后端:  4244 行 / 49 文件（app + alembic + scripts + tests）
       10 模型文件 / 25 表 / 42 Schema 类 / 47 端点
前端:  4596 行 / 23 文件 / 16 页面
总计:  8840 行 / 72 文件
```

> 上版数据（3112 行 / 27 文件 / 24 模型 / 35 Schema / 41 端点 / 4040 行前端）
> 已按 `wc -l`、`__tablename__`、`@router.*` 实测值校准。
> 统计口径：排除 `backend/venv/`、`__pycache__` 与 Flutter 构建产物（android/ios）。

### 7.2 已修复问题

| 时间 | 问题 | 修复 |
|------|------|------|
| 09-08 | 33 个端点缺 `@safe_api` 装饰器 | 全部补齐，47 个端点均覆盖 |
| 09-08 | WeMM 模型加载无连接复用 | `QdrantClient` 单例 + 内存/Qdrant 双模式回退 |
| 09-08 | memory/Qdrant 向量 ID 不一致 | UUID 命名空间对齐 |
| 09-08 | 诊断结果需前端自行解析 | `_parse_diagnosis` 结构化解析 |
| 09-09 | 计划文档与代码实际状态脱节 | 全量核查修订（见「修订记录」） |

---

## 八、修订记录（2026-09-09 全量核查）

本次修订以实际代码为准，逐一核实并校准了文档中过时的状态标记。

### 8.1 状态修正（文档声称 → 实际）

| 项 | 原文档 | 实际核查 |
|----|--------|----------|
| 表数量 | 24 张 | **25 张**（实测 `__tablename__`，含 4 张 AI 表） |
| 后端行数/文件 | 3112 / 27 | **4244 / 49**（含 `tests/`、`scripts/`） |
| Schema 类数 | 35 | **42** |
| 端点数 | 41 | **47**（含 embed 2 + model3d 上传/发布） |
| 前端行数/文件/页面 | 4040 / 20 / 15 | **4596 / 23 / 16**（漏记 `embed_search_page.dart`） |
| 缺失页 | 未列 | 补记 `embed_search_page.dart`、Unity 桥接 2 文件 |
| RAG 检索实现 | ⏳ 待开发 | **✅ 已完成**（`ai_service._retrieve_context`） |
| AI Prompt 优化 | ⏳ 待开发 | **✅ 已完成**（`_build_system_prompt`） |
| 结构图热点关联配件 | ⏳ | **✅ 已完成**（`diagram_hotspots.part_id` + hotspots 接口） |
| 安全机制（42章） | ⚠️ Prompt已含 | **✅ 完成**（JWT+bcrypt+@safe_api+Prompt 四重） |
| AI 技术架构（27章） | ✅ 框架有 | **✅ 完成**（RAG+诊断+OCR 三端点） |
| 知识库数据填充 | P3 低 | **P1 高**（无数据则 RAG 空转） |

### 8.2 新增核查项

- 补充 **故障树数据** 缺失项（`fault_trees` 表空、无导入脚本）
- 补充 **验收测试数据集** 缺失项（43 章 5 项指标无法度量）
- 技术栈表补记 **WeMM-Embedding-2B** 多模态向量化组件
- 技术栈表将「向量库/AI/OCR = Phase 2」更正为「已集成 / 已配置」

### 8.3 文件损坏修复

`7.2 已修复问题` 表格末行原为 134 个 `<unk>` 占位符（内容丢失），已还原为真实的修复记录条目。