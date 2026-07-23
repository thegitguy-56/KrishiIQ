import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../services/api_service.dart';

class AuthState {
  final bool isAuthenticated;
  final String? userId;
  final String? role;
  final String language;
  final bool isLoading;
  final String? error;
  final bool onboardingComplete;

  const AuthState({
    this.isAuthenticated = false,
    this.userId,
    this.role,
    this.language = 'en',
    this.isLoading = false,
    this.error,
    this.onboardingComplete = false,
  });

  bool get isFarmer => role == 'farmer';

  AuthState copyWith({
    bool? isAuthenticated,
    String? userId,
    String? role,
    String? language,
    bool? isLoading,
    String? error,
    bool? onboardingComplete,
  }) => AuthState(
    isAuthenticated: isAuthenticated ?? this.isAuthenticated,
    userId: userId ?? this.userId,
    role: role ?? this.role,
    language: language ?? this.language,
    isLoading: isLoading ?? this.isLoading,
    error: error,
    onboardingComplete: onboardingComplete ?? this.onboardingComplete,
  );
}

class AuthNotifier extends StateNotifier<AuthState> {
  final _api = ApiService();
  final _storage = const FlutterSecureStorage();

  AuthNotifier() : super(const AuthState()) {
    _checkExistingSession();
  }

  Future<void> _checkExistingSession() async {
    final token = await _storage.read(key: 'access_token');
    final lang = await _storage.read(key: 'language') ?? 'en';
    final role = await _storage.read(key: 'role');
    final onboarded = await _storage.read(key: 'onboarding_complete') == 'true';
    if (token != null) {
      state = state.copyWith(
        isAuthenticated: true,
        role: role,
        language: lang,
        onboardingComplete: onboarded,
      );
    }
  }

  Future<Map<String, dynamic>> login(String phone, String password) async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final data = await _api.login(phone, password);
      final role = data['role'] as String?;
      if (role != 'farmer') {
        await _api.logout();
        state = state.copyWith(isLoading: false);
        throw Exception('Officers and admins must use the KrishiIQ web dashboard at localhost:5173');
      }
      await _storage.write(key: 'user_id', value: data['user_id']);
      await _storage.write(key: 'language', value: data['preferred_language'] ?? 'en');
      var onboarded = await _storage.read(key: 'onboarding_complete') == 'true';
      if (!onboarded) {
        try {
          final farms = await _api.getFarms();
          if (farms.isNotEmpty) {
            await completeOnboarding();
            onboarded = true;
          }
        } catch (_) {}
      }
      state = state.copyWith(
        isAuthenticated: true,
        userId: data['user_id'],
        role: role,
        language: data['preferred_language'] ?? 'en',
        isLoading: false,
        onboardingComplete: onboarded,
      );
      return data;
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
      rethrow;
    }
  }

  Future<void> register({
    required String phone,
    required String password,
    required String email,
    required String name,
    required String district,
    required String language,
  }) async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final data = await _api.register({
        'phone': phone,
        'password': password,
        'email': email,
        'name': name,
        'district': district,
        'state': 'Tamil Nadu', // TODO: Add state field in registration form
        'preferred_language': language,
        'role': 'farmer',
      });
      await _storage.write(key: 'language', value: language);
      state = state.copyWith(
        isAuthenticated: true,
        userId: data['user_id'],
        role: 'farmer',
        language: language,
        isLoading: false,
        onboardingComplete: false,
      );
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
      rethrow;
    }
  }

  Future<void> completeOnboarding() async {
    await _storage.write(key: 'onboarding_complete', value: 'true');
    state = state.copyWith(onboardingComplete: true);
  }

  Future<void> logout() async {
    await _api.logout();
    state = const AuthState();
  }

  void setLanguage(String lang) {
    _storage.write(key: 'language', value: lang);
    state = state.copyWith(language: lang);
  }
}

final authProvider = StateNotifierProvider<AuthNotifier, AuthState>(
  (ref) => AuthNotifier(),
);
