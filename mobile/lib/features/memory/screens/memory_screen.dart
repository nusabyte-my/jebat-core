import 'package:flutter/material.dart';

class MemoryScreen extends StatelessWidget {
  const MemoryScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Memory')),
      body: const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.memory, size: 64, color: Color(0xFF00E5FF)),
            SizedBox(height: 16),
            Text('Memory Browser', style: TextStyle(fontSize: 20)),
            SizedBox(height: 8),
            Text('M0 Sensory · M1 Episodic · M2 Semantic · M3 Conceptual · M4 Procedural',
                textAlign: TextAlign.center, style: TextStyle(color: Colors.grey)),
          ],
        ),
      ),
    );
  }
}
