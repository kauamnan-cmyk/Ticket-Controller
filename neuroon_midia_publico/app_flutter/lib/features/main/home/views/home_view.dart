import 'dart:async';

import 'package:flutter/material.dart';
import 'package:audioplayers/audioplayers.dart';
import 'package:provider/provider.dart';
import 'package:nextpubli/core/components/homepage/header_component.dart';
import 'package:nextpubli/core/components/homepage/count_total_tickets.dart';
import 'package:nextpubli/core/components/homepage/count_number_waiting_peoples.dart';
import 'package:nextpubli/core/components/homepage/count_number_calling_peoples.dart';
import 'package:nextpubli/core/components/homepage/add_action_button.dart';
import 'package:nextpubli/core/components/homepage/create_ticket_popup.dart';
import 'package:nextpubli/features/main/home/viewmodels/ticket_viewmodel.dart';
import 'package:nextpubli/core/components/ticket/ticket_card_component.dart';
import 'package:nextpubli/core/themes/app_colors.dart';
import 'package:nextpubli/core/components/homepage/ticket_status_filter.dart';
import 'package:nextpubli/core/components/homepage/release_tickets_popup.dart';
import 'package:nextpubli/core/components/homepage/block_tickets_popup.dart';
import 'package:nextpubli/features/main/home/viewmodels/open_viewmodel.dart';
import 'package:nextpubli/features/main/home/viewmodels/block_viewmodel.dart';
import 'package:nextpubli/core/providers/session_provider.dart';
import 'package:nextpubli/main.dart';
import 'package:nextpubli/features/main/home/viewmodels/verify_open_tickets.dart';

class HomeView extends StatefulWidget {
  const HomeView({super.key});

  @override
  State<HomeView> createState() => _HomeViewState();
}

class _HomeViewState extends State<HomeView> with WidgetsBindingObserver {
  static const _pollInterval = Duration(seconds: 5);

  String _searchQuery = '';
  Timer? _pollTimer;
  bool _isLockOpen = false;
  bool _isProcessingLock = false;

  // Player de som para notificaÃ§Ãµes (funciona em Android e iOS)
  final AudioPlayer _audioPlayer = AudioPlayer();

  // Contagens anteriores para detectar qualquer mudanÃ§a (total, aguardando, chamando)
  int _prevTotal = 0;
  int _prevWaiting = 0;
  int _prevCalling = 0;

  // Evita tocar som durante a carga inicial dos dados
  bool _isInitialLoad = true;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);

    WidgetsBinding.instance.addPostFrameCallback((_) {
      // Adiciona listener para detectar mudanÃ§as nas contagens
      context.read<TicketViewModel>().addListener(_onTicketsChanged);
      _loadInitial();
    });
  }

  @override
  void dispose() {
    // Remove o listener e libera o player de Ã¡udio
    context.read<TicketViewModel>().removeListener(_onTicketsChanged);
    _audioPlayer.dispose();
    _stopPolling();
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  /// Chamado sempre que o TicketViewModel notifica uma mudanÃ§a.
  /// Toca o som se qualquer contagem (total, aguardando ou chamando) tiver mudado.
  void _onTicketsChanged() {
    if (!mounted) return;
    // NÃ£o toca som durante a carga inicial dos dados
    if (_isInitialLoad) return;

    final vm = context.read<TicketViewModel>();
    final total   = vm.totalTickets;
    final waiting = vm.waitingCount;
    final calling = vm.callingCount;

    if (total != _prevTotal || waiting != _prevWaiting || calling != _prevCalling) {
      _audioPlayer.play(AssetSource('sounds/notification.mp3'));
    }

    _prevTotal   = total;
    _prevWaiting = waiting;
    _prevCalling = calling;
  }

  // Pausa o polling quando o app vai para background, retoma quando volta
  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      _startPolling();
    } else if (state == AppLifecycleState.paused) {
      _stopPolling();
    }
  }

  Future<void> _loadInitial() async {
    await context.read<TicketViewModel>().buscarSenhas();

    if (mounted) {
      final openVM = context.read<VerifyOpenTickets>();
      final isLiberado = await openVM.verifyStatus();
      if (mounted) {
        setState(() {
          _isLockOpen = isLiberado;
        });
      }
    }

    // ApÃ³s a carga inicial, captura os valores base e habilita o som
    if (mounted) {
      final vm = context.read<TicketViewModel>();
      _prevTotal   = vm.totalTickets;
      _prevWaiting = vm.waitingCount;
      _prevCalling = vm.callingCount;
      _isInitialLoad = false;
    }
    _startPolling();
  }

  void _startPolling() {
    _stopPolling(); // garante que nÃ£o hÃ¡ timer duplicado
    _pollTimer = Timer.periodic(_pollInterval, (_) {
      if (mounted) {
        context.read<TicketViewModel>().pollSenhas();
      }
    });
  }

  void _stopPolling() {
    _pollTimer?.cancel();
    _pollTimer = null;
  }

  void _showMenuDialog(BuildContext context) {
    showDialog(
      context: context,
      barrierColor: Colors.black.withAlpha(153),
      builder: (BuildContext dialogContext) {
        return Dialog(
          backgroundColor: const Color(0xFF1E2230),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
          ),
          child: Padding(
            padding: const EdgeInsets.all(20.0),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const Text(
                  'Opções do Aplicativo',
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 16),
                const Divider(color: Colors.white24, height: 1),
                const SizedBox(height: 12),
                ListTile(
                  leading: const Icon(Icons.logout, color: Colors.red),
                  title: const Text(
                    'Sair do Aplicativo',
                    style: TextStyle(color: Colors.white),
                  ),
                  onTap: () async {
                    // Fechar o modal
                    Navigator.of(dialogContext).pop();

                    // Encerrar sessÃ£o no servidor e limpar estado local
                    if (context.mounted) {
                      await context.read<SessionProvider>().clearSession();
                    }

                    // Reiniciar toda a Ã¡rvore de providers do zero
                    if (context.mounted) {
                      RestartWidget.restartApp(context);
                    }
                  },
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  Future<void> _handleLockPressed() async {
    if (_isProcessingLock) return;
    _isProcessingLock = true;

    try {
      final ticketVM = context.read<TicketViewModel>();
      final clienteId = ticketVM.clienteId;

      if (clienteId == null) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Erro: cliente nÃ£o identificado.')),
        );
        return;
      }

      if (!_isLockOpen) {
        // Cadeado fechado â†’ mostrar popup de liberar
        final quantidade = await ReleaseTicketsPopup.show(context);
        if (quantidade != null && mounted) {
          final openVM = context.read<OpenViewModel>();
          final success = await openVM.open(
            quantidade: quantidade,
            context: context,
          );
          if (success && mounted) {
            setState(() => _isLockOpen = true);
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                content: Text('$quantidade senhas liberadas com sucesso!'),
                backgroundColor: Colors.green,
              ),
            );
          } else if (mounted) {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(
                content: Text('Erro ao liberar senhas.'),
                backgroundColor: Colors.red,
              ),
            );
          }
        }
      } else {
        // Cadeado aberto â†’ mostrar popup de bloquear
        final quantidade = await BlockTicketsPopup.show(context);
        if (quantidade != null && mounted) {
          final blockVM = context.read<BlockViewModel>();
          final success = await blockVM.open(
            quantidade: quantidade,
            context: context,
          );
          if (success && mounted) {
            setState(() => _isLockOpen = false);
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(
                content: Text('EmissÃ£o de senhas bloqueada com sucesso!'),
                backgroundColor: Colors.orange,
              ),
            );
          } else if (mounted) {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(
                content: Text('Erro ao bloquear senhas.'),
                backgroundColor: Colors.red,
              ),
            );
          }
        }
      }
    } finally {
      _isProcessingLock = false;
    }
  }

  @override
  Widget build(BuildContext context) {
    final viewModel = context.watch<TicketViewModel>();

    return Scaffold(
      resizeToAvoidBottomInset: false,
      backgroundColor: AppColors.black,
      body: SafeArea(
        child: Column(
          children: [
            HeaderComponent(
              title: 'Controle de acesso',
              onMenuPressed: () => _showMenuDialog(context),
              onLockPressed: _handleLockPressed,
              isLockOpen: _isLockOpen,
            ),
            const SizedBox(height: 18),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20.0),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(child: CountTotalTickets()),
                  const SizedBox(width: 12),
                  Expanded(child: CountNumberWaitingPeoples()),
                  const SizedBox(width: 12),
                  Expanded(child: CountNumberCallingPeoples()),
                ],
              ),
            ),
            /*
            const SizedBox(height: 18),
            Row(
            children: [
              Expanded(
                child: ActionButton(
                  title: 'Liberar senha',
                  icon: Icons.arrow_upward,
                  color: const Color(0xFFFF00AA),
                  onTap: () {},
                ),
              ),
            const SizedBox(width: 16),
              Expanded(
                child: ActionButton(
                  title: 'Bloquear senha',
                  icon: Icons.lock_outline,
                  color: const Color(0xFF00A3FF),
                  onTap: () {},
                ),
              ),
            ],
          ),
            */
            const SizedBox(height: 18),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20.0),
              child: Row(
                children: [
                  Expanded(
                    child: TextField(
                      onChanged: (value) {
                        setState(() => _searchQuery = value.toLowerCase());
                      },
                      style: const TextStyle(color: Colors.white),
                      decoration: InputDecoration(
                        hintText: 'Pesquisar por senha, nome ou telefone...',
                        hintStyle: const TextStyle(color: Colors.white54),
                        prefixIcon: const Icon(Icons.search, color: Colors.white54),
                        filled: true,
                        fillColor: const Color(0xFF2A2F45),
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(12),
                          borderSide: BorderSide.none,
                        ),
                        enabledBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(12),
                          borderSide: BorderSide.none,
                        ),
                        focusedBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(12),
                          borderSide: BorderSide.none,
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  AddActionButton(
                    onTap: () {
                      showDialog(
                        context: context,
                        barrierDismissible: false,
                        builder: (context) => const CreateTicketPopup(),
                      );
                    },
                  ),
                ],
              ),
            ),
            const SizedBox(height: 12),
            if (viewModel.isLoading)
              const Expanded(child: Center(child: CircularProgressIndicator()))
            else if (viewModel.errorMessage != null)
              Expanded(
                child: Center(
                  child: Text(
                    viewModel.errorMessage!,
                    textAlign: TextAlign.center,
                    style: const TextStyle(color: Colors.white70),
                  ),
                ),
              )
            else
              Expanded(
                child: TicketStatusFilterBar(
                  tickets: viewModel.tickets
                      .where((t) => t.matchesSearch(_searchQuery))
                      .toList(),
                  builder: (filteredTickets) {
                    if (filteredTickets.isEmpty) {
                      return const Center(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(
                              Icons.inbox_outlined,
                              color: Colors.white24,
                              size: 48,
                            ),
                            SizedBox(height: 12),
                            Text(
                              'Nenhum ticket disponÃ­vel',
                              textAlign: TextAlign.center,
                              style: TextStyle(color: Colors.white38),
                            ),
                          ],
                        ),
                      );
                    }

                    return ListView.separated(
                      padding: const EdgeInsets.fromLTRB(20, 0, 20, 20),
                      itemCount: filteredTickets.length,
                      separatorBuilder: (_, _) => const SizedBox(height: 12),
                      itemBuilder: (context, index) {
                        final ticket = filteredTickets[index];
                        return TicketCard(
                          ticketNumber: ticket.senha,
                          clientName: ticket.clienteNome,
                          createdAt: ticket.gerada,
                          whatsapp: ticket.telefone,
                          entradaFila: ticket.entradaFila,
                          elapsedText: ticket.tempoEspera,
                          userCount: ticket.qtdPessoas,
                          qtdCadeirantes: ticket.qtdCadeirantes,
                          qtdCriancas: ticket.qtdCriancas,
                          status: ticket.status,
                          senhaId: ticket.id,
                          qtdChamadas: ticket.chamadasTotal,
                        );
                      },
                    );
                  },
                ),
              ),
          ],
        ),
      ),
    );
  }
}
