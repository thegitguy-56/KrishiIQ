import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:geolocator/geolocator.dart';
import '../services/api_service.dart';
import '../providers/auth_provider.dart';

class FarmSetupScreen extends ConsumerStatefulWidget {
  const FarmSetupScreen({super.key});

  @override
  ConsumerState<FarmSetupScreen> createState() => _FarmSetupScreenState();
}

class _FarmSetupScreenState extends ConsumerState<FarmSetupScreen> {
  final _name = TextEditingController(text: 'My Farm');
  final _area = TextEditingController(text: '2.0');
  final _crop = TextEditingController(text: 'Rice');
  final _soil = TextEditingController(text: 'black_cotton');
  double _lat = 11.0168;
  double _lon = 76.9558;
  String _district = 'Coimbatore';
  bool _loading = false;

  Future<void> _useGps() async {
    final perm = await Geolocator.requestPermission();
    if (perm == LocationPermission.denied) return;
    final pos = await Geolocator.getCurrentPosition();
    setState(() {
      _lat = pos.latitude;
      _lon = pos.longitude;
    });
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Location captured')));
    }
  }

  Future<void> _finish() async {
    setState(() => _loading = true);
    try {
      final farm = await ApiService().createFarm({
        'name': _name.text.trim(),
        'area_acres': double.tryParse(_area.text) ?? 2.0,
        'latitude': _lat,
        'longitude': _lon,
        'soil_type': _soil.text.trim(),
        'district': _district,
        'irrigation_source': 'Borewell',
      });
      await ApiService().createCrop({
        'farm_id': farm['id'],
        'crop_name': _crop.text.trim(),
        'season': 'kharif',
        'area_acres': double.tryParse(_area.text) ?? 2.0,
      });
      await ref.read(authProvider.notifier).completeOnboarding();
      if (mounted) context.go('/main');
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('$e'), backgroundColor: Colors.red));
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Farm Profile Setup'), backgroundColor: const Color(0xFF16A34A), foregroundColor: Colors.white),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          const Text('Set up your first farm to receive personalized AI advisories.', style: TextStyle(color: Colors.grey)),
          const SizedBox(height: 16),
          TextField(key: const ValueKey('farm_setup_name_field'), controller: _name, decoration: const InputDecoration(labelText: 'Farm Name', border: OutlineInputBorder())),
          const SizedBox(height: 12),
          TextField(key: const ValueKey('farm_setup_area_field'), controller: _area, keyboardType: TextInputType.number, decoration: const InputDecoration(labelText: 'Land Area (acres)', border: OutlineInputBorder())),
          const SizedBox(height: 12),
          TextField(key: const ValueKey('farm_setup_crop_field'), controller: _crop, decoration: const InputDecoration(labelText: 'Primary Crop', border: OutlineInputBorder())),
          const SizedBox(height: 12),
          TextField(key: const ValueKey('farm_setup_soil_field'), controller: _soil, decoration: const InputDecoration(labelText: 'Soil Type', border: OutlineInputBorder())),
          const SizedBox(height: 12),
          OutlinedButton.icon(
            key: const ValueKey('farm_setup_gps_button'),
            onPressed: _useGps,
            icon: const Icon(Icons.my_location),
            label: Text('Use GPS ($_lat, $_lon)'),
          ),
          const SizedBox(height: 24),
          ElevatedButton(
            key: const ValueKey('farm_setup_submit_button'),
            onPressed: _loading ? null : _finish,
            style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF16A34A), foregroundColor: Colors.white, minimumSize: const Size.fromHeight(52)),
            child: _loading ? const CircularProgressIndicator(color: Colors.white) : const Text('Complete Setup'),
          ),
        ],
      ),
    );
  }
}
