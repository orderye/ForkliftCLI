import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:forklift_bao/core/api/api_client.dart';
import 'package:forklift_bao/core/models/models.dart';

class ManualListPage extends StatefulWidget {
  final int? modelId;
  const ManualListPage({super.key, this.modelId});
  @override State<ManualListPage> createState() => _ManualListPageState();
}

class _ManualListPageState extends State<ManualListPage> {
  final _controller = TextEditingController();
  List<ManualItem> _items = [];
  bool _loading = true;
  String? _error;

  @override void initState() { super.initState(); _load(); }

  Future<void> _load() async {
    setState(() { _loading = true; _error = null; });
    try {
      final data = widget.modelId == null
          ? await ApiClient().getManuals(keyword: _controller.text.trim())
          : await ApiClient().getModelManuals(widget.modelId!);
      setState(() => _items = (data['items'] as List? ?? []).map((e) => ManualItem.fromJson(Map<String, dynamic>.from(e))).toList());
    } catch (e) { setState(() => _error = ApiClient.readableError(e)); }
    finally { if (mounted) setState(() => _loading = false); }
  }

  @override Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('维修手册')),
    body: Padding(padding: const EdgeInsets.all(16), child: Column(children: [
      if (widget.modelId == null) TextField(controller: _controller, onSubmitted: (_) => _load(), decoration: InputDecoration(hintText: '搜索手册、车型或控制器', suffixIcon: IconButton(icon: const Icon(Icons.search), onPressed: _load), border: const OutlineInputBorder())),
      const SizedBox(height: 12),
      if (_loading) const LinearProgressIndicator(),
      if (_error != null) Text(_error!, style: const TextStyle(color: Colors.red)),
      Expanded(child: _items.isEmpty && !_loading ? const Center(child: Text('暂无维修手册')) : ListView.separated(itemCount: _items.length, separatorBuilder: (_, __) => const SizedBox(height: 8), itemBuilder: (_, i) { final item = _items[i]; return Card(child: ListTile(leading: const CircleAvatar(child: Icon(Icons.menu_book)), title: Text(item.title), subtitle: Text('${item.category}\n${item.summary}', maxLines: 3, overflow: TextOverflow.ellipsis), isThreeLine: true, trailing: const Icon(Icons.chevron_right), onTap: () => context.push('/manuals/${item.id}'))); }))
    ])),
  );
}
