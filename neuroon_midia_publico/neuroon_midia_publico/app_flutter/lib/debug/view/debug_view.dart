import 'package:flutter/material.dart';

class DebugView extends StatelessWidget {
  const DebugView({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Debug Menu'),
      ),
      body: const Center(
        child: Text('Debug actions will appear here.'),
      ),
    );
  }
}
