import 'dart:io';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:permission_handler/permission_handler.dart';

class NetworkPermissionService {
  static const _permissions = [
    Permission.nearbyWifiDevices,
    Permission.accessLocalNetwork,
  ];

  // kIsWeb est vérifié en premier et court-circuite avant Platform.isAndroid :
  // dart:io Platform lève une exception sur le web.
  bool get _requiresCheck => !kIsWeb && Platform.isAndroid;

  Future<bool> isGranted() async {
    if (!_requiresCheck) return true;
    for (final permission in _permissions) {
      final status = await permission.status;
      if (!status.isGranted && !status.isLimited) return false;
    }
    return true;
  }

  Future<bool> request() async {
    if (!_requiresCheck) return true;
    final statuses = await _permissions.request();
    return statuses.values.every((s) => s.isGranted || s.isLimited);
  }

  Future<bool> isPermanentlyDenied() async {
    if (!_requiresCheck) return false;
    for (final permission in _permissions) {
      if (await permission.isPermanentlyDenied) return true;
    }
    return false;
  }
}
