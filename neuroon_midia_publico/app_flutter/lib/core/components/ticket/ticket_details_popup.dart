import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:nextpubli/core/themes/app_colors.dart';
import 'package:nextpubli/features/main/home/viewmodels/call_viewmodel.dart';
import 'package:nextpubli/features/main/home/viewmodels/ticket_viewmodel.dart';
import 'package:nextpubli/features/main/home/viewmodels/cancel_viewmodel.dart';

class TicketDetailsPopup extends StatefulWidget {
  final String codigo;
  final String nome;
  final String whatsapp;
  final String grupo;
  final String tempoEspera;
  final String entradaFila;
  //final String preferencia;
  final String callButtonLabel;
  final VoidCallback? onCallPressed;
  final ValueChanged<int>? onStatusChanged;
  final int senhaId;

  const TicketDetailsPopup({
    super.key,
    required this.codigo,
    required this.nome,
    required this.whatsapp,
    required this.grupo,
    required this.tempoEspera,
    required this.entradaFila,
    //required this.preferencia,
    this.callButtonLabel = 'Chamar',
    this.onCallPressed,
    this.onStatusChanged,
    required this.senhaId,
  });

  @override
  State<TicketDetailsPopup> createState() => _TicketDetailsPopupState();
}

class _TicketDetailsPopupState extends State<TicketDetailsPopup> {
  bool _isCalling = false;
  final bool _isFinishing = false;
  bool _isCancelling = false;

  bool get _isProcessing => _isFinishing || _isCancelling;

  Future<void> _refreshTickets() async {
    if (!mounted) return;
    await context.read<TicketViewModel>().buscarSenhas();
  }

  Future<void> _goToHome() async {
    if (!mounted) return;
    Navigator.of(context).popUntil((route) => route.isFirst);
  }

  void _showError(String message) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(message)));
  }

  Future<void> _handleCall() async {
    if (_isCalling || _isProcessing) return;
    setState(() => _isCalling = true);

    final ticketVM = context.read<TicketViewModel>();
    final success = await context.read<CallViewModel>().chamar(
      usuarioId: ticketVM.usuarioId ?? 0,
      clienteId: ticketVM.clienteId ?? 0,
      senhaId: widget.senhaId,
      context: context,
    );

    if (!mounted) return;
    setState(() => _isCalling = false);

    if (!success) return;

    widget.onCallPressed?.call();
  }
  Future<void> _showCancelConfirmationDialog() async {
    final bool? shouldCancel = await showDialog<bool>(
      context: context,
      builder: (BuildContext context) {
        return AlertDialog(
          backgroundColor: const Color(0xFF1E2230),
          title: const Text(
            'Cancelar Atendimento?',
            style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
          ),
          content: const Text(
            'Tem certeza que deseja cancelar o atendimento deste cliente?',
            style: TextStyle(color: Colors.white70),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(false),
              child: const Text(
                'NÃ£o',
                style: TextStyle(
                  color: Colors.grey,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
            TextButton(
              onPressed: () => Navigator.of(context).pop(true),
              child: const Text(
                'Sim, Cancelar',
                style: TextStyle(
                  color: Colors.red,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
          ],
        );
      },
    );

    if (shouldCancel == true) {
      _handleCancel();
    }
  }

  Future<void> _handleCancel() async {
    if (_isProcessing) return;

    setState(() => _isCancelling = true);

    final ticketVM = context.read<TicketViewModel>();
    final success = await context.read<CancelViewModel>().cancel(
      usuarioId: ticketVM.usuarioId ?? 0,
      clienteId: ticketVM.clienteId ?? 0,
      senhaId: widget.senhaId,
      context: context,
    );

    if (!mounted) return;
    setState(() => _isCancelling = false);

    if (success) {
      widget.onStatusChanged?.call(5);
      await _refreshTickets();
      if (!mounted) return;
      await _goToHome();
    } else {
      _showError('NÃ£o foi possÃ­vel cancelar o atendimento.');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(22),
      decoration: BoxDecoration(
        color: AppColors.black,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                widget.codigo,
                style: const TextStyle(
                  color: AppColors.primary,
                  fontWeight: FontWeight.bold,
                  fontSize: 18,
                ),
              ),
              GestureDetector(
                onTap: () => Navigator.pop(context),
                child: const Icon(
                  Icons.close,
                  color: AppColors.white,
                  size: 22,
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Text(
            widget.nome,
            style: const TextStyle(
              color: AppColors.white,
              fontSize: 24,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 12),
          _InfoLine(label: 'WhatsApp:', value: widget.whatsapp),
          const SizedBox(height: 6),
          _InfoLine(label: 'Grupo:', value: widget.grupo),
          const SizedBox(height: 18),
          Divider(
            color: AppColors.white.withAlpha(38),
            thickness: 1,
            height: 1,
          ),
          const SizedBox(height: 18),
          _InfoRowSpaced(label: 'Tempo de espera', value: widget.tempoEspera),
          const SizedBox(height: 10),
          _InfoRowSpaced(label: 'Entrada na fila', value: widget.entradaFila),
          const SizedBox(height: 10),
          const SizedBox(height: 22),
          _GradientCallButton(
            label: widget.callButtonLabel,
            enabled:
                !_isCalling &&
                !_isProcessing &&
                (context.read<TicketViewModel>().usuarioId ?? 0) > 0 &&
                (context.read<TicketViewModel>().clienteId ?? 0) > 0 &&
                widget.senhaId > 0,
            isLoading: _isCalling,
            onPressed: _handleCall,
          ),
          const SizedBox(height: 12),
          Center(
            child: TextButton(
              onPressed: _isProcessing ? null : _showCancelConfirmationDialog,
              child: _isCancelling
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: Colors.red,
                      ),
                    )
                  : const Text(
                      'Cancelar atendimento',
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        color: Colors.red,
                        fontSize: 15,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
            ),
          ),
        ],
      ),
    );
  }
}

class _GradientCallButton extends StatelessWidget {
  final String label;
  final VoidCallback onPressed;
  final bool enabled;
  final bool isLoading;

  const _GradientCallButton({
    required this.label,
    required this.onPressed,
    this.enabled = true,
    this.isLoading = false,
  });

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: double.infinity,
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: enabled && !isLoading ? onPressed : null,
          borderRadius: BorderRadius.circular(14),
          child: Ink(
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: enabled && !isLoading
                    ? const [AppColors.primary, AppColors.ticketBackground]
                    : [Colors.grey, Colors.grey.shade700],
                begin: Alignment.centerLeft,
                end: Alignment.centerRight,
              ),
              borderRadius: BorderRadius.circular(14),
            ),
            child: Padding(
              padding: const EdgeInsets.symmetric(vertical: 16),
              child: isLoading
                  ? const Center(
                      child: SizedBox(
                        width: 22,
                        height: 22,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          color: AppColors.white,
                        ),
                      ),
                    )
                  : Text(
                      label,
                      textAlign: TextAlign.center,
                      style: const TextStyle(
                        color: AppColors.white,
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
            ),
          ),
        ),
      ),
    );
  }
}

class _InfoLine extends StatelessWidget {
  final String label;
  final String value;

  const _InfoLine({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return RichText(
      text: TextSpan(
        style: const TextStyle(fontSize: 14, height: 1.4),
        children: [
          TextSpan(
            text: label,
            style: TextStyle(color: AppColors.white.withAlpha(230)),
          ),
          const TextSpan(text: ' '),
          TextSpan(
            text: value,
            style: const TextStyle(
              color: AppColors.white,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }
}

class _InfoRowSpaced extends StatelessWidget {
  final String label;
  final String value;

  const _InfoRowSpaced({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(
          label,
          style: TextStyle(color: AppColors.white.withAlpha(230), fontSize: 14),
        ),
        Text(
          value,
          style: const TextStyle(
            color: AppColors.white,
            fontSize: 14,
            fontWeight: FontWeight.w600,
          ),
        ),
      ],
    );
  }
}
