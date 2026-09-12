import 'package:webview_flutter/webview_flutter.dart';

import '../bridge/js_bridge.dart';
import '../config/viewer_config.dart';

/// 抽象渲染器基类。
///
/// 两套实现（ModelViewerRenderer / ThreeJSRenderer）继承它。
/// 业务层通过 ViewerController 间接调用，无需关心具体是哪套。
///
/// [init] 已实现：以 asset 协议加载本渲染器对应 HTML 并建立命令桥。
/// JS→Dart 的事件由 ViewerControllerImpl 统一接收（同一 WebViewController 只注册一次通道）。
abstract class ViewerRenderer {
  /// 对应 HTML 资源路径（相对 Flutter assets）。
  String get assetPath;

  /// 能力等级。
  RendererTier get tier;

  /// HTML 加载后等待组件就绪的时间（子类可覆盖）。
  Duration get initDelay => const Duration(milliseconds: 300);

  /// 命令桥（[init] 后可用）。
  JsBridge? bridge;

  /// 初始化渲染器：加载 HTML + 建立命令桥。
  ///
  /// 用 [WebViewController.loadFileUrl] + Flutter 的 `asset` 协议，而不是
  /// `loadHtmlString(..., baseUrl: 'file:///')`。原因：
  /// 1. `file:///` 基址下无法访问打包进 Flutter 的 vendor 资源，
  ///    ES module（`import ... from 'three'`）会被 CORS 直接拦死；
  /// 2. `asset:///assets/viewer_full.html` 与 `asset:///assets/vendor/three/...`
  ///    同源，module 脚本无需 CORS 即可加载，Three.js 因此可完全离线。
  ///
  /// 注意：文档里的相对路径（importmap 中的 `vendor/...`）以本 HTML 所在目录
  /// 为基准解析，改动 assets 目录结构时必须同步检查。
  Future<void> init(WebViewController webView) async {
    final uri = Uri.parse('asset:///$assetPath');
    await webView.loadFileUrl(uri, allowedHeaders: const ['*']);
    bridge = JsBridge(webView);
    await Future<void>.delayed(initDelay);
  }

  /// 释放资源（同一 WebViewController 由控制器持有，此处只断命令桥）。
  Future<void> dispose() async => bridge = null;

  /// 向 JS 下发命令（子类统一入口）。
  Future<void> invoke(String method, [Map<String, dynamic> args = const {}]) =>
      bridge?.call(method, args) ?? Future.value();

  // ---------- 基础功能（两套必须实现） ----------

  Future<void> loadModel(String url, {String? modelId, String? format});
  Future<void> enterAR();
  Future<void> exitAR();
  Future<void> setCamera({double? azimuth, double? polarAngle, double? targetDistance});
  Future<void> resetView();
  Future<void> setAutoRotate(bool enabled, {double? speed});

  // ---------- 高级功能（full 才实现，否则抛 UnsupportedError） ----------

  Future<void> highlightPart(String partId, {String color = '#ffeb3b'}) async {
    throw UnsupportedError('当前渲染器不支持零件高亮');
  }

  Future<void> clearHighlight() async {
    throw UnsupportedError('当前渲染器不支持清除高亮');
  }

  Future<void> setExploded(double progress) async {
    throw UnsupportedError('当前渲染器不支持爆炸图');
  }

  Future<void> playAnimation(String name, {double speed = 1}) async {
    throw UnsupportedError('当前渲染器不支持动画');
  }

  Future<void> stopAnimation() async {
    throw UnsupportedError('当前渲染器不支持动画');
  }

  Future<void> measure({required String from, required String to, String? label}) async {
    throw UnsupportedError('当前渲染器不支持测量');
  }

  Future<void> clearMeasure() async {
    throw UnsupportedError('当前渲染器不支持测量');
  }
}
