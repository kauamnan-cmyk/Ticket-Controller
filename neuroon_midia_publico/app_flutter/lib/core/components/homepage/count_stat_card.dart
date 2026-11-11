import 'package:flutter/material.dart';
import 'package:nextpubli/core/themes/app_colors.dart';

class CountStatCard extends StatelessWidget {
  final IconData icon;
  final Color iconColor;
  final Color countColor;
  final int count;
  final String label;

  const CountStatCard({
    super.key,
    required this.icon,
    required this.iconColor,
    required this.countColor,
    required this.count,
    required this.label,
  });

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final width = constraints.maxWidth;
        final iconSize = (width * 0.32).clamp(18.0, 36.0);
        final countFontSize = (width * 0.22).clamp(16.0, 28.0);
        final labelFontSize = (width * 0.1).clamp(9.0, 12.0);

        return Container(
          width: double.infinity,
          padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 8),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(12),
            color: AppColors.gray,
          ),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(icon, color: iconColor, size: iconSize),
              const SizedBox(height: 6),
              FittedBox(
                fit: BoxFit.scaleDown,
                child: Text(
                  count.toString(),
                  style: TextStyle(
                    color: countColor,
                    fontSize: countFontSize,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
              const SizedBox(height: 2),
              Text(
                label,
                textAlign: TextAlign.center,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(
                  color: AppColors.white.withAlpha(179),
                  fontSize: labelFontSize,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}
