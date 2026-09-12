class DecoderStatus {
  final bool isOnline;
  final bool isOn;
  final String friendlyName;
  final String osdContext;
  final String playedMediaId;
  final String playedMediaType;
  final String timeShiftingState;
  final String macAddress;
  final String? errorMessage;
  final DateTime lastUpdated;

  DecoderStatus({
    required this.isOnline,
    required this.isOn,
    required this.friendlyName,
    required this.osdContext,
    required this.playedMediaId,
    required this.playedMediaType,
    required this.timeShiftingState,
    required this.macAddress,
    this.errorMessage,
    required this.lastUpdated,
  });

  factory DecoderStatus.fromJson(Map<String, dynamic> json) {
    final result = json['result'] as Map<String, dynamic>? ?? {};
    final data = result['data'] as Map<String, dynamic>? ?? {};
    
    final activeStandbyState = data['activeStandbyState']?.toString() ?? '1';
    final isOn = activeStandbyState == '0';

    return DecoderStatus(
      isOnline: true,
      isOn: isOn,
      friendlyName: data['friendlyName']?.toString() ?? 'Décodeur TV Orange',
      osdContext: data['osdContext']?.toString() ?? 'LIVE',
      playedMediaId: data['playedMediaId']?.toString() ?? '',
      playedMediaType: data['playedMediaType']?.toString() ?? '',
      timeShiftingState: data['timeShiftingState']?.toString() ?? '0',
      macAddress: data['macAddress']?.toString() ?? '',
      lastUpdated: DateTime.now(),
    );
  }

  factory DecoderStatus.offline([String? message]) {
    return DecoderStatus(
      isOnline: false,
      isOn: false,
      friendlyName: 'Décodeur déconnecté',
      osdContext: 'INCONNU',
      playedMediaId: '',
      playedMediaType: '',
      timeShiftingState: '0',
      macAddress: '',
      errorMessage: message ?? 'Impossible de joindre le décodeur',
      lastUpdated: DateTime.now(),
    );
  }
}
