import 'package:flutter/material.dart';
import 'package:forklift_bao/core/api/api_client.dart';
import 'package:forklift_bao/features/parts/parts_search_page.dart';

class DiagramViewPage extends StatefulWidget {
  final Map<String, dynamic> diagram;
  const DiagramViewPage({super.key, required this.diagram});

  @override
  State<DiagramViewPage> createState() => _DiagramViewPageState();
}

class _DiagramViewPageState extends State<DiagramViewPage> {
  List<dynamic> _hotspots = [];
  bool _isLoading = true;
  int? _selectedHotspot;

  @override
  void initState() {
    super.initState();
    _loadHotspots();
  }

  Future<void> _loadHotspots() async {
    try {
      final data = await ApiClient().getHotspots(widget.diagram['id']);
      if (mounted) {
        setState(() {
          _hotspots = data;
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
        title: Text(widget.diagram['title'] ?? widget.diagram['diagram_type'] ?? '结构图'),
        actions: [
          if (_hotspots.isNotEmpty)
            IconButton(
              icon: const Icon(Icons.info_outline),
              onPressed: () {
                showModalBottomSheet(
                  context: context,
                  builder: (context) => ListView.builder(
                    itemCount: _hotspots.length,
                    itemBuilder: (context, index) {
                      final h = _hotspots[index];
                      return ListTile(
                        title: Text(h['label'] ?? '零件 ${h['id']}'),
                        subtitle: Text('坐标: (${h['x']}, ${h['y']})'),
                        onTap: () {
                          Navigator.pop(context);
                          setState(() => _selectedHotspot = index);
                        },
                      );
                    },
                  ),
                );
              },
            ),
        ],
      ),
      body: Column(
        children: [
          // 结构图展示区
          Expanded(
            child: InteractiveViewer(
              maxScale: 5.0,
              minScale: 0.5,
              child: Stack(
                children: [
                  // 图片
                  Image.network(
                    widget.diagram['image_url'] ?? '',
                    fit: BoxFit.contain,
                    width: double.infinity,
                    height: double.infinity,
                    errorBuilder: (context, error, stackTrace) {
                      return Container(
                        color: Colors.grey[200],
                        child: const Center(
                          child: Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Icon(Icons.image_not_supported, size: 64, color: Colors.grey),
                              SizedBox(height: 8),
                              Text('结构图图片待上传'),
                            ],
                          ),
                        ),
                      );
                    },
                  ),

                  // 热点标记
                  for (int i = 0; i < _hotspots.length; i++)
                    Positioned(
                      left: _hotspots[i]['x']?.toDouble() ?? 0,
                      top: _hotspots[i]['y']?.toDouble() ?? 0,
                      child: GestureDetector(
                        onTap: () => setState(() => _selectedHotspot = i),
                        child: Container(
                          width: _hotspots[i]['width']?.toDouble() ?? 40,
                          height: _hotspots[i]['height']?.toDouble() ?? 40,
                          decoration: BoxDecoration(
                            color: _selectedHotspot == i
                                ? Colors.red.withOpacity(0.5)
                                : Colors.blue.withOpacity(0.3),
                            border: Border.all(
                              color: _selectedHotspot == i ? Colors.red : Colors.blue,
                              width: 2,
                            ),
                            borderRadius: BorderRadius.circular(4),
                          ),
                          child: Center(
                            child: Text(
                              '${i + 1}',
                              style: TextStyle(
                                color: _selectedHotspot == i ? Colors.red : Colors.blue,
                                fontWeight: FontWeight.bold,
                                fontSize: 12,
                              ),
                            ),
                          ),
                        ),
                      ),
                    ),
                ],
              ),
            ),
          ),

          // 底部零件信息
          if (_selectedHotspot != null && _selectedHotspot! < _hotspots.length)
            _buildHotspotInfo(_hotspots[_selectedHotspot!]),
        ],
      ),
    );
  }

  Widget _buildHotspotInfo(Map<String, dynamic> hotspot) {
    return Container(
      padding: const EdgeInsets.all(16),
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
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Expanded(
                child: Text(
                  hotspot['label'] ?? '零件',
                  style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                ),
              ),
              IconButton(
                icon: const Icon(Icons.close),
                onPressed: () => setState(() => _selectedHotspot = null),
              ),
            ],
          ),
          if (hotspot['part_id'] != null)
            Padding(
              padding: const EdgeInsets.only(top: 8),
              child: ElevatedButton.icon(
                onPressed: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (_) => PartsSearchPage(initialQuery: hotspot['part_id']?.toString()),
                    ),
                  );
                },
                icon: const Icon(Icons.settings),
                label: const Text('查看配件详情'),
              ),
            ),
        ],
      ),
    );
  }
}
