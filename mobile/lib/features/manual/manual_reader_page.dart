import 'package:flutter/material.dart';
import 'package:forklift_bao/core/api/api_client.dart';
import 'package:forklift_bao/core/models/models.dart';

class ManualReaderPage extends StatefulWidget {
  final int manualId;
  const ManualReaderPage({super.key, required this.manualId});
  @override State<ManualReaderPage> createState() => _ManualReaderPageState();
}
class _ManualReaderPageState extends State<ManualReaderPage> {
  List<ManualChunk> _chunks = []; bool _loading = true; String? _error;
  @override void initState() { super.initState(); _load(); }
  Future<void> _load() async { try { final rows = await ApiClient().getManualChunks(widget.manualId, pageSize: 100); setState(() => _chunks = rows.map((e) => ManualChunk.fromJson(Map<String, dynamic>.from(e))).toList()); } catch (e) { setState(() => _error = ApiClient.readableError(e)); } finally { if (mounted) setState(() => _loading = false); } }
  @override Widget build(BuildContext context) => Scaffold(appBar: AppBar(title: const Text('手册阅读')), body: _loading ? const Center(child: CircularProgressIndicator()) : _error != null ? Center(child: Text(_error!, style: const TextStyle(color: Colors.red))) : ListView.builder(padding: const EdgeInsets.all(16), itemCount: _chunks.length, itemBuilder: (_, i) { final chunk = _chunks[i]; return Padding(padding: const EdgeInsets.only(bottom: 24), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Text(chunk.sectionTitle.isEmpty ? '第 ${i + 1} 节' : chunk.sectionTitle, style: Theme.of(context).textTheme.titleMedium), const SizedBox(height: 8), Text(chunk.text, style: const TextStyle(height: 1.7)), const Divider() ])); }));
}
