import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:forklift_bao/core/api/api_client.dart';
import 'package:forklift_bao/features/home/home_page.dart';
import 'package:forklift_bao/features/auth/login_page.dart';
import 'package:forklift_bao/features/forklift/brand_list_page.dart';
import 'package:forklift_bao/features/ai_assistant/ai_chat_page.dart';
import 'package:forklift_bao/features/profile/profile_page.dart';
import 'package:forklift_bao/features/ocr/ocr_scan_page.dart';
import 'package:forklift_bao/features/parts/parts_search_page.dart';
import 'package:forklift_bao/features/maintenance/my_forklifts_page.dart';
import 'package:forklift_bao/features/engine/engine_list_page.dart';
import 'package:forklift_bao/features/threed/threed_viewer_page.dart';
import 'package:forklift_bao/features/ar/ar_view_page.dart';
import 'package:forklift_bao/features/embed/embed_search_page.dart';

final routerProvider = Provider<GoRouter>((ref) {
  return GoRouter(
    initialLocation: '/',
    redirect: (context, state) async {
      final loggedIn = await ApiClient().isLoggedIn();
      final isLoginRoute = state.matchedLocation == '/login';

      if (!loggedIn && !isLoginRoute) return '/login';
      if (loggedIn && isLoginRoute) return '/';
      return null;
    },
    routes: [
      GoRoute(
        path: '/login',
        builder: (context, state) => const LoginPage(),
      ),
      ShellRoute(
        builder: (context, state, child) => MainShell(child: child),
        routes: [
          GoRoute(path: '/', builder: (context, state) => const HomePage()),
          GoRoute(path: '/brands', builder: (context, state) => const BrandListPage()),
          GoRoute(path: '/ai', builder: (context, state) => const AiChatPage()),
          GoRoute(path: '/profile', builder: (context, state) => const ProfilePage()),
        ],
      ),
      GoRoute(path: '/ocr', builder: (context, state) => const OcrScanPage()),
      GoRoute(path: '/parts', builder: (context, state) => const PartsSearchPage()),
      GoRoute(path: '/my-forklifts', builder: (context, state) => const MyForkliftsPage()),
      GoRoute(path: '/engines', builder: (context, state) => const EngineListPage()),
      GoRoute(
        path: '/3d',
        builder: (context, state) {
          final modelId = state.uri.queryParameters['modelId'];
          return ThreeDViewerPage(forkliftModelId: modelId != null ? int.tryParse(modelId) : null);
        },
      ),
      GoRoute(
        path: '/ar',
        builder: (context, state) {
          final modelId = state.uri.queryParameters['modelId'];
          return ArViewPage(forkliftModelId: modelId != null ? int.tryParse(modelId) : null);
        },
      ),
      GoRoute(path: '/embed', builder: (context, state) => const EmbedSearchPage()),
    ],
  );
});

class MainShell extends StatelessWidget {
  final Widget child;
  const MainShell({super.key, required this.child});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: child,
      bottomNavigationBar: NavigationBar(
        selectedIndex: _calculateSelectedIndex(context),
        onDestinationSelected: (index) => _onItemTapped(index, context),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.home), label: '首页'),
          NavigationDestination(icon: Icon(Icons.directions_car), label: '车型库'),
          NavigationDestination(icon: Icon(Icons.smart_toy), label: 'AI维修'),
          NavigationDestination(icon: Icon(Icons.person), label: '我的'),
        ],
      ),
    );
  }

  int _calculateSelectedIndex(BuildContext context) {
    final location = GoRouterState.of(context).matchedLocation;
    if (location == '/') return 0;
    if (location.startsWith('/brands')) return 1;
    if (location.startsWith('/ai')) return 2;
    if (location.startsWith('/profile')) return 3;
    return 0;
  }

  void _onItemTapped(int index, BuildContext context) {
    switch (index) {
      case 0: context.go('/');
      case 1: context.go('/brands');
      case 2: context.go('/ai');
      case 3: context.go('/profile');
    }
  }
}
