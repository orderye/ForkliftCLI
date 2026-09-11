import 'package:flutter/material.dart';
import 'package:forklift_bao/core/api/api_client.dart';
import 'package:forklift_bao/core/models/models.dart';
import 'package:forklift_bao/features/maintenance/records_page.dart';
import 'package:forklift_bao/features/maintenance/reminders_page.dart';
import 'package:forklift_bao/features/subscription/upgrade_dialog.dart';

class MyForkliftsPage extends StatefulWidget {
  const MyForkliftsPage({super.key});

  @override
  State<MyForkliftsPage> createState() => _MyForkliftsPageState();
}

class _MyForkliftsPageState extends State<MyForkliftsPage> {
  List<UserForkliftItem> _forklifts = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadForklifts();
  }

  Future<void> _loadForklifts() async {
    try {
      final data = await ApiClient().getMyForklifts();
      if (mounted) {
        setState(() {
          _forklifts = data.map((e) => UserForkliftItem.fromJson(e)).toList();
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _addForklift() async {
    final result = await Navigator.push(
      context,
      MaterialPageRoute(builder: (_) => const AddForkliftPage()),
    );
    if (result == true) _loadForklifts();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('我的叉车'),
        actions: [
          IconButton(
            icon: const Icon(Icons.add),
            onPressed: _addForklift,
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _forklifts.isEmpty
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(Icons.agriculture, size: 64, color: Colors.grey),
                      const SizedBox(height: 16),
                      const Text('还没有添加叉车', style: TextStyle(color: Colors.grey, fontSize: 16)),
                      const SizedBox(height: 16),
                      ElevatedButton.icon(
                        onPressed: _addForklift,
                        icon: const Icon(Icons.add),
                        label: const Text('添加叉车'),
                      ),
                    ],
                  ),
                )
              : RefreshIndicator(
                  onRefresh: _loadForklifts,
                  child: ListView.builder(
                    padding: const EdgeInsets.all(12),
                    itemCount: _forklifts.length,
                    itemBuilder: (context, index) {
                      final f = _forklifts[index];
                      return Card(
                        margin: const EdgeInsets.only(bottom: 8),
                        child: ListTile(
                          leading: CircleAvatar(
                            backgroundColor: const Color(0xFF1565C0).withOpacity(0.1),
                            child: const Icon(Icons.agriculture, color: Color(0xFF1565C0)),
                          ),
                          title: Text(
                            f.modelName.isNotEmpty ? '${f.brandName} ${f.modelName}' : '未指定车型',
                            style: const TextStyle(fontWeight: FontWeight.w500),
                          ),
                          subtitle: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              if (f.customerName.isNotEmpty) Text('客户: ${f.customerName}'),
                              if (f.serialNumber.isNotEmpty) Text('序列号: ${f.serialNumber}'),
                              if (f.engineModel.isNotEmpty) Text('发动机: ${f.engineModel}'),
                            ],
                          ),
                          trailing: const Icon(Icons.chevron_right),
                          onTap: () {
                            Navigator.push(
                              context,
                              MaterialPageRoute(
                                builder: (_) => ForkliftDetailPage(forklift: f),
                              ),
                            );
                          },
                        ),
                      );
                    },
                  ),
                ),
    );
  }
}

class AddForkliftPage extends StatefulWidget {
  const AddForkliftPage({super.key});

  @override
  State<AddForkliftPage> createState() => _AddForkliftPageState();
}

class _AddForkliftPageState extends State<AddForkliftPage> {
  final _formKey = GlobalKey<FormState>();
  final _customerController = TextEditingController();
  final _serialController = TextEditingController();
  final _engineController = TextEditingController();
  final _notesController = TextEditingController();
  bool _isSaving = false;

  @override
  void dispose() {
    _customerController.dispose();
    _serialController.dispose();
    _engineController.dispose();
    _notesController.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _isSaving = true);
    try {
      await ApiClient().addMyForklift({
        'customer_name': _customerController.text,
        'serial_number': _serialController.text,
        'engine_model': _engineController.text,
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
      appBar: AppBar(title: const Text('添加叉车')),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            TextFormField(
              controller: _customerController,
              decoration: const InputDecoration(labelText: '客户名称'),
            ),
            const SizedBox(height: 16),
            TextFormField(
              controller: _serialController,
              decoration: const InputDecoration(labelText: '序列号'),
            ),
            const SizedBox(height: 16),
            TextFormField(
              controller: _engineController,
              decoration: const InputDecoration(labelText: '发动机型号'),
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

class ForkliftDetailPage extends StatelessWidget {
  final UserForkliftItem forklift;
  const ForkliftDetailPage({super.key, required this.forklift});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(forklift.modelName.isNotEmpty ? '${forklift.brandName} ${forklift.modelName}' : '叉车详情'),
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Card(
            child: Column(
              children: [
                _buildRow('客户', forklift.customerName),
                _buildRow('序列号', forklift.serialNumber),
                _buildRow('发动机', forklift.engineModel),
                _buildRow('工作小时', '${forklift.currentHours} h'),
              ],
            ),
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (_) => RecordsPage(
                          forkliftId: forklift.id,
                          forkliftName: forklift.modelName.isNotEmpty
                              ? '${forklift.brandName} ${forklift.modelName}'
                              : '叉车',
                        ),
                      ),
                    );
                  },
                  icon: const Icon(Icons.build),
                  label: const Text('维修记录'),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (_) => RemindersPage(forkliftId: forklift.id),
                      ),
                    );
                  },
                  icon: const Icon(Icons.notifications),
                  label: const Text('保养提醒'),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(color: Colors.grey)),
          Text(value.isNotEmpty ? value : '-', style: const TextStyle(fontWeight: FontWeight.w500)),
        ],
      ),
    );
  }
}
