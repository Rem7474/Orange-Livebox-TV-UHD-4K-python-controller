import 'dart:async';
import 'dart:convert';
import 'package:flutter/services.dart' show rootBundle;
import 'package:http/http.dart' as http;
import '../models/channel.dart';
import '../models/decoder_status.dart';
import '../models/remote_key.dart';
import 'storage_service.dart';

class LiveboxService {
  final StorageService storage;
  final http.Client _client;

  Map<String, String> _keys = {};
  Map<String, String> _epgIds = {};
  List<Channel> _allChannels = [];
  bool _isDataLoaded = false;

  LiveboxService({StorageService? storage, http.Client? client})
      : storage = storage ?? StorageService(),
        _client = client ?? http.Client();

  List<Channel> get allChannels => _allChannels;
  bool get isDataLoaded => _isDataLoaded;

  Future<void> init() async {
    if (_isDataLoaded) return;
    try {
      final keysStr = await rootBundle.loadString('assets/keys.json');
      final keysMap = jsonDecode(keysStr) as Map<String, dynamic>;
      _keys = keysMap.map((k, v) => MapEntry(k, v.toString()));
    } catch (_) {}

    try {
      final epgStr = await rootBundle.loadString('assets/epg_ids.json');
      final epgMap = jsonDecode(epgStr) as Map<String, dynamic>;
      _epgIds = epgMap.map((k, v) => MapEntry(k, v.toString()));

      // Construction de la liste des chaînes
      final favs = await storage.getFavorites();
      final Map<String, Channel> channelsByEpg = {};

      // 1. Ajouter les chaînes nommées
      epgMap.forEach((key, val) {
        final epgId = val.toString();
        final numVal = int.tryParse(key);
        if (numVal == null) {
          // C'est un nom (ex: TF1)
          channelsByEpg.putIfAbsent(
            epgId,
            () => Channel(
              name: key,
              epgId: epgId,
              isFavorite: favs.contains(epgId),
            ),
          );
        }
      });

      // 2. Associer les numéros de chaînes
      epgMap.forEach((key, val) {
        final epgId = val.toString();
        final numVal = int.tryParse(key);
        if (numVal != null && channelsByEpg.containsKey(epgId)) {
          final existing = channelsByEpg[epgId]!;
          channelsByEpg[epgId] = Channel(
            name: existing.name,
            number: numVal,
            epgId: epgId,
            isFavorite: favs.contains(epgId),
          );
        }
      });

      final list = channelsByEpg.values.toList();
      list.sort((a, b) {
        if (a.number != null && b.number != null) {
          return a.number!.compareTo(b.number!);
        } else if (a.number != null) {
          return -1;
        } else if (b.number != null) {
          return 1;
        }
        return a.name.compareTo(b.name);
      });

      _allChannels = list;
      _isDataLoaded = true;
    } catch (_) {}
  }

  Future<String> _getBaseUrl() async {
    final ip = await storage.getIp();
    final port = await storage.getPort();
    final cleanIp = ip.trim().replaceAll(RegExp(r'^https?://'), '');
    return 'http://$cleanIp:$port/remoteControl/cmd';
  }

  Future<bool> sendKey(RemoteKey key, {int mode = 0}) async {
    return sendKeyRaw(key.keyCode, mode: mode);
  }

  Future<bool> sendKeyRaw(String keyNameOrCode, {int mode = 0}) async {
    try {
      final baseUrl = await _getBaseUrl();
      final keyCode = _keys[keyNameOrCode] ?? keyNameOrCode;
      final uri = Uri.parse(baseUrl).replace(queryParameters: {
        'operation': '1',
        'key': keyCode,
        'mode': mode.toString(),
      });

      final response = await _client.get(uri).timeout(const Duration(seconds: 3));
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final res = data['result'];
        return res != null && (res['responseCode'] == '0' || res['message'] == 'ok');
      }
      return false;
    } catch (_) {
      return false;
    }
  }

  Future<bool> changeChannel(String epgId) async {
    try {
      final baseUrl = await _getBaseUrl();
      final targetEpg = _epgIds[epgId] ?? epgId;
      final uri = Uri.parse(baseUrl).replace(queryParameters: {
        'operation': '9',
        'epg_id': targetEpg,
        'uui': '1',
      });

      final response = await _client.get(uri).timeout(const Duration(seconds: 3));
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final res = data['result'];
        return res != null && (res['responseCode'] == '0' || res['message'] == 'ok');
      }
      return false;
    } catch (_) {
      return false;
    }
  }

  Future<DecoderStatus> getStatus() async {
    try {
      final baseUrl = await _getBaseUrl();
      final uri = Uri.parse(baseUrl).replace(queryParameters: {
        'operation': '10',
      });

      final response = await _client.get(uri).timeout(const Duration(seconds: 3));
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body) as Map<String, dynamic>;
        return DecoderStatus.fromJson(data);
      } else {
        return DecoderStatus.offline('Code HTTP ${response.statusCode}');
      }
    } catch (e) {
      return DecoderStatus.offline(e.toString());
    }
  }
}
