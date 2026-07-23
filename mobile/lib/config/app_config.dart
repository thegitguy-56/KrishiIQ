import 'dart:io' show Platform;

import 'package:flutter/foundation.dart' show kIsWeb;

class AppConfig {
  // ── Local development backend URL ─────────────────────────────────────────
  // Android emulator → backend on same machine:
  static const String _localUrl = 'http://10.0.2.2:8001';

  // Flutter Web or Windows desktop (uncomment if needed):
  // static const String _localUrl = 'http://localhost:8001';

  // Physical Android/iOS device on the same WiFi (replace with your PC's IP):
  // static const String _localUrl = 'http://192.168.x.x:8001';

  // Production ngrok tunnel (update when you start a new ngrok session):
  // static const String _localUrl = 'https://your-ngrok-url.ngrok-free.app';
  // ──────────────────────────────────────────────────────────────────────────

  static String get baseUrl => '$_localUrl/api/v1';

  static const String appName = 'KrishiIQ';
  static const List<String> supportedLanguages = ['en', 'hi', 'ta'];
  static const int sensorRefreshSeconds = 30;
  static const int advisoryRefreshMinutes = 60;
}