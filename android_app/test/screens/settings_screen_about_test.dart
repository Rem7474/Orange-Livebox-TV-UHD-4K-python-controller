import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:package_info_plus/package_info_plus.dart';
import 'package:plugin_platform_interface/plugin_platform_interface.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:url_launcher_platform_interface/link.dart';
import 'package:url_launcher_platform_interface/url_launcher_platform_interface.dart';
import 'package:android_app/screens/settings_screen.dart';
import 'package:android_app/services/livebox_service.dart';
import 'package:android_app/services/storage_service.dart';

class _FakeUrlLauncher extends UrlLauncherPlatform
    with MockPlatformInterfaceMixin {
  String? lastLaunchedUrl;

  @override
  LinkDelegate? get linkDelegate => null;

  @override
  Future<bool> canLaunch(String url) async => true;

  @override
  Future<bool> launchUrl(String url, LaunchOptions options) async {
    lastLaunchedUrl = url;
    return true;
  }
}

void main() {
  late _FakeUrlLauncher fakeLauncher;

  setUp(() {
    fakeLauncher = _FakeUrlLauncher();
    UrlLauncherPlatform.instance = fakeLauncher;
    PackageInfo.setMockInitialValues(
      appName: 'Télécommande TV Orange',
      packageName: 'fr.remcorp.remotetv',
      version: '1.0.0',
      buildNumber: '1',
      buildSignature: '',
    );
  });

  Future<void> pumpSettings(WidgetTester tester) async {
    SharedPreferences.setMockInitialValues({});
    final service = LiveboxService(storage: StorageService());
    await tester.pumpWidget(
      ChangeNotifierProvider.value(
        value: service,
        child: const MaterialApp(home: SettingsScreen()),
      ),
    );
    await tester.pumpAndSettle();
  }

  testWidgets('affiche la version de l\'app et l\'email de contact', (
    tester,
  ) async {
    await pumpSettings(tester);

    expect(find.textContaining('Version 1.0.0 (1)'), findsOneWidget);
    expect(find.textContaining('contact@remcorp.fr'), findsWidgets);
  });

  testWidgets('le bouton "Politique de confidentialité" ouvre la bonne URL', (
    tester,
  ) async {
    await pumpSettings(tester);

    final button = find.text('Politique de confidentialité');
    expect(button, findsOneWidget);

    await tester.ensureVisible(button);
    await tester.pumpAndSettle();
    await tester.tap(button);
    await tester.pumpAndSettle();

    expect(
      fakeLauncher.lastLaunchedUrl,
      'https://rem7474.github.io/Orange-Livebox-TV-UHD-4K-python-controller/privacy.html',
    );
  });
}
