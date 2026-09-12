import 'dart:async';

import 'package:flutter/material.dart';

import 'config/viewer_config.dart';
import 'viewer_controller.dart';
import 'viewer_controller_impl.dart';

/// UnityBridge → ViewerController 迁移适配器。
///
/// 提供与 [UnityBridge] 相同的方法签名，内部使用 [ViewerController] 实现。
/// 业务方可逐步将 `UnityBridge` 引用替换为本适配器，无需修改调用代码。
///
/// 不支持的功能（Unity 特有）：
/// - setMastHeight / setTiltAngle / setSteerAngle → 通过 playAnimation 映射
/// - setTransparent → 忽略（Web 渲染器暂不支持透明模式）
/// - beginARGuide / endARGuide → 忽略（Web 渲染器暂不支持 AR 维修指导）
/// - showARDimensions / hideARDimensions → 忽略
/// - confirmARPlacement → 忽略（model-viewer 自动处理放置）
/// - setARScale → 忽略（Web 渲染器不支持 AR 缩放控制）
/// - repositionAR → 映射到 resetView
///
/// 使用示例：
/// ```dart
/// // 旧代码（Unity）
/// final bridge = UnityBridge();
/// await bridge.loadModel(url, modelId: 1);
/// await bridge.highlightPart(3, color: '#FF0000');
///
/// // 新代码（Web 渲染器）
/// final bridge = UnityBridgeAdapter();
/// await bridge.loadModel(url, modelId: 1);
/// await bridge.highlightPart(3, color: '#FF0000'); // 同接口
/// ```
class UnityBridgeAdapter {
  final ViewerController _viewer = ViewerControllerImpl();

  /// Unity 侧事件名常量（与 UnityBridge 一致）。
  static const kOnModelLoaded = 'onModelLoaded';
  static const kOnModelCleared = 'onModelCleared';
  static const kOnAnimationComplete = 'onAnimationComplete';
  static const kOnPartClicked = 'onPartClicked';
  static const kOnARPlaneDetected = 'onARPlaneDetected';
  static const kOnARSessionReady = 'onARSessionReady';
  static const kOnARPlaced = 'onARPlaced';
  static const kOnMastHeightChanged = 'onMastHeightChanged';
  static const kOnARGuideStep = 'onARGuideStep';
  static const kOnARGuideEnded = 'onARGuideEnded';
  static const kOnError = 'onError';

  final _eventController = StreamController<Map<String, dynamic>>.broadcast();
  StreamSubscription? _viewerSub;

  /// Unity → Flutter 事件流（与 UnityBridge.events 格式一致）。
  Stream<Map<String, dynamic>> get events => _eventController.stream;

  /// 初始化适配器（加载 viewer 并监听事件）。
  Future<void> init({String? modelUrl, int? modelId}) async {
    if (modelUrl != null) {
      await loadModel(modelUrl, modelId: modelId ?? 0);
    }
    _viewerSub = _viewer.events.listen((event) {
      _eventController.add({'eventName': event.name, 'data': event.data});
    });
  }

  /// 释放资源。
  Future<void> dispose() async {
    await _viewerSub?.cancel();
    await _viewer.dispose();
  }

  // ───────────── Flutter → Renderer ─────────────

  /// 加载 3D 模型。
  Future<void> loadModel(
    String url,
    int modelId, {
    int version = 1,
    String? contentHash,
    String? format,
  }) async =>
      _viewer.loadModel(url, modelId: modelId.toString(), format: format);

  /// 播放动画片段。
  Future <void> playAnimation(String name, {double speed = 1.0}) async {
    await _viewer.requireFeatures({ViewerFeature.animation});
    await _viewer.playAnimation(name, speed: speed);
  }

  /// 停止动画。
  Future <void> stopAnimation(String name) async {
    await _viewer.requireFeatures({ViewerFeature.animation});
    await _viewer.stopAnimation();
  }

  /// 设置门架高度（通过动画映射）。
  ///
  /// Unity 侧用 setMastHeight(mm)，Web 渲染器用 playAnimation('mast_up'/'mast_down')。
  /// 此适配器将 mm 值映射到最近的动画名。
  Future <void> setMastHeight(double heightMm) async {
    // 简单映射：大于平均高度 → mast_up，否则 → mast_down
    const avgHeightMm = 3000;
    await playAnimation(heightMm > avgHeightMm ? 'mast_up' : 'mast_down');
  }

  /// 设置门架倾斜角（通过动画映射）。
  Future <void> setTiltAngle(double angle) async {
    await playAnimation(angle > 0 ? 'tilt_forward' : 'tilt_backward');
  }

  /// 设置后轮转向角（忽略，Web 渲染器暂不支持）。
  Future <void> setSteerAngle(double angle) async {}

  /// 高亮零件。
  Future <void> highlightPart(int partId, {String color = '#FFD700'}) async {
    await _viewer.requireFeatures({ViewerFeature.highlight});
    await _viewer.highlightPart(partId.toString(),
        color: _hexToColor(color));
  }

  /// 清除全部高亮。
  Future <void> clearHighlight() async {
    await _viewer.requireFeatures({ViewerFeature.highlight});
    await _viewer.clearHighlight();
  }

  /// 透明模式（忽略，Web 渲染器暂不支持）。
  Future <void> setTransparent(bool enabled, {String group = 'all'}) async {}

  /// 爆炸图进度。
  Future <void> setExploded(double progress) async {
    await _viewer.requireFeatures({ViewerFeature.exploded});
    await _viewer.setExploded(progress);
  }

  /// 进入 AR 模式。
  Future <void> enterAR(int modelId, Map<String, dynamic> arConfig) async {
    // Web 渲染器不支持 enterAR 参数，直接调用
    await _viewer.enterAR();
  }

  /// 确认 AR 放置（忽略，model-viewer 自动处理）。
  Future <void> confirmARPlacement() async {}

  /// 设置 AR 缩放因子（忽略）。
  Future <void> setARScale(double factor) async {}

  /// 显示 AR 尺寸标注（忽略）。
  Future <void> showARDimensions(bool show) async {}

  /// 隐藏 AR 尺寸标注（忽略）。
  Future <void> hideARDimensions() async {}

  /// 重新放置 AR 模型 → 映射到 resetView。
  Future <void> repositionAR() async => _viewer.resetView();

  /// 重置 3D 相机视角。
  Future <void> resetView() async => _viewer.resetView();

  /// 手动设置相机视角。
  Future <void> setView({
    required double yaw,
    required double pitch,
    double? distance,
  }) async =>
      _viewer.setCamera(azimuth: yaw, polarAngle: pitch, targetDistance: distance);

  /// 清除已加载模型。
  Future <void> clearModel() async {
    // ViewerController 没有 clearModel，通过加载空 URL 模拟
    // 或者调用 dispose + init 重新初始化
    await _viewer.loadModel('', modelId: '0');
  }

  /// AR 维修指导：显示步骤（忽略，Web 渲染器暂不支持）。
  Future <void> beginARGuide(String step, {Map<String, double>? anchor}) async {}

  /// 结束 AR 维修指导（忽略）。
  Future <void> endARGuide() async {}

  // ───────────── private ─────────────

  /// 将十六进制颜色字符串转为 Flutter Color。
  Color _hexToColor(String hex) {
    hex = hex.replaceFirst('#', '');
    if (hex.length == 6) hex = 'FF$hex';
    final val = int.tryParse(hex, radix: 16) ?? 0xFF888888;
    return Color(val);
  }
}
