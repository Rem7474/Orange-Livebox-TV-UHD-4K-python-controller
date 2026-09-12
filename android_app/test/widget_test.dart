import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:android_app/main.dart';
import 'package:android_app/services/livebox_service.dart';
import 'package:android_app/services/storage_service.dart';

void main() {
  testWidgets('Vérification du chargement de LiveboxApp et de la navigation', (WidgetTester tester) async {
    SharedPreferences.setMockInitialValues({
      'livebox_ip': '192.168.1.15',
      'livebox_port': '8080',
    });

    final storage = StorageService();
    final service = LiveboxService(storage: storage);

    await tester.pumpWidget(LiveboxApp(service: service));
    await tester.pumpAndSettle();

    // Vérifier les 3 onglets de navigation
    expect(find.text('Télécommande'), findsOneWidget);
    expect(find.text('Chaînes'), findsOneWidget);
    expect(find.text('Paramètres'), findsOneWidget);

    // Vérifier la présence du bouton Power
    expect(find.text('Power'), findsOneWidget);
  });
}
