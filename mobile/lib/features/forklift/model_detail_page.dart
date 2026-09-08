import 'package:flutter/material.dart';
import 'package:forklift_bao/core/api/api_client.dart';
import 'package:forklift_bao/core/models/models.dart';
import 'package:forklift_bao/features/diagram/diagram_view_page.dart';
import 'package:forklift_bao/features/parts/parts_search_page.dart';

class ModelDetailPage extends StatefulWidget {
  final int modelId;
  const ModelDetailPage({super.key, required this.modelId});

  @override
  State<ModelDetailPage> createState() => _ModelDetailPageState();
}

class _ModelDetailPageState extends State<ModelDetailPage> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  Map<String, dynamic>? _model;
  Map<String, dynamic>? _spec;
  List<dynamic> _diagrams = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 4, vsync: this);
    _loadData();
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  Future<void> _loadData() async {
    try {
      final api = ApiClient();
      final modelData = await api.getModelDetail(widget.modelId);

      List<dynamic> diagrams = [];
      try {
        diagrams = await api.getModelDiagrams(widget.modelId);
      } catch (_) {}

      Map<String, dynamic>? spec;
      try {
        final resp = await api.dio.get('/api/v1/forklifts/models/${widget.modelId}/specification');
        spec = resp.data;
      } catch (_) {}

      if (mounted) {
        setState(() {
          _model = modelData;
          _spec = spec;
          _diagrams = diagrams;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return Scaffold(appBar: AppBar(title: const Text('加载中...')), body: const Center(child: CircularProgressIndicator()));
    }
    if (_model == null) {
      return Scaffold(appBar: AppBar(title: const Text('车型详情')), body: const Center(child: Text('加载失败')));
    }

    final m = _model!;
    return Scaffold(
      appBar: AppBar(
        title: Text('${m['brand_name'] ?? ''} ${m['name'] ?? ''}'),
        bottom: TabBar(
          controller: _tabController,
          tabs: const [
            Tab(text: '参数'),
            Tab(text: '结构图'),
            Tab(text: '配件'),
            Tab(text: '故障'),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          _buildParamsTab(m),
          _buildDiagramsTab(),
          _buildPartsTab(),
          _buildFaultsTab(),
        ],
      ),
    );
  }

  Widget _buildParamsTab(Map<String, dynamic> m) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        // 基本信息
        _buildSection('基本信息', [
          _buildRow('品牌', m['brand_name'] ?? '-'),
          _buildRow('系列', m['series_name'] ?? '-'),
          _buildRow('车型', m['name'] ?? '-'),
          _buildRow('燃料类型', m['fuel_type'] ?? '-'),
        ]),

        // 性能参数
        _buildSection('性能参数', [
          _buildRow('额定载荷', '${m['load_capacity_kg']?.toInt() ?? "-"} kg'),
          _buildRow('载荷中心距', '${m['load_capacity_ton']?.toStringAsFixed(1) ?? "-"} t'),
          _buildRow('起升高度', '${m['lift_height_mm']?.toInt() ?? "-"} mm'),
          _buildRow('最大速度', '${m['max_speed_kmh']?.toInt() ?? "-"} km/h'),
        ]),

        // 尺寸参数
        _buildSection('尺寸参数', [
          _buildRow('整车长度', '${m['length_mm']?.toInt() ?? "-"} mm'),
          _buildRow('整车宽度', '${m['width_mm']?.toInt() ?? "-"} mm'),
          _buildRow('整车高度', '${m['height_mm']?.toInt() ?? "-"} mm'),
          _buildRow('轴距', '${m['wheelbase_mm']?.toInt() ?? "-"} mm'),
          _buildRow('最小转弯半径', '${m['turning_radius_mm']?.toInt() ?? "-"} mm'),
          _buildRow('整车重量', '${m['weight_kg']?.toInt() ?? "-"} kg'),
        ]),

        // 详细规格
        if (_spec != null) ...[
          _buildSection('详细规格', [
            _buildRow('发动机类型', _spec!['engine_type'] ?? '-'),
            _buildRow('排量', _spec!['engine_displacement'] ?? '-'),
            _buildRow('功率', '${_spec!['engine_power_kw'] ?? "-"} kW'),
            _buildRow('变速箱', _spec!['transmission_type'] ?? '-'),
            _buildRow('液压系统', _spec!['hydraulic_system'] ?? '-'),
            _buildRow('制动系统', _spec!['brake_type'] ?? '-'),
            _buildRow('转向系统', _spec!['steering_type'] ?? '-'),
            _buildRow('轮胎规格', _spec!['tire_spec'] ?? '-'),
            _buildRow('电瓶电压', _spec!['battery_voltage'] ?? '-'),
          ]),
        ],
      ],
    );
  }

  Widget _buildDiagramsTab() {
    if (_diagrams.isEmpty) {
      return const Center(child: Text('暂无结构图'));
    }
    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: _diagrams.length,
      itemBuilder: (context, index) {
        final d = _diagrams[index];
        return Card(
          margin: const EdgeInsets.only(bottom: 12),
          child: ListTile(
            leading: const Icon(Icons.image, color: Color(0xFF1565C0)),
            title: Text(d['title'] ?? d['diagram_type']),
            subtitle: Text(d['system_type'] ?? ''),
            trailing: const Icon(Icons.chevron_right),
            onTap: () {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (_) => DiagramViewPage(diagram: d),
                ),
              );
            },
          ),
        );
      },
    );
  }

  Widget _buildPartsTab() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.settings, size: 48, color: Colors.grey),
          const SizedBox(height: 16),
          const Text('搜索该车型的配件'),
          const SizedBox(height: 16),
          ElevatedButton(
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (_) => PartsSearchPage(modelId: widget.modelId),
                ),
              );
            },
            child: const Text('去配件查询'),
          ),
        ],
      ),
    );
  }

  Widget _buildFaultsTab() {
    return const Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.warning_amber, size: 48, color: Colors.grey),
          SizedBox(height: 16),
          Text('故障诊断功能需配置AI服务后使用'),
          SizedBox(height: 8),
          Text('请在 AI维修 功能中咨询', style: TextStyle(color: Colors.grey)),
        ],
      ),
    );
  }

  Widget _buildSection(String title, List<Widget> children) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 4),
            child: Text(title, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
          ),
          ...children,
        ],
      ),
    );
  }

  Widget _buildRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(color: Colors.grey, fontSize: 14)),
          Text(value, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w500)),
        ],
      ),
    );
  }
}
