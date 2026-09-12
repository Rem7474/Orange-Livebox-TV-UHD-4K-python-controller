import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../models/decoder_status.dart';
import '../models/remote_key.dart';
import '../services/livebox_service.dart';
import '../widgets/status_banner.dart';

class RemoteScreen extends StatefulWidget {
  final LiveboxService service;

  const RemoteScreen({super.key, required this.service});

  @override
  State<RemoteScreen> createState() => _RemoteScreenState();
}

class _RemoteScreenState extends State<RemoteScreen> with WidgetsBindingObserver {
  static const _pollInterval = Duration(seconds: 10);

  DecoderStatus? _status;
  bool _isRefreshing = false;
  bool _showNumpad = false;
  Timer? _pollTimer;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    widget.service.addListener(_onServiceStatusChanged);
    _status = widget.service.lastStatus;
    _refreshStatus();
    _startPolling();
  }

  @override
  void dispose() {
    _pollTimer?.cancel();
    WidgetsBinding.instance.removeObserver(this);
    widget.service.removeListener(_onServiceStatusChanged);
    super.dispose();
  }

  // Reflète immédiatement le statut quand un autre écran (Paramètres, Chaînes)
  // déclenche un getStatus(), sans attendre le prochain polling de cet écran.
  void _onServiceStatusChanged() {
    if (mounted) setState(() => _status = widget.service.lastStatus);
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      _refreshStatus();
      _startPolling();
    } else {
      _pollTimer?.cancel();
    }
  }

  void _startPolling() {
    _pollTimer?.cancel();
    _pollTimer = Timer.periodic(_pollInterval, (_) => _refreshStatus());
  }

  Future<void> _refreshStatus() async {
    if (_isRefreshing) return;
    setState(() => _isRefreshing = true);
    final status = await widget.service.getStatus();
    if (mounted) {
      setState(() {
        _status = status;
        _isRefreshing = false;
      });
    }
  }

  Future<void> _sendKey(RemoteKey key) async {
    HapticFeedback.lightImpact();
    final ok = await widget.service.sendKey(key);
    if (!ok && mounted) {
      final reason = widget.service.lastError;
      ScaffoldMessenger.of(context).removeCurrentSnackBar();
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            reason != null
                ? 'Échec de la commande ${key.label} : $reason'
                : 'Échec de la commande ${key.label}',
          ),
          backgroundColor: Colors.redAccent,
          duration: const Duration(milliseconds: 1800),
          behavior: SnackBarBehavior.floating,
        ),
      );
    }
    if (ok) {
      _refreshStatus();
      // Le décodeur met un peu de temps à changer d'état après un Power.
      if (key == RemoteKey.power) {
        Future.delayed(const Duration(milliseconds: 1500), _refreshStatus);
      }
    }
  }

  Widget _buildCircleButton({
    required IconData icon,
    required String label,
    required VoidCallback onTap,
    Color? color,
    Color? iconColor,
    double size = 52,
  }) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Material(
          color: color ?? const Color(0xFF26262E),
          shape: const CircleBorder(),
          clipBehavior: Clip.antiAlias,
          child: InkWell(
            onTap: onTap,
            child: SizedBox(
              width: size,
              height: size,
              child: Icon(
                icon,
                color: iconColor ?? Colors.white,
                size: size * 0.48,
              ),
            ),
          ),
        ),
        if (label.isNotEmpty) ...[
          const SizedBox(height: 4),
          Text(
            label,
            style: const TextStyle(fontSize: 11, color: Colors.white70),
          ),
        ],
      ],
    );
  }

  Widget _buildRocker({
    required String title,
    required IconData upIcon,
    required VoidCallback onUp,
    required IconData downIcon,
    required VoidCallback onDown,
    required IconData centerIcon,
  }) {
    return Container(
      width: 72,
      height: 150,
      decoration: BoxDecoration(
        color: const Color(0xFF26262E),
        borderRadius: BorderRadius.circular(36),
        border: Border.all(color: Colors.white10),
      ),
      child: Column(
        children: [
          Expanded(
            child: InkWell(
              onTap: onUp,
              borderRadius: const BorderRadius.vertical(top: Radius.circular(36)),
              child: Center(
                child: Icon(upIcon, color: Colors.white, size: 28),
              ),
            ),
          ),
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 4),
            child: Column(
              children: [
                Icon(centerIcon, color: const Color(0xFFFF6600), size: 18),
                Text(
                  title,
                  style: const TextStyle(
                    fontSize: 10,
                    fontWeight: FontWeight.bold,
                    color: Colors.white54,
                  ),
                ),
              ],
            ),
          ),
          Expanded(
            child: InkWell(
              onTap: onDown,
              borderRadius: const BorderRadius.vertical(bottom: Radius.circular(36)),
              child: Center(
                child: Icon(downIcon, color: Colors.white, size: 28),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildDPad() {
    return SizedBox(
      width: 210,
      height: 210,
      child: Stack(
        alignment: Alignment.center,
        children: [
          // Anneau extérieur D-Pad
          Container(
            width: 210,
            height: 210,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: const Color(0xFF22222A),
              border: Border.all(color: Colors.white12, width: 2),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withValues(alpha: 0.3),
                  blurRadius: 10,
                  spreadRadius: 2,
                ),
              ],
            ),
          ),
          // HAUT
          Positioned(
            top: 6,
            child: IconButton(
              iconSize: 34,
              icon: const Icon(Icons.keyboard_arrow_up_rounded, color: Colors.white),
              onPressed: () => _sendKey(RemoteKey.up),
              tooltip: 'Haut',
            ),
          ),
          // BAS
          Positioned(
            bottom: 6,
            child: IconButton(
              iconSize: 34,
              icon: const Icon(Icons.keyboard_arrow_down_rounded, color: Colors.white),
              onPressed: () => _sendKey(RemoteKey.down),
              tooltip: 'Bas',
            ),
          ),
          // GAUCHE
          Positioned(
            left: 6,
            child: IconButton(
              iconSize: 34,
              icon: const Icon(Icons.keyboard_arrow_left_rounded, color: Colors.white),
              onPressed: () => _sendKey(RemoteKey.left),
              tooltip: 'Gauche',
            ),
          ),
          // DROITE
          Positioned(
            right: 6,
            child: IconButton(
              iconSize: 34,
              icon: const Icon(Icons.keyboard_arrow_right_rounded, color: Colors.white),
              onPressed: () => _sendKey(RemoteKey.right),
              tooltip: 'Droite',
            ),
          ),
          // BOUTON CENTRAL OK
          Material(
            color: const Color(0xFFFF6600),
            shape: const CircleBorder(),
            elevation: 4,
            child: InkWell(
              onTap: () => _sendKey(RemoteKey.ok),
              customBorder: const CircleBorder(),
              child: const SizedBox(
                width: 76,
                height: 76,
                child: Center(
                  child: Text(
                    'OK',
                    style: TextStyle(
                      color: Colors.white,
                      fontWeight: FontWeight.bold,
                      fontSize: 20,
                    ),
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildNumpad() {
    final numbers = [
      [RemoteKey.num1, RemoteKey.num2, RemoteKey.num3],
      [RemoteKey.num4, RemoteKey.num5, RemoteKey.num6],
      [RemoteKey.num7, RemoteKey.num8, RemoteKey.num9],
    ];

    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 24, vertical: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xFF1B1B22),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: Colors.white10),
      ),
      child: Column(
        children: [
          for (final row in numbers) ...[
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: row.map((key) {
                return Padding(
                  padding: const EdgeInsets.symmetric(vertical: 4),
                  child: Material(
                    color: const Color(0xFF26262E),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                    child: InkWell(
                      onTap: () => _sendKey(key),
                      borderRadius: BorderRadius.circular(14),
                      child: SizedBox(
                        width: 72,
                        height: 48,
                        child: Center(
                          child: Text(
                            key.label,
                            style: const TextStyle(
                              fontSize: 20,
                              fontWeight: FontWeight.bold,
                              color: Colors.white,
                            ),
                          ),
                        ),
                      ),
                    ),
                  ),
                );
              }).toList(),
            ),
          ],
          // Ligne du zéro
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 4),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Material(
                  color: const Color(0xFF26262E),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                  child: InkWell(
                    onTap: () => _sendKey(RemoteKey.num0),
                    borderRadius: BorderRadius.circular(14),
                    child: const SizedBox(
                      width: 72,
                      height: 48,
                      child: Center(
                        child: Text(
                          '0',
                          style: TextStyle(
                            fontSize: 20,
                            fontWeight: FontWeight.bold,
                            color: Colors.white,
                          ),
                        ),
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF121214),
      body: SafeArea(
        child: RefreshIndicator(
          onRefresh: _refreshStatus,
          color: const Color(0xFFFF6600),
          child: SingleChildScrollView(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.only(bottom: 24),
            child: Column(
              children: [
                // Bannière de statut connectivité
                StatusBanner(
                  status: _status,
                  isLoading: _isRefreshing,
                  onRefresh: _refreshStatus,
                ),

                const SizedBox(height: 8),

                // Rangée supérieure : Power, Mute, Direct
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 24),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      _buildCircleButton(
                        icon: Icons.power_settings_new_rounded,
                        label: 'Power',
                        color: _status?.isOn == true
                            ? const Color(0xFFE53935)
                            : const Color(0xFF2E7D32),
                        onTap: () => _sendKey(RemoteKey.power),
                        size: 56,
                      ),
                      _buildCircleButton(
                        icon: Icons.volume_off_rounded,
                        label: 'Muet',
                        onTap: () => _sendKey(RemoteKey.mute),
                        size: 50,
                      ),
                      _buildCircleButton(
                        icon: _showNumpad ? Icons.dialpad : Icons.dialpad_outlined,
                        label: 'Clavier',
                        color: _showNumpad ? const Color(0xFFFF6600) : const Color(0xFF26262E),
                        onTap: () {
                          HapticFeedback.selectionClick();
                          setState(() => _showNumpad = !_showNumpad);
                        },
                        size: 50,
                      ),
                      _buildCircleButton(
                        icon: Icons.tv_rounded,
                        label: 'Direct',
                        onTap: () => _sendKey(RemoteKey.direct),
                        size: 50,
                      ),
                    ],
                  ),
                ),

                if (_showNumpad) ...[
                  const SizedBox(height: 8),
                  _buildNumpad(),
                ],

                const SizedBox(height: 20),

                // Pavé Directionnel (D-Pad)
                _buildDPad(),

                const SizedBox(height: 20),

                // Touches Système : Retour, Menu, Guide, VOD, REC
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                    children: [
                      _buildCircleButton(
                        icon: Icons.arrow_back_rounded,
                        label: 'Retour',
                        onTap: () => _sendKey(RemoteKey.back),
                        size: 48,
                      ),
                      _buildCircleButton(
                        icon: Icons.home_rounded,
                        label: 'Menu',
                        color: const Color(0xFF33333E),
                        iconColor: const Color(0xFFFF6600),
                        onTap: () => _sendKey(RemoteKey.menu),
                        size: 54,
                      ),
                      _buildCircleButton(
                        icon: Icons.calendar_month_rounded,
                        label: 'Guide',
                        onTap: () => _sendKey(RemoteKey.guide),
                        size: 48,
                      ),
                      _buildCircleButton(
                        icon: Icons.movie_outlined,
                        label: 'VOD',
                        onTap: () => _sendKey(RemoteKey.vod),
                        size: 48,
                      ),
                      _buildCircleButton(
                        icon: Icons.fiber_manual_record_rounded,
                        label: 'REC',
                        iconColor: Colors.redAccent,
                        onTap: () => _sendKey(RemoteKey.rec),
                        size: 48,
                      ),
                    ],
                  ),
                ),

                const SizedBox(height: 24),

                // Volume, Lecteur et Chaînes
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 24),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceAround,
                    children: [
                      // Rocker Volume
                      _buildRocker(
                        title: 'VOL',
                        upIcon: Icons.add_rounded,
                        onUp: () => _sendKey(RemoteKey.volUp),
                        downIcon: Icons.remove_rounded,
                        onDown: () => _sendKey(RemoteKey.volDown),
                        centerIcon: Icons.volume_up_rounded,
                      ),

                      // Contrôles Médias au centre
                      Column(
                        children: [
                          _buildCircleButton(
                            icon: Icons.play_arrow_rounded,
                            label: 'Lecture / Pause',
                            size: 60,
                            color: const Color(0xFFFF6600),
                            onTap: () => _sendKey(RemoteKey.playPause),
                          ),
                          const SizedBox(height: 12),
                          Row(
                            children: [
                              _buildCircleButton(
                                icon: Icons.fast_rewind_rounded,
                                label: 'Recul',
                                size: 44,
                                onTap: () => _sendKey(RemoteKey.fbwd),
                              ),
                              const SizedBox(width: 14),
                              _buildCircleButton(
                                icon: Icons.fast_forward_rounded,
                                label: 'Avance',
                                size: 44,
                                onTap: () => _sendKey(RemoteKey.ffwd),
                              ),
                            ],
                          ),
                        ],
                      ),

                      // Rocker Chaînes
                      _buildRocker(
                        title: 'CH',
                        upIcon: Icons.keyboard_arrow_up_rounded,
                        onUp: () => _sendKey(RemoteKey.chUp),
                        downIcon: Icons.keyboard_arrow_down_rounded,
                        onDown: () => _sendKey(RemoteKey.chDown),
                        centerIcon: Icons.tv_rounded,
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
