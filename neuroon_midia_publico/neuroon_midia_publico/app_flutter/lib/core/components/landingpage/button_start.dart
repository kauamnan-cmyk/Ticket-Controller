import 'package:flutter/material.dart';
import 'package:nextpubli/core/themes/app_colors.dart';

class ButtonComponent extends StatelessWidget {
  final VoidCallback onPressed;

  const ButtonComponent({
    super.key,
    required this.onPressed,
  });

  void _handlePressed() {
    onPressed();
  }

  @override
  Widget build(BuildContext context) {
    return ElevatedButton(
      onPressed: _handlePressed,
      style: ElevatedButton.styleFrom(
        backgroundColor: AppColors.primary,
        foregroundColor: AppColors.ticketBackground,
      ),
      child: 
      Text('Começar',
       style: const TextStyle(
        fontSize: 16, 
        fontWeight: FontWeight.bold)
        ),
    );
  }
}