import 'dart:convert';
import 'dart:io';

import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:path_provider/path_provider.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../core/api/api_client.dart';

/// 模型资源管理器 —— 从后端获取模型元数据 + 本地缓存。
///
/// 缓存策略：
/// - 元数据缓存：SharedPreferences（按 modelId 键值存储）
/// - 模型文件缓存：本地文件系统（persistentDataPath/ForkliftCLI/Models/）
/// - 缓存失效：version + contentHash 不一致则重新下载
///
/// 使用示例：
/// ```dart
/// final asset = await ModelAssetManager.instance.getAsset(modelId: 1);
/// await viewer.loadModel(asset.fileUrl);
/// ```
class ModelAssetManager {
  ModelAssetManager._();
  static final ModelAssetManager instance = ModelAssetManager._();

  static const _cacheDirName = 'ForkliftCLI/Models';
  static const _metadataPrefix = 'model_meta_';

  /// 获取模型元数据（带缓存）。
  ///
  /// [forkliftModelId] 叉车模型 ID。
  /// [forceRefresh] 忽略缓存，强制从后端拉取。
  Future<ModelAsset> getAsset({
    required int forkliftModelId,
    bool forceRefresh = false,
  }) async {
    // 1. 尝试读缓存
    if (!forceRefresh) {
      final cached = await _readCachedMetadata(forkliftModelId);
      if (cached != null) return _resolveAssetUrls(cached);
    }

    // 2. 从后端获取
    final asset = await _fetchFromApi(forkliftModelId);

    // 3. 写入缓存
    await _writeCachedMetadata(forkliftModelId, asset);

    return asset;
  }

  /// 解析模型文件的本地缓存路径（已缓存则返回，否则 null）。
  Future<String?> getCachedFilePath(ModelAsset asset) async {
    final dir = await _getCacheDir();
    final path = '$dir/${asset.cacheFilename}';
    final file = File(path);
    return file.existsSync() ? path : null;
  }

  /// 下载并缓存模型文件到本地。
  Future<String> downloadAndCache(ModelAsset asset) async {
    final dir = await _getCacheDir();
    final path = '$dir/${asset.cacheFilename}';

    final file = File(path);
    if (file.existsSync()) return path;

    try {
      await dir.create(recursive: true);
      await ApiClient().dio.download(asset.fileUrl, path);
      debugPrint('[ModelAssetManager] 已缓存 ${asset.cacheFilename} (${file.lengthSync()} bytes)');
      return path;
    } catch (e) {
      debugPrint('[ModelAssetManager] 下载失败: $e');
      throw ModelAssetException('模型下载失败', cause: e);
    }
  }

  /// 清除指定模型的缓存。
  Future<void> clearCache(int modelId) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('$_metadataPrefix$modelId');

    final asset = await _readCachedMetadata(modelId);
    if (asset != null) {
      final dir = await _getCacheDir();
      final file = File('$dir/${asset.cacheFilename}');
      if (file.existsSync()) await file.delete();
    }
  }

  /// 清除所有模型缓存。
  Future<void> clearAllCaches() async {
    final prefs = await SharedPreferences.getInstance();
    final keys = prefs.getKeys().where((k) => k.startsWith(_metadataPrefix));
    for (final key in keys) {
      await prefs.remove(key);
    }

    final dir = await _getCacheDir();
    if (dir.existsSync()) {
      await for (final entity in dir.list()) {
        if (entity is File) await entity.delete();
      }
    }
  }

  // ---------- private ----------

  Future<Directory> _getCacheDir() async {
    final docs = await getApplicationDocumentsDirectory();
    return Directory('${docs.path}/$_cacheDirName');
  }

  Future<ModelAsset?> _readCachedMetadata(int modelId) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final json = prefs.getString('$_metadataPrefix$modelId');
      if (json == null) return null;
      return ModelAsset.fromJson(jsonDecode(json) as Map<String, dynamic>);
    } catch (e) {
      debugPrint('[ModelAssetManager] 读缓存失败: $e');
      return null;
    }
  }

  Future<void> _writeCachedMetadata(int modelId, ModelAsset asset) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('$_metadataPrefix$modelId', jsonEncode(asset.toJson()));
    } catch (e) {
      debugPrint('[ModelAssetManager] 写缓存失败: $e');
    }
  }

  Future<ModelAsset> _fetchFromApi(int modelId) async {
    try {
      final response = await ApiClient().dio.get('/api/v1/3d/forklift/$modelId');
      final data = response.data;

      final model = data['model'] as Map<String, dynamic>? ?? {};
      final parts = (data['parts'] as List<dynamic>?) ?? [];
      final animations = (data['animations'] as List<dynamic>?) ?? [];

      return _resolveAssetUrls(ModelAsset(
        modelId: modelId,
        name: model['name'] ?? '',
        fileUrl: model['file_url'] ?? model['url'] ?? '',
        version: (model['version'] as int?) ?? 1,
        contentHash: model['content_hash'] ?? '',
        format: model['format'] ?? 'glb',
        parts: parts.map((p) => PartInfo.fromJson(p as Map<String, dynamic>)).toList(),
        animations: animations.map((a) => AnimationInfo.fromJson(a as Map<String, dynamic>)).toList(),
      ));
    } catch (e) {
      throw ModelAssetException('获取模型元数据失败', cause: e);
    }
  }

  /// 把后端返回的相对资源地址补全为绝对地址。
  ///
  /// 后端 `/api/v1/3d/forklift/{id}` 返回的是 `/uploads/models/...` 这类
  /// **相对**路径；3D 模型最终由 WebView 里的 GLTFLoader 去请求，而该 WebView
  /// 的基址是 `file:///`，相对路径会被解析成 `file:///uploads/...` 并 404。
  /// 在这里统一补全，业务层拿到的一定是可直接请求的绝对 URL。
  static String resolveUrl(String? url) {
    final raw = (url ?? '').trim();
    if (raw.isEmpty ||
        raw.startsWith('http://') ||
        raw.startsWith('https://') ||
        raw.startsWith('file:///') ||
        raw.startsWith('asset://')) {
      return raw;
    }
    final base = ApiClient.baseUrl.trim();
    if (!base.endsWith('/')) return '$base$raw';
    return '$base${raw.startsWith('/') ? raw.substring(1) : raw}';
  }

  /// 统一补全资产内所有相对地址（模型文件 + 缩略图类字段）。
  static ModelAsset _resolveAssetUrls(ModelAsset asset) => ModelAsset(
        modelId: asset.modelId,
        name: asset.name,
        fileUrl: resolveUrl(asset.fileUrl),
        version: asset.version,
        contentHash: asset.contentHash,
        format: asset.format,
        parts: asset.parts,
        animations: asset.animations,
      );
}

/// 模型资源元数据。
class ModelAsset {
  final int modelId;
  final String name;
  final String fileUrl;
  final int version;
  final String contentHash;
  final String format;
  final List<PartInfo> parts;
  final List<AnimationInfo> animations;

  const ModelAsset({
    required this.modelId,
    required this.name,
    required this.fileUrl,
    this.version = 1,
    this.contentHash = '',
    this.format = 'glb',
    this.parts = const [],
    this.animations = const [],
  });

  /// 缓存文件名（不含目录）。
  String get cacheFilename =>
      'model_${modelId}_v${version}_${contentHash.isEmpty ? '0' : contentHash.substring(0, 8)}.$format';

  /// 文件本地路径（相对于 persistentDataPath）。
  String get cacheRelativePath => 'ForkliftCLI/Models/$cacheFilename';

  factory ModelAsset.fromJson(Map<String, dynamic> json) => ModelAsset(
        modelId: json['modelId'] as int? ?? 0,
        name: json['name'] as String? ?? '',
        fileUrl: json['fileUrl'] as String? ?? '',
        version: json['version'] as int? ?? 1,
        contentHash: json['contentHash'] as String? ?? '',
        format: json['format'] as String? ?? 'glb',
        parts: (json['parts'] as List<dynamic>? ?? [])
            .map((p) => PartInfo.fromJson(p as Map<String, dynamic>))
            .toList(),
        animations: (json['animations'] as List<dynamic>? ?? [])
            .map((a) => AnimationInfo.fromJson(a as Map<String, dynamic>))
            .toList(),
      );

  Map<String, dynamic> toJson() => {
        'modelId': modelId,
        'name': name,
        'fileUrl': fileUrl,
        'version': version,
        'contentHash': contentHash,
        'format': format,
        'parts': parts.map((p) => p.toJson()).toList(),
        'animations': animations.map((a) => a.toJson()).toList(),
      };
}

/// 零件信息。
class PartInfo {
  final String name;
  final String meshName;
  final String? partNumber;
  final String? oem;
  final String? group;
  final String? color;
  final bool isInteractive;

  const PartInfo({
    required this.name,
    required this.meshName,
    this.partNumber,
    this.oem,
    this.group,
    this.color,
    this.isInteractive = false,
  });

  factory PartInfo.fromJson(Map<String, dynamic> json) => PartInfo(
        name: json['name'] as String? ?? '',
        meshName: json['mesh_name'] as String? ?? json['name'] as String? ?? '',
        partNumber: json['part_number'] as String?,
        oem: json['oem'] as String?,
        group: json['group'] as String?,
        color: json['color'] as String?,
        isInteractive: json['is_interactive'] == 1,
      );

  Map<String, dynamic> toJson() => {
        'name': name,
        'meshName': meshName,
        'partNumber': partNumber,
        'oem': oem,
        'group': group,
        'color': color,
        'isInteractive': isInteractive,
      };
}

/// 动画信息。
class AnimationInfo {
  final String name;
  final String? displayName;
  final double? duration;

  const AnimationInfo({required this.name, this.displayName, this.duration});

  factory AnimationInfo.fromJson(Map<String, dynamic> json) => AnimationInfo(
        name: json['name'] as String? ?? '',
        displayName: json['display_name'] as String?,
        duration: (json['duration'] as num?)?.toDouble(),
      );

  Map<String, dynamic> toJson() => {
        'name': name,
        'displayName': displayName,
        'duration': duration,
      };
}

/// 模型资源异常。
class ModelAssetException implements Exception {
  final String message;
  final Object? cause;

  const ModelAssetException(this.message, {this.cause});

  @override
  String toString() => 'ModelAssetException: $message${cause != null ? ' cause: $cause' : ''}';
}
