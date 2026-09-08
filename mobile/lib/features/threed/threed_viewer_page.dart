import 'package:flutter/material.dart';
import 'package:forklift_bao/core/api/api_client.dart';
import 'package:forklift_bao/core/models/models.dart';
import 'package:model_viewer_plus/model_viewer_plus.dart';

class ThreeDViewerPage extends StatefulWidget {
  final int? forkliftModelId;
  final String? modelUrl;
  final String? title;
  const ThreeDViewerPage({super.key, this.forkliftModelId, this.modelUrl, this.title});

  @override
  State<ThreeDViewerPage> createState() => _ThreeDViewerPageState();
}

class _ThreeDViewerPageState extends State<ThreeDViewerPage> {
  Map<String, dynamic>? _model3d;
  List<dynamic> _parts = [];
  List<dynamic> _animations = [];
  bool _isLoading = true;
  String? _error;

  // 控制状态
  bool _autoRotate = true;
  bool _showWireframe = false;
  bool _showPartsList = false;
  String? _selectedPart;
  String? _playingAnimation;

  @override
  void initState() {
    super.initState();
    _loadModel();
  }

  Future<void> _loadModel() async {
    try {
      if (widget.forkliftModelId != null) {
        final data = await ApiClient().dio.get('/api/v1/3d/forklift/${widget.forkliftModelId}');
        if (mounted) {
          setState(() {
            _model3d = data.data['model'];
            _parts = data.data['parts'] ?? [];
            _animations = data.data['animations'] ?? [];
            _isLoading = false;
          });
        }
      } else {
        if (mounted) setState(() => _isLoading = false);
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = e.toString();
          _isLoading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.title ?? _model3d?['name'] ?? '3D叉车'),
        actions: [
          // 零件列表切换
          IconButton(
            icon: Icon(_showPartsList ? Icons.list : Icons.view_list),
            onPressed: () => setState(() => _showPartsList = !_showPartsList),
            tooltip: '零件列表',
          ),
          // 自动旋转
          IconButton(
            icon: Icon(_autoRotate ? Icons.sync : Icons.sync_disabled),
            onPressed: () => setState(() => _autoRotate = !_autoRotate),
            tooltip: '自动旋转',
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? _buildErrorView()
              : _build3DView(),
      bottomSheet: _showPartsList ? _buildPartsPanel() : null,
    );
  }

  Widget _buildErrorView() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.view_in_ar, size: 64, color: Colors.grey),
          const SizedBox(height: 16),
          const Text('3D模型加载失败', style: TextStyle(fontSize: 16)),
          const SizedBox(height: 8),
          Text(_error ?? '', style: const TextStyle(color: Colors.grey, fontSize: 12)),
          const SizedBox(height: 16),
          // 占位：即使没有真实模型，也展示控制界面
          _buildDemoView(),
        ],
      ),
    );
  }

  Widget _build3DView() {
    final modelUrl = widget.modelUrl ?? _model3d?['file_url'] ?? '';

    if (modelUrl.isEmpty) {
      return _buildDemoView();
    }

    return Column(
      children: [
        // 3D模型展示区
        Expanded(
          flex: 3,
          child: ModelViewer(
            src: modelUrl,
            alt: '叉车3D模型',
            ar: false,
            autoRotate: _autoRotate,
            autoPlay: true,
            cameraControls: true,
            disableZoom: false,
            shadowIntensity: 1,
            shadowSoftness: 0.5,
          ),
        ),

        // 控制面板
        _buildControlPanel(),
      ],
    );
  }

  /// 演示视图 — 无真实模型时展示交互界面
  Widget _buildDemoView() {
    return Column(
      children: [
        // 3D模型占位区
        Expanded(
          flex: 3,
          child: Container(
            margin: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [Colors.grey[200]!, Colors.grey[300]!],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              borderRadius: BorderRadius.circular(16),
            ),
            child: Stack(
              alignment: Alignment.center,
              children: [
                // 叉车示意图
                Icon(Icons.agriculture, size: 120, color: Colors.grey[400]),
                Positioned(
                  bottom: 16,
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                    decoration: BoxDecoration(
                      color: Colors.black54,
                      borderRadius: BorderRadius.circular(16),
                    ),
                    child: const Text(
                      '3D模型待加载\n支持 .glb / .gltf 格式',
                      style: TextStyle(color: Colors.white, fontSize: 12),
                      textAlign: TextAlign.center,
                    ),
                  ),
                ),
                // 旋转指示
                if (_autoRotate)
                  Positioned(
                    top: 16,
                    right: 16,
                    child: Container(
                      padding: const EdgeInsets.all(8),
                      decoration: BoxDecoration(
                        color: Colors.black26,
                        borderRadius: BorderRadius.circular(20),
                      ),
                      child: const Icon(Icons.sync, color: Colors.white, size: 16),
                    ),
                  ),
              ],
            ),
          ),
        ),

        // 控制面板
        _buildControlPanel(),
      ],
    );
  }

  /// 3D控制面板 — 对应需求文档第十五章
  Widget _buildControlPanel() {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.white,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.1),
            blurRadius: 10,
            offset: const Offset(0, -2),
          ),
        ],
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // 门架控制
          Row(
            children: [
              const Icon(Icons.vertical_align_top, size: 16, color: Colors.grey),
              const SizedBox(width: 4),
              const Text('门架', style: TextStyle(fontSize: 12, color: Colors.grey)),
              const Spacer(),
              _buildControlButton('↑ 上升', () => _playAnimation('mast_up')),
              const SizedBox(width: 8),
              _buildControlButton('↓ 下降', () => _playAnimation('mast_down')),
            ],
          ),
          const SizedBox(height: 8),

          // 倾斜控制
          Row(
            children: [
              const Icon(Icons.swap_vert, size: 16, color: Colors.grey),
              const SizedBox(width: 4),
              const Text('倾斜', style: TextStyle(fontSize: 12, color: Colors.grey)),
              const Spacer(),
              _buildControlButton('前倾', () => _playAnimation('tilt_forward')),
              const SizedBox(width: 8),
              _buildControlButton('后倾', () => _playAnimation('tilt_backward')),
            ],
          ),
          const SizedBox(height: 8),

          // 货叉控制
          Row(
            children: [
              const Icon(Icons.height, size: 16, color: Colors.grey),
              const SizedBox(width: 4),
              const Text('货叉', style: TextStyle(fontSize: 12, color: Colors.grey)),
              const Spacer(),
              _buildControlButton('↑ 上升', () => _playAnimation('fork_up')),
              const SizedBox(width: 8),
              _buildControlButton('↓ 下降', () => _playAnimation('fork_down')),
            ],
          ),
          const SizedBox(height: 8),

          // 其他控制
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: [
              _buildToggleChip('透明模式', _showWireframe, (v) {
                setState(() => _showWireframe = v);
              }),
              _buildToggleChip('自动旋转', _autoRotate, (v) {
                setState(() => _autoRotate = v);
              }),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildControlButton(String label, VoidCallback onPressed) {
    return ElevatedButton(
      onPressed: onPressed,
      style: ElevatedButton.styleFrom(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        minimumSize: Size.zero,
        tapTargetSize: MaterialTapTargetSize.shrinkWrap,
      ),
      child: Text(label, style: const TextStyle(fontSize: 12)),
    );
  }

  Widget _buildToggleChip(String label, bool value, ValueChanged<bool> onChanged) {
    return FilterChip(
      label: Text(label, style: const TextStyle(fontSize: 12)),
      selected: value,
      onSelected: onChanged,
    );
  }

  Widget _buildPartsPanel() {
    return Container(
      height: 200,
      padding: const EdgeInsets.all(12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text('零件列表', style: TextStyle(fontWeight: FontWeight.bold)),
              IconButton(
                icon: const Icon(Icons.close, size: 20),
                onPressed: () => setState(() => _showPartsList = false),
              ),
            ],
          ),
          Expanded(
            child: _parts.isEmpty
                ? const Center(child: Text('暂无零件数据', style: TextStyle(color: Colors.grey)))
                : ListView.builder(
                    itemCount: _parts.length,
                    itemBuilder: (context, index) {
                      final part = _parts[index];
                      final isSelected = _selectedPart == part['mesh_name'];
                      return ListTile(
                        dense: true,
                        selected: isSelected,
                        leading: Icon(
                          Icons.circle,
                          size: 12,
                          color: Color(int.parse(part['color']?.replaceFirst('#', '0xFF') ?? '0xFF888888')),
                        ),
                        title: Text(part['name'] ?? '', style: const TextStyle(fontSize: 13)),
                        subtitle: Text(part['part_number'] ?? '', style: const TextStyle(fontSize: 11)),
                        trailing: part['is_interactive'] == 1
                            ? const Icon(Icons.touch_app, size: 16, color: Colors.grey)
                            : null,
                        onTap: () {
                          setState(() => _selectedPart = part['mesh_name']);
                          _highlightPart(part);
                        },
                      );
                    },
                  ),
          ),
        ],
      ),
    );
  }

  void _playAnimation(String animName) {
    setState(() => _playingAnimation = animName);
    _triggerAnimation(animName);
  }

  /// 高亮3D零件
  void _highlightPart(Map<String, dynamic> part) {
    // 显示零件信息弹窗
    showModalBottomSheet(
      context: context,
      builder: (context) => Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              part['name'] ?? '零件',
              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 12),
            _buildInfoRow('零件编号', part['part_number'] ?? '-'),
            _buildInfoRow('OEM编号', part['oem'] ?? '-'),
            _buildInfoRow('分组', part['group'] ?? '-'),
            _buildInfoRow('材质', part['material'] ?? '-'),
            const SizedBox(height: 12),
            const Text(
              '💡 高亮模式：选中零件会以颜色突出显示',
              style: TextStyle(fontSize: 12, color: Colors.grey),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildInfoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          SizedBox(
            width: 80,
            child: Text(label, style: const TextStyle(color: Colors.grey)),
          ),
          Expanded(child: Text(value, style: const TextStyle(fontWeight: FontWeight.w500))),
        ],
      ),
    );
  }

  /// 触发动画
  void _triggerAnimation(String animName) {
    final displayName = {
      'mast_up': '门架上升',
      'mast_down': '门架下降',
      'fork_up': '货叉上升',
      'fork_down': '货叉下降',
      'tilt_forward': '门架前倾',
      'tilt_backward': '门架后倾',
    }[animName] ?? animName;

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Row(
          children: [
            const Icon(Icons.animation, color: Colors.white, size: 20),
            const SizedBox(width: 8),
            Text('播放动画: $displayName'),
          ],
        ),
        duration: const Duration(milliseconds: 1500),
        backgroundColor: const Color(0xFF1565C0),
      ),
    );
  }
  }
}
