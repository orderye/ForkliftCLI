import '../config/viewer_config.dart';
import 'viewer_renderer.dart';

/// 轻量渲染器：<model-viewer> + WebXR / Scene Viewer / AR Quick Look。
///
/// 覆盖：加载模型、相机旋转/缩放、AR 放置、重置视角。
/// 不支持：零件高亮、爆炸图、自定义动画、测量标注 —— 调用这些方法会抛 UnsupportedError，
/// 由门面控制器在 requireFeatures 后自动升级到 Three.js 渲染器。
class ModelViewerRenderer extends ViewerRenderer {
  @override
  String get assetPath => 'assets/viewer_lite.html';

  @override
  RendererTier get tier => RendererTier.lite;

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
}
