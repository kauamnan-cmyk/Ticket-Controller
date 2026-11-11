import 'package:flutter/material.dart';
import 'package:nextpubli/features/main/home/models/senha_ticket.dart';
import 'package:nextpubli/core/themes/app_colors.dart';
import 'package:provider/provider.dart';
import 'package:nextpubli/core/providers/session_provider.dart';

class _StatusFilter {
  final int? id;
  final String label;
  final Color color;

  const _StatusFilter({
    required this.id,
    required this.label,
    required this.color,
  });
}

class TicketStatusFilterBar extends StatefulWidget {
  final List<SenhaTicket> tickets;
  final Widget Function(List<SenhaTicket> filteredTickets) builder;

  const TicketStatusFilterBar({
    super.key,
    required this.tickets,
    required this.builder,
  });

  @override
  State<TicketStatusFilterBar> createState() => _TicketStatusFilterBarState();
}

class _TicketStatusFilterBarState extends State<TicketStatusFilterBar> {
  int? _activeStatus;
  bool _initialized = false;
  final ScrollController _scrollController = ScrollController();

  static const List<_StatusFilter> _allFilters = [
    _StatusFilter(id: null, label: 'Todos', color: AppColors.primary),
    _StatusFilter(id: 1, label: 'Aguardando', color: Color(0xFFFF6A00)),
    _StatusFilter(id: 2, label: 'Chamado', color: AppColors.ticketBackground),
    _StatusFilter(id: 3, label: 'Aceito', color: Colors.green),
    _StatusFilter(id: 4, label: 'Confirmado', color: AppColors.secundary),
    _StatusFilter(id: 5, label: 'Cancelado', color: Colors.red),
  ];

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  List<_StatusFilter> _buildAvailableFilters(String? permitidoStr) {
    if (permitidoStr == null || permitidoStr.isEmpty) {
      // Sem dado definido: não exibe nenhum filtro
      return [];
    }

    final permittedIds = permitidoStr
        .split(',')
        .map((e) => int.tryParse(e.trim()))
        .whereType<int>()
        .toList();

    // "Todos" só aparece se os 5 status (1..5) estiverem presentes
    final hasAll = [1, 2, 3, 4, 5].every((id) => permittedIds.contains(id));

    return _allFilters.where((f) {
      if (f.id == null) return hasAll;
      return permittedIds.contains(f.id);
    }).toList();
  }

  List<SenhaTicket> _filtered(int? activeStatus) {
    if (activeStatus == null) return widget.tickets;
    return widget.tickets.where((t) => t.status == activeStatus).toList();
  }

  int _countFor(int? statusId) {
    if (statusId == null) return widget.tickets.length;
    return widget.tickets.where((t) => t.status == statusId).length;
  }

  @override
  Widget build(BuildContext context) {
    final session = context.watch<SessionProvider>();

    // Aguarda o provider carregar os dados do SharedPreferences
    if (session.isLoading) {
      return const Center(child: CircularProgressIndicator());
    }

    debugPrint('=== TicketStatusFilterBar ===');
    debugPrint('statusPermitidos: "${session.statusPermitidos}"');
    debugPrint('statusPrincipal: "${session.statusPrincipal}"');

    final availableFilters = _buildAvailableFilters(session.statusPermitidos);

    // Inicializa o status ativo apenas uma vez, após o provider carregar
    if (!_initialized) {
      final principalStr = session.statusPrincipal;
      final parsed = principalStr != null
          ? int.tryParse(principalStr.trim())
          : null;

      // Usa o principal se ele estiver entre os permitidos, senão usa o primeiro disponível
      if (parsed != null && availableFilters.any((f) => f.id == parsed)) {
        _activeStatus = parsed;
      } else {
        _activeStatus = availableFilters.isNotEmpty
            ? availableFilters.first.id
            : null;
      }
      _initialized = true;
    }

    // Segurança: se o status ativo não estiver mais disponível, reseta
    if (!availableFilters.any((f) => f.id == _activeStatus)) {
      _activeStatus = availableFilters.isNotEmpty
          ? availableFilters.first.id
          : null;
    }

    return Column(
      children: [
        SizedBox(
          height: 52,
          child: RawScrollbar(
            controller: _scrollController,
            thumbVisibility: true,
            thickness: 3.0,
            radius: const Radius.circular(8),
            thumbColor: Colors.white.withAlpha(140),
            padding: const EdgeInsets.only(left: 20, right: 20, bottom: 2),
            child: Padding(
              padding: const EdgeInsets.only(bottom: 10.0),
              child: ListView.separated(
                controller: _scrollController,
                scrollDirection: Axis.horizontal,
                padding: const EdgeInsets.symmetric(horizontal: 20),
                itemCount: availableFilters.length,
                separatorBuilder: (_, _) => const SizedBox(width: 8),
                itemBuilder: (context, index) {
                  final filter = availableFilters[index];
                  final isActive = _activeStatus == filter.id;
                  final color = filter.color;
                  final count = _countFor(filter.id);

                  return GestureDetector(
                    onTap: () => setState(() => _activeStatus = filter.id),
                    child: AnimatedContainer(
                      duration: const Duration(milliseconds: 200),
                      padding: const EdgeInsets.symmetric(
                        horizontal: 14,
                        vertical: 6,
                      ),
                      decoration: BoxDecoration(
                        color: isActive
                            ? color.withAlpha(40)
                            : Colors.transparent,
                        borderRadius: BorderRadius.circular(20),
                        border: Border.all(
                          color: isActive ? color : Colors.white24,
                          width: 1.5,
                        ),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Text(
                            filter.label,
                            style: TextStyle(
                              color: isActive ? color : Colors.white60,
                              fontSize: 13,
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                          const SizedBox(width: 6),
                          Container(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 6,
                              vertical: 1,
                            ),
                            decoration: BoxDecoration(
                              color: isActive
                                  ? color.withAlpha(60)
                                  : Colors.white12,
                              borderRadius: BorderRadius.circular(10),
                            ),
                            child: Text(
                              '$count',
                              style: TextStyle(
                                color: isActive ? color : Colors.white38,
                                fontSize: 11,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  );
                },
              ),
            ),
          ),
        ),
        const SizedBox(height: 12),
        Expanded(child: widget.builder(_filtered(_activeStatus))),
      ],
    );
  }
}
