import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:mocktail/mocktail.dart';
import 'package:android_app/services/discovery_service.dart';
import 'package:android_app/services/network_permission_service.dart';

class MockNetworkPermissionService extends Mock
    implements NetworkPermissionService {}

void main() {
  group('DiscoveryService.probeDevice', () {
    test(
      'renvoie un DiscoveredDevice quand le décodeur répond correctement',
      () async {
        final mockClient = MockClient((request) async {
          expect(request.url.queryParameters['operation'], '10');
          return http.Response(
            '{"result": {"responseCode": "0", "message": "ok", "data": {"friendlyName": "Livebox Play TV"}}}',
            200,
          );
        });

        final service = DiscoveryService(client: mockClient);
        final device = await service.probeDevice('192.168.1.42');

        expect(device, isNotNull);
        expect(device!.ip, '192.168.1.42');
        expect(device.port, '8080');
        expect(device.friendlyName, 'Livebox Play TV');
      },
    );

    test(
      'renvoie null quand la réponse indique un échec (responseCode != 0)',
      () async {
        final mockClient = MockClient((request) async {
          return http.Response('{"result": {"responseCode": "1"}}', 200);
        });

        final service = DiscoveryService(client: mockClient);
        final device = await service.probeDevice('192.168.1.42');

        expect(device, isNull);
      },
    );

    test('renvoie null sur un code HTTP différent de 200', () async {
      final mockClient = MockClient((request) async {
        return http.Response('Not Found', 404);
      });

      final service = DiscoveryService(client: mockClient);
      final device = await service.probeDevice('192.168.1.42');

      expect(device, isNull);
    });

    test(
      'renvoie null quand la requête échoue (timeout/exception réseau)',
      () async {
        final mockClient = MockClient((request) async {
          throw Exception('host unreachable');
        });

        final service = DiscoveryService(client: mockClient);
        final device = await service.probeDevice('192.168.1.42');

        expect(device, isNull);
      },
    );
  });

  group('DiscoveryService.discover — permission refusée', () {
    test(
      'renvoie une liste vide immédiatement si la permission réseau local est refusée',
      () async {
        final mockPermissionService = MockNetworkPermissionService();
        when(mockPermissionService.request).thenAnswer((_) async => false);

        final mockClient = MockClient((request) async {
          fail('Aucune requête HTTP ne doit être envoyée sans permission.');
        });

        final service = DiscoveryService(
          client: mockClient,
          permissionService: mockPermissionService,
        );

        final messages = <String>[];
        final devices = await service.discover(
          onProgress: (msg, progress) => messages.add(msg),
        );

        expect(devices, isEmpty);
        expect(messages, isNotEmpty);
        expect(messages.last, contains('Autorisation'));
      },
    );
  });

  group('DiscoveryService.discover — agrégation multi-décodeurs', () {
    test('ne s\'arrête pas au premier décodeur trouvé et renvoie tous les '
        'décodeurs, triés numériquement par IP', () async {
      final mockClient = MockClient((request) async {
        final host = request.url.host;
        // Simule deux décodeurs qui répondent, sur des IP différentes du
        // même sous-réseau balayé en priorité (10 à 60).
        if (host.endsWith('.20') || host.endsWith('.15')) {
          return http.Response(
            '{"result": {"responseCode": "0", "message": "ok", '
            '"data": {"friendlyName": "Décodeur $host"}}}',
            200,
          );
        }
        return http.Response('Not Found', 404);
      });

      final service = DiscoveryService(client: mockClient);
      final devices = await service.discover();

      expect(devices.length, 2);
      expect(devices[0].ip, endsWith('.15'));
      expect(devices[1].ip, endsWith('.20'));
    }, timeout: const Timeout(Duration(seconds: 30)));
  });
}
