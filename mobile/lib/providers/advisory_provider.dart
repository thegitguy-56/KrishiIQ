import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../services/api_service.dart';
import '../services/cache_service.dart';
import '../models/advisory.dart';

class AdvisoryState {
  final List<Advisory> advisories;
  final Map<String, dynamic> weatherSummary;
  final Map<String, dynamic> soilSummary;
  final String farmerName;
  final bool isLoading;
  final String? error;
  final bool fromCache;

  const AdvisoryState({
    this.advisories = const [],
    this.weatherSummary = const {},
    this.soilSummary = const {},
    this.farmerName = '',
    this.isLoading = false,
    this.error,
    this.fromCache = false,
  });

  AdvisoryState copyWith({
    List<Advisory>? advisories,
    Map<String, dynamic>? weatherSummary,
    Map<String, dynamic>? soilSummary,
    String? farmerName,
    bool? isLoading,
    String? error,
    bool? fromCache,
  }) {
    return AdvisoryState(
      advisories: advisories ?? this.advisories,
      weatherSummary: weatherSummary ?? this.weatherSummary,
      soilSummary: soilSummary ?? this.soilSummary,
      farmerName: farmerName ?? this.farmerName,
      isLoading: isLoading ?? this.isLoading,
      error: error,
      fromCache: fromCache ?? this.fromCache,
    );
  }
}

class AdvisoryNotifier extends StateNotifier<AdvisoryState> {
  final ApiService _api = ApiService();

  AdvisoryNotifier() : super(const AdvisoryState()) {
    load();
  }

  Future<void> load() async {
    state = state.copyWith(
      isLoading: true,
      error: null,
    );

    try {
      final data = await _api.getPersonalizedAdvisory();

      await CacheService.saveAdvisoryCache(data);

      _applyData(data, fromCache: false);
    } catch (e) {
      final cached = CacheService.getAdvisoryCache();

      if (cached != null) {
        _applyData(cached, fromCache: true);
      } else {
        state = state.copyWith(
          isLoading: false,
          error: e.toString(),
        );
      }
    }
  }

  void _applyData(Map<String, dynamic> data, {required bool fromCache}) {
    final advisoryList = data['advisories'];

    final advisories = advisoryList is List
        ? advisoryList
            .map((a) => Advisory.fromJson(Map<String, dynamic>.from(a)))
            .toList()
        : <Advisory>[];

    state = AdvisoryState(
      advisories: advisories,
      weatherSummary: Map<String, dynamic>.from(data['weather_summary'] ?? {}),
      soilSummary: Map<String, dynamic>.from(data['soil_summary'] ?? {}),
      farmerName: data['farmer_name']?.toString() ?? '',
      isLoading: false,
      error: null,
      fromCache: fromCache,
    );
  }

  Future<void> markRead(String advisoryId) async {
    try {
      await _api.markAdvisoryRead(advisoryId);
    } catch (_) {}

    final updatedAdvisories = state.advisories.map((a) {
      if (a.id == advisoryId) {
        return Advisory(
          id: a.id,
          advisoryType: a.advisoryType,
          titleEn: a.titleEn,
          titleHi: a.titleHi,
          titleTa: a.titleTa,
          bodyEn: a.bodyEn,
          bodyHi: a.bodyHi,
          bodyTa: a.bodyTa,
          voiceUrlEn: a.voiceUrlEn,
          voiceUrlHi: a.voiceUrlHi,
          voiceUrlTa: a.voiceUrlTa,
          priority: a.priority,
          isRead: 'true',
          createdAt: a.createdAt,
        );
      }
      return a;
    }).toList();

    state = state.copyWith(
      advisories: updatedAdvisories,
      isLoading: false,
    );
  }
}

final advisoryProvider = StateNotifierProvider<AdvisoryNotifier, AdvisoryState>(
  (ref) => AdvisoryNotifier(),
);
