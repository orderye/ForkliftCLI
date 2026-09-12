import 'dart:async';
import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';

import 'bridge/js_bridge.dart';
import 'config/viewer_config.dart';
import 'renderer/model_viewer_renderer.dart';
import 'renderer/threejs_renderer.dart';
import 'renderer/viewer_renderer.dart';
import 'viewer_controller.dart';

/// [ViewerController] 默认实现：门面 + 懒加载 + 按需升级渲染器。
///
/// 整个生命周期复用同一个 [WebViewController]：页面直接渲染 [webView]；
/// 切换渲染器只是用同一个 controller 重新加载另一份 HTML，视图无需重建。
///
/// JS→Dart 事件通过一次性注册的 `FlutterViewer` JavascriptChannel 回流；
/// Dart→JS 命令由各渲染器的 [JsBridge] 下发。
class ViewerControllerImpl implements ViewerController {
  ViewerControllerImpl() {
    _webView.addJavaScriptChannel(
      JavaScriptChannel(
        name: 'FlutterViewer',
        onMessageReceived: _onMessageFromJS,
      ),
    );
  }

  final Set<ViewerFeature> _requiredFeatures = {ViewerFeature.basic, ViewerFeature.ar};
  final StreamController<ViewerEvent> _events = StreamController<ViewerEvent>.broadcast();

  /// 页面用这个 controller 渲染 WebViewWidget（生命周期与本控制器一致）。
  final WebViewController _webView = WebViewController()
    ..setJavaScriptMode(JavaScriptMode.unrestricted)
    ..setBackgroundColor(const Color(0xFF1A1A2E));

  ViewerRenderer? _renderer;
  RendererTier? _currentTier;

  String? _lastModelUrl;
  String? _lastModelId;
  bool _loading = false;

  // 自动旋转意图需要在渲染器切换（lite→full 重建 HTML）后重新下发，
  // 否则切到 full 后 JS 侧默认 autoRotate=true 会覆盖用户之前的关闭操作。
  bool _autoRotate = true;

  @override
  WebViewController get webView => _webView;

  @override
  bool get isReady => _renderer?.bridge != null;

  @override
  bool get isLoading => _loading;

  @override
  RendererTier? get currentTier => _currentTier;

  @override
  String? get currentModelUrl => _lastModelUrl;

  @override
  Stream<ViewerEvent> get events => _events.stream;

  @override
  void requireFeatures(Set<ViewerFeature> features) {
    _requiredFeatures.addAll(features);
  }

  // ---------- 内部：按需求等级确保渲染器就绪 ----------

  Future<ViewerRenderer> _ensureRenderer(RendererTier tier) async {
    if (_currentTier == tier && _renderer != null) return _renderer!;

    // 切换渲染器：断开旧桥，把新 HTML 载入同一个 controller。
    await _renderer?.dispose();

    _renderer = tier == RendererTier.lite
        ? ModelViewerRenderer()
        : ThreeJSRenderer();
    _currentTier = tier;

    await _renderer!.init(_webView);

    // 若已加载过模型，切换渲染器后自动重加载（保持业务无感）。
    if (_lastModelUrl != null) {
      await _renderer!.loadModel(_lastModelUrl!, modelId: _lastModelId);
    }

    // 重新下发自动旋转状态（JS 侧默认开启，需覆盖用户的显式关闭）。
    await _renderer!.setAutoRotate(_autoRotate);

    debugPrint('[Viewer] 渲染器就绪 tier=$tier');
    return _renderer!;
  }

  // ---------- 基础功能（自动解析等级） ----------

  @override
  Future<void> loadModel(String url, {String? modelId, String? format}) async {
    if (_loading) {
      debugPrint('[Viewer] 已有加载任务进行中，忽略本次请求');
      return;
    }

    // URL 校验（拒绝相对路径等非显式协议，避免 JS 侧静默失败）
    final allowed = url.startsWith('http://') ||
        url.startsWith('https://') ||
        url.startsWith('file://') ||
        url.startsWith('data:');
    if (!allowed) {
      _events.add(ViewerEvent(
          name: 'onError', data: {'message': '无效的模型 URL', 'url': url, 'method': 'loadModel'}));
      return;
    }

    _lastModelUrl = url;
    _lastModelId = modelId;
    _loading = true;
    try {
      final r = await _ensureRenderer(resolveTier(_requiredFeatures));
      await r.loadModel(url, modelId: modelId, format: format);
    } catch (e, st) {
      debugPrint('[Viewer] loadModel 异常: $e\n$st');
      _events.add(ViewerEvent(
          name: 'onError', data: {'message': e.toString(), 'url': url, 'method': 'loadModel'}));
    } finally {
      _loading = false;
    }
  }

  @override
  Future<void> enterAR() async =>
      (await _ensureRenderer(resolveTier(_requiredFeatures))).enterAR();

  @override
  Future<void> exitAR() async =>
      (await _ensureRenderer(resolveTier(_requiredFeatures))).exitAR();

  @override
  Future<void> setCamera(
          {double? azimuth, double? polarAngle, double? targetDistance}) async =>
      (await _ensureRenderer(resolveTier(_requiredFeatures)))
          .setCamera(azimuth: azimuth, polarAngle: polarAngle, targetDistance: targetDistance);

  @override
  Future<void> resetView() async =>
      (await _ensureRenderer(resolveTier(_requiredFeatures))).resetView();

  @override
  Future<void> setAutoRotate(bool enabled, {double? speed}) async {
    _autoRotate = enabled;
    await (await _ensureRenderer(resolveTier(_requiredFeatures))).setAutoRotate(enabled, speed: speed);
  }

  // ---------- 高级功能（自动升级到 full） ----------

  @override
  Future<void> highlightPart(String partId, {Color color = const Color(0xFFFFEB3B)}) async {
    _requiredFeatures.add(ViewerFeature.highlight);
    final r = await _ensureRenderer(resolveTier(_requiredFeatures));
    await r.highlightPart(partId, color: _cssColor(color));
  }

  @override
  Future<void> clearHighlight() async {
    _requiredFeatures.add(ViewerFeature.highlight);
    await (await _ensureRenderer(resolveTier(_requiredFeatures))).clearHighlight();
  }

  @override
  Future<void> setExploded(double progress) async {
    _requiredFeatures.add(ViewerFeature.exploded);
    await (await _ensureRenderer(resolveTier(_requiredFeatures))).setExploded(progress);
  }

  @override
  Future<void> playAnimation(String name, {double speed = 1}) async {
    _requiredFeatures.add(ViewerFeature.animation);
    await (await _ensureRenderer(resolveTier(_requiredFeatures))).playAnimation(name, speed: speed);
  }

  @override
  Future<void> stopAnimation() async {
    _requiredFeatures.add(ViewerFeature.animation);
    await (await _ensureRenderer(resolveTier(_requiredFeatures))).stopAnimation();
  }

  @override
  Future<void> measure({required String from, required String to, String? label}) async {
    _requiredFeatures.add(ViewerFeature.measure);
    await (await _ensureRenderer(resolveTier(_requiredFeatures))).measure(from: from, to: to, label: label);
  }

  @override
  Future<void> clearMeasure() async {
    _requiredFeatures.add(ViewerFeature.measure);
    await (await _ensureRenderer(resolveTier(_requiredFeatures))).clearMeasure();
  }

  // ---------- 事件回流 ----------

  void _onMessageFromJS(JavaScriptMessage message) {
    try {
      final map = jsonDecode(message.message) as Map<String, dynamic>;
      final name = map['event'] as String?;
      if (name == null) return;
      final data = map['data'];
      _events.add(ViewerEvent(
        name: name,
        data: data is Map
            ? data.map((k, v) => MapEntry(k.toString(), v))
            : const {},
      ));
    } catch (e) {
      debugPrint('[Viewer] JS 事件解析失败: $e');
    }
  }

  /// CSS 颜色字符串 `#rrggbb`。JS 侧（three.js Color / CSS）不认 ARGB。
  static String _cssColor(Color c) {
    String two(int v) => v.clamp(0, 255).toRadixString(16).padLeft(2, '0');
    return '#${two((c.r * 255).round())}${two((c.g * 255).round())}${two((c.b * 255).round())}';
  }

  // ---------- 生命周期 ----------

  @override
  Future<void> dispose() async {
    await _renderer?.dispose();
    _renderer = null;
    _currentTier = null;
    await _events.close();
  }
}
