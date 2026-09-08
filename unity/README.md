# ForkliftCLI Unity 3D/AR 模块

**版本：** 0.2.0（通信桥可用，场景待建）
**Unity 版本：** 2022.3.20f1 LTS
**渲染管线：** URP 14.x

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
编辑器里只会打印到 Console。这是当前最大的未决项。

## Flutter 侧

`mobile/pubspec.yaml` 已添加 `flutter_unity_widget: ^2.3.0`，`flutter pub get` 后生效。
桥接代码在 `mobile/lib/core/unity/`。

## 完整方案

见仓库根目录 `UNITY_INTEGRATION_PLAN.md`。
