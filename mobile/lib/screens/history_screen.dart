import 'package:flutter/material.dart';
import '../services/api_service.dart';

class HistoryScreen extends StatefulWidget {
  const HistoryScreen({super.key});

  @override
  State<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends State<HistoryScreen> with SingleTickerProviderStateMixin {
  late TabController _tabs;
  Map<String, dynamic>? _summary;
  List<dynamic> _crops = [];
  List<dynamic> _diseases = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _tabs = TabController(length: 4, vsync: this);
    _load();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    try {
      final api = ApiService();
      final results = await Future.wait([
        api.getHistorySummary(),
        api.getCropHistory(),
        api.getDiseaseHistory(),
      ]);
      setState(() {
        _summary = results[0] as Map<String, dynamic>;
        _crops = results[1] as List<dynamic>;
        _diseases = results[2] as List<dynamic>;
        _loading = false;
      });
    } catch (_) {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('History & Analytics'),
        backgroundColor: const Color(0xFF7C3AED),
        foregroundColor: Colors.white,
        bottom: TabBar(
          controller: _tabs,
          labelColor: Colors.white,
          tabs: const [
            Tab(text: 'Summary'),
            Tab(text: 'Crops'),
            Tab(text: 'Carbon'),
            Tab(text: 'Water'),
          ],
        ),
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : TabBarView(
              controller: _tabs,
              children: [
                _summaryTab(),
                _listTab(_crops, 'crop_name', 'status'),
                _carbonTab(),
                _waterTab(),
              ],
            ),
    );
  }

  Widget _summaryTab() {
    final s = _summary ?? {};
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        _statCard('Farms', '${s['total_farms'] ?? 0}', Icons.agriculture),
        _statCard('Area (acres)', '${s['total_area_acres'] ?? 0}', Icons.landscape),
        _statCard('Crop Records', '${s['crop_records'] ?? 0}', Icons.grass),
        _statCard('Sensor Readings', '${s['sensor_readings'] ?? 0}', Icons.sensors),
        _statCard('Disease Scans', '${s['disease_scans'] ?? 0}', Icons.biotech),
      ],
    );
  }

  Widget _carbonTab() {
    final c = (_summary?['carbon_footprint'] as Map?) ?? {};
    return Padding(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('Carbon Footprint', style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
          const SizedBox(height: 16),
          _statCard('Estimated CO₂ (kg)', '${c['estimated_kg_co2'] ?? '—'}', Icons.cloud_outlined),
          _statCard('Reduced CO₂ (kg)', '${c['reduced_kg_co2'] ?? '—'}', Icons.eco),
          _statCard('Trees equivalent', '${c['trees_equivalent'] ?? '—'}', Icons.park),
        ],
      ),
    );
  }

  Widget _waterTab() {
    final w = (_summary?['water_usage'] as Map?) ?? {};
    return Padding(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('Water Conservation', style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
          const SizedBox(height: 16),
          _statCard('Water saved (L)', '${w['estimated_saved_liters'] ?? '—'}', Icons.water_drop),
          _statCard('Irrigation efficiency', '${w['irrigation_efficiency_percent'] ?? '—'}%', Icons.percent),
        ],
      ),
    );
  }

  Widget _listTab(List<dynamic> items, String titleKey, String subKey) {
    if (items.isEmpty) return const Center(child: Text('No records yet'));
    return ListView.builder(
      itemCount: items.length,
      itemBuilder: (_, i) {
        final item = items[i];
        return ListTile(
          title: Text('${item[titleKey] ?? item['detected_disease'] ?? 'Record'}'),
          subtitle: Text('${item[subKey] ?? item['severity'] ?? ''}'),
        );
      },
    );
  }

  Widget _statCard(String title, String value, IconData icon) {
    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      child: ListTile(leading: Icon(icon, color: const Color(0xFF7C3AED)), title: Text(title), trailing: Text(value, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18))),
    );
  }
}
