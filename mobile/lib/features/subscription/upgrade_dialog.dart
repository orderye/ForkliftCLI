import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

/// 受限功能触发的升级引导弹窗
/// 当用户接口返回 429（免费额度用完）/ 403（权限不足）时调用。
class UpgradeDialog {
  static Future<void> showIfLimit(BuildContext context, Object error) async {
    final msg = error.toString();
    final needUpgrade = msg.contains('429') ||
        msg.contains('今日免费额度') ||
        msg.contains('403') ||
        msg.contains('权限') ||
        msg.contains('最多');
    if (!needUpgrade) return;
    if (!context.mounted) return;
    await showDialog(
      context: context,
      builder: (_) => AlertDialog(
        title: const Row(
          children: [
            Icon(Icons.workspace_premium, color: Color(0xFFF9A825)),
            SizedBox(width: 8),
            Text('功能受限'),
          ],
        ),
        content: const Text('当前为 Free，升级 Pro 即可解锁无限次使用、最多 10 台叉车，并去除开屏广告。'),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('稍后再说'),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.of(context).pop();
              context.push('/subscription/plans');
            },
            style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF1565C0)),
            child: const Text('去升级', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );
  }
}
