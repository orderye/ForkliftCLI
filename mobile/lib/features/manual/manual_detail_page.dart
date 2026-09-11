import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:forklift_bao/core/api/api_client.dart';
import 'package:forklift_bao/core/models/models.dart';

class ManualDetailPage extends StatefulWidget {
  final int manualId;
  const ManualDetailPage({super.key, required this.manualId});
  @override State<ManualDetailPage> createState() => _ManualDetailPageState();
}
class _ManualDetailPageState extends State<ManualDetailPage> {
  ManualDetail? _manual; String? _error;
  @override void initState() { super.initState(); _load(); }
  Future<void> _load() async { try { final data = await ApiClient().getManualDetail(widget.manualId); setState(() => _manual = ManualDetail.fromJson(data)); } catch (e) { setState(() => _error = ApiClient.readableError(e)); } }
  @override Widget build(BuildContext context) { final manual = _manual; return Scaffold(appBar: AppBar(title: Text(manual?.title ?? '手册详情')), body: _error != null ? Center(child: Text(_error!, style: const TextStyle(color: Colors.red))) : manual == null ? const Center(child: CircularProgressIndicator()) : ListView(padding: const EdgeInsets.all(16), children: [Text(manual.title, style: Theme.of(context).textTheme.headlineSmall), const SizedBox(height: 12), Text(manual.summary), const SizedBox(height: 12), Wrap(spacing: 8, children: [Chip(label: Text(manual.category.isEmpty ? '维修手册' : manual.category)), Chip(label: Text('${manual.chunkCount} 个章节'))]), const Divider(height: 32), Text('来源与授权', style: Theme.of(context).textTheme.titleMedium), Text(manual.source.isEmpty ? '内部资料' : manual.source), if (manual.copyrightOwner.isNotEmpty) Text('版权所有：${manual.copyrightOwner}'), const SizedBox(height: 20), FilledButton.icon(onPressed: () => context.push('/manuals/${manual.id}/read'), icon: const Icon(Icons.menu_book), label: const Text('开始阅读')), const SizedBox(height: 24), Text(manual.content, style: const TextStyle(height: 1.6))]); }
}
