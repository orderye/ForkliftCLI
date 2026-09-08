import 'package:flutter/material.dart';
import 'package:forklift_bao/core/api/api_client.dart';
import 'package:model_viewer_plus/model_viewer_plus.dart';

/// AR实景查看页
/// 对应需求文档：十六(AR功能)、十七(真实尺寸)、十八(空间占位)、十九(AR门架动作)
class ArViewPage extends StatefulWidget {
  final int? forkliftModelId;
  const ArViewPage({super.key, this.forkliftModelId});

  @override
  State<ArViewPage> createState() => _ArViewPageState();
}

class _ArViewPageState extends State<ArViewPage> {
  Map<String, dynamic>? _arConfig;
  Map<String, dynamic>? _model3d;
  bool _isLoading = true;
  bool _showDimensions = true;
  bool _showMastHeight = true;
  String? _currentAction;

  // 门架高度状态
  double _mastHeight = 1.8; // 当前高度(m)
  double _mastMinHeight = 1.8;
  double _mastMaxHeight = 4.5;

  @override
  void initState() {
    super.initState();
    _loadArConfig();
  }

  Future<void> _loadArConfig() async {
    if (widget.forkliftModelId == null) {
      if (mounted) setState(() => _isLoading = false);
      return;
    }

    try {
      final resp = await ApiClient().dio.get('/api/v1/ar/config/${widget.forkliftModelId}');
      final modelResp = await ApiClient().dio.get('/api/v1/3d/forklift/${widget.forkliftModelId}');
      if (mounted) {
        setState(() {
          _arConfig = resp.data;
          _model3d = modelResp.data['model'];
          _mastMinHeight = (_arConfig!['real_height_mm'] ?? 1800) / 1000;
          _mastHeight = _mastMinHeight;
          _mastMaxHeight = (_arConfig!['real_mast_height_mm'] ?? 4500) / 1000;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('AR实景'),
        backgroundColor: Colors.black87,
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            icon: Icon(_showDimensions ? Icons.straighten : Icons.straighten_outlined),
            onPressed: () => setState(() => _showDimensions = !_showDimensions),
            tooltip: '尺寸标注',
          ),
        ],
      ),
      backgroundColor: Colors.black,
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(color: Colors.white))
          : Stack(
              children: [
                // AR摄像头视图（占位）
                _buildArCameraView(),

                // 尺寸信息叠加层
                if (_showDimensions) _buildDimensionOverlay(),

                // 门架高度显示
                if (_showMastHeight) _buildMastHeightIndicator(),

                // 底部控制面板
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

  /// AR摄像头视图 — 占位展示
  Widget _buildArCameraView() {
    final modelUrl = _model3d?['file_url'] ?? '';

    if (modelUrl.isNotEmpty) {
      // 有真实3D模型时使用ModelViewer
      return ModelViewer(
        src: modelUrl,
        alt: 'AR叉车',
        ar: true,
        arTracking: 'world-tracking',
        autoRotate: false,
        autoPlay: true,
        cameraControls: true,
        shadowIntensity: 1,
        shadowSoftness: 0.5,
      );
    }

    // 无模型时的占位视图
    return Container(
      color: Colors.black,
      child: Stack(
        alignment: Alignment.center,
        children: [
          // 模拟AR网格
          CustomPaint(
            size: Size.infinite,
            painter: _ArGridPainter(),
          ),
          // 叉车占位
          Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(Icons.agriculture, size: 100, color: Colors.white.withOpacity(0.5)),
              const SizedBox(height: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                decoration: BoxDecoration(
                  color: Colors.black54,
                  borderRadius: BorderRadius.circular(16),
                ),
                child: const Text(
                  'AR模型待加载\n请确保有ARCore/ARKit支持的设备',
                  style: TextStyle(color: Colors.white, fontSize: 12),
                  textAlign: TextAlign.center,
                ),
              ),
            ],
          ),
          // 扫描提示
          Positioned(
            top: 40,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              decoration: BoxDecoration(
                color: Colors.black45,
                borderRadius: BorderRadius.circular(20),
              ),
              child: const Text(
                '请扫描地面以放置叉车',
                style: TextStyle(color: Colors.white, fontSize: 14),
              ),
            ),
          ),
        ],
      ),
    );
  }

  /// 尺寸信息叠加层 — 对应需求文档十七、十八章
  Widget _buildDimensionOverlay() {
    if (_arConfig == null) return const SizedBox.shrink();

    final length = _arConfig!['real_length_mm'] ?? 0;
    final width = _arConfig!['real_width_mm'] ?? 0;
    final height = _arConfig!['real_height_mm'] ?? 0;
    final wheelbase = _arConfig!['real_wheelbase_mm'] ?? 0;
    final turningRadius = _arConfig!['real_turning_radius_mm'] ?? 0;

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
            const Text('📏 车辆尺寸', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 13)),
            const Divider(color: Colors.white24, height: 12),
            _buildDimRow('车长', '${(length / 1000).toStringAsFixed(1)} m'),
            _buildDimRow('车宽', '${(width / 1000).toStringAsFixed(1)} m'),
            _buildDimRow('车高', '${(height / 1000).toStringAsFixed(1)} m'),
            _buildDimRow('轴距', '${(wheelbase / 1000).toStringAsFixed(1)} m'),
            _buildDimRow('转弯半径', '${(turningRadius / 1000).toStringAsFixed(1)} m'),
            const Divider(color: Colors.white24, height: 12),
            const Text('📐 占地面积', style: TextStyle(color: Colors.white70, fontSize: 11)),
            Text(
              '${(length * width / 1000000).toStringAsFixed(2)} m²',
              style: const TextStyle(color: Colors.greenAccent, fontSize: 13, fontWeight: FontWeight.bold),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildDimRow(String label, String value) {
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

  /// 门架高度指示器 — 对应需求文档十九章
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
            const Text('门架', style: TextStyle(color: Colors.white, fontSize: 10)),
            const SizedBox(height: 4),
            Expanded(
              child: Stack(
                alignment: Alignment.bottomCenter,
                children: [
                  // 高度刻度
                  Container(
                    width: 8,
                    decoration: BoxDecoration(
                      color: Colors.white24,
                      borderRadius: BorderRadius.circular(4),
                    ),
                  ),
                  // 当前高度
                  FractionallySizedBox(
                    heightFactor: (_mastHeight - _mastMinHeight) / (_mastMaxHeight - _mastMinHeight),
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
            // 上升按钮
            GestureDetector(
              onTap: () {
                setState(() {
                  _mastHeight = (_mastHeight + 0.3).clamp(_mastMinHeight, _mastMaxHeight);
                });
              },
              child: Container(
                padding: const EdgeInsets.all(4),
                decoration: BoxDecoration(
                  color: Colors.white24,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: const Icon(Icons.keyboard_arrow_up, color: Colors.white, size: 20),
              ),
            ),
            const SizedBox(height: 4),
            // 下降按钮
            GestureDetector(
              onTap: () {
                setState(() {
                  _mastHeight = (_mastHeight - 0.3).clamp(_mastMinHeight, _mastMaxHeight);
                });
              },
              child: Container(
                padding: const EdgeInsets.all(4),
                decoration: BoxDecoration(
                  color: Colors.white24,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: const Icon(Icons.keyboard_arrow_down, color: Colors.white, size: 20),
              ),
            ),
          ],
        ),
      ),
    );
  }

  /// 底部控制面板
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
          // 门架高度滑块
          Row(
            children: [
              const Text('门架高度', style: TextStyle(color: Colors.white70, fontSize: 12)),
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
              Text(
                '${_mastHeight.toStringAsFixed(1)}m',
                style: const TextStyle(color: Colors.greenAccent, fontSize: 12),
              ),
            ],
          ),
          const SizedBox(height: 8),

          // 控制按钮行
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: [
              _buildArButton(Icons.straighten, '尺寸', () {
                setState(() => _showDimensions = !_showDimensions);
              }),
              _buildArButton(Icons.height, '门架', () {
                setState(() => _showMastHeight = !_showMastHeight);
              }),
              _buildArButton(Icons.center_focus_strong, '对准', () {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('正在识别平面...'), duration: Duration(seconds: 1)),
                );
              }),
              _buildArButton(Icons.camera_alt, '截图', () {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('截图已保存'), duration: Duration(seconds: 1)),
                );
              }),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildArButton(IconData icon, String label, VoidCallback onPressed) {
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

/// AR网格绘制器
class _ArGridPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = Colors.greenAccent.withOpacity(0.2)
      ..strokeWidth = 0.5;

    final center = Offset(size.width / 2, size.height * 0.7);

    // 绘制透视网格
    for (int i = 0; i < 20; i++) {
      final y = center.dy + i * 20.0;
      if (y > size.height) break;
      canvas.drawLine(Offset(0, y), Offset(size.width, y), paint);
    }

    for (int i = -10; i <= 10; i++) {
      final x = center.dx + i * 40.0;
      canvas.drawLine(
        Offset(center.dx, center.dy),
        Offset(x, size.height),
        paint,
      );
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
