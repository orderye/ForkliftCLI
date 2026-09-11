import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:forklift_bao/core/api/api_client.dart';

class EmbedSearchPage extends StatefulWidget {
  const EmbedSearchPage({super.key});

  @override
  State<EmbedSearchPage> createState() => _EmbedSearchPageState();
}

class _EmbedSearchPageState extends State<EmbedSearchPage> {
  final _ctl = TextEditingController();
  final _picker = ImagePicker();
  List<dynamic> _hits = [];
  bool _loading = false;
  String? _error;

  // ── 筛选状态 ──
  bool _filterExpanded = false;
  int? _forkliftBrandId, _forkliftSeriesId, _forkliftModelId;
  int? _engineBrandId, _engineModelId;
  List<dynamic> _forkliftBrands = [], _forkliftSeries = [], _forkliftModels = [];
  List<dynamic> _engineBrands = [], _engineModels = [];

  @override
  void initState() {
    super.initState();
    _loadBrands();
  }

  Future<void> _loadBrands() async {
    try {
      final fb = await ApiClient().getBrands();
      final eb = await ApiClient().getEngineBrands();
      if (mounted) {
        setState(() {
          _forkliftBrands = fb;
          _engineBrands = eb;
        });
      }
    } catch (_) {}
  }

  Future<void> _onForkliftBrandChanged(int? brandId) async {
    setState(() {
      _forkliftBrandId = brandId;
      _forkliftSeriesId = null;
      _forkliftModelId = null;
      _forkliftSeries = [];
      _forkliftModels = [];
    });
    if (brandId == null) return;
    try {
      final series = await ApiClient().getSeries(brandId);
      if (mounted) setState(() => _forkliftSeries = series);
    } catch (_) {}
  }

  Future<void> _onForkliftSeriesChanged(int? seriesId) async {
    setState(() {
      _forkliftSeriesId = seriesId;
      _forkliftModelId = null;
      _forkliftModels = [];
    });
    if (seriesId == null) return;
    try {
      final models = await ApiClient().getModels(seriesId);
      if (mounted) setState(() => _forkliftModels = models);
    } catch (_) {}
  }

  Future<void> _onEngineBrandChanged(int? brandId) async {
    setState(() {
      _engineBrandId = brandId;
      _engineModelId = null;
      _engineModels = [];
    });
    if (brandId == null) return;
    try {
      final models = await ApiClient().getEngineModels(brandId);
      if (mounted) setState(() => _engineModels = models);
    } catch (_) {}
  }

  void _clearFilters() {
    setState(() {
      _forkliftBrandId = null;
      _forkliftSeriesId = null;
      _forkliftModelId = null;
      _engineBrandId = null;
      _engineModelId = null;
      _forkliftSeries = [];
      _forkliftModels = [];
      _engineModels = [];
    });
  }

  Future<void> _searchText() async {
    final q = _ctl.text.trim();
    if (q.isEmpty) return;
    setState(() {
      _loading = true;
      _error = null;
      _hits = [];
    });
    try {
      final hits = await ApiClient().searchEmbed(
        q,
        topK: 8,
        forkliftModelId: _forkliftModelId,
        engineModelId: _engineModelId,
      );
      setState(() => _hits = hits);
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      setState(() => _loading = false);
    }
  }

  Future<void> _pickAndSearch() async {
    final f = await _picker.pickImage(source: ImageSource.gallery, maxWidth: 1024);
    if (f == null) return;
    final bytes = await f.readAsBytes();
    final b64 = base64Encode(bytes);
    setState(() {
      _loading = true;
      _error = null;
      _hits = [];
    });
    try {
      final hits = await ApiClient().searchEmbed(
        null,
        queryImageBase64: b64,
        topK: 8,
        forkliftModelId: _forkliftModelId,
        engineModelId: _engineModelId,
      );
      setState(() => _hits = hits);
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      setState(() => _loading = false);
    }
  }

  Widget _buildDropdown<T>({
    required String hint,
    required int? value,
    required List<dynamic> items,
    required String Function(dynamic) labelOf,
    required int Function(dynamic) idOf,
    required ValueChanged<int?> onChanged,
  }) {
    return Expanded(
      child: DropdownButtonFormField<int>(
        value: value,
        decoration: InputDecoration(
          hintText: hint,
          isDense: true,
          border: const OutlineInputBorder(),
          contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
        ),
        items: [
          const DropdownMenuItem<int>(value: null, child: Text('全部')),
          ...items.map((item) => DropdownMenuItem<int>(
                value: idOf(item),
                child: Text(labelOf(item), overflow: TextOverflow.ellipsis),
              )),
        ],
        onChanged: onChanged,
      ),
    );
  }

  Widget _buildFilterPanel() {
    return AnimatedCrossFade(
      firstChild: const SizedBox(width: double.infinity),
      secondChild: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // 叉车筛选
          Row(
            children: [
              const Icon(Icons.directions_car, size: 18, color: Colors.grey),
              const SizedBox(width: 6),
              const Text('叉车车型', style: TextStyle(fontWeight: FontWeight.w500)),
              const Spacer(),
              if (_forkliftModelId != null)
                TextButton(
                  onPressed: _clearFilters,
                  child: const Text('清除', style: TextStyle(fontSize: 12)),
                ),
            ],
          ),
          const SizedBox(height: 4),
          Row(
            children: [
              _buildDropdown(
                hint: '品牌',
                value: _forkliftBrandId,
                items: _forkliftBrands,
                labelOf: (b) => b['name'] ?? '',
                idOf: (b) => b['id'] as int,
                onChanged: _onForkliftBrandChanged,
              ),
              const SizedBox(width: 8),
              _buildDropdown(
                hint: '系列',
                value: _forkliftSeriesId,
                items: _forkliftSeries,
                labelOf: (s) => s['name'] ?? '',
                idOf: (s) => s['id'] as int,
                onChanged: _onForkliftSeriesChanged,
              ),
              const SizedBox(width: 8),
              _buildDropdown(
                hint: '车型',
                value: _forkliftModelId,
                items: _forkliftModels,
                labelOf: (m) => m['name'] ?? '',
                idOf: (m) => m['id'] as int,
                onChanged: (v) => setState(() => _forkliftModelId = v),
              ),
            ],
          ),
          const SizedBox(height: 12),
          // 发动机筛选
          Row(
            children: [
              const Icon(Icons.precision_manufacturing, size: 18, color: Colors.grey),
              const SizedBox(width: 6),
              const Text('发动机型号', style: TextStyle(fontWeight: FontWeight.w500)),
            ],
          ),
          const SizedBox(height: 4),
          Row(
            children: [
              _buildDropdown(
                hint: '品牌',
                value: _engineBrandId,
                items: _engineBrands,
                labelOf: (b) => b['name'] ?? '',
                idOf: (b) => b['id'] as int,
                onChanged: _onEngineBrandChanged,
              ),
              const SizedBox(width: 8),
              _buildDropdown(
                hint: '型号',
                value: _engineModelId,
                items: _engineModels,
                labelOf: (m) => m['model_name'] ?? '',
                idOf: (m) => m['id'] as int,
                onChanged: (v) => setState(() => _engineModelId = v),
              ),
              const SizedBox(width: 8),
              const Spacer(),
            ],
          ),
          const SizedBox(height: 8),
        ],
      ),
      crossFadeState: _filterExpanded ? CrossFadeState.showSecond : CrossFadeState.showFirst,
      duration: const Duration(milliseconds: 200),
    );
  }

  @override
  Widget build(BuildContext context) {
    final hasFilter = _forkliftModelId != null || _engineModelId != null;
    return Scaffold(
      appBar: AppBar(title: const Text('多模态检索')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            TextField(
              controller: _ctl,
              decoration: const InputDecoration(
                hintText: '输入文字查询，例如：门架提升缓慢',
                border: OutlineInputBorder(),
              ),
              onSubmitted: (_) => _searchText(),
            ),
            const SizedBox(height: 8),
            // 筛选折叠面板
              InkWell(
                onTap: () => setState(() => _filterExpanded = !_filterExpanded),
                child: Row(
                  children: [
                    Icon(
                      _filterExpanded ? Icons.expand_less : Icons.expand_more,
                      size: 20,
                      color: Theme.of(context).colorScheme.primary,
                    ),
                    const SizedBox(width: 4),
                    Text('筛选', style: TextStyle(
                      color: Theme.of(context).colorScheme.primary,
                      fontWeight: FontWeight.w500,
                    )),
                    const SizedBox(width: 6),
                    if (hasFilter)
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 1),
                        decoration: BoxDecoration(
                          color: Theme.of(context).colorScheme.primaryContainer,
                          borderRadius: BorderRadius.circular(10),
                        ),
                        child: Text(
                          [
                            if (_forkliftModelId != null) '车型',
                            if (_engineModelId != null) '发动机',
                          ].join(' + '),
                          style: TextStyle(
                            fontSize: 11,
                            color: Theme.of(context).colorScheme.onPrimaryContainer,
                          ),
                        ),
                      ),
                  ],
                ),
              ),
              _buildFilterPanel(),
            const SizedBox(height: 8),
            Row(
              children: [
                Expanded(
                  child: FilledButton.icon(
                    onPressed: _loading ? null : _searchText,
                    icon: const Icon(Icons.search),
                    label: const Text('文本检索'),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: FilledButton.tonalIcon(
                    onPressed: _loading ? null : _pickAndSearch,
                    icon: const Icon(Icons.image),
                    label: const Text('图片检索'),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            if (_loading) const LinearProgressIndicator(),
            if (_error != null)
              Text(_error!, style: const TextStyle(color: Colors.red)),
            Expanded(
              child: ListView.separated(
                itemCount: _hits.length,
                separatorBuilder: (_, __) => const Divider(height: 1),
                itemBuilder: (_, i) {
                  final h = _hits[i] as Map<String, dynamic>;
                  final payload = (h['payload'] as Map?) ?? {};
                  final title = payload['title'] ?? h['id'];
                  final text = payload['text'] ?? '';
                  final score = h['score'];
                  return ListTile(
                    title: Text(title.toString()),
                    subtitle: Text(
                      text.toString().length > 200
                          ? '${text.toString().substring(0, 200)}…'
                          : text.toString(),
                    ),
                    trailing: Text(score == null ? '' : score.toStringAsFixed(3)),
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}
