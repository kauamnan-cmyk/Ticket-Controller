import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:nextpubli/core/components/homepage/count_stat_card.dart';
import 'package:nextpubli/core/themes/app_colors.dart';
import 'package:nextpubli/features/main/home/viewmodels/ticket_viewmodel.dart';

class CountTotalTickets extends StatelessWidget {
  const CountTotalTickets({super.key});

  @override
  Widget build(BuildContext context) {
    final count = context.watch<TicketViewModel>().totalTickets;
    return CountStatCard(
      icon: Icons.format_list_numbered,
      iconColor: AppColors.primary,
      countColor: AppColors.primary,
      count: count,
      label: 'Total de senhas',
    );
  }
}
