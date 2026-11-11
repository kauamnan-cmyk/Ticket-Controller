import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:nextpubli/core/themes/app_colors.dart';
import 'package:nextpubli/core/providers/session_provider.dart';
import 'package:nextpubli/features/main/home/viewmodels/ticket_viewmodel.dart';
import 'package:nextpubli/features/main/home/viewmodels/cancel_viewmodel.dart';
import 'package:nextpubli/features/main/home/viewmodels/confirm_arrival_viewmodel.dart';
import 'package:nextpubli/features/main/home/views/home_view.dart';
import 'package:nextpubli/features/main/home/viewmodels/return_line.dart';

class AttendanceConfirmationView extends StatefulWidget {
  final String ticketNumber;
  final String clientName;
  final String? whatsapp;
  final int userCount;
  final int senhaId;
  final String entradaFila;
  final String tempoEspera;
  final ValueChanged<int>? onStatusChanged;

  const AttendanceConfirmationView({
    super.key,
    required this.ticketNumber,
    required this.clientName,
    required this.senhaId,
    this.whatsapp,
    this.userCount = 1,
    this.entradaFila = '--',
    this.tempoEspera = '--',
    this.onStatusChanged,
  });

  @override
  State<AttendanceConfirmationView> createState() =>
      _AttendanceConfirmationViewState();
}

class _AttendanceConfirmationViewState
    extends State<AttendanceConfirmationView> {
  bool _isFinishing = false;
  bool _isCancelling = false;
  bool _isReturning = false;

  String _grupoLabel() {
    if (widget.userCount == 1) return '1 pessoa';
    return '${widget.userCount} pessoas';
  }

  bool get _isProcessing => _isFinishing || _isCancelling || _isReturning;

  Future<void> _refreshTickets() async {
    if (!mounted) return;
    await context.read<TicketViewModel>().buscarSenhas();
  }

  Future<void> _goToHome() async {
    if (!mounted) return;
    Navigator.of(context).popUntil((route) => route.isFirst);
  }

  Future<void> _handleFinish() async {
    if (_isProcessing) return;
    setState(() => _isFinishing = true);

    final ticketVM = context.read<TicketViewModel>();
    final success = await context.read<ConfirmArrivalViewModel>().confirmar(
      usuarioId: ticketVM.usuarioId ?? 0,
      clienteId: ticketVM.clienteId ?? 0,
      senhaId: widget.senhaId,
      context: context,
    );

    if (!mounted) return;
    setState(() => _isFinishing = false);

    if (!success) {
      _showError('NÃ£o foi possÃ­vel finalizar o atendimento.');
      return;
    }

    widget.onStatusChanged?.call(4);

    await _refreshTickets();

    if (!mounted) return;

    await _goToHome();
    Navigator.of(
      context,
    ).push(MaterialPageRoute(builder: (_) => const HomeView()));
  }

  Future<void> _handleReturn() async {
    if (_isProcessing) return;
    setState(() => _isReturning = true);

    final ticketVM = context.read<TicketViewModel>();
    final sessionProvider = context.read<SessionProvider>();

    final success = await ReturnLine().returnLine(
      usuarioId: ticketVM.usuarioId ?? 0,
      clienteId: ticketVM.clienteId ?? 0,
      senhaId: widget.senhaId,
      cookie: sessionProvider.cookie,
      sessionProvider: sessionProvider,
      context: context,
    );

    if (!mounted) return;
    setState(() => _isReturning = false);

    if (success) {
      await _refreshTickets();
      if (!mounted) return;
      await _goToHome();
    } else {
      _showError('NÃ£o foi possÃ­vel devolver Ã  fila.');
    }
  }

  void _showError(String message) {
    if (!mounted) return;
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(SnackBar(content: Text(message)));
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
    return Scaffold(
      backgroundColor: AppColors.black,
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 28),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(height: 16),

              // Header
              Row(
                children: [
                  GestureDetector(
                    onTap: _isProcessing
                        ? null
                        : () => Navigator.of(context).pop(),
                    child: Container(
                      padding: const EdgeInsets.all(8),
                      decoration: BoxDecoration(
                        color: AppColors.gray,
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: const Icon(
                        Icons.arrow_back_ios_new,
                        color: AppColors.white,
                        size: 18,
                      ),
                    ),
                  ),
                  const SizedBox(width: 16),
                  const Text(
                    'Atendimento',
                    style: TextStyle(
                      color: AppColors.white,
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),

              const SizedBox(height: 40),

              // Ticket badge + nome
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(
                      vertical: 10,
                      horizontal: 16,
                    ),
                    decoration: BoxDecoration(
                      color: Colors.blue,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Text(
                      widget.ticketNumber,
                      style: const TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.bold,
                        fontSize: 18,
                      ),
                    ),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          widget.clientName,
                          style: const TextStyle(
                            color: AppColors.white,
                            fontSize: 22,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 10,
                            vertical: 3,
                          ),
                          decoration: BoxDecoration(
                            color: Colors.blue.withAlpha(40),
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: const Text(
                            'Chamado',
                            style: TextStyle(
                              color: Colors.blue,
                              fontSize: 12,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),

              const SizedBox(height: 32),

              // Divider
              Divider(color: AppColors.white.withAlpha(30), height: 1),

              const SizedBox(height: 28),

              // Info cards
              _InfoCard(
                icon: Icons.people_outline,
                label: 'Grupo',
                value: _grupoLabel(),
              ),
              const SizedBox(height: 12),
              _InfoCard(
                icon: Icons.access_time_outlined,
                label: 'Entrada na fila',
                value: widget.entradaFila,
              ),
              const SizedBox(height: 12),
              _InfoCard(
                icon: Icons.hourglass_bottom_outlined,
                label: 'Tempo de espera',
                value: widget.tempoEspera,
              ),
              if (widget.whatsapp != null) ...[
                const SizedBox(height: 12),
                _InfoCard(
                  icon: Icons.phone_outlined,
                  label: 'WhatsApp',
                  value: widget.whatsapp!,
                ),
              ],

              const Spacer(),

              // InstruÃ§Ã£o
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.blue.withAlpha(20),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: Colors.blue.withAlpha(60)),
                ),
                child: Row(
                  children: [
                    const Icon(
                      Icons.info_outline,
                      color: Colors.blue,
                      size: 20,
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        'Cliente CHAMADO. Realize a confirmaÃ§Ã£o quando o cliente comparecer.',
                        style: TextStyle(
                          color: Colors.white.withAlpha(204),
                          fontSize: 13,
                          height: 1.4,
                        ),
                      ),
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 20),

              // BotÃ£o Devolver Ã  Fila
              SizedBox(
                width: double.infinity,
                child: Material(
                  color: Colors.transparent,
                  child: InkWell(
                    onTap: _isProcessing ? null : _handleReturn,
                    borderRadius: BorderRadius.circular(14),
                    child: Ink(
                      decoration: BoxDecoration(
                        color: AppColors.gray,
                        borderRadius: BorderRadius.circular(14),
                      ),
                      child: Padding(
                        padding: const EdgeInsets.symmetric(vertical: 18),
                        child: _isReturning
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
                                'Devolver a Fila',
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

              const SizedBox(height: 14),

              // BotÃ£o Confirmar Chegada
              SizedBox(
                width: double.infinity,
                child: Material(
                  color: Colors.transparent,
                  child: InkWell(
                    onTap: _isProcessing ? null : _handleFinish,
                    borderRadius: BorderRadius.circular(14),
                    child: Ink(
                      decoration: BoxDecoration(
                        gradient: LinearGradient(
                          colors: _isProcessing
                              ? [Colors.grey, Colors.grey.shade700]
                              : const [
                                  AppColors.primary,
                                  AppColors.ticketBackground,
                                ],
                          begin: Alignment.centerLeft,
                          end: Alignment.centerRight,
                        ),
                        borderRadius: BorderRadius.circular(14),
                      ),
                      child: Padding(
                        padding: const EdgeInsets.symmetric(vertical: 18),
                        child: _isFinishing
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
                                'Confirmar Chegada',
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

              const SizedBox(height: 14),

              // BotÃ£o cancelar atendimento
              Center(
                child: TextButton(
                  onPressed: _isProcessing
                      ? null
                      : _showCancelConfirmationDialog,
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

              const SizedBox(height: 12),
            ],
          ),
        ),
      ),
    );
  }
}

class _InfoCard extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;

  const _InfoCard({
    required this.icon,
    required this.label,
    required this.value,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      decoration: BoxDecoration(
        color: AppColors.gray,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        children: [
          Icon(icon, color: AppColors.white.withAlpha(150), size: 20),
          const SizedBox(width: 12),
          Text(
            label,
            style: TextStyle(
              color: AppColors.white.withAlpha(150),
              fontSize: 14,
            ),
          ),
          const Spacer(),
          Text(
            value,
            style: const TextStyle(
              color: AppColors.white,
              fontSize: 14,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }
}