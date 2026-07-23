import 'package:flutter/material.dart';
import '../models/advisory.dart';

class AdvisoryCard extends StatelessWidget {
  final Advisory advisory;
  final String language;

  const AdvisoryCard({super.key, required this.advisory, required this.language});

  Color get _priorityColor {
    switch (advisory.priority) {
      case 'urgent': return const Color(0xFFDC2626);
      case 'high': return const Color(0xFFEA580C);
      default: return const Color(0xFF2563EB);
    }
  }

  IconData get _typeIcon {
    switch (advisory.advisoryType) {
      case 'irrigation': return Icons.water_drop;
      case 'fertilizer': return Icons.eco;
      case 'pest_control': return Icons.bug_report;
      case 'weather_alert': return Icons.cloud;
      default: return Icons.info_outline;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: advisory.isRead == 'false' ? _priorityColor.withOpacity(0.4) : Colors.grey[200]!),
        boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.04), blurRadius: 6, offset: const Offset(0, 2))],
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 40, height: 40,
            decoration: BoxDecoration(color: _priorityColor.withOpacity(0.1), borderRadius: BorderRadius.circular(10)),
            child: Icon(_typeIcon, color: _priorityColor, size: 20),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(advisory.getTitle(language), style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14), maxLines: 2, overflow: TextOverflow.ellipsis),
                const SizedBox(height: 4),
                Text(advisory.getBody(language), style: TextStyle(color: Colors.grey[600], fontSize: 13, height: 1.4), maxLines: 3, overflow: TextOverflow.ellipsis),
              ],
            ),
          ),
          if (advisory.isRead == 'false')
            Container(width: 8, height: 8, margin: const EdgeInsets.only(top: 4), decoration: BoxDecoration(color: _priorityColor, shape: BoxShape.circle)),
        ],
      ),
    );
  }
}
