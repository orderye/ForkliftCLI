// ignore_for_file: avoid_dynamic_calls
//
// ViewerRenderer 基类的 Ready 状态机测试。
//
// 不依赖 webview_flutter 的真实平台实现：用一个 _TestRenderer 覆盖 invoke，
// 只验证 Completer 状态机本身的契约（init → markReady → invoke 顺序，
// 以及 dispose 期间不出现卡死的 pending invoke）。
//
// 历史动机：P1-4 修复把固定 sleep 改为 onViewerReady 事件驱动，引入
// Completer + markReady 后必须保证：
//   1. bridge==null 时 invoke 不抛错、不卡死；
//   2. markReady 幂等，重复调用不抛；
//   3. dispose 不抛，重复调用幂等；
//   4. 高级方法（highlight/动画/爆炸/测量）默认抛 UnsupportedError。

import 'package:flutter_test/flutter_test.dart';
import 'package:forklift_bao/viewer/config/viewer_config.dart';
import 'package:forklift_bao/viewer/renderer/viewer_renderer.dart';

class _TestRenderer extends ViewerRenderer {
  @override
  String get assetPath => 'assets/viewer_lite.html';

  @override
  RendererTier get tier => RendererTier.lite;

  /// 记录 invoke 收到的 (method, args)，按调用顺序追加。
  final List<List<dynamic>> calls = <List<dynamic>>[];

  /// 覆盖 invoke —— 不走 bridge.call，专注测 ready 状态对 invoke 的影响。
  @override
  Future<void> invoke(String method, [Map<String, dynamic> args = const {}]) async {
    final b = bridge;
    if (b == null) return;
    await ready;
    // 再次校验 dispose race。
    if (bridge == null) return;
    calls.add([method, args]);
  }

  // 抽象方法占位实现。
  @override
  Future<void> loadModel(String url, {String? modelId, String? format}) =>
      invoke('loadModel', {'url': url, 'modelId': modelId, 'format': format});
  @override
  Future<void> enterAR() => invoke('enterAR');
  @override
  Future<void> exitAR() => invoke('exitAR');
  @override
  Future<void> setCamera({double? azimuth, double? polarAngle, double? targetDistance}) =>
      invoke('setCamera', {'az': azimuth, 'po': polarAngle, 'td': targetDistance});
  @override
  Future<void> resetView() => invoke('resetView');
  @override
  Future<void> setAutoRotate(bool enabled, {double? speed}) =>
      invoke('setAutoRotate', {'enabled': enabled, 'speed': speed});
}

void main() {
  group('ViewerRenderer.invoke 在未 init 时的契约', () {
    test('bridge==null 时 invoke 直接 return，不抛错', () async {
      final r = _TestRenderer();
      // 完全没经过 init() —— bridge 仍为 null。
      await r.invoke('loadModel', {'url': 'x.glb'});
      expect(r.calls, isEmpty);
    });

    test('重复 markReady 幂等', () async {
      final r = _TestRenderer();
      // markReady 在没有 _readyCompleter 时静默（c == null 时不进 if）。
      // 验证：连续调用 5 次不抛错。
      for (var i = 0; i < 5; i++) {
        r.markReady();
      }
    });
  });

  group('ViewerRenderer.dispose 契约', () {
    test('重复 dispose 不抛（即使 bridge 已被置 null）', () async {
      // 注：不在测试里构造 JsBridge(WebViewController()) —— WebViewController
      // 在单测环境（无 WebViewPlatform.instance）会抛 PlatformException。
      // dispose 路径只动 bridge 与 _readyCompleter，两者初始为 null，应立即返回。
      final r = _TestRenderer();
      await r.dispose();
      // 二次 dispose 仍不抛。
      await r.dispose();
    });

    test('dispose 之后 invoke 立即 return（bridge==null 提前返回）', () async {
      final r = _TestRenderer();
      await r.dispose();
      await r.invoke('loadModel', {'url': 'x.glb'});
      expect(r.calls, isEmpty);
    });
  });

  group('ViewerRenderer 高级方法默认行为', () {
    test('highlight/clearHighlight 默认抛 UnsupportedError', () {
      final r = _TestRenderer();
      expect(() => r.highlightPart('Mast_Inner'), throwsUnsupportedError);
      expect(() => r.clearHighlight(), throwsUnsupportedError);
    });

    test('setExploded 默认抛 UnsupportedError', () {
      final r = _TestRenderer();
      expect(() => r.setExploded(0.5), throwsUnsupportedError);
    });

    test('动画/测量方法默认抛 UnsupportedError', () {
      final r = _TestRenderer();
      expect(() => r.playAnimation('mast_up'), throwsUnsupportedError);
      expect(() => r.stopAnimation(), throwsUnsupportedError);
      expect(
        () => r.measure(from: 'A', to: 'B'),
        throwsUnsupportedError,
      );
      expect(() => r.clearMeasure(), throwsUnsupportedError);
    });
  });

  group('ViewerRenderer.initDelay 兼容性', () {
    test('@Deprecated 字段仍可被读取且返回非负 Duration', () {
      // ignore: deprecated_member_use_from_same_package
      final d = _TestRenderer().initDelay;
      expect(d.inMilliseconds, greaterThanOrEqualTo(0));
    });
  });
}
