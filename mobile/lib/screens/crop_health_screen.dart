import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';
import 'package:permission_handler/permission_handler.dart';

import '../services/api_service.dart';
import '../providers/farm_provider.dart';
import '../providers/auth_provider.dart';

class CropHealthScreen extends ConsumerStatefulWidget {
  const CropHealthScreen({super.key});

  @override
  ConsumerState<CropHealthScreen> createState() => _CropHealthScreenState();
}

class _CropHealthScreenState extends ConsumerState<CropHealthScreen> {
  File? _image;
  Map<String, dynamic>? _result;
  bool _loading = false;
  String? _selectedFarmId;

  @override
  void initState() {
    super.initState();
    Future.microtask(() {
      ref.invalidate(farmsProvider);
    });
  }

  Future<void> _pickImage(ImageSource source) async {
    try {
      if (source == ImageSource.camera) {
        final status = await Permission.camera.request();

        if (!status.isGranted) {
          if (mounted) {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(content: Text('Camera permission denied')),
            );
          }
          return;
        }
      }

      final picked = await ImagePicker().pickImage(
        source: source,
        imageQuality: 70,
        maxWidth: 1024,
        maxHeight: 1024,
      );

      if (picked != null && mounted) {
        setState(() {
          _image = File(picked.path);
          _result = null;
        });
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Image picker failed: $e')),
        );
      }
    }
  }

  Future<void> _detect() async {
    debugPrint('SELECTED FARM ID: $_selectedFarmId');
    debugPrint('IMAGE PATH: ${_image?.path}');

    if (_image == null || _selectedFarmId == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please select farm and image')),
      );
      return;
    }

    setState(() => _loading = true);

    try {
      final result = await ApiService().detectDisease(
        _selectedFarmId!,
        _image!.path,
      );

      if (mounted) {
        setState(() => _result = result);
      }
    } catch (e) {
      debugPrint('DETECTION ERROR: $e');

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Detection failed: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _loading = false);
      }
    }
  }

  Color _severityColor(String? severity) {
    switch (severity) {
      case 'critical':
        return const Color(0xFFDC2626);
      case 'high':
        return const Color(0xFFEA580C);
      case 'medium':
        return const Color(0xFFD97706);
      default:
        return const Color(0xFF16A34A);
    }
  }

  Widget _farmDropdown(List<dynamic> data) {
    debugPrint('SCREEN FARMS DATA: $data');

    if (data.isEmpty) {
      return const Text('No farms found. Please create a farm first.');
    }

    final validSelected = data.any(
      (f) => f['id'].toString() == _selectedFarmId,
    );

    if (!validSelected && _selectedFarmId != null) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (mounted) {
          setState(() => _selectedFarmId = null);
        }
      });
    }

    return DropdownButtonFormField<String>(
      key: const ValueKey('crop_health_farm_dropdown'),
      value: validSelected ? _selectedFarmId : null,
      hint: const Text('Select Farm'),
      isExpanded: true,
      decoration: InputDecoration(
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
        ),
      ),
      items: data.map((f) {
        final id = f['id'].toString();
        final name = f['name']?.toString() ?? 'Unnamed Farm';

        return DropdownMenuItem<String>(
          value: id,
          child: Text(
            '$name - $id',
            overflow: TextOverflow.ellipsis,
          ),
        );
      }).toList(),
      onChanged: (v) {
        debugPrint('DROPDOWN FARM ID: $v');
        setState(() {
          _selectedFarmId = v;
          _result = null;
        });
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final farms = ref.watch(farmsProvider);
    final lang = ref.watch(authProvider).language;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Crop Disease Detection'),
        backgroundColor: const Color(0xFF16A34A),
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () {
              ref.invalidate(farmsProvider);
              setState(() {
                _selectedFarmId = null;
                _image = null;
                _result = null;
              });
            },
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            farms.when(
              data: _farmDropdown,
              loading: () => const LinearProgressIndicator(),
              error: (err, _) => Text('Could not load farms: $err'),
            ),
            const SizedBox(height: 16),
            GestureDetector(
              key: const ValueKey('crop_health_image_picker_area'),
              onTap: _showImageSourceDialog,
              child: Container(
                width: double.infinity,
                height: 220,
                decoration: BoxDecoration(
                  color: Colors.grey[100],
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: Colors.grey[300]!),
                ),
                child: _image != null
                    ? ClipRRect(
                        borderRadius: BorderRadius.circular(16),
                        child: Image.file(_image!, fit: BoxFit.cover),
                      )
                    : const Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(
                            Icons.add_a_photo_outlined,
                            size: 48,
                            color: Colors.grey,
                          ),
                          SizedBox(height: 8),
                          Text(
                            'Tap to capture or upload crop image',
                            style: TextStyle(color: Colors.grey),
                          ),
                        ],
                      ),
              ),
            ),
            const SizedBox(height: 16),
            SizedBox(
              width: double.infinity,
              height: 52,
              child: ElevatedButton.icon(
                key: const ValueKey('crop_health_detect_button'),
                onPressed:
                    (_image != null && _selectedFarmId != null && !_loading)
                        ? _detect
                        : null,
                icon: _loading
                    ? const SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          color: Colors.white,
                        ),
                      )
                    : const Icon(Icons.search),
                label: Text(
                  _loading ? 'Analyzing…' : 'Detect Disease (EfficientNet AI)',
                ),
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF16A34A),
                  foregroundColor: Colors.white,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
              ),
            ),
            if (_result != null) ...[
              const SizedBox(height: 24),
              Container(
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(
                    color:
                        _severityColor(_result!['severity']).withOpacity(0.3),
                  ),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Expanded(
                          child: Text(
                            _result!['disease_name'] ?? 'Unknown',
                            style: const TextStyle(
                              fontSize: 20,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                        Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 10,
                            vertical: 4,
                          ),
                          decoration: BoxDecoration(
                            color: _severityColor(_result!['severity'])
                                .withOpacity(0.1),
                            borderRadius: BorderRadius.circular(20),
                          ),
                          child: Text(
                            (_result!['severity'] ?? '').toUpperCase(),
                            style: TextStyle(
                              color: _severityColor(_result!['severity']),
                              fontWeight: FontWeight.bold,
                              fontSize: 12,
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'Confidence: ${((_result!['confidence'] ?? 0) * 100).toStringAsFixed(1)}%',
                      style: const TextStyle(color: Colors.grey),
                    ),
                    const Divider(height: 24),
                    const Text(
                      'Treatment Recommendation:',
                      style: TextStyle(fontWeight: FontWeight.w600),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      lang == 'hi'
                          ? (_result!['treatment_hi'] ??
                              _result!['treatment_en'] ??
                              '')
                          : lang == 'ta'
                              ? (_result!['treatment_ta'] ??
                                  _result!['treatment_en'] ??
                                  '')
                              : (_result!['treatment_en'] ?? ''),
                      style: const TextStyle(height: 1.5),
                    ),
                  ],
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  void _showImageSourceDialog() {
    showModalBottomSheet(
      context: context,
      builder: (_) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(
              leading: const Icon(Icons.camera_alt),
              title: const Text('Camera'),
              onTap: () {
                Navigator.pop(context);
                _pickImage(ImageSource.camera);
              },
            ),
            ListTile(
              leading: const Icon(Icons.photo_library),
              title: const Text('Gallery'),
              onTap: () {
                Navigator.pop(context);
                _pickImage(ImageSource.gallery);
              },
            ),
          ],
        ),
      ),
    );
  }
}
