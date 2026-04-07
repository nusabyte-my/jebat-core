import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class ApiService {
  static final ApiService _instance = ApiService._internal();
  factory ApiService() => _instance;
  ApiService._internal();

  final Dio _dio = Dio(BaseOptions(
    baseUrl: 'https://jebat.online',
    connectTimeout: const Duration(seconds: 30),
    receiveTimeout: const Duration(seconds: 60),
  ));

  final _storage = const FlutterSecureStorage();

  Future<String> chat(String message, {String mode = 'deliberate'}) async {
    final response = await _dio.post(
      '/api/v1/chat/completions',
      data: {
        'message': message,
        'mode': mode,
      },
    );
    return response.data['response'] ?? response.data['choices']?[0]?['message']?['content'] ?? '';
  }

  Future<List<Map<String, dynamic>>> getMemories() async {
    final response = await _dio.get('/api/v1/memories');
    return List<Map<String, dynamic>>.from(response.data ?? []);
  }

  Future<Map<String, dynamic>> getStatus() async {
    final response = await _dio.get('/api/v1/status');
    return response.data ?? {};
  }

  Future<Map<String, dynamic>> healthCheck() async {
    final response = await _dio.get('/api/v1/health');
    return response.data ?? {};
  }
}
