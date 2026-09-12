# 本地化的前端渲染依赖

3D/AR 渲染器原先从 `https://unpkg.com` CDN 加载 Three.js 与 model-viewer。
叉车维修场景多在车库、仓库、室外，弱网环境下 CDN 不可达，整个 3D/AR 页面直接白屏。
因此把依赖打进 Flutter assets，随包分发、完全离线。

## 文件清单与校验值

| 文件 | 版本 | 大小 | SHA256 |
|---|---|---|---|
| `three/three.module.js` | 0.160.0（`REVISION='160'`） | 1.27 MB | `76dea8151bc9352aef3528b4262e249b2604f62543828328db978d060d61a495` |
| `three/addons/controls/OrbitControls.js` | 0.160.0 | 29.9 KB | `5a44a9e86a2a0fb11933eed69bc2cd33c76a496854c1aed6ed776efa87d7b064` |
| `three/addons/loaders/GLTFLoader.js` | 0.160.0 | 108.5 KB | `d073b438e6a07e1359741dd5d6c76c953420cc0d4fd84eb1bdde94315540e6a3` |
| `three/addons/utils/BufferGeometryUtils.js` | 0.160.0 | 31.9 KB | `9be041e96308775d00e2695cc607645b9a9b64fd7c0e759dd8f7c00a8d92becb` |
| `model-viewer/model-viewer.min.js` | 3.5.0 | 935.2 KB | `8923739c8c1b4a02dd9c8cf66da5c2a448235cb5e49e439dd7bbba944ba4fbe1` |

合计 **2.3 MB**。

> `BufferGeometryUtils.js` 是 `GLTFLoader.js` 的隐式依赖
> （`import { toTrianglesDrawMode } from '../utils/BufferGeometryUtils.js'`），
> 漏掉它会在真机上表现为 GLTFLoader 静默加载失败。
>
> `DRACOLoader` 已不再引用：现有 GLB 资产 `extensionsUsed` 为空、未启用
> `KHR_draco_mesh_compression`，去掉它省下一个 WASM 解码器与一处 CDN 依赖。

## 包体代价（诚实记录）

Web 渲染器方案的原始卖点是「+200 KB」，那是把 Three.js 放在 CDN 上算的。
本地化后 3D/AR 相关资产的真实增量是：

```
assets/viewer_full.html      约 18 KB
assets/viewer_lite.html      约 6 KB
assets/vendor/               2.3 MB
```

即用 ~2.3 MB 包体换取完全不依赖网络的 3D/AR。对比 Unity 方案的 ~+25 MB，
仍然划算得多；但「200 KB」这个数字在离线要求下不成立，文档里不要再引用它。

## 路径解析（改动 assets 结构前必读）

`viewer_renderer.dart` 用 `webView.loadFileUrl(Uri.parse('asset:///$assetPath'))`
加载 HTML，**不是** `loadHtmlString(..., baseUrl: 'file:///')`。原因：

1. `file:///` 基址下无法访问打包进 Flutter 的资源，
   ES module（`import ... from 'three'`）会被 CORS 拦死；
2. `asset:///assets/viewer_full.html` 与 `asset:///assets/vendor/three/...` 同源，
   module 脚本无需 CORS 即可加载。

因此两份 HTML 里的引用都是**相对本文件所在目录**（`asset:///assets/`）的相对路径：

```html
<!-- viewer_full.html -->
<script type="importmap">
{ "imports": {
    "three": "vendor/three/three.module.js",
    "three/addons/": "vendor/three/addons/"
}}
</script>

<!-- viewer_lite.html -->
<script type="module" src="vendor/model-viewer/model-viewer.min.js"></script>
```

- 不要把这三个 `vendor/...` 改成绝对路径（`assets/vendor/...`）——
  基准目录已经是 `asset:///assets/`，再加 `assets/` 会重复成
  `asset:///assets/assets/vendor/...` 而 404。
- `pubspec.yaml` 的 `assets:` 里已包含 `- assets/`，整个目录都会被打包，
  vendor 下的文件无需单独声明。

## 升级依赖

```bash
cd mobile/assets/vendor/three
curl -sS -o three.module.js                 https://unpkg.com/three@<新版本>/build/three.module.js
curl -sS -o addons/controls/OrbitControls.js https://unpkg.com/three@<新版本>/examples/jsm/controls/OrbitControls.js
curl -sS -o addons/loaders/GLTFLoader.js    https://unpkg.com/three@<新版本>/examples/jsm/loaders/GLTFLoader.js
curl -sS -o addons/utils/BufferGeometryUtils.js https://unpkg.com/three@<新版本>/examples/jsm/utils/BufferGeometryUtils.js
```

升级后必须：
1. 重新计算 SHA256 并更新本表；
2. 检查各 addon 是否新增了 `import`（新版本可能引入新依赖文件）；
3. 在真机上跑一遍 3D 查看 + AR 放置，确认 module 加载与 GLTF 解析正常。

> import map 需要 Chromium 89+ / iOS 16.4+ 的 WebView 支持。
> 若要兼容更早系统，只能把 Three.js 内联进 HTML 或改用打包工具合并成单文件。

## 已知限制（真机行为需实测确认）

以下涉及原生 WebView 能力，本地静态检查无法验证，**上真机前必须实测**：

- `asset://` 协议加载 ES module 在 Android WebView 与 iOS WKWebView 上的实际行为
  （iOS 侧可能需要在 `Info.plist` 配置 `WKWebViewCustomProtocolAllowedSchemes`）；
- `viewer_lite.html` 的 AR 能力：`ar-modes="webxr scene-viewer quick-look"` 中
  WebXR 在 WebView 内不可用，Scene Viewer 依赖 Google Play 服务，Quick Look 仅 iOS 有效；
- `viewer_full.html` 的 WebXR `immersive-ar` 在 WebView 内**预期不可用**，
  该路径目前视为不可用，AR 请走 lite 渲染器。
