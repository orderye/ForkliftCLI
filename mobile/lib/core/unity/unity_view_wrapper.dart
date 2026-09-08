import 'package:flutter/material.dart';
import 'package:flutter_unity_widget/flutter_unity_widget.dart';

import 'unity_bridge.dart';

/// 嵌入式 Unity 视图。包裹 [UnityWidget]，自动绑定 [UnityBridge]。
///
/// 两种模式：
/// - [enableAR=false]：纯 3D 查看器，加载 glb 模型。
/// - [enableAR=true]：AR 实景，进入后等待平面检测与放置。
///
/// AR 配置来源：[arConfig] 已传入则直接使用；否则通过 [onARConfig] 回调让上层
/// 从后端 `/api/v1/ar/config/{forkliftModelId}` 拉取后注入，拿到配置才下发 `enterAR`。
/// 早先版本会在配置为空时立刻下发，Unity 侧随后把 `modelContainer` 缩放成 1mm，
/// 用户看到的是「模型缩成了一个点」。
class UnityViewWrapper extends StatefulWidget {
  /// 车型 ID（用于加载 3D 模型与 AR 配置）。
  final int? forkliftModelId;

  /// 3D 模型 URL（.glb/.gltf）。
  final String? modelUrl;

  /// 模型当前版本号（后端返回）。用于 Unity 本地缓存 key。
  final int modelVersion;

  /// 模型内容 SHA256（后端返回）。用于缓存校验与失效。
  final String? contentHash;

  /// 模型格式（glb | gltf）。
  final String format;

  /// AR 模式开关。
  final bool enableAR;

  /// 已知的 AR 配置（真实尺寸等）。非空时立刻下发。
  final Map<String, dynamic>? arConfig;

  /// 上层拉取 AR 配置；返回 null 表示拿不到，页面应自行提示用户。
  final Future<Map<String, dynamic>?>? Function()? onARConfig;

  /// 模型加载完成后回调。
  final VoidCallback? onModelLoaded;

  /// 零件被点击回调（Unity 返回 partId/partName）。
  final void Function(Map<String, dynamic>)? onPartClicked;

  /// Unity 报错回调（未注册方法、下载失败、解析失败等）。
  final void Function(Map<String, dynamic>)? onUnityError;

  /// 平面检测成功。
  final VoidCallback? onARPlaneDetected;

  const UnityViewWrapper({
    super.key,
    this.forkliftModelId,
    this.modelUrl,
    this.modelVersion = 1,
    this.contentHash,
    this.format = 'glb',
    this.enableAR = false,
    this.arConfig,
    this.onARConfig,
    this.onModelLoaded,
    this.onPartClicked,
    this.onUnityError,
    this.onARPlaneDetected,
  });

  @override
  State<UnityViewWrapper> createState() => _UnityViewWrapperState();
}

class _UnityViewWrapperState extends State<UnityViewWrapper> {
  final UnityBridge _bridge = UnityBridge();
  bool _ready = false;
  String? _error;
  bool _enterArSent = false;

  @override
  void initState() {
    super.initState();
    _bridge.events.listen(_handleEvent);
  }

  @override
  void didUpdateWidget(covariant UnityViewWrapper oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (!widget.enableAR &&
        widget.modelUrl != oldWidget.modelUrl &&
        widget.modelUrl != null) {
      _load3D();
    }
  }

  void _load3D() {
    if (widget.modelUrl == null || widget.forkliftModelId == null) return;
    setState(() {
      _ready = false;
      _error = null;
    });
    _bridge.loadModel(
      widget.modelUrl!,
      widget.forkliftModelId!,
      version: widget.modelVersion,
      contentHash: widget.contentHash,
      format: widget.format,
    );
  }

  Future<void> _enterAR() async {
    if (_enterArSent) return;

    Map<String, dynamic> config = widget.arConfig ?? const {};
    if (config.isEmpty && widget.onARConfig != null) {
      try {
        config = await widget.onARConfig!() ?? const {};
      } catch (e) {
        if (mounted) _reportError('AR 配置获取失败: $e');
      }
    }
    if (!mounted) return;

    if (config.isEmpty) {
      _reportError('缺少 AR 配置（真实尺寸），无法按 1:1 显示');
      return;
    }

    _enterArSent = true;
    _bridge.enterAR(widget.forkliftModelId ?? 0, config);
  }

  void _handleEvent(Map<String, dynamic> event) {
    switch (event['eventName']) {
      case UnityBridge.kOnModelLoaded:
        if (mounted) setState(() => _ready = true);
        widget.onModelLoaded?.call();
        break;

      case UnityBridge.kOnPartClicked:
        widget.onPartClicked?.call((event['data'] ?? const {}) as Map<String, dynamic>);
        break;

      case UnityBridge.kOnARPlaneDetected:
        widget.onARPlaneDetected?.call();
        break;

      case UnityBridge.kOnError:
        final data = (event['data'] ?? const {}) as Map<String, dynamic>;
        _reportError('${data['method']} ${data['message']}');
        break;
    }
  }

  void _reportError(String message) {
    debugPrint('[Unity] $message');
    if (!mounted) return;
    setState(() => _error = message);
    widget.onUnityError?.call({'message': message});
  }

  void _onUnityCreated(UnityWidgetController controller) {
    _bridge.attach(controller);

    if (widget.enableAR) {
      _enterAR();
    } else if (widget.modelUrl != null && widget.forkliftModelId != null) {
      _load3D();
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
          enablePlaceholder: !_ready && _error == null,
          placeholder: _placeholder(context),
        ),
        if (_error != null) _errorOverlay(context),
      ],
    );
  }

  Widget _placeholder(BuildContext context) {
    if (widget.enableAR) return const Center(child: CircularProgressIndicator());
    return Center(
      child: Text(
        '加载 3D 模型中…',
        style: Theme.of(context).textContentStyle,
      ),
    );
  }

  Widget _errorOverlay(BuildContext context) {
    return Positioned(
      left: 8,
      right: 8,
      bottom: 8,
      child: MaterialBanner(
        content: Text(_error!),
        backgroundColor: Colors.red.shade900,
        leading: const Icon(Icons.error_outline),
        actions: [
          TextButton(
            onPressed: () => setState(() => _error = null),
            child: const Text('关闭'),
          ),
          TextButton(
            onPressed: () {
              setState(() {
                _error = null;
                _enterArSent = false;
                _ready = false;
              });
              if (widget.enableAR) {
                _enterAR();
              } else {
                _load3D();
              }
            },
            child: const Text('重试'),
          ),
        ],
      ),
    );
  }

  @override
  void dispose() {
    _bridge.detach();
    super.dispose();
  }
}
