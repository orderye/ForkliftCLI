import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:forklift_bao/core/models/models.dart';
import 'package:forklift_bao/features/ai_assistant/ai_diagnosis_page.dart';

void main() {
  Widget buildPage(DiagnoseCallback callback) {
    return MaterialApp(
      home: AiDiagnosisPage(
        onDiagnose: callback,
        enableContextSelection: false,
      ),
    );
  }

  testWidgets('validates empty symptom', (tester) async {
    await tester.pumpWidget(buildPage((_, __, ___) async => _result));
    await tester.ensureVisible(find.byKey(const Key('diagnose-button')));
    await tester.tap(find.byKey(const Key('diagnose-button')));
    await tester.pump();

    expect(find.text('请描述故障现象'), findsOneWidget);
  });

  testWidgets('disables submit while loading and renders structured result',
      (tester) async {
    final completer = Completer<DiagnosisResult>();
    await tester.pumpWidget(buildPage((_, __, ___) => completer.future));
    await tester.enterText(
      find.byKey(const Key('symptom-field')),
      '发动机热车以后无法启动',
    );
    await tester.ensureVisible(find.byKey(const Key('diagnose-button')));
    await tester.tap(find.byKey(const Key('diagnose-button')));
    await tester.pump();

    expect(find.text('正在分析...'), findsOneWidget);
    completer.complete(_result);
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('diagnosis-result')), findsOneWidget);
    expect(find.text('蓄电池电压不足'), findsOneWidget);
    expect(find.text('测量蓄电池电压'), findsOneWidget);
    expect(find.byKey(const Key('safety-section')), findsOneWidget);
  });

  testWidgets('keeps input and retries after an error', (tester) async {
    var calls = 0;
    await tester.pumpWidget(buildPage((_, __, ___) async {
      calls += 1;
      if (calls == 1) throw Exception('temporary');
      return _result;
    }));
    await tester.enterText(
      find.byKey(const Key('symptom-field')),
      '门架起升速度明显变慢',
    );
    await tester.ensureVisible(find.byKey(const Key('diagnose-button')));
    await tester.tap(find.byKey(const Key('diagnose-button')));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('diagnosis-error')), findsOneWidget);
    expect(find.text('门架起升速度明显变慢'), findsOneWidget);
    await tester.scrollUntilVisible(
      find.byKey(const Key('retry-button')),
      400,
      scrollable: find.byType(Scrollable).first,
    );
    await tester.drag(
      find.byType(Scrollable).first,
      const Offset(0, -120),
    );
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('retry-button')));
    await tester.pumpAndSettle();

    expect(calls, 2);
    expect(find.byKey(const Key('diagnosis-result')), findsOneWidget);
  });
}

const _result = DiagnosisResult(
  possibleCauses: [DiagnosisCause(cause: '蓄电池电压不足', probability: '高')],
  checkOrder: ['测量蓄电池电压'],
  safetyWarnings: ['停车并熄火'],
  references: ['维修手册 A'],
);
