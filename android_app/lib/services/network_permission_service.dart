import 'dart:io';
import 'package:permission_handler/permission_handler.dart';

class NetworkPermissionService {
  static const _permissions = [
    Permission.nearbyWifiDevices,
    Permission.accessLocalNetwork,
  ];

  static Future<bool> isGranted() async {
    if (!Platform.isAndroid) return true;
    for (final permission in _permissions) {
      final status = await permission.status;
      if (!status.isGranted && !status.isLimited) return false;
    }
    return true;
  }

  static Future<bool> request() async {
    if (!Platform.isAndroid) return true;
    final statuses = await _permissions.request();
    return statuses.values.every((s) => s.isGranted || s.isLimited);
  }

  static Future<bool> isPermanentlyDenied() async {
    if (!Platform.isAndroid) return false;
    for (final permission in _permissions) {
      if (await permission.isPermanentlyDenied) return true;
    }
    return false;
  }
}
