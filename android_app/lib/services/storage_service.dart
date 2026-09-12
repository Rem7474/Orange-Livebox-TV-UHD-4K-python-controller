import 'package:shared_preferences/shared_preferences.dart';

class StorageService {
  static const String _keyIp = 'livebox_ip';
  static const String _keyPort = 'livebox_port';
  static const String _keyFavorites = 'livebox_favorites';

  static const String defaultIp = '192.168.1.15';
  static const String defaultPort = '8080';

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
    return prefs.getString(_keyPort) ?? defaultPort;
  }

  Future<void> setPort(String port) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_keyPort, port.trim());
  }

  Future<List<String>> getFavorites() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getStringList(_keyFavorites) ?? ['192', '4', '80', '34', '47', '118', '111'];
  }

  Future<void> toggleFavorite(String epgId) async {
    final prefs = await SharedPreferences.getInstance();
    final favs = prefs.getStringList(_keyFavorites) ?? ['192', '4', '80', '34', '47', '118', '111'];
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
