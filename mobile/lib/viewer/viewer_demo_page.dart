import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';

import 'model_asset_manager.dart';
import 'viewer_controller.dart';
import 'viewer_controller_impl.dart';
import 'config/viewer_config.dart';

/// 3D 查看器演示页 —— 展示双渲染器架构。
///
/// 按需从 lite（model-viewer）自动升级到 full（Three.js）。
class ViewerDemoPage extends StatefulWidget {
  const ViewerDemoPage({super.key, this.modelUrl, this.forkliftModelId});

  /// 直接指定模型 URL（优先）。
  final String? modelUrl;

  /// 叉车模型 ID（通过 ModelAssetManager 获取 URL）。
  final int? forkliftModelId;

  @override
  State<ViewerDemoPage> createState() => _ViewerDemoPageState();
}

class _ViewerDemoPageState extends State<ViewerDemoPage> {
  final ViewerController _viewer = ViewerControllerImpl();

  bool _loading = true;
  String? _status;
  String _currentMode = 'lite';
  String? _resolvedUrl;

  @override
  void initState() {
    super.initState();
    _initViewer();
  }

  Future<void> _initViewer() async {
    try {
      _resolvedUrl = await _resolveModelUrl();
      await _viewer.loadModel(_resolvedUrl!, modelId: 'demo');
      _setStatus('模型加载完成 (Lite)');
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

  Future<void> _switchToFull() async {
    if (_currentMode == 'full') return;
    setState(() { _currentMode = 'full'; _loading = true; });
    _viewer.requireFeatures(advancedFeatures);
    await _viewer.loadModel(_resolvedUrl!, modelId: 'demo');
    _setStatus('已切换到全功能模式');
    setState(() => _loading = false);
  }

  void _setStatus(String msg) {
    if (!mounted) return;
    setState(() => _status = msg);
  }

  @override
  void dispose() {
    _viewer.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('3D 查看器 ($_currentMode)'),
        actions: [
          IconButton(icon: const Icon(Icons.view_in_ar_outlined), onPressed: _viewer.enterAR, tooltip: 'AR'),
          IconButton(icon: const Icon(Icons.refresh), onPressed: _viewer.resetView, tooltip: 'Reset'),
        ],
      ),
      body: Stack(
        children: [
          WebViewWidget(controller: _viewer.webView),
          if (_loading)
            const Positioned(top: 0, left: 0, right: 0, child: LinearProgressIndicator())
          else if (_status != null)
            Positioned(
              top: 0, left: 0, right: 0,
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                color: Colors.black54,
                child: Text(_status!, style: const TextStyle(color: Colors.white70, fontSize: 12)),
              ),
            ),
          Positioned(
            bottom: 0, left: 0, right: 0,
            child: Container(
              color: Colors.black87,
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  if (_currentMode == 'lite')
                    Padding(
                      padding: const EdgeInsets.only(bottom: 8),
                      child: OutlinedButton.icon(
                        icon: const Icon(Icons.bolt),
                        label: const Text('切换到全功能模式'),
                        onPressed: _switchToFull,
                      ),
                    ),
                  _cameraBar(),
                  if (_currentMode == 'full') ...[
                    const Divider(height: 1, color: Colors.white24),
                    _advancedBar(),
                  ],
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _cameraBar() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceAround,
      children: [
        _btn(Icons.rotate_left, '左转', () => _viewer.setCamera(azimuth: 90)),
        _btn(Icons.rotate_right, '右转', () => _viewer.setCamera(azimuth: -90)),
        _btn(Icons.zoom_in, '拉近', () => _viewer.setCamera(targetDistance: 2)),
        _btn(Icons.zoom_out, '拉远', () => _viewer.setCamera(targetDistance: 5)),
        _btn(Icons.center_focus_strong, '居中', () => _viewer.resetView()),
      ],
    );
  }

  Widget _advancedBar() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceAround,
      children: [
        _btn(Icons.highlight, '高亮', () async {
          await _viewer.highlightPart('Mast_Inner', color: Colors.red);
          _setStatus('高亮 Mast_Inner');
        }),
        _btn(Icons.layers, '爆炸', () async {
          await _viewer.setExploded(0.6);
          _setStatus('爆炸图 60%');
        }),
        _btn(Icons.straighten, '测量', () async {
          await _viewer.measure(from: 'Fork_Left', to: 'Fork_Right', label: '间距');
          _setStatus('测量完成');
        }),
        _btn(Icons.play_circle, '动画', () async {
          await _viewer.playAnimation('mast_up');
          _setStatus('播放动画');
        }),
        _btn(Icons.delete, '清除', () async {
          await _viewer.clearHighlight();
          await _viewer.clearMeasure();
          await _viewer.setExploded(0);
          _setStatus('已清除');
        }),
      ],
    );
  }

  Widget _btn(IconData icon, String label, VoidCallback onTap) {
    return SizedBox(
      width: 60,
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          IconButton(icon: Icon(icon, size: 22), color: Colors.white, onPressed: onTap),
          Text(label, style: const TextStyle(color: Colors.white70, fontSize: 10)),
        ],
      ),
    );
  }
}
