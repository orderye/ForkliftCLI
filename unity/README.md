# ForkliftCLI Unity 3D/AR 模块

**版本：** 0.2.0
**Unity 版本：** 2022.3.20f1 LTS
**渲染管线：** URP 14.x

## ⚠️ 当前状态（2026-09-12 实测）：已弃用，不在运行时路径上

3D/AR 渲染已从 Unity 迁移到 **Web 渲染器**（`<model-viewer>` + Three.js，跑在
`webview_flutter` 里）。当前 App 的 `/3d`、`/ar` 路由指向 V2 页面，**完全不加载本 Unity 工程**。

| 事实 | 实测结论 |
|---|---|
| 运行路径 | `/3d` → `ThreeDViewerPageV2`，`/ar` → `ArViewPageV2`（`mobile/lib/app/router.dart`） |
| `flutter_unity_widget` | 已在 `mobile/pubspec.yaml` 中**注释掉** |
| `lib/core/unity/` | `UnityBridge` / `UnityViewWrapper` 已标 `@deprecated`，仅留作回退 |
| 替代实现 | `mobile/lib/viewer/`（14 文件 / 1659 行）+ `assets/viewer_{lite,full}.html`（654 行） |
| 迁移状态 | **未提交**：`lib/viewer/`、`assets/`、V2 页面、`test/viewer/` 均为 git untracked |
| 包体 | Unity ~+25MB → Web ~+200KB（见 `lib/viewer/MIGRATION.md`） |

### 本模块的真实完成度（代码已写，但无法上真机）

- ✅ **通信桥是完整的**：`UnityMessageManager` JSON 解析/分发/错误回传，22 个已注册方法
  （文档写的 12 个 + 额外 9 个：clearModel/setSteerAngle/resetView/setView/confirmARPlacement/
  repositionAR/hideARDimensions/beginARGuide/endARGuide）
- ✅ **模型加载是真实现**：GLTFast 异步导入 + 按包围盒归一 + 内容 hash 缓存；
  `FORKLIFT_GLTFAST` 降级分支会诚实报错，不假装成功
- ❌ **场景 0 个**：`Assets/Scenes/` 为空。`Editor/CreateScenes.cs` 只能靠人手点菜单生成，
  且生成的场景**缺 `ModelLoader` 和 `CameraController`** → 即使跑了菜单，
  `loadModel`/`resetView` 仍会回 `"未注册方法"`
- ❌ **原生桥 0 个文件**：全仓库无 `.kt` / `.mm`（`NativeBridge_iOS.cs` 的
  `DllImport("__Internal")` 没有对应实现）。Android 调 `UnityPlayer.sendMessageToFlutter`
  会 NoSuchMethodError，iOS 链接期就失败
- ❌ **素材 0 个**：`Materials/` `Prefabs/` `Shaders/` `Scenes/` 全空，无 URP
  `UniversalRenderPipelineAsset`；`StreamingAssets/models/` 只有一个
  `animation_config_template.json`
- ❌ **GLTFast 不输出 Collider** → `CameraController.onPartClicked` 永不触发

### 资产断点（2026-09-12 已修复 Web 侧，Unity 侧仍未接入）

- ✅ `backend/uploads/` 此前被清空导致两条 `file_url` 404，已按 SHA256
  从仓库根 `Glb/` 找回并放回原位（`backend/scripts/fix_3d_assets.py`，幂等）
- ✅ `ar_model_config` 已录入 1 条（8FG30：3850×1240×2150 mm）
- ✅ `model_3d_parts` 已按**真实节点名**写入 2 条
- ❌ `model_3d_animations` 仍为 0 行 —— 两份 GLB 都是 tripo3d.ai 生成的
  **单网格**资产（1 节点 / 0 动画 / 无部件层级），根本不存在可标注的动画
- ❌ Unity `Assets/StreamingAssets/models/` 仍只有模板 JSON，
  真实 GLB 未放入；`PartMapping.cs` 那 8 个部件名在这些资产里一个都对不上

**结论：** 本目录是滞留的基础设施。要复活它，最少需要：写原生桥（Android/iOS）、
补齐 `CreateScenes` 缺失的组件挂载、建 URP 资产与材质、导入 GLB 与元数据；
然后还得把 Flutter 路由切回 V1。更现实的路径是走 Web 渲染器（见下）。

## Web 渲染器（现役，替代本模块）

见 `mobile/lib/viewer/README.md`（架构）与 `mobile/lib/viewer/MIGRATION.md`（迁移指南）。

- 双渲染器插件化：`assets/viewer_lite.html`（model-viewer 3.5.0）/
  `assets/viewer_full.html`（Three.js 0.160.0），按 `requireFeatures` 自动升级
- 后端契约已对齐：`ModelAssetManager` → `GET /api/v1/3d/forklift/{id}`，
  返回 `{model, parts, animations}` 与后端 `model3d.py` 完全一致
- 已知缺口：Three.js 从 unpkg CDN 加载（**无离线**）；full 渲染器
  `onPointerEnd` 仍是占位 → **零件点击不工作**；`navigator.xr` 的
  immersive-ar 在 WebView 内基本不可用 → full 的 AR 是死路，只有 lite 的
  `<model-viewer>` AR 按钮（Scene Viewer）有戏；Web 侧无透明模式、
  无 AR 尺寸标注、无 AR 维修指导（这三项只有 Unity 侧写了实现）

---

# 以下为 Unity 模块原始文档（保留供回退参考）

## 目录结构

```
unity/
├── Assets/
│   ├── Scenes/              # ThreeDViewer.unity + ARView.unity（待创建）
│   ├── Scripts/
│   │   ├── Core/            # 通信桥 + 全局管理
│   │   │   ├── AppManager.cs
│   │   │   ├── UnityMessageManager.cs
│   │   │   ├── FlutterApi.cs
│   │   │   └── NativeBridge_iOS.cs
│   │   ├── Viewer/          # 3D 查看器
│   │   │   ├── ModelLoader.cs
│   │   │   ├── CameraController.cs
│   │   │   ├── AnimationController.cs
│   │   │   ├── PartHighlighter.cs
│   │   │   └── ExplodedView.cs
│   │   └── AR/              # AR 实景
│   │       ├── ARPlacementController.cs
│   │       ├── ARDimensionOverlay.cs
│   │       └── ARRepairGuide.cs
│   ├── Shaders/             # 高亮/透明 Shader（待创建）
│   ├── Materials/
│   ├── Prefabs/
│   └── StreamingAssets/models/   # .glb 模型文件（待放置）
├── Packages/
│   └── manifest.json
└── ProjectSettings/
    └── ProjectVersion.txt
```

## 如何打开

1. 安装 **Unity Hub** + **Unity 2022.3.20f1**（含 Android Build Support + iOS Build Support + ARCore/ARKit 扩展）
2. Unity Hub → Add → 选择本目录 `unity/`
3. 首次打开 Unity 会解析 `Packages/manifest.json` 并自动下载所有依赖
4. 打开 `Project Settings → XR Plug-in Management`，勾选 Android (ARCore) 和 iOS (ARKit)
5. **Player Settings → Other Settings → Scripting Define Symbols**，三个平台都要加 `FORKLIFT_GLTFAST`。
   不加的话 `ModelLoader` 走降级分支：只把 .glb 下载到本地缓存，不解析显示。

## 依赖 Package

| Package | 版本 | 用途 |
|---------|------|------|
| com.unity.render-pipelines.universal | 14.0.0 | URP 渲染 |
| com.unity.inputsystem | 1.5.3 | 新输入系统 |
| com.unity.textmeshpro | 3.0.6 | UI 文字 |
| com.unity.cloud.gltfast | 5.1.0 | **glTF/GLB 加载，ModelLoader 的核心依赖** |
| com.unity.xr.arfoundation | 5.1.0 | AR 跨平台接口 |
| com.unity.xr.arcore | 5.1.0 | Android AR |
| com.unity.xr.arkit | 5.1.0 | iOS AR |
| com.unity.xr.management | 4.4.0 | XR 插件管理 |
| com.unity.xr.core | 10.0.1 | XR 核心 |

> 如 Unity 版本与 manifest 中 AR 包版本不兼容，Package Manager 会自动调整或提示错误，按提示更新版本即可。

## 场景怎么配（必须在编辑器里做）

### ThreeDViewer.unity

| GameObject | 组件 | 关键连线 |
|---|---|---|
| `UnityMessageManager` | `UnityMessageManager` | 无，单例且 DontDestroyOnLoad |
| `CameraRig` | `CameraController` | `pivot` → ModelContainer |
| `AnimationRig` | `AnimationController` | `mastInner` / `mastOuter` / `fork` / `mastAssembly` / `rearWheel` |
| `ModelRoot` | `ModelLoader` | `modelContainer` → ModelContainer |
| `Highlighter` | `PartHighlighter` | `highlightMaterial` / `transparentMaterial` |
| `Exploded` | `ExplodedView` | 挂到 ModelContainer 下 |

### ARView.unity

AR Foundation 三件套：`ARSession`、`ARCameraManager`、`ARRaycastManager`、`ARPlaneManager`，
后两者的引用要拖进 `ARPlacementController` 的 `raycastManager` / `planeManager`。

`ARDimensionOverlay` 需要：5 个 TextMeshProUGUI（长/宽/高/轴距/面积）+ 3 个 LineRenderer
（长边/宽边/转弯圆），线宽默认 0.02m、离地 0.005m，AR 里肉眼可辨。

## 消息注册模型

每个功能脚本在自己的 `Awake()` 里调
`Core.UnityMessageManager.Register("方法名", 方法引用)`，**不再需要集中写注册表**。
好处：脚本不在场景中时不会 NPE 打断整个桥；Flutter 调到未注册方法会收到
`onError`（`"未注册方法"`）而不是静默失败。

当前已注册：

| 方法 | 处理方 | 参数 |
|---|---|---|
| `loadModel` / `clearModel` | `ModelLoader` | `{url, modelId}` |
| `playAnimation` / `stopAnimation` | `AnimationController` | `{name, speed}` |
| `setMastHeight` / `setTiltAngle` / `setSteerAngle` | `AnimationController` | `{heightMm}` / `{angle}` |
| `highlightPart` / `clearHighlight` / `setTransparent` | `PartHighlighter` | `{partId, color}` / `{enabled, group}` |
| `setExploded` | `ExplodedView` | `{progress}` |
| `resetView` / `setView` | `CameraController` | `{}` / `{yaw, pitch, distance}` |
| `enterAR` / `confirmARPlacement` / `setARScale` / `repositionAR` | `ARPlacementController` | `{modelId, arConfig}` 等 |
| `showARDimensions` / `hideARDimensions` | `ARDimensionOverlay` | `{show}` |
| `beginARGuide` / `endARGuide` | `ARRepairGuide` | `{step, anchor}` |

`highlightPart` 依赖 `PartHighlighter.RegisterPart(partId, GameObject)` 先把零件注册进来；
模型导入后需要把 partId 映射到子物体。

## 模型加载

- 后端 `file_url` 必须是 `.glb`（GLTFast 也支持 `.gltf` + 外部 `.bin`，但那样后端要能提供多个资源）。
- `ModelLoader` 用 `UnityWebRequest` 下载（60s 超时），`GltfImport` 解析，然后按包围盒最长边
  归一到 1m 左右。AR 模式再由 `ARPlacementController` 按后端 `scale_factor` 乘成真实尺寸。
- 失败路径都会回传 `onError`（HTTP 状态码 / 解析失败 / 缺包），不再假装成功。

## 通信约定

- Flutter → Unity：`controller.postMessage('UnityMessageManager', 'OnMessageFromFlutter',
  '{"method":"loadModel","data":{...}}')`
- Unity → Flutter：`SendToFlutter(eventName, json)`，打包成 `{"eventName":"...","data":{...}}`。
- 事件名清单见 `mobile/lib/core/unity/unity_bridge.dart`。

## 原生侧（尚未完成，真机上事件回传断掉）

`SendToFlutter` 在非编辑器平台依赖原生插件：

- Android：需要 `FlutterUnityPlugin.kt` + `UnityPlayerFragment.kt`，
  Activity 要实现 `sendMessageToFlutter(String, String)`。
- iOS：需要 `NativeBridge_iOS.mm`（ObjC++），实现 `_forkliftBao_sendToFlutter`，
  并调用 `NativeBridge_iOS.SendMessageFromFlutter` 接住 Flutter → Unity 方向。

这两个原生文件还没写，所以**真机上 Unity → Flutter 的事件回传是断的**，
编辑器里只会打印到 Console。

> **2026-09-12 更新：** 这不再是"当前最大的未决项" —— 因为整个 Unity 模块已不在
> 运行时路径上（见文首状态表）。实测：全仓库无 `.kt` / `.mm` 文件
> （唯一原生文件是 `mobile/ios/Runner/GeneratedPluginRegistrant.m`），
> Android 分支调用的 `UnityPlayer.sendMessageToFlutter` 并不存在。
> 本段仅作为将来回退 Unity 时的任务清单保留。

## Flutter 侧

> **2026-09-12 修正：** 本文档原先写"已添加 `flutter_unity_widget: ^2.3.0`"，**已失效**。
> 该依赖现已在 `mobile/pubspec.yaml` 中注释掉（迁移到 Web 渲染器），
> `lib/core/unity/` 两个类也已标记 `@deprecated`。现役代码见 `mobile/lib/viewer/`。
> 若取消注释回退，`flutter pub get` 后才生效。

## 完整方案

见仓库根目录 `UNITY_INTEGRATION_PLAN.md`。
