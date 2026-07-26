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

  void _showCropDetails(Map<String, dynamic> crop) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (_) => _CropPredictionSheet(crop: crop),
    );
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
                _listTab(_crops, 'crop_name', 'status', isCrop: true),
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

  Widget _listTab(List<dynamic> items, String titleKey, String subKey, {bool isCrop = false}) {
    if (items.isEmpty) return const Center(child: Text('No records yet'));
    return ListView.builder(
      itemCount: items.length,
      itemBuilder: (_, i) {
        final item = items[i];
        return ListTile(
          leading: Icon(isCrop ? Icons.grass : Icons.warning_amber, color: const Color(0xFF7C3AED)),
          title: Text('${item[titleKey] ?? item['detected_disease'] ?? 'Record'}'),
          subtitle: Text('${item[subKey] ?? item['severity'] ?? ''}'),
          trailing: isCrop ? const Icon(Icons.chevron_right) : null,
          onTap: isCrop ? () => _showCropDetails(item) : null,
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

class _CropPredictionSheet extends StatefulWidget {
  final Map<String, dynamic> crop;

  const _CropPredictionSheet({required this.crop});

  @override
  State<_CropPredictionSheet> createState() => _CropPredictionSheetState();
}

class _CropPredictionSheetState extends State<_CropPredictionSheet> {
  bool _loading = false;
  Map<String, dynamic>? _prediction;
  String? _error;

  Future<void> _predictYield() async {
    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      final cropId = widget.crop['id'].toString();
      final res = await ApiService().predictYield(cropId);
      setState(() => _prediction = res);
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              children: [
                const Icon(Icons.grass, color: Color(0xFF7C3AED), size: 32),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        widget.crop['crop_name'] ?? 'Crop',
                        style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                      ),
                      Text(
                        '${widget.crop['area_acres'] ?? 0} acres',
                        style: const TextStyle(color: Colors.grey),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 24),
            if (_prediction == null) ...[
              if (_error != null)
                Padding(
                  padding: const EdgeInsets.only(bottom: 16),
                  child: Text(_error!, style: const TextStyle(color: Colors.red)),
                ),
              ElevatedButton.icon(
                onPressed: _loading ? null : _predictYield,
                icon: _loading
                    ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                    : const Icon(Icons.analytics),
                label: Text(_loading ? 'Predicting...' : 'Predict Yield'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF7C3AED),
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                ),
              ),
            ] else ...[
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.purple.shade50,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: Colors.purple.shade100),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text('Prediction Results', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                          decoration: BoxDecoration(
                            color: _prediction!['prediction_method'] == 'ml_model' ? Colors.green.shade100 : Colors.orange.shade100,
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: Text(
                            _prediction!['prediction_method'] == 'ml_model' ? 'AI Prediction' : 'Estimated',
                            style: TextStyle(
                              fontSize: 12,
                              fontWeight: FontWeight.bold,
                              color: _prediction!['prediction_method'] == 'ml_model' ? Colors.green.shade700 : Colors.orange.shade700,
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),
                    Row(
                      children: [
                        Expanded(
                          child: _resultBox('Total Yield', '${(_prediction!['predicted_yield_kg'] as num).round()} kg'),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: _resultBox('Per Acre', '${(_prediction!['yield_per_acre_kg'] as num).round()} kg'),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    Text(
                      'Confidence: ${((_prediction!['confidence_percent'] as num) * 100).round()}%',
                      style: const TextStyle(color: Colors.grey, fontSize: 14),
                    ),
                    if ((_prediction!['limiting_factors'] as List?)?.isNotEmpty == true) ...[
                      const SizedBox(height: 12),
                      const Text('Limiting Factors:', style: TextStyle(fontWeight: FontWeight.w600, color: Colors.red)),
                      const SizedBox(height: 4),
                      ...(_prediction!['limiting_factors'] as List).map((f) => Text('• $f', style: const TextStyle(color: Colors.red, fontSize: 13))),
                    ],
                  ],
                ),
              ),
            ],
            const SizedBox(height: 16),
          ],
        ),
      ),
    );
  }

  Widget _resultBox(String label, String value) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.purple.shade100),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: const TextStyle(fontSize: 12, color: Colors.grey)),
          const SizedBox(height: 4),
          Text(value, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Color(0xFF7C3AED))),
        ],
      ),
    );
  }
}
