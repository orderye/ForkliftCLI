import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';

import '../../core/api/api_client.dart';
import '../../viewer/config/viewer_config.dart';
import '../../viewer/model_asset_manager.dart';
import '../../viewer/viewer_controller.dart';
import '../../viewer/viewer_controller_impl.dart';

/// AR 实景查看页 V2 —— 使用 ViewerController（Web 渲染器）替代 UnityViewWrapper。
///
/// 保留原有 Flutter UI 覆盖层（尺寸信息、门架高度指示器、控制面板），
/// 仅替换底层 3D/AR 渲染层。
class ArViewPageV2 extends StatefulWidget {
  final int? forkliftModelId;

  const ArViewPageV2({super.key, this.forkliftModelId});

  @override
  State<ArViewPageV2> createState() => _ArViewPageV2State();
}

class _ArViewPageV2State extends State<ArViewPageV2> {
  final ViewerController _viewer = ViewerControllerImpl();


  Map<String, dynamic>? _arConfig;
  ModelAsset? _asset;
  bool _isLoading = true;
  bool _showDimensions = true;
  bool _showMastHeight = true;
  bool _arActive = false;

  double _mastHeight = 1.8;
  double _mastMinHeight = 1.8;
  double _mastMaxHeight = 4.5;

  /// 门架可动行程。AR 配置缺失时为 0，此时不应渲染门架指示条
  /// （用写死的默认值显示门架行程，同样是假数据）。
  double get _mastRange => _mastMaxHeight - _mastMinHeight;
  bool get _hasArConfig => _arConfig != null && _mastRange > 0;

  @override
  void initState() {
    super.initState();
    _loadConfig();
    _listenEvents();
  }

  Future <void> _loadConfig() async {
    if (widget.forkliftModelId == null) {
      if (mounted) setState(() => _isLoading = false);
      return;
    }

    try {
      final [arResp, asset] = await Future.wait([
        ApiClient().dio.get('/api/v1/ar/config/${widget.forkliftModelId}'),
        ModelAssetManager.instance.getAsset(forkliftModelId: widget.forkliftModelId!),
      ]);

      if (mounted) {
        setState(() {
          _arConfig = arResp.data;
          _asset = asset;
          // AR 的卖点是「真实尺寸 1:1」。配置缺失时必须明确告知，
          // 不能悄悄用写死的默认值继续显示 —— 那等于把假尺寸当真尺寸给用户看。
          if (_arConfig != null) {
            final h = _arConfig!['real_height_mm'];
            final mast = _arConfig!['real_mast_height_mm'];
            if (h != null && mast != null) {
              _mastMinHeight = h / 1000;
              _mastHeight = _mastMinHeight;
              _mastMaxHeight = mast / 1000;
            }
          }
        });
      }

      // Load model into viewer
      if (asset.fileUrl.isNotEmpty) {
        await _viewer.loadModel(asset.fileUrl, modelId: widget.forkliftModelId!.toString());
      }
    } catch (e) {
      debugPrint('[ArViewV2] Load failed: $e');
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  void _listenEvents() {
    _viewer.events.listen((event) {
      switch (event.name) {
        case 'onARActivated':
          setState(() => _arActive = true);
        case 'onARExitRequested':
          setState(() => _arActive = false);
      }
    });
  }

  Future <void> _enterAR() async {
    try {
      await _viewer.enterAR();
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('AR failed: $e')),
      );
    }
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
        title: const Text('AR View'),
        backgroundColor: Colors.black87,
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            icon: Icon(_showDimensions ? Icons.straighten : Icons.straighten_outlined),
            onPressed: () => setState(() => _showDimensions = !_showDimensions),
            tooltip: 'Dimensions',
          ),
          if (!_arActive)
            IconButton(
              icon: const Icon(Icons.view_in_ar_outlined),
              onPressed: _enterAR,
              tooltip: 'Enter AR',
            ),
        ],
      ),
      backgroundColor: Colors.black,
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(color: Colors.white))
          : Stack(
              children: [
                WebViewWidget(controller: _viewer.webView),
                if (_showDimensions && _arConfig != null) _buildDimensionOverlay(),
                if (_showMastHeight && _hasArConfig) _buildMastHeightIndicator(),
                if (!_hasArConfig)
                  Positioned(
                    top: 80,
                    left: 12,
                    right: 12,
                    child: MaterialBanner(
                      backgroundColor: Colors.orange.shade900,
                      leading: const Icon(Icons.info_outline, color: Colors.white70),
                      content: const Text(
                        '该车型未录入 AR 真实尺寸配置，尺寸与门架行程暂不可显示。'
                        '请先在后台为该车补 ar_model_config。',
                        style: TextStyle(color: Colors.white, fontSize: 12),
                      ),
                    ),
                  ),
                Positioned(
                  bottom: 0,
                  left: 0,
                  right: 0,
                  child: _buildControlPanel(),
                ),
              ],
            ),
    );
  }

  /// Dimension overlay
  ///
  /// 后端未录入的字段显示为 "—"，不显示 0.0 —— 这是「真实尺寸 1:1」的展示层，
  /// 把 NULL 当 0 显示等于给用户一个确定但错误的数（例如 8FG30 的轴距/转弯半径
  /// 数据库里就是空的）。
  Widget _buildDimensionOverlay() {
    final length = _mm(_arConfig!['real_length_mm']);
    final width = _mm(_arConfig!['real_width_mm']);
    final height = _mm(_arConfig!['real_height_mm']);
    final wheelbase = _mm(_arConfig!['real_wheelbase_mm']);
    final turningRadius = _mm(_arConfig!['real_turning_radius_mm']);
    final scale = _arConfig!['scale_factor'];
    final isScale1to1 = scale == null || scale == 1.0;

    return Positioned(
      top: 80,
      right: 12,
      child: Container(
        width: 180,
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: Colors.black.withOpacity(0.7),
          borderRadius: BorderRadius.circular(12),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Vehicle Dimensions', style:TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 13)),
            const Divider(color: Colors.white24, height: 12),
            _dimRow('Length', length),
            _dimRow('Width', width),
            _dimRow('Height', height),
            _dimRow('Wheelbase', wheelbase),
            _dimRow('Turning', turningRadius),
            const Divider(color: Colors.white24, height: 12),
            const Text('Footprint', style: TextStyle(color: Colors.white70, fontSize: 11)),
            Text(
              length != null && width != null
                  ? '${(length * width / 1000000).toStringAsFixed(2)} m²'
                  : '—',
              style: const TextStyle(color: Colors.greenAccent, fontSize: 13, fontWeight: FontWeight.bold),
            ),
            if (!isScale1to1)
              Padding(
                padding: const EdgeInsets.top(6),
                child: Text(
                  '非 1:1（×${scale.toStringAsFixed(2)}）',
                  style: const TextStyle(color: Colors.orangeAccent, fontSize: 11),
                ),
              ),
          ],
        ),
      ),
    );
  }

  /// 毫米 → 展示用字符串；NULL 返回 "—"，0 与 NULL 区别对待。
  String _mm(dynamic mm) {
    if (mm == null) return '—';
    final v = (mm as num).toDouble();
    return '${(v / 1000).toStringAsFixed(1)} m';
  }

  Widget _dimRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(color: Colors.white70, fontSize: 12)),
          Text(value, style: const TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.w500)),
        ],
      ),
    );
  }

  /// Mast height indicator
  Widget _buildMastHeightIndicator() {
    return Positioned(
      left: 12,
      top: 80,
      child: Container(
        width: 60,
        height: 250,
        padding: const EdgeInsets.all(8),
        decoration: BoxDecoration(
          color: Colors.black.withOpacity(0.7),
          borderRadius: BorderRadius.circular(12),
        ),
        child: Column(
          children: [
            const Text('Mast', style: TextStyle(color: Colors.white, fontSize: 10)),
            const SizedBox(height: 4),
            Expanded(
              child: Stack(
                alignment: Alignment.bottomCenter,
                children: [
                  Container(
                    width: 8,
                    decoration: BoxDecoration(
                      color: Colors.white24,
                      borderRadius: BorderRadius.circular(4),
                    ),
                  ),
                  FractionallySizedBox(
                    // 门架上下限相同时避免除以零（会得到 Infinity，布局直接崩）
                    heightFactor: _mastRange == 0
                        ? 0
                        : ((_mastHeight - _mastMinHeight) / _mastRange).clamp(0.0, 1.0),
                    child: Container(
                      width: 8,
                      decoration: BoxDecoration(
                        color: Colors.greenAccent,
                        borderRadius: BorderRadius.circular(4),
                      ),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 4),
            Text(
              '${_mastHeight.toStringAsFixed(1)} m',
              style: const TextStyle(color: Colors.greenAccent, fontSize: 14, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 4),
            GestureDetector(
              onTap: () => setState(() => _mastHeight = (_mastHeight + 0.3).clamp(_mastMinHeight, _mastMaxHeight)),
              child: Container(
                padding: const EdgeInsets.all(4),
                decoration: BoxDecoration(color: Colors.white24, borderRadius: BorderRadius.circular(8)),
                child: const Icon(Icons.keyboard_arrow_up, color: Colors.white, size: 20),
              ),
            ),
            const SizedBox(height: 4),
            GestureDetector(
              onTap: () => setState(() => _mastHeight = (_mastHeight - 0.3).clamp(_mastMinHeight, _mastMaxHeight)),
              child: Container(
                padding: const EdgeInsets.all(4),
                decoration: BoxDecoration(color: Colors.white24, borderRadius: BorderRadius.circular(8)),
                child: const Icon(Icons.keyboard_arrow_down, color: Colors.white, size: 20),
              ),
            ),
          ],
        ),
      ),
    );
  }

  /// Control panel
  Widget _buildControlPanel() {
    return Container(
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 32),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: [Colors.transparent, Colors.black.withOpacity(0.8)],
        ),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Row(
            children: [
              const Text('Mast Height', style: TextStyle(color: Colors.white70, fontSize: 12)),
              Expanded(
                child: Slider(
                  value: _mastHeight,
                  min: _mastMinHeight,
                  max: _mastMaxHeight,
                  divisions: ((_mastMaxHeight - _mastMinHeight) * 10).toInt(),
                  activeColor: Colors.greenAccent,
                  onChanged: (v) => setState(() => _mastHeight = v),
                ),
              ),
              Text('${_mastHeight.toStringAsFixed(1)}m', style: const TextStyle(color: Colors.greenAccent, fontSize: 12)),
            ],
          ),
          const SizedBox(height: 8),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: [
              _arBtn(Icons.straighten, 'Dims', () => setState(() => _showDimensions = !_showDimensions)),
              _arBtn(Icons.height, 'Mast', () => setState(() => _showMastHeight = !_showMastHeight)),
              _arBtn(Icons.center_focus_strong, 'Center', () => _viewer.resetView()),
              _arBtn(Icons.camera_alt, 'Snap', () {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Screenshot saved'), duration: Duration(seconds: 1)),
                );
              }),
            ],
          ),
        ],
      ),
    );
  }

  Widget _arBtn(IconData icon, String label, VoidCallback onPressed) {
    return GestureDetector(
      onTap: onPressed,
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 48,
            height: 48,
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.15),
              borderRadius: BorderRadius.circular(24),
            ),
            child: Icon(icon, color: Colors.white, size: 24),
          ),
          const SizedBox(height: 4),
          Text(label, style: const TextStyle(color: Colors.white, fontSize: 10)),
        ],
      ),
    );
  }
}
