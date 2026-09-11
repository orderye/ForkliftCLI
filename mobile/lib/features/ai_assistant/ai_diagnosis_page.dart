import 'package:flutter/material.dart';
import 'package:forklift_bao/core/api/api_client.dart';
import 'package:forklift_bao/core/models/models.dart';

typedef DiagnoseCallback = Future<DiagnosisResult> Function(
  String symptom,
  int? forkliftModelId,
  int? engineModelId,
);

class AiDiagnosisPage extends StatefulWidget {
  final int? initialForkliftModelId;
  final int? initialEngineModelId;
  final DiagnoseCallback? onDiagnose;
  final bool enableContextSelection;

  const AiDiagnosisPage({
    super.key,
    this.initialForkliftModelId,
    this.initialEngineModelId,
    this.onDiagnose,
    this.enableContextSelection = true,
  });

  @override
  State<AiDiagnosisPage> createState() => _AiDiagnosisPageState();
}

class _AiDiagnosisPageState extends State<AiDiagnosisPage> {
  static const _suggestions = [
    '发动机无法启动，启动机有转动声音',
    '门架起升缓慢，重载时无法升高',
    '行驶时制动距离变长，并伴有异响',
    '转向沉重，液压油温度偏高',
  ];

  final _formKey = GlobalKey<FormState>();
  final _symptomController = TextEditingController();
  List<Brand> _brands = [];
  List<ForkliftSeries> _series = [];
  List<ForkliftModel> _models = [];
  List<EngineBrand> _engineBrands = [];
  List<EngineModelItem> _engineModels = [];
  int? _brandId;
  int? _seriesId;
  int? _modelId;
  int? _engineBrandId;
  int? _engineModelId;
  String? _presetModelName;
  String? _contextWarning;
  bool _loadingContext = false;
  bool _isDiagnosing = false;
  DiagnosisResult? _result;
  String? _error;

  @override
  void initState() {
    super.initState();
    _modelId = widget.initialForkliftModelId;
    _engineModelId = widget.initialEngineModelId;
    if (widget.enableContextSelection) _loadInitialContext();
  }

  @override
  void dispose() {
    _symptomController.dispose();
    super.dispose();
  }

  Future<void> _loadInitialContext() async {
    setState(() => _loadingContext = true);
    try {
      final api = ApiClient();
      final responses = await Future.wait([
        api.getBrands(),
        api.getEngineBrands(),
      ]);
      var presetName = _presetModelName;
      if (_modelId != null) {
        final detail = await api.getModelDetail(_modelId!);
        presetName =
            '${detail['brand_name'] ?? ''} ${detail['name'] ?? ''}'.trim();
      }
      if (!mounted) return;
      setState(() {
        _brands = responses[0].map((item) => Brand.fromJson(item)).toList();
        _engineBrands =
            responses[1].map((item) => EngineBrand.fromJson(item)).toList();
        _presetModelName = presetName;
      });
    } catch (_) {
      if (mounted) {
        setState(() => _contextWarning = '车型上下文加载失败，仍可直接描述故障进行诊断');
      }
    } finally {
      if (mounted) setState(() => _loadingContext = false);
    }
  }

  Future<void> _selectBrand(int? value) async {
    setState(() {
      _brandId = value;
      _seriesId = null;
      _modelId = null;
      _presetModelName = null;
      _series = [];
      _models = [];
    });
    if (value == null) return;
    try {
      final data = await ApiClient().getSeries(value);
      if (mounted && _brandId == value) {
        setState(() => _series =
            data.map((item) => ForkliftSeries.fromJson(item)).toList());
      }
    } catch (_) {
      _showMessage('系列加载失败，请稍后重试');
    }
  }

  Future<void> _selectSeries(int? value) async {
    setState(() {
      _seriesId = value;
      _modelId = null;
      _models = [];
    });
    if (value == null) return;
    try {
      final data = await ApiClient().getModels(value);
      if (mounted && _seriesId == value) {
        setState(() => _models =
            data.map((item) => ForkliftModel.fromJson(item)).toList());
      }
    } catch (_) {
      _showMessage('车型加载失败，请稍后重试');
    }
  }

  Future<void> _selectEngineBrand(int? value) async {
    setState(() {
      _engineBrandId = value;
      _engineModelId = null;
      _engineModels = [];
    });
    if (value == null) return;
    try {
      final data = await ApiClient().getEngineModels(value);
      if (mounted && _engineBrandId == value) {
        setState(() => _engineModels =
            data.map((item) => EngineModelItem.fromJson(item)).toList());
      }
    } catch (_) {
      _showMessage('发动机型号加载失败，请稍后重试');
    }
  }

  void _showMessage(String message) {
    if (!mounted) return;
    ScaffoldMessenger.of(context)
        .showSnackBar(SnackBar(content: Text(message)));
  }

  Future<void> _diagnose() async {
    if (_isDiagnosing || !_formKey.currentState!.validate()) return;
    FocusScope.of(context).unfocus();
    setState(() {
      _isDiagnosing = true;
      _error = null;
      _result = null;
    });
    try {
      final callback = widget.onDiagnose ??
          (symptom, forkliftModelId, engineModelId) => ApiClient().aiDiagnose(
                symptom,
                forkliftModelId: forkliftModelId,
                engineModelId: engineModelId,
              );
      final result = await callback(
        _symptomController.text.trim(),
        _modelId,
        _engineModelId,
      );
      if (mounted) setState(() => _result = result);
    } catch (error) {
      if (mounted) setState(() => _error = ApiClient.readableError(error));
    } finally {
      if (mounted) setState(() => _isDiagnosing = false);
    }
  }

  void _resetResult() {
    setState(() {
      _result = null;
      _error = null;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('AI 故障诊断'),
        actions: [
          IconButton(
            tooltip: '诊断说明',
            onPressed: _showHelp,
            icon: const Icon(Icons.info_outline),
          ),
        ],
      ),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            _buildIntroCard(),
            const SizedBox(height: 12),
            _buildSymptomCard(),
            if (widget.enableContextSelection) ...[
              const SizedBox(height: 12),
              _buildContextCard(),
            ],
            const SizedBox(height: 16),
            ElevatedButton.icon(
              key: const Key('diagnose-button'),
              onPressed: _isDiagnosing ? null : _diagnose,
              icon: _isDiagnosing
                  ? const SizedBox.square(
                      dimension: 20,
                      child: CircularProgressIndicator(
                          strokeWidth: 2, color: Colors.white),
                    )
                  : const Icon(Icons.health_and_safety),
              label: Text(_isDiagnosing ? '正在分析...' : '开始诊断'),
            ),
            if (_isDiagnosing) ...[
              const SizedBox(height: 12),
              const Card(
                child: Padding(
                  padding: EdgeInsets.all(16),
                  child: Row(
                    children: [
                      Icon(Icons.auto_awesome, color: Color(0xFF1565C0)),
                      SizedBox(width: 12),
                      Expanded(child: Text('正在结合车型、知识库和故障树分析，请稍候…')),
                    ],
                  ),
                ),
              ),
            ],
            if (_error != null) ...[
              const SizedBox(height: 12),
              _buildErrorCard(),
            ],
            if (_result != null) ...[
              const SizedBox(height: 20),
              _buildResult(_result!),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildIntroCard() {
    return Card(
      color: const Color(0xFFE3F2FD),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Icon(Icons.psychology_alt,
                color: Color(0xFF1565C0), size: 30),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('描述越具体，诊断越准确',
                      style: TextStyle(fontWeight: FontWeight.bold)),
                  const SizedBox(height: 6),
                  Text(
                    '建议包含故障发生时机、声音或仪表表现、冷热车状态和已完成的检查。AI 结果仅用于辅助判断。',
                    style:
                        TextStyle(color: Colors.blueGrey.shade700, height: 1.4),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSymptomCard() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('故障现象',
                style: TextStyle(fontSize: 17, fontWeight: FontWeight.bold)),
            const SizedBox(height: 12),
            TextFormField(
              key: const Key('symptom-field'),
              controller: _symptomController,
              minLines: 4,
              maxLines: 7,
              textInputAction: TextInputAction.newline,
              decoration: const InputDecoration(
                hintText: '例如：冷车启动正常，工作两小时后熄火，再次启动时启动机转动但发动机无法着车…',
                alignLabelWithHint: true,
              ),
              validator: (value) {
                final text = value?.trim() ?? '';
                if (text.isEmpty) return '请描述故障现象';
                if (text.length < 6) return '请至少输入 6 个字符，以便准确分析';
                return null;
              },
            ),
            const SizedBox(height: 12),
            const Text('常见现象',
                style: TextStyle(color: Colors.grey, fontSize: 13)),
            const SizedBox(height: 6),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: _suggestions
                  .map(
                    (text) => ActionChip(
                      label: Text(text, overflow: TextOverflow.ellipsis),
                      onPressed: _isDiagnosing
                          ? null
                          : () => _symptomController.text = text,
                    ),
                  )
                  .toList(),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildContextCard() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Expanded(
                  child: Text('诊断上下文（可选）',
                      style:
                          TextStyle(fontSize: 17, fontWeight: FontWeight.bold)),
                ),
                if (_loadingContext)
                  const SizedBox.square(
                      dimension: 18,
                      child: CircularProgressIndicator(strokeWidth: 2)),
              ],
            ),
            const SizedBox(height: 4),
            const Text('选择车型和发动机可缩小知识库检索范围',
                style: TextStyle(color: Colors.grey, fontSize: 13)),
            if (_contextWarning != null) ...[
              const SizedBox(height: 8),
              Text(_contextWarning!,
                  style: const TextStyle(color: Colors.orange, fontSize: 13)),
            ],
            if (_presetModelName != null) ...[
              const SizedBox(height: 12),
              InputChip(
                avatar: const Icon(Icons.agriculture, size: 18),
                label: Text(_presetModelName!),
                onDeleted: _isDiagnosing
                    ? null
                    : () => setState(() {
                          _modelId = null;
                          _presetModelName = null;
                        }),
              ),
            ] else ...[
              const SizedBox(height: 12),
              _dropdown<int>(
                key: const Key('brand-dropdown'),
                value: _brandId,
                hint: '叉车品牌',
                items: _brands
                    .map((item) => DropdownMenuItem(
                        value: item.id, child: Text(item.name)))
                    .toList(),
                onChanged: _isDiagnosing ? null : _selectBrand,
              ),
              const SizedBox(height: 8),
              _dropdown<int>(
                value: _seriesId,
                hint: '叉车系列',
                items: _series
                    .map((item) => DropdownMenuItem(
                        value: item.id, child: Text(item.name)))
                    .toList(),
                onChanged: _isDiagnosing ? null : _selectSeries,
              ),
              const SizedBox(height: 8),
              _dropdown<int>(
                value: _modelId,
                hint: '叉车型号',
                items: _models
                    .map((item) => DropdownMenuItem(
                        value: item.id, child: Text(item.name)))
                    .toList(),
                onChanged: _isDiagnosing
                    ? null
                    : (value) => setState(() => _modelId = value),
              ),
            ],
            const Divider(height: 28),
            _dropdown<int>(
              value: _engineBrandId,
              hint: '发动机品牌',
              items: _engineBrands
                  .map((item) =>
                      DropdownMenuItem(value: item.id, child: Text(item.name)))
                  .toList(),
              onChanged: _isDiagnosing ? null : _selectEngineBrand,
            ),
            const SizedBox(height: 8),
            _dropdown<int>(
              value: _engineModelId,
              hint: '发动机型号',
              items: _engineModels
                  .map((item) => DropdownMenuItem(
                      value: item.id, child: Text(item.modelName)))
                  .toList(),
              onChanged: _isDiagnosing
                  ? null
                  : (value) => setState(() => _engineModelId = value),
            ),
          ],
        ),
      ),
    );
  }

  Widget _dropdown<T>({
    Key? key,
    required T? value,
    required String hint,
    required List<DropdownMenuItem<T>> items,
    required ValueChanged<T?>? onChanged,
  }) {
    return DropdownButtonFormField<T>(
      key: key ?? ValueKey((hint, value, items.length)),
      initialValue: value,
      isExpanded: true,
      decoration: InputDecoration(labelText: hint),
      items: items,
      onChanged: onChanged,
    );
  }

  Widget _buildErrorCard() {
    return Card(
      key: const Key('diagnosis-error'),
      color: const Color(0xFFFFEBEE),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.error_outline, color: Colors.red),
                const SizedBox(width: 8),
                Expanded(
                    child: Text(_error!,
                        style: const TextStyle(fontWeight: FontWeight.w600))),
              ],
            ),
            const SizedBox(height: 8),
            TextButton.icon(
              key: const Key('retry-button'),
              onPressed: _isDiagnosing ? null : _diagnose,
              icon: const Icon(Icons.refresh),
              label: const Text('保留当前内容并重试'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildResult(DiagnosisResult result) {
    return Column(
      key: const Key('diagnosis-result'),
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('诊断结果',
            style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
        const SizedBox(height: 12),
        _resultSection(
          title: '可能原因',
          icon: Icons.report_problem_outlined,
          color: Colors.orange,
          children: result.possibleCauses.asMap().entries.map((entry) {
            final cause = entry.value;
            return ListTile(
              contentPadding: EdgeInsets.zero,
              leading:
                  CircleAvatar(radius: 14, child: Text('${entry.key + 1}')),
              title: Text(cause.cause),
              trailing: _probabilityChip(cause.probability),
            );
          }).toList(),
        ),
        const SizedBox(height: 12),
        _resultSection(
          title: '建议检查顺序',
          icon: Icons.fact_check_outlined,
          color: const Color(0xFF1565C0),
          children: result.checkOrder.asMap().entries.map((entry) {
            return ListTile(
              contentPadding: EdgeInsets.zero,
              leading: CircleAvatar(
                radius: 14,
                backgroundColor: const Color(0xFF1565C0),
                foregroundColor: Colors.white,
                child: Text('${entry.key + 1}'),
              ),
              title: Text(entry.value),
            );
          }).toList(),
        ),
        const SizedBox(height: 12),
        _buildSafetySection(result.safetyWarnings),
        if (result.references.isNotEmpty) ...[
          const SizedBox(height: 12),
          Card(
            child: ExpansionTile(
              leading:
                  const Icon(Icons.menu_book_outlined, color: Colors.blueGrey),
              title: const Text('参考信息',
                  style: TextStyle(fontWeight: FontWeight.bold)),
              children: result.references
                  .map((reference) => ListTile(
                      title: Text(reference,
                          style: const TextStyle(fontSize: 13))))
                  .toList(),
            ),
          ),
        ],
        const SizedBox(height: 12),
        OutlinedButton.icon(
          onPressed: _resetResult,
          icon: const Icon(Icons.edit_note),
          label: const Text('修改描述后重新诊断'),
        ),
      ],
    );
  }

  Widget _resultSection({
    required String title,
    required IconData icon,
    required Color color,
    required List<Widget> children,
  }) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(icon, color: color),
                const SizedBox(width: 8),
                Text(title,
                    style: const TextStyle(
                        fontSize: 17, fontWeight: FontWeight.bold)),
              ],
            ),
            const Divider(),
            if (children.isEmpty)
              const Padding(
                padding: EdgeInsets.symmetric(vertical: 8),
                child: Text('暂无相关信息', style: TextStyle(color: Colors.grey)),
              )
            else
              ...children,
          ],
        ),
      ),
    );
  }

  Widget _probabilityChip(String probability) {
    final color = switch (probability) {
      '高' => Colors.red,
      '中' => Colors.orange,
      '低' => Colors.green,
      _ => Colors.blueGrey,
    };
    return Chip(
      visualDensity: VisualDensity.compact,
      label:
          Text('$probability概率', style: TextStyle(color: color, fontSize: 12)),
      side: BorderSide(color: color.withValues(alpha: 0.5)),
      backgroundColor: color.withValues(alpha: 0.08),
    );
  }

  Widget _buildSafetySection(List<String> warnings) {
    return Card(
      key: const Key('safety-section'),
      color: const Color(0xFFFFF3E0),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Row(
              children: [
                Icon(Icons.health_and_safety, color: Colors.deepOrange),
                SizedBox(width: 8),
                Text('安全提示',
                    style:
                        TextStyle(fontSize: 17, fontWeight: FontWeight.bold)),
              ],
            ),
            const Divider(),
            ...warnings.map(
              (warning) => Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('• ',
                        style: TextStyle(fontWeight: FontWeight.bold)),
                    Expanded(child: Text(warning)),
                  ],
                ),
              ),
            ),
            const Text(
              '请由具备相应资质的维修人员操作。',
              style: TextStyle(
                  color: Colors.deepOrange, fontWeight: FontWeight.bold),
            ),
          ],
        ),
      ),
    );
  }

  void _showHelp() {
    showDialog<void>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('关于故障诊断'),
        content: const Text(
          '系统会结合您选择的车型、发动机、维修知识库和故障树，给出可能原因及检查顺序。'
          '\n\n当前版本支持文字故障描述；诊断结果不能替代现场检测和专业维修判断。',
        ),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('知道了')),
        ],
      ),
    );
  }
}
