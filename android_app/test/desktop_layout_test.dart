import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:mocktail/mocktail.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:android_app/main.dart';
import 'package:android_app/services/livebox_service.dart';
import 'package:android_app/services/network_permission_service.dart';
import 'package:android_app/services/storage_service.dart';

class MockNetworkPermissionService extends Mock
    implements NetworkPermissionService {}

void main() {
  testWidgets('Layout desktop affiche NavigationRail et 2 colonnes', (
    WidgetTester tester,
  ) async {
    tester.view.physicalSize = const Size(1280, 800);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(() {
      tester.view.resetPhysicalSize();
      tester.view.resetDevicePixelRatio();
    });

    SharedPreferences.setMockInitialValues({
      'livebox_ip': '192.168.1.15',
      'livebox_port': '8080',
    });

    final mockPerm = MockNetworkPermissionService();
    when(mockPerm.request).thenAnswer((_) async => false);
    when(mockPerm.isGranted).thenAnswer((_) async => false);

    final service = LiveboxService(
      storage: StorageService(),
      permissionService: mockPerm,
    );

    await tester.pumpWidget(
      ChangeNotifierProvider.value(value: service, child: const LiveboxApp()),
    );
    await tester.pumpAndSettle();

    expect(find.byType(NavigationRail), findsOneWidget);
    expect(find.byType(NavigationBar), findsNothing);
    expect(find.text('Power'), findsOneWidget);
    expect(find.text('Chaînes TV'), findsOneWidget);

    await tester.tap(find.text('Paramètres'));
    await tester.pumpAndSettle();

    expect(find.text('Paramètres & Réseau'), findsOneWidget);
  });

  testWidgets('Raccourci clavier desktop envoie la commande correspondante', (
    WidgetTester tester,
  ) async {
    tester.view.physicalSize = const Size(1280, 800);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(() {
      tester.view.resetPhysicalSize();
      tester.view.resetDevicePixelRatio();
    });

    SharedPreferences.setMockInitialValues({
      'livebox_ip': '192.168.1.15',
      'livebox_port': '8080',
    });

    final sentKeys = <String>[];
    final mockClient = MockClient((request) async {
      final op = request.url.queryParameters['operation'];
      if (op == '1') {
        sentKeys.add(request.url.queryParameters['key'] ?? '');
        return http.Response(
          jsonEncode({
            'result': {'responseCode': '0', 'message': 'ok'},
          }),
          200,
        );
      }
      return http.Response(
        jsonEncode({
          'result': {
            'responseCode': '0',
            'message': 'ok',
            'data': {'activeStandbyState': '0'},
          },
        }),
        200,
      );
    });

    final mockPerm = MockNetworkPermissionService();
    when(mockPerm.request).thenAnswer((_) async => true);
    when(mockPerm.isGranted).thenAnswer((_) async => true);

    final service = LiveboxService(
      storage: StorageService(),
      client: mockClient,
      permissionService: mockPerm,
    );

    await tester.pumpWidget(
      ChangeNotifierProvider.value(value: service, child: const LiveboxApp()),
    );
    await tester.pumpAndSettle();

    await tester.sendKeyEvent(LogicalKeyboardKey.arrowUp);
    await tester.pump();

    expect(sentKeys, contains('103'));
  });
}
