import 'package:flutter/material.dart';
import 'package:nextpubli/core/components/ticket/status_badge_component.dart';
import 'package:nextpubli/core/components/ticket/ticket_details_popup.dart';
import 'package:nextpubli/core/components/ticket/attendance_confirmation_view.dart';
import 'package:nextpubli/core/themes/app_colors.dart';

class TicketCard extends StatefulWidget {
  final String ticketNumber;
  final String clientName;
  final String createdAt;
  final String? createdAtText;
  final String? elapsedText;
  final String? whatsapp;
  final String? preferencia;
  final String? entradaFila;
  final int userCount;
  final int qtdCadeirantes;
  final int qtdCriancas;
  final int status;
  final int? senhaId;
  final VoidCallback? onTap;
  final ValueChanged<int>? onStatusChanged;
  final int? qtdChamadas;

  const TicketCard({
    super.key,
    this.ticketNumber = '01',
    this.clientName = 'Joao',
    this.createdAt = '01/01/2026 12:00',
    this.createdAtText,
    this.elapsedText,
    this.whatsapp,
    this.preferencia,
    this.entradaFila,
    this.userCount = 1,
    this.qtdCadeirantes = 0,
    this.qtdCriancas = 0,
    this.status = 1,
    this.senhaId,
    this.onTap,
    this.onStatusChanged,
    this.qtdChamadas,
  });

  @override
  State<TicketCard> createState() => _TicketCardState();
}

class _TicketCardState extends State<TicketCard> with SingleTickerProviderStateMixin {
  late int _status;
  late final AnimationController _animationController;
  late final Animation<double> _animation;

  @override
  void initState() {
    super.initState();
    _status = widget.status;
    _animationController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 900),
      lowerBound: 0.7,
      upperBound: 1.0,
    )..repeat(reverse: true);
    _animation = CurvedAnimation(
      parent: _animationController,
      curve: Curves.easeInOut,
    );
  }

  @override
  void didUpdateWidget(TicketCard oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.status != widget.status) {
      _status = widget.status;
    }
  }

  void _updateStatus(int newStatus) {
    if (!mounted) return;
    setState(() => _status = newStatus);
    widget.onStatusChanged?.call(newStatus);
  }

  @override
  void dispose() {
    _animationController.dispose();
    super.dispose();
  }

  String statusToString() {
    switch (_status) {
      case 1:
        return 'Aguardando';
      case 2:
        return 'Chamado';
      case 3:
        return 'Aceito';
      case 4:
        return 'Confirmado';
      case 5:
        return 'Cancelado';
      default:
        return 'Desconhecido';
    }
  }

  Color statusColor() {
    switch (_status) {
      case 1:
        return const Color(0xFFFF6A00);
      case 2:
        return AppColors.ticketBackground;
      case 3:
        return Colors.green;
      case 4:
        return AppColors.secundary;
      case 5:
        return Colors.red;
      default:
        return Colors.grey;
    }
  }

  String _grupoLabel() {
    if (widget.userCount == 1) return '1 pessoa';
    return '${widget.userCount} pessoas';
  }

  String _entradaFilaLabel() {
    if (widget.entradaFila != null) return widget.entradaFila!;
    final parts = widget.createdAt.split(' ');
    if (parts.length >= 2) return parts.last;
    return widget.createdAt;
  }

  // Navega direto para a tela de atendimento (ignora o popup de aceite/cronômetro)
  // O status já foi atualizado para 2 (Chamado) pelo CallViewModel antes de chegar aqui.
  void _navigateToAttendance() {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => AttendanceConfirmationView(
          ticketNumber: widget.ticketNumber,
          clientName: widget.clientName,
          senhaId: widget.senhaId ?? 0,
          whatsapp: widget.whatsapp,
          userCount: widget.userCount,
          entradaFila: _entradaFilaLabel(),
          tempoEspera: widget.elapsedText ?? '--',
          onStatusChanged: _updateStatus,
        ),
      ),
    );
  }

  void handleTap() {
    if (_status == 1) {
      showDialog(
        context: context,
        barrierColor: Colors.black.withAlpha(153),
        builder: (BuildContext dialogContext) {
          return Dialog(
            backgroundColor: Colors.transparent,
            insetPadding: const EdgeInsets.symmetric(horizontal: 24),
            child: TicketDetailsPopup(
              codigo: widget.ticketNumber,
              nome: widget.clientName,
              whatsapp:
                  widget.whatsapp ?? widget.createdAtText ?? '(11) 99999-9999',
              grupo: _grupoLabel(),
              tempoEspera: widget.elapsedText ?? '00 min',
              entradaFila: _entradaFilaLabel(),
              //preferencia: widget.preferencia ?? 'Area interna',
              callButtonLabel: 'Chamar',
              senhaId: widget.senhaId ?? 0,
              onStatusChanged: (status) {
                _updateStatus(status);
              },
              onCallPressed: () {
                // CallViewModel já foi chamado com sucesso dentro do TicketDetailsPopup.
                // Aqui só refletimos o novo status (2 = Chamado) e navegamos.
                _updateStatus(2);
                Navigator.pop(dialogContext);
                // Chamar agora vai direto para a tela de atendimento,
                // sem passar pelo popup de aceite com cronômetro de 5 min.
                _navigateToAttendance();
              },
            ),
          );
        },
      );
    } else if (_status == 2) {
      // Status "Chamado" (caso já exista algum ticket nesse estado):
      // também segue direto para a tela de atendimento.
      _navigateToAttendance();
    } else if (_status == 3) {
      // Lógica para status "Aceito"
    } else if (_status == 4) {
      // Lógica para status "Confirmado"
    } else if (_status == 5) {
      // Lógica para status "Cancelado"
    }
  }

  static const Color _textPrimary = Colors.white;
  static final Color _textSecondary = Colors.white.withValues(alpha: 0.88);

  Widget _buildInfoBadge({required IconData icon, required int value}) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.16),
        borderRadius: BorderRadius.circular(999),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, color: _textPrimary, size: 16),
          const SizedBox(width: 4),
          Text(
            '$value',
            style: TextStyle(
              color: _textPrimary,
              fontSize: 13,
              fontWeight: FontWeight.w700,
            ),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final color = statusColor();
    final phone = widget.whatsapp ??
        widget.createdAtText ??
        '(11) 99999-9999';

    return InkWell(
      onTap: () => handleTap(),
      borderRadius: BorderRadius.circular(12),
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 6, horizontal: 12),
        padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 16),
        decoration: BoxDecoration(
          color: color.withAlpha(64),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: color,
            width: 1.5,
          ),
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            Container(
              padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 22),
              decoration: BoxDecoration(
                color: AppColors.secundary,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(
                  color: AppColors.secundary,
                  width: 1.5,
                ),
              ),
              child: Text(
                widget.ticketNumber,
                style: TextStyle(
                  color: _textPrimary,
                  fontWeight: FontWeight.bold,
                  fontSize: 22,
                ),
              ),
            ),

            const SizedBox(width: 12),

            Expanded(
              flex: 3,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    widget.clientName,
                    style: TextStyle(
                      color: _textPrimary,
                      fontSize: 16,
                      fontWeight: FontWeight.w700,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      Icon(
                        Icons.person,
                        color: _textPrimary,
                        size: 22,
                      ),
                      const SizedBox(width: 6),
                      Text(
                        '${widget.userCount}',
                        style: TextStyle(
                          color: _textPrimary,
                          fontSize: 22,
                          fontWeight: FontWeight.w800,
                          height: 1,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  Wrap(
                    spacing: 10,
                    runSpacing: 8,
                    children: [
                      if (widget.qtdCadeirantes > 0)
                        _buildInfoBadge(
                          icon: Icons.accessible,
                          value: widget.qtdCadeirantes,
                        ),
                      if (widget.qtdCriancas > 0)
                        _buildInfoBadge(
                          icon: Icons.child_care,
                          value: widget.qtdCriancas,
                        ),
                    ],
                  ),
                ],
              ),
            ),

            const SizedBox(width: 2),

            Expanded(
              flex: 4,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                mainAxisAlignment: MainAxisAlignment.center,
                children: [

                  Row(
                    mainAxisAlignment: MainAxisAlignment.end,
                    children: [
                      if ((widget.qtdChamadas ?? 0) > 1) ...[
                        Flexible(
                          child: FittedBox(
                            fit: BoxFit.scaleDown,
                            alignment: Alignment.topRight,
                            child: ScaleTransition(
                              scale: _animation,
                              child: Container(
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 10,
                                  vertical: 12,
                                ),
                                decoration: BoxDecoration(
                                  color: AppColors.ticketBackground,
                                  borderRadius: BorderRadius.circular(999),
                                  boxShadow: [
                                    BoxShadow(
                                      color: AppColors.ticketBackground.withAlpha(80),
                                      blurRadius: 8,
                                      spreadRadius: 1,
                                    ),
                                  ],
                                ),
                                child: Row(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    const Icon(
                                      Icons.repeat,
                                      size: 18,
                                      color: Colors.white,
                                    ),
                                    const SizedBox(width: 4),
                                    Text(
                                      '${widget.qtdChamadas}',
                                      style: const TextStyle(
                                        color: Colors.white,
                                        fontSize: 14,
                                        fontWeight: FontWeight.bold,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            ),
                          ),
                        ),
                        const SizedBox(width: 8),
                      ],
                      Flexible(
                        child: FittedBox(
                          fit: BoxFit.scaleDown,
                          alignment: Alignment.topRight,
                          child: StatusBadge(
                            status: statusToString(),
                            textColor: color,
                            backgroundColor: color.withAlpha(96),
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 36),
                  Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(
                        Icons.phone,
                        color: _textSecondary,
                        size: 13,
                      ),
                      const SizedBox(width: 2),
                      Flexible(
                        child: Text(
                          phone,
                          style: TextStyle(
                            color: _textSecondary,
                            fontSize: 12,
                            fontWeight: FontWeight.w600,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          textAlign: TextAlign.right,
                        ),
                      ),
                      Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 6),
                        child: Text(
                          '·',
                          style: TextStyle(
                            color: _textSecondary,
                            fontSize: 14,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                      Text(
                        widget.elapsedText ?? '00:00',
                        style: TextStyle(
                          color: _textSecondary,
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      const SizedBox(width: 4),
                      Icon(
                        Icons.access_time,
                        color: _textSecondary,
                        size: 13,
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}