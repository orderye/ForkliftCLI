import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:forklift_bao/core/api/api_client.dart';
import 'package:forklift_bao/core/models/models.dart';

class PartsSearchPage extends StatefulWidget {
  final int? modelId;
  final String? initialQuery;
  final int? partId;
  const PartsSearchPage({super.key, this.modelId, this.initialQuery, this.partId});

  @override
  State<PartsSearchPage> createState() => _PartsSearchPageState();
}

class _PartsSearchPageState extends State<PartsSearchPage> {
  final _searchController = TextEditingController();
  List<PartItem> _parts = [];
  bool _isLoading = false;
  bool _hasSearched = false;
  int _page = 1;
  int _total = 0;

  @override
  void initState() {
    super.initState();
    if (widget.initialQuery != null && widget.initialQuery!.isNotEmpty) {
      _searchController.text = widget.initialQuery!;
      WidgetsBinding.instance.addPostFrameCallback((_) => _search());
    }
  }

  Future<SharedPreferences> _getPrefs() async {
    return await SharedPreferences.getInstance();
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  Future<void> _search({int page = 1}) async {
    final query = _searchController.text.trim();
    if (query.isEmpty) return;

    setState(() {
      _isLoading = true;
      _page = page;
    });

    try {
      final result = await ApiClient().searchParts(query, page: page);
      final items = (result['parts'] as List).map((e) => PartItem.fromJson(e)).toList();
      setState(() {
        _parts = items;
        _total = result['total'] ?? 0;
        _isLoading = false;
        _hasSearched = true;
      });
    } catch (e) {
      setState(() => _isLoading = false);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('搜索失败: $e')));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('配件查询')),
      body: Column(
        children: [
          // 搜索栏
          Container(
            padding: const EdgeInsets.all(12),
            color: Colors.white,
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _searchController,
                    decoration: InputDecoration(
                      hintText: '输入OEM编号或配件名称',
                      prefixIcon: const Icon(Icons.search),
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(24),
                        borderSide: BorderSide.none,
                      ),
                      filled: true,
                      fillColor: Colors.grey[100],
                      contentPadding: const EdgeInsets.symmetric(horizontal: 16),
                    ),
                    onSubmitted: (_) => _search(),
                  ),
                ),
                const SizedBox(width: 8),
                IconButton(
                  onPressed: _search,
                  icon: const Icon(Icons.search, color: Color(0xFF1565C0)),
                ),
              ],
            ),
          ),

          // 搜索结果
          if (_hasSearched && !_isLoading)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              child: Row(
                children: [
                  Text('找到 $_total 个配件', style: const TextStyle(color: Colors.grey)),
                ],
              ),
            ),

          if (_isLoading)
            const Expanded(child: Center(child: CircularProgressIndicator()))
          else if (_parts.isEmpty && _hasSearched)
            const Expanded(
              child: Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.search_off, size: 64, color: Colors.grey),
                    SizedBox(height: 16),
                    Text('未找到匹配的配件', style: TextStyle(color: Colors.grey)),
                  ],
                ),
              ),
            )
          else if (_parts.isEmpty)
            const Expanded(
              child: Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.settings, size: 64, color: Colors.grey),
                    SizedBox(height: 16),
                    Text('输入关键词搜索配件', style: TextStyle(color: Colors.grey)),
                    SizedBox(height: 8),
                    Text('如: 轴承、滤芯、油封', style: TextStyle(color: Colors.grey, fontSize: 12)),
                  ],
                ),
              ),
            )
          else
            Expanded(
              child: ListView.builder(
                padding: const EdgeInsets.all(12),
                itemCount: _parts.length,
                itemBuilder: (context, index) {
                  final part = _parts[index];
                  return Card(
                    margin: const EdgeInsets.only(bottom: 8),
                    child: ListTile(
                      title: Text(part.name, style: const TextStyle(fontWeight: FontWeight.w500)),
                      subtitle: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const SizedBox(height: 4),
                          Text('OEM: ${part.oemNumber}', style: const TextStyle(fontSize: 12)),
                          if (part.brand.isNotEmpty)
                            Text('品牌: ${part.brand}', style: const TextStyle(fontSize: 12)),
                        ],
                      ),
                      trailing: const Icon(Icons.chevron_right),
                      onTap: () => _showPartDetail(part),
                    ),
                  );
                },
              ),
            ),
        ],
      ),
    );
  }

  void _showPartDetail(PartItem part) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (context) => DraggableScrollableSheet(
        initialChildSize: 0.6,
        minChildSize: 0.3,
        maxChildSize: 0.9,
        expand: false,
        builder: (context, scrollController) {
          return SingleChildScrollView(
            controller: scrollController,
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Center(
                  child: Container(
                    width: 40,
                    height: 4,
                    decoration: BoxDecoration(
                      color: Colors.grey[300],
                      borderRadius: BorderRadius.circular(2),
                    ),
                  ),
                ),
                const SizedBox(height: 16),
                Text(part.name, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
                const SizedBox(height: 16),
                _buildDetailRow('OEM编号', part.oemNumber),
                if (part.brand.isNotEmpty) _buildDetailRow('品牌', part.brand),
                if (part.category.isNotEmpty) _buildDetailRow('分类', part.category),
                if (part.specifications.isNotEmpty) _buildDetailRow('规格', part.specifications),
                if (part.priceReference != null) _buildDetailRow('参考价格', '¥${part.priceReference}'),
                const SizedBox(height: 16),
                Row(
                  children: [
                    Expanded(
                      child: OutlinedButton.icon(
                        onPressed: () {
                          Navigator.pop(context);
                          _searchController.text = part.oemNumber;
                          _search();
                        },
                        icon: const Icon(Icons.swap_horiz),
                        label: const Text('替代件'),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: OutlinedButton.icon(
                        onPressed: () async {
                          final prefs = await _getPrefs();
                          final favorites = prefs.getStringList('favorite_parts') ?? [];
                          if (!favorites.contains(part.oemNumber)) {
                            favorites.add(part.oemNumber);
                            await prefs.setStringList('favorite_parts', favorites);
                            if (context.mounted) {
                              Navigator.pop(context);
                              ScaffoldMessenger.of(context).showSnackBar(
                                const SnackBar(content: Text('已加入收藏')),
                              );
                            }
                          } else {
                            if (context.mounted) {
                              Navigator.pop(context);
                              ScaffoldMessenger.of(context).showSnackBar(
                                const SnackBar(content: Text('该配件已在收藏夹')),
                              );
                            }
                          }
                        },
                        icon: const Icon(Icons.favorite_border),
                        label: const Text('收藏'),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _buildDetailRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 80,
            child: Text(label, style: const TextStyle(color: Colors.grey)),
          ),
          Expanded(child: Text(value)),
        ],
      ),
    );
  }
}
