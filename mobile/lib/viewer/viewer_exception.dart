/// 查看器相关异常，用于区分不同失败原因。

class ViewerException implements Exception {
  final String message;
  final String? method;
  final Object? cause;

  const ViewerException(this.message, {this.method, this.cause});

  @override
  String toString() {
    final buf = StringBuffer('ViewerException: $message');
    if (method != null) buf.write(' [method=$method]');
    if (cause != null) buf.write(' cause: $cause');
    return buf.toString();
  }
}

/// 模型加载失败。
class ModelLoadException extends ViewerException {
  const ModelLoadException(String url, {Object? cause})
      : super('模型加载失败: $url', method: 'loadModel', cause: cause);
}

/// 渲染器初始化失败（WebView 创建、JS 加载失败）。
class RendererInitException extends ViewerException {
  const RendererInitException(Object? cause)
      : super('渲染器初始化失败', cause: cause);
}

/// 桥接调用失败（JS 侧返回错误）。
class BridgeCallException extends ViewerException {
  const BridgeCallException(String method, String message, {Object? cause})
      : super(message, method: method, cause: cause);
}

/// 不支持的操作（lite 渲染器调用高级功能且未自动升级）。
class UnsupportedOperationException extends ViewerException {
  const UnsupportedOperationException(String operation)
      : super('当前渲染器不支持: $operation');
}
