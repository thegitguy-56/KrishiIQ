import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:google_fonts/google_fonts.dart';
import 'screens/splash_screen.dart';
import 'screens/welcome_screen.dart';
import 'screens/register_screen.dart';
import 'screens/login_screen.dart';
import 'screens/farm_setup_screen.dart';
import 'screens/main_shell.dart';
import 'screens/crop_health_screen.dart';
import 'screens/irrigation_screen.dart';
import 'screens/ai_chat_screen.dart';
import 'screens/farm_map_screen.dart';
import 'screens/farm_data_input_screen.dart';
import 'screens/advisory_screen.dart';
import 'screens/soil_data_screen.dart';
final _router = GoRouter(
  initialLocation: '/',
  routes: [
    GoRoute(path: '/', builder: (_, __) => const SplashScreen()),
    GoRoute(path: '/welcome', builder: (_, __) => const WelcomeScreen()),
    GoRoute(path: '/register', builder: (_, __) => const RegisterScreen()),
    GoRoute(path: '/login', builder: (_, __) => const LoginScreen()),
    GoRoute(path: '/farm-setup', builder: (_, __) => const FarmSetupScreen()),
    GoRoute(path: '/main', builder: (_, __) => const MainShell()),
    GoRoute(path: '/crop-health', builder: (_, __) => const CropHealthScreen()),
    GoRoute(path: '/irrigation', builder: (_, __) => const IrrigationScreen()),
    GoRoute(path: '/ai-chat', builder: (_, __) => const AiChatScreen()),
    GoRoute(path: '/farm-map', builder: (_, __) => const FarmMapScreen()),
    GoRoute(path: '/farm-data', builder: (_, __) => const FarmDataInputScreen()),
    GoRoute(path: '/advisory',builder: (context, state) => const AdvisoryScreen()),
    GoRoute(path: '/soildata',builder: (_,__) => const SoilDataScreen()),
  ],
);

class KrishiIQApp extends ConsumerWidget {
  const KrishiIQApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return MaterialApp.router(
      title: 'KrishiIQ',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF16A34A)),
        useMaterial3: true,
        textTheme: GoogleFonts.notoSansTextTheme(),
        navigationBarTheme: const NavigationBarThemeData(
          indicatorColor: Color(0xFFD1FAE5),
          labelTextStyle: WidgetStatePropertyAll(TextStyle(fontSize: 11, fontWeight: FontWeight.w600)),
        ),
      ),
      routerConfig: _router,
    );
  }
}
