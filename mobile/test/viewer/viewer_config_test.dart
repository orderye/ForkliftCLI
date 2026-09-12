import 'package:flutter_test/flutter_test.dart';
import 'package:forklift_bao/viewer/config/viewer_config.dart';

void main() {
  group('resolveTier', () {
    test('空集返回 lite', () {
      expect(resolveTier({}), RendererTier.lite);
    });

    test('仅基础功能返回 lite', () {
      expect(resolveTier({ViewerFeature.basic}), RendererTier.lite);
    });

    test('仅 AR 功能返回 lite', () {
      expect(resolveTier({ViewerFeature.ar}), RendererTier.lite);
    });

    test('基础 + AR 返回 lite', () {
      expect(resolveTier({ViewerFeature.basic, ViewerFeature.ar}), RendererTier.lite);
    });

    test('含高亮返回 full', () {
      expect(resolveTier({ViewerFeature.highlight}), RendererTier.full);
    });

    test('含爆炸图返回 full', () {
      expect(resolveTier({ViewerFeature.exploded}), RendererTier.full);
    });

    test('含动画返回 full', () {
      expect(resolveTier({ViewerFeature.animation}), RendererTier.full);
    });

    test('含测量返回 full', () {
      expect(resolveTier({ViewerFeature.measure}), RendererTier.full);
    });

    test('基础 + 高亮混合，取更高等级', () {
      expect(
        resolveTier({ViewerFeature.basic, ViewerFeature.highlight}),
        RendererTier.full,
      );
    });

    test('advancedFeatures 集合返回 full', () {
      expect(resolveTier(advancedFeatures), RendererTier.full);
    });
  });
}
