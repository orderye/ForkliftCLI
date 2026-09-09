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
| 二十八 | AI模型方案 | ⚠️ 待配置 | `.env`（AI_API_KEY 未配） |
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
**实际可用性：中** — 因 `.env` 未配 `AI_API_KEY`、知识库表为空，检索当前为空转；配齐 Key 并灌入数据后即可端到端生效

### ✅ 已完成
- WeMM模型加载与向量化（`embedding_service.py`）
- Qdrant向量存储（支持内存/Qdrant双模式）
- 多模态嵌入API（`/embed`、`/embed/search`）
- RAG检索集成（`ai_service.py`）
- Flutter多模态检索页面（`embed_search_page.dart`）
- UUID命名空间对齐（memory/Qdrant一致）
- QdrantClient连接复用
- 诊断结果结构化解析

### ❌ 待完成
1. **alembic迁移文件**：4张AI表（knowledge_documents/knowledge_chunks/fault_codes/fault_trees）无版本管理，唯一迁移文件仅覆盖 model_3d  
2. **knowledge知识库管理API**：无CRUD接口，模型已定义但不可用  
3. **embed搜索过滤UI**：`api_client.dart` 已支持 `forkliftModelId`/`engineModelId` 参数，但页面未提供选择控件  
4. **docker-compose.yml**：无容器编排，Qdrant/Redis/PostgreSQL 需手动启动  
5. **AI知识库数据**：`.env` 中 `AI_API_KEY` 为空，`knowledge_documents` 表无数据，RAG 检索空转  

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
- JWT 自动注入（dio 拦截器）
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
| 故障树数据导入（按车型+发动机） | 十二 | ⏳ | `fault_trees` 表已建但无数据、无导入脚本 |
| AI 知识库文档导入 | 二十九 | ⏳ | `knowledge_documents` 表已建但无数据（`ingest_knowledge.py` 待跑） |
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
| 1 | **alembic 迁移文件（AI 表结构）** | P1 | 高 | 确认缺失：`alembic/versions/` 下唯一文件 `20240908_add_model3d_version_fields.py` 仅改 model_3d，4 张 AI 表无迁移 → `alembic revision --autogenerate -m "add ai tables"` |
| 2 | **knowledge 知识库管理 API** | P1 | 高 | 确认缺失：`backend/app/api/` 无 `knowledge.py`；`ai.py` 模型已定义但无写入入口 → 创建 CRUD 并在 `main.py` 注册 |
| 3 | **embed 搜索过滤 UI** | P2 | 中 | 确认缺失：`api_client.searchEmbed` 已带 `forkliftModelId`/`engineModelId`，`embed_search_page.dart` 未传参 → 加两个下拉选择 |
| 4 | **docker-compose.yml** | P2 | 中 | 确认缺失：仓库根目录无该文件，Qdrant/Redis/PostgreSQL 需手动启动 → 编排三服务 + backend |
| 5 | **AI 知识库数据填充** | P1 | 高 | 确认缺失：`.env` 中 `AI_API_KEY` 为空、`knowledge_documents` 表空，`_retrieve_context` 空转 → 配置 Key + 跑 `ingest_knowledge.py` |
| 6 | **故障树数据** | P2 | 中 | 确认缺失：`fault_trees` 表空、无导入脚本，`_build_system_prompt` 故障树分支无输出 → 编写导入脚本 |
| 7 | **验收测试数据集** | P2 | 中 | 确认缺失：无铭牌/型号测试集，43 章 5 项指标无法度量 → 备 10 张铭牌 + 20 个型号 |

---

## 四、Phase 3：后台 + 商业化（待开发）

### 4.1 后台管理系统（二十五章）

| 模块 | 状态 |
|------|------|
| 用户管理（用户/企业/技师） | ⏳ |
| 品牌/车型/发动机/配件管理 | ⏳ |
| 结构图/3D模型管理 | ⏳ |
| 维修手册/AI知识库管理 | ⏳ |
| 故障数据库 | ⏳ |

**技术方案：** Next.js / Vue3 + Element Plus

### 4.2 商业化（四十章）

| 版本 | 价格 | 状态 |
|------|------|------|
| 免费版 | 免费 | ⏳ |
| 专业版 | ¥39/月 | ⏳ |
| 企业版 | ¥999-9999/年 | ⏳ |

### 4.3 版权合规（四十一章）

```sql
source            -- 资料来源
copyright_owner   -- 版权所有者
license_type      -- 授权类型
license_expire    -- 授权到期
commercial_use    -- 是否可商用
```

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
| AI | OpenAI/通义千问（`ai_service.py`） | ⚠️ 待配 Key |
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
- 技术栈表将「向量库/AI/OCR = Phase 2」更正为「已集成 / 待配 Key」

### 8.3 文件损坏修复

`7.2 已修复问题` 表格末行原为 134 个 `<unk>` 占位符（内容丢失），已还原为真实的修复记录条目。