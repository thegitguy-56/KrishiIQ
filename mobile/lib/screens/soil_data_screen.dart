import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/farm_provider.dart';
import '../models/sensor_reading.dart';

class SoilDataScreen extends ConsumerStatefulWidget {
  const SoilDataScreen({super.key});

  @override
  ConsumerState<SoilDataScreen> createState() => _SoilDataScreenState();
}

class _SoilDataScreenState extends ConsumerState<SoilDataScreen> {
  String? _selectedFarmId;

  @override
  Widget build(BuildContext context) {
    final farms = ref.watch(farmsProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Soil Data & IoT Sensors'),
        backgroundColor: const Color(0xFF2563EB),
        foregroundColor: Colors.white,
      ),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            farms.when(
              data: (data) => DropdownButtonFormField<String>(
                value: _selectedFarmId,
                hint: const Text('Select Farm'),
                decoration: InputDecoration(border: OutlineInputBorder(borderRadius: BorderRadius.circular(12))),
                items: data.map((f) => DropdownMenuItem(value: f['id'].toString(), child: Text(f['name'] ?? ''))).toList(),
                onChanged: (v) => setState(() => _selectedFarmId = v),
              ),
              loading: () => const LinearProgressIndicator(),
              error: (_, __) => const Text('Could not load farms'),
            ),
            const SizedBox(height: 16),
            if (_selectedFarmId != null)
              Expanded(child: _SensorDataView(farmId: _selectedFarmId!))
            else
              const Expanded(
                child: Center(child: Text('Select a farm to view soil sensor data', style: TextStyle(color: Colors.grey))),
              ),
          ],
        ),
      ),
    );
  }
}

class _SensorDataView extends ConsumerWidget {
  final String farmId;
  const _SensorDataView({required this.farmId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final sensorAsync = ref.watch(latestSensorProvider(farmId));
    return sensorAsync.when(
      data: (data) => _SensorCards(data: data),
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (e, _) => Center(child: Text('Error: $e')),
    );
  }
}

class _SensorCards extends StatelessWidget {
  final LatestSensorData data;
  const _SensorCards({required this.data});

  @override
  Widget build(BuildContext context) {
    final r = data.latestReading;
    if (r == null) return const Center(child: Text('No sensor data available', style: TextStyle(color: Colors.grey)));

    final statusColor = data.soilHealthStatus == 'good' ? const Color(0xFF16A34A) : data.soilHealthStatus == 'moderate' ? const Color(0xFFD97706) : const Color(0xFFDC2626);

    return SingleChildScrollView(
      child: Column(
        children: [
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(color: statusColor.withOpacity(0.1), borderRadius: BorderRadius.circular(12), border: Border.all(color: statusColor.withOpacity(0.3))),
            child: Row(children: [
              Icon(Icons.circle, color: statusColor, size: 12),
              const SizedBox(width: 8),
              Text('Soil Health: ${data.soilHealthStatus.toUpperCase()}', style: TextStyle(color: statusColor, fontWeight: FontWeight.bold)),
              if (data.irrigationNeeded) ...[const Spacer(), const Icon(Icons.water_drop, color: Color(0xFF2563EB), size: 16), const SizedBox(width: 4), const Text('Irrigation needed', style: TextStyle(color: Color(0xFF2563EB), fontSize: 12, fontWeight: FontWeight.w600))],
            ]),
          ),
          if (data.npkAlert != null) ...[
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(color: const Color(0xFFFEF3C7), borderRadius: BorderRadius.circular(12)),
              child: Row(children: [
                const Icon(Icons.warning_amber, color: Color(0xFFD97706)),
                const SizedBox(width: 8),
                Text(data.npkAlert!, style: const TextStyle(color: Color(0xFFD97706), fontWeight: FontWeight.w500)),
              ]),
            ),
          ],
          const SizedBox(height: 16),
          GridView.count(
            crossAxisCount: 2, shrinkWrap: true, physics: const NeverScrollableScrollPhysics(),
            crossAxisSpacing: 12, mainAxisSpacing: 12, childAspectRatio: 1.5,
            children: [
              _GaugeCard('Moisture', '${r.soilMoisturePercent?.toStringAsFixed(1) ?? "--"}%', Icons.water_drop, const Color(0xFF2563EB), r.soilMoisturePercent, 100),
              _GaugeCard('Soil pH', r.soilPh?.toStringAsFixed(1) ?? "--", Icons.science, const Color(0xFF7C3AED), r.soilPh != null ? (r.soilPh! / 14) * 100 : null, 100),
              _GaugeCard('Nitrogen', '${r.nitrogenPpm?.toStringAsFixed(0) ?? "--"} ppm', Icons.eco, const Color(0xFF16A34A), r.nitrogenPpm, 200),
              _GaugeCard('Temperature', '${r.airTemperatureCelsius?.toStringAsFixed(1) ?? "--"}°C', Icons.thermostat, const Color(0xFFDC2626), r.airTemperatureCelsius != null ? (r.airTemperatureCelsius! / 50) * 100 : null, 100),
            ],
          ),
        ],
      ),
    );
  }
}

class _GaugeCard extends StatelessWidget {
  final String label;
  final String value;
  final IconData icon;
  final Color color;
  final double? percent;
  final double max;

  const _GaugeCard(this.label, this.value, this.icon, this.color, this.percent, this.max);

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(14), boxShadow: [BoxShadow(color: color.withOpacity(0.08), blurRadius: 8)]),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
        Row(children: [Icon(icon, color: color, size: 18), const SizedBox(width: 6), Text(label, style: TextStyle(color: color, fontSize: 12, fontWeight: FontWeight.w600))]),
        Text(value, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
        if (percent != null) LinearProgressIndicator(value: (percent! / max).clamp(0, 1), color: color, backgroundColor: color.withOpacity(0.1), borderRadius: BorderRadius.circular(4), minHeight: 6),
      ]),
    );
  }
}
