import 'package:shared_preferences/shared_preferences.dart';

class StorageService {
  static const String _keyIp = 'livebox_ip';
  static const String _keyPort = 'livebox_port';
  static const String _keyFavorites = 'livebox_favorites';

  static const String defaultIp = '192.168.1.15';
  static const String defaultPort = '8080';
  static const List<String> defaultFavorites = [
    '192',
    '4',
    '80',
    '34',
    '47',
    '118',
    '111',
  ];

  Future<String> getIp() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_keyIp) ?? defaultIp;
  }

  Future<void> setIp(String ip) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_keyIp, ip.trim());
  }

  Future<String> getPort() async {
    final prefs = await SharedPreferences.getInstance();
    final port = prefs.getString(_keyPort);
    return (port == null || port.isEmpty) ? defaultPort : port;
  }

  Future<void> setPort(String port) async {
    final prefs = await SharedPreferences.getInstance();
    final trimmed = port.trim();
    await prefs.setString(_keyPort, trimmed.isEmpty ? defaultPort : trimmed);
  }

  Future<List<String>> getFavorites() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getStringList(_keyFavorites) ??
        List<String>.from(defaultFavorites);
  }

  Future<void> toggleFavorite(String epgId) async {
    final prefs = await SharedPreferences.getInstance();
    final favs = List<String>.from(
      prefs.getStringList(_keyFavorites) ?? defaultFavorites,
    );
    if (favs.contains(epgId)) {
      favs.remove(epgId);
    } else {
      favs.add(epgId);
    }
    await prefs.setStringList(_keyFavorites, favs);
  }

  Future<bool> isFavorite(String epgId) async {
    final favs = await getFavorites();
    return favs.contains(epgId);
  }
}
