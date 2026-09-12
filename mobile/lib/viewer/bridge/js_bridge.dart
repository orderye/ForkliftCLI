import 'dart:convert';

import 'package:webview_flutter/webview_flutter.dart';

/// Dart → JS 命令通道。
///
/// 协议（两套 HTML 统一实现）：
/// - Dart→JS：`window.flutterBridge.callMethod(method, argsObject)`
/// - JS→Dart：`window.FlutterViewer.postMessage({event, data})`
///
/// JS→Dart 的事件接收由 [ViewerControllerImpl] 在创建 WebViewController 时
/// 注册的 `FlutterViewer` JavascriptChannel 负责，本类只做命令下发。
class JsBridge {
  final WebViewController webView;

  JsBridge(this.webView);

  /// 发送命令到 JS 侧。args 统一为一个对象（callMethod 的第二个参数）。
  Future<void> call(String method, [Map<String, dynamic> args = const {}]) {
    final script =
        'window.flutterBridge.callMethod(${jsonEncode(method)}, ${jsonEncode(args)})';
    return webView.runJavaScript(script);
  }
}

/// JS 侧上报的事件。
class ViewerEvent {
  final String name;
  final Map<String, dynamic> data;

  const ViewerEvent({required this.name, required this.data});

  @override
  bool operator ==(Object other) =>
      other is ViewerEvent &&
      other.name == name &&
      other.data.length == data.length &&
      data.entries.every((e) => other.data[e.key] == e.value);

  @override
  int get hashCode => name.hashCode ^ data.toString().hashCode;

  @override
  String toString() => 'ViewerEvent($name, $data)';
}
