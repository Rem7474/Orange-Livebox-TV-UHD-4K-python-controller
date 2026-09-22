import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:provider/provider.dart';
import '../models/decoder_status.dart';
import '../services/discovery_service.dart';
import '../services/livebox_service.dart';
import '../services/network_permission_service.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  final TextEditingController _ipController = TextEditingController();
  final TextEditingController _portController = TextEditingController();

  final DiscoveryService _discoveryService = DiscoveryService();
  final NetworkPermissionService _permissionService =
      NetworkPermissionService();

  late final LiveboxService _service;

  bool _isScanning = false;
  String _scanStatusMessage = '';
  double _scanProgress = 0.0;
  List<DiscoveredDevice> _foundDevices = [];
  bool _scanPermissionDenied = false;

  bool _isTesting = false;
  DecoderStatus? _testResult;

  @override
  void initState() {
    super.initState();
    _service = context.read<LiveboxService>();
    _loadCurrentSettings();
  }

  @override
  void dispose() {
    _ipController.dispose();
    _portController.dispose();
    super.dispose();
  }

  Future<void> _loadCurrentSettings() async {
    final ip = await _service.storage.getIp();
    final port = await _service.storage.getPort();
    if (mounted) {
      setState(() {
        _ipController.text = ip;
        _portController.text = port;
      });
    }
  }

  Future<void> _saveSettings({bool showSnackbar = true}) async {
    unawaited(HapticFeedback.selectionClick());
    final ip = _ipController.text.trim();
    final port = _portController.text.trim();
    if (ip.isEmpty) return;

    await _service.storage.setIp(ip);
    await _service.storage.setPort(port.isEmpty ? '8080' : port);

    if (mounted && showSnackbar) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Configuration réseau sauvegardée !'),
          backgroundColor: Color(0xFF2E7D32),
          duration: Duration(seconds: 2),
        ),
      );
    }
  }

  Future<void> _startDiscovery() async {
    if (_isScanning) return;
    setState(() {
      _isScanning = true;
      _scanProgress = 0.0;
      _scanStatusMessage = 'Démarrage du scan...';
      _foundDevices = [];
      _scanPermissionDenied = false;
    });

    final devices = await _discoveryService.discover(
      onProgress: (msg, prog) {
        if (mounted) {
          setState(() {
            _scanStatusMessage = msg;
            _scanProgress = prog;
          });
        }
      },
    );

    final permissionDenied =
        devices.isEmpty && !await _permissionService.isGranted();

    if (mounted) {
      setState(() {
        _isScanning = false;
        _foundDevices = devices;
        _scanPermissionDenied = permissionDenied;
      });

      // Un seul décodeur trouvé : on le configure directement, comme avant.
      // S'il y en a plusieurs, l'utilisateur choisit dans la liste affichée.
      if (devices.length == 1) {
        await _selectDevice(devices.first);
      }
    }
  }

  Future<void> _selectDevice(DiscoveredDevice device) async {
    _ipController.text = device.ip;
    _portController.text = device.port;
    await _saveSettings(showSnackbar: false);
    if (!mounted) return;

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          'Décodeur configuré : ${device.friendlyName} (${device.ip})',
        ),
        backgroundColor: const Color(0xFFFF6600),
        duration: const Duration(seconds: 3),
      ),
    );
  }

  Future<void> _testConnection() async {
    if (_isTesting) return;
    setState(() {
      _isTesting = true;
      _testResult = null;
    });

    // Forcer la sauvegarde avant le test
    await _service.storage.setIp(_ipController.text.trim());
    await _service.storage.setPort(_portController.text.trim());

    final status = await _service.getStatus();

    if (mounted) {
      setState(() {
        _isTesting = false;
        _testResult = status;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF121214),
      appBar: AppBar(
        title: const Text('Paramètres & Réseau'),
        backgroundColor: const Color(0xFF1B1B22),
        elevation: 0,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // CARTE RECHERCHE AUTOMATIQUE
            Card(
              color: const Color(0xFF1E1E24),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(16),
              ),
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.all(8),
                          decoration: BoxDecoration(
                            color: const Color(
                              0xFFFF6600,
                            ).withValues(alpha: 0.15),
                            borderRadius: BorderRadius.circular(10),
                          ),
                          child: const Icon(
                            Icons.radar_rounded,
                            color: Color(0xFFFF6600),
                          ),
                        ),
                        const SizedBox(width: 12),
                        const Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                'Recherche Automatique',
                                style: TextStyle(
                                  color: Colors.white,
                                  fontWeight: FontWeight.bold,
                                  fontSize: 16,
                                ),
                              ),
                              Text(
                                'Détection automatique sur le Wi-Fi local',
                                style: TextStyle(
                                  color: Colors.white54,
                                  fontSize: 12,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),
                    if (_isScanning) ...[
                      LinearProgressIndicator(
                        value: _scanProgress,
                        backgroundColor: Colors.white12,
                        color: const Color(0xFFFF6600),
                      ),
                      const SizedBox(height: 8),
                    ],
                    if (_scanStatusMessage.isNotEmpty &&
                        (_isScanning || _foundDevices.isEmpty)) ...[
                      Text(
                        _scanStatusMessage,
                        style: const TextStyle(
                          color: Colors.white70,
                          fontSize: 12,
                        ),
                      ),
                      if (_scanPermissionDenied) ...[
                        const SizedBox(height: 4),
                        TextButton.icon(
                          onPressed: openAppSettings,
                          icon: const Icon(Icons.settings_rounded, size: 16),
                          label: const Text(
                            'Ouvrir les paramètres de l\'application',
                          ),
                          style: TextButton.styleFrom(
                            foregroundColor: const Color(0xFFFF6600),
                            padding: EdgeInsets.zero,
                            minimumSize: const Size(0, 0),
                            tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                          ),
                        ),
                      ],
                      const SizedBox(height: 12),
                    ],
                    if (_foundDevices.isNotEmpty) ...[
                      if (_foundDevices.length > 1) ...[
                        Text(
                          '${_foundDevices.length} décodeurs détectés — choisissez-en un :',
                          style: const TextStyle(
                            color: Colors.white70,
                            fontSize: 12,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        const SizedBox(height: 8),
                      ],
                      for (final device in _foundDevices)
                        Padding(
                          padding: const EdgeInsets.only(bottom: 8),
                          child: _DiscoveredDeviceTile(
                            device: device,
                            isActive: _ipController.text.trim() == device.ip,
                            onTap: () => _selectDevice(device),
                          ),
                        ),
                      const SizedBox(height: 4),
                    ],
                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton.icon(
                        icon: _isScanning
                            ? const SizedBox(
                                width: 16,
                                height: 16,
                                child: CircularProgressIndicator(
                                  strokeWidth: 2,
                                  color: Colors.white,
                                ),
                              )
                            : const Icon(Icons.search_rounded),
                        label: Text(
                          _isScanning
                              ? 'Scan en cours...'
                              : 'Scanner le réseau',
                        ),
                        onPressed: _isScanning ? null : _startDiscovery,
                        style: ElevatedButton.styleFrom(
                          backgroundColor: const Color(0xFFFF6600),
                          foregroundColor: Colors.white,
                          padding: const EdgeInsets.symmetric(vertical: 12),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(10),
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),

            const SizedBox(height: 16),

            // CARTE CONFIGURATION MANUELLE
            Card(
              color: const Color(0xFF1E1E24),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(16),
              ),
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Adresse IP & Port du Décodeur',
                      style: TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.bold,
                        fontSize: 16,
                      ),
                    ),
                    const SizedBox(height: 12),
                    TextField(
                      controller: _ipController,
                      style: const TextStyle(color: Colors.white),
                      keyboardType: TextInputType.text,
                      decoration: InputDecoration(
                        labelText: 'Adresse IP locale',
                        labelStyle: const TextStyle(color: Colors.white54),
                        hintText: '192.168.1.15',
                        hintStyle: const TextStyle(color: Colors.white24),
                        prefixIcon: const Icon(
                          Icons.lan_rounded,
                          color: Color(0xFFFF6600),
                        ),
                        filled: true,
                        fillColor: const Color(0xFF26262E),
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(10),
                          borderSide: BorderSide.none,
                        ),
                      ),
                    ),
                    const SizedBox(height: 12),
                    TextField(
                      controller: _portController,
                      style: const TextStyle(color: Colors.white),
                      keyboardType: TextInputType.number,
                      decoration: InputDecoration(
                        labelText: 'Port (défaut : 8080)',
                        labelStyle: const TextStyle(color: Colors.white54),
                        hintText: '8080',
                        hintStyle: const TextStyle(color: Colors.white24),
                        prefixIcon: const Icon(
                          Icons.tag_rounded,
                          color: Color(0xFFFF6600),
                        ),
                        filled: true,
                        fillColor: const Color(0xFF26262E),
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(10),
                          borderSide: BorderSide.none,
                        ),
                      ),
                    ),
                    const SizedBox(height: 14),
                    Row(
                      children: [
                        Expanded(
                          child: OutlinedButton.icon(
                            icon: const Icon(Icons.save_rounded),
                            label: const Text('Enregistrer'),
                            onPressed: _saveSettings,
                            style: OutlinedButton.styleFrom(
                              foregroundColor: Colors.white,
                              side: const BorderSide(color: Colors.white24),
                              padding: const EdgeInsets.symmetric(vertical: 12),
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(10),
                              ),
                            ),
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: FilledButton.icon(
                            icon: _isTesting
                                ? const SizedBox(
                                    width: 16,
                                    height: 16,
                                    child: CircularProgressIndicator(
                                      strokeWidth: 2,
                                      color: Colors.white,
                                    ),
                                  )
                                : const Icon(Icons.bolt_rounded),
                            label: const Text('Tester'),
                            onPressed: _isTesting ? null : _testConnection,
                            style: FilledButton.styleFrom(
                              backgroundColor: const Color(0xFF33333E),
                              foregroundColor: const Color(0xFFFF6600),
                              padding: const EdgeInsets.symmetric(vertical: 12),
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(10),
                              ),
                            ),
                          ),
                        ),
                      ],
                    ),
                    if (_testResult != null) ...[
                      const SizedBox(height: 14),
                      Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: _testResult!.isOnline
                              ? const Color(0xFF1B5E20).withValues(alpha: 0.3)
                              : const Color(0xFFB71C1C).withValues(alpha: 0.3),
                          borderRadius: BorderRadius.circular(10),
                          border: Border.all(
                            color: _testResult!.isOnline
                                ? const Color(0xFF00E676)
                                : Colors.redAccent,
                          ),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                Icon(
                                  _testResult!.isOnline
                                      ? Icons.check_circle_rounded
                                      : Icons.error_rounded,
                                  color: _testResult!.isOnline
                                      ? const Color(0xFF00E676)
                                      : Colors.redAccent,
                                  size: 18,
                                ),
                                const SizedBox(width: 8),
                                Text(
                                  _testResult!.isOnline
                                      ? 'Connexion établie avec succès !'
                                      : 'Échec de la connexion',
                                  style: const TextStyle(
                                    color: Colors.white,
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                              ],
                            ),
                            if (_testResult!.isOnline) ...[
                              const SizedBox(height: 6),
                              Text(
                                'Appareil : ${_testResult!.friendlyName}',
                                style: const TextStyle(
                                  color: Colors.white70,
                                  fontSize: 12,
                                ),
                              ),
                              Text(
                                'État : ${_testResult!.isOn ? "Allumé" : "En veille"} (${_testResult!.osdContext})',
                                style: const TextStyle(
                                  color: Colors.white70,
                                  fontSize: 12,
                                ),
                              ),
                              if (_testResult!.macAddress.isNotEmpty)
                                Text(
                                  'Adresse MAC : ${_testResult!.macAddress}',
                                  style: const TextStyle(
                                    color: Colors.white70,
                                    fontSize: 12,
                                  ),
                                ),
                            ] else ...[
                              const SizedBox(height: 4),
                              Text(
                                _testResult!.errorMessage ??
                                    'Délai d\'attente dépassé.',
                                style: const TextStyle(
                                  color: Colors.white54,
                                  fontSize: 12,
                                ),
                              ),
                              if (_testResult!.permissionDenied) ...[
                                const SizedBox(height: 8),
                                TextButton.icon(
                                  onPressed: openAppSettings,
                                  icon: const Icon(
                                    Icons.settings_rounded,
                                    size: 16,
                                  ),
                                  label: const Text(
                                    'Ouvrir les paramètres de l\'application',
                                  ),
                                  style: TextButton.styleFrom(
                                    foregroundColor: const Color(0xFFFF6600),
                                    padding: EdgeInsets.zero,
                                    minimumSize: const Size(0, 0),
                                    tapTargetSize:
                                        MaterialTapTargetSize.shrinkWrap,
                                  ),
                                ),
                              ],
                            ],
                          ],
                        ),
                      ),
                    ],
                  ],
                ),
              ),
            ),

            const SizedBox(height: 16),

            // CARTE À PROPOS
            Card(
              color: const Color(0xFF1E1E24),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(16),
              ),
              child: const Padding(
                padding: EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'À propos',
                      style: TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.bold,
                        fontSize: 16,
                      ),
                    ),
                    SizedBox(height: 8),
                    Text(
                      'Télécommande mobile pour décodeur Orange Livebox TV UHD 4K.',
                      style: TextStyle(color: Colors.white70, fontSize: 13),
                    ),
                    SizedBox(height: 4),
                    Text(
                      'API locale HTTP : port 8080/remoteControl/cmd (Opérations 1, 9, 10).',
                      style: TextStyle(color: Colors.white38, fontSize: 11),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// Carte représentant un décodeur détecté lors du scan réseau, permettant de
/// différencier plusieurs décodeurs trouvés (nom, IP:port, méthode de
/// détection) et de choisir celui à configurer.
class _DiscoveredDeviceTile extends StatelessWidget {
  final DiscoveredDevice device;
  final bool isActive;
  final VoidCallback onTap;

  const _DiscoveredDeviceTile({
    required this.device,
    required this.isActive,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final accentColor = isActive ? const Color(0xFF00E676) : Colors.white24;
    return Material(
      color: const Color(0xFF2E7D32).withValues(alpha: isActive ? 0.22 : 0.1),
      borderRadius: BorderRadius.circular(10),
      child: InkWell(
        borderRadius: BorderRadius.circular(10),
        onTap: onTap,
        child: Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(10),
            border: Border.all(color: accentColor),
          ),
          child: Row(
            children: [
              Icon(
                isActive ? Icons.check_circle_rounded : Icons.dns_rounded,
                color: isActive ? const Color(0xFF00E676) : Colors.white54,
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      device.friendlyName,
                      style: const TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    Text(
                      '${device.ip}:${device.port} (${device.source})',
                      style: const TextStyle(
                        color: Colors.white70,
                        fontSize: 12,
                      ),
                    ),
                  ],
                ),
              ),
              if (!isActive)
                const Icon(Icons.chevron_right_rounded, color: Colors.white38),
            ],
          ),
        ),
      ),
    );
  }
}
