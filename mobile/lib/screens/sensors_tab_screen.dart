import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/farm_provider.dart';
import '../services/api_service.dart';
import 'soil_data_screen.dart';

class SensorsTabScreen extends ConsumerStatefulWidget {
  const SensorsTabScreen({super.key});

  @override
  ConsumerState<SensorsTabScreen> createState() => _SensorsTabScreenState();
}

class _SensorsTabScreenState extends ConsumerState<SensorsTabScreen> {
  String? _farmId;
  final _deviceId = TextEditingController();

  @override
  Widget build(BuildContext context) {
    final farms = ref.watch(farmsProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('IoT Sensors'),
        backgroundColor: const Color(0xFF2563EB),
        foregroundColor: Colors.white,
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: () => ref.invalidate(farmsProvider)),
        ],
      ),
      body: farms.when(
        data: (data) {
          if (data.isEmpty) {
            return const Center(child: Text('No farms — complete farm setup in Profile'));
          }
          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              ...data.map((f) {
                final hasSensor = f['has_iot_sensor'] == true;
                return Card(
                  margin: const EdgeInsets.only(bottom: 12),
                  child: ListTile(
                    leading: Icon(hasSensor ? Icons.sensors : Icons.sensors_off, color: hasSensor ? Colors.green : Colors.grey),
                    title: Text(f['name'] ?? 'Farm'),
                    subtitle: Text(hasSensor ? 'Device: ${f['sensor_device_id'] ?? 'paired'}' : 'No sensor paired'),
                    trailing: const Icon(Icons.chevron_right),
                    onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const SoilDataScreen())),
                  ),
                );
              }),
              const SizedBox(height: 16),
              const Text('Pair New Sensor', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
              const SizedBox(height: 8),
              DropdownButtonFormField<String>(
                value: _farmId ?? data.first['id'].toString(),
                items: data.map((f) => DropdownMenuItem(value: f['id'].toString(), child: Text(f['name']))).toList(),
                onChanged: (v) => setState(() => _farmId = v),
                decoration: const InputDecoration(border: OutlineInputBorder(), labelText: 'Select Farm'),
              ),
              const SizedBox(height: 8),
              TextField(
                controller: _deviceId,
                decoration: const InputDecoration(labelText: 'Sensor Device ID', border: OutlineInputBorder()),
              ),
              const SizedBox(height: 12),
              ElevatedButton.icon(
                onPressed: () async {
                  try {
                    await ApiService().registerSensor(_farmId ?? data.first['id'].toString(), _deviceId.text.trim().isEmpty ? 'SENSOR-001' : _deviceId.text.trim());
                    ref.invalidate(farmsProvider);
                    if (context.mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Sensor paired')));
                  } catch (e) {
                    if (context.mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('$e'), backgroundColor: Colors.red));
                  }
                },
                icon: const Icon(Icons.bluetooth_connected),
                label: const Text('Pair Sensor'),
                style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF2563EB), foregroundColor: Colors.white),
              ),
            ],
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('$e')),
      ),
    );
  }
}
