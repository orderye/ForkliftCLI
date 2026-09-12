import 'dart:convert';

import 'package:forklift_bao/viewer/bridge/js_bridge.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('ViewerEvent', () {
    test('构造和访问', () {
      const event = ViewerEvent(name: 'onModelLoaded', data: {'success': true});
      expect(event.name, 'onModelLoaded');
      expect(event.data['success'], true);
    });

    test('相等性判断', () {
      const a = ViewerEvent(name: 'onCameraChange', data: {'x': 1});
      const b = ViewerEvent(name: 'onCameraChange', data: {'x': 1});
      expect(a, equals(b));
    });

    test('不同名称不相等', () {
      const a = ViewerEvent(name: 'onModelLoaded', data: {});
      const b = ViewerEvent(name: 'onCameraChange', data: {});
      expect(a, isNot(equals(b)));
    });

    test('不同数据不相等', () {
      const a = ViewerEvent(name: 'test', data: {'x': 1});
      const b = ViewerEvent(name: 'test', data: {'x': 2});
      expect(a, isNot(equals(b)));
    });
  });

  group('JSON 桥协议', () {
    test('命令 payload 序列化', () {
      final payload = jsonEncode({'method': 'loadModel', 'args': {'url': 'test.glb'}});
      expect(payload, contains('"method":"loadModel"'));
      expect(payload, contains('"url":"test.glb"'));
    });

    test('事件 payload 反序列化', () {
      final json = jsonEncode({
        'event': 'onModelLoaded',
        'data': {'success': true, 'modelId': 1}
      });
      final map = jsonDecode(json) as Map<String, dynamic>;
      expect(map['event'], 'onModelLoaded');
      expect((map['data'] as Map)['success'], true);
    });
  });
}
