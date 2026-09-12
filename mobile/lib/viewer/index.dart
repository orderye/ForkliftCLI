/// ForkliftCLI 3D 查看器模块 —— 双渲染器插件化架构。
///
/// - [RendererTier.lite]  → `<model-viewer>`（能看、能 AR、能旋转缩放）
/// - [RendererTier.full]  → Three.js（零件高亮、爆炸图、动画、测量）
///
/// 业务方通过 [ViewerController] 间接调用，门面自动按需求升级渲染器。
library;

export 'bridge/js_bridge.dart' show JsBridge, ViewerEvent;
export 'config/viewer_config.dart';
export 'renderer/model_viewer_renderer.dart';
export 'renderer/threejs_renderer.dart';
export 'renderer/viewer_renderer.dart';
export 'viewer_controller.dart';
export 'viewer_controller_impl.dart';
export 'viewer_demo_page.dart';
export 'viewer_exception.dart';
export 'ar_view_page.dart';
export 'maintenance_guide_page.dart' show MaintenanceGuidePage, RepairStep;
export 'model_asset_manager.dart';
export 'unity_bridge_adapter.dart';
