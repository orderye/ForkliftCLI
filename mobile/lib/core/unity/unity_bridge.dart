import 'dart:async';
import 'dart:convert';

import 'package:flutter_unity_widget/flutter_unity_widget.dart';

/// Unity ↔ Flutter 通信桥。
///
/// 传输层由 [flutter_unity_widget] 提供：
/// - Flutter → Unity：`controller.postMessage('UnityMessageManager',
///   'OnMessageFromFlutter', json)`，Unity 侧 [UnityMessageManager] 解析 JSON。
/// - Unity → Flutter：Unity 调用 `UnityMessageManager.SendToFlutter(event, json)`，
///   经原生桥（Step 6）转发到 `UnityWidget.onUnityMessage`，本桥转成 Dart 流。
///
/// 事件载荷统一为 `{"eventName": "...", "data": {...}}`。
class UnityBridge {
  static const String _gameObject = 'UnityMessageManager';
  static const String _method = 'OnMessageFromFlutter';

  /// Unity 侧事件名常量。
  static const kOnModelLoaded = 'onModelLoaded';
  static const kOnAnimationComplete = 'onAnimationComplete';
  static const kOnPartClicked = 'onPartClicked';
  static const kOnARPlaneDetected = 'onARPlaneDetected';
  static const kOnARSessionReady = 'onARSessionReady';
  static const kOnARPlaced = 'onARPlaced';
  static const kOnMastHeightChanged = 'onMastHeightChanged';
  static const kOnError = 'onError';

  UnityWidgetController? _controller;
  final _eventController = StreamController<Map<String, dynamic>>.broadcast();
  bool _attached = false;

  /// Unity → Flutter 事件流，每项为 `{eventName, data}`。
  Stream<Map<String, dynamic>> get events => _eventController.stream;

  /// 由 [UnityViewWrapper] 在 `onUnityCreated` 时调用，绑定控制器。
  void attach(UnityWidgetController controller) {
    _controller = controller;
    _attached = true;
  }

  /// 由 [UnityViewWrapper] 在 `onUnityMessage` 时调用，转发 Unity 事件。
  void onUnityMessage(dynamic message) {
    if (message is! Map) return;
    final map = message.map((k, v) => MapEntry(k.toString(), v));
    if (map['eventName'] == null) return;
    _eventController.add(map);
  }

  /// 由 [UnityViewWrapper] 在 `dispose` 时调用。
  void detach() {
    _controller = null;
    _attached = false;
  }

  bool get isAttached => _attached;

  // ─────────────────────────── Flutter → Unity ───────────────────────────

  /// 加载 3D 模型（.glb URL）。
  Future<void> loadModel(String url, int modelId) async =>
      _post('loadModel', {'url': url, 'modelId': modelId});

  /// 播放动画片段（mast_up / tilt_forward / fork_up ...）。
  Future<void> playAnimation(String name, {double speed = 1.0}) async =>
      _post('playAnimation', {'name': name, 'speed': speed});

  /// 停止动画。
  Future<void> stopAnimation(String name) async =>
      _post('stopAnimation', {'name': name});

  /// 设置门架高度（毫米）。
  Future<void> setMastHeight(double heightMm) async =>
      _post('setMastHeight', {'heightMm': heightMm});

  /// 设置门架倾斜角（度，前倾为正）。
  Future<void> setTiltAngle(double angle) async =>
      _post('setTiltAngle', {'angle': angle});

  /// 设置后轮转向角（度）。
  Future<void> setSteerAngle(double angle) async =>
      _post('setSteerAngle', {'angle': angle});

  /// 高亮零件。
  Future<void> highlightPart(int partId, {String color = '#FFD700'}) async =>
      _post('highlightPart', {'partId': partId, 'color': color});

  /// 清除全部高亮。
  Future<void> clearHighlight() async => _post('clearHighlight', {});

  /// 透明模式。
  Future<void> setTransparent(bool enabled, {String group = 'all'}) async =>
      _post('setTransparent', {'enabled': enabled, 'group': group});

  /// 爆炸图进度（0.0 ~ 1.0）。
  Future<void> setExploded(double progress) async =>
      _post('setExploded', {'progress': progress});

  /// 进入 AR 模式。
  Future<void> enterAR(int modelId, Map<String, dynamic> arConfig) async =>
      _post('enterAR', {'modelId': modelId, 'arConfig': arConfig});

  /// 确认 AR 放置。
  Future<void> confirmARPlacement() async =>
      _post('confirmARPlacement', {});

  /// 设置 AR 缩放因子（1.0 = 1:1）。
  Future<void> setARScale(double factor) async =>
      _post('setARScale', {'factor': factor});

  /// 显示/隐藏 AR 尺寸标注。
  Future<void> showARDimensions(bool show) async =>
      _post('showARDimensions', {'show': show});

  /// 重置 3D 相机视角。
  Future<void> resetView() async => _post('resetView', {});

  Future<void> _post(String method, Map<String, dynamic> data) async {
    if (_controller == null) {
      _eventController.add({
        'eventName': kOnError,
        'data': {'message': 'Unity 未连接', 'method': method},
      });
      return;
    }
    final json = jsonEncode({'method': method, 'data': data});
    _controller!.postMessage(_gameObject, _method, json);
  }
}