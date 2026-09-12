# Unity → Web 渲染器迁移指南

## 迁移状态

| 组件 | 状态 | 替代方案 |
|------|------|----------|
| `UnityBridge` | ⚠️ DEPRECATED | `UnityBridgeAdapter` 或 `ViewerController` |
| `UnityViewWrapper` | ⚠️ DEPRECATED | `WebViewWidget` + `ViewerController` |
| `ThreeDViewerPage` (V1) | 已替换 | `ThreeDViewerPageV2` |
| `ArViewPage` (V1) | 已替换 | `ArViewPageV2` |
| `flutter_unity_widget` 依赖 | 已注释 | `webview_flutter` |

## 迁移步骤

### Step 1: 替换 UnityBridge 调用

```dart
// 旧代码
final bridge = UnityBridge();
await bridge.loadModel(url, modelId: 1);
await bridge.highlightPart(3, color: '#FF0000');

// 新代码（适配器，接口不变）
final bridge = UnityBridgeAdapter();
await bridge.init(modelUrl: url, modelId: 1);
await bridge.loadModel(url, modelId: 1);
await bridge.highlightPart(3, color: '#FF0000');
```

### Step 2: 替换 UnityViewWrapper

```dart
// 旧代码
UnityViewWrapper(
  forkliftModelId: modelId,
  modelUrl: url,
  enableAR: false,
  onModelLoaded: () {},
);

// 新代码
WebViewWidget(controller: _webView)
// + ViewerController 在 initState 中加载
```

### Step 3: 页面迁移清单

| 旧页面 | 新页面 | 路由 |
|--------|--------|------|
| `features/threed/threed_viewer_page.dart` | `features/threed/threed_viewer_page_v2.dart` | `/3d` |
| `features/ar/ar_view_page.dart` | `features/ar/ar_view_page_v2.dart` | `/ar` |
| （新增） | `viewer/maintenance_guide_page.dart` | `/maintenance/:id` |
| （新增） | `viewer/viewer_demo_page.dart` | `/viewer` |
| （新增） | `viewer/ar_view_page.dart` | `/ar-web` |

## 功能差异

| 功能 | Unity | Web 渲染器 | 备注 |
|------|-------|-----------|------|
| 加载模型 | ✅ | ✅ | glTF/GLB |
| 相机旋转/缩放 | ✅ | ✅ | OrbitControls |
| AR 放置 | ✅ | ✅ | Scene Viewer / WebXR |
| 零件高亮 | ✅ | ✅ | emissive 材质 |
| 爆炸图 | ✅ | ✅ | 按方向分离 |
| 动画播放 | ✅ | ✅ | AnimationMixer |
| 测量标注 | ✅ | ✅ | Line + Sprite |
| 门架高度控制 | ✅ (Transform) | ⚠️ 动画映射 | `setMastHeight` → `playAnimation` |
| 透明模式 | ✅ | ❌ | Web 渲染器暂不支持 |
| AR 维修指导 | ✅ | ❌ | Web 渲染器暂不支持 |
| AR 尺寸标注 | ✅ | ❌ | Web 渲染器暂不支持 |

## 回退方案

如需回退到 Unity 渲染器：

1. 取消 `pubspec.yaml` 中 `flutter_unity_widget` 的注释
2. 将路由指回 V1 页面：
   ```dart
   GoRoute(path: '/3d', builder: (context, state) => ThreeDViewerPage(...));
   GoRoute(path: '/ar', builder: (context, state) => ArViewPage(...));
   ```
3. 确认 Unity 工程 (`unity/` 目录) 仍存在

## 包体对比

| 方案 | 包体增量 | 启动速度 |
|------|---------|---------|
| Unity (V1) | +25 MB | 慢（~3-5s） |
| Web 渲染器 (V2) | +200 KB | 快（~1-2s） |

## 后续清理（验证通过后）

```bash
# 1. 删除 V1 页面
rm lib/features/threed/threed_viewer_page.dart
rm lib/features/ar/ar_view_page.dart

# 2. 删除 Unity 核心代码
rm -rf lib/core/unity/

# 3. 删除 Unity 工程
rm -rf unity/

# 4. 确认 pubspec.yaml 无 flutter_unity_widget
```
