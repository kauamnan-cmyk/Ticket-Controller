import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:nextpubli/core/components/homepage/count_stat_card.dart';
import 'package:nextpubli/features/main/home/viewmodels/ticket_viewmodel.dart';

class CountNumberWaitingPeoples extends StatelessWidget {
  const CountNumberWaitingPeoples({super.key});

  @override
  Widget build(BuildContext context) {
    final count = context.watch<TicketViewModel>().waitingCount;
    return CountStatCard(
      icon: Icons.timer,
      iconColor: const Color.fromARGB(255, 255, 106, 0),
      countColor: const Color.fromARGB(255, 255, 106, 0),
      count: count,
      label: 'Aguardando',
    );
  }
}
