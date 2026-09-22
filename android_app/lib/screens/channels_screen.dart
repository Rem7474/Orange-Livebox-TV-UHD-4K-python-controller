import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import '../models/channel.dart';
import '../services/livebox_service.dart';

class ChannelsScreen extends StatefulWidget {
  const ChannelsScreen({super.key});

  @override
  State<ChannelsScreen> createState() => _ChannelsScreenState();
}

class _ChannelsScreenState extends State<ChannelsScreen> {
  final TextEditingController _searchController = TextEditingController();
  late final LiveboxService _service;
  List<Channel> _filteredChannels = [];
  bool _onlyFavorites = false;
  String? _zappingChannelName;

  @override
  void initState() {
    super.initState();
    _service = context.read<LiveboxService>();
    _initChannels();
    _searchController.addListener(_applyFilter);
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  void _initChannels() {
    _filteredChannels = _service.allChannels;
    _applyFilter();
  }

  void _applyFilter() {
    final query = _searchController.text.trim().toLowerCase();
    setState(() {
      _filteredChannels = _service.allChannels.where((c) {
        if (_onlyFavorites && !c.isFavorite) return false;
        if (query.isEmpty) return true;
        final matchName = c.name.toLowerCase().contains(query);
        final matchNum = c.number?.toString().contains(query) ?? false;
        return matchName || matchNum;
      }).toList();
    });
  }

  Future<void> _zapToChannel(Channel channel) async {
    unawaited(HapticFeedback.mediumImpact());
    setState(() => _zappingChannelName = channel.name);

    final ok = await _service.changeChannel(channel.epgId);
    if (ok) {
      unawaited(_service.getStatus());
    }

    if (mounted) {
      setState(() => _zappingChannelName = null);
      final reason = _service.lastError;
      ScaffoldMessenger.of(context).removeCurrentSnackBar();
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            ok
                ? 'Zappé sur ${channel.displayName}'
                : (reason != null
                      ? 'Échec du zapping vers ${channel.displayName} : $reason'
                      : 'Échec du zapping vers ${channel.displayName}'),
          ),
          backgroundColor: ok ? const Color(0xFFFF6600) : Colors.redAccent,
          duration: Duration(seconds: ok ? 2 : 3),
          behavior: SnackBarBehavior.floating,
        ),
      );
    }
  }

  Future<void> _toggleFavorite(Channel channel) async {
    unawaited(HapticFeedback.selectionClick());
    await _service.storage.toggleFavorite(channel.epgId);
    setState(() {
      channel.isFavorite = !channel.isFavorite;
    });
    _applyFilter();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF121214),
      appBar: AppBar(
        title: const Text('Chaînes TV'),
        backgroundColor: const Color(0xFF1B1B22),
        elevation: 0,
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(105),
          child: Column(
            children: [
              // Champ de recherche
              Padding(
                padding: const EdgeInsets.symmetric(
                  horizontal: 16,
                  vertical: 6,
                ),
                child: TextField(
                  controller: _searchController,
                  style: const TextStyle(color: Colors.white),
                  decoration: InputDecoration(
                    hintText: 'Rechercher une chaîne ou un numéro...',
                    hintStyle: const TextStyle(color: Colors.white38),
                    prefixIcon: const Icon(
                      Icons.search,
                      color: Color(0xFFFF6600),
                    ),
                    suffixIcon: _searchController.text.isNotEmpty
                        ? IconButton(
                            icon: const Icon(
                              Icons.clear,
                              color: Colors.white70,
                            ),
                            onPressed: () {
                              _searchController.clear();
                              _applyFilter();
                            },
                          )
                        : null,
                    filled: true,
                    fillColor: const Color(0xFF26262E),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(14),
                      borderSide: BorderSide.none,
                    ),
                    contentPadding: const EdgeInsets.symmetric(
                      vertical: 0,
                      horizontal: 16,
                    ),
                  ),
                ),
              ),

              // Barre de filtres (Total et Favoris)
              Padding(
                padding: const EdgeInsets.symmetric(
                  horizontal: 16,
                  vertical: 4,
                ),
                child: Row(
                  children: [
                    FilterChip(
                      label: const Text('Favoris'),
                      selected: _onlyFavorites,
                      onSelected: (val) {
                        setState(() => _onlyFavorites = val);
                        _applyFilter();
                      },
                      avatar: Icon(
                        _onlyFavorites ? Icons.star : Icons.star_border,
                        size: 16,
                        color: _onlyFavorites ? Colors.amber : Colors.white70,
                      ),
                      selectedColor: const Color(0xFF3E2723),
                      backgroundColor: const Color(0xFF26262E),
                      labelStyle: TextStyle(
                        color: _onlyFavorites
                            ? const Color(0xFFFF9800)
                            : Colors.white70,
                        fontSize: 12,
                      ),
                    ),
                    const Spacer(),
                    Text(
                      '${_filteredChannels.length} chaîne(s)',
                      style: const TextStyle(
                        color: Colors.white54,
                        fontSize: 12,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
      body: _filteredChannels.isEmpty
          ? Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(
                    Icons.tv_off_rounded,
                    size: 56,
                    color: Colors.white24,
                  ),
                  const SizedBox(height: 12),
                  Text(
                    _onlyFavorites
                        ? 'Aucune chaîne favorite.'
                        : 'Aucune chaîne trouvée.',
                    style: const TextStyle(color: Colors.white54, fontSize: 16),
                  ),
                ],
              ),
            )
          : ListView.builder(
              padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 12),
              itemCount: _filteredChannels.length,
              itemBuilder: (context, index) {
                final channel = _filteredChannels[index];
                final isZappingThis = _zappingChannelName == channel.name;

                return Card(
                  margin: const EdgeInsets.symmetric(vertical: 4),
                  elevation: 1,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                    side: isZappingThis
                        ? const BorderSide(color: Color(0xFFFF6600), width: 1.5)
                        : BorderSide.none,
                  ),
                  color: const Color(0xFF1E1E24),
                  child: ListTile(
                    contentPadding: const EdgeInsets.symmetric(
                      horizontal: 14,
                      vertical: 2,
                    ),
                    leading: Container(
                      width: 46,
                      height: 46,
                      decoration: BoxDecoration(
                        color: channel.number != null
                            ? const Color(0xFF2E2E38)
                            : const Color(0xFF22222A),
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(
                          color: channel.number != null
                              ? const Color(0xFFFF6600).withValues(alpha: 0.3)
                              : Colors.white12,
                        ),
                      ),
                      child: Center(
                        child: Text(
                          channel.number?.toString() ?? '–',
                          style: TextStyle(
                            color: channel.number != null
                                ? const Color(0xFFFF6600)
                                : Colors.white38,
                            fontWeight: FontWeight.bold,
                            fontSize: 16,
                          ),
                        ),
                      ),
                    ),
                    title: Text(
                      channel.name,
                      style: const TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.w600,
                        fontSize: 15,
                      ),
                    ),
                    trailing: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        IconButton(
                          icon: Icon(
                            channel.isFavorite
                                ? Icons.star_rounded
                                : Icons.star_border_rounded,
                            color: channel.isFavorite
                                ? Colors.amber
                                : Colors.white24,
                            size: 24,
                          ),
                          onPressed: () => _toggleFavorite(channel),
                          tooltip: channel.isFavorite
                              ? 'Retirer des favoris'
                              : 'Ajouter aux favoris',
                        ),
                        const SizedBox(width: 4),
                        FilledButton(
                          onPressed: isZappingThis
                              ? null
                              : () => _zapToChannel(channel),
                          style: FilledButton.styleFrom(
                            backgroundColor: const Color(0xFFFF6600),
                            padding: const EdgeInsets.symmetric(
                              horizontal: 12,
                              vertical: 8,
                            ),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(8),
                            ),
                          ),
                          child: isZappingThis
                              ? const SizedBox(
                                  width: 16,
                                  height: 16,
                                  child: CircularProgressIndicator(
                                    strokeWidth: 2,
                                    color: Colors.white,
                                  ),
                                )
                              : const Text(
                                  'Zapper',
                                  style: TextStyle(fontSize: 12),
                                ),
                        ),
                      ],
                    ),
                    onTap: () => _zapToChannel(channel),
                  ),
                );
              },
            ),
    );
  }
}
