import 'package:flutter/material.dart';
import 'package:nextpubli/core/themes/app_colors.dart';

class ActionButton extends StatelessWidget {
  final String title;
  final IconData icon;
  final Color color;
  final VoidCallback onTap;

  const ActionButton({
    super.key,
    required this.title,
    required this.icon,
    required this.color,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        borderRadius: BorderRadius.circular(24),
        onTap: onTap,
        child: Container(
  height: 55,
  decoration: BoxDecoration(
    borderRadius: BorderRadius.circular(20),
    border: Border.all(color: color, width: 2),
  ),
  child: Stack(
    children: [
      // Ícone fixo
      Positioned(
        left: 12,
        top: 0,
        bottom: 0,
        child: Center(
          child: Icon(
            icon,
            color: color,
            size: 28,
          ),
        ),
      ),

      // Texto independente
      Center(
        child: Padding(
          padding: const EdgeInsets.only(left: 40), 
          child: Text(
           title,
           style: TextStyle(
             fontSize: 14,
             fontWeight: FontWeight.bold,
             color:(AppColors.white).withAlpha(172),
           ),
          ),
        ),
      ),
    ],
  ),
)
            ,
          ),
    );
  }
}