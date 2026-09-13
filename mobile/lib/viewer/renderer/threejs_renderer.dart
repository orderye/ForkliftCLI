import '../config/viewer_config.dart';
import 'viewer_renderer.dart';

/// 全功能渲染器：Three.js + GLTFLoader + OrbitControls。
///
/// 覆盖 ModelViewerRenderer 的全部能力，并额外提供：
/// 零件高亮、爆炸图、自定义动画、测量标注。
/// 对应 HTML：assets/viewer_full.html。
///
/// JS 桥协议与 ModelViewerRenderer 完全一致 —— 业务层无感切换。
class ThreeJSRenderer extends ViewerRenderer {
  @override
  String get assetPath => 'assets/viewer_full.html';

  @override
  RendererTier get tier => RendererTier.full;

  @override
  Future<void> loadModel(String url, {String? modelId, String? format}) =>
      invoke('loadModel', {'url': url, 'modelId': modelId, 'format': format});

  @override
  Future<void> enterAR() => invoke('enterAR');

  @override
  Future<void> exitAR() => invoke('exitAR');

  @override
  Future<void> setCamera({double? azimuth, double? polarAngle, double? targetDistance}) =>
      invoke('setCamera', {
        'azimuth': azimuth,
        'polarAngle': polarAngle,
        'targetDistance': targetDistance,
      });

  @override
  Future<void> resetView() => invoke('resetView');

  @override
  Future<void> setAutoRotate(bool enabled, {double? speed}) => invoke(
    'setAutoRotate', {
      'enabled': enabled,
      if (speed != null) 'speed': speed,
    },
  );

  // ---------- 高级功能 ----------

  @override
  Future<void> highlightPart(String partId, {String color = '#ffeb3b'}) =>
      invoke('highlightPart', {'partId': partId, 'color': color});

  @override
  Future<void> clearHighlight() => invoke('clearHighlight');

  @override
  Future<void> setExploded(double progress) =>
      invoke('setExploded', {'progress': progress});

  @override
  Future<void> playAnimation(String name, {double speed = 1}) =>
      invoke('playAnimation', {'name': name, 'speed': speed});

  @override
  Future<void> stopAnimation() => invoke('stopAnimation');

  @override
  Future<void> measure({required String from, required String to, String? label}) =>
      invoke('measure', {'from': from, 'to': to, 'label': label});

  @override
  Future<void> clearMeasure() => invoke('clearMeasure');
}
