import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../providers/auth_provider.dart';
import '../services/api_service.dart';

class ProfileScreen extends ConsumerStatefulWidget {
  const ProfileScreen({super.key});

  @override
  ConsumerState<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends ConsumerState<ProfileScreen> {
  Map<String, dynamic>? _profile;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final p = await ApiService().getFarmerProfile();
      setState(() {
        _profile = p;
        _loading = false;
      });
    } catch (_) {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final auth = ref.watch(authProvider);
    final p = _profile;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Profile'),
        backgroundColor: const Color(0xFF16A34A),
        foregroundColor: Colors.white,
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.all(16),
              children: [
                CircleAvatar(
                  radius: 40,
                  backgroundColor: const Color(0xFF16A34A),
                  child: Text((p?['name'] ?? 'F')[0].toUpperCase(),
                      style:
                          const TextStyle(fontSize: 32, color: Colors.white)),
                ),
                const SizedBox(height: 12),
                Text(p?['name'] ?? 'Farmer',
                    style: const TextStyle(
                        fontSize: 22, fontWeight: FontWeight.bold),
                    textAlign: TextAlign.center),
                Text(p?['phone'] ?? '',
                    textAlign: TextAlign.center,
                    style: const TextStyle(color: Colors.grey)),
                const SizedBox(height: 24),
                _tile(Icons.language, 'Language', auth.language.toUpperCase(),
                    () => _pickLanguage()),
                _tile(Icons.map, 'District', p?['district'] ?? '—', null),
                _tile(Icons.badge, 'Soil Health Card',
                    p?['soil_health_card_id'] ?? 'Not linked', null),
                _tile(Icons.help_outline, 'Help & Support',
                    'Call agriculture helpline 1800-2345678', null),
                const Divider(height: 32),
                ListTile(
                  leading: const Icon(Icons.input, color: Color(0xFF16A34A)),
                  title: const Text('Input Farm Data'),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () => context.push('/farm-data'),
                ),
                ListTile(
                  leading: const Icon(Icons.logout, color: Colors.red),
                  title: const Text('Sign Out',
                      style: TextStyle(color: Colors.red)),
                  onTap: () async {
                    await ref.read(authProvider.notifier).logout();
                    if (context.mounted) context.go('/welcome');
                  },
                ),
              ],
            ),
    );
  }

  void _pickLanguage() {
    showModalBottomSheet(
      context: context,
      builder: (_) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(title: const Text('English'), onTap: () => _setLang('en')),
            ListTile(title: const Text('हिंदी'), onTap: () => _setLang('hi')),
            ListTile(title: const Text('தமிழ்'), onTap: () => _setLang('ta')),
          ],
        ),
      ),
    );
  }

  Future<void> _setLang(String lang) async {
    ref.read(authProvider.notifier).setLanguage(lang);
    try {
      await ApiService().updateFarmerProfile({'preferred_language': lang});
    } catch (_) {}
    if (mounted) Navigator.pop(context);
    setState(() {});
  }

  Widget _tile(IconData icon, String title, String sub, VoidCallback? onTap) {
    return ListTile(
      leading: Icon(icon, color: const Color(0xFF16A34A)),
      title: Text(title),
      subtitle: Text(sub),
      trailing: onTap != null ? const Icon(Icons.chevron_right) : null,
      onTap: onTap,
    );
  }
}
