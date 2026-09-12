import 'package:forklift_bao/viewer/model_asset_manager.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('ModelAssetManager.resolveUrl', () {
    // 后端 /api/v1/3d/forklift/{id} 返回的是 /uploads/models/... 这类相对地址。
    // 3D 模型由 WebView 内的 GLTFLoader 请求，而该 WebView 基址是 asset:///，
    // 相对路径会解析成 asset:///uploads/... 直接 404 —— 3D 链路曾因此端到端不通。
    test('相对路径补全为后端绝对地址', () {
      expect(
        ModelAssetManager.resolveUrl('/uploads/models/1/623408c9631c90ba.glb'),
        'http://localhost:8000/uploads/models/1/623408c9631c90ba.glb',
      );
    });

    test('不以斜杠开头的相对路径也能补全', () {
      expect(
        ModelAssetManager.resolveUrl('uploads/models/1/x.glb'),
        'http://localhost:8000/uploads/models/1/x.glb',
      );
    });

    test('已经是 http 的 URL 原样返回', () {
      const url = 'http://cdn.example.com/m.glb';
      expect(ModelAssetManager.resolveUrl(url), url);
    });

    test('https URL 原样返回', () {
      const url = 'https://cdn.example.com/m.glb';
      expect(ModelAssetManager.resolveUrl(url), url);
    });

    test('asset:// 与 file:// 等本地协议原样返回', () {
      expect(
        ModelAssetManager.resolveUrl('asset:///assets/model.glb'),
        'asset:///assets/model.glb',
      );
      expect(
        ModelAssetManager.resolveUrl('file:///data/local/tmp/model.glb'),
        'file:///data/local/tmp/model.glb',
      );
    });

    test('data: URL 原样返回', () {
      const url = 'data:application/octet-stream;base64,AAAB';
      expect(ModelAssetManager.resolveUrl(url), url);
    });

    test('空串与 null 不抛异常，返回空串', () {
      expect(ModelAssetManager.resolveUrl(''), isEmpty);
      expect(ModelAssetManager.resolveUrl(null), isEmpty);
    });

    test('仅空白字符按空处理', () {
      expect(ModelAssetManager.resolveUrl('   '), isEmpty);
    });

    test('前后空白被去除后再拼', () {
      expect(
        ModelAssetManager.resolveUrl('  /uploads/models/1/x.glb  '),
        'http://localhost:8000/uploads/models/1/x.glb',
      );
    });
  });

  group('ModelAsset 缓存往返', () {
    test('toJson/fromJson 保真', () {
      final original = ModelAsset(
        modelId: 7,
        name: '8FG30 3D',
        fileUrl: 'http://localhost:8000/uploads/models/1/x.glb',
        version: 3,
        contentHash: 'abc123',
        format: 'glb',
        parts: const [PartInfo(name: 'tripo_node_x', meshName: 'tripo_node_x', group: 'body')],
        animations: const [AnimationInfo(name: 'mast_lift', duration: 3.0)],
      );
      final round = ModelAsset.fromJson(original.toJson());
      expect(round.modelId, 7);
      expect(round.name, '8FG30 3D');
      expect(round.fileUrl, original.fileUrl);
      expect(round.version, 3);
      expect(round.contentHash, 'abc123');
      expect(round.format, 'glb');
      expect(round.parts.single.meshName, 'tripo_node_x');
      expect(round.animations.single.duration, 3.0);
    });

    test('缺省字段有安全默认值', () {
      final asset = ModelAsset.fromJson(const {});
      expect(asset.modelId, 0);
      expect(asset.version, 1);
      expect(asset.format, 'glb');
      expect(asset.parts, isEmpty);
      expect(asset.animations, isEmpty);
    });
  });
}
