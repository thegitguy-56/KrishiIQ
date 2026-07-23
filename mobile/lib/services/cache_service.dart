import 'dart:convert';
import 'package:hive_flutter/hive_flutter.dart';

class CacheService {
  static const _boxName = 'krishiiq_cache';
  static Box? _box;

  static Future<void> init() async {
    await Hive.initFlutter();
    _box = await Hive.openBox(_boxName);
  }

  static Future<void> saveAdvisoryCache(Map<String, dynamic> data) async {
    await _box?.put('advisory_cache', jsonEncode(data));
    await _box?.put('advisory_cached_at', DateTime.now().toIso8601String());
  }

  static Map<String, dynamic>? getAdvisoryCache() {
    final raw = _box?.get('advisory_cache');
    if (raw == null) return null;
    return jsonDecode(raw as String) as Map<String, dynamic>;
  }

  static bool hasFreshCache({Duration maxAge = const Duration(hours: 1)}) {
    final at = _box?.get('advisory_cached_at') as String?;
    if (at == null) return false;
    return DateTime.now().difference(DateTime.parse(at)) < maxAge;
  }
}
