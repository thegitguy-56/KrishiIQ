import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../services/api_service.dart';
import '../models/sensor_reading.dart';

final farmsProvider = FutureProvider<List<dynamic>>((ref) async {
  final farms = await ApiService().getFarms();
  debugPrint('FARMS PROVIDER DATA: $farms');
  return farms;
});

final latestSensorProvider =
    FutureProvider.family<LatestSensorData, String>((ref, farmId) async {
  debugPrint('LATEST SENSOR FARM ID: $farmId');

  final data = await ApiService().getLatestSensor(farmId);

  debugPrint('LATEST SENSOR API DATA: $data');

  return LatestSensorData.fromJson(data);
});

final weatherProvider =
    FutureProvider.family<Map<String, dynamic>, (double, double)>(
        (ref, coords) async {
  final data = await ApiService().getWeather(coords.$1, coords.$2);
  debugPrint('WEATHER PROVIDER DATA: $data');
  return data;
});