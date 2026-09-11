# ForkliftCLI 调试前台

这是一个用于调试 ForkliftCLI 项目后端 API 的纯前端 HTML 页面。

## 使用方法

### 1. 启动后端服务

后端服务默认运行在 `http://localhost:8000`。启动命令：

```bash
cd backend
uvicorn app.main:app --reload
```

### 2. 启动调试前端

```bash
cd debug-frontend
python3 -m http.server 8080
```

然后访问 `http://localhost:8080`

### 3. 配置调试前台

- 在首页顶部输入框中输入后端 API 地址 (默认: `http://localhost:8000`)
- 点击"健康检查"按钮验证后端连接状态
- 如果需要认证，请先点击"🔐 认证"模块登录获取 Token

## 功能模块

### 🔐 认证
- **手机号**: 使用格式 `13800138000`（示例）  
- **密码**: 初始密码 `123456`
- 登录后会自动保存 JWT Token 到输入框

### 📋 车型库
- **搜索**: 输入车型名称、系列或品牌进行搜索
- **加载品牌**: 查看所有叉车品牌

### 🔧 配件
- **搜索**: 输入配件名称或 OEM 编号
- **车型ID**: 可选，筛选特定车型的配件

### 🤖 AI维修助手
- **AI问答**: 输入故障描述，获取 AI 助手的建议
- **故障诊断**: 基于症状进行故障诊断

### 🧩 3D模型
- **获取3D模型**: 输入车型ID获取对应的3D模型信息

### 📦 我的叉车
- **列出我的叉车**: 查看用户添加的叉车档案

## API 端点概览

| 模块 | 路径 | 方法 | 是否需认证 |
|------|------|------|----------|
| 认证 | `/api/v1/auth/login` | POST | 否 |
| 健康检查 | `/health` | GET | 否 |
| 车型搜索 | `/api/v1/forklifts/search` | GET | 否 |
| 品牌列表 | `/api/v1/forklifts/brands` | GET | 否 |
| 配件搜索 | `/api/v1/parts/search` | GET | 否 |
| AI对话 | `/api/v1/ai/chat` | POST | 是 |
| AI诊断 | `/api/v1/ai/diagnose` | POST | 是 |
| 3D模型 | `/api/v1/3d/forklift/{id}` | GET | 是 |
| 我的叉车 | `/api/v1/my-forklifts` | GET | 是 |

## 常见问题

**Q: 提示"无法连接到后端"?**
A: 检查后端服务是否已在 `http://localhost:8000` 运行，或在输入框中输入正确的 API 地址

**Q: 登录失败?**
A: 确保 account-service 在 `http://127.0.0.1:8001` 运行，或检查手机号/密码格式

**Q: AI功能无法使用?**
A: 需要配置 AI_API_KEY 和 AI_BASE_URL 到 `.env` 文件中
