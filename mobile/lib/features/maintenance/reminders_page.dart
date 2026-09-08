import 'package:flutter/material.dart';
import 'package:forklift_bao/core/api/api_client.dart';

class RemindersPage extends StatefulWidget {
  final int forkliftId;
  const RemindersPage({super.key, required this.forkliftId});

  @override
  State<RemindersPage> createState() => _RemindersPageState();
}

class _RemindersPageState extends State<RemindersPage> {
  List<dynamic> _reminders = [];
  bool _isLoading = true;

  static const _itemTypes = {
    'engine_oil': '发动机机油',
    'hydraulic_oil': '液压油',
    'gear_oil': '齿轮油',
    'air_filter': '空气滤芯',
    'oil_filter': '机油滤芯',
    'fuel_filter': '柴油滤芯',
    'coolant': '冷却液',
    'brake': '制动系统',
  };

  @override
  void initState() {
    super.initState();
    _loadReminders();
  }

  Future<void> _loadReminders() async {
    try {
      final data = await ApiClient().dio.get('/api/v1/my-forklifts/${widget.forkliftId}/reminders');
      if (mounted) {
        setState(() {
          _reminders = data.data;
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
        title: const Text('保养提醒'),
        actions: [
          IconButton(
            icon: const Icon(Icons.add),
            onPressed: () => _showAddDialog(),
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _reminders.isEmpty
              ? const Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.notifications_none, size: 64, color: Colors.grey),
                      SizedBox(height: 16),
                      Text('暂无保养提醒', style: TextStyle(color: Colors.grey, fontSize: 16)),
                      SizedBox(height: 8),
                      Text('点击右上角添加保养计划', style: TextStyle(color: Colors.grey, fontSize: 12)),
                    ],
                  ),
                )
              : ListView.builder(
                  padding: const EdgeInsets.all(12),
                  itemCount: _reminders.length,
                  itemBuilder: (context, index) {
                    final r = _reminders[index];
                    final itemName = _itemTypes[r['item_type']] ?? r['item_name'] ?? r['item_type'];
                    return Card(
                      margin: const EdgeInsets.only(bottom: 8),
                      child: ListTile(
                        leading: Icon(
                          r['is_active'] == 1 ? Icons.notifications_active : Icons.notifications_off,
                          color: r['is_active'] == 1 ? const Color(0xFF1565C0) : Colors.grey,
                        ),
                        title: Text(itemName, style: const TextStyle(fontWeight: FontWeight.w500)),
                        subtitle: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text('间隔: ${r['interval_value']} ${r['interval_type'] == 'hours' ? '小时' : '天'}'),
                            if (r['next_date'] != null && r['next_date'].isNotEmpty)
                              Text('下次保养: ${r['next_date']}', style: const TextStyle(fontSize: 12)),
                          ],
                        ),
                        trailing: Switch(
                          value: r['is_active'] == 1,
                          onChanged: (value) async {
                            try {
                              await ApiClient().dio.patch(
                                '/api/v1/my-forklifts/reminders/${r['id']}/toggle',
                              );
                              _loadReminders();
                            } catch (e) {
                              if (mounted) {
                                ScaffoldMessenger.of(context).showSnackBar(
                                  SnackBar(content: Text('切换失败: $e')),
                                );
                              }
                            }
                          },
                        ),
                      ),
                    );
                  },
                ),
    );
  }

  void _showAddDialog() {
    String selectedType = 'engine_oil';
    final intervalController = TextEditingController(text: '500');

    showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setDialogState) => AlertDialog(
          title: const Text('添加保养提醒'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              DropdownButtonFormField<String>(
                value: selectedType,
                decoration: const InputDecoration(labelText: '保养项目'),
                items: _itemTypes.entries
                    .map((e) => DropdownMenuItem(value: e.key, child: Text(e.value)))
                    .toList(),
                onChanged: (v) => setDialogState(() => selectedType = v!),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: intervalController,
                decoration: const InputDecoration(labelText: '间隔值'),
                keyboardType: TextInputType.number,
              ),
              const SizedBox(height: 8),
              const Text('单位: 工作小时', style: TextStyle(fontSize: 12, color: Colors.grey)),
            ],
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(context), child: const Text('取消')),
            ElevatedButton(
              onPressed: () async {
                Navigator.pop(context);
                try {
                  await ApiClient().dio.post(
                    '/api/v1/my-forklifts/${widget.forkliftId}/reminders',
                    data: {
                      'item_type': selectedType,
                      'item_name': _itemTypes[selectedType],
                      'interval_type': 'hours',
                      'interval_value': double.tryParse(intervalController.text) ?? 500,
                    },
                  );
                  _loadReminders();
                } catch (e) {
                  if (mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('添加失败: $e')));
                  }
                }
              },
              child: const Text('确定'),
            ),
          ],
        ),
      ),
    );
  }
}
