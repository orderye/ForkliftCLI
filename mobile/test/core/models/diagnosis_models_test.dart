import 'package:flutter_test/flutter_test.dart';
import 'package:forklift_bao/core/models/models.dart';

void main() {
  group('DiagnosisResult', () {
    test('parses complete response and extracts inline probability', () {
      final result = DiagnosisResult.fromJson({
        'possible_causes': [
          {'cause': '蓄电池电压不足', 'probability': '高概率'},
          {'cause': '启动机磨损（中）', 'probability': ''},
        ],
        'check_order': ['测量蓄电池电压', '检查启动机'],
        'safety_warnings': ['停车并熄火'],
        'references': ['维修手册 A'],
      });

      expect(result.possibleCauses, hasLength(2));
      expect(result.possibleCauses.first.probability, '高');
      expect(result.possibleCauses[1].cause, '启动机磨损');
      expect(result.possibleCauses[1].probability, '中');
      expect(result.checkOrder, ['测量蓄电池电压', '检查启动机']);
      expect(result.safetyWarnings, ['停车并熄火']);
      expect(result.references, ['维修手册 A']);
    });

    test('tolerates malformed and missing fields', () {
      final result = DiagnosisResult.fromJson({
        'possible_causes': [
          {'cause': null, 'probability': 42},
          'invalid item',
        ],
        'check_order': 'not a list',
        'safety_warnings': [null, '', 123],
      });

      expect(result.possibleCauses, hasLength(1));
      expect(result.possibleCauses.first.cause, '未提供具体原因');
      expect(result.possibleCauses.first.probability, '待确认');
      expect(result.checkOrder, isEmpty);
      expect(result.safetyWarnings, ['123']);
      expect(result.references, isEmpty);
    });
  });
}
