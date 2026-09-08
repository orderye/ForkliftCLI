# ForkliftCLI Unity 3D/AR 模块

**版本：** 0.1.0 骨架  
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
4. 等待 Package Manager 安装完成，打开 `Project Settings → XR Plug-in Management`，勾选 Android (ARCore) 和 iOS (ARKit)

## 依赖 Package

| Package | 版本 | 用途 |
|---------|------|------|
| com.unity.render-pipelines.universal | 14.0.0 | URP 渲染 |
| com.unity.inputsystem | 1.5.3 | 新输入系统 |
| com.unity.textmeshpro | 3.0.6 | UI 文字 |
| com.unity.xr.arfoundation | 5.1.0 | AR 跨平台接口 |
| com.unity.xr.arcore | 5.1.0 | Android AR |
| com.unity.xr.arkit | 5.1.0 | iOS AR |
| com.unity.xr.management | 4.4.0 | XR 插件管理 |

> **注意：** 如 Unity 版本与 manifest 中 AR 包版本不兼容，Package Manager 会自动调整或提示错误，按提示更新版本即可。

## 首次打开后待办（在 Unity 编辑器内）

1. `Assets/Scenes/` 下新建 `ThreeDViewer.unity` 与 `ARView.unity`
2. ThreeDViewer 场景：Camera + Directional Light + 空物体挂 `AppManager`
3. ARView 场景：AR Session + AR Session Origin + AR Camera（需先勾选 XR Plug-in）
4. 在 `Project Settings → Player` 设置包名（与 Flutter Android 包一致）
5. 导出一个 "export" Unity 工程用于 flutter_unity_widget 集成

## 模型加载说明

`ModelLoader.cs` 中模型加载需要 **GLTFast** 包（`com.unity.cloud.gltfast`）。
未安装时 Unity 会编译失败（提示 GltfImport 未找到），两种处理：
- 安装 GLTFast 包（推荐，动态加载远程 .glb）
- 或改为预置模型：把 .glb 导入 Unity 转 Prefab，用 Resources.Load 加载

## Flutter 侧

`mobile/pubspec.yaml` 已添加 `flutter_unity_widget: ^2.3.0`，`flutter pub get` 后生效。

## 通信协议

见 `UNITY_INTEGRATION_PLAN.md` Step 2（12 个 Flutter→Unity 指令 + 6 个 Unity→Flutter 事件）。