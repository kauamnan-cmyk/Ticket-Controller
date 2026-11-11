import 'package:flutter/material.dart';
import 'package:nextpubli/core/themes/app_colors.dart';

class BlockTicketsPopup extends StatefulWidget {
  const BlockTicketsPopup({super.key});

  /// Exibe o popup e retorna a quantidade selecionada, ou null se cancelado.
  static Future<int?> show(BuildContext context) {
    return showDialog<int>(
      context: context,
      barrierColor: Colors.black.withAlpha(178),
      builder: (_) => const BlockTicketsPopup(),
    );
  }

  @override
  State<BlockTicketsPopup> createState() => _BlockTicketsPopupState();
}

class _BlockTicketsPopupState extends State<BlockTicketsPopup>
    with SingleTickerProviderStateMixin {
  late AnimationController _animController;
  late Animation<double> _scaleAnim;

  @override
  void initState() {
    super.initState();
    _animController = AnimationController(
      duration: const Duration(milliseconds: 300),
      vsync: this,
    );
    _scaleAnim = CurvedAnimation(
      parent: _animController,
      curve: Curves.easeOutBack,
    );
    _animController.forward();
  }

  @override
  void dispose() {
    _animController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return ScaleTransition(
      scale: _scaleAnim,
      child: Dialog(
        backgroundColor: const Color(0xFF131729),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        insetPadding: const EdgeInsets.symmetric(horizontal: 32),
        child: Padding(
          padding: const EdgeInsets.fromLTRB(24, 28, 24, 20),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              // Ícone circular no topo (rosa/vermelho para bloqueio)
              Container(
                width: 56,
                height: 56,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: AppColors.primary.withAlpha(30),
                  border: Border.all(color: AppColors.primary, width: 2.5),
                ),
                child: const Icon(
                  Icons.arrow_upward_rounded,
                  color: AppColors.primary,
                  size: 28,
                ),
              ),

              const SizedBox(height: 18),

              // Título
              const Text(
                'Bloquear senhas',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                ),
              ),

              const SizedBox(height: 12),

              // Subtítulo
              const Text(
                'Deseja bloquear a emissão de\nnovas senhas para atendimento?',
                textAlign: TextAlign.center,
                style: TextStyle(
                  color: Colors.white70,
                  fontSize: 14,
                  height: 1.4,
                ),
              ),

              const SizedBox(height: 24),

              // Texto informativo
              const Text(
                'A fila de espera será pausada.\nNenhuma nova senha será emitida.',
                textAlign: TextAlign.center,
                style: TextStyle(
                  color: Colors.white54,
                  fontSize: 12,
                  height: 1.4,
                ),
              ),

              const SizedBox(height: 24),

              // Botões de ação
              Row(
                children: [
                  // Botão Cancelar
                  Expanded(
                    child: OutlinedButton(
                      onPressed: () => Navigator.of(context).pop(),
                      style: OutlinedButton.styleFrom(
                        side: const BorderSide(color: Colors.white24),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12),
                        ),
                        padding: const EdgeInsets.symmetric(vertical: 14),
                      ),
                      child: const Text(
                        'Cancelar',
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 14,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                  ),

                  const SizedBox(width: 12),

                  // Botão Bloquear
                  Expanded(
                    flex: 2,
                    child: Container(
                      decoration: BoxDecoration(
                        borderRadius: BorderRadius.circular(12),
                        gradient: const LinearGradient(
                          colors: [
                            AppColors.ticketBackground,
                            Color(0xFF9C40FF),
                            AppColors.primary,
                          ],
                        ),
                      ),
                      child: ElevatedButton(
                        onPressed: () => Navigator.of(context).pop(1),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.transparent,
                          shadowColor: Colors.transparent,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(12),
                          ),
                          padding: const EdgeInsets.symmetric(vertical: 14),
                        ),
                        child: const Text(
                          'Bloquear senhas',
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 14,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
