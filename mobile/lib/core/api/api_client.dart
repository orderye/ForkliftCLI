import 'package:dio/dio.dart';
import 'package:shared_preferences/shared_preferences.dart';

class ApiClient {
  static const String _baseUrl = 'http://localhost:8000';
  static const String _tokenKey = 'auth_token';

  late final Dio _dio;

  static final ApiClient _instance = ApiClient._internal();
  factory ApiClient() => _instance;

  ApiClient._internal() {
    _dio = Dio(BaseOptions(
      baseUrl: _baseUrl,
      connectTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 30),
      headers: {'Content-Type': 'application/json'},
    ));

    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        final prefs = await SharedPreferences.getInstance();
        final token = prefs.getString(_tokenKey);
        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        handler.next(options);
      },
      onError: (error, handler) {
        if (error.response?.statusCode == 401) {
          // Token过期，清除并跳转登录
          SharedPreferences.getInstance().then((prefs) {
            prefs.remove(_tokenKey);
          });
        }
        handler.next(error);
      },
    ));
  }

  Dio get dio => _dio;

  // ========== 认证 ==========
  Future<Map<String, dynamic>> register(String phone, String password, {String nickname = ''}) async {
    final response = await _dio.post('/api/v1/auth/register', data: {
      'phone': phone,
      'password': password,
      'nickname': nickname,
    });
    return response.data;
  }

  Future<Map<String, dynamic>> login(String phone, String password) async {
    final response = await _dio.post('/api/v1/auth/login', data: {
      'phone': phone,
      'password': password,
    });
    final data = response.data;
    if (data['access_token'] != null) {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(_tokenKey, data['access_token']);
    }
    return data;
  }

  Future<void> logout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_tokenKey);
  }

  Future<bool> isLoggedIn() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_tokenKey) != null;
  }

  // ========== 车型库 ==========
  Future<List<dynamic>> getBrands() async {
    final response = await _dio.get('/api/v1/forklifts/brands');
    return response.data;
  }

  Future<List<dynamic>> getSeries(int brandId) async {
    final response = await _dio.get('/api/v1/forklifts/brands/$brandId/series');
    return response.data;
  }

  Future<List<dynamic>> getModels(int seriesId) async {
    final response = await _dio.get('/api/v1/forklifts/series/$seriesId/models');
    return response.data;
  }

  Future<Map<String, dynamic>> getModelDetail(int modelId) async {
    final response = await _dio.get('/api/v1/forklifts/models/$modelId');
    return response.data;
  }

  Future<List<dynamic>> searchModels(String query) async {
    final response = await _dio.get('/api/v1/forklifts/search', queryParameters: {'q': query});
    return response.data;
  }

  // ========== 发动机 ==========
  Future<List<dynamic>> getEngineBrands() async {
    final response = await _dio.get('/api/v1/engines/brands');
    return response.data;
  }

  Future<List<dynamic>> getEngineModels(int brandId) async {
    final response = await _dio.get('/api/v1/engines/brands/$brandId/models');
    return response.data;
  }

  // ========== 配件 ==========
  Future<Map<String, dynamic>> searchParts(String query, {int page = 1}) async {
    final response = await _dio.get('/api/v1/parts/search', queryParameters: {
      'q': query,
      'page': page,
    });
    return response.data;
  }

  // ========== 结构图 ==========
  Future<List<dynamic>> getModelDiagrams(int modelId) async {
    final response = await _dio.get('/api/v1/diagrams/model/$modelId');
    return response.data;
  }

  Future<List<dynamic>> getEngineDiagrams(int engineModelId) async {
    final response = await _dio.get('/api/v1/diagrams/engine/$engineModelId');
    return response.data;
  }

  Future<List<dynamic>> getHotspots(int diagramId) async {
    final response = await _dio.get('/api/v1/diagrams/$diagramId/hotspots');
    return response.data;
  }

  // ========== AI ==========
  Future<Map<String, dynamic>> aiChat(String message, {int? forkliftModelId}) async {
    final response = await _dio.post('/api/v1/ai/chat', data: {
      'message': message,
      'forklift_model_id': forkliftModelId,
    });
    return response.data;
  }

  Future<Map<String, dynamic>> aiDiagnose(String symptom, {int? forkliftModelId}) async {
    final response = await _dio.post('/api/v1/ai/diagnose', data: {
      'symptom': symptom,
      'forklift_model_id': forkliftModelId,
    });
    return response.data;
  }

  // ========== 我的叉车 ==========
  Future<List<dynamic>> getMyForklifts() async {
    final response = await _dio.get('/api/v1/my-forklifts');
    return response.data;
  }

  Future<Map<String, dynamic>> addMyForklift(Map<String, dynamic> data) async {
    final response = await _dio.post('/api/v1/my-forklifts', data: data);
    return response.data;
  }

  Future<List<dynamic>> getMaintenanceRecords(int forkliftId) async {
    final response = await _dio.get('/api/v1/my-forklifts/$forkliftId/records');
    return response.data;
  }

  Future<Map<String, dynamic>> addMaintenanceRecord(int forkliftId, Map<String, dynamic> data) async {
    final response = await _dio.post('/api/v1/my-forklifts/$forkliftId/records', data: data);
    return response.data;
  }

  // ========== 多模态向量搜索 ==========
  Future<List<dynamic>> searchEmbed(String? queryText, {String? queryImageBase64, int topK = 5}) async {
    final response = await _dio.post('/api/v1/embed/search', data: {
      if (queryText != null) 'query_text': queryText,
      if (queryImageBase64 != null) 'query_image_base64': queryImageBase64,
      'top_k': topK,
    });
    return response.data['hits'];
  }
}
