class SensorReading {
  final String id;
  final String farmId;
  final double? soilMoisturePercent;
  final double? soilTemperatureCelsius;
  final double? soilPh;
  final double? nitrogenPpm;
  final double? phosphorusPpm;
  final double? potassiumPpm;
  final double? airTemperatureCelsius;
  final double? airHumidityPercent;
  final String recordedAt;

  const SensorReading({
    required this.id,
    required this.farmId,
    required this.recordedAt,
    this.soilMoisturePercent,
    this.soilTemperatureCelsius,
    this.soilPh,
    this.nitrogenPpm,
    this.phosphorusPpm,
    this.potassiumPpm,
    this.airTemperatureCelsius,
    this.airHumidityPercent,
  });

  factory SensorReading.fromJson(Map<String, dynamic> json) {
    return SensorReading(
      id: json['id']?.toString() ?? '',
      farmId: json['farm_id']?.toString() ?? '',
      soilMoisturePercent: (json['soil_moisture_percent'] as num?)?.toDouble(),
      soilTemperatureCelsius: (json['soil_temperature_celsius'] as num?)?.toDouble(),
      soilPh: (json['soil_ph'] as num?)?.toDouble(),
      nitrogenPpm: (json['nitrogen_ppm'] as num?)?.toDouble(),
      phosphorusPpm: (json['phosphorus_ppm'] as num?)?.toDouble(),
      potassiumPpm: (json['potassium_ppm'] as num?)?.toDouble(),
      airTemperatureCelsius: (json['air_temperature_celsius'] as num?)?.toDouble(),
      airHumidityPercent: (json['air_humidity_percent'] as num?)?.toDouble(),
      recordedAt: json['recorded_at']?.toString() ?? '',
    );
  }
}

class LatestSensorData {
  final String farmId;
  final SensorReading? latestReading;
  final String soilHealthStatus;
  final bool irrigationNeeded;
  final String? npkAlert;

  const LatestSensorData({
    required this.farmId,
    required this.soilHealthStatus,
    required this.irrigationNeeded,
    this.latestReading,
    this.npkAlert,
  });

  factory LatestSensorData.fromJson(Map<String, dynamic> json) {
    return LatestSensorData(
      farmId: json['farm_id']?.toString() ?? '',
      latestReading: json['latest_reading'] != null
          ? SensorReading.fromJson(json['latest_reading'] as Map<String, dynamic>)
          : null,
      soilHealthStatus: json['soil_health_status']?.toString() ?? 'unknown',
      irrigationNeeded: json['irrigation_needed'] == true,
      npkAlert: json['npk_alert']?.toString(),
    );
  }
}
