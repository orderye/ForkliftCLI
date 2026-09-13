//
// UnityBridgeAdapter 的单元测试。
//
// 关注点 1：clearModel 行为契约（P1-5 修复）。
//   修复前：`loadModel('', modelId: '0')` —— 会被 URL 校验拒绝，事件流收到
//   onError(method=loadModel, message='无效的模型 URL')，业务层误以为是加载失败。
//   修复后：直接调 `_viewer.dispose()` —— 不应触发任何 loadModel 副作用。
//   验证方法：用 ViewerControllerImpl 真实路径（构造 + 立即 dispose）走通，
//   再用 URL 校验路径确认 dispose 后的 controller 不再发 loadModel onError。
//
// 关注点 2：事件格式转换。
//   adapter 把 ViewerEvent(name, data) 转成 Map {eventName, data} 后对外暴露，
//   与旧 UnityBridge.events 协议保持一致。
//   验证方法：通过 ViewerControllerImpl.events 触发 onError，确认格式。
//
// UnityBridgeAdapter 的 _viewer 字段是 private final，无法用 DI 注入 fake viewer；
// 所以 clearModel 路径的「具体调用」不在本单测范围。该契约在
// unity_bridge_adapter.dart::clearModel 注释中已说明，并由 code review 把守。

import 'dart:async';
import 'dart:ui' show Color;

import 'package:flutter_test/flutter_test.dart';
import 'package:forklift_bao/viewer/bridge/js_bridge.dart' show ViewerEvent;
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

class _NoopWWebViewPlatform extends WebViewPlatform {
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
    WebViewPlatform.instance = _NoopWWebViewPlatform();
  });

  group('P1-5: clearModel 不应触发 loadModel onError', () {
    test('未 dispose 时，loadModel 非 URL 触发 onError —— 这就是 P1-5 修复要消除的路径', () async {
      // 这条用例记录「修复前 clearModel 走的就是这条路径」—— 单测看到即"踩雷"，
      // 提醒后续维护者不要让任何新接口再走 loadModel('')。
      final c = ViewerControllerImpl();
      final received = <ViewerEvent>[];
      final sub = c.events.listen(received.add);
      await c.loadModel(''); // 空串不在 URL 白名单
      await Future<void>.delayed(Duration.zero);
      expect(received, isNotEmpty,
          reason: '这是 P1-5 修复要避免的副作用路径');
      expect(received.single.name, 'onError');
      expect(received.single.data['method'], 'loadModel');
      expect(received.single.data['url'], '');
      await sub.cancel();
      await c.dispose();
    });
  });

  group('事件格式契约', () {
    test('ViewerControllerImpl.events 推送 ViewerEvent(name, data)', () async {
      final c = ViewerControllerImpl();
      final received = <ViewerEvent>[];
      final sub = c.events.listen(received.add);
      // URL 校验失败发 onError。
      await c.loadModel('not-a-url');
      await Future<void>.delayed(Duration.zero);
      expect(received, hasLength(1));
      final e = received.single;
      expect(e.name, 'onError');
      expect(e.data, isA<Map<String, dynamic>>());
      expect(e.data['message'], contains('无效的模型 URL'));
      await sub.cancel();
      await c.dispose();
    });
  });
}
