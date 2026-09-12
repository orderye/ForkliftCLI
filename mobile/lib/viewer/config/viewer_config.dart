/// 渲染器能力分级与功能→等级映射。
///
/// 设计原则：
/// - [RendererTier.lite] 对应 `<model-viewer>` WebView，包体 ~2KB，覆盖查看/AR/相机。
/// - [RendererTier.full] 对应 Three.js WebView，包体 ~200KB gz，额外覆盖高亮/爆炸/动画/测量。
///
/// 业务方在调用高级功能前 `requireFeatures()`，控制器自动按最低满足功能集的等级选择渲染器。
library;

/// 渲染器能力等级。
enum RendererTier {
  /// 轻量：`model-viewer`（能看、能 AR、能旋转缩放）。
  lite,

  /// 全功能：Three.js（额外支持零件高亮、爆炸图、自定义动画、测量标注）。
  full,
}

/// 单个功能需求。
enum ViewerFeature {
  /// 加载模型 + 相机旋转/缩放（基础）。
  basic,

  /// AR 放置（Scene Viewer / AR Quick Look / WebXR）。
  ar,

  /// 零件高亮（材质覆盖 / emissive）。
  highlight,

  /// 爆炸图（进度 0-1，按方向分离零件）。
  exploded,

  /// 自定义动画播放（动画剪辑切换 / 速度）。
  animation,

  /// 测量标注（两点距离，显示尺寸线）。
  measure,
}

/// 功能 → 最小渲染器等级 映射表。
///
/// 任何一项需求为 [RendererTier.full]，整套就升到 full。
const Map<ViewerFeature, RendererTier> _featureTier = {
  ViewerFeature.basic: RendererTier.lite,
  ViewerFeature.ar: RendererTier.lite,
  ViewerFeature.highlight: RendererTier.full,
  ViewerFeature.exploded: RendererTier.full,
  ViewerFeature.animation: RendererTier.full,
  ViewerFeature.measure: RendererTier.full,
};

/// 按需求功能集解析出需要的渲染器等级。
RendererTier resolveTier(Set<ViewerFeature> required) {
  if (required.isEmpty) return RendererTier.lite;
  return required
      .map((f) => _featureTier[f] ?? RendererTier.lite)
      .reduce((a, b) => a.index > b.index ? a : b);
}

/// 高级功能集合（便于业务方 `requireFeatures(advancedFeatures)`）。
const Set<ViewerFeature> advancedFeatures = {
  ViewerFeature.highlight,
  ViewerFeature.exploded,
  ViewerFeature.animation,
  ViewerFeature.measure,
};
