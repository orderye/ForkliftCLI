import 'package:flutter/material.dart';
import 'package:flutter_unity_widget/flutter_unity_widget.dart';

import 'unity_bridge.dart';

/// 嵌入式 Unity 视图。包裹 [UnityWidget]，自动绑定 [UnityBridge]。
///
/// 两种模式：
/// - [enableAR=false]：纯 3D 查看器，加载 glb 模型。
/// - [enableAR=true]：AR 实景，进入后等待平面检测与放置。
class UnityViewWrapper extends StatefulWidget {
  /// 车型 ID（用于加载 3D 模型与 AR 配置）。
  final int? forkliftModelId;

  /// 3D 模型 URL（.glb）。
  final String? modelUrl;

  /// AR 模式开关。
  final bool enableAR;

  /// 模型加载完成后回调。
  final VoidCallback? onModelLoaded;

  /// 零件被点击回调（Unity 返回 partId/partName）。
  final void Function(Map<String, dynamic>)? onPartClicked;

  const UnityViewWrapper({
    super.key,
    this.forkliftModelId,
    this.modelUrl,
    this.enableAR = false,
    this.onModelLoaded,
    this.onPartClicked,
  });

  @override
  State<UnityViewWrapper> createState() => _UnityViewWrapperState();
}

class _UnityViewWrapperState extends State<UnityViewWrapper> {
  final UnityBridge _bridge = UnityBridge();
  bool _ready = false;

  @override
  void initState() {
    super.initState();
    _bridge.events.listen(_handleEvent);
  }

  void _handleEvent(Map<String, dynamic> event) {
    switch (event['eventName']) {
      case UnityBridge.kOnModelLoaded:
        if (mounted) setState(() => _ready = true);
        widget.onModelLoaded?.call();
        break;
      case UnityBridge.kOnPartClicked:
        widget.onPartClicked?.call(event['data'] ?? {});
        break;
    }
  }

  void _onUnityCreated(UnityWidgetController controller) {
    _bridge.attach(controller);

    if (widget.enableAR) {
      // 进入 AR 模式，arConfig 由上层传入后调用 enterAR；
      // 这里仅触发 Unity 侧 AR 场景初始化。
      _bridge.enterAR(widget.forkliftModelId ?? 0, {});
    } else if (widget.modelUrl != null && widget.forkliftModelId != null) {
      _bridge.loadModel(widget.modelUrl!, widget.forkliftModelId!);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        UnityWidget(
          onUnityCreated: _onUnityCreated,
          onUnityMessage: (controller, message) =>
              _bridge.onUnityMessage(message),
          useAndroidViewSurface: true,
          enablePlaceholder: !_ready,
          placeholder: widget.enableAR
              ? const Center(child: Text('初始化 AR...'))
              : const Center(child: Text('加载 3D 模型...')),
        ),
      ],
    );
  }

  @override
  void dispose() {
    _bridge.detach();
    super.dispose();
  }
}