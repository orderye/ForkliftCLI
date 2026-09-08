import 'dart:io';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:forklift_bao/core/api/api_client.dart';
import 'package:forklift_bao/core/models/models.dart';
import 'package:forklift_bao/features/forklift/model_detail_page.dart';

class OcrScanPage extends StatefulWidget {
  const OcrScanPage({super.key});

  @override
  State<OcrScanPage> createState() => _OcrScanPageState();
}

class _OcrScanPageState extends State<OcrScanPage> {
  final ImagePicker _picker = ImagePicker();
  File? _imageFile;
  Map<String, dynamic>? _result;
  bool _isProcessing = false;
  String? _error;

  Future<void> _pickImage(ImageSource source) async {
    try {
      final XFile? image = await _picker.pickImage(
        source: source,
        maxWidth: 2048,
        maxHeight: 2048,
        imageQuality: 85,
      );
      if (image == null) return;

      setState(() {
        _imageFile = File(image.path);
        _result = null;
        _error = null;
        _isProcessing = true;
      });

      final bytes = await _imageFile!.readAsBytes();
      final response = await ApiClient().dio.post(
        '/api/v1/ai/ocr/recognize',
        data: FormData.fromMap({
          'file': MultipartFile.fromBytes(bytes, filename: 'nameplate.jpg'),
        }),
      );

      setState(() {
        _result = response.data;
        _isProcessing = false;
      });
    } catch (e) {
      setState(() {
        _error = '识别失败: $e';
        _isProcessing = false;
      });
    }
  }

  void _showImageSourceDialog() {
    showModalBottomSheet(
      context: context,
      builder: (context) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(
              leading: const Icon(Icons.camera_alt),
              title: const Text('拍照'),
              onTap: () {
                Navigator.pop(context);
                _pickImage(ImageSource.camera);
              },
            ),
            ListTile(
              leading: const Icon(Icons.photo_library),
              title: const Text('从相册选择'),
              onTap: () {
                Navigator.pop(context);
                _pickImage(ImageSource.gallery);
              },
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('扫描铭牌')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // 图片预览区
            Container(
              height: 250,
              decoration: BoxDecoration(
                color: Colors.grey[200],
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: Colors.grey[300]!),
              ),
              child: _imageFile != null
                  ? ClipRRect(
                      borderRadius: BorderRadius.circular(12),
                      child: Image.file(_imageFile!, fit: BoxFit.cover),
                    )
                  : Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.camera_alt, size: 64, color: Colors.grey[400]),
                        const SizedBox(height: 12),
                        Text('点击下方按钮拍摄铭牌', style: TextStyle(color: Colors.grey[600])),
                      ],
                    ),
            ),
            const SizedBox(height: 16),

            // 拍照按钮
            ElevatedButton.icon(
              onPressed: _isProcessing ? null : _showImageSourceDialog,
              icon: const Icon(Icons.camera_alt),
              label: const Text('拍摄铭牌'),
            ),
            const SizedBox(height: 16),

            // 处理中
            if (_isProcessing)
              const Card(
                child: Padding(
                  padding: EdgeInsets.all(20),
                  child: Column(
                    children: [
                      CircularProgressIndicator(),
                      SizedBox(height: 12),
                      Text('AI正在识别铭牌...'),
                    ],
                  ),
                ),
              ),

            // 错误
            if (_error != null)
              Card(
                color: Colors.red[50],
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Text(_error!, style: const TextStyle(color: Colors.red)),
                ),
              ),

            // 识别结果
            if (_result != null && !_isProcessing) ...[
              const Text('识别结果', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
              const SizedBox(height: 12),
              _buildResultCard(),
              const SizedBox(height: 16),

              // 匹配车型
              if (_result!['matched_model_id'] != null)
                ElevatedButton(
                  onPressed: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (_) => ModelDetailPage(modelId: _result!['matched_model_id']),
                      ),
                    );
                  },
                  child: const Text('查看匹配车型'),
                ),

              if (_result!['matched_model_id'] == null && _result!['fields'] != null)
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('未匹配到车型', style: TextStyle(fontWeight: FontWeight.bold)),
                        const SizedBox(height: 8),
                        const Text('您可以手动搜索车型：'),
                        const SizedBox(height: 8),
                        ElevatedButton(
                          onPressed: () => Navigator.pushReplacementNamed(context, '/brands'),
                          child: const Text('去车型库搜索'),
                        ),
                      ],
                    ),
                  ),
                ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildResultCard() {
    final fields = _result!['fields'] as Map<String, dynamic>? ?? {};
    final items = [
      ('品牌', fields['brand']),
      ('型号', fields['model']),
      ('序列号', fields['serial_number']),
      ('产品编号', fields['product_number']),
      ('额定载荷', fields['load_capacity']),
      ('起升高度', fields['lift_height']),
      ('整车重量', fields['weight']),
      ('制造年份', fields['manufacture_year']),
      ('发动机型号', fields['engine_model']),
    ];

    return Card(
      child: Column(
        children: [
          for (final (label, value) in items)
            if (value != null && value.toString().isNotEmpty)
              ListTile(
                dense: true,
                title: Text(label, style: const TextStyle(fontSize: 13, color: Colors.grey)),
                trailing: Text(value.toString(), style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w500)),
              ),
          if (_result!['confidence'] != null)
            ListTile(
              dense: true,
              title: const Text('置信度', style: TextStyle(fontSize: 13, color: Colors.grey)),
              trailing: Text('${(_result!['confidence'] * 100).toInt()}%', style: const TextStyle(fontSize: 15)),
            ),
        ],
      ),
    );
  }
}
