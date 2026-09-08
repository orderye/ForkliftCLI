import 'package:flutter/material.dart';
import 'package:forklift_bao/core/api/api_client.dart';
import 'package:forklift_bao/core/models/models.dart';

class BrandListPage extends StatefulWidget {
  const BrandListPage({super.key});

  @override
  State<BrandListPage> createState() => _BrandListPageState();
}

class _BrandListPageState extends State<BrandListPage> {
  List<Brand> _brands = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadBrands();
  }

  Future<void> _loadBrands() async {
    try {
      final data = await ApiClient().getBrands();
      setState(() {
        _brands = data.map((e) => Brand.fromJson(e)).toList();
        _isLoading = false;
      });
    } catch (e) {
      setState(() => _isLoading = false);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('加载失败: $e')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('车型库')),
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
                      backgroundColor: const Color(0xFF1565C0).withOpacity(0.1),
                      child: Text(
                        brand.name.substring(0, 1),
                        style: const TextStyle(color: Color(0xFF1565C0), fontWeight: FontWeight.bold),
                      ),
                    ),
                    title: Text(brand.name),
                    subtitle: Text('${brand.nameEn} · ${brand.country}'),
                    trailing: const Icon(Icons.chevron_right),
                    onTap: () {
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (_) => SeriesListPage(brand: brand),
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

class SeriesListPage extends StatefulWidget {
  final Brand brand;
  const SeriesListPage({super.key, required this.brand});

  @override
  State<SeriesListPage> createState() => _SeriesListPageState();
}

class _SeriesListPageState extends State<SeriesListPage> {
  List<ForkliftSeries> _series = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadSeries();
  }

  Future<void> _loadSeries() async {
    try {
      final data = await ApiClient().getSeries(widget.brand.id);
      setState(() {
        _series = data.map((e) => ForkliftSeries.fromJson(e)).toList();
        _isLoading = false;
      });
    } catch (e) {
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('${widget.brand.name} - 系列')),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: _series.length,
              itemBuilder: (context, index) {
                final s = _series[index];
                return Card(
                  margin: const EdgeInsets.only(bottom: 8),
                  child: ListTile(
                    title: Text(s.name),
                    subtitle: Text(s.description),
                    trailing: const Icon(Icons.chevron_right),
                    onTap: () {
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (_) => ModelListPage(series: s, brandName: widget.brand.name),
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

class ModelListPage extends StatefulWidget {
  final ForkliftSeries series;
  final String brandName;
  const ModelListPage({super.key, required this.series, required this.brandName});

  @override
  State<ModelListPage> createState() => _ModelListPageState();
}

class _ModelListPageState extends State<ModelListPage> {
  List<ForkliftModel> _models = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadModels();
  }

  Future<void> _loadModels() async {
    try {
      final data = await ApiClient().getModels(widget.series.id);
      setState(() {
        _models = data.map((e) => ForkliftModel.fromJson(e)).toList();
        _isLoading = false;
      });
    } catch (e) {
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('${widget.brandName} ${widget.series.name}')),
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
                        Text(m.name, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                        const SizedBox(height: 8),
                        _buildSpecRow('额定载荷', '${m.loadCapacityKg?.toInt() ?? "-"} kg'),
                        _buildSpecRow('起升高度', '${m.liftHeightMm?.toInt() ?? "-"} mm'),
                        _buildSpecRow('整车重量', '${m.weightKg?.toInt() ?? "-"} kg'),
                        _buildSpecRow('燃料类型', m.fuelType),
                      ],
                    ),
                  ),
                );
              },
            ),
    );
  }

  Widget _buildSpecRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: Row(
        children: [
          SizedBox(
            width: 80,
            child: Text(label, style: const TextStyle(color: Colors.grey, fontSize: 13)),
          ),
          Text(value, style: const TextStyle(fontSize: 13)),
        ],
      ),
    );
  }
}
