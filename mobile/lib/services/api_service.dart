import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../config/app_config.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

class ApiService {
  static final ApiService _instance = ApiService._internal();
  factory ApiService() => _instance;

  late final Dio _dio;
  final _storage = const FlutterSecureStorage();

  ApiService._internal() {
    _dio = Dio(BaseOptions(
      baseUrl: AppConfig.baseUrl,
      connectTimeout: const Duration(seconds: 15),
      receiveTimeout: const Duration(seconds: 30),
    ));

    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        final token = await _storage.read(key: 'access_token');
        if (token != null) options.headers['Authorization'] = 'Bearer $token';
        handler.next(options);
      },
      onError: (error, handler) async {
        debugPrint('API ERROR URL: ${error.requestOptions.uri}');
        debugPrint('API ERROR STATUS: ${error.response?.statusCode}');
        debugPrint('API ERROR DATA: ${error.response?.data}');

        handler.next(error);
      },
    ));
  }

  Future<bool> _refreshToken() async {
    try {
      final refresh = await _storage.read(key: 'refresh_token');
      if (refresh == null) return false;
      final response = await _dio
          .post('/auth/refresh', queryParameters: {'refresh_token': refresh});
      await _storage.write(
          key: 'access_token', value: response.data['access_token']);
      return true;
    } catch (_) {
      return false;
    }
  }

  Future<Map<String, dynamic>> register(Map<String, dynamic> data) async {
    final res = await _dio.post('/auth/register', data: data);
    await _saveTokens(res.data);
    return res.data;
  }

  Future<Map<String, dynamic>> login(String phone, String password) async {
    final res = await _dio
        .post('/auth/login', data: {'phone': phone, 'password': password});
    await _saveTokens(res.data);
    return res.data;
  }

  Future<void> _saveTokens(Map<String, dynamic> data) async {
    await _storage.write(key: 'access_token', value: data['access_token']);
    await _storage.write(key: 'refresh_token', value: data['refresh_token']);
    await _storage.write(key: 'user_id', value: data['user_id']);
    await _storage.write(key: 'role', value: data['role']);
  }

  Future<void> logout() async {
    await _storage.deleteAll();
  }

  Future<String?> getRole() => _storage.read(key: 'role');

  Future<Map<String, dynamic>> getPersonalizedAdvisory() async {
    final res = await _dio.get('/advisory/personalized');
    return res.data;
  }

  Future<List<dynamic>> getFarms() async {
    final res = await _dio.get(
      '/farms/',
      options: Options(
        headers: {
          'Cache-Control': 'no-cache',
          'Pragma': 'no-cache',
        },
      ),
    );

    debugPrint('FARMS FROM API: ${res.data}');
    return res.data;
  }

  Future<Map<String, dynamic>> createFarm(Map<String, dynamic> data) async {
    final res = await _dio.post('/farms/', data: data);
    return res.data;
  }

  Future<Map<String, dynamic>> getFarmerProfile() async {
    final res = await _dio.get('/farmers/me');
    return res.data;
  }

  Future<Map<String, dynamic>> updateFarmerProfile(
      Map<String, dynamic> data) async {
    final res = await _dio.patch('/farmers/me', data: data);
    return res.data;
  }

  Future<Map<String, dynamic>> getLatestSensor(String farmId) async {
    final res = await _dio.get('/sensors/farm/$farmId/latest');
    return res.data;
  }

  Future<List<dynamic>> getSensorHistory(String farmId,
      {int hours = 168}) async {
    final res = await _dio.get('/sensors/farm/$farmId/history',
        queryParameters: {'hours': hours});
    return res.data;
  }

  Future<void> registerSensor(String farmId, String deviceId) async {
    await _dio.post('/sensors/farm/$farmId/register-device',
        queryParameters: {'device_id': deviceId});
  }

  Future<Map<String, dynamic>> getWeather(double lat, double lon) async {
    final res = await _dio
        .get('/weather/forecast', queryParameters: {'lat': lat, 'lon': lon});
    return res.data;
  }

  Future<Map<String, dynamic>> detectDisease(
      String farmId, String imagePath) async {
    try {
      final formData = FormData.fromMap({
        'farm_id': farmId,
        'image': await MultipartFile.fromFile(
          imagePath,
          filename: imagePath.split('/').last,
        ),
      });

      final res = await _dio.post(
        '/disease/detect',
        data: formData,
        options: Options(
          contentType: 'multipart/form-data',
        ),
      );

      return Map<String, dynamic>.from(res.data);
    } on DioException catch (e) {
      throw Exception(
        e.response?.data?['detail'] ??
            e.response?.data.toString() ??
            e.message ??
            'Disease detection failed',
      );
    }
  }

  Future<void> markAdvisoryRead(String advisoryId) async {
    await _dio.patch('/advisory/$advisoryId/read');
  }

  Future<String> aiChat(
      String message, List<Map<String, String>> history) async {
    final res = await _dio
        .post('/ai/chat', data: {'message': message, 'history': history});
    return res.data['reply'] as String;
  }

  Future<Map<String, dynamic>> getHistorySummary() async {
    final res = await _dio.get('/history/summary');
    return res.data;
  }

  Future<List<dynamic>> getCropHistory() async {
    final res = await _dio.get('/history/crops');
    return res.data;
  }

  Future<List<dynamic>> getDiseaseHistory() async {
    final res = await _dio.get('/history/diseases');
    return res.data;
  }

  Future<Map<String, dynamic>> createCrop(Map<String, dynamic> data) async {
    final res = await _dio.post('/crops/', data: data);
    return res.data;
  }

  Future<Map<String, dynamic>> getPublicConfig() async {
    final res = await _dio.get('/ai/config/public');
    return res.data;
  }
}
