import 'package:flutter/material.dart';

class StatusBadge extends StatelessWidget {
  final String status;
  final Color? textColor;
  final Color? backgroundColor;
  final Color? borderColor;

  const StatusBadge({
    super.key,
    required this.status,
    this.textColor,
    this.backgroundColor,
    this.borderColor,
  });

  @override
  Widget build(BuildContext context) {
    final badgeTextColor = textColor ?? Colors.grey.shade700;
    final badgeBorderColor = borderColor ?? badgeTextColor;

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 5),
      decoration: BoxDecoration(
        color: backgroundColor ?? Colors.transparent,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(
          color: badgeBorderColor,
          width: 1.5,
        ),
      ),
      child: Text(
        status,
        style: TextStyle(
          color: badgeTextColor,
          fontSize: 12,
          fontWeight: FontWeight.w700,
        ),
      ),
    );
  }
}
