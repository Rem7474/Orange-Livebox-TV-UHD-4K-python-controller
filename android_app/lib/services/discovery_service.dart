import 'dart:async';
import 'dart:convert';
import 'dart:developer' as developer;
import 'dart:io';
import 'package:http/http.dart' as http;
import 'network_permission_service.dart';

class DiscoveredDevice {
  final String ip;
  final String port;
  final String friendlyName;
  final String source;

  DiscoveredDevice({
    required this.ip,
    required this.port,
    required this.friendlyName,
    required this.source,
  });
}

class DiscoveryService {
  final http.Client _client;
  final NetworkPermissionService _permissionService;

  DiscoveryService({
    http.Client? client,
    NetworkPermissionService? permissionService,
  }) : _client = client ?? http.Client(),
       _permissionService = permissionService ?? NetworkPermissionService();

  static const List<String> dnsCandidates = [
    'livebox-tv.home',
    'decodeur-tv.home',
    'tv.home',
    'decodeurtv.home',
    'livebox-tv',
    'decodeur-tv',
    'tv',
    'orange-tv.home',
    'orangetv.home',
  ];

  /// Recherche tous les décodeurs joignables sur le réseau local, sans
  /// s'arrêter au premier trouvé, pour permettre à l'utilisateur de choisir
  /// s'il y en a plusieurs (foyer avec plusieurs décodeurs Orange).
  Future<List<DiscoveredDevice>> discover({
    void Function(String message, double progress)? onProgress,
  }) async {
    if (!await _permissionService.request()) {
      onProgress?.call(
        "Autorisation d'accès au réseau local refusée. Activez-la dans les paramètres de l'application.",
        1.0,
      );
      return [];
    }

    // Dédupliqué par IP : un même décodeur peut répondre à la fois à un nom
    // DNS et au scan de sous-réseau.
    final foundByIp = <String, DiscoveredDevice>{};
    void addDevice(DiscoveredDevice dev) =>
        foundByIp.putIfAbsent(dev.ip, () => dev);

    // 1. Recherche par noms d'hôtes DNS
    onProgress?.call("Recherche par noms d'hôtes DNS...", 0.1);
    for (var i = 0; i < dnsCandidates.length; i++) {
      final host = dnsCandidates[i];
      try {
        final addrs = await InternetAddress.lookup(
          host,
        ).timeout(const Duration(milliseconds: 600));
        for (final addr in addrs) {
          if (addr.type == InternetAddressType.IPv4) {
            final dev = await probeDevice(addr.address, source: "DNS '$host'");
            if (dev != null) {
              addDevice(dev);
              onProgress?.call(
                "Décodeur trouvé : ${dev.friendlyName} (${dev.ip})",
                0.1,
              );
            }
          }
        }
      } catch (_) {}
    }

    // 2. Détection du sous-réseau local via NetworkInterface
    onProgress?.call("Analyse des interfaces réseau locales...", 0.25);
    String? localSubnet;
    try {
      final interfaces = await NetworkInterface.list(
        type: InternetAddressType.IPv4,
        includeLoopback: false,
      );
      for (final iface in interfaces) {
        for (final addr in iface.addresses) {
          if (addr.address.startsWith('192.168.') ||
              addr.address.startsWith('10.') ||
              addr.address.startsWith('172.')) {
            final parts = addr.address.split('.');
            if (parts.length == 4) {
              localSubnet = '${parts[0]}.${parts[1]}.${parts[2]}';
              break;
            }
          }
        }
        if (localSubnet != null) break;
      }
    } catch (e) {
      developer.log(
        'Échec de la détection des interfaces réseau, repli sur 192.168.1.x',
        name: 'DiscoveryService',
        error: e,
      );
    }

    localSubnet ??= '192.168.1';

    // 3. Balayage du sous-réseau (1 à 254) par lots
    onProgress?.call("Scan du réseau $localSubnet.x sur le port 8080...", 0.35);

    // Prioriser les adresses usuelles du décodeur TV Orange (souvent 10 à 60)
    final priorityIps = <String>[];
    for (var i = 10; i <= 60; i++) {
      priorityIps.add('$localSubnet.$i');
    }
    final remainingIps = <String>[];
    for (var i = 1; i <= 254; i++) {
      final ip = '$localSubnet.$i';
      if (!priorityIps.contains(ip)) {
        remainingIps.add(ip);
      }
    }

    final allIps = [...priorityIps, ...remainingIps];
    const batchSize = 25;

    for (var i = 0; i < allIps.length; i += batchSize) {
      final end = (i + batchSize < allIps.length)
          ? i + batchSize
          : allIps.length;
      final batch = allIps.sublist(i, end);
      final progress = 0.35 + (0.6 * (i / allIps.length));
      onProgress?.call(
        "Scan de $localSubnet.${i + 1} à $localSubnet.$end...",
        progress,
      );

      final futures = batch.map((ip) => probeDevice(ip, source: 'Scan réseau'));
      final results = await Future.wait(futures);
      for (final dev in results) {
        if (dev != null) {
          addDevice(dev);
          onProgress?.call(
            "Décodeur trouvé : ${dev.friendlyName} (${dev.ip})",
            progress,
          );
        }
      }
    }

    final devices = foundByIp.values.toList()
      ..sort((a, b) => _compareIps(a.ip, b.ip));

    onProgress?.call(
      devices.isEmpty
          ? "Aucun décodeur TV détecté."
          : "${devices.length} décodeur(s) TV détecté(s).",
      1.0,
    );
    return devices;
  }

  Future<DiscoveredDevice?> probeDevice(
    String ip, {
    String source = 'Détection',
  }) async {
    try {
      // Test rapide de l'API Livebox opération 10
      final uri = Uri.parse('http://$ip:8080/remoteControl/cmd?operation=10');
      final response = await _client
          .get(uri)
          .timeout(const Duration(milliseconds: 750));
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body) as Map<String, dynamic>;
        final result = data['result'] as Map<String, dynamic>?;
        if (result != null &&
            (result['responseCode'] == '0' || result['message'] == 'ok')) {
          final resData = result['data'] as Map<String, dynamic>? ?? {};
          final friendlyName =
              resData['friendlyName']?.toString() ?? 'Décodeur TV Orange';
          return DiscoveredDevice(
            ip: ip,
            port: '8080',
            friendlyName: friendlyName,
            source: source,
          );
        }
      }
    } catch (_) {}
    return null;
  }
}

/// Compare deux adresses IPv4 numériquement (et non lexicographiquement),
/// pour que '...192.168.1.9' se trie bien avant '...192.168.1.10'.
int _compareIps(String a, String b) {
  final partsA = a.split('.').map(int.parse).toList();
  final partsB = b.split('.').map(int.parse).toList();
  for (var i = 0; i < partsA.length && i < partsB.length; i++) {
    final cmp = partsA[i].compareTo(partsB[i]);
    if (cmp != 0) return cmp;
  }
  return 0;
}
