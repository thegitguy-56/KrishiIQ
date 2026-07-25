import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../providers/auth_provider.dart';
import '../providers/advisory_provider.dart';
import '../widgets/weather_card.dart';
import '../widgets/advisory_card.dart';

class HomeScreen extends ConsumerStatefulWidget {
  const HomeScreen({super.key});

  @override
  ConsumerState<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends ConsumerState<HomeScreen> {
  @override
  void initState() {
    super.initState();

    Future.microtask(() {
      ref.read(advisoryProvider.notifier).load();
    });
  }

  @override
  Widget build(BuildContext context) {
    final auth = ref.watch(authProvider);
    final advisory = ref.watch(advisoryProvider);

    return Scaffold(
      backgroundColor: const Color(0xFFF0FDF4),
      appBar: AppBar(
        backgroundColor: const Color(0xFF16A34A),
        foregroundColor: Colors.white,
        elevation: 0,
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Vanakkam, ${advisory.farmerName.isNotEmpty ? advisory.farmerName : "Farmer"}!',
              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            ),
            Text(
              auth.language == 'ta'
                  ? 'இன்று என்ன செய்வோம்?'
                  : 'What shall we do today?',
              style: const TextStyle(fontSize: 12, color: Colors.white70),
            ),
          ],
        ),
        actions: [
          IconButton(
            key: const ValueKey('home_notifications_button'),
            icon: const Icon(Icons.notifications_outlined),
            onPressed: () {},
          ),
          IconButton(
            key: const ValueKey('home_logout_button'),
            icon: const Icon(Icons.logout),
            onPressed: () {
              ref.read(authProvider.notifier).logout();
              context.go('/login');
            },
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () => ref.read(advisoryProvider.notifier).load(),
        child: SingleChildScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              WeatherCard(weather: advisory.weatherSummary),
              const SizedBox(height: 16),

              const Text(
                'Quick Actions',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 12),

              GridView.count(
                crossAxisCount: 2,
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                crossAxisSpacing: 12,
                mainAxisSpacing: 12,
                childAspectRatio: 1.35,
                children: [
                  _ActionTile(
                    icon: Icons.camera_alt_outlined,
                    label: 'Detect Disease',
                    color: const Color(0xFFEF4444),
                    onTap: () => context.push('/crop-health'),
                  ),
                  // _ActionTile(
                  //   icon: Icons.water_drop_outlined,
                  //   label: 'Soil Data',
                  //   color: const Color(0xFF2563EB),
                  //   onTap: () => context.push('/soil-data'),
                  // ),
                  _ActionTile(
                    icon: Icons.record_voice_over_outlined,
                    label: 'Advisory',
                    color: const Color(0xFF16A34A),
                    onTap: () => context.push('/advisory'),
                  ),
                  _ActionTile(
                    icon: Icons.schedule_outlined,
                    label: 'Irrigation',
                    color: const Color(0xFFD97706),
                    onTap: () => context.push('/irrigation'),
                  ),
                  _ActionTile(
                    icon: Icons.smart_toy_outlined,
                    label: 'AI Assistant',
                    color: const Color(0xFF7C3AED),
                    onTap: () => context.push('/ai-chat'),
                  ),
                  _ActionTile(
                    icon: Icons.map_outlined,
                    label: 'My Farms',
                    color: const Color(0xFF0891B2),
                    onTap: () => context.push('/farm-map'),
                  ),
                ],
              ),

              const SizedBox(height: 24),

              const Text(
                'Your Advisories',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 12),

              if (advisory.isLoading)
                const Center(child: CircularProgressIndicator())
              else if (advisory.advisories.isEmpty)
                Container(
                  padding: const EdgeInsets.all(24),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: const Center(
                    child: Text(
                      'No advisories yet',
                      style: TextStyle(color: Colors.grey),
                    ),
                  ),
                )
              else
                ...advisory.advisories.take(5).map(
                      (a) => Padding(
                        padding: const EdgeInsets.only(bottom: 12),
                        child: AdvisoryCard(
                          advisory: a,
                          language: auth.language,
                        ),
                      ),
                    ),
            ],
          ),
        ),
      ),
    );
  }
}

class _ActionTile extends StatelessWidget {
  final IconData icon;
  final String label;
  final Color color;
  final VoidCallback onTap;

  const _ActionTile({
    required this.icon,
    required this.label,
    required this.color,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(16),
      child: Container(
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(16),
          boxShadow: [
            BoxShadow(
              color: color.withOpacity(0.1),
              blurRadius: 8,
              offset: const Offset(0, 2),
            )
          ],
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, color: color, size: 32),
            const SizedBox(height: 8),
            Text(
              label,
              style: TextStyle(
                fontWeight: FontWeight.w600,
                color: color,
                fontSize: 13,
              ),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }
}