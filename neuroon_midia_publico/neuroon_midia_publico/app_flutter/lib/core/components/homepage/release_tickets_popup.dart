import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:nextpubli/core/themes/app_colors.dart';

class ReleaseTicketsPopup extends StatefulWidget {
  const ReleaseTicketsPopup({super.key});

  /// Exibe o popup e retorna a quantidade selecionada, ou null se cancelado.
  static Future<int?> show(BuildContext context) {
    return showDialog<int>(
      context: context,
      barrierColor: Colors.black.withAlpha(178),
      builder: (_) => const ReleaseTicketsPopup(),
    );
  }

  @override
  State<ReleaseTicketsPopup> createState() => _ReleaseTicketsPopupState();
}

class _ReleaseTicketsPopupState extends State<ReleaseTicketsPopup>
    with SingleTickerProviderStateMixin {
  int _count = 100;
  bool _isEditing = false;
  late TextEditingController _textController;
  late FocusNode _focusNode;
  late AnimationController _animController;
  late Animation<double> _scaleAnim;

  @override
  void initState() {
    super.initState();
    _textController = TextEditingController(text: '$_count');
    _focusNode = FocusNode();
    _focusNode.addListener(_onFocusChange);
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
    _focusNode.removeListener(_onFocusChange);
    _focusNode.dispose();
    _textController.dispose();
    _animController.dispose();
    super.dispose();
  }

  void _onFocusChange() {
    if (!_focusNode.hasFocus && _isEditing) {
      _commitEdit();
    }
  }

  void _startEditing() {
    setState(() {
      _isEditing = true;
      _textController.text = '$_count';
    });
    Future.delayed(const Duration(milliseconds: 50), () {
      _focusNode.requestFocus();
      _textController.selection = TextSelection(
        baseOffset: 0,
        extentOffset: _textController.text.length,
      );
    });
  }

  void _commitEdit() {
    final parsed = int.tryParse(_textController.text);
    setState(() {
      if (parsed != null && parsed >= 1) {
        _count = parsed;
      }
      _textController.text = '$_count';
      _isEditing = false;
    });
  }

  void _increment() {
    setState(() => _count++);
  }

  void _decrement() {
    if (_count > 1) {
      setState(() => _count--);
    }
  }

  @override
  Widget build(BuildContext context) {
    return ScaleTransition(
      scale: _scaleAnim,
      child: Dialog(
        backgroundColor: const Color(0xFF131729),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(20),
        ),
        insetPadding: const EdgeInsets.symmetric(horizontal: 32),
        child: Padding(
          padding: const EdgeInsets.fromLTRB(24, 28, 24, 20),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              // Ícone circular no topo
              Container(
                width: 56,
                height: 56,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: AppColors.ticketBackground.withAlpha(30),
                  border: Border.all(
                    color: AppColors.ticketBackground,
                    width: 2.5,
                  ),
                ),
                child: const Icon(
                  Icons.arrow_upward_rounded,
                  color: AppColors.ticketBackground,
                  size: 28,
                ),
              ),

              const SizedBox(height: 18),

              // Título
              const Text(
                'Liberar senhas',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                ),
              ),

              const SizedBox(height: 12),

              // Subtítulo
              const Text(
                'Quantas senhas você deseja\nliberar para atendimento?',
                textAlign: TextAlign.center,
                style: TextStyle(
                  color: Colors.white70,
                  fontSize: 14,
                  height: 1.4,
                ),
              ),

              const SizedBox(height: 24),

              // Contador com - e +
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                decoration: BoxDecoration(
                  color: const Color(0xFF1A1F35),
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(
                    color: Colors.white.withAlpha(20),
                    width: 1,
                  ),
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    // Botão de decrementar
                    _buildCounterButton(
                      icon: Icons.remove,
                      onTap: _decrement,
                      enabled: _count > 1,
                    ),

                    // Valor atual (toque para editar)
                    GestureDetector(
                      onTap: _isEditing ? null : _startEditing,
                      child: SizedBox(
                        width: 80,
                        child: _isEditing
                            ? TextField(
                                controller: _textController,
                                focusNode: _focusNode,
                                keyboardType: TextInputType.number,
                                inputFormatters: [
                                  FilteringTextInputFormatter.digitsOnly,
                                  LengthLimitingTextInputFormatter(3),
                                ],
                                textAlign: TextAlign.center,
                                style: const TextStyle(
                                  color: Colors.white,
                                  fontSize: 36,
                                  fontWeight: FontWeight.bold,
                                ),
                                cursorColor: AppColors.ticketBackground,
                                decoration: const InputDecoration(
                                  border: InputBorder.none,
                                  contentPadding: EdgeInsets.zero,
                                  isDense: true,
                                ),
                                onSubmitted: (_) => _commitEdit(),
                              )
                            : AnimatedSwitcher(
                                duration: const Duration(milliseconds: 200),
                                transitionBuilder: (child, animation) {
                                  return ScaleTransition(scale: animation, child: child);
                                },
                                child: Text(
                                  '$_count',
                                  key: ValueKey<int>(_count),
                                  style: const TextStyle(
                                    color: Colors.white,
                                    fontSize: 36,
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                              ),
                      ),
                    ),

                    // Botão de incrementar
                    _buildCounterButton(
                      icon: Icons.add,
                      onTap: _increment,
                      enabled: true,
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 16),

              // Texto informativo
              Text(
                _count == 1 
                    ? 'Será liberada a próxima senha\nda fila de espera.' 
                    : 'Serão liberadas as próximas $_count senhas\nda fila de espera.',
                textAlign: TextAlign.center,
                style: const TextStyle(
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

                  // Botão Liberar
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
                        onPressed: () => Navigator.of(context).pop(_count),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.transparent,
                          shadowColor: Colors.transparent,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(12),
                          ),
                          padding: const EdgeInsets.symmetric(vertical: 14),
                        ),
                        child: Text(
                          _count == 1 ? 'Liberar 1 senha' : 'Liberar $_count senhas',
                          style: const TextStyle(
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

  Widget _buildCounterButton({
    required IconData icon,
    required VoidCallback onTap,
    required bool enabled,
  }) {
    return GestureDetector(
      onTap: enabled ? onTap : null,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        width: 44,
        height: 44,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          color: Colors.transparent,
          border: Border.all(
            color: enabled
                ? AppColors.ticketBackground
                : Colors.white.withAlpha(30),
            width: 2,
          ),
        ),
        child: Icon(
          icon,
          color: enabled ? AppColors.ticketBackground : Colors.white24,
          size: 22,
        ),
      ),
    );
  }
}
