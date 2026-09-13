import 'dart:async';

import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';

import 'bridge/js_bridge.dart' show ViewerEvent;
import 'model_asset_manager.dart';
import 'viewer_controller.dart';
import 'viewer_controller_impl.dart';

/// AR 查看页 —— 展示轻量渲染器的 AR 放置能力。
///
/// 使用 <model-viewer> 的原生 AR 按钮（Scene Viewer / AR Quick Look / WebXR）。
class ARViewPage extends StatefulWidget {
  const ARViewPage({super.key, this.modelUrl, this.forkliftModelId});

  final String? modelUrl;
  final int? forkliftModelId;

  @override
  State<ARViewPage> createState() => _ARViewPageState();
}

class _ARViewPageState extends State<ARViewPage> {
  final ViewerController _viewer = ViewerControllerImpl();
  StreamSubscription<ViewerEvent>? _eventsSub;

  bool _loading = true;
  String? _status;
  bool _arActive = false;

  @override
  void initState() {
    super.initState();
    _initViewer();
    _eventsSub = _viewer.events.listen((event) {
      switch (event.name) {
        case 'onARActivated':
          if (mounted) setState(() { _arActive = true; _setStatus('AR 已激活'); });
          break;
        case 'onARExitRequested':
          if (mounted) setState(() { _arActive = false; _setStatus('AR 已退出'); });
          break;
        case 'onModelLoaded':
          if (mounted) setState(() => _setStatus('AR 就绪，点击"进入 AR"'));
          break;
        case 'onError':
          if (mounted) setState(() => _setStatus('错误: ${event.data['message']}'));
          break;
      }
    });
  }

  Future<void> _initViewer() async {
    try {
      final url = await _resolveModelUrl();
      await _viewer.loadModel(url, modelId: 'ar');
    } catch (e) {
      _setStatus('加载失败: $e');
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<String> _resolveModelUrl() async {
    if (widget.modelUrl != null && widget.modelUrl!.isNotEmpty) return widget.modelUrl!;
    if (widget.forkliftModelId != null) {
      return (await ModelAssetManager.instance.getAsset(forkliftModelId: widget.forkliftModelId!)).fileUrl;
    }
    return '';
  }

  Future<void> _enterAR() async {
    try {
      await _viewer.enterAR();
    } catch (e) {
      _setStatus('AR 激活失败: $e');
    }
  }

  Future<void> _exitAR() async => _viewer.exitAR();

  void _setStatus(String msg) {
    if (!mounted) return;
    setState(() => _status = msg);
  }

  @override
  void dispose() {
    _eventsSub?.cancel();
    _viewer.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('AR 查看'),
        leading: IconButton(icon: const Icon(Icons.arrow_back), onPressed: () => Navigator.pop(context)),
        actions: [
          if (_arActive)
            IconButton(icon: const Icon(Icons.exit_to_app), onPressed: _exitAR, tooltip: '退出 AR'),
        ],
      ),
      body: Stack(
        children: [
          WebViewWidget(controller: _viewer.webView),
          if (_loading)
            const Center(child: CircularProgressIndicator())
          else if (_status != null)
            Positioned(
              top: 8, left: 8, right: 8,
              child: Container(
                padding: const EdgeInsets.all(8),
                color: Colors.black54,
                child: Text(_status!, style: const TextStyle(color: Colors.white)),
              ),
            ),
          if (!_loading && !_arActive)
            Positioned(
              bottom: 32, left: 32, right: 32,
              child: FilledButton.icon(
                icon: const Icon(Icons.view_in_ar),
                label: const Text('进入 AR'),
                onPressed: _enterAR,
                style: FilledButton.styleFrom(padding: const EdgeInsets.symmetric(vertical: 16)),
              ),
            ),
        ],
      ),
    );
  }
}
