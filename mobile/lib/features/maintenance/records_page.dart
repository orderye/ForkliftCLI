import 'package:flutter/material.dart';
import 'package:forklift_bao/core/api/api_client.dart';

class RecordsPage extends StatefulWidget {
  final int forkliftId;
  final String forkliftName;
  const RecordsPage({super.key, required this.forkliftId, required this.forkliftName});

  @override
  State<RecordsPage> createState() => _RecordsPageState();
}

class _RecordsPageState extends State<RecordsPage> {
  List<dynamic> _records = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadRecords();
  }

  Future<void> _loadRecords() async {
    try {
      final data = await ApiClient().getMaintenanceRecords(widget.forkliftId);
      if (mounted) {
        setState(() {
          _records = data;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('${widget.forkliftName} - 维修记录'),
        actions: [
          IconButton(
            icon: const Icon(Icons.add),
            onPressed: () async {
              final result = await Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (_) => AddRecordPage(forkliftId: widget.forkliftId),
                ),
              );
              if (result == true) _loadRecords();
            },
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _records.isEmpty
              ? const Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.build_circle, size: 64, color: Colors.grey),
                      SizedBox(height: 16),
                      Text('暂无维修记录', style: TextStyle(color: Colors.grey, fontSize: 16)),
                    ],
                  ),
                )
              : ListView.builder(
                  padding: const EdgeInsets.all(12),
                  itemCount: _records.length,
                  itemBuilder: (context, index) {
                    final r = _records[index];
                    return Card(
                      margin: const EdgeInsets.only(bottom: 8),
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Text(r['date'] ?? '', style: const TextStyle(fontWeight: FontWeight.bold)),
                                if (r['cost'] != null && r['cost'] > 0)
                                  Text('¥${r['cost']}', style: const TextStyle(color: Colors.red)),
                              ],
                            ),
                            if (r['fault_description'] != null && r['fault_description'].isNotEmpty)
                              Padding(
                                padding: const EdgeInsets.only(top: 8),
                                child: Text('故障: ${r['fault_description']}', style: const TextStyle(fontSize: 14)),
                              ),
                            if (r['cause'] != null && r['cause'].isNotEmpty)
                              Padding(
                                padding: const EdgeInsets.only(top: 4),
                                child: Text('原因: ${r['cause']}', style: const TextStyle(fontSize: 13, color: Colors.grey)),
                              ),
                            if (r['technician'] != null && r['technician'].isNotEmpty)
                              Padding(
                                padding: const EdgeInsets.only(top: 4),
                                child: Text('维修人员: ${r['technician']}', style: const TextStyle(fontSize: 13, color: Colors.grey)),
                              ),
                          ],
                        ),
                      ),
                    );
                  },
                ),
    );
  }
}

class AddRecordPage extends StatefulWidget {
  final int forkliftId;
  const AddRecordPage({super.key, required this.forkliftId});

  @override
  State<AddRecordPage> createState() => _AddRecordPageState();
}

class _AddRecordPageState extends State<AddRecordPage> {
  final _formKey = GlobalKey<FormState>();
  final _dateController = TextEditingController(text: DateTime.now().toString().substring(0, 10));
  final _faultController = TextEditingController();
  final _causeController = TextEditingController();
  final _technicianController = TextEditingController();
  final _costController = TextEditingController();
  final _notesController = TextEditingController();
  bool _isSaving = false;

  @override
  void dispose() {
    _dateController.dispose();
    _faultController.dispose();
    _causeController.dispose();
    _technicianController.dispose();
    _costController.dispose();
    _notesController.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _isSaving = true);
    try {
      await ApiClient().addMaintenanceRecord(widget.forkliftId, {
        'date': _dateController.text,
        'fault_description': _faultController.text,
        'cause': _causeController.text,
        'technician': _technicianController.text,
        'cost': double.tryParse(_costController.text) ?? 0,
        'notes': _notesController.text,
      });
      if (mounted) Navigator.pop(context, true);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('保存失败: $e')));
      }
    } finally {
      if (mounted) setState(() => _isSaving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('新增维修记录')),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            TextFormField(
              controller: _dateController,
              decoration: const InputDecoration(labelText: '维修日期'),
            ),
            const SizedBox(height: 16),
            TextFormField(
              controller: _faultController,
              decoration: const InputDecoration(labelText: '故障描述'),
              maxLines: 2,
            ),
            const SizedBox(height: 16),
            TextFormField(
              controller: _causeController,
              decoration: const InputDecoration(labelText: '故障原因'),
              maxLines: 2,
            ),
            const SizedBox(height: 16),
            TextFormField(
              controller: _technicianController,
              decoration: const InputDecoration(labelText: '维修人员'),
            ),
            const SizedBox(height: 16),
            TextFormField(
              controller: _costController,
              decoration: const InputDecoration(labelText: '维修费用'),
              keyboardType: TextInputType.number,
            ),
            const SizedBox(height: 16),
            TextFormField(
              controller: _notesController,
              decoration: const InputDecoration(labelText: '备注'),
              maxLines: 3,
            ),
            const SizedBox(height: 24),
            ElevatedButton(
              onPressed: _isSaving ? null : _save,
              child: _isSaving
                  ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2))
                  : const Text('保存'),
            ),
          ],
        ),
      ),
    );
  }
}
