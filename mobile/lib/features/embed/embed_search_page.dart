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

  Future<void> _searchText() async {
    final q = _ctl.text.trim();
    if (q.isEmpty) return;
    setState(() {
      _loading = true;
      _error = null;
      _hits = [];
    });
    try {
      final hits = await ApiClient().searchEmbed(q, topK: 8);
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
      final hits = await ApiClient().searchEmbed(null, queryImageBase64: b64, topK: 8);
      setState(() => _hits = hits);
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
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
            const SizedBox(height: 12),
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