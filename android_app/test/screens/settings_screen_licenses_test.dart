import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:android_app/screens/settings_screen.dart';
import 'package:android_app/services/livebox_service.dart';
import 'package:android_app/services/storage_service.dart';

void main() {
  testWidgets(
    'le bouton "Licences open source" ouvre la page de licences native',
    (tester) async {
      SharedPreferences.setMockInitialValues({});
      final service = LiveboxService(storage: StorageService());

      await tester.pumpWidget(
        ChangeNotifierProvider.value(
          value: service,
          child: const MaterialApp(home: SettingsScreen()),
        ),
      );
      await tester.pumpAndSettle();

      final licensesButton = find.text('Licences open source');
      expect(licensesButton, findsOneWidget);

      await tester.ensureVisible(licensesButton);
      await tester.pumpAndSettle();
      await tester.tap(licensesButton);
      await tester.pumpAndSettle();

      expect(find.byType(LicensePage), findsOneWidget);
      expect(find.text('Télécommande TV Orange'), findsWidgets);
    },
  );
}
