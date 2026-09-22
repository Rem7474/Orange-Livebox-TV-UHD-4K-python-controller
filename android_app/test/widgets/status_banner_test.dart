import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:android_app/models/decoder_status.dart';
import 'package:android_app/widgets/status_banner.dart';

void main() {
  Future<void> pumpBanner(
    WidgetTester tester, {
    required DecoderStatus? status,
    bool isLoading = false,
    VoidCallback? onRefresh,
  }) async {
    await tester.pumpWidget(
      MaterialApp(
        theme: ThemeData(brightness: Brightness.dark),
        home: Scaffold(
          body: StatusBanner(
            status: status,
            isLoading: isLoading,
            onRefresh: onRefresh ?? () {},
          ),
        ),
      ),
    );
  }

  testWidgets('statut null affiche "Déconnecté"', (tester) async {
    await pumpBanner(tester, status: null);

    expect(find.text('Déconnecté'), findsOneWidget);
    expect(find.text('Décodeur TV Orange'), findsOneWidget);
  });

  testWidgets('statut hors ligne affiche "Déconnecté" et le nom déconnecté', (
    tester,
  ) async {
    await pumpBanner(tester, status: DecoderStatus.offline('Erreur réseau'));

    expect(find.text('Déconnecté'), findsOneWidget);
    expect(find.text('Décodeur déconnecté'), findsOneWidget);
  });

  testWidgets('statut allumé affiche "Allumé (contexte)"', (tester) async {
    final status = DecoderStatus.fromJson({
      'result': {
        'data': {
          'friendlyName': 'Livebox Play TV',
          'activeStandbyState': '0',
          'osdContext': 'LIVE',
        },
      },
    });

    await pumpBanner(tester, status: status);

    expect(find.text('Allumé (LIVE)'), findsOneWidget);
    expect(find.text('Livebox Play TV'), findsOneWidget);
  });

  testWidgets('statut en veille affiche "En veille"', (tester) async {
    final status = DecoderStatus.fromJson({
      'result': {
        'data': {'friendlyName': 'Livebox Play TV', 'activeStandbyState': '1'},
      },
    });

    await pumpBanner(tester, status: status);

    expect(find.text('En veille'), findsOneWidget);
  });

  testWidgets('isLoading affiche un indicateur et masque le bouton refresh', (
    tester,
  ) async {
    await pumpBanner(tester, status: null, isLoading: true);

    expect(find.byType(CircularProgressIndicator), findsOneWidget);
    expect(find.byIcon(Icons.refresh), findsNothing);

    final button = tester.widget<IconButton>(find.byType(IconButton));
    expect(button.onPressed, isNull);
  });

  testWidgets('tap sur le bouton refresh déclenche le callback', (
    tester,
  ) async {
    var refreshCount = 0;
    await pumpBanner(tester, status: null, onRefresh: () => refreshCount++);

    await tester.tap(find.byIcon(Icons.refresh));
    await tester.pump();

    expect(refreshCount, 1);
  });
}
