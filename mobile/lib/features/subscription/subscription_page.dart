import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:forklift_bao/core/api/api_client.dart';
import 'package:forklift_bao/core/models/models.dart';

/// 会员 / 订阅中心
class SubscriptionPage extends StatefulWidget {
  const SubscriptionPage({super.key});

  @override
  State<SubscriptionPage> createState() => _SubscriptionPageState();
}

class _SubscriptionPageState extends State<SubscriptionPage> {
  SubscriptionMe? _me;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    try {
      final data = await ApiClient().getSubscriptionMe();
      _me = SubscriptionMe.fromJson(data);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('加载订阅信息失败：$e')),
        );
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  String _levelLabel(String level) {
    switch (level) {
      case 'pro':
        return '专业版';
      case 'enterprise':
        return '企业版';
      default:
        return '免费版';
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('会员中心')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _load,
              child: ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  _buildCurrentPlanCard(),
                  const SizedBox(height: 20),
                  if (_me == null || !_me!.isPaid) _buildUpgradeCard(),
                  if (_me != null && _me!.isPaid) ...[
                    _buildTrialCardSection(),
                    if (_me!.level == 'enterprise') _buildEnterpriseSection(),
                  ],
                  const SizedBox(height: 12),
                  _buildPlanComparison(),
                ],
              ),
            ),
    );
  }

  Widget _buildCurrentPlanCard() {
    final level = _me?.level ?? 'free';
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: _me?.isPaid == true
              ? [const Color(0xFFFBC02D), const Color(0xFFF9A825)]
              : [const Color(0xFF1565C0), const Color(0xFF0D47A1)],
        ),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                _me?.isPaid == true ? Icons.workspace_premium : Icons.person,
                size: 28,
                color: Colors.white,
              ),
              const SizedBox(width: 10),
              Text(
                _levelLabel(level),
                style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: Colors.white),
              ),
            ],
          ),
          const SizedBox(height: 12),
          if (_me?.expiresAt != null && _me!.isPaid)
            Text('有效期至：${_me!.expiresAt}', style: const TextStyle(color: Colors.white70))
          else
            const Text('当前为 Free，部分功能受限', style: TextStyle(color: Colors.white70)),
          if (_me?.enterpriseName.isNotEmpty == true)
            Padding(
              padding: const EdgeInsets.only(top: 4),
              child: Text('所属企业：${_me!.enterpriseName}', style: const TextStyle(color: Colors.white70)),
            ),
        ],
      ),
    );
  }

  Widget _buildUpgradeCard() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('解锁全部功能', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            const Text('升级专业版，享受无限次 AI 维修、最多 10 台叉车、无开屏广告。',
                style: TextStyle(color: Colors.grey)),
            const SizedBox(height: 16),
            Row(
              children: [
                Expanded(
                  child: ElevatedButton(
                    onPressed: () => context.push('/subscription/plans'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF1565C0),
                      foregroundColor: Colors.white,
                    ),
                    child: const Text('立即升级'),
                  ),
                ),
                const SizedBox(width: 12),
                OutlinedButton(
                  onPressed: () => context.push('/subscription/trial'),
                  child: const Text('领取体验卡'),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTrialCardSection() {
    return Card(
      child: ListTile(
        leading: const Icon(Icons.card_giftcard, color: Color(0xFF1565C0)),
        title: Text('我的体验卡（剩余 ${_me!.trialCardsRemaining} 张）'),
        subtitle: const Text('赠送给免费好友，激活 7 天专业版'),
        trailing: const Icon(Icons.chevron_right),
        onTap: () => context.push('/subscription/trial'),
      ),
    );
  }

  Widget _buildEnterpriseSection() {
    return Card(
      child: ListTile(
        leading: const Icon(Icons.business, color: Color(0xFF1565C0)),
        title: const Text('企业版绑定账户'),
        subtitle: const Text('可绑定最多 5 个账户，共享企业版权益'),
        trailing: const Icon(Icons.chevron_right),
        onTap: () => context.push('/subscription/enterprise'),
      ),
    );
  }

  Widget _buildPlanComparison() {
    final rows = [
      _PlanRow('每日功能调用', '3 次', '无限', '无限'),
      _PlanRow('叉车数据库', '1 台', '10 台', '不限'),
      _PlanRow('开屏广告', '有', '无', '无'),
      _PlanRow('体验卡赠送', '—', '每月 2 张', '每月 10 张'),
      _PlanRow('绑定账户', '—', '—', '最多 5 个'),
    ];
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('套餐对比', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
            const SizedBox(height: 12),
            Table(
              border: TableBorder.symmetric(
                inside: BorderSide(color: Colors.grey.shade300),
              ),
              columnWidths: const {
                0: FlexColumnWidth(2),
                1: FlexColumnWidth(1.4),
                2: FlexColumnWidth(1.4),
                3: FlexColumnWidth(1.4),
              },
              children: [
                const TableRow(
                  children: [
                    _TableHeader('功能'),
                    _TableHeader('Free'),
                    _TableHeader('Pro'),
                    _TableHeader('Ultra'),
                  ],
                ),
                ...rows.map((r) => TableRow(children: [
                      Padding(padding: const EdgeInsets.all(6), child: Text(r.feature)),
                      Padding(padding: const EdgeInsets.all(6), child: Text(r.free)),
                      Padding(padding: const EdgeInsets.all(6), child: Text(r.pro)),
                      Padding(padding: const EdgeInsets.all(6), child: Text(r.enterprise)),
                    ])),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _PlanRow {
  final String feature;
  final String free;
  final String pro;
  final String enterprise;
  _PlanRow(this.feature, this.free, this.pro, this.enterprise);
}

class _TableHeader extends StatelessWidget {
  final String text;
  const _TableHeader(this.text);
  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.all(6),
        child: Text(text, style: const TextStyle(fontWeight: FontWeight.bold)),
      );
}
