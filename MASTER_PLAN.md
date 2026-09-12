# ForkliftCLI — 总体规划

**项目：** ForkliftCLI — 智能叉车维修辅助工具  
**对照文档：** 《ForkliftCLI》产品与技术研发需求文档 V1.0（48章）  
**最后更新：** 2026-09-12（Unity 3D/AR 模块完成度与接入度实测）  
**状态：** Phase 1 完成 / Phase 2 完成 / Phase 3 已完成（后台+商业化+版权合规） / 验收待执行  
**⚠️ 3D/AR 架构变更：** 渲染已从 Unity 迁移到 Web 渲染器（`<model-viewer>` + Three.js）。
Unity 工程仍在仓库中但**不在运行时路径上**，细节见「九、Unity 3D/AR 模块状态」  

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
| 十二 | AI故障诊断逻辑 | ✅ 完成 | `ai_service.py` + `ai_diagnosis_page.dart` |
| 十三 | 3D叉车系统 | ⚠️ 链路已通，待真机验证 | `threed/threed_viewer_page_v2.dart`（Web）；模型文件已恢复 |
| 十四 | 机械动作系统 | ⚠️ 代码通，无数据 | Web `playAnimation`/Unity `AnimationController`；`model_3d_animations`=0 行 |
| 十五 | 3D控制界面 | ⚠️ 部分可用 | 相机控制✅；自动旋转开关未接线、动画/清高亮无入口 |
| 十六 | AR实景系统 | ⚠️ 仅 lite 可试 | WebXR immersive-ar 在 WebView 内不可用，只有 `<model-viewer>` AR 按钮 |
| 十七 | AR真实尺寸 | ⚠️ 已录入 1 台车，待真机验证 | `ar_model_config` 已写入 8FG30 实测尺寸；其余车型仍无数据 |
| 十八 | AR空间占位 | ⚠️ 仅 Unity 侧有 | Web 渲染器不支持（`MIGRATION.md` 已标注） |
| 十九 | AR门架动作 | ⚠️ 仅 Unity 侧有 | 同上映射到动画；无动画数据 |
| 二十 | 3D拆解模式 | ⚠️ 需模型资产 | Web `setExploded` 已实现；待真实 GLB + 零件映射 |
| 二十一 | 维修AR | ⚠️ 未提交 | `maintenance_guide_page.dart`（Web 版已写，git untracked）；Unity 侧 `ARRepairGuide` 有实现 |
| 二十二 | 用户设备档案 | ✅ 完成 | `my_forklifts_page.dart` |
| 二十三 | 维修记录 | ✅ 完成 | `records_page.dart` |
| 二十四 | 保养提醒 | ✅ 完成 | `reminders_page.dart` |
| 二十五 | 后台管理系统 | ✅ 完成 | Vue3 admin（12页面）+ 后端 CRUD（58端点） |
| 二十六 | 数据库设计 | ✅ 完成 | 31张表已建（含4张AI表+3张商业化表+1张审计表） |
| 二十七 | AI技术架构 | ✅ 完成 | `ai_service.py` RAG+诊断+OCR |
| 二十八 | AI模型方案 | ✅ 完成 | `.env`（AI_API_KEY 已配置，GLM-4.5-air） |
| 二十九 | RAG知识库 | ✅ 完成 | WeMM 检索✅；知识库管理API✅；数据已灌入✅ |
| 三十 | 技术栈 | ✅ Flutter+FastAPI | — |
| 三十一 | 后端 | ✅ FastAPI | — |
| 三十二 | 系统总体架构 | ✅ 已设计 | 含 account-service 代理架构 |
| 三十三 | V1.0 MVP | ✅ Phase 1-2 完成 | — |
| 三十四 | V2.0 | ✅ Phase 3 完成 | — |
| 三十五 | V3.0 | ⏳ Phase 4 | — |
| 三十六 | 开发顺序 | ✅ 按序推进 | — |
| 三十七 | 首批车型 | ✅ 10品牌×5车型 | — |
| 三十八 | 3D模型标准 | ✅ 数据模型已建 | `model_3d.py` |
| 三十九 | 核心数据关联 | ✅ 已打通 | 后端关联✅；详情接口聚合✅；维修手册按车型检索✅ |
| 四十 | 商业模式 | ✅ Phase 3 完成 | 订阅/支付/体验卡/企业绑定 全部实现 |
| 四十一 | 版权与合规 | ✅ 完成 | CopyrightMixin + 合规看板 + 到期巡检 + C端过滤 + AI引用控制 |
| 四十二 | 安全机制 | ✅ 完成 | JWT+bcrypt+@safe_api+Prompt安全提示 + admin token隔离 |
| 四十三 | MVP验收标准 | ⏳ 待执行 | 5项指标待度量（验收脚本已有） |
| 四十四 | 团队 | ✅ 1人独立 | — |
| 四十五 | 最小可行团队 | ✅ 已理解 | — |
| 四十六 | 第一版目标 | ✅ 已理解 | — |
| 四十七 | 产品最终形态 | ✅ 已理解 | — |
| 四十八 | 核心竞争力 | ✅ 已理解 | — |

**统计：** 37 章完成（含已理解/已设计） / 9 章部分完成 / 2 章待执行（含 V3.0 AR维修）

> **2026-09-12 修正：** 第三章统计的 3D/AR 各章此前按 Unity V1 页面标记为「✅ 完成」。
> 实测发现：① 3D/AR 渲染已迁移到 Web 渲染器，Unity 工程不在运行时路径上；
> ② 模型二进制缺失（`backend/uploads/` 为空）、`model_3d_parts`/`model_3d_animations`/
> `ar_model_config` 均为 0 行，导致链路端到端不通。故十三~十九、二十一改为 ⚠️，
> 十七（AR真实尺寸）因无数据降为 ❌。详见「九、Unity 3D/AR 模块状态」
>
> **同日数据断点已修复**（见 8.5）：模型文件按哈希找回、`ar_model_config` 已录入
> 8FG30 实测尺寸、`model_3d_parts` 已按真实节点写入。十三、十七回升为 ⚠️。
> 3D/AR 链路代码与数据已齐，**剩余卡点是本机无 Flutter SDK，真机行为未验证**。

> **2026-09-12 修正：** 第三章统计的 3D/AR 各章此前按 Unity V1 页面标记为「✅ 完成」。
> 实测发现：① 3D/AR 渲染已迁移到 Web 渲染器，Unity 工程不在运行时路径上；
> ② 模型二进制缺失（`backend/uploads/` 为空）、`model_3d_parts`/`model_3d_animations`/
> `ar_model_config` 均为 0 行，导致链路端到端不通。故十三~十九、二十一改为 ⚠️，
> 十七（AR真实尺寸）因无数据降为 ❌。详见「九、Unity 3D/AR 模块状态」

## WeMM-Embedding 集成状态

**框架完成度：100%** — 代码链路完整可用  
**实际可用性：高** — `.env` 中 `AI_API_KEY` 已配置（GLM-4.5-air），`knowledge_documents` 表已灌入 5 条文档及分块，向量化至 Qdrant/memory store

### ✅ 已完成
- WeMM模型加载与向量化（`embedding_service.py`）
- Qdrant向量存储（支持内存/Qdrant双模式，`vector_store.py` + `memory_vector_store.py`）
- 多模态嵌入API（`/embed`、`/embed/search`）
- RAG检索集成（`ai_service._retrieve_context`），含授权过期文档过滤
- Flutter多模态检索页面（`embed_search_page.dart`）
- UUID命名空间对齐（memory/Qdrant一致）
- QdrantClient连接复用
- 诊断结果结构化解析（`_parse_diagnosis`）
- alembic迁移文件（14个，含 base_schema + reconcile_legacy + AI表 + 商业化表 + 手册元数据）

### ✅ 已完成（此前标记为待完成）
1. **knowledge知识库管理API**：✅ `app/api/knowledge.py` CRUD + 分块查询（6端点）  
2. **embed搜索过滤UI**：⚠️ API已支持 `forkliftModelId`/`engineModelId` 参数，页面选择控件仍缺  
3. **docker-compose.yml**：✅ 编排 PostgreSQL/Redis/Qdrant/Backend + Dockerfile  
4. **AI知识库数据填充**：✅ `ingest_knowledge.py` 导入5条文档及分块，向量化至 Qdrant（memory store）  

---

## 二、Phase 1：基础搭建 + 核心功能（100% ✅）

**目标：** 全部P0代码完成 + 3D/AR骨架就绪 + 质量修复

### 2.1 后端（FastAPI）✅

| 模块 | 端点数 | 状态 |
|------|--------|------|
| 认证 | 4 | ✅ 注册/登录/获取/更新（委托 account-service） |
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
| 知识库管理 | 6 | ✅ CRUD + 分块查询 |
| 维修手册 | 5 | ✅ 列表/按车型/搜索/详情/分块 |
| 订阅 | 4 | ✅ 查询/激活/取消/续费（本地实现，main.py 走代理转发） |
| 体验卡 | 2 | ✅ 查看我的/领取（同上） |
| 企业绑定 | 3 | ✅ 绑定/解绑/列表 |
| 支付 | 3 | ✅ 创建订单/回调/历史 |
| 账户代理 | 5 | ✅ /subscription /payment /enterprise /trial /public 透传 |
| **C端合计** | **71** | ✅ 59注册 + 12本地回退 |
| 后台管理 | 58 | ✅ 用户/企业/目录/资产/知识库/合规/看板/审计 |
| **总计** | **129** | ✅ 全部 `@safe_api`（代理路由除外） |

**数据库：** 31 张表 + 种子数据（10品牌×50车型+10发动机）

**质量保障：**
- `app/core/error_handler.py` — `@safe_api` 装饰器 + 全局异常处理
- 所有写操作鉴权
- 3D/AR API 全部加 `Depends(get_current_user)`
- 管理员 token 与用户 token 密钥隔离（`SECRET_KEY` vs `SECRET_KEY + ":admin"`）

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
| 13 | **AI故障诊断** | `ai_assistant/ai_diagnosis_page.dart` | 结构化诊断（症状/原因/检查/安全） | ✅ |
| 14 | 个人中心 | `profile/profile_page.dart` | 菜单+退出 | ✅ |
| 15 | 3D查看 | `threed/threed_viewer_page_v2.dart`（Web 渲染器，现役） | 旋转+缩放+高亮 | ⚠️ 自动旋转未接线、动画无入口 |
| 15b | 3D查看 V1 | `threed/threed_viewer_page.dart`（Unity，已弃用未路由） | — | ⚠️ 死代码 |
| 16 | AR实景 | `ar/ar_view_page_v2.dart`（Web，现役） | `<model-viewer>` AR | ⚠️ WebXR 不可用、无 1:1 数据 |
| 16b | AR实景 V1 | `ar/ar_view_page.dart`（Unity，已弃用未路由） | — | ⚠️ 死代码 |
| 16c | 维修指导 | `viewer/maintenance_guide_page.dart` | 高亮+爆炸+测量 | ⚠️ 已写，git untracked |
| 17 | 多模态检索 | `embed/embed_search_page.dart` | 文本/图片向量检索（缺车型筛选） | ⚠️ |
| 18 | **维修手册列表** | `manual/manual_list_page.dart` | 手册列表+按车型筛选 | ✅ |
| 19 | **维修手册详情** | `manual/manual_detail_page.dart` | 手册元数据+版权信息 | ✅ |
| 20 | **维修手册阅读** | `manual/manual_reader_page.dart` | 分块阅读+分页 | ✅ |
| 21 | **订阅中心** | `subscription/subscription_page.dart` | 套餐展示+当前等级 | ✅ |
| 22 | **套餐对比** | `subscription/plans_page.dart` | 四档套餐对比 | ✅ |
| 23 | **体验卡** | `subscription/trial_page.dart` | 领取体验卡 | ✅ |
| 24 | **企业管理** | `subscription/enterprise_page.dart` | 绑定/解绑账户 | ✅ |
| 25 | **升级弹窗** | `subscription/upgrade_dialog.dart` | 429/403引导升级 | ✅ |
| 26 | **开屏广告** | `ad/splash_ad_page.dart` | 3s可跳过广告 | ✅ |

**核心交互：**
- JWT 自动注入（dio 拦截器）✅ 已完成优化
- GoRouter 路由（含维修手册/订阅路由）✅
- Riverpod 状态管理 ✅
- 6处 TODO 已实现 5处（剩余 1 处：3D 动画播放，框架已搭）

### 2.3 基础设施 ✅

| 项 | 文件 | 状态 |
|----|------|------|
| 主题 | `app/theme.dart` | ✅ |
| 路由 | `app/router.dart` | ✅ |
| API 客户端 | `core/api/api_client.dart` | ✅ 37个方法覆盖全部C端API |
| 数据模型 | `core/models/models.dart` | ✅ |
| pubspec | `pubspec.yaml` | ✅ |
| Web 3D/AR 渲染 | `mobile/lib/viewer/`（14 文件 / 1659 行）+ `assets/viewer_{lite,full}.html`（654 行） | ⚠️ 未提交；CDN 依赖无离线 |
| model_viewer_plus | pubspec 中仍声明，**lib 下 0 处引用** | ⚠️ 死依赖 |
| Unity 桥接 | `core/unity/unity_bridge.dart` + `unity_view_wrapper.dart` | ⚠️ `@deprecated`，仅留作回退 |
| 依赖 | FastAPI/UVicorn/SQLAlchemy/Alembic/... | ✅ |
| Docker | `backend/Dockerfile` + `docker-compose.yml` | ✅ PostgreSQL/Redis/Qdrant/Backend |
| 环境配置 | `backend/.env` + `.env.example` | ✅ |

---

## 三、Phase 2：数据关联 + AI 接通（100% ✅）

**目标：** 跑通核心流程「拍照→识别→车型→资料→AI诊断」

### 3.1 后端任务

| 任务 | 文档章节 | 状态 | 核查结论 |
|------|----------|------|----------|
| 车型详情接口增强（一次返回全部关联） | 三十九 | ✅ | `ModelDetail` 返回品牌/系列名；参数/系统/零部件有独立端点；维修手册按车型检索已通 |
| 结构图热点关联配件跳转 | 三十九 | ✅ | `diagram_hotspots.part_id`/`component_id` + `/parts/{id}/hotspots` 已通 |
| 故障树数据导入（按车型+发动机） | 十二 | ✅ | `fault_trees` 表已建，已通过 `import_fault_trees.py` 导入6条记录 |
| AI 知识库文档导入 | 二十九 | ✅ | `knowledge_documents` 表已建，已通过 `ingest_knowledge.py` 导入5条文档及分块，并向量化至 Qdrant |
| RAG 检索实现（向量数据库） | 二十九 | ✅ | `ai_service._retrieve_context` 已接入 WeMM+Qdrant，含授权过期过滤 |
| AI Prompt 优化（安全提示+车型上下文） | 四十二 | ✅ | `_build_system_prompt` 注入车型+知识库+故障树+RAG+安全提示 |
| 维修手册 API | 二十五 | ✅ | `app/api/manual.py` 5端点：列表/按车型/搜索/详情/分块；含授权过滤+安全提示 |

### 3.2 前端任务

| 任务 | 文档章节 | 状态 | 核查结论 |
|------|----------|------|----------|
| 车型详情 Tab 完善 | 三十九 | ✅ | 4 Tab 已搭；故障 Tab 已接诊断页；参数/系统/零部件有独立端点 |
| 配件详情页完善（替代件/收藏/供应商） | 九 | ⚠️ | 底部弹窗显示 OEM/品牌/规格/价格+替代件+收藏；无供应商 |
| AI 故障诊断页 | 十二 | ✅ | 独立结构化诊断页已完成：症状输入、车型/发动机上下文、原因概率、检查顺序、安全提示与重试 |
| 维修手册浏览页 | 二十五 | ✅ | 列表+详情+分块阅读 3 页面已完成 |
| 多模态检索车型/发动机筛选 | 二十九 | ✅ | 级联筛选面板（叉车品牌→系列→车型 + 发动机品牌→型号）已接入 `embed_search_page.dart` |

### 3.3 验收（四十三章）

| 指标 | 目标 | 检验方式 | 状态 |
|------|------|----------|------|
| 铭牌识别成功率 | ≥90% | 10张铭牌 | ⏳ 验收脚本已有（`acceptance_test.py`），待执行 |
| 型号识别准确率 | ≥95% | 20个型号 | ⏳ 同上 |
| 车型匹配成功率 | ≥95% | 手动输入 | ⏳ 同上 |
| AI 引用资料 | 能引用 | 知识库问题 | ⏳ 同上 |
| AI 不编造参数 | 必须 | 不存在的问题 | ⏳ 同上 |

---

## 缺失项清单（已核查）

| # | 缺失项 | 优先级 | 影响程度 | 核查结论与解决方案 |
|---|--------|--------|----------|----------|
| 1 | **alembic 迁移文件** | P1 | 高 | ✅ 已完成，14个迁移文件，含 base_schema + reconcile_legacy + AI表 + 商业化表 + 手册元数据 |
| 2 | **knowledge 知识库管理 API** | P1 | 高 | ✅ 已完成，`app/api/knowledge.py` CRUD + 分块查询（6端点） |
| 3 | **embed 搜索过滤 UI** | P2 | 中 | ✅ 已完成：`embed_search_page.dart` 级联筛选面板（叉车品牌→系列→车型 + 发动机品牌→型号） |
| 4 | **docker-compose.yml** | P2 | 中 | ✅ 已完成，编排 PostgreSQL/Redis/Qdrant/Backend + Dockerfile |
| 5 | **AI 知识库数据填充** | P1 | 高 | ✅ 已完成，`ingest_knowledge.py` 导入5条文档及分块，向量化至 Qdrant |
| 6 | **故障树数据** | P2 | 中 | ✅ 已完成，`import_fault_trees.py` 导入6条故障树记录 |
| 7 | **验收测试数据集** | P2 | 中 | ⏳ 验收脚本已有（`acceptance_test.py`），需准备10张铭牌图片+20个型号 |
| 8 | **维修手册数据导入** | P2 | 中 | ✅ 已完成，`import_manuals.py` 可导入手册 |
| 9 | **embed 搜索过滤 UI** | P2 | 中 | ✅ 已完成：`embed_search_page.dart` 级联筛选面板（叉车品牌→系列→车型 + 发动机品牌→型号） |
| 10 | **配件供应商信息** | P3 | 低 | ⚠️ 配件详情无供应商字段 |
| 11 | **3D动画播放** | P3 | 低 | ⚠️ 框架已搭，TODO未实现 |
| 12 | **FCM/APNs 真实推送** | P2 | 中 | ⚠️ `push_service.py` 为 stub 实现，待接入真实 SDK |
| 13 | **支付平台真实对接** | P1 | 高 | ⚠️ `payment.py` 为 stub 框架，待接入微信/支付宝/Apple IAP SDK |
| 14 | **subscription_levels 四级体系** | P2 | 中 | ✅ 已对齐：account-system 为权威源（Free/Air/Pro/Ultra 四级），ForkliftCLI 本地 `subscription_levels.py` 镜像同一套常量；旧值 `enterprise`→`ultra` 自动归一化 |

---

## 四、Phase 3：后台 + 商业化 + 版权合规（100% ✅）

### 4.1 后台管理系统（二十五章）✅

| 模块 | 状态 | Vue 页面 | API 端点 |
|------|------|----------|----------|
| 用户管理 | ✅ | `Users.vue` | 5端点（列表/详情/创建/更新/删除） |
| 企业管理 | ✅ | `Enterprises.vue` | 5端点 |
| 品牌/车型管理 | ✅ | `Brands.vue` + `Models.vue` | 12端点（品牌+系列+车型 CRUD） |
| 发动机管理 | ✅ | `Engines.vue` | 8端点（品牌+型号 CRUD） |
| 配件管理 | ✅ | `Parts.vue` | 4端点 |
| 结构图/3D模型管理 | ✅ | `Diagrams.vue` | 7端点（结构图 CRUD + 3D模型 更新/删除） |
| 维修手册/AI知识库管理 | ✅ | `Documents.vue` + `Faults.vue` | 12端点（文档+故障码+故障树 CRUD） |
| 合规看板 | ✅ | 内嵌 Dashboard | 3端点（汇总/到期/导出） |
| 运营看板 | ✅ | `Dashboard.vue` | 1端点（统计） |
| 审计日志 | ✅ | `AuditLogs.vue` | 1端点 |
| **合计** | ✅ | **12 个 Vue 页面** | **58 个 API 端点** |

**技术方案：** Vue3 + Element Plus + Vite + TypeScript（部署于 `admin/` 目录）

### 4.2 商业化（四十章）✅

#### 4.2.1 版本与定价

**四级套餐体系（与 account-system 对齐，单一数据源 `subscription_levels.py` + `subscription_configs` 表）：**

| 等级 | 内部名 | 价格 | 计费周期 | 定位 |
|------|--------|------|----------|------|
| 免费版 | `free` | ¥0 | — | 基础使用，引导付费 |
| Air 轻量版 | `air` | ¥9/月 | monthly | 轻度使用者，性价比入门 |
| Pro 专业版 | `pro` | ¥39/月 | monthly | 个体技师日常使用 |
| Ultra 企业版 | `ultra` | ¥899/年 | yearly | 维修企业团队使用 |

> **向后兼容：** 旧值 `enterprise` 通过 `_LEGACY_LEVEL_MAP` 自动归一化为 `ultra`，`basic`→`free`，`premium`→`pro`。
>
> **动态配置：** account-system 的 `subscription_configs` 表支持管理后台实时修改价格/配额/折扣/注册开关，无需重启服务。`GET /public/plans` 返回四级套餐列表（含折扣后价格）。ForkliftCLI 本地 `subscription_levels.py` 镜像同一套常量，供本地限流/配额逻辑使用。

#### 4.2.2 功能权限矩阵

| 权限 | 免费版 | Air 轻量版 | Pro 专业版 | Ultra 企业版 |
|------|--------|-----------|-----------|-------------|
| 各功能每日调用次数 | 3 次/功能 | 30 次/功能 | 不限 | 不限 |
| 叉车数据库容量 | 1 台 | 3 台 | 10 台 | 不限 |
| 开屏广告 | 每次启动展示 | 无 | 无 | 无 |
| 每月体验卡（7天Pro） | — | 1 张 | 2 张 | 10 张 |
| 绑定账户上限 | — | — | — | 5 个 |

#### 4.2.3 免费版限制逻辑 ✅

```python
# 每日调用计数器（Redis）— app/core/rate_limit.py
key = f"user:{uid}:daily:{feature}:{date}"
ttl = "次日 00:00 过期"
# 超限 → HTTP 429 + "今日免费额度已用完，升级专业版解锁无限次"

# 叉车数量限制 — app/core/forklift_limit.py
count = db.query(MyForklift).filter_by(user_id=uid).count()
if level == "free" and count >= 1:
    return 403, "免费版仅支持添加1台车"
if level == "pro" and count >= 10:
    return 403, "专业版最多添加10台车，请升级 Ultra"
```

**实测验证：** ✅ 测试通过（`test_e2e_limits.py` 8个用例，含配额/日限/per-feature/付费用户跳过）

#### 4.2.4 开屏广告控制 ✅

```
App 启动 → GET /api/v1/subscription/me → level
  free        → 展示开屏广告（3s 可跳过）→ 进入首页   ✅ splash_ad_page.dart
  air         → 直接进入首页
  pro         → 直接进入首页
  ultra       → 直接进入首页
```

#### 4.2.5 体验卡机制 ✅

| 环节 | 说明 | 状态 |
|------|------|------|
| 发放 | 每月 1 日自动发放：Air 1 张、Pro 2 张、Ultra 10 张（cron job） | ✅ `subscription_tasks.py` |
| 使用条件 | 仅免费用户可领取 | ✅ 校验 `effective_level == "free"` |
| 领取方式 | 免费用户输入注册手机号 → 验证 → 激活 7 天专业版 | ✅ `trial.py` |
| 推送激活 | FCM/APNs 推送 `premium_activated` | ⚠️ stub 实现 |
| 并发限制 | 一个手机号同时只能持有 1 张活跃体验卡 | ✅ |

#### 4.2.6 Ultra 企业版账户绑定 ✅

```
Ultra 企业管理员 → POST /api/v1/enterprise/bind_account { phone_number }
  → 查找用户 → 创建绑定关系 → 目标账户升级为 Pro → 推送激活  ✅ enterprise.py

Ultra 最多绑定 5 个账户；解绑后 Pro 即时失效  ✅
```

**实测验证：** ✅ 测试通过（`test_e2e_api.py` 企业绑定上限+列表+权限校验）

#### 4.2.7 数据库设计 ✅

**users 表字段：** `subscription_level` / `subscription_expires_at` / `enterprise_id` / `device_token` / `phone` / `last_login_at`

**新增表：**

| 表名 | 用途 | ORM 模型 |
|------|------|----------|
| `enterprises` | 企业 | `Enterprise`（含 plan/plan_expire_at/status） |
| `enterprise_accounts` | 企业绑定账户 | `EnterpriseAccount`（UniqueConstraint） |
| `trial_cards` | 体验卡 | `TrialCard`（unused/used/expired） |
| `subscription_logs` | 订阅变更审计 | `SubscriptionLog` |
| `payments` | 支付订单 | `Payment`（pending/success/failed/closed） |
| `admin_audit_logs` | 管理操作审计 | `AdminAuditLogs` |

#### 4.2.8 后端 API ✅

| 模块 | 端点 | 方法 | 说明 | 状态 |
|------|------|------|------|------|
| 订阅 | `/api/v1/subscription/me` | GET | 查询当前订阅状态 | ✅ |
| 订阅 | `/api/v1/subscription/activate` | POST | 激活订阅 | ✅ |
| 订阅 | `/api/v1/subscription/cancel` | POST | 取消续订 | ✅ |
| 订阅 | `/api/v1/subscription/renew` | POST | 手动续费 | ✅ |
| 体验卡 | `/api/v1/trial/my-cards` | GET | 查看我的体验卡 | ✅ |
| 体验卡 | `/api/v1/trial/claim` | POST | 免费用户领取 | ✅ |
| 企业 | `/api/v1/enterprise/bind_account` | POST | 绑定账户 | ✅ |
| 企业 | `/api/v1/enterprise/unbind_account` | POST | 解绑账户 | ✅ |
| 企业 | `/api/v1/enterprise/accounts` | GET | 已绑定列表 | ✅ |
| 支付 | `/api/v1/payment/create` | POST | 创建订单 | ✅ stub |
| 支付 | `/api/v1/payment/notify` | POST | 支付回调 | ✅ stub |
| 支付 | `/api/v1/payment/orders` | GET | 订单历史 | ✅ |

> **架构说明：** 订阅/支付/体验卡/企业的本地实现保留为参考回退；`main.py` 通过 `proxy.py` 将同前缀请求透传到 account-service（账户权威服务），避免双库逻辑漂移。ForkliftCLI 本地仅保留用户投影表（`users`）。

#### 4.2.9 任务实施状态

| 任务 | 内容 | 状态 |
|------|------|------|
| 任务1：数据库表设计 | ORM + alembic 迁移 | ✅ |
| 任务2：权限中间件 | `rate_limit.py` + `forklift_limit.py` | ✅ 测试通过 |
| 任务3：订阅状态 API | `subscription.py` + `subscription_helper.py` | ✅ |
| 任务4：体验卡机制 | `trial.py` + `subscription_tasks.py` | ✅ |
| 任务5：企业绑定逻辑 | `enterprise.py` | ✅ 测试通过 |
| 任务6：广告 SDK 集成 | `splash_ad_page.dart` 框架完成 | ⚠️ AdMob SDK 未接入 |
| 任务7：支付对接 | `payment.py` stub 框架 | ⚠️ 真实 SDK 未接入 |
| 任务8：前端订阅页+引导升级 | 5个订阅页面 + 升级弹窗 | ✅ |

### 4.3 版权合规（四十一章）✅

**字段设计（CopyrightMixin，复用于三张内容表）：**

```sql
source            -- 资料来源（URL/书名/供应商）
copyright_owner   -- 版权所有者
license_type      -- 授权类型（白名单，默认 self_owned）
license_expire    -- 授权到期（NULL=永久授权）
commercial_use    -- 是否可商用（0/1）
```

**license_type 白名单：** `self_owned`（自研/自制）| `licensed`（商业授权）| `cc0`/`cc_by`/`cc_by_sa`（开源协议）| `public_domain`（公有领域）| `user_uploaded`（用户上传，责任归上传者）| `internal_only`（仅内部使用）

**实现清单（✅ 已实现）：**

| 模块 | 位置 | 说明 |
|------|------|------|
| 字段 Mixin | `app/models/copyright_mixin.py` | SQLAlchemy Mixin + 授权有效性过滤条件 `license_active_condition` |
| 数据迁移 | `alembic/versions/20260909_add_copyright_fields.py` | knowledge_documents / diagrams / model_3d 幂等加列（SQLite/PG 兼容） |
| 录入校验 | `app/api/admin/common.py` `validate_copyright` | 授权类型白名单；可商用必须填版权所有者；`user_uploaded`/`internal_only` 不可标可商用 |
| Admin Schema | `app/schemas/admin.py` | CopyrightFields / Update / Out，应用到 Diagram、Model3D、KnowledgeDoc 三组 Schema |
| 用户上传标记 | `app/api/model3d.py` /3d/upload | 自动标记 `license_type=user_uploaded` |
| 合规看板 | `app/api/admin/compliance.py` + `app/services/compliance_service.py` | `GET /admin/compliance/summary`、`/expiring`、`/export`（CSV） |
| 到期巡检 | `scripts/check_license.py` | 可挂 cron；发现已过期资产退出码 1 |
| C 端过滤 | `app/api/parts.py`、`app/api/model3d.py`、`app/api/manual.py` | 授权过期资产不下发；详情返回 404 |
| AI 引用控制 | `app/services/ai_service.py` | RAG 召回排除授权过期文档；引用附带「来源: …」标注 |

**验收标准：** ✅ 无版权信息的受控资产无法上传；license_expire 到期后资产在 C 端隐藏且不参与 RAG 召回；合规看板可列出/导出已过期与即将到期资产。测试通过（`test_e2e_api.py` 版权过滤用例 + `test_e2e_admin_catalog.py` 版权校验用例）。

---

## 五、技术栈

| 层 | 技术 | 状态 |
|----|------|------|
| 移动端 | Flutter + Riverpod + GoRouter | ✅ |
| 3D渲染（现役） | Web：`<model-viewer>` 3.5.0 + Three.js 0.160.0（`webview_flutter`） | ⚠️ 从 unpkg CDN 加载，**无离线**；迁移未提交 |
| 3D渲染（Unity，已弃用） | Unity 2022.3.20f1 + URP 14.x + GLTFast 5.1.0 | ⚠️ 0 场景 / 0 原生桥 / 0 素材，仅 Editor 可跑 |
| AR（现役） | lite：`<model-viewer>` AR 按钮（Scene Viewer） | ⚠️ full 渲染器的 WebXR immersive-ar 在 WebView 内不可用 |
| AR（Unity，已弃用） | ARFoundation/ARCore 5.1.0 + ARKit 5.1.0 | ⚠️ 场景未建，原生桥缺失 |
| model_viewer_plus | pubspec 声明中，lib 下 0 处引用 | ⚠️ 死依赖，可删 |
| 后端 | Python + FastAPI | ✅ |
| 数据库 | SQLite（开发）→ PostgreSQL（部署） | ✅ |
| 缓存 | Redis（限流计数器） | ✅ `rate_limit.py` |
| 对象存储 | 本地文件 → S3/MinIO（`storage.py` 统一客户端） | ✅ |
| 向量库 | Qdrant（`vector_store.py`，含内存回退） | ✅ 已集成 |
| AI | GLM-4.5-air（`ai_service.py`，OpenAI 兼容接口） | ✅ 已配置 |
| OCR | PaddleOCR（`ocr_service.py`） | ⚠️ 框架已搭，待装依赖 |
| 多模态向量化 | WeMM-Embedding-2B（`embedding_service.py`） | ✅ 已集成 |
| 后台 | Vue3 + Element Plus + Vite + TypeScript | ✅ |
| 容器化 | Docker + docker-compose | ✅ |
| 账户服务 | account-service（独立微服务，JWT 共享密钥） | ✅ 代理架构 |

---

## 六、安全机制（四十二章）✅

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

**实现位置：** `ai_service.py` 的 system_prompt 中强制注入；维修手册搜索接口也返回安全提示

**安全机制清单：**
- ✅ JWT 认证（与 account-service 共享密钥，本地验签）
- ✅ bcrypt 密码哈希（兼容保留，认证委托 account-service）
- ✅ `@safe_api` 装饰器（统一异常处理，47→129端点全覆盖）
- ✅ Prompt 安全提示（AI 回复强制包含）
- ✅ 管理员 token 与用户 token 密钥隔离（`SECRET_KEY` vs `SECRET_KEY + ":admin"`）
- ✅ 管理操作审计日志（`AdminAuditLogs` 表）
- ✅ 路径遍历防护（`storage.py` `_local_path` 校验）
- ✅ CORS 配置

---

## 七、代码质量（4.5/5）

| 维度 | 评分 | 说明 |
|------|------|------|
| 编译/运行 | ⭐⭐⭐⭐⭐ | 后端可启动，61测试通过 |
| 语法规范 | ⭐⭐⭐⭐⭐ | 无错误 |
| 类型安全 | ⭐⭐⭐⭐ | 完整（Python type hints + Pydantic） |
| 错误处理 | ⭐⭐⭐⭐⭐ | @safe_api + 全局 |
| 鉴权 | ⭐⭐⭐⭐⭐ | 全部写操作 + 管理员隔离 |
| 代码组织 | ⭐⭐⭐⭐⭐ | 分层清晰（api/core/models/schemas/services/tasks） |
| 安全性 | ⭐⭐⭐⭐ | bcrypt + JWT + admin token 隔离 |
| 测试 | ⭐⭐⭐⭐ | 64个测试用例（61 pass / 2 skip / 1 xfail），覆盖 E2E+迁移+限流+版权 |

### 7.1 数字总览（实测 2026-09-11）

```
后端:   12136 行 / 108 文件（app + alembic + scripts + tests）
        14 模型文件 / 31 表 / 92 Schema 类 / 129 端点（71 C端 + 58 管理端）
        14 个 alembic 迁移文件
        64 个测试用例（61 passed / 2 skipped / 1 xfailed）

前端:    9376 行 / 49 文件 / 32 页面
         37 个 API 方法（api_client.dart）
         其中 lib/viewer/ 1659 行 / 14 文件 + assets/*.html 654 行（Web 3D/AR 渲染器）
         其中 lib/core/unity/ 424 行（已弃用，仅回退用）
         2 个 viewer 测试（99 行，Flutter SDK 未安装，未执行验证）

后台:    2549 行 / 22 文件 / 12 个 Vue 页面

总计:   24061 行 / 179 文件
```

> 本次增量（2026-09-12）：前端 6820→9376 行，全部来自 Web 3D/AR 渲染器迁移，
> 且**尚未 git 提交**（`lib/viewer/`、`assets/`、V2 页面、`test/viewer/` 为 untracked）。

> 上版数据（4244 行 / 49 文件 / 25 表 / 42 Schema / 47 端点 / 4596 行前端 / 4个测试）
> 已按 `wc -l`、`__tablename__`、`@router.*`、`grep "class.*BaseModel"` 实测值校准。
> 统计口径：排除 `backend/venv/`、`__pycache__`、`.mimosa/`、Flutter 构建产物（android/ios）、admin/node_modules。

### 7.2 已修复问题

| 时间 | 问题 | 修复 |
|------|------|------|
| 09-08 | 33 个端点缺 `@safe_api` 装饰器 | 全部补齐，129 个端点均覆盖 |
| 09-08 | WeMM 模型加载无连接复用 | `QdrantClient` 单例 + 内存/Qdrant 双模式回退 |
| 09-08 | memory/Qdrant 向量 ID 不一致 | UUID 命名空间对齐 |
| 09-08 | 诊断结果需前端自行解析 | `_parse_diagnosis` 结构化解析 |
| 09-09 | 计划文档与代码实际状态脱节 | 全量核查修订 |
| 09-10 | account-service 集成后双库权限漂移风险 | 代理架构 + 本地投影表 + admin token 隔离 |
| 09-10 | 版权过期资产仍参与 RAG 召回 | `_retrieve_context` 增加授权过滤 |
| 09-11 | 测试覆盖不足（仅4个用例） | 新增 60 个 E2E/迁移/限流/版权用例 |

---

## 八、Unity 3D/AR 模块状态（2026-09-12 实测）

### 8.1 架构结论：Unity 已让位给 Web 渲染器

| 维度 | Unity 方案（V1） | Web 渲染器（V2，现役） |
|------|------------------|------------------------|
| Flutter 接入 | `lib/core/unity/`（424 行） | `lib/viewer/`（1659 行 / 14 文件） |
| 路由 | **未挂载**（V1 页面无路由） | `/3d`、`/ar`、`/viewer`、`/ar-web`、`/maintenance/:id` 全部挂载 |
| pubspec | `flutter_unity_widget` 已注释 | `webview_flutter: ^4.8.0` |
| 代码状态 | `@deprecated`，仅回退用 | 已写，**git untracked（未提交）** |
| 渲染器 | URP 14.x + GLTFast 5.1.0 | `<model-viewer>` 3.5.0（lite）/ Three.js 0.160.0（full），按 `requireFeatures` 自动升级 |
| 原生依赖 | 需 Android/iOS 原生桥 | 无（WebView 内置） |
| 包体增量 | ~+25 MB | ~+200 KB |

### 8.2 完成度（Web 渲染器）

| 能力 | 状态 | 证据 / 缺口 |
|------|------|-------------|
| 模型加载（GLB/GLTF） | ✅ | `GLTFLoader` + `normalizeScale` 包围盒归一 |
| 相机旋转/缩放/复位 | ✅ | `OrbitControls` + `setCamera`/`resetView` |
| 零件高亮/清除 | ✅ | emissive 材质替换 + `originalMats` 还原 |
| 爆炸图 | ✅ | `setExploded` 按方向位移 |
| 动画播放/停止 | ✅ | `AnimationMixer` |
| 测量标注 | ✅ | `measure`/`clearMeasure` + TextSprite |
| 渲染器自动升级 | ✅ | `requireFeatures` 懒销毁 lite、新建 full 并重载模型 |
| 零件点击（`onPartClicked`） | ❌ | full 渲染器 `onPointerEnd` 仍是 `/* reserved */` 占位 |
| 离线使用 | ❌ | Three.js / model-viewer 均从 `unpkg.com` CDN 加载，无本地副本 |
| 模型文件缓存 | ❌ 死代码 | `ModelAssetManager.downloadAndCache`/`getCachedFilePath` 无人调用 |
| 3D 拆解 | ✅ 代码可用 | 后端 `model_3d` 2 行但缺文件 |

### 8.3 接入度（后端 → App 链路）

| 环节 | 状态 | 实测 |
|------|------|------|
| 后端端点 | ✅ | `GET /api/v1/3d/forklift/{id}` 返回 `{model, parts, animations}`，`model3d.py:87` |
| 契约对齐 | ✅ | `ModelAssetManager._fetchFromApi` 读取字段与 `Model3DOut`/`Model3DPartOut` 一致 |
| AR 配置端点 | ✅ 存在，无数据 | `GET /api/v1/ar/config/{id}` 已实现；`ar_model_config` 表 **0 行** |
| 3D 模型元数据 | ⚠️ 2 条 | `model_3d`：`forklift_model_id=1`，v1/v2，`status=ready` |
| 模型二进制 | ❌ 缺失 | `backend/uploads/` **完全为空**，两条 `file_url` 全部 404 |
| 零件数据 | ❌ 空 | `model_3d_parts` = 0 行（前端零件列表必然空） |
| 动画数据 | ❌ 空 | `model_3d_animations` = 0 行 |
| 真实模型资产 | ⚠️ 有但未接入 | `Glb/001.glb`、`Glb/002.glb`（各 42MB）在仓库根，既未进 Unity `StreamingAssets` 也未上传后端 |
| 授权过滤 | ✅ | 端点带 `license_active_condition`，过期模型不下发 |

**端到端结论：链路代码全通，但当前一次真实加载都会失败** ——
元数据返回成功，随即 `GLTFLoader` 请求的 `file_url` 404。

### 8.4 Unity 工程完成度（供回退评估）

| 项 | 状态 |
|----|------|
| C# 代码量 | 1742 行 / 17 文件，`Assets/Scripts/` |
| 消息桥 | ✅ 完整：JSON 解析/分发/错误回传，**22 个已注册方法** |
| 注册方法超文档 | 9 个未写入 `unity/README.md` 与 `UNITY_INTEGRATION_PLAN.md`：`clearModel`、`setSteerAngle`、`resetView`、`setView`、`confirmARPlacement`、`repositionAR`、`hideARDimensions`、`beginARGuide`、`endARGuide` |
| GLTFast 降级 | ✅ 诚实降级：写本地缓存后回 `onError`，不假装成功 |
| 场景 | ❌ 0 个 `.unity`；`Editor/CreateScenes.cs` 需人工点菜单，且生成的场景**缺 `ModelLoader`/`CameraController`**，AR 场景缺 `ARSession`/`ARCamera`/`ARRaycastManager`/`ARPlaneManager` |
| 原生桥 | ❌ 全仓库 0 个 `.kt` / `.mm`；`DllImport("__Internal") _forkliftBao_sendToFlutter` 无实现 |
| 素材 | ❌ `Scenes/` `Materials/` `Prefabs/` `Shaders/` 全空；无 URP `UniversalRenderPipelineAsset` |
| 点击拾取 | ❌ GLTFast 不输出 Collider，`CameraController.onPartClicked` 永不触发 |
| 零件映射 | ⚠️ `PartMapping.cs` 硬编码 8 个叉车部件名，按精确节点名匹配，通用 GLB 不匹配 |
| 潜在缺陷 | `UnityMessageManager.Awake()` 调 `s_handlers.Clear()`，Awake 顺序反转会清空所有注册 |

**Unity 侧结论：** 通信层扎实，设备 I/O 与场景脚手架全部未交付。复活需 4 项前置工作
（原生桥 / 场景组件补挂 / URP 与材质 / GLB 与元数据导入）外加把 Flutter 路由切回 V1，
**建议不复活**，以 Web 渲染器为主线。

### 8.5 建议动作执行记录（2026-09-12 当日完成）

> 上表 8.1–8.4 的问题于同日修复，逐项结果如下。修完后再测出的新问题也一并列出。

| # | 优先级 | 动作 | 结果 |
|---|--------|------|------|
| 1 | P0 | 修复数据断点 | ✅ **根因不是 DB 错，是 `uploads/` 被清空**：`Glb/001.glb` 的 SHA256 前缀 `623408c9631c90ba` 正好等于 `model_3d` v1 的 `storage_key`，`002.glb` 同理匹配 v2。因此按哈希找回**恢复原文件**而非新建 v3，避免出现两条内容重复的模型记录。`backend/scripts/fix_3d_assets.py`（幂等，已验证复跑不产生重复数据） |
| 2 | P0 | 填 `ar_model_config` | ✅ 1 行，尺寸取自 `forklift_models` 已录入的 8FG30 实测参数（3850×1240×2150 mm，门架 3000 mm，scale_factor=1.0）。**轴距/转弯半径未编造**：车型表里就是 NULL，展示层显示 "—" |
| 3 | P1 | 提交 Web 渲染器迁移 | ✅ 已提交（见 9.0 记录） |
| 4 | P1 | Three.js 本地化 | ✅ three@0.160.0 + model-viewer@3.5.0 打进 `assets/vendor/`（2.3 MB，含 SHA256 与升级步骤，见 `assets/vendor/README.md`）。**代价修正：原「+200 KB」是把依赖放 CDN 的算法，离线化的真实增量是 ~2.3 MB**。加载方式从 `loadHtmlString(baseUrl: 'file:///')` 改为 `loadFileUrl(asset:///...)`，否则 `file:///` 基址下 ES module 被 CORS 拦死 |
| 5 | P2 | 补 `model_3d_parts` | ⚠️ **不能按原方案跑**：`tools/generate_model_metadata.py` 原先只吐硬编码模板（8 个叉车部件），从不读模型；实测两份 GLB 均为 tripo3d.ai 生成的**单网格**资产，1 节点 0 动画，与那 8 个部件名完全对不上。已重写该工具改为真实解析 GLB（含能力校验与告警），据此写入 2 条**真实节点名**的零件记录 |
| 6 | P2 | 清理死代码 | ✅ 删 `model_viewer_plus`（lib 下 0 引用）；`_autoRotate` 接线到 `setAutoRotate`（两渲染器均支持，切渲染器后状态自动重下发，拖拽自动停）；full 渲染器补上真实点击判定（位移<12px 且 <600ms），`onPointerEnd` 空实现移除 |
| 7 | P3 | AR 技术路线 | ✅ 已决策并写入 `mobile/lib/viewer/README.md`：AR 走 lite（`<model-viewer>` 的 Scene Viewer / Quick Look），full 的 WebXR `immersive-ar` 在 WebView 内不可用、视为不可交付；原生 ARKit/ARCore 留到 V3.0。full 的 `enterAR` 保留但预期真机报"浏览器不支持 WebXR" |

**修完数据断点后又发现并修掉的两个隐藏断点：**

| 问题 | 影响 | 修复 |
|------|------|------|
| 后端 `file_url` 是**相对路径**（`/uploads/...`），而 WebView 基址是 `asset:///` | GLTFLoader 会请求 `asset:///uploads/...` 直接 404 —— 即使模型文件已恢复，3D 仍然打不开 | `ApiClient` 暴露 `baseUrl`，`ModelAssetManager.resolveUrl` 统一补全（含读缓存后补全，防旧缓存残留），并新增 9 个测试用例 |
| full 渲染器 `buildPartMap` 只按 `userData.partId`/自身名建索引，而 GLTFLoader 给 mesh 的名字是 `tripo_mesh_...`、后端存的是节点名 `tripo_node_...` | 零件列表点谁都报"未找到零件" | 索引改为 `partId → partName → 自身名 → 最近具名父节点` 多键命中；`highlightPart` 的模糊匹配分支原会在 `meshes` 为 undefined 时 `push` 抛 TypeError，一并修掉；高亮材质用完即 dispose（原先每次点击泄漏一份 GPU 资源） |

**遗留未决：**

- `model_3d` 现存 2 条记录的 `license_type` 均为 `self_owned`（自研/自制），
  但资产明确来自 tripo3d.ai 生成。这是**存疑的权利声明**：若没有 tripo3d 的
  商用授权，按 `self_owned` 随付费套餐下发存在合规风险。新上传走
  `internal_only`；存量两条是否改，需要确认授权情况后人工定，脚本未擅自改动。
- Web 渲染器迁移的**真机行为未验证**：本机无 Flutter SDK，改动的 Dart 未编译、
  `test/viewer/` 3 个用例未执行；`asset://` 协议加载 ES module 在
  Android WebView / iOS WKWebView 的实际表现需上真机确认（含 iOS 可能需要的
  `WKWebViewCustomProtocolAllowedSchemes` 配置）。

---

## 九、修订记录

### 9.0 2026-09-12 Unity 3D/AR 模块完成度与接入度实测（本次）

**核查范围：** `unity/` 全部 17 个 C# 文件 + `mobile/lib/viewer/` 14 文件 +
`mobile/assets/*.html` + V1/V2 页面 + `backend/app/api/model3d.py` +
SQLite 数据库实测 + `git status`

**关键发现：**

| 发现 | 详情 |
|------|------|
| 架构已变 | 3D/AR 渲染从 Unity 迁移到 Web 渲染器；`/3d`、`/ar` 路由指向 V2 页面，Unity 不在运行时路径 |
| Unity 文档失效 | `unity/README.md` 声称「pubspec 已添加 `flutter_unity_widget: ^2.3.0`」——实测已注释掉 |
| Unity 无法上真机 | 0 场景 / 0 `.kt`/`.mm` 原生桥 / 0 素材；`CreateScenes` 生成的场景还缺 `ModelLoader` 与 `CameraController` |
| **模型二进制缺失（P0）** | `backend/uploads/` 完全为空，`model_3d` 2 条 `file_url` 全 404 |
| **AR 无数据（P0）** | `ar_model_config` 0 行；`model_3d_parts` 0 行；`model_3d_animations` 0 行 |
| 真实模型未接入 | `Glb/001.glb`、`Glb/002.glb`（各 42MB）在仓库根，两边都没进 |
| Web 侧真缺口 | full 渲染器 `onPointerEnd` 占位 → 零件点击失效；Three.js 走 CDN → 无离线 |
| 迁移未提交 | `lib/viewer/`、`assets/`、V2 页面、`test/viewer/` 全部 git untracked |

**数字校准：** 前端 6820 行 / 33 文件 → **9376 行 / 49 文件**；
总计 21505 行 / 163 文件 → **24061 行 / 179 文件**；
48 章统计 40 ✅ / 2 ⚠️ / 2 ⏳ → **37 ✅ / 8 ⚠️ / 1 ❌ / 2 ⏳**。

**后续修复（同日，逐项结果见 8.5）：** 上表 P0/P1/P2 项均已处置 ——
模型文件按哈希找回（根因是 `uploads/` 被清空，DB 记录本身是对的）、
`ar_model_config` 与 `model_3d_parts` 已按真实数据写入、Three.js/model-viewer
本地化到 `assets/vendor/`（2.3 MB）、`model_viewer_plus` 死依赖删除、
full 渲染器补上真实点击判定、AR 路线已决策走 lite。
十三、十七回升为 ⚠️，统计变为 **37 ✅ / 9 ⚠️ / 0 ❌ / 2 ⏳**。
**剩余卡点：本机无 Flutter SDK，改动未编译、真机行为未验证。**

**文档修订：** 新增「八、Unity 3D/AR 模块状态」；第三章十三~十九、二十一状态下调；
技术栈 3D/AR 行按现役 Unity 双轨重写；`unity/README.md` 加状态表并修正失效表述。
修订记录原 8.x 顺延为 9.x。

### 9.1 2026-09-11 全量审校

**审校范围：** 后端全部 108 文件 + 前端全部 33 文件 + 后台全部 22 文件 + 14 迁移文件 + 7 测试文件 + 配置文件

**数字校准：**

| 项 | 原文档 | 实测值 |
|----|--------|--------|
| 表数量 | 25 张 | **31 张**（新增 enterprises / enterprise_accounts / trial_cards / subscription_logs / payments / admin_audit_logs） |
| 后端行数/文件 | 4244 / 49 | **12136 / 108**（含 tests/7 + scripts/9 + 新增 API/core 模块） |
| Schema 类数 | 42 | **92**（新增 subscription/manual/admin 扩展） |
| C端端点数 | 47 | **71**（59注册 + 12本地回退，新增 knowledge/manual/subscription/trial/enterprise/payment） |
| 管理端点数 | 53 | **58**（新增合规3端点） |
| 前端行数/文件/页面 | 4596 / 23 / 16 | **6820 / 33 / 26**（新增 manual 3页 + subscription 5页 + diagnosis + splash_ad + upgrade_dialog） |
| 后台行数/文件/页面 | Phase 3 待开发 | **2549 / 22 / 12**（已全部实现） |
| 测试用例 | 4 | **64**（61 pass / 2 skip / 1 xfail） |
| 迁移文件 | 未统计 | **14 个** |
| 总行数 | 8840 | **21505** |

### 9.2 新增核查项

- **维修手册 API**（`app/api/manual.py`）：5端点，含授权过滤+向量搜索+安全提示，此前标记为「未实现」，现已完成
- **维修手册前端**（3页面）：列表+详情+分块阅读，已完成
- **AI故障诊断页**（`ai_diagnosis_page.dart`）：独立结构化诊断页，已完成
- **订阅/商业化前端**（5页面）：订阅中心+套餐+体验卡+企业管理+升级弹窗，已完成
- **开屏广告**（`splash_ad_page.dart`）：框架完成，AdMob SDK 未接入
- **account-service 代理架构**：`proxy.py` 透传5个前缀，本地保留回退实现，避免双库权限漂移
- **subscription_levels 四级方案**：`subscription_levels.py` 定义了 Free/Air/Pro/Ultra 四级，与 account-system 权威源完全对齐；旧值 `enterprise`→`ultra` 自动归一化
- **Docker**：`Dockerfile` + `docker-compose.yml` 已完成（PostgreSQL/Redis/Qdrant/Backend）
- **版权合规服务**：`compliance_service.py` 资产枚举+到期巡检汇总
- **测试套件**：从4个扩展到64个，覆盖 E2E API / 管理后台 CRUD / 限流配额 / 3D资产 / 迁移完整性 / 版权过滤

### 9.3 状态修正（文档声称 → 实际）

| 项 | 原文档 | 实际核查 |
|----|--------|----------|
| Phase 3 | ⏳ 待开发 | **✅ 已完成**（后台12页面+58端点+商业化+版权合规） |
| 维修手册 API | ⏳ 未实现 | **✅ 已完成**（5端点） |
| 维修手册浏览页 | ⏳ 未实现 | **✅ 已完成**（3页面） |
| AI故障诊断页 | ✅ | **✅ 确认完成** |
| docker-compose | ✅ | **✅ 确认完成** |
| 知识库管理API | ✅ | **✅ 确认完成**（6端点） |
| 安全机制 | ✅ 完成 | **✅ 四重→五重**（新增 admin token 隔离 + 审计日志） |
| 后台管理 | ⏳ Phase 3 | **✅ 完成**（Vue3 + 12页面 + 58端点） |
| 商业化 | ⏳ Phase 3 | **✅ 完成**（订阅+支付+体验卡+企业绑定，支付SDK为stub） |
| 版权合规 | ⏳ Phase 3 | **✅ 完成**（Mixin+迁移+校验+看板+巡检+过滤） |

### 9.4 待完成项汇总

| # | 待完成项 | 优先级 | 说明 |
|---|----------|--------|------|
| 1 | ~~3D 模型二进制缺失~~ | ~~P0~~ | ✅ 已修复（根因是 `uploads/` 被清空，按哈希找回原文件，见 8.5） |
| 2 | ~~AR 真实尺寸无数据~~ | ~~P0~~ | ✅ 已填 8FG30 实测参数（十七章可从 ❌ 回升为 ⚠️，见下） |
| 3 | ~~Web 渲染器迁移未提交~~ | ~~P1~~ | ✅ 已提交 |
| 4 | ~~Three.js 本地化~~ | ~~P1~~ | ✅ 已打进 `assets/vendor/`（2.3 MB） |
| 5 | **真机验证（含 Flutter 测试执行）** | **P1** | 本机无 Flutter SDK：改动未编译、`test/viewer/` 3 用例未跑、`asset://` 加载 ES module 的真机行为未确认 —— **这是当前最高优先级** |
| 6 | `model_3d` 存量记录 license 复核 | P1 | 两条 `self_owned` 但资产来自 tripo3d.ai，权利存疑；脚本未擅改，需人工确认授权 |
| 7 | 支付平台真实对接 | P1 | `payment.py` 为 stub，需接入微信/支付宝/IAP |
| 8 | 有零件层级的模型资产 | P2 | 现有两份 GLB 均为 tripo3d 单网格，无零件/动画；需按 `docs/SOLIDWORKS_EXPORT_GUIDE.md` 从 STEP 重新导出（八部件 + 三动画） |
| 9 | 3D 拆解模式 | P2 | Web `setExploded` 已实现，但需第 8 项的多部件模型才真正可用 |
| 10 | 验收测试数据集执行 | P2 | 需准备10张铭牌+20个型号 |
| 11 | FCM/APNs 真实推送 | P2 | `push_service.py` 为 stub |
| 12 | AdMob SDK 集成 | P2 | `splash_ad_page.dart` 框架完成，SDK未接入 |
| 13 | 配件供应商信息 | P3 | 配件详情无供应商字段 |
| 14 | V3.0 原生 AR（ARKit/ARCore） | P3 | WebXR 在 WebView 内不可用已定论；若 AR 为主卖点需回到原生路线 |
| 15 | ~~3D动画播放~~ | — | ✅ Web full 渲染器 `AnimationMixer` 已实现（此前标 P3 TODO 不准确） |
| ~~—~~ | ~~embed 搜索筛选 UI~~ / ~~subscription_levels 四级统一~~ / ~~清理死代码~~ / ~~AR 技术路线决策~~ | — | ✅ 均已完成 |
