import 'package:flutter/material.dart';
import 'package:nextpubli/core/themes/app_colors.dart';

class EmailComponente extends StatelessWidget {
  final TextEditingController controller;
  final String hintText;
  final IconData icon;

  const EmailComponente({
    super.key,
    required this.controller,
    this.hintText = 'Digite seu e-mail',
    this.icon = Icons.email_outlined,
  });

  @override
  Widget build(BuildContext context) {
    return TextFormField(
      controller: controller,
      style: const TextStyle(color: AppColors.white),
      decoration: InputDecoration(
        hintText: hintText,
        hintStyle: const TextStyle(color: Color(0xFF9CA3AF)),
        prefixIcon: Icon(icon, color: AppColors.white),
        contentPadding: const EdgeInsets.symmetric(vertical: 18, horizontal: 16),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: BorderSide.none,
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: BorderSide.none,
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: BorderSide.none,
        ),
        filled: true,
        fillColor: AppColors.gray,
      ),
      cursorColor: AppColors.white,
      keyboardType: TextInputType.emailAddress,
    );
  }
}
