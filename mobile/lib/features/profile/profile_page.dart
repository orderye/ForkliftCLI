import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:forklift_bao/core/api/api_client.dart';

class ProfilePage extends StatelessWidget {
  const ProfilePage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('我的')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // 用户信息卡片
          Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                colors: [Color(0xFF1565C0), Color(0xFF0D47A1)],
              ),
              borderRadius: BorderRadius.circular(16),
            ),
            child: const Row(
              children: [
                CircleAvatar(
                  radius: 30,
                  backgroundColor: Colors.white24,
                  child: Icon(Icons.person, size: 36, color: Colors.white),
                ),
                SizedBox(width: 16),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('ForkliftCLI用户', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white)),
                    SizedBox(height: 4),
                    Text('专业版', style: TextStyle(color: Colors.white70)),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(height: 20),

          // 功能列表
          _buildMenuItem(context, Icons.agriculture, '我的叉车', '管理已添加的叉车', '/my-forklifts'),
          _buildMenuItem(context, Icons.build, '维修记录', '查看维修历史', null),
          _buildMenuItem(context, Icons.notifications, '保养提醒', '查看保养计划', null),
          _buildMenuItem(context, Icons.engineering, '发动机库', '浏览发动机型号', '/engines'),
          _buildMenuItem(context, Icons.favorite, '收藏夹', '收藏的配件和资料', null),
          _buildMenuItem(context, Icons.history, '浏览历史', '最近查看的内容', null),
          const Divider(height: 32),
          _buildMenuItem(context, Icons.settings, '设置', '账号与偏好设置', null),
          _buildMenuItem(context, Icons.help, '帮助与反馈', '获取帮助', null),
          const SizedBox(height: 20),

          // 退出登录
          OutlinedButton(
            onPressed: () async {
              await ApiClient().logout();
              if (context.mounted) context.go('/login');
            },
            style: OutlinedButton.styleFrom(
              foregroundColor: Colors.red,
              side: const BorderSide(color: Colors.red),
              minimumSize: const Size(double.infinity, 48),
            ),
            child: const Text('退出登录'),
          ),
        ],
      ),
    );
  }

  Widget _buildMenuItem(BuildContext context, IconData icon, String title, String subtitle, String? route) {
    return ListTile(
      leading: Icon(icon, color: const Color(0xFF1565C0)),
      title: Text(title),
      subtitle: Text(subtitle, style: const TextStyle(fontSize: 12)),
      trailing: const Icon(Icons.chevron_right),
      onTap: route != null ? () => context.push(route) : null,
    );
  }
}
