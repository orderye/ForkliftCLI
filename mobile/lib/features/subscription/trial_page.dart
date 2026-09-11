import 'package:flutter/material.dart';
import 'package:forklift_bao/core/api/api_client.dart';
import 'package:forklift_bao/core/models/models.dart';

/// 体验卡：免费用户领取 / 付费用户分享
class TrialPage extends StatefulWidget {
  const TrialPage({super.key});

  @override
  State<TrialPage> createState() => _TrialPageState();
}

class _TrialPageState extends State<TrialPage> {
  List<TrialCardItem> _cards = [];
  bool _loading = true;
  bool _isFree = true;
  final _phoneController = TextEditingController();
  bool _claiming = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    try {
      final me = await ApiClient().getSubscriptionMe();
      _isFree = (me['level'] ?? 'free') == 'free';
      final data = await ApiClient().getMyTrialCards();
      _cards = data.map((e) => TrialCardItem.fromJson(e)).toList();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('加载失败：$e')));
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _claim() async {
    final phone = _phoneController.text.trim();
    if (phone.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('请输入目标手机号')));
      return;
    }
    setState(() => _claiming = true);
    try {
      await ApiClient().claimTrial(phone);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('领取成功，已激活 7 天专业版')));
      _phoneController.clear();
      Navigator.of(context).pop(true);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('领取失败：$e')));
      }
    } finally {
      if (mounted) setState(() => _claiming = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('体验卡')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.all(16),
              children: [
                if (_isFree) ...[
                  Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: const Color(0xFF1565C0).withOpacity(0.08),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('我是免费用户', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                        const SizedBox(height: 8),
                        const Text('输入好友分享的手机号，领取 7 天 Pro 体验卡。'),
                        const SizedBox(height: 12),
                        Row(
                          children: [
                            Expanded(
                              child: TextField(
                                controller: _phoneController,
                                decoration: const InputDecoration(
                                  hintText: '好友注册手机号',
                                  border: OutlineInputBorder(),
                                  contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                                ),
                                keyboardType: TextInputType.phone,
                              ),
                            ),
                            const SizedBox(width: 12),
                            ElevatedButton(
                              onPressed: _claiming ? null : _claim,
                              style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF1565C0)),
                              child: _claiming
                                  ? const SizedBox(
                                      width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                                  : const Text('领取', style: TextStyle(color: Colors.white)),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                ] else ...[
                  Text('我分享的体验卡（${_cards.length} 张）',
                      style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 12),
                  if (_cards.isEmpty)
                    const Text('暂无体验卡，每月自动发放。', style: TextStyle(color: Colors.grey))
                  else
                    ..._cards.map((c) => _buildCardTile(c)).toList(),
                ],
              ],
            ),
    );
  }

  Widget _buildCardTile(TrialCardItem c) {
    final statusText = switch (c.status) {
      'used' => '已使用',
      'expired' => '已过期',
      _ => '可用',
    };
    final color = c.status == 'unused' ? Colors.green : Colors.grey;
    return Card(
      child: ListTile(
        leading: const Icon(Icons.card_giftcard, color: Color(0xFF1565C0)),
        title: Text('体验卡 #${c.id}'),
        subtitle: c.expireAt != null ? Text('有效期至：${c.expireAt}') : null,
        trailing: Container(
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
          decoration: BoxDecoration(
            color: color.withOpacity(0.12),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Text(statusText, style: TextStyle(color: color)),
        ),
      ),
    );
  }
}
