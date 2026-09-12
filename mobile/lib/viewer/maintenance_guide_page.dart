import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';

import 'config/viewer_config.dart';
import 'model_asset_manager.dart';
import 'viewer_controller.dart';
import 'viewer_controller_impl.dart';

/// Maintenance guide page - full renderer (highlight + exploded + measure).
class MaintenanceGuidePage extends StatefulWidget {
  const MaintenanceGuidePage({super.key, this.modelUrl, this.forkliftModelId, this.repairGuide});

  final String? modelUrl;
  final int? forkliftModelId;
  final List<RepairStep>? repairGuide;

  @override
  State<MaintenanceGuidePage> createState() => _MaintenanceGuidePageState();
}

/// Repair step data model.
class RepairStep {
  final String title;
  final String partId;
  final double? explodeProgress;
  final String? animationName;

  const RepairStep({
    required this.title,
    required this.partId,
    this.explodeProgress,
    this.animationName,
  });
}

class _MaintenanceGuidePageState extends State<MaintenanceGuidePage> {
  final ViewerController _viewer = ViewerControllerImpl();

  int _currentStep = 0;
  bool _loading = true;
  List<RepairStep> _steps = [];

  @override
  void initState() {
    super.initState();
    _steps = widget.repairGuide ?? _defaultSteps;
    _initViewer();
  }

  static const List<RepairStep> _defaultSteps = [
    RepairStep(title: 'Step 1: Open cover', partId: 'Cabin'),
    RepairStep(title: 'Step 2: Check mast', partId: 'Mast_Inner', explodeProgress: 0.3),
    RepairStep(title: 'Step 3: Adjust fork', partId: 'Carriage_Fork', explodeProgress: 0.5),
    RepairStep(title: 'Step 4: Measure spacing', partId: 'Fork_Left'),
    RepairStep(title: 'Step 5: Mast test', partId: 'Mast_Inner', animationName: 'mast_up'),
  ];

  Future <void> _initViewer() async {
    try {
      final url = await _resolveModelUrl();
      _viewer.requireFeatures(advancedFeatures);
      await _viewer.loadModel(url, modelId: 'maintenance');
    } catch (e) {
      debugPrint('[MaintenanceGuide] Load failed: $e');
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future <String> _resolveModelUrl() async {
    if (widget.modelUrl != null && widget.modelUrl!.isNotEmpty) return widget.modelUrl!;
    if (widget.forkliftModelId != null) {
      final asset = await ModelAssetManager.instance.getAsset(
          forkliftModelId: widget.forkliftModelId!);
      return asset.fileUrl;
    }
    return 'https://cdn.xxx/forklift.glb';
  }

  Future <void> _nextStep() async {
    if (_currentStep >= _steps.length - 1) return;
    _currentStep++;
    await _applyStep(_steps[_currentStep]);
  }

  Future <void> _prevStep() async {
    if (_currentStep <= 0) return;
    _currentStep--;
    await _applyStep(_steps[_currentStep]);
  }

  Future <void> _applyStep(RepairStep step) async {
    await _viewer.clearHighlight();
    await _viewer.clearMeasure();
    await _viewer.setExploded(0);
    await _viewer.stopAnimation();

    if (step.explodeProgress != null) {
      await _viewer.setExploded(step.explodeProgress!);
    }
    await _viewer.highlightPart(step.partId, color: Colors.red);

    if (step.animationName != null) {
      await _viewer.playAnimation(step.animationName!);
    }

    setState(() {});
  }

  @override
  void dispose() {
    _viewer.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final step = _currentStep < _steps.length ? _steps[_currentStep] : null;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Maintenance Guide'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : Stack(
              children: [
                WebViewWidget(controller: _viewer.webView),
                Positioned(
                  bottom: 0,
                  left: 0,
                  right: 0,
                  child: Container(
                    color: Colors.black87,
                    padding: const EdgeInsets.all(12),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Row(
                          children: List.generate(_steps.length, (i) {
                            final isActive = i == _currentStep;
                            return Container(
                              width: 24,
                              height: 24,
                              margin: const EdgeInsets.only(right: 8),
                              decoration: BoxDecoration(
                                color: isActive ? Colors.blue : Colors.grey,
                                shape: BoxShape.circle,
                              ),
                              child: Center(
                                child: Text(
                                  '${i + 1}',
                                  style: const TextStyle(color: Colors.white, fontSize: 12),
                                ),
                              ),
                            );
                          }),
                        ),
                        const SizedBox(height: 8),
                        if (step != null)
                          Text(
                            step.title,
                            style: const TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold),
                          ),
                        const SizedBox(height: 12),
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            TextButton.icon(
                              icon: const Icon(Icons.chevron_left),
                              label: const Text('Prev'),
                              onPressed: _currentStep > 0 ? _prevStep : () {},
                            ),
                            TextButton.icon(
                              label: const Text('Next'),
                              icon: const Icon(Icons.chevron_right),
                              iconAlignment: IconAlignment.end,
                              onPressed: _currentStep < _steps.length - 1 ? _nextStep : () {},
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ),
    );
  }
}
