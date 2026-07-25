// TEST-ONLY ENTRYPOINT — never used for real devices, TestFlight, or the
// Play Store. It exists solely so the mobile-tests Appium CI job can drive
// the app via appium-flutter-driver.
//
// It is built with:
//   flutter build apk --debug -t lib/main_test.dart
//
// The regular app is unaffected — lib/main.dart is untouched and does not
// import flutter_driver, so production bundles never ship this code path.
import 'package:flutter/material.dart';
import 'package:flutter_driver/driver_extension.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'app.dart';
import 'services/cache_service.dart';

void main() async {
  enableFlutterDriverExtension();
  WidgetsFlutterBinding.ensureInitialized();
  await CacheService.init();
  runApp(const ProviderScope(child: KrishiIQApp()));
}
