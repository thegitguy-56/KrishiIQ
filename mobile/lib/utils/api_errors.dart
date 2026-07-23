import 'package:dio/dio.dart';

import '../config/app_config.dart';

String friendlyApiError(Object error) {
  if (error is DioException) {
    switch (error.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.sendTimeout:
      case DioExceptionType.receiveTimeout:
      case DioExceptionType.connectionError:
        return 'Cannot reach the server at ${AppConfig.baseUrl}.\n\n'
            '• Make sure the backend is running\n'
            '• Make sure ngrok is running: ngrok http 8001\n'
            '• Check your internet connection';
      default:
        final status = error.response?.statusCode;
        final detail = error.response?.data;
        if (status != null) return 'Server error ($status): $detail';
    }
  }
  return error.toString();
}