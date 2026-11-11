import 'package:flutter/material.dart';
import 'package:nextpubli/core/themes/app_colors.dart';

class LandingPageView extends StatelessWidget {
  const LandingPageView({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.gray,
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text('Bem-vindo ao NextPubli', style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: AppColors.primary)),
            SizedBox(height: 16),
            Text('Gerencie suas filas de atendimento de forma eficiente e moderna.', style: TextStyle(fontSize: 16, color: AppColors.gray)),
          ],
        ),
      ),
    );
  }
}