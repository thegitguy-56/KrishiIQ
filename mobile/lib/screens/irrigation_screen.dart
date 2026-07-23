import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/farm_provider.dart';

class IrrigationScreen extends ConsumerStatefulWidget {
  const IrrigationScreen({super.key});

  @override
  ConsumerState<IrrigationScreen> createState() => _IrrigationScreenState();
}

class _IrrigationScreenState extends ConsumerState<IrrigationScreen> {
  String? _selectedFarmId;
  String? _selectedFarmName;

  @override
  Widget build(BuildContext context) {
    final farms = ref.watch(farmsProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Irrigation Schedule'),
        backgroundColor: const Color(0xFFD97706),
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () {
              ref.invalidate(farmsProvider);
              if (_selectedFarmId != null) {
                ref.invalidate(latestSensorProvider(_selectedFarmId!));
              }
            },
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () async {
          ref.invalidate(farmsProvider);
          if (_selectedFarmId != null) {
            ref.invalidate(latestSensorProvider(_selectedFarmId!));
          }
        },
        child: SingleChildScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              farms.when(
                data: (data) {
                  if (data.isEmpty) {
                    return const Text('No farms found');
                  }

                  return DropdownButtonFormField<String>(
                    value: _selectedFarmId,
                    hint: const Text('Select Farm'),
                    decoration: InputDecoration(
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                    ),
                    items: data
                        .map(
                          (f) => DropdownMenuItem<String>(
                            value: f['id'].toString(),
                            child: Text(f['name'] ?? 'Unnamed Farm'),
                          ),
                        )
                        .toList(),
                    onChanged: (v) {
                      final farm = data.firstWhere(
                        (f) => f['id'].toString() == v,
                      );

                      setState(() {
                        _selectedFarmId = v;
                        _selectedFarmName = farm['name'] ?? 'Farm';
                      });
                    },
                  );
                },
                loading: () => const LinearProgressIndicator(),
                error: (e, _) => Text('Could not load farms: $e'),
              ),

              const SizedBox(height: 20),

              if (_selectedFarmId == null)
                const Center(
                  child: Padding(
                    padding: EdgeInsets.only(top: 40),
                    child: Text(
                      'Please select a farm to view irrigation schedule',
                      style: TextStyle(color: Colors.grey),
                    ),
                  ),
                )
              else ...[
                Text(
                  _selectedFarmName ?? 'Selected Farm',
                  style: const TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 12),
                _IrrigationStatus(farmId: _selectedFarmId!),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

class _IrrigationStatus extends ConsumerWidget {
  final String farmId;

  const _IrrigationStatus({required this.farmId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final sensorAsync = ref.watch(latestSensorProvider(farmId));

    return sensorAsync.when(
      data: (data) {
        final moisture = data.latestReading?.soilMoisturePercent ?? 50.0;
        final needed = data.irrigationNeeded;

        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _statusCard(moisture, needed),
            const SizedBox(height: 20),
            const Text(
              'This Week\'s Schedule',
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
            ),
            const SizedBox(height: 12),
            ..._buildDynamicSchedule(moisture, needed),
          ],
        );
      },
      loading: () => const LinearProgressIndicator(),
      error: (e, _) => Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.red.shade50,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: Colors.red.shade200),
        ),
        child: Text(
          'Could not load sensor data: $e',
          style: const TextStyle(color: Colors.red),
        ),
      ),
    );
  }

  Widget _statusCard(double moisture, bool needed) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: needed ? const Color(0xFFFFF7ED) : const Color(0xFFF0FDF4),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(
          color: needed ? const Color(0xFFD97706) : const Color(0xFF16A34A),
        ),
      ),
      child: Row(
        children: [
          Icon(
            needed ? Icons.water_drop : Icons.check_circle,
            color: needed ? const Color(0xFFD97706) : const Color(0xFF16A34A),
            size: 28,
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  needed ? 'Irrigation Recommended' : 'Moisture Level OK',
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    color: needed
                        ? const Color(0xFFD97706)
                        : const Color(0xFF16A34A),
                  ),
                ),
                Text(
                  'Soil moisture: ${moisture.toStringAsFixed(1)}%',
                  style: const TextStyle(color: Colors.grey, fontSize: 13),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  List<Widget> _buildDynamicSchedule(double moisture, bool irrigationNeeded) {
    final now = DateTime.now();

    final int intervalDays;
    final String duration;

    if (moisture < 25) {
      intervalDays = 1;
      duration = '60 min';
    } else if (moisture < 40) {
      intervalDays = 2;
      duration = '45 min';
    } else {
      intervalDays = 3;
      duration = '30 min';
    }

    final schedule = List.generate(4, (i) {
      final date = now.add(Duration(days: i * intervalDays));

      return {
        'day': i == 0
            ? 'Today'
            : i == 1
                ? 'Next'
                : '${date.day}/${date.month}',
        'time': '06:00 AM',
        'duration': duration,
        'status': i == 0 && irrigationNeeded ? 'upcoming' : 'scheduled',
      };
    });

    return schedule.map((s) {
      final isUpcoming = s['status'] == 'upcoming';

      return Padding(
        padding: const EdgeInsets.only(bottom: 10),
        child: Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: isUpcoming ? const Color(0xFFF0FDF4) : Colors.white,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(
              color: isUpcoming ? const Color(0xFF16A34A) : Colors.grey[200]!,
            ),
          ),
          child: Row(
            children: [
              Icon(
                Icons.water,
                color: isUpcoming
                    ? const Color(0xFF16A34A)
                    : const Color(0xFF2563EB),
                size: 20,
              ),
              const SizedBox(width: 12),
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    s['day']!,
                    style: const TextStyle(fontWeight: FontWeight.bold),
                  ),
                  Text(
                    '${s['time']} · ${s['duration']}',
                    style: const TextStyle(color: Colors.grey, fontSize: 12),
                  ),
                ],
              ),
              const Spacer(),
              if (isUpcoming)
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: const Color(0xFF16A34A),
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: const Text(
                    'NEXT',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 11,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
            ],
          ),
        ),
      );
    }).toList();
  }
}