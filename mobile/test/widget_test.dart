import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:krishiiq/app.dart';

void main() {
  testWidgets('KrishiIQ app builds', (WidgetTester tester) async {
    await tester.pumpWidget(const ProviderScope(child: KrishiIQApp()));
    await tester.pump();
    expect(find.text('KrishiIQ'), findsNothing);
  });
}
