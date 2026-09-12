import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';

import '../../viewer/config/viewer_config.dart';
import '../../viewer/model_asset_manager.dart';
import '../../viewer/viewer_controller.dart';
import '../../viewer/viewer_controller_impl.dart';

/// 3D 查看器 V2 —— 使用 ViewerController（Web 渲染器）替代 UnityViewWrapper。
///
/// 与 V1（Unity 版）接口一致，可无缝替换。
class ThreeDViewerPageV2 extends StatefulWidget {
  final int? forkliftModelId;
  final String? modelUrl;
  final String? title;

  const ThreeDViewerPageV2({super.key, this.forkliftModelId, this.modelUrl, this.title});

  @override
  State<ThreeDViewerPageV2> createState() => _ThreeDViewerPageV2State();
}

class _ThreeDViewerPageV2State extends State<ThreeDViewerPageV2> {
  final ViewerController _viewer = ViewerControllerImpl();


  ModelAsset? _asset;
  bool _isLoading = true;
  String? _error;

  bool _autoRotate = true;
  bool _showPartsList = false;
  String? _selectedPart;

  /// 模型实际可识别的零件数（由 JS 侧 onModelLoaded 回传）。
  /// 0 表示模型没有零件层级，零件列表与高亮功能不可用。
  int _loadedPartCount = -1;
  int _loadedAnimationCount = 0;

  @override
  void initState() {
    super.initState();
    _loadModel();
    _listenEvents();
  }

  Future <void> _loadModel() async {
    try {
      if (widget.forkliftModelId != null) {
        _asset = await ModelAssetManager.instance.getAsset(
            forkliftModelId: widget.forkliftModelId!);
      }

      final url = widget.modelUrl ?? _asset?.fileUrl ?? '';
      if (url.isEmpty) {
        if (mounted) {
          setState(() {
            _error = 'No model URL available';
            _isLoading = false;
          });
        }
        return;
      }

      await _viewer.loadModel(url, modelId: widget.forkliftModelId?.toString());
      if (mounted) setState(() => _isLoading = false);
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = e.toString();
          _isLoading = false;
        });
      }
    }
  }

  void _listenEvents() {
    _viewer.events.listen((event) {
      switch (event.name) {
        case 'onModelLoaded':
          final parts = event.data['parts'];
          if (parts is int) _loadedPartCount = parts;
          final anims = event.data['animations'];
          if (anims is int) _loadedAnimationCount = anims;
          break;

        case 'onPartClicked':
          final partId = event.data['partId']?.toString();
          if (partId != null) {
            setState(() => _selectedPart = partId);
            _highlightPart(partId);
          }
          break;

        case 'onHighlightCleared':
          if (mounted) setState(() => _selectedPart = null);
          break;

        case 'onAutoRotate':
          // 用户手动拖拽相机时 JS 侧会自动停止旋转，同步回来保持图标一致。
          final on = event.data['enabled'];
          if (on is bool && on != _autoRotate && mounted) {
            setState(() => _autoRotate = on);
          }
          break;

        case 'onError':
          debugPrint('[ThreeDViewerV2] Error: ${event.data['message']}');
          break;
      }
    });
  }

  Future <void> _highlightPart(String partId) async {
    _viewer.requireFeatures({ViewerFeature.highlight});
    await _viewer.highlightPart(partId, color: Colors.red);
  }

  Future <void> _clearHighlight() async {
    _viewer.requireFeatures({ViewerFeature.highlight});
    await _viewer.clearHighlight();
    setState(() => _selectedPart = null);
  }

  Future <void> _playAnimation(String name) async {
    _viewer.requireFeatures({ViewerFeature.animation});
    await _viewer.playAnimation(name);
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Row(
          children: [
            const Icon(Icons.animation, color: Colors.white, size: 20),
            const SizedBox(width: 8),
            Text('Playing: $name'),
          ],
        ),
        duration: const Duration(milliseconds: 1500),
        backgroundColor: const Color(0xFF1565C0),
      ),
    );
  }

  @override
  void dispose() {
    _viewer.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final title = widget.title ?? _asset?.name ?? '3D Forklift';

    return Scaffold(
      appBar: AppBar(
        title: Text(title),
        actions: [
          IconButton(
            icon: Icon(_showPartsList ? Icons.list : Icons.view_list),
            onPressed: () => setState(() => _showPartsList = !_showPartsList),
            tooltip: 'Parts list',
          ),
          IconButton(
            icon: Icon(_autoRotate ? Icons.sync : Icons.sync_disabled),
            onPressed: () async {
              final next = !_autoRotate;
              setState(() => _autoRotate = next);
              await _viewer.setAutoRotate(next);
            },
            tooltip: 'Auto rotate',
          ),
          IconButton(
            icon: const Icon(Icons.view_in_ar_outlined),
            onPressed: () => _viewer.enterAR(),
            tooltip: 'Enter AR',
          ),
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => _viewer.resetView(),
            tooltip: 'Reset view',
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? _buildErrorView()
              : Stack(
                  children: [
                    WebViewWidget(controller: _viewer.webView),
                    if (_showPartsList) _buildPartsPanel(),
                  ],
                ),
      bottomSheet: _showPartsList ? _buildPartsPanelBottom() : null,
    );
  }

  Widget _buildErrorView() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.view_in_ar, size: 64, color: Colors.grey),
          const SizedBox(height: 16),
          const Text('Model load failed', style: TextStyle(fontSize: 16)),
          const SizedBox(height: 8),
          Text(_error ?? '', style: const TextStyle(color: Colors.grey, fontSize: 12)),
          const SizedBox(height: 16),
          ElevatedButton(
            onPressed: _loadModel,
            child: const Text('Retry'),
          ),
        ],
      ),
    );
  }

  Widget _buildPartsPanel() {
    final asset = _asset;
    if (asset == null || asset.parts.isEmpty) {
      return Container(
        height: 200,
        padding: const EdgeInsets.all(12),
        child: Center(
          child: Text(
            _loadedPartCount == 0
                ? '该模型没有零件层级，无法高亮单件零件'
                : 'No parts data',
            style: const TextStyle(color: Colors.grey),
          ),
        ),
      );
    }

    return Container(
      height: 280,
      padding: const EdgeInsets.all(12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text('Parts', style: TextStyle(fontWeight: FontWeight.bold)),
              IconButton(
                icon: const Icon(Icons.close, size: 20),
                onPressed: () => setState(() => _showPartsList = !_showPartsList),
              ),
            ],
          ),
          Expanded(
            child: ListView.builder(
              itemCount: asset.parts.length,
              itemBuilder: (context, index) {
                final part = asset.parts[index];
                final isSelected = _selectedPart == part.meshName;
                return ListTile(
                  dense: true,
                  selected: isSelected,
                  leading: Icon(
                    Icons.circle,
                    size: 12,
                    color: part.color != null
                        ? Color(int.parse(part.color!.replaceFirst('#', '0xFF')))
                        : Colors.grey,
                  ),
                  title: Text(part.name, style: const TextStyle(fontSize: 13)),
                  subtitle: part.partNumber != null
                      ? Text(part.partNumber!, style: const TextStyle(fontSize: 11))
                      : null,
                  onTap: () => _highlightPart(part.meshName),
                );
              },
            ),
          ),
          if (_selectedPart != null)
            FilledButton.tonalIcon(
              onPressed: _clearHighlight,
              icon: const Icon(Icons.clear),
              label: const Text('清除高亮'),
            ),
          if (asset.animations.isEmpty || _loadedAnimationCount == 0)
            const Padding(
              padding: EdgeInsets.only(top: 6),
              child: Text(
                '该模型无动画剪辑，门架升降/倾斜/货叉开合暂不可用',
                style:TextStyle(color: Colors.grey, fontSize: 11),
              ),
            ),
          if (asset.animations.isNotEmpty) ...[
            const SizedBox(height: 4),
            for (final anim in asset.animations)
              ListTile(
                dense: true,
                leading: const Icon(Icons.animation, size: 16),
                title: Text(anim.displayName.isEmpty ? anim.name : anim.displayName,
                    style: const TextStyle(fontSize: 13)),
                onTap: () => _playAnimation(anim.name),
              ),
          ],
        ],
      ),
    );
  }

  Widget _buildPartsPanelBottom() {
    return Container(
      height: 250,
      padding: const EdgeInsets.all(12),
      child: _buildPartsPanel(),
    );
  }
}
