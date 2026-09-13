import 'dart:async';

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

  /// HTML 加载后等待组件就绪的时间。
  /// 该字段仅保留兼容旧逻辑；现在改用 onViewerReady 事件驱动，固定 sleep 不可靠。
  @Deprecated('由 onViewerReady 事件替代；保留仅为避免破坏性变更')
  Duration get initDelay => const Duration(milliseconds: 300);

  /// 命令桥（[init] 后可用）。
  JsBridge? bridge;

  /// JS 侧 init 完成后才会被 complete；[invoke] 每次都会 await 它。
  /// 用 Completer 而不是 [Future] 是因为 JS 端通过 [onViewerReady] 事件回调触发，
  /// 这个时点发生在 init 之后、Dart 侧无法预知。
  Completer<void>? _readyCompleter;

  /// 等待 JS 侧发出 [onViewerReady] 后才 resolve。
  Future<void> get ready {
    final c = _readyCompleter;
    return c == null ? Future.value() : c.future;
  }

  /// 由 [ViewerControllerImpl] 在收到 onViewerReady 事件时调用。
  void markReady() {
    final c = _readyCompleter;
    if (c != null && !c.isCompleted) c.complete();
  }

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
  ///
  /// 同步就绪时点：JS 侧 init 完成后主动 `postMessage({event: 'onViewerReady'})`，
  /// [ViewerControllerImpl] 收到后调用 [markReady]；后续 [invoke] 都会先 await
  /// 这个 future，不再用固定 sleep。
  Future<void> init(WebViewController webView) async {
    // webview_flutter 4.x 提供了 loadFlutterAsset，专门用于从 Flutter assets
    // 加载 HTML/CSS/JS，并自动允许同源子资源（vendor/three/...）被同源访问。
    // 旧 API loadFileUrl(assetUri, allowedHeaders) 已在 4.x 移除。
    await webView.loadFlutterAsset(assetPath);
    bridge = JsBridge(webView);
    _readyCompleter = Completer<void>();
  }

  /// 释放资源（同一 WebViewController 由控制器持有，此处只断命令桥）。
  Future<void> dispose() async {
    bridge = null;
    final c = _readyCompleter;
    if (c != null && !c.isCompleted) c.complete();
    _readyCompleter = null;
  }

  /// 向 JS 下发命令（子类统一入口；每次都会等待 JS 侧就绪）。
  Future<void> invoke(String method, [Map<String, dynamic> args = const {}]) async {
    final b = bridge;
    if (b == null) return;
    await ready;
    // dispose 可能在我们 await ready 期间把 bridge 置 null；再次校验避免 race。
    final b2 = bridge;
    if (b2 == null) return;
    await b2.call(method, args);
  }

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
