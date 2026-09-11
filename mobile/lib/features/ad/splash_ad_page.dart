import 'dart:async';

import 'package:flutter/material.dart';

/// 开屏广告页：免费版用户每次启动展示，3 秒后可跳过
class SplashAdPage extends StatefulWidget {
  final VoidCallback onFinish;

  const SplashAdPage({super.key, required this.onFinish});

  @override
  State<SplashAdPage> createState() => _SplashAdPageState();
}

class _SplashAdPageState extends State<SplashAdPage> {
  int _countdown = 3;
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _timer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (_countdown <= 1) {
        timer.cancel();
        setState(() => _countdown = 0);
      } else {
        setState(() => _countdown -= 1);
      }
    });
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  void _skip() {
    _timer?.cancel();
    widget.onFinish();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Stack(
        fit: StackFit.expand,
        children: [
          // 广告背景（占位渐变，可替换为真实广告图片/SDK）
          Container(
            decoration: const BoxDecoration(
              gradient: LinearGradient(
                colors: [Color(0xFF1565C0), Color(0xFF0D47A1)],
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
              ),
            ),
            child: const Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Icon(Icons.local_shipping, size: 80, color: Colors.white),
                  SizedBox(height: 16),
                  Text('ForkliftCLI', style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold, color: Colors.white)),
                  SizedBox(height: 8),
                  Text('智能叉车维修辅助工具', style: TextStyle(color: Colors.white70)),
                ],
              ),
            ),
          ),
          // 跳过按钮：3 秒后出现
          Positioned(
            top: MediaQuery.of(context).padding.top + 16,
            right: 16,
            child: _countdown > 0
                ? TextButton(
                    onPressed: _skip,
                    style: TextButton.styleFrom(
                      backgroundColor: Colors.black38,
                      foregroundColor: Colors.white,
                    ),
                    child: Text('跳过 $_countdown'),
                  )
                : TextButton(
                    onPressed: _skip,
                    style: TextButton.styleFrom(
                      backgroundColor: Colors.black38,
                      foregroundColor: Colors.white,
                    ),
                    child: const Text('进入'),
                  ),
          ),
        ],
      ),
    );
  }
}
