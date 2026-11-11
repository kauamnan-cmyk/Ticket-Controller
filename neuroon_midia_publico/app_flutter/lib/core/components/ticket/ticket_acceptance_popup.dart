import 'dart:async';

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:nextpubli/core/themes/app_colors.dart';
import 'package:nextpubli/features/main/home/viewmodels/cancel_viewmodel.dart';
import 'package:nextpubli/features/main/home/viewmodels/confirm_arrival_viewmodel.dart';
import 'package:nextpubli/features/main/home/viewmodels/return_waiting_viewmodel.dart';
import 'package:nextpubli/features/main/home/viewmodels/ticket_viewmodel.dart';
import 'package:nextpubli/core/components/ticket/attendance_confirmation_view.dart';

class TicketAcceptancePopup extends StatefulWidget {
  static const int countdownDurationSeconds = 5 * 60;

  final String nome;
  final String mesa;
  final int senhaId;
  final String? whatsapp;
  final int userCount;
  final String entradaFila;
  final String tempoEspera;
  final ValueChanged<int>? onStatusChanged;

  const TicketAcceptancePopup({
    super.key,
    required this.nome,
    required this.mesa,
    required this.senhaId,
    this.whatsapp,
    this.userCount = 1,
    this.entradaFila = '--',
    this.tempoEspera = '--',
    this.onStatusChanged,
  });

  @override
  State<TicketAcceptancePopup> createState() => _TicketAcceptancePopupState();
}

class _TicketAcceptancePopupState extends State<TicketAcceptancePopup> {
  Timer? _timer;
  int _remainingSeconds = TicketAcceptancePopup.countdownDurationSeconds;
  bool _actionTaken = false;
  bool _isProcessing = false;

  @override
  void initState() {
    super.initState();
    _startTimer();
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  void _startTimer() {
    _timer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (!mounted) {
        timer.cancel();
        return;
      }

      if (_remainingSeconds <= 1) {
        timer.cancel();
        setState(() => _remainingSeconds = 0);
        _handleTimeout();
        return;
      }

      setState(() => _remainingSeconds--);
    });
  }

  String _formatTime(int totalSeconds) {
    final minutes = (totalSeconds ~/ 60).toString().padLeft(2, '0');
    final seconds = (totalSeconds % 60).toString().padLeft(2, '0');
    return '$minutes:$seconds';
  }

  Future<void> _refreshTickets() async {
    if (!mounted) return;
    await context.read<TicketViewModel>().buscarSenhas();
  }

  // Fecha o dialog e notifica o status (para casos que NÃƒO navegam para nova tela)
  Future<void> _closeWithStatus(int status) async {
    if (_actionTaken || !mounted) return;

    _actionTaken = true;
    _timer?.cancel();
    widget.onStatusChanged?.call(status);
    await _refreshTickets();

    if (mounted) Navigator.pop(context);
  }

  // Fecha o dialog e navega para a tela de atendimento (status 4)
  Future<void> _navigateToAttendance() async {
    if (_actionTaken || !mounted) return;

    _actionTaken = true;
    _timer?.cancel();
    widget.onStatusChanged?.call(4);
    await _refreshTickets();

    if (!mounted) return;

    // Fecha o dialog
    Navigator.pop(context);

    // Navega para a tela de atendimento por cima da home
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => AttendanceConfirmationView(
          ticketNumber: widget.mesa,
          clientName: widget.nome,
          senhaId: widget.senhaId,
          whatsapp: widget.whatsapp,
          userCount: widget.userCount,
          entradaFila: widget.entradaFila,
          tempoEspera: widget.tempoEspera,
        ),
      ),
    );
  }

  Future<void> _handleTimeout() async {
    if (_actionTaken || _isProcessing || !mounted) return;

    setState(() => _isProcessing = true);

    final ticketVM = context.read<TicketViewModel>();
    final success = await context.read<ReturnWaitingViewModel>().returnWaiting(
      usuarioId: ticketVM.usuarioId ?? 0,
      clienteId: ticketVM.clienteId ?? 0,
      senhaId: widget.senhaId,
      context: context,
    );

    if (!mounted) return;
    setState(() => _isProcessing = false);

    if (success) {
      await _closeWithStatus(1);
    } else {
      _actionTaken = false;
      _showError('NÃ£o foi possÃ­vel retornar o cliente para a fila.');
    }
  }

  Future<void> _handleConfirm() async {
    if (_actionTaken || _isProcessing || !mounted) return;

    setState(() => _isProcessing = true);

    final ticketVM = context.read<TicketViewModel>();
    final success = await context.read<ConfirmArrivalViewModel>().confirmar(
      usuarioId: ticketVM.usuarioId ?? 0,
      clienteId: ticketVM.clienteId ?? 0,
      senhaId: widget.senhaId,
      context: context,
    );

    if (!mounted) return;
    setState(() => _isProcessing = false);

    if (success) {
      await _navigateToAttendance(); // <â€” navega em vez de sÃ³ fechar
    } else {
      _showError('NÃ£o foi possÃ­vel confirmar a chegada.');
    }
  }

  Future<void> _handleCancel() async {
    if (_actionTaken || _isProcessing || !mounted) return;

    setState(() => _isProcessing = true);

    final ticketVM = context.read<TicketViewModel>();
    final success = await context.read<CancelViewModel>().cancel(
      usuarioId: ticketVM.usuarioId ?? 0,
      clienteId: ticketVM.clienteId ?? 0,
      senhaId: widget.senhaId,
      context: context,
    );

    if (!mounted) return;
    setState(() => _isProcessing = false);

    if (success) {
      await _closeWithStatus(5);
    } else {
      _showError('NÃ£o foi possÃ­vel cancelar a chamada.');
    }
  }

  void _showError(String message) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message)),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      height: double.infinity,
      color: AppColors.black,
      padding: const EdgeInsets.symmetric(horizontal: 28),
      child: SafeArea(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              width: 88,
              height: 88,
              decoration: const BoxDecoration(
                shape: BoxShape.circle,
                color: AppColors.secundary,
              ),
              child: const Icon(
                Icons.celebration_outlined,
                color: AppColors.white,
                size: 42,
              ),
            ),
            const SizedBox(height: 28),
            const Text(
              'Cliente chamado!',
              textAlign: TextAlign.center,
              style: TextStyle(
                color: AppColors.white,
                fontSize: 30,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 12),
            Text(
              '${widget.nome} foi chamado para a Mesa ${widget.mesa}.',
              textAlign: TextAlign.center,
              style: TextStyle(
                color: AppColors.white.withAlpha(204),
                fontSize: 15,
                height: 1.4,
              ),
            ),
            const SizedBox(height: 40),
            Container(
              width: 220,
              height: 220,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                border: Border.all(color: AppColors.secundary, width: 6),
              ),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(
                    _formatTime(_remainingSeconds),
                    style: const TextStyle(
                      color: AppColors.white,
                      fontSize: 52,
                      fontWeight: FontWeight.bold,
                      fontFeatures: [FontFeature.tabularFigures()],
                    ),
                  ),
                  const SizedBox(height: 8),
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 28),
                    child: Text(
                      'Tempo para confirmar a chegada',
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        color: AppColors.white.withAlpha(179),
                        fontSize: 13,
                        height: 1.3,
                      ),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 28),
            Text(
              'Confirme quando o cliente chegar Ã  mesa.',
              textAlign: TextAlign.center,
              style: TextStyle(
                color: AppColors.white.withAlpha(179),
                fontSize: 14,
              ),
            ),
            const SizedBox(height: 36),
            SizedBox(
              width: double.infinity,
              child: Material(
                color: Colors.transparent,
                child: InkWell(
                  onTap: _isProcessing ? null : _handleConfirm,
                  borderRadius: BorderRadius.circular(14),
                  child: Ink(
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        colors: _isProcessing
                            ? [Colors.grey, Colors.grey.shade700]
                            : const [AppColors.primary, AppColors.ticketBackground],
                        begin: Alignment.centerLeft,
                        end: Alignment.centerRight,
                      ),
                      borderRadius: BorderRadius.circular(14),
                    ),
                    child: Padding(
                      padding: const EdgeInsets.symmetric(vertical: 18),
                      child: _isProcessing
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
                          : const Text(
                              'Confirmar chegada',
                              textAlign: TextAlign.center,
                              style: TextStyle(
                                color: AppColors.white,
                                fontSize: 16,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                    ),
                  ),
                ),
              ),
            ),
            const SizedBox(height: 20),
            TextButton(
              onPressed: _isProcessing ? null : _handleCancel,
              child: const Text(
                'Cancelar chamada',
                style: TextStyle(
                  color: Colors.red,
                  fontSize: 15,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}