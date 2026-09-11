import 'package:flutter/material.dart';
import 'package:forklift_bao/core/api/api_client.dart';
import 'package:forklift_bao/core/models/models.dart';

/// 企业版账户绑定管理
class EnterprisePage extends StatefulWidget {
  const EnterprisePage({super.key});

  @override
  State<EnterprisePage> createState() => _EnterprisePageState();
}

class _EnterprisePageState extends State<EnterprisePage> {
  List<EnterpriseAccountItem> _accounts = [];
  bool _loading = true;
  final _phoneController = TextEditingController();
  bool _binding = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    try {
      final data = await ApiClient().getEnterpriseAccounts();
      _accounts = data.map((e) => EnterpriseAccountItem.fromJson(e)).toList();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('加载失败：$e')));
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _bind() async {
    final phone = _phoneController.text.trim();
    if (phone.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('请输入手机号')));
      return;
    }
    setState(() => _binding = true);
    try {
      await ApiClient().bindEnterpriseAccount(phone);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('绑定成功')));
      _phoneController.clear();
      await _load();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('绑定失败：$e')));
      }
    } finally {
      if (mounted) setState(() => _binding = false);
    }
  }

  Future<void> _unbind(EnterpriseAccountItem acc) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('确认解绑'),
        content: Text('解绑后 ${acc.phone} 将降级为 Free'),
        actions: [
          TextButton(onPressed: () => Navigator.of(context).pop(false), child: const Text('取消')),
          TextButton(onPressed: () => Navigator.of(context).pop(true), child: const Text('确认解绑', style: TextStyle(color: Colors.red))),
        ],
      ),
    );
    if (ok != true) return;
    try {
      await ApiClient().unbindEnterpriseAccount(acc.phone);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('已解绑')));
      await _load();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('解绑失败：$e')));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Ultra 绑定账户')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.all(16),
              children: [
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: const Color(0xFFFBC02D).withOpacity(0.1),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: const Color(0xFFFBC02D)),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.business, color: Color(0xFFF9A825)),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text('已绑定账户', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                            Text('${_accounts.length} / 5', style: const TextStyle(color: Colors.grey)),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 16),
                Row(
                  children: [
                    Expanded(
                      child: TextField(
                        controller: _phoneController,
                        decoration: const InputDecoration(
                          hintText: '待绑定手机号',
                          border: OutlineInputBorder(),
                        ),
                        keyboardType: TextInputType.phone,
                      ),
                    ),
                    const SizedBox(width: 12),
                    ElevatedButton(
                      onPressed: _binding ? null : _bind,
                      style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF1565C0)),
                      child: _binding
                          ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                          : const Text('绑定', style: TextStyle(color: Colors.white)),
                    ),
                  ],
                ),
                const SizedBox(height: 20),
                if (_accounts.isEmpty)
                  const Text('暂无绑定账户', style: TextStyle(color: Colors.grey))
                else
                  ..._accounts.map((acc) => Card(
                        child: ListTile(
                          leading: const Icon(Icons.person, color: Color(0xFF1565C0)),
                          title: Text(acc.phone.isNotEmpty ? acc.phone : '用户#${acc.userId}'),
                          subtitle: acc.nickname.isNotEmpty ? Text(acc.nickname) : null,
                          trailing: IconButton(
                            icon: const Icon(Icons.close, color: Colors.red),
                            onPressed: () => _unbind(acc),
                          ),
                        ),
                      )).toList(),
              ],
            ),
    );
  }
}
