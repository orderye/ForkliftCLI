import 'dart:async';

import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';

import 'bridge/js_bridge.dart';
import 'config/viewer_config.dart';

/// 统一对外接口 —— 业务方只依赖此接口，不关心底层用哪套渲染器。
///
/// 用法：
/// ```dart
/// final viewer = ViewerControllerImpl();
/// await viewer.loadModel('https://cdn.xxx/forklift.glb');
/// await viewer.enterAR();
///
/// // 需要高级功能时，先声明
/// viewer.requireFeatures(advancedFeatures);
/// await viewer.highlightPart('Mast_Inner', color: Colors.red);
/// await viewer.setExploded(0.6);
/// ```
///
/// 内部：首次调用或 `requireFeatures` 后，按 [RendererTier] 自动选择/切换渲染器。
///
/// [webView] 由控制器持有，页面直接：
/// ```dart
/// WebViewWidget(controller: viewer.webView)
/// ```
/// 同一 controller 在渲染器切换时保持不变，视图无需重建。
abstract class ViewerController {
  /// 页面用这个 controller 渲染 WebViewWidget（生命周期与本控制器一致）。
  WebViewController get webView;

  /// 声明即将需要的功能（会自动升级到需要的渲染器等级）。
  void requireFeatures(Set<ViewerFeature> features);

  /// 是否已初始化。
  bool get isReady;

  /// 是否正在加载（模型加载中或渲染器切换中）。
  bool get isLoading;

  /// 当前渲染器等级。
  RendererTier? get currentTier;

  /// 当前加载的模型 URL（未加载则为 null）。
  String? get currentModelUrl;

  /// 事件流（模型加载完成、相机变化、AR 状态、错误等）。
  Stream<ViewerEvent> get events;

  // ---------- 基础 ----------

  Future<void> loadModel(String url, {String? modelId, String? format});

  Future<void> enterAR();

  Future<void> exitAR();

  Future<void> setCamera({double? azimuth, double? polarAngle, double? targetDistance});

  Future<void> resetView();

  /// 开关自动旋转。用户手动拖拽相机时会自动停止（两套渲染器均如此）。
  /// [speed] 可选：full 渲染器为 OrbitControls.autoRotateSpeed（默认 2.0），
  /// lite 渲染器为 model-viewer autoRotateSpeed（默认 30，量纲不同）。
  Future<void> setAutoRotate(bool enabled, {double? speed});

  // ---------- 高级（lite 渲染器下自动升级；full 渲染器下直接执行） ----------

  Future<void> highlightPart(String partId, {Color color = const Color(0xFFFFEB3B)});

  Future<void> clearHighlight();

  Future<void> setExploded(double progress);

  Future<void> playAnimation(String name, {double speed = 1});

  Future<void> stopAnimation();

  Future<void> measure({required String from, required String to, String? label});

  Future<void> clearMeasure();

  // ---------- 生命周期 ----------

  /// 释放 WebView + 渲染器资源。调用后不可再使用。
  Future<void> dispose();
}
