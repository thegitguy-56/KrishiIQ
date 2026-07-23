import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_tts/flutter_tts.dart';

import '../providers/advisory_provider.dart';
import '../providers/auth_provider.dart';
import '../models/advisory.dart';

class AdvisoryScreen extends ConsumerStatefulWidget {
  const AdvisoryScreen({super.key});

  @override
  ConsumerState<AdvisoryScreen> createState() => _AdvisoryScreenState();
}

class _AdvisoryScreenState extends ConsumerState<AdvisoryScreen> {
  final FlutterTts _tts = FlutterTts();
  String? _speakingId;

  @override
  void initState() {
    super.initState();

    _tts.setCompletionHandler(() {
      if (mounted) {
        setState(() => _speakingId = null);
      }
    });

    _tts.setCancelHandler(() {
      if (mounted) {
        setState(() => _speakingId = null);
      }
    });

    _tts.setErrorHandler((message) {
      if (mounted) {
        setState(() => _speakingId = null);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('TTS error: $message')),
        );
      }
    });
  }

  Future<void> _speak(Advisory advisory, String lang) async {
    try {
      if (_speakingId == advisory.id) {
        await _tts.stop();
        setState(() => _speakingId = null);
        return;
      }

      await _tts.stop();

      setState(() => _speakingId = advisory.id);

      final languageCode = lang == 'hi'
          ? 'hi-IN'
          : lang == 'ta'
              ? 'ta-IN'
              : 'en-IN';

      await _tts.setLanguage(languageCode);
      await _tts.setSpeechRate(0.45);
      await _tts.setPitch(1.0);
      await _tts.speak(advisory.getBody(lang));
    } catch (e) {
      if (mounted) {
        setState(() => _speakingId = null);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Unable to play audio: $e')),
        );
      }
    }
  }

  @override
  void dispose() {
    _tts.stop();
    super.dispose();
  }

  Color _priorityColor(String priority) {
    switch (priority) {
      case 'urgent':
        return const Color(0xFFDC2626);
      case 'high':
        return const Color(0xFFEA580C);
      case 'normal':
        return const Color(0xFF2563EB);
      default:
        return Colors.grey;
    }
  }

  IconData _typeIcon(String type) {
    switch (type) {
      case 'irrigation':
        return Icons.water_drop;
      case 'fertilizer':
        return Icons.eco;
      case 'pest_control':
        return Icons.bug_report;
      case 'weather_alert':
        return Icons.cloud;
      case 'sowing':
        return Icons.grass;
      default:
        return Icons.info_outline;
    }
  }

  Future<void> _refresh() async {
    await ref.read(advisoryProvider.notifier).load();
  }

  @override
  Widget build(BuildContext context) {
    final advisoryState = ref.watch(advisoryProvider);
    final lang = ref.watch(authProvider).language;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Personalized Advisory'),
        backgroundColor: const Color(0xFF16A34A),
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _refresh,
          ),
        ],
      ),
      body: advisoryState.isLoading
          ? const Center(child: CircularProgressIndicator())
          : advisoryState.advisories.isEmpty
              ? const Center(
                  child: Text(
                    'No advisories yet. Check back later.',
                    style: TextStyle(color: Colors.grey),
                  ),
                )
              : RefreshIndicator(
                  onRefresh: _refresh,
                  child: ListView.separated(
                    padding: const EdgeInsets.all(16),
                    itemCount: advisoryState.advisories.length,
                    separatorBuilder: (_, __) => const SizedBox(height: 12),
                    itemBuilder: (context, i) {
                      final advisory = advisoryState.advisories[i];
                      final isSpeaking = _speakingId == advisory.id;
                      final isUnread = advisory.isRead == 'false';

                      return Container(
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(16),
                          border: Border.all(
                            color: isUnread
                                ? _priorityColor(advisory.priority)
                                    .withOpacity(0.3)
                                : Colors.grey.withOpacity(0.1),
                          ),
                          boxShadow: [
                            BoxShadow(
                              color: Colors.black.withOpacity(0.04),
                              blurRadius: 8,
                              offset: const Offset(0, 3),
                            ),
                          ],
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Padding(
                              padding:
                                  const EdgeInsets.fromLTRB(16, 16, 16, 0),
                              child: Row(
                                children: [
                                  Icon(
                                    _typeIcon(advisory.advisoryType),
                                    color: _priorityColor(advisory.priority),
                                    size: 20,
                                  ),
                                  const SizedBox(width: 8),
                                  Expanded(
                                    child: Text(
                                      advisory.getTitle(lang),
                                      style: TextStyle(
                                        fontWeight: FontWeight.bold,
                                        fontSize: 15,
                                        color: isUnread
                                            ? Colors.black
                                            : Colors.grey[600],
                                      ),
                                    ),
                                  ),
                                  Container(
                                    padding: const EdgeInsets.symmetric(
                                      horizontal: 8,
                                      vertical: 3,
                                    ),
                                    decoration: BoxDecoration(
                                      color: _priorityColor(advisory.priority)
                                          .withOpacity(0.1),
                                      borderRadius: BorderRadius.circular(20),
                                    ),
                                    child: Text(
                                      advisory.priority.toUpperCase(),
                                      style: TextStyle(
                                        fontSize: 10,
                                        fontWeight: FontWeight.bold,
                                        color:
                                            _priorityColor(advisory.priority),
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                            ),
                            Padding(
                              padding:
                                  const EdgeInsets.fromLTRB(16, 8, 16, 12),
                              child: Text(
                                advisory.getBody(lang),
                                style: TextStyle(
                                  color: Colors.grey[700],
                                  height: 1.5,
                                  fontSize: 14,
                                ),
                              ),
                            ),
                            Divider(height: 1, color: Colors.grey[100]),
                            Row(
                              children: [
                                IconButton(
                                  icon: Icon(
                                    isSpeaking
                                        ? Icons.stop_circle
                                        : Icons.volume_up_outlined,
                                    color: isSpeaking
                                        ? const Color(0xFFDC2626)
                                        : const Color(0xFF16A34A),
                                  ),
                                  onPressed: () => _speak(advisory, lang),
                                  tooltip: isSpeaking ? 'Stop' : 'Listen',
                                ),
                                const Spacer(),
                                if (isUnread)
                                  TextButton(
                                    onPressed: () {
                                      ref
                                          .read(advisoryProvider.notifier)
                                          .markRead(advisory.id);
                                    },
                                    child: const Text(
                                      'Mark Read',
                                      style: TextStyle(fontSize: 12),
                                    ),
                                  ),
                              ],
                            ),
                          ],
                        ),
                      );
                    },
                  ),
                ),
    );
  }
}