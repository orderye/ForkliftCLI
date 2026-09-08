import 'package:flutter/material.dart';
import 'package:forklift_bao/core/api/api_client.dart';
import 'package:forklift_bao/core/models/models.dart';

class EngineListPage extends StatefulWidget {
  const EngineListPage({super.key});

  @override
  State<EngineListPage> createState() => _EngineListPageState();
}

class _EngineListPageState extends State<EngineListPage> {
  List<EngineBrand> _brands = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadBrands();
  }

  Future<void> _loadBrands() async {
    try {
      final data = await ApiClient().getEngineBrands();
      if (mounted) {
        setState(() {
          _brands = data.map((e) => EngineBrand.fromJson(e)).toList();
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
      appBar: AppBar(title: const Text('发动机库')),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: _brands.length,
              itemBuilder: (context, index) {
                final brand = _brands[index];
                return Card(
                  margin: const EdgeInsets.only(bottom: 8),
                  child: ListTile(
                    leading: CircleAvatar(
                      backgroundColor: const Color(0xFF4CAF50).withOpacity(0.1),
                      child: Text(
                        brand.name.substring(0, 1),
                        style: const TextStyle(color: Color(0xFF4CAF50), fontWeight: FontWeight.bold),
                      ),
                    ),
                    title: Text(brand.name),
                    subtitle: Text('${brand.nameEn} · ${brand.country}'),
                    trailing: const Icon(Icons.chevron_right),
                    onTap: () {
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (_) => EngineModelListPage(brand: brand),
                        ),
                      );
                    },
                  ),
                );
              },
            ),
    );
  }
}

class EngineModelListPage extends StatefulWidget {
  final EngineBrand brand;
  const EngineModelListPage({super.key, required this.brand});

  @override
  State<EngineModelListPage> createState() => _EngineModelListPageState();
}

class _EngineModelListPageState extends State<EngineModelListPage> {
  List<EngineModelItem> _models = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadModels();
  }

  Future<void> _loadModels() async {
    try {
      final data = await ApiClient().getEngineModels(widget.brand.id);
      if (mounted) {
        setState(() {
          _models = data.map((e) => EngineModelItem.fromJson(e)).toList();
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
      appBar: AppBar(title: Text('${widget.brand.name} 发动机')),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: _models.length,
              itemBuilder: (context, index) {
                final m = _models[index];
                return Card(
                  margin: const EdgeInsets.only(bottom: 8),
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(m.modelName, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                        const SizedBox(height: 8),
                        Row(
                          children: [
                            _buildSpec('排量', m.displacement),
                            const SizedBox(width: 16),
                            _buildSpec('功率', '${m.powerKw ?? "-"} kW'),
                            const SizedBox(width: 16),
                            _buildSpec('缸数', '${m.cylinders ?? "-"}'),
                          ],
                        ),
                        const SizedBox(height: 4),
                        _buildSpec('燃料', m.fuelType),
                      ],
                    ),
                  ),
                );
              },
            ),
    );
  }

  Widget _buildSpec(String label, String value) {
    return Text(
      '$label: $value',
      style: const TextStyle(fontSize: 13, color: Colors.grey),
    );
  }
}
