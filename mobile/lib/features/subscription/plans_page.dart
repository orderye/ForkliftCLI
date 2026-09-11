import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:forklift_bao/core/api/api_client.dart';

/// 套餐方案 + 下单
class PlansPage extends StatefulWidget {
  const PlansPage({super.key});

  @override
  State<PlansPage> createState() => _PlansPageState();
}

class _PlansPageState extends State<PlansPage> {
  bool _paying = false;

  Future<void> _buy(String plan, String platform) async {
    setState(() => _paying = true);
    try {
      final data = await ApiClient().createPayment(plan, platform: platform);
      final orderId = data['order_id'];
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('订单已创建（订单号 #$orderId），等待支付回调激活订阅')),
      );
      // 模拟支付回调（stub）：真实环境由第三方异步通知后端激活
      context.pop(true);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('下单失败：$e')),
        );
      }
    } finally {
      if (mounted) setState(() => _paying = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('升级会员')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _buildPlanCard(
            context,
            title: '专业版',
            price: '¥39',
            unit: '/ 月',
            highlights: const [
              '无限次功能调用',
              '最多 10 台叉车',
              '无开屏广告',
              '每月 2 张体验卡',
            ],
            plan: 'pro',
            color: const Color(0xFF1565C0),
            recommended: true,
          ),
          const SizedBox(height: 16),
          _buildPlanCard(
            context,
            title: 'Ultra',
            price: '¥899',
            unit: '/ 年',
            highlights: const [
              '无限次功能调用',
              '不限叉车数量',
              '每月 10 张体验卡',
              '可绑定 5 个账户',
            ],
            plan: 'enterprise',
            color: const Color(0xFFF9A825),
            recommended: false,
          ),
          const SizedBox(height: 16),
          const Text('支付方式', style: TextStyle(fontWeight: FontWeight.bold)),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            children: const [
              Chip(label: Text('微信支付')),
              Chip(label: Text('支付宝')),
              Chip(label: Text('App Store')),
            ],
          ),
          const SizedBox(height: 16),
          if (_paying) const Center(child: CircularProgressIndicator()),
        ],
      ),
    );
  }

  Widget _buildPlanCard(
    BuildContext context, {
    required String title,
    required String price,
    required String unit,
    required List<String> highlights,
    required String plan,
    required Color color,
    required bool recommended,
  }) {
    return Card(
      elevation: recommended ? 4 : 1,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: recommended ? BorderSide(color: color, width: 2) : BorderSide.none,
      ),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Text(title, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
                if (recommended) ...[
                  const SizedBox(width: 8),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                    decoration: BoxDecoration(
                      color: color,
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: const Text('推荐', style: TextStyle(color: Colors.white, fontSize: 12)),
                  ),
                ],
              ],
            ),
            const SizedBox(height: 8),
            Row(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text(price, style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold, color: color)),
                const SizedBox(width: 4),
                Text(unit, style: const TextStyle(color: Colors.grey)),
              ],
            ),
            const SizedBox(height: 16),
            ...highlights.map((h) => Padding(
                  padding: const EdgeInsets.only(bottom: 6),
                  child: Row(
                    children: [
                      Icon(Icons.check_circle, color: color, size: 18),
                      const SizedBox(width: 8),
                      Text(h),
                    ],
                  ),
                )),
            const SizedBox(height: 16),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: _paying ? null : () => _buy(plan, 'wechat'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: color,
                  foregroundColor: Colors.white,
                ),
                child: const Text('立即购买'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
