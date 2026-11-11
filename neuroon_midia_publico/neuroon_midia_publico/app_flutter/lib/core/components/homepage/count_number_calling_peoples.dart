import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:nextpubli/core/components/homepage/count_stat_card.dart';
import 'package:nextpubli/core/themes/app_colors.dart';
import 'package:nextpubli/features/main/home/viewmodels/ticket_viewmodel.dart';

class CountNumberCallingPeoples extends StatelessWidget {
  const CountNumberCallingPeoples({super.key});

  @override
  Widget build(BuildContext context) {
    final count = context.watch<TicketViewModel>().callingCount;
    return CountStatCard(
      icon: Icons.family_restroom,
      iconColor: AppColors.ticketBackground,
      countColor: Colors.blue,
      count: count,
      label: 'Chamados',
    );
  }
}
