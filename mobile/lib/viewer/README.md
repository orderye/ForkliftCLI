# ForkliftCLI 3D 查看器模块

双渲染器插件化架构 —— 轻量任务用 `<model-viewer>`，需要零件高亮/爆炸图/测量标注时用 Three.js。

## 架构

```
lib/viewer/
├── index.dart                       # 模块导出
├── viewer_controller.dart           # 抽象接口（业务方只依赖这个）
├── viewer_controller_impl.dart      # 门面：自动切换、懒加载、自动旋转状态保持
├── viewer_demo_page.dart            # 演示页
├── viewer_exception.dart            # 异常定义
├── model_asset_manager.dart         # 模型元数据 + 本地缓存 + 相对 URL 补全
├── bridge/
│   └── js_bridge.dart               # Dart↔JS 命令通道
├── config/
│   └── viewer_config.dart           # 功能→渲染器映射
├── renderer/
│   ├── viewer_renderer.dart         # 抽象基类（asset 协议加载 HTML）
│   ├── model_viewer_renderer.dart   # 轻量：model-viewer
│   └── threejs_renderer.dart        # 全功能：Three.js
assets/
├── viewer_lite.html                 # model-viewer 页面（~5 KB）
├── viewer_full.html                 # Three.js 页面（~18 KB）
└── vendor/                          # 本地化的 Three.js 0.160.0 + model-viewer 3.5.0（2.3 MB）
```

> 依赖已**完全本地化**到 `assets/vendor/`，不再从 unpkg CDN 加载。
> 校验值、升级步骤、以及包体代价见 `assets/vendor/README.md`。

## 用法

### 基础查看（能看、能 AR、能旋转缩放）

```dart
import 'package:forklift_bao/viewer/index.dart';

final viewer = ViewerControllerImpl();
await viewer.loadModel('https://cdn.xxx/forklift.glb');
await viewer.enterAR();
await viewer.setCamera(azimuth: 45, polarAngle: 60, targetDistance: 3);
await viewer.resetView();
```

### 维修指导（高亮 + 爆炸 + 测量）

```dart
final viewer = ViewerControllerImpl();
viewer.requireFeatures(advancedFeatures); // 自动升级到 Three.js
await viewer.loadModel('https://cdn.xxx/forklift.glb');
await viewer.highlightPart('Mast_Inner', color: Colors.red);
await viewer.setExploded(0.6);
await viewer.measure(from: 'Fork_Left', to: 'Fork_Right', label: '间距');
await viewer.clearMeasure();
await viewer.clearHighlight();
```

### 监听事件

```dart
viewer.events.listen((event) {
  switch (event.name) {
    case 'onModelLoaded': print('模型加载完成');
    case 'onCameraChange': print('相机变化');
    case 'onARStatus': print('AR 状态: ${event.data['status']}');
    case 'onError': print('错误: ${event.data['message']}');
    case 'onPartClicked': print('零件点击: ${event.data['partId']}');
  }
});
```

## 渲染器切换逻辑

| 功能 | 最低等级 | 渲染器 |
|------|---------|--------|
| 加载模型 | lite | `<model-viewer>` |
| AR 放置 | lite | `<model-viewer>` |
| 相机旋转/缩放 | lite | `<model-viewer>` |
| 自动旋转 | lite | 两者都有（full 用 OrbitControls，lite 用 model-viewer 原生） |
| 零件高亮 | **full** | Three.js |
| 爆炸图 | **full** | Three.js |
| 动画播放 | **full** | Three.js |
| 测量标注 | **full** | Three.js |

首次调用高级功能时，门面控制器用**同一个** `WebViewController` 重新加载 full 版本的 HTML，
已加载的模型会自动重载，自动旋转状态也会重新下发。业务层无感。

## 依赖

```yaml
dependencies:
  webview_flutter: ^4.8.0   # 唯一新增原生依赖
```

- Three.js 0.160.0 与 model-viewer 3.5.0 已本地化在 `assets/vendor/`（2.3 MB），
  不再依赖 CDN；升级方式见 `assets/vendor/README.md`。
- `model_viewer_plus`、`flutter_unity_widget` 均已不在依赖中（见 `MIGRATION.md`）。

## 模型约定

- 格式：`.glb`（推荐）或 `.gltf`
- 零件 ID：在 glTF 节点的 `extras.partId` / `extras.partName` 写入
  （`buildPartMap` 会同时索引 `partId`、`partName`、mesh 自身名、最近的具名父节点名，
  所以后端 `model_3d_parts.mesh_name` 存节点名还是 mesh 名都能命中）
- 动画：标准 glTF 动画剪辑（`animations` 数组）
- 点击拾取：位移 < 12px 且时长 < 600ms 判定为点击，否则视为拖拽旋转
- 资产校验：跑 `python3 tools/generate_model_metadata.py --glb <文件> --json`
  可提前知道该资产到底有没有零件层级/动画，避免上线后才发现高亮是假的

## 错误处理

- `onError` 事件：所有错误都会通过事件流上报，载荷含 `method` 便于定位
- 加载失败：不阻塞桥接，可重试；`ThreeDViewerPageV2` 有独立的错误页与重试按钮
- 渲染器切换：没有自动回退到 lite 的机制 —— 切换失败会抛异常并转成
  `onError` 事件，由页面自行处理。（早先文档写的「回退到 lite」并未实现）
- 后端 `file_url` 是相对路径：`ModelAssetManager.resolveUrl` 统一补全成绝对地址，
  因为 WebView 基址是 `asset:///`，相对路径会解析成 `asset:///uploads/...` 直接 404

## AR 技术路线决策（2026-09-12）

**结论：AR 走 lite 渲染器（`<model-viewer>` 原生 AR 按钮），full 渲染器的 WebXR
路径视为不可用，暂不投入。**

依据：

| 方案 | 现状 | 判定 |
|------|------|------|
| WebXR `immersive-ar`（full） | `navigator.xr` 在 Android WebView / iOS WKWebView 内基本不可用；iOS Safari 也不支持 WebXR AR | ❌ 不作为交付路径 |
| Scene Viewer（lite，Android） | 依赖 Google Play 服务 + `com.google.ar.core` 设备白名单 | ⚠️ 可用，覆盖率有限 |
| AR Quick Look（lite，iOS） | 系统原生，无需额外权限 | ✅ 可用 |
| 原生 ARKit / ARCore | 需写原生插件，等价于复活 Unity 那套原生桥工作 | ⏸ 留到 V3.0「维修 AR」阶段 |

落地动作：`viewer_full.html` 的 `enterAR` 保留但会在真机上报
`"浏览器不支持 WebXR"`，`ArViewPageV2` 应引导到 lite 渲染器入口
（`/ar` 路由），不要让用户在 full 渲染器里点一个必然失败的 AR 按钮。

**遗留风险：** 若 AR 1:1 是核心卖点，Scene Viewer 的设备覆盖率不足以支撑主流程，
需要回到原生 ARKit/ARCore。这属于 V3.0 的范围，不应阻塞当前交付。

