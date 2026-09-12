import 'package:flutter/material.dart';
import '../models/decoder_status.dart';

class StatusBanner extends StatelessWidget {
  final DecoderStatus? status;
  final bool isLoading;
  final VoidCallback onRefresh;
  final VoidCallback? onTap;

  const StatusBanner({
    super.key,
    required this.status,
    required this.isLoading,
    required this.onRefresh,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isOnline = status?.isOnline ?? false;
    final isOn = status?.isOn ?? false;

    Color statusColor;
    String statusText;

    if (!isOnline) {
      statusColor = Colors.redAccent;
      statusText = 'Déconnecté';
    } else if (isOn) {
      statusColor = const Color(0xFF00E676);
      final ctx = status!.osdContext;
      statusText = ctx.isNotEmpty ? 'Allumé ($ctx)' : 'Allumé';
    } else {
      statusColor = Colors.amber;
      statusText = 'En veille';
    }

    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      color: const Color(0xFF1E1E24),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(16),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          child: Row(
            children: [
              Container(
                width: 12,
                height: 12,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: statusColor,
                  boxShadow: [
                    BoxShadow(
                      color: statusColor.withValues(alpha: 0.5),
                      blurRadius: 8,
                      spreadRadius: 2,
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(
                      status?.friendlyName ?? 'Décodeur TV Orange',
                      style: theme.textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    const SizedBox(height: 2),
                    Text(
                      statusText,
                      style: theme.textTheme.bodySmall?.copyWith(
                        color: Colors.white70,
                      ),
                    ),
                  ],
                ),
              ),
              IconButton(
                icon: isLoading
                    ? const SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          color: Color(0xFFFF6600),
                        ),
                      )
                    : const Icon(Icons.refresh, color: Colors.white70),
                onPressed: isLoading ? null : onRefresh,
                tooltip: 'Actualiser le statut',
              ),
            ],
          ),
        ),
      ),
    );
  }
}
