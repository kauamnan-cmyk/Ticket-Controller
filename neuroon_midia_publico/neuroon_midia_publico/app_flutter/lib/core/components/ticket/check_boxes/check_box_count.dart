import 'package:flutter/material.dart';

class CheckBox extends StatefulWidget {
  final int initialCount;
  final String nome;
  final int totalPessoas;
  final ValueChanged<int>? onChanged;
  final ValueChanged<bool>? onValidationChanged;

  const CheckBox({
    super.key,
    required this.initialCount,
    required this.nome,
    required this.totalPessoas,
    this.onChanged,
    this.onValidationChanged,
  });

  @override
  State<CheckBox> createState() => _CheckBoxState();
}

class _CheckBoxState extends State<CheckBox> {
  late int count;
  bool? _lastValidationState;

  bool get _hasError =>
      count > widget.totalPessoas ||
      (widget.nome.toLowerCase() == 'crianças' && count == widget.totalPessoas);

  void _notifyValidationIfChanged() {
    final hasError = _hasError;
    if (_lastValidationState == hasError) return;

    _lastValidationState = hasError;
    widget.onValidationChanged?.call(hasError);
  }

  void _scheduleValidationNotification() {
    if (_lastValidationState == _hasError) return;

    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) _notifyValidationIfChanged();
    });
  }

  @override
  void initState() {
    super.initState();
    count = widget.initialCount.clamp(1, 20).toInt();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      widget.onChanged?.call(count);
      _notifyValidationIfChanged();
    });
  }

  @override
  void didUpdateWidget(covariant CheckBox oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.totalPessoas != widget.totalPessoas ||
        oldWidget.nome != widget.nome) {
      _scheduleValidationNotification();
    }
  }

  void _increment() {
    if (count < 20) {
      setState(() {
        count++;
      });
      widget.onChanged?.call(count);
      _notifyValidationIfChanged();
    }
  }

  void _decrement() {
    if (count > 1) {
      setState(() {
        count--;
      });
      widget.onChanged?.call(count);
      _notifyValidationIfChanged();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          widget.nome,
          style: TextStyle(
            color: Colors.white,
            fontSize: 14,
            fontWeight: FontWeight.w600,
          ),
        ),
        const SizedBox(height: 8),
        Container(
          height: 60,
          decoration: BoxDecoration(
            color: const Color(0xFF131722),
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: const Color(0xFF2A2F45)),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 12.0),
                child: InkWell(
                  onTap: _decrement,
                  borderRadius: BorderRadius.circular(20),
                  child: Container(
                    width: 40,
                    height: 40,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      border: Border.all(
                        color: const Color(0xFFFF20BD).withValues(alpha: 0.5),
                      ),
                    ),
                    child: const Icon(Icons.remove, color: Color(0xFFFF20BD)),
                  ),
                ),
              ),
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 12.0),
                child: Text(
                  '$count',
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 20,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 12.0),
                child: InkWell(
                  onTap: _increment,
                  borderRadius: BorderRadius.circular(20),
                  child: Container(
                    width: 40,
                    height: 40,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      border: Border.all(
                        color: const Color(0xFF00A3FF).withValues(alpha: 0.5),
                      ),
                    ),
                    child: const Icon(Icons.add, color: Color(0xFF00A3FF)),
                  ),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 8),
        Text(
          'Mínimo 1 pessoa • Máximo ${widget.totalPessoas} pessoas',
          style: const TextStyle(color: Color(0xFF8A94A6), fontSize: 12),
        ),
        const SizedBox(height: 40),

        if (count > widget.totalPessoas) ...[
          const SizedBox(height: 8),
          const Text(
            'O número de pessoas não pode exceder o total de pessoas.',
            style: TextStyle(color: Colors.red, fontSize: 12),
          ),
        ],
        if (widget.nome.toLowerCase() == 'crianças' &&
            count == widget.totalPessoas) ...[
          const SizedBox(height: 8),
          const Text(
            'O número de crianças não pode ser igual ao total de pessoas.',
            style: TextStyle(color: Colors.red, fontSize: 12),
          ),
        ],
      ],
    );
  }
}
