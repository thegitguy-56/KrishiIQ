import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../providers/auth_provider.dart';

class _Language {
  final String code;
  final String name;
  final String nativeName;
  final String flag;
  const _Language(this.code, this.name, this.nativeName, this.flag);
}

const _languages = [
  _Language('en', 'English', 'English', '🇬🇧'),
  _Language('hi', 'Hindi', 'हिन्दी', '🇮🇳'),
  _Language('ta', 'Tamil', 'தமிழ்', '🇮🇳'),
];

class LanguageSelectScreen extends ConsumerWidget {
  const LanguageSelectScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Scaffold(
      backgroundColor: const Color(0xFF15803D),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(height: 40),
              const Text('Welcome to', style: TextStyle(color: Colors.white70, fontSize: 18)),
              const Text('KrishiIQ', style: TextStyle(color: Colors.white, fontSize: 40, fontWeight: FontWeight.bold)),
              const SizedBox(height: 8),
              const Text('Select your language / अपनी भाषा चुनें / மொழியை தேர்ந்தெடுக்கவும்',
                style: TextStyle(color: Colors.white70, fontSize: 14)),
              const SizedBox(height: 48),
              ..._languages.map((lang) => Padding(
                padding: const EdgeInsets.only(bottom: 16),
                child: InkWell(
                  onTap: () {
                    ref.read(authProvider.notifier).setLanguage(lang.code);
                    context.go('/login');
                  },
                  borderRadius: BorderRadius.circular(16),
                  child: Container(
                    padding: const EdgeInsets.all(20),
                    decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.12),
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: Colors.white.withOpacity(0.2)),
                    ),
                    child: Row(
                      children: [
                        Text(lang.flag, style: const TextStyle(fontSize: 32)),
                        const SizedBox(width: 16),
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(lang.nativeName, style: const TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold)),
                            Text(lang.name, style: const TextStyle(color: Colors.white70, fontSize: 14)),
                          ],
                        ),
                        const Spacer(),
                        const Icon(Icons.arrow_forward_ios, color: Colors.white54, size: 16),
                      ],
                    ),
                  ),
                ),
              )),
            ],
          ),
        ),
      ),
    );
  }
}
