import 'package:flutter/material.dart';

class AgentsScreen extends StatelessWidget {
  const AgentsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final agents = [
      {'name': 'Panglima', 'role': 'Orchestration', 'icon': '⚔️'},
      {'name': 'Hikmat', 'role': 'Memory', 'icon': '🧠'},
      {'name': 'Tukang', 'role': 'Development', 'icon': '🔧'},
      {'name': 'Hulubalang', 'role': 'Security', 'icon': '🛡️'},
      {'name': 'Pawang', 'role': 'Research', 'icon': '🔍'},
      {'name': 'Syahbandar', 'role': 'Operations', 'icon': '⚙️'},
      {'name': 'Pengawal', 'role': 'CyberSec', 'icon': '🔒'},
    ];

    return Scaffold(
      appBar: AppBar(title: const Text('Agents')),
      body: GridView.builder(
        padding: const EdgeInsets.all(16),
        gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
          crossAxisCount: 2,
          childAspectRatio: 1.5,
          crossAxisSpacing: 12,
          mainAxisSpacing: 12,
        ),
        itemCount: agents.length,
        itemBuilder: (context, index) {
          final agent = agents[index];
          return Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(agent['icon']!, style: const TextStyle(fontSize: 32)),
                  const SizedBox(height: 8),
                  Text(agent['name']!, style: const TextStyle(fontWeight: FontWeight.bold)),
                  Text(agent['role']!, style: const TextStyle(color: Colors.grey, fontSize: 12)),
                ],
              ),
            ),
          );
        },
      ),
    );
  }
}
