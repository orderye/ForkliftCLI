import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

class HomePage extends StatelessWidget {
  const HomePage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('ForkliftCLI'),
        actions: [
          IconButton(
            icon: const Icon(Icons.search),
            onPressed: () => context.push('/parts'),
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // 搜索栏
            GestureDetector(
              onTap: () => context.push('/parts'),
              child: Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(12),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withValues(alpha: 0.05),
                      blurRadius: 10,
                      offset: const Offset(0, 2),
                    ),
                  ],
                ),
                child: const Row(
                  children: [
                    Icon(Icons.search, color: Colors.grey),
                    SizedBox(width: 12),
                    Text('搜索车型/配件', style: TextStyle(color: Colors.grey)),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 20),

            // 扫描铭牌大按钮
            GestureDetector(
              onTap: () => context.push('/ocr'),
              child: Container(
                width: double.infinity,
                padding: const EdgeInsets.all(24),
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [Color(0xFF1565C0), Color(0xFF0D47A1)],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  borderRadius: BorderRadius.circular(16),
                ),
                child: const Column(
                  children: [
                    Icon(Icons.camera_alt, size: 48, color: Colors.white),
                    SizedBox(height: 12),
                    Text(
                      '扫描铭牌',
                      style: TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.bold,
                          color: Colors.white),
                    ),
                    SizedBox(height: 4),
                    Text(
                      '拍摄叉车铭牌，自动识别车型',
                      style: TextStyle(fontSize: 14, color: Colors.white70),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 20),

            // 六大功能入口
            const Text('功能入口',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 12),
            GridView.count(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              crossAxisCount: 3,
              mainAxisSpacing: 12,
              crossAxisSpacing: 12,
              childAspectRatio: 1.0,
              children: [
                _buildFeatureCard(
                    context, Icons.agriculture, '我的叉车', '/my-forklifts'),
                _buildFeatureCard(context, Icons.smart_toy, 'AI维修助手', '/ai'),
                _buildFeatureCard(
                    context, Icons.health_and_safety, '故障诊断', '/ai/diagnose'),
                _buildFeatureCard(
                    context, Icons.account_tree, '结构图', '/brands'),
                _buildFeatureCard(context, Icons.settings, '配件查询', '/parts'),
                _buildFeatureCard(
                    context, Icons.engineering, '发动机', '/engines'),
                _buildFeatureCard(context, Icons.view_in_ar, '3D叉车', '/3d'),
                _buildFeatureCard(context, Icons.view_in_ar, 'AR实景', '/ar'),
                _buildFeatureCard(context, Icons.menu_book, '维修手册', '/manuals'),
                _buildFeatureCard(
                    context, Icons.image_search, '图文检索', '/embed'),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildFeatureCard(
      BuildContext context, IconData icon, String label, String? route,
      {bool comingSoon = false}) {
    return GestureDetector(
      onTap: route != null ? () => context.push(route) : null,
      child: Container(
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(12),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.05),
              blurRadius: 8,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Stack(
              children: [
                Icon(icon,
                    size: 32,
                    color: comingSoon ? Colors.grey : const Color(0xFF1565C0)),
                if (comingSoon)
                  Positioned(
                    right: -8,
                    top: -4,
                    child: Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 4, vertical: 1),
                      decoration: BoxDecoration(
                        color: Colors.orange,
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: const Text('即将',
                          style: TextStyle(fontSize: 8, color: Colors.white)),
                    ),
                  ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              label,
              style: TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w500,
                color: comingSoon ? Colors.grey : null,
              ),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }
}
