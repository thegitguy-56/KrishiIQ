import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/farm_provider.dart';
import '../services/api_service.dart';

class FarmDataInputScreen extends ConsumerStatefulWidget {
  const FarmDataInputScreen({super.key});

  @override
  ConsumerState<FarmDataInputScreen> createState() =>
      _FarmDataInputScreenState();
}

class _FarmDataInputScreenState extends ConsumerState<FarmDataInputScreen> {
  String _category = 'crop_history';
  final _crop = TextEditingController();
  final _yield = TextEditingController();
  final _fertilizer = TextEditingController();
  final _shc = TextEditingController();
  String? _farmId;
  bool _loading = false;

  @override
  void dispose() {
    _crop.dispose();
    _yield.dispose();
    _fertilizer.dispose();
    _shc.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    if (_farmId == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
            content: Text('Please select a farm profile first'),
            backgroundColor: Colors.orange),
      );
      return;
    }

    setState(() => _loading = true);
    try {
      if (_category == 'crop_history') {
        await ApiService().createCrop({
          'farm_id': _farmId,
          'crop_name': _crop.text.trim(),
          'season': 'kharif',
          'area_acres': 1.0,
          'actual_yield_kg': double.tryParse(_yield.text.trim()) ?? 0.0,
        });
      } else {
        await ApiService().updateFarmerProfile({
          'soil_health_card_id': _shc.text.trim(),
        });
      }

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
              content: Text('Data saved successfully!'),
              backgroundColor: Colors.green),
        );
        Navigator.pop(context);
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error: $e'), backgroundColor: Colors.red),
        );
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final farms = ref.watch(farmsProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Input Farm Data'),
        backgroundColor: const Color(0xFF16A34A),
        foregroundColor: Colors.white,
      ),
      body: farms.when(
        data: (data) {
          if (data.isEmpty) {
            return const Center(
              child: Padding(
                padding: EdgeInsets.all(16.0),
                child: Text(
                  'No farms found. Please complete the Farm Profile Setup first.',
                  textAlign: TextAlign.center,
                  style: TextStyle(fontSize: 16),
                ),
              ),
            );
          }

          // Automatically auto-select the first farm in the list if none chosen yet
          _farmId ??= data.first['id'].toString();

          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              // Farm Selector Dropdown
              DropdownButtonFormField<String>(
                value: _farmId,
                decoration: const InputDecoration(
                  labelText: 'Select Farm Profile',
                  border: OutlineInputBorder(),
                  prefixIcon: Icon(Icons.gite, color: Color(0xFF16A34A)),
                ),
                items: data.map<DropdownMenuItem<String>>((farm) {
                  return DropdownMenuItem<String>(
                    value: farm['id'].toString(),
                    child: Text(farm['name'] ?? 'Unnamed Farm'),
                  );
                }).toList(),
                onChanged: (value) {
                  setState(() => _farmId = value);
                },
              ),
              const SizedBox(height: 20),

              // Category Segmented Switch
              SegmentedButton<String>(
                segments: const [
                  ButtonSegment(
                      value: 'crop_history', label: Text('Crop History')),
                  ButtonSegment(
                      value: 'soil_health', label: Text('Soil Health Card')),
                ],
                selected: {_category},
                onSelectionChanged: (s) => setState(() => _category = s.first),
                style: SegmentedButton.styleFrom(
                  selectedBackgroundColor: const Color(0xFF16A34A),
                  selectedForegroundColor: Colors.white,
                ),
              ),
              const SizedBox(height: 20),

              // Form Input Switch Fields
              if (_category == 'crop_history') ...[
                TextField(
                  controller: _crop,
                  decoration: const InputDecoration(
                      labelText: 'Crop Name', border: OutlineInputBorder()),
                ),
                const SizedBox(height: 16),
                TextField(
                  controller: _yield,
                  keyboardType:
                      const TextInputType.numberWithOptions(decimal: true),
                  decoration: const InputDecoration(
                      labelText: 'Yield (kg)', border: OutlineInputBorder()),
                ),
                const SizedBox(height: 16),
                TextField(
                  controller: _fertilizer,
                  decoration: const InputDecoration(
                      labelText: 'Fertilizers Used',
                      border: OutlineInputBorder()),
                ),
              ] else ...[
                TextField(
                  controller: _shc,
                  decoration: const InputDecoration(
                      labelText: 'Soil Health Card ID',
                      border: OutlineInputBorder()),
                ),
              ],
              const SizedBox(height: 28),

              // Submission Button
              ElevatedButton(
                onPressed: _loading ? null : _save,
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF16A34A),
                  foregroundColor: Colors.white,
                  minimumSize: const Size.fromHeight(50),
                  shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(8)),
                ),
                child: _loading
                    ? const SizedBox(
                        height: 24,
                        width: 24,
                        child: CircularProgressIndicator(
                            color: Colors.white, strokeWidth: 2.5),
                      )
                    : const Text('Save Data',
                        style: TextStyle(
                            fontSize: 16, fontWeight: FontWeight.bold)),
              ),
            ],
          );
        },
        loading: () => const Center(
            child: CircularProgressIndicator(color: Color(0xFF16A34A))),
        error: (e, _) => Center(
            child: Text('Error loading farms: $e',
                style: const TextStyle(color: Colors.red))),
      ),
    );
  }
}
