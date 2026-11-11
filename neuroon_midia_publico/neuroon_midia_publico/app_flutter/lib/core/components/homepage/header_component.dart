import 'package:flutter/material.dart';
import 'package:nextpubli/core/themes/app_colors.dart';
import 'package:nextpubli/core/providers/session_provider.dart';
import 'package:provider/provider.dart';

class HeaderComponent extends StatelessWidget {
  final String title;
  final VoidCallback? onMenuPressed;
  final VoidCallback? onFilterPressed;
  final VoidCallback? onLockPressed;
  final bool isLockOpen;
  

  const HeaderComponent({
    super.key,
    required this.title,
    this.onMenuPressed,
    this.onFilterPressed,
    this.onLockPressed,
    this.isLockOpen = false,
  });
  

  @override
  Widget build(BuildContext context) {
    final session = Provider.of<SessionProvider>(context, listen: false);
    final String? acessoSenhas = session.acessoLiberarSenhas;

    return Container(
      width: double.infinity,
      color: AppColors.black,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
      child: Row(
        children: [
          // Ícone de menu (hambúrguer) - esquerda
          IconButton(
            onPressed: onMenuPressed,
            icon: const Icon(Icons.menu, color: Colors.white, size: 22),
            padding: EdgeInsets.zero,
            constraints: const BoxConstraints(),
          ),

          // Título centralizado
          Expanded(
            child: Text(
              title,
              textAlign: TextAlign.center,
              style: const TextStyle(
                color: Colors.white,
                fontSize: 16,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),

          // Ícone de cadeado - direita (muda conforme estado)
          if (acessoSenhas == '1')
            IconButton(
              onPressed: onLockPressed,
              icon: AnimatedSwitcher(
                duration: const Duration(milliseconds: 250),
                transitionBuilder: (child, animation) {
                  return ScaleTransition(scale: animation, child: child);
                },
                child: Icon(
                  isLockOpen ? Icons.lock_open : Icons.lock,
                  key: ValueKey<bool>(isLockOpen),
                  color: isLockOpen ? Colors.green : AppColors.orange,
                  size: 22,
                ),
              ),
              padding: EdgeInsets.zero,
              constraints: const BoxConstraints(),
            ),
        ],
      ),
    );
  }
}
