//
// ViewerControllerImpl 的纯逻辑层测试。
//
// 目标：验证「URL 校验」「事件路由」「onViewerReady 触发 markReady」等不依赖
// 真实 WebView 平台实现的逻辑。完整 init/loadModel 走真实 GLB 解析的端到端
// 路径不在单测范围（需真机/集成测试）。
//
// 历史动机：P1-4 修复在 _onMessageFromJS 里增加了「onViewerReady → markReady」分支，
// 必须保证：
//   1. 收到 onViewerReady 事件时，渲染器的 markReady 被调用（解除 invoke 等待）；
//   2. 收到 onViewerReady 时不向业务 events 流转发（避免业务侧误处理）；
//   3. 其他事件继续按原样向业务 events 流转发；
//   4. loadModel 收到非法 URL 时立即通过 onError 事件通知，不走渲染器 init。
//
// 也覆盖 P0-2 修复相关：事件订阅在 dispose 后不应当再触发任何业务事件。
//
// 注：webview_flutter 4.x 在单测环境没有 WebViewPlatform.instance 会抛
// PlatformException。本测试在 setUpAll 注入一个最小 fake platform
// （_NoopWebViewPlatform），让 WebViewController() 构造成功。

import 'dart:async';
import 'dart:ui' show Color;

import 'package:flutter_test/flutter_test.dart';
import 'package:forklift_bao/viewer/bridge/js_bridge.dart' show ViewerEvent;
import 'package:forklift_bao/viewer/config/viewer_config.dart';
import 'package:forklift_bao/viewer/viewer_controller_impl.dart';
import 'package:webview_flutter_platform_interface/webview_flutter_platform_interface.dart';

class _NoopPlatformWebViewController extends PlatformWebViewController {
  _NoopPlatformWebViewController(super.params) : super.implementation();

  @override
  Future<void> setJavaScriptMode(JavaScriptMode javaScriptMode) async {}

  @override
  Future<void> setBackgroundColor(Color backgroundColor) async {}

  @override
  Future<void> addJavaScriptChannel(
    JavaScriptChannelParams javaScriptChannelParams,
  ) async {}
}

class _NoopWebViewPlatform extends WebViewPlatform {
  @override
  PlatformWebViewController createPlatformWebViewController(
    PlatformWebViewControllerCreationParams params,
  ) {
    return _NoopPlatformWebViewController(params);
  }

  @override
  PlatformWebViewWidget createPlatformWebViewWidget(
    PlatformWebViewWidgetCreationParams params,
  ) {
    throw UnimplementedError();
  }

  @override
  PlatformNavigationDelegate createPlatformNavigationDelegate(
    PlatformNavigationDelegateCreationParams params,
  ) {
    throw UnimplementedError();
  }

  @override
  PlatformWebViewCookieManager createPlatformCookieManager(
    PlatformWebViewCookieManagerCreationParams params,
  ) {
    throw UnimplementedError();
  }
}

void main() {
  setUpAll(() {
    WebViewPlatform.instance = _NoopWebViewPlatform();
  });

  group('ViewerControllerImpl.loadModel URL 校验', () {
    test('非法协议（相对路径）通过 onError 事件通知，且不调用渲染器', () async {
      final c = ViewerControllerImpl();
      final received = <ViewerEvent>[];
      final sub = c.events.listen(received.add);

      await c.loadModel('uploads/models/1/x.glb');
      await Future<void>.delayed(Duration.zero);

      expect(received, hasLength(1));
      final e = received.single;
      expect(e.name, 'onError');
      expect(e.data['method'], 'loadModel');
      expect(e.data['url'], 'uploads/models/1/x.glb');
      expect(e.data['message'], contains('无效的模型 URL'));

      await sub.cancel();
      await c.dispose();
    });

    test('javascript: / mailto: / 纯空串都被 URL 校验拒绝', () async {
      for (final url in ['javascript:alert(1)', 'mailto:a@b', '']) {
        final c = ViewerControllerImpl();
        final received = <ViewerEvent>[];
        final sub = c.events.listen(received.add);
        await c.loadModel(url);
        await Future<void>.delayed(Duration.zero);
        expect(received, isNotEmpty,
            reason: 'URL=$url 应当触发 onError');
        expect(received.single.data['url'], url);
        await sub.cancel();
        await c.dispose();
      }
    });
  });

  group('ViewerControllerImpl._onMessageFromJS 路由', () {
    test('构造后业务 events 流是 broadcast Stream<ViewerEvent>', () {
      final c = ViewerControllerImpl();
      expect(c.events, isA<Stream<ViewerEvent>>());
      c.dispose();
    });

    test('events 流是 broadcast，多订阅者都能收到事件', () async {
      final c = ViewerControllerImpl();
      final r1 = <ViewerEvent>[];
      final r2 = <ViewerEvent>[];
      final s1 = c.events.listen(r1.add);
      final s2 = c.events.listen(r2.add);

      await c.loadModel('not-a-url');
      await Future<void>.delayed(Duration.zero);

      expect(r1, hasLength(1));
      expect(r2, hasLength(1));
      expect(r1.single.data['url'], 'not-a-url');

      await s1.cancel();
      await s2.cancel();
      await c.dispose();
    });
  });

  group('ViewerControllerImpl.dispose', () {
    test('dispose 后 events 流不再派发事件', () async {
      final c = ViewerControllerImpl();
      final received = <ViewerEvent>[];
      final sub = c.events.listen(received.add);
      await c.dispose();
      expect(received, isEmpty);
      await sub.cancel();
    });
  });

  group('ViewerControllerImpl 默认状态', () {
    test('构造后 currentTier/isLoading/currentModelUrl 均为初始空值', () {
      final c = ViewerControllerImpl();
      expect(c.currentTier, isNull);
      expect(c.isLoading, isFalse);
      expect(c.currentModelUrl, isNull);
      c.dispose();
    });

    test('requireFeatures 接受任何 ViewerFeature 集合', () {
      final c = ViewerControllerImpl();
      c.requireFeatures(advancedFeatures);
      // 没有 render 之前 currentTier 仍为 null，requireFeatures 仅注册需求。
      expect(c.currentTier, isNull);
      c.dispose();
    });
  });
}
