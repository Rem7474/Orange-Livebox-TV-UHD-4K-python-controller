import 'dart:convert';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:android_app/models/channel.dart';
import 'package:android_app/models/decoder_status.dart';
import 'package:android_app/models/remote_key.dart';
import 'package:android_app/services/livebox_service.dart';
import 'package:android_app/services/storage_service.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  group('Modèles de données', () {
    test('Channel displayName et JSON', () {
      final ch1 = Channel(name: 'TF1', number: 1, epgId: '192', isFavorite: true);
      expect(ch1.displayName, '1 - TF1');
      expect(ch1.isFavorite, true);

      final json = ch1.toJson();
      final ch2 = Channel.fromJson(json);
      expect(ch2.name, 'TF1');
      expect(ch2.number, 1);
      expect(ch2.epgId, '192');
      expect(ch2.isFavorite, true);

      final chNoNum = Channel(name: 'TEST', epgId: '999');
      expect(chNoNum.displayName, 'TEST');
    });

    test('DecoderStatus parsing en ligne et hors ligne', () {
      final mockData = {
        'result': {
          'responseCode': '0',
          'message': 'ok',
          'data': {
            'friendlyName': 'Livebox Play TV',
            'activeStandbyState': '0',
            'osdContext': 'LIVE',
            'playedMediaId': '192',
            'playedMediaType': 'LIVE',
            'macAddress': '00:11:22:33:44:55',
          }
        }
      };

      final status = DecoderStatus.fromJson(mockData);
      expect(status.isOnline, true);
      expect(status.isOn, true);
      expect(status.friendlyName, 'Livebox Play TV');
      expect(status.osdContext, 'LIVE');
      expect(status.playedMediaId, '192');

      final offline = DecoderStatus.offline('Erreur réseau');
      expect(offline.isOnline, false);
      expect(offline.isOn, false);
      expect(offline.errorMessage, 'Erreur réseau');
    });

    test('RemoteKey enum vérification des codes essentiels', () {
      expect(RemoteKey.power.keyCode, '116');
      expect(RemoteKey.ok.keyCode, '352');
      expect(RemoteKey.up.keyCode, '103');
      expect(RemoteKey.down.keyCode, '108');
      expect(RemoteKey.left.keyCode, '105');
      expect(RemoteKey.right.keyCode, '106');
      expect(RemoteKey.volUp.keyCode, '115');
      expect(RemoteKey.volDown.keyCode, '114');
      expect(RemoteKey.chUp.keyCode, '402');
      expect(RemoteKey.chDown.keyCode, '403');
    });
  });

  group('LiveboxService avec MockClient HTTP', () {
    late StorageService storage;

    setUp(() {
      SharedPreferences.setMockInitialValues({
        'livebox_ip': '192.168.1.50',
        'livebox_port': '8080',
        'livebox_favorites': ['192', '4'],
      });
      storage = StorageService();
    });

    test('sendKey envoie l\'opération 1 avec les bons paramètres', () async {
      final mockClient = MockClient((request) async {
        expect(request.url.host, '192.168.1.50');
        expect(request.url.port, 8080);
        expect(request.url.path, '/remoteControl/cmd');
        expect(request.url.queryParameters['operation'], '1');
        expect(request.url.queryParameters['key'], '116');
        expect(request.url.queryParameters['mode'], '0');

        return http.Response(
          jsonEncode({
            'result': {'responseCode': '0', 'message': 'ok'}
          }),
          200,
        );
      });

      final service = LiveboxService(storage: storage, client: mockClient);
      final success = await service.sendKey(RemoteKey.power);
      expect(success, true);
    });

    test('changeChannel envoie l\'opération 9 avec l\'epg_id', () async {
      final mockClient = MockClient((request) async {
        expect(request.url.queryParameters['operation'], '9');
        expect(request.url.queryParameters['epg_id'], '192');
        expect(request.url.queryParameters['uui'], '1');

        return http.Response(
          jsonEncode({
            'result': {'responseCode': '0', 'message': 'ok'}
          }),
          200,
        );
      });

      final service = LiveboxService(storage: storage, client: mockClient);
      final success = await service.changeChannel('192');
      expect(success, true);
    });

    test('getStatus récupère l\'état du décodeur (opération 10)', () async {
      final mockClient = MockClient((request) async {
        expect(request.url.queryParameters['operation'], '10');

        return http.Response(
          jsonEncode({
            'result': {
              'responseCode': '0',
              'message': 'ok',
              'data': {
                'friendlyName': 'Décodeur TV UHD',
                'activeStandbyState': '0',
                'osdContext': 'HOMEPAGE',
              }
            }
          }),
          200,
        );
      });

      final service = LiveboxService(storage: storage, client: mockClient);
      final status = await service.getStatus();
      expect(status.isOnline, true);
      expect(status.isOn, true);
      expect(status.friendlyName, 'Décodeur TV UHD');
      expect(status.osdContext, 'HOMEPAGE');
    });
  });
}
