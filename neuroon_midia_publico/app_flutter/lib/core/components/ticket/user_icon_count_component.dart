import 'package:flutter/material.dart';

class UserIconCount extends StatelessWidget {
  final int count;

  const UserIconCount({super.key, required this.count});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        const Icon(Icons.person, color: Colors.black54, size: 18),
        const SizedBox(width: 6),
        Text(
          count.toString(),
          style: const TextStyle(fontWeight: FontWeight.bold),
        ),
      ],
    );
  }
}
