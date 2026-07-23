import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../services/api_service.dart';

class FarmMapScreen extends ConsumerStatefulWidget {
  const FarmMapScreen({super.key});

  @override
  ConsumerState<FarmMapScreen> createState() => _FarmMapScreenState();
}

class _FarmMapScreenState extends ConsumerState<FarmMapScreen> {
  List<dynamic> _farms = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final farms = await ApiService().getFarms();
      setState(() {
        _farms = farms;
        _loading = false;
      });
    } catch (_) {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final center = _farms.isNotEmpty
        ? LatLng(
            (_farms.first['latitude'] as num).toDouble(),
            (_farms.first['longitude'] as num).toDouble(),
          )
        : const LatLng(11.0168, 76.9558);

    return Scaffold(
      appBar: AppBar(
        title: const Text('My Farms Map'),
        backgroundColor: const Color(0xFF16A34A),
        foregroundColor: Colors.white,
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _farms.isEmpty
              ? const Center(child: Text('No farms registered yet'))
              : Column(
                  children: [
                    Expanded(
                      flex: 2,
                      child: FlutterMap(
                        options: MapOptions(initialCenter: center, initialZoom: 13),
                        children: [
                          TileLayer(
                            urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                            userAgentPackageName: 'com.krishiiq.app',
                          ),
                          MarkerLayer(
                            markers: _farms.map((f) {
                              final lat = (f['latitude'] as num).toDouble();
                              final lon = (f['longitude'] as num).toDouble();
                              return Marker(
                                point: LatLng(lat, lon),
                                width: 40,
                                height: 40,
                                child: const Icon(Icons.location_on, color: Color(0xFF16A34A), size: 36),
                              );
                            }).toList(),
                          ),
                        ],
                      ),
                    ),
                    Expanded(
                      child: ListView.builder(
                        padding: const EdgeInsets.all(12),
                        itemCount: _farms.length,
                        itemBuilder: (context, i) {
                          final f = _farms[i];
                          return Card(
                            child: ListTile(
                              leading: const Icon(Icons.agriculture, color: Color(0xFF16A34A)),
                              title: Text(f['name'] ?? 'Farm'),
                              subtitle: Text(
                                '${f['area_acres']} acres · ${f['district'] ?? ''}\n'
                                'Lat ${f['latitude']}, Lon ${f['longitude']}',
                              ),
                              isThreeLine: true,
                            ),
                          );
                        },
                      ),
                    ),
                  ],
                ),
    );
  }
}
