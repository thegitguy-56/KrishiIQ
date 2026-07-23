import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../providers/auth_provider.dart';
import '../utils/api_errors.dart';

class RegisterScreen extends ConsumerStatefulWidget {
  const RegisterScreen({super.key});

  @override
  ConsumerState<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends ConsumerState<RegisterScreen> {
  final _name = TextEditingController();
  final _email = TextEditingController();
  final _phone = TextEditingController();
  final _pass = TextEditingController();
  final _district = TextEditingController(text: 'Coimbatore');
  String _lang = 'en';
  bool _loading = false;

  Future<void> _register() async {
    final name = _name.text.trim();
    final email = _email.text.trim();
    final phone = _phone.text.trim();
    final district = _district.text.trim();

    if (name.isEmpty || email.isEmpty || phone.length < 10 || district.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please fill name, email, phone (10 digits), and district')),
      );
      return;
    }
    if (!_email.text.contains('@')) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Enter a valid email address')));
      return;
    }
    if (_pass.text.length < 6) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Password must be at least 6 characters')));
      return;
    }

    setState(() => _loading = true);
    try {
      await ref.read(authProvider.notifier).register(
            phone: phone,
            password: _pass.text,
            email: email,
            name: name,
            district: district,
            language: _lang,
          );
      if (!mounted) return;
      context.go('/farm-setup');
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(friendlyApiError(e)),
            backgroundColor: Colors.red,
            duration: const Duration(seconds: 6),
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Create Account'),
        backgroundColor: const Color(0xFF16A34A),
        foregroundColor: Colors.white,
      ),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          TextField(controller: _name, decoration: _dec('Full Name', Icons.person)),
          const SizedBox(height: 12),
          TextField(
            controller: _email,
            keyboardType: TextInputType.emailAddress,
            decoration: _dec('Email', Icons.email_outlined),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _phone,
            keyboardType: TextInputType.phone,
            decoration: _dec('Mobile Number', Icons.phone),
          ),
          const SizedBox(height: 12),
          TextField(controller: _pass, obscureText: true, decoration: _dec('Password', Icons.lock)),
          const SizedBox(height: 12),
          TextField(controller: _district, decoration: _dec('District', Icons.map)),
          const SizedBox(height: 16),
          const Text('Preferred Language', style: TextStyle(fontWeight: FontWeight.w600)),
          SegmentedButton<String>(
            segments: const [
              ButtonSegment(value: 'en', label: Text('English')),
              ButtonSegment(value: 'hi', label: Text('हिंदी')),
              ButtonSegment(value: 'ta', label: Text('தமிழ்')),
            ],
            selected: {_lang},
            onSelectionChanged: (s) => setState(() => _lang = s.first),
          ),
          const SizedBox(height: 28),
          SizedBox(
            height: 52,
            child: ElevatedButton(
              onPressed: _loading ? null : _register,
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF16A34A),
                foregroundColor: Colors.white,
              ),
              child: _loading
                  ? const CircularProgressIndicator(color: Colors.white)
                  : const Text('Create Account'),
            ),
          ),
        ],
      ),
    );
  }

  InputDecoration _dec(String label, IconData icon) => InputDecoration(
        labelText: label,
        prefixIcon: Icon(icon),
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
      );
}
